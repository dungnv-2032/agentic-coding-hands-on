"""Tests for `_feature_sot_capability_lib.py` -- `## 4. Technical Behavior by
Capability` bucket assembly, and **T-12, the single sanctioned REMOVE in the whole
plan**. Both branches are exercised and named explicitly per phase-10's non-
negotiable testing rule.
"""
from __future__ import annotations

import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from _feature_sot_capability_lib import (  # noqa: E402
    build_capability_body, cap_buckets, cap_code_map, twin_us_codes,
)
from _feature_sot_extract_lib import CclPieces, UsBlock  # noqa: E402

FIXTURES = _TESTS_DIR / "fixtures" / "action_thread"

TWIN_WITH_US001 = """
## 7. User Stories

### US001_SampleStory — Sample story (Priority: P1)
"""

TWIN_WITHOUT_US001 = """
## 7. User Stories

### US999_SomeOtherStory — Some other story (Priority: P1)
"""

TWIN_WITH_CAPABILITIES = """
## 2. Functional Capabilities

| ID | Capability | What the user can do | Requirements | Screens |
|----|------------|------------------------|---------------|---------|
| CAP-01 | Sample capability | Do the sample thing | FR-001 | — |
| CAP-02 | Second capability | Do a second thing | FR-002 | — |
"""

TWIN_EMPTY_CAPABILITIES = """
## 2. Functional Capabilities

| ID | Capability | What the user can do | Requirements | Screens |
|----|------------|------------------------|---------------|---------|
"""


def _us(code: str, what_happens: str) -> UsBlock:
    return UsBlock(code=code, title=code, priority="P1", fields={"What happens": what_happens})


def test_twin_us_codes_reads_the_sot_shaped_section_7():
    assert twin_us_codes(TWIN_WITH_US001) == {"US001_SampleStory"}


def test_cap_buckets_falls_back_to_single_bucket_when_empty():
    buckets = cap_buckets(TWIN_EMPTY_CAPABILITIES, "F999_Sample")
    assert buckets == [("CAP-01", "F999_Sample")]


def test_cap_buckets_reads_real_cap_rows_in_order():
    buckets = cap_buckets(TWIN_WITH_CAPABILITIES, "F999_Sample")
    assert buckets == [("CAP-01", "Sample capability"), ("CAP-02", "Second capability")]


# --------------------------------------------------------------------------- #
# T-12 GUARD -- both branches, named explicitly
# --------------------------------------------------------------------------- #
def test_t12_branch_a_narrative_removed_when_twin_has_the_us_code():
    """Branch A (REMOVE): the twin's § 7 already carries US001_SampleStory, so the
    `**What happens:**` narrative for that code is dropped entirely -- `removed`
    increments by exactly 1, and the literal narrative text does not survive
    anywhere in the capability body."""
    ccl = CclPieces()
    us_blocks = [_us("US001_SampleStory", "A user does the sample thing and it works.")]
    body, removed = build_capability_body(ccl, us_blocks, "", TWIN_WITH_US001, "F999_Sample")
    assert removed == 1
    assert "A user does the sample thing and it works." not in body
    assert "[UNVERIFIED] carried from technical-spec §User Stories" not in body


def test_t12_branch_b_narrative_carried_forward_with_unverified_prefix_when_twin_lacks_it():
    """Branch B (MOVE, guard fails): the twin's § 7 does NOT carry US001_SampleStory
    (a different code, US999, is the only one declared) -- the narrative is
    preserved, prefixed exactly `[UNVERIFIED] carried from technical-spec
    §User Stories — `, never silently dropped."""
    ccl = CclPieces()
    us_blocks = [_us("US001_SampleStory", "A user does the sample thing and it works.")]
    body, removed = build_capability_body(ccl, us_blocks, "", TWIN_WITHOUT_US001, "F999_Sample")
    assert removed == 0
    assert (
        "[UNVERIFIED] carried from technical-spec §User Stories — "
        "A user does the sample thing and it works." in body
    )


def test_t12_mixed_batch_removes_one_and_carries_the_other_with_explicit_count():
    """Both branches in the SAME run -- the removal count must be exactly the
    number of US codes the guard actually matched, not the total US count."""
    ccl = CclPieces()
    us_blocks = [
        _us("US001_SampleStory", "Kept-out narrative (twin has this one)."),
        _us("US002_OrphanStory", "Carried-forward narrative (twin lacks this one)."),
    ]
    body, removed = build_capability_body(ccl, us_blocks, "", TWIN_WITH_US001, "F999_Sample")
    assert removed == 1
    assert "Kept-out narrative" not in body
    assert "[UNVERIFIED] carried from technical-spec §User Stories — Carried-forward narrative" in body


def test_t12_us_with_no_what_happens_field_is_simply_skipped():
    ccl = CclPieces()
    us_blocks = [UsBlock(code="US003_NoNarrative", title="x", priority="P1", fields={})]
    body, removed = build_capability_body(ccl, us_blocks, "", TWIN_WITHOUT_US001, "F999_Sample")
    assert removed == 0
    assert "**Carried User Story Narratives**" not in body


def test_br_and_dec_blocks_land_in_the_primary_bucket():
    ccl = CclPieces(
        br_blocks=[("### Sample rule. (BR-001)", "**Source:** `x.rb:1`")],
        dec_blocks=[("#### Sample decision. (DEC-001)", "**Source:** `x.rb:2`")],
    )
    body, _ = build_capability_body(ccl, [], "", TWIN_EMPTY_CAPABILITIES, "F999_Sample")
    assert "### Sample rule. (BR-001)" in body
    assert "#### Sample decision. (DEC-001)" in body


def test_extra_capability_buckets_beyond_the_first_get_a_pending_regroup_note():
    """The composer must NEVER invent which BR/DEC blocks belong to CAP-02 -- every
    real block lands in bucket 1 (the first CAP row); any additional bucket is an
    honest 'pending manual regrouping' stub, never a guess."""
    ccl = CclPieces(br_blocks=[("### Sample rule. (BR-001)", "x")])
    body, _ = build_capability_body(ccl, [], "", TWIN_WITH_CAPABILITIES, "F999_Sample")
    assert "### 4.1 Sample capability" in body
    assert "### 4.2 Second capability" in body
    assert "pending manual regrouping" in body


def test_edge_cases_body_carried_under_the_primary_bucket():
    ccl = CclPieces()
    edge_cases = "| Scenario | Behavior |\n|----------|----------|\n| X | Y |"
    body, _ = build_capability_body(ccl, [], edge_cases, TWIN_EMPTY_CAPABILITIES, "F999_Sample")
    assert "#### Edge Cases" in body
    assert "| X | Y |" in body


def test_no_blocks_and_no_edge_cases_yields_the_na_sentinels():
    ccl = CclPieces()
    body, _ = build_capability_body(ccl, [], "", TWIN_EMPTY_CAPABILITIES, "F999_Sample")
    assert "N/A — no BR-### blocks routed to this capability." in body
    assert "N/A — no user-facing decision logic" in body
    assert "N/A — no edge cases carried from technical-spec.md." in body


# --------------------------------------------------------------------------- #
# `cap_code_map` (phase 03, defect 1) -- the twin's own § 2 `User Stories` /
# `Requirements` / `Business Rules` columns are the declared code->capability
# map `assign_capability_and_detail` buckets actions on.
# --------------------------------------------------------------------------- #

def test_cap_code_map_reads_the_real_f002_twin():
    """Direct unit test against the real F002 corpus twin (verbatim fixture, see
    fixtures/action_thread/README.md) -- the exact five code->index pairs the
    phase-03 spec names."""
    twin = (FIXTURES / "F002_functional-spec.md").read_text()
    code_map = cap_code_map(twin)
    assert code_map["FR-101"] == 0
    assert code_map["US006"] == 2
    assert code_map["FR-403"] == 4
    assert code_map["FR-602"] == 3
    assert code_map["BR-008"] == 5


def test_cap_code_map_first_writer_wins_on_a_duplicated_code():
    twin = (
        "## 2. Functional Capabilities\n\n"
        "| ID | Capability | Requirements |\n|---|---|---|\n"
        "| CAP-01 | First | FR-001 |\n| CAP-02 | Second | FR-001 |\n"
    )
    assert cap_code_map(twin) == {"FR-001": 0}


def test_cap_code_map_returns_empty_when_section_2_is_absent():
    twin = "## 1. Overview\n\nSomething else entirely.\n"
    assert cap_code_map(twin) == {}


def test_cap_code_map_returns_empty_on_a_header_only_table():
    twin = (
        "## 2. Functional Capabilities\n\n"
        "| ID | Capability | Requirements |\n|---|---|---|\n"
    )
    assert cap_code_map(twin) == {}


def test_cap_code_map_returns_empty_when_the_header_carries_no_code_columns():
    """A twin whose § 2 table declares only `ID`/`Capability` -- none of `User
    Stories`/`Requirements`/`Business Rules` present -- degrades to `{}` rather
    than raising (`col_index`/`cell` are absence-tolerant by construction)."""
    twin = (
        "## 2. Functional Capabilities\n\n"
        "| ID | Capability |\n|---|---|\n"
        "| CAP-01 | First |\n"
    )
    assert cap_code_map(twin) == {}
