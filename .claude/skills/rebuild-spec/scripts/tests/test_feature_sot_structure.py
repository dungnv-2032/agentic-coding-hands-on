"""Tests for `_feature_sot_structure_lib.py` -- `## 3. System Design` (T-04/T-05/
T-06/T-07/T-08 + the D8 client-behavior anchor) and `## 5. Verification & Technical
Notes` (T-09/T-14/T-15/T-19/T-20/T-21/T-22).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from _audience_split_md_sections_lib import split_sections  # noqa: E402
from _feature_sot_extract_lib import (  # noqa: E402
    CclPieces, ExtractedTechPieces, ExtractedThreadPieces, UsBlock, extract_v27_thread_pieces,
)
from _feature_sot_mapping_lib import ActionRecord, assign_codes, build_action_records  # noqa: E402
from _feature_sot_structure_lib import (  # noqa: E402
    _action_title, assign_capability_and_detail, build_action_rungs, build_system_design,
    build_verification_notes,
)
from _feature_sot_technical_lib import compose_action_thread  # noqa: E402
from _spec_constants import REQUIRED_VERIF_H3, _LEGACY_SYSDESIGN_H3  # noqa: E402

FIXTURES = _TESTS_DIR / "fixtures" / "action_thread"


def _load_fixture(feature: str) -> tuple[str, str]:
    old = (FIXTURES / f"{feature}_technical-spec.md").read_text()
    twin = (FIXTURES / f"{feature}_functional-spec.md").read_text()
    return old, twin


def _pieces(**overrides) -> ExtractedTechPieces:
    base = dict(
        preamble="", overview="", polymorphic="", ccl=CclPieces(), us_blocks=[],
        edge_cases_body="", key_entities="", artifact_refs="", assumptions="",
        source_refs="", unresolved_questions="", source_walkthrough="", db_impact="",
        unknown_h2=[],
    )
    base.update(overrides)
    return ExtractedTechPieces(**base)


def test_system_design_carries_all_seven_required_h3_in_order():
    body = build_system_design(_pieces(), "N/A — no HTTP/RPC surface; background feature only.")
    _, h3 = split_sections(body, 3)
    present = [h for h in h3 if h in _LEGACY_SYSDESIGN_H3]
    assert present == _LEGACY_SYSDESIGN_H3


def test_system_design_ends_with_the_client_behavior_anchor():
    # D8: FeatureSpec.missing_client_behavior_anchor scans ## 3.'s OWN bounds --
    # the anchor must be somewhere inside this returned body, not merely nearby.
    body = build_system_design(_pieces(), "N/A")
    assert "**Client behavior:** see" in body
    assert "behavior-logic.md" in body


def test_polymorphic_and_key_entities_land_under_data_model():
    pieces = _pieces(key_entities="| Entity | Table |\n|---|---|\n| X | y |",
                      polymorphic="### DISC-001 — X.kind\n\nsomething")
    body = build_system_design(pieces, "N/A")
    _, h3 = split_sections(body, 3)
    data_model = h3["### 3.2 Data Model"]
    assert "#### Key Entities" in data_model and "| X | y |" in data_model
    assert "#### Polymorphic Behavior" in data_model and "DISC-001" in data_model


def test_sm_alg_int_blocks_or_none_literal():
    # SM/ALG/INT blocks are PROMOTED SIBLING H3s to their container (same convention
    # the old CCL shape used, and validate_feature_spec.py's own sysdesign_subsections
    # check explicitly expects: "a populated ### 3.3/3.5/3.6 legitimately holds its
    # SM-###/ALG-###/INT-### blocks as PROMOTED SIBLING H3 headings") -- so a filled
    # container's OWN dict body is empty, and the block appears as the NEXT H3 key.
    ccl = CclPieces(sm_blocks=[("### SM one (SM-001)", "body")])
    body = build_system_design(_pieces(ccl=ccl), "N/A")
    _, h3 = split_sections(body, 3)
    assert h3["### 3.3 State Management"].strip() == ""
    assert "### SM one (SM-001)" in h3
    assert h3["### SM one (SM-001)"].strip() == "body"
    assert h3["### 3.5 Algorithms & Processing Logic"].strip() == "None."
    assert h3["### 3.6 Integrations"].strip() == "None."


def test_verification_notes_carries_all_five_required_h3_in_order():
    body = build_verification_notes(_pieces())
    _, h3 = split_sections(body, 3)
    present = [h for h in h3 if h in REQUIRED_VERIF_H3]
    assert present == REQUIRED_VERIF_H3


def test_verification_notes_us_subblock_carries_independent_test_and_scenarios():
    us = UsBlock(code="US001_X", title="x", priority="P1", fields={
        "Independent Test": "Do the thing and check.",
        "Acceptance Scenarios": "1. **Given** a, **When** b, **Then** c.",
    })
    body = build_verification_notes(_pieces(us_blocks=[us]))
    _, h3 = split_sections(body, 3)
    verif = h3["### 5.1 Technical Verification"]
    assert "#### US001_X" in verif
    assert "Do the thing and check." in verif
    assert "**Given** a" in verif


def test_verification_notes_defaults_when_nothing_present():
    body = build_verification_notes(_pieces())
    _, h3 = split_sections(body, 3)
    assert h3["### 5.1 Technical Verification"].strip() == "None."
    assert h3["### 5.2 Assumptions"].strip() == "None recorded."
    assert h3["### 5.3 Unresolved Questions"].strip() == "None recorded."


def test_fence_boundaries_preserved_when_relocating_a_pseudocode_block():
    # Security Considerations (phase-10.md): a mangled fence during relocation
    # could expose a code block as rendered prose, or swallow the rest of the doc.
    fenced_alg_block = (
        "**Source:** `x.rb:1`\n\n"
        "**Pseudocode:**\n```ruby\nif a > b\n  do_thing\nend\n```\n"
    )
    ccl = CclPieces(alg_blocks=[("### Do a computation (ALG-001)", fenced_alg_block)])
    body = build_system_design(_pieces(ccl=ccl), "N/A")
    assert body.count("```ruby") == 1
    assert body.count("```") == 2  # exactly one opening + one closing delimiter
    # the code between the fences survives byte-for-byte
    assert "if a > b\n  do_thing\nend" in body


# ---------------------------------------------------------------------------
# rebuild-spec 27.7.0 (action-thread reshape, phase 05) -- `## 3. Actions` bucket
# assignment and rung rendering. Small synthetic inputs (this is pure-function
# coverage of the assignment/rendering logic, not a corpus-fidelity concern --
# real-document coverage lives in test_action_thread_composer.py).
# ---------------------------------------------------------------------------

def _thread_pieces(**overrides) -> ExtractedThreadPieces:
    base = dict(
        preamble="", overview_body="", sysdesign_verbatim={}, endpoints=[],
        endpoints_note="", int_blocks=[], mapping_rows=[], capability_buckets=[],
        verif_body="", source_walkthrough="", db_impact_body="", unknown_h2=[],
    )
    base.update(overrides)
    return ExtractedThreadPieces(**base)


def _action(aid: str, codes: set[str] | None = None) -> ActionRecord:
    # `handler`'s method segment is real, case-preserving CamelCase
    # (`NewSession`), while `method_norm` is its lowercased-at-construction
    # sibling (`_ActionBuilder._new`'s real derivation, "newsession") -- the two
    # MUST differ in case, or a title-ladder assertion on the humanized result
    # can pass by accident without ever reaching the case-preserving branch it
    # means to prove (negative-tests-must-reach-the-branch; this fixture used to
    # make handler and method_norm identical strings, so two `_action_title`
    # tests passed today without exercising the bug they claimed to cover).
    return ActionRecord(
        id=aid, handler="Ctrl#NewSession", handler_norm="ctrl#newsession",
        handler_class_norm="ctrl", method_norm="newsession", codes=codes or set(),
    )


def test_action_with_no_traceable_capability_lands_in_last_bucket():
    """wire-format-contract.md § 3: "An action whose capability cannot be
    determined goes in the LAST bucket, never the first" -- never guessed toward
    the front.

    Phase 03 rewrite: bucketing now reads the twin's own § 2 table
    (`cap_code_map`), not a BR/DEC-derived map built from the OLD file's `## 4.N`
    body (that map is deleted -- measured dead on the real corpus, see phase-03's
    Key Insights). So this test's twin carries a REAL `Business Rules` column
    declaring `BR-001` on `CAP-01` -- A1 traces through the twin table, and
    codeless-for-this-twin A2 (`FR-999` appears nowhere in it) still lands last.
    Both halves of the contract sentence now reach the branch they name."""
    a_traceable = _action("A1", codes={"BR-001"})
    a_untraceable = _action("A2", codes={"FR-999"})  # not in the twin's code columns
    owner = {"BR-001": "A1"}
    twin = (
        "## 2. Functional Capabilities\n\n"
        "| ID | Capability | Business Rules |\n|---|---|---|\n"
        "| CAP-01 | First | BR-001 |\n| CAP-02 | Second | — |\n"
    )
    buckets, unbound = assign_capability_and_detail(
        _thread_pieces(), [a_traceable, a_untraceable], owner, twin, "Feature",
    )
    assert len(buckets) == 2
    assert a_traceable in buckets[0][2]
    assert a_untraceable in buckets[-1][2]
    assert a_untraceable.detail_ref == "§ 3.2"
    assert unbound == 1


def test_build_action_rungs_omits_who_and_request_never_invents_them():
    a = _action("A1")
    a.write_reason = "read-only"
    text = build_action_rungs(a, _thread_pieces(), {}, {}, {})
    assert "**Who**" not in text
    assert "**Request**" not in text
    assert "N/A" not in text
    assert "None." not in text
    assert "**Result** · — **read-only**." in text


def test_build_action_rungs_rule_rung_only_when_bin1_owner():
    from _feature_sot_extract_lib import ThreadCapabilityBucket, ThreadRuleBlock

    bucket = ThreadCapabilityBucket(
        heading="### 4.1 X",
        br_blocks=[ThreadRuleBlock(code="BR-001", heading="### Some rule (BR-001)", body="**Source:** x.rb:1")],
    )
    pieces = _thread_pieces(capability_buckets=[bucket])
    a = _action("A1")
    text_owned = build_action_rungs(a, pieces, {"BR-001": ["A1"]}, {}, {})
    assert "**Rule** ·" in text_owned
    assert "Some rule (BR-001)" in text_owned
    text_not_owned = build_action_rungs(a, pieces, {"BR-001": ["A2"]}, {}, {})
    assert "**Rule**" not in text_not_owned


def test_build_action_rungs_order_follows_rung_labels_contract():
    from _spec_constants import RUNG_LABELS

    a = _action("A1")
    a.write_notes = ["did a thing"]
    a.source_citations = ["x.rb:1"]
    text = build_action_rungs(a, _thread_pieces(), {}, {"A1": ["fe note"]}, {"A1": ["be note"]})
    present = [label for label in RUNG_LABELS if f"**{label}**" in text]
    positions = [text.index(f"**{label}**") for label in present]
    assert positions == sorted(positions)


# --------------------------------------------------------------------------- #
# `_action_title` family priority (phase 02, self-sufficiency v27.8)
# --------------------------------------------------------------------------- #
def test_action_title_prefers_fr_name_over_br_rule_sentence():
    # `sorted(action.codes)` used to pick BR-001 first (lexicographic accident:
    # "BR-001" < "FR-204") and silently return its rule-sentence name as the H4
    # title instead of the action-shaped FR-204 name -- plan.md's own finding.
    a = _action("A1", codes={"BR-001", "FR-204"})
    name_by_code = {
        "BR-001": "Approve/reject only apply while pending",
        "FR-204": "Approve a pending listing",
    }
    assert _action_title(a, name_by_code) == "Approve a pending listing"


def test_action_title_prefers_us_name_over_dec_rule_sentence():
    a = _action("A1", codes={"DEC-001", "US084"})
    name_by_code = {
        "DEC-001": "Feedback content must be present",
        "US084": "View the admin dashboard",
    }
    assert _action_title(a, name_by_code) == "View the admin dashboard"


def test_action_title_never_returns_a_rule_family_name_even_as_last_resort():
    # Every declared code belongs to a rule family (BR/DEC/SM/ALG/INT) -- even
    # though DEC-001 has a `name_by_code` entry, `_action_title` must fall through
    # to the humanized handler/method name rather than ever surface it.
    #
    # Phase 05 (defect 3): `_action`'s fixture now makes `handler` ("Ctrl#
    # NewSession") and `method_norm` ("newsession") differ in CASE -- against
    # pre-fix code (which reads `action.method_norm`), this asserts "Newsession"
    # and FAILS (the fallback yields "Newsession", not "New session") -- the
    # branch this test claims to cover was never actually reached before this
    # phase, since the old fixture's handler and method_norm were the identical
    # string ("ctrl#a1" / "a1"), so no case difference could ever surface.
    a = _action("A1", codes={"DEC-001", "SM-002"})
    name_by_code = {
        "DEC-001": "Feedback content must be present",
        "SM-002": "A listing moves from pending to approved",
    }
    assert _action_title(a, name_by_code) == "New session"


def test_action_title_falls_back_to_handler_when_no_codes_resolve():
    # Phase 05: same fixture-case-difference reasoning as the test above --
    # against pre-fix code (`action.method_norm`), this asserts "Newsession" and
    # FAILS. Post-fix (`action.handler`, case-preserving, humanized): "New
    # session". "falls back to handler" always meant the handler-derived title,
    # not necessarily the raw un-humanized string -- see the ladder's rung 2 for
    # the genuinely-verbatim case (no "#" in handler), covered separately below.
    a = _action("A1", codes={"BR-001"})
    assert _action_title(a, {}) == "New session"


def test_action_title_raw_handler_with_no_hash_is_verbatim_not_humanized():
    """Ladder rung 2 (phase 05): a `handler` carrying no "#" at all is the
    `ensure_raw` shape (a DB-Impact fallback event with no resolvable class,
    e.g. F002's real "Scheduled cleanup") -- the raw text IS the title,
    verbatim, never humanized (it is real content, not a guess)."""
    a = ActionRecord(
        id="A1", handler="Scheduled cleanup", handler_norm="raw:scheduled cleanup",
        handler_class_norm="", method_norm="", codes=set(),
    )
    assert _action_title(a, {}) == "Scheduled cleanup"


def test_action_title_perform_bug_on_a_real_kept_job_class():
    """RED against pre-fix code (`action.method_norm` -> "perform" -> "Perform"):
    `DownloadListingImageJob` is one of phase 04's own 11 corpus-measured KEPT
    real job classes (`_action_thread_handler_lib.is_job_class`'s docstring) --
    `ensure_background` gives it exactly this shape (`handler=f"{cls}#perform"`,
    `is_background=True`, `method_norm="perform"` via `_new`'s default
    derivation). NOT F002-based: F002's own 11 DB-Impact fallback events are ALL
    dropped by `is_job_class` (fb_kept=0 per `measure-corpus.py`'s per-feature
    table), so F002 alone cannot demonstrate this sub-bug -- see the companion
    note in test_action_thread_composer.py."""
    a = ActionRecord(
        id="A1", handler="DownloadListingImageJob#perform",
        handler_norm="downloadlistingimagejob#perform",
        handler_class_norm="downloadlistingimagejob", method_norm="perform",
        is_background=True, codes=set(),
    )
    title = _action_title(a, {})
    assert title != "Perform", f"still the bare method_norm fallback: {title!r}"
    assert title == "Download listing image"


# ---------------------------------------------------------------------------
# Phase 03 (defect 1) -- capability bucketing reads the twin's own § 2 table
# instead of the OLD file's BR/DEC-derived map. Corpus-fidelity coverage on the
# real F002 fixture pair (verbatim copy, see fixtures/action_thread/README.md);
# small synthetic-input coverage of `assign_capability_and_detail` itself lives
# above, next to the rest of this module's pure-function tests.
# ---------------------------------------------------------------------------

_CAP_SECTION_RE = re.compile(r"(?m)^### 3\.\d+ CAP-\d+.*$")
_ACTION_HEADING_RE = re.compile(r"(?m)^#### A\d+")


def _cap_section_bodies(text: str) -> list[str]:
    marks = list(_CAP_SECTION_RE.finditer(text))
    return [
        text[m.end():(marks[i + 1].start() if i + 1 < len(marks) else len(text))]
        for i, m in enumerate(marks)
    ]


def test_f002_multi_capability_buckets_are_not_all_empty():
    """RED against pre-fix code: F002's twin declares 6 CAP rows, but the OLD
    BR/DEC-derived map resolves almost nothing (actions carry FR/US codes, not
    BR/DEC), so every action falls to `n - 1` -- measured baseline distribution
    `[0,0,0,0,0,16]`, i.e. 5 of 6 `### 3.N CAP-NN` bodies hold zero `#### A`
    headings. Phase 03 buckets on the twin's own § 2 table instead -- measured
    fixed distribution `[2,2,2,2,1,7]`, zero empty buckets."""
    old, twin = _load_fixture("F002")
    result = compose_action_thread(old, twin)
    bodies = _cap_section_bodies(result.text)
    assert len(bodies) == 6
    empty = sum(1 for b in bodies if not _ACTION_HEADING_RE.search(b))
    assert empty == 0


def test_f002_seven_named_actions_land_in_the_seven_named_capabilities():
    """The brief's own hand-worked expectation (phase-03 Implementation Steps,
    step 7) -- asserted explicitly per action, not just as a distribution count,
    because a distribution count alone would not catch an off-by-one in the
    index. Verified against the real library's own `build_action_records` output
    (F002 has 16 actions total; these are the 7 the phase named)."""
    old, twin = _load_fixture("F002")
    pieces = extract_v27_thread_pieces(old)
    actions = build_action_records(pieces)
    owner, _rule_owners = assign_codes(pieces, actions)
    feature_name = "F002_AuthenticationAndSession"
    buckets, _unbound = assign_capability_and_detail(pieces, actions, owner, twin, feature_name)

    by_id = {a.id: a for a in actions}
    cap_of = {a.id: cap_id for cap_id, _title, cap_actions in buckets for a in cap_actions}

    expected = {
        "A1": "CAP-01", "A2": "CAP-01", "A3": "CAP-03", "A4": "CAP-03",
        "A5": "CAP-05", "A6": "CAP-04", "A7": "CAP-02",
    }
    for action_id, expected_cap in expected.items():
        assert action_id in by_id, f"{action_id} missing from F002 action set"
        assert cap_of[action_id] == expected_cap, (
            f"{action_id} (codes={sorted(by_id[action_id].codes)}) landed in "
            f"{cap_of[action_id]}, expected {expected_cap}"
        )
