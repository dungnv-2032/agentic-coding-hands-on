"""Direct unit tests for `_cap_table_lib.py` — the single § 2 Functional Capabilities
table contract (AD-6, phase 05 of plans/260819-1016-rebuild-spec-capability-map).

`data_rows`/`claim_columns`/`claim_state` are pure functions over already-split lines —
every test here constructs its own tiny `header_cells`/`rows` or `lines` fixture and
calls straight into the function under test, per idiom (b) (see
test_functional_spec_sot_sections.py's own docstring for why (b), not subprocess).
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))
import _cap_table_lib as ctl  # noqa: E402

_HEADER = (
    "| ID | Capability | What the user can do | User Stories | Requirements | "
    "Business Rules | Screens |\n"
    "|----|------------|------------------------|-----------------|---------------|"
    "-------------------|---------|\n"
)


def _lines(*extra_rows: str) -> list[str]:
    return (_HEADER + "".join(extra_rows)).splitlines()


class TestDataRows:
    def test_absent_section_returns_empty(self):
        # Reaches: `if not b2: return [], []`.
        header, rows = ctl.data_rows(["x"], None)
        assert header == [] and rows == []

    def test_no_table_at_all_returns_empty(self):
        # Reaches: `if not table_rows: return [], []` — a § 2 with prose, no `|` lines.
        header, rows = ctl.data_rows(["some prose, no table"], (0, 1))
        assert header == [] and rows == []

    def test_header_only_no_data_rows(self):
        lines = _lines()
        # Reaches: table_rows has header+separator only; table_rows[2:] is empty.
        header, rows = ctl.data_rows(lines, (0, len(lines)))
        assert header[0] == "id"
        assert rows == []

    def test_data_row_split_into_cells(self):
        lines = _lines("| CAP-01 | Sign in | Do the thing | US001 | FR-101 | BR-001 | SCR001 |\n")
        # Reaches: table_rows[2:] has one row, first cell non-empty and not `{`-prefixed.
        _, rows = ctl.data_rows(lines, (0, len(lines)))
        assert rows == [["CAP-01", "Sign in", "Do the thing", "US001", "FR-101", "BR-001", "SCR001"]]

    def test_placeholder_row_filtered_out(self):
        lines = _lines("| {CAP-##} | {name} | {desc} | {US###} | {FR-###} | {BR-###} | {SCR###} |\n")
        # Reaches: first cell starts with `{` -> filtered.
        _, rows = ctl.data_rows(lines, (0, len(lines)))
        assert rows == []

    def test_empty_first_cell_row_filtered_out(self):
        lines = _lines("|  | Sign in | Do the thing | US001 | FR-101 | BR-001 | SCR001 |\n")
        # Reaches: first cell strips to empty -> filtered (matches the old inline filter).
        _, rows = ctl.data_rows(lines, (0, len(lines)))
        assert rows == []


class TestClaimColumns:
    def test_all_four_families_resolved(self):
        header, _ = ctl.data_rows(_lines(), (0, 2))
        cols = ctl.claim_columns(header)
        assert set(cols) == {"US", "FR", "BR", "SCR"}
        # Column order in the standard header, left to right.
        assert cols["US"] < cols["FR"] < cols["BR"] < cols["SCR"]

    def test_missing_family_omitted_not_raised(self):
        # Reaches: "business rule" substring absent from this 5-column legacy header —
        # claim_columns must omit "BR", never raise.
        header = ["id", "capability", "what the user can do", "requirements", "screens"]
        cols = ctl.claim_columns(header)
        assert "BR" not in cols
        assert cols == {"FR": 3, "SCR": 4}

    def test_empty_header_returns_empty_dict(self):
        assert ctl.claim_columns([]) == {}


class TestClaimState:
    def test_absent_when_no_rows(self):
        # Reaches: `if not rows: return "absent"`.
        assert ctl.claim_state(["id", "user stor", "requirement", "business rule", "screen"], []) == "absent"

    def test_unfilled_when_every_row_every_claim_cell_empty(self):
        lines = _lines(
            "| CAP-01 | Sign in |  |  |  |  |  |\n",
            "| CAP-02 | Register |  |  |  |  |  |\n",
        )
        header, rows = ctl.data_rows(lines, (0, len(lines)))
        # Reaches: `empties` all True -> "unfilled".
        assert ctl.claim_state(header, rows) == "unfilled"

    def test_filled_when_every_row_every_claim_cell_non_empty(self):
        lines = _lines(
            "| CAP-01 | Sign in | Do the thing | US001 | FR-101 | BR-001 | SCR001 |\n",
            "| CAP-02 | Register | Fill the form | US002 | FR-102 | BR-002 | SCR002 |\n",
        )
        header, rows = ctl.data_rows(lines, (0, len(lines)))
        # Reaches: `empties` all False -> "filled".
        assert ctl.claim_state(header, rows) == "filled"

    def test_partial_when_one_row_filled_one_empty(self):
        lines = _lines(
            "| CAP-01 | Sign in | Do the thing | US001 | FR-101 | BR-001 | SCR001 |\n",
            "| CAP-02 | Register |  |  |  |  |  |\n",
        )
        header, rows = ctl.data_rows(lines, (0, len(lines)))
        # Reaches: `empties` mixed True/False -> "partial" (the all-or-nothing branch).
        assert ctl.claim_state(header, rows) == "partial"

    def test_na_is_not_empty(self):
        """A background feature's Screens cell legitimately reads `N/A` — that is a
        real answer, not an unfilled placeholder, and must not prevent "filled"."""
        lines = _lines("| CAP-01 | Background job | Runs nightly | US001 | FR-101 | BR-001 | N/A |\n")
        header, rows = ctl.data_rows(lines, (0, len(lines)))
        # Reaches: `_cell_is_empty("N/A")` False for every claim cell -> "filled".
        assert ctl.claim_state(header, rows) == "filled"

    def test_placeholder_and_dash_count_as_empty(self):
        lines = _lines("| CAP-01 | Sign in | Do the thing | {US###} | — | - |  |\n")
        header, rows = ctl.data_rows(lines, (0, len(lines)))
        # Reaches: `{...}` and bare dash both satisfy `_cell_is_empty` -> row is empty.
        assert ctl.claim_state(header, rows) == "unfilled"
