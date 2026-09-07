"""Backfill `## Source Code References` from inline `**Source:**` citations
already present elsewhere in a composed `technical-spec.md` (P11 / class 2).

`render_technical_spec` (`_audience_split_compose_a_lib.py`) splices block headings
and normalizes CCL, but otherwise passes every other section through byte-for-byte
-- including `## Source Code References`. The real sharetribe corpus authored that
section's body ONCE, up front, as a boilerplate pointer ("See source citations in
cross-cutting logic sections above.") before the per-block `**Source:**` citations
existed alongside it. Every citation the pointer refers to is ALREADY in the same
document; this aggregates them, it invents nothing.

A document with a genuinely non-boilerplate body (real citations, or truly blank)
is left untouched. A document with ZERO inline citations to aggregate is also left
untouched -- FeatureSpec.source_refs_empty must still fire on a spec that actually
has no evidence, not be silently satisfied by a fabricated one.

Stdlib only.
"""
from __future__ import annotations

import re

# Matches the SAME shape validate_feature_spec.py's `_SOURCE_LINE_RE` requires per
# rendered line: `**Source:** ` followed by real content. Citations are extracted
# from backtick-wrapped `path:N-M` tokens specifically, since those are what this
# module re-emits (a `**Source:** \`path:N-M\`` line satisfies the validator's
# per-line check directly).
_INLINE_SOURCE_RE = re.compile(r"^\*\*Source:\*\*\s+(.+)$", re.MULTILINE)
_BACKTICK_PATH_RE = re.compile(r"`([^`\n]+:\d+(?:-\d+)?)`")

_PLACEHOLDER_BODY_RE = re.compile(
    r"^\s*See source citations in cross-cutting logic sections above\.?\s*$",
    re.IGNORECASE,
)


def _collect_citations(text: str) -> list[str]:
    """Every distinct backtick-wrapped `path:N-M` citation cited by an inline
    **Source:** line anywhere in the document, in first-seen order."""
    seen: list[str] = []
    seen_set: set[str] = set()
    for m in _INLINE_SOURCE_RE.finditer(text):
        for path in _BACKTICK_PATH_RE.findall(m.group(1)):
            if path not in seen_set:
                seen_set.add(path)
                seen.append(path)
    return seen


def backfill_source_references(text: str) -> str:
    """Replace a boilerplate (non-citation) `## Source Code References` body with
    a `**Source:** \\`path:N-M\\`` bullet per distinct citation already cited inline
    elsewhere in the document. No-ops when the section already has real content
    (or is genuinely blank -- left as-is), or when the document has zero inline
    citations to aggregate (nothing invented; the spec must still fail)."""
    lines = text.splitlines()
    heading_idx = next(
        (i for i, ln in enumerate(lines) if ln.strip() == "## Source Code References"),
        None,
    )
    if heading_idx is None:
        return text
    end_idx = next(
        (i for i in range(heading_idx + 1, len(lines)) if re.match(r"^#{1,2}\s", lines[i])),
        len(lines),
    )
    body = "\n".join(lines[heading_idx + 1:end_idx]).strip()
    if not _PLACEHOLDER_BODY_RE.match(body):
        return text
    citations = _collect_citations(text)
    if not citations:
        return text
    new_body = "\n".join(f"**Source:** `{c}`" for c in citations)
    new_section = ["## Source Code References", "", new_body, ""]
    return "\n".join(lines[:heading_idx] + new_section + lines[end_idx:])
