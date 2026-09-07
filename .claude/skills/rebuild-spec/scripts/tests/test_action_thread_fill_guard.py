"""Tests for `_action_thread_fill_guard_lib.py` -- the action-thread fill-pass
runtime anti-rewrite guard (phase 04,
plans/260824-1846-rebuild-spec-action-self-sufficiency-v27-8).

Covers, in order: (1) the six adversarial `check_scope`/`evaluate_fill`
post-states the phase's own risk assessment names as merge blockers, each with
a non-vacuity proof for its revert case; (2) `check_owner_plausibility` against
a real § 2 Action Index; (3) a guard-too-strict regression -- `pre == post`
against every committed, real (never hand-authored) `action-thread-shapes/`
corpus fixture must return zero violations, or the fill pass could never
complete; (4) purity of `_action_thread_reopen_lib.needs_reopen` across
working directories; (5) the four newly registered `REOPEN_RULE_IDS` members
(`action_ref_unglossed`, `diagram_required_missing`, `rule_bin_misplaced`,
`crosscutting_unlabelled`) each demonstrably reopening a file that fires only
that one detector.

STEP-1 GREP RESULT (requirement 3, phase-04.md): grepped `validate_feature_spec.
py` for an existing check that a `Used in:`-claimed action id actually exists
in § 2 -- ABSENT. `action_unclaimed` (§ 2 -> § 3/§ 4 declared-vs-claimed) and
`rule_bin_misplaced`/`crosscutting_unlabelled` (bin PLACEMENT, never id
EXISTENCE) are the only neighbours; none of them checks the reverse direction.
`check_owner_plausibility` in `_action_thread_owner_plausibility_lib.py` is net
new, not a duplicate.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import _action_thread_fill_guard_lib as g  # noqa: E402
import _action_thread_reopen_lib as reopen_lib  # noqa: E402

_TESTS_DIR = Path(__file__).resolve().parent
_CORPUS = _TESTS_DIR / "fixtures" / "corpora" / "action-thread-shapes"
_CORPUS_FEATURES = (
    "F950_CleanMigrated", "F951_UnresolvedRules", "F952_NoActionsData", "F953_MissingDiagram",
)
for _name in _CORPUS_FEATURES:
    assert (_CORPUS / _name / "technical-spec.md").is_file(), f"committed fixture missing: {_name}"


# --------------------------------------------------------------------------- #
# A clean, hand-built, action-thread-shaped base that fires NONE of the five
# REOPEN_RULE_IDS members -- proven below (TestGuardTooStrict). Same pattern
# `test_rule_bins.py`/`test_action_ref_unglossed.py` already use for scope-
# isolated fixtures; each check-scope test mutates ONE thing off this base.
# --------------------------------------------------------------------------- #
_BASE = """# F901_GuardProbe — Technical Spec

## 1. Technical Overview

Overview text.

## 2. Action Index

| # | Action (handler) | Method · Path | Codes | Writes | Detail |
|---|---|---|---|---|---|
| **A0** | *cross-cutting — belongs to no single action* | — | FR-601 | — | § 4.4 |
| **A1** | `WidgetsController#index` | `GET` `.../widgets` | FR-101, US101 | — *(read-only)* | § 3.1 |
| **A2** | `WidgetsController#update` | `PATCH` `.../update` | FR-102 | `widgets` | § 3.1 |
| **A3** | `WidgetsController#close` | `PATCH` `.../close` | FR-103, BR-001 | `widgets` | § 3.1 |

## 3. Actions

### 3.1 CAP-01 — Manage widgets

#### A1 · List widgets

`GET .../widgets` → `WidgetsController#index`
`FR-101` `US101`

**Who** · Admin
**Result** · read-only — **no DB write**.
**Source:** `widgets_controller.rb:5-10`

#### A2 · Update a widget

`PATCH .../update` → `WidgetsController#update`
`FR-102`

**Who** · Admin
**Result** · updates `widgets.state`.
**Source:** `widgets_controller.rb:12-18`

#### A3 · Close a widget

`PATCH .../close` → `WidgetsController#close`
`BR-001` `FR-103`

**Who** · Admin
**Rule** · **BR-001** A widget cannot be closed twice — the service checks `widget.closed?`
before applying any column change.
**Result** · updates `widgets.state`.
**Source:** `widgets_controller.rb:20-25`

## 4. Shared Foundation

### 4.1 Components

None.

### 4.2 Data Model

None.

### 4.3 State Management

None.

### 4.4 Shared Rules

#### Bin 3 — cross-cutting, belongs to no single action

**FR-601** applies globally: every widget action requires an admin session.

### 4.5 Algorithms & Integrations

None.

### 4.6 Configuration

None.
"""


def _write(tmp_path: Path, text: str, name: str = "F901_GuardProbe") -> Path:
    feature_dir = tmp_path / "features" / name
    feature_dir.mkdir(parents=True)
    (feature_dir / "technical-spec.md").write_text(text, encoding="utf-8")
    return feature_dir


# --------------------------------------------------------------------------- #
# The six adversarial post-states (phase-04.md step 3) -- each a merge-blocker
# risk per the phase's own risk assessment.
# --------------------------------------------------------------------------- #
class TestCheckScopeSixAdversarialCases:
    def test_1_rung_body_changed_is_allowed(self):
        post = _BASE.replace(
            "**Result** · updates `widgets.state`.\n**Source:** `widgets_controller.rb:12-18`",
            "**Result** · updates `widgets.state` and clears `widgets.cache_key`.\n"
            "**Source:** `widgets_controller.rb:12-18`",
        )
        assert g.check_scope(_BASE, post) == []
        assert g.evaluate_fill(_BASE, post, Path(".")).must_revert is False

    def test_2_a_different_actions_rung_body_also_changed_must_revert(self, monkeypatch):
        # A2's rung resolved (the intended edit) AND A1's rung ALSO rewritten --
        # the dangerous shape: an LLM scoped to one action rewriting another.
        # The unit's DISPATCHED scope is what makes A1 out of bounds, so this
        # test must declare it; without a declared scope there is nothing to be
        # "outside of". See `check_scope`'s "WHY A SET AND NOT A COUNT".
        post = _BASE.replace(
            "**Result** · updates `widgets.state`.\n**Source:** `widgets_controller.rb:12-18`",
            "**Result** · updates `widgets.state` and clears `widgets.cache_key`.\n"
            "**Source:** `widgets_controller.rb:12-18`",
        ).replace(
            "**Result** · read-only — **no DB write**.",
            "**Result** · read-only — no DB write of any kind, ever.",
        )
        violations = g.check_scope(_BASE, post, frozenset({"A2"}))
        assert violations, "must revert: A1 changed but only A2 was dispatched"
        assert "A1" in violations[0]

        # Non-vacuity: with `_changed_action_blocks` weakened to see nothing,
        # the out-of-scope violation disappears -- proving THIS test depends on
        # that specific guard, not on the (unrelated) skeleton check.
        monkeypatch.setattr(g, "_changed_action_blocks", lambda pre, post: [])
        assert (
            g.check_scope(_BASE, post, frozenset({"A2"})) == []
        ), "weakened guard should have missed this"

    def test_2a_one_for_one_swap_is_caught_though_a_count_bound_would_miss_it(self):
        """The case the original `len(changed) > 1` bound let straight through:
        the unit was dispatched to fill A2 and instead edited ONLY A1. Exactly
        one block changes, so a count bound sees nothing wrong. A dispatched-set
        bound reverts it. This is why the set is strictly stronger, not merely
        more permissive."""
        post = _BASE.replace(
            "**Result** · read-only — **no DB write**.",
            "**Result** · read-only — no DB write of any kind, ever.",
        )
        assert len(g._changed_action_blocks(_BASE, post)) == 1, "must be a 1-block change"
        violations = g.check_scope(_BASE, post, frozenset({"A2"}))
        assert violations, "must revert: A1 edited, A2 dispatched"
        assert "A1" in violations[0]

    def test_2b_multi_action_fill_is_allowed_when_all_are_dispatched(self):
        """Per-feature dispatch is the REAL granularity
        (`references/pipeline-migrate.md:56` -- "One researcher unit = ONE
        feature"; phase 07 requirement 2 clones it). A feature with pending
        rungs in two actions changes two blocks on a perfectly honest fill, and
        that must NOT revert -- otherwise every real wave reverts and the fill
        pass can never complete (phase 04's own High/High risk)."""
        post = _BASE.replace(
            "**Result** · updates `widgets.state`.\n**Source:** `widgets_controller.rb:12-18`",
            "**Result** · updates `widgets.state` and clears `widgets.cache_key`.\n"
            "**Source:** `widgets_controller.rb:12-18`",
        ).replace(
            "**Result** · read-only — **no DB write**.",
            "**Result** · read-only — no DB write of any kind, ever.",
        )
        assert len(g._changed_action_blocks(_BASE, post)) == 2
        assert g.check_scope(_BASE, post, frozenset({"A1", "A2"})) == []
        assert (
            g.evaluate_fill(_BASE, post, Path("."), frozenset({"A1", "A2"})).must_revert
            is False
        )

    def test_3_h4_heading_renamed_must_revert(self, monkeypatch):
        post = _BASE.replace(
            "#### A2 · Update a widget", "#### A2 · Update a widget (renamed)",
        )
        violations = g.check_scope(_BASE, post)
        assert violations, "must revert: a heading is outside the editable surface"

        # Non-vacuity: with `_skeleton` weakened to a constant, no heading
        # difference can ever be seen, and no rung CONTENT changed either
        # (only the heading text did) -- so `_changed_action_blocks` alone
        # also finds nothing. Proves this case depends on `_skeleton`.
        monkeypatch.setattr(g, "_skeleton", lambda text: "")
        assert g.check_scope(_BASE, post) == [], "weakened guard should have missed this"

    def test_4_section2_codes_cell_edited_must_revert(self, monkeypatch):
        post = _BASE.replace(
            "| **A2** | `WidgetsController#update` | `PATCH` `.../update` | FR-102 | `widgets` | § 3.1 |",
            "| **A2** | `WidgetsController#update` | `PATCH` `.../update` | FR-102, FR-999 | `widgets` | § 3.1 |",
        )
        violations = g.check_scope(_BASE, post)
        assert violations, "must revert: § 2's table is outside the editable surface"

        monkeypatch.setattr(g, "_skeleton", lambda text: "")
        assert g.check_scope(_BASE, post) == [], "weakened guard should have missed this"

    def test_5_mermaid_fence_inserted_in_the_right_bucket_is_allowed(self):
        post = _BASE.replace(
            "### 3.1 CAP-01 — Manage widgets\n\n#### A1",
            "### 3.1 CAP-01 — Manage widgets\n\n```mermaid\nsequenceDiagram\n"
            "Admin->>WidgetsController: PATCH update\n```\n\n#### A1",
        )
        assert g.check_scope(_BASE, post) == []
        assert g.evaluate_fill(_BASE, post, Path(".")).must_revert is False

    def test_6_used_in_names_a_nonexistent_action_must_revert(self, monkeypatch, tmp_path):
        # § 2's index stops at A3 -- a `Used in:` list naming A99 is implausible.
        post = _BASE.replace(
            "#### Bin 3 — cross-cutting, belongs to no single action",
            "#### Bin 2 — used by ≥2 named actions\n\n"
            "**BR-777 — a shared rule.**\nUsed in: A2, A99\n"
            "**Source:** `widgets_service.rb:1-5`\n\n"
            "#### Bin 3 — cross-cutting, belongs to no single action",
        )
        result = g.evaluate_fill(_BASE, post, tmp_path)
        assert result.must_revert is True
        assert any("A99" in v for v in result.owner_plausibility)
        # check_scope alone must be silent here -- § 4.4 paragraphs are
        # declared editable; only owner_plausibility catches this case.
        assert g.check_scope(_BASE, post) == []

        # Non-vacuity: weaken check_owner_plausibility to a no-op and confirm
        # the guard would then have missed this entirely.
        monkeypatch.setattr(g, "check_owner_plausibility", lambda *a, **k: [])
        assert g.evaluate_fill(_BASE, post, tmp_path).must_revert is False, (
            "weakened guard should have missed this"
        )


# --------------------------------------------------------------------------- #
# Guard-too-strict regression -- pre == post on real corpus fixtures must
# never revert, or the fill pass can never complete (phase-04.md risk table).
# --------------------------------------------------------------------------- #
class TestGuardIsNotTooStrict:
    def test_base_fixture_fires_no_reopen_rule_id(self, tmp_path):
        fd = _write(tmp_path, _BASE)
        assert reopen_lib.firing_reopen_rule_ids(fd, tmp_path) == frozenset()

    def test_pre_equals_post_is_zero_violations_on_every_real_corpus_fixture(self):
        for name in _CORPUS_FEATURES:
            text = (_CORPUS / name / "technical-spec.md").read_text(encoding="utf-8")
            result = g.evaluate_fill(text, text, _CORPUS)
            assert result.must_revert is False, (name, result.all_violations)


# --------------------------------------------------------------------------- #
# check_owner_plausibility against a real § 2 Action Index
# --------------------------------------------------------------------------- #
class TestCheckOwnerPlausibility:
    def test_every_used_in_id_present_in_index_is_silent(self):
        rows = [{"id": "A0"}, {"id": "A1"}, {"id": "A2"}, {"id": "A3"}]
        text = "Used in: A2, A3\n"
        from _action_thread_owner_plausibility_lib import check_owner_plausibility
        assert check_owner_plausibility(text, rows) == []

    def test_an_id_outside_the_index_is_flagged_by_line_number(self):
        rows = [{"id": "A0"}, {"id": "A1"}]
        text = "intro\nUsed in: A1, A9\n"
        from _action_thread_owner_plausibility_lib import check_owner_plausibility
        violations = check_owner_plausibility(text, rows)
        assert len(violations) == 1
        assert "line 2" in violations[0] and "'A9'" in violations[0]


# --------------------------------------------------------------------------- #
# Purity of `_action_thread_reopen_lib.needs_reopen` -- same inputs, different
# process working directories, identical answer (F1: path-based, not text-
# based, and never sensitive to the caller's cwd).
# --------------------------------------------------------------------------- #
class TestNeedsReopenPurityAcrossWorkingDirectories:
    def test_identical_result_from_two_different_cwds(self, tmp_path):
        feature_dir = _write(tmp_path, _BASE).resolve()
        root = tmp_path.resolve()
        other_cwd = feature_dir  # any real, unrelated directory works
        original_cwd = os.getcwd()
        try:
            os.chdir(str(root))
            from_root = reopen_lib.firing_reopen_rule_ids(feature_dir, root)
            os.chdir(str(other_cwd))
            from_feature_dir = reopen_lib.firing_reopen_rule_ids(feature_dir, root)
        finally:
            os.chdir(original_cwd)
        assert from_root == from_feature_dir == frozenset()


# --------------------------------------------------------------------------- #
# Job 3 / D7 -- the four newly registered detectors, each proven to reopen a
# file that fires ONLY it (phase-04.md step 6, the "dead-gate" merge blocker).
# --------------------------------------------------------------------------- #
class TestFourNewlyRegisteredDetectorsReopen:
    def test_action_ref_unglossed_reopens_alone(self, tmp_path):
        post = _BASE.replace(
            "`FR-101` `US101`\n\n**Who** · Admin\n**Result** · read-only",
            "`FR-101` `US101` `DEC-001`\n\n**Who** · Admin\n**Result** · read-only",
        )
        fd = _write(tmp_path, post)
        assert reopen_lib.firing_reopen_rule_ids(fd, tmp_path) == frozenset(
            {"FeatureSpec.action_ref_unglossed"}
        )
        assert reopen_lib.needs_reopen(fd, tmp_path) is True

    def test_diagram_required_missing_reopens_alone(self, tmp_path):
        post = _BASE.replace(
            "| **A2** | `WidgetsController#update` | `PATCH` `.../update` | FR-102 | `widgets` | § 3.1 |",
            "| **A2** | `WidgetsController#update` | `PATCH` `.../update` | FR-102 | `widgets, orders` | § 3.1 |",
        )
        fd = _write(tmp_path, post)
        assert reopen_lib.firing_reopen_rule_ids(fd, tmp_path) == frozenset(
            {"FeatureSpec.diagram_required_missing"}
        )
        assert reopen_lib.needs_reopen(fd, tmp_path) is True

    def test_rule_bin_misplaced_reopens_alone(self, tmp_path):
        post = _BASE.replace(
            "**Who** · Admin\n**Rule** · **BR-001** A widget cannot be closed twice — "
            "the service checks `widget.closed?`\nbefore applying any column change.\n"
            "**Result** · updates `widgets.state`.\n**Source:** `widgets_controller.rb:20-25`",
            "**Who** · Admin\n**Rule** · **BR-001** A widget cannot be closed twice — "
            "the service checks `widget.closed?`\nbefore applying any column change.\n"
            "Used in: A2, A3\n**Result** · updates `widgets.state`.\n"
            "**Source:** `widgets_controller.rb:20-25`",
        )
        fd = _write(tmp_path, post)
        assert reopen_lib.firing_reopen_rule_ids(fd, tmp_path) == frozenset(
            {"FeatureSpec.rule_bin_misplaced"}
        )
        assert reopen_lib.needs_reopen(fd, tmp_path) is True

    def test_crosscutting_unlabelled_reopens_alone(self, tmp_path):
        post = _BASE.replace(
            "### 4.4 Shared Rules\n\n#### Bin 3",
            "### 4.4 Shared Rules\n\n**BR-002** applies without a clear single owner.\n\n#### Bin 3",
        )
        fd = _write(tmp_path, post)
        assert reopen_lib.firing_reopen_rule_ids(fd, tmp_path) == frozenset(
            {"FeatureSpec.crosscutting_unlabelled"}
        )
        assert reopen_lib.needs_reopen(fd, tmp_path) is True


def test_reopen_lib_still_delegates_to_the_validator_not_a_second_predicate():
    """D7/F1 sanity, scoped to this phase's own change: registering four new
    rule_ids must not have tempted a second, locally-computed predicate."""
    source = (SCRIPTS_DIR / "_action_thread_reopen_lib.py").read_text(encoding="utf-8")
    assert "validate_feature_spec._check_feature_dir" in source
    assert "_action_thread_lib" not in source
    assert "_action_thread_diagram_lib" not in source
