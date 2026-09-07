"""FR-linking backfill for structural_fixer.py (Wave 7.5): insert a placeholder
`**Linked FR:** FR-???` line into any BR/SM/ALG/INT block missing it.

Extracted out of structural_fixer.py (P09, human-readable SOT retaxonomy) to
keep that file under the repo's 200-line guidance. This is a pure extraction,
not a behavior change: `find_blocks_missing_linked_fr` (_spec_block_lib.py)
already scans for BR/SM/ALG/INT block headings ANYWHERE in the document by
their own trailing-tag shape, so it needs no section-awareness to keep
working once those blocks moved from `## Cross-Cutting Logic` to
`## 3. System Design` / `## 4. Technical Behavior by Capability` — the
insertion point is always "right after the block's own heading," regardless
of which H2 currently contains it.

Stdlib only.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _spec_block_lib import find_blocks_missing_linked_fr, has_linked_fr  # noqa: E402


def atomic_write_text(path: Path, text: str) -> None:
    """Write `text` to `path` via a same-directory temp file + `os.replace`,
    so a crash mid-write never leaves a half-written spec on disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def fix_spec(spec_path: Path, backup_root: Path) -> int:
    """Insert `**Linked FR:** FR-???` into blocks missing it. Return count fixed.

    Backs up the pre-fix file once (`backup_root/<fcode>/<name>.orig`, never
    overwritten by a later run) before writing the fixed content back.
    """
    text = spec_path.read_text(encoding="utf-8")
    missing = find_blocks_missing_linked_fr(text)
    if not missing:
        return 0

    lines = text.splitlines(keepends=True)
    eol = "\r\n" if lines and lines[0].endswith("\r\n") else "\n"
    fixed = 0
    for block in reversed(missing):
        hl = block["heading_line"]
        be = block["block_end"]
        current_text = "".join(lines)
        if has_linked_fr(current_text, hl, be):
            continue
        lines.insert(hl + 1, f"**Linked FR:** FR-???{eol}")
        fixed += 1

    if fixed == 0:
        return 0

    fcode = spec_path.parent.name
    backup_path = backup_root / fcode / f"{spec_path.name}.orig"
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    if not backup_path.exists():
        shutil.copy2(spec_path, backup_path)

    atomic_write_text(spec_path, "".join(lines))
    return fixed
