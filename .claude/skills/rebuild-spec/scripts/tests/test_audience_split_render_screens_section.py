"""Tests for phase-05 (B4c)'s `render_screens`/`render_open_decisions` in
`_audience_split_render_screens_lib.py`: header-driven column detection (no more
positional `cells[1]`), ladder-based SCR### resolution, the L3 degradation contract
(`### Unbound Screens` + one continuous § 2 Open Decisions row per unbound screen --
never a `—` placeholder row in the table), and the edge cases from the phase file's
test matrix (T9-T14). See
plans/260817-1420-rebuild-spec-v27-migrate-legacy-docs/phase-05-screen-binding-degradation.md.
"""
from __future__ import annotations

import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from _audience_split_render_func_sections_lib import sanitize  # noqa: E402
from _audience_split_render_screens_lib import render_open_decisions, render_screens  # noqa: E402

_INDEX = {"login page": "SCR020_LoginPage", "homepage / search": "SCR001_Homepage"}


def _screens(header, rows, background=False, journey="N/A"):
    return {"header": header, "rows": rows, "background": background, "user_journey": journey}


# --------------------------------------------------------------------------- #
# T9 -- 3-column v26 table (no SCR column) -> 4-column output, SCR inserted at 1
# --------------------------------------------------------------------------- #

def test_t9_three_column_table_gets_scr_column_inserted():
    screens = _screens(
        ["Screen Name", "What User Sees", "What User Can Do"],
        [["Login Page", "An email form", "Submit credentials"]],
    )
    body, unbound = render_screens(screens, _INDEX)
    assert unbound == []
    lines = body.splitlines()
    assert lines[0] == "| Screen Name | SCR### | What User Sees | What User Can Do |"
    assert "| Login Page | SCR020 | An email form | Submit credentials |" in body


# --------------------------------------------------------------------------- #
# T10 -- 4-column table that already has an SCR column: no duplicate SCR column
# --------------------------------------------------------------------------- #

def test_t10_four_column_coded_table_no_duplicate_scr_column():
    screens = _screens(
        ["Screen Name", "SCR###", "What User Sees", "What User Can Do"],
        [["Login Page", "SCR020_LoginPage", "An email form", "Submit credentials"]],
    )
    body, unbound = render_screens(screens, {})
    assert unbound == []
    header_line = body.splitlines()[0]
    assert header_line.count("SCR###") == 1
    assert "| Login Page | SCR020 | An email form | Submit credentials |" in body


# --------------------------------------------------------------------------- #
# T11 -- all rows L3: header + separator only, Unbound block, zero table data rows
# --------------------------------------------------------------------------- #

def test_t11_all_unresolved_yields_header_only_table_plus_unbound_block():
    screens = _screens(
        ["Screen Name", "What User Sees", "What User Can Do"],
        [["Access Denied", "Explains denial", "Read explanation; no action"]],
    )
    body, unbound = render_screens(screens, {})
    assert len(unbound) == 1
    assert unbound[0]["name"] == "Access Denied"
    lines = [ln for ln in body.splitlines() if ln.strip().startswith("|")]
    # header + separator only -- no data row for the unresolved screen.
    assert len(lines) == 2
    assert "### Unbound Screens" in body
    assert "**Access Denied**" in body


# --------------------------------------------------------------------------- #
# T12 -- mixed resolved/unresolved; D### numbering continuous with markers
# --------------------------------------------------------------------------- #

def test_t12_mixed_resolved_and_unresolved_rows():
    screens = _screens(
        ["Screen Name", "What User Sees", "What User Can Do"],
        [
            ["Login Page", "An email form", "Submit credentials"],
            ["Access Denied", "Explains denial", "Read explanation"],
        ],
    )
    body, unbound = render_screens(screens, _INDEX)
    assert len(unbound) == 1
    assert "SCR020" in body
    assert "### Unbound Screens" in body
    assert "**Access Denied**" in body

    open_decisions = render_open_decisions(["marker one"], unbound)
    lines = open_decisions.splitlines()
    assert lines[2].startswith("| D001 | marker one |")
    assert lines[3].startswith('| D002 | Screen "Access Denied" has no SCR### binding |')


def test_open_decisions_continuous_numbering_unbound_only():
    unbound = [{"name": "Access Denied", "sees": "x", "can_do": "y"},
               {"name": "Homepage / Topbar", "sees": "x", "can_do": "y"}]
    out = render_open_decisions([], unbound)
    lines = out.splitlines()
    assert lines[2].startswith("| D001 |")
    assert lines[3].startswith("| D002 |")


def test_open_decisions_none_when_both_empty():
    assert render_open_decisions([], []) == "None — no unresolved domain confirmations."
    assert render_open_decisions([], None) == "None — no unresolved domain confirmations."


# --------------------------------------------------------------------------- #
# T13/T14 -- background feature: N/A, no edge-case-row-count critical concern
# --------------------------------------------------------------------------- #

def test_t13_background_feature_is_na_with_no_table():
    screens = _screens([], [], background=True, journey="")
    body, unbound = render_screens(screens, {})
    assert body == "N/A — background feature (no screens)."
    assert unbound == []


# --------------------------------------------------------------------------- #
# Sanitize choke point survives (P04's fencing call) -- must not regress
# --------------------------------------------------------------------------- #

def test_sanitize_still_fences_dev_tokens_and_strips_markers():
    out = sanitize("User submits POST /people to register. [NEEDS_DOMAIN_CONFIRMATION] x")
    assert "[NEEDS_DOMAIN_CONFIRMATION]" not in out
    assert "`POST`" in out


# --------------------------------------------------------------------------- #
# Anti-fuzzy guard threaded all the way through render_screens
# --------------------------------------------------------------------------- #

def test_homepage_topbar_never_binds_through_render_screens():
    screens = _screens(
        ["Screen Name", "What User Sees", "What User Can Do"],
        [["Homepage / Topbar", "Logout link", "Click logout"]],
    )
    body, unbound = render_screens(screens, _INDEX)
    assert len(unbound) == 1
    assert unbound[0]["name"] == "Homepage / Topbar"
    assert "SCR001" not in body.split("### Unbound Screens")[0]
