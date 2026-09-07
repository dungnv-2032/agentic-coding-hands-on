"""Runbook-lockstep guard for the `action-thread` auto fill-pass (phase 07,
plans/260824-1846-rebuild-spec-action-self-sufficiency-v27-8, requirement 4).

Mirrors `test_confidence_report_functional_spec_exclusion.py`'s shape: parse the REAL
`references/pipeline-migrate.md` prose (never a hardcoded copy of it) and assert it
names `_action_thread_fill_guard_lib` and every rule_id
`_action_thread_pending_breakdown_lib`/`_action_thread_reopen_lib.REOPEN_RULE_IDS`
actually emits. Without this, the orchestrator runbook and the guard/breakdown code
can drift apart silently -- a rule_id the code counts but the runbook never mentions
is dispatched-set protection that exists in code but that no operator reading the
runbook would ever know to rely on.

Per the phase's own instruction, this test was written and watched RED (the prose
did not yet exist) BEFORE `references/pipeline-migrate.md` gained the `## Fill
fan-out` / `## Prompt contract` / `## The wave gate` / `## Idempotency` / `##
Handoff` subsections under the `action-thread` step -- see the phase report for the
literal failure this file produced pre-authoring.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from _action_thread_reopen_lib import REOPEN_RULE_IDS  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[5]  # agent-kit/
PIPELINE_MIGRATE = REPO_ROOT / "claude/skills/rebuild-spec/references/pipeline-migrate.md"

# The rule_id SHORT names (the part after "FeatureSpec.") the breakdown emits --
# imported from the SAME registry the breakdown module keys off of (D7/C1: never a
# second, hand-copied list), so this guard cannot itself drift from the code it
# protects.
REQUIRED_RULE_IDS: tuple[str, ...] = tuple(rid.rsplit(".", 1)[-1] for rid in REOPEN_RULE_IDS)

_ACTION_THREAD_HEADING_RE = re.compile(r"^## The `action-thread` step\b")


def extract_action_thread_section(pipeline_text: str) -> str:
    """The `action-thread` step's own section: from its H2 heading through (but
    excluding) the next H2 heading. Bounded by heading TEXT, never a fixed line
    range, so an edit anywhere else in the file never desyncs this -- and never
    reads into `a3-b4`'s or `--rollback STEP`'s own sections, which this phase
    must not disturb."""
    lines = pipeline_text.splitlines()
    h2_idx = [i for i, ln in enumerate(lines) if ln.startswith("## ")]
    start = next((i for i in h2_idx if _ACTION_THREAD_HEADING_RE.match(lines[i])), None)
    if start is None:
        return ""
    later = [i for i in h2_idx if i > start]
    end = later[0] if later else len(lines)
    return "\n".join(lines[start:end])


def assert_section_is_non_vacuous(section_text: str) -> None:
    """A guard that silently matched nothing (heading renamed, section emptied)
    protects nothing -- MUST fail loudly rather than pass on an accidental empty
    string, same discipline `test_confidence_report_functional_spec_exclusion.py`
    already applies to its own discovery step."""
    assert len(section_text.splitlines()) > 10, (
        "the action-thread section extracted 10 lines or fewer -- extraction is "
        "almost certainly broken, not the section genuinely thin"
    )


def assert_section_names_the_guard_and_every_rule_id(section_text: str) -> None:
    """The load-bearing single-section assertion, reused by the negative probes."""
    assert "_action_thread_fill_guard_lib" in section_text, (
        "the action-thread section must name `_action_thread_fill_guard_lib` -- "
        "the wave gate the runbook instructs the orchestrator to call"
    )
    missing = [rid for rid in REQUIRED_RULE_IDS if rid not in section_text]
    assert not missing, (
        f"the action-thread section never names rule_id(s) {missing} -- the "
        "breakdown counts them but the runbook never tells an operator they exist"
    )


class TestRealRunbookSection:
    def test_action_thread_section_is_non_vacuous(self):
        text = PIPELINE_MIGRATE.read_text(encoding="utf-8")
        section = extract_action_thread_section(text)
        assert_section_is_non_vacuous(section)

    def test_action_thread_section_names_the_guard_and_every_rule_id(self):
        text = PIPELINE_MIGRATE.read_text(encoding="utf-8")
        section = extract_action_thread_section(text)
        assert_section_names_the_guard_and_every_rule_id(section)

    def test_section_never_reaches_into_the_rollback_section(self):
        # File-ownership guard: this phase must not disturb `--rollback STEP`'s own
        # section (a3-b4's/a3-screens' sections are earlier in the file and are
        # bounded out structurally by starting the scan at the action-thread
        # heading itself).
        text = PIPELINE_MIGRATE.read_text(encoding="utf-8")
        section = extract_action_thread_section(text)
        assert "## `--rollback STEP`" not in section


class TestNonVacuityProbes:
    """Prove the guard actually goes red -- deleting the mention it depends on must
    fail the check, not silently pass."""

    def test_missing_guard_mention_is_caught(self):
        regressed = (
            "## The `action-thread` step\n\n"
            "The wave gate calls the fill guard after each unit completes: "
            "state_rung_missing, action_ref_unglossed, diagram_required_missing, "
            "rule_bin_misplaced, crosscutting_unlabelled.\n"
        )
        with pytest.raises(AssertionError):
            assert_section_names_the_guard_and_every_rule_id(regressed)

    @pytest.mark.parametrize("rule_id", REQUIRED_RULE_IDS)
    def test_missing_one_rule_id_is_caught(self, rule_id):
        other_ids = [r for r in REQUIRED_RULE_IDS if r != rule_id]
        regressed = (
            "## The `action-thread` step\n\n"
            "`_action_thread_fill_guard_lib.evaluate_fill` runs the wave gate; "
            f"registered rule_ids: {', '.join(other_ids)}.\n"
        )
        with pytest.raises(AssertionError):
            assert_section_names_the_guard_and_every_rule_id(regressed)

    def test_empty_section_fails_non_vacuity(self):
        with pytest.raises(AssertionError):
            assert_section_is_non_vacuous("")

    def test_heading_not_found_yields_empty_section(self):
        assert extract_action_thread_section("## Something else entirely\n\nprose\n") == ""
