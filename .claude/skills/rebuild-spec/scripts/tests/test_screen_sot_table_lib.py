"""Tests for `_screen_sot_table_lib` -- the fence-aware table-split primitive every
Phase 05 sibling reuses. Mirrors the fence-awareness discipline the ADDENDUM required
of `_audience_split_data_inventory_lib.reshape_data_inventory`.
"""
from __future__ import annotations

import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from _screen_sot_table_lib import build_table, cell, col_index, split_around_first_table  # noqa: E402


def test_split_around_first_table_returns_header_rows_and_no_surrounding_text():
    # Reaches the found-a-table branch with empty prefix/suffix.
    body = "| A | B |\n|---|---|\n| 1 | 2 |"
    prefix, header, rows, suffix = split_around_first_table(body)
    assert prefix == "" and suffix == ""
    assert header == ["A", "B"]
    assert rows == [["1", "2"]]


def test_split_around_first_table_captures_prefix_and_suffix_prose():
    # Reaches the found-a-table branch with BOTH non-empty prefix and suffix -- the
    # mechanism `_screen_sot_elements_lib` relies on to never drop surrounding notes.
    body = "Some intro.\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\nA trailing note."
    prefix, header, rows, suffix = split_around_first_table(body)
    assert prefix == "Some intro."
    assert suffix == "A trailing note."
    assert header == ["A", "B"]
    assert rows == [["1", "2"]]


def test_split_around_first_table_returns_none_header_when_no_table_present():
    # Reaches the no-table branch (prose-only body, e.g. an `N/A` fallback line) --
    # the whole body is handed back as prefix so callers never special-case this.
    body = "N/A — nothing to see here."
    prefix, header, rows, suffix = split_around_first_table(body)
    assert header is None
    assert rows == []
    assert suffix == ""
    assert prefix == body


def test_split_around_first_table_is_fence_aware_and_ignores_fenced_lookalike():
    # Reaches the no-table branch specifically BECAUSE the only pipe-led lines live
    # inside a fence -- proves the fence-awareness the ADDENDUM demanded is real here
    # too, not just in the data-inventory fix.
    body = "```\n| Field | Display Label |\n|-|-|\n| foo | bar |\n```"
    prefix, header, rows, suffix = split_around_first_table(body)
    assert header is None
    assert prefix == body


def test_split_around_first_table_finds_real_table_after_a_fenced_lookalike():
    # Reaches the found-a-table branch, walking PAST an earlier fenced lookalike to
    # find the real (non-fenced) table -- the fence must not just be ignored, later
    # real content must still be found.
    body = "```\n| x | y |\n|-|-|\n```\n\n| Real | Header |\n|---|---|\n| 1 | 2 |"
    prefix, header, rows, suffix = split_around_first_table(body)
    assert header == ["Real", "Header"]
    assert rows == [["1", "2"]]
    assert "```" in prefix  # the fenced lookalike survives, untouched, in the prefix


def test_split_around_first_table_requires_header_and_separator_pair():
    # Reaches the no-table branch: a lone `|`-led line with no following separator row
    # is not mistaken for a table header (guards against false positives on stray
    # prose that happens to start with a pipe).
    body = "| not a table, just a sentence starting with a pipe"
    prefix, header, rows, suffix = split_around_first_table(body)
    assert header is None
    assert prefix == body


def test_build_table_renders_header_separator_and_rows():
    out = build_table(["ID", "Name"], [["E01", "Foo"], ["E02", "Bar"]])
    lines = out.splitlines()
    assert lines[0] == "| ID | Name |"
    assert lines[1] == "|----|------|"
    assert lines[2] == "| E01 | Foo |"
    assert lines[3] == "| E02 | Bar |"


def test_col_index_omits_absent_names_without_raising():
    # Reaches the "name not in header_cf" filter branch -- absent columns are simply
    # left out of the returned dict rather than raising.
    idx = col_index(["id", "name"], "id", "name", "missing")
    assert idx == {"id": 0, "name": 1}
    assert "missing" not in idx


def test_cell_returns_default_when_column_absent_or_row_short():
    col = {"name": 5}  # index far past any real row -- exercises the len(cells) guard
    assert cell(["only", "two"], col, "name") == "—"
    assert cell(["only", "two"], col, "name", default="N/A") == "N/A"
    assert cell(["only", "two"], {}, "name") == "—"  # column not found at all
