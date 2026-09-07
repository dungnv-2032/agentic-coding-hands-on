# layout-exempt: rebuild-spec a3-screens tests — docs paths are managed targets
"""Tests for `_a3_screens_step_lib.py` + the `a3-screens` registry entry (phase-08,
plans/260818-0758-rebuild-spec-post-migration-completion; prerequisite + guard-import
updates phase-09, plans/260824-1846-rebuild-spec-action-self-sufficiency-v27-8).

Originally a SECOND APPLICATION of the mechanism P02/P03 proved on
`features/*/technical-spec.md` -- phase-08.md was explicit that any need to edit
`_a3_b4_scaffold_lib.py`, `_a3_b4_fill_guard_lib.py`, or
`validate_reading_guide_db_impact.py` was a P01 design finding, not a workaround.
That first application, the `a3-b4` step, retired in phase 09 (A3/B4 left
technical-spec.md's target shape in phase 08, leaving it nothing left to scaffold) --
`a3-screens` is this mechanism's one surviving application now, its own prerequisite
repointed straight to `audience-split`, and its guard imports repointed to the
renamed, A3-only `_a3_fill_guard_lib.py`. This suite still proves the substitution
holds: same brace-placeholder shape (WARN, never CRITICAL -- verified against the REAL
validator, not assumed from CORRECTION 2's table), same fence-aware presence predicate
reused by import, and B4 absent from the screens family by construction (there is no
B4 reference anywhere in the module under test).
"""
from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import _a3_fill_guard_lib as fill_guard  # noqa: E402
from _spec_constants import A3_HEADING  # noqa: E402
from validate_reading_guide_db_impact import _section_body  # noqa: E402
import _a3_screens_step_lib as lib  # noqa: E402
import _doc_migration_registry_lib as registry  # noqa: E402
import validate_reading_guide_db_impact as validator  # noqa: E402

_BASE = (
    "# SCR001_Login — Screen Spec\n\n## Purpose\n\nLogin form.\n\n"
    "## Source References\n\n- `app/views/login.haml:1`\n"
)

_SCRATCH = Path(
    "/tmp/claude-1208602877/-home-pham-van-duc-sun-asterisk-com-github-agent-kit/"
    "dbcca1a0-49d6-4fd9-ab62-4fd3e94147d6/scratchpad"
)
_POST_SRC = _SCRATCH / "e2e7" / "docs"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fingerprint(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)): _sha(p) for p in sorted(root.rglob("*")) if p.is_file()}


class TestScaffoldTextA3Only:
    def test_missing_a3_appends_it(self):
        out = lib.scaffold_text(_BASE)
        assert out is not None
        assert "## Source Walkthrough" in out

    def test_never_appends_b4(self):
        out = lib.scaffold_text(_BASE)
        assert out is not None
        assert "## DB Impact per Event" not in out
        assert "DB Impact" not in out

    def test_already_has_a3_returns_none(self):
        filled = _BASE + "\n## Source Walkthrough\n\nreal content\n"
        assert lib.scaffold_text(filled) is None

    def test_fenced_heading_is_treated_as_absent_and_scaffolded(self):
        fenced = _BASE + "\n```\n## Source Walkthrough\n\nnot real\n```\n"
        out = lib.scaffold_text(fenced)
        assert out is not None
        assert out.count("## Source Walkthrough") == 2

    def test_scaffold_never_contains_fabrication_markers(self):
        """Checks the APPENDED block only -- `_BASE` itself legitimately cites a
        `.haml` source file in its (pre-existing) Source References section."""
        out = lib.scaffold_text(_BASE)
        assert out is not None
        appended = out[len(_BASE):]
        for token in ("**File:**", "**Source:**", ".rb", ".haml"):
            assert token not in appended, f"scaffold leaked a fabrication marker: {token!r}"

    def test_placeholder_names_the_correct_step_not_a3_b4(self):
        """The scaffold text must NOT reuse `_a3_b4_scaffold_lib.A3_BLOCK` verbatim --
        that block's fill command is `--only a3-b4`, the wrong step for a screen
        spec. Regression guard for the exact bug caught during implementation."""
        out = lib.scaffold_text(_BASE)
        assert "--only a3-screens" in out
        assert "--only a3-b4" not in out


class TestPresencePredicateIdentity:
    def test_reuses_validators_section_body_not_a_reimplementation(self):
        assert lib._section_body is validator._section_body


class TestValidatorIntegration:
    """The verification gate: run the REAL validator against scaffolded text."""

    def test_scaffold_grades_warning_unmapped_never_critical(self):
        out = lib.scaffold_text(_BASE)
        issues = validator.check_source_walkthrough(out, "f")
        assert [i["rule_id"] for i in issues] == ["reading_guide.unmapped"]
        assert [i["severity"] for i in issues] == ["warning"]

    def test_negative_probe_empty_a3_body_is_critical(self):
        """Proves the test CAN detect the failure our real block avoids."""
        mutated = _BASE + "\n## Source Walkthrough\n\n"
        issues = validator.check_source_walkthrough(mutated, "f")
        assert issues[0]["severity"] == "critical"
        assert issues[0]["rule_id"] == "reading_guide.malformed"

    def test_filled_screen_spec_passes_clean(self):
        filled = (
            _BASE + "\n## Source Walkthrough\n\n"
            "1. `app/models/user.rb:1` -- data model, start here.\n"
            "2. `app/controllers/sessions_controller.rb:1` -- entry point.\n"
        )
        assert validator.check_source_walkthrough(filled, "f") == []


class TestScaffoldFile:
    def _make_spec(self, tmp_path: Path, body: str) -> Path:
        screen = tmp_path / "docs" / "screens" / "SCR001_Login"
        screen.mkdir(parents=True)
        spec = screen / "spec.md"
        spec.write_text(body, encoding="utf-8")
        return spec

    def test_scaffolds_missing_file_in_place(self, tmp_path):
        spec = self._make_spec(tmp_path, _BASE)
        added = lib.scaffold_file(spec)
        assert added is True
        text = spec.read_text(encoding="utf-8")
        assert "## Source Walkthrough" in text
        assert "## DB Impact per Event" not in text

    def test_prefilled_file_is_left_byte_identical(self, tmp_path):
        filled = _BASE + "\n## Source Walkthrough\n\nreal content\n"
        spec = self._make_spec(tmp_path, filled)
        before = _sha(spec)
        added = lib.scaffold_file(spec)
        assert added is False
        assert _sha(spec) == before

    def test_three_consecutive_scaffolds_are_byte_identical_after_the_first(self, tmp_path):
        spec = self._make_spec(tmp_path, _BASE)
        lib.scaffold_file(spec)
        after_first = _sha(spec)
        lib.scaffold_file(spec)
        after_second = _sha(spec)
        lib.scaffold_file(spec)
        after_third = _sha(spec)
        assert after_first == after_second == after_third

    def test_unreadable_file_is_skipped_not_raised(self, tmp_path):
        import os
        if os.geteuid() == 0:
            pytest.skip("root reads chmod-000 files; permission case unreproducible")
        spec = self._make_spec(tmp_path, _BASE)
        spec.chmod(0o000)
        try:
            result = lib.scaffold_file(spec)
        finally:
            spec.chmod(0o644)
        assert result is False


class TestScaffoldCorpus:
    def _make_corpus(self, tmp_path: Path, names: list[str]) -> Path:
        docs = tmp_path / "docs"
        for name in names:
            screen = docs / "screens" / name
            screen.mkdir(parents=True)
            (screen / "spec.md").write_text(_BASE, encoding="utf-8")
        return docs

    def test_scaffolds_every_screen_spec_and_counts_match(self, tmp_path):
        docs = self._make_corpus(tmp_path, ["SCR001_A", "SCR002_B", "SCR003_C"])
        changed, errors = lib.scaffold_corpus(docs)
        assert (changed, errors) == (3, 0)

    def test_features_param_is_accepted_and_ignored(self, tmp_path):
        """`features` has no meaning for screen dirs (keyed by SCR###, not F###) --
        accepted for CountPendingFn/RunFn signature parity, silently ignored."""
        docs = self._make_corpus(tmp_path, ["SCR001_A", "SCR002_B"])
        changed, errors = lib.scaffold_corpus(docs, frozenset({"SCR001_A"}))
        assert (changed, errors) == (2, 0)


class TestScopeGuardAppliesUnchanged:
    """Requirement 4: the P03 scope guard applies unchanged -- only the A3 body may
    change in a screen spec. `_a3_fill_guard_lib.check_scope` (phase 09: A3-only by
    construction, not merely "B4 happens to be absent") strips exactly the A3 body,
    which is exactly what a screen spec ever carries."""

    def test_a3_only_edit_passes_scope_guard(self):
        pre = lib.scaffold_text(_BASE)
        post = pre.replace(
            "{UNFILLED SCAFFOLD -- this reading list has not been authored yet; it "
            "requires reading the screen's source. Fill it by running "
            "`run_doc_migrations.py --migrate --only a3-screens`.}",
            "1. `app/models/user.rb:1` -- data model, start here.\n",
        )
        assert fill_guard.check_scope(pre, post) == []

    def test_edit_outside_a3_body_fails_scope_guard(self):
        pre = lib.scaffold_text(_BASE)
        post = pre.replace("Login form.", "Rewritten purpose text.")
        assert fill_guard.check_scope(pre, post) != []


class TestRegistryStep:
    """`count_pending`/`run` -- the StepSpec seam `run_doc_migrations.py` registers."""

    def _make_corpus(self, tmp_path: Path, n: int) -> Path:
        docs = tmp_path / "docs"
        for i in range(n):
            screen = docs / "screens" / f"SCR{i:03d}_X"
            screen.mkdir(parents=True)
            (screen / "spec.md").write_text(_BASE, encoding="utf-8")
        return docs

    def test_count_pending_reports_per_file_before_and_zero_after(self, tmp_path):
        docs = self._make_corpus(tmp_path, 5)
        assert lib.count_pending(docs, tmp_path, None) == 5
        lib.scaffold_corpus(docs)
        assert lib.count_pending(docs, tmp_path, None) == 0

    def test_run_reports_progress_and_needs_llm_fill(self, tmp_path):
        docs = self._make_corpus(tmp_path, 2)
        result = lib.run(docs, tmp_path, None)
        assert result.category == "progress"
        assert result.needs_llm_fill is True

    def test_run_reports_already_when_nothing_pending(self, tmp_path):
        docs = self._make_corpus(tmp_path, 1)
        lib.scaffold_corpus(docs)
        result = lib.run(docs, tmp_path, None)
        assert result.category == "already"
        assert result.needs_llm_fill is False

    def test_run_on_empty_corpus_is_already_not_a_crash(self, tmp_path):
        docs = tmp_path / "docs"
        (docs / "screens").mkdir(parents=True)
        result = lib.run(docs, tmp_path, None)
        assert result.category == "already"


class TestPrerequisiteGating:
    """Requirement: `resolve_steps(["a3-screens"])` with its prerequisite unsatisfied
    refuses and names the prerequisite -- proven against the real
    `StepRegistry`/`execute`, not a re-read of its docstring.

    RENAMED (phase-09, plans/260824-1846-rebuild-spec-action-self-sufficiency-v27-8,
    correction X4): `a3-screens`'s prerequisite used to be the now-retired `a3-b4`
    step; it repoints straight to `audience-split` now, so this suite tests refusal
    against a fake `audience-split` StepSpec with real pending work instead of a
    real `a3-b4` one."""

    def _build_registry(self, tmp_path: Path, *,
                         audience_split_pending: int) -> tuple[registry.StepRegistry, Path]:
        docs = tmp_path / "docs"
        (docs / "screens" / "SCR001_X").mkdir(parents=True)
        (docs / "screens" / "SCR001_X" / "spec.md").write_text(_BASE, encoding="utf-8")

        reg = registry.StepRegistry()
        reg.register(registry.StepSpec(
            name="audience-split", prerequisite=None,
            count_pending=lambda d, p, f: audience_split_pending,
            run=lambda d, p, f: registry.StepResult(category="already", message="n/a"),
        ))
        reg.register(registry.StepSpec(
            name="a3-screens", prerequisite="audience-split",
            count_pending=lib.count_pending, run=lib.run,
        ))
        return reg, docs

    def test_refuses_when_audience_split_has_pending_work(self, tmp_path, capsys):
        reg, docs = self._build_registry(tmp_path, audience_split_pending=1)

        exit_code, tally = registry.execute(reg, ("a3-screens",), docs, tmp_path, None)

        err = capsys.readouterr().err
        assert "[REFUSED] step=a3-screens prerequisite=audience-split pending=1" in err
        assert exit_code == 4  # nothing advanced, nothing broken
        # the screen spec must be untouched -- the refusal never called run()
        assert lib.count_pending(docs, tmp_path, None) == 1

    def test_proceeds_once_audience_split_is_satisfied(self, tmp_path):
        reg, docs = self._build_registry(tmp_path, audience_split_pending=0)

        exit_code, _tally = registry.execute(reg, ("a3-screens",), docs, tmp_path, None)

        assert exit_code == 4  # a3-screens itself still INERT (needs_llm_fill)
        assert lib.count_pending(docs, tmp_path, None) == 0


@pytest.mark.skipif(not _POST_SRC.is_dir(),
                     reason="real-corpus scratch copy (e2e7) not present in this environment")
class TestRealCorpusIntegration:
    """Success Criteria from phase-08.md, proven on the actual 182-screen
    post-migration corpus, not a synthetic fixture."""

    def _copy_corpus(self, tmp_path: Path) -> Path:
        """Copy the shared scratch corpus, then RESET every screen to un-scaffolded.

        `_POST_SRC` is a scratch directory OUTSIDE the repo that any operator -- or a
        real fill wave -- may have advanced since this test was written. Asserting on
        its current migration state made these two tests fail the moment someone ran
        `--migrate --only a3-screens` against it for real, which is a fragile-test
        problem, not a product problem. The corpus is still valuable as real INPUT (182
        genuine screen specs); its migration STATE is not, so the fixture normalises the
        state it asserts on rather than trusting it.
        """
        dest = tmp_path / "docs"
        shutil.copytree(_POST_SRC, dest)
        for spec in dest.glob("screens/*/spec.md"):
            text = spec.read_text(encoding="utf-8")
            if _section_body(text, A3_HEADING) is None:
                continue
            spec.write_text(
                text[: text.index(A3_HEADING)].rstrip("\n") + "\n", encoding="utf-8")
        return dest

    def test_182_pending_before_zero_after(self, tmp_path):
        docs = self._copy_corpus(tmp_path)
        assert lib.count_pending(docs, tmp_path, None) == 182
        changed, errors = lib.scaffold_corpus(docs)
        assert (changed, errors) == (182, 0)
        assert lib.count_pending(docs, tmp_path, None) == 0

    def test_validator_sweep_before_and_after_zero_new_criticals(self, tmp_path):
        before_dir = self._copy_corpus(tmp_path)
        before_result = validator.validate(before_dir)
        before_screens = [i for i in before_result["issues"] if "/screens/" in i["location"]["file"]]
        assert {i["rule_id"] for i in before_screens} == {"reading_guide.pre_migration"}
        assert before_result["summary"]["critical"] == 0

        lib.scaffold_corpus(before_dir)
        after_result = validator.validate(before_dir)
        after_screens = [i for i in after_result["issues"] if "/screens/" in i["location"]["file"]]
        assert len(after_screens) == 182
        assert {i["rule_id"] for i in after_screens} == {"reading_guide.unmapped"}
        assert all(i["severity"] == "warning" for i in after_screens)
        assert after_result["summary"]["critical"] == 0

    def test_no_b4_heading_in_any_screen_spec_after_scaffold(self, tmp_path):
        docs = self._copy_corpus(tmp_path)
        lib.scaffold_corpus(docs)
        for spec in docs.glob("screens/*/spec.md"):
            assert "DB Impact per Event" not in spec.read_text(encoding="utf-8")

    def test_three_consecutive_runs_byte_identical_after_the_first(self, tmp_path):
        docs = self._copy_corpus(tmp_path)
        lib.scaffold_corpus(docs)
        after_first = _fingerprint(docs)
        lib.scaffold_corpus(docs)
        after_second = _fingerprint(docs)
        lib.scaffold_corpus(docs)
        after_third = _fingerprint(docs)
        assert after_first == after_second == after_third
