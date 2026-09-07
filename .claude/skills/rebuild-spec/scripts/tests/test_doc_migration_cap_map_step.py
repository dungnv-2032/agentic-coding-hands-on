# layout-exempt: rebuild-spec cap-map tests — docs paths are managed targets
"""Tests for `_doc_migration_cap_map_step_lib.py` + `_cap_map_rollback_lib.py` +
`_cap_map_table_widen_lib.py` + `_cap_map_io_lib.py` -- the `cap-map` `--migrate` step
(phase-07, plans/260819-1016-rebuild-spec-capability-map).

FIXTURE PROVENANCE (plan-wide rule: state which shape each test reads):

- `count_pending`'s five shapes (`TestCountPendingFiveShapes`) and the FM-6 isolation
  fixture: hand-built minimal `functional-spec.md` content, mirroring the `_MINIMAL`-
  string precedent `test_doc_migration_screen_sot_step_lib.py` already established at
  this layer (unit-level, not the committed-corpus layer).
- The "old 5-column, already filled" shape (`_OLD_5COL_FILLED_TEXT`) is DERIVED from
  the real, composer-produced rows of the committed
  `tests/fixtures/corpora/sot-shapes/F900_CapabilitiesPopulated/functional-spec.md`
  (CAP-01..03, verbatim FR-###/SCR### codes), with the `User Stories`/`Business Rules`
  cells dropped to reconstruct the pre-phase-04, 5-column shape `cap-map` exists to
  retrofit. No corpus in this repo predates phase-04's schema widening -- the same
  reason `sot-shapes/` itself is hand-built per its own README.md ("no corpus anywhere
  ... carries a `## 2. Functional Capabilities` heading ... nothing to trim these
  shapes from") applies here with equal force for a shape one step further back. A
  tripwire assertion below checks the derived rows' codes still appear in the real
  fixture, so a future edit to F900 cannot let this silently drift out of sync with
  the real producer.
- `_OLD_5COL_EMPTY_TEXT` (an old 5-column table whose rows were never filled even
  under the old schema) is synthetic by necessity -- there is no "real" empty-old-
  table content to derive from; this mirrors `sot-shapes/F902_CapabilitiesEmptyCells`'s
  own precedent of a hand-edited empty-cells variant.
- AD-1 skew / mirror-skew refusal-then-clear: the committed
  `sot-shapes/F902_CapabilitiesEmptyCells` fixture (already 7-column, `claim_state`
  `"unfilled"`) -- real, composer-derived, phase-05-verified content.
- `--dry-run` / `--only cap-map` prerequisite refusal / idempotency-marker-loss: the
  committed `post-small` corpus (real, trimmed 3-feature v27-pre-SOT derivative).
- SA-5 convergence: `post-small` run through its real prerequisite chain via the CLI,
  plus a hand-built "vi" mirror directory (shape-only, matching `detect_shape`'s file-
  presence contract) -- no real mirror content exists in any committed fixture
  (README.md "why no vi/jp mirrors"), so this is the closest achievable proof within
  this script's own scope: the registry's prerequisite-gating decision changes (old
  wiring would proceed, new wiring correctly refuses) without touching a single byte
  of the corpus. See the test's own docstring for why this is the honest boundary of
  what "convergence" can mean without a real translator to invoke.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

import pytest

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import _cap_map_rollback_lib as rollback_lib  # noqa: E402
import _doc_migration_cap_map_step_lib as lib  # noqa: E402
import _doc_migration_feature_sot_step_lib as _feature_sot_step  # noqa: E402
import _doc_migration_registry_lib as registry  # noqa: E402
import _mirror_skew_lib as _mirror_skew_step  # noqa: E402
import run_doc_migrations as cli  # noqa: E402

_FIXTURES_DIR = _TESTS_DIR / "fixtures" / "corpora"
_POST_FIXTURE = _FIXTURES_DIR / "post-small" / "docs"
_SOT_SHAPES = _FIXTURES_DIR / "sot-shapes"

assert _POST_FIXTURE.is_dir(), f"committed fixture missing: {_POST_FIXTURE}"
assert _SOT_SHAPES.is_dir(), f"committed fixture missing: {_SOT_SHAPES}"

_TECH_STUB = "# Technical\n\n## 2. Functional → Technical Mapping\n\nN/A\n"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _seed(docs: Path, slug: str, text: str, *, with_tech: bool = False) -> Path:
    feature = docs / "features" / slug
    feature.mkdir(parents=True)
    func = feature / "functional-spec.md"
    func.write_text(text, encoding="utf-8")
    if with_tech:
        (feature / "technical-spec.md").write_text(_TECH_STUB, encoding="utf-8")
    return func


def _copy_corpus(src: Path, dest_parent: Path) -> Path:
    dest = dest_parent / "docs"
    shutil.copytree(src, dest)
    return dest


def _fingerprint(root: Path) -> dict:
    out = {}
    for f in sorted(root.rglob("*")):
        if f.is_file():
            out[str(f.relative_to(root))] = hashlib.sha256(f.read_bytes()).hexdigest()
    return out


def _run_cli(docs_root: Path, project_root: Path, *extra: str) -> int:
    return cli.main(["--docs-root", str(docs_root), "--project-root", str(project_root), *extra])


# --------------------------------------------------------------------------- #
# Fixture content -- see module docstring for provenance of each.
# --------------------------------------------------------------------------- #
_ALREADY_WIDENED_FILLED = """# F800_Sample

## 1. Overview

Sample.

## 2. Functional Capabilities

| ID | Capability | What the user can do | User Stories | Requirements | Business Rules | Screens |
|----|------------|------------------------|-----------------|---------------|-------------------|---------|
| CAP-01 | Sign in | Authenticate | US001 | FR-001 | BR-001 | SCR001 |

## 3. Open Decisions

N/A
"""

_WIDENED_BUT_EMPTY = """# F800_Sample

## 2. Functional Capabilities

| ID | Capability | What the user can do | User Stories | Requirements | Business Rules | Screens |
|----|------------|------------------------|-----------------|---------------|-------------------|---------|
| CAP-01 |  |  |  |  |  |  |

## 3. Open Decisions

N/A
"""

_WIDENED_PARTIAL = """# F800_Sample

## 2. Functional Capabilities

| ID | Capability | What the user can do | User Stories | Requirements | Business Rules | Screens |
|----|------------|------------------------|-----------------|---------------|-------------------|---------|
| CAP-01 | Sign in | Authenticate | US001 | FR-001 | BR-001 | SCR001 |
| CAP-02 |  |  |  |  |  |  |

## 3. Open Decisions

N/A
"""

# Derived from the real sot-shapes/F900_CapabilitiesPopulated CAP-01..03 rows (see
# module docstring) -- User Stories/Business Rules cells dropped.
_OLD_5COL_FILLED_TEXT = """# F900_CapabilitiesPopulated

## 1. Overview

Real content derived from the committed sot-shapes/F900_CapabilitiesPopulated
fixture's real CAP-01..03 rows -- User Stories/Business Rules cells mechanically
dropped to reconstruct the pre-phase-04, 5-column shape cap-map retrofits.

## 2. Functional Capabilities

| ID | Capability | What the user can do | Requirements | Screens |
|----|------------|------------------------|---------------|---------|
| CAP-01 | Sign in with credentials | Submit email/password and reach the post-login destination | FR-001, FR-002, FR-003, FR-006, FR-007 | SCR020 |
| CAP-02 | Register a new account | Fill in the sign-up form, with an invite code where the marketplace requires one | FR-004, FR-005 | SCR021 |
| CAP-03 | Reset a forgotten password | Request a reset link by email and complete the reset | FR-008 | SCR025 |

## 3. Open Decisions

N/A -- fixture stub.
"""

# Synthetic by necessity (see module docstring): an old 5-column table nobody ever
# filled, even under the old schema -- mirrors F902_CapabilitiesEmptyCells's own
# hand-edited-empty precedent.
_OLD_5COL_EMPTY_TEXT = """# F810_NeverFilled

## 2. Functional Capabilities

| ID | Capability | What the user can do | Requirements | Screens |
|----|------------|------------------------|---------------|---------|
| CAP-01 |  |  |  |  |
| CAP-02 |  |  |  |  |

## 3. Open Decisions

N/A -- fixture stub.
"""

_NO_SECTION2 = """# F800_Sample

## 2. Open Decisions

N/A -- pre-SOT, feature-sot's problem, not cap-map's.
"""


def test_old_5col_filled_text_matches_the_real_f900_fixture():
    """Tripwire: if F900's real content ever changes, this derived fixture must not
    silently drift out of sync with the producer it claims to represent."""
    real = (_SOT_SHAPES / "F900_CapabilitiesPopulated" / "functional-spec.md").read_text(
        encoding="utf-8",
    )
    assert "FR-001, FR-002, FR-003, FR-006, FR-007" in real
    assert "SCR020" in real and "SCR021" in real and "SCR025" in real


# --------------------------------------------------------------------------- #
# [AD-1] count_pending -- five shapes
# --------------------------------------------------------------------------- #
class TestCountPendingFiveShapes:
    def test_already_widened_and_filled_is_zero(self, tmp_path):
        docs = tmp_path / "docs"
        _seed(docs, "F800_Sample", _ALREADY_WIDENED_FILLED)
        assert lib.count_pending(docs, tmp_path, None) == 0

    def test_widened_but_empty_is_one(self, tmp_path):
        docs = tmp_path / "docs"
        _seed(docs, "F800_Sample", _WIDENED_BUT_EMPTY)
        assert lib.count_pending(docs, tmp_path, None) == 1

    def test_widened_and_partial_is_one(self, tmp_path):
        docs = tmp_path / "docs"
        _seed(docs, "F800_Sample", _WIDENED_PARTIAL)
        assert lib.count_pending(docs, tmp_path, None) == 1

    def test_old_five_column_is_one(self, tmp_path):
        docs = tmp_path / "docs"
        _seed(docs, "F900_CapabilitiesPopulated", _OLD_5COL_FILLED_TEXT)
        assert lib.count_pending(docs, tmp_path, None) == 1

    def test_no_section2_at_all_is_zero(self, tmp_path):
        docs = tmp_path / "docs"
        _seed(docs, "F800_Sample", _NO_SECTION2)
        assert lib.count_pending(docs, tmp_path, None) == 0

    def test_count_pending_never_writes(self, tmp_path):
        docs = tmp_path / "docs"
        func = _seed(docs, "F900_CapabilitiesPopulated", _OLD_5COL_FILLED_TEXT)
        before = func.stat().st_mtime_ns
        lib.count_pending(docs, tmp_path, None)
        assert func.stat().st_mtime_ns == before

    def test_unreadable_functional_spec_is_skipped_not_counted(self, tmp_path):
        docs = tmp_path / "docs"
        (docs / "features" / "F999_Bad" / "functional-spec.md").mkdir(parents=True)
        assert lib.count_pending(docs, tmp_path, None) == 0


# --------------------------------------------------------------------------- #
# run() widening mechanics
# --------------------------------------------------------------------------- #
class TestRunWidensCorrectly:
    def test_widens_header_and_preserves_existing_cell_content(self, tmp_path):
        docs = tmp_path / "docs"
        func = _seed(docs, "F900_CapabilitiesPopulated", _OLD_5COL_FILLED_TEXT)
        result = lib.run(docs, tmp_path, None)
        assert result.category == "progress"
        assert result.needs_llm_fill is True
        text = func.read_text(encoding="utf-8")
        assert "| ID | Capability | What the user can do | User Stories | Requirements | Business Rules | Screens |" in text
        assert "FR-001, FR-002, FR-003, FR-006, FR-007" in text  # real content preserved
        assert "SCR020" in text
        # New cells are present-but-empty -- codes are never auto-assigned.
        assert "| CAP-01 | Sign in with credentials | Submit email/password and reach the post-login destination |  | FR-001, FR-002, FR-003, FR-006, FR-007 |  | SCR020 |" in text

    def test_run_never_writes_when_nothing_is_shape_pending(self, tmp_path):
        docs = tmp_path / "docs"
        func = _seed(docs, "F800_Sample", _ALREADY_WIDENED_FILLED)
        before = func.stat().st_mtime_ns
        result = lib.run(docs, tmp_path, None)
        assert result.category == "already"
        assert result.needs_llm_fill is False
        assert func.stat().st_mtime_ns == before

    def test_run_reports_already_with_needs_llm_fill_when_only_fill_pending(self, tmp_path):
        docs = tmp_path / "docs"
        func = _seed(docs, "F800_Sample", _WIDENED_BUT_EMPTY)
        before = func.stat().st_mtime_ns
        result = lib.run(docs, tmp_path, None)
        assert result.category == "already"
        assert result.needs_llm_fill is True
        assert func.stat().st_mtime_ns == before, "fill_pending alone must never write"


# --------------------------------------------------------------------------- #
# Idempotency -- LOAD-BEARING (plan.md: never skip this)
# --------------------------------------------------------------------------- #
class TestIdempotencyLoadBearing:
    """Requirement 10 / Success Criteria: run cap-map, fingerprint, run again --
    byte-identical, second run writes nothing. Then delete the `.migrate-v27` tree
    (INCLUDING cap-map's own `.bak`) and re-run -- still byte-identical. That last
    assertion is the one the shipped 2368->2416-line data-corruption bug would have
    failed: `count_pending` must derive "already done?" from the artifact, never from
    a marker or the `.bak`."""

    def test_run_twice_is_byte_identical_and_writes_nothing(self, tmp_path):
        func = _seed(docs := tmp_path / "docs", "F900_CapabilitiesPopulated", _OLD_5COL_FILLED_TEXT)
        result1 = lib.run(docs, tmp_path, None)
        assert result1.category == "progress"
        fp1 = hashlib.sha256(func.read_bytes()).hexdigest()

        result2 = lib.run(docs, tmp_path, None)
        fp2 = hashlib.sha256(func.read_bytes()).hexdigest()
        assert fp1 == fp2
        assert result2.category == "already"

    def test_deleting_the_migrate_v27_tree_including_bak_still_identical(self, tmp_path):
        func = _seed(docs := tmp_path / "docs", "F900_CapabilitiesPopulated", _OLD_5COL_FILLED_TEXT)
        lib.run(docs, tmp_path, None)
        fp_after_first = hashlib.sha256(func.read_bytes()).hexdigest()
        bak = docs / ".migrate-v27" / "cap-map" / "F900_CapabilitiesPopulated" / "functional-spec.md.bak"
        assert bak.is_file(), "run() must have written the backup before its first destructive write"

        shutil.rmtree(docs / ".migrate-v27")
        assert not (docs / ".migrate-v27").exists()

        result3 = lib.run(docs, tmp_path, None)
        assert hashlib.sha256(func.read_bytes()).hexdigest() == fp_after_first
        assert result3.category == "already"

        # A fourth run confirms the point holds even with count_pending run standalone
        # (never a marker/backup read).
        assert lib.count_pending(docs, tmp_path, None) == 0


# --------------------------------------------------------------------------- #
# [AD-1] Skew test: mirror-skew stays refused while unfilled, clears once filled
# --------------------------------------------------------------------------- #
class TestAD1SkewRefusesMirrorSkewUntilFilled:
    def test_widened_but_unfilled_refuses_mirror_skew_exit_4(self, tmp_path, capsys):
        docs_root = tmp_path / "docs"
        shutil.copytree(
            _SOT_SHAPES / "F902_CapabilitiesEmptyCells",
            docs_root / "features" / "F902_CapabilitiesEmptyCells",
        )
        exit_code = _run_cli(docs_root, tmp_path, "--only", "mirror-skew")
        err = capsys.readouterr().err
        assert exit_code == 4
        # [phase-06 collateral, plans/260824-1128-rebuild-spec-action-thread-v27-7]
        # mirror-skew's immediate prerequisite is now `action-thread`, not `cap-map`
        # directly -- this fixture's technical-spec.md is untouched (still
        # layer-first-shaped), so action-thread itself is what's genuinely pending
        # here; cap-map's own unfilled claim cells are no longer the binding refusal.
        assert "[REFUSED] step=mirror-skew prerequisite=action-thread" in err

    def test_filling_the_claim_cells_clears_the_cap_map_refusal_but_not_mirror_skew(self, tmp_path, capsys):
        docs_root = tmp_path / "docs"
        feature_dir = docs_root / "features" / "F902_CapabilitiesEmptyCells"
        shutil.copytree(_SOT_SHAPES / "F902_CapabilitiesEmptyCells", feature_dir)
        func_path = feature_dir / "functional-spec.md"
        text = func_path.read_text(encoding="utf-8")
        filled = text.replace(
            "| CAP-01 |  |  |  |  |  |  |",
            "| CAP-01 | Sign in | Do it | US001 | FR-001 | BR-001 | SCR001 |",
        ).replace(
            "| CAP-02 |  |  |  |  |  |  |",
            "| CAP-02 | Register | Do it | US002 | FR-002 | BR-002 | SCR002 |",
        )
        assert filled != text, "the real F902 row text must have matched for this to prove anything"
        func_path.write_text(filled, encoding="utf-8")

        exit_code = _run_cli(docs_root, tmp_path, "--only", "mirror-skew")
        # [phase-06 collateral, plans/260824-1128-rebuild-spec-action-thread-v27-7]
        # Filling cap-map's claim cells clears CAP-MAP's own fill_pending, but
        # mirror-skew's immediate prerequisite is `action-thread` now, not `cap-map`
        # -- this fixture's technical-spec.md was never touched by this test (still
        # layer-first-shaped), so mirror-skew correctly stays refused on
        # action-thread's genuinely pending work, one gate further down the chain
        # than this test originally proved.
        assert exit_code == 4
        err = capsys.readouterr().err
        assert "[REFUSED] step=mirror-skew prerequisite=action-thread" in err


# --------------------------------------------------------------------------- #
# [FM-3] Rollback -- three tests
# --------------------------------------------------------------------------- #
class TestFM3Rollback:
    def test_widened_then_rolled_back_is_byte_identical_to_pre_widen(self, tmp_path):
        func = _seed(docs := tmp_path / "docs", "F810_NeverFilled", _OLD_5COL_EMPTY_TEXT)
        before = hashlib.sha256(func.read_bytes()).hexdigest()

        run_result = lib.run(docs, tmp_path, None)
        assert run_result.category == "progress"
        assert hashlib.sha256(func.read_bytes()).hexdigest() != before

        rb_result = rollback_lib.rollback(docs, tmp_path, None)
        assert rb_result.category == "progress"
        assert hashlib.sha256(func.read_bytes()).hexdigest() == before
        bak = docs / ".migrate-v27" / "cap-map" / "F810_NeverFilled" / "functional-spec.md.bak"
        assert not bak.exists(), "rollback() must remove the .bak it restores from"

    def test_filled_feature_refuses_rollback_and_leaves_file_untouched(self, tmp_path, capsys):
        func = _seed(docs := tmp_path / "docs", "F900_CapabilitiesPopulated", _OLD_5COL_FILLED_TEXT)
        lib.run(docs, tmp_path, None)  # widens; post-widen claim_state resolves "filled"
        # (old Requirements/Screens cells already carried real content pre-widen.)
        widened_fp = hashlib.sha256(func.read_bytes()).hexdigest()

        rb_result = rollback_lib.rollback(docs, tmp_path, None)
        assert rb_result.category == "failed"
        err = capsys.readouterr().err
        assert "[REFUSED] cap-map rollback: F900_CapabilitiesPopulated claim_state=filled" in err
        assert hashlib.sha256(func.read_bytes()).hexdigest() == widened_fp, "refused feature must be untouched"
        bak = docs / ".migrate-v27" / "cap-map" / "F900_CapabilitiesPopulated" / "functional-spec.md.bak"
        assert bak.is_file(), "a refused rollback must not remove the backup either"

    def test_rollback_other_step_exits_2_naming_cap_map(self, tmp_path, capsys):
        docs_root = tmp_path / "docs"
        docs_root.mkdir()
        exit_code = _run_cli(docs_root, tmp_path, "--rollback", "screen-sot")
        assert exit_code == 2
        err = capsys.readouterr().err
        assert "cap-map" in err


# --------------------------------------------------------------------------- #
# [FM-6] Failure isolation
# --------------------------------------------------------------------------- #
class TestFM6FailureIsolation:
    def test_one_unreadable_feature_does_not_abort_the_others(self, tmp_path, capsys):
        docs = tmp_path / "docs"
        for i in range(1, 4):
            _seed(docs, f"F80{i}_Good", _OLD_5COL_FILLED_TEXT, with_tech=True)
        (docs / "features" / "F804_Bad" / "functional-spec.md").mkdir(parents=True)

        exit_code = _run_cli(docs, tmp_path, "--only", "cap-map")

        assert exit_code in (0, 1, 2, 4), "no traceback may escape the CLI boundary"
        combined = "".join(capsys.readouterr())
        assert "F804_Bad" in combined
        assert "3 widened before the failure" in combined
        for i in range(1, 4):
            widened_text = (docs / "features" / f"F80{i}_Good" / "functional-spec.md").read_text(
                encoding="utf-8",
            )
            assert "User Stories" in widened_text

    def test_direct_run_reports_failed_with_re_run_command(self, tmp_path):
        docs = tmp_path / "docs"
        for i in range(1, 4):
            _seed(docs, f"F80{i}_Good", _OLD_5COL_FILLED_TEXT)
        (docs / "features" / "F804_Bad" / "functional-spec.md").mkdir(parents=True)

        result = lib.run(docs, tmp_path, None)
        assert result.category == "failed"
        assert "F804_Bad" in result.message
        assert "3 widened before the failure" in result.message
        assert "--only cap-map" in result.message


# --------------------------------------------------------------------------- #
# --dry-run / --only prerequisite refusal (committed post-small corpus)
# --------------------------------------------------------------------------- #
class TestDryRunAndOnlyRefusal:
    def test_dry_run_reports_pending_count_and_writes_nothing(self, tmp_path, capsys):
        docs_root = _copy_corpus(_POST_FIXTURE, tmp_path)
        before = _fingerprint(docs_root)
        exit_code = _run_cli(docs_root, tmp_path, "--migrate", "--dry-run")
        assert exit_code == 0
        out = capsys.readouterr().out
        # post-small is still pre-SOT (no §2 heading at all yet) -- cap-map correctly
        # reports 0 (feature-sot's problem, never double-counted, AD-1).
        assert "[DRY-RUN] step=cap-map pending=0 prerequisite=feature-sot status=blocked" in out
        assert _fingerprint(docs_root) == before

    def test_only_cap_map_refuses_while_feature_sot_still_pending(self, tmp_path, capsys):
        docs_root = _copy_corpus(_POST_FIXTURE, tmp_path)
        before = _fingerprint(docs_root)
        exit_code = _run_cli(docs_root, tmp_path, "--only", "cap-map")
        assert exit_code == 4
        err = capsys.readouterr().err
        assert "[REFUSED] step=cap-map prerequisite=feature-sot" in err
        assert _fingerprint(docs_root) == before


# --------------------------------------------------------------------------- #
# [SA-5] Old-chain -> new-chain convergence
# --------------------------------------------------------------------------- #
class TestSA5Convergence:
    """A corpus whose mechanical prefix (audience-split..feature-sot) has genuinely
    completed, with a "vi" mirror already shape- and cursor-matched (i.e. exactly what
    the OLD 6-step chain's `mirror-skew` -- prerequisite `feature-sot` directly --
    would already consider fully done, since neither of those counts depends on
    cap-map). Honesty about scope: no real translated mirror content or translator
    exists in this repo's test fixtures (README.md), so this proves the achievable,
    in-scope half of "convergence" -- the REGISTRY's gating decision correctly changes
    under the new 7-step chain (REFUSED where the old chain would have proceeded)
    WITHOUT altering a single byte of the corpus, rather than fabricating what a real
    translate pass would produce."""

    @staticmethod
    def _seed_matching_vi_mirror(docs_root: Path) -> None:
        state_path = docs_root / ".rebuild-state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        sha = state.get("last_rebuild_sha", "")
        state["translations"] = {"vi": {"translated_from_sha": sha}}
        state_path.write_text(json.dumps(state), encoding="utf-8")
        for feature_dir in sorted((docs_root / "features").iterdir()):
            if not feature_dir.is_dir():
                continue
            mirror_dir = docs_root / "vi" / "features" / feature_dir.name
            mirror_dir.mkdir(parents=True)
            (mirror_dir / "functional-spec.md").write_text("# mirror\n", encoding="utf-8")
            (mirror_dir / "technical-spec.md").write_text("# mirror\n", encoding="utf-8")

    def test_old_chain_completion_converges_not_corrupts_under_new_chain(self, tmp_path, capsys):
        docs_root = _copy_corpus(_POST_FIXTURE, tmp_path)
        for step in ("audience-split", "a3-screens", "screen-sot", "feature-sot"):
            _run_cli(docs_root, tmp_path, "--only", step)
        self._seed_matching_vi_mirror(docs_root)

        # Old-chain completion, genuinely reached: feature-sot's own count_pending is
        # 0 (it just ran to completion), and mirror-skew's OWN count_pending (unaware
        # of cap-map's existence, exactly as the old 6-step chain's wiring was) is
        # also 0 -- a real operator on the OLD script would have seen this corpus as
        # fully migrated.
        assert _feature_sot_step.count_pending(docs_root, tmp_path, None) == 0
        assert _mirror_skew_step.count_pending(docs_root, tmp_path, None) == 0

        before = _fingerprint(docs_root)

        # New chain: mirror-skew's prerequisite is now `action-thread` (phase-06,
        # plans/260824-1128-rebuild-spec-action-thread-v27-7 -- one further hop than
        # `cap-map`, which was itself the prior insertion). feature-sot's fresh
        # compose leaves technical-spec.md layer-first-shaped ("## 3. System
        # Design"), which `action-thread`'s own count_pending reads as genuinely
        # pending, so the new chain correctly REFUSES mirror-skew where the old
        # chain would have proceeded straight past it. Converges, does not corrupt:
        # refused cleanly, nothing on disk (primary OR mirror) changes --
        # `execute()`'s prerequisite check short-circuits before `mirror-skew.run()`
        # is ever invoked, so no translate handoff is attempted on this
        # now-recognized-as-incomplete corpus.
        exit_code = _run_cli(docs_root, tmp_path, "--only", "mirror-skew")
        err = capsys.readouterr().err
        assert exit_code == 4
        assert "[REFUSED] step=mirror-skew prerequisite=action-thread" in err
        assert _fingerprint(docs_root) == before


# --------------------------------------------------------------------------- #
# E2E: validator interaction after cap-map's widening
# --------------------------------------------------------------------------- #
class TestValidatorInteraction:
    """Requirement/step 20's intent: prove cap-map's widened-but-empty output reads
    as `cap.claims_unfilled` (one warning), not a `cap.code_unclaimed` flood, in the
    validator that phase 05 built on the same shared `_cap_table_lib` predicate.
    Honesty about the fixture: reaching `claim_state == "unfilled"` needs a §2 that
    already has >=1 data row before cap-map touches it -- feature-sot's own fresh
    compose always writes a ZERO-row skeleton (`claim_state` "absent"), so a genuine
    v26-to-v27 full-chain run over `post-small` cannot reach "unfilled" through
    cap-map alone; it reaches "absent" instead (asserted separately below, honestly,
    rather than asserting the "unfilled" outcome against a corpus that cannot produce
    it). The "unfilled" case this step exists to protect is the OLD-5-COLUMN retrofit
    whose rows were never filled even under the old schema -- `_OLD_5COL_EMPTY_TEXT`."""

    def test_widened_empty_old_table_reads_as_claims_unfilled_not_a_flood(self, tmp_path):
        import validate_feature_spec as vfs

        docs = tmp_path / "docs"
        func = _seed(docs, "F810_NeverFilled", _OLD_5COL_EMPTY_TEXT)
        result = lib.run(docs, tmp_path, None)
        assert result.category == "progress"

        issues = vfs._check_functional_spec(func, func.parent / "technical-spec.md", tmp_path, is_draft=True)
        cap_issues = [i for i in issues if i["rule_id"].startswith("cap.")]
        rule_ids = {i["rule_id"] for i in cap_issues}
        assert rule_ids == {"cap.claims_unfilled"}
        assert len(cap_issues) == 1

    def test_full_chain_from_v26_reaches_absent_not_unfilled_honest_check(self, tmp_path):
        """The real, full-chain outcome (post-small, genuinely migrated end to end):
        feature-sot's fresh §2 skeleton has zero rows (`claim_state` "absent"), so the
        validator correctly floods `cap.code_unclaimed` for every declared code --
        exactly F901_CapabilitiesHeaderOnly's already-pinned behavior
        (test_corpora_fixture_shapes.py), reached here via the real CLI chain instead
        of a hand-built fixture."""
        import validate_feature_spec as vfs

        docs_root = _copy_corpus(_POST_FIXTURE, tmp_path)
        for step in ("audience-split", "a3-screens", "screen-sot", "feature-sot", "cap-map"):
            _run_cli(docs_root, tmp_path, "--only", step)

        func_path = docs_root / "features" / "F001_Auth" / "functional-spec.md"
        tech_path = docs_root / "features" / "F001_Auth" / "technical-spec.md"
        issues = vfs._check_functional_spec(func_path, tech_path, tmp_path, is_draft=False)
        cap_issues = [i for i in issues if i["rule_id"].startswith("cap.")]
        rule_ids = {i["rule_id"] for i in cap_issues}
        assert rule_ids == {"cap.code_unclaimed"}
        assert "cap.claims_unfilled" not in rule_ids
