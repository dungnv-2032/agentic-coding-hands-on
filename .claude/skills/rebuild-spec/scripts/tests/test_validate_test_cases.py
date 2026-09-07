"""Tests for validate_test_cases.py (Wave TC.2 gate).

Coverage: TC### regex + per-feature uniqueness, Type in {UT,IT,UAT}, Traces-to
presence + citation-source-family match (UT/IT vs UAT split), coverage-gap WARN
cross-ref against technical-spec.md, missing-file (sidecar) warning, CLI exit
codes + summary merge. Also: sidecar-not-gated regression (test-cases.md must
NOT be part of FEATURE_FILES / the promotion gate) — F1/F15 guardrail.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from validate_test_cases import validate, main, CODE_FAMILY_RE  # noqa: E402
from _slug_lib import FEATURE_FILES  # noqa: E402

VALID_TEST_CASES = """\
# Test Cases — F001_Login

## Test Cases

| Test-ID | Type (UT|IT|UAT) | Given | When | Then | Traces-to |
|---------|---------------------|-------|------|------|-----------|
| TC001 | UT | invalid password | user submits login form | error shown | `BR-001` |
| TC002 | IT | valid credentials | user submits login form | session created | `app/auth/session.rb:22` |
| TC003 | UAT | user on login page | user enters valid credentials and submits | dashboard is shown | functional-spec.md § User Journey step 2 |

## Coverage Notes

- `SM-001` — [NO_TEST_CASE] pure internal state, nothing user-observable to assert.
"""

# v27.0.0 (audience split): block headings use the canonical trailing-tag form
# (`### {plain sentence} (BR-001)`), not the retired anchored-slug form
# (`### BR-001_Slug`) — see _spec_block_lib.py.
TECH_SPEC_WITH_CODES = """\
# F001_Login

## Cross-Cutting Logic

### Business Rules

### Password is required (BR-001)

Password is required.

### Session state lifecycle (SM-001)

State machine.
"""


def _write(tmp_path: Path, rel: str, content: str) -> Path:
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


class TestValidate:
    def test_valid_test_cases_passes(self, tmp_path):
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/test-cases.md", VALID_TEST_CASES)
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/technical-spec.md", TECH_SPEC_WITH_CODES)
        result = validate(tmp_path / "plans/p1", tmp_path, None)
        issues = result["specs"]["F001_Login"]["issues"]
        assert not any(i["severity"] == "critical" for i in issues), issues
        assert not any(i["rule_id"] == "TestCases.coverage_gap" for i in issues)

    def test_missing_file_is_warning_not_critical(self, tmp_path):
        (tmp_path / "plans/p1/artifacts/features/F002_Empty").mkdir(parents=True)
        result = validate(tmp_path / "plans/p1", tmp_path, None)
        issues = result["specs"]["F002_Empty"]["issues"]
        assert issues[0]["rule_id"] == "TestCases.file_missing"
        assert issues[0]["severity"] == "warning"

    def test_bad_code_format_is_critical(self, tmp_path):
        bad = VALID_TEST_CASES.replace("TC001", "TC1")
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/test-cases.md", bad)
        result = validate(tmp_path / "plans/p1", tmp_path, None)
        issues = result["specs"]["F001_Login"]["issues"]
        assert any(i["rule_id"] == "TestCases.code_format" and i["severity"] == "critical" for i in issues)

    def test_duplicate_tc_id_is_critical(self, tmp_path):
        dup = VALID_TEST_CASES.replace("TC002", "TC001")
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/test-cases.md", dup)
        result = validate(tmp_path / "plans/p1", tmp_path, None)
        issues = result["specs"]["F001_Login"]["issues"]
        assert any(i["rule_id"] == "TestCases.no_dup_tc" for i in issues)

    def test_invalid_type_is_critical(self, tmp_path):
        bad = VALID_TEST_CASES.replace("| UT |", "| E2E |")
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/test-cases.md", bad)
        result = validate(tmp_path / "plans/p1", tmp_path, None)
        issues = result["specs"]["F001_Login"]["issues"]
        assert any(i["rule_id"] == "TestCases.type_invalid" for i in issues)

    def test_uat_row_citing_bare_code_is_mismatch(self, tmp_path):
        bad = VALID_TEST_CASES.replace(
            "functional-spec.md § User Journey step 2", "`BR-002`"
        )
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/test-cases.md", bad)
        result = validate(tmp_path / "plans/p1", tmp_path, None)
        issues = result["specs"]["F001_Login"]["issues"]
        assert any(i["rule_id"] == "TestCases.citation_source_mismatch" for i in issues)

    def test_ut_row_citing_functional_spec_now_passes(self, tmp_path):
        # v27.0.0: edge-cases.md merged into functional-spec.md — a UT/IT row citing
        # functional-spec.md (formerly a UAT-only doc family) is now a VALID citation, not a
        # mismatch, since both UAT and UT/IT citation families point at the same merged file.
        merged = VALID_TEST_CASES.replace("`BR-001`", "functional-spec.md § something")
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/test-cases.md", merged)
        result = validate(tmp_path / "plans/p1", tmp_path, None)
        issues = result["specs"]["F001_Login"]["issues"]
        assert not any(i["rule_id"] == "TestCases.citation_source_mismatch" for i in issues)

    def test_ut_row_citing_plain_prose_is_still_mismatch(self, tmp_path):
        # A UT/IT row citing prose that is neither a code, a file:line, nor functional-spec.md
        # is still a genuine mismatch — the citation-family gate isn't a no-op after the merge.
        bad = VALID_TEST_CASES.replace("`BR-001`", "some unrelated free-text note")
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/test-cases.md", bad)
        result = validate(tmp_path / "plans/p1", tmp_path, None)
        issues = result["specs"]["F001_Login"]["issues"]
        assert any(i["rule_id"] == "TestCases.citation_source_mismatch" for i in issues)

    def test_empty_traces_to_is_critical(self, tmp_path):
        bad = VALID_TEST_CASES.replace("`BR-001`", "")
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/test-cases.md", bad)
        result = validate(tmp_path / "plans/p1", tmp_path, None)
        issues = result["specs"]["F001_Login"]["issues"]
        assert any(i["rule_id"] == "TestCases.traces_missing" for i in issues)

    def test_coverage_gap_warns_on_untraced_code(self, tmp_path):
        # Remove the [NO_TEST_CASE] note for SM-001 → SM-001 becomes an uncovered gap.
        no_note = VALID_TEST_CASES.split("## Coverage Notes")[0]
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/test-cases.md", no_note)
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/technical-spec.md", TECH_SPEC_WITH_CODES)
        result = validate(tmp_path / "plans/p1", tmp_path, None)
        issues = result["specs"]["F001_Login"]["issues"]
        gap = next(i for i in issues if i["rule_id"] == "TestCases.coverage_gap")
        assert gap["severity"] == "warning"
        assert "SM-001" in gap["message"]

    def test_scoped_fcodes_filter(self, tmp_path):
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/test-cases.md", VALID_TEST_CASES)
        (tmp_path / "plans/p1/artifacts/features/F002_Other").mkdir(parents=True)
        result = validate(tmp_path / "plans/p1", tmp_path, ["F001_Login"])
        assert list(result["specs"].keys()) == ["F001_Login"]


class TestFileLinePathShape:
    """Minor fix: FILE_LINE_RE must require an actual path shape (`/` or `.<ext>:`), not
    accept bare `Note:1`-style tokens as a file:line citation."""

    def test_bare_note_reference_is_still_flagged(self, tmp_path):
        bad = VALID_TEST_CASES.replace("`app/auth/session.rb:22`", "Note:1")
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/test-cases.md", bad)
        result = validate(tmp_path / "plans/p1", tmp_path, None)
        issues = result["specs"]["F001_Login"]["issues"]
        assert any(i["rule_id"] == "TestCases.citation_source_mismatch" and "TC002" in i["message"]
                   for i in issues), issues

    def test_real_file_line_citation_still_passes(self, tmp_path):
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/test-cases.md", VALID_TEST_CASES)
        result = validate(tmp_path / "plans/p1", tmp_path, None)
        issues = result["specs"]["F001_Login"]["issues"]
        assert not any(i["rule_id"] == "TestCases.citation_source_mismatch" for i in issues)

    def test_functional_spec_reference_still_passes(self, tmp_path):
        # v27.0.0: edge-cases.md merged into functional-spec.md (§8 Edge Cases) — a UT/IT row
        # citing the merged file's edge-case section is still an accepted citation family.
        via_functional_spec = VALID_TEST_CASES.replace(
            "`app/auth/session.rb:22`", "functional-spec.md § EC-1"
        )
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/test-cases.md", via_functional_spec)
        result = validate(tmp_path / "plans/p1", tmp_path, None)
        issues = result["specs"]["F001_Login"]["issues"]
        assert not any(i["rule_id"] == "TestCases.citation_source_mismatch" for i in issues)


class TestFencedRowIgnored:
    """I1 regression: a fenced illustrative malformed row must not be parsed as a live
    test-case row (attack/t7_testcases_fence)."""

    def test_fenced_malformed_row_no_false_criticals(self, tmp_path):
        content = """\
# Test Cases

| Test-ID | Type | Given | When | Then | Traces-to |
|---------|------|-------|------|------|-----------|
| TC001 | UT | valid input | called | returns 200 | BR-001 |

Example of a malformed row we want authors to avoid (illustrative only, from a code review
comment found in the scanned repo):

```markdown
| bad-id | XX | x | y | z | nowhere |
```
"""
        tech_spec = "# Technical Spec\n\n### Something must hold (BR-001)\n\nBusiness rule text.\n"
        _write(tmp_path, "plans/p1/artifacts/features/F001_Test/test-cases.md", content)
        _write(tmp_path, "plans/p1/artifacts/features/F001_Test/technical-spec.md", tech_spec)
        result = validate(tmp_path / "plans/p1", tmp_path, None)
        issues = result["specs"]["F001_Test"]["issues"]
        assert not any(i["severity"] == "critical" for i in issues), issues
        assert not any("bad-id" in i["message"] for i in issues)


class TestMainCli:
    def test_exit_0_on_valid(self, tmp_path):
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/test-cases.md", VALID_TEST_CASES)
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/technical-spec.md", TECH_SPEC_WITH_CODES)
        rc = main(["--plan-dir", str(tmp_path / "plans/p1"), "--project-root", str(tmp_path)])
        assert rc == 0

    def test_exit_1_on_critical(self, tmp_path):
        bad = VALID_TEST_CASES.replace("TC001", "TC1")
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/test-cases.md", bad)
        rc = main(["--plan-dir", str(tmp_path / "plans/p1"), "--project-root", str(tmp_path)])
        assert rc == 1

    def test_summary_out_merges(self, tmp_path):
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/test-cases.md", VALID_TEST_CASES)
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/technical-spec.md", TECH_SPEC_WITH_CODES)
        summary_out = tmp_path / "plans/p1/artifacts/validation/tc-validation-summary.json"
        rc = main([
            "--plan-dir", str(tmp_path / "plans/p1"),
            "--project-root", str(tmp_path),
            "--summary-out", str(summary_out),
        ])
        assert rc == 0
        data = json.loads(summary_out.read_text())
        assert "specs" in data["validators"]
        assert data["overall_status"] in ("PASS", "WARN")


class TestNewFormHeadingCoverageGapRegression:
    """v27.0.0 silent-pass regression guard: the coverage-gap WARN cross-ref (_known_codes) must
    detect BR/SM codes from the CANONICAL trailing-tag heading form (`### {sentence} (BR-001)`),
    not just the retired anchored-slug form (`### BR-001_Slug`). Before the Phase 04 fix, the old
    local regex (`^###\\s+(BR|SM)-(\\d{3})_`) matched ONLY the retired form — a technical-spec.md
    written entirely in the new form produced ZERO known codes, so the coverage-gap check had
    nothing to compare against and silently reported no gaps at all, even when every code was
    genuinely untraced. This test uses ONLY new-form headings (no retired form anywhere) so it
    fails again immediately if that regression is reintroduced."""

    NEW_FORM_TECH_SPEC = """\
# F002_Checkout

## Cross-Cutting Logic

### Business Rules

### Cart must have at least one item (BR-001)

Rule text.

### Checkout submission lifecycle (SM-001)

State machine.

#### Decide shipping method automatically (DEC-001)

Decision text.
"""

    NO_TRACING_TEST_CASES = """\
# Test Cases — F002_Checkout

## Test Cases

| Test-ID | Type (UT|IT|UAT) | Given | When | Then | Traces-to |
|---------|---------------------|-------|------|------|-----------|
| TC001 | UT | n/a | n/a | n/a | `app/checkout/session.rb:10` |
"""

    def test_new_form_br_sm_dec_codes_are_detected_as_known(self, tmp_path):
        _write(tmp_path, "plans/p1/artifacts/features/F002_Checkout/test-cases.md",
               self.NO_TRACING_TEST_CASES)
        _write(tmp_path, "plans/p1/artifacts/features/F002_Checkout/technical-spec.md",
               self.NEW_FORM_TECH_SPEC)
        result = validate(tmp_path / "plans/p1", tmp_path, None)
        issues = result["specs"]["F002_Checkout"]["issues"]
        gap = next((i for i in issues if i["rule_id"] == "TestCases.coverage_gap"), None)
        assert gap is not None, (
            "coverage_gap WARN did not fire for untraced new-form BR/SM/DEC codes — "
            "this is the exact silent-pass regression this test guards against"
        )
        assert gap["severity"] == "warning"
        for code in ("BR-001", "SM-001", "DEC-001"):
            assert code in gap["message"], gap["message"]


class TestSidecarNotGated:
    """F1/F15 regression: test-cases.md must NEVER join the mandatory tuple."""

    def test_not_in_feature_files(self):
        # v27.0.0 (audience split): FEATURE_FILES is now 2 files (technical-spec.md,
        # functional-spec.md) — business-context.md/screens.md/edge-cases.md retired.
        assert "test-cases.md" not in FEATURE_FILES
        assert FEATURE_FILES == ("technical-spec.md", "functional-spec.md")


class TestCodeFamilyRegexBoundary:
    """Phase 03 (capability-map plan) — CODE_FAMILY_RE's trailing `\\b` never matched
    past a slugged code's `_` (BR-001_Slug), because `_` is a word char and `\\b` needs a
    word/non-word transition right where the 3 digits end. `(?!\\d)` ("not followed by
    another digit") is the correct end-of-code anchor: it accepts the slug and still
    rejects a genuinely longer numeric run (BR-0012)."""

    def test_matches_bare_and_slugged_forms(self):
        assert CODE_FAMILY_RE.search("BR-001")
        assert CODE_FAMILY_RE.search("BR-001_Slug")
        assert CODE_FAMILY_RE.search("DISC-042_Thing")

    def test_does_not_match_four_digit_code(self):
        # Reaches: (?!\d) lookahead rejects BR-0012 as a valid 3-digit BR-001 match.
        assert CODE_FAMILY_RE.search("BR-0012") is None


class TestSluggedCitationCoverageGap:
    """Phase 03 — the coverage-gap set-builder (`_check_one`'s `traced`/`noted` sets) scans
    raw text with CODE_FAMILY_RE. Because under-matching can only SHRINK `traced`/`noted`,
    the pre-fix regex could only ever make `gaps = known - traced - noted` LARGER, never
    smaller — so the observable defect is a FALSE coverage-gap warning on a code that IS
    genuinely traced, only via its slugged form. This is the mandatory RED/GREEN proof:
    the branch that recognizes a slugged citation as coverage was dead pre-fix (BR-001
    wrongly reported as an untested gap despite TC001 citing `BR-001_Slug`), and live
    post-fix (BR-001 correctly drops out of the gap set)."""

    SLUGGED_CITATION_TEST_CASES = """\
# Test Cases — F001_Login

## Test Cases

| Test-ID | Type (UT|IT|UAT) | Given | When | Then | Traces-to |
|---------|---------------------|-------|------|------|-----------|
| TC001 | UT | invalid password | user submits login form | error shown | `BR-001_Slug` |

## Coverage Notes

- `SM-001` — [NO_TEST_CASE] pure internal state, nothing user-observable to assert.
"""

    def test_slugged_citation_recognized_as_coverage_not_a_gap(self, tmp_path):
        # Reaches: CODE_FAMILY_RE matches inside "BR-001_Slug", adding BR-001 to `traced`
        # (validate_test_cases.py's _check_one), so BR-001 must NOT appear in the
        # coverage_gap message. Pre-fix this assertion is FALSE (BR-001 wrongly listed as
        # a gap) — see the implementer report for the observed RED output.
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/test-cases.md",
               self.SLUGGED_CITATION_TEST_CASES)
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/technical-spec.md",
               TECH_SPEC_WITH_CODES)
        result = validate(tmp_path / "plans/p1", tmp_path, None)
        issues = result["specs"]["F001_Login"]["issues"]
        gap = next((i for i in issues if i["rule_id"] == "TestCases.coverage_gap"), None)
        assert gap is None or "BR-001" not in gap["message"], (
            f"BR-001 wrongly reported as an untested gap despite being traced via its "
            f"slugged citation form 'BR-001_Slug' — issues: {issues}"
        )

    def test_slugged_citation_is_not_a_family_mismatch(self, tmp_path):
        # Companion branch: the same under-match also made `_citation_family_ok` reject a
        # valid slugged citation outright, raising a spurious critical for TC001.
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/test-cases.md",
               self.SLUGGED_CITATION_TEST_CASES)
        _write(tmp_path, "plans/p1/artifacts/features/F001_Login/technical-spec.md",
               TECH_SPEC_WITH_CODES)
        result = validate(tmp_path / "plans/p1", tmp_path, None)
        issues = result["specs"]["F001_Login"]["issues"]
        assert not any(i["rule_id"] == "TestCases.citation_source_mismatch" for i in issues), issues
