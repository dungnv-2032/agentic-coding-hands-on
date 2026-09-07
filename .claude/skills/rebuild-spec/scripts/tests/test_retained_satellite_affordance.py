"""Tests for phase-05 (plans/260818-0758-rebuild-spec-post-migration-completion/
phase-05-retained-satellite-affordance.md): the retained-satellite reporting
affordance -- `Tally.retained`, `summary_line()`'s `retained=N` term, `to_dict`/
`from_dict` round-trip, `count_retained_satellite_dirs` (artifact-derived, never a
tally lookup), and `action_required_block` (the `[ACTION REQUIRED]` next-step
message). The delete gate itself (`_audience_split_review_gate_lib.py`) is untouched
by this phase -- these tests only prove the new reporting is correct and truthful.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import _audience_split_tally_lib as tally_lib  # noqa: E402
import migrate_feature_audience_split as cli  # noqa: E402

FIXTURES = _TESTS_DIR / "fixtures" / "migrate_feature_audience_split" / "valid-content"
VALID_FUNC = (FIXTURES / "functional-spec.md").read_text(encoding="utf-8")
VALID_TECH = (FIXTURES / "technical-spec.md").read_text(encoding="utf-8")

V26_SATELLITES = ("business-context.md", "screens.md", "edge-cases.md")


# --------------------------------------------------------------------------- #
# Shared fixture helpers (self-contained -- mirrors test_audience_split_run_
# contract.py's helpers of the same name/shape without importing that test module).
# --------------------------------------------------------------------------- #
def _init_git_repo(d: Path) -> None:
    subprocess.run(["git", "init", str(d)], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(d), "config", "user.email", "test@test.com"],
                    capture_output=True, check=True)
    subprocess.run(["git", "-C", str(d), "config", "user.name", "Test"],
                    capture_output=True, check=True)


def _commit_all(d: Path, message: str = "commit") -> None:
    subprocess.run(["git", "-C", str(d), "add", "-A"], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(d), "commit", "-q", "-m", message],
                    capture_output=True, check=False)


def _write_v26_feature_clean(feature_dir: Path) -> None:
    """CLEAN provenance (authored_by: rebuild-spec on every file) -- probes CLEAN, so
    Mode A proceeds to compose."""
    feature_dir.mkdir(parents=True, exist_ok=True)
    fm = "---\nauthored_by: rebuild-spec\n---\n"
    (feature_dir / "technical-spec.md").write_text(
        fm + "# F_Auth\n\n## Overview\n\nOld v26 technical spec placeholder.\n", encoding="utf-8",
    )
    for name, title in (("business-context.md", "Business Context"),
                        ("screens.md", "Screens"), ("edge-cases.md", "Edge Cases")):
        (feature_dir / name).write_text(fm + f"# {title}\n\nPlaceholder.\n", encoding="utf-8")


def _run(docs_root: Path, project_root: Path, **extra) -> int:
    argv = ["--docs-root", str(docs_root), "--project-root", str(project_root)]
    for k, v in extra.items():
        argv.append(f"--{k.replace('_', '-')}")
        if v is not True:
            argv.append(str(v))
    return cli.main(argv)


def _always_compose(_fd):
    """Monkeypatch target for `compose_mode_a` -- the VALID_FUNC/VALID_TECH fixture
    pair is a background feature with no screen/route cross-refs (§5 "N/A"), so it
    validates clean without needing `docs/generated/*` registration, exactly like
    test_audience_split_run_contract.py's test_t6 uses it."""
    return {"functional-spec.md": VALID_FUNC, "technical-spec.md": VALID_TECH}


# --------------------------------------------------------------------------- #
# Unit -- Tally.retained (Requirements 1/2/4)
# --------------------------------------------------------------------------- #
def test_add_migrated_originals_retained_increments_progress_and_retained():
    tally = tally_lib.Tally()
    category = tally.add("migrated-originals-retained")
    assert category == tally_lib.PROGRESS
    assert tally.progress == 1
    assert tally.retained == 1


def test_add_other_progress_action_does_not_touch_retained():
    tally = tally_lib.Tally()
    tally.add("migrated")
    assert tally.progress == 1
    assert tally.retained == 0


def test_summary_line_carries_retained_term():
    tally = tally_lib.Tally()
    tally.add("migrated-originals-retained")
    line = tally.summary_line(sentinel_state="WRITTEN")
    assert "retained=1" in line
    # existing keys/order the doc-migration step's _SUMMARY_RE depends on must survive
    assert "[SUMMARY] units=1 progress=1 already=0 inert=0 failed=0" in line


def test_to_dict_from_dict_round_trip_preserves_retained():
    tally = tally_lib.Tally()
    for _ in range(3):
        tally.add("migrated-originals-retained")
    restored = tally_lib.Tally.from_dict(tally.to_dict())
    assert restored.retained == 3
    assert restored.progress == tally.progress


def test_from_dict_missing_key_defaults_to_zero_no_raise():
    """An old sentinel written before `retained` existed must restore cleanly."""
    restored = tally_lib.Tally.from_dict({})
    assert restored.retained == 0
    assert restored.units == 0


# --------------------------------------------------------------------------- #
# Unit -- action_required_block (Requirement 3)
# --------------------------------------------------------------------------- #
def test_action_required_block_none_when_retained_zero():
    block = tally_lib.action_required_block(
        0, script_path=Path("script.py"), docs_root=Path("/docs"), project_root=Path("/repo"),
    )
    assert block is None


def test_action_required_block_names_sample_size_and_reviewed_command():
    block = tally_lib.action_required_block(
        66, script_path=Path("/repo/scripts/migrate_feature_audience_split.py"),
        docs_root=Path("/repo/docs"), project_root=Path("/repo"),
    )
    assert block is not None
    assert "[ACTION REQUIRED]" in block
    assert "66 feature dir(s)" in block
    assert "least 7" in block  # required_sample_size(66) == max(3, ceil(6.6)) == 7
    assert "--reviewed" in block
    assert "/repo/scripts/migrate_feature_audience_split.py" in block
    assert "--docs-root /repo/docs" in block
    assert "--project-root /repo" in block


def test_action_required_block_never_emits_a_prefilled_manifest():
    """Non-goal (phase-00/phase-05): the block names the command, never an actual slug
    list a hand could pass straight back to --reviewed -- structurally guaranteed here
    since the function takes only a count, never the candidate slugs themselves."""
    block = tally_lib.action_required_block(
        7, script_path=Path("script.py"), docs_root=Path("/d"), project_root=Path("/p"),
    )
    assert "F001" not in block  # no concrete feature slug is ever named


# --------------------------------------------------------------------------- #
# Unit -- count_retained_satellite_dirs (artifact-derived, never a tally lookup)
# --------------------------------------------------------------------------- #
def test_count_retained_satellite_dirs_counts_only_dirs_holding_a_satellite(tmp_path):
    holds = tmp_path / "F001_Holds"
    holds.mkdir()
    (holds / "business-context.md").write_text("x", encoding="utf-8")

    clean = tmp_path / "F002_Clean"
    clean.mkdir()
    (clean / "functional-spec.md").write_text("x", encoding="utf-8")

    assert tally_lib.count_retained_satellite_dirs([holds, clean]) == 1


def test_count_retained_satellite_dirs_ignores_tally_entirely(tmp_path):
    """The count must come from disk, not from any Tally state -- a dir can hold
    satellites for a reason this run's tally never recorded at all (e.g. the
    SHAPE_V27_HYBRID confirm-and-seal branch, which reports 'confirmed-v27' / ALREADY,
    never 'migrated-originals-retained')."""
    fd = tmp_path / "F001_Hybrid"
    fd.mkdir()
    for name in V26_SATELLITES:
        (fd / name).write_text("x", encoding="utf-8")
    (fd / "functional-spec.md").write_text("x", encoding="utf-8")
    (fd / "technical-spec.md").write_text("x", encoding="utf-8")

    empty_tally = tally_lib.Tally()  # never touched -- proves independence
    assert empty_tally.retained == 0
    assert tally_lib.count_retained_satellite_dirs([fd]) == 1


def test_count_retained_satellite_dirs_zero_once_satellites_removed(tmp_path):
    fd = tmp_path / "F001_Clean"
    fd.mkdir()
    (fd / "functional-spec.md").write_text("x", encoding="utf-8")
    (fd / "technical-spec.md").write_text("x", encoding="utf-8")
    assert tally_lib.count_retained_satellite_dirs([fd]) == 0


# --------------------------------------------------------------------------- #
# Integration -- live CLI run without --reviewed prints [ACTION REQUIRED] with the
# real required-sample-size arithmetic, exit code and [SUMMARY] shape unchanged
# --------------------------------------------------------------------------- #
def test_live_run_without_reviewed_prints_action_required(tmp_path, capsys, monkeypatch):
    _init_git_repo(tmp_path)
    docs_root = tmp_path / "docs"
    n = 5
    for i in range(1, n + 1):
        _write_v26_feature_clean(docs_root / "features" / f"F{i:03d}_Feature{i}")
    _commit_all(tmp_path)
    monkeypatch.setattr(cli, "compose_mode_a", _always_compose)

    exit_code = _run(docs_root, tmp_path)
    out = capsys.readouterr().out

    assert exit_code == 0  # retained satellites are a designed outcome, not a failure
    assert "[SUMMARY]" in out
    assert f"retained={n}" in out
    assert "[ACTION REQUIRED]" in out
    assert f"{n} feature dir(s)" in out
    assert "least 3" in out  # required_sample_size(5) == max(3, ceil(0.5)) == 3
    assert "--reviewed" in out
    assert str(docs_root) in out
    assert str(tmp_path) in out
    for i in range(1, n + 1):
        feature_dir = docs_root / "features" / f"F{i:03d}_Feature{i}"
        for name in V26_SATELLITES:
            assert (feature_dir / name).is_file()  # nothing deleted


def test_action_required_disappears_once_reviewed_manifest_clears_satellites(
    tmp_path, capsys, monkeypatch,
):
    _init_git_repo(tmp_path)
    docs_root = tmp_path / "docs"
    n = 3
    slugs = [f"F{i:03d}_Feature{i}" for i in range(1, n + 1)]
    for slug in slugs:
        _write_v26_feature_clean(docs_root / "features" / slug)
    _commit_all(tmp_path)
    monkeypatch.setattr(cli, "compose_mode_a", _always_compose)

    manifest = tmp_path / "reviewed.txt"
    manifest.write_text("\n".join(slugs) + "\n", encoding="utf-8")

    exit_code = _run(docs_root, tmp_path, reviewed=manifest)
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "retained=0" in out
    assert "[ACTION REQUIRED]" not in out
    for slug in slugs:
        for name in V26_SATELLITES:
            assert not (docs_root / "features" / slug / name).exists()


# --------------------------------------------------------------------------- #
# Integration -- second invocation honoring the run sentinel still prints the
# block, with the artifact-derived count, not a cached zero
# --------------------------------------------------------------------------- #
def test_second_run_honoring_sentinel_still_prints_action_required(
    tmp_path, capsys, monkeypatch,
):
    _init_git_repo(tmp_path)
    docs_root = tmp_path / "docs"
    n = 4
    for i in range(1, n + 1):
        _write_v26_feature_clean(docs_root / "features" / f"F{i:03d}_Feature{i}")
    _commit_all(tmp_path)
    monkeypatch.setattr(cli, "compose_mode_a", _always_compose)

    first = _run(docs_root, tmp_path)
    assert first == 0
    capsys.readouterr()  # discard first run's output

    second = _run(docs_root, tmp_path)
    out = capsys.readouterr().out

    assert second == 0
    assert "already migrated" in out
    assert f"retained={n}" in out
    assert "[ACTION REQUIRED]" in out
    assert f"{n} feature dir(s)" in out


# --------------------------------------------------------------------------- #
# Integration -- Gate 8c: the printed --reviewed command must actually work on a
# corpus whose run sentinel (and every per-feature sentinel) is already sealed --
# exactly the real sharetribe corpus's current state. Before this fix, the run
# sentinel short-circuit in main() AND the has_feature_sentinel no-op in
# migrate_feature() both pre-empted `reviewed` forever after the first run, making
# the [ACTION REQUIRED] block's own printed command silent dead code.
# --------------------------------------------------------------------------- #
def test_reviewed_manifest_deletes_satellites_on_a_sealed_corpus_second_invocation(
    tmp_path, capsys, monkeypatch,
):
    _init_git_repo(tmp_path)
    docs_root = tmp_path / "docs"
    n = 3
    slugs = [f"F{i:03d}_Feature{i}" for i in range(1, n + 1)]
    for slug in slugs:
        _write_v26_feature_clean(docs_root / "features" / slug)
    _commit_all(tmp_path)
    monkeypatch.setattr(cli, "compose_mode_a", _always_compose)

    first = _run(docs_root, tmp_path)  # no --reviewed -- the documented default run
    assert first == 0
    capsys.readouterr()
    for slug in slugs:
        for name in V26_SATELLITES:
            assert (docs_root / "features" / slug / name).is_file()

    manifest = tmp_path / "reviewed.txt"
    manifest.write_text("\n".join(slugs) + "\n", encoding="utf-8")

    second = _run(docs_root, tmp_path, reviewed=manifest)  # the printed follow-up
    out = capsys.readouterr().out

    assert second == 0
    assert "retained=0" in out
    for slug in slugs:
        for name in V26_SATELLITES:
            assert not (docs_root / "features" / slug / name).exists()


def test_reviewed_manifest_not_naming_a_slug_leaves_its_satellites_retained(
    tmp_path, capsys, monkeypatch,
):
    """Gate 8c only authorizes a delete for a slug the manifest actually names --
    every other already-sealed feature keeps its fast no-op path untouched.

    FIXTURE SIZE IS LOAD-BEARING (changed after review): this originally used 3 features
    with a 1-slug manifest, which only passed because `resolve_reviewed_gate` computed
    eligibility as `detect_shape(fd) == SHAPE_V26` -- the empty set on a retry, so the
    sample gate was vacuous and honored ANY manifest. This test was therefore asserting
    the bug. Eligibility is now "still holds a retained satellite", so 30 features means
    the >=10% bar is 3: the manifest names exactly 3 and 27 remain to prove the real
    property (only named slugs are deleted) WITHOUT leaning on a bypassed gate."""
    _init_git_repo(tmp_path)
    docs_root = tmp_path / "docs"
    slugs = [f"F{i:03d}_Feature{i}" for i in range(1, 31)]
    for slug in slugs:
        _write_v26_feature_clean(docs_root / "features" / slug)
    _commit_all(tmp_path)
    monkeypatch.setattr(cli, "compose_mode_a", _always_compose)

    assert _run(docs_root, tmp_path) == 0
    capsys.readouterr()

    named, unnamed = slugs[:3], slugs[3:]
    manifest = tmp_path / "reviewed.txt"
    manifest.write_text("\n".join(named) + "\n", encoding="utf-8")

    assert _run(docs_root, tmp_path, reviewed=manifest) == 0
    for name in V26_SATELLITES:
        for slug in named:
            assert not (docs_root / "features" / slug / name).exists()
        for slug in unnamed:
            assert (docs_root / "features" / slug / name).is_file()
