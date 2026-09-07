"""Mode A -- parse OLD-form `### BR-001_Slug` / `#### DEC-001_Slug` blocks out of a v26
technical-spec.md. Split out of `_audience_split_parse_v26_lib.py` to keep each module
under the repo's 200-line guidance. Stdlib only.

v27.0.0 (phase-10, B4d): `_OLD_BLOCK_HEADING_RE` now tolerates an optional trailing
annotation after the slug (e.g. `### INT-001_Foo (see Cross-Cutting Logic)`) -- this is
the 5th+ recurrence of the same over-anchored-trailing-boundary hazard family in this
skill (the `\\b`-on-`CODE-###_Slug` variant fails because `_` is a word char; this one
anchored `\\s*$` immediately after the slug instead). The slug itself is captured as a
plain `\\S+` run so an annotation can never be swallowed into it, whatever it says --
recognition does NOT depend on the literal English wording.

Recognizing an annotated heading is only half the fix: `find_old_blocks()` also
classifies each occurrence as a RESTATEMENT (a per-user-story backlink to a CCL block
defined elsewhere) vs a canonical definition, and synthesizes what a restatement needs to
satisfy the validator once spliced into canonical heading form -- see
`_audience_split_restatement_lib.py` for the full rationale and the structural test.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _audience_split_restatement_lib import (  # noqa: E402
    is_restatement_body, synthesize_restatement_content,
)
from _spec_parse import parse_headings_and_blocks  # noqa: E402

# Group 5 (annotation) is optional and requires its first character to be non-whitespace
# (`\S.*?`) so a heading with ONLY trailing whitespace (no real annotation) can never have
# that whitespace itself captured as a bogus annotation.
_OLD_BLOCK_HEADING_RE = re.compile(
    r"^(#{3,4})\s+(BR|SM|ALG|INT|DEC)-(\d{3})_(\S+)(?:\s+(\S.*?))?\s*$"
)
_CAMEL_SPLIT_RE = re.compile(r"(?<!^)(?=[A-Z])")


def slug_to_words(slug: str) -> str:
    """`PasswordComplexity` -> `Password Complexity`; underscores also split."""
    words: list[str] = []
    for token in slug.replace("_", " ").split(" "):
        words.extend(w for w in _CAMEL_SPLIT_RE.split(token) if w)
    return " ".join(words)


def field(block_text: str, name: str) -> str:
    m = re.search(rf"^\*\*{re.escape(name)}:\*\*\s*(.*)$", block_text, re.MULTILINE)
    return m.group(1).strip() if m else ""


def find_old_blocks(text: str) -> list[dict]:
    """Every OLD-form `### {PREFIX}-NNN_Slug` / `#### DEC-NNN_Slug` block, bounded by
    the next heading (of any kind) whose level is <= its own -- a sibling or a parent
    closing it. Fence-aware via `parse_headings_and_blocks`. A code CAN legitimately
    appear more than once (per-US "Rules enforced:"/"State transitions:" restate the
    full block, matching `technical-spec-template.md`'s own shape) -- every physical
    occurrence is returned so the renderer reshapes each one's heading; callers that
    want the unique code SET (e.g. functional-spec.md's one bullet per code) dedupe
    themselves (see `unique_by_code`)."""
    lines = text.splitlines()
    headings, _ = parse_headings_and_blocks(lines)
    old_heads = []
    for idx, raw in headings:
        m = _OLD_BLOCK_HEADING_RE.match(raw)
        if m:
            old_heads.append((idx, len(m.group(1)), m.group(2), m.group(3), m.group(4), m.group(5)))

    blocks: list[dict] = []
    for idx, level, prefix, number, slug, annotation in old_heads:
        end = len(lines)
        for h_idx, h_raw in headings:
            if h_idx <= idx:
                continue
            h_level = len(h_raw) - len(h_raw.lstrip("#"))
            if h_level <= level:
                end = h_idx
                break
        code = f"{prefix}-{number}"
        body_lines = lines[idx + 1:end]
        blocks.append({
            "code": code, "prefix": prefix, "slug": slug, "level": level,
            "start": idx, "end": end, "body_lines": body_lines,
            "body_text": "\n".join(body_lines),
            "annotation": annotation,
            "is_restatement": is_restatement_body(body_lines),
        })

    synthesize_restatement_content(blocks)
    return blocks


def unique_by_code(blocks: list[dict]) -> list[dict]:
    """First occurrence of each code only -- for building the ONE functional-spec.md
    §4 bullet per code, even when technical-spec.md restates the block per-US."""
    seen: set[str] = set()
    out: list[dict] = []
    for b in blocks:
        if b["code"] not in seen:
            seen.add(b["code"])
            out.append(b)
    return out


def sentence_for_block(blk: dict) -> str:
    """The plain-language sentence used BOTH as the new technical-spec.md heading AND
    as the functional-spec.md §4 one-liner for this code (DRY -- one derivation, two
    call sites, so the two files can never drift out of sync for the same code)."""
    prefix, body = blk["prefix"], blk["body_text"]
    words = slug_to_words(blk["slug"])
    if prefix == "BR":
        return field(body, "Rule") or words
    if prefix == "DEC":
        return field(body, "user_visible_outcome") or words
    if prefix == "SM":
        states = field(body, "States")
        base = f"Tracks the {words.lower()} state machine"
        return f"{base} (states: {states})" if states else base
    if prefix == "ALG":
        return field(body, "Description") or f"Computes {words.lower()}"
    if prefix == "INT":
        itype, target = field(body, "Type"), field(body, "Target")
        if itype and target:
            return f"Sends {itype.replace('-', ' ')} to {target}"
        return words
    return words
