"""The single § 2 Functional Capabilities table contract (AD-6, phase 05 of
plans/260819-1016-rebuild-spec-capability-map).

Before this module, `validate_feature_spec.py`'s `_check_capabilities_section` was the
ONLY place that split a § 2 markdown table into header + data rows, and it did so
inline. AD-6 forbids a second independent implementation of that same invariant — every
caller listed below MUST import this module rather than re-deriving the parse:

- `validate_feature_spec.py` — `_check_capabilities_section` (forward + reverse checks)
  and `_cap_claims()`, both phase 05.
- phase 06's `_check_capability_analysis` (reads `data_rows`/`claim_state` read-only).
- phase 07's `_doc_migration_cap_map_step_lib.count_pending` (reads `claim_state`
  read-only — MUST NOT edit this file).
- phase 08's `_check_promote_candidates`.

`claim_state()` is the ONE definition of "is this § 2 table filled in yet" — the
validator's `cap.claims_unfilled` warning and the migrate step's `cap-map` pending count
both call it, so the two can never disagree about what "unfilled" means.

No I/O, no regex construction from untrusted input, no `eval` — three pure functions
over already-read `lines`/`header_cells`/`rows`.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Column resolution — family -> casefolded substring, same "search the header text"
# idiom already used throughout validate_feature_spec.py (e.g. `_check_screens_section`'s
# `scr_idx` / `_check_capabilities_section`'s old `req_idx`). Position-independent: a
# column can move anywhere in the row without breaking resolution.
# ---------------------------------------------------------------------------
_CLAIM_COLUMN_SUBSTRINGS: dict[str, str] = {
    "US": "user stor",
    "FR": "requirement",
    "BR": "business rule",
    "SCR": "screen",
}


def data_rows(lines: list[str], b2: tuple[int, int] | None) -> tuple[list[str], list[list[str]]]:
    """Header cells (casefolded) and the filtered § 2 data rows, each row already split
    into stripped cells. Carries the `{...}` placeholder and empty-first-cell filter that
    used to be inlined at `validate_feature_spec.py:1344-1348`.

    `b2` absent, or the table missing entirely (no `|`-prefixed lines at all), both
    return `([], [])` — the caller decides what that means (absent § 2 vs. malformed
    header are different findings, not this module's concern)."""
    if not b2:
        return [], []
    section_lines = lines[b2[0]:b2[1]]
    table_rows = [ln for ln in section_lines if ln.strip().startswith("|")]
    if not table_rows:
        return [], []
    header_cells = [c.strip().casefold() for c in table_rows[0].strip().strip("|").split("|")]
    rows: list[list[str]] = []
    for raw in table_rows[2:]:  # skip header + markdown separator row
        cells = [c.strip() for c in raw.strip().strip("|").split("|")]
        first = cells[0] if cells else ""
        if first and not first.startswith("{"):
            rows.append(cells)
    return header_cells, rows


def claim_columns(header_cells: list[str]) -> dict[str, int]:
    """Family -> column index, resolved by casefolded substring. A family whose column
    is absent from this header is simply omitted from the returned dict — never raises,
    matching the `req_idx is None` fail-soft precedent (a malformed header is already
    covered by `func.missing_h2`/schema checks elsewhere)."""
    cols: dict[str, int] = {}
    for family, substr in _CLAIM_COLUMN_SUBSTRINGS.items():
        idx = next((i for i, h in enumerate(header_cells) if substr in h), None)
        if idx is not None:
            cols[family] = idx
    return cols


def _cell_is_empty(cell: str) -> bool:
    """A claim cell counts as empty when it is blank, an unfilled `{...}` template
    placeholder, or a bare dash — the three shapes the researcher contract calls out as
    "never leave this way". `N/A` (and any other real prose) is a substantive answer,
    not emptiness — a background feature's Screens cell legitimately reads `N/A` and
    must not be treated as unfilled."""
    c = cell.strip()
    if not c:
        return True
    if c.startswith("{") and c.endswith("}"):
        return True
    return c in ("—", "-")


def claim_state(header_cells: list[str], rows: list[list[str]]) -> str:
    """The ONE definition of § 2's fill state, shared by the validator's
    `cap.claims_unfilled` warning and phase 07's `cap-map` `count_pending`:

    - `"absent"`   — no data rows at all (header/placeholder-only § 2, or § 2 missing).
    - `"unfilled"` — >=1 data row, and EVERY row's claim cells are empty (the post-
      `cap-map`/pre-fill window: the table was widened but nobody has filled a claim
      cell yet).
    - `"filled"`   — >=1 data row, and EVERY row's claim cells are non-empty.
    - `"partial"`  — a mix: some rows/cells populated, others not. Deliberately its own
      state, never folded into `"unfilled"` — a human mid-fill is real, informative
      signal, not something to mute (no percentage threshold; all-or-nothing by design).

    ACCEPTED LIMITATION — `"absent"` is ambiguous per-file, and deliberately so.
    Measured 2026-08-19 on a real 66-feature v26->v27 migration: `feature-sot` writes
    `FUNC_CAPABILITIES_SKELETON` (a 7-column header with ZERO data rows), so a freshly
    migrated corpus lands in `"absent"`, NOT `"unfilled"`. The FM-4 mute gates on
    `"unfilled"` only, so it does not engage on that path and the corpus emits one
    `cap.code_unclaimed` per declared code — 1225 criticals across 66/66 features.
    This is not a defect to mute: `"absent"` with populated §§ 4-7 is byte-identical to
    red-team finding SA-2 (emptying § 2 is the cheapest way to defeat the partition),
    so muting it here would reopen a Critical. The two meanings are indistinguishable
    from a single file; only a corpus-wide view could separate them. Decision (user,
    2026-08-19): the criticals are TRUE — nothing is claimed yet — and they are the
    fill work queue. `cap-map` INERT and `mirror-skew` REFUSED already gate the
    pipeline; driving the count to 0 is the fill's acceptance criterion.
    See plan.md "Fresh-migration flood" and reports/implementer-260819-1754-phase-07b-*."""
    if not rows:
        return "absent"
    col_indices = list(claim_columns(header_cells).values())

    def _row_is_empty(cells: list[str]) -> bool:
        return all(
            idx >= len(cells) or _cell_is_empty(cells[idx])
            for idx in col_indices
        )

    empties = [_row_is_empty(r) for r in rows]
    if all(empties):
        return "unfilled"
    if not any(empties):
        return "filled"
    return "partial"
