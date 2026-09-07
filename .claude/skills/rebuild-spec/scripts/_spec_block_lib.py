"""Reusable helpers for parsing BR/SM/ALG/INT sub-blocks in feature spec files.

Heading pattern (v27.0.0, audience split): `### {plain sentence} ({BR|SM|ALG|INT}-NNN)`
— the code moves from an anchored prefix (`### BR-001_NameSlug`) to a trailing tag on a
plain-language heading. DEC blocks are H4 and follow the same trailing-tag shape:
`#### {plain sentence} (DEC-NNN)`.

`LEGACY_BLOCK_HEADING_RE` recognizes the RETIRED `### {PREFIX}-NNN_Slug` form so callers
can reject it explicitly — the new trailing-tag regexes simply don't match old-form
headings, and a pattern that matches zero blocks reports zero issues (the silent-pass
failure mode this v27.0.0 change exists to close). See validate_feature_spec.py's
FeatureSpec.legacy_block_heading check.

Stdlib only. O(n) single pass.
"""
from __future__ import annotations
import re

BLOCK_HEADING_RE = re.compile(r"^### .+\((BR|SM|ALG|INT)-(\d{3})\)\s*$")
LINKED_FR_RE = re.compile(r"^\*\*Linked FR:\*\*")

# Prefix-only variant of BLOCK_HEADING_RE — no capture group on the numeric suffix.
# NOT interchangeable with BLOCK_HEADING_RE (different capture groups); relocated verbatim
# from validate_feature_spec.py (was `_BLOCK_HEADING_RE`).
BLOCK_HEADING_PREFIX_RE = re.compile(r"^### .+\((BR|SM|ALG|INT)-\d{3}\)\s*$")

# SM/DEC sub-block headings — distinct heading levels (### vs ####) from BLOCK_HEADING_RE /
# BLOCK_HEADING_PREFIX_RE above. Relocated verbatim from validate_feature_spec.py.
SM_BLOCK_RE = re.compile(r"^###\s+.+\(SM-\d{3}\)\s*$")
DEC_BLOCK_RE = re.compile(r"^####\s+.+\(DEC-\d{3}\)\s*$")

# Retired heading form: `### BR-001_NameSlug` / `#### DEC-001_NameSlug`. A heading matching
# this AND not matching one of the trailing-tag regexes above is a migration miss, not a
# non-block heading — validate_feature_spec.py flags it explicitly (FeatureSpec.legacy_block_heading)
# so the old form is rejected rather than silently treated as ordinary prose.
LEGACY_BLOCK_HEADING_RE = re.compile(r"^#{3,4}\s+(BR|SM|ALG|INT|DEC)-\d{3}_\S+")


def find_blocks(text: str) -> list[dict]:
    """Return a list of dicts for every BR/SM/ALG/INT block heading.

    Each dict has:
        heading_line  int   0-based line index of the heading
        heading_text  str   full heading line text
        prefix        str   BR | SM | ALG | INT
        code          str   e.g. "BR-001"
        block_end     int   line index of the next ### heading, or len(lines)

    Headings inside fenced code blocks (``` or ~~~) are skipped.
    """
    lines = text.splitlines()
    total = len(lines)
    found: list[dict] = []
    in_fence = False
    fence_char = ""

    for i, ln in enumerate(lines):
        stripped = ln.strip()
        if not in_fence:
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_fence = True
                fence_char = stripped[:3]
                continue
        else:
            if stripped.startswith(fence_char):
                in_fence = False
            continue

        m = BLOCK_HEADING_RE.match(ln)
        if m:
            prefix = m.group(1)
            number = m.group(2)       # e.g. "001"
            code = f"{prefix}-{number}"  # e.g. "BR-001"
            found.append({
                "heading_line": i,
                "heading_text": ln,
                "prefix": prefix,
                "code": code,
                "block_end": total,    # filled in next pass
            })

    # fill block_end: each block ends where the next ### heading starts
    for k in range(len(found) - 1):
        found[k]["block_end"] = found[k + 1]["heading_line"]

    return found


def has_linked_fr(text: str, heading_line: int, block_end: int) -> bool:
    """Return True if **Linked FR:** appears between heading_line and block_end."""
    lines = text.splitlines()
    for i in range(heading_line + 1, min(block_end, len(lines))):
        if LINKED_FR_RE.match(lines[i]):
            return True
    return False


def find_blocks_missing_linked_fr(text: str) -> list[dict]:
    """Return only blocks that are missing a **Linked FR:** line."""
    blocks = find_blocks(text)
    return [b for b in blocks if not has_linked_fr(text, b["heading_line"], b["block_end"])]
