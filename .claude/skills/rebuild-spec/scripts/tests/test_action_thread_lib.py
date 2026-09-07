"""Unit tests for `_action_thread_lib.py` (phase 02, action-thread reshape, D2/D4):
`parse_action_index`, `action_blocks`, `rungs`, and the handler-fallback classifier.

No family-code regex lives in the library under test (by design — see the module
docstring), so these tests never assert on FR/BR/US family classification; that
happens in `validate_feature_spec.py` and is covered by test_action_index_validation.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

import _action_thread_lib as lib  # noqa: E402
from _spec_parse import parse_headings_and_blocks  # noqa: E402


def _bounds(h2, name, total):
    for i, (idx, h) in enumerate(h2):
        if h == name:
            return idx + 1, (h2[i + 1][0] if i + 1 < len(h2) else total)
    return None


_INDEX_DOC = """\
## 2. Action Index

| # | Action (handler) | Method · Path | Codes | Writes | Detail |
|---|---|---|---|---|---|
| **A0** | *cross-cutting — belongs to no single action* | — | FR-601 | — | § 4.4 |
| **A1** | `ManageListingsController#index` | `GET` `.../manage-listings` | FR-201, US127 | — *(read-only)* | § 3.1 |
| **A9** | `ExportListingsJob#perform` *(background, no FE)* | queue · `Delayed::Job` | FR-203, US160 | `export_task_results` | § 3.3 |

## 3. Actions
"""


def _index_bounds():
    lines = _INDEX_DOC.splitlines()
    headings, _ = parse_headings_and_blocks(lines)
    h2 = [(i, h) for i, h in headings if h.startswith("## ")]
    return lines, _bounds(h2, "## 2. Action Index", len(lines))


class TestParseActionIndex:
    def test_bounds_absent_returns_empty(self):
        assert lib.parse_action_index(["x"], None) == []

    def test_no_table_lines_returns_empty(self):
        lines = ["## 2. Action Index", "", "no table here", ""]
        assert lib.parse_action_index(lines, (1, 4)) == []

    def test_three_rows_parsed_with_expected_ids(self):
        lines, bounds = _index_bounds()
        rows = lib.parse_action_index(lines, bounds)
        assert [r["id"] for r in rows] == ["A0", "A1", "A9"]

    def test_a0_row_shape(self):
        lines, bounds = _index_bounds()
        row = lib.parse_action_index(lines, bounds)[0]
        assert row["key"] == "*cross-cutting — belongs to no single action*"
        assert row["codes"] == ["FR-601"]
        assert row["tables"] == []
        assert row["detail"] == "§ 4.4"

    def test_a1_row_handler_and_method_path(self):
        lines, bounds = _index_bounds()
        row = lib.parse_action_index(lines, bounds)[1]
        assert row["key"] == "`ManageListingsController#index`"
        assert row["method"] == "GET"
        assert row["path"] == ".../manage-listings"
        assert row["codes"] == ["FR-201", "US127"]
        assert row["tables"] == []  # "— *(read-only)*" writes cell -> no tables

    def test_a9_row_queue_driven_method_path_and_tables(self):
        lines, bounds = _index_bounds()
        row = lib.parse_action_index(lines, bounds)[2]
        assert row["method"] == "queue"
        assert row["path"] == "Delayed::Job"
        assert row["tables"] == ["export_task_results"]

    def test_row_line_numbers_are_absolute(self):
        lines, bounds = _index_bounds()
        rows = lib.parse_action_index(lines, bounds)
        for row in rows:
            assert lines[row["line"]].strip().startswith(f"| **{row['id']}**")

    def test_placeholder_row_skipped(self):
        lines = [
            "## 2. Action Index", "",
            "| # | Action (handler) | Method · Path | Codes | Writes | Detail |",
            "|---|---|---|---|---|---|",
            "| {ID} | {HANDLER} | {METHOD_PATH} | {CODES} | {WRITES} | {DETAIL} |",
        ]
        assert lib.parse_action_index(lines, (0, len(lines))) == []


class TestIsHandlerFallback:
    def test_bare_method_path_is_fallback(self):
        assert lib.is_handler_fallback("`GET /manage-listings`") is True

    def test_class_method_handler_is_not_fallback(self):
        assert lib.is_handler_fallback("`ManageListingsController#index`") is False

    def test_a0_cross_cutting_label_is_not_fallback(self):
        assert lib.is_handler_fallback("*cross-cutting — belongs to no single action*") is False

    def test_background_suffix_handler_is_not_fallback(self):
        assert lib.is_handler_fallback("`ExportListingsJob#perform` *(background, no FE)*") is False


_ACTIONS_DOC = """\
## 3. Actions

### 3.1 CAP-01 — Bucket one

#### A1 · View, search and filter

`GET .../manage-listings` -> `ManageListingsController#index`
`FR-201` `US127`

**Who** · Marketplace admin
**FE** · `index.haml:1-23` renders the table.
**Request** · param `q`
**BE** · `ListPresenter#resource_scope`
**Rule** · no per-row conditional logic here.
**Result** · read-only.
**Source:** `index.haml:1-29` -> `manage_listings_controller.rb:5`

#### A7 · Approve via member route · A8 · Reject via member route

**Who** · Marketplace admin

## 4. Shared Foundation
"""


def _actions_headings():
    lines = _ACTIONS_DOC.splitlines()
    headings, _ = parse_headings_and_blocks(lines)
    return lines, headings


class TestActionBlocks:
    def test_two_blocks_found(self):
        _, headings = _actions_headings()
        blocks = lib.action_blocks(headings, 999)
        assert [b["ids"] for b in blocks] == [["A1"], ["A7", "A8"]]

    def test_block_bounded_at_next_heading_of_any_level(self):
        lines, headings = _actions_headings()
        blocks = lib.action_blocks(headings, len(lines))
        a1 = blocks[0]
        # A1's block must stop at the next H4 (#### A7 ...), not run past it.
        assert lines[a1["end"]].startswith("#### A7")

    def test_block_bounded_at_next_h2_when_no_h3_or_h4_follows(self):
        lines, headings = _actions_headings()
        blocks = lib.action_blocks(headings, len(lines))
        a7a8 = blocks[1]
        assert lines[a7a8["end"]] == "## 4. Shared Foundation"

    def test_block_bounded_at_total_when_truly_nothing_follows(self):
        lines, headings = _actions_headings()
        # Drop everything from "## 4. Shared Foundation" onward.
        cut = lines.index("## 4. Shared Foundation")
        lines = lines[:cut]
        headings = [(i, h) for i, h in headings if i < cut]
        blocks = lib.action_blocks(headings, len(lines))
        assert blocks[1]["end"] == len(lines)


class TestRungs:
    def test_all_seven_rungs_found_in_order(self):
        lines, headings = _actions_headings()
        blocks = lib.action_blocks(headings, len(lines))
        found = lib.rungs(lines, blocks[0])
        assert [lbl for lbl, _ in found] == [
            "Who", "FE", "Request", "BE", "Rule", "Result", "Source",
        ]

    def test_source_rung_uses_colon_shape_and_is_captured(self):
        lines, headings = _actions_headings()
        blocks = lib.action_blocks(headings, len(lines))
        found = dict(lib.rungs(lines, blocks[0]))
        assert found["Source"] == "`index.haml:1-29` -> `manage_listings_controller.rb:5`"

    def test_middot_source_shape_is_not_recognized(self):
        """The wire-format contract's ORIGINAL (wrong) example used '**Source** ·
        `path`' — that shape must NOT be picked up as a Source rung, or a real
        Source rung written that way would silently vanish from `rungs()` (the
        exact gate-that-cannot-fail class this phase's merge blockers forbid)."""
        broken = _ACTIONS_DOC.replace(
            "**Source:** `index.haml:1-29` -> `manage_listings_controller.rb:5`",
            "**Source** · `index.haml:1-29` -> `manage_listings_controller.rb:5`",
        )
        lines = broken.splitlines()
        headings, _ = parse_headings_and_blocks(lines)
        blocks = lib.action_blocks(headings, len(lines))
        found = [lbl for lbl, _ in lib.rungs(lines, blocks[0])]
        assert "Source" not in found

    def test_absent_rung_is_simply_missing_not_an_empty_entry(self):
        lines, headings = _actions_headings()
        blocks = lib.action_blocks(headings, len(lines))
        found = dict(lib.rungs(lines, blocks[1]))  # A7/A8 block only has "Who"
        assert list(found) == ["Who"]

    def test_multiline_body_joined_and_stripped(self):
        doc = _ACTIONS_DOC.replace(
            "**Rule** · no per-row conditional logic here.\n",
            "**Rule** · decides the per-row action menu:\n\n"
            "| DEC | Condition |\n|---|---|\n| DEC-001 | admin_mode |\n\n",
        )
        lines = doc.splitlines()
        headings, _ = parse_headings_and_blocks(lines)
        blocks = lib.action_blocks(headings, len(lines))
        found = dict(lib.rungs(lines, blocks[0]))
        assert "DEC-001" in found["Rule"]
        assert found["Rule"].startswith("decides the per-row action menu:")


# ---------------------------------------------------------------------------
# `State` — the 8th rung (phase 01, self-sufficiency v27.8). `_RUNG_LINE_RE`
# deliberately spells rung labels literally rather than importing
# `_spec_constants.RUNG_LABELS` (see the module comment above that regex), so this
# is a two-place edit: this test proves the SECOND place (the regex) actually
# recognizes the middot `**State** · ...` shape, not just that the constants tuple
# grew an entry.
# ---------------------------------------------------------------------------

class TestMatchRungLineState:
    def test_state_rung_recognized_in_middot_shape(self):
        assert lib._match_rung_line("**State** · x") == ("State", "x")

    def test_state_rung_found_by_rungs_when_present(self):
        doc = _ACTIONS_DOC.replace(
            "**Result** · read-only.\n",
            "**Result** · read-only.\n"
            "**State** · `SM-001`: `pending` → `approved` *(§ 4.3)*\n",
        )
        lines = doc.splitlines()
        headings, _ = parse_headings_and_blocks(lines)
        blocks = lib.action_blocks(headings, len(lines))
        found = [lbl for lbl, _ in lib.rungs(lines, blocks[0])]
        assert found == ["Who", "FE", "Request", "BE", "Rule", "Result", "State", "Source"]
