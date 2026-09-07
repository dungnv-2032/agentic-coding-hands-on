"""CLI-only helpers for `migrate_feature_audience_split.py` -- feature-dir discovery,
the `--reviewed` manifest loader, `--dry-run`, `--rollback`, Mode C's per-screen loop,
the sampled-review gate, and B5's cross-repo project-root resolution / language-mirror
refusal guard. Split out of the main script (pass A already exceeded the repo's 200-line
guidance; pass B and phase-06 add more on top, so this extraction keeps the orchestrator
file readable). `migrate_feature` (Mode A) stays in the main module regardless -- its
`compose_fn` default resolves the bare name `compose_mode_a` from THAT module's globals at
call time (see its docstring), so `_run_features` (which calls `migrate_feature` directly)
also stays there to avoid a circular import back into this module. Stdlib only.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _audience_split_migrate_lib import (  # noqa: E402
    backup_path_for, has_feature_sentinel, rollback_feature, staging_feature_dir,
)
from _audience_split_orchestrate_bc_lib import migrate_screen  # noqa: E402
from _audience_split_probe_lib import HAND_EDITED, probe_feature  # noqa: E402
from _audience_split_review_gate_lib import sample_meets_threshold  # noqa: E402
from _audience_split_shape_lib import (  # noqa: E402
    FUNCTIONAL_SPEC, SHAPE_UNKNOWN, SHAPE_V25, SHAPE_V26, SHAPE_V27, TECHNICAL_SPEC,
    V26_SATELLITE_FILES, describe_shape, detect_shape,
)
from _audience_split_tally_lib import ALREADY, FAILED, INERT, PROGRESS, Tally  # noqa: E402
from _slug_lib import is_valid_slug, resolve_project_root  # noqa: E402

__all__ = [
    "split_valid_slugs", "load_reviewed_manifest", "dry_run", "rollback_all",
    "run_screens", "resolve_reviewed_gate", "git_toplevel",
    "resolve_project_root_for_docs", "mirror_refusal_reason",
]

_GIT_TIMEOUT = 5


def _iter_candidate_feature_dirs(docs_root: Path):
    root = docs_root / "features"
    if not root.is_dir():
        return
    for child in sorted(root.iterdir()):
        if child.is_dir():
            yield child


def split_valid_slugs(docs_root: Path) -> tuple[list[Path], list[str]]:
    """M-SEC3: split discovered feature dirs into SLUG_RE-valid (usable) vs rejected
    (name never composed into a staging path)."""
    valid: list[Path] = []
    rejected: list[str] = []
    for fd in _iter_candidate_feature_dirs(docs_root):
        if is_valid_slug(fd.name):
            valid.append(fd)
        else:
            rejected.append(fd.name)
    return valid, rejected


def load_reviewed_manifest(path_str: str) -> set[str]:
    p = Path(path_str).resolve()
    if not p.is_file():
        raise ValueError(f"--reviewed manifest not found: {p}")
    slugs: set[str] = set()
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            slugs.add(line)
    return slugs


def resolve_reviewed_gate(candidates: list[Path], reviewed: set[str] | None) -> set[str] | None:
    """Requirement 5's sample-size arithmetic: a `--reviewed` manifest listing fewer
    than the required threshold of the features whose satellites are still on disk is
    treated as ABSENT for the whole run (not honored for the slugs it does list).

    ELIGIBILITY IS "STILL HOLDS A RETAINED SATELLITE", NOT "IS STILL SHAPE_V26".
    Those coincide only on a corpus's FIRST migration. The original
    `detect_shape(fd) == SHAPE_V26` test silently zeroed the gate on every RETRY: once a
    corpus has been migrated once, every dir is `SHAPE_V27_HYBRID`, so `eligible` was the
    empty set, `required_sample_size(0)` was 0, and `sample_meets_threshold` returned ok
    with "no v26 features eligible this run -- nothing to sample" for ANY manifest size.
    Measured on a real 66-feature corpus after a 7-slug first pass: eligible read 0 while
    59 dirs still held satellites, and a ONE-slug manifest was authorized to delete --
    with the tool's own `[ACTION REQUIRED]` block simultaneously printing "review at least
    6 of them". The retry path is the documented remedy this block tells operators to run,
    so the only control protecting an irreversible delete was dead exactly where it was
    needed. Same predicate as `count_retained_satellite_dirs`, so the required number now
    always matches the number that block prints."""
    if reviewed is None:
        return None
    eligible = {fd.name for fd in candidates
                if any((fd / f).is_file() for f in V26_SATELLITE_FILES)}
    ok, reason = sample_meets_threshold(reviewed, eligible)
    print(f"[INFO] --reviewed gate: {reason}")
    return reviewed if ok else None


def run_screens(project_root: Path, docs_root: Path, tally: Tally) -> None:
    """Mode C, one screen dir at a time -- folds each outcome's action string into
    *tally* (phase-06 B2/B3)."""
    screens_root = docs_root / "screens"
    if not screens_root.is_dir():
        return
    for screen_dir in sorted(screens_root.iterdir()):
        if not screen_dir.is_dir():
            continue
        outcome = migrate_screen(screen_dir, project_root, docs_root)
        print(f"[INFO] {outcome.slug}: {outcome.action} -- {outcome.message}")
        tally.add(outcome.action)


def dry_run(candidates: list[Path], project_root: Path, docs_root: Path) -> int:
    """Read-only: no lock, no staging dir, no mutation of any kind. Scoped to Mode A
    features -- Mode B/C previews are a documented limitation, not a silent gap (see
    the CLI docstring in migrate_feature_audience_split.py). Prints the same
    `[SUMMARY]` shape a real run would (T17) so an operator can predict the verdict;
    the "would-migrate" bucket is an ESTIMATE -- dry-run never runs compose/validate, so
    a unit bucketed PROGRESS here could still turn out `failed-validation` for real."""
    tally = Tally()
    for fd in candidates:
        slug = fd.name
        feat_staging_dir = staging_feature_dir(docs_root, slug)
        if has_feature_sentinel(feat_staging_dir):
            print(f"[DRY-RUN] {slug}: already migrated (sentinel present) -- no-op")
            tally.record(ALREADY, action="no-op")
            continue
        shape = detect_shape(fd)
        if shape in (SHAPE_UNKNOWN, SHAPE_V25):
            print(f"[DRY-RUN] {slug}: REFUSE -- {describe_shape(shape)}")
            tally.record(FAILED, action="refused-unrecognized-shape")
            continue
        if shape == SHAPE_V27:
            print(f"[DRY-RUN] {slug}: {describe_shape(shape)} -- would validate + write sentinel")
            # Derive the category from the action string via the SAME map the live run
            # uses (`Tally.add` -> `categorize`), never a hand-picked constant. A
            # hardcoded PROGRESS here silently drifted from `categorize()`'s ALREADY, so
            # `--dry-run` promised progress a live run would report as already-done --
            # the same "two sources of truth" shape as blocker B2.
            tally.add("confirmed-v27")
            continue
        probe_paths = [fd / TECHNICAL_SPEC] + [fd / f for f in V26_SATELLITE_FILES]
        verdict = probe_feature(probe_paths, project_root)
        would_delete = "skip (hand-edited)" if verdict.verdict == HAND_EDITED else list(V26_SATELLITE_FILES)
        print(
            f"[DRY-RUN] {slug}: shape={shape} probe={verdict.verdict} ({verdict.reason}) "
            f"would-stage=[{FUNCTIONAL_SPEC}, {TECHNICAL_SPEC}] would-delete={would_delete}"
        )
        if verdict.verdict == HAND_EDITED:
            tally.record(INERT, action="skipped-hand-edited")
        else:
            tally.record(PROGRESS, action="would-migrate", provenance=verdict.verdict)
    print(tally.summary_line(sentinel_state="N/A (dry-run writes nothing)"))
    return 0


def rollback_all(candidates: list[Path], docs_root: Path) -> int:
    exit_code = 0
    for fd in candidates:
        feat_staging_dir = staging_feature_dir(docs_root, fd.name)
        if not backup_path_for(feat_staging_dir).is_file():
            continue  # nothing staged for this feature -- nothing to roll back
        try:
            restored = rollback_feature(fd, feat_staging_dir)
            print(f"[INFO] {fd.name}: rolled back {restored}")
        except RuntimeError as exc:
            print(f"[ERROR] {fd.name}: {exc}", file=sys.stderr)
            exit_code = 1
    return exit_code


# --------------------------------------------------------------------------- #
# B5 -- cross-repo usability
# --------------------------------------------------------------------------- #
def git_toplevel(path: Path) -> str | None:
    """Git toplevel of *path*, or None if undeterminable (no git binary, no repo)."""
    try:
        r = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=_GIT_TIMEOUT, check=False,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except (FileNotFoundError, subprocess.SubprocessError):
        pass
    return None


def resolve_project_root_for_docs(arg: str | None, docs_root: Path) -> Path:
    """B5 change 1: default `--project-root` from `--docs-root`'s OWN git toplevel, not
    the CWD's -- makes the common cross-repo invocation (docs tree in a different repo
    than the one this script runs from) just work. Falls back to
    `resolve_project_root(None)` (CWD-based) when *docs_root* has no git toplevel of its
    own."""
    if arg:
        return Path(arg).resolve()
    toplevel = git_toplevel(docs_root)
    if toplevel:
        return Path(toplevel)
    return resolve_project_root(None)


def mirror_refusal_reason(docs_root: Path) -> str | None:
    """B5 change 3: refuse a language-mirror docs root loudly rather than half-work it.
    Verified discriminator (phase-00): `docs/vi/` and `docs/jp/` carry no
    `.rebuild-state.json` of their own; the primary `docs/` does -- state lives only at
    `docs/.rebuild-state.json`. Returns the refusal message, or None when *docs_root*
    is not recognizable as a mirror.

    Phase-06 (P06) change: names the concrete 3-command sequence rather than the
    vague "migrate first" -- the policy itself (refuse a mirror root outright) was
    already correct and is unchanged; only the message gained the exact commands
    an operator runs, in order (phase-00 § CORRECTION 3)."""
    if (docs_root / ".rebuild-state.json").is_file():
        return None
    primary = docs_root.parent
    parent_state = primary / ".rebuild-state.json"
    if parent_state.is_file():
        return (
            f"{docs_root} looks like a translated mirror of {primary} (no "
            f".rebuild-state.json of its own). Non-primary language trees are "
            f"regenerated by the translate pipeline, not migrated. Run these in "
            f"order: (1) clear any retained v26 satellites on the primary -- "
            f"migrate_feature_audience_split.py --docs-root {primary} --project-root "
            f"<repo root> --reviewed <reviewed-file> (see its [ACTION REQUIRED] block "
            f"for the exact required sample size); (2) prune_mirror_v26_satellites.py "
            f"--docs-root {primary} --delete to drop the retired v26 satellite files "
            f"this mirror still carries; (3) /tkm:rebuild-spec --lang <code> to "
            f"regenerate this tree by translating from {primary}."
        )
    return None
