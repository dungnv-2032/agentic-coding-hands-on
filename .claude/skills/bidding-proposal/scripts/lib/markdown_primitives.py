"""Stateless markdown content primitives shared by `profile_parser.py` and
`extra_slide_classifier.py`.

Kept dependency-free (no imports from either module) so both can import from
here without a circular import.
"""
from __future__ import annotations

import re

# `\[`, `Sun\*`, `1\.` — escapes a Google Docs export sprinkles through text.
_ESCAPE = re.compile(r'\\(.)')
# `[label](url)` → `label`. Non-greedy up to the first `](`, so a label that
# itself contains brackets (`[[Styleport] ROOV compass …`) survives intact.
_LINK = re.compile(r'\[(.+?)\]\((?:[^()\s]|\([^()]*\))*\)')
# `**bold**` → `bold`. Single asterisks are deliberately left alone: `Sun*` is a
# brand name in these documents, not emphasis.
_BOLD = re.compile(r'\*\*(.+?)\*\*')


def strip_inline_markup(text: str) -> str:
    """Render markdown inline markup as the plain text a slide should show.

    A slide is not a markdown reader: `**bold**`, `[label](url)` and backslash
    escapes reach the deck verbatim if nobody removes them. Schema markdown
    written by gen-md.py carries none of this, so this is a no-op there; it
    matters for a chapter lifted straight out of a human-written proposal.
    """
    text = _ESCAPE.sub(r'\1', text)
    text = _LINK.sub(r'\1', text)
    return _BOLD.sub(r'\1', text)


def split_subsections(content: str) -> dict[str, str]:
    """Split section content by `^### ` headings. Returns {heading_text: content}."""
    parts: dict[str, str] = {}
    current = None
    buf: list[str] = []
    for line in content.splitlines():
        m = re.match(r'^###\s+(.+?)\s*$', line)
        if m:
            if current is not None:
                parts[current] = '\n'.join(buf).strip()
            current = m.group(1).strip()
            buf = []
        else:
            if current is not None:
                buf.append(line)
    if current is not None:
        parts[current] = '\n'.join(buf).strip()
    return parts


def parse_table(content: str) -> list[dict]:
    """Parse a markdown pipe table into a list of dicts (keys = header row)."""
    lines = [l.strip() for l in content.splitlines() if l.strip().startswith('|')]
    if len(lines) < 2:
        return []

    def split_row(line: str) -> list[str]:
        cells = [c.strip() for c in line.split('|')]
        # Strip empty leading/trailing cells from outer pipes
        if cells and cells[0] == '':
            cells = cells[1:]
        if cells and cells[-1] == '':
            cells = cells[:-1]
        return cells

    # Header cells become dict keys, and a table layout paints them as the
    # header row — so they need the same markup cleanup the body cells get, or
    # a column is titled `Sun\*` on the finished slide.
    header = [strip_inline_markup(cell) for cell in split_row(lines[0])]
    rows = []
    for line in lines[1:]:
        # Skip separator |---|---|
        if all(c in '|-: \t' for c in line):
            continue
        cells = split_row(line)
        if not cells:
            continue
        row = {header[i] if i < len(header) else f'col{i}': strip_inline_markup(cells[i])
               for i in range(len(cells))}
        rows.append(row)
    return rows


def parse_tables(content: str) -> list[list[dict]]:
    """Parse EVERY pipe table in *content* separately, in order.

    `parse_table` concatenates whatever pipe rows it finds, which is right for
    a block holding one table and wrong for a chapter holding several: the
    first table's header would be applied to the second table's rows. This
    splits on the prose between them and parses each block on its own.
    """
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in content.splitlines():
        if line.strip().startswith('|'):
            current.append(line)
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    tables = [parse_table('\n'.join(block)) for block in blocks]
    return [table for table in tables if table]


def parse_list(content: str) -> list[str]:
    """Parse bulleted (`- item`) or numbered (`1. item`) list. Other lines ignored."""
    items: list[str] = []
    for line in content.splitlines():
        s = line.strip()
        m = re.match(r'^(?:-|\*|\d+\.)\s+(.+)$', s)
        if m:
            items.append(strip_inline_markup(m.group(1).strip()))
    return items


def parse_image_ref(content: str) -> str:
    """Extract path from `Image: path` line. Returns empty string if not found."""
    m = re.search(r'^Image:\s*(.+)$', content, re.MULTILINE)
    return m.group(1).strip() if m else ''


def parse_text(content: str) -> str:
    """Strip and return text content (multi-line preserved), inline markup removed."""
    return strip_inline_markup(content.strip())


def parse_prose(content: str) -> str:
    """Return only the prose of *content* — table rows, list items and image
    refs removed, blank lines collapsed.

    A schema-shaped section keeps its prose under its own `### Description`
    subsection, but a chapter lifted straight out of a proposal has the prose
    and its table sitting together in one block. This gives the description
    half of that block without dragging the table into it.
    """
    kept = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith('|') or stripped.startswith('Image:'):
            continue
        if re.match(r'^(?:-|\*|\d+\.)\s+', stripped):
            continue
        kept.append(stripped)  # blank lines survive — they separate paragraphs
    return strip_inline_markup(re.sub(r'\n{3,}', '\n\n', '\n'.join(kept)).strip())


def split_paragraphs(content: str) -> list[str]:
    """Split prose into blank-line-separated paragraphs."""
    blocks = re.split(r'\n\s*\n', content.strip())
    return [block.strip() for block in blocks if block.strip()]
