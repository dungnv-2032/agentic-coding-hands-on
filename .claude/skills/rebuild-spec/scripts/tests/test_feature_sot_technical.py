"""Tests for `_feature_sot_technical_lib.compose_technical_sot` -- the top-level
orchestrator over `_feature_sot_extract_lib`/`_feature_sot_mapping_lib`/
`_feature_sot_structure_lib`/`_feature_sot_capability_lib`. Covers idempotency, the
`## 2.`/`## Source Walkthrough`/`## DB Impact per Event` structural contract, the
content-conservation guarantee (round-trip: every non-heading content line survives
somewhere across the functional+technical pair, except exactly the T-12 lines whose
guard passed), and end-to-end coverage against the plan's own real fixtures.

`OLD_FUNC`/`OLD_TECH` are a synthetic, hand-paired v27.0-shaped functional/technical
pair -- labeled synthetic throughout. Shape verified against the real producer
(`_audience_split_compose_a_lib.py` / `_audience_split_ccl_normalize_lib.
LEGACY_CCL_H3`) and against the real corpus (st-post/docs/features/F001_Auth/*.md,
which is where the per-US-nested-BR-block and multi-line-**Users:**-block shapes
below were confirmed real, not merely theoretical).
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
from _feature_sot_functional_lib import compose_functional_sot  # noqa: E402
from _feature_sot_technical_lib import compose_technical_sot  # noqa: E402
from _spec_constants import A3_HEADING, B4_HEADING, _LEGACY_TECH_H2_5BUCKET  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[5]  # agent-kit/
_SOT_CORPUS = Path(__file__).resolve().parent / "fixtures" / "sot-corpus"
"""Real generated corpus, git-tracked. Lived under `plans/` (gitignored) until it took
the whole CI suite down at collection time — see fixtures/sot-corpus/README.md."""
EVIDENCE_DIR = _SOT_CORPUS

# Mirrors `test_feature_sot_functional.OLD_FUNC` byte-for-byte (kept as an inline
# copy, not a cross-test-file import, so this file's fixtures stay self-contained --
# same convention every other test module in this directory already uses).
OLD_FUNC = """---
authored_by: rebuild-spec
---
# F999_Sample

**Priority**: P2
**Type**: ui
**Generated**: migrated

**See also:** [`technical-spec.md`](./technical-spec.md) — endpoints, Source citations, pseudocode, key entities, and DB writes for a Dev/QA/SA audience.

## 1. Overview

**Problem:** Sample problem statement.
**Solution:** Sample solution statement.

**Users:**

- **Visitors** — do a sample thing.

**Goals:**

1. Do a sample thing.

**Non-Goals:** None called out.

## 2. Open Decisions

None — no unresolved domain confirmations.

## 3. Requirements

- **FR-001** Sample requirement one.

## 4. Business Rules

- Sample rule text. (BR-001)

## 5. Screens

N/A — background feature (no screens).

## 6. User Stories

### US001_SampleStory — Sample story (Priority: P1)

Sample narrative referencing § 4 and § 2 for cross-check.

## 7. Scenarios

Given a thing, When it happens, Then it works.

## 8. Edge Cases

| Scenario | What Happens | User-Facing Message |
|----------|--------------|----------------------|
| Empty input | Rejected | "Required." |

## 9. Edge Behaviours to Verify

Behaviours verified via scenarios above.

## 10. Configuration

No configuration constants.
"""

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

**Pseudocode:**
```ruby
validates :thing, presence: true
```

### Decision Logic

#### Sample decision statement. (DEC-001)
**subtype:** render
**Triggers in:** SCR001_Sample mount
**Involved entities:** Sample.status
**Source:** `app/models/sample.rb:20-25`

```pseudo
if sample.status == 'active' then show else hide
```

### State Machines

None.

### Tracks the sample status state machine (states: draft, active) (SM-001)
**kind:** entity
**Linked FR:** FR-001
**Source:** `app/models/sample.rb:10-15`

**States:** draft, active

### Algorithms

None.

### External Integrations

None.

### Sends queue job to SampleJob (INT-001)
**Linked FR:** FR-001
**Source:** `app/jobs/sample_job.rb:1-5`
**Type:** queue-job
**Target:** SampleJob
**Trigger:** on create
**Payload:** sample_id
**Failure handling:** none

### Verification

- **SC-001** — Sample check passes (covers FR-001, BR-001)

---

**Client behavior:** see [`behavior-logic.md`](../../generated/behavior-logic.md).

## User Stories

### US001_SampleStory — Sample story (Priority: P1)

**What happens:** A user does the sample thing and it works.
**Why this priority:** Core to the sample flow.
**Independent Test:** Do the sample thing and check the result.

**Acceptance Scenarios:**

1. **Given** a thing, **When** it happens, **Then** it works.

**Requirements fulfilled:**
- **FR-001** Sample requirement one — `POST /sample` via `SampleController#create`
  **Source:** `app/controllers/sample_controller.rb:1-10`

**Rules enforced:**

### Nested per-US rule statement. (BR-002)
**Linked FR:** FR-001
**Source:** `app/models/sample.rb:30-35`
**Applies to:** Sample nested check

**State transitions:** SM-001 (draft -> active)

**Verification:**
- **SC-002** — Nested check passes (covers BR-002)

---

### US002_OrphanStory — Orphan story (Priority: P2)

**What happens:** An orphan user does an orphan thing not known to the functional twin.
**Why this priority:** Edge flow.
**Independent Test:** Do the orphan thing.

**Acceptance Scenarios:**

1. **Given** an orphan, **When** it happens, **Then** nothing special.

**Requirements fulfilled:**
- **FR-001** Sample requirement one — `POST /sample` via `SampleController#create`
  **Source:** `app/controllers/sample_controller.rb:1-10`

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
- Sample assumption two.

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
| POST /sample | `samples` | status | INSERT | literal from request | `app/controllers/sample_controller.rb:5` |

## Unknown Extra Section

Some unrouted content that must not be dropped.
"""


def _compose_pair():
    func_result = compose_functional_sot(OLD_FUNC)
    tech_result = compose_technical_sot(OLD_TECH, func_result.text)
    return func_result, tech_result


def test_required_h2_present_in_order():
    _, tech_result = _compose_pair()
    _, h2 = split_sections(tech_result.text, 2)
    present = [h for h in h2 if h in _LEGACY_TECH_H2_5BUCKET]
    assert present == _LEGACY_TECH_H2_5BUCKET


def test_a3_b4_stay_literal_unnumbered_h2_at_the_end():
    _, tech_result = _compose_pair()
    assert A3_HEADING in tech_result.text
    assert B4_HEADING in tech_result.text
    assert f"## {A3_HEADING.lstrip('# ')}" not in tech_result.text.replace(A3_HEADING, "")
    walkthrough_idx = tech_result.text.index(A3_HEADING)
    db_impact_idx = tech_result.text.index(B4_HEADING)
    assert walkthrough_idx < db_impact_idx


def test_t12_guard_removes_matched_us_and_carries_the_orphan():
    """US001_SampleStory IS in OLD_FUNC's § 7 (its old § 6) -- REMOVED. US002 is not
    -- CARRIED with the [UNVERIFIED] prefix. Both branches exercised on the full
    pipeline, not just the isolated capability-lib unit test."""
    _, tech_result = _compose_pair()
    assert tech_result.removed == 1
    assert "A user does the sample thing and it works." not in tech_result.text
    assert (
        "[UNVERIFIED] carried from technical-spec §User Stories — "
        "An orphan user does an orphan thing" in tech_result.text
    )


def test_mapping_table_has_no_missing_twin_declared_codes():
    """Mirrors `validate_feature_spec.FeatureSpec.mapping_table_missing` exactly --
    every FR/BR/DEC/SM/US### code the (composed) twin declares anywhere must have a
    `## 2.` row."""
    func_result, tech_result = _compose_pair()
    code_re = re.compile(r"\b(?:FR|BR|DEC|SM)-\d{3}(?!\d)|\bUS\d{3}\w*(?!\d)")
    _, th2 = split_sections(tech_result.text, 2)
    map_codes = set(code_re.findall(th2["## 2. Functional → Technical Mapping"]))
    twin_codes = set(code_re.findall(func_result.text))
    assert twin_codes <= map_codes


def test_unknown_h2_preserved_before_source_walkthrough():
    _, tech_result = _compose_pair()
    assert "## Unknown Extra Section" in tech_result.text
    assert tech_result.text.index("## Unknown Extra Section") < tech_result.text.index(A3_HEADING)


def test_fence_integrity_across_relocated_pseudocode_blocks():
    _, tech_result = _compose_pair()
    text = tech_result.text
    assert text.count("```ruby") == 1
    assert text.count("```pseudo") == 1
    assert text.count("```") == 4  # 2 opens + 2 closes, none swallowed/duplicated


def test_idempotent_second_run_is_a_no_op():
    func_result, tech_result = _compose_pair()
    second = compose_technical_sot(tech_result.text, func_result.text)
    assert second.text == tech_result.text
    assert second.removed == 0


def test_needs_llm_fill_true_on_fresh_compose():
    _, tech_result = _compose_pair()
    assert tech_result.needs_llm_fill is True


# --------------------------------------------------------------------------- #
# Content conservation -- round-trip guard (Implementation Step 7)
# --------------------------------------------------------------------------- #
_LABEL_RE = re.compile(r"^\*\*[^*:]+:\*\*\s*(.*)$")


def _value_only(line: str) -> str:
    """Strip a leading `**Label:**` marker (if any) -- a relabel (Goals->Scope) or a
    merge-with-prefix (Why this priority -> "Priority rationale: ...") changes the
    LABEL, never the VALUE; comparing on value only makes both sanctioned
    transformations transparent to the conservation check instead of false
    positives."""
    m = _LABEL_RE.match(line)
    if not m:
        return line
    return m.group(1).strip()


_SECTION_REF_RE = re.compile(r"§\s*\d+")


def _content_lines(text: str) -> list[str]:
    """Non-heading, non-table, non-bare-label content lines -- the population this
    round-trip guard checks line-for-line. Table ROWS are excluded on purpose: T-03/
    T-06/T-16/etc. are sanctioned MERGEs into tables with DIFFERENT columns (e.g. the
    old 4-column CCL Requirements table becomes the new 5-column mapping table) --
    the cell VALUES survive (checked by dedicated tests, e.g.
    `test_mapping_table_has_no_missing_twin_declared_codes`), but the exact row text
    legitimately does not, so it is not this check's job."""
    out = []
    for raw in text.splitlines():
        s = raw.strip()
        if not s or re.match(r"^#{1,6}\s", s) or s.startswith("|"):
            continue
        if re.match(r"^\*\*[^*:]+:\*\*$", s):  # a bare label with no inline value
            continue
        # T-16: "Requirements fulfilled" bullets are a MERGE, not a byte-preserving
        # MOVE -- only the FR code + any endpoint token are folded into ## 2./§ 3.4
        # (content-preservation-map.md's own words: "the FR codes make the ## 2.
        # row"). The bullet's own descriptive prose is redundant with that row and
        # is not separately preserved verbatim; its FR code IS checked, by
        # `test_mapping_table_has_no_missing_twin_declared_codes`.
        if re.match(r"^-\s+\*\*FR-\d+\*\*", s):
            continue
        out.append(s)
    return out


def test_content_conservation_every_line_survives_except_the_guarded_t12_removal():
    func_result, tech_result = _compose_pair()
    combined_output = func_result.text + "\n" + tech_result.text
    # F-03's in-body `§ N` renumber is a SANCTIONED rewrite (old § 4 -> new § 5,
    # old § 2 -> new § 3 in this fixture) -- normalize both sides before comparing so
    # the round-trip guard isn't tripped by the very rewrite it's supposed to allow.
    normalized_output = _SECTION_REF_RE.sub("§ N", combined_output)

    removed_value = "A user does the sample thing and it works."
    missing = []
    for ln in _content_lines(OLD_FUNC) + _content_lines(OLD_TECH):
        value = _SECTION_REF_RE.sub("§ N", _value_only(ln))
        if not value:
            continue
        if value == removed_value:
            continue  # accounted for by the explicit T-12 removal below
        if value in normalized_output or _SECTION_REF_RE.sub("§ N", ln) in normalized_output:
            continue
        missing.append(ln)

    assert missing == [], f"content lost (not the T-12 removal): {missing}"
    # the removal count is EXPLICIT, not hand-waved (success criteria).
    assert tech_result.removed == 1
    assert removed_value not in combined_output


# --------------------------------------------------------------------------- #
# Real-fixture coverage (plan-mandated evidence files)
# --------------------------------------------------------------------------- #
def test_real_g2_functional_fixture_composes_without_error():
    text = (EVIDENCE_DIR / "corpus-g2" / "F999_Sample.functional-spec.md").read_text(encoding="utf-8")
    result = compose_functional_sot(text)
    assert "## 2. Functional Capabilities" in result.text
    # idempotent on its own output
    assert compose_functional_sot(result.text).text == result.text


def test_real_g2_technical_fixture_composes_without_error():
    tech_text = (EVIDENCE_DIR / "corpus-g2" / "F010_FollowSystem.technical-spec.md").read_text(
        encoding="utf-8"
    )
    # F010 has no real functional-spec.md twin in the fixture set -- an empty twin is
    # the documented degraded input (no CAP rows, no § 7 codes): every capability
    # falls into the single "### 4.1 {Feature name}" bucket and every US narrative is
    # CARRIED (branch B), never guessed as matched.
    result = compose_technical_sot(tech_text, "")
    _, h2 = split_sections(result.text, 2)
    assert set(_LEGACY_TECH_H2_5BUCKET) <= set(h2)
    assert result.removed == 0  # empty twin -- nothing can match branch A
    assert "### 4.1 F010_FollowSystem" in result.text
    assert compose_technical_sot(result.text, "").text == result.text
