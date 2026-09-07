"""Tests for `_feature_sot_extract_lib.extract_v27_tech_pieces` -- the v27.0
technical-spec.md unpacker. Covers the CCL container/promoted-sibling classification
(mirrors `_audience_split_ccl_normalize_lib.LEGACY_CCL_H3`'s own shape) and the
per-US-NESTED block case (content-preservation-map T-17), which real corpus data
(st-post/docs/features/F001_Auth/technical-spec.md, BR-006 sitting between US020 and
US021) proved is a real, not merely theoretical, input shape.
"""
from __future__ import annotations

import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from _feature_sot_extract_lib import extract_v27_tech_pieces  # noqa: E402

OLD_TECH = """---
authored_by: rebuild-spec
---
<!-- Contract: references/feature-spec-researcher-contract.md -->

# F999_Sample — Technical Spec

**Priority**: P2
**Type**: ui
**Generated**: 2026-01-01

## Overview

Sample technical overview sentence.

## Polymorphic Behavior

N/A — no discriminator fields in Key Entities.

## Cross-Cutting Logic

### Requirements

| Code | Description | Endpoint/Handler | Verifiable |
|------|-------------|------------------|------------|
| FR-001 | Sample requirement one | `POST /sample` via `SampleController#create` | yes |

**Source:** `app/controllers/sample_controller.rb:1-10`

### Business Rules

None.

### Sample business rule statement. (BR-001)
**Linked FR:** FR-001
**Source:** `app/models/sample.rb:1-5`
**Applies to:** Sample creation

### Decision Logic

#### Sample decision statement. (DEC-001)
**subtype:** render
**Source:** `app/models/sample.rb:20-25`

### State Machines

None.

### Tracks the sample status state machine (states: draft, active) (SM-001)
**kind:** entity
**Linked FR:** FR-001
**Source:** `app/models/sample.rb:10-15`

### Algorithms

None.

### External Integrations

None.

### Sends queue job to SampleJob (INT-001)
**Linked FR:** FR-001
**Source:** `app/jobs/sample_job.rb:1-5`

### Verification

- **SC-001** — Sample check passes (covers FR-001, BR-001)

## User Stories

### US001_SampleStory — Sample story (Priority: P1)

**What happens:** A user does the sample thing and it works.
**Why this priority:** Core to the sample flow.

**Rules enforced:**

### Nested per-US rule statement. (BR-002)
**Linked FR:** FR-001
**Source:** `app/models/sample.rb:30-35`

### US002_OrphanStory — Orphan story (Priority: P2)

**What happens:** An orphan user does an orphan thing.

### Edge Cases

| Scenario | Behavior |
|----------|----------|
| Sample edge | HTTP 422 |

## Key Entities

| Entity | Table | Key Columns | Purpose |
|--------|-------|-------------|---------|
| Sample | `samples` | id, status | Sample entity |

## Artifact References

| Artifact | File | Codes Used | Reviewed |
|----------|------|------------|----------|
| Feature List | [feature-list.md](../../feature-list.md) | F999 | [x] |

## Assumptions

- Sample assumption one.

## Source Code References

| Symbol | Path | Purpose |
|--------|------|---------|
| SampleController#create | `app/controllers/sample_controller.rb:1-10` | creates sample |

## Unresolved Questions

1. **Sample topic**: sample question.

## Source Walkthrough

1. **File:** `app/models/sample.rb:1-40` — start here.

## DB Impact per Event

| Event/Endpoint | Table | Columns | Operation | Value Derivation | Source |
|---|---|---|---|---|---|
| POST /sample | `samples` | status | INSERT | literal | `app/controllers/sample_controller.rb:5` |

## Unknown Extra Section

Some unrouted content that must not be dropped.
"""


def test_overview_and_polymorphic_extracted_verbatim():
    p = extract_v27_tech_pieces(OLD_TECH)
    assert "Sample technical overview sentence." in p.overview
    assert "no discriminator fields" in p.polymorphic


def test_ccl_requirements_and_verification_extracted():
    p = extract_v27_tech_pieces(OLD_TECH)
    assert "FR-001" in p.ccl.requirements_body
    assert "SC-001" in p.ccl.verification_body


def test_ccl_promoted_sibling_blocks_classified_by_code_tag():
    p = extract_v27_tech_pieces(OLD_TECH)
    br_headings = [h for h, _ in p.ccl.br_blocks]
    dec_headings = [h for h, _ in p.ccl.dec_blocks]
    sm_headings = [h for h, _ in p.ccl.sm_blocks]
    int_headings = [h for h, _ in p.ccl.int_blocks]
    assert any("(BR-001)" in h for h in br_headings)
    assert any("(DEC-001)" in h for h in dec_headings)
    assert any("(SM-001)" in h for h in sm_headings)
    assert any("(INT-001)" in h for h in int_headings)
    # container headings ("### Business Rules" etc.) are never treated as blocks
    assert not any(h == "### Business Rules" for h in br_headings)


def test_per_us_nested_block_is_captured_not_dropped():
    """T-17: BR-002 sits BETWEEN the two `### US### -- ...` headings, positionally
    nested under US001 -- must land in the SAME ccl.br_blocks list as the
    cross-cutting BR-001, with a Linked US annotation, never silently skipped."""
    p = extract_v27_tech_pieces(OLD_TECH)
    br_headings = {h: b for h, b in p.ccl.br_blocks}
    nested = next(b for h, b in br_headings.items() if "(BR-002)" in h)
    assert "**Linked US:** US001_SampleStory" in nested


def test_us_blocks_parsed_with_fields():
    p = extract_v27_tech_pieces(OLD_TECH)
    codes = [us.code for us in p.us_blocks]
    assert codes == ["US001_SampleStory", "US002_OrphanStory"]
    us1 = p.us_blocks[0]
    assert us1.title == "Sample story"
    assert us1.priority == "P1"
    assert "A user does the sample thing" in us1.fields["What happens"]
    assert "Rules enforced" in us1.fields
    # the nested BR-002 heading is NOT part of US001's own field body (it started a
    # new H3 boundary) -- Rules enforced is empty/blank for this fixture
    assert "BR-002" not in us1.fields.get("Rules enforced", "")


def test_edge_cases_table_captured_separately_from_us_blocks():
    p = extract_v27_tech_pieces(OLD_TECH)
    assert "Sample edge" in p.edge_cases_body
    assert not any("Edge Cases" in us.title for us in p.us_blocks)


def test_known_h2_sections_all_extracted():
    p = extract_v27_tech_pieces(OLD_TECH)
    assert "Sample assumption one." in p.assumptions
    assert "SampleController#create" in p.source_refs
    assert "Sample topic" in p.unresolved_questions
    assert "start here" in p.source_walkthrough
    assert "INSERT" in p.db_impact
    assert "Feature List" in p.artifact_refs
    assert "samples" in p.key_entities


def test_unknown_h2_preserved_in_fallback_list():
    p = extract_v27_tech_pieces(OLD_TECH)
    names = [n for n, _ in p.unknown_h2]
    assert "## Unknown Extra Section" in names
