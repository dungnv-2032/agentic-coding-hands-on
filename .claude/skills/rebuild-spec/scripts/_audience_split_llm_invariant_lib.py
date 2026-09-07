"""Pre/post invariant gate for the LLM prose-compaction pass (Requirement 5, H-FM4).

The LLM pass itself is NOT run by this module -- it is a separate, human-in-the-loop
authoring step (see `references/migration-audience-split.md`). This module is the
MECHANICAL gate a caller runs before accepting whatever the LLM produced: compare the
pre-compaction text against the post-compaction text and refuse anything that dropped
structure or content, never trusting "it still reads fine."

Structural invariants (H-FM4 names these as necessary but NOT sufficient on their own):
  - identical H2 heading set
  - identical FR/BR/SM/DEC/SCR code set
  - edge-case table row count not decreased

Semantic invariant (the one that actually matters, per H-FM4): structure alone lets a
rule keep its code and heading while quietly losing two of its three conditions. Every
numeral, threshold, enum value, date and endpoint count present pre-compaction MUST
still be present, verbatim, post-compaction. A rewording that keeps the code/heading
but drops a `$10,000`-class threshold passes every structural check and must still FAIL
here -- that is the fixture this module is built to catch.

Stdlib only.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _md_scan_lib import iter_lines_with_fence, mask_fenced  # noqa: E402

_H2_RE = re.compile(r"^##\s+\S")
_HEADING_RE = re.compile(r"^#{1,6}\s")
# (?!\d) not a trailing \b: a trailing \b never matches a slug-suffixed code like
# "SCR001_Login" or "BR-001_Login" because "_" is a word character, so digit->"_" is
# not a word boundary. This is the SAME bug already fixed at validate_feature_spec.py:67
# (_TECH_CODE_RE) and :492 (the SCR cell match) -- re-typed here for a THIRD time before
# being caught by adversarial review. Both code-matching regexes in this module are
# fixed for consistency, even though only the SCR form was confirmed live-exploitable
# here (FR/BR/SM/DEC codes always appear paren-terminated, e.g. "(BR-001)", in this
# codebase's v27 canonical form) -- the underlying pattern is identical and slug-suffixed
# rule codes are not something this module can assume will never occur.
_CODE_RE = re.compile(r"\b(?:FR|BR|SM|DEC)-\d{3}(?!\d)")
_SCR_RE = re.compile(r"\bSCR\d{3}(?!\d)")
_EDGE_CASES_HEADING_RE = re.compile(r"^#{1,6}\s.*edge cases", re.IGNORECASE)
_TABLE_ROW_RE = re.compile(r"^\s*\|")
_TABLE_SEP_RE = re.compile(r"^\s*\|[\s:|-]+\|\s*$")

# Semantic tokens: money, percentages, ISO/slash dates, bare numerals (codes are
# matched too, which is harmless -- a code number is a superset member the code-set
# check already covers), and short backtick-wrapped enum/status/config tokens.
_MONEY_RE = re.compile(r"\$[\d,]+(?:\.\d+)?")
_PERCENT_RE = re.compile(r"\b\d+(?:\.\d+)?%")
_DATE_ISO_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
_DATE_SLASH_RE = re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b")
_NUMBER_RE = re.compile(r"\b\d[\d,]*(?:\.\d+)?\b")
_ENUM_TOKEN_RE = re.compile(r"`([A-Za-z0-9_.:/-]{1,30})`")


@dataclass(frozen=True)
class InvariantResult:
    ok: bool
    violations: list[str] = field(default_factory=list)


def _h2_set(text: str) -> set[str]:
    return {ln.strip() for ln in text.splitlines() if _H2_RE.match(ln)}


def _code_set(text: str) -> set[str]:
    masked = mask_fenced(text)
    return set(_CODE_RE.findall(masked)) | set(_SCR_RE.findall(masked))


def _section_body(text: str, heading_re: re.Pattern) -> str | None:
    """Body of the first heading matching *heading_re*, bounded by the next heading
    (any level) or EOF. Fence-aware -- a fenced line shaped like a heading never closes
    the section early. None if the heading is absent."""
    body_lines: list[str] | None = None
    for _, line, in_fence in iter_lines_with_fence(text):
        if body_lines is None:
            if not in_fence and heading_re.match(line):
                body_lines = []
            continue
        if not in_fence and _HEADING_RE.match(line):
            break
        body_lines.append(line)
    return "\n".join(body_lines) if body_lines is not None else None


def _edge_case_row_count(text: str) -> int:
    body = _section_body(text, _EDGE_CASES_HEADING_RE)
    if body is None:
        return 0
    rows = [ln for ln in body.splitlines() if _TABLE_ROW_RE.match(ln) and not _TABLE_SEP_RE.match(ln)]
    # Drop the header row (first table row) -- only DATA rows count.
    return max(0, len(rows) - 1) if rows else 0


def _semantic_tokens(text: str) -> set[str]:
    masked = mask_fenced(text)
    body = "\n".join(ln for ln in masked.splitlines() if not _HEADING_RE.match(ln))
    tokens: set[str] = set()
    tokens |= set(_MONEY_RE.findall(body))
    tokens |= set(_PERCENT_RE.findall(body))
    tokens |= set(_DATE_ISO_RE.findall(body))
    tokens |= set(_DATE_SLASH_RE.findall(body))
    tokens |= set(_NUMBER_RE.findall(body))
    tokens |= set(_ENUM_TOKEN_RE.findall(body))
    return tokens


def check_invariants(pre: str, post: str) -> InvariantResult:
    """Compare *pre* (before compaction) against *post* (after). Never mutates either
    string. `ok=False` means the compacted version must be REJECTED -- the caller must
    not swap it into staging/live, matching the same fail-closed posture as I3/I4."""
    violations: list[str] = []

    pre_h2, post_h2 = _h2_set(pre), _h2_set(post)
    if pre_h2 != post_h2:
        missing = pre_h2 - post_h2
        added = post_h2 - pre_h2
        violations.append(
            f"H2 set changed -- missing: {sorted(missing)}, added: {sorted(added)}"
        )

    pre_codes, post_codes = _code_set(pre), _code_set(post)
    if pre_codes != post_codes:
        missing = pre_codes - post_codes
        added = post_codes - pre_codes
        violations.append(
            f"FR/BR/SM/DEC/SCR code set changed -- missing: {sorted(missing)}, "
            f"added: {sorted(added)}"
        )

    pre_edge_rows, post_edge_rows = _edge_case_row_count(pre), _edge_case_row_count(post)
    if post_edge_rows < pre_edge_rows:
        violations.append(
            f"edge-case row count decreased: {pre_edge_rows} -> {post_edge_rows}"
        )

    # Semantic invariant (H-FM4) -- the one that actually matters. A rule can keep its
    # code and its heading while quietly losing a threshold; only a token-level diff
    # catches that.
    pre_tokens, post_tokens = _semantic_tokens(pre), _semantic_tokens(post)
    dropped = pre_tokens - post_tokens
    if dropped:
        violations.append(
            f"numeral/threshold/enum/date token(s) dropped by compaction: {sorted(dropped)}"
        )

    return InvariantResult(ok=not violations, violations=violations)
