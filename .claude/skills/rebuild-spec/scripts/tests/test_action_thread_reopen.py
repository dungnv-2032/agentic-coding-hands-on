"""Tests for `_action_thread_reopen_lib.py` -- the generalized reopen predicate
(C1, D7/F1), plans/260824-1846-rebuild-spec-action-self-sufficiency-v27-8, phase 02.

The mandated invocation contract (D7/F1): `needs_reopen`/`firing_reopen_rule_ids`
must ONLY ever filter `validate_feature_spec._check_feature_dir`'s own issue list --
never re-implement or approximate a firing predicate. This file proves that
contract three ways: (1) `needs_reopen` actually fires on the `backfill-pending`
fixture built for C1's reproduction; (2) a brand-new, never-seen-before dummy
rule_id reopens a file the moment it is appended to `REOPEN_RULE_IDS`, with zero
other edit; (3) breaking/faking `_check_feature_dir` FROM the test (monkeypatch,
never a file edit) moves `needs_reopen`'s answer in lockstep -- if it didn't, the
firing logic would have forked from the detector, which is exactly what D7 forbids.
"""
from __future__ import annotations

import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import _action_thread_reopen_lib as reopen_lib  # noqa: E402
import validate_feature_spec  # noqa: E402

_FIXTURES = _TESTS_DIR / "fixtures" / "action_thread"
_BACKFILL_PENDING = _FIXTURES / "backfill-pending"
_CLEAN_MIGRATED = (
    _TESTS_DIR / "fixtures" / "corpora" / "action-thread-shapes" / "F950_CleanMigrated"
)
assert _BACKFILL_PENDING.is_dir(), f"committed fixture missing: {_BACKFILL_PENDING}"
assert _CLEAN_MIGRATED.is_dir(), f"committed fixture missing: {_CLEAN_MIGRATED}"


# --------------------------------------------------------------------------- #
# Grep-provable anti-duplication (F1): the invocation contract in source, not
# merely in a docstring's promise.
# --------------------------------------------------------------------------- #
def test_reopen_lib_imports_validator_not_action_thread_parsers():
    source = (_SCRIPTS_DIR / "_action_thread_reopen_lib.py").read_text(encoding="utf-8")
    assert "import validate_feature_spec" in source
    assert "_action_thread_lib" not in source
    assert "_action_thread_diagram_lib" not in source


# --------------------------------------------------------------------------- #
# needs_reopen / firing_reopen_rule_ids against real fixtures
# --------------------------------------------------------------------------- #
def test_needs_reopen_true_on_the_backfill_pending_fixture():
    # The exact shape C1 closes: already Action-Index-shaped, zero [UNVERIFIED]
    # markers, a real SM-### block, a writing action, no State rung.
    assert reopen_lib.needs_reopen(_BACKFILL_PENDING, _FIXTURES) is True
    assert reopen_lib.firing_reopen_rule_ids(_BACKFILL_PENDING, _FIXTURES) == frozenset(
        {"FeatureSpec.state_rung_missing"}
    )


def test_needs_reopen_false_on_a_clean_graduated_file_with_no_sm_block():
    # [C1 regression guard] F950_CleanMigrated models no state machine at all
    # (`### 4.3 State Management` is `None.`) -- `state_rung_missing` never fires
    # on it regardless of what it writes. A file where NOTHING in REOPEN_RULE_IDS
    # fires must never be reopened.
    assert reopen_lib.needs_reopen(_CLEAN_MIGRATED, _FIXTURES) is False
    assert reopen_lib.firing_reopen_rule_ids(_CLEAN_MIGRATED, _FIXTURES) == frozenset()


# --------------------------------------------------------------------------- #
# Generality proof (a): a brand-new dummy detector reopens with ZERO edit to
# this module's functions beyond appending its rule_id.
# --------------------------------------------------------------------------- #
def test_registering_a_dummy_detector_reopens_with_no_other_edit(monkeypatch):
    monkeypatch.setattr(
        reopen_lib, "REOPEN_RULE_IDS", (*reopen_lib.REOPEN_RULE_IDS, "FeatureSpec._dummy_probe"),
    )
    real_check = validate_feature_spec._check_feature_dir

    def _fake_check(feature_dir, root):
        return [*real_check(feature_dir, root),
                {"rule_id": "FeatureSpec._dummy_probe", "severity": "warning",
                 "message": "dummy", "location": {"file": "x", "line": 1}}]

    monkeypatch.setattr(validate_feature_spec, "_check_feature_dir", _fake_check)

    # F950 fires nothing registered on its own -- the dummy alone must now flip it.
    assert reopen_lib.needs_reopen(_CLEAN_MIGRATED, _FIXTURES) is True
    assert "FeatureSpec._dummy_probe" in reopen_lib.firing_reopen_rule_ids(
        _CLEAN_MIGRATED, _FIXTURES,
    )


# --------------------------------------------------------------------------- #
# Generality proof (b): "moves in step" -- breaking/faking the validator's OWN
# check (monkeypatch, never a file edit) moves needs_reopen's answer in lockstep.
# If it didn't, the reopen predicate would have forked from the detector.
# --------------------------------------------------------------------------- #
def test_needs_reopen_moves_in_lockstep_when_the_underlying_check_is_muted(monkeypatch):
    assert reopen_lib.needs_reopen(_BACKFILL_PENDING, _FIXTURES) is True  # baseline: fires

    monkeypatch.setattr(validate_feature_spec, "_check_feature_dir", lambda *a, **k: [])

    assert reopen_lib.needs_reopen(_BACKFILL_PENDING, _FIXTURES) is False  # moved with it


def test_needs_reopen_moves_in_lockstep_when_the_underlying_check_starts_firing(monkeypatch):
    assert reopen_lib.needs_reopen(_CLEAN_MIGRATED, _FIXTURES) is False  # baseline: silent

    monkeypatch.setattr(
        validate_feature_spec, "_check_feature_dir",
        lambda *a, **k: [{"rule_id": "FeatureSpec.state_rung_missing", "severity": "warning",
                           "message": "forced", "location": {"file": "x", "line": 1}}],
    )

    assert reopen_lib.needs_reopen(_CLEAN_MIGRATED, _FIXTURES) is True  # moved with it
