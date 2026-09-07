"""Parsers shared by build_traceability_matrix.py and validate_traceability_matrix.py.

Extracted to keep both scripts under the 200-LOC convention (mirrors _nav_lib.py /
_nav_table_parse_lib.py's role for build_navigation.py / validate_feature_screen_link.py).

Re-projection join graph (see docs-canonical-mapping.md — screen-list.md/user-stories.md/
behavior-logic.md/permissions-matrix.md all state "Feature mapping is managed in
FeatureList.md only"):

  F### -> SCR###/US###/BL###/PERM###  via generated/feature-list.md's per-F###
          "**Related X**:" bullets (the ONLY place that edge is recorded)
  F### -> ROUTE###                    via generated/route-list.md's own "Owner F###"
          column (route-list.md carries the edge itself — no feature-list.md hop needed)

Reuses _md_scan_lib for fence/comment-aware scanning — no hand-rolled markdown scanner.
Stdlib only, best-effort (never raises on malformed input).
"""
from __future__ import annotations

import re

from _md_scan_lib import iter_lines_with_fence, mask_fenced, split_table_row, strip_comments
from _nav_table_parse_lib import data_rows

_FCODE_H3_RE = re.compile(r"^###\s+(F\d{3})", re.IGNORECASE)
_RELATED_LABEL_RE = re.compile(
    r"^\*\*Related (Screens|User Stories|Background Logic|Permissions)\*\*:\s*$"
)
_RELATED_LABEL_KEY = {
    "Screens": "scr", "User Stories": "us",
    "Background Logic": "bl", "Permissions": "perm",
}

# Boundary-safe ID patterns — a bare trailing \b fails on "SCR001_LoginForm" ("_" is a
# word char); (?!\d) closes the over-match hazard ("SCR0011" resolving as "SCR001")
# without reintroducing that slug-defeated trailing boundary. House convention — see
# validate_feature_screen_link.py / _nav_table_parse_lib.py for the identical shape.
ID_PATTERNS: dict[str, re.Pattern] = {
    "scr": re.compile(r"\bSCR\d{3}(?!\d)"),
    "us": re.compile(r"\bUS\d{3}(?!\d)"),
    "bl": re.compile(r"\bBL\d{3}(?!\d)"),
    "perm": re.compile(r"\bPERM\d{3}(?!\d)"),
    "route": re.compile(r"\bROUTE\d{3}(?!\d)"),
    "tc": re.compile(r"\bTC\d{3}(?!\d)"),
    "f": re.compile(r"\bF\d{3}(?!\d)"),
}


def inventory(text: str, key: str) -> set[str]:
    """Whole-file existence scan for an ID family (fence/comment-safe)."""
    clean = mask_fenced(strip_comments(text))
    return {m.group(0).upper() for m in ID_PATTERNS[key].finditer(clean)}


def iter_tables(text: str) -> list[list[str]]:
    """Every contiguous run of `|`-prefixed lines in the document (fence-safe).

    route-list.md carries one Backend-Routes table per `### File:` sub-section — this
    walks all of them rather than assuming a single table (unlike `_first_table_after`,
    which stops at the first).
    """
    tables: list[list[str]] = []
    current: list[str] = []
    for ln in mask_fenced(text).splitlines():
        s = ln.strip()
        if s.startswith("|"):
            current.append(s)
        else:
            if current:
                tables.append(current)
                current = []
    if current:
        tables.append(current)
    return tables


def _parse_related(body: str) -> dict[str, list[str]]:
    """Extract SCR###/US###/BL###/PERM### tokens from a feature-list.md F### block's
    '**Related X**:' bullet groups (order-preserving, de-duplicated per key)."""
    result: dict[str, list[str]] = {"scr": [], "us": [], "bl": [], "perm": []}
    current: str | None = None
    for raw in body.splitlines():
        line = raw.strip()
        m = _RELATED_LABEL_RE.match(line)
        if m:
            current = _RELATED_LABEL_KEY[m.group(1)]
            continue
        if not line:
            current = None
            continue
        if current and line.startswith("-"):
            for mm in ID_PATTERNS[current].finditer(line):
                code = mm.group(0).upper()
                if code not in result[current]:
                    result[current].append(code)
        else:
            current = None
    return result


def parse_feature_details(text: str) -> dict[str, dict[str, list[str]]]:
    """Split feature-list.md's '## Feature Details' into one dict per F### (fence-aware)."""
    clean = strip_comments(text)
    sections: dict[str, dict[str, list[str]]] = {}
    current_fcode: str | None = None
    lines: list[str] = []
    for _, line, in_fence in iter_lines_with_fence(clean):
        m = _FCODE_H3_RE.match(line) if not in_fence else None
        if m:
            if current_fcode:
                sections[current_fcode] = _parse_related("\n".join(lines))
            current_fcode = m.group(1).upper()
            lines = []
            continue
        if current_fcode:
            if not in_fence and line.startswith("## "):
                sections[current_fcode] = _parse_related("\n".join(lines))
                current_fcode = None
                lines = []
            else:
                lines.append(line)
    if current_fcode:
        sections[current_fcode] = _parse_related("\n".join(lines))
    return sections


def parse_route_owners(text: str) -> dict[str, list[str]]:
    """F### -> [ROUTE###] from every Backend-Routes table's Code/Owner F### columns."""
    owners: dict[str, list[str]] = {}
    for table in iter_tables(text):
        if len(table) < 2:
            continue
        header = [h.casefold() for h in split_table_row(table[0])]
        code_idx = next((i for i, h in enumerate(header) if h == "code"), None)
        owner_idx = next((i for i, h in enumerate(header) if "owner" in h), None)
        if code_idx is None or owner_idx is None:
            continue
        for raw in data_rows(table):
            cells = split_table_row(raw)
            if max(code_idx, owner_idx) >= len(cells):
                continue
            code_m = ID_PATTERNS["route"].search(cells[code_idx])
            if not code_m:
                continue
            route_code = code_m.group(0).upper()
            for f_m in ID_PATTERNS["f"].finditer(cells[owner_idx]):
                fcode = f_m.group(0).upper()
                bucket = owners.setdefault(fcode, [])
                if route_code not in bucket:
                    bucket.append(route_code)
    return owners
