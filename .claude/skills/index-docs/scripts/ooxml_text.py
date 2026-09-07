#!/usr/bin/env python3
"""Recover text from OOXML documents using only the standard library.

Written for one case above all: graphify has **no** `.pptx` support. `.pptx` is not in its
`OFFICE_EXTENSIONS`, so a slide deck contributes nothing to the graph no matter which
optional extras are installed. Decks are common early in a project and carry the
architecture in their titles and bullets, so "nothing" is expensive.

`.docx` and `.xlsx` are a weaker case: graphify parses them properly when
`graphifyy[office]` is installed, keeping heading levels and tables. This module is the
fallback for when it is not — a default `uv tool install graphifyy` ships neither
`python-docx` nor `openpyxl`, and the extractor then returns an empty string with no
warning. Flat text beats silence, but prefer the extra when it is available.

OOXML is a ZIP of XML: `<a:t>` holds slide text, `<w:t>` document text, and
`xl/sharedStrings.xml` the strings a sheet references. Reading those needs no dependency.

Never raises: an unreadable document yields no text and is reported.

Usage:
    python3 ooxml_text.py <doc>... [--out <dir>]      # sidecar .md per document
    python3 ooxml_text.py <doc> --stdout              # print one document
"""

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

_DRAWING = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
_WORD = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
DRAWING_P, DRAWING_T = f"{_DRAWING}p", f"{_DRAWING}t"
WORD_P, WORD_T = f"{_WORD}p", f"{_WORD}t"
SHEET_T = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"
MAX_DOC_BYTES = 50 * 1024 * 1024


def _texts(payload: bytes, tag: str) -> list[str]:
    """Non-empty text nodes with `tag`, in document order."""
    try:
        root = ElementTree.fromstring(payload)
    except ElementTree.ParseError:
        return []
    return [node.text.strip() for node in root.iter(tag) if node.text and node.text.strip()]


def _paragraphs(payload: bytes, para_tag: str, text_tag: str) -> list[str]:
    """One string per paragraph, runs joined.

    A paragraph splits into a new run at every formatting change, and real decks change
    formatting mid-sentence constantly — bolding a term, or switching font between Japanese
    and Latin. Walking `<a:t>`/`<w:t>` flat therefore shreds one sentence into several
    fragments: a real requirements deck produced "APPBOX" / "で配信したお知らせの内容を" /
    "Web" / "サーバー側で取得可能です。" as four separate lines. Joining within the
    paragraph restores the sentence, which is what the extraction subagent needs to find
    entities in.
    """
    try:
        root = ElementTree.fromstring(payload)
    except ElementTree.ParseError:
        return []
    lines = []
    for para in root.iter(para_tag):
        joined = "".join(node.text for node in para.iter(text_tag) if node.text).strip()
        if joined:
            lines.append(joined)
    return lines


def _slide_order(name: str) -> tuple[int, str]:
    """Sort slide2.xml before slide10.xml, which a plain string sort would not."""
    digits = "".join(c for c in Path(name).stem if c.isdigit())
    return (int(digits) if digits else 0, name)


def pptx_text(archive: zipfile.ZipFile) -> str:
    """One markdown section per slide. The first text run is treated as the title."""
    slides = sorted(
        (n for n in archive.namelist()
         if n.startswith("ppt/slides/slide") and n.endswith(".xml")),
        key=_slide_order,
    )
    blocks: list[str] = []
    for index, name in enumerate(slides, start=1):
        paragraphs = _paragraphs(archive.read(name), DRAWING_P, DRAWING_T)
        if not paragraphs:
            continue
        # The first paragraph is usually the slide title, but decks routinely open with a
        # numbering fragment ("3.") — too short to be one, so keep it in the body instead.
        title, body = paragraphs[0], paragraphs[1:]
        if len(title) < 4:
            title, body = f"(slide {index})", paragraphs
        lines = [f"## Slide {index} — {title}"]
        lines += [f"- {line}" for line in body]
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def docx_text(archive: zipfile.ZipFile) -> str:
    """Flat paragraphs. Loses heading levels and tables — see the module docstring."""
    try:
        payload = archive.read("word/document.xml")
    except KeyError:
        return ""
    return "\n\n".join(_paragraphs(payload, WORD_P, WORD_T))


def xlsx_text(archive: zipfile.ZipFile) -> str:
    """Cell text — labels and headers, which is what carries meaning.

    Two storage forms exist and a workbook uses one or the other. Most writers pool text
    into `xl/sharedStrings.xml`; others emit `t="inlineStr"` cells carrying `<is><t>`
    inside the sheet itself, with no shared table at all. Reading only the first form
    returns nothing for the second — two real workbooks in a test corpus came back empty
    that way — so both are collected.
    """
    values: list[str] = []
    try:
        values += _texts(archive.read("xl/sharedStrings.xml"), SHEET_T)
    except KeyError:
        pass
    for name in sorted(n for n in archive.namelist()
                       if n.startswith("xl/worksheets/") and n.endswith(".xml")):
        values += _texts(archive.read(name), SHEET_T)

    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            unique.append(value)
    return "\n".join(f"- {value}" for value in unique)


EXTRACTORS = {".pptx": pptx_text, ".docx": docx_text, ".xlsx": xlsx_text}


def extract(document: Path) -> tuple[str, str | None]:
    """Return (text, problem). Text is empty when nothing could be read."""
    extractor = EXTRACTORS.get(document.suffix.lower())
    if extractor is None:
        return "", "unsupported-suffix"
    try:
        if document.stat().st_size > MAX_DOC_BYTES:
            return "", "over-size-cap"
        with zipfile.ZipFile(document) as archive:
            return extractor(archive), None
    except zipfile.BadZipFile:
        return "", "not-a-zip"
    except Exception as exc:
        return "", type(exc).__name__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Recover OOXML text with the stdlib only.")
    parser.add_argument("documents", nargs="+", help=".pptx / .docx / .xlsx files")
    parser.add_argument("--out", help="write <name>.ooxml.md sidecars into this directory")
    parser.add_argument("--stdout", action="store_true", help="print text instead of writing")
    args = parser.parse_args(argv)

    if not args.out and not args.stdout:
        parser.error("pass --out <dir> or --stdout")

    out_dir = Path(args.out) if args.out else None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)

    written: dict[str, str] = {}
    problems: list[dict] = []
    for raw in args.documents:
        document = Path(raw)
        text, problem = extract(document)
        if problem:
            problems.append({"document": str(document), "reason": problem})
            continue
        if not text:
            problems.append({"document": str(document), "reason": "no-text-found"})
            continue
        if args.stdout:
            print(text)
            continue
        # Suffix with a path hash: a corpus routinely holds the same stem in several
        # directories (a translated copy beside its source), and a bare `<stem>.ooxml.md`
        # lets the later one overwrite the earlier without a word. Three documents were
        # lost that way on a real corpus before this.
        tag = hashlib.sha256(str(document.resolve()).encode("utf-8")).hexdigest()[:8]
        sidecar = out_dir / f"{document.stem}-{tag}.ooxml.md"
        sidecar.write_text(f"# {document.name}\n\n{text}\n", encoding="utf-8")
        written[str(sidecar)] = str(document)

    if not args.stdout:
        print(json.dumps({"written": written, "count": len(written),
                          "problems": problems}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
