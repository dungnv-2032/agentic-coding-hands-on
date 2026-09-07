"""Generic fence-aware heading-level section splitter shared by the Mode A/B/C
composers (`_audience_split_compose_a_lib.py` / `_audience_split_mode_b_lib.py` /
`_audience_split_mode_c_lib.py`). One primitive, not three near-duplicates. Stdlib only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _md_scan_lib import iter_lines_with_fence  # noqa: E402


def split_sections(text: str, level: int) -> tuple[str, dict[str, str]]:
    """Split *text* into (preamble, {heading line: raw body}) at H*level* boundaries.

    Body includes any DEEPER heading level as content verbatim (never split further
    here -- call again on a body string for the next level down). Fence-aware -- a
    fenced line shaped like a heading is never treated as one. Preamble is everything
    before the first H*level* heading."""
    prefix = "#" * level + " "
    boundary_re = re.compile(r"^" + re.escape("#" * level) + r"\s+(.+?)\s*$")
    preamble: list[str] = []
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for _, line, in_fence in iter_lines_with_fence(text):
        if not in_fence:
            m = boundary_re.match(line)
            if m:
                current = prefix + m.group(1)
                sections[current] = []
                continue
        (preamble if current is None else sections[current]).append(line)
    return "\n".join(preamble), {k: "\n".join(v).strip("\n") for k, v in sections.items()}


def extract_h3_body(container_text: str, h3_heading: str) -> str | None:
    """Body of *h3_heading* (exact text) within *container_text*, bounded by the next
    heading of level 1-3 or EOF. Fence-aware. `None` if *h3_heading* is absent."""
    boundary_re = re.compile(r"^#{1,3}\s")
    found = False
    body: list[str] = []
    for _, line, in_fence in iter_lines_with_fence(container_text):
        if not in_fence and not found and line.strip() == h3_heading:
            found = True
            continue
        if found and not in_fence and boundary_re.match(line):
            break
        if found:
            body.append(line)
    if not found:
        return None
    return "\n".join(body).strip("\n")
