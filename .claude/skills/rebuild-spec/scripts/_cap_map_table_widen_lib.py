#!/usr/bin/env python3
"""_cap_map_table_widen_lib.py -- pure §2 table analysis + widening mechanics for the
`cap-map` `--migrate` step (phase-07, plans/260819-1016-rebuild-spec-capability-map).
Split out of `_doc_migration_cap_map_step_lib.py` to keep that file under the repo's
200-line guidance (the `_mirror_skew_lib` / `_mirror_skew_detect_lib` precedent).

No I/O here -- every function is a pure transform over an already-read `lines` list.
Locating "## 2. Functional Capabilities" and its bounds is a GENERIC heading-bounds
computation (`_h2_bounds`, mirroring `validate_feature_spec._bounds`) -- distinct from
AD-6's table-parsing invariant. The actual TABLE contract (header/row split, claim
column resolution, fill-state) is never re-derived here: `data_rows`/`claim_columns`/
`claim_state` are imported from `_cap_table_lib` (phase 05), the single authority both
this step and `validate_feature_spec.py`'s `cap.*` checks read.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _cap_table_lib import claim_columns, claim_state, data_rows  # noqa: E402
from _spec_parse import parse_headings_and_blocks  # noqa: E402

_SECTION_HEADING = "## 2. Functional Capabilities"
_US_LABEL = "User Stories"
_BR_LABEL = "Business Rules"


def _h2_bounds(lines: list[str]) -> tuple[int, int] | None:
    """(start, end) line-index bounds of `_SECTION_HEADING`'s body, or None when the
    heading is absent -- a pre-SOT file (`## 2. Open Decisions`) is `feature-sot`'s
    problem, not this step's, and must resolve to None here, never a false match."""
    headings, _ = parse_headings_and_blocks(lines)
    h2 = [(i, h) for i, h in headings if h.startswith("## ") and not h.startswith("### ")]
    for i, (idx, h) in enumerate(h2):
        if h == _SECTION_HEADING:
            end = h2[i + 1][0] if i + 1 < len(h2) else len(lines)
            return idx + 1, end
    return None


@dataclass(frozen=True)
class Analysis:
    """One functional-spec.md's §2 state, read ONCE and shared by `count_pending`,
    `run`, and `rollback` -- so none of the three can disagree about what they saw.
    `state` carries the raw `_cap_table_lib.claim_state()` string (needed verbatim by
    `rollback`'s filled/partial refusal); `fill_pending` is the coarser bool
    `count_pending`/`run` need (AD-1: pending unless exactly `"filled"`)."""
    has_section: bool
    shape_pending: bool
    state: "str | None"  # None when shape_pending or the section is absent

    @property
    def fill_pending(self) -> bool:
        return self.state is not None and self.state != "filled"


def analyze(lines: list[str]) -> Analysis:
    b2 = _h2_bounds(lines)
    if b2 is None:
        return Analysis(has_section=False, shape_pending=False, state=None)
    header_cells, rows = data_rows(lines, b2)
    cols = claim_columns(header_cells)
    if "US" not in cols or "BR" not in cols:
        return Analysis(has_section=True, shape_pending=True, state=None)
    return Analysis(has_section=True, shape_pending=False, state=claim_state(header_cells, rows))


def _raw_cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _render(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def widen_lines(lines: list[str]) -> "list[str] | None":
    """New §2 table lines with `User Stories`/`Business Rules` inserted at their
    template positions (before `Requirements`/`Screens` respectively), or None when
    there is nothing to widen (no §2, no header+separator pair, or already 7-column).
    Never mutates `lines`. Writes empty cells into every existing data row -- codes are
    never auto-assigned (phase-07b's job, with a human in the loop)."""
    b2 = _h2_bounds(lines)
    if b2 is None:
        return None
    start, end = b2
    positions = [i for i in range(start, end) if lines[i].strip().startswith("|")]
    if len(positions) < 2:
        return None  # no header+separator pair -- nothing safe to widen
    header_cells = _raw_cells(lines[positions[0]])
    cols = claim_columns([c.casefold() for c in header_cells])
    missing_us, missing_br = "US" not in cols, "BR" not in cols
    if not missing_us and not missing_br:
        return None

    # Insertion indices computed against the ORIGINAL (pre-insert) header. Business
    # Rules goes immediately before Screens; User Stories immediately before
    # Requirements. Requirements always precedes Screens in every known header shape,
    # so inserting BR first (at the higher index) never shifts the US index below it.
    br_idx = cols.get("SCR", len(header_cells))
    us_idx = cols.get("FR", br_idx)

    def _widen_row(cells: list[str], kind: str) -> list[str]:
        out = list(cells)
        if missing_br:
            fill = {"header": _BR_LABEL, "sep": "---"}.get(kind, "")
            out = out[:br_idx] + [fill] + out[br_idx:]
        if missing_us:
            fill = {"header": _US_LABEL, "sep": "---"}.get(kind, "")
            out = out[:us_idx] + [fill] + out[us_idx:]
        return out

    new_lines = list(lines)
    for i, pos in enumerate(positions):
        kind = "header" if i == 0 else "sep" if i == 1 else "data"
        new_lines[pos] = _render(_widen_row(_raw_cells(lines[pos]), kind))
    return new_lines
