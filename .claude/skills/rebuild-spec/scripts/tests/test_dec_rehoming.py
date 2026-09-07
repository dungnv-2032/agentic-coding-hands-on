"""Phase 03b — regression coverage for C13 (the DEC-block silent-gate defect).

C13 proved, by running the real validator, that the action-thread reshape
silently killed `FeatureSpec.dec_blocks_well_formed`/`dec_lazy_na` via TWO
independent causes:

  P1 — `_check_dec_blocks`'s search bound (`b_cap`) was keyed on the exact OLD
       § 4 title ('## 4. Technical Behavior by Capability'). Retitling § 4 to
       '## 4. Shared Foundation' (the action-thread shape) made `_bounds`
       return `None`, and the block-form scan died before examining anything
       — PROVEN with the SAME malformed DEC block, only the § 4 heading
       differing, producing 4 findings under the old heading and ZERO under
       the new one.
  P2 — even with P1 fixed, `DEC_BLOCK_RE` (an H4 heading regex) matches
       nothing under the new shape: a DEC is now a 5-column table row inside
       the claiming action's own **Rule** rung (`## 3. Actions`), not a
       heading at all.

This file proves both are fixed and stay fixed:
  - `TestP1SameMalformedDecBothHeadings` reproduces C13's own proof exactly —
    same malformed H4 block, only the § 4 title changes — and asserts the
    SAME rule_id fires under both.
  - `TestP2RowFormWellFormed` / `TestP2RowForm*` prove the NEW row
    representation is validated for the same substance the H4 block was:
    every negative test starts from a fixture PROVEN clean (asserted `== []`
    before the mutation is even discussed) so a single, named mutation is
    what turns on a single, named finding — never a bare non-zero exit.
  - `TestP2Degradation` proves the D4 WARN-first window (`_thread_sev_msg`)
    applies to the new row checks exactly like it does to every other
    action-thread check.
  - `TestBoundsByNumber` unit-tests the new `_bounds_by_number` helper in
    isolation (the mechanism P1's fix relies on).
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

import validate_feature_spec as vfs  # noqa: E402

_DEC_PREFIX = "FeatureSpec.dec_"


def _dec_rule_ids(issues: list[dict]) -> list[str]:
    return [i["rule_id"] for i in issues if i["rule_id"].startswith(_DEC_PREFIX)]


def _dec_issues(issues: list[dict]) -> list[dict]:
    return [i for i in issues if i["rule_id"].startswith(_DEC_PREFIX)]


def _write_spec(tmp_path: Path, tech_text: str) -> Path:
    feat_dir = tmp_path / "docs" / "features" / "F901_Test"
    feat_dir.mkdir(parents=True)
    spec = feat_dir / "technical-spec.md"
    spec.write_text(tech_text, encoding="utf-8")
    return spec


# ---------------------------------------------------------------------------
# P1 — same malformed H4 DEC block, only the § 4 heading title differs.
# Reproduces C13's own proof table verbatim (old: 4 findings; new: silent).
# ---------------------------------------------------------------------------

_OLD_HEADING = "## 4. Technical Behavior by Capability"
_NEW_HEADING = "## 4. Shared Foundation"

_MALFORMED_H4_BLOCK_TEMPLATE = """\
# F901_Test — DEC Rehoming P1 Probe

{heading}

### 4.1 Login

**Decision Logic**

#### Redirect after login attempt (DEC-001)

<!-- subtype field intentionally omitted -->
**Triggers in:** SCR001_LoginForm — form submit event
**Involved entities:** User.status
**Source:** app/controllers/login_controller.rb:10-20
"""

_WELL_FORMED_H4_BLOCK_TEMPLATE = """\
# F901_Test — DEC Rehoming P1 Probe (well-formed)

{heading}

### 4.1 Login

**Decision Logic**

#### Redirect after login attempt (DEC-001)

**subtype:** render
**Triggers in:** SCR001_LoginForm — form submit event
**Involved entities:** User.status
**Source:** app/controllers/login_controller.rb:10-20
"""


class TestP1SameMalformedDecBothHeadings:
    def test_malformed_block_fires_under_old_heading(self, tmp_path):
        spec = _write_spec(tmp_path, _MALFORMED_H4_BLOCK_TEMPLATE.format(heading=_OLD_HEADING))
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert _dec_rule_ids(issues) == ["FeatureSpec.dec_blocks_well_formed"], _dec_issues(issues)
        assert _dec_issues(issues)[0]["severity"] == "critical"

    def test_same_malformed_block_fires_identically_under_new_heading(self, tmp_path):
        """THE regression test for C13/P1: identical malformed content, only the
        § 4 title renamed to the action-thread shape. Before the fix this
        produced ZERO dec_* findings (silent pass, forever) — this assertion
        is what makes that regression impossible to reintroduce."""
        spec = _write_spec(tmp_path, _MALFORMED_H4_BLOCK_TEMPLATE.format(heading=_NEW_HEADING))
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert _dec_rule_ids(issues) == ["FeatureSpec.dec_blocks_well_formed"], _dec_issues(issues)
        assert _dec_issues(issues)[0]["severity"] == "critical"

    def test_well_formed_block_is_silent_under_old_heading(self, tmp_path):
        spec = _write_spec(tmp_path, _WELL_FORMED_H4_BLOCK_TEMPLATE.format(heading=_OLD_HEADING))
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert _dec_rule_ids(issues) == [], _dec_issues(issues)

    def test_well_formed_block_is_silent_under_new_heading(self, tmp_path):
        """Two-sided companion: the fix must not turn a genuinely well-formed
        block into a false positive just because § 4 was renamed."""
        spec = _write_spec(tmp_path, _WELL_FORMED_H4_BLOCK_TEMPLATE.format(heading=_NEW_HEADING))
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert _dec_rule_ids(issues) == [], _dec_issues(issues)


# ---------------------------------------------------------------------------
# P2 — the new row representation, inside `## 3. Actions`' Rule rung.
# ---------------------------------------------------------------------------

_GOOD_ROW_SPEC = """\
# F901_Test — DEC Row Test

## 1. Technical Overview

Overview text.

## 2. Action Index

| # | Action (handler) | Method · Path | Codes | Writes | Detail |
|---|---|---|---|---|---|
| **A0** | *cross-cutting — belongs to no single action* | — | FR-601 | — | § 4.4 |
| **A1** | `ManageListingsController#index` | `GET` `.../manage-listings` | FR-201, DEC-001, US127 | — *(read-only)* | § 3.1 |

## 3. Actions

### 3.1 CAP-01 — Browse & filter the listing table

#### A1 · View, search and filter the listing table

`GET .../manage-listings` → `ManageListingsController#index`
`FR-201` `DEC-001` `US127` · `SCR001_ManageListings`

**Who** · Marketplace admin
**FE** · `index.haml:1-23` renders the table via `Listing::ListPresenter#listings`.
**Request** · param `q` *(text)* and `status[]` *(multi-value)*
**BE** · `ListPresenter#resource_scope` — `q` matches title/category via SQL `LIKE`.
**Rule** · decides the per-row action menu:

| DEC | subtype | Condition | What the user sees | Source |
|---|---|---|---|---|
| **DEC-001** | render | `admin_mode` AND `state == 'approval_pending'` | shows Approve + Reject | `_actions.haml:4-16` |

**Result** · read-only — **no DB write**. Paginated table.
**Source:** `index.haml:1-29` → `manage_listings_controller.rb:5` → `list_presenter.rb:1-142`

## 4. Shared Foundation

### 4.1 Components

None.

### 4.2 Data Model

None.

### 4.3 State Management

None.

### 4.4 Shared Rules

#### Bin 3 — cross-cutting, belongs to no single action

**FR-601** applies globally: every listing action is scoped to the current org.

### 4.5 Algorithms & Integrations

None.

### 4.6 Configuration

None.

## 5. Verification & Technical Notes

### 5.1 Technical Verification

None.

### 5.2 Assumptions

None.

### 5.3 Unresolved Questions

None.

### 5.4 Source References

**Source:** `manage_listings_controller.rb:5`

### 5.5 Artifact References

None.
"""

# The exact DEC row line the mutations below target — kept as one named
# constant so every mutation is a single, auditable string replacement
# (and so a change to `_GOOD_ROW_SPEC` above can't silently desync a
# `.replace()` call elsewhere in this file).
_GOOD_DEC_ROW = (
    "| **DEC-001** | render | `admin_mode` AND `state == 'approval_pending'` "
    "| shows Approve + Reject | `_actions.haml:4-16` |"
)

assert _GOOD_DEC_ROW in _GOOD_ROW_SPEC  # guard: the fixture and the constant must agree


class TestP2RowFormWellFormed:
    def test_well_formed_row_fires_nothing(self, tmp_path):
        spec = _write_spec(tmp_path, _GOOD_ROW_SPEC)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert _dec_rule_ids(issues) == [], _dec_issues(issues)


class TestP2RowFormEmptyColumn:
    def test_empty_subtype_column_fires_well_formed_critical(self, tmp_path):
        """Reaches: `_dec_row_cell_state` returning 'empty' for the subtype
        cell — proven by first asserting the base fixture is clean (above),
        then applying exactly this one mutation."""
        broken_row = _GOOD_DEC_ROW.replace("| render |", "|  |")
        assert broken_row != _GOOD_DEC_ROW  # the mutation must actually apply
        spec = _write_spec(tmp_path, _GOOD_ROW_SPEC.replace(_GOOD_DEC_ROW, broken_row))
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert _dec_rule_ids(issues) == ["FeatureSpec.dec_blocks_well_formed"], _dec_issues(issues)
        matching = _dec_issues(issues)[0]
        assert matching["severity"] == "critical"
        assert "DEC-001" in matching["message"]
        assert "subtype" in matching["message"]

    def test_empty_source_column_fires_well_formed_critical(self, tmp_path):
        broken_row = _GOOD_DEC_ROW.replace("| `_actions.haml:4-16` |", "|  |")
        assert broken_row != _GOOD_DEC_ROW
        spec = _write_spec(tmp_path, _GOOD_ROW_SPEC.replace(_GOOD_DEC_ROW, broken_row))
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert _dec_rule_ids(issues) == ["FeatureSpec.dec_blocks_well_formed"], _dec_issues(issues)
        assert "Source" in _dec_issues(issues)[0]["message"]


class TestP2RowFormInvalidSubtype:
    def test_invalid_subtype_fires_well_formed_critical(self, tmp_path):
        """Reaches: `declared - VALID_SUBTYPES` being non-empty — the cell is
        real content ('explode'), not empty and not a lazy placeholder, so
        this is the ONLY branch that can fire on it."""
        broken_row = _GOOD_DEC_ROW.replace("| render |", "| explode |")
        assert broken_row != _GOOD_DEC_ROW
        spec = _write_spec(tmp_path, _GOOD_ROW_SPEC.replace(_GOOD_DEC_ROW, broken_row))
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert _dec_rule_ids(issues) == ["FeatureSpec.dec_blocks_well_formed"], _dec_issues(issues)
        matching = _dec_issues(issues)[0]
        assert matching["severity"] == "critical"
        assert "invalid subtype" in matching["message"].lower()
        assert "explode" in matching["message"]


class TestP2RowFormLazyPlaceholder:
    def test_lazy_na_condition_fires_warning_not_critical(self, tmp_path):
        """Reaches: `_dec_row_cell_state` returning 'lazy' for the Condition
        cell — 'N/A' is neither empty nor real content, and must NOT be
        conflated with the empty-cell (critical) branch."""
        broken_row = _GOOD_DEC_ROW.replace(
            "| `admin_mode` AND `state == 'approval_pending'` |", "| N/A |")
        assert broken_row != _GOOD_DEC_ROW
        spec = _write_spec(tmp_path, _GOOD_ROW_SPEC.replace(_GOOD_DEC_ROW, broken_row))
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert _dec_rule_ids(issues) == ["FeatureSpec.dec_lazy_na"], _dec_issues(issues)
        matching = _dec_issues(issues)[0]
        assert matching["severity"] == "warning"
        assert "Condition" in matching["message"]

    def test_lazy_tbd_source_fires_warning_not_the_citation_critical(self, tmp_path):
        """'TBD' in the Source column must be caught as a LAZY placeholder
        (warning), not fall through to the 'not a real path:line citation'
        critical branch — the two must not double-fire on the same cell."""
        broken_row = _GOOD_DEC_ROW.replace("| `_actions.haml:4-16` |", "| TBD |")
        assert broken_row != _GOOD_DEC_ROW
        spec = _write_spec(tmp_path, _GOOD_ROW_SPEC.replace(_GOOD_DEC_ROW, broken_row))
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert _dec_rule_ids(issues) == ["FeatureSpec.dec_lazy_na"], _dec_issues(issues)


class TestP2RowFormSourceNotRealCitation:
    def test_source_present_but_no_pathline_fires_well_formed_critical(self, tmp_path):
        """Real content, non-lazy, but not a `path:line` shape — must fail
        the citation check specifically, distinct from both the empty-cell
        and lazy-placeholder branches."""
        broken_row = _GOOD_DEC_ROW.replace(
            "| `_actions.haml:4-16` |", "| somewhere in the haml partial |")
        assert broken_row != _GOOD_DEC_ROW
        spec = _write_spec(tmp_path, _GOOD_ROW_SPEC.replace(_GOOD_DEC_ROW, broken_row))
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert _dec_rule_ids(issues) == ["FeatureSpec.dec_blocks_well_formed"], _dec_issues(issues)
        matching = _dec_issues(issues)[0]
        assert matching["severity"] == "critical"
        assert "path:line" in matching["message"]


# ---------------------------------------------------------------------------
# D4 degradation — row findings must WARN-first while the OLD § 3 sentinel is
# present, mirroring `_thread_sev_msg`'s treatment of every other
# action-thread check (reused here, not re-derived).
# ---------------------------------------------------------------------------

class TestP2Degradation:
    def test_row_finding_degrades_to_warning_while_pre_thread_sentinel_present(self, tmp_path):
        broken_row = _GOOD_DEC_ROW.replace("| render |", "|  |")
        degraded_text = _GOOD_ROW_SPEC.replace(_GOOD_DEC_ROW, broken_row).replace(
            "## 2. Action Index",
            "## 3. System Design\n\nNone — degradation-window probe only.\n\n## 2. Action Index",
        )
        spec = _write_spec(tmp_path, degraded_text)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = _dec_issues(issues)
        assert [i["rule_id"] for i in matching] == ["FeatureSpec.dec_blocks_well_formed"], matching
        assert matching[0]["severity"] == "warning"
        assert "(_pre_thread)" in matching[0]["message"]

    def test_old_shape_block_form_is_never_degraded(self, tmp_path):
        """Merge blocker #4 guard: the OLD H4 block-form checks must NEVER be
        wrapped in D4 degradation — every pre-existing DEC fixture already
        carries '## 3. System Design' and expects `critical`, unconditionally.
        This is what keeps the 7 existing DEC tests green."""
        spec = _write_spec(tmp_path, _MALFORMED_H4_BLOCK_TEMPLATE.format(heading=_OLD_HEADING))
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = _dec_issues(issues)
        assert matching[0]["severity"] == "critical"
        assert "(_pre_thread)" not in matching[0]["message"]


# ---------------------------------------------------------------------------
# `_bounds_by_number` — the mechanism P1's fix relies on, unit-tested in
# isolation from the DEC checks that consume it.
# ---------------------------------------------------------------------------

class TestBoundsByNumber:
    def _h2(self, headings: list[tuple[int, str]]) -> list[tuple[int, str]]:
        return [(i, h) for i, h in headings if h.startswith("## ") and not h.startswith("### ")]

    def test_resolves_old_title(self):
        lines = ["## 4. Technical Behavior by Capability", "body", "## 5. Next"]
        headings = [(0, lines[0]), (2, lines[2])]
        h2 = self._h2(headings)
        assert vfs._bounds_by_number(h2, 4, len(lines)) == (1, 2)

    def test_resolves_new_title(self):
        lines = ["## 4. Shared Foundation", "body", "## 5. Next"]
        headings = [(0, lines[0]), (2, lines[2])]
        h2 = self._h2(headings)
        assert vfs._bounds_by_number(h2, 4, len(lines)) == (1, 2)

    def test_absent_number_returns_none(self):
        lines = ["## 1. Overview", "body"]
        headings = [(0, lines[0])]
        h2 = self._h2(headings)
        assert vfs._bounds_by_number(h2, 4, len(lines)) is None

    def test_extends_to_end_of_document_when_last(self):
        lines = ["## 4. Shared Foundation", "body", "more body"]
        headings = [(0, lines[0])]
        h2 = self._h2(headings)
        assert vfs._bounds_by_number(h2, 4, len(lines)) == (1, 3)
