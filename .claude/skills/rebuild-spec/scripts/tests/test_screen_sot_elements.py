"""Tests for `_screen_sot_elements_lib.build_elements` -- the S-06/S-07 merge, the
hardest logic in Phase 05 per the phase file's own Implementation Steps ordering.
Covers allocation order, cross-source dedup, the button/link Decision-point heuristic,
and the leftover-prose preservation the ADDENDUM's data-loss bug made mandatory.
"""
from __future__ import annotations

import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from _screen_sot_elements_lib import build_elements, build_validation_section  # noqa: E402

DATA_INVENTORY = (
    "| Display Label | Source | Format | Empty Behavior | Cross-ref |\n"
    "|---------------|--------|--------|-----------------|-----------|\n"
    "| Account balance | computed | currency | dash | MODEL001.balance |"
)
CLIENT_SIDE = (
    "| Field | Type | Required | Constraints | Async Check | Error Message |\n"
    "|-------|------|----------|--------------|--------------|----------------|\n"
    "| Email | email | yes | valid email format | POST /check_email | Please enter a valid email |"
)
BRANCHES = (
    "| Decision point | Condition | Outcome on this screen | Source |\n"
    "|-----------------|-----------|--------------------------|--------|\n"
    "| Already logged in | logged_in? | Redirect | `a.rb:1` |\n"
    "| Facebook button | fb_enabled? | Facebook button rendered | `a.rb:2` |\n"
    "| Forgot password link clicked | click | Panel opens | `a.rb:3` |\n"
)


def test_allocation_order_data_inventory_then_client_side_then_branches():
    # Reaches all three allocation sources in one pass -- pins the ORDER (not just
    # presence) the phase file's Implementation Steps #1 specifies.
    result = build_elements(DATA_INVENTORY, CLIENT_SIDE, BRANCHES)
    ids = [row[0] for row in _rows_from_table(result.table_text)]
    labels = [row[1] for row in _rows_from_table(result.table_text)]
    assert ids == ["E01", "E02", "E03", "E04"]
    assert labels == ["Account balance", "Email", "Facebook button", "Forgot password link"]


def test_branches_decision_point_already_logged_in_is_not_an_element():
    # Reaches the _BUTTON_LINK_RE no-match branch: "Already logged in" names a
    # condition, not a UI control, and must NOT become an element row.
    result = build_elements("", "", BRANCHES)
    labels = [row[1] for row in _rows_from_table(result.table_text)]
    assert "Already logged in" not in labels
    assert "Facebook button" in labels


def test_dedup_by_label_case_insensitive_trimmed_across_sources():
    # Reaches the _alloc() dedup guard: the SAME visible label appears in both Data
    # Inventory and the Branches Decision-point column (case/whitespace varied) and
    # must be allocated exactly ONE E## id, from whichever source saw it first.
    data_inv = (
        "| Display Label | Source | Format | Empty Behavior | Cross-ref |\n"
        "|---------------|--------|--------|-----------------|-----------|\n"
        "|  facebook button  | API field | raw | dash | N/A |"
    )
    branches = (
        "| Decision point | Condition | Outcome on this screen | Source |\n"
        "|-----------------|-----------|--------------------------|--------|\n"
        "| Facebook button | fb_enabled? | rendered | `a.rb:1` |\n"
    )
    result = build_elements(data_inv, "", branches)
    assert result.row_count == 1
    rows = _rows_from_table(result.table_text)
    assert len(rows) == 1
    assert rows[0][0] == "E01"


def test_client_side_field_seeds_both_element_row_and_validation_row():
    result = build_elements("", CLIENT_SIDE, "")
    rows = _rows_from_table(result.table_text)
    assert rows[0][0] == "E01"
    assert rows[0][1] == "Email"
    assert rows[0][2] == "email"  # Type column carried through
    assert rows[0][3] == "yes"  # Required column carried through
    assert result.validation_rows == [["E01", "valid email format", "Please enter a valid email", "submit"]]
    assert result.async_checks == [("E01", "POST /check_email")]


def test_async_check_dash_placeholder_is_not_recorded():
    # Reaches the `check not in ("—", "-", "N/A")` guard -- a placeholder Async Check
    # cell must not produce a spurious Implementation Mapping row.
    client_side = (
        "| Field | Type | Required | Constraints | Async Check | Error Message |\n"
        "|-------|------|----------|--------------|--------------|----------------|\n"
        "| Username | text | yes | Required | — | This field is required |"
    )
    result = build_elements("", client_side, "")
    assert result.async_checks == []


def test_data_inventory_leading_and_trailing_notes_are_preserved_not_dropped():
    # Reaches the data_notes prefix/suffix capture -- the exact class of loss the
    # ADDENDUM's data-loss bug caused in `reshape_data_inventory` must not recur here.
    body = (
        "<!-- Cap: max 20 primary fields. -->\n\n"
        + DATA_INVENTORY
        + "\n\n**Note:** the totals row is hidden for guest checkout — see SCR044."
    )
    result = build_elements(body, "", "")
    assert "<!-- Cap: max 20 primary fields. -->" in result.table_text
    assert "**Note:** the totals row is hidden for guest checkout — see SCR044." in result.table_text


def test_client_side_na_body_is_preserved_verbatim_as_validation_fallback():
    # Reaches the cs_header is None branch (bare N/A prose, no real table) -- the
    # exact original N/A sentence must survive into `## 6.`, not a generic
    # replacement string, since it is a more precise (and pre-existing) statement.
    result = build_elements("", "`N/A — no client-side form validation detected.`", "")
    section = build_validation_section(result, "`N/A — no submit-style action handlers detected.`")
    assert section == "`N/A — no client-side form validation detected.`"


def test_validation_section_scaffolds_placeholder_row_when_server_side_pending():
    # Reaches the has_pending_server_rows branch: a real (non-N/A) `### B) Server-side`
    # body means a researcher judgment call is still owed, signaled by a scaffold row.
    result = build_elements("", "", "")
    section = build_validation_section(result, "#### Login\n\n- **Errors:** bad password")
    assert "{…}" in section
    assert "{blur \\| change \\| submit \\| server response}" in section  # pipes escaped, not corrupting the table


def test_validation_section_no_scaffold_when_server_side_is_na():
    # Reaches the NOT has_pending_server_rows branch via the backtick-wrapped N/A
    # convention -- the exact bug this phase's addendum-adjacent fix targets.
    result = build_elements("", "", "")
    section = build_validation_section(result, "`N/A — no submit-style action handlers detected.`")
    assert "{…}" not in section


def _rows_from_table(table_text: str) -> list[list[str]]:
    lines = table_text.splitlines()
    if not lines[0].startswith("| ID"):
        return []
    return [
        [c.strip() for c in ln.strip("|").split("|")]
        for ln in lines[2:]
        if ln.strip().startswith("|")
    ]
