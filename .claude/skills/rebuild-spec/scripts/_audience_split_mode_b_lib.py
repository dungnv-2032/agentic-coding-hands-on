"""Mode B -- fold `docs/system/business-rules.md` into `docs/generated/behavior-logic.md`'s
BA section (phase-06 Requirement 2 / Phase 03).

`business-rules.md`'s own contract described it as "behavior-logic.md mirrored here in
plain language" -- the exact derived view ADR-0003 abolished (Phase 03). This module
does the one-time fold for an EXISTING repo still carrying that file: parse its
`### {Rule Name}` blocks and insert them as a new H2 section in behavior-logic.md,
positioned before the first `## BL###` fragment so it lands in the BA-reading zone
regardless of whether the target document is still old-shape (Index straight into BL
fragments) or already Phase-03-shape (Index -> Dev Appendix -> BL fragments) -- existing
BL### sections are never touched, so every pre-fold BL### code survives untouched.

Stdlib only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from validate_behavior_logic import BL_H2_RE  # noqa: E402

_RULE_HEADING_RE = re.compile(r"^###\s+(.+?)\s*$")
_APPLIES_WHEN_RE = re.compile(r"^\*\*Applies when:\*\*\s*(.*)$")
_SAYS_RE = re.compile(r"^\*\*Says:\*\*\s*(.*)$")
_SOURCE_ARTIFACT_RE = re.compile(r"^\*\*Source artifact:\*\*\s*(.*)$")

FOLD_H2_HEADING = "## Business Rules (folded from business-rules.md)"
_FOLD_NOTE = (
    "<!-- v27.0.0 (audience split): business-rules.md is retired (ADR-0003/Phase 03) -- "
    "its plain-language rules are folded in here, ahead of the Dev Appendix / BL### "
    "fragments below, rather than duplicated in a standalone file. -->"
)


def parse_business_rules(text: str) -> list[dict]:
    """Parse the old `business-rules-template.md` shape: repeated `### {Rule Name}`
    blocks carrying `**Applies when:**` / `**Says:**` / `**Source artifact:**` fields,
    separated by `---`. Best-effort -- an unparseable block is skipped, never raised."""
    blocks: list[dict] = []
    current: dict | None = None
    for line in text.splitlines():
        m = _RULE_HEADING_RE.match(line)
        if m:
            if current is not None:
                blocks.append(current)
            current = {"name": m.group(1).strip(), "applies_when": "", "says": "",
                       "source_artifact": ""}
            continue
        if current is None:
            continue
        for field_re, key in ((_APPLIES_WHEN_RE, "applies_when"), (_SAYS_RE, "says"),
                              (_SOURCE_ARTIFACT_RE, "source_artifact")):
            fm = field_re.match(line)
            if fm:
                current[key] = fm.group(1).strip()
                break
    if current is not None:
        blocks.append(current)
    return [b for b in blocks if b["name"] and b["name"] != "{Rule Name}"]


def render_fold_section(rules: list[dict]) -> str:
    lines = [FOLD_H2_HEADING, "", _FOLD_NOTE, ""]
    for r in rules:
        pieces = [f"**{r['name']}**"]
        if r["applies_when"]:
            pieces.append(f"Applies when {r['applies_when']}.")
        if r["says"]:
            pieces.append(r["says"] if r["says"].endswith((".", "!", "?")) else r["says"] + ".")
        if r["source_artifact"]:
            pieces.append(f"({r['source_artifact']})")
        lines.append("- " + " ".join(pieces))
    lines.append("")
    return "\n".join(lines)


def bl_codes(text: str) -> set[str]:
    """Every `BL###` code declared as an H2 fragment heading -- used to prove the fold
    dropped none of them (Integration (B))."""
    return {m.group(1)[:5].upper() for m in
            (BL_H2_RE.match(ln) for ln in text.splitlines()) if m}


_DEV_APPENDIX_H2_RE = re.compile(r"^##\s+Dev Appendix\s*$")


def fold_business_rules(behavior_logic_text: str, rules: list[dict]) -> str:
    """Insert the rendered fold section into *behavior_logic_text*, right before the
    EARLIER of `## Dev Appendix` or the first `## BL###` fragment heading (whichever
    the document actually has -- old-shape docs have no Dev Appendix wrapper, new-shape
    docs do; inserting only before the bare BL heading would otherwise land the fold
    heading AFTER `## Dev Appendix` has already opened, breaking it into two
    disconnected halves). Falls back to end-of-document if neither is present. Every
    line before and after the insertion point is passed through byte-for-byte -- no
    existing BL### section is read into, or moved out of, its original position."""
    if not rules:
        return behavior_logic_text
    lines = behavior_logic_text.splitlines()
    insert_at = len(lines)
    for i, ln in enumerate(lines):
        if _DEV_APPENDIX_H2_RE.match(ln) or BL_H2_RE.match(ln):
            insert_at = i
            break
    section = render_fold_section(rules).splitlines()
    new_lines = lines[:insert_at] + section + [""] + lines[insert_at:]
    return "\n".join(new_lines).rstrip("\n") + "\n"
