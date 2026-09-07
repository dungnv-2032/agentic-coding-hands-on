"""Tests for validate_traceability_matrix.py — FR-3/FR-6 (phase-01, rebuild-spec 27.11.0).

WARN-first (NFR): this validator must never fail a pass. Covers the happy path (PASS,
zero issues), a genuine tripped WARN on a fabricated/unresolved ID (the negative-test
discipline this repo has been burned by skipping before — see
negative-tests-must-reach-the-branch), the FR-6 crosswalk-staleness fallback firing then
clearing after a README regeneration, and the missing-matrix degradation.

Also covers, as of 28.0.0 (a retired lane narrowed this matrix, and a narrowing edit is
exactly the direction a silent PASS hides in):
  * template <-> implementation agreement — the SHIPPED template's own worked example must
    validate clean and its column set must equal what `render()` emits (27.14.3 lesson);
  * the summary-JSON negative probe — a broken SURVIVING lane must still surface as
    `overall_status == "WARN"`, asserted on output because this validator returns 0 by NFR.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

TEMPLATE = SCRIPTS.parent / "templates" / "traceability-matrix-template.md"

from build_navigation import run as run_navigation  # noqa: E402
from build_traceability_matrix import build_rows, render, run as run_matrix  # noqa: E402
from validate_traceability_matrix import (  # noqa: E402
    check_crosswalk_staleness, main as validate_main, validate_reprojection,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _full_corpus(docs: Path) -> None:
    _write(docs / "system" / "architecture.md", "# Architecture\n")
    _write(docs / "generated" / "screen-list.md", """# Screen List

## Screen Index

| Code | Name | Type | Components | Data Displayed |
|------|------|------|------------|----------------|
| SCR001_Login | Login | form | 1 | 1 |
""")
    _write(docs / "generated" / "user-stories.md", """# User Stories

## User Story Index

| Code | Title | Type | Priority | Screens |
|------|-------|------|----------|---------|
| US001 | Login | ui | P0 | SCR001 |
""")
    _write(docs / "generated" / "behavior-logic.md", """# Behavior Logic

## BL001_SendWelcomeEmail

**Type**: queue-worker
""")
    _write(docs / "generated" / "permissions-matrix.md", """# Permissions Matrix

## Permissions Index

| Code | Name | Type | Enforced At |
|------|------|------|-------------|
| PERM001_ViewBilling | ViewBilling | role-based | route-guard |
""")
    _write(docs / "generated" / "route-list.md", """# Route List

### File: routes.rb

| Method | Path | Code | Owner F### | Handler | Middleware |
|--------|------|------|------------|---------|------------|
| GET | /login | ROUTE001 | F001 | AuthController@login | - |
""")
    _write(docs / "generated" / "feature-list.md", """# Feature List

## Feature Hierarchy

| Code | Name | Type | Language | Workspace | Priority |
|------|------|------|----------|-----------|----------|
| F001_Auth | Auth | ui | ruby | . | P0 |

## Feature Details

### F001_Auth: Auth

**Type**: ui

**Related Screens**:
- SCR001_Login: Login

**Related User Stories**:
- US001: Login

**Related Background Logic**:
- BL001_SendWelcomeEmail: SendWelcomeEmail

**Related Permissions**:
- PERM001_ViewBilling: ViewBilling
""")


class TestHappyPath:
    def test_valid_matrix_passes_clean(self, tmp_path):
        docs = tmp_path / "docs"
        _full_corpus(docs)
        assert run_matrix(str(docs), "Proj", "full") == 0
        issues = validate_reprojection(docs)
        assert issues == []


class TestGenuineWarnTrip:
    def test_fabricated_id_trips_scr_unresolved_warn(self, tmp_path):
        """Negative test that actually reaches the failing branch: inject an ID the
        matrix prints but screen-list.md never registered."""
        docs = tmp_path / "docs"
        _full_corpus(docs)
        run_matrix(str(docs), "Proj", "full")
        matrix_path = docs / "generated" / "traceability-matrix.md"
        text = matrix_path.read_text(encoding="utf-8")
        assert "| F001 | SCR001 |" in text
        matrix_path.write_text(text.replace("| F001 | SCR001 |", "| F001 | SCR001, SCR999 |"),
                               encoding="utf-8")
        issues = validate_reprojection(docs)
        rule_ids = {i["rule_id"] for i in issues}
        assert "TraceabilityMatrix.scr_unresolved" in rule_ids
        assert all(i["severity"] == "warning" for i in issues)  # WARN-first, never critical

    def test_tc_id_not_in_that_features_own_file_warns(self, tmp_path):
        docs = tmp_path / "docs"
        _full_corpus(docs)
        _write(docs / "features" / "F001_Auth" / "functional-spec.md", "# spec\n")
        _write(docs / "features" / "F001_Auth" / "test-cases.md",
               "# Test Cases\n\n| Test-ID | Type | Given | When | Then | Traces-to |\n"
               "|---|---|---|---|---|---|\n| TC001 | UT | x | y | z | BR-001 |\n")
        run_matrix(str(docs), "Proj", "full")
        matrix_path = docs / "generated" / "traceability-matrix.md"
        text = matrix_path.read_text(encoding="utf-8")
        # fabricate a TC### this feature's own test-cases.md never declared
        assert "TC001" in text
        matrix_path.write_text(text.replace("TC001", "TC001, TC999"), encoding="utf-8")
        issues = validate_reprojection(docs)
        assert any(i["rule_id"] == "TraceabilityMatrix.tc_unresolved" for i in issues)


class TestEmptyMatrixOverPopulatedCorpus:
    """The silent-absence case. A header-only matrix over a corpus that HAS features must
    WARN, not pass clean — an empty matrix reads as 'this project has no traceable
    features', which is worse than no matrix at all.

    Real cause reproduced here: the row set is parsed from feature-list.md's hierarchy
    table via FEATURE_LIST_ROW_RE, which requires a leading `| F###_Slug |` cell. Degrade
    that one cell to a bare `| F### |` and the feature count drops to zero while
    '## Feature Details' still describes every feature — so the matrix renders empty.
    Before TraceabilityMatrix.empty_but_features_exist, this validated PASS/0 warnings.
    """

    def _degrade_hierarchy_rows(self, docs: Path) -> None:
        fl = docs / "generated" / "feature-list.md"
        text = fl.read_text(encoding="utf-8")
        assert "| F001_Auth |" in text, "fixture shape changed — hierarchy row not found"
        fl.write_text(text.replace("| F001_Auth |", "| F001 |", 1), encoding="utf-8")

    def test_empty_matrix_over_populated_corpus_warns(self, tmp_path):
        docs = tmp_path / "docs"
        _full_corpus(docs)
        self._degrade_hierarchy_rows(docs)
        assert run_matrix(str(docs), "Proj", "full") == 0

        matrix = (docs / "generated" / "traceability-matrix.md").read_text(encoding="utf-8")
        data_rows = [
            ln for ln in matrix.splitlines()
            if ln.startswith("| F") and "F###" not in ln
        ]
        assert data_rows == [], "precondition: the matrix must actually be empty here"

        issues = validate_reprojection(docs)
        rule_ids = {i["rule_id"] for i in issues}
        assert "TraceabilityMatrix.empty_but_features_exist" in rule_ids, (
            f"empty matrix over a populated corpus must WARN; got {rule_ids}"
        )
        assert all(i["severity"] == "warning" for i in issues), "must stay WARN-first"

    def test_warn_clears_once_rows_render(self, tmp_path):
        """Same corpus, hierarchy row intact — the WARN must NOT fire. Proves the check
        discriminates, rather than firing unconditionally."""
        docs = tmp_path / "docs"
        _full_corpus(docs)
        assert run_matrix(str(docs), "Proj", "full") == 0
        rule_ids = {i["rule_id"] for i in validate_reprojection(docs)}
        assert "TraceabilityMatrix.empty_but_features_exist" not in rule_ids

    def test_empty_matrix_over_empty_corpus_does_not_warn(self, tmp_path):
        """A genuinely feature-less corpus is honestly empty — no WARN, no false positive."""
        docs = tmp_path / "docs"
        _full_corpus(docs)
        _write(docs / "generated" / "feature-list.md", "# Feature List\n\n## Feature Details\n")
        assert run_matrix(str(docs), "Proj", "full") == 0
        rule_ids = {i["rule_id"] for i in validate_reprojection(docs)}
        assert "TraceabilityMatrix.empty_but_features_exist" not in rule_ids


class TestRetiredColumnIsNotSilentlySkipped:
    """A column the validator does not know about must WARN, not be skipped.

    `validate_reprojection` walks `_COL_FAMILY` (the registry), not the matrix header. When
    28.0.0 retired the JOB### lane, a consumer's already-generated matrix kept the column while
    the registry entry that made anyone look at it went away — checked by nothing, reported by
    nothing. No corpus migration ships, so the population still carrying the column is exactly
    the population that lost the check. This guards the NEXT retired column too.
    """

    def test_unknown_column_warns(self, tmp_path):
        docs = tmp_path / "docs"
        _full_corpus(docs)
        run_matrix(str(docs), "Proj", "full")
        matrix_path = docs / "generated" / "traceability-matrix.md"
        text = matrix_path.read_text(encoding="utf-8")
        # Re-introduce a retired column exactly as a stale consumer corpus would carry it.
        text = text.replace("| F### |", "| F### | JOB### |", 1)
        text = text.replace("| F001 |", "| F001 | JOB999 |", 1)
        matrix_path.write_text(text, encoding="utf-8")
        issues = validate_reprojection(docs)
        rule_ids = {i["rule_id"] for i in issues}
        assert "TraceabilityMatrix.unknown_column" in rule_ids
        assert all(i["severity"] == "warning" for i in issues)  # WARN-first, never critical

    def test_known_columns_do_not_warn(self, tmp_path):
        """The discriminator — without it the assertion above would also pass against a
        validator that flagged every column unconditionally."""
        docs = tmp_path / "docs"
        _full_corpus(docs)
        run_matrix(str(docs), "Proj", "full")
        issues = validate_reprojection(docs)
        assert [i for i in issues if i["rule_id"] == "TraceabilityMatrix.unknown_column"] == []


class TestMissingMatrix:
    def test_missing_matrix_warns_not_fails(self, tmp_path):
        docs = tmp_path / "docs"
        _full_corpus(docs)  # matrix never built
        issues = validate_reprojection(docs)
        assert len(issues) == 1
        assert issues[0]["rule_id"] == "TraceabilityMatrix.missing"
        assert issues[0]["severity"] == "warning"


_API_CONTRACTS = """# API Contracts

## Contract Index

| Endpoint | Method | Request | Response |
|----------|--------|---------|----------|
| /login | POST | credentials | session |
"""


class TestCrosswalkStaleness:
    def test_present_api_contracts_unlisted_in_readme_warns(self, tmp_path):
        docs = tmp_path / "docs"
        _full_corpus(docs)
        run_navigation(str(docs), pass_complete=False)  # README with no api-contracts.md yet
        _write(docs / "generated" / "api-contracts.md", _API_CONTRACTS)
        issues = check_crosswalk_staleness(docs)
        assert any(i["rule_id"] == "TraceabilityMatrix.crosswalk_stale" for i in issues)

    def test_clears_after_readme_regenerated(self, tmp_path):
        docs = tmp_path / "docs"
        _full_corpus(docs)
        run_navigation(str(docs), pass_complete=False)
        _write(docs / "generated" / "api-contracts.md", _API_CONTRACTS)
        assert check_crosswalk_staleness(docs)  # stale before rerun
        run_navigation(str(docs), pass_complete=False)  # rerun picks up api-contracts.md
        assert check_crosswalk_staleness(docs) == []

    def test_no_readme_yields_no_issues(self, tmp_path):
        docs = tmp_path / "docs"
        _full_corpus(docs)  # no README.md written at all
        assert check_crosswalk_staleness(docs) == []


# --- Template <-> implementation agreement -----------------------------------------
# 27.14.3 lesson: this repo's most common defect is a template teaching a shape its own
# validator rejects. These two tests read the SHIPPED template file, so a column added to
# or removed from either side without the other reds here.

_TEMPLATE_SUBS = {
    "{PROJECT_NAME}": "Proj",
    "{DATE}": "2026-01-01T00:00:00Z",
    "{SCOPE}": "full",
    "{F001_CODE}": "F001",
    "{F001_SCR_LIST}": "SCR001",
    "{F001_US_LIST}": "US001",
    "{F001_BL_LIST}": "BL001",
    "{F001_ROUTE_LIST}": "ROUTE001",
    "{F001_PERM_LIST}": "PERM001",
    "{F001_TC_LIST}": "TC001",
    "{F002_CODE}": "F002",
    "{F002_US_LIST}": "US002",
    "{F002_ROUTE_LIST}": "ROUTE002",
    "{F002_PERM_LIST}": "PERM002",
}


def _matrix_table_lines(text: str) -> list[str]:
    """The '## Matrix' table's `|`-prefixed run, verbatim."""
    lines = text.splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.strip().lower() == "## matrix")
    out: list[str] = []
    for ln in lines[start + 1:]:
        s = ln.strip()
        if s.startswith("|"):
            out.append(s)
        elif out:
            break
    return out


def _template_corpus(docs: Path) -> None:
    """A corpus in which every ID the template's worked example prints genuinely exists."""
    _full_corpus(docs)
    _write(docs / "generated" / "user-stories.md", """# User Stories

## User Story Index

| Code | Title | Type | Priority | Screens |
|------|-------|------|----------|---------|
| US001 | Login | ui | P0 | SCR001 |
| US002 | ViewInvoice | ui | P0 | — |
""")
    _write(docs / "generated" / "permissions-matrix.md", """# Permissions Matrix

## Permissions Index

| Code | Name | Type | Enforced At |
|------|------|------|-------------|
| PERM001_ViewBilling | ViewBilling | role-based | route-guard |
| PERM002_ManageBilling | ManageBilling | role-based | route-guard |
""")
    _write(docs / "generated" / "route-list.md", """# Route List

### File: routes.rb

| Method | Path | Code | Owner F### | Handler | Middleware |
|--------|------|------|------------|---------|------------|
| GET | /login | ROUTE001 | F001 | AuthController@login | - |
| GET | /billing | ROUTE002 | F002 | BillingController@index | auth |
""")
    fl = docs / "generated" / "feature-list.md"
    text = fl.read_text(encoding="utf-8")
    assert "| F001_Auth | Auth | ui | ruby | . | P0 |" in text, "fixture shape changed"
    fl.write_text(
        text.replace("| F001_Auth | Auth | ui | ruby | . | P0 |",
                     "| F001_Auth | Auth | ui | ruby | . | P0 |\n"
                     "| F002_Billing | Billing | ui | ruby | . | P0 |")
        + """
### F002_Billing: Billing

**Type**: ui

**Related User Stories**:
- US002: ViewInvoice

**Related Permissions**:
- PERM002_ManageBilling: ManageBilling
""",
        encoding="utf-8")
    _write(docs / "features" / "F001_Auth" / "functional-spec.md", "# spec\n")
    _write(docs / "features" / "F001_Auth" / "test-cases.md",
           "# Test Cases\n\n| Test-ID | Type | Given | When | Then | Traces-to |\n"
           "|---|---|---|---|---|---|\n| TC001 | UT | x | y | z | BR-001 |\n")


class TestTemplateAgreesWithImplementation:
    def test_template_worked_example_validates_clean(self, tmp_path):
        """The template's OWN worked example, instantiated over a corpus that backs every
        ID it prints, must produce ZERO issues from the shipped validator."""
        docs = tmp_path / "docs"
        _template_corpus(docs)

        rendered = TEMPLATE.read_text(encoding="utf-8")
        for placeholder, value in _TEMPLATE_SUBS.items():
            rendered = rendered.replace(placeholder, value)
        table = "\n".join(_matrix_table_lines(rendered))
        assert "{" not in table, (
            f"the template's worked example still carries an unsubstituted placeholder — a "
            f"column was added to the template without a corpus behind it: {table}")

        _write(docs / "generated" / "traceability-matrix.md", rendered)
        assert validate_reprojection(docs) == []

    def test_template_matrix_header_matches_builder_output(self, tmp_path):
        """Template column set == what build_traceability_matrix.render() actually emits."""
        docs = tmp_path / "docs"
        _template_corpus(docs)
        rows, tc_present = build_rows(docs)
        assert tc_present
        built = render("Proj", "full", rows, tc_present, "2026-01-01T00:00:00Z")
        assert _matrix_table_lines(built)[0] == _matrix_table_lines(
            TEMPLATE.read_text(encoding="utf-8"))[0]


class TestSummaryOutNegativeProbe:
    """The lane count just dropped. A green suite after a column removal is NOT evidence
    that the validator still flags anything — only a deliberately-broken input is.

    Asserted on the emitted summary JSON, never on the exit code: this validator is
    WARN-first by NFR and returns 0 unconditionally (`validate_traceability_matrix.py:206`).
    """

    def _run_main(self, docs: Path, summary: Path, monkeypatch) -> int:
        monkeypatch.setattr(sys, "argv", [
            "validate_traceability_matrix.py",
            "--docs-root", str(docs), "--summary-out", str(summary),
        ])
        return validate_main()

    def test_broken_surviving_lane_yields_overall_status_warn(self, tmp_path, monkeypatch,
                                                              capsys):
        docs = tmp_path / "docs"
        _full_corpus(docs)
        assert run_matrix(str(docs), "Proj", "full") == 0
        matrix_path = docs / "generated" / "traceability-matrix.md"
        text = matrix_path.read_text(encoding="utf-8")
        assert "| F001 | SCR001 |" in text, "fixture shape changed"
        # SCR999 is printed in the matrix but was never registered in screen-list.md —
        # a violation of the SCR lane's re-projection invariant, which SURVIVES this phase.
        matrix_path.write_text(text.replace("| F001 | SCR001 |", "| F001 | SCR001, SCR999 |"),
                               encoding="utf-8")

        summary = tmp_path / "validation-summary.json"
        assert self._run_main(docs, summary, monkeypatch) == 0  # NFR: exit 0 always
        capsys.readouterr()

        result = json.loads(summary.read_text(encoding="utf-8"))
        assert result["overall_status"] == "WARN", result["overall_status"]
        slot = result["validators"]["traceability_matrix"]
        assert any(i["rule_id"] == "TraceabilityMatrix.scr_unresolved" for i in slot["issues"]), \
            [i["rule_id"] for i in slot["issues"]]

    def test_intact_corpus_yields_overall_status_pass(self, tmp_path, monkeypatch, capsys):
        """The discriminator: same path, unbroken input — must NOT WARN. Without this the
        probe above would still pass if the validator WARNed unconditionally."""
        docs = tmp_path / "docs"
        _full_corpus(docs)
        assert run_matrix(str(docs), "Proj", "full") == 0

        summary = tmp_path / "validation-summary.json"
        assert self._run_main(docs, summary, monkeypatch) == 0
        capsys.readouterr()

        result = json.loads(summary.read_text(encoding="utf-8"))
        assert result["overall_status"] == "PASS", result
