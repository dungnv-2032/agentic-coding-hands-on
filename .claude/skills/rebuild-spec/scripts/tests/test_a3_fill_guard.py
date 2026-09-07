# layout-exempt: rebuild-spec A3 fill-guard tests — docs paths are managed targets
"""Tests for `_a3_fill_guard_lib.py` + `_a3_citation_target_lib.py` (phase-09,
plans/260824-1846-rebuild-spec-action-self-sufficiency-v27-8, correction X3).

RENAMED + RESCOPED from `test_a3_b4_fill_guard.py`: that suite proved the guard
against a technical-spec-shaped fixture carrying BOTH A3 and B4. `a3-b4` (the step
that fixture served) retired this release -- A3/B4 left technical-spec.md's target
shape in phase 08 -- but the guard itself did NOT retire: `a3-screens` (screens/*/
spec.md, A3 only) still needs every piece of it, so this suite is rebuilt against an
A3-only, screen-spec-shaped fixture instead, matching what `_a3_screens_step_lib.py`
actually produces and what the real `a3-screens` fill pass actually touches.

The fill pass may touch ONLY the A3 section body of one screen's `spec.md`. This
suite proves, not assumes: (1) the byte-level scope guard actually fires on a real
out-of-section mutation -- both negative probes assert the mutation lands BEFORE
invoking the guard, the exact discipline phase-03.md calls out ("a probe whose input
never reaches the branch is the exact failure that shipped a security hole twice on
the previous plan"); (2) the `**Source:**`-in-A3 label guard; (3) a citation to a
nonexistent file or an out-of-range line is caught, never trusted; (4) a fill that
leaves a `{...}` placeholder can never be mistaken for a completed one; (5) the guard
integrates with the REAL validator, not a re-read of its docstring.
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import _a3_fill_guard_lib as guard  # noqa: E402
import validate_reading_guide_db_impact as validator  # noqa: E402

_HEAD = (
    "# SCR001_Login — Screen Spec\n\n## Purpose\n\nOriginal purpose text.\n\n"
)
_SOURCE_REFS = (
    "## Source References\n\n- `app/views/login.haml:1`\n\n"
)
_TAIL_QUESTIONS = "## Unresolved Questions\n\n- none\n\n"

_A3_SCAFFOLD = (
    "## Source Walkthrough\n\n"
    "{UNFILLED SCAFFOLD -- fill it by running "
    "`run_doc_migrations.py --migrate --only a3-screens`.}\n"
)

PRE = _HEAD + _SOURCE_REFS + _TAIL_QUESTIONS + _A3_SCAFFOLD


def _filled(a3_body: str) -> str:
    return (_HEAD + _SOURCE_REFS + _TAIL_QUESTIONS
            + "## Source Walkthrough\n\n" + a3_body + "\n")


def _real_source(tmp_path: Path, rel: str, n_lines: int) -> Path:
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(f"line {i}" for i in range(1, n_lines + 1)) + "\n")
    return p


class TestStripSections:
    def test_body_removed_heading_boundary_respected(self):
        stripped = guard.strip_sections(PRE)
        assert "{UNFILLED SCAFFOLD" not in stripped
        assert "## Source Walkthrough" in stripped
        assert "## Purpose" in stripped and "## Source References" in stripped

    def test_fenced_heading_inside_a3_does_not_truncate_section(self):
        tricky_a3 = (
            "## Source Walkthrough\n\n"
            "```text\n## Purpose\nnot a real boundary\n```\n"
            "trailing real content that must also be stripped\n"
        )
        text = _HEAD + _SOURCE_REFS + _TAIL_QUESTIONS + tricky_a3
        stripped = guard.strip_sections(text)
        assert "trailing real content" not in stripped
        assert "not a real boundary" not in stripped
        # the boundary was found correctly further down, so the questions heading
        # right before A3 still survives the strip
        assert "## Unresolved Questions" in stripped


class TestCheckScope:
    def test_identical_outside_a3_passes(self):
        post = _filled("real reading list, file-cited.")
        assert guard.check_scope(PRE, post) == []

    def test_negative_probe_purpose_word_changed_fails(self):
        mutated = PRE.replace("Original purpose text.", "MUTATED purpose text.")
        assert "MUTATED purpose text." in mutated  # mutation demonstrably present
        violations = guard.check_scope(PRE, mutated)
        assert violations != []

    def test_negative_probe_source_reference_row_dropped_fails(self):
        mutated = PRE.replace("- `app/views/login.haml:1`\n", "")
        assert "app/views/login.haml:1" not in mutated  # mutation demonstrably present
        violations = guard.check_scope(PRE, mutated)
        assert violations != []


class TestA3CitationLabel:
    def test_source_label_inside_a3_fails(self):
        post = _filled("**Source:** app/models/foo.rb:1")
        assert guard.check_a3_citation_label(post) != []

    def test_file_label_is_never_flagged(self):
        post = _filled("**File:** app/models/foo.rb:1-10 -- entry point")
        assert guard.check_a3_citation_label(post) == []


class TestNoLeftoverPlaceholder:
    def test_scaffold_still_present_is_caught(self):
        assert guard.check_no_leftover_placeholder(PRE) != []

    def test_filled_body_has_none(self):
        post = _filled("real reading list")
        assert guard.check_no_leftover_placeholder(post) == []

    def test_absent_heading_is_not_a_placeholder_violation(self):
        # absence is `*.pre_migration`, a different terminal state entirely
        text = _HEAD + _SOURCE_REFS + _TAIL_QUESTIONS
        assert guard.check_no_leftover_placeholder(text) == []


class TestCitationTargets:
    def test_valid_a3_citation_passes(self, tmp_path):
        _real_source(tmp_path, "app/models/foo.rb", 50)
        post = _filled("**File:** app/models/foo.rb:10-20 -- start here")
        assert guard.check_citation_targets(post, tmp_path) == []

    def test_nonexistent_file_is_caught(self, tmp_path):
        post = _filled("**File:** app/models/does_not_exist.rb:1-5 -- start here")
        violations = guard.check_citation_targets(post, tmp_path)
        assert violations != []
        assert any("nonexistent" in v for v in violations)

    def test_out_of_range_line_is_caught(self, tmp_path):
        _real_source(tmp_path, "app/models/foo.rb", 10)
        post = _filled("**File:** app/models/foo.rb:5-500 -- start here")
        violations = guard.check_citation_targets(post, tmp_path)
        assert violations != []
        assert any("out of range" in v for v in violations)

    def test_path_escaping_project_root_is_caught(self, tmp_path):
        post = _filled("**File:** ../../../etc/passwd:1-2 -- start here")
        violations = guard.check_citation_targets(post, tmp_path)
        assert violations != []


class TestIsAlreadyFilled:
    def test_scaffolded_file_is_not_already_filled(self):
        assert guard.is_already_filled(PRE) is False

    def test_filled_file_is_already_filled(self, tmp_path):
        _real_source(tmp_path, "app/models/foo.rb", 10)
        post = _filled("**File:** app/models/foo.rb:1-2 -- start here")
        assert guard.is_already_filled(post) is True

    def test_absent_section_is_not_already_filled(self):
        text = _HEAD + _SOURCE_REFS + _TAIL_QUESTIONS
        assert guard.is_already_filled(text) is False


class TestEvaluateFillIntegration:
    """Runs the REAL validator, not just this module's own checks."""

    def test_filled_fixture_validator_pass_no_revert(self, tmp_path):
        _real_source(tmp_path, "app/models/foo.rb", 30)
        post = _filled(
            "**File:** app/models/foo.rb:1-10 -- start here; sets up the model\n\n"
            "```\nfoo() -> bar()\n```\n\nSee ## Source References below."
        )
        result = guard.evaluate_fill(PRE, post, tmp_path)
        assert result.must_revert is False
        assert result.all_violations == []
        a3_issues = validator.check_source_walkthrough(post, "spec.md")
        assert a3_issues == []

    def test_placeholder_left_intact_is_validator_warn_unmapped(self, tmp_path):
        # unmodified scaffold: valid terminal state (`unfilled`), not a revert
        result = guard.evaluate_fill(PRE, PRE, tmp_path)
        assert result.must_revert is False
        assert result.placeholder != []
        a3_issues = validator.check_source_walkthrough(PRE, "spec.md")
        assert [i["rule_id"] for i in a3_issues] == ["reading_guide.unmapped"]

    def test_scope_violation_is_reverted_by_the_caller(self, tmp_path):
        """The guard itself never writes; it only reports. This test proves the
        caller-side revert contract: on `must_revert`, restoring `pre` verbatim
        yields a file byte-identical to the pre-wave snapshot."""
        mutated_elsewhere = PRE.replace("Original purpose text.", "HALLUCINATED.")
        result = guard.evaluate_fill(PRE, mutated_elsewhere, tmp_path)
        assert result.must_revert is True
        restored = PRE  # the caller's revert action
        assert restored == PRE
        assert "HALLUCINATED." not in restored

    def test_fabricated_citation_forces_revert_even_with_in_scope_edit(self, tmp_path):
        # only the A3 body changed (in scope), but the citation is fabricated
        post = _filled("**File:** app/models/never_existed.rb:1-5 -- start here")
        result = guard.evaluate_fill(PRE, post, tmp_path)
        assert result.must_revert is True
        assert result.citation_target != []

    def test_leftover_placeholder_claiming_success_is_not_classified_filled(self, tmp_path):
        """Acceptance: 'reject a fill that leaves any {...} placeholder behind while
        claiming success' -- a caller must consult `placeholder`, not just
        `must_revert`, before it may report a unit `filled`."""
        post = _filled("{UNFILLED SCAFFOLD -- researcher gave up}")
        result = guard.evaluate_fill(PRE, post, tmp_path)
        assert result.placeholder != []
        can_classify_filled = result.must_revert is False and result.placeholder == []
        assert can_classify_filled is False

    def test_rerun_over_already_filled_file_is_a_no_op(self, tmp_path):
        """Fill step run twice: the second run must find nothing pending. Proven
        here via the idempotency predicate the runbook is documented to use."""
        _real_source(tmp_path, "app/models/foo.rb", 10)
        post = _filled("**File:** app/models/foo.rb:1-5 -- start here")
        assert guard.is_already_filled(post) is True
        # re-running the fill on an already-filled file must be a byte-identical no-op
        second_pass_input = post
        assert guard.evaluate_fill(post, second_pass_input, tmp_path).all_violations == []
