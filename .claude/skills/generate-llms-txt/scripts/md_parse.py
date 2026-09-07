#!/usr/bin/env python3
"""Pure markdown parsers for the llms.txt generator — no filesystem walking, pure stdlib.
Separated from discovery.py (which owns the ladder + fs traversal) so parsing stays testable
in isolation.
"""
import re
from pathlib import Path

DESC_MAX = 160


def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def h1_title(content: str, fallback: Path) -> str:
    """First H1 OUTSIDE a fenced code block; else the file stem, title-cased."""
    in_fence = False
    for line in content.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            m = re.match(r"#\s+(.+)$", line.strip())
            if m:
                return m.group(1).strip()
    return fallback.stem.replace("-", " ").replace("_", " ").title()


def extract_description(content: str) -> str:
    """Baseline description: first prose paragraph after the H1, skipping frontmatter,
    headings, lists, bold-key metadata (`**Key**:`), and fenced code blocks (a blockquote
    counts). Truncated to DESC_MAX chars. The LLM step enriches this."""
    seen_h1 = in_fence = False
    para = []
    for raw in content.splitlines():
        s = raw.strip()
        if s.startswith("```"):
            if para:
                break
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not seen_h1:
            if s.startswith("# "):
                seen_h1 = True
            continue
        if not s:
            if para:
                break
            continue
        if s.startswith("#") or s.startswith("---"):
            if para:
                break
            continue
        if s.startswith(">"):
            para.append(s.lstrip("> ").strip())
            continue
        if s.startswith(("- ", "* ", "| ")):
            if para:
                break
            continue
        if re.match(r"\*\*[^*]+\*\*:\s", s):  # bold-key metadata (**Project**: …) — not prose
            continue
        para.append(s)
    desc = " ".join(para).strip()
    if len(desc) > DESC_MAX:
        desc = desc[: DESC_MAX - 1].rsplit(" ", 1)[0] + "…"
    return desc


_BOLD_FIELD = re.compile(r"^\*\*([^*]+)\*\*:\s*(.+)$")


def bold_fields(content: str) -> dict:
    """Generic `**Key**: value` extractor, fence-aware — a line inside a ``` block is skipped.
    First occurrence of a key wins; later duplicates of the same key are ignored. Keys and
    values come back stripped, in source order."""
    fields = {}
    in_fence = False
    for raw in content.splitlines():
        line = raw.strip()
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = _BOLD_FIELD.match(line)
        if m and m.group(1).strip() not in fields:
            fields[m.group(1).strip()] = m.group(2).strip()
    return fields


def project_field(content: str) -> str:
    """Product name from the `**Project**: X` line of a rebuild-spec overview (its H1 is the
    hardcoded '# System Overview'). Ignored if still an unfilled placeholder ({...}).

    Delegates to bold_fields() — documented behavior change from v1: v1 ran a raw re.search
    over the whole content and was NOT fence-aware, so a `**Project**: X` line shown inside a
    fenced code block (e.g. a doc-writing example) would match. bold_fields() skips fenced
    lines, so that case is now correctly ignored. Identical to v1 on all non-fenced input."""
    val = bold_fields(content).get("Project", "")
    if val and not (val.startswith("{") and val.endswith("}")):
        return val
    return ""
