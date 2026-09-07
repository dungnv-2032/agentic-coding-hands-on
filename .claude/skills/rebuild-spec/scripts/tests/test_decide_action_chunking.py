"""Tests for decide_action_chunking.py — phase 07's action-count/capability-count chunk gate.

Covers the predicate directly (decide), the two parsers (count_action_index_rows,
extract_capability_order), the feature-dir end-to-end path, and the CLI (subprocess, asserting
on parsed JSON fields, never on exit code alone).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from decide_action_chunking import (  # noqa: E402
    ACTION_INDEX_HEADER,
    DEFAULT_THRESHOLD,
    count_action_index_rows,
    decide,
    decide_for_feature_dir,
    extract_capability_order,
)

SCRIPT = Path(__file__).resolve().parents[1] / "decide_action_chunking.py"


def _run(args: list[str], env: dict | None = None) -> tuple[int, str, dict]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, timeout=30, env=env,
    )
    data = json.loads(result.stdout) if result.stdout.strip() else {}
    return result.returncode, result.stderr, data


def _action_index(n_data_rows: int) -> str:
    """Build a minimal '## 2. Action Index' table with n_data_rows rows (A0..A{n-1})."""
    rows = "\n".join(
        f"| **A{i}** | `Controller#a{i}` | `GET` `.../a{i}` | FR-{i:03d} | — | § 3.1 |"
        for i in range(n_data_rows)
    )
    return (
        "## 2. Action Index\n\n"
        "| # | Action (handler) | Method · Path | Codes | Writes | Detail |\n"
        "|---|---|---|---|---|---|\n"
        f"{rows}\n"
    )


def _cap_table(caps: list[str]) -> str:
    rows = "\n".join(f"| {c} | Some capability {c} | Does a thing | US001 | FR-001 | BR-001 | SCR001 |" for c in caps)
    return (
        "## 2. Functional Capabilities\n\n"
        "| ID | Capability | What the user can do | User Stories | Requirements | Business Rules | Screens |\n"
        "|----|------------|------------------------|-----------------|---------------|-------------------|---------|\n"
        f"{rows}\n"
    )


# ---------------------------------------------------------------------------
# decide() — the pure predicate. The two-sided check the merge blockers require.
# ---------------------------------------------------------------------------

class TestDecidePredicate:
    def test_over_threshold_and_multi_capability_chunks(self):
        result = decide(20, ["CAP-01", "CAP-02", "CAP-03"], 15)
        assert result["chunk"] is True
        assert result["slices"] == ["CAP-01", "CAP-02", "CAP-03"]
        assert "chunking by capability" in result["reason"]

    def test_under_threshold_does_not_chunk(self):
        result = decide(9, ["CAP-01", "CAP-02"], 15)
        assert result["chunk"] is False
        assert result["slices"] == []
        assert "single-pass" in result["reason"]

    def test_f011_shape_one_capability_eight_actions_no_chunk(self):
        # F011_ListingModeration: 1 capability / ~8-9 actions — must NOT chunk.
        result = decide(9, ["CAP-01"], 15)
        assert result["chunk"] is False

    def test_f010_shape_forty_seven_actions_five_capabilities_chunks(self):
        # F010_ListingCatalogConfiguration: 47 actions, chunks by capability.
        caps = [f"CAP-{n:02d}" for n in range(1, 6)]
        result = decide(47, caps, 15)
        assert result["chunk"] is True
        assert result["slices"] == caps

    def test_boundary_one_below_threshold(self):
        assert decide(14, ["CAP-01", "CAP-02"], 15)["chunk"] is False

    def test_boundary_exactly_at_threshold(self):
        assert decide(15, ["CAP-01", "CAP-02"], 15)["chunk"] is True

    def test_over_threshold_but_single_capability_does_not_chunk(self):
        """The provable-but-not-guaranteed case: ≥15 actions, only 1 capability recognized.
        Must not silently fall through — the reason names the exact cause."""
        result = decide(20, ["CAP-01"], 15)
        assert result["chunk"] is False
        assert result["slices"] == []
        assert "no slice axis to chunk on" in result["reason"]

    def test_over_threshold_zero_capabilities_does_not_chunk(self):
        result = decide(30, [], 15)
        assert result["chunk"] is False
        assert "no slice axis to chunk on" in result["reason"]

    def test_slice_order_preserved_not_sorted(self):
        caps = ["CAP-03", "CAP-01", "CAP-02"]  # deliberately out of numeric order
        result = decide(20, caps, 15)
        assert result["slices"] == caps


# ---------------------------------------------------------------------------
# count_action_index_rows — the denominator parser
# ---------------------------------------------------------------------------

class TestCountActionIndexRows:
    def test_counts_all_data_rows_including_a0(self):
        text = _action_index(9)
        count, err = count_action_index_rows(text)
        assert err is None
        assert count == 9

    def test_large_row_count(self):
        text = _action_index(47)
        count, err = count_action_index_rows(text)
        assert count == 47
        assert err is None

    def test_missing_header_is_reported_not_zero(self):
        count, err = count_action_index_rows("## 2. Functional -> Technical Mapping\nnothing here\n")
        assert count is None
        assert err is not None
        assert "not found" in err

    def test_empty_document(self):
        count, err = count_action_index_rows("")
        assert count is None
        assert err is not None

    def test_header_must_match_exactly(self):
        garbled = ACTION_INDEX_HEADER.replace("Writes", "Effects")
        count, err = count_action_index_rows(f"## 2. Action Index\n\n{garbled}\n|---|\n| **A0** | x |\n")
        assert count is None
        assert err is not None


# ---------------------------------------------------------------------------
# extract_capability_order — the slice-axis parser
# ---------------------------------------------------------------------------

class TestExtractCapabilityOrder:
    def test_extracts_in_document_order(self):
        text = _cap_table(["CAP-01", "CAP-02", "CAP-03"])
        codes, err = extract_capability_order(text)
        assert err is None
        assert codes == ["CAP-01", "CAP-02", "CAP-03"]

    def test_single_capability(self):
        codes, err = extract_capability_order(_cap_table(["CAP-01"]))
        assert codes == ["CAP-01"]

    def test_missing_section_reports_error(self):
        codes, err = extract_capability_order("## 1. Overview\nNothing about capabilities.\n")
        assert codes == []
        assert err is not None

    def test_section_present_but_no_table(self):
        codes, err = extract_capability_order("## 2. Functional Capabilities\n\nNo table yet.\n\n## 3. Open Decisions\n")
        assert codes == []
        assert err is not None

    def test_ignores_non_cap_rows(self):
        text = (
            "## 2. Functional Capabilities\n\n"
            "| ID | Capability |\n|---|---|\n"
            "| N/A | placeholder |\n"
            "| CAP-01 | real one |\n"
        )
        codes, _ = extract_capability_order(text)
        assert codes == ["CAP-01"]


# ---------------------------------------------------------------------------
# decide_for_feature_dir — end to end, real file layout
# ---------------------------------------------------------------------------

class TestDecideForFeatureDir:
    def test_f011_like_feature_does_not_chunk(self, tmp_path):
        feat = tmp_path / "F011_ListingModeration"
        feat.mkdir()
        (feat / "technical-spec.md").write_text(_action_index(9), encoding="utf-8")
        (feat / "functional-spec.md").write_text(_cap_table(["CAP-01"]), encoding="utf-8")

        result = decide_for_feature_dir(feat, DEFAULT_THRESHOLD)
        assert result["chunk"] is False

    def test_f010_like_feature_chunks(self, tmp_path):
        feat = tmp_path / "F010_ListingCatalogConfiguration"
        feat.mkdir()
        (feat / "technical-spec.md").write_text(_action_index(47), encoding="utf-8")
        caps = [f"CAP-{n:02d}" for n in range(1, 6)]
        (feat / "functional-spec.md").write_text(_cap_table(caps), encoding="utf-8")

        result = decide_for_feature_dir(feat, DEFAULT_THRESHOLD)
        assert result["chunk"] is True
        assert result["slices"] == caps

    def test_missing_technical_spec_fails_open(self, tmp_path):
        feat = tmp_path / "F999_Empty"
        feat.mkdir()
        result = decide_for_feature_dir(feat, DEFAULT_THRESHOLD)
        assert result["chunk"] is False
        assert "not found" in result["reason"]
        assert "fail-open" in result["reason"]

    def test_malformed_action_index_fails_open(self, tmp_path):
        feat = tmp_path / "F998_Malformed"
        feat.mkdir()
        (feat / "technical-spec.md").write_text("## 2. Something Else\nno table\n", encoding="utf-8")
        (feat / "functional-spec.md").write_text(_cap_table(["CAP-01", "CAP-02"]), encoding="utf-8")

        result = decide_for_feature_dir(feat, DEFAULT_THRESHOLD)
        assert result["chunk"] is False
        assert "fail-open" in result["reason"]

    def test_missing_functional_spec_falls_through_to_no_slice_axis(self, tmp_path):
        """Over threshold, but functional-spec.md absent entirely -> 0 capabilities -> no
        special case needed, the ordinary '< 2 capabilities' branch already covers it."""
        feat = tmp_path / "F997_NoFunctionalSpec"
        feat.mkdir()
        (feat / "technical-spec.md").write_text(_action_index(20), encoding="utf-8")

        result = decide_for_feature_dir(feat, DEFAULT_THRESHOLD)
        assert result["chunk"] is False
        assert "no slice axis to chunk on" in result["reason"]


# ---------------------------------------------------------------------------
# CLI — subprocess, asserting on parsed JSON fields (never bare exit code)
# ---------------------------------------------------------------------------

class TestCli:
    def test_direct_counts_chunk(self):
        code, _stderr, data = _run(["--actions", "20", "--capabilities", "3"])
        assert code == 0
        assert data["chunk"] is True
        assert data["slices"] == ["CAP-01", "CAP-02", "CAP-03"]

    def test_direct_counts_no_chunk(self):
        code, _stderr, data = _run(["--actions", "9", "--capabilities", "1"])
        assert code == 0
        assert data["chunk"] is False
        assert data["slices"] == []

    def test_missing_required_args_is_usage_error(self):
        code, stderr, _data = _run(["--actions", "9"])
        assert code == 2
        assert "feature-dir" in stderr or "actions" in stderr

    def test_feature_dir_mode_end_to_end(self, tmp_path):
        feat = tmp_path / "F010_ListingCatalogConfiguration"
        feat.mkdir()
        (feat / "technical-spec.md").write_text(_action_index(47), encoding="utf-8")
        caps = [f"CAP-{n:02d}" for n in range(1, 6)]
        (feat / "functional-spec.md").write_text(_cap_table(caps), encoding="utf-8")

        code, _stderr, data = _run(["--feature-dir", str(feat)])
        assert code == 0
        assert data["chunk"] is True
        assert data["slices"] == caps

    def test_threshold_flag_overrides_default(self):
        code, _stderr, data = _run(["--actions", "16", "--capabilities", "2", "--threshold", "20"])
        assert code == 0
        assert data["chunk"] is False

    def test_env_threshold_is_honored(self):
        env = {**os.environ, "REBUILD_ACTION_CHUNK_THRESHOLD": "5"}
        code, _stderr, data = _run(["--actions", "6", "--capabilities", "2"], env=env)
        assert code == 0
        assert data["chunk"] is True

    def test_invalid_env_threshold_falls_back_to_default_with_warning(self):
        env = {**os.environ, "REBUILD_ACTION_CHUNK_THRESHOLD": "not-a-number"}
        code, stderr, data = _run(["--actions", "15", "--capabilities", "2"], env=env)
        assert code == 0
        assert data["chunk"] is True  # fell back to default 15, 15 >= 15
        assert "invalid" in stderr
        assert "REBUILD_ACTION_CHUNK_THRESHOLD" in stderr

    def test_negative_env_threshold_falls_back_to_default(self):
        env = {**os.environ, "REBUILD_ACTION_CHUNK_THRESHOLD": "-3"}
        code, stderr, data = _run(["--actions", "10", "--capabilities", "2"], env=env)
        assert code == 0
        assert data["chunk"] is False  # default 15, 10 < 15
        assert "invalid" in stderr

    def test_threshold_flag_takes_precedence_over_env(self):
        env = {**os.environ, "REBUILD_ACTION_CHUNK_THRESHOLD": "5"}
        code, _stderr, data = _run(
            ["--actions", "6", "--capabilities", "2", "--threshold", "15"], env=env
        )
        assert code == 0
        assert data["chunk"] is False  # explicit --threshold 15 wins, 6 < 15
