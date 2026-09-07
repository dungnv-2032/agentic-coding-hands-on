"""Tests for STATE_SCHEMA_VERSION lockstep with _stack_profile_lib.SCHEMA_VERSION.

Phase 01 (state-schema-version-lockstep): build_source_to_fcode.py used to redeclare
STATE_SCHEMA_VERSION as its own literal, which drifted from _stack_profile_lib.SCHEMA_VERSION
(the single source of truth also consumed by detect_stack_profile.py). These tests prove the
writer now imports the constant instead of shadowing it, and that the imported value genuinely
reaches the emitted `.rebuild-state.json` artifact — not just the module attribute.

Do not assert the literal string "22.1.0" (or any other version literal) anywhere below: that
would recreate the exact drift class this phase exists to kill. Assert only against
_stack_profile_lib.SCHEMA_VERSION.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import _stack_profile_lib  # noqa: E402
import build_source_to_fcode  # noqa: E402

PYTHON = sys.executable


class TestWriterConstantIsTheLibConstant:
    def test_writer_constant_is_the_lib_constant(self):
        """STATE_SCHEMA_VERSION must be the SAME object as _stack_profile_lib.SCHEMA_VERSION,
        not a separately-declared literal that merely happens to be equal today.

        Assert both `is` and `==`: a re-declared literal that copies the current value would
        still pass an `==`-only check (and, depending on string interning, might even pass
        `is` by luck), while an aliased import guarantees identity regardless of interning.
        """
        assert build_source_to_fcode.STATE_SCHEMA_VERSION is _stack_profile_lib.SCHEMA_VERSION
        assert build_source_to_fcode.STATE_SCHEMA_VERSION == _stack_profile_lib.SCHEMA_VERSION


class TestEmittedStateFileCarriesCurrentSchemaVersion:
    def test_emitted_state_file_carries_current_schema_version(self, tmp_path):
        """Run the real writer end-to-end on a tmp_path and read back the emitted
        `.rebuild-state.json` — proves the constant actually reaches the write path at
        the `state_data["schema_version"] = STATE_SCHEMA_VERSION` line, not merely that the
        module attribute holds the right value.
        """
        specs_root = tmp_path / "features"
        specs_root.mkdir(parents=True, exist_ok=True)
        state_out = tmp_path / ".rebuild-state.json"
        index_out = tmp_path / "_source-to-fcode.json"

        result = subprocess.run(
            [
                PYTHON,
                str(_SCRIPTS_DIR / "build_source_to_fcode.py"),
                "--specs-root", str(specs_root),
                "--state-out", str(state_out),
                "--index-out", str(index_out),
                "--mode", "full",
                # Bypass the git dependency entirely (RT-F4 stamping is orthogonal to the
                # SHA resolution path) so this test is deterministic in any environment.
                "--last-rebuild-sha", "0" * 40,
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode == 0, (
            f"build_source_to_fcode.py exited {result.returncode}; stderr={result.stderr}"
        )

        written_state = json.loads(state_out.read_text(encoding="utf-8"))
        assert written_state["schema_version"] == _stack_profile_lib.SCHEMA_VERSION
