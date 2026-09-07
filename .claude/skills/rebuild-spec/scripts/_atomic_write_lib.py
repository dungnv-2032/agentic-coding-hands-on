#!/usr/bin/env python3
"""_atomic_write_lib.py -- the tmp+os.replace crash-safe write path shared by every
migrate-registry step that scaffolds or reshapes a spec in place.

Extracted (phase-09, plans/260824-1846-rebuild-spec-action-self-sufficiency-v27-8,
correction X2) from `_a3_b4_scaffold_lib.py` before that module was deleted:
`_atomic_write` was imported by two OTHER live steps --
`_a3_screens_step_lib.py` and `_doc_migration_screen_sot_step_lib.py` -- so deleting
the scaffold module outright would have been an immediate `ImportError` in both. This
module exists solely to give the function a home neither of its real importers owns,
so retiring `a3-b4` never touches the write path two other steps depend on for
crash-safe writes. Behavior is byte-identical to the function it was extracted from --
verified by the extraction's own direct test, `test_atomic_write_lib.py`.

Stdlib only.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path


def _atomic_write(path: Path, text: str) -> None:
    """tmp + os.replace, matching `scaffold_spec.py::_atomic_write_text`'s precedent."""
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
