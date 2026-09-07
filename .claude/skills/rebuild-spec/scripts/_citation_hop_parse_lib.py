"""Shared `**Source:**` citation-reference parser (phase 03b, D10).

A regex anchored on `**Source:**` followed by exactly one `path:N` / `path:N-M`
pair can only ever see the FIRST reference on a line. Real `**Source:**` lines on
the migrated corpus carry THREE distinct multi-reference shapes that a single
`.search()` silently truncates to one:

  F1 arrow chain       `a.rb:1` -> `b.rb:2-5`              -- N separate path tokens
  F2 comma line-list   `a.rb:115-116,186,188`              -- 1 path, N ranges
  F3 comma-joined refs `a.rb:28`, `b.rb:40-46`             -- N separate path tokens

(F1 and F3 differ only in the separator between path tokens -- an arrow vs a bare
comma -- and are handled identically here: each is just "the next `path:linespec`
token after this one".)

This is deliberately the ONE parser both `validate_source_citations.py` and
`derive_confidence_report.py` import, instead of each re-deriving its own regex --
three separate scripts/measurements in this codebase independently made the same
"only sees the first reference" mistake before this fix (phase 03b report).

Stdlib only.
"""
from __future__ import annotations

import re
from typing import Iterator, NamedTuple, Optional

# The literal prefix every citation line starts with. `validate_source_citations.py`
# and `derive_confidence_report.py` each still own their own CITATION_RE (single
# path:N/N-M pair) for pre-existing external contracts -- `_action_thread_diagram_lib.py`
# derives its fenced `path:line` matcher from validate_source_citations.CITATION_RE's
# exact pattern text, and existing tests assert CITATION_RE's literal single-match
# behaviour. Parsing every reference on a line needs a different capture shape than
# that single-pair regex, so it is written directly here rather than sliced from it.
SOURCE_CITATION_PREFIX = r"\*\*Source:\*\*\s+"
_SOURCE_PREFIX_RE = re.compile(SOURCE_CITATION_PREFIX)

# One path:linespec token, where linespec is a comma-list of `N` or `N-M` segments
# (F2). Optional surrounding backticks, same convention as the single-hop regex.
_HOP_TOKEN_RE = re.compile(
    r"`?([^`\n:]+):(\d+(?:-\d+)?(?:\s*,\s*\d+(?:-\d+)?)*)`?"
)


class CitationToken(NamedTuple):
    path: str
    ranges: list[tuple[int, Optional[int]]]  # end is None when no "-M" was present
    match: "re.Match[str]"


def parse_linespec(spec: str) -> list[tuple[int, Optional[int]]]:
    """Split a comma-list linespec ('115-116,186,188') into (start, end) pairs.
    `end` is None when the segment carried no `-M` (a bare single-line ref) --
    this mirrors the original single-hop regex's optional group-3 semantics."""
    out: list[tuple[int, Optional[int]]] = []
    for seg in spec.split(","):
        seg = seg.strip()
        if not seg:
            continue
        if "-" in seg:
            a, b = seg.split("-", 1)
            out.append((int(a), int(b)))
        else:
            out.append((int(seg), None))
    return out


def iter_citation_tokens(line: str) -> Iterator[CitationToken]:
    """Yield one CitationToken per `path:linespec` reference after a single
    `**Source:**` prefix on `line`. Covers F1 (arrow chain) and F3 (comma-joined
    citations) by finding every token after the prefix regardless of the separator
    between them, and F2 (comma line-list) by expanding each token's linespec into
    all of its ranges. A plain, non-chained, single-range line yields exactly the
    one token a simple `**Source:** path:N` regex would have found."""
    pm = _SOURCE_PREFIX_RE.search(line)
    if not pm:
        return
    for m in _HOP_TOKEN_RE.finditer(line, pm.end()):
        path = m.group(1).strip()
        yield CitationToken(path, parse_linespec(m.group(2)), m)
