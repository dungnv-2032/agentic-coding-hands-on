"""Tests for `_feature_sot_functional_lib.compose_functional_sot` --
content-preservation-map.md § B rows F-01 through F-08, plus idempotency, the
renumber map (headings AND in-body `§ N` cross-references), and the unknown-H2
fallback.

`OLD_FUNC` below is a synthetic v27.0-shaped (old 10-section) functional-spec.md,
labeled synthetic throughout -- its shape (field labels, section order) is copied
from the real producer (`_audience_split_compose_a_lib.render_functional_spec`'s own
`numbered` list and `render_overview`'s field order) and cross-checked against the
real corpus (st-post/docs/features/F001_Auth/functional-spec.md), never invented.
"""
from __future__ import annotations

import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from _audience_split_md_sections_lib import split_sections  # noqa: E402
from _feature_sot_functional_lib import compose_functional_sot  # noqa: E402
from _spec_constants import REQUIRED_H2_FUNC  # noqa: E402

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

## Some Unknown Section

Content a future format might add -- must not be dropped.
"""


def _compose():
    return compose_functional_sot(OLD_FUNC)


def test_required_sections_present_in_order():
    result = _compose()
    _, h2 = split_sections(result.text, 2)
    present = [h for h in h2 if h in REQUIRED_H2_FUNC]
    assert present == REQUIRED_H2_FUNC


def test_f01_goals_relabeled_to_scope_body_verbatim():
    result = _compose()
    _, h2 = split_sections(result.text, 2)
    overview = h2["## 1. Overview"]
    assert "**Scope:** " not in OLD_FUNC  # sanity: old text never had this label
    assert "1. Do a sample thing." in overview
    assert "**Scope:**" in overview
    assert "**Non-Scope:** None called out." in overview
    assert "**Goals:**" not in overview
    assert "**Non-Goals:**" not in overview


def test_f01_problem_solution_survive_verbatim():
    result = _compose()
    assert "**Problem:** Sample problem statement." in result.text
    assert "**Solution:** Sample solution statement." in result.text


def test_f02_users_block_carried_in_comment_and_actors_table_scaffolded():
    result = _compose()
    _, h2 = split_sections(result.text, 2)
    overview = h2["## 1. Overview"]
    assert "**Users:**" not in overview.split("<!--")[0]  # not left inline
    assert "do a sample thing" in overview  # original value preserved verbatim
    assert "**Actors**" in overview
    assert "| Actor | Description | Primary goal |" in overview


def test_f03_renumber_map_moves_body_to_new_heading():
    result = _compose()
    _, h2 = split_sections(result.text, 2)
    assert "None — no unresolved domain confirmations." in h2["## 3. Open Decisions"]
    assert "**FR-001** Sample requirement one." in h2["## 4. Requirements"]
    assert "Sample rule text. (BR-001)" in h2["## 5. Business Rules"]
    assert "N/A — background feature (no screens)." in h2["## 6. Screens"]
    assert "US001_SampleStory" in h2["## 7. User Stories"]
    assert "Given a thing" in h2["## 8. Scenarios"]
    assert "Empty input" in h2["## 9. Edge Cases"]
    assert "Behaviours verified" in h2["## 10. Edge Behaviours to Verify"]
    assert "No configuration constants." in h2["## 13. Configuration"]


def test_f03_in_body_section_refs_rewritten_by_the_same_map():
    # old "§ 4" (Business Rules) -> new "§ 5"; old "§ 2" (Open Decisions) -> new "§ 3".
    result = _compose()
    _, h2 = split_sections(result.text, 2)
    us_body = h2["## 7. User Stories"]
    assert "§ 5" in us_body
    assert "§ 3" in us_body
    assert "§ 4 and" not in us_body
    assert "and § 2 " not in us_body


def test_f04_f05_f06_new_sections_scaffolded_with_header_rows():
    result = _compose()
    _, h2 = split_sections(result.text, 2)
    assert (
        "| ID | Capability | What the user can do | User Stories | Requirements | "
        "Business Rules | Screens |"
    ) in h2["## 2. Functional Capabilities"]
    assert "N/A — none found." in h2["## 11. Risks & Known Issues"]
    assert "N/A — none found." in h2["## 12. Dependencies"]


def test_f07_see_also_line_preserved_in_preamble():
    result = _compose()
    assert "[`technical-spec.md`](./technical-spec.md)" in result.text


def test_unknown_h2_preserved_never_dropped():
    result = _compose()
    assert "## Some Unknown Section" in result.text
    assert "Content a future format might add" in result.text


def test_needs_llm_fill_true_on_fresh_compose():
    result = _compose()
    assert result.needs_llm_fill is True


def test_idempotent_second_run_is_a_no_op():
    first = _compose()
    second = compose_functional_sot(first.text)
    assert second.text == first.text
    assert second.moved == 0
    assert second.scaffolded == 0


def test_idempotent_reports_needs_llm_fill_false_once_scaffolds_are_filled():
    first = _compose()
    filled = first.text.replace(
        "| ID | Capability | What the user can do | User Stories | Requirements | "
        "Business Rules | Screens |\n"
        "|----|------------|------------------------|-----------------|---------------|"
        "-------------------|---------|",
        "| ID | Capability | What the user can do | User Stories | Requirements | "
        "Business Rules | Screens |\n"
        "|----|------------|------------------------|-----------------|---------------|"
        "-------------------|---------|\n"
        "| CAP-01 | Sample | Do the thing | US001 | FR-001 | BR-001 | — |",
    ).replace(
        "## 11. Risks & Known Issues\n\n| ID | Type | Description | Impact | Status |\n"
        "|----|------|--------------|--------|--------|\n\nN/A — none found.",
        "## 11. Risks & Known Issues\n\n| ID | Type | Description | Impact | Status |\n"
        "|----|------|--------------|--------|--------|\n\nRISK-01 | risk | x | y | confirmed",
    ).replace(
        "## 12. Dependencies\n\n| Dependency | Type | Why this feature needs it | Evidence |\n"
        "|------------|------|-----------------------------|----------|\n\nN/A — none found.",
        "## 12. Dependencies\n\n| Dependency | Type | Why this feature needs it | Evidence |\n"
        "|------------|------|-----------------------------|----------|\n\nNone at all — verified.",
    )
    result = compose_functional_sot(filled)
    assert result.text == filled  # still idempotent
    assert result.needs_llm_fill is False


def test_field_with_no_users_line_still_gets_an_actors_scaffold():
    no_users = OLD_FUNC.replace(
        "**Users:**\n\n- **Visitors** — do a sample thing.\n\n**Goals:**",
        "**Goals:**",
    )
    result = compose_functional_sot(no_users)
    _, h2 = split_sections(result.text, 2)
    overview = h2["## 1. Overview"]
    assert "**Actors**" in overview
    assert "<!--" not in overview  # nothing to carry -- no comment emitted
