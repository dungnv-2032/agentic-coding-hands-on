"""content-preservation-map.md § C: `## 3. System Design` (T-04/T-05/T-06/T-07/T-08/
T-25/T-26/T-27) + `## 5. Verification & Technical Notes` (T-09/T-14/T-15/T-19/T-20/
T-21/T-22). Split out of `_feature_sot_technical_lib.py` to hold the repo's 200-line
guidance -- capability-scoped behavior (T-10/T-11/T-12/T-17/T-18) lives in the
sibling `_feature_sot_capability_lib.py` instead; this module is capability-agnostic
STRUCTURE and cross-cutting verification only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _action_thread_handler_lib import (  # noqa: E402
    humanize_class, humanize_method, render_handler, sanitize_title,
)
from _feature_sot_capability_lib import cap_buckets, cap_code_map  # noqa: E402
from _feature_sot_extract_lib import (  # noqa: E402
    CclPieces, ExtractedTechPieces, ExtractedThreadPieces,
)
from _feature_sot_mapping_lib import ActionRecord  # noqa: E402
from _md_scan_lib import iter_lines_with_fence  # noqa: E402
from _spec_constants import (  # noqa: E402
    REQUIRED_APPENDIX_H3, _LEGACY_SYSDESIGN_H3, REQUIRED_VERIF_H3, RUNG_LABELS,
)

_HEADING_RE = re.compile(r"^(#{1,6})(\s.*)$")

_COMPONENTS_SCAFFOLD = (
    "{UNFILLED SCAFFOLD -- no v27.0 predecessor section; list this feature's "
    "primary components/services/classes here.}\n\n"
    "| Component | Responsibility | File |\n|-----------|------------------|------|\n"
)
_CONFIG_SCAFFOLD = (
    "{UNFILLED SCAFFOLD -- no v27.0 predecessor section; confirm technical "
    "configuration (env vars, feature-flag keys, timeouts) against source.}\n\n"
    "N/A — no technical configuration beyond framework defaults."
)

# D8 (plan.md "Orchestrator decisions"): the `**Client behavior:** see [...]`
# paragraph is RE-HOMED to the end of `## 3. System Design`, not retired --
# `FeatureSpec.missing_client_behavior_anchor` (validate_feature_spec.py) now scans
# THIS section's bounds for the literal anchor text. Mandatory even though every
# linked doc is generic/unscoped by this composer -- verbatim match of
# `technical-spec-template.md`'s own anchor block, never re-typed elsewhere.
_CLIENT_BEHAVIOR_ANCHOR = (
    "**Client behavior:** see\n"
    "[`behavior-logic.md`](../../docs/generated/behavior-logic.md) (client-side "
    "patterns — debounce, optimistic UI, polling, upload, realtime),\n"
    "[`permissions.md`](../../docs/system/permissions.md) (feature flags / "
    "experiments / env / locale gates),\n"
    "[`architecture.md`](../../docs/system/architecture.md) (guards / deep-link "
    "state restoration / unsaved-changes protection)."
)


def _join_blocks(blocks: list[tuple[str, str]]) -> str:
    return "\n\n".join(f"{heading}\n{body}".rstrip() for heading, body in blocks)


def _demote_headings(text: str, delta: int) -> str:
    """Add *delta* `#`s to every heading line in *text* -- fence-aware, so a fenced
    line shaped like a heading is never touched. The old `## Polymorphic Behavior`
    H2's own `### DISC-### ...` children (real corpus: st-post/docs/features/
    F001_Auth/technical-spec.md) are H3 -- embedding them verbatim under the new
    `#### Polymorphic Behavior` (H4) would make them read as SIBLINGS of
    `### 3.2 Data Model` once the whole document is heading-parsed, silently
    truncating that section. Demoting by 2 (H3 -> H5, matching
    technical-spec-template.md's own `##### DISC-### — ...` depth) fixes that."""
    if delta <= 0:
        return text
    extra = "#" * delta
    out = []
    for _, line, in_fence in iter_lines_with_fence(text):
        if not in_fence:
            m = _HEADING_RE.match(line)
            if m:
                out.append(extra + line)
                continue
        out.append(line)
    return "\n".join(out)


def build_system_design(pieces: ExtractedTechPieces, api_endpoints_text: str) -> str:
    key_entities = pieces.key_entities.strip() or (
        "| Entity | Table | Key Columns | Purpose |\n|--------|-------|-------------|---------|\n"
    )
    polymorphic = _demote_headings(pieces.polymorphic.strip(), 2) or (
        "N/A — no discriminator fields in Key Entities."
    )
    data_model = f"#### Key Entities\n\n{key_entities}\n\n#### Polymorphic Behavior\n\n{polymorphic}"

    ccl: CclPieces = pieces.ccl
    body_by_h3 = {
        _LEGACY_SYSDESIGN_H3[0]: _COMPONENTS_SCAFFOLD,
        _LEGACY_SYSDESIGN_H3[1]: data_model,
        _LEGACY_SYSDESIGN_H3[2]: _join_blocks(ccl.sm_blocks) or "None.",
        _LEGACY_SYSDESIGN_H3[3]: api_endpoints_text,
        _LEGACY_SYSDESIGN_H3[4]: _join_blocks(ccl.alg_blocks) or "None.",
        _LEGACY_SYSDESIGN_H3[5]: _join_blocks(ccl.int_blocks) or "None.",
        _LEGACY_SYSDESIGN_H3[6]: _CONFIG_SCAFFOLD,
    }
    body = "\n\n".join(f"{h3}\n\n{body_by_h3[h3]}" for h3 in _LEGACY_SYSDESIGN_H3)
    return f"{body}\n\n{_CLIENT_BEHAVIOR_ANCHOR}"


def _us_verification_subblock(us) -> str:
    lines = [f"#### {us.code}", ""]
    indep = us.fields.get("Independent Test", "").strip()
    if indep:
        lines += [f"**Independent Test:** {indep}", ""]
    accept = us.fields.get("Acceptance Scenarios", "").strip()
    if accept:
        lines += ["**Acceptance Scenarios:**", "", accept, ""]
    rules = us.fields.get("Rules enforced", "").strip()
    if rules:
        lines += [f"**Rules enforced:** {rules}", ""]
    transitions = us.fields.get("State transitions", "").strip()
    if transitions:
        lines += [f"**State transitions:** {transitions}", ""]
    verif = us.fields.get("Verification", "").strip()
    if verif:
        lines += ["**Verification:**", "", verif, ""]
    return "\n".join(lines).rstrip()


def build_verification_notes(pieces: ExtractedTechPieces) -> str:
    sc_body = pieces.ccl.verification_body.strip() or "None."
    us_sub_blocks = [_us_verification_subblock(us) for us in pieces.us_blocks]
    verif_5_1 = "\n\n".join([sc_body, *us_sub_blocks]) if us_sub_blocks else sc_body

    source_refs = pieces.source_refs.strip() or (
        "| Order | Symbol | Path | Purpose |\n|-------|--------|------|---------|\n"
    )
    artifact_refs = pieces.artifact_refs.strip() or (
        "| Artifact | File | Codes Used | Reviewed |\n|----------|------|------------|----------|\n"
    )
    body_by_h3 = {
        REQUIRED_VERIF_H3[0]: verif_5_1,
        REQUIRED_VERIF_H3[1]: pieces.assumptions.strip() or "None recorded.",
        REQUIRED_VERIF_H3[2]: pieces.unresolved_questions.strip() or "None recorded.",
        REQUIRED_VERIF_H3[3]: source_refs,
        REQUIRED_VERIF_H3[4]: artifact_refs,
    }
    return "\n\n".join(f"{h3}\n\n{body_by_h3[h3]}" for h3 in REQUIRED_VERIF_H3)


# ---------------------------------------------------------------------------
# rebuild-spec 27.7.0 (action-thread reshape, phase 05) -- `## 3. Actions` (the new
# spine) and `## 4. Shared Foundation` (the appendix the old `## 3. System Design`
# becomes). See wire-format-contract.md for the exact rung/heading shapes.
# ---------------------------------------------------------------------------

Bucket = tuple[str, str, list[ActionRecord]]  # (cap_id, cap_title, actions in this bucket)


def assign_capability_and_detail(
    pieces: ExtractedThreadPieces, actions: list[ActionRecord], owner: dict[str, str],
    twin_functional_text: str, feature_name: str,
) -> tuple[list[Bucket], int]:
    """Buckets *actions* by the twin functional-spec's own § 2 `Functional
    Capabilities` table (`cap_code_map`) and mutates each action's
    `detail_ref`/`cap_id` in place; a multi-capability action lands under the
    EARLIEST one declared (`min()`), an unresolved one lands LAST (never
    guessed toward the front) and is counted in `unbound_action_count`.

    Corpus evidence: `plans/260825-1010-rebuild-spec-action-thread-migration-defects/
    phase-03-defect-1-capability-bucketing.md`."""
    code_map = cap_code_map(twin_functional_text)
    twin_caps = cap_buckets(twin_functional_text, feature_name)
    n = max(len(twin_caps), 1)
    unbound_action_count = 0

    def _idx_for(action: ActionRecord) -> int:
        nonlocal unbound_action_count
        candidates = {code_map[c] for c in action.codes if c in code_map}
        if not candidates:
            unbound_action_count += 1
            return n - 1
        return min(candidates)

    grouped: list[list[ActionRecord]] = [[] for _ in range(n)]
    for a in actions:
        grouped[min(_idx_for(a), n - 1)].append(a)
    out: list[Bucket] = []
    for i, cap_actions in enumerate(grouped):
        cap_id, cap_title = twin_caps[i] if i < len(twin_caps) else (f"CAP-{i + 1:02d}", feature_name)
        for a in cap_actions:
            a.cap_id = cap_id
            a.detail_ref = f"§ 3.{i + 1}"
        out.append((cap_id, cap_title, cap_actions))
    return out, unbound_action_count


def _rung(label: str, content: str) -> str:
    return f"**{label}** · {content}" if label != "Source" else f"**Source:** {content}"


# A BR/DEC rule's OWN `**Source:**` field, carried verbatim from the v27 input
# (e.g. `**Source:** \`app/services/foo_service.rb:15-23\``). Rendering this line
# unchanged inside the `**Rule**` rung's body produces a SECOND line that
# `_action_thread_lib._RUNG_LINE_RE` reads as a rung marker regardless of where it
# sits in the block -- confirmed root cause of `rung_order` firing 70x across 43
# real corpus features (phase 11 triage, item 3). The citation is real content, not
# noise, so it is stripped here and folded into the action's single,
# contract-mandated final Source rung instead of being dropped (merge blocker #3).
_RULE_OWN_SOURCE_LINE_RE = re.compile(r"^\*\*Source:\*\*\s+(.*)$")


def _strip_rule_own_source(body: str) -> tuple[str, list[str]]:
    """Returns `(body_without_its_own_Source_line, [citation, ...])`. A rule body
    normally carries at most one such field, but this collects every match so
    nothing is silently dropped if a block ever carries more than one."""
    kept: list[str] = []
    citations: list[str] = []
    for line in body.splitlines():
        m = _RULE_OWN_SOURCE_LINE_RE.match(line)
        if m:
            citations.append(m.group(1).strip())
        else:
            kept.append(line)
    # collapse a now-consecutive blank-line pair left by the removed field line
    cleaned: list[str] = []
    for line in kept:
        if line == "" and cleaned and cleaned[-1] == "":
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip("\n"), citations


def _bin1_rule_body(
    pieces: ExtractedThreadPieces, action_id: str, rule_owners: dict[str, list[str]],
) -> tuple[str, list[str]]:
    parts = []
    citations: list[str] = []
    for bucket in pieces.capability_buckets:
        for rule in (*bucket.br_blocks, *bucket.dec_blocks):
            owners = rule_owners.get(rule.code, [])
            if owners == [action_id]:
                stripped_body, cites = _strip_rule_own_source(rule.body.strip())
                parts.append(f"**{rule.heading.lstrip('#').strip()}**\n\n{stripped_body}")
                citations.extend(cites)
    return "\n\n".join(parts), citations


def build_action_rungs(
    action: ActionRecord, pieces: ExtractedThreadPieces, rule_owners: dict[str, list[str]],
    fe_notes: dict[str, list[str]], be_notes: dict[str, list[str]],
) -> str:
    """Renders every rung `RUNG_LABELS` names, in order, OMITTING any rung with no
    mechanically-derived content (`rung_empty_rendered`) -- `Who` and `Request` are
    essentially never derivable from a v27 input and are expected to be absent on
    most actions; inventing either would violate merge blocker #5."""
    content: dict[str, str] = {}
    if fe_notes.get(action.id):
        content["FE"] = "; ".join(fe_notes[action.id])
    if be_notes.get(action.id):
        content["BE"] = "; ".join(be_notes[action.id])
    rule_body, rule_citations = _bin1_rule_body(pieces, action.id, rule_owners)
    if action.write_notes:
        content["Result"] = "; ".join(action.write_notes)
    elif action.write_reason:
        content["Result"] = f"— **{action.write_reason}**."
    # merge deduped, order-preserving: the action's own (endpoint/DB-impact)
    # citations first, then any bin-1 rule's own citation not already present --
    # ONE final Source rung carries every citation this action's block would
    # otherwise have scattered across multiple top-level lines.
    all_citations = list(action.source_citations)
    for c in rule_citations:
        if c not in all_citations:
            all_citations.append(c)
    if all_citations:
        content["Source"] = " → ".join(all_citations)
    lines = []
    for label in RUNG_LABELS:
        if label == "Rule" and rule_body:
            lines.append(f"**Rule** ·\n\n{rule_body}")
        elif label in content:
            lines.append(_rung(label, content[label]))
    return "\n".join(lines)


def _context_lines(action: ActionRecord) -> str:
    # Phase 05: `render_handler` -- shared with `build_action_index_table`'s § 2
    # cell -- so the handler+annotation pair is never rendered two different ways.
    rendered_handler = render_handler(action.handler, action.annotation)
    if action.path:
        first = f"`{action.http_method} {action.path}` → {rendered_handler}"
    elif action.is_background:
        first = f"queue · `Delayed::Job` → {rendered_handler}"
    else:
        first = rendered_handler
    codes = " ".join(f"`{c}`" for c in sorted(action.codes))
    return f"{first}\n{codes}" if codes else first


# Phase 02 (self-sufficiency v27.8) -- `_action_title` family priority. Never a
# name from one of these families: a BR/DEC/SM/ALG/INT code's `name_by_code` entry
# is a one-line RULE STATEMENT (`build_mapping_rows`'s naming convention for those
# families), not an action-shaped label. `sorted(action.codes)` used to decide the
# title by lexicographic accident (`ALG < BR < DEC < FR < INT < SM < US`), so any
# action carrying both a BR/DEC code and an FR/US code -- the common case --
# silently got the rule sentence as its H4 title (e.g. "Approve/reject only apply
# while pending") and never left a marker, so a fill pass had no signal a second
# look was owed (plan.md's `_action_title` finding).
_TITLE_NEVER_FAMILIES = ("BR", "DEC", "SM", "ALG", "INT")


def _code_family(code: str) -> str:
    return "US" if code.startswith("US") else code.split("-", 1)[0]


def _action_title(action: ActionRecord, name_by_code: dict[str, str]) -> str:
    """Prefers an FR/US code's own name; else a four-rung ladder over the
    case-preserving `handler` (never `method_norm`, lowercased at construction):
    (1) FR/US name; (2) no "#" in `handler` -> raw text verbatim; (3) background
    or method `perform` -> humanized CLASS basename; (4) else humanized METHOD.
    `sanitize_title` runs on every rung.

    Corpus evidence (the "Perform" collapse this ladder fixes):
    `plans/260825-1010-rebuild-spec-action-thread-migration-defects/
    phase-05-defect-3-malformed-headings.md`."""
    for code in sorted(action.codes):
        if _code_family(code) in _TITLE_NEVER_FAMILIES:
            continue
        if code in name_by_code:
            return sanitize_title(name_by_code[code])
    cls, sep, meth = action.handler.partition("#")
    if not sep:
        title = action.handler
    elif action.is_background or meth.lower() == "perform":
        title = humanize_class(cls)
    else:
        title = humanize_method(meth)
    return sanitize_title(title)


def build_actions_section(
    buckets: list[Bucket], pieces: ExtractedThreadPieces, rule_owners: dict[str, list[str]],
    fe_notes: dict[str, list[str]], be_notes: dict[str, list[str]],
) -> str:
    name_by_code = {(row[0] if row else ""): row[1] for row in pieces.mapping_rows if len(row) > 1}
    parts = []
    for i, (cap_id, cap_title, cap_actions) in enumerate(buckets):
        parts.append(f"### 3.{i + 1} {cap_id} — {cap_title}")
        for a in cap_actions:
            parts.append(f"#### {a.id} · {_action_title(a, name_by_code)}")
            parts.append(_context_lines(a))
            rungs = build_action_rungs(a, pieces, rule_owners, fe_notes, be_notes)
            if rungs:
                parts.append(rungs)
            parts.append("---")
        if parts and parts[-1] == "---":
            parts.pop()
    edge_cases = [b.edge_cases_body.strip() for b in pieces.capability_buckets if b.edge_cases_body.strip()]
    if edge_cases:
        # B-v sample's own placement (technical-spec-bv-sample/technical-spec.md
        # § 3.4): one trailing numbered section after every capability bucket,
        # not folded into any single action -- an edge case routinely spans
        # several actions (e.g. "A2·A3·A4: concurrent update").
        parts.append(f"### 3.{len(buckets) + 1} Edge Cases")
        parts.append("\n\n".join(edge_cases))
    return "\n\n".join(parts)


def build_shared_foundation(pieces: ExtractedThreadPieces, bin2_writeup: str, a0_writeup: str) -> str:
    """`## 4. Shared Foundation`: 4.1/4.2/4.3/4.5/4.6 are the old 3.1/3.2/3.3/3.5+3.6/
    3.7 bodies relocated VERBATIM (plan.md's own requirement); 4.4 is net-new (the
    three-bin rule catalogue)."""
    extra = "\n\n".join(p for bucket in pieces.capability_buckets for p in bucket.extra_prose)
    shared_rules = "\n\n".join(x for x in (bin2_writeup.strip(), a0_writeup.strip(), extra) if x)
    body_by_h3 = {
        REQUIRED_APPENDIX_H3[0]: pieces.sysdesign_verbatim.get(_LEGACY_SYSDESIGN_H3[0], "") or "None.",
        REQUIRED_APPENDIX_H3[1]: pieces.sysdesign_verbatim.get(_LEGACY_SYSDESIGN_H3[1], "") or "None.",
        REQUIRED_APPENDIX_H3[2]: pieces.sysdesign_verbatim.get(_LEGACY_SYSDESIGN_H3[2], "") or "None.",
        REQUIRED_APPENDIX_H3[3]: shared_rules or "None.",
        REQUIRED_APPENDIX_H3[4]: "\n\n".join(x for x in (
            pieces.sysdesign_verbatim.get(_LEGACY_SYSDESIGN_H3[4], ""),
            pieces.sysdesign_verbatim.get(_LEGACY_SYSDESIGN_H3[5], ""),
        ) if x) or "None.",
        REQUIRED_APPENDIX_H3[5]: pieces.sysdesign_verbatim.get(_LEGACY_SYSDESIGN_H3[6], "") or "None.",
    }
    return "\n\n".join(f"{h3}\n\n{body_by_h3[h3]}" for h3 in REQUIRED_APPENDIX_H3)
