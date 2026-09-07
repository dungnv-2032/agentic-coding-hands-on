"""Tests for the `state_staleness` block added to `detect_stack_profile.py` (Phase 03,
state-schema `schema_version` lockstep).

`sys.path` already has scripts/ on it (see conftest.py), so this file imports
`detect_stack_profile` directly for in-process calls to `detect()` -- the fastest way to
exercise `_state_staleness` against a real `docs/.rebuild-state.json` fixture without paying
subprocess overhead for every case. The one test that guards the additive-output contract
(`test_existing_output_keys_unchanged`) runs through the CLI via subprocess, mirroring the
`_run` convention in `test_detect_stack_profile_ui_sniff.py`, so it exercises the real stdout
JSON contract exactly as the orchestrator (SKILL.md Preflight) consumes it.

`required` is built from the imported `SCHEMA_VERSION` constant in every test that needs it --
never hardcoded -- so this suite cannot itself reintroduce the drift Phase 01 killed.
"""
from __future__ import annotations

import json
import pytest
import subprocess
import sys
from pathlib import Path

import detect_stack_profile as dsp

SCRIPT = Path(dsp.__file__)

# Pre-existing top-level keys `detect()` returned before this phase's additive
# `state_staleness` key -- see detect_stack_profile.py:248-263.
_PRE_EXISTING_KEYS = {
    "schema_version",
    "root",
    "matched",
    "recommended_profile",
    "confidence",
    "encoding",
    "detected_language_heading",
    "components",
    "component_profile",
    "auto_switch",
    "auto_switch_reason",
    "shared",
    "ui_sniff",
    "warnings",
}


def _run(root: Path, extra: list[str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root)] + (extra or []),
        capture_output=True, text=True, timeout=60, cwd=str(root),
    )


def _write_state(root: Path, payload) -> None:
    docs = root / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / ".rebuild-state.json").write_text(json.dumps(payload))


def _detect(root: Path) -> dict:
    return dsp.detect(str(root), file_cap=50_000, sample_cap=5)


class TestStateStaleness:
    def test_stale_when_state_below_current(self, tmp_path):
        _write_state(tmp_path, {"schema_version": "21.0.0"})
        out = _detect(tmp_path)
        block = out["state_staleness"]
        assert block["stale"] is True
        assert block["found"] == "21.0.0"
        assert block["required"] == dsp.SCHEMA_VERSION
        assert block["state_present"] is True

    def test_not_stale_when_state_equals_current(self, tmp_path):
        _write_state(tmp_path, {"schema_version": dsp.SCHEMA_VERSION})
        out = _detect(tmp_path)
        block = out["state_staleness"]
        assert block["stale"] is False, "the equality boundary must NOT fire -- over-firing bug"
        assert block["found"] == dsp.SCHEMA_VERSION
        assert block["required"] == dsp.SCHEMA_VERSION

    def test_not_stale_when_state_absent(self, tmp_path):
        # No docs/.rebuild-state.json at all -- greenfield first run.
        out = _detect(tmp_path)
        block = out["state_staleness"]
        assert block["state_present"] is False
        assert block["stale"] is False, "a first run has no checkpoint to invalidate"
        assert block["found"] is None

    def test_stale_when_key_missing(self, tmp_path):
        # Valid JSON, valid state file, but no schema_version key -- pre-profile legacy state.
        _write_state(tmp_path, {"last_rebuild_sha": "a" * 40})
        out = _detect(tmp_path)
        block = out["state_staleness"]
        assert block["state_present"] is True
        assert block["stale"] is True
        assert block["found"] is None

    def test_stale_when_state_corrupt(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir(parents=True, exist_ok=True)
        (docs / ".rebuild-state.json").write_bytes(b"\x00\x01not-json{{{")
        out = _detect(tmp_path)  # must not raise
        block = out["state_staleness"]
        assert block["state_present"] is True
        assert block["stale"] is True
        assert block["found"] is None

    def test_semver_compared_numerically_not_lexically(self, tmp_path):
        # "9.0.0" > "22.1.0" as STRINGS ("9" > "2" lexically) -- a naive `found < required`
        # string comparison would read this as fresh. Numeric comparison must catch it.
        _write_state(tmp_path, {"schema_version": "9.0.0"})
        out = _detect(tmp_path)
        block = out["state_staleness"]
        assert block["found"] == "9.0.0"
        assert block["required"] == dsp.SCHEMA_VERSION
        assert block["stale"] is True, (
            "9.0.0 must compare numerically BELOW the current schema; a lexical string "
            "comparison would wrongly report this as fresh"
        )


class TestSemverWidthAsymmetry:
    def test_equal_schema_written_with_fewer_components_is_not_stale(self, tmp_path):
        # A stamp naming the SAME schema with fewer components ("22.1" vs "22.1.0") must not
        # read as older. Bare tuple comparison makes the shorter equal-prefix tuple smaller,
        # so (22,1) < (22,1,0) would wrongly report stale. Derive the truncated form from the
        # constant -- never hardcode it, or this test carries the drift it exists to prevent.
        parts = dsp.SCHEMA_VERSION.split(".")
        if len(parts) < 3 or parts[-1] != "0":
            pytest.skip(f"SCHEMA_VERSION {dsp.SCHEMA_VERSION!r} has no trailing-zero component to drop")
        truncated = ".".join(parts[:-1])

        _write_state(tmp_path, {"schema_version": truncated})
        block = _detect(tmp_path)["state_staleness"]
        assert block["found"] == truncated
        assert block["stale"] is False, (
            f"{truncated!r} names the same schema as {dsp.SCHEMA_VERSION!r}; zero-padding must "
            "make them compare equal rather than treating the shorter tuple as older"
        )


class TestExistingOutputKeysUnchanged:
    def test_existing_output_keys_unchanged(self, tmp_path):
        (tmp_path / "README.txt").write_text("hello")
        r = _run(tmp_path)
        assert r.returncode == 0, r.stderr
        out = json.loads(r.stdout)

        missing = _PRE_EXISTING_KEYS - out.keys()
        assert not missing, f"pre-existing keys dropped from stdout contract: {missing}"
        assert "state_staleness" in out, "new additive key must be present"
        assert out["schema_version"] == dsp.SCHEMA_VERSION
