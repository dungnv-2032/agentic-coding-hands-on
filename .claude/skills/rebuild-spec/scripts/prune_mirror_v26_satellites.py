#!/usr/bin/env python3
"""prune_mirror_v26_satellites.py -- narrow, provable removal of the three retired
v26 satellite files (business-context.md / screens.md / edge-cases.md) from
translated mirror trees (phase-06,
plans/260818-0758-rebuild-spec-post-migration-completion).

Translate never deletes (`_translation_sync_lib.discover_artifacts` enumerates the
primary tree forward only, phase-00 CORRECTION 3) -- so whatever a mirror holds
that the primary no longer has survives forever unless something explicitly
removes it. This script is that something, and ONLY that: the allow-list below is
exactly the three retired filenames, nowhere else -- never `technical-spec.md`,
`functional-spec.md`, `confidence-report_*.md`, or anything outside
`features/*/`, and never the PRIMARY tree (every candidate path is joined onto
`docs_root/<lang>/`, a CHILD of the directory holding `.rebuild-state.json`,
never written under `docs_root` itself). A general "delete any mirror file with
no primary counterpart" rule is a stated non-goal -- such a file is a signal to
report, not garbage to sweep.

Usage:
    prune_mirror_v26_satellites.py --docs-root <primary> [--lang vi] [--delete]
                                    [--project-root PATH]

Default: lists every path it WOULD remove, with a count. Writes nothing.
--delete: removes exactly those paths, logging each one.

Refuses (exit 2), before listing or deleting anything, if the PRIMARY tree still
holds any of the three retired filenames anywhere under `features/*/` -- pruning a
mirror while the primary is still mid-review (v26 or v27-hybrid shape) would
destroy the only translated copy of content the primary has not yet released
(phase-00 § "The v27 delete gate").
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _audience_split_cli_lib import resolve_project_root_for_docs  # noqa: E402
from _audience_split_shape_lib import V26_SATELLITE_FILES  # noqa: E402
from _lang_lib import normalize_lang  # noqa: E402
from _slug_lib import assert_under  # noqa: E402
from _translation_sync_lib import load_state, secondary_langs  # noqa: E402

_SATELLITE_SET = frozenset(V26_SATELLITE_FILES)

_AUDIENCE_SPLIT_SCRIPT = Path(__file__).parent / "migrate_feature_audience_split.py"


def primary_still_holds_satellites(docs_root: Path) -> int:
    """Count of PRIMARY `features/*/` dirs still holding >=1 retired satellite
    file -- the exact primary-safety refusal predicate. Artifact-derived, read
    fresh every call, never a sentinel."""
    root = docs_root / "features"
    if not root.is_dir():
        return 0
    return sum(
        1 for fd in sorted(root.iterdir())
        if fd.is_dir() and any((fd / name).is_file() for name in _SATELLITE_SET)
    )


def resolve_mirror_langs(docs_root: Path, requested: str | None) -> list[str]:
    """Registered secondary-language keys (raw, undedup-normalized, so the actual
    on-disk dir name is used) from `docs_root/.rebuild-state.json` -- never
    `resolve_docs_root` (phase-00 CORRECTION 4). *requested* (already
    `normalize_lang`-safe) narrows the result to the one matching lang, or `[]` if
    none matches."""
    state = load_state(docs_root / ".rebuild-state.json")
    langs = secondary_langs(state)
    if requested is None:
        return langs
    for lang in langs:
        try:
            if normalize_lang(lang) == requested:
                return [lang]
        except ValueError:
            continue
    return []


def find_satellite_paths(docs_root: Path, project_root: Path, langs: list[str]) -> list[Path]:
    """Every retired satellite path under `docs_root/<lang>/features/*/` for each
    *lang* in *langs* -- glob-derived only (never a string built from CLI text):
    *langs* itself comes only from `resolve_mirror_langs`, which reads the state
    file, and every candidate is re-validated with `assert_under` against
    *project_root* before being returned, so a symlink pointing outside the
    project root is silently skipped rather than followed.

    Mirrors are children of `docs_root` (holding `.rebuild-state.json`), never
    `docs_root.parent` -- measured on the real corpus: `docs_root / "vi"` exists,
    `docs_root.parent / "vi"` does not, for this at-root primary layout."""
    found: list[Path] = []
    for lang in langs:
        features_root = docs_root / lang / "features"
        if not features_root.is_dir():
            continue
        for fd in sorted(features_root.iterdir()):
            if not fd.is_dir():
                continue
            for name in V26_SATELLITE_FILES:
                candidate = fd / name
                if not candidate.is_file():
                    continue
                try:
                    assert_under(candidate, project_root)
                except ValueError:
                    continue  # escapes project_root (e.g. a symlink) -- never touched
                found.append(candidate)
    return found


def _primary_refusal_message(docs_root: Path, project_root: Path, retained: int) -> str:
    return (
        f"[ERROR] refusing to prune: {docs_root} (the PRIMARY tree) still holds "
        f"retired v26 satellite file(s) in {retained} feature dir(s) -- pruning a "
        "mirror now would destroy the only translated copy of content the primary "
        "has not yet released. Clear the primary first: "
        f"python3 {_AUDIENCE_SPLIT_SCRIPT} --docs-root {docs_root} --project-root "
        f"{project_root} --reviewed <reviewed-file> (see its own [ACTION REQUIRED] "
        "block for the exact required sample size)."
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--docs-root", required=True)
    p.add_argument("--project-root", default=None)
    p.add_argument("--lang", default=None)
    p.add_argument("--delete", action="store_true")
    args = p.parse_args(argv)

    docs_root = Path(args.docs_root).resolve()
    if not docs_root.is_dir():
        print(f"[ERROR] --docs-root is not a directory: {docs_root}", file=sys.stderr)
        return 2

    project_root = resolve_project_root_for_docs(args.project_root, docs_root)
    try:
        assert_under(docs_root, project_root)
    except ValueError as exc:
        print(f"[ERROR] {exc} Pass --project-root <repo root>.", file=sys.stderr)
        return 2

    requested_lang: str | None = None
    if args.lang:
        try:
            requested_lang = normalize_lang(args.lang)
        except ValueError as exc:
            print(f"[ERROR] --lang {args.lang!r}: {exc}", file=sys.stderr)
            return 2

    retained = primary_still_holds_satellites(docs_root)
    if retained > 0:
        print(_primary_refusal_message(docs_root, project_root, retained), file=sys.stderr)
        return 2

    langs = resolve_mirror_langs(docs_root, requested_lang)
    if args.lang and not langs:
        print(
            f"[ERROR] --lang {args.lang!r} is not a registered secondary language "
            f"in {docs_root / '.rebuild-state.json'}", file=sys.stderr,
        )
        return 2

    paths = find_satellite_paths(docs_root, project_root, langs)

    if not args.delete:
        for path in paths:
            print(f"[DRY-RUN] would remove {path}")
        print(
            f"[SUMMARY] {len(paths)} retired v26 satellite file(s) would be removed "
            f"across {len(langs)} mirror lang(s) -- pass --delete to remove them"
        )
        return 0

    removed = 0
    errors = 0
    for path in paths:
        try:
            path.unlink()
        except OSError as exc:
            print(f"[ERROR] failed to remove {path}: {exc}", file=sys.stderr)
            errors += 1
            continue
        print(f"[INFO] removed {path}")
        removed += 1

    print(
        f"[SUMMARY] removed {removed} retired v26 satellite file(s) across "
        f"{len(langs)} mirror lang(s)"
        + (f" ({errors} error(s))" if errors else "")
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
