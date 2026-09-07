"""Mode A -- compose `functional-spec.md` + a reshaped `technical-spec.md` from a v26
feature dir (phase-06 Requirement 1). Parsing lives in `_audience_split_parse_v26_lib.py`;
the 10 per-section renderers live in `_audience_split_render_func_sections_lib.py`
(split out to keep each module under the repo's 200-line guidance); this module wires
the two together plus the technical-spec.md heading-splice.

BR/DEC/SM one-liners in functional-spec.md §4 reuse the EXACT SAME plain-language
sentence that becomes the new technical-spec.md heading for that code
(`sentence_for_block`, one derivation, two call sites) -- the two files can never say
something different about the same code.

Stdlib only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _audience_split_ccl_normalize_lib import normalize_ccl, stamp_frontmatter  # noqa: E402
from _audience_split_md_sections_lib import split_sections  # noqa: E402
from _audience_split_parse_v26_lib import (  # noqa: E402
    find_old_blocks, parse_business_context, parse_edge_cases, parse_fr_items,
    parse_needs_confirmation, parse_screens, parse_user_stories,
    parse_verification_fr_map, sentence_for_block,
)
from _audience_split_render_func_sections_lib import (  # noqa: E402
    render_business_rules, render_edge_behaviours, render_edge_cases,
    render_overview, render_requirements, render_scenarios,
    render_user_stories, sanitize,
)
from _audience_split_render_screens_lib import render_open_decisions, render_screens  # noqa: E402
from _audience_split_screen_bind_lib import build_index  # noqa: E402
from _audience_split_source_refs_lib import backfill_source_references  # noqa: E402

_FCODE_H1_RE = re.compile(r"^#\s+(F\d{3}_\w+)")
_RULE_LINE_RE = re.compile(r"^\*\*Rule:\*\*")
_OUTCOME_LINE_RE = re.compile(r"^\*\*user_visible_outcome:\*\*")


def _extract_fcode_heading(text: str) -> str:
    for line in text.splitlines()[:10]:
        m = _FCODE_H1_RE.match(line.strip())
        if m:
            return f"# {m.group(1)}"
    return "# F000_Unknown"


def render_functional_spec(fcode_heading: str, func_type: str, sections: dict[str, str]) -> str:
    preamble = (
        "---\nauthored_by: rebuild-spec\n---\n"
        f"{fcode_heading}\n\n"
        "**Priority**: P2\n"
        f"**Type**: {func_type}\n"
        "**Generated**: migrated\n\n"
        "**See also:** [`technical-spec.md`](./technical-spec.md) — endpoints, Source "
        "citations, pseudocode, key entities, and DB writes for a Dev/QA/SA audience."
    )
    numbered = [
        ("1. Overview", sections["overview"]), ("2. Open Decisions", sections["open_decisions"]),
        ("3. Requirements", sections["requirements"]), ("4. Business Rules", sections["business_rules"]),
        ("5. Screens", sections["screens"]), ("6. User Stories", sections["user_stories"]),
        ("7. Scenarios", sections["scenarios"]), ("8. Edge Cases", sections["edge_cases"]),
        ("9. Edge Behaviours to Verify", sections["edge_behaviours"]),
        ("10. Configuration", sections["configuration"]),
    ]
    parts = [preamble] + [f"## {title}\n\n{body}" for title, body in numbered]
    return sanitize("\n\n".join(parts).rstrip("\n") + "\n")


def render_technical_spec(old_text: str, blocks: list[dict]) -> str:
    """Splice every old-form block heading to the new trailing-tag form and strip the
    ONE field that moved to functional-spec.md (BR's Rule:, DEC's user_visible_outcome:).
    Every other line -- including SM/ALG/INT bodies, which are UNCHANGED except their
    own heading -- passes through byte-for-byte, save for two disclosed exceptions:
    `normalize_ccl` backfilling a blank CCL H3 with `None.`, and `stamp_frontmatter`
    prepending provenance when absent. Splice itself is processed bottom-up so
    earlier splices never shift a later block's line indices."""
    lines = old_text.splitlines()
    out = list(lines)
    for blk in sorted(blocks, key=lambda b: b["start"], reverse=True):
        heading_level = "####" if blk["prefix"] == "DEC" else "###"
        new_heading = f"{heading_level} {sentence_for_block(blk)} ({blk['code']})"
        body_lines = list(blk["body_lines"])
        if blk["prefix"] == "BR":
            body_lines = [ln for ln in body_lines if not _RULE_LINE_RE.match(ln)]
        elif blk["prefix"] == "DEC":
            body_lines = [ln for ln in body_lines if not _OUTCOME_LINE_RE.match(ln)]
        out[blk["start"]:blk["end"]] = [new_heading] + body_lines
    out = normalize_ccl(out)
    text = "\n".join(out).rstrip("\n") + "\n"
    text = backfill_source_references(text)
    return stamp_frontmatter(text)


def compose_mode_a(feature_dir: Path) -> dict[str, str]:
    """Real Mode A composition -- see Requirement 1. Reads the 4 v26 files, composes
    functional-spec.md (10 sections) + a reshaped technical-spec.md.

    `compose_mode_a` keeps its single-positional-argument shape (three existing
    tests monkeypatch it as `lambda fd: composed`, and `migrate_feature`'s
    `compose_fn` default resolves the bare name from module globals at call time --
    see migrate_feature_audience_split.py's module docstring). So the SCR###
    resolution ladder's index (phase-05, B4c) is derived HERE from `feature_dir`
    itself: `docs_root = feature_dir.parent.parent` (features/F###_Slug -> docs
    root), mirroring the same derivation `_audience_split_migrate_lib.
    validate_feature_dir` already uses for `plan_dir`. Best-effort -- a missing or
    unparseable `generated/screen-list.md` yields an empty index, and every row
    then falls to L0-or-L3 (never a crash)."""
    bc_text = (feature_dir / "business-context.md").read_text(encoding="utf-8", errors="replace")
    screens_text = (feature_dir / "screens.md").read_text(encoding="utf-8", errors="replace")
    edge_text = (feature_dir / "edge-cases.md").read_text(encoding="utf-8", errors="replace")
    tech_text = (feature_dir / "technical-spec.md").read_text(encoding="utf-8", errors="replace")

    bc = parse_business_context(bc_text)
    screens = parse_screens(screens_text)
    edge_rows = parse_edge_cases(edge_text)
    blocks = find_old_blocks(tech_text)
    fr_items = parse_fr_items(tech_text)
    fr_verification = parse_verification_fr_map(tech_text)
    stories = parse_user_stories(tech_text)
    markers = parse_needs_confirmation(bc_text, screens_text, edge_text, tech_text)

    _, tech_h2 = split_sections(tech_text, 2)
    tech_overview = tech_h2.get("## Overview", "")
    func_type = "background" if screens["background"] else "ui"

    screen_index = build_index(feature_dir.parent.parent)
    screens_body, unbound_screens = render_screens(screens, screen_index)

    sections = {
        "overview": render_overview(bc, tech_overview),
        "open_decisions": render_open_decisions(markers, unbound_screens),
        "requirements": render_requirements(fr_items),
        "business_rules": render_business_rules(blocks),
        "screens": screens_body,
        "user_stories": render_user_stories(stories),
        "scenarios": render_scenarios(stories),
        "edge_cases": render_edge_cases(edge_rows),
        "edge_behaviours": render_edge_behaviours(fr_verification),
        "configuration": "N/A — no user-facing configuration constants for this feature.",
    }
    functional_spec = render_functional_spec(_extract_fcode_heading(tech_text), func_type, sections)
    technical_spec = render_technical_spec(tech_text, blocks)
    return {"functional-spec.md": functional_spec, "technical-spec.md": technical_spec}
