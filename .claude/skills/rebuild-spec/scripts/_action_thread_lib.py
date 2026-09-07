"""Action-thread parsing (D2) — the § 2 Action Index table, § 3 action-block bounds,
and the fixed rung set inside each action block. Phase 02 of
plans/260824-1128-rebuild-spec-action-thread-v27-7 (D2, D4).

`validate_feature_spec.py` wires the 6 new `FeatureSpec.action_*`/`rung_*` checks
against what this module parses; per the phase's Architecture note, the table/heading
parse happens HERE exactly once, so the validator never re-derives it — mirrors how
`_cap_table_lib` is the sole § 2 Functional Capabilities parser for the twin
(AD-6-equivalent discipline for this new binding).

No family-code regex lives here. `_FAMILY_CODE_RE` (US/FR/BR family classification)
stays defined in `validate_feature_spec.py`, which already imports it for every other
check in that file; this module cannot import it back (that file will import THIS
module — a reverse import would be circular) and the phase explicitly forbids a
second family-code regex. So `parse_action_index` hands back raw strings (the Codes
column's comma-split tokens) and the caller classifies them by family.
"""
from __future__ import annotations

import re

from _spec_constants import ACTION_HEADING_RE, ACTION_ID_RE

_ACTION_HEADING_RE = re.compile(ACTION_HEADING_RE)
_ACTION_ID_RE = re.compile(ACTION_ID_RE)

# § 2 Action Index row's `#` column: `**A0**`, `**A12**`, ...
_ROW_ID_RE = re.compile(r"^\*\*(A\d+)\*\*$")

# D2 — the handler-fallback shape: a bare backticked `` `METHOD PATH` `` in the
# Action (handler) column instead of `` `Class#method` ``. Matched against the WHOLE
# cell (`fullmatch` via `$`/`^` anchors) — a real handler cell that merely CONTAINS an
# HTTP-verb-looking substring elsewhere must not be misread as this fallback shape.
# The caller never calls this for the `A0` row: A0's cell is an italic cross-cutting
# label, not a handler slot to begin with.
_METHOD_PATH_FALLBACK_RE = re.compile(
    r"^`(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+\S+`$"
)

# Method · Path column's two-backtick-token shape: `` `GET` `.../path` ``.
_TWO_BACKTICK_RE = re.compile(r"^`([^`]+)`\s+`([^`]+)`$")

# A rendered rung line. Six of the seven rungs are `**<Label>** · <body-start>`.
# `**Source**` is the ONE exception — D3 requires it to satisfy
# `derive_confidence_report.py:29`'s `CITATION_RE`
# (`\*\*Source:\*\*\s+`?([^`\n:]+):(\d+)(?:-(\d+))?`?`), which needs the colon INSIDE
# the bold markup and plain whitespace after it, not the ` · ` middot separator every
# other rung uses. Verified empirically (wire-format-contract.md correction,
# 2026-08-24): `**Source** · ` and `**Source:** · ` both fail that regex; only
# `**Source:** ` (colon, then whitespace, no middot) matches. Two alternatives, not
# one uniform pattern — an extractor that only recognizes the middot shape silently
# never sees the Source rung at all, which would make `rung_order`/
# `rung_empty_rendered` gates that cannot fail on it (see TestSourceRungBothShapes).
# Labels spelled out literally (not built from `_spec_constants.RUNG_LABELS`) because
# a rung-line pattern is not a family-code regex and carries none of that hazard —
# keep the two lists in lockstep by inspection. `State` (phase 01, self-sufficiency
# v27.8) joins the middot group like its five siblings; it is never sniffed from
# prose (D3) — it is only ever a rendered rung line, matched here exactly the same
# way as Who/FE/Request/BE/Rule/Result.
_RUNG_LINE_RE = re.compile(
    r"^\*\*(Who|FE|Request|BE|Rule|Result|State)\*\*\s*·\s*(.*)$"
    r"|^\*\*(Source):\*\*\s+(.*)$"
)


def _match_rung_line(line: str) -> tuple[str, str] | None:
    """`(label, first_line_remainder)` for a rung line in either shape (see
    `_RUNG_LINE_RE`), or `None`. Normalizes to the bare label (`"Source"`, not
    `"Source:"`) so callers never need to know which shape matched."""
    m = _RUNG_LINE_RE.match(line)
    if not m:
        return None
    if m.group(1) is not None:
        return m.group(1), m.group(2)
    return m.group(3), m.group(4)


def is_handler_fallback(key: str) -> bool:
    """True when `key` (the Action (handler) column's raw cell text) is the bare
    `` `METHOD PATH` `` fallback the wire-format contract reserves for a genuinely
    unparseable handler — the shape that fires `FeatureSpec.action_key_not_handler`."""
    return bool(_METHOD_PATH_FALLBACK_RE.match(key.strip()))


def _split_method_path(cell: str) -> tuple[str, str]:
    """`` `GET` `.../path` `` -> ("GET", ".../path"); `queue · \\`Delayed::Job\\`` ->
    ("queue", "Delayed::Job"); a literal `—` (neither applies) -> ("—", "")."""
    cell = cell.strip()
    if cell in ("—", "-", ""):
        return cell or "—", ""
    m = _TWO_BACKTICK_RE.match(cell)
    if m:
        return m.group(1), m.group(2)
    if "·" in cell:
        left, _, right = cell.partition("·")
        return left.strip().strip("`"), right.strip().strip("`")
    return cell.strip("`"), ""


def _split_csv_cell(cell: str, strip_backticks: bool) -> list[str]:
    """Comma-space separated tokens; a `—`-shaped cell (optionally with a trailing
    italic reason, e.g. `— *(read-only)*`) yields `[]` — there is nothing to list."""
    cell = cell.strip()
    if not cell or cell.startswith("—") or cell.startswith("-"):
        return []
    tokens = [c.strip() for c in cell.split(",") if c.strip()]
    return [t.strip("`") for t in tokens] if strip_backticks else tokens


def parse_action_index(lines: list[str], bounds: tuple[int, int] | None) -> list[dict]:
    """Parse `## 2. Action Index`'s table into row dicts, ONCE — every action-thread
    check reads this return value rather than re-splitting `|` rows itself.

    `bounds` absent, or fewer than 2 `|`-prefixed lines inside it (no real header +
    separator), both return `[]` — the caller (`action_index_missing`) decides what
    an empty return means (absent section vs. zero data rows are both "nothing to
    claim with", which is exactly the condition that check fires on).

    Each row: `{id, key, method, path, codes, tables, detail, line}`. `codes` and
    `tables` are already comma-split into bare tokens (`codes` keeps its `-`/digits
    intact for the caller's family regex; `tables` has its backticks stripped since
    nothing downstream needs them). `line` is the absolute 0-indexed source line, for
    issue locations. Header/separator rows and any placeholder row (`{...}` first
    cell — mirrors `_cap_table_lib.data_rows`) are skipped."""
    if not bounds:
        return []
    start, end = bounds
    table_lines = [(i, lines[i]) for i in range(start, end) if lines[i].strip().startswith("|")]
    if len(table_lines) < 2:
        return []
    rows: list[dict] = []
    for i, raw in table_lines[2:]:  # skip header + markdown separator row
        cells = [c.strip() for c in raw.strip().strip("|").split("|")]
        if len(cells) < 6 or not cells[0] or cells[0].startswith("{"):
            continue
        m = _ROW_ID_RE.match(cells[0])
        row_id = m.group(1) if m else cells[0].strip("*")
        method, path = _split_method_path(cells[2])
        rows.append({
            "id": row_id,
            "key": cells[1],
            "method": method,
            "path": path,
            "codes": _split_csv_cell(cells[3], strip_backticks=False),
            "tables": _split_csv_cell(cells[4], strip_backticks=True),
            "detail": cells[5],
            "line": i,
        })
    return rows


def action_blocks(headings: list[tuple[int, str]], total: int) -> list[dict]:
    """Per-action-block bounds: one entry per `#### A<n> · ...` H4 heading
    (`ACTION_HEADING_RE`), bounded at the next H2/H3/H4 heading of ANY kind, or
    `total`. `ids` holds every action ID the heading text carries — usually one, but
    two actions may share a single H4 (`#### A7 · ... · A8 · ...`), so this scans the
    WHOLE heading line with `ACTION_ID_RE`, not just the anchored leading id
    `ACTION_HEADING_RE` itself captures."""
    action_idx = [(i, h) for i, h in headings if _ACTION_HEADING_RE.match(h)]
    bound_idx = sorted(
        i for i, h in headings
        if h.startswith("## ") or h.startswith("### ") or h.startswith("#### ")
    )
    blocks: list[dict] = []
    for idx, h in action_idx:
        nxt = next((b for b in bound_idx if b > idx), total)
        blocks.append({
            "ids": _ACTION_ID_RE.findall(h),
            "heading_line": idx,
            "start": idx + 1,
            "end": nxt,
        })
    return blocks


def rungs(lines: list[str], block: dict) -> list[tuple[str, str]]:
    """Ordered `(label, body)` pairs for every rung line found inside `block`'s
    bounds (see `action_blocks`). `body` is the rung's full rendered text — the first
    line's remainder after the `**Label** · ` marker, plus every continuation line up
    to the next rung marker or the block's end, joined and stripped.

    A rung whose label never appears in the block is simply absent from the returned
    list — presence is never required (only the RELATIVE ORDER of whichever rungs DO
    appear), matching the wire-format contract's "an absent rung is omitted entirely,
    never stubbed" rule. Duplicate labels inside one block are returned as separate
    entries in encounter order — the caller's order check treats that as a real
    ordering defect rather than silently merging them."""
    found: list[tuple[str, int, str]] = []  # (label, start_line, first_line_remainder)
    for i in range(block["start"], block["end"]):
        matched = _match_rung_line(lines[i])
        if matched:
            found.append((matched[0], i, matched[1]))
    result: list[tuple[str, str]] = []
    for k, (label, start_line, remainder) in enumerate(found):
        end_line = found[k + 1][1] if k + 1 < len(found) else block["end"]
        body_lines = [remainder] + lines[start_line + 1:end_line]
        result.append((label, "\n".join(body_lines).strip()))
    return result
