#!/usr/bin/env python3
"""_cap_map_io_lib.py -- shared I/O helpers for the `cap-map` `--migrate` step
(phase-07, plans/260819-1016-rebuild-spec-capability-map): feature-dir discovery,
boundary-checked atomic writes, and the `.bak` path convention. Split out so
`_doc_migration_cap_map_step_lib.py` (registry wiring) and `_cap_map_rollback_lib.py`
(`--rollback cap-map`) share ONE implementation of each rather than two that could
drift -- both files stay under the repo's 200-line guidance as a result.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

FeatureFilter = "frozenset[str] | None"

# Backup staging dir name under `<docs_root>/.migrate-v27/<name>/<feature>/...` --
# rollback state ONLY (see module docstrings of the two callers): never read by
# `count_pending`.
BACKUP_DIRNAME = "cap-map"


def iter_feature_dirs(docs_root: Path, features: "FeatureFilter" = None) -> list[Path]:
    """Same glob precedent as `_doc_migration_feature_sot_step_lib.py` -- reused
    verbatim (never a fresh glob) so rollback's symlink-following exposure is no
    different from every other step's."""
    dirs = sorted(p.parent for p in docs_root.glob("features/*/functional-spec.md"))
    if features is not None:
        dirs = [d for d in dirs if d.name in features]
    return dirs


def read_text(path: Path) -> "str | None":
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def backup_path(docs_root: Path, feature_name: str) -> Path:
    return docs_root / ".migrate-v27" / BACKUP_DIRNAME / feature_name / "functional-spec.md.bak"


def _cleanup(tmp_path: str) -> None:
    try:
        os.unlink(tmp_path)
    except OSError:
        pass


def atomic_write(path: Path, text: str) -> None:
    """Staged temp-file-then-`os.replace` -- CRASH-SAFETY only (a concurrent reader
    never sees a half-written file). This is NOT undo; see the callers' docstrings
    for why that distinction is stated explicitly rather than assumed."""
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
    except Exception:
        _cleanup(tmp)
        raise
    os.replace(tmp, path)
