"""S-06/S-07 (content-preservation-map.md § A): merge the retired `## Data Inventory`
+ `## Validation & Error Feedback § A) Client-side` rows + button/link mentions in
`### Branches` into ONE `## 3. UI Elements` E## inventory, and seed the mechanical part
of `## 6. Validation & Feedback` from the client-side table. Split out of
`_screen_sot_compose_lib.py` to hold the repo's 200-line guidance.

Allocation order (stable IDs across regenerations, per the phase file): Data Inventory
rows, then client-side fields not already present by label, then buttons/links found in
`### Branches` `Decision point` cells. Dedup by visible label, case-insensitive, trimmed.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _screen_sot_table_lib import build_table, cell, col_index, split_around_first_table  # noqa: E402

ELEMENTS_HEADER = [
    "ID", "Element", "Type", "Required", "Default", "Visibility", "Action",
    "Source", "Format", "Empty Behavior", "Cross-ref",
]
VALIDATION_HEADER = ["Element", "Rule", "Feedback", "Trigger"]
ELEMENTS_NA_TEXT = (
    "N/A — screen displays no dynamic data and has no interactive elements "
    "(static marketing/error page)"
)

# A Decision-point cell names a real UI control only when it ends in "button" or
# "link" (e.g. "Facebook button", "Forgot password link clicked") -- every other
# Decision point (a pure condition like "Already logged in") is left alone rather
# than guessed at.
_BUTTON_LINK_RE = re.compile(r"^(.+?\b(?:button|link))\b", re.IGNORECASE)


@dataclass
class ElementsResult:
    table_text: str
    validation_rows: list[list[str]] = field(default_factory=list)
    async_checks: list[tuple[str, str]] = field(default_factory=list)  # (E##, check text)
    data_notes: list[str] = field(default_factory=list)  # leftover Data Inventory prose
    client_side_notes: list[str] = field(default_factory=list)  # leftover Client-side prose
    row_count: int = 0


def _next_id(n: int) -> str:
    return f"E{n:02d}"


def build_elements(
    data_inventory_body: str, client_side_body: str, branches_body: str,
) -> ElementsResult:
    rows: list[list[str]] = []
    label_to_id: dict[str, str] = {}
    validation_rows: list[list[str]] = []
    async_checks: list[tuple[str, str]] = []
    data_notes: list[str] = []
    client_side_notes: list[str] = []

    def _alloc(label: str) -> str | None:
        key = label.strip().casefold()
        if not key or key in label_to_id:
            return None
        eid = _next_id(len(rows) + 1)
        label_to_id[key] = eid
        return eid

    # --- S-06: Data Inventory rows -> display-field E## rows -------------------
    prefix, header, data_rows, suffix = split_around_first_table(data_inventory_body)
    data_notes.extend(t for t in (prefix, suffix) if t.strip())
    if header:
        header_cf = [h.casefold() for h in header]
        col = col_index(header_cf, "display label", "source", "format", "empty behavior", "cross-ref")
        for cells in data_rows:
            if "display label" not in col:
                continue
            label = cell(cells, col, "display label", "")
            eid = _alloc(label)
            if eid is None:
                continue
            rows.append([
                eid, label, "display field", "—", "—", "Always", "—",
                cell(cells, col, "source"), cell(cells, col, "format"),
                cell(cells, col, "empty behavior"), cell(cells, col, "cross-ref", "N/A"),
            ])

    # --- S-07: client-side validation fields -> input E## rows + §6 rows -------
    cs_prefix, cs_header, cs_rows, cs_suffix = split_around_first_table(client_side_body)
    if cs_header is None:
        if cs_prefix.strip():
            client_side_notes.append(cs_prefix)
    else:
        client_side_notes.extend(t for t in (cs_prefix, cs_suffix) if t.strip())
        header_cf = [h.casefold() for h in cs_header]
        col = col_index(
            header_cf, "field", "type", "required", "constraints", "async check", "error message",
        )
        for cells in cs_rows:
            if "field" not in col:
                continue
            label = cell(cells, col, "field", "")
            key = label.strip().casefold()
            eid = label_to_id.get(key)
            is_new = eid is None
            if is_new:
                eid = _alloc(label)
            if eid is None:
                continue
            if is_new:
                rows.append([
                    eid, label, cell(cells, col, "type"), cell(cells, col, "required"),
                    "—", "Always", "—", "—", "—", "—", "N/A",
                ])
            rule = cell(cells, col, "constraints")
            feedback = cell(cells, col, "error message")
            validation_rows.append([eid, rule, feedback, "submit"])
            check = cell(cells, col, "async check", "")
            if check and check not in ("—", "-", "N/A"):
                async_checks.append((eid, check))

    # --- S-07(cont.): buttons/links named in Branches Decision point cells -----
    _, br_header, br_rows, _ = split_around_first_table(branches_body)
    if br_header:
        header_cf = [h.casefold() for h in br_header]
        col = col_index(header_cf, "decision point")
        if "decision point" in col:
            for cells in br_rows:
                dp = cell(cells, col, "decision point", "")
                m = _BUTTON_LINK_RE.match(dp.strip())
                if not m:
                    continue
                label = m.group(1).strip()
                eid = _alloc(label)
                if eid is None:
                    continue
                kind = "link" if label.lower().endswith("link") else "button"
                rows.append([eid, label, kind, "—", "—", "Always", "—", "—", "—", "—", "N/A"])

    table_text = build_table(ELEMENTS_HEADER, rows) if rows else ELEMENTS_NA_TEXT
    if data_notes:
        table_text = table_text + "\n\n" + "\n\n".join(data_notes)
    return ElementsResult(table_text, validation_rows, async_checks, data_notes, client_side_notes, len(rows))


def build_validation_section(elements: ElementsResult, server_side_body: str) -> str:
    """`## 6.`: mechanical client-side rows (S-07) always carried, plus any leftover
    prose/comment that sat around the old `### A) Client-side` table (or the whole
    body verbatim when it was a bare N/A line) -- never silently dropped just because
    it wasn't shaped like a table row. When the moved `### B) Server-side` block has
    real content pending a researcher's [L] judgment call (which submitting E## saw
    which message), a single scaffold row signals it rather than silently implying
    "nothing left to check here.\""""
    rows = list(elements.validation_rows)
    server_stripped = server_side_body.strip()
    # N/A bodies are conventionally backtick-wrapped in this corpus (e.g.
    # `` `N/A — no submit-style action handlers detected.` ``) -- strip the backticks
    # before the prefix check, matching `_audience_split_mode_c_lib.resolve_layout_rule_ids`.
    has_pending_server_rows = bool(server_stripped) and not server_stripped.strip("`").upper().startswith("N/A")
    if has_pending_server_rows:
        rows.append([
            "{…}", "{plain-language rule}", "{user-visible message text}",
            "{blur \\| change \\| submit \\| server response}",
        ])
    notes = "\n\n".join(elements.client_side_notes)
    if not rows:
        # The original `### A) Client-side` N/A text (verbatim) is a more precise
        # statement than a generic fallback -- prefer it when it exists.
        return notes or "N/A — no validation rules or submit-side error feedback detected."
    body = build_table(VALIDATION_HEADER, rows)
    return (notes + "\n\n" + body) if notes else body
