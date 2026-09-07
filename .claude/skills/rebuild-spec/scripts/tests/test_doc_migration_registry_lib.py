"""Tests for `_doc_migration_registry_lib.py` -- phase-01 of
plans/260818-0758-rebuild-spec-post-migration-completion. Pure registry/driver
mechanics: fixture `StepSpec`s stand in for the real per-phase step bodies (P02/P06/
P08 wire those separately), so these tests exercise ordering, prerequisite gating,
the `needs_llm_fill`/`not_implemented` fail-closed overrides, and `Tally` reuse in
isolation, with no real docs corpus involved.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import _doc_migration_registry_lib as reg  # noqa: E402
from _audience_split_tally_lib import ALREADY, FAILED, INERT, PROGRESS  # noqa: E402

_NOWHERE = Path("/nonexistent-does-not-matter")


def _spec(name, prerequisite, *, pending=0, category=PROGRESS, message="ok",
          needs_llm_fill=False, not_implemented=False, calls=None):
    """A fixture StepSpec whose count_pending/run are constants -- *calls* (a list),
    if given, records every `run()` invocation so a test can assert it was/wasn't
    called (e.g. a refused step's `run` must never fire)."""

    def _count_pending(_d, _p, _f):
        return pending

    def _run(_d, _p, _f):
        if calls is not None:
            calls.append(name)
        return reg.StepResult(category=category, message=message,
                               needs_llm_fill=needs_llm_fill, not_implemented=not_implemented)

    return reg.StepSpec(name=name, prerequisite=prerequisite,
                         count_pending=_count_pending, run=_run)


# --------------------------------------------------------------------------- #
# STEP_ORDER / StepRegistry wiring
# --------------------------------------------------------------------------- #
def test_step_order_is_the_fixed_seven_step_chain():
    # phase-06 (human-readable-SOT plan) inserted "screen-sot" between "a3-screens"
    # and "mirror-skew"; phase-10 inserted "feature-sot" between "screen-sot" and
    # "mirror-skew"; phase-07 (capability-map plan) inserted "cap-map" between
    # "feature-sot" and "mirror-skew"; phase-06 (action-thread-v27-7 plan,
    # plans/260824-1128-rebuild-spec-action-thread-v27-7) inserted "action-thread"
    # between "cap-map" and "mirror-skew"; phase-09 (action-self-sufficiency-v27-8
    # plan) RETIRED the "a3-b4" step entirely -- A3/B4 left technical-spec.md's
    # target shape in phase 08, leaving it nothing left to scaffold -- and
    # repointed "a3-screens"'s own prerequisite from "a3-b4" straight to
    # "audience-split".
    assert reg.STEP_ORDER == (
        "audience-split", "a3-screens", "screen-sot", "feature-sot", "cap-map",
        "action-thread", "mirror-skew",
    )


def test_register_rejects_a_name_outside_step_order():
    registry = reg.StepRegistry()
    with pytest.raises(ValueError):
        registry.register(_spec("not-a-real-step", None))


def test_register_rejects_prerequisite_not_yet_registered():
    registry = reg.StepRegistry()
    with pytest.raises(ValueError):
        registry.register(_spec("a3-screens", "audience-split"))  # audience-split not registered yet


def test_get_unknown_step_raises_unknown_step_error():
    registry = reg.StepRegistry()
    registry.register(_spec("audience-split", None))
    with pytest.raises(reg.UnknownStepError):
        registry.get("a3-screens")


def test_names_returns_canonical_step_order_not_insertion_order():
    registry = reg.StepRegistry()
    registry.register(_spec("audience-split", None))
    registry.register(_spec("mirror-skew", None))  # out of dependency order on purpose
    assert registry.names() == ("audience-split", "mirror-skew")


# --------------------------------------------------------------------------- #
# make_stub_step -- a real, safe seam, never a NotImplementedError trap
# --------------------------------------------------------------------------- #
def test_stub_step_count_pending_is_a_nonzero_sentinel_and_never_writes():
    step = reg.make_stub_step("a3-screens", "audience-split", owner_phase="P02")
    assert step.count_pending(_NOWHERE, _NOWHERE, None) == 1


def test_stub_step_run_reports_inert_and_not_implemented():
    step = reg.make_stub_step("a3-screens", "audience-split", owner_phase="P02")
    result = step.run(_NOWHERE, _NOWHERE, None)
    assert result.category == INERT
    assert result.not_implemented is True
    assert "P02" in result.message


def test_not_implemented_line_format():
    assert reg.not_implemented_line("a3-screens", "detail") == "[NOT-IMPLEMENTED] step=a3-screens -- detail"


def test_handoff_line_format():
    assert (reg.handoff_line("a3-screens", "detail")
            == "[HANDOFF] step=a3-screens needs_llm_fill=true -- detail")


# --------------------------------------------------------------------------- #
# prerequisite_pending / preview -- read-only, writes nothing
# --------------------------------------------------------------------------- #
def test_prerequisite_pending_zero_when_step_has_no_prerequisite():
    registry = reg.StepRegistry()
    registry.register(_spec("audience-split", None, pending=5))
    step = registry.get("audience-split")
    assert reg.prerequisite_pending(registry, step, _NOWHERE, _NOWHERE, None) == 0


def test_prerequisite_pending_reads_the_prerequisites_own_count():
    registry = reg.StepRegistry()
    registry.register(_spec("audience-split", None, pending=3))
    registry.register(_spec("a3-screens", "audience-split", pending=0))
    step = registry.get("a3-screens")
    assert reg.prerequisite_pending(registry, step, _NOWHERE, _NOWHERE, None) == 3


def test_preview_reports_pending_and_blocked_status_without_calling_run():
    calls: list[str] = []
    registry = reg.StepRegistry()
    registry.register(_spec("audience-split", None, pending=2, calls=calls))
    registry.register(_spec("a3-screens", "audience-split", pending=0, calls=calls))
    lines = reg.preview(registry, reg.STEP_ORDER[:2], _NOWHERE, _NOWHERE, None)
    assert lines == [
        "[DRY-RUN] step=audience-split pending=2 prerequisite=none status=ready",
        "[DRY-RUN] step=a3-screens pending=0 prerequisite=audience-split status=blocked",
    ]
    assert calls == [], "preview() must never call a step's run()"


# --------------------------------------------------------------------------- #
# execute -- prerequisite refusal, needs_llm_fill/not_implemented overrides, Tally
# --------------------------------------------------------------------------- #
def test_execute_refuses_a_step_whose_prerequisite_is_still_pending(capsys):
    calls: list[str] = []
    registry = reg.StepRegistry()
    registry.register(_spec("audience-split", None, pending=4, calls=calls))
    registry.register(_spec("a3-screens", "audience-split", pending=0, category=PROGRESS, calls=calls))
    exit_code, tally = reg.execute(registry, ("a3-screens",), _NOWHERE, _NOWHERE, None)
    assert "a3-screens" not in calls, "a refused step must never have its run() called"
    assert exit_code == 4
    assert tally.inert == 1
    assert "[REFUSED]" in capsys.readouterr().err


def test_execute_needs_llm_fill_forces_inert_even_though_category_is_progress():
    registry = reg.StepRegistry()
    registry.register(_spec("audience-split", None, pending=0, category=PROGRESS,
                             needs_llm_fill=True))
    exit_code, tally = reg.execute(registry, ("audience-split",), _NOWHERE, _NOWHERE, None)
    assert exit_code == 4, "a needs_llm_fill step can never read as a complete (exit 0) run"
    assert tally.inert == 1 and tally.progress == 0


def test_execute_prints_handoff_line_for_needs_llm_fill(capsys):
    registry = reg.StepRegistry()
    registry.register(_spec("audience-split", None, pending=0, category=PROGRESS,
                             needs_llm_fill=True, message="wrote scaffold"))
    reg.execute(registry, ("audience-split",), _NOWHERE, _NOWHERE, None)
    assert "[HANDOFF] step=audience-split needs_llm_fill=true -- wrote scaffold" in capsys.readouterr().out


def test_execute_failed_outranks_inert_exit_1():
    registry = reg.StepRegistry()
    registry.register(_spec("audience-split", None, pending=0, category=FAILED))
    registry.register(_spec("a3-screens", "audience-split", pending=0, category=INERT))
    exit_code, tally = reg.execute(registry, reg.STEP_ORDER[:2], _NOWHERE, _NOWHERE, None)
    assert exit_code == 1
    assert tally.failed == 1 and tally.inert == 1


def test_execute_all_already_exits_0():
    registry = reg.StepRegistry()
    registry.register(_spec("audience-split", None, pending=0, category=ALREADY))
    exit_code, tally = reg.execute(registry, ("audience-split",), _NOWHERE, _NOWHERE, None)
    assert exit_code == 0
    assert tally.already == 1 and tally.failed == 0 and tally.inert == 0

