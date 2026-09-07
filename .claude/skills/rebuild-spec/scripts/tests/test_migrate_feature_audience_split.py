"""Tests for migrate_feature_audience_split.py — phase-06 safety machinery (pass A)
plus Mode A/B/C composition, the LLM-invariant gate, and the sampled-review sizing
arithmetic (pass B).

Pass A coverage: I1 (sentinel is the sole migration-state source), I2 (no live source
ever overwritten — atomic swap + pre-swap backup + rollback), I3 (fail-closed hand-edit
probe), I4 (verdict gates composition), I5 (one lock for the whole run), I6
(unrecognized shapes refused) and M-SEC3 (SLUG_RE path guard) — these tests inject a
fake `compose_fn` to exercise the safety pipeline without real composition.

Pass B coverage: real Mode A composition end-to-end through `cli.main()` plus the
migrate→validate triple-pass (`validate_feature_spec` / `validate_feature_screen_link`
/ `validate_feature_api_link`); Mode B business-rules fold (BL### retention); Mode C
screen reorder (`validate_reading_guide_db_impact` pass, zero `## Screen Layout`, both
Phase 02 rule_ids resolved); the LLM structural+semantic invariant gate, including the
condition-dropping fixture that MUST fail; and the `--reviewed` sample-size gate.
"""
from __future__ import annotations

import fcntl
import subprocess
import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import _audience_split_llm_invariant_lib as invariant_lib  # noqa: E402
import _audience_split_mode_b_lib as mode_b_lib  # noqa: E402
import _audience_split_mode_c_lib as mode_c_lib  # noqa: E402
import _audience_split_migrate_lib as mig_lib  # noqa: E402
import _audience_split_orchestrate_bc_lib as orchestrate_bc_lib  # noqa: E402
import _audience_split_probe_lib as probe_lib  # noqa: E402
import _audience_split_review_gate_lib as review_gate_lib  # noqa: E402
import _audience_split_shape_lib as shape_lib  # noqa: E402
import migrate_feature_audience_split as cli  # noqa: E402
import validate_feature_api_link as vfal  # noqa: E402
import validate_feature_screen_link as vfsl  # noqa: E402
import validate_feature_spec as vfs  # noqa: E402
import validate_reading_guide_db_impact as vrg  # noqa: E402

FIXTURES = _TESTS_DIR / "fixtures" / "migrate_feature_audience_split" / "valid-content"
VALID_FUNC = (FIXTURES / "functional-spec.md").read_text(encoding="utf-8")
VALID_TECH = (FIXTURES / "technical-spec.md").read_text(encoding="utf-8")

V26_FIXTURES = _TESTS_DIR / "fixtures" / "migrate_feature_audience_split" / "v26-valid-content"
_V26_FILES = ("business-context.md", "screens.md", "edge-cases.md", "technical-spec.md")


def _valid_composed() -> dict[str, str]:
    return {"functional-spec.md": VALID_FUNC, "technical-spec.md": VALID_TECH}


def _init_git_repo(d: Path) -> None:
    subprocess.run(["git", "init", str(d)], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(d), "config", "user.email", "test@test.com"],
                    capture_output=True, check=True)
    subprocess.run(["git", "-C", str(d), "config", "user.name", "Test"],
                    capture_output=True, check=True)


def _commit_all(d: Path, message: str = "commit") -> None:
    subprocess.run(["git", "-C", str(d), "add", "-A"], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(d), "commit", "-q", "-m", message],
                    capture_output=True, check=True)


def _fm(*lines: str) -> str:
    if not lines:
        return ""
    return "---\n" + "\n".join(lines) + "\n---\n"


def _write_v26_feature(feature_dir: Path, *, tech_frontmatter: str = "authored_by: rebuild-spec",
                       satellite_frontmatter: str = "authored_by: rebuild-spec") -> None:
    """A v26 4-file feature dir: technical-spec.md + the 3 retired satellites."""
    feature_dir.mkdir(parents=True, exist_ok=True)
    (feature_dir / "technical-spec.md").write_text(
        _fm(tech_frontmatter) + "# F001_Auth\n\n## Overview\n\nOld v26 technical spec placeholder.\n",
        encoding="utf-8",
    )
    for name, title in (("business-context.md", "Business Context"),
                        ("screens.md", "Screens"), ("edge-cases.md", "Edge Cases")):
        (feature_dir / name).write_text(
            _fm(satellite_frontmatter) + f"# {title}\n\nPlaceholder.\n", encoding="utf-8",
        )


def _write_v27_feature(feature_dir: Path) -> None:
    """A feature dir already in target (v27) shape, using the valid known-good pair."""
    feature_dir.mkdir(parents=True, exist_ok=True)
    (feature_dir / "functional-spec.md").write_text(VALID_FUNC, encoding="utf-8")
    (feature_dir / "technical-spec.md").write_text(VALID_TECH, encoding="utf-8")


def _write_v26_real_feature(feature_dir: Path) -> None:
    """A REAL (non-placeholder) v26 4-file feature dir, from the hand-built
    v26-valid-content fixture -- used by the migrate→validate integration test, which
    needs content that actually satisfies every deterministic validator, not just a
    shape-detection placeholder."""
    feature_dir.mkdir(parents=True, exist_ok=True)
    for name in _V26_FILES:
        (feature_dir / name).write_text(
            (V26_FIXTURES / name).read_text(encoding="utf-8"), encoding="utf-8",
        )


# --------------------------------------------------------------------------- #
# I6 — shape detection / refusal
# --------------------------------------------------------------------------- #
def test_shape_detects_v26_four_file(tmp_path):
    _write_v26_feature(tmp_path)
    assert shape_lib.detect_shape(tmp_path) == shape_lib.SHAPE_V26


def test_shape_detects_v27_two_file(tmp_path):
    _write_v27_feature(tmp_path)
    assert shape_lib.detect_shape(tmp_path) == shape_lib.SHAPE_V27


def test_i6_refuse_v25_single_spec(tmp_path):
    docs_root = tmp_path / "docs"
    feature_dir = docs_root / "features" / "F001_Auth"
    feature_dir.mkdir(parents=True)
    (feature_dir / "spec.md").write_text("# F001_Auth\n\nOld single-file spec.\n", encoding="utf-8")

    assert shape_lib.detect_shape(feature_dir) == shape_lib.SHAPE_V25
    try:
        cli.migrate_feature(feature_dir, project_root=tmp_path, docs_root=docs_root)
        assert False, "expected UnrecognizedShapeError"
    except shape_lib.UnrecognizedShapeError as exc:
        assert exc.shape == shape_lib.SHAPE_V25
    # REFUSE: zero bytes written anywhere.
    assert not (docs_root / mig_lib.STAGING_DIRNAME).exists()
    assert (feature_dir / "spec.md").is_file()


def test_i6_refuse_unknown_partially_restructured(tmp_path):
    docs_root = tmp_path / "docs"
    feature_dir = docs_root / "features" / "F001_Auth"
    # Mid-hand-restructure mix: a functional-spec.md alongside only ONE retired
    # satellite (screens.md) and no edge-cases.md/business-context.md — matches
    # neither v26 (needs all 3 satellites) nor v27 (must have zero satellites).
    _write_v27_feature(feature_dir)
    (feature_dir / "screens.md").write_text("# Screens\n\nleftover.\n", encoding="utf-8")

    assert shape_lib.detect_shape(feature_dir) == shape_lib.SHAPE_UNKNOWN
    try:
        cli.migrate_feature(feature_dir, project_root=tmp_path, docs_root=docs_root)
        assert False, "expected UnrecognizedShapeError"
    except shape_lib.UnrecognizedShapeError as exc:
        assert exc.shape == shape_lib.SHAPE_UNKNOWN
    assert not (docs_root / mig_lib.STAGING_DIRNAME).exists()


# --------------------------------------------------------------------------- #
# I3 — fail-closed hand-edit probe
# --------------------------------------------------------------------------- #
def test_probe_clean_when_authored_by_rebuild_spec_and_clean_git_trail(tmp_path):
    _init_git_repo(tmp_path)
    path = tmp_path / "docs" / "features" / "F001_Auth" / "technical-spec.md"
    path.parent.mkdir(parents=True)
    path.write_text(_fm("authored_by: rebuild-spec") + "# F001_Auth\n\nContent.\n", encoding="utf-8")
    _commit_all(tmp_path)

    result = probe_lib.probe_file(path, tmp_path)
    assert result.verdict == probe_lib.CLEAN


def test_c2_probe_uncommitted_hand_edit_after_commit_is_hand_edited(tmp_path):
    """C2: `_has_git_trail` alone only proves the file was EVER committed -- it says
    nothing about whether the working tree still matches that commit. A file committed
    once with `authored_by: rebuild-spec` and then hand-edited locally, without
    re-committing and without touching `authored_by:`, must be HAND_EDITED, not CLEAN.
    Before the fix this was misclassified `clean` and would proceed straight to
    composition and, with `--reviewed`, deletion (I3/I4)."""
    _init_git_repo(tmp_path)
    path = tmp_path / "docs" / "features" / "F001_Auth" / "technical-spec.md"
    path.parent.mkdir(parents=True)
    path.write_text(_fm("authored_by: rebuild-spec") + "# F001_Auth\n\nGenerated content.\n",
                     encoding="utf-8")
    _commit_all(tmp_path)

    # Human hand-edits the body only -- never re-commits, never touches authored_by:.
    path.write_text(_fm("authored_by: rebuild-spec") + "# F001_Auth\n\nHAND-EDITED, uncommitted.\n",
                     encoding="utf-8")
    status = subprocess.run(
        ["git", "-C", str(tmp_path), "status", "--porcelain"],
        capture_output=True, text=True, check=True,
    ).stdout
    assert status.strip(), "fixture setup bug: expected a dirty working tree"

    result = probe_lib.probe_file(path, tmp_path)
    assert result.verdict == probe_lib.HAND_EDITED
    assert "HEAD" in result.reason or "uncommitted" in result.reason


def test_probe_authored_by_absent_is_hand_edited_not_default(tmp_path):
    """I3 trap: read_authored_by() defaults to 'rebuild-spec' when absent — the probe
    must NOT consume that default for a delete decision.

    Phase-02 (B1) note: this fixture's content ("# F001_Auth\\n\\nNo frontmatter at
    all.\\n") carries no legacy generator marker either (no `**Generated**:` line, no
    `<!-- Contract: -->` header), so under the new origin/integrity split it still
    resolves HAND_EDITED via the "no generator marker found" path — absence of
    `authored_by:` is necessary but no longer sufficient on its own; see
    test_audience_split_probe_legacy_markers.py for the marker-bearing counter-cases
    (T1-T14) that this fixture deliberately does NOT cover. No assertion changed here
    (phase-00 U2)."""
    _init_git_repo(tmp_path)
    path = tmp_path / "docs" / "features" / "F001_Auth" / "technical-spec.md"
    path.parent.mkdir(parents=True)
    path.write_text("# F001_Auth\n\nNo frontmatter at all.\n", encoding="utf-8")
    _commit_all(tmp_path)

    from _slug_lib import read_authored_by
    assert read_authored_by(path) == "rebuild-spec"  # the default this test guards against

    result = probe_lib.probe_file(path, tmp_path)
    assert result.verdict == probe_lib.HAND_EDITED
    assert "absent" in result.reason


def test_probe_doc_lock_user_is_hand_edited(tmp_path):
    _init_git_repo(tmp_path)
    path = tmp_path / "docs" / "features" / "F001_Auth" / "technical-spec.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        _fm("authored_by: rebuild-spec", "doc_lock: user") + "# F001_Auth\n\nLocked.\n",
        encoding="utf-8",
    )
    _commit_all(tmp_path)

    result = probe_lib.probe_file(path, tmp_path)
    assert result.verdict == probe_lib.HAND_EDITED
    assert result.doc_lock is True


def test_probe_no_git_trail_untracked_is_hand_edited(tmp_path):
    _init_git_repo(tmp_path)
    path = tmp_path / "docs" / "features" / "F001_Auth" / "technical-spec.md"
    path.parent.mkdir(parents=True)
    path.write_text(_fm("authored_by: rebuild-spec") + "# F001_Auth\n\nUntracked.\n", encoding="utf-8")
    # deliberately never `git add`/`git commit`ed

    result = probe_lib.probe_file(path, tmp_path)
    assert result.verdict == probe_lib.HAND_EDITED
    assert "git trail" in result.reason


def test_probe_no_git_directory_is_hand_edited(tmp_path):
    # No `git init` at all under tmp_path.
    path = tmp_path / "docs" / "features" / "F001_Auth" / "technical-spec.md"
    path.parent.mkdir(parents=True)
    path.write_text(_fm("authored_by: rebuild-spec") + "# F001_Auth\n\nNo repo.\n", encoding="utf-8")

    result = probe_lib.probe_file(path, tmp_path)
    assert result.verdict == probe_lib.HAND_EDITED
    assert ".git directory" in result.reason


def test_probe_git_binary_unavailable_is_hand_edited(tmp_path, monkeypatch):
    _init_git_repo(tmp_path)
    path = tmp_path / "docs" / "features" / "F001_Auth" / "technical-spec.md"
    path.parent.mkdir(parents=True)
    path.write_text(_fm("authored_by: rebuild-spec") + "# F001_Auth\n\nContent.\n", encoding="utf-8")
    _commit_all(tmp_path)

    monkeypatch.setattr(probe_lib.shutil, "which", lambda _name: None)
    result = probe_lib.probe_file(path, tmp_path)
    assert result.verdict == probe_lib.HAND_EDITED
    assert "git binary" in result.reason


def test_probe_feature_hand_edited_never_reaches_compose_fn(tmp_path):
    """I4: a hand-edited/locked feature's content is never composed — compose_fn must
    not even be called."""
    docs_root = tmp_path / "docs"
    feature_dir = docs_root / "features" / "F001_Auth"
    _write_v26_feature(feature_dir, tech_frontmatter="authored_by: rebuild-spec\ndoc_lock: user")
    _init_git_repo(tmp_path)
    _commit_all(tmp_path)

    called = []

    def _spy_compose(fd):
        called.append(fd)
        return _valid_composed()

    outcome = cli.migrate_feature(feature_dir, project_root=tmp_path, docs_root=docs_root,
                                  compose_fn=_spy_compose)
    assert outcome.action == "skipped-hand-edited"
    assert outcome.exit_ok
    assert called == []  # compose_fn never invoked
    # originals untouched
    assert (feature_dir / "business-context.md").is_file()
    assert not (feature_dir / "functional-spec.md").is_file()


# --------------------------------------------------------------------------- #
# I1 — sentinel is the sole migration-state source; resume after a crash
# --------------------------------------------------------------------------- #
def test_i1_resume_after_functional_spec_swap_before_sentinel(tmp_path):
    _init_git_repo(tmp_path)
    docs_root = tmp_path / "docs"
    feature_dir = docs_root / "features" / "F001_Auth"
    _write_v26_feature(feature_dir)
    _commit_all(tmp_path)

    feat_staging_dir = mig_lib.staging_feature_dir(docs_root, "F001_Auth")
    composed = _valid_composed()
    mig_lib.stage_feature(feature_dir, feat_staging_dir, composed)
    ok, issues = mig_lib.validate_feature_dir(feat_staging_dir, tmp_path)
    assert ok, issues

    # Simulate a crash: only the functional-spec.md swap completes.
    mig_lib.swap_functional_spec(feature_dir, feat_staging_dir)
    assert not mig_lib.has_feature_sentinel(feat_staging_dir)
    assert (feature_dir / "technical-spec.md").read_text(encoding="utf-8") != composed["technical-spec.md"]

    # Re-run must RESUME, not no-op (I1: file presence never implies "already migrated").
    outcome = cli.migrate_feature(feature_dir, project_root=tmp_path, docs_root=docs_root,
                                  compose_fn=lambda fd: composed)
    assert outcome.action != "no-op"
    assert outcome.exit_ok
    assert mig_lib.has_feature_sentinel(feat_staging_dir)
    assert (feature_dir / "functional-spec.md").read_text(encoding="utf-8") == composed["functional-spec.md"]
    assert (feature_dir / "technical-spec.md").read_text(encoding="utf-8") == composed["technical-spec.md"]


def test_c1_resume_never_swaps_content_that_was_never_validated(tmp_path):
    """C1: the resume path must not infer "already validated" from the pre-swap
    backup's mere existence. Reproduces the exact crash window the review named:
    `stage_feature()` completed (backup + BOTH staged files written), but the process
    died before `validate_feature_dir()` ever ran on that staged content. Before the
    fix, the next invocation read the backup's existence as "resuming an already-
    validated run", skipped validation entirely, and swapped the broken staged content
    straight into the live feature dir while reporting exit_ok=True."""
    _init_git_repo(tmp_path)
    docs_root = tmp_path / "docs"
    feature_dir = docs_root / "features" / "F001_Auth"
    _write_v26_feature(feature_dir)
    _commit_all(tmp_path)

    originals = {
        name: (feature_dir / name).read_bytes()
        for name in ("technical-spec.md", "business-context.md", "screens.md", "edge-cases.md")
    }

    feat_staging_dir = mig_lib.staging_feature_dir(docs_root, "F001_Auth")
    broken_composed = {
        "functional-spec.md": "# F001_Auth\n\n## 1. Overview\n\nBROKEN -- missing all required sections.\n",
        "technical-spec.md": "# BROKEN too\n",
    }
    # Simulate the crash: stage_feature() runs to completion (writes the pre-swap
    # backup + both staged files) but validate_feature_dir() is deliberately never
    # called -- this IS the crash window, not a shortcut around it.
    mig_lib.stage_feature(feature_dir, feat_staging_dir, broken_composed)
    assert mig_lib.backup_path_for(feat_staging_dir).is_file()  # the pre-fix "resuming" signal

    outcome = cli.migrate_feature(feature_dir, project_root=tmp_path, docs_root=docs_root)

    assert not outcome.exit_ok
    assert outcome.action == "failed-validation"
    for name, data in originals.items():
        assert (feature_dir / name).read_bytes() == data, f"{name} was mutated"
    assert not (feature_dir / "functional-spec.md").is_file()


# --------------------------------------------------------------------------- #
# I2 — no live source ever overwritten; --rollback restores from the pre-swap backup
# --------------------------------------------------------------------------- #
def test_i2_rollback_restores_technical_spec_byte_identical(tmp_path):
    _init_git_repo(tmp_path)
    docs_root = tmp_path / "docs"
    feature_dir = docs_root / "features" / "F001_Auth"
    _write_v26_feature(feature_dir)
    _commit_all(tmp_path)
    original_tech_bytes = (feature_dir / "technical-spec.md").read_bytes()

    feat_staging_dir = mig_lib.staging_feature_dir(docs_root, "F001_Auth")
    composed = _valid_composed()
    mig_lib.stage_feature(feature_dir, feat_staging_dir, composed)
    ok, issues = mig_lib.validate_feature_dir(feat_staging_dir, tmp_path)
    assert ok, issues

    # Simulate a crash mid-swap of technical-spec.md: both swaps land live, but the
    # sentinel is never written.
    mig_lib.swap_functional_spec(feature_dir, feat_staging_dir)
    mig_lib.swap_technical_spec(feature_dir, feat_staging_dir)
    assert not mig_lib.has_feature_sentinel(feat_staging_dir)
    assert (feature_dir / "technical-spec.md").read_bytes() != original_tech_bytes

    restored = mig_lib.rollback_feature(feature_dir, feat_staging_dir)
    assert "technical-spec.md" in restored
    assert (feature_dir / "technical-spec.md").read_bytes() == original_tech_bytes
    assert not (feature_dir / "functional-spec.md").is_file()


def test_rollback_refuses_when_sentinel_present(tmp_path):
    _init_git_repo(tmp_path)
    docs_root = tmp_path / "docs"
    feature_dir = docs_root / "features" / "F001_Auth"
    _write_v26_feature(feature_dir)
    _commit_all(tmp_path)

    feat_staging_dir = mig_lib.staging_feature_dir(docs_root, "F001_Auth")
    composed = _valid_composed()
    mig_lib.stage_feature(feature_dir, feat_staging_dir, composed)
    mig_lib.swap_functional_spec(feature_dir, feat_staging_dir)
    mig_lib.swap_technical_spec(feature_dir, feat_staging_dir)
    mig_lib.write_feature_sentinel(feat_staging_dir)

    try:
        mig_lib.rollback_feature(feature_dir, feat_staging_dir)
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        assert "COMPLETE" in str(exc)


# --------------------------------------------------------------------------- #
# Negative probe — a fixture whose staged output fails validation
# --------------------------------------------------------------------------- #
def test_negative_probe_failed_validation_leaves_all_originals_byte_identical(tmp_path):
    _init_git_repo(tmp_path)
    docs_root = tmp_path / "docs"
    feature_dir = docs_root / "features" / "F001_Auth"
    _write_v26_feature(feature_dir)
    _commit_all(tmp_path)

    originals = {
        name: (feature_dir / name).read_bytes()
        for name in ("technical-spec.md", "business-context.md", "screens.md", "edge-cases.md")
    }

    broken_composed = {
        "functional-spec.md": "# F001_Auth\n\n## 1. Overview\n\nMissing 9 required sections.\n",
        "technical-spec.md": VALID_TECH,
    }
    outcome = cli.migrate_feature(feature_dir, project_root=tmp_path, docs_root=docs_root,
                                  compose_fn=lambda fd: broken_composed)

    assert not outcome.exit_ok
    assert outcome.action == "failed-validation"
    for name, data in originals.items():
        assert (feature_dir / name).read_bytes() == data, f"{name} was mutated"
    assert not (feature_dir / "functional-spec.md").is_file()


def test_negative_probe_cli_exit_code_nonzero(tmp_path, monkeypatch):
    """Same fixture, driven through main() with compose_mode_a monkeypatched to the
    broken composer, asserting the REAL process-level exit code is non-zero."""
    _init_git_repo(tmp_path)
    docs_root = tmp_path / "docs"
    feature_dir = docs_root / "features" / "F001_Auth"
    _write_v26_feature(feature_dir)
    _commit_all(tmp_path)

    broken_composed = {
        "functional-spec.md": "# F001_Auth\n\n## 1. Overview\n\nMissing 9 required sections.\n",
        "technical-spec.md": VALID_TECH,
    }
    monkeypatch.setattr(cli, "compose_mode_a", lambda fd: broken_composed)

    exit_code = cli.main(["--docs-root", str(docs_root), "--project-root", str(tmp_path)])
    assert exit_code != 0
    assert not (feature_dir / "functional-spec.md").is_file()


# --------------------------------------------------------------------------- #
# --dry-run writes zero bytes; a second run on a sentineled tree is a no-op
# --------------------------------------------------------------------------- #
def test_dry_run_writes_zero_bytes(tmp_path):
    _init_git_repo(tmp_path)
    docs_root = tmp_path / "docs"
    v26_dir = docs_root / "features" / "F001_Auth"
    v27_dir = docs_root / "features" / "F002_Search"
    _write_v26_feature(v26_dir)
    _write_v27_feature(v27_dir)
    _commit_all(tmp_path)

    before = {
        p: p.stat().st_mtime
        for p in docs_root.rglob("*") if p.is_file()
    }
    listing_before = sorted(str(p) for p in docs_root.rglob("*"))

    exit_code = cli.main(["--docs-root", str(docs_root), "--project-root", str(tmp_path), "--dry-run"])

    assert exit_code == 0
    listing_after = sorted(str(p) for p in docs_root.rglob("*"))
    assert listing_after == listing_before
    for p, mtime in before.items():
        assert p.stat().st_mtime == mtime
    assert not (docs_root / mig_lib.STAGING_DIRNAME).exists()


def test_second_run_on_sentineled_tree_is_noop(tmp_path):
    _init_git_repo(tmp_path)
    docs_root = tmp_path / "docs"
    feature_dir = docs_root / "features" / "F001_Auth"
    _write_v27_feature(feature_dir)  # already-target shape needs no compose_fn
    _commit_all(tmp_path)

    first = cli.main(["--docs-root", str(docs_root), "--project-root", str(tmp_path)])
    assert first == 0
    assert mig_lib.has_run_sentinel(docs_root)

    run_sentinel_mtime = mig_lib.run_sentinel_path(docs_root).stat().st_mtime
    feature_sentinel = mig_lib.staging_feature_dir(docs_root, "F001_Auth") / mig_lib.FEATURE_SENTINEL_NAME
    feature_sentinel_mtime = feature_sentinel.stat().st_mtime

    second = cli.main(["--docs-root", str(docs_root), "--project-root", str(tmp_path)])
    assert second == 0
    # No re-write: mtimes unchanged (fast no-op via the run-level sentinel, I1).
    assert mig_lib.run_sentinel_path(docs_root).stat().st_mtime == run_sentinel_mtime
    assert feature_sentinel.stat().st_mtime == feature_sentinel_mtime


# --------------------------------------------------------------------------- #
# I5 — one lock for the whole run
# --------------------------------------------------------------------------- #
def test_i5_second_invocation_while_lock_held_aborts(tmp_path):
    _init_git_repo(tmp_path)
    docs_root = tmp_path / "docs"
    feature_dir = docs_root / "features" / "F001_Auth"
    _write_v26_feature(feature_dir)
    _commit_all(tmp_path)

    lock_path = mig_lib.staging_root(docs_root) / mig_lib.LOCK_NAME
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    held_fh = open(lock_path, "w")
    fcntl.flock(held_fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        exit_code = cli.main(["--docs-root", str(docs_root), "--project-root", str(tmp_path)])
        assert exit_code == 3
        # staging never touched by the second invocation
        assert not mig_lib.staging_features_root(docs_root).exists()
    finally:
        fcntl.flock(held_fh, fcntl.LOCK_UN)
        held_fh.close()


def test_lock_context_manager_raises_lock_held_error_directly(tmp_path):
    lock_path = tmp_path / ".migrate-feature-audience-split.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    held_fh = open(lock_path, "w")
    fcntl.flock(held_fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        try:
            with mig_lib.Lock(lock_path):
                assert False, "expected LockHeldError"
        except mig_lib.LockHeldError:
            pass
    finally:
        fcntl.flock(held_fh, fcntl.LOCK_UN)
        held_fh.close()


# --------------------------------------------------------------------------- #
# M-SEC3 — a feature-dir name failing SLUG_RE is skipped/rejected
# --------------------------------------------------------------------------- #
def test_msec3_invalid_slug_dir_never_staged(tmp_path):
    docs_root = tmp_path / "docs"
    bad_dir = docs_root / "features" / "F001-Bad-Name"  # hyphens fail SLUG_RE
    _write_v26_feature(bad_dir)

    outcome = cli.migrate_feature(bad_dir, project_root=tmp_path, docs_root=docs_root)
    assert outcome.action == "rejected-bad-slug"
    assert outcome.exit_ok is False
    assert not mig_lib.staging_feature_dir(docs_root, bad_dir.name).exists()


def test_msec3_cli_splits_valid_and_rejected_slugs(tmp_path):
    docs_root = tmp_path / "docs"
    good_dir = docs_root / "features" / "F001_Auth"
    bad_dir = docs_root / "features" / "not-a-feature"
    _write_v27_feature(good_dir)
    bad_dir.mkdir(parents=True)
    (bad_dir / "technical-spec.md").write_text("# stray\n", encoding="utf-8")

    candidates, rejected = cli._split_valid_slugs(docs_root)
    assert [c.name for c in candidates] == ["F001_Auth"]
    assert rejected == ["not-a-feature"]


# --------------------------------------------------------------------------- #
# PASS B -- Integration: Mode A migrate -> validate triple pass
# --------------------------------------------------------------------------- #
def test_integration_migrate_then_validate_triple_pass(tmp_path):
    """A real v26 fixture tree migrates through the actual CLI (no injected
    compose_fn), and validate_feature_spec.py + validate_feature_screen_link.py +
    validate_feature_api_link.py all PASS on the result."""
    _init_git_repo(tmp_path)
    docs_root = tmp_path / "docs"
    feature_dir = docs_root / "features" / "F001_Auth"
    _write_v26_real_feature(feature_dir)

    generated = docs_root / "generated"
    generated.mkdir(parents=True)
    (generated / "feature-list.md").write_text(
        "# Feature List\n\n| Code | Priority | Type |\n|------|----------|------|\n"
        "| F001_Auth | P2 | ui |\n", encoding="utf-8",
    )
    (generated / "screen-list.md").write_text(
        "# Screen List\n\n| Code | Feature |\n|------|---------|\n"
        "| SCR001_Login | F001_Auth |\n", encoding="utf-8",
    )
    (generated / "route-list.md").write_text(
        "# Route List\n\n## Backend Routes\n\n| Code | Method | Path | Owner F### |\n"
        "|------|--------|------|------------|\n| ROUTE001 | POST | /login | F001_Auth |\n",
        encoding="utf-8",
    )
    _commit_all(tmp_path)

    exit_code = cli.main(["--docs-root", str(docs_root), "--project-root", str(tmp_path)])
    assert exit_code == 0
    assert (feature_dir / "functional-spec.md").is_file()
    assert (feature_dir / "technical-spec.md").is_file()

    spec_result = vfs.validate(plan_dir=docs_root, root=tmp_path, single=None, docs_root=docs_root)
    spec_critical = [i for entry in spec_result["specs"].values() for i in entry["issues"]
                     if i["severity"] == "critical"]
    assert not spec_critical, spec_critical

    screen_link_result = vfsl.validate(docs_root)
    assert screen_link_result["status"] == "PASS", screen_link_result["issues"]

    api_link_result = vfal.validate(docs_root)
    assert api_link_result["status"] == "PASS", api_link_result["issues"]


# --------------------------------------------------------------------------- #
# PASS B -- Integration (B): Mode B fold retains every pre-fold BL### code
# --------------------------------------------------------------------------- #
def test_integration_mode_b_fold_retains_bl_codes(tmp_path):
    _init_git_repo(tmp_path)
    docs_root = tmp_path / "docs"
    (docs_root / "system").mkdir(parents=True)
    (docs_root / "generated").mkdir(parents=True)
    (docs_root / "system" / "business-rules.md").write_text(
        _fm("authored_by: rebuild-spec") + (
            "# Business Rules\n\n### Password Complexity\n"
            "**Applies when:** a user sets or changes their password\n"
            "**Says:** the system requires at least 8 characters\n"
            "**Source artifact:** [architecture.md](../../docs/system/architecture.md)\n"
        ),
        encoding="utf-8",
    )
    bl_text = (
        "## Behavior Logic Index\n\ntable\n\n## Dev Appendix\n\n### Cardinality Contract\n\n"
        "rules\n\n## BL001: SendWelcomeMail\n\n**Type**: mail\n"
        "**Source File**: app/Mail/WelcomeMail.php\n**Source Symbol**: WelcomeMail\n\n"
        "## BL002: AuditLog\n\n**Type**: observer\n"
        "**Source File**: app/Observers/AuditObserver.php\n"
        "**Source Symbol**: AuditObserver::created\n"
    )
    (docs_root / "generated" / "behavior-logic.md").write_text(bl_text, encoding="utf-8")
    _commit_all(tmp_path)

    pre_codes = mode_b_lib.bl_codes(bl_text)
    outcome = orchestrate_bc_lib.migrate_business_rules(docs_root, tmp_path)
    assert outcome.exit_ok, outcome.message
    assert outcome.action == "migrated"

    post_text = (docs_root / "generated" / "behavior-logic.md").read_text(encoding="utf-8")
    post_codes = mode_b_lib.bl_codes(post_text)
    assert pre_codes == {"BL001", "BL002"}
    assert pre_codes == post_codes  # every pre-fold BL### code survives the fold
    assert "## Business Rules (folded from business-rules.md)" in post_text


# --------------------------------------------------------------------------- #
# PASS B -- Integration (C): Mode C reorder passes the reading-guide validator,
# drops '## Screen Layout' entirely, and resolves both new Phase 02 rule_ids
# --------------------------------------------------------------------------- #
_OLD_SCREEN_SPEC = """---
authored_by: rebuild-spec
---
# SCR001_Login — Screen Spec

**Screen**: SCR001: Login
**Feature**: F001_Auth
**Type**: atomic
**Route**: /login
**Generated**: 2026-01-01

## Purpose

Lets a user sign in.

## Screen Layout

The screen has a header and a centered form (login.vue:1).

### Layout Sketch

```
box
```

### Layout Regions

| Region ID | Name | Position | Scrollable | Key Components | Responsive Behavior |
|-----------|------|----------|------------|----------------|---------------------|
| R1 | Header | fixed-top | no | Header | always |

## User Flow

### Happy Path

1. User submits the form.

## Data Inventory

N/A — screen displays no dynamic data (static marketing/error page)

## UI States

N/A — no async ops

## Validation & Error Feedback

N/A

## Interaction Patterns

N/A

## Accessibility

N/A

## Conditional Rendering

N/A

## Component Variants

N/A

## Security Surface

N/A

## Source References

1. Page/View: `login.vue:1`

## Source Walkthrough

1. **File:** `login.vue:1` — start here

### Call Hierarchy

```text
Login -> Form -> Store
```
"""


def test_integration_mode_c_reorder_passes_reading_guide_validator(tmp_path):
    _init_git_repo(tmp_path)
    docs_root = tmp_path / "docs"
    screen_dir = docs_root / "screens" / "SCR001_Login"
    screen_dir.mkdir(parents=True)
    (screen_dir / "spec.md").write_text(_OLD_SCREEN_SPEC, encoding="utf-8")
    _commit_all(tmp_path)

    outcome = orchestrate_bc_lib.migrate_screen(screen_dir, tmp_path, docs_root)
    assert outcome.exit_ok, outcome.message
    assert outcome.action == "migrated"

    new_text = (screen_dir / "spec.md").read_text(encoding="utf-8")
    assert new_text.count("## Screen Layout") == 0
    assert mode_c_lib.resolve_layout_rule_ids(new_text) == []

    issues = vrg.check_source_walkthrough(new_text, str(screen_dir / "spec.md"))
    assert not any(i["severity"] == "critical" for i in issues), issues


# --------------------------------------------------------------------------- #
# PASS B -- LLM structural + semantic invariant gate (H-FM4)
# --------------------------------------------------------------------------- #
def test_llm_invariant_passes_on_faithful_compaction():
    pre = (
        "## 1. Overview\n\nA fee of $10,000 applies if the balance exceeds the limit. "
        "(BR-001)\n\n## 8. Edge Cases\n\n| Scenario | What Happens | User-Facing Message |\n"
        "|---|---|---|\n| a | b | c |\n| d | e | f |\n"
    )
    post = (
        "## 1. Overview\n\nA $10,000 fee applies once the balance exceeds the limit. "
        "(BR-001)\n\n## 8. Edge Cases\n\n| Scenario | What Happens | User-Facing Message |\n"
        "|---|---|---|\n| a | b | c |\n| d | e | f |\n"
    )
    result = invariant_lib.check_invariants(pre, post)
    assert result.ok, result.violations


def test_llm_invariant_fails_when_h2_or_code_dropped():
    pre = "## 1. Overview\n\ntext (BR-001)\n\n## 2. Open Decisions\n\nNone.\n"
    post = "## 1. Overview\n\ntext\n"
    result = invariant_lib.check_invariants(pre, post)
    assert not result.ok
    assert any("H2" in v for v in result.violations)
    assert any("code set" in v for v in result.violations)


def test_llm_invariant_fails_when_slug_suffixed_scr_code_dropped():
    """H1: a trailing `\\b` never matches a slug-suffixed code like `SCR001_Login`
    because `_` is a word character (no boundary between "1" and "_") -- the same bug
    already fixed at validate_feature_spec.py:67 (`_TECH_CODE_RE`) and :492 (the SCR
    cell match), re-typed here for a third time. No prior test in this file used a
    slug-suffixed SCR reference; every existing "code dropped" test only exercises the
    paren-terminated BR-family form, which is why this gap stayed green."""
    pre = (
        "## 5. Screens\n\nThis flow references SCR001_Login for navigation and "
        "SCR002_Search as fallback.\n"
    )
    post = "## 5. Screens\n\nThis flow references SCR002_Search as fallback.\n"
    result = invariant_lib.check_invariants(pre, post)
    assert not result.ok
    assert any("SCR001" in v for v in result.violations), result.violations


def test_llm_invariant_fails_when_edge_case_rows_decrease():
    pre = (
        "## 8. Edge Cases\n\n| Scenario | What Happens | User-Facing Message |\n"
        "|---|---|---|\n| a | b | c |\n| d | e | f |\n| g | h | i |\n"
    )
    post = (
        "## 8. Edge Cases\n\n| Scenario | What Happens | User-Facing Message |\n"
        "|---|---|---|\n| a | b | c |\n"
    )
    result = invariant_lib.check_invariants(pre, post)
    assert not result.ok
    assert any("edge-case row count decreased" in v for v in result.violations)


def test_llm_invariant_fails_when_dollar_threshold_silently_dropped():
    """H-FM4's named fixture: structure (code, heading) survives; the $10,000
    threshold does not. Must FAIL, with a real distinguishable violation."""
    pre = (
        "## 4. Business Rules\n\nA fee of $10,000 applies if the balance exceeds the "
        "limit and the account is overdue. (BR-001)\n"
    )
    post = (
        "## 4. Business Rules\n\nA fee applies if the account is overdue. (BR-001)\n"
    )
    result = invariant_lib.check_invariants(pre, post)
    assert not result.ok
    assert any("$10,000" in v for v in result.violations), result.violations


# --------------------------------------------------------------------------- #
# PASS B -- Requirement 5 sample-size arithmetic (>=10% of features, minimum 3)
# --------------------------------------------------------------------------- #
def test_required_sample_size_minimum_and_ratio():
    assert review_gate_lib.required_sample_size(0) == 0
    assert review_gate_lib.required_sample_size(5) == 3   # ceil(0.5)=1, floored by minimum 3
    assert review_gate_lib.required_sample_size(50) == 5  # ceil(5.0)=5, exceeds minimum


def test_sample_meets_threshold_insufficient_vs_sufficient():
    eligible = {f"F{i:03d}_X" for i in range(1, 5)}  # 4 features -> requires 3
    ok, reason = review_gate_lib.sample_meets_threshold({"F001_X"}, eligible)
    assert ok is False
    assert "F001_X" not in reason or "1 of 4" in reason
    ok, reason = review_gate_lib.sample_meets_threshold(
        {"F001_X", "F002_X", "F003_X"}, eligible,
    )
    assert ok is True


def test_reviewed_gate_insufficient_sample_treated_as_absent_for_whole_run(tmp_path):
    docs_root = tmp_path / "docs"
    dirs = []
    for i in range(1, 5):
        fd = docs_root / "features" / f"F00{i}_Feat{i}"
        _write_v26_feature(fd)
        dirs.append(fd)
    reviewed = {"F001_Feat1"}  # 1 of 4 -- below max(3, ceil(0.4))=3
    gate = cli._resolve_reviewed_gate(dirs, reviewed)
    assert gate is None


def test_reviewed_gate_sufficient_sample_is_honored(tmp_path):
    docs_root = tmp_path / "docs"
    dirs = []
    for i in range(1, 5):
        fd = docs_root / "features" / f"F00{i}_Feat{i}"
        _write_v26_feature(fd)
        dirs.append(fd)
    reviewed = {"F001_Feat1", "F002_Feat2", "F003_Feat3"}  # 3 of 4 -- meets the threshold
    gate = cli._resolve_reviewed_gate(dirs, reviewed)
    assert gate == reviewed
