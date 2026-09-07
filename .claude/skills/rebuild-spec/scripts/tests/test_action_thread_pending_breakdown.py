"""Tests for `_action_thread_pending_breakdown_lib.py` (phase 07,
plans/260824-1846-rebuild-spec-action-self-sufficiency-v27-8): the structured
pending breakdown, the D13 dispatched-action-id set, and the `[HANDOFF]`
summary text. Nothing here writes a sidecar -- that is the step lib's job
(`test_doc_migration_action_thread_step.py`).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import _action_thread_fill_guard_lib as guard_lib  # noqa: E402
import _action_thread_pending_breakdown_lib as lib  # noqa: E402
from _action_thread_reopen_lib import REOPEN_RULE_IDS  # noqa: E402

_ROOT = _SCRIPTS_DIR.parent  # claude/skills/rebuild-spec -- a stable, real project_root
_CORPORA = _TESTS_DIR / "fixtures" / "corpora" / "action-thread-shapes"
_MISSING_DIAGRAM = _CORPORA / "F953_MissingDiagram"
_CLEAN_MIGRATED = _CORPORA / "F950_CleanMigrated"
_BACKFILL_PENDING = _TESTS_DIR / "fixtures" / "action_thread" / "backfill-pending"
assert _MISSING_DIAGRAM.is_dir(), f"committed fixture missing: {_MISSING_DIAGRAM}"
assert _CLEAN_MIGRATED.is_dir(), f"committed fixture missing: {_CLEAN_MIGRATED}"
assert _BACKFILL_PENDING.is_dir(), f"committed fixture missing: {_BACKFILL_PENDING}"


def _copy_feature(src: Path, dst: Path) -> Path:
    dst.mkdir(parents=True)
    for name in ("technical-spec.md", "functional-spec.md"):
        (dst / name).write_text((src / name).read_text(encoding="utf-8"), encoding="utf-8")
    return dst


def _graduated_backfill_dir(dst: Path) -> Path:
    """`backfill-pending` with a **State** rung inserted by hand (test data, never
    composer logic) so `state_rung_missing` no longer fires -- the same derivation
    `test_doc_migration_action_thread_step.py::_graduated_backfill_text` uses,
    inlined here so this file has no cross-test-module import."""
    dst.mkdir(parents=True)
    text = (_BACKFILL_PENDING / "technical-spec.md").read_text(encoding="utf-8")
    old = "**Result** · `listings.state` flips `pending` → `approved`.\n**Source:**"
    new = (
        "**Result** · `listings.state` flips `pending` → `approved`.\n"
        "**State** · `listings.state`: `pending` → `approved`.\n**Source:**"
    )
    assert old in text, "fixture shape changed -- update this derivation"
    (dst / "technical-spec.md").write_text(text.replace(old, new), encoding="utf-8")
    (dst / "functional-spec.md").write_text(
        (_BACKFILL_PENDING / "functional-spec.md").read_text(encoding="utf-8"), encoding="utf-8",
    )
    return dst


class TestBuildBreakdown:
    def test_rule_id_counts_key_set_always_equals_reopen_rule_ids(self, tmp_path):
        # C1's generalization, requirement 6: the breakdown can never count a
        # rule_id the reopen registry doesn't know, nor omit one it does --
        # true even on a feature with NOTHING firing.
        feature_dir = _copy_feature(_CLEAN_MIGRATED, tmp_path / "F950_CleanMigrated")
        breakdown = lib.build_breakdown(feature_dir, _ROOT)
        assert set(breakdown["rule_id_counts"]) == set(REOPEN_RULE_IDS)

    def test_counts_come_from_the_real_validator_not_grep(self, tmp_path):
        feature_dir = _copy_feature(_MISSING_DIAGRAM, tmp_path / "F953_MissingDiagram")
        breakdown = lib.build_breakdown(feature_dir, _ROOT)
        counts = breakdown["rule_id_counts"]
        assert counts["FeatureSpec.state_rung_missing"] == 5  # A2,A3,A4,A5,A9
        assert counts["FeatureSpec.diagram_required_missing"] == 1  # A9
        assert counts["FeatureSpec.crosscutting_unlabelled"] == 1
        assert counts["FeatureSpec.rule_bin_misplaced"] == 0
        assert breakdown["unverified_tag_count"] == 3

    def test_diagram_count_is_independent_of_the_unverified_proxy(self, tmp_path):
        # Requirement 2's own non-vacuity proof: resolve every [UNVERIFIED] marker
        # (the composer-only fill-pending signal) while leaving A9's missing
        # diagram untouched -- the diagram count must still fire. A count that
        # only ever tracked unverified_tag_count > 0 would silently read 0 here.
        feature_dir = _copy_feature(_MISSING_DIAGRAM, tmp_path / "F953_NoMarkers")
        tech_path = feature_dir / "technical-spec.md"
        text = tech_path.read_text(encoding="utf-8")
        resolved = text.replace("[UNVERIFIED] no resolvable owner — needs a researcher pass", "")
        assert resolved.count("[UNVERIFIED]") == 0
        assert resolved != text
        tech_path.write_text(resolved, encoding="utf-8")

        breakdown = lib.build_breakdown(feature_dir, _ROOT)

        assert breakdown["unverified_tag_count"] == 0
        assert breakdown["rule_id_counts"]["FeatureSpec.diagram_required_missing"] > 0

    def test_unverified_tag_counts_the_tag_not_one_sentence(self, tmp_path):
        # C14, made un-repeatable: F953's 3 unresolved rules are all the DEC "no
        # resolvable owner" sentence -- zero hits for the BR "carried from
        # **Applies to:**" sentence. Counting only the latter would read 0 here.
        feature_dir = _copy_feature(_MISSING_DIAGRAM, tmp_path / "F953_MissingDiagram")
        text = (feature_dir / "technical-spec.md").read_text(encoding="utf-8")
        assert text.count("[UNVERIFIED] carried from **Applies to:**") == 0
        assert text.count("[UNVERIFIED] no resolvable owner") == 3

        breakdown = lib.build_breakdown(feature_dir, _ROOT)

        assert breakdown["unverified_tag_count"] == 3


class TestDispatchedActionIds:
    def test_maps_each_finding_to_its_enclosing_action_block(self, tmp_path):
        feature_dir = _copy_feature(_MISSING_DIAGRAM, tmp_path / "F953_MissingDiagram")
        dispatched = lib.dispatched_action_ids(feature_dir, _ROOT)
        # state_rung_missing: A2,A3,A4,A5,A9; diagram_required_missing: A9 (already
        # in the set); crosscutting_unlabelled sits in § 4.4, outside every § 3
        # action block, so it contributes nothing on its own; [UNVERIFIED] always
        # lives in § 4.4 Bin 3's A0 entry, so its presence adds "A0".
        assert dispatched == frozenset({"A2", "A3", "A4", "A5", "A9", "A0"})

    def test_empty_when_nothing_is_pending(self, tmp_path):
        feature_dir = _graduated_backfill_dir(tmp_path / "F999_Graduated")
        assert lib.dispatched_action_ids(feature_dir, _ROOT) == frozenset()

    def test_returns_a_frozenset(self, tmp_path):
        feature_dir = _copy_feature(_MISSING_DIAGRAM, tmp_path / "F953_MissingDiagram")
        assert isinstance(lib.dispatched_action_ids(feature_dir, _ROOT), frozenset)


class TestDispatchedActionIdsInteropWithTheWaveGate:
    """D13 end-to-end: prove `dispatched_action_ids`'s output is directly usable
    as `_action_thread_fill_guard_lib.evaluate_fill`'s `allowed_actions` --
    not just format-compatible by assumption, but actually accepted/enforced by
    the real guard phase 04 shipped."""

    def _post_with_state_rung_added_to_a2(self, pre_text: str) -> str:
        old = (
            "**Result** · UPDATE `listings` state, approval_count — `state` literal from "
            "submitted param; `approval_count` derived as current+1; UPDATE `listings` "
            "state — literal from submitted param\n**Source:**"
        )
        new = (
            "**Result** · UPDATE `listings` state, approval_count — `state` literal from "
            "submitted param; `approval_count` derived as current+1; UPDATE `listings` "
            "state — literal from submitted param\n"
            "**State** · `listings.state`: `approval_pending` → `approved`/`approval_rejected`.\n"
            "**Source:**"
        )
        assert old in pre_text, "fixture shape changed -- update this derivation"
        return pre_text.replace(old, new)

    def test_a_dispatched_action_may_have_its_rungs_changed(self, tmp_path):
        """REGRESSION GUARD for the release's headline workflow.

        Phase 07 discovered this as a real defect and recorded it
        `xfail(strict=True)` because `_action_thread_fill_guard_lib.py` was
        outside its ownership. It has since been FIXED (see that module's
        `_skeleton`): the rung region is now DROPPED rather than sentinelled
        per label, because rungs are the declared editable surface and adding
        an absent rung is the sanctioned edit.

        Un-xfailed deliberately, per the original marker's own instruction
        ("must be un-xfailed, not silently forgotten") -- and kept as a live
        assertion, because if this ever reverts again, resolving the 95
        `state_rung_missing` findings becomes impossible at the wave gate and
        the whole release's core capability is silently dead. Its negative twin
        below (`test_an_undispatched_action_may_not_...`) proves the fix did not
        simply disable the guard.
        """
        feature_dir = _copy_feature(_MISSING_DIAGRAM, tmp_path / "F953_MissingDiagram")
        pre = (feature_dir / "technical-spec.md").read_text(encoding="utf-8")
        dispatched = lib.dispatched_action_ids(feature_dir, _ROOT)
        assert "A2" in dispatched
        post = self._post_with_state_rung_added_to_a2(pre)

        result = guard_lib.evaluate_fill(pre, post, _ROOT, allowed_actions=dispatched)

        assert result.must_revert is False, result.all_violations

    def test_an_undispatched_action_may_not_have_its_rungs_changed(self, tmp_path):
        feature_dir = _copy_feature(_MISSING_DIAGRAM, tmp_path / "F953_MissingDiagram")
        pre = (feature_dir / "technical-spec.md").read_text(encoding="utf-8")
        post = self._post_with_state_rung_added_to_a2(pre)
        narrow_dispatch = frozenset({"A3"})  # A2 deliberately excluded

        result = guard_lib.evaluate_fill(pre, post, _ROOT, allowed_actions=narrow_dispatch)

        assert result.must_revert is True
        assert any("A2" in v for v in result.scope)


class TestSummarize:
    def test_summarize_breakdown_lists_only_nonzero_counts(self):
        breakdown = {
            "unverified_tag_count": 3,
            "rule_id_counts": {
                "FeatureSpec.state_rung_missing": 5,
                "FeatureSpec.action_ref_unglossed": 0,
                "FeatureSpec.diagram_required_missing": 1,
                "FeatureSpec.rule_bin_misplaced": 0,
                "FeatureSpec.crosscutting_unlabelled": 1,
            },
        }
        line = lib.summarize_breakdown("F953_MissingDiagram", breakdown)
        assert line == (
            "feature=F953_MissingDiagram unverified=3 state_rung_missing=5 "
            "diagram_required_missing=1 crosscutting_unlabelled=1"
        )

    def test_summarize_breakdown_reports_nothing_pending(self):
        breakdown = {
            "unverified_tag_count": 0,
            "rule_id_counts": {rid: 0 for rid in REOPEN_RULE_IDS},
        }
        assert lib.summarize_breakdown("F001_Clean", breakdown) == (
            "feature=F001_Clean nothing pending"
        )

    def test_summarize_breakdowns_aggregates_totals_and_lists_each_feature(self, tmp_path):
        f953 = _copy_feature(_MISSING_DIAGRAM, tmp_path / "F953_MissingDiagram")
        f950 = _copy_feature(_CLEAN_MIGRATED, tmp_path / "F950_CleanMigrated")
        pairs = [
            (f953.name, lib.build_breakdown(f953, _ROOT)),
            (f950.name, lib.build_breakdown(f950, _ROOT)),
        ]
        summary = lib.summarize_breakdowns(pairs)
        assert summary.startswith("pending breakdown totals: ")
        assert "unverified=6" in summary  # 3 + 3
        assert "state_rung_missing=5" in summary
        assert "feature=F953_MissingDiagram" in summary
        assert "feature=F950_CleanMigrated" in summary

    def test_summarize_breakdowns_empty_input_is_empty_string(self):
        assert lib.summarize_breakdowns([]) == ""
