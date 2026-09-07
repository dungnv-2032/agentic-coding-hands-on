"""Engine 3 — the § 2 Functional Capabilities table parser for `functional-spec.md` (phase 09,
plans/260819-1016-rebuild-spec-capability-map).

[AD-6] SANCTIONED second § 2 parser. rebuild-spec's `_cap_table_lib.py` is the single § 2
contract THERE (phase 05 of the same plan forbids a second parser inside rebuild-spec). This
skill cannot import it: `audit-synthesis-judgment` is a separate skill with its own `scripts/`
tree, and cross-skill imports are not a pattern this kit relies on for load-bearing parsing (the
one soft exception, `_citation_lib._import_lang_lib`, is a best-effort optional enhancement that
degrades gracefully when absent — this parser is NOT optional, so that shape does not fit). A
second, independent implementation is therefore unavoidable here, which makes PINNING it
mandatory rather than merely permitted: `tests/test_cap_map_lib_parity.py` asserts this module
agrees with rebuild-spec's `_cap_table_lib` on the same fixture, so a future drift between the
two surfaces as a FAILING TEST, never as two silently different answers in two reports.

Mirrors rebuild-spec's conventions exactly (same header-substring column resolution, same
`US\\d{3}(?!\\d)` code regex with `(?!\\d)` — never a trailing `\\b`, which fails open on a
`US001_Slug` shape because `_` is a word character):
  - `_h2_bounds`      mirrors `validate_feature_spec.py::_bounds`
  - `data_rows`       mirrors `_cap_table_lib.data_rows` (same placeholder/empty-cell filter)
  - `resolve_us_column` mirrors `_cap_table_lib.claim_columns` narrowed to the "US" family

Stdlib only. No I/O — callers hand this module already-read file text.
"""
from __future__ import annotations

import re

_H2_RE = re.compile(r"^## \d+\. ")
_CAP_HEADING = "## 2. Functional Capabilities"
_SEVEN_HEADING = "## 7. User Stories"
_US_COLUMN_SUBSTRING = "user stor"  # casefolded — matches "User Stories" header cell
_REQ_COLUMN_SUBSTRING = "requirement"  # matches "Requirements" header cell
_BR_COLUMN_SUBSTRING = "business rul"  # matches "Business Rules" header cell
_SCR_COLUMN_SUBSTRING = "screen"  # matches "Screens" header cell
_US_CODE_RE = re.compile(r"\bUS\d{3}(?!\d)")
_FR_CODE_RE = re.compile(r"\bFR-\d{3}(?!\d)")
_BR_CODE_RE = re.compile(r"\bBR-\d{3}(?!\d)")
_SCR_CODE_RE = re.compile(r"\bSCR\d{3}(?!\d)")
# [SA-1 precedent, phase 06] `[ \t]*` cannot cross a newline, so an EMPTY label can never match
# this pattern at all — mirrored verbatim from rebuild-spec's `validate_feature_spec.py`
# `_FUNC_CAP_RATIONALE_RE` (never `\s*`, which walks past the label's own line).
_CAP_RATIONALE_RE = re.compile(
    r"^\*\*Single-capability rationale:\*\*[ \t]*(?P<body>\S[^\n]*)$", re.MULTILINE)
# `###\s+US###_Slug...` headings inside § 7, title after an em-dash or hyphen separator —
# DISTINCT from `_ipe_parse_lib._US_HEADER_RE`, which parses `user-stories.md`'s own
# `## US###: title` shape (different artifact, different heading depth, different separator).
# The `code` group captures ONLY the bare `US\d{3}` — never the `_Slug` suffix — so it keys the
# same way § 2's `_US_CODE_RE` claim codes do; the optional slug is matched but not captured.
_US7_HEADING_RE = re.compile(
    r"^###\s+(?P<code>US\d{3})(?!\d)[A-Za-z0-9_]*\s*(?:—|-)\s*(?P<title>.+?)\s*$")


def _h2_bounds(lines: list[str], heading: str) -> tuple[int, int] | None:
    """Locate `heading`'s body span among top-level `## N. ` headings — the next top-level
    heading (or EOF) ends it. `None` when `heading` is absent entirely."""
    h2 = [(i, ln.rstrip()) for i, ln in enumerate(lines) if _H2_RE.match(ln)]
    for i, (idx, h) in enumerate(h2):
        if h == heading:
            end = h2[i + 1][0] if i + 1 < len(h2) else len(lines)
            return idx + 1, end
    return None


def data_rows(lines: list[str], bounds: tuple[int, int] | None) -> tuple[list[str], list[list[str]]]:
    """Header cells (casefolded) and the filtered § 2 data rows, each row split into stripped
    cells. `bounds` absent, or no `|`-prefixed lines at all inside it, both return `([], [])` —
    the caller decides what that means (no § 2 vs. a header-only § 2 are different signals)."""
    if not bounds:
        return [], []
    section_lines = lines[bounds[0]:bounds[1]]
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


def resolve_us_column(header_cells: list[str]) -> int | None:
    """Casefolded-substring column resolution — position-independent, matching the
    `_cap_table_lib.claim_columns` idiom. `None` when no header cell mentions "user stor(ies)"."""
    return next((i for i, h in enumerate(header_cells) if _US_COLUMN_SUBSTRING in h), None)


def us_claim_sets(text: str) -> list[set[str]]:
    """Per-CAP-row US claim sets from a `functional-spec.md`'s § 2 table, in row order.

    Returns `[]` when `## 2. Functional Capabilities` is missing, or is present with zero data
    rows (placeholder/header-only § 2) — both mean "no rows to measure". A non-empty return with
    every set empty means "rows exist but no row's User Stories cell resolved any US### code" —
    the caller (judgment_engine._feature_metrics) is the one that decides that shape is an
    [AD-3] OMIT, not this module's concern (this module reports what it parsed, nothing more).
    """
    lines = text.splitlines()
    bounds = _h2_bounds(lines, _CAP_HEADING)
    header_cells, rows = data_rows(lines, bounds)
    if not rows:
        return []
    us_idx = resolve_us_column(header_cells)
    if us_idx is None:
        return [set() for _ in rows]
    return [
        set(_US_CODE_RE.findall(row[us_idx])) if us_idx < len(row) else set()
        for row in rows
    ]


def resolve_column(header_cells: list[str], substring: str) -> int | None:
    """Casefolded-substring column resolution, generalised from `resolve_us_column` for the
    other § 2 code families (phase 10, capability-intent). `None` when no header cell matches."""
    return next((i for i, h in enumerate(header_cells) if substring in h), None)


def cap_rows(text: str) -> list[dict]:
    """Per-CAP-row struct for the capability-intent dimension (phase 10): `id` plus the claimed
    code sets by family (`us`, `fr`, `br`, `scr`). Reads the SAME § 2 table `us_claim_sets` does,
    through the SAME `_h2_bounds`/`data_rows` bounds and placeholder filtering — this is one more
    column read off an already-located row, never a second table scan with different rules (AD-6:
    a divergent second reading of § 2 inside this same module would defeat the whole point of
    having a single sanctioned parser).

    Returns `[]` under the same conditions `us_claim_sets` does (§ 2 absent or header-only).
    The `id` column resolves to header cell "id" (exact, casefolded) and falls back to column 0
    — the template's stable position — rather than `None`, because every CAP row needs SOME
    identifier for the anchor string; a row can never emit a candidate with a blank one.
    """
    lines = text.splitlines()
    bounds = _h2_bounds(lines, _CAP_HEADING)
    header_cells, rows = data_rows(lines, bounds)
    if not rows:
        return []
    id_idx = next((i for i, h in enumerate(header_cells) if h == "id"), 0)
    us_idx = resolve_us_column(header_cells)
    fr_idx = resolve_column(header_cells, _REQ_COLUMN_SUBSTRING)
    br_idx = resolve_column(header_cells, _BR_COLUMN_SUBSTRING)
    scr_idx = resolve_column(header_cells, _SCR_COLUMN_SUBSTRING)

    def _cell(row: list[str], idx: int | None) -> str:
        return row[idx] if idx is not None and idx < len(row) else ""

    out: list[dict] = []
    for i, row in enumerate(rows):
        cap_id = _cell(row, id_idx).strip() or f"CAP-{i + 1:02d}"
        out.append({
            "id": cap_id,
            "us": set(_US_CODE_RE.findall(_cell(row, us_idx))),
            "fr": set(_FR_CODE_RE.findall(_cell(row, fr_idx))),
            "br": set(_BR_CODE_RE.findall(_cell(row, br_idx))),
            "scr": set(_SCR_CODE_RE.findall(_cell(row, scr_idx))),
        })
    return out


def section7_us_titles(text: str) -> dict[str, str]:
    """US-code → title map from `functional-spec.md`'s own § 7 `### US###_Slug — Title`
    headings. DISTINCT from `_ipe_parse_lib.parse().us_titles`, which reads the promoted
    `user-stories.md`'s own `## US###: title` shape — a different artifact, a different heading
    depth and separator. This is a different SECTION of the same artifact `us_claim_sets` and
    `cap_rows` already read, not a third § 2 parser (§ 7 is not § 2)."""
    lines = text.splitlines()
    bounds = _h2_bounds(lines, _SEVEN_HEADING)
    if not bounds:
        return {}
    titles: dict[str, str] = {}
    for line in lines[bounds[0]:bounds[1]]:
        m = _US7_HEADING_RE.match(line.rstrip())
        if m:
            titles[m.group("code")] = m.group("title").strip()
    return titles


def single_capability_rationale(text: str) -> str | None:
    """The `**Single-capability rationale:**` body, scoped to § 2 only — mirrors rebuild-spec's
    own `_cap_rationale_verdict`, which also scopes its search to `section2_text` alone (a
    rationale-shaped line quoted elsewhere in the document is not this feature's own claim).
    `None` when § 2 is absent or carries no such line."""
    lines = text.splitlines()
    bounds = _h2_bounds(lines, _CAP_HEADING)
    if not bounds:
        return None
    section_text = "\n".join(lines[bounds[0]:bounds[1]])
    m = _CAP_RATIONALE_RE.search(section_text)
    return m.group("body").strip() if m else None
