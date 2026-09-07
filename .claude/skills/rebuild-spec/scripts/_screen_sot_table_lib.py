"""Fence-aware markdown table parsing shared by the SOT composer siblings.

Phase 05 (plans/260818-1332-rebuild-spec-human-readable-sot): every sibling that reads
a v27-shaped table (Data Inventory, Client-side validation, Branches, Layout Regions,
Accessibility, Conditional Rendering) needs the same primitive: find the first REAL
(non-fenced) markdown table in a section body, split it into header/rows, and hand back
whatever text sits before/after it so callers never silently drop that surrounding
content (the exact class of bug fixed in `_audience_split_data_inventory_lib.py`).
Stdlib only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _md_scan_lib import iter_lines_with_fence, split_table_row  # noqa: E402

_TABLE_SEP_RE = re.compile(r"^\s*\|?[\s:|-]+\|?\s*$")


def split_around_first_table(
    body: str,
) -> tuple[str, list[str] | None, list[list[str]], str]:
    """Fence-aware: locate the first real markdown table (a `|`-led header line
    immediately followed by a separator line) in *body*.

    Returns `(prefix, header, data_rows, suffix)`. When no table is found, `header` is
    `None`, `data_rows` is `[]`, `prefix == body.strip("\\n")`, and `suffix == ""` --
    the whole body is handed back as `prefix` so a caller that only wants "the leftover
    text" never has to special-case the no-table case.
    """
    lines_ctx = list(iter_lines_with_fence(body))
    all_lines = [line for _, line, _ in lines_ctx]
    n = len(lines_ctx)
    for i in range(n - 1):
        _, line, in_fence = lines_ctx[i]
        if in_fence or not line.strip().startswith("|"):
            continue
        _, next_line, next_in_fence = lines_ctx[i + 1]
        if next_in_fence or not _TABLE_SEP_RE.match(next_line):
            continue
        header = split_table_row(line)
        rows: list[list[str]] = []
        j = i + 2
        while j < n:
            _, row_line, row_in_fence = lines_ctx[j]
            if row_in_fence or not row_line.strip().startswith("|"):
                break
            rows.append(split_table_row(row_line))
            j += 1
        prefix = "\n".join(all_lines[:i]).strip("\n")
        suffix = "\n".join(all_lines[j:]).strip("\n")
        return prefix, header, rows, suffix
    return body.strip("\n"), None, [], ""


def build_table(header: list[str], rows: list[list[str]]) -> str:
    """Render a markdown table from a header row and data rows. Column widths in the
    separator row are sized off the header text, mirroring the regeneration style
    already used by `_audience_split_data_inventory_lib.reshape_data_inventory`."""
    out = ["| " + " | ".join(header) + " |"]
    out.append("|" + "|".join("-" * max(3, len(h) + 2) for h in header) + "|")
    for row in rows:
        out.append("| " + " | ".join(row) + " |")
    return "\n".join(out)


def col_index(header_cf: list[str], *names: str) -> dict[str, int]:
    """`{name: index}` for every *names* entry present (casefold-compared) in
    *header_cf* -- absent names are simply omitted, never raise."""
    return {name: header_cf.index(name) for name in names if name in header_cf}


def cell(cells: list[str], col: dict[str, int], name: str, default: str = "—") -> str:
    """`cells[col[name]]` if *name* was found and the row is long enough, else
    *default* -- the single guard every column lookup in this module needs."""
    idx = col.get(name)
    if idx is None or idx >= len(cells):
        return default
    return cells[idx]
