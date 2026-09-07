#!/usr/bin/env python3
"""Extract embedded raster images from OOXML documents so graphify can see them.

Graphify reads `.docx`/`.xlsx` as text only (`doc.paragraphs`,
`load_workbook(data_only=True)`) and does not read `.pptx` at all, so a diagram pasted
into a spec or a slide deck contributes nothing to the graph. `.docx`, `.xlsx` and
`.pptx` are ZIP containers whose media sit under `word/media/`, `xl/media/` and
`ppt/media/`, so pulling them out needs the standard library and nothing else — no
`python-docx`, no `python-pptx`, no optional graphify extra.

Extracted files are handed to the same vision path `/graphify` already uses for
standalone images. Two invariants make that safe and are the reason this is a script
rather than prose in SKILL.md:

  * De-duplication by content hash. A slide master repeats its logo on every slide, so a
    40-slide deck can yield 40 copies of one image — and each image costs its own
    extraction subagent. Identical bytes are written once.
  * Provenance. Extracted files live in a scratch directory; the emitted map records
    which document each one came from, so callers can rewrite `source_file` back to the
    original after extraction. Skip that and the graph ends up with nodes pointing at
    temp paths that no longer exist.

Never raises: an unreadable or non-ZIP document is reported and skipped. Exit code is 0
unless the arguments themselves are wrong.

Usage:
    python3 extract_embedded_media.py <doc>... --out <dir> [--cap N] [--clean]
"""

import argparse
import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path

OOXML_SUFFIXES = {".docx", ".xlsx", ".pptx"}
MEDIA_PREFIXES = ("word/media/", "xl/media/", "ppt/media/")
# Raster formats the vision path can read. `.svg` is deliberately absent: it is XML text,
# and nothing in /graphify says how a subagent should render one.
RASTER_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
# 30, not 20: across a corpus of real requirements decks the busiest held 21 raster images,
# so a cap of 20 clipped the largest genuine document by one. The cap exists to stop a
# scanned 300-page monster, not to trim ordinary decks.
DEFAULT_CAP = 30
# Mirrors graphify's own office zip-bomb screen (detect.py `_OFFICE_MAX_RAW_BYTES`).
MAX_DOC_BYTES = 50 * 1024 * 1024
MAX_MEMBER_BYTES = 20 * 1024 * 1024


def media_members(archive: zipfile.ZipFile) -> list[str]:
    """Media entries worth extracting, in stable order."""
    return sorted(
        name
        for name in archive.namelist()
        if name.startswith(MEDIA_PREFIXES) and Path(name).suffix.lower() in RASTER_SUFFIXES
    )


def extract_document(
    document: Path, out_dir: Path, cap: int, seen: dict[str, Path]
) -> tuple[list[dict], list[dict]]:
    """Extract deduped media from one document. Returns (records, problems)."""
    records: list[dict] = []
    problems: list[dict] = []

    try:
        if document.stat().st_size > MAX_DOC_BYTES:
            return [], [{"document": str(document), "reason": "over-size-cap"}]
        with zipfile.ZipFile(document) as archive:
            members = media_members(archive)
            for member in members[:cap]:
                info = archive.getinfo(member)
                if info.file_size > MAX_MEMBER_BYTES:
                    problems.append({"document": str(document), "member": member,
                                     "reason": "member-over-cap"})
                    continue
                payload = archive.read(member)
                digest = hashlib.sha256(payload).hexdigest()
                target = seen.get(digest)
                if target is None:
                    target = out_dir / f"{digest[:16]}{Path(member).suffix.lower()}"
                    target.write_bytes(payload)
                    seen[digest] = target
                records.append({"image": str(target), "document": str(document),
                                "member": member, "sha256": digest})
            if len(members) > cap:
                problems.append({"document": str(document), "reason": "cap-reached",
                                 "extracted": cap, "remaining": len(members) - cap})
    except zipfile.BadZipFile:
        problems.append({"document": str(document), "reason": "not-a-zip"})
    except Exception as exc:  # a broken document must never abort the caller's run
        problems.append({"document": str(document), "reason": type(exc).__name__})

    return records, problems


def run(documents: list[Path], out_dir: Path, cap: int) -> dict:
    """Extract from every OOXML document, returning a JSON-serialisable summary."""
    out_dir.mkdir(parents=True, exist_ok=True)
    seen: dict[str, Path] = {}
    records: list[dict] = []
    problems: list[dict] = []

    for document in documents:
        if document.suffix.lower() not in OOXML_SUFFIXES:
            continue
        if not document.is_file():
            # Report rather than skip. A real corpus held an *unpacked* deck — a directory
            # literally named `<name>.pptx` — and dropping it without a word would look
            # exactly like a deck that simply had no images.
            problems.append({"document": str(document), "reason": "not-a-file"})
            continue
        found, issues = extract_document(document, out_dir, cap, seen)
        records.extend(found)
        problems.extend(issues)

    # provenance maps the extracted file back to the document it came from, so the caller
    # can rewrite source_file after extraction. A duplicate keeps its first document.
    provenance: dict[str, str] = {}
    for record in records:
        provenance.setdefault(record["image"], record["document"])

    return {
        "images": sorted(provenance),
        "unique": len(provenance),
        "occurrences": len(records),
        "deduplicated": len(records) - len(provenance),
        "provenance": provenance,
        "problems": problems,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract embedded images from OOXML docs.")
    parser.add_argument("documents", nargs="+", help=".docx / .xlsx / .pptx files")
    parser.add_argument("--out", required=True, help="scratch directory for the images")
    parser.add_argument("--cap", type=int, default=DEFAULT_CAP,
                        help=f"max images per document (default {DEFAULT_CAP})")
    parser.add_argument("--clean", action="store_true", help="empty --out before writing")
    args = parser.parse_args(argv)

    out_dir = Path(args.out)
    if args.clean and out_dir.exists():
        shutil.rmtree(out_dir)

    summary = run([Path(d) for d in args.documents], out_dir, args.cap)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
