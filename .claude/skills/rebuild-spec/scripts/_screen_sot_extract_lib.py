"""Unpack a v27-shaped (G2) screen spec into its raw named pieces, ready for the
per-section builders in `_screen_sot_sections_lib` / `_screen_sot_actions_lib` /
`_screen_sot_elements_lib`. Split out of `_screen_sot_compose_lib.py` to hold the
200-line guidance -- this is purely the BA/dev marker split + H2/H3 unpacking, no
target-shape knowledge lives here.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _audience_split_md_sections_lib import extract_h3_body, split_sections  # noqa: E402
from _audience_split_mode_c_lib import DEV_APPENDIX_MARKER, SCREEN_LAYOUT_H2  # noqa: E402

LAYOUT_SKETCH_H3 = "### Layout Sketch"
LAYOUT_REGIONS_H3 = "### Layout Regions"
_CLIENT_SIDE_H3 = "### A) Client-side"
_SERVER_SIDE_H3 = "### B) Server-side"
_HAPPY_PATH_H3 = "### Happy Path"
_BRANCHES_H3 = "### Branches"

KNOWN_BA_H2 = {
    "## Purpose", "## User Flow", "## Data Inventory", "## UI States",
    "## Validation & Error Feedback", "## Interaction Patterns", "## Conditional Rendering",
}
KNOWN_DEV_H2 = {
    "## Component Variants", "## Child Routes", "## Security Surface",
    "## Accessibility", "## Source References", "## Source Walkthrough",
}


@dataclass
class ExtractedPieces:
    preamble: str
    purpose_pre: str
    sketch_body: str
    regions_body: str
    happy_path: str
    branches: str
    interaction_notes: str
    client_side: str
    server_side: str
    data_inventory: str
    ui_states: str
    conditional_rendering: str
    dev_h2: dict[str, str]
    ba_h2: dict[str, str]
    # KEEP/MOVE hits found purely by "was there content here at all" -- S-01, S-03,
    # S-04, S-09, S-10, S-11, S-12, S-14. The composer adds the rest (elements/
    # conditional/appendix counts) on top of this.
    moved_structural: int = field(default=0)


def extract_v27_pieces(old_text: str) -> ExtractedPieces:
    if DEV_APPENDIX_MARKER in old_text:
        idx = old_text.index(DEV_APPENDIX_MARKER)
        ba_raw, dev_raw = old_text[:idx], old_text[idx + len(DEV_APPENDIX_MARKER):]
    else:
        ba_raw, dev_raw = old_text, ""

    preamble, ba_h2 = split_sections(ba_raw, 2)
    dev_preamble, dev_h2 = split_sections(dev_raw, 2)
    moved = 0

    # Fallback (reviewer-260819-0858-inspection.md C1, generalizing the
    # SCREEN_LAYOUT_H2 fallback below past just `## Screen Layout`): when Mode C
    # never ran, `dev_raw` is "" and `dev_h2` never gets populated by the marker
    # split above -- every appendix-destined H2 in KNOWN_DEV_H2 is still sitting in
    # `ba_h2` under its own flat heading (the pre-Mode-C shape never separates them
    # out at all). Whole-hunk transfer any of them found there into `dev_h2` -- no
    # reshaping needed, unlike `## Screen Layout` below, which wraps two logically
    # separate destinations and must be split by H3 instead. No-op when Mode C DID
    # run: a real marker split never leaves any KNOWN_DEV_H2 name behind in `ba_h2`
    # (Mode C only ever places them in the dev half), so this loop finds nothing to
    # move. The `name not in dev_h2` guard is belt-and-suspenders against a
    # malformed document that repeats a heading on both sides of the marker --
    # never overwrite content Mode C's own split already resolved.
    for _name in KNOWN_DEV_H2:
        if _name in ba_h2 and _name not in dev_h2:
            dev_h2[_name] = ba_h2.pop(_name)

    # Fallback (p14-migration-report.md § Risks item 3): Mode C normally unwraps the
    # OLD `## Screen Layout` H2 into a bare `### Layout Sketch` H3 trailing `##
    # Purpose` (BA half) plus a bare `### Layout Regions` H3 leading the dev
    # appendix. When Mode C never ran (e.g. an untracked/hand-edited screen
    # `audience-split` declined, that `screen-sot` composes anyway), `## Screen
    # Layout` survives intact as its own H2 instead of either bare H3 -- recognize
    # that shape directly so its content reaches the mechanical S-03/S-04 merge
    # rather than falling through to the S-25 unknown-heading catch-all (which used
    # to leave § 2 as empty `N/A` while duplicating the real content at the
    # appendix tail). Popped out of `ba_h2` up front so it can never also survive
    # as an S-25 "unknown H2" once its content has been routed here.
    raw_screen_layout = ba_h2.pop(SCREEN_LAYOUT_H2, None)
    if raw_screen_layout is not None:
        layout_pre, layout_h3 = split_sections(raw_screen_layout, 3)
        fallback_sketch = "\n\n".join(
            p for p in (layout_pre.strip(), layout_h3.get(LAYOUT_SKETCH_H3, "").strip()) if p
        )
        fallback_regions = layout_h3.get(LAYOUT_REGIONS_H3, "")
    else:
        fallback_sketch = fallback_regions = ""

    purpose_full = ba_h2.get("## Purpose", "")
    purpose_pre, purpose_h3 = split_sections(purpose_full, 3)
    sketch_body = purpose_h3.get(LAYOUT_SKETCH_H3, "") or fallback_sketch
    moved += bool(purpose_pre.strip())  # S-01

    regions_body = extract_h3_body(dev_preamble, LAYOUT_REGIONS_H3)
    if regions_body is None:
        regions_body = dev_preamble or fallback_regions
    moved += bool(sketch_body.strip())  # S-03
    moved += bool(regions_body.strip())  # S-04

    uf_full = ba_h2.get("## User Flow", "")
    uf_pre, uf_h3 = split_sections(uf_full, 3)
    # S-12 KEEP+edit: the one deliberate content edit the preservation map names as
    # such -- any original scope blockquote is superseded by the canonical D3
    # restatement `_screen_sot_actions_lib` always emits, never silently vanished.
    moved += bool(uf_pre.strip())
    happy_path = uf_h3.get(_HAPPY_PATH_H3, "")
    branches = uf_h3.get(_BRANCHES_H3, "")
    interaction_notes = ba_h2.get("## Interaction Patterns", "")
    moved += sum(bool(b.strip()) for b in (happy_path, branches, interaction_notes))

    vef_full = ba_h2.get("## Validation & Error Feedback", "")
    _, vef_h3 = split_sections(vef_full, 3)
    client_side = vef_h3.get(_CLIENT_SIDE_H3, "")
    server_side = vef_h3.get(_SERVER_SIDE_H3, "")

    ui_states = ba_h2.get("## UI States", "")
    moved += bool(ui_states.strip())  # S-09

    return ExtractedPieces(
        preamble=preamble, purpose_pre=purpose_pre, sketch_body=sketch_body,
        regions_body=regions_body, happy_path=happy_path, branches=branches,
        interaction_notes=interaction_notes, client_side=client_side, server_side=server_side,
        data_inventory=ba_h2.get("## Data Inventory", ""), ui_states=ui_states,
        conditional_rendering=ba_h2.get("## Conditional Rendering", ""),
        dev_h2=dev_h2, ba_h2=ba_h2, moved_structural=moved,
    )
