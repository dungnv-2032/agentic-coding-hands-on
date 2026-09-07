"""Tests for `_screen_sot_compose_lib.compose_screen_sot` -- content-preservation-map.md
§ A rows S-01 through S-25, one test (or small group) per row, plus the phase's
structural requirements: idempotency, the anti-drift template check, the HARD
CONSTRAINT re-entry substring, the round-trip content-preservation guard, real-fixture
end-to-end coverage, and `resolve_sot_layout_rule_ids`.

Real fixtures (`evidence/corpus-g2/`) don't exercise every branch (real client-side
validation, populated server-side blocks, Component Variants/Child Routes, an unknown
H2) -- `FULL_G2_FIXTURE` below fills that gap. Its shape (column names, heading text,
`DEV_APPENDIX_MARKER`) is copied from `templates/screen-spec-template.md` at `main`
(the v27 template Mode C's own fixtures are built against), not invented; it is labeled
synthetic throughout and never treated as a stand-in for real-corpus provenance.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from _audience_split_mode_c_lib import DEV_APPENDIX_MARKER  # noqa: E402
from _screen_sot_compose_lib import (  # noqa: E402
    SOT_APPENDIX_ORDER, SOT_BA_ORDER, compose_screen_sot, resolve_sot_layout_rule_ids,
)

REPO_ROOT = Path(__file__).resolve().parents[5]  # agent-kit/
_SOT_CORPUS = Path(__file__).resolve().parent / "fixtures" / "sot-corpus"
"""Real generated corpus, git-tracked. Lived under `plans/` (gitignored) until it took
the whole CI suite down at collection time — see fixtures/sot-corpus/README.md."""
EVIDENCE_DIR = _SOT_CORPUS
CORPUS_G2 = EVIDENCE_DIR / "corpus-g2"
TEMPLATE_PATH = REPO_ROOT / "claude" / "skills" / "rebuild-spec" / "templates" / "screen-spec-template.md"

SCR020 = (CORPUS_G2 / "SCR020_LoginPage.spec.md").read_text(encoding="utf-8")
SCR012 = (CORPUS_G2 / "SCR012_ErrorNotFound.spec.md").read_text(encoding="utf-8")

FULL_G2_FIXTURE = f"""---
authored_by: rebuild-spec
---

# SCR999_FullSample — Screen Spec

**Screen**: SCR999: Full Sample
**Type**: atomic
**Route**: POST /sample
**Generated**: 2026-08-18

## Purpose

A synthetic fully-populated screen used to exercise every mechanical branch.

### Layout Sketch

A single form with a text field and a submit button. (app/views/sample.html:1)

## User Flow

### Happy Path

1. User fills the Email field and clicks Submit.

### Branches

| Decision point | Condition | Outcome on this screen | Source |
|----------------|-----------|------------------------|--------|
| Submit button | form valid | Form submits | `app/views/sample.html:5` |

## Data Inventory

| Display Label | Source | Format | Empty Behavior | Cross-ref |
|---------------|--------|--------|-----------------|-----------|
| Account balance | computed | currency | dash | MODEL001.balance |

## UI States

| State | Trigger | Visual Behavior | User Action Available | Source |
|-------|---------|------------------|-------------------------|--------|
| loading | API in-flight | spinner | none | `app/views/sample.html:2` |

## Validation & Error Feedback

### A) Client-side

| Field | Type | Required | Constraints | Async Check | Error Message |
|-------|------|----------|--------------|--------------|----------------|
| Email | email | yes | valid email format | `POST /check_email` | Please enter a valid email |

### B) Server-side

#### Submit

- **Endpoint:** `POST /sample`
- **Request:** `email`
- **Success:** `302` → redirect to confirmation
- **Errors:** `422` Email already taken
- **Trigger:** Submit button click
- **Source:** `app/controllers/sample_controller.rb:10`

## Interaction Patterns

- **Clicking Submit shows a loading spinner** — source: `app/views/sample.html:6`

## Conditional Rendering

| Condition | Type | Renders | Hidden | Notes |
|-----------|------|---------|--------|-------|
| `beta_enabled?` | feature-flag | Beta banner | — | Checks the beta feature flag |

{DEV_APPENDIX_MARKER}

### Layout Regions

| Region ID | Name | Position | Scrollable | Key Components | Responsive Behavior |
|-----------|------|----------|------------|-------------------|------------------------|
| R1 | Form | static | no | form, input, button | stacks vertically on mobile |

## Component Variants

| Component | Discriminating field | Variants on this screen | Screen-specific props/slots | Cross-ref |
|-----------|------------------------|-----------------------------|--------------------------------|-----------|
| Banner | kind | info, warning | text | DISC-001 |

## Child Routes

| Route | SCR | URL | Notes |
|-------|-----|-----|-------|
| Sample child | SCR999a | /sample/child | one-line purpose |

## Security Surface

| Guard | Type | Consequence if bypassed |
|-------|------|----------------------------|
| `require_login` | auth | Redirect to login |

## Weird Future Section

Some content this composer has never heard of before.

## Accessibility

| Aspect | Status | Notes |
|--------|--------|-------|
| ARIA roles/labels | present | aria-label on Submit |
| Keyboard navigation | supported | tab order follows form |
| Focus management | managed | autofocus on Email |
| Screen reader compatibility | tested | labels linked |

## Source References

1. Page/View: `app/views/sample.html:1`

## Source Walkthrough

1. **File:** `app/views/sample.html:1-10` -- the form itself.
"""

MINIMAL_NA_FIXTURE = f"""# SCR888_Blank — Screen Spec

**Screen**: SCR888: Blank
**Type**: atomic
**Route**: GET /blank
**Generated**: 2026-08-18

## Purpose

A minimal screen with nothing detected anywhere.

### Layout Sketch

Nothing but a blank page. (app/views/blank.html:1)

## User Flow

### Happy Path

1. User sees a blank page.

### Branches

`N/A — single-action screen, no branches`

## Data Inventory

`N/A — screen displays no dynamic data (static marketing/error page)`

## UI States

`N/A — no async ops`

## Validation & Error Feedback

### A) Client-side

`N/A — no client-side form validation detected.`

### B) Server-side

`N/A — no submit-style action handlers detected.`

## Interaction Patterns

`N/A — no non-trivial interaction patterns detected (only standard form input bindings).`

## Conditional Rendering

`N/A — no conditional rendering detected.`

{DEV_APPENDIX_MARKER}

### Layout Regions

| Region ID | Name | Position | Scrollable | Key Components | Responsive Behavior |
|-----------|------|----------|------------|-------------------|------------------------|
| R1 | Body | static | no | div | — |

## Security Surface

`N/A — no auth guards or permission checks detected on this screen.`

## Accessibility

| Aspect | Status | Notes |
|--------|--------|-------|
| ARIA roles/labels | absent | none |
| Keyboard navigation | unknown | none |
| Focus management | unmanaged | none |
| Screen reader compatibility | unknown | none |

## Source References

1. Page/View: `app/views/blank.html:1`

## Source Walkthrough

1. **File:** `app/views/blank.html:1` -- the whole screen.
"""


def _section(text: str, start: str, end: str) -> str:
    return text.split(start, 1)[1].split(end, 1)[0]


# --------------------------------------------------------------------------- #
# S-01 .. S-25, content-preservation-map.md § A -- one test group per row.
# --------------------------------------------------------------------------- #
def test_s01_purpose_merges_into_overview_purpose_field():
    result = compose_screen_sot(FULL_G2_FIXTURE)
    assert (
        "**Purpose:** A synthetic fully-populated screen used to exercise every "
        "mechanical branch." in result.text
    )


def test_s02_overview_actors_entry_exit_scaffolded():
    result = compose_screen_sot(FULL_G2_FIXTURE)
    overview = _section(result.text, "## 1. Overview", "## 2.")
    assert "**Actors:** {plain role names" in overview
    assert "**Entry Conditions:** {" in overview
    assert "**Exit Conditions:** {" in overview


def test_s03_layout_sketch_kept_verbatim_under_screen_layout():
    result = compose_screen_sot(FULL_G2_FIXTURE)
    layout = _section(result.text, "## 2. Screen Layout", "## 3.")
    assert "### Layout Sketch" in layout
    assert "A single form with a text field and a submit button." in layout


def test_s04_layout_regions_moved_into_screen_layout_reader_body():
    result = compose_screen_sot(FULL_G2_FIXTURE)
    layout = _section(result.text, "## 2. Screen Layout", "## 3.")
    assert "### Layout Regions" in layout
    assert "form, input, button" in layout


def test_s05_responsive_behavior_column_dropped_and_projected_to_section10():
    result = compose_screen_sot(FULL_G2_FIXTURE)
    layout = _section(result.text, "## 2. Screen Layout", "## 3.")
    assert "Responsive Behavior" not in layout  # column header gone (DRY)
    responsive = _section(result.text, "## 10. Responsive Behavior", "## Technical Appendix")
    assert "stacks vertically on mobile" in responsive
    assert "R1" in responsive


def test_s06_data_inventory_row_becomes_display_field_element_row():
    result = compose_screen_sot(FULL_G2_FIXTURE)
    elements = _section(result.text, "## 3. UI Elements", "## 4.")
    assert "| E01 | Account balance | display field | — | — | Always | — | computed | currency | dash | MODEL001.balance |" in elements


def test_s07_client_side_field_becomes_element_row_and_validation_row_and_async_check():
    result = compose_screen_sot(FULL_G2_FIXTURE)
    elements = _section(result.text, "## 3. UI Elements", "## 4.")
    assert "| E02 | Email | email | yes |" in elements
    validation = _section(result.text, "## 6. Validation & Feedback", "## 7.")
    assert "| E02 | valid email format | Please enter a valid email | submit |" in validation
    mapping = _section(result.text, "## Implementation Mapping", "## Component Variants")
    assert "endpoint" in mapping
    assert "POST /check_email" in mapping


def test_s08_server_side_block_moved_verbatim_to_implementation_mapping():
    result = compose_screen_sot(FULL_G2_FIXTURE)
    mapping = _section(result.text, "## Implementation Mapping", "## Component Variants")
    assert "#### Submit" in mapping
    assert "**Endpoint:** `POST /sample`" in mapping
    assert "Email already taken" in mapping


def test_s08_pending_server_rows_scaffold_a_placeholder_in_section6():
    result = compose_screen_sot(FULL_G2_FIXTURE)
    validation = _section(result.text, "## 6. Validation & Feedback", "## 7.")
    assert "{…}" in validation


def test_s09_ui_states_kept_renumbered():
    result = compose_screen_sot(FULL_G2_FIXTURE)
    states = _section(result.text, "## 5. UI States", "## 6.")
    assert "| loading | API in-flight | spinner | none |" in states


def test_s10_happy_path_kept_under_user_actions():
    result = compose_screen_sot(FULL_G2_FIXTURE)
    actions = _section(result.text, "## 4. User Actions", "## 5.")
    assert "User fills the Email field and clicks Submit." in actions


def test_s11_branches_kept_under_user_actions():
    result = compose_screen_sot(FULL_G2_FIXTURE)
    actions = _section(result.text, "## 4. User Actions", "## 5.")
    assert "| Submit button | form valid | Form submits | `app/views/sample.html:5` |" in actions


def test_s12_user_actions_intro_references_navigation_section_not_old_scope_text():
    result = compose_screen_sot(FULL_G2_FIXTURE)
    actions = _section(result.text, "## 4. User Actions", "### Available Actions")
    assert "## 8. Navigation" in actions
    assert "screen-flow.md" in actions


def test_s13_available_actions_scaffolded_with_header_only_and_needs_llm_fill():
    result = compose_screen_sot(FULL_G2_FIXTURE)
    available = _section(result.text, "### Available Actions", "### Happy Path")
    assert "{action name}" in available
    assert result.needs_llm_fill is True


def test_s14_interaction_patterns_moved_to_interaction_notes():
    result = compose_screen_sot(FULL_G2_FIXTURE)
    notes = _section(result.text, "### Interaction Notes", "## 5.")
    assert "Clicking Submit shows a loading spinner" in notes


def test_s15_conditional_rendering_projected_mechanically_with_tbd_element():
    result = compose_screen_sot(FULL_G2_FIXTURE)
    conditional = _section(result.text, "## 7. Conditional UI", "## 8.")
    assert "`beta_enabled?`" in conditional
    assert "{TBD}" in conditional
    assert "Beta banner" in conditional  # Renders -> Visible when


def test_s15_raw_expression_also_lands_in_implementation_mapping():
    result = compose_screen_sot(FULL_G2_FIXTURE)
    mapping = _section(result.text, "## Implementation Mapping", "## Component Variants")
    assert "`beta_enabled?`" in mapping
    assert "feature-flag" in mapping


def test_s16_navigation_scaffolded_and_never_invents_a_destination():
    result = compose_screen_sot(FULL_G2_FIXTURE)
    nav = _section(result.text, "## 8. Navigation", "## 9.")
    assert "screen-flow.md" in nav
    assert "### Entry Points" in nav
    assert "### Exits" in nav
    assert "{SCR###_Name" in nav  # scaffold placeholder, never a guessed real SCR code
    assert "SCR999a" not in nav  # would be an invented destination if it appeared


def test_s17_accessibility_moved_to_reader_body_with_5th_row_appended():
    result = compose_screen_sot(FULL_G2_FIXTURE)
    a11y = _section(result.text, "## 9. Accessibility", "## 10.")
    assert "| ARIA roles/labels | present |" in a11y
    assert "| Error announcement | [UNVERIFIED] |" in a11y


def test_s18_responsive_behavior_na_fallback_when_nothing_projected():
    result = compose_screen_sot(MINIMAL_NA_FIXTURE)
    responsive = _section(result.text, "## 10. Responsive Behavior", "## Technical Appendix")
    assert "N/A — no responsive behavior found in source." in responsive


def test_s19_dev_appendix_marker_rewritten_to_technical_appendix_heading():
    result = compose_screen_sot(FULL_G2_FIXTURE)
    assert "## Technical Appendix" in result.text
    assert DEV_APPENDIX_MARKER not in result.text
    assert "PO/BA/QA/Designer readers can stop at § 10." in result.text


def test_s20_component_variants_kept_when_present():
    result = compose_screen_sot(FULL_G2_FIXTURE)
    assert "## Component Variants" in result.text
    assert "DISC-001" in result.text


def test_s21_child_routes_kept_when_present():
    result = compose_screen_sot(FULL_G2_FIXTURE)
    assert "## Child Routes" in result.text
    assert "SCR999a" in result.text


def test_component_variants_and_child_routes_omitted_when_absent_from_input():
    # Reaches the `if dev_h2.get(name, "").strip():` False branch for both optional
    # appendix sections -- neither is ever emitted just to carry a placeholder.
    result = compose_screen_sot(SCR020)
    assert "## Component Variants" not in result.text
    assert "## Child Routes" not in result.text


def test_s22_security_surface_kept_unchanged():
    result = compose_screen_sot(FULL_G2_FIXTURE)
    assert "`require_login`" in result.text


def test_s23_source_references_kept_unchanged():
    result = compose_screen_sot(FULL_G2_FIXTURE)
    assert "Page/View: `app/views/sample.html:1`" in result.text


def test_s24_source_walkthrough_stays_literal_unnumbered_h2():
    result = compose_screen_sot(FULL_G2_FIXTURE)
    assert "\n## Source Walkthrough\n" in result.text
    assert "## 11. Source Walkthrough" not in result.text
    assert "### Source Walkthrough" not in result.text


def test_s25_unknown_h2_preserved_and_placed_before_source_walkthrough():
    result = compose_screen_sot(FULL_G2_FIXTURE)
    assert "## Weird Future Section" in result.text
    assert "Some content this composer has never heard of before." in result.text
    idx_unknown = result.text.index("## Weird Future Section")
    idx_walkthrough = result.text.index("## Source Walkthrough")
    assert idx_unknown < idx_walkthrough


# --------------------------------------------------------------------------- #
# Defect 3 (p14-migration-report.md § Risks item 3): Mode-C-declined (raw v26)
# input reaching `compose_screen_sot` directly -- e.g. an untracked/hand-edited
# screen spec that `audience-split` refused to touch, composed anyway because
# `compose_screen_sot` has no dependency on Mode C having run. Real fixture:
# `evidence/corpus-g1/SCR001_Login.spec.md`, the actual v26 shape with its own
# unnumbered `## Screen Layout` H2 (intro + nested Layout Sketch/Layout Regions),
# never passed through `_audience_split_mode_c_lib.compose_mode_c`.
# --------------------------------------------------------------------------- #
_G1_LOGIN_TEXT = (
    _SOT_CORPUS
    / "corpus-g1" / "SCR001_Login.spec.md"
).read_text(encoding="utf-8")


def test_mode_c_declined_input_fills_screen_layout_from_raw_h2_not_na():
    """Pre-fix: § 2's Layout Sketch/Regions landed as empty `N/A` placeholders
    because `extract_v27_pieces` only ever looked for Mode C's post-reorder shape
    (bare `### Layout Sketch` under `## Purpose`, bare `### Layout Regions` leading
    the dev appendix) and never recognized the pre-Mode-C `## Screen Layout` H2
    wrapper still present here. Reaches that exact branch: `_G1_LOGIN_TEXT` has no
    `DEV_APPENDIX_MARKER` at all, so this is unambiguously the declined-Mode-C shape."""
    assert DEV_APPENDIX_MARKER not in _G1_LOGIN_TEXT  # confirms the branch reached
    result = compose_screen_sot(_G1_LOGIN_TEXT)
    layout = _section(result.text, "## 2. Screen Layout", "## 3.")
    sketch = _section(layout, "### Layout Sketch", "### Layout Regions")
    assert "The screen has a header and a centered form (login.vue:1)." in sketch
    assert "box" in sketch
    assert sketch.strip() != "N/A"
    regions = layout.split("### Layout Regions", 1)[1]
    assert "R1" in regions and "Header" in regions and "fixed-top" in regions
    assert regions.strip() != "N/A"


def test_mode_c_declined_input_screen_layout_not_duplicated_in_appendix():
    """The raw `## Screen Layout` H2 must not ALSO survive as an S-25
    unknown-heading duplicate once its content has been routed into § 2 -- the
    exact duplication `evidence/defect3-mode-c-decline-repro/README.md` observed."""
    result = compose_screen_sot(_G1_LOGIN_TEXT)
    assert "\n## Screen Layout\n" not in result.text


# --------------------------------------------------------------------------- #
# C1 (reviewer-260819-0858-inspection.md): the SCREEN_LAYOUT_H2 fallback above
# fixed ONLY `## Screen Layout` -- the other five KNOWN_DEV_H2 names (Accessibility,
# Component Variants, Child Routes, Security Surface, Source References) hit the
# identical Mode-C-declined trigger and were never fixed. `evidence/corpus-g1/
# SCR001_Login.spec.md` (used above) cannot expose this: its Accessibility/
# Component Variants/Security Surface bodies are all literally "N/A", so even a
# test asserting on those sections would pass trivially whether promotion happened
# or not -- the fixture-blindness the inspection flagged. `_G1_DECLINED_FULL_FIXTURE`
# below is a fresh, synthetic-but-labeled fixture in the same real Mode-C-declined
# shape (no `DEV_APPENDIX_MARKER` anywhere) carrying REAL, distinctive, non-"N/A"
# content in every one of the five appendix-destined sections, plus one genuinely
# novel heading (`## Weird Future Section`) this composer has never heard of, to
# get an order-based signal (mirrors `test_s25_unknown_h2_preserved_and_placed_
# before_source_walkthrough` above) that distinguishes "correctly routed to its
# named appendix slot" from "swept into the S-25 unknown catch-all with everything
# else that landed in ba_h2".
# --------------------------------------------------------------------------- #
_G1_DECLINED_FULL_FIXTURE = """---
authored_by: rebuild-spec
---
# SCR998_FullDeclined — Screen Spec

**Screen**: SCR998: Full Declined
**Type**: atomic
**Route**: /declined
**Generated**: 2026-08-19

## Purpose

Confirms a dialog action. Exercises every appendix-destined H2 with real,
distinctive content while never having passed through Mode C.

## Screen Layout

The screen shows a single confirmation dialog (confirm.vue:1).

### Layout Sketch

```
dialog
```

### Layout Regions

| Region ID | Name | Position | Scrollable | Key Components | Responsive Behavior |
|-----------|------|----------|------------|----------------|---------------------|
| R1 | Dialog | center | no | Dialog | always |

## User Flow

### Happy Path

1. User confirms the dialog.

## Data Inventory

N/A — screen displays no dynamic data

## UI States

N/A — no async ops

## Validation & Error Feedback

N/A

## Interaction Patterns

N/A

## Accessibility

| Aspect | Status | Notes |
|--------|--------|-------|
| ARIA roles/labels | present | dialog has role="alertdialog" and aria-label |
| Focus management | present | focus trapped inside dialog while open |

## Conditional Rendering

N/A

## Component Variants

| Variant | Trigger | Notes |
|---------|---------|-------|
| destructive | props.kind === "destructive" | red Confirm button |

## Child Routes

| Route | Purpose |
|-------|---------|
| /declined/history | View past confirmations |

## Security Surface

| Aspect | Status | Notes |
|--------|--------|-------|
| CSRF token | present | dialog submit carries X-CSRF-Token |
| Rate limiting | present | 5 confirms / minute per session |

## Weird Future Section

Some content this composer has never heard of before.

## Source References

1. Page/View: `confirm.vue:1`

## Source Walkthrough

1. **File:** `confirm.vue:1` — start here
"""


def test_mode_c_declined_full_fixture_has_no_marker_and_all_na_sections_are_absent():
    # Confirms the branch reached AND confirms this fixture is not fixture-blind --
    # unlike SCR001_Login, none of the five appendix sections under test are "N/A".
    assert DEV_APPENDIX_MARKER not in _G1_DECLINED_FULL_FIXTURE
    for marker in (
        '| ARIA roles/labels | present', "destructive", "/declined/history",
        "X-CSRF-Token", "Page/View: `confirm.vue:1`",
    ):
        assert marker in _G1_DECLINED_FULL_FIXTURE


def test_c1_mode_c_declined_accessibility_promoted_to_reader_body_not_left_na():
    """S-17: real Accessibility content must reach `## 9. Accessibility` in the
    reader-facing body -- pre-fix, `p.dev_h2.get("## Accessibility", "")` always
    returns "" for Mode-C-declined input (dev_h2 stays empty, nothing ever pops
    "## Accessibility" out of ba_h2 the way SCREEN_LAYOUT_H2 already does), so
    `build_accessibility("")` renders the reader body's "N/A" default while the
    real content is buried, unlabeled, past the point PO/BA/QA/Designer readers are
    told they can stop reading."""
    result = compose_screen_sot(_G1_DECLINED_FULL_FIXTURE)
    section9 = _section(result.text, "## 9. Accessibility", "## 10.")
    assert "alertdialog" in section9
    assert "Focus management" in section9
    assert section9.strip().upper() != "N/A"
    # And it must not ALSO survive as a bare, unlabeled S-25 duplicate once promoted.
    assert "\n## Accessibility\n" not in result.text


def test_c1_mode_c_declined_appendix_sections_routed_to_named_slot_not_unknown_dump():
    """Component Variants/Child Routes/Security Surface/Source References must land
    under their own named appendix heading, in `SOT_APPENDIX_ORDER`'s position --
    not swept into the S-25 unknown-heading catch-all alongside `## Weird Future
    Section`. Pre-fix, `dev_h2` stays `{}` for Mode-C-declined input, so NONE of
    these are recognized by `p.dev_h2.get(...)`/`name in p.dev_h2` in
    `compose_screen_sot`; they fall through to `extract_unknown_h2(p.ba_h2, ...)`
    right alongside the genuinely-unknown heading, ahead of where a real S-25 item
    belongs (immediately before `## Source Walkthrough`, per the HARD CONSTRAINT) --
    landing BEFORE `## Source References`/`## Security Surface` instead of after."""
    result = compose_screen_sot(_G1_DECLINED_FULL_FIXTURE)
    appendix = result.text.split("## Technical Appendix", 1)[1]
    variants = _section(appendix, "## Component Variants", "## Child Routes")
    assert "destructive" in variants
    routes = _section(appendix, "## Child Routes", "## Security Surface")
    assert "/declined/history" in routes
    security = _section(appendix, "## Security Surface", "## Source References")
    assert "X-CSRF-Token" in security
    refs = appendix.split("## Source References", 1)[1]
    assert "confirm.vue:1" in refs
    # The HARD CONSTRAINT (target-shape-spec.md § 1.3): a genuinely-unknown heading
    # sits immediately before `## Source Walkthrough` -- AFTER every named appendix
    # section, never interleaved before them.
    idx_security = appendix.index("## Security Surface")
    idx_refs = appendix.index("## Source References")
    idx_unknown = appendix.index("## Weird Future Section")
    idx_walkthrough = appendix.index("## Source Walkthrough")
    assert idx_security < idx_refs < idx_unknown < idx_walkthrough


# --------------------------------------------------------------------------- #
# Structural / HARD CONSTRAINT requirements.
# --------------------------------------------------------------------------- #
def test_output_never_contains_the_mode_c_reentry_substring():
    # Pins target-shape-spec.md § 1.3's safety property: "## 2. Screen Layout" does
    # NOT contain "## Screen Layout" as a substring, which is what keeps a SOT-shaped
    # spec invisible to Mode C's re-entry predicate and prevents an infinite loop.
    for old in (SCR020, SCR012, FULL_G2_FIXTURE, MINIMAL_NA_FIXTURE):
        result = compose_screen_sot(old)
        assert "## Screen Layout" not in result.text


def test_idempotent_on_real_and_synthetic_fixtures():
    for old in (SCR020, SCR012, FULL_G2_FIXTURE, MINIMAL_NA_FIXTURE):
        once = compose_screen_sot(old)
        twice = compose_screen_sot(once.text)
        assert twice.text == once.text


def test_idempotency_short_circuit_reports_zero_moved_and_scaffolded_on_second_pass():
    # Reaches the `_SOT_SENTINEL in old_text` branch directly -- the second pass does
    # no work at all, it just recognizes the shape and returns.
    once = compose_screen_sot(SCR020)
    twice = compose_screen_sot(once.text)
    assert twice.moved == 0
    assert twice.scaffolded == 0


def test_anti_drift_template_h2_sequence_matches_sot_order_constants():
    # The mechanism that keeps P03's template and this module's order constants from
    # diverging (phase file, Implementation Steps #7) -- non-negotiable per the phase.
    template_text = TEMPLATE_PATH.read_text(encoding="utf-8")
    h2_lines = [line.strip() for line in template_text.splitlines() if re.match(r"^## ", line.strip())]
    expected = SOT_BA_ORDER + ["## Technical Appendix"] + SOT_APPENDIX_ORDER
    assert h2_lines == expected


def test_real_g2_fixtures_compose_end_to_end_without_crashing_and_need_llm_fill():
    for old in (SCR020, SCR012):
        result = compose_screen_sot(old)
        assert result.needs_llm_fill is True
        assert result.moved > 0
        assert result.scaffolded > 0


def test_minimal_na_fixture_composes_without_crashing_and_preserves_na_markers():
    result = compose_screen_sot(MINIMAL_NA_FIXTURE)
    assert "## Screen Layout" not in result.text
    assert result.needs_llm_fill is True
    elements = _section(result.text, "## 3. UI Elements", "## 4.")
    assert "N/A — screen displays no dynamic data and has no interactive elements" in elements
    conditional = _section(result.text, "## 7. Conditional UI", "## 8.")
    assert "`N/A — no conditional rendering detected.`" in conditional  # original text preserved verbatim


def test_element_ids_stable_when_a_new_row_is_appended_at_the_end():
    # Risk Assessment mitigation, direct test: appending a new source row must not
    # renumber IDs already allocated to earlier rows.
    before = compose_screen_sot(FULL_G2_FIXTURE)
    mutated = FULL_G2_FIXTURE.replace(
        "| Account balance | computed | currency | dash | MODEL001.balance |",
        "| Account balance | computed | currency | dash | MODEL001.balance |\n"
        "| Loyalty points | computed | number | dash | MODEL001.points |",
    )
    after = compose_screen_sot(mutated)
    assert "| E01 | Account balance |" in before.text
    assert "| E01 | Account balance |" in after.text  # unchanged despite the new row
    assert "| Loyalty points |" in after.text


def test_fenced_table_lookalike_in_data_inventory_is_not_mistaken_for_the_real_table():
    # Reaches build_elements' fence-aware split_around_first_table path end to end --
    # a fenced ASCII table before the real Data Inventory table must not corrupt it.
    fixture = FULL_G2_FIXTURE.replace(
        "## Data Inventory\n\n| Display Label | Source | Format | Empty Behavior | Cross-ref |",
        "## Data Inventory\n\n```\n| fenced | pseudo | table |\n|-|-|-|\n| x | y | z |\n```\n\n"
        "| Display Label | Source | Format | Empty Behavior | Cross-ref |",
    )
    result = compose_screen_sot(fixture)
    elements = _section(result.text, "## 3. UI Elements", "## 4.")
    assert "| E01 | Account balance |" in elements  # the real row, correctly reshaped
    assert "```" in elements  # the fenced lookalike survives, untouched, as a trailing note
    assert "| fenced | pseudo | table |" in elements


# --------------------------------------------------------------------------- #
# `resolve_sot_layout_rule_ids` -- the G3 equivalent of Mode C's
# `resolve_layout_rule_ids`, evaluating BOTH H3s inside the single `## 2.` section.
# --------------------------------------------------------------------------- #
def test_resolve_sot_layout_rule_ids_clean_on_composed_output():
    for old in (SCR020, SCR012, FULL_G2_FIXTURE):
        result = compose_screen_sot(old)
        assert resolve_sot_layout_rule_ids(result.text) == []


def test_resolve_sot_layout_rule_ids_fires_sketch_missing_when_h3_renamed():
    # Reaches the `sketch_body is None` branch (heading text no longer matches).
    result = compose_screen_sot(SCR020)
    mutated = result.text.replace("### Layout Sketch", "### Renamed Sketch", 1)
    assert resolve_sot_layout_rule_ids(mutated) == ["screen.layout_sketch_missing"]


def test_resolve_sot_layout_rule_ids_fires_sketch_missing_when_body_bare_na():
    # Reaches the `sketch_body.strip().upper().startswith("N/A")` branch.
    result = compose_screen_sot(SCR020)
    idx = result.text.index("### Layout Sketch")
    idx_next = result.text.index("### Layout Regions")
    mutated = result.text[:idx] + "### Layout Sketch\n\nN/A\n\n" + result.text[idx_next:]
    assert resolve_sot_layout_rule_ids(mutated) == ["screen.layout_sketch_missing"]


def test_resolve_sot_layout_rule_ids_fires_regions_missing_when_h3_renamed():
    # Reaches the `regions_body is None` branch.
    result = compose_screen_sot(SCR020)
    mutated = result.text.replace("### Layout Regions", "### Renamed Regions", 1)
    assert resolve_sot_layout_rule_ids(mutated) == ["screen.layout_regions_missing"]


def test_resolve_sot_layout_rule_ids_fires_regions_missing_when_section2_absent():
    # Reaches the `h2.get("## 2. Screen Layout", "")` empty-default branch: the
    # section itself is gone, so BOTH H3s resolve to None inside an empty string.
    result = compose_screen_sot(SCR020)
    mutated = result.text.replace("## 2. Screen Layout", "## 2. Renamed Layout Section", 1)
    assert resolve_sot_layout_rule_ids(mutated) == [
        "screen.layout_sketch_missing", "screen.layout_regions_missing",
    ]


# --------------------------------------------------------------------------- #
# The mechanical "nothing is lost" guard: every non-whitespace content line of the
# input must be findable in the output, or fall into a small, explicitly documented
# set of sanctioned reshapes (heading renumbering, table-structure regeneration,
# S-06/S-15's documented column renames, S-19's marker rewrite).
# --------------------------------------------------------------------------- #
_SEP_ROW_RE = re.compile(r"^\s*\|[\s:|-]+\|\s*$")
_SANCTIONED_LINES = {
    "---",
    "*Developer appendix below — implementation detail (layout regions, component "
    "wiring, security guards, accessibility audit, source citations, code-reading "
    "order). BA/QA readers can stop here.*",
}
# S-06: "Display Label" -> "Element". S-07: the retired `### A) Client-side` table's
# "Field"/"Constraints"/"Async Check"/"Error Message" columns are redistributed across
# `## 3.`'s Element/`## 6.`'s Rule+Feedback/`## Implementation Mapping` -- their VALUES
# survive, their column NAMES don't need to. S-15: "Renders" -> "Visible when". Column
# NAMES changing is the entire point of a MERGE (target-shape-spec.md § 1.4), not loss.
_SANCTIONED_HEADER_RENAMES = {
    "Display Label", "Renders", "Field", "Constraints", "Async Check", "Error Message",
}


def _assert_round_trip_preserved(old_text: str, new_text: str) -> None:
    lost: list[str] = []
    for line in old_text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or _SEP_ROW_RE.match(s) or s in _SANCTIONED_LINES:
            continue
        if s in new_text:
            continue
        if "|" in s:
            cells = [c.strip() for c in s.strip("|").split("|") if c.strip()]
            missing = [c for c in cells if c not in new_text and c not in _SANCTIONED_HEADER_RENAMES]
            lost.extend(f"{s!r} cell {c!r}" for c in missing)
            continue
        lost.append(s)
    assert not lost, f"content lost from input, not found (or sanctioned) in output: {lost}"


def test_round_trip_no_content_lost_scr020():
    result = compose_screen_sot(SCR020)
    _assert_round_trip_preserved(SCR020, result.text)


def test_round_trip_no_content_lost_scr012():
    result = compose_screen_sot(SCR012)
    _assert_round_trip_preserved(SCR012, result.text)


def test_round_trip_no_content_lost_full_synthetic_fixture():
    result = compose_screen_sot(FULL_G2_FIXTURE)
    _assert_round_trip_preserved(FULL_G2_FIXTURE, result.text)


def test_round_trip_no_content_lost_minimal_na_fixture():
    result = compose_screen_sot(MINIMAL_NA_FIXTURE)
    _assert_round_trip_preserved(MINIMAL_NA_FIXTURE, result.text)
