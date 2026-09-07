"""Mode A -- dev-token fencing for `functional-spec.md` prose (phase-04, B4b).

`validate_feature_spec.FUNC_DEV_TOKEN_RE` forbids HTTP-verb and `path.ext:123`
file:line dev tokens appearing OUTSIDE inline code in `functional-spec.md` (the
BA/QA audience file) -- but exempts anything already inside a backtick span
(`strip_inline_code`, phase-03). v26 prose copies these tokens through bare:
composing straight through trips the validator on ~145 occurrences across the
corpus. `fence_dev_tokens` wraps each bare occurrence in backticks so the
validator's own exemption applies, without disturbing anything already fenced,
any ``` fenced block, table structure, or heading lines.

Stdlib only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from validate_feature_spec import FUNC_DEV_TOKEN_RE  # noqa: E402 -- DRY: single pattern source

_BACKTICK_RUN_RE = re.compile(r"`+")
_HEADING_RE = re.compile(r"^#{1,6}\s")
_FENCE_MARK_RE = re.compile(r"^```")


def _inline_code_spans(line: str) -> list[tuple[int, int]]:
    """[start, end) character ranges already inside a backtick span on *line*.

    Mirrors `validate_feature_spec.strip_inline_code`'s CommonMark delimiter-
    matching rule (an opening run of N backticks closes at the next run of
    exactly N backticks) but returns spans rather than masking the text --
    fencing needs to know what to skip past, not blank it out. Fail-open here
    is the safe direction (unlike the validator's fail-closed masking):
    an unterminated opening run is simply not treated as "inside a span", so
    any dev token after it is still a fencing candidate -- worst case it gets
    (harmlessly) fenced, never silently left dangerous."""
    runs = list(_BACKTICK_RUN_RE.finditer(line))
    spans: list[tuple[int, int]] = []
    i, total = 0, len(runs)
    while i < total:
        open_run = runs[i]
        open_len = len(open_run.group())
        close_idx = next(
            (j for j in range(i + 1, total) if len(runs[j].group()) == open_len),
            None,
        )
        if close_idx is None:
            break  # unterminated -- nothing further on this line is "inside a span"
        spans.append((open_run.start(), runs[close_idx].end()))
        i = close_idx + 1
    return spans


def _fence_line(line: str) -> str:
    """Wrap every bare FUNC_DEV_TOKEN_RE match on *line* in backticks.

    Never touches a heading line (a stray backtick there would break
    REQUIRED_H2_FUNC's exact-string match). A match already inside a backtick
    span (of any delimiter length) is left alone -- this is what makes the
    function idempotent, since `sanitize()` runs once per `_field_block` and
    once again on final document assembly."""
    if _HEADING_RE.match(line):
        return line
    spans = _inline_code_spans(line)

    def _in_span(pos: int) -> bool:
        return any(s <= pos < e for s, e in spans)

    out: list[str] = []
    last = 0
    for m in FUNC_DEV_TOKEN_RE.finditer(line):
        if _in_span(m.start()):
            continue
        out.append(line[last:m.start()])
        out.append(f"`{m.group()}`")
        last = m.end()
    out.append(line[last:])
    return "".join(out)


def fence_dev_tokens(text: str) -> str:
    """Wrap every bare dev-token match (see `FUNC_DEV_TOKEN_RE`) in inline
    backticks, line by line.

    Idempotent: a token already inside a backtick span is left untouched, so
    running this twice on the same text is byte-identical to running it once
    -- required, since composition calls `sanitize()` (which wires this in)
    both per-section and again on the assembled document. Skips the contents
    of ``` fenced code blocks entirely (composition emits none into
    functional-spec.md today, but Mode A copies raw v26 prose verbatim in
    places, so a future corpus could carry one). Table rows ARE fenced in
    place -- a backtick inside a `|`-delimited cell is ordinary markdown and
    does not change the cell count or pipe positions.
    """
    out_lines: list[str] = []
    in_fence = False
    for line in text.split("\n"):
        if _FENCE_MARK_RE.match(line.strip()):
            in_fence = not in_fence
            out_lines.append(line)
            continue
        if in_fence:
            out_lines.append(line)
            continue
        out_lines.append(_fence_line(line))
    return "\n".join(out_lines)
