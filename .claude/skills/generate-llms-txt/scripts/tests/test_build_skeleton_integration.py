"""Integration tests: run build-llms-skeleton.py end to end (subprocess) against the six
fixture repos, asserting the frozen v2 manifest shape and the phase's sealed success criteria.

Every fixture is staged into `tmp_path` before use (see `conftest.stage_fixture` for why) and
every run's `--output` is also `tmp_path` — nothing is ever written back into the fixture
directories themselves.
"""
import discovery

from conftest import (
    DEV_TOOL_REPO,
    GOLDEN_DIR,
    OVERSIZED_REPO,
    RICH_REPO,
    SCRIPTS_DIR,
    SECRET_REPO,
    THIN_REPO,
    UNFILLED_API_REPO,
    run_for_manifest,
    run_script,
    stage_fixture,
)


def test_rich_repo_contract(tmp_path):
    source = stage_fixture(tmp_path, RICH_REPO)
    out = tmp_path / "out"
    manifest = run_for_manifest(source, out, "--audience", "user")

    contract = manifest["contract"]
    assert [c["id"] for c in contract] == ["intro", "install", "usage", "screens",
                                            "features", "api", "optional"]
    assert all(c["status"] in ("filled", "omitted") for c in contract), contract

    assert manifest["self_containment"]["remaining"] == 0
    assert manifest["budget"]["over_cap"] is False

    dropped = manifest["audience_filter"]["dropped_files"]
    assert "docs/system/architecture.md" in dropped
    assert "docs/screens/SCR001_Login/spec.md" in dropped  # F7

    assert "docs/misc/notes.md" in manifest["audience_filter"]["dropped_unmatched"]  # F6a

    assert "docs/generated/api-map.md" in manifest["content_contract"]["unclaimed"]  # F6b

    by_id = {c["id"]: c for c in contract}
    assert by_id["screens"]["status"] == "filled"
    assert by_id["screens"]["sources"] == ["docs/user-guide/screens.md"]  # F2


def test_thin_repo_advisories(tmp_path):
    source = stage_fixture(tmp_path, THIN_REPO)
    out = tmp_path / "out"
    manifest = run_for_manifest(source, out)

    assert manifest["profile"]["status"] == "missing"
    by_id = {c["id"]: c for c in manifest["contract"]}

    # Required sections with nothing to fill them carry an explicit, path-naming advisory.
    for sid in ("intro", "usage", "screens", "features"):
        assert by_id[sid]["status"] == "gap", sid
        assert by_id[sid]["advisory"], f"{sid} gap must name an export path"

    # install IS filled here — the contract's own source list includes "README user-install
    # parts" (phase-02 table), and this fixture's only file is a README.
    assert by_id["install"]["status"] == "filled"
    assert by_id["install"]["sources"] == ["README.md"]

    # api is genuinely absent (no surfaces declared, no OpenAPI spec anywhere) -> silent omit.
    assert by_id["api"]["status"] == "omitted"
    assert by_id["api"]["advisory"] is None


def test_dev_tool_repo_audience_resolved_from_profile(tmp_path):
    source = stage_fixture(tmp_path, DEV_TOOL_REPO)
    out = tmp_path / "out"
    manifest = run_for_manifest(source, out)  # no --audience flag passed
    assert manifest["audience"] == "dev"
    assert manifest["audience_source"] == "profile"


def test_index_only_skips_full_artifact(tmp_path):
    source = stage_fixture(tmp_path, RICH_REPO)
    out = tmp_path / "out"
    manifest = run_for_manifest(source, out, "--index-only")
    assert "budget" not in manifest
    assert "self_containment" not in manifest
    assert "secret_scan" not in manifest
    assert not (out / ".llms-full.txt.work").exists()
    assert (out / ".llms.txt.work").exists()


def test_full_flag_is_deprecated_noop_alias(tmp_path):
    source = stage_fixture(tmp_path, RICH_REPO)
    out = tmp_path / "out"
    code, manifest, _out, err = run_script(
        ["--source", str(source), "--output", str(out), "--manifest", "-", "--full"]
    )
    assert code == 0
    assert "deprecated" in err.lower()
    assert (out / ".llms-full.txt.work").exists()  # full still stages by default


def test_promote_publishes_both_artifacts_and_refuses_without_staging(tmp_path):
    source = stage_fixture(tmp_path, RICH_REPO)
    out = tmp_path / "out"
    run_for_manifest(source, out)

    code, _manifest, stdout, _err = run_script(["--output", str(out), "--promote"])
    assert code == 0
    assert (out / "llms.txt").is_file()
    assert (out / "llms-full.txt").is_file()
    assert "promoted" in stdout

    empty_out = tmp_path / "empty-out"
    empty_out.mkdir()
    code, _manifest, _stdout, err = run_script(["--output", str(empty_out), "--promote"])
    assert code == 1
    assert "refusing to promote" in err
    assert not (empty_out / "llms.txt").exists()


def test_secret_repo_withholds_full_artifact_but_promotes_index(tmp_path):
    source = stage_fixture(tmp_path, SECRET_REPO)
    out = tmp_path / "out"
    manifest = run_for_manifest(source, out)

    assert manifest["secret_scan"]["status"] != "clean"
    assert manifest["secret_scan"]["blocks_full_artifact"] is True
    assert manifest["secret_scan"]["warnings"]

    code, _manifest, stdout, err = run_script(["--output", str(out), "--promote"])
    assert code == 0
    assert (out / "llms.txt").is_file()
    assert not (out / "llms-full.txt").exists()
    assert "withholding llms-full.txt" in err
    assert "llms-full.txt" not in stdout


def test_unfilled_api_repo_reports_gap_not_silent_omit(tmp_path):
    """F6c: unfilled `Surfaces` + a real OpenAPI spec on disk -> the api section is a `gap`
    naming the fill-the-profile advisory, never a silent `omitted`."""
    source = stage_fixture(tmp_path, UNFILLED_API_REPO)
    out = tmp_path / "out"
    manifest = run_for_manifest(source, out)
    assert manifest["profile"]["status"] == "incomplete"
    assert "surfaces" in manifest["profile"]["missing_fields"]

    by_id = {c["id"]: c for c in manifest["contract"]}
    assert by_id["api"]["status"] == "gap"
    assert by_id["api"]["advisory"] and "surfaces" in by_id["api"]["advisory"].lower()


def test_oversized_repo_forces_trim_and_self_containment_holds_after(tmp_path):
    """F9: a small explicit --budget forces the ladder deterministically without needing a
    genuinely huge fixture on disk; self_containment.remaining must hold at 0 AFTER trimming."""
    source = stage_fixture(tmp_path, OVERSIZED_REPO)
    out = tmp_path / "out"
    manifest = run_for_manifest(source, out, "--budget", "30")

    trims = manifest["budget"]["trims"]
    assert trims, "a tiny cap must force at least one trim step"
    assert trims[0]["step"] == "optional-dropped"
    assert manifest["self_containment"]["remaining"] == 0


def test_golden_dev_index_byte_for_byte(tmp_path):
    """FR-4: `--audience dev` on the fixture rich repo matches a committed golden file byte for
    byte. The only golden file in the suite, scoped to the one path the plan freezes by
    contract; everything else in this suite asserts fields, not bytes."""
    source = stage_fixture(tmp_path, RICH_REPO)
    out = tmp_path / "out"
    run_for_manifest(source, out, "--audience", "dev")
    actual = (out / ".llms.txt.work").read_text(encoding="utf-8")
    expected = (GOLDEN_DIR / "rich-repo-dev-index.txt").read_text(encoding="utf-8")
    assert actual == expected


def test_scan_of_this_repo_never_lists_paths_under_tests_fixtures():
    """Risk mitigation: if EXCLUDE_DIRS ever stops excluding `tests`/`fixtures`, this test
    catches the regression before our own fixture repos start polluting a real scan. Scans the
    generate-llms-txt skill's own `scripts/` tree (which contains this suite's fixtures) exactly
    the way build-llms-skeleton.py would scan any repo's docs root."""
    files = discovery.collect_markdown(SCRIPTS_DIR, SCRIPTS_DIR)
    for f in files:
        parts = set(f["rel"].replace("\\", "/").split("/"))
        assert "fixtures" not in parts and "tests" not in parts, f["rel"]


def test_manifest_carries_readiness_block(tmp_path):
    """The preflight gate reads `readiness` straight off the manifest — no re-derivation."""
    src = stage_fixture(tmp_path, RICH_REPO)
    manifest = run_for_manifest(src, tmp_path / "out")
    assert manifest["readiness"] == {"required_total": 6, "filled": 6, "gaps": [], "thin": False}


def test_require_complete_passes_on_a_complete_repo(tmp_path):
    src = stage_fixture(tmp_path, RICH_REPO)
    code, _m, _out, err = run_script(
        ["--source", str(src), "--output", str(tmp_path / "out"), "--require-complete"])
    assert code == 0, err


def test_require_complete_exits_two_and_names_the_gaps(tmp_path):
    """CI enforcement gates on the OUTCOME. The manifest is still emitted first so the job log
    shows WHAT is missing, then the non-zero exit fails the build."""
    src = stage_fixture(tmp_path, THIN_REPO)
    code, manifest, _out, err = run_script(
        ["--source", str(src), "--output", str(tmp_path / "out"), "--require-complete"])
    assert code == 2
    assert manifest is not None, "manifest must be emitted before the gate exits"
    assert manifest["readiness"]["thin"] is True
    for gap in ("intro", "usage", "screens", "features"):
        assert gap in err


def test_require_complete_fails_on_an_empty_repo(tmp_path):
    """Tier 4 stages nothing at all — incomplete by definition, even though `contract` is absent
    from the manifest, so the gate must not read that absence as 'no gaps'."""
    empty = tmp_path / "empty-repo"
    empty.mkdir()
    code, manifest, _out, err = run_script(
        ["--source", str(empty), "--output", str(tmp_path / "out"), "--require-complete"])
    assert code == 2
    assert manifest["tier"] == 4
    assert "T1-T3 empty" in err
