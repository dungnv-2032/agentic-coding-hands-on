"""Tests for phase-06 (B2/B3/B5): the migration run contract -- the outcome tally
(`_audience_split_tally_lib.py`), the JSON run sentinel + poisoned-sentinel self-heal
(`_audience_split_migrate_lib.write_run_sentinel` / `read_run_sentinel`), the new exit
code 4, the always-printed `[SUMMARY]` line, and B5's cross-repo `--project-root`
default + language-mirror refusal guard.

B2, exactly: the OLD `_run_migration` computed `all_ok` from `outcome.exit_ok`, and
`skipped-hand-edited` carries `exit_ok=True` -- so a 100%-skipped run looked fully
successful and sealed the run sentinel over an UNMIGRATED corpus, permanently locking
the next invocation out (`has_run_sentinel` short-circuited to "already migrated").
Every test below either reproduces that shape and proves it no longer seals (T1-T3,
T6), or proves genuine idempotency still holds when the corpus really did migrate
(T4-T5, T9), or proves the sentinel format's own escape hatch (T7-T8).
"""
from __future__ import annotations

import fcntl
import json
import subprocess
import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import _audience_split_migrate_lib as mig_lib  # noqa: E402
import _audience_split_tally_lib as tally_lib  # noqa: E402
import migrate_feature_audience_split as cli  # noqa: E402

FIXTURES = _TESTS_DIR / "fixtures" / "migrate_feature_audience_split" / "valid-content"
VALID_FUNC = (FIXTURES / "functional-spec.md").read_text(encoding="utf-8")
VALID_TECH = (FIXTURES / "technical-spec.md").read_text(encoding="utf-8")

V26_FIXTURES = _TESTS_DIR / "fixtures" / "migrate_feature_audience_split" / "v26-valid-content"
_V26_FILES = ("business-context.md", "screens.md", "edge-cases.md", "technical-spec.md")


# --------------------------------------------------------------------------- #
# Shared fixture helpers (this file is self-contained -- see
# test_migrate_feature_audience_split.py for the sibling pass A/B suite).
# --------------------------------------------------------------------------- #
def _init_git_repo(d: Path) -> None:
    subprocess.run(["git", "init", str(d)], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(d), "config", "user.email", "test@test.com"],
                    capture_output=True, check=True)
    subprocess.run(["git", "-C", str(d), "config", "user.name", "Test"],
                    capture_output=True, check=True)


def _commit_all(d: Path, message: str = "commit") -> None:
    """Best-effort: some fixtures set up an otherwise-empty tree (e.g. a bare
    `features/` dir with no files) where git legitimately has nothing to commit --
    that is not a setup failure, so this does not `check=True` the commit step."""
    subprocess.run(["git", "-C", str(d), "add", "-A"], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(d), "commit", "-q", "-m", message], capture_output=True, check=False)


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


def _write_v26_feature_hand_edited(feature_dir: Path) -> None:
    """NO authored_by and NO legacy generator marker -- probes HAND_EDITED (fail-closed,
    phase-00 U2), matching the raw sharetribe-corpus shape B1 diagnosed."""
    feature_dir.mkdir(parents=True, exist_ok=True)
    (feature_dir / "technical-spec.md").write_text(
        "# F_HandEdited\n\n## Overview\n\nNo provenance markers at all.\n", encoding="utf-8",
    )
    for name, title in (("business-context.md", "Business Context"),
                        ("screens.md", "Screens"), ("edge-cases.md", "Edge Cases")):
        (feature_dir / name).write_text(f"# {title}\n\nNo provenance markers.\n", encoding="utf-8")


def _write_v26_real_feature(feature_dir: Path) -> None:
    """The hand-built v26-valid-content fixture (slug F001_Auth) -- satisfies every
    deterministic validator, so it migrates end to end for real, not just past shape
    detection."""
    feature_dir.mkdir(parents=True, exist_ok=True)
    for name in _V26_FILES:
        (feature_dir / name).write_text(
            (V26_FIXTURES / name).read_text(encoding="utf-8"), encoding="utf-8",
        )


def _write_generated_docs(docs_root: Path) -> None:
    """The `docs/generated/*` cross-refs `F001_Auth`'s real fixture needs to pass the
    screen-link / api-link / route validators (mirrors
    test_integration_migrate_then_validate_triple_pass in the sibling suite)."""
    generated = docs_root / "generated"
    generated.mkdir(parents=True, exist_ok=True)
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


def _run(docs_root: Path, project_root: Path, **extra) -> int:
    argv = ["--docs-root", str(docs_root), "--project-root", str(project_root)]
    for k, v in extra.items():
        argv.append(f"--{k.replace('_', '-')}")
        if v is not True:
            argv.append(str(v))
    return cli.main(argv)


# --------------------------------------------------------------------------- #
# T1/T2 -- an all-skipped run never seals the run sentinel (the B2 defect itself)
# --------------------------------------------------------------------------- #
def test_t1_all_hand_edited_units_exit_4_no_sentinel_written(tmp_path, capsys):
    _init_git_repo(tmp_path)
    docs_root = tmp_path / "docs"
    for i in (1, 2, 3):
        _write_v26_feature_hand_edited(docs_root / "features" / f"F00{i}_HandEdited{i}")
    _commit_all(tmp_path)

    exit_code = _run(docs_root, tmp_path)
    captured = capsys.readouterr()

    assert exit_code == 4
    assert not mig_lib.has_run_sentinel(docs_root), "B2: an all-skip run must NOT seal the corpus"
    assert "[SUMMARY]" in captured.out
    assert "inert=3" in captured.out
    assert "failed=0" in captured.out
    assert "run sentinel: NOT WRITTEN" in captured.out
    assert "accomplished nothing" in captured.err


def test_t2_second_invocation_after_all_skip_still_runs_same_exit_4(tmp_path, capsys):
    """The regression this phase is FOR: since no sentinel was written, a second
    invocation must not short-circuit on a false 'already migrated' -- it re-assesses
    and reaches the same honest exit 4, not exit 0."""
    _init_git_repo(tmp_path)
    docs_root = tmp_path / "docs"
    _write_v26_feature_hand_edited(docs_root / "features" / "F001_HandEdited")
    _commit_all(tmp_path)

    first = _run(docs_root, tmp_path)
    capsys.readouterr()
    second = _run(docs_root, tmp_path)
    out = capsys.readouterr().out

    assert first == 4
    assert second == 4
    assert "already migrated" not in out
    assert "inert=1" in out


# --------------------------------------------------------------------------- #
# T3 -- mixed: one migrated, one skipped -> still exit 4, sentinel NOT written
# --------------------------------------------------------------------------- #
def test_t3_mixed_migrated_and_skipped_exit_4_sentinel_not_written(tmp_path, capsys):
    _init_git_repo(tmp_path)
    docs_root = tmp_path / "docs"
    _write_v26_real_feature(docs_root / "features" / "F001_Auth")
    _write_v26_feature_hand_edited(docs_root / "features" / "F002_HandEdited")
    _write_generated_docs(docs_root)
    _commit_all(tmp_path)

    exit_code = _run(docs_root, tmp_path)
    out = capsys.readouterr().out

    assert exit_code == 4
    assert not mig_lib.has_run_sentinel(docs_root)
    assert "progress=1" in out
    assert "inert=1" in out
    assert (docs_root / "features" / "F001_Auth" / "functional-spec.md").is_file()


# --------------------------------------------------------------------------- #
# T4/T5 -- a fully-migrated corpus seals, and a real second run is a clean no-op
# --------------------------------------------------------------------------- #
def test_t4_all_migrated_exit_0_sentinel_written_json_parses(tmp_path, capsys):
    _init_git_repo(tmp_path)
    docs_root = tmp_path / "docs"
    _write_v26_real_feature(docs_root / "features" / "F001_Auth")
    _write_generated_docs(docs_root)
    _commit_all(tmp_path)

    exit_code = _run(docs_root, tmp_path)
    out = capsys.readouterr().out

    assert exit_code == 0
    assert mig_lib.has_run_sentinel(docs_root)
    data = json.loads(mig_lib.run_sentinel_path(docs_root).read_text(encoding="utf-8"))
    assert data["format_version"] == "27"
    assert data["inert"] == 0
    assert data["failed"] == 0
    assert data["progress"] >= 1
    assert "run sentinel: WRITTEN" in out


def test_t5_second_run_over_migrated_docs_is_clean_noop(tmp_path, capsys):
    _init_git_repo(tmp_path)
    docs_root = tmp_path / "docs"
    _write_v26_real_feature(docs_root / "features" / "F001_Auth")
    _write_generated_docs(docs_root)
    _commit_all(tmp_path)

    first = _run(docs_root, tmp_path)
    assert first == 0
    sentinel_mtime = mig_lib.run_sentinel_path(docs_root).stat().st_mtime
    capsys.readouterr()

    second = _run(docs_root, tmp_path)
    out = capsys.readouterr().out

    assert second == 0
    assert mig_lib.run_sentinel_path(docs_root).stat().st_mtime == sentinel_mtime
    assert "already migrated" in out
    assert "[SUMMARY]" in out


# --------------------------------------------------------------------------- #
# T6 -- FAILED outranks INERT: one failed-validation + one migrated + one hand-edited
# --------------------------------------------------------------------------- #
def test_t6_failed_validation_outranks_inert_exit_1_sentinel_not_written(tmp_path, capsys, monkeypatch):
    _init_git_repo(tmp_path)
    docs_root = tmp_path / "docs"
    good_dir = docs_root / "features" / "F001_Good"
    bad_dir = docs_root / "features" / "F002_Bad"
    hand_edited_dir = docs_root / "features" / "F003_HandEdited"
    _write_v26_feature_clean(good_dir)
    _write_v26_feature_clean(bad_dir)
    _write_v26_feature_hand_edited(hand_edited_dir)
    _commit_all(tmp_path)

    broken = {
        "functional-spec.md": "# F002_Bad\n\n## 1. Overview\n\nMissing required sections.\n",
        "technical-spec.md": VALID_TECH,
    }

    def _compose(fd):
        return broken if fd.name == "F002_Bad" else {
            "functional-spec.md": VALID_FUNC, "technical-spec.md": VALID_TECH,
        }

    monkeypatch.setattr(cli, "compose_mode_a", _compose)

    exit_code = _run(docs_root, tmp_path)
    out = capsys.readouterr().out

    assert exit_code == 1
    assert not mig_lib.has_run_sentinel(docs_root)
    assert "failed=1" in out
    assert "inert=1" in out


# --------------------------------------------------------------------------- #
# T7/T8 -- a poisoned sentinel self-heals: WARN, then re-run (no new flag)
# --------------------------------------------------------------------------- #
def test_t7_legacy_plaintext_sentinel_is_poisoned_and_reruns(tmp_path, capsys):
    _init_git_repo(tmp_path)
    docs_root = tmp_path / "docs"
    _write_v26_real_feature(docs_root / "features" / "F001_Auth")
    _write_generated_docs(docs_root)
    _commit_all(tmp_path)

    sentinel_path = mig_lib.run_sentinel_path(docs_root)
    sentinel_path.parent.mkdir(parents=True, exist_ok=True)
    sentinel_path.write_text("migrated\n", encoding="utf-8")

    exit_code = _run(docs_root, tmp_path)
    captured = capsys.readouterr()

    assert exit_code == 0  # self-healed, then genuinely migrated
    assert "POISONED" in captured.err
    assert (docs_root / "features" / "F001_Auth" / "functional-spec.md").is_file()
    # sentinel was rewritten as real JSON, not left as the poisoned plain-text form
    data = json.loads(sentinel_path.read_text(encoding="utf-8"))
    assert data["progress"] >= 1


def test_t8_zero_progress_json_sentinel_is_poisoned_and_reruns(tmp_path, capsys):
    _init_git_repo(tmp_path)
    docs_root = tmp_path / "docs"
    _write_v26_real_feature(docs_root / "features" / "F001_Auth")
    _write_generated_docs(docs_root)
    _commit_all(tmp_path)

    sentinel_path = mig_lib.run_sentinel_path(docs_root)
    sentinel_path.parent.mkdir(parents=True, exist_ok=True)
    sentinel_path.write_text(
        json.dumps({"format_version": "27", "written_at": "2026-01-01T00:00:00+00:00",
                    "units": 1, "progress": 0, "already": 0, "inert": 1, "failed": 0,
                    "clean": 0, "clean_legacy": 0}),
        encoding="utf-8",
    )

    exit_code = _run(docs_root, tmp_path)
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "POISONED" in captured.err


# --------------------------------------------------------------------------- #
# T9 -- a valid, positive-progress JSON sentinel is honored, not re-run
# --------------------------------------------------------------------------- #
def test_t9_valid_sentinel_honored_no_rerun(tmp_path, capsys):
    _init_git_repo(tmp_path)
    docs_root = tmp_path / "docs"
    (docs_root / "features").mkdir(parents=True)

    mig_lib.write_run_sentinel(docs_root, {
        "units": 66, "progress": 66, "already": 0, "inert": 0, "failed": 0,
        "clean": 10, "clean_legacy": 56,
    })
    sentinel_mtime = mig_lib.run_sentinel_path(docs_root).stat().st_mtime

    exit_code = _run(docs_root, tmp_path)
    out = capsys.readouterr().out

    assert exit_code == 0
    assert mig_lib.run_sentinel_path(docs_root).stat().st_mtime == sentinel_mtime
    assert "progress=66" in out
    assert "already migrated" in out


# --------------------------------------------------------------------------- #
# T10 -- categorize() is exhaustive over U1's verified action vocabulary; unknown
# action is FAILED, fail-closed, never a KeyError.
# --------------------------------------------------------------------------- #
def test_t10_categorize_matches_u1_exhaustive_action_vocabulary():
    # REWORK (adversarial review finding 4, LOW): `confirmed-v27` moved
    # PROGRESS -> ALREADY -- phase-00 § U1's settled table always said ALREADY
    # ("already in the target shape"); this test previously encoded the
    # mismatch itself, which is exactly why the drift survived a green suite.
    expected = {
        "migrated": tally_lib.PROGRESS,
        "migrated-originals-retained": tally_lib.PROGRESS,
        "confirmed-v27": tally_lib.ALREADY,
        "no-op": tally_lib.ALREADY,
        "skipped-hand-edited": tally_lib.INERT,
        "rejected-bad-slug": tally_lib.INERT,
        "skipped-no-target": tally_lib.INERT,
        "failed-validation": tally_lib.FAILED,
        "refused-invalid-v27": tally_lib.FAILED,
    }
    for action, category in expected.items():
        assert tally_lib.categorize(action) == category, action


def test_t10_unknown_action_is_failed_fail_closed(capsys):
    result = tally_lib.categorize("some-action-nobody-wrote-yet")
    assert result == tally_lib.FAILED

    tally = tally_lib.Tally()
    category = tally.add("some-action-nobody-wrote-yet")
    err = capsys.readouterr().err
    assert category == tally_lib.FAILED
    assert tally.failed == 1
    assert "unrecognized migration action" in err


# --------------------------------------------------------------------------- #
# T11/T12 -- B5 change 1/2: cross-repo --project-root default + actionable failure
# --------------------------------------------------------------------------- #
def test_t11_docs_root_in_other_repo_no_project_root_flag_still_works(tmp_path, monkeypatch):
    repo_b = tmp_path / "repo-b"
    docs_root = repo_b / "docs"
    _init_git_repo(repo_b)
    (docs_root / "features").mkdir(parents=True)
    _commit_all(repo_b)

    # Prove the CWD is irrelevant: run from a totally unrelated directory.
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    exit_code = cli.main(["--docs-root", str(docs_root)])  # no --project-root
    assert exit_code == 0  # empty features/ -- proves assert_under passed, not a refusal


def test_t12_assert_under_violation_names_project_root_remedy(tmp_path, capsys):
    repo_a = tmp_path / "repo-a"
    repo_b = tmp_path / "repo-b"
    docs_root = repo_b / "docs"
    _init_git_repo(repo_a)
    _init_git_repo(repo_b)
    (docs_root / "features").mkdir(parents=True)
    _commit_all(repo_b)

    exit_code = cli.main(["--docs-root", str(docs_root), "--project-root", str(repo_a)])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "--project-root" in captured.err
    assert "Detected git toplevel of --docs-root" in captured.err
    assert "[SUMMARY]" in captured.out


# --------------------------------------------------------------------------- #
# T13/T14 -- B5 change 3: language-mirror refusal guard
# --------------------------------------------------------------------------- #
def test_t13_docs_root_at_language_mirror_is_refused(tmp_path, capsys):
    _init_git_repo(tmp_path)
    docs_root = tmp_path / "docs"
    (docs_root / "features").mkdir(parents=True)
    (docs_root / ".rebuild-state.json").write_text("{}", encoding="utf-8")
    mirror_root = docs_root / "vi"
    (mirror_root / "features").mkdir(parents=True)
    _commit_all(tmp_path)

    exit_code = cli.main(["--docs-root", str(mirror_root), "--project-root", str(tmp_path)])
    err = capsys.readouterr().err

    assert exit_code == 2
    assert "translate" in err
    assert "mirror" in err


def test_t14_docs_root_at_primary_tree_is_not_refused(tmp_path):
    _init_git_repo(tmp_path)
    docs_root = tmp_path / "docs"
    (docs_root / "features").mkdir(parents=True)
    (docs_root / ".rebuild-state.json").write_text("{}", encoding="utf-8")
    _commit_all(tmp_path)

    exit_code = cli.main(["--docs-root", str(docs_root), "--project-root", str(tmp_path)])
    assert exit_code == 0  # not refused -- empty features/ so nothing to migrate either


# --------------------------------------------------------------------------- #
# T15 -- [SUMMARY] on every exit path (0, 1, 2, 3, 4, dry-run) -- the linchpin
# --------------------------------------------------------------------------- #
def test_t15_summary_line_present_on_every_exit_path(tmp_path, capsys):
    # exit 2 -- --docs-root not a directory
    rc = cli.main(["--docs-root", str(tmp_path / "nope"), "--project-root", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 2 and "[SUMMARY]" in out

    # exit 2 -- assert_under violated
    repo_a, repo_b = tmp_path / "a", tmp_path / "b"
    _init_git_repo(repo_a)
    _init_git_repo(repo_b)
    (repo_b / "docs" / "features").mkdir(parents=True)
    _commit_all(repo_b)
    rc = cli.main(["--docs-root", str(repo_b / "docs"), "--project-root", str(repo_a)])
    out = capsys.readouterr().out
    assert rc == 2 and "[SUMMARY]" in out

    # exit 3 -- lock held
    project_root = tmp_path / "repo3"
    _init_git_repo(project_root)
    docs_root = project_root / "docs"
    _write_v26_feature_hand_edited(docs_root / "features" / "F001_HandEdited")
    _commit_all(project_root)
    lock_path = mig_lib.staging_root(docs_root) / mig_lib.LOCK_NAME
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    held_fh = open(lock_path, "w")
    fcntl.flock(held_fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        rc = cli.main(["--docs-root", str(docs_root), "--project-root", str(project_root)])
        out = capsys.readouterr().out
        assert rc == 3 and "[SUMMARY]" in out
    finally:
        fcntl.flock(held_fh, fcntl.LOCK_UN)
        held_fh.close()

    # exit 4 -- all-inert
    docs_root4 = tmp_path / "repo4" / "docs"
    _init_git_repo(tmp_path / "repo4")
    _write_v26_feature_hand_edited(docs_root4 / "features" / "F001_HandEdited")
    _commit_all(tmp_path / "repo4")
    rc = _run(docs_root4, tmp_path / "repo4")
    out = capsys.readouterr().out
    assert rc == 4 and "[SUMMARY]" in out

    # exit 0 -- full success
    docs_root0 = tmp_path / "repo0" / "docs"
    _init_git_repo(tmp_path / "repo0")
    _write_v26_real_feature(docs_root0 / "features" / "F001_Auth")
    _write_generated_docs(docs_root0)
    _commit_all(tmp_path / "repo0")
    rc = _run(docs_root0, tmp_path / "repo0")
    out = capsys.readouterr().out
    assert rc == 0 and "[SUMMARY]" in out

    # dry-run -- always exit 0
    rc = _run(docs_root4, tmp_path / "repo4", dry_run=True)
    out = capsys.readouterr().out
    assert rc == 0 and "[SUMMARY]" in out


# --------------------------------------------------------------------------- #
# T16 -- the sentinel write is still atomic (temp sibling + os.replace); no stray
# temp files survive a successful run.
# --------------------------------------------------------------------------- #
def test_t16_sentinel_write_leaves_no_stray_temp_files(tmp_path):
    _init_git_repo(tmp_path)
    docs_root = tmp_path / "docs"
    _write_v26_real_feature(docs_root / "features" / "F001_Auth")
    _write_generated_docs(docs_root)
    _commit_all(tmp_path)

    exit_code = _run(docs_root, tmp_path)
    assert exit_code == 0
    stray = list(mig_lib.staging_root(docs_root).glob("*.tmp"))
    assert stray == [], f"leftover temp file(s) after a successful run: {stray}"
    assert mig_lib.run_sentinel_path(docs_root).is_file()


# --------------------------------------------------------------------------- #
# T17 -- --dry-run on an all-INERT corpus: same tally shape, exit 0, zero bytes written
# --------------------------------------------------------------------------- #
def test_t17_dry_run_on_all_inert_corpus_exits_0_writes_nothing(tmp_path, capsys):
    _init_git_repo(tmp_path)
    docs_root = tmp_path / "docs"
    _write_v26_feature_hand_edited(docs_root / "features" / "F001_HandEdited")
    _commit_all(tmp_path)

    before = sorted(str(p) for p in docs_root.rglob("*"))
    exit_code = _run(docs_root, tmp_path, dry_run=True)
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "[SUMMARY]" in out
    assert "inert=1" in out
    assert sorted(str(p) for p in docs_root.rglob("*")) == before
    assert not (docs_root / mig_lib.STAGING_DIRNAME).exists()


# --------------------------------------------------------------------------- #
# Tally unit coverage -- happy path and failure paths for the class itself
# --------------------------------------------------------------------------- #
def test_tally_sentinel_worthy_true_only_when_no_failed_and_no_inert():
    t = tally_lib.Tally()
    t.add("migrated")
    t.add("no-op")
    assert t.sentinel_worthy is True
    assert t.exit_code() == 0

    t.add("skipped-hand-edited")
    assert t.sentinel_worthy is False
    assert t.exit_code() == 4

    t.add("failed-validation")
    assert t.sentinel_worthy is False
    assert t.exit_code() == 1  # FAILED outranks INERT


def test_tally_to_dict_from_dict_roundtrip():
    t = tally_lib.Tally()
    t.add("migrated", provenance=tally_lib.CLEAN)
    t.add("migrated-originals-retained", provenance=tally_lib.CLEAN_LEGACY)
    t.add("skipped-hand-edited")
    restored = tally_lib.Tally.from_dict(t.to_dict())
    assert restored.to_dict() == t.to_dict()
