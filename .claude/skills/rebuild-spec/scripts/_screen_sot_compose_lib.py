"""`compose_screen_sot` — the SOLE source of the SOT target section order.

Reshapes a v27-shaped (G2, already through Mode C) screen spec into the 10-section
BA/PO/QA/Designer body + `## Technical Appendix` + 6 appendix H2 siblings shape
(target-shape-spec.md § 1). It is the only thing in the codebase that knows this
order -- P06's registry step and any fresh-v27-corpus entry point both call THIS
function, so the two paths cannot drift (phase-05's Key Insight).

Mode C (`_audience_split_mode_c_lib.compose_mode_c`, G1->G2) is untouched and stays a
separate, earlier step; this module only reads its output and its `DEV_APPENDIX_MARKER`
constant (via `_screen_sot_extract_lib`) -- it never modifies that module.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _audience_split_md_sections_lib import extract_h3_body, split_sections  # noqa: E402
from _screen_sot_actions_lib import build_conditional_ui, build_navigation, build_user_actions  # noqa: E402
from _screen_sot_appendix_lib import (  # noqa: E402
    assemble_document, build_implementation_mapping, extract_unknown_h2,
)
from _screen_sot_elements_lib import build_elements, build_validation_section  # noqa: E402
from _screen_sot_extract_lib import (  # noqa: E402
    KNOWN_BA_H2, KNOWN_DEV_H2, LAYOUT_REGIONS_H3, LAYOUT_SKETCH_H3, extract_v27_pieces,
)
from _screen_sot_sections_lib import (  # noqa: E402
    build_accessibility, build_overview, build_responsive_behavior, build_screen_layout,
)

SOT_BA_ORDER = [
    "## 1. Overview", "## 2. Screen Layout", "## 3. UI Elements", "## 4. User Actions",
    "## 5. UI States", "## 6. Validation & Feedback", "## 7. Conditional UI",
    "## 8. Navigation", "## 9. Accessibility", "## 10. Responsive Behavior",
]
SOT_APPENDIX_ORDER = [
    "## Implementation Mapping", "## Component Variants", "## Child Routes",
    "## Security Surface", "## Source References", "## Source Walkthrough",
]

# Scaffold sentinels this module itself writes -- their presence means a researcher
# pass is still owed (S-02 / S-13 / S-15's rewrite half / S-16), per the phase's Key
# Insight: "do not 'complete' them by guessing."
_SCAFFOLD_MARKERS = (
    "{plain role names", "{TBD}", "{action name}",
    "needs_llm_fill: do not invent a destination",
)

# Sentinel unique to SOT output -- this heading string never appears in v27/G2 input
# (it is new in this phase), so its presence is a safe idempotency signal.
_SOT_SENTINEL = "## 3. UI Elements"


@dataclass(frozen=True)
class ComposeResult:
    text: str
    needs_llm_fill: bool
    moved: int
    scaffolded: int


def _has_scaffold(text: str) -> bool:
    return any(marker in text for marker in _SCAFFOLD_MARKERS)


def compose_screen_sot(old_text: str) -> ComposeResult:
    """Reshape a v27-shaped screen spec into the SOT shape.

    Idempotent: text already carrying `## 3. UI Elements` is returned unchanged --
    re-deriving the SOT shape's own sources (`## Data Inventory`, `## Validation &
    Error Feedback`, ...) FROM already-SOT text is not a defined transform, so the
    safe and correct move is to not attempt it, not to guess at a re-parse.
    """
    if _SOT_SENTINEL in old_text:
        return ComposeResult(old_text, _has_scaffold(old_text), 0, 0)

    p = extract_v27_pieces(old_text)
    moved = p.moved_structural
    scaffolded = 0

    elements = build_elements(p.data_inventory, p.client_side, p.branches)
    moved += elements.row_count  # S-06 + S-07 [M]

    conditional = build_conditional_ui(p.conditional_rendering)
    moved += conditional.row_count  # S-15 [M]

    layout_text, responsive_rows = build_screen_layout(p.sketch_body, p.regions_body)
    overview_text = build_overview(p.purpose_pre)
    scaffolded += 1  # Overview Actors/Entry/Exit (S-02)
    user_actions_text = build_user_actions(p.happy_path, p.branches, p.interaction_notes)
    scaffolded += 1  # Available Actions (S-13)
    navigation_text = build_navigation()
    scaffolded += 2  # Entry Points + Exits (S-16)
    scaffolded += conditional.row_count  # each Element(s) `{TBD}` (S-15 [L] half)

    validation_text = build_validation_section(elements, p.server_side)
    responsive_text = build_responsive_behavior(responsive_rows)
    accessibility_body = p.dev_h2.get("## Accessibility", "")
    accessibility_text = build_accessibility(accessibility_body)
    moved += bool(accessibility_body.strip())  # S-17

    implementation_mapping_text = build_implementation_mapping(
        elements.async_checks, conditional.raw_expressions, p.server_side,
    )
    if elements.async_checks or conditional.raw_expressions or p.server_side.strip():
        moved += 1  # S-07 async / S-15 expressions / S-08 [M]

    ba_sections = {
        "## 1. Overview": overview_text,
        "## 2. Screen Layout": layout_text,
        "## 3. UI Elements": elements.table_text,
        "## 4. User Actions": user_actions_text,
        "## 5. UI States": p.ui_states.strip() or "N/A — no async ops",
        "## 6. Validation & Feedback": validation_text,
        "## 7. Conditional UI": conditional.table_text,
        "## 8. Navigation": navigation_text,
        "## 9. Accessibility": accessibility_text,
        "## 10. Responsive Behavior": responsive_text,
    }

    appendix_sections: dict[str, str] = {"## Implementation Mapping": implementation_mapping_text}
    for name in ("## Component Variants", "## Child Routes"):
        if p.dev_h2.get(name, "").strip():
            appendix_sections[name] = p.dev_h2[name]
            moved += 1  # S-20 / S-21
    for name in ("## Security Surface", "## Source References", "## Source Walkthrough"):
        if name in p.dev_h2:
            appendix_sections[name] = p.dev_h2[name]
            moved += 1  # S-22 / S-23 / S-24

    unknown = extract_unknown_h2(p.ba_h2, KNOWN_BA_H2) + extract_unknown_h2(p.dev_h2, KNOWN_DEV_H2)
    moved += len(unknown)  # S-25

    text = assemble_document(
        p.preamble, SOT_BA_ORDER, ba_sections, SOT_APPENDIX_ORDER, appendix_sections, unknown,
    )
    return ComposeResult(text, True, moved, scaffolded)


def resolve_sot_layout_rule_ids(text: str) -> list[str]:
    """The G3 (SOT-shaped) equivalent of `_audience_split_mode_c_lib.
    resolve_layout_rule_ids`. **NOT interchangeable with it**:
    `resolve_layout_rule_ids` evaluates a G2 (Mode-C-reordered) document, where Layout
    Sketch lives in the BA half and Layout Regions in the dev-appendix half of a
    `DEV_APPENDIX_MARKER` string split. This function evaluates a G3 (SOT) document,
    where BOTH H3s live together inside the single `## 2. Screen Layout` section --
    there is no marker to split on any more. Returns the rule_ids that FIRE (empty =
    both resolved/clean)."""
    _, h2 = split_sections(text, 2)
    layout_body = h2.get("## 2. Screen Layout", "")
    fired: list[str] = []
    sketch_body = extract_h3_body(layout_body, LAYOUT_SKETCH_H3)
    if sketch_body is None or sketch_body.strip().upper().startswith("N/A"):
        fired.append("screen.layout_sketch_missing")
    regions_body = extract_h3_body(layout_body, LAYOUT_REGIONS_H3)
    if regions_body is None or regions_body.strip().upper().startswith("N/A"):
        fired.append("screen.layout_regions_missing")
    return fired
