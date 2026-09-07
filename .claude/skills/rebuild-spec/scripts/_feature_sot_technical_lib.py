"""`compose_technical_sot` -- the SOLE source of the SOT target section order for
technical-spec.md (phase-10, plans/260818-1332-rebuild-spec-human-readable-sot).
Sibling of `_feature_sot_functional_lib.compose_functional_sot` and of
`_screen_sot_compose_lib.compose_screen_sot`. content-preservation-map.md § C
(T-01..T-28), target-shape-spec.md § 3 (normative).

Reshapes the old (v27.0) 9-section technical-spec.md into the 5-bucket retaxonomy.
Reads the (already-composed) TWIN functional-spec.md text -- never the raw old
functional text -- for the `## 2. Functional Capabilities` bucket list and the T-12
removal guard's `## 7. User Stories` code set (target-shape-spec.md § 3's own
dependency). Parsing lives in `_feature_sot_extract_lib.py`; § 2/§ 3.4 row-building
lives in `_feature_sot_mapping_lib.py`; § 3/§ 5 structure lives in
`_feature_sot_structure_lib.py`; § 4 (incl. the T-12 guard) lives in
`_feature_sot_capability_lib.py`. This module only orchestrates and assembles.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _audience_split_md_sections_lib import split_sections  # noqa: E402
from _feature_sot_capability_lib import build_capability_body  # noqa: E402
from _feature_sot_extract_lib import extract_v27_tech_pieces, extract_v27_thread_pieces  # noqa: E402
from _feature_sot_mapping_lib import (  # noqa: E402
    add_source_refs_action_column, assign_codes,
    build_a0_writeup, build_action_index_table, build_action_records, build_api_endpoints,
    build_be_fe_notes, build_bin2_writeup, build_mapping_rows, build_mapping_table,
    build_title_index,
)
from _feature_sot_structure_lib import (  # noqa: E402
    assign_capability_and_detail, build_actions_section, build_shared_foundation,
    build_system_design, build_verification_notes,
)
from _spec_constants import (  # noqa: E402
    A3_HEADING, B4_HEADING, _LEGACY_TECH_H2_5BUCKET, REQUIRED_H2_TECH_THREAD, REQUIRED_VERIF_H3,
)

# Sentinel unique to SOT output -- absent from every old (v27.0) technical-spec.md,
# since "## 2." there does not exist at all (the old shape's 2nd H2 is
# "## Polymorphic Behavior", unnumbered).
_SOT_SENTINEL = "## 2. Functional → Technical Mapping"

# Literal placeholders this module itself writes when a source has nothing to
# route -- their presence on the idempotent re-entry path means a researcher pass
# is still owed (mirrors `_screen_sot_compose_lib._SCAFFOLD_MARKERS`'s convention).
_SCAFFOLD_MARKERS = (
    "{UNFILLED SCAFFOLD",
    "N/A — no FR/BR/US/AC codes found to map.",
    "N/A — pending manual regrouping once capability boundaries are confirmed.",
)


@dataclass(frozen=True)
class ComposeResult:
    text: str
    needs_llm_fill: bool
    moved: int
    scaffolded: int
    removed: int = 0


def _has_scaffold(text: str) -> bool:
    return any(marker in text for marker in _SCAFFOLD_MARKERS)


def _feature_name(old_text: str) -> str:
    for line in old_text.splitlines()[:10]:
        s = line.strip()
        if s.startswith("# "):
            title = s[2:].strip()
            return title.split(" — ")[0].strip() or title
    return "{Feature name}"


def compose_technical_sot(old_text: str, twin_functional_text: str) -> ComposeResult:
    """Reshape a v27.0-shaped technical-spec.md into the 5-bucket SOT shape, reading
    *twin_functional_text* (the twin functional-spec.md, already composed to its own
    SOT shape by `compose_functional_sot`) for the capability list and the T-12
    guard.

    Idempotent: text already carrying `## 2. Functional → Technical Mapping` is
    returned unchanged."""
    if _SOT_SENTINEL in old_text:
        return ComposeResult(old_text, _has_scaffold(old_text), 0, 0, 0)

    pieces = extract_v27_tech_pieces(old_text)
    title_index = build_title_index(twin_functional_text)
    mapping_rows = build_mapping_rows(
        pieces.ccl.requirements_body, pieces.ccl.dec_blocks, pieces.ccl.br_blocks,
        pieces.ccl.sm_blocks, pieces.us_blocks, title_index, twin_functional_text,
    )
    api_endpoints = build_api_endpoints(pieces.ccl.requirements_body, pieces.us_blocks)
    feature_name = _feature_name(old_text)
    behavior_text, removed = build_capability_body(
        pieces.ccl, pieces.us_blocks, pieces.edge_cases_body, twin_functional_text, feature_name,
    )

    sections = {
        "## 1. Technical Overview": pieces.overview.strip() or "N/A",
        "## 2. Functional → Technical Mapping": build_mapping_table(mapping_rows),
        "## 3. System Design": build_system_design(pieces, api_endpoints),
        "## 4. Technical Behavior by Capability": behavior_text,
        "## 5. Verification & Technical Notes": build_verification_notes(pieces),
    }

    moved = int(bool(pieces.overview.strip()))  # T-01
    moved += int(bool(mapping_rows))  # T-02/T-03/T-11 seed
    moved += int(bool(pieces.source_walkthrough.strip()))  # T-23
    moved += int(bool(pieces.db_impact.strip()))  # T-24
    moved += len(pieces.unknown_h2) + len(pieces.ccl.unrouted)  # T-28

    parts = [pieces.preamble.rstrip("\n")]
    for name in _LEGACY_TECH_H2_5BUCKET:
        parts.append(name + "\n\n" + sections[name].strip("\n"))
    for uname, ubody in [*pieces.unknown_h2, *pieces.ccl.unrouted]:
        parts.append(uname + "\n\n" + ubody.strip("\n"))
    parts.append(A3_HEADING + "\n\n" + (pieces.source_walkthrough.strip() or "N/A"))
    parts.append(B4_HEADING + "\n\n" + (pieces.db_impact.strip() or "N/A"))

    text = "\n\n".join(parts).rstrip("\n") + "\n"
    return ComposeResult(text, True, moved, 1, removed)


# ---------------------------------------------------------------------------
# rebuild-spec 27.7.0 (action-thread reshape, phase 05) -- `compose_action_thread`
# is NET-NEW, never a rename of `compose_technical_sot` above (preflight C4):
# that function is the sole v26->v27 authority the still-live `feature-sot` migrate
# step depends on; this one is v27 (the 5-bucket shape) -> v27.7 (action-thread),
# a different input shape and a different `STEP_ORDER` entry
# (`_doc_migration_action_thread_step_lib.py`, phase 06). Both stay green.
# ---------------------------------------------------------------------------

_THREAD_SENTINEL = REQUIRED_H2_TECH_THREAD[1]  # "## 2. Action Index"


@dataclass(frozen=True)
class ThreadComposeResult:
    text: str
    needs_llm_fill: bool
    action_count: int
    unresolved_rule_count: int
    # Phase 03 (defect 1): actions `assign_capability_and_detail` could not trace
    # to any capability the twin's § 2 table declares -- they still land in the
    # LAST bucket (contract § 3), but this count makes that degradation VISIBLE
    # to an operator instead of silently indistinguishable from a bucketing
    # failure. Defaulted so the early (already-thread-shaped) return path below
    # need not compute it.
    unbound_action_count: int = 0


def _strip_retired_sections(text: str) -> str:
    """Phase 08 (self-sufficiency v27.8) -- one-shot strip of the retired A3
    (`## Source Walkthrough`) and B4 (`## DB Impact per Event`) trailing sections
    from an ALREADY action-thread-shaped `technical-spec.md`. Exercised by the C1
    reopen path (`_doc_migration_action_thread_step_lib.run()`) once
    `FeatureSpec.retired_section_present` fires on a file this function's own
    idempotent early-return used to hand back byte-unchanged.

    True no-op (returns *text* verbatim, same object) when NEITHER heading is
    present -- this is what makes a second run, after the strip already applied
    once, byte-identical: `retired_section_present` no longer fires, so this
    function is never even asked to do anything on that second pass, but even if
    it were, the fast path guarantees identity."""
    if A3_HEADING not in text and B4_HEADING not in text:
        return text
    preamble, sections = split_sections(text, 2)
    parts = [preamble.rstrip("\n")]
    for heading, body in sections.items():
        if heading in (A3_HEADING, B4_HEADING):
            continue
        parts.append(heading + "\n\n" + body.strip("\n"))
    return "\n\n".join(parts).rstrip("\n") + "\n"


def compose_action_thread(old_text: str, twin_functional_text: str) -> ThreadComposeResult:
    """Reshape a v27 (5-bucket) technical-spec.md -- `compose_technical_sot`'s own
    output shape -- into the v27.7 action-thread shape. Idempotent: text already
    carrying `## 2. Action Index` is returned unchanged, MINUS a one-shot A3/B4
    strip (phase 08) applied on the way out -- see `_strip_retired_sections`.

    Deterministic/mechanical only: an `**Applies to:**` rule that cannot be bound to
    exactly one or more actions by handler- or path-match is marked `[UNVERIFIED]`
    and left in § 4.4 bin 3 -- never guessed (merge blocker #2)."""
    if _THREAD_SENTINEL in old_text:
        stripped = _strip_retired_sections(old_text)
        has_unverified = "[UNVERIFIED] carried from **Applies to:**" in stripped or \
            "[UNVERIFIED] no resolvable owner" in stripped
        return ThreadComposeResult(stripped, has_unverified, 0, 0)

    pieces = extract_v27_thread_pieces(old_text)
    actions = build_action_records(pieces)
    owner, rule_owners = assign_codes(pieces, actions)
    feature_name = _feature_name(old_text)
    buckets, unbound_action_count = assign_capability_and_detail(
        pieces, actions, owner, twin_functional_text, feature_name,
    )

    fe_notes, be_notes = build_be_fe_notes(pieces, owner)
    a0_codes = [c for c, o in owner.items() if o == "A0"]
    action_index = build_action_index_table(actions, a0_codes, pieces.endpoints_note)
    actions_body = build_actions_section(buckets, pieces, rule_owners, fe_notes, be_notes)
    shared_foundation = build_shared_foundation(
        pieces, build_bin2_writeup(pieces, rule_owners), build_a0_writeup(pieces, owner),
    )

    verif_body = pieces.verif_body
    verif_preamble, verif_h3 = _split_h3(verif_body)
    if REQUIRED_VERIF_H3[3] in verif_h3:
        verif_h3[REQUIRED_VERIF_H3[3]] = add_source_refs_action_column(
            verif_h3[REQUIRED_VERIF_H3[3]], actions,
        )
        verif_body = "\n\n".join(
            p for p in (verif_preamble, *(f"{h}\n\n{b}" for h, b in verif_h3.items())) if p
        )

    rule_codes = {rule.code for bucket in pieces.capability_buckets
                  for rule in (*bucket.br_blocks, *bucket.dec_blocks)}
    unresolved = sum(1 for code, o in owner.items() if o == "A0" and code in rule_codes)

    sections = {
        REQUIRED_H2_TECH_THREAD[0]: pieces.overview_body.strip() or "N/A",
        REQUIRED_H2_TECH_THREAD[1]: action_index,
        REQUIRED_H2_TECH_THREAD[2]: actions_body,
        REQUIRED_H2_TECH_THREAD[3]: shared_foundation,
        REQUIRED_H2_TECH_THREAD[4]: verif_body.strip() or "N/A",
    }
    parts = [pieces.preamble.rstrip("\n")]
    for name in REQUIRED_H2_TECH_THREAD:
        parts.append(name + "\n\n" + sections[name].strip("\n"))
    for uname, ubody in pieces.unknown_h2:
        parts.append(uname + "\n\n" + ubody.strip("\n"))
    # A3/B4 retired from technical-spec.md (phase 08, self-sufficiency v27.8) --
    # `pieces.source_walkthrough`/`pieces.db_impact_body` are read as INPUT signal
    # elsewhere (`build_action_records` synthesizes background actions from the
    # OLD file's B4 rows), but neither is re-emitted as an OUTPUT section here any
    # more. See `_strip_retired_sections` for the already-composed-file half of
    # this retirement.

    text = "\n\n".join(parts).rstrip("\n") + "\n"
    return ThreadComposeResult(text, unresolved > 0, len(actions), unresolved, unbound_action_count)


def _split_h3(text: str) -> tuple[str, dict[str, str]]:
    return split_sections(text, 3)
