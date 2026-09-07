"""Mode C -- screen-spec reorder (phase-06 Requirement 3 / Phase 02 Track 2).

Pure reordering: every heading's TEXT is preserved verbatim, only its POSITION moves.
`validate_reading_guide_db_impact.py` (the one Python validator that touches
screen-spec) locates `## Source Walkthrough` by heading text via `_section_body()`,
never by position -- Phase 02's own research confirmed reordering breaks zero Python
checks. No LLM pass is involved (Requirement 3: "Pure reordering... no LLM pass").

`## Screen Layout` cannot survive the reorder (Phase 02 C-AD3): the new order puts its
child `### Layout Sketch` in the BA body (right after `## Purpose`) and its other child
`### Layout Regions` in the dev appendix -- a single H2 cannot wrap two disconnected
regions of a linear document any more, so the wrapper is unwrapped: `### Layout Sketch`
absorbs the wrapper's own intro prose (the ASCII-diagram lead-in that used to sit
directly under `## Screen Layout`) and both children keep their own heading text as-is.

`## Data Inventory`'s `Field` column is dropped; `Display Label` becomes the sole
identity column (Phase 02 Requirement); the old `Field` value survives as a
`(binding: ...)` annotation on the Cross-ref cell rather than being discarded, so no
information is silently lost even though the column is.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _audience_split_data_inventory_lib import reshape_data_inventory  # noqa: E402
from _audience_split_md_sections_lib import extract_h3_body, split_sections  # noqa: E402
from _md_scan_lib import iter_lines_with_fence  # noqa: E402

SCREEN_LAYOUT_H2 = "## Screen Layout"
LAYOUT_SKETCH_H3 = "### Layout Sketch"
LAYOUT_REGIONS_H3 = "### Layout Regions"
DEV_APPENDIX_MARKER = (
    "---\n\n"
    "*Developer appendix below — implementation detail (layout regions, component "
    "wiring, security guards, accessibility audit, source citations, code-reading "
    "order). BA/QA readers can stop here.*"
)

# BA body, in the Phase 02 order (after `## Purpose` + the relocated Layout Sketch).
_BA_H2_ORDER = [
    "## User Flow", "## Data Inventory", "## UI States",
    "## Validation & Error Feedback", "## Interaction Patterns",
    "## Conditional Rendering",
]
# Dev appendix, in the Phase 02 order. `### Layout Regions` is emitted first (H3, no
# wrapping H2 any more), the rest are unchanged H2 sections.
_DEV_H2_ORDER = [
    "## Component Variants", "## Child Routes", "## Security Surface",
    "## Accessibility", "## Source References", "## Source Walkthrough",
]


_H3_BOUNDARY_RE = re.compile(r"^#{1,3}\s")


def _split_screen_layout(body: str) -> tuple[str, str, str]:
    """Split the OLD `## Screen Layout` body into (intro, sketch_body, regions_body).

    `intro` = prose before `### Layout Sketch` (its own heading line excluded from the
    returned body -- the caller re-emits it once, merged with `sketch_body`).
    `sketch_body` = content between `### Layout Sketch` and the NEXT H1-H3 heading
    (correctly stopping at `### Layout Regions` rather than swallowing it).
    `regions_body` = content between `### Layout Regions` and the next H1-H3 heading.
    Fence-aware; each is `""` if its heading is absent."""
    lines = body.splitlines()
    buckets: dict[str, list[str]] = {"intro": [], LAYOUT_SKETCH_H3: [], LAYOUT_REGIONS_H3: []}
    current = "intro"
    for _, line, in_fence in iter_lines_with_fence(body):
        if not in_fence and _H3_BOUNDARY_RE.match(line):
            stripped = line.strip()
            if stripped in (LAYOUT_SKETCH_H3, LAYOUT_REGIONS_H3):
                current = stripped
                continue
            if stripped != SCREEN_LAYOUT_H2:
                current = None  # an unrelated heading closes both known sections
        if current is not None:
            buckets[current].append(line)
    return (
        "\n".join(buckets["intro"]).strip("\n"),
        "\n".join(buckets[LAYOUT_SKETCH_H3]).strip("\n"),
        "\n".join(buckets[LAYOUT_REGIONS_H3]).strip("\n"),
    )


def resolve_layout_rule_ids(new_text: str) -> list[str]:
    """Mechanically evaluate the two Phase 02 rule_ids against a reordered spec.md.

    Returns the list of rule_ids that FIRE (empty = both resolved/clean). Mirrors
    `screen.layout_sketch_missing` / `screen.layout_regions_missing` from
    `references/verification-checklist-screen-spec.md` -- absent, or bare `N/A`, in
    the section each now lives in."""
    fired: list[str] = []
    ba_text = new_text.split(DEV_APPENDIX_MARKER)[0]
    dev_text = new_text.split(DEV_APPENDIX_MARKER)[-1] if DEV_APPENDIX_MARKER in new_text else ""

    sketch_body = extract_h3_body(ba_text, LAYOUT_SKETCH_H3)
    if sketch_body is None:
        fired.append("screen.layout_sketch_missing")
    elif sketch_body.strip().upper().startswith("N/A"):
        fired.append("screen.layout_sketch_missing")

    regions_body = extract_h3_body(dev_text, LAYOUT_REGIONS_H3)
    if regions_body is None:
        fired.append("screen.layout_regions_missing")
    elif regions_body.strip().upper().startswith("N/A"):
        fired.append("screen.layout_regions_missing")
    return fired


def compose_mode_c(old_text: str) -> str:
    """Reorder a v26-order screen-spec.md into the Phase 02 BA-first order. Every
    heading's text is preserved verbatim; `## Screen Layout` is unwrapped per C-AD3."""
    preamble, h2 = split_sections(old_text, 2)

    layout_body = h2.pop(SCREEN_LAYOUT_H2, "")
    intro, sketch_body, regions_body = _split_screen_layout(layout_body)
    merged_sketch = "\n\n".join(p for p in (intro, sketch_body) if p.strip())

    if "## Data Inventory" in h2:
        h2["## Data Inventory"] = reshape_data_inventory(h2["## Data Inventory"])

    parts: list[str] = [preamble.rstrip("\n")]
    if "## Purpose" in h2:
        parts.append("## Purpose\n\n" + h2["## Purpose"].strip("\n"))
    parts.append(LAYOUT_SKETCH_H3 + "\n\n" + merged_sketch)
    for name in _BA_H2_ORDER:
        if name in h2:
            parts.append(name + "\n\n" + h2[name].strip("\n"))

    parts.append(DEV_APPENDIX_MARKER)
    parts.append(LAYOUT_REGIONS_H3 + "\n\n" + regions_body)
    for name in _DEV_H2_ORDER:
        if name in h2:
            parts.append(name + "\n\n" + h2[name].strip("\n"))

    # Anything unrecognized (future H2 this module doesn't know about) is preserved,
    # appended at the end of the dev appendix, rather than silently dropped.
    known = {"## Purpose", *_BA_H2_ORDER, *_DEV_H2_ORDER}
    for name, body in h2.items():
        if name not in known:
            parts.append(name + "\n\n" + body.strip("\n"))

    return "\n\n".join(parts).rstrip("\n") + "\n"
