# layout-exempt: rebuild-spec screen-sot tests — docs paths are managed targets
"""Tests for `_doc_migration_screen_sot_step_lib.py` + the `screen-sot` registry entry
(phase-06, plans/260818-1332-rebuild-spec-human-readable-sot).

Deliberately imports `_doc_migration_registry_lib` directly, never
`run_doc_migrations.py` -- the latter transitively imports `migrate_feature_
audience_split` -> ... -> `_audience_split_ccl_normalize_lib`, which currently fails to
import (`_spec_constants.REQUIRED_CCL_H3` was retired by the concurrently-running P08
of a SIBLING plan; P09 fixes the consumer chain). `test_a3_screens_step.py` already
established this same import-avoidance pattern for exactly this reason -- this suite
follows it rather than reinventing it.

Real-corpus fixtures come from this plan's own evidence directory (measured, read-only
originals never touched): `evidence/corpus-g1/SCR001_Login.spec.md` (v26 shape, has the
unnumbered `## Screen Layout` H2) and `evidence/corpus-g2/SCR012_ErrorNotFound.spec.md`
+ `SCR020_LoginPage.spec.md` (Mode-C/v27 shape, no `## Screen Layout` H2 at all --
Layout Sketch/Regions already live as bare H3s). Both shapes are pending under the
`"## 2. Screen Layout" not in text` predicate; the composer only supports G2-shaped
input in production (screen-sot's own prerequisite, `a3-screens`, only ever sees G2 --
G1 reaches G2 through Mode C, a separate, earlier step). Copied into `tmp_path` per
test, never mutated in place.
"""
from __future__ import annotations

import sys
from pathlib import Path


_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import _doc_migration_registry_lib as registry  # noqa: E402
import _doc_migration_screen_sot_step_lib as lib  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[5]  # agent-kit/
_SOT_CORPUS = Path(__file__).resolve().parent / "fixtures" / "sot-corpus"
"""Real generated corpus, git-tracked. Lived under `plans/` (gitignored) until it took
the whole CI suite down at collection time — see fixtures/sot-corpus/README.md."""
_EVIDENCE = _SOT_CORPUS
_G1_LOGIN = _EVIDENCE / "corpus-g1" / "SCR001_Login.spec.md"
_G2_ERROR = _EVIDENCE / "corpus-g2" / "SCR012_ErrorNotFound.spec.md"
_G2_LOGIN = _EVIDENCE / "corpus-g2" / "SCR020_LoginPage.spec.md"

_MINIMAL = (
    "# SCR001_Login — Screen Spec\n\n## Purpose\n\nLogin form.\n\n"
    "## Source References\n\n- `app/views/login.haml:1`\n"
)


def _seed(docs: Path, slug: str, source: Path | str) -> Path:
    screen = docs / "screens" / slug
    screen.mkdir(parents=True)
    spec = screen / "spec.md"
    text = source.read_text(encoding="utf-8") if isinstance(source, Path) else source
    spec.write_text(text, encoding="utf-8")
    return spec


class TestPendingPredicateOnRealFixtures:
    """`count_pending`'s artifact predicate must fire for BOTH generations reaching
    this step -- see module docstring's grep proof that the composer is the sole
    writer of the `"## 2. Screen Layout"` heading."""

    def test_g1_fixture_is_pending(self, tmp_path):
        docs = tmp_path / "docs"
        _seed(docs, "SCR001_Login", _G1_LOGIN)
        assert lib.count_pending(docs, tmp_path, None) == 1

    def test_g2_fixtures_are_pending(self, tmp_path):
        docs = tmp_path / "docs"
        _seed(docs, "SCR012_ErrorNotFound", _G2_ERROR)
        _seed(docs, "SCR020_LoginPage", _G2_LOGIN)
        assert lib.count_pending(docs, tmp_path, None) == 2

    def test_composed_text_is_no_longer_pending(self, tmp_path):
        docs = tmp_path / "docs"
        spec = _seed(docs, "SCR012_ErrorNotFound", _G2_ERROR)
        result = lib.run(docs, tmp_path, None)
        assert result.category == "progress"
        assert "## 2. Screen Layout" in spec.read_text(encoding="utf-8")
        assert lib.count_pending(docs, tmp_path, None) == 0

    def test_count_pending_never_writes(self, tmp_path):
        docs = tmp_path / "docs"
        spec = _seed(docs, "SCR012_ErrorNotFound", _G2_ERROR)
        before = spec.stat().st_mtime_ns
        lib.count_pending(docs, tmp_path, None)
        assert spec.stat().st_mtime_ns == before

    def test_unreadable_spec_is_skipped_not_counted(self, tmp_path):
        # a directory named "spec.md" makes read_text() raise IsADirectoryError
        # (an OSError subclass) -- count_pending must swallow it, never raise.
        docs = tmp_path / "docs"
        (docs / "screens" / "SCR999_Bad" / "spec.md").mkdir(parents=True)
        assert lib.count_pending(docs, tmp_path, None) == 0


class TestFeatureFilterIgnored:
    def test_features_param_is_accepted_and_ignored(self, tmp_path):
        docs = tmp_path / "docs"
        _seed(docs, "SCR001_A", _MINIMAL)
        _seed(docs, "SCR002_B", _MINIMAL)
        result = lib.run(docs, tmp_path, frozenset({"SCR001_A"}))
        assert result.category == "progress"
        assert "composed 2" in result.message


class TestRun:
    def test_composes_real_g2_corpus_progress_and_needs_llm_fill(self, tmp_path):
        docs = tmp_path / "docs"
        _seed(docs, "SCR012_ErrorNotFound", _G2_ERROR)
        _seed(docs, "SCR020_LoginPage", _G2_LOGIN)

        result = lib.run(docs, tmp_path, None)

        assert result.category == "progress"
        assert result.needs_llm_fill is True
        assert "composed 2" in result.message

    def test_second_run_reports_already_with_zero_pending(self, tmp_path):
        docs = tmp_path / "docs"
        spec = _seed(docs, "SCR012_ErrorNotFound", _G2_ERROR)
        lib.run(docs, tmp_path, None)
        after_first = spec.read_text(encoding="utf-8")

        result = lib.run(docs, tmp_path, None)

        assert result.category == "already"
        assert result.needs_llm_fill is False
        assert lib.count_pending(docs, tmp_path, None) == 0
        assert spec.read_text(encoding="utf-8") == after_first, "second run must write nothing"

    def test_run_on_empty_corpus_is_already_not_a_crash(self, tmp_path):
        docs = tmp_path / "docs"
        (docs / "screens").mkdir(parents=True)
        result = lib.run(docs, tmp_path, None)
        assert result.category == "already"

    def test_read_failure_isolated_good_screen_still_composed(self, tmp_path):
        # reaches the `except OSError` branch in run()'s read (IsADirectoryError):
        # spec.md is a directory, not a file, for the BAD screen only. "Bad" sorts
        # BEFORE "Good" (glob is processed in sorted order) so this genuinely proves
        # the loop CONTINUES past a failure rather than merely proving a screen
        # processed before any failure is unaffected -- a `break` in place of
        # `continue` would leave the good screen unwritten and fail this assertion.
        docs = tmp_path / "docs"
        (docs / "screens" / "SCR001_Bad" / "spec.md").mkdir(parents=True)
        good = _seed(docs, "SCR999_Good", _MINIMAL)

        result = lib.run(docs, tmp_path, None)

        assert result.category == "failed"
        assert "SCR001_Bad" in result.message
        assert "read failed" in result.message
        assert "## 2. Screen Layout" in good.read_text(encoding="utf-8"), (
            "the good screen must still be composed despite the other's read failure"
        )

    def test_write_failure_isolated_good_screen_still_composed(self, tmp_path, monkeypatch):
        # reaches the `except OSError` branch in run()'s write: `_atomic_write` is
        # monkeypatched to raise ONLY for the bad screen's path, proving the write
        # (not read) failure branch specifically, and that the loop does not abort.
        # "Bad" sorts before "Good" for the same reason as the read-failure test above.
        docs = tmp_path / "docs"
        bad = _seed(docs, "SCR001_Bad", _MINIMAL)
        good = _seed(docs, "SCR999_Good", _MINIMAL)

        real_atomic_write = lib._atomic_write

        def _flaky_write(path: Path, text: str) -> None:
            if path == bad:
                raise OSError("disk full (simulated)")
            real_atomic_write(path, text)

        monkeypatch.setattr(lib, "_atomic_write", _flaky_write)

        result = lib.run(docs, tmp_path, None)

        assert result.category == "failed"
        assert "SCR001_Bad" in result.message
        assert "write failed" in result.message
        assert "## 2. Screen Layout" in good.read_text(encoding="utf-8")
        assert "## 2. Screen Layout" not in bad.read_text(encoding="utf-8"), (
            "the failed write must never have landed"
        )


class TestPrerequisiteGating:
    """Proven against the real `StepRegistry`/`execute` (not a re-read of a docstring):
    `screen-sot` refuses while its prerequisite `a3-screens` still has pending work."""

    def _build_registry(self, tmp_path: Path, *, a3_screens_pending: int) -> "tuple[registry.StepRegistry, Path]":
        docs = tmp_path / "docs"
        _seed(docs, "SCR001_X", _MINIMAL)

        reg = registry.StepRegistry()
        reg.register(registry.StepSpec(
            name="a3-screens", prerequisite=None,
            count_pending=lambda d, p, f: a3_screens_pending,
            run=lambda d, p, f: registry.StepResult(category="already", message="n/a"),
        ))
        reg.register(registry.StepSpec(
            name="screen-sot", prerequisite="a3-screens",
            count_pending=lib.count_pending, run=lib.run,
        ))
        return reg, docs

    def test_refuses_when_a3_screens_has_pending_work(self, tmp_path, capsys):
        reg, docs = self._build_registry(tmp_path, a3_screens_pending=1)
        before_pending = lib.count_pending(docs, tmp_path, None)

        exit_code, _tally = registry.execute(reg, ("screen-sot",), docs, tmp_path, None)

        err = capsys.readouterr().err
        assert "[REFUSED] step=screen-sot prerequisite=a3-screens pending=1" in err
        assert exit_code == 4
        # the refusal never called run() -- the spec is untouched.
        assert lib.count_pending(docs, tmp_path, None) == before_pending == 1

    def test_proceeds_once_a3_screens_is_satisfied(self, tmp_path):
        reg, docs = self._build_registry(tmp_path, a3_screens_pending=0)

        exit_code, _tally = registry.execute(reg, ("screen-sot",), docs, tmp_path, None)

        assert exit_code == 4  # screen-sot itself still INERT (needs_llm_fill)
        assert lib.count_pending(docs, tmp_path, None) == 0

    def test_ran_output_set_reflects_refusal_vs_actual_run(self, tmp_path):
        # Negative half reaches the REFUSED branch in `execute()` (the `continue`
        # before `step.run()` is ever called, a3-screens still pending) -- proves
        # `ran` is never populated for a refusal, the exact fact phase-06's ADDENDUM
        # fix in run_doc_migrations.py depends on. Positive half reaches the normal
        # `step.run()` call path (a3-screens satisfied) for contrast.
        reg_refused, docs_refused = self._build_registry(tmp_path / "a", a3_screens_pending=1)
        ran_refused: set[str] = set()
        registry.execute(reg_refused, ("screen-sot",), docs_refused, tmp_path, None, ran=ran_refused)
        assert "screen-sot" not in ran_refused

        reg_ran, docs_ran = self._build_registry(tmp_path / "b", a3_screens_pending=0)
        ran_ok: set[str] = set()
        registry.execute(reg_ran, ("screen-sot",), docs_ran, tmp_path, None, ran=ran_ok)
        assert "screen-sot" in ran_ok
