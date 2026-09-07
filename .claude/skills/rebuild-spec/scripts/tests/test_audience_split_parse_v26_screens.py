"""Tests for phase-05 (B4c)'s `parse_screens` changes in
`_audience_split_parse_v26_lib.py`: the header row is now returned (so the renderer
can be header-driven instead of reading `cells[1]` positionally -- the root defect
this phase fixes), and background detection is widened to scan the whole file when
no `## Screen List` table is found. See
plans/260817-1420-rebuild-spec-v27-migrate-legacy-docs/phase-05-screen-binding-degradation.md.
"""
from __future__ import annotations

import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from _audience_split_parse_v26_lib import parse_screens  # noqa: E402

_THREE_COL = """# Screens — F001_Auth

## Screen List

| Screen Name | What User Sees | What User Can Do |
|-------------|-----------------|-------------------|
| Login Page | An email and password form | Submit credentials |

## User Journey

User arrives, submits, lands on dashboard.
"""

_FOUR_COL_CODED = """# Screens — F999_Coded

## Screen List

| Screen Name | SCR### | What User Sees | What User Can Do |
|-------------|--------|-----------------|-------------------|
| Login | SCR001_Login | A form | Submit |

## User Journey

N/A
"""


def test_t9_three_column_table_header_is_returned_uncoded():
    result = parse_screens(_THREE_COL)
    assert result["header"] == ["Screen Name", "What User Sees", "What User Can Do"]
    assert result["rows"] == [["Login Page", "An email and password form", "Submit credentials"]]
    assert result["background"] is False


def test_t10_four_column_coded_table_header_includes_scr_column():
    result = parse_screens(_FOUR_COL_CODED)
    assert result["header"] == ["Screen Name", "SCR###", "What User Sees", "What User Can Do"]
    assert result["rows"] == [["Login", "SCR001_Login", "A form", "Submit"]]


def test_background_detected_inside_screen_list_h2_body_regression():
    """Existing behavior (already correct on the real corpus, measured directly
    against F052_EmailNotifications/F056_SESWebhook) -- must not regress."""
    text = (
        "# Screens — F052_EmailNotifications\n\n"
        "N/A — background feature; no user-facing screen flow.\n\n"
        "## Screen List\n\n"
        "N/A — background feature; no user-facing screens.\n\n"
        "## User Journey\n\n"
        "N/A — background feature; no user-facing journey.\n"
    )
    result = parse_screens(text)
    assert result["background"] is True
    assert result["rows"] == []
    assert result["header"] == []


def test_t13_background_with_no_h1_and_no_screen_list_heading_at_all():
    """Widened fallback: some background dirs could -- in principle -- carry the
    marker with no '## Screen List' heading to anchor on at all. When no table is
    found, scan the WHOLE file text for the marker rather than only the (possibly
    absent) H2 body."""
    text = "N/A — background feature; no user-facing screen flow.\n"
    result = parse_screens(text)
    assert result["background"] is True
    assert result["rows"] == []


def test_t14_second_background_wording_variant():
    text = "N/A — background feature; no user-facing screens.\n"
    result = parse_screens(text)
    assert result["background"] is True


def test_non_background_file_with_no_table_is_not_misdetected():
    text = "# Screens — F000_Weird\n\nSome unrelated prose, no table, no marker.\n"
    result = parse_screens(text)
    assert result["background"] is False
    assert result["rows"] == []
    assert result["header"] == []
