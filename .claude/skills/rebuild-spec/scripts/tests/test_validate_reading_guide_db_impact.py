# layout-exempt: rebuild-spec A3 validator tests — docs paths are managed targets
"""Tests for validate_reading_guide_db_impact.py (v26.0.0, acsim-learnings phase-03).

Covers the degradation contract for A3 `## Source Walkthrough` (shared: technical-spec.md
+ screen-spec spec.md): absent → WARN pre_migration; empty body → CRITICAL malformed;
unfilled placeholder → WARN unmapped; well-formed → no issues.

B4 `## DB Impact per Event` (technical-spec.md only) and `check_db_impact()` RETIRED this
release (phase 08, self-sufficiency v27.8) — every `db_impact.*`-rule_id test that used to
live here retired with it (deleted, not left green over a check that can no longer fire);
`FeatureSpec.retired_section_present` (validate_feature_spec.py, its own dedicated test
file) is what now flags a technical-spec.md still carrying either retired heading.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import validate_reading_guide_db_impact as v  # noqa: E402


def _sev(issues, rid):
    return [i for i in issues if i["rule_id"] == rid]


# ---------------------------------------------------------------------------
# A3 — Source Walkthrough (shared check, both families)
# ---------------------------------------------------------------------------

class TestSourceWalkthrough:
    def test_absent_is_pre_migration_warn(self):
        text = "## Overview\n\nSome content.\n"
        issues = v.check_source_walkthrough(text, "f")
        assert len(_sev(issues, "reading_guide.pre_migration")) == 1
        assert issues[0]["severity"] == "warning"

    def test_empty_body_is_malformed_critical(self):
        text = "## Source Walkthrough\n\n## Unresolved Questions\n\nx\n"
        issues = v.check_source_walkthrough(text, "f")
        assert len(_sev(issues, "reading_guide.malformed")) == 1
        assert issues[0]["severity"] == "critical"

    def test_unfilled_placeholder_is_unmapped_warn(self):
        text = ("## Source Walkthrough\n\n"
                "1. **File:** `{path/to/file.ext:start-end}` — {why read this first}\n\n"
                "## Unresolved Questions\n")
        issues = v.check_source_walkthrough(text, "f")
        assert len(_sev(issues, "reading_guide.unmapped")) == 1
        assert issues[0]["severity"] == "warning"

    def test_filled_content_passes(self):
        text = ("## Source Walkthrough\n\n"
                "1. **File:** `models/order.rb:1-40` — defines the Order entity.\n\n"
                "## Unresolved Questions\n")
        assert v.check_source_walkthrough(text, "f") == []

    def test_bounded_by_next_h2_not_leaking_into_following_section(self):
        text = ("## Source Walkthrough\n\n"
                "1. **File:** `x.rb:1-2` — real content.\n\n"
                "## DB Impact per Event\n\nN/A — read-only feature, no DB writes.\n")
        issues = v.check_source_walkthrough(text, "f")
        assert issues == []


# TestDbImpact RETIRED (phase 08, self-sufficiency v27.8): `check_db_impact()` no
# longer exists — B4 left technical-spec.md's target shape this release. Every
# `db_impact.*` rule_id this class exercised (`pre_migration`/`malformed`/
# `unmapped`/`uncited`) retired with it. Not left green-on-nothing; deleted
# outright, per requirement 3's own instruction.

# ---------------------------------------------------------------------------
# C1 regression — fenced heading-shaped line must not truncate the section body
# (phase-01, attack/t3_placeholder_hidden_by_fence + t3_control_no_fence)
# ---------------------------------------------------------------------------

class TestFenceAwareSectionBoundary:
    def test_fenced_heading_shaped_line_no_longer_hides_trailing_placeholder(self):
        # Was PASS before the C1 fix: the fence-blind boundary regex stopped the body
        # right before the fenced "# Note:" line, hiding the {placeholder} that follows it.
        text = (
            "# Technical Spec\n\n"
            "## Source Walkthrough\n\n"
            "Reading order:\n\n"
            "```python\n"
            "# Note: see handler\n"
            "```\n"
            "{Ordered reading list (data model -> entry point -> view -> logic), 1 file per "
            "step, with a 1-sentence \"why start here.\"}\n\n"
            "1. **File:** `{path/to/file.ext:start-end}` — {why read this first}\n\n"
            "## DB Impact per Event\n\n"
            "N/A — no DB writes in this feature.\n"
        )
        issues = v.check_source_walkthrough(text, "f")
        assert len(_sev(issues, "reading_guide.unmapped")) == 1
        assert issues[0]["severity"] == "warning"

    def test_control_no_fence_still_warns_unmapped_parity(self):
        # Same content minus the fence — must produce the identical WARN (parity proof).
        text = (
            "# Technical Spec\n\n"
            "## Source Walkthrough\n\n"
            "Reading order:\n\n"
            "{Ordered reading list (data model -> entry point -> view -> logic), 1 file per "
            "step, with a 1-sentence \"why start here.\"}\n\n"
            "1. **File:** `{path/to/file.ext:start-end}` — {why read this first}\n\n"
            "## DB Impact per Event\n\n"
            "N/A — no DB writes in this feature.\n"
        )
        issues = v.check_source_walkthrough(text, "f")
        assert len(_sev(issues, "reading_guide.unmapped")) == 1
        assert issues[0]["severity"] == "warning"

    def test_tilde_fenced_heading_shaped_line_also_handled(self):
        text = (
            "## Source Walkthrough\n\n"
            "~~~\n# fake heading\n~~~\n"
            "{still unfilled}\n\n"
            "## Unresolved Questions\n"
        )
        issues = v.check_source_walkthrough(text, "f")
        assert len(_sev(issues, "reading_guide.unmapped")) == 1


# TestFencedExampleTableIgnored and TestEscapedPipeInB4Row RETIRED (phase 08,
# self-sufficiency v27.8): both existed solely to exercise `check_db_impact`'s B4
# table parsing, which no longer exists. Not left green-on-nothing; deleted
# outright.

# ---------------------------------------------------------------------------
# integration: validate() over both families + main() exit codes + summary merge
# ---------------------------------------------------------------------------

_TECH_WELL_FORMED = "## Source Walkthrough\n\n1. **File:** `x.rb:1-2` — real content.\n"
_SCREEN_WELL_FORMED = "## Source Walkthrough\n\n1. **File:** `x.vue:1-2` — real content.\n"


def _make_docs(tmp_path: Path, tech_body: str = _TECH_WELL_FORMED,
               screen_body: str = _SCREEN_WELL_FORMED) -> Path:
    docs = tmp_path / "docs"
    feat = docs / "features" / "F001_Login"
    feat.mkdir(parents=True)
    (feat / "technical-spec.md").write_text(tech_body, encoding="utf-8")
    scr = docs / "screens" / "SCR001_Login"
    scr.mkdir(parents=True)
    (scr / "spec.md").write_text(screen_body, encoding="utf-8")
    return docs


class TestIntegration:
    def test_validate_passes_on_well_formed_docs(self, tmp_path):
        docs = _make_docs(tmp_path)
        result = v.validate(docs)
        assert result["status"] == "PASS", result["issues"]

    def test_validate_warns_on_pre_migration_docs(self, tmp_path):
        docs = _make_docs(tmp_path, tech_body="## Overview\n\nx\n", screen_body="## Purpose\n\nx\n")
        result = v.validate(docs)
        assert result["status"] == "WARN"
        rids = {i["rule_id"] for i in result["issues"]}
        # ONLY the screen-spec absence fires now: A3 retired from
        # technical-spec.md (phase 08) so `validate()` no longer walks it, and
        # B4's own `db_impact.pre_migration` retired with `check_db_impact`.
        assert rids == {"reading_guide.pre_migration"}
        locs = [i["location"]["file"] for i in result["issues"]]
        assert all("screens/" in p for p in locs), locs

    def test_validate_fails_on_malformed_docs(self, tmp_path):
        # Driven through the SCREEN spec: screens are A3's only remaining family
        # (phase 08 retired A3 from technical-spec.md), so a malformed A3 body
        # must be constructed there to reach `reading_guide.malformed`.
        docs = _make_docs(
            tmp_path, screen_body="## Source Walkthrough\n\n## Unresolved Questions\n"
        )
        result = v.validate(docs)
        assert result["status"] == "FAIL"

    def test_technical_specs_are_not_walked_for_a3(self, tmp_path):
        """REGRESSION GUARD (phase 08 req 3, missed there, closed in phase 09).

        A3 is retired from `technical-spec.md`, so a technical spec with NO A3
        section is CORRECT output and must produce zero issues. While
        `validate()` still walked the features tree, this fired
        `reading_guide.pre_migration` on 43/43 real-corpus technical-specs, each
        message telling the operator to run `migrate-reading-guide-db-impact.py`
        — a script phase 09 deleted. A warning that fires on correct output and
        names a nonexistent script trains operators to ignore the validator.
        """
        docs = _make_docs(tmp_path, tech_body="## Overview\n\nx\n")
        result = v.validate(docs)
        tech = [
            i for i in result["issues"] if "technical-spec" in i["location"]["file"]
        ]
        assert tech == [], tech

    def test_main_exit_zero_on_warn(self, tmp_path):
        docs = _make_docs(tmp_path, tech_body="## Overview\n\nx\n", screen_body="## Purpose\n\nx\n")
        rc = v.main(["--docs-root", str(docs), "--project-root", str(tmp_path)])
        assert rc == 0

    def test_main_exit_one_on_critical(self, tmp_path):
        # Screen-driven for the same reason as test_validate_fails_on_malformed_docs.
        docs = _make_docs(
            tmp_path, screen_body="## Source Walkthrough\n\n## Unresolved Questions\n"
        )
        rc = v.main(["--docs-root", str(docs), "--project-root", str(tmp_path)])
        assert rc == 1

    def test_summary_merge(self, tmp_path):
        docs = _make_docs(tmp_path)
        sp = tmp_path / "validation-summary.json"
        v.main(["--docs-root", str(docs), "--project-root", str(tmp_path),
                "--summary-out", str(sp)])
        data = json.loads(sp.read_text())
        assert "reading_guide_db_impact" in data["validators"]
