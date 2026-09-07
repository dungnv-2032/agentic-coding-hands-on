"""Unpack a v27.0-shaped (old 9-section) technical-spec.md into raw named pieces,
ready for `_feature_sot_technical_lib.compose_technical_sot` and its sibling
builders. Split out to hold the repo's 200-line guidance -- this module is purely
the H2/H3/H4 unpacking; no target-shape knowledge lives here.

`## Cross-Cutting Logic`'s own internal shape mirrors
`_audience_split_ccl_normalize_lib.LEGACY_CCL_H3` exactly (that module IS the G1->G2
producer of this shape) -- a container heading (e.g. `### Business Rules`) followed
by zero or more PROMOTED SIBLING H3 blocks (`### {sentence} (BR-001)`), never nested
children. Verified against the real corpus
(st-post/docs/features/F001_Auth/technical-spec.md).

`## User Stories` carries the SAME code-tagged blocks, but per-US -- a BR/SM/ALG/INT
block can appear NESTED (positionally, between two `### US### -- ...` H3s) rather
than under Cross-Cutting Logic (content-preservation-map T-17; confirmed for real by
BR-006 sitting between US020 and US021 in the F001_Auth fixture above). Both
placements route through the exact same classifier so nothing depends on which one a
given corpus used.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _audience_split_md_sections_lib import split_sections  # noqa: E402
from _md_scan_lib import iter_lines_with_fence  # noqa: E402
from _spec_constants import (  # noqa: E402
    A3_HEADING, B4_HEADING, _LEGACY_SYSDESIGN_H3, _LEGACY_TECH_H2_5BUCKET,
)

LEGACY_CCL_H3 = [
    "### Requirements", "### Business Rules", "### Decision Logic",
    "### State Machines", "### Algorithms", "### External Integrations", "### Verification",
]
_CODE_TAG_RE = re.compile(r"\((BR|SM|ALG|INT|DEC)-\d+\)\s*$")
_US_HEADING_RE = re.compile(r"^###\s+(US\S+)\s+—\s+(.*?)\s+\(Priority:\s*(P\d)\)\s*$")
_FIELD_LINE_RE = re.compile(r"^\*\*([A-Za-z][A-Za-z /]*):\*\*\s*(.*)$")

KNOWN_TECH_H2 = {
    "## Overview", "## Polymorphic Behavior", "## Cross-Cutting Logic", "## User Stories",
    "## Key Entities", "## Artifact References", "## Assumptions",
    "## Source Code References", "## Unresolved Questions", A3_HEADING, B4_HEADING,
}

Block = tuple[str, str]


@dataclass
class CclPieces:
    requirements_body: str = ""
    verification_body: str = ""
    br_blocks: list[Block] = field(default_factory=list)
    dec_blocks: list[Block] = field(default_factory=list)
    sm_blocks: list[Block] = field(default_factory=list)
    alg_blocks: list[Block] = field(default_factory=list)
    int_blocks: list[Block] = field(default_factory=list)
    unrouted: list[Block] = field(default_factory=list)


@dataclass
class UsBlock:
    code: str
    title: str
    priority: str
    fields: dict[str, str]


@dataclass
class ExtractedTechPieces:
    preamble: str
    overview: str
    polymorphic: str
    ccl: CclPieces
    us_blocks: list[UsBlock]
    edge_cases_body: str
    key_entities: str
    artifact_refs: str
    assumptions: str
    source_refs: str
    unresolved_questions: str
    source_walkthrough: str
    db_impact: str
    unknown_h2: list[Block]


def _annotate_linked_us(body: str, us_code: str | None) -> str:
    if not us_code or "**Linked US:**" in body:
        return body
    suffix = f"**Linked US:** {us_code}"
    return f"{body}\n{suffix}" if body.strip() else suffix


def _route_tagged(pieces: CclPieces, heading: str, body: str, us_code: str | None = None) -> None:
    m = _CODE_TAG_RE.search(heading)
    if not m:
        if heading.strip() or body.strip():
            pieces.unrouted.append((heading, body))
        return
    body = _annotate_linked_us(body, us_code)
    kind = m.group(1)
    target = {
        "BR": pieces.br_blocks, "SM": pieces.sm_blocks,
        "ALG": pieces.alg_blocks, "INT": pieces.int_blocks, "DEC": pieces.dec_blocks,
    }[kind]
    target.append((heading, body))


def _extract_ccl(ccl_body: str) -> CclPieces:
    _, h3 = split_sections(ccl_body, 3)
    pieces = CclPieces()
    pieces.requirements_body = h3.get("### Requirements", "")
    pieces.verification_body = h3.get("### Verification", "")
    decision_logic_body = h3.get("### Decision Logic", "")
    for heading, body in h3.items():
        if heading in LEGACY_CCL_H3:
            continue
        _route_tagged(pieces, heading, body)
    _, h4 = split_sections(decision_logic_body, 4)
    for heading, body in h4.items():
        _route_tagged(pieces, heading, body)
    return pieces


def _parse_us_fields(body: str) -> dict[str, str]:
    fields: dict[str, list[str]] = {}
    current: str | None = None
    for line in body.splitlines():
        m = _FIELD_LINE_RE.match(line.strip())
        if m:
            current = m.group(1).strip()
            fields[current] = [m.group(2)] if m.group(2) else []
            continue
        if current is not None:
            fields[current].append(line)
    return {k: "\n".join(v).strip("\n") for k, v in fields.items()}


def _extract_user_stories(us_body: str, ccl: CclPieces) -> tuple[list[UsBlock], str]:
    """Populates *ccl*'s BR/SM/ALG/INT/DEC lists in place with any per-US-nested
    block found here (T-17) -- so the caller has ONE combined list per kind
    regardless of which of the two legal placements a given corpus used."""
    _, h3 = split_sections(us_body, 3)
    blocks: list[UsBlock] = []
    edge_cases_body = ""
    current_us: str | None = None
    for heading, body in h3.items():
        m = _US_HEADING_RE.match(heading)
        if m:
            current_us = m.group(1)
            blocks.append(UsBlock(code=current_us, title=m.group(2), priority=m.group(3),
                                   fields=_parse_us_fields(body)))
            continue
        if heading == "### Edge Cases":
            edge_cases_body = body
            continue
        _route_tagged(ccl, heading, body, us_code=current_us)
    return blocks, edge_cases_body


def extract_v27_tech_pieces(old_text: str) -> ExtractedTechPieces:
    preamble, h2 = split_sections(old_text, 2)
    ccl = _extract_ccl(h2.get("## Cross-Cutting Logic", ""))
    us_blocks, edge_cases_body = _extract_user_stories(h2.get("## User Stories", ""), ccl)
    unknown_h2 = [(name, body) for name, body in h2.items() if name not in KNOWN_TECH_H2]
    return ExtractedTechPieces(
        preamble=preamble,
        overview=h2.get("## Overview", ""),
        polymorphic=h2.get("## Polymorphic Behavior", ""),
        ccl=ccl,
        us_blocks=us_blocks,
        edge_cases_body=edge_cases_body,
        key_entities=h2.get("## Key Entities", ""),
        artifact_refs=h2.get("## Artifact References", ""),
        assumptions=h2.get("## Assumptions", ""),
        source_refs=h2.get("## Source Code References", ""),
        unresolved_questions=h2.get("## Unresolved Questions", ""),
        source_walkthrough=h2.get(A3_HEADING, ""),
        db_impact=h2.get(B4_HEADING, ""),
        unknown_h2=unknown_h2,
    )


# ---------------------------------------------------------------------------
# rebuild-spec 27.7.0 (action-thread reshape, phase 05) -- `extract_v27_thread_pieces`
# unpacks a v27-shaped (5-bucket) technical-spec.md: the OUTPUT of
# `compose_technical_sot` above, NOT the old 9-section input that function unpacks.
# Deliberately a SIBLING of `extract_v27_tech_pieces`, never the same function --
# the input shapes differ (`_LEGACY_TECH_H2_5BUCKET` vs the pre-v27 9 H2s), so a shared
# parser would silently accept the wrong shape. Feeds
# `_feature_sot_technical_lib.compose_action_thread`.
#
# `KNOWN_THREAD_H2` is this shape's OWN "known H2" set (C3, preflight report) --
# NOT `KNOWN_TECH_H2` above, which holds the PRE-v27 vocabulary and stays
# untouched for `extract_v27_tech_pieces`'s own unknown-H2 fallback.
# ---------------------------------------------------------------------------

KNOWN_THREAD_H2 = set(_LEGACY_TECH_H2_5BUCKET) | {A3_HEADING, B4_HEADING}

_BR_TAG_RE = re.compile(r"\((BR-\d+)\)\s*$")
_DEC_TAG_RE = re.compile(r"\((DEC-\d+)\)\s*$")
_INT_TAG_RE = re.compile(r"\((INT-\d+)\)\s*$")
_SM_TAG_RE = re.compile(r"\((SM-\d+)\)\s*$")
_ALG_TAG_RE = re.compile(r"\((ALG-\d+)\)\s*$")
_SYSDESIGN_NUMBERED_RE = re.compile(r"^### 3\.\d+ ")
_CAP_NUMBERED_RE = re.compile(r"^### 4\.\d+ ")
_H4_BOUNDARY_RE = re.compile(r"^#### ")
_DECISION_LOGIC_MARK_RE = re.compile(r"^\*\*Decision Logic\*\*\s*$")
_FIELD_VALUE_RE = re.compile(r"^\*\*([A-Za-z][A-Za-z ]*):\*\*\s*(.*)$")


@dataclass
class ThreadEndpointRow:
    method: str
    path: str
    handler: str
    linked_codes: str
    source: str


@dataclass
class ThreadRuleBlock:
    code: str
    heading: str
    body: str  # own content only -- any Decision-Logic/DEC/Edge-Cases tail already split off


@dataclass
class ThreadIntBlock:
    code: str
    heading: str
    body: str
    kind: str
    target: str


@dataclass
class ThreadCapabilityBucket:
    heading: str
    br_blocks: list[ThreadRuleBlock] = field(default_factory=list)
    dec_blocks: list[ThreadRuleBlock] = field(default_factory=list)
    edge_cases_body: str = ""
    extra_prose: list[str] = field(default_factory=list)  # non-boilerplate carried text (no home yet)


@dataclass
class ExtractedThreadPieces:
    preamble: str
    overview_body: str
    sysdesign_verbatim: dict[str, str]  # _LEGACY_SYSDESIGN_H3 entries except "### 3.4 ...", verbatim
    endpoints: list[ThreadEndpointRow]
    endpoints_note: str  # old "### 3.4" prose (e.g. "N/A -- background feature only") when there's no table
    int_blocks: list[ThreadIntBlock]
    mapping_rows: list[list[str]]  # old "## 2." table rows: [code, name, where, notes, source]
    capability_buckets: list[ThreadCapabilityBucket]
    verif_body: str  # entire "## 5. Verification & Technical Notes" body, verbatim
    source_walkthrough: str
    db_impact_body: str
    unknown_h2: list[tuple[str, str]]
    # rebuild-spec 27.7.1 -- SM-###/ALG-### code-tagged blocks living directly under
    # § 3.3 State Management / § 3.5 Algorithms & Processing Logic, i.e. OUTSIDE any
    # "### 4.N" capability bucket (unlike BR/DEC, which always sit inside one). These
    # never had a structured home before: `sysdesign_verbatim` only carries them as
    # opaque rendered strings, so `_feature_sot_mapping_lib.assign_codes` had no way
    # to see their codes at all -- a declared SM-###/ALG-### could vanish from every
    # ownership check (measured: F026_TransactionalEmailSettings's SM-001, corpus
    # real-run defect, `FeatureSpec.action_unclaimed`). Flat lists, not nested in a
    # bucket, because these subsections are NOT capability-scoped -- there is no
    # "### 4.N" parent to attach them to. Default-factory'd (appended at the END of
    # the dataclass, after every field lacking a default) so existing keyword-based
    # construction (this module's own return statement, and
    # test_feature_sot_structure.py's `_thread_pieces` helper) keeps working
    # unmodified.
    sm_blocks: list[ThreadRuleBlock] = field(default_factory=list)
    alg_blocks: list[ThreadRuleBlock] = field(default_factory=list)


def _group_numbered_h3(
    h3_items: list[tuple[str, str]], numbered_re: re.Pattern[str],
) -> list[tuple[str, list[tuple[str, str]]]]:
    """Group a flat, document-ordered H3 dict's items under the nearest PRECEDING
    heading matching *numbered_re* -- the fix for the "typographic, not structural"
    grouping this whole plan exists to fix (plan.md's own problem statement):
    `### {sentence} (BR-001)` is a markdown SIBLING of `### 4.1 {capability}`, not a
    child, so a real nesting-based split can never bound it. Any item before the
    first numbered heading is dropped (should not occur in a well-formed input)."""
    groups: list[tuple[str, list[tuple[str, str]]]] = []
    for heading, body in h3_items:
        if numbered_re.match(heading):
            groups.append((heading, [(heading, body)]))
        elif groups:
            groups[-1][1].append((heading, body))
    return groups


def _split_at_h4_or_marker(body: str) -> tuple[str, str]:
    """Fence-aware split of *body* at the first H4 heading or a literal
    `**Decision Logic**` marker line -- whichever comes first. Returns
    `(head, tail)`; `tail` is `""` when neither is present. A pseudocode fence
    routinely follows a BR block's own fields, so this must never cut inside one."""
    lines = body.splitlines()
    for lineno, line, in_fence in iter_lines_with_fence(body):
        if in_fence:
            continue
        if _H4_BOUNDARY_RE.match(line) or _DECISION_LOGIC_MARK_RE.match(line.strip()):
            return "\n".join(lines[:lineno - 1]).rstrip("\n"), "\n".join(lines[lineno - 1:])
    return body, ""


def _extract_dec_and_edge(body: str) -> tuple[str, list[ThreadRuleBlock], str, str]:
    """Returns `(remaining_head, dec_blocks, edge_cases_body, decision_logic_intro)`
    for any capability-bucket body text -- the group's own body (no BR children) or
    a single BR block's body (its usual home, per the real corpus's own shape)."""
    head, tail = _split_at_h4_or_marker(body)
    if not tail:
        return head, [], "", ""
    intro, h4 = split_sections(tail, 4)
    dec_blocks: list[ThreadRuleBlock] = []
    edge_cases = ""
    for heading, h4body in h4.items():
        m = _DEC_TAG_RE.search(heading)
        if m:
            dec_blocks.append(ThreadRuleBlock(code=m.group(1), heading=heading, body=h4body))
        elif heading.strip() == "#### Edge Cases":
            edge_cases = h4body
    return head, dec_blocks, edge_cases, intro.strip()


def _parse_capability_bucket(heading: str, entries: list[tuple[str, str]]) -> ThreadCapabilityBucket:
    bucket = ThreadCapabilityBucket(heading=heading)
    for i, (h, b) in enumerate(entries):
        head, dec_blocks, edge_cases, intro = _extract_dec_and_edge(b)
        bucket.dec_blocks.extend(dec_blocks)
        if edge_cases:
            bucket.edge_cases_body = edge_cases
        if intro and intro != "**Decision Logic**":
            bucket.extra_prose.append(intro)
        if i == 0:
            # the numbered "### 4.N {cap}" heading's own body -- pure boilerplate
            # (`**Business Rules**`) is dropped; anything else is preserved.
            if head.strip() not in ("", "**Business Rules**"):
                bucket.extra_prose.append(head.strip())
            continue
        m = _BR_TAG_RE.search(h)
        if m:
            bucket.br_blocks.append(ThreadRuleBlock(code=m.group(1), heading=h, body=head))
        elif head.strip():
            bucket.extra_prose.append(head.strip())
    return bucket


def _parse_endpoints(body: str) -> list[ThreadEndpointRow]:
    from _screen_sot_table_lib import cell, col_index, split_around_first_table
    _, header, rows, _ = split_around_first_table(body)
    if not header:
        return []
    col = col_index([h.casefold() for h in header], "method", "path", "handler", "linked code", "source")
    out = []
    for r in rows:
        out.append(ThreadEndpointRow(
            method=cell(r, col, "method", ""), path=cell(r, col, "path", ""),
            handler=cell(r, col, "handler", ""), linked_codes=cell(r, col, "linked code", ""),
            source=cell(r, col, "source", ""),
        ))
    return out


def _parse_int_blocks(int_group: list[tuple[str, str]]) -> list[ThreadIntBlock]:
    blocks = []
    for heading, body in int_group[1:]:  # [0] is the "### 3.6 Integrations" heading itself
        m = _INT_TAG_RE.search(heading)
        if not m:
            continue
        fields: dict[str, str] = {}
        for line in body.splitlines():
            fm = _FIELD_VALUE_RE.match(line.strip())
            if fm:
                fields[fm.group(1).strip().lower()] = fm.group(2).strip()
        blocks.append(ThreadIntBlock(
            code=m.group(1), heading=heading, body=body,
            kind=fields.get("type", ""), target=fields.get("target", ""),
        ))
    return blocks


def _parse_coded_blocks(group: list[tuple[str, str]], tag_re: re.Pattern[str]) -> list[ThreadRuleBlock]:
    """SM-###/ALG-### blocks living directly under one non-capability § 3 System
    Design subsection (3.3 State Management, 3.5 Algorithms & Processing Logic) --
    same shape and same `[0] is the subsection's own heading` convention as
    `_parse_int_blocks`, minus the extra `kind`/`target` fields INT alone needs for
    background-job synthesis. These blocks have no `### 4.N` capability parent (BR/
    DEC always do), so they come back as a flat list, not a bucket."""
    blocks: list[ThreadRuleBlock] = []
    for heading, body in group[1:]:
        m = tag_re.search(heading)
        if m:
            blocks.append(ThreadRuleBlock(code=m.group(1), heading=heading, body=body))
    return blocks


def extract_v27_thread_pieces(old_text: str) -> ExtractedThreadPieces:
    from _screen_sot_table_lib import split_around_first_table
    preamble, h2 = split_sections(old_text, 2)
    _, h3sys = split_sections(h2.get(_LEGACY_TECH_H2_5BUCKET[2], ""), 3)
    sys_groups = dict(_group_numbered_h3(list(h3sys.items()), _SYSDESIGN_NUMBERED_RE))

    def _render_group(name: str) -> str:
        group = sys_groups.get(name, [(name, "")])
        return "\n\n".join(
            (b if i == 0 else f"{h}\n{b}").rstrip() for i, (h, b) in enumerate(group)
        ).strip("\n")

    verbatim = {name: _render_group(name) for name in _LEGACY_SYSDESIGN_H3
                if name != _LEGACY_SYSDESIGN_H3[3]}
    sysdesign_34_text = _render_group(_LEGACY_SYSDESIGN_H3[3])
    endpoints = _parse_endpoints(sysdesign_34_text)
    endpoints_note = "" if endpoints else sysdesign_34_text.strip()
    int_blocks = _parse_int_blocks(sys_groups.get(_LEGACY_SYSDESIGN_H3[5], []))
    sm_blocks = _parse_coded_blocks(sys_groups.get(_LEGACY_SYSDESIGN_H3[2], []), _SM_TAG_RE)
    alg_blocks = _parse_coded_blocks(sys_groups.get(_LEGACY_SYSDESIGN_H3[4], []), _ALG_TAG_RE)

    _, mheader, mrows, _ = split_around_first_table(h2.get(_LEGACY_TECH_H2_5BUCKET[1], ""))
    mapping_rows = mrows if mheader else []

    _, h3cap = split_sections(h2.get(_LEGACY_TECH_H2_5BUCKET[3], ""), 3)
    cap_groups = _group_numbered_h3(list(h3cap.items()), _CAP_NUMBERED_RE)
    capability_buckets = [_parse_capability_bucket(h, entries) for h, entries in cap_groups]

    unknown_h2 = [(name, body) for name, body in h2.items() if name not in KNOWN_THREAD_H2]
    return ExtractedThreadPieces(
        preamble=preamble,
        overview_body=h2.get(_LEGACY_TECH_H2_5BUCKET[0], ""),
        sysdesign_verbatim=verbatim,
        endpoints=endpoints,
        endpoints_note=endpoints_note,
        int_blocks=int_blocks,
        mapping_rows=[list(r) for r in mapping_rows],
        capability_buckets=capability_buckets,
        verif_body=h2.get(_LEGACY_TECH_H2_5BUCKET[4], ""),
        source_walkthrough=h2.get(A3_HEADING, ""),
        db_impact_body=h2.get(B4_HEADING, ""),
        unknown_h2=unknown_h2,
        sm_blocks=sm_blocks,
        alg_blocks=alg_blocks,
    )
