"""Tests for SHAPE_V27_HYBRID -- the resumable "already composed, satellites retained"
migration state (adversarial-review HIGH fix: the default run's own documented output
had no automatic recovery path if the per-feature sentinel under docs/.migrate-v27/ was
ever lost). See claude/skills/rebuild-spec/references/migration-audience-split.md,
"SHAPE_V27_HYBRID -- the resumable common case", for the full design record.

This file covers, in order:

  - detect_shape() recognizes func+tech+ALL THREE v26 satellites as SHAPE_V27_HYBRID,
    without widening SHAPE_UNKNOWN's genuine-corruption catch -- a partial one-satellite
    leftover (the scenario test_migrate_feature_audience_split.py's
    test_i6_refuse_unknown_partially_restructured already covers) must stay
    SHAPE_UNKNOWN, unchanged by this fix.
  - detect_shape() does not shadow the two shapes SHAPE_V27_HYBRID sits between.
  - migrate_feature() validates-and-seals a hybrid dir WITHOUT ever calling compose_fn --
    the anti-re-composition guarantee that is the actual point of this fix (re-deriving
    functional-spec.md from the still-present satellites risks overwriting reviewed
    edits).
  - A hybrid dir that fails validation refuses (FAILED), never guesses.
  - A hybrid dir recognized this way is STILL eligible for --reviewed satellite deletion.
  - A small-scale reproduction of the orchestrator-measured failure: migrate, delete
    docs/.migrate-v27/ entirely, re-run -- every hybrid unit must resolve ALREADY with
    zero FAILED, exit 0, and byte-identical functional-spec.md content.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import _audience_split_migrate_lib as mig_lib  # noqa: E402
import _audience_split_shape_lib as shape_lib  # noqa: E402
import migrate_feature_audience_split as cli  # noqa: E402

FIXTURES = _TESTS_DIR / "fixtures" / "migrate_feature_audience_split" / "valid-content"
VALID_FUNC = (FIXTURES / "functional-spec.md").read_text(encoding="utf-8")
VALID_TECH = (FIXTURES / "technical-spec.md").read_text(encoding="utf-8")

V26_SATELLITES = ("business-context.md", "screens.md", "edge-cases.md")


def _write_hybrid_feature(feature_dir: Path, *, valid: bool = True) -> None:
    """func + tech + all 3 retained v26 satellites -- the documented common-case output
    of a default (no --reviewed) migration run. `valid=True` uses the known-good v27
    pair (passes validate_feature_spec.py); `valid=False` writes content the validator
    rejects, to exercise the refuse path."""
    feature_dir.mkdir(parents=True, exist_ok=True)
    if valid:
        (feature_dir / "functional-spec.md").write_text(VALID_FUNC, encoding="utf-8")
        (feature_dir / "technical-spec.md").write_text(VALID_TECH, encoding="utf-8")
    else:
        (feature_dir / "functional-spec.md").write_text(
            "# F001_Auth\n\nnot a real functional spec.\n", encoding="utf-8",
        )
        (feature_dir / "technical-spec.md").write_text(
            "# F001_Auth\n\nnot a real technical spec.\n", encoding="utf-8",
        )
    for name in V26_SATELLITES:
        (feature_dir / name).write_text(f"# {name}\n\nretained v26 satellite.\n", encoding="utf-8")


# --------------------------------------------------------------------------- #
# Shape detection
# --------------------------------------------------------------------------- #
def test_shape_detects_v27_hybrid_with_all_three_satellites(tmp_path):
    _write_hybrid_feature(tmp_path)
    assert shape_lib.detect_shape(tmp_path) == shape_lib.SHAPE_V27_HYBRID


def test_shape_partial_satellite_leftover_stays_unknown_not_hybrid(tmp_path):
    """Non-widening guard: func+tech+ONE satellite is a genuinely ambiguous
    hand-restructure mix, not the documented hybrid state -- must remain SHAPE_UNKNOWN,
    exactly as before this fix (mirrors
    test_migrate_feature_audience_split.py::test_i6_refuse_unknown_partially_restructured,
    which this fix must not break)."""
    (tmp_path / "functional-spec.md").write_text(VALID_FUNC, encoding="utf-8")
    (tmp_path / "technical-spec.md").write_text(VALID_TECH, encoding="utf-8")
    (tmp_path / "screens.md").write_text("# Screens\n\nleftover.\n", encoding="utf-8")
    assert shape_lib.detect_shape(tmp_path) == shape_lib.SHAPE_UNKNOWN


def test_shape_hybrid_does_not_shadow_pure_v26_or_v27(tmp_path):
    """Regression guard: the new branch must not fire for the two shapes it sits
    between -- SHAPE_V26 (no functional-spec.md yet) and SHAPE_V27 (zero satellites)."""
    v26_dir = tmp_path / "v26"
    v26_dir.mkdir()
    (v26_dir / "technical-spec.md").write_text("# t\n", encoding="utf-8")
    for name in V26_SATELLITES:
        (v26_dir / name).write_text(f"# {name}\n", encoding="utf-8")
    assert shape_lib.detect_shape(v26_dir) == shape_lib.SHAPE_V26

    v27_dir = tmp_path / "v27"
    v27_dir.mkdir()
    (v27_dir / "functional-spec.md").write_text(VALID_FUNC, encoding="utf-8")
    (v27_dir / "technical-spec.md").write_text(VALID_TECH, encoding="utf-8")
    assert shape_lib.detect_shape(v27_dir) == shape_lib.SHAPE_V27


# --------------------------------------------------------------------------- #
# migrate_feature() -- validate-and-seal, NEVER re-compose
# --------------------------------------------------------------------------- #
def test_migrate_feature_hybrid_never_calls_compose_fn(tmp_path):
    """The anti-re-composition guarantee: re-deriving functional-spec.md from the
    still-present satellites would risk overwriting reviewed edits -- the actual
    data-loss risk this fix exists to close. compose_fn must be UNREACHABLE for this
    shape."""
    docs_root = tmp_path / "docs"
    feature_dir = docs_root / "features" / "F001_Auth"
    _write_hybrid_feature(feature_dir)

    def _boom(_feature_dir):
        raise AssertionError("compose_fn must never be called for SHAPE_V27_HYBRID")

    outcome = cli.migrate_feature(
        feature_dir, project_root=tmp_path, docs_root=docs_root, compose_fn=_boom,
    )
    assert outcome.action == "confirmed-v27"
    assert outcome.exit_ok is True


def test_migrate_feature_hybrid_valid_confirms_and_seals(tmp_path):
    docs_root = tmp_path / "docs"
    feature_dir = docs_root / "features" / "F001_Auth"
    _write_hybrid_feature(feature_dir)
    func_before = (feature_dir / "functional-spec.md").read_text(encoding="utf-8")
    tech_before = (feature_dir / "technical-spec.md").read_text(encoding="utf-8")

    outcome = cli.migrate_feature(feature_dir, project_root=tmp_path, docs_root=docs_root)

    assert outcome.action == "confirmed-v27"
    assert outcome.exit_ok is True
    assert mig_lib.has_feature_sentinel(mig_lib.staging_feature_dir(docs_root, "F001_Auth"))
    # Anti-re-composition proof: byte-identical, nothing was re-derived.
    assert (feature_dir / "functional-spec.md").read_text(encoding="utf-8") == func_before
    assert (feature_dir / "technical-spec.md").read_text(encoding="utf-8") == tech_before
    # Satellites retained -- no --reviewed authorization was given.
    for name in V26_SATELLITES:
        assert (feature_dir / name).is_file()


def test_migrate_feature_hybrid_invalid_content_refuses(tmp_path):
    docs_root = tmp_path / "docs"
    feature_dir = docs_root / "features" / "F001_Auth"
    _write_hybrid_feature(feature_dir, valid=False)

    outcome = cli.migrate_feature(feature_dir, project_root=tmp_path, docs_root=docs_root)

    assert outcome.action == "refused-invalid-v27"
    assert outcome.exit_ok is False
    assert not mig_lib.has_feature_sentinel(mig_lib.staging_feature_dir(docs_root, "F001_Auth"))
    # Originals untouched -- never guessed, never swapped, never deleted.
    for name in V26_SATELLITES:
        assert (feature_dir / name).is_file()


def test_migrate_feature_hybrid_reviewed_deletes_satellites(tmp_path):
    docs_root = tmp_path / "docs"
    feature_dir = docs_root / "features" / "F001_Auth"
    _write_hybrid_feature(feature_dir)
    func_before = (feature_dir / "functional-spec.md").read_text(encoding="utf-8")

    outcome = cli.migrate_feature(
        feature_dir, project_root=tmp_path, docs_root=docs_root, reviewed={"F001_Auth"},
    )

    assert outcome.action == "migrated"
    assert outcome.exit_ok is True
    assert (feature_dir / "functional-spec.md").read_text(encoding="utf-8") == func_before
    for name in V26_SATELLITES:
        assert not (feature_dir / name).is_file()


def test_migrate_feature_hybrid_not_in_reviewed_retains_satellites(tmp_path):
    docs_root = tmp_path / "docs"
    feature_dir = docs_root / "features" / "F001_Auth"
    _write_hybrid_feature(feature_dir)

    outcome = cli.migrate_feature(
        feature_dir, project_root=tmp_path, docs_root=docs_root, reviewed={"F999_Other"},
    )

    assert outcome.action == "confirmed-v27"
    for name in V26_SATELLITES:
        assert (feature_dir / name).is_file()


# --------------------------------------------------------------------------- #
# Small-scale reproduction of the orchestrator-measured delete-sentinel scenario
# --------------------------------------------------------------------------- #
def test_cli_recovers_all_hybrid_units_after_staging_deleted(tmp_path):
    """Reproduces the orchestrator-measured failure at small scale: migrate a corpus,
    delete docs/.migrate-v27/ entirely (simulating the dot-directory being lost), then
    re-run. BEFORE this fix every hybrid unit refused (SHAPE_UNKNOWN, exit 1). AFTER,
    every one resolves ALREADY, FAILED stays 0, the run seals with exit 0, and the
    functional-spec.md content is provably untouched -- proof nothing was re-composed."""
    docs_root = tmp_path / "docs"
    slugs = [f"F00{i}_Feat{i}" for i in range(1, 4)]
    for slug in slugs:
        _write_hybrid_feature(docs_root / "features" / slug)
    func_before = {
        slug: (docs_root / "features" / slug / "functional-spec.md").read_text(encoding="utf-8")
        for slug in slugs
    }

    first_exit = cli.main(["--docs-root", str(docs_root), "--project-root", str(tmp_path)])
    assert first_exit == 0
    assert mig_lib.has_run_sentinel(docs_root)

    # Simulate the dot-directory loss: wipe docs/.migrate-v27/ entirely, including both
    # the run sentinel and every per-feature sentinel underneath it.
    shutil.rmtree(mig_lib.staging_root(docs_root))
    assert not mig_lib.has_run_sentinel(docs_root)

    second_exit = cli.main(["--docs-root", str(docs_root), "--project-root", str(tmp_path)])
    assert second_exit == 0
    assert mig_lib.has_run_sentinel(docs_root)
    for slug in slugs:
        feature_dir = docs_root / "features" / slug
        for name in V26_SATELLITES:
            assert (feature_dir / name).is_file(), f"{slug}: satellite {name} must be retained"
        assert (feature_dir / "functional-spec.md").read_text(encoding="utf-8") == func_before[slug]
