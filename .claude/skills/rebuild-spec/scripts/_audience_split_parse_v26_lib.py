"""Mode A -- parse an OLD (pre-audience-split) v26 4-file feature dir into a structured
dict the renderer (`_audience_split_compose_a_lib.py`) consumes.

The four v26 files: `business-context.md`, `screens.md`, `edge-cases.md` (retired
satellites, absorbed into `functional-spec.md`) + `technical-spec.md` (kept, but
reshaped: old block heading form `### BR-001_Slug` -> `### {sentence} (BR-001)`, and
two fields move out -- BR's `**Rule:**` and DEC's `**user_visible_outcome:**`). The
old-block (BR/DEC/SM/ALG/INT) parsing itself lives in
`_audience_split_parse_old_blocks_lib.py` (split out to keep each module under the
repo's 200-line guidance); this module re-exports it alongside the business-context/
screens/edge-cases/user-stories/verification parsers so `_audience_split_compose_a_lib.py`
has one import surface.

Stdlib only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _audience_split_md_sections_lib import split_sections  # noqa: E402
from _audience_split_parse_old_blocks_lib import (  # noqa: E402,F401
    field, find_old_blocks, sentence_for_block, slug_to_words, unique_by_code,
)
from _nav_table_parse_lib import _first_table_after, _split_row, data_rows  # noqa: E402
from _spec_parse import parse_headings_and_blocks  # noqa: E402

_NEEDS_CONFIRM_RE = re.compile(r"\[NEEDS_DOMAIN_CONFIRMATION\]")
_FR_TABLE_ROW_RE = re.compile(r"^FR-(\d{3})$")
_FR_BULLET_RE = re.compile(r"^-\s+\*\*FR-(\d{3})\*\*\s+(.+?)(?:\s+—.*)?\s*$")
_SC_LINE_RE = re.compile(r"\*\*SC-\d{3}\*\*\s+(.+?)\s*\(covers\s+([^)]+)\)")
_US_HEADING_RE = re.compile(
    r"^###\s+(US\d{3}[A-Za-z0-9_]*)\s*(?:—|-)\s*(.+?)\s*\(Priority:\s*(P\d)\)\s*$"
)
_GIVEN_WHEN_THEN_RE = re.compile(
    r"\*\*Given\*\*\s*(.+?),\s*\*\*When\*\*\s*(.+?),\s*\*\*Then\*\*\s*(.+?)\.?\s*$",
    re.MULTILINE,
)
_LIST_PREFIX_RE = re.compile(r"^\s*(?:\d+\.|[-*])\s*")


def parse_fr_items(tech_text: str) -> dict[str, str]:
    """Every FR code declared anywhere -- the CCL `### Requirements` table AND every
    US's `**Requirements fulfilled:**` bullet -- code -> one-sentence description."""
    items: dict[str, str] = {}
    table = _first_table_after(tech_text, r"###\s*Requirements\s*$")
    for row in data_rows(table):
        cells = _split_row(row)
        if len(cells) < 2:
            continue
        m = _FR_TABLE_ROW_RE.match(cells[0])
        if m and cells[1] and not cells[1].startswith("{"):
            items.setdefault(f"FR-{m.group(1)}", cells[1].strip())
    for line in tech_text.splitlines():
        m = _FR_BULLET_RE.match(line.strip())
        if m:
            items.setdefault(f"FR-{m.group(1)}", m.group(2).strip())
    return items


def parse_verification_fr_map(tech_text: str) -> dict[str, list[str]]:
    """`- **SC-001** {condition} (covers FR-001, BR-001)` -> {FR-001: [condition, ...]}
    -- feeds functional-spec.md §9 Edge Behaviours to Verify (back-references an FR).
    Per-code condition list is de-duplicated (order preserved) -- an SC-### line that's
    restated verbatim under a US's own `**Verification:**` (matching
    `technical-spec-template.md`'s own shape) must not double-report the same check."""
    out: dict[str, list[str]] = {}
    for m in _SC_LINE_RE.finditer(tech_text):
        condition, covers = m.group(1).strip(), m.group(2)
        for code in re.findall(r"FR-\d{3}", covers):
            bucket = out.setdefault(code, [])
            if condition not in bucket:
                bucket.append(condition)
    return out


def parse_user_stories(tech_text: str) -> list[dict]:
    """Each `### {US###} — {Title} (Priority: P#)` block: narrative (`**What
    happens:**`) + Given/When/Then acceptance scenarios."""
    lines = tech_text.splitlines()
    headings, _ = parse_headings_and_blocks(lines)
    us_heads = [(idx, m) for idx, raw in headings if (m := _US_HEADING_RE.match(raw))]
    stories: list[dict] = []
    for k, (idx, m) in enumerate(us_heads):
        end = us_heads[k + 1][0] if k + 1 < len(us_heads) else len(lines)
        body = "\n".join(lines[idx + 1:end])
        scenarios = [
            {"given": gm.group(1).strip(), "when": gm.group(2).strip(), "then": gm.group(3).strip()}
            for gm in _GIVEN_WHEN_THEN_RE.finditer(body)
        ]
        stories.append({
            "code": m.group(1), "title": m.group(2).strip(), "priority": m.group(3),
            "narrative": field(body, "What happens"), "scenarios": scenarios,
        })
    return stories


def parse_needs_confirmation(*texts: str) -> list[str]:
    """One entry per `[NEEDS_DOMAIN_CONFIRMATION]` marker across all four v26 files --
    the containing line, marker + any leading numbered-list/bullet prefix stripped and
    whitespace collapsed -- promoted to functional-spec.md § 2 Open Decisions rows
    (never left inline, per Requirement 4)."""
    out: list[str] = []
    for text in texts:
        for line in text.splitlines():
            if _NEEDS_CONFIRM_RE.search(line):
                cleaned = _NEEDS_CONFIRM_RE.sub("", line)
                cleaned = _LIST_PREFIX_RE.sub("", cleaned)
                out.append(re.sub(r"\s+", " ", cleaned).strip(" -*"))
    return out


def parse_business_context(text: str) -> dict:
    _, h2 = split_sections(text, 2)
    return {
        "why_it_matters": h2.get("## Why It Matters", "").strip(),
        "who_uses_it": h2.get("## Who Uses It", "").strip(),
        "what_they_do": h2.get("## What They Do", "").strip(),
        "unresolved_questions": h2.get("## Unresolved Questions", "").strip(),
    }


_BACKGROUND_RE = re.compile(r"N/A\s+—\s+background feature", re.IGNORECASE)


def parse_screens(text: str) -> dict:
    _, h2 = split_sections(text, 2)
    body = h2.get("## Screen List", "")
    table = _first_table_after(text, r"##\s*Screen List\s*$")
    # Phase-05 (B4c): header-driven rendering needs the header row itself, not
    # just the data rows -- `render_screens` no longer reads cells[1] positionally.
    header = _split_row(table[0]) if table else []
    rows = [_split_row(r) for r in data_rows(table) if not _split_row(r)[0].startswith("{")]
    # Widen background detection: normally the marker is inside the "## Screen
    # List" H2 body, but fall back to a whole-file scan when no table was found
    # at all -- covers a dir with no "## Screen List" heading to anchor on.
    background = bool(_BACKGROUND_RE.search(body)) or (
        not table and bool(_BACKGROUND_RE.search(text))
    )
    return {
        "background": background, "rows": rows, "header": header,
        "user_journey": h2.get("## User Journey", "").strip(),
    }


def parse_edge_cases(text: str) -> list[list[str]]:
    table = _first_table_after(text, r"#\s+Edge Cases\b")
    return [_split_row(r) for r in data_rows(table) if not _split_row(r)[0].startswith("{")]
