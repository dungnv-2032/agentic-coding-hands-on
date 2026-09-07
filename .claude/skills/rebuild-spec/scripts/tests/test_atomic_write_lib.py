# layout-exempt: rebuild-spec atomic-write tests — docs paths are managed targets
"""Tests for `_atomic_write_lib.py` (phase-09,
plans/260824-1846-rebuild-spec-action-self-sufficiency-v27-8, correction X2).

`_atomic_write` is the tmp+`os.replace` write path two live migrate steps
(`_a3_screens_step_lib.py`, `_doc_migration_screen_sot_step_lib.py`) depend on for
crash-safe writes -- a partial-write regression here corrupts user corpora, so this
suite tests the extracted module directly rather than relying solely on its callers'
own tests: (1) a fresh file is written correctly; (2) an existing file is fully
replaced, never appended or partially overwritten; (3) the write is atomic -- no
`.tmp` sibling survives a successful write; (4) a write failure cleans up its temp
file and leaves the original target untouched; (5) both real callers still import and
use this exact function (no drifted duplicate).
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import _atomic_write_lib as lib  # noqa: E402


class TestAtomicWrite:
    def test_writes_a_fresh_file(self, tmp_path):
        target = tmp_path / "spec.md"
        lib._atomic_write(target, "hello world\n")
        assert target.read_text(encoding="utf-8") == "hello world\n"

    def test_fully_replaces_existing_content(self, tmp_path):
        target = tmp_path / "spec.md"
        target.write_text("old content that must not survive\n", encoding="utf-8")
        lib._atomic_write(target, "new content\n")
        assert target.read_text(encoding="utf-8") == "new content\n"

    def test_no_tmp_sibling_survives_a_successful_write(self, tmp_path):
        target = tmp_path / "spec.md"
        lib._atomic_write(target, "content\n")
        leftovers = [p for p in tmp_path.iterdir() if p.name != "spec.md"]
        assert leftovers == [], f"unexpected leftover file(s): {leftovers}"

    def test_write_failure_cleans_up_the_tmp_file_and_leaves_target_untouched(self, tmp_path):
        target = tmp_path / "spec.md"
        target.write_text("original\n", encoding="utf-8")

        with mock.patch("os.replace", side_effect=OSError("disk full")):
            with pytest.raises(OSError):
                lib._atomic_write(target, "would-be new content\n")

        assert target.read_text(encoding="utf-8") == "original\n"
        leftovers = [p for p in tmp_path.iterdir() if p.name != "spec.md"]
        assert leftovers == [], f"a failed write left a temp file behind: {leftovers}"

    def test_real_callers_import_the_same_function(self):
        """Regression guard: both live steps must import THIS function, never a
        second, hand-rolled copy that could silently drift from it."""
        import _a3_screens_step_lib as a3_screens
        import _doc_migration_screen_sot_step_lib as screen_sot

        assert a3_screens._atomic_write is lib._atomic_write
        assert screen_sot._atomic_write is lib._atomic_write
