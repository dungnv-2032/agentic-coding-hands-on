"""content-preservation-map.md § C: `## 4. Technical Behavior by Capability`
(T-10/T-11/T-17/T-18) -- including **T-12, the single sanctioned REMOVE in the
entire plan.** Split out of `_feature_sot_technical_lib.py` to hold the repo's
200-line guidance, and to keep the guard's two branches easy to find and test in
isolation.

T-12 GUARD (mandatory, unit-tested, both branches): a per-US `**What happens:**`
narrative is REMOVED only when the twin functional-spec.md's `## 7. User Stories`
carries that exact `US###` code. If it does not, the narrative is instead CARRIED
forward here, prefixed `[UNVERIFIED] carried from technical-spec §User Stories — `.
An unconditional delete is a plan violation (content-preservation-map.md's own
words) -- this is the single highest-consequence line of code in the whole plan.

Bucket count (T-10/T-11's dynamic `### 4.N`): one per `CAP-N` row in the twin's
`## 2. Functional Capabilities`, in CAP- order; exactly one `### 4.1 {Feature name}`
when that section is absent/empty (target-shape-spec.md § 3). The mechanical migrate
step ALWAYS routes every BR/DEC/edge-case block into the FIRST bucket --
redistributing across a real multi-capability twin is the [L] regrouping pass a
researcher performs once § 2 is filled; this module must never guess it, and must
never name a capability the twin does not carry (risk table, phase-10.md).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _audience_split_md_sections_lib import split_sections  # noqa: E402
from _feature_sot_extract_lib import CclPieces, UsBlock  # noqa: E402
from _feature_sot_mapping_lib import _CODE_RE  # noqa: E402
from _screen_sot_table_lib import cell, col_index, split_around_first_table  # noqa: E402

_US_HEADING_CODE_RE = re.compile(r"^###\s+(US\S+)\b")
_CARRIED_PREFIX = "[UNVERIFIED] carried from technical-spec §User Stories — "

_BR_NA = "N/A — no BR-### blocks routed to this capability."
_DEC_NA = "N/A — no user-facing decision logic beyond DISC-### Polymorphic Behavior."
_EDGE_NA = "| Scenario | Behavior |\n|----------|----------|\n\nN/A — no edge cases carried from technical-spec.md."
_REGROUP_NA = "N/A — pending manual regrouping once capability boundaries are confirmed."


def twin_us_codes(twin_functional_text: str) -> set[str]:
    """T-12 guard's predicate source: the twin's `## 7. User Stories` US### code
    set. Falls back to scanning the whole twin text for `### US### —` headings if
    the twin isn't SOT-shaped yet (shouldn't happen in practice -- `feature-sot`'s
    own step always composes functional first -- but a guard must never crash or
    remove blind just because its input arrived in an unexpected shape)."""
    _, h2 = split_sections(twin_functional_text, 2)
    body = h2.get("## 7. User Stories", twin_functional_text)
    return {m.group(1) for m in _US_HEADING_CODE_RE.finditer(body)}


# Phase 03 (defect 1): the twin's own § 2 table is the single declared source for
# BOTH the CAP row list (`cap_buckets`) and the code->capability map
# (`cap_code_map`) -- one parse helper, not two copies of
# `split_around_first_table` + `col_index` (DRY, phase-03 Requirements). Rows
# with no `id` cell are dropped here, once, so both callers see the same
# (and therefore index-aligned) row sequence.
_CODE_COLUMNS = ("user stories", "requirements", "business rules")


def _cap_table_rows(twin_functional_text: str) -> tuple[dict[str, int], list[list[str]]]:
    _, h2 = split_sections(twin_functional_text, 2)
    cap_body = h2.get("## 2. Functional Capabilities", "")
    _, header, rows, _ = split_around_first_table(cap_body)
    if not header:
        return {}, []
    header_cf = [h.casefold() for h in header]
    col = col_index(header_cf, "id", "capability", *_CODE_COLUMNS)
    filtered = [r for r in rows if cell(r, col, "id", "").strip()]
    return col, filtered


def cap_buckets(twin_functional_text: str, feature_name: str) -> list[tuple[str, str]]:
    col, rows = _cap_table_rows(twin_functional_text)
    buckets = [
        (cell(r, col, "id", "").strip(), cell(r, col, "capability", "").strip() or "{Capability name}")
        for r in rows
    ]
    return buckets or [("CAP-01", feature_name)]


def cap_code_map(twin_functional_text: str) -> dict[str, int]:
    """`{code: cap_row_index}` from the twin's § 2 `User Stories` / `Requirements`
    / `Business Rules` columns -- the declared code->capability mapping
    `assign_capability_and_detail` buckets actions on (phase-03 Requirements #1).
    Absent columns, an absent `## 2. Functional Capabilities` section, or a
    header-only table all degrade to `{}` (never raise -- `col_index`/`cell` are
    already absence-tolerant). First-writer-wins on a duplicated code
    (`setdefault`, row order = table order) so resolution is deterministic run
    after run (phase-03 Requirements, non-functional)."""
    col, rows = _cap_table_rows(twin_functional_text)
    out: dict[str, int] = {}
    for idx, r in enumerate(rows):
        for col_name in _CODE_COLUMNS:
            raw = cell(r, col, col_name, "")
            for token in re.split(r"[,/]", raw):
                token = token.strip().strip("`")
                if token and _CODE_RE.match(token):
                    out.setdefault(token, idx)
    return out


def _cap_number(cap_id: str, index: int) -> str:
    m = re.search(r"(\d+)", cap_id)
    return str(int(m.group(1))) if m else str(index + 1)


def _join_blocks(blocks: list[tuple[str, str]]) -> str:
    return "\n\n".join(f"{heading}\n{body}".rstrip() for heading, body in blocks)


def build_capability_body(
    ccl: CclPieces, us_blocks: list[UsBlock], edge_cases_body: str,
    twin_functional_text: str, feature_name: str,
) -> tuple[str, int]:
    """Returns `(section_body, removed_count)` -- `removed_count` is EXACTLY the
    number of per-US narratives the T-12 guard dropped this run (success criteria:
    "a stated, non-hand-waved removal count")."""
    buckets = cap_buckets(twin_functional_text, feature_name)
    twin_codes = twin_us_codes(twin_functional_text)

    removed = 0
    carried: list[str] = []
    for us in us_blocks:
        what_happens = us.fields.get("What happens", "").strip()
        if not what_happens:
            continue
        if us.code in twin_codes:
            removed += 1  # T-12 branch A: guard passes -- twin already states it in § 7
            continue
        carried.append(f"- **{us.code}:** {_CARRIED_PREFIX}{what_happens}")  # T-12 branch B

    br_text = _join_blocks(ccl.br_blocks) or _BR_NA
    dec_text = _join_blocks(ccl.dec_blocks) or _DEC_NA

    primary_parts = ["**Business Rules**", "", br_text, "", "**Decision Logic**", "", dec_text]
    if carried:
        primary_parts += ["", "**Carried User Story Narratives**", "", "\n".join(carried)]
    primary_parts += ["", "#### Edge Cases", "", edge_cases_body.strip() or _EDGE_NA]  # T-18

    out: list[str] = []
    for i, (cap_id, cap_name) in enumerate(buckets):
        n = _cap_number(cap_id, i)
        out.append(f"### 4.{n} {cap_name}")
        out.append("")
        if i == 0:
            out.append("\n".join(primary_parts))
        else:
            out.append(_REGROUP_NA)
        out.append("")
    return "\n".join(out).rstrip("\n") + "\n", removed
