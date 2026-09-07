"""content-preservation-map.md § A: `## 1. Overview`, `## 2. Screen Layout`,
`## 9. Accessibility`, `## 10. Responsive Behavior` (S-01/S-02/S-04/S-05/S-17/S-18).
Split out of `_screen_sot_compose_lib.py` to hold the 200-line guidance.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _screen_sot_table_lib import build_table, cell, col_index, split_around_first_table  # noqa: E402

ACCESSIBILITY_HEADER = ["Aspect", "Status", "Notes"]
RESPONSIVE_HEADER = ["Breakpoint", "Region / Element", "Behavior", "Source"]
RESPONSIVE_NA_TEXT = "N/A — no responsive behavior found in source."


def build_overview(purpose_text: str) -> str:
    """S-01 (`## Purpose` body -> `**Purpose:**`) + S-02 (Actors/Entry/Exit -- absent
    in v27, scaffolded `{...}` -- a researcher judgment call, never guessed here)."""
    purpose = purpose_text.strip() or "{UNVERIFIED — no Purpose body found in source.}"
    return (
        f"**Purpose:** {purpose}\n"
        "**Actors:** {plain role names, comma separated — no auth-class names}\n"
        "**Entry Conditions:** {what must be true for a user to reach this screen}\n"
        "**Exit Conditions:** {the terminal states — what \"done with this screen\" means}"
    )


def build_screen_layout(sketch_body: str, regions_body: str) -> tuple[str, list[list[str]]]:
    """S-03 (`### Layout Sketch`, KEEP verbatim) + S-04 (`### Layout Regions`, MOVE into
    the reader body) + S-05 (drop the Regions table's `Responsive Behavior` column,
    project each non-empty cell into `## 10.` rows instead -- DRY, target-shape §1.4).

    Returns `(section_text, responsive_rows)` -- the caller assembles `## 10.` from the
    second element alongside any other responsive-behavior sources.
    """
    parts = ["### Layout Sketch", "", sketch_body.strip() or "N/A"]
    responsive_rows: list[list[str]] = []
    prefix, header, rows, suffix = split_around_first_table(regions_body)
    parts += ["", "### Layout Regions", ""]
    if header is None:
        parts.append(regions_body.strip() or "N/A")
    else:
        header_cf = [h.casefold() for h in header]
        col = col_index(header_cf, "region id", "name", "position", "scrollable",
                         "key components", "responsive behavior")
        new_header = ["Region ID", "Name", "Position", "Scrollable", "Key Components"]
        new_rows = []
        for cells in rows:
            new_rows.append([
                cell(cells, col, "region id"), cell(cells, col, "name"),
                cell(cells, col, "position"), cell(cells, col, "scrollable"),
                cell(cells, col, "key components"),
            ])
            behavior = cell(cells, col, "responsive behavior", "")
            if behavior and behavior not in ("—", "-", "N/A"):
                region_ref = cell(cells, col, "region id") or cell(cells, col, "name")
                responsive_rows.append([
                    "—", region_ref, behavior, "—",
                ])
        if prefix.strip():
            parts.append(prefix.strip())
            parts.append("")
        parts.append(build_table(new_header, new_rows))
        if suffix.strip():
            parts.append("")
            parts.append(suffix.strip())
    return "\n".join(parts), responsive_rows


def build_responsive_behavior(responsive_rows: list[list[str]]) -> str:
    """S-05 + S-18: header row + the rows projected out of Layout Regions above. No
    other source of `## 10.` content exists mechanically -- an empty result is the
    single required `N/A` line, never a bare empty table."""
    if not responsive_rows:
        return RESPONSIVE_NA_TEXT
    return build_table(RESPONSIVE_HEADER, responsive_rows)


def build_accessibility(accessibility_body: str) -> str:
    """S-17: MOVE the dev-appendix `## Accessibility` table into the reader body
    (`## 9.`), appending the 5th `Error announcement` row (`[UNVERIFIED]`) when the
    source table -- written under the old 4-row contract -- doesn't already carry it.
    Any trailing note (e.g. `[NO_A11Y_DETECTED] — ...`) is preserved verbatim."""
    prefix, header, rows, suffix = split_around_first_table(accessibility_body)
    if header is None:
        return accessibility_body.strip() or "N/A"
    header_cf = [h.casefold() for h in header]
    col = col_index(header_cf, "aspect", "status", "notes")
    have_aspects = {cell(r, col, "aspect", "").strip().casefold() for r in rows}
    new_rows = [[cell(r, col, "aspect"), cell(r, col, "status"), cell(r, col, "notes")] for r in rows]
    if "error announcement" not in have_aspects:
        new_rows.append(["Error announcement", "[UNVERIFIED]", "—"])
    out = []
    if prefix.strip():
        out.append(prefix.strip())
        out.append("")
    out.append(build_table(ACCESSIBILITY_HEADER, new_rows))
    if suffix.strip():
        out.append("")
        out.append(suffix.strip())
    return "\n".join(out)
