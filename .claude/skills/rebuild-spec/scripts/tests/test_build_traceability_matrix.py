"""Tests for build_traceability_matrix.py — FR-3 (phase-01, rebuild-spec 27.11.0).

Covers: full corpus (the optional TC### column present), sparse/core-only corpus (optional
column omitted, no broken links), the F###->ROUTE### join via route-list.md's Owner
column (incl. multi-owner), and the re-projection invariant (the builder never invents an
ID beyond what feature-list.md's own '**Related X**:' bullets already claim).
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

from build_traceability_matrix import build_rows, render, run  # noqa: E402


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _core_corpus(docs: Path) -> None:
    """Core-tier artifacts only — no features/, no test-cases.md."""
    _write(docs / "generated" / "feature-list.md", """# Feature List

## Feature Hierarchy

| Code | Name | Type | Language | Workspace | Priority |
|------|------|------|----------|-----------|----------|
| F001_Auth | Auth | ui | ruby | . | P0 |
| F002_Billing | Billing | ui | ruby | . | P0 |

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
- None

### F002_Billing: Billing

**Type**: ui

**Related Screens**:
- SCR002_Billing: Billing

**Related User Stories**:
- US002: ViewInvoice

**Related Background Logic**:
- None

**Related Permissions**:
- PERM001_ViewBilling: ViewBilling
""")
    _write(docs / "generated" / "route-list.md", """# Route List

### File: routes.rb

| Method | Path | Code | Owner F### | Handler | Middleware |
|--------|------|------|------------|---------|------------|
| GET | /login | ROUTE001 | F001 | AuthController@login | - |
| GET | /billing | ROUTE002 | F001, F002 | BillingController@index | auth |
""")


class TestFullCorpus:
    def test_route_scr_us_bl_perm_thread(self, tmp_path):
        docs = tmp_path / "docs"
        _core_corpus(docs)
        rows, tc_present = build_rows(docs)
        assert not tc_present
        by_f = {r["fcode"]: r for r in rows}
        assert by_f["F001"]["scr"] == ["SCR001"]
        assert by_f["F001"]["us"] == ["US001"]
        assert by_f["F001"]["bl"] == ["BL001"]
        assert by_f["F001"]["route"] == ["ROUTE001", "ROUTE002"]  # multi-owner join
        assert by_f["F001"]["perm"] == []
        assert by_f["F002"]["perm"] == ["PERM001"]
        assert by_f["F002"]["route"] == ["ROUTE002"]  # shared route, both owners see it

    def test_tc_column_present_and_scoped_per_feature(self, tmp_path):
        docs = tmp_path / "docs"
        _core_corpus(docs)
        _write(docs / "features" / "F001_Auth" / "functional-spec.md", "# spec\n")
        _write(docs / "features" / "F001_Auth" / "test-cases.md",
               "# Test Cases\n\n| Test-ID | Type | Given | When | Then | Traces-to |\n"
               "|---|---|---|---|---|---|\n| TC001 | UT | x | y | z | BR-001 |\n")
        rows, tc_present = build_rows(docs)
        assert tc_present
        by_f = {r["fcode"]: r for r in rows}
        assert by_f["F001"]["tc"] == ["TC001"]
        assert by_f["F002"]["tc"] == []  # no test-cases.md for F002 -> empty, not missing


class TestClosedColumnSet:
    """28.0.0 retired a lane from this matrix. The column set is CLOSED from here: the six
    core families, plus `TC###` when and only when the `--test-cases` pass produced files.

    Asserted as an exact list rather than as absences. An absence assertion only guards the
    one column someone thought to name; an exact header guards every column that could be
    revived by a half-removed branch or a stray artifact left in `generated/` by an older
    kit version (consumer corpora are not migrated).
    """

    CORE = ["F###", "SCR###", "US###", "BL###", "ROUTE###", "PERM###"]

    def _header(self, content: str) -> list[str]:
        line = next(ln for ln in content.splitlines() if ln.startswith("| F###"))
        return [c.strip() for c in line.strip().strip("|").split("|")]

    def test_core_corpus_header_is_exactly_the_six_core_families(self, tmp_path):
        docs = tmp_path / "docs"
        _core_corpus(docs)
        rows, tc_present = build_rows(docs)
        content = render("Proj", "core", rows, tc_present, "2026-01-01T00:00:00Z")
        assert self._header(content) == self.CORE

    def test_unrelated_generated_artifacts_add_no_column(self, tmp_path):
        """A retired-pass artifact left behind on disk must not re-open a column."""
        docs = tmp_path / "docs"
        _core_corpus(docs)
        for name in ("retired-artifact.md", "some-index.md", "legacy-list.md"):
            _write(docs / "generated" / name,
                   "# Retired\n\n## Index\n\n| Code | Name | BL Ref |\n|---|---|---|\n"
                   "| XYZ001 | Thing | BL001_SendWelcomeEmail |\n")
        rows, tc_present = build_rows(docs)
        content = render("Proj", "core", rows, tc_present, "2026-01-01T00:00:00Z")
        assert self._header(content) == self.CORE
        assert all(set(row) <= {"fcode", "scr", "us", "bl", "route", "perm"} for row in rows)

    def test_test_cases_pass_adds_exactly_one_column(self, tmp_path):
        docs = tmp_path / "docs"
        _core_corpus(docs)
        _write(docs / "features" / "F001_Auth" / "test-cases.md",
               "# Test Cases\n\n| Test-ID | Type | Given | When | Then | Traces-to |\n"
               "|---|---|---|---|---|---|\n| TC001 | UT | x | y | z | BR-001 |\n")
        rows, tc_present = build_rows(docs)
        content = render("Proj", "full", rows, tc_present, "2026-01-01T00:00:00Z")
        assert self._header(content) == self.CORE + ["TC###"]


class TestSparseCorpus:
    def test_core_only_omits_optional_columns_no_broken_links(self, tmp_path):
        docs = tmp_path / "docs"
        _core_corpus(docs)
        rows, tc_present = build_rows(docs)
        content = render("Proj", "core", rows, tc_present, "2026-01-01T00:00:00Z")
        assert "TC###" not in content
        assert "F001 |" in content and "SCR001" in content
        # every printed cell is either a real code or the explicit "none" marker
        assert "{" not in content  # no leftover template placeholders

    def test_run_writes_file(self, tmp_path):
        docs = tmp_path / "docs"
        _core_corpus(docs)
        rc = run(str(docs), "Proj", "core")
        assert rc == 0
        out = docs / "generated" / "traceability-matrix.md"
        assert out.is_file()
        assert "## Matrix" in out.read_text()
        assert "## Cross-Reference Validation" in out.read_text()

    def test_no_feature_list_is_a_noop_warn(self, tmp_path, capsys):
        docs = tmp_path / "docs"
        docs.mkdir(parents=True)
        rc = run(str(docs), "Proj", "core")
        assert rc == 0
        assert not (docs / "generated" / "traceability-matrix.md").is_file()
        assert "WARN" in capsys.readouterr().err


class TestReprojectionInvariant:
    def test_builder_never_invents_beyond_feature_list_bullets(self, tmp_path):
        """The matrix must never print an ID feature-list.md's own bullets didn't claim —
        it re-projects, it does not re-derive from screen-list.md/user-stories.md/etc."""
        docs = tmp_path / "docs"
        _core_corpus(docs)
        # A screen exists in screen-list.md that NO feature claims — must not leak in.
        _write(docs / "generated" / "screen-list.md", """# Screen List

## Screen Index

| Code | Name | Type | Components | Data Displayed |
|------|------|------|------------|----------------|
| SCR001_Login | Login | form | 1 | 1 |
| SCR999_Orphan | Orphan | form | 1 | 1 |
""")
        rows, _ = build_rows(docs)
        all_scr = {c for r in rows for c in r["scr"]}
        assert "SCR999" not in all_scr
        assert "SCR001" in all_scr
