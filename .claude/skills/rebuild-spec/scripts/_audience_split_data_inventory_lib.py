"""Data Inventory `Field` -> `Display Label` column reshape (Mode C, Phase 02 Requirement).

Split out of `_audience_split_mode_c_lib.py` to keep each module under the repo's
200-line guidance. Stdlib only.

Phase 05 ADDENDUM fix (plans/260818-1332-rebuild-spec-human-readable-sot): this function
used to (a) scan every PHYSICAL line with a plain regex, so a fenced code sample whose
lines happened to start with `|` was mistaken for the real table, and (b) rebuild its
output from ONLY the lines it recognized as table rows, silently dropping any prefix,
interleaved, or trailing non-table content (comments, notes) in the section body. Both
were bugs, not a contract -- reported active data loss in a migration already run over
the real corpus (see the phase's ADDENDUM). Fixed here by (1) routing the table-row scan
through the shared `_md_scan_lib.iter_lines_with_fence` primitive, consistent with every
other scanner in this skill, and (2) rebuilding the output line-by-line over the ORIGINAL
line sequence, only substituting the lines identified as real table rows and copying
every other line through verbatim, wherever it sits.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _md_scan_lib import iter_lines_with_fence, split_table_row  # noqa: E402

_DATA_INV_ROW_RE = re.compile(r"^\s*\|")
_TABLE_SEP_RE = re.compile(r"^\s*\|[\s:|-]+\|\s*$")


def reshape_data_inventory(body: str) -> str:
    """Drop the `Field` column, promote `Display Label` to the sole identity column;
    a Field value that differs from Display Label survives as `(binding: {field})` on
    the Cross-ref cell instead of being discarded outright. Fence-aware: a fenced code
    sample is never mistaken for the real table. Every non-table-row line -- prefix,
    interleaved, or trailing -- is preserved verbatim in its original position."""
    all_lines = [line for _, line, _ in iter_lines_with_fence(body)]
    table_idx = [
        i for i, (_, line, in_fence) in enumerate(iter_lines_with_fence(body))
        if not in_fence and _DATA_INV_ROW_RE.match(line)
    ]
    if len(table_idx) < 2:
        return body  # no parseable REAL (non-fenced) table -- leave untouched
    header = split_table_row(all_lines[table_idx[0]])
    header_cf = [h.casefold() for h in header]
    if "field" not in header_cf or "display label" not in header_cf:
        return body  # already reshaped, or not the expected shape -- leave untouched
    field_i = header_cf.index("field")
    label_i = header_cf.index("display label")
    cross_i = header_cf.index("cross-ref") if "cross-ref" in header_cf else None
    keep = [i for i in range(len(header)) if i != field_i]
    new_header = [header[label_i]] + [header[i] for i in keep if i != label_i]

    out = list(all_lines[:table_idx[0]])  # prefix before the table, untouched
    out.append("| " + " | ".join(new_header) + " |")
    prev_idx = table_idx[0]
    for i in table_idx[1:]:
        # Preserve any non-table-row content interleaved since the last table line
        # (the BUG-2 fix: this used to be silently dropped for the trailing case, and
        # was never even considered for the interleaved case).
        out.extend(all_lines[prev_idx + 1:i])
        line = all_lines[i]
        if _TABLE_SEP_RE.match(line):
            out.append("|" + "|".join(["-" * max(3, len(c) + 2) for c in new_header]) + "|")
            prev_idx = i
            continue
        cells = split_table_row(line)
        if len(cells) <= max(field_i, label_i):
            out.append(line)  # malformed/placeholder row -- pass through unchanged
            prev_idx = i
            continue
        field_val, label_val = cells[field_i], cells[label_i]
        rest_cells = [cells[i] for i in keep if i != label_i and i < len(cells)]
        if cross_i is not None and field_val and field_val != label_val and field_val != "-":
            rest_idx = [i for i in keep if i != label_i].index(cross_i) if cross_i in keep else None
            if rest_idx is not None and rest_idx < len(rest_cells):
                suffix = f" (binding: `{field_val}`)"
                rest_cells[rest_idx] = (rest_cells[rest_idx] + suffix).strip()
        out.append("| " + " | ".join([label_val] + rest_cells) + " |")
        prev_idx = i
    # Preserve everything after the LAST table row too (the BUG-2 fix proper).
    out.extend(all_lines[prev_idx + 1:])
    return "\n".join(out)
