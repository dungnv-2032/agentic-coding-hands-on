"""Tests for `run_doc_migrations.py` -- phase-01 of
plans/260818-0758-rebuild-spec-post-migration-completion. CLI-level: flag composition
(exit 2 / warn-and-ignore), `--only` prerequisite refusal, `--dry-run` against a real
corpus copy (writes nothing), and the three-consecutive-runs idempotency guarantee.

LOAD-BEARING vs OPPORTUNISTIC (phase-00,
plans/260819-1016-rebuild-spec-capability-map): every assertion in this file that
proves migration BEHAVIOR (flag refusal, dry-run pending counts, prerequisite
refusal, composition, idempotency, the A1 confidence-report trigger rule) runs
against the COMMITTED fixtures under `tests/fixtures/corpora/` -- see that
directory's `README.md` for shape provenance. Those fixtures are trimmed (3
feature dirs, 3 screens) real-corpus derivatives; they can never vanish, so these
tests can never silently read as green-via-skip.

A small number of tests at the bottom of this file are OPPORTUNISTIC: they assert
the same properties again at REAL SCALE (66 features / 182 screens) against a
previous session's scratch corpus copy, when that copy happens to be present on
this machine. They are individually `skipif`-guarded with the reason string
"optional large-corpus check -- not load-bearing", so their skip reads nothing
like the file-level `pytestmark` this module used to carry (phase-00's whole
point: a hardcoded `/tmp/<session-uuid>/...` path must never be the thing that
silently converts a load-bearing test into a skip).
"""
from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

import pytest

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import run_doc_migrations as cli  # noqa: E402

# --------------------------------------------------------------------------- #
# LOAD-BEARING fixtures -- committed, cannot vanish. See
# tests/fixtures/corpora/README.md for what each one pins and why.
# --------------------------------------------------------------------------- #
_FIXTURES_DIR = _TESTS_DIR / "fixtures" / "corpora"
_POST_FIXTURE = _FIXTURES_DIR / "post-small" / "docs"
_PRISTINE_FIXTURE = _FIXTURES_DIR / "pristine-small" / "docs"

assert _POST_FIXTURE.is_dir(), f"committed fixture missing: {_POST_FIXTURE}"
assert _PRISTINE_FIXTURE.is_dir(), f"committed fixture missing: {_PRISTINE_FIXTURE}"

# --------------------------------------------------------------------------- #
# OPPORTUNISTIC-ONLY -- a previous session's real-corpus scratch copy. Read by
# exactly two tests at the bottom of this file, each individually skipif-guarded.
# NEVER referenced by a load-bearing test above this line.
# --------------------------------------------------------------------------- #
_SCRATCH = Path(
    "/tmp/claude-1208602877/-home-pham-van-duc-sun-asterisk-com-github-agent-kit/"
    "dbcca1a0-49d6-4fd9-ab62-4fd3e94147d6/scratchpad"
)
_OPPORTUNISTIC_POST_SRC = _SCRATCH / "st-post" / "docs"
_OPPORTUNISTIC_SKIP_REASON = (
    "optional large-corpus check -- not load-bearing (real-corpus scratch copy "
    "absent in this environment)"
)


def _copy_corpus(src: Path, dest_parent: Path) -> Path:
    dest = dest_parent / "docs"
    shutil.copytree(src, dest)
    return dest


def _fingerprint(root: Path) -> dict:
    """sha256 per relative file path -- content only, immune to mtime/permission
    noise, so it proves byte-identity rather than merely "nothing touched"."""
    out = {}
    for f in sorted(root.rglob("*")):
        if f.is_file():
            out[str(f.relative_to(root))] = hashlib.sha256(f.read_bytes()).hexdigest()
    return out


def _run(docs_root: Path, project_root: Path, *extra: str) -> int:
    return cli.main(["--docs-root", str(docs_root), "--project-root", str(project_root), *extra])


# --------------------------------------------------------------------------- #
# Flag composition -- exit 2 for bad combos, warn-and-ignore for --full/--since
# --------------------------------------------------------------------------- #
def test_generation_flag_combined_with_migrate_exits_2_naming_the_flag(tmp_path, capsys):
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    exit_code = _run(docs_root, tmp_path, "--migrate", "--flows")
    assert exit_code == 2
    assert "--flows" in capsys.readouterr().err


def test_secondary_lang_combined_with_migrate_exits_2(tmp_path, capsys):
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    (docs_root / ".rebuild-state.json").write_text('{"primary_lang": "en"}', encoding="utf-8")
    exit_code = _run(docs_root, tmp_path, "--migrate", "--lang", "vi")
    assert exit_code == 2
    assert "--lang" in capsys.readouterr().err


def test_lang_matching_primary_is_not_refused(tmp_path):
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    (docs_root / ".rebuild-state.json").write_text('{"primary_lang": "en"}', encoding="utf-8")
    exit_code = _run(docs_root, tmp_path, "--migrate", "--lang", "en", "--dry-run")
    assert exit_code == 0


def test_full_and_since_warn_and_continue_rather_than_exit_2(tmp_path, capsys):
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    exit_code = _run(docs_root, tmp_path, "--migrate", "--full", "--since", "abc123", "--dry-run")
    assert exit_code == 0
    err = capsys.readouterr().err
    assert "[WARN]" in err and "--full" in err


def test_unknown_only_step_exits_2(tmp_path, capsys):
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    exit_code = _run(docs_root, tmp_path, "--only", "not-a-real-step")
    assert exit_code == 2
    assert "not-a-real-step" in capsys.readouterr().err


def test_missing_docs_root_exits_2(tmp_path):
    assert _run(tmp_path / "nope", tmp_path) == 2


# --------------------------------------------------------------------------- #
# --dry-run against a committed corpus copy -- prints pending counts, writes
# nothing. `post-small` is post-audience-split (functional/technical-spec pairs
# already exist, still pre-SOT) but pre a3-screens/screen-sot/feature-sot --
# 3 feature dirs, 3 screens, all genuinely pending on those three steps.
# --------------------------------------------------------------------------- #
def test_dry_run_against_post_migration_corpus_prints_all_steps_and_writes_nothing(tmp_path):
    docs_root = _copy_corpus(_POST_FIXTURE, tmp_path)
    before = _fingerprint(docs_root)

    exit_code = _run(docs_root, tmp_path, "--migrate", "--dry-run")

    assert exit_code == 0
    assert _fingerprint(docs_root) == before, "--dry-run must write NOTHING"


def test_dry_run_reports_zero_pending_for_audience_split_on_sealed_corpus(tmp_path, capsys):
    docs_root = _copy_corpus(_POST_FIXTURE, tmp_path)
    _run(docs_root, tmp_path, "--migrate", "--dry-run")
    out = capsys.readouterr().out
    assert "[DRY-RUN] step=audience-split pending=0 prerequisite=none status=ready" in out
    # a3-screens is REAL: 3 = the screen dirs genuinely missing A3 on this fixture --
    # `status=ready` because its OWN prerequisite (audience-split, phase-09 repointed
    # it here after the `a3-b4` step retired) has nothing pending on this sealed
    # corpus. screen-sot/feature-sot follow the same real prerequisite chain, each
    # blocked on the real pending work of the step immediately before it. cap-map is
    # REAL too: pending=0, because this fixture's functional-spec.md is still
    # pre-SOT (`## 2. Open Decisions`, no `## 2. Functional Capabilities` at all) --
    # cap-map's own count_pending never double-counts a file feature-sot still owns
    # (AD-1). action-thread is REAL too: pending=0, because this fixture's
    # technical-spec.md is still pre-SOT (no `## 3. System Design` -- that heading is
    # feature-sot's own output shape) -- action-thread's own count_pending never
    # double-counts a file feature-sot still owns either (same AD-1 discipline).
    # mirror-skew's prerequisite is now `action-thread`, not `feature-sot` or
    # `cap-map`, so its status reads its OWN immediate prerequisite (action-thread=0)
    # -- `status=ready`, even though the corpus is nowhere near mirror-skew-ready end
    # to end; each step checks only its immediate prerequisite, never the whole
    # transitive chain (true of every step here, not new to cap-map or action-thread)
    # -- the sibling OPPORTUNISTIC test at the bottom of this file exercises the real
    # 2-language-stale count on the full scratch corpus instead.
    assert "[DRY-RUN] step=a3-screens pending=3 prerequisite=audience-split status=ready" in out
    assert "[DRY-RUN] step=screen-sot pending=3 prerequisite=a3-screens status=blocked" in out
    assert "[DRY-RUN] step=feature-sot pending=3 prerequisite=screen-sot status=blocked" in out
    assert "[DRY-RUN] step=cap-map pending=0 prerequisite=feature-sot status=blocked" in out
    assert "[DRY-RUN] step=action-thread pending=0 prerequisite=cap-map status=ready" in out
    assert "[DRY-RUN] step=mirror-skew pending=0 prerequisite=action-thread status=ready" in out


def test_dry_run_reports_audience_split_pending_on_pre_migration_corpus(tmp_path, capsys):
    docs_root = _copy_corpus(_PRISTINE_FIXTURE, tmp_path)
    before = _fingerprint(docs_root)

    exit_code = _run(docs_root, tmp_path, "--migrate", "--dry-run")

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "[DRY-RUN] step=audience-split pending=3 prerequisite=none status=ready" in out
    assert _fingerprint(docs_root) == before


# --------------------------------------------------------------------------- #
# --only prerequisite refusal
# --------------------------------------------------------------------------- #
def test_only_audience_split_runs_and_reports_already_on_sealed_corpus(tmp_path, capsys):
    docs_root = _copy_corpus(_POST_FIXTURE, tmp_path)
    before = _fingerprint(docs_root)

    exit_code = _run(docs_root, tmp_path, "--only", "audience-split")

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "step=audience-split category=already" in out
    after = _fingerprint(docs_root)
    # audience-split itself makes zero content changes here (category=already -- the
    # corpus was already sealed before this run). But `--only audience-split` still
    # names a technical-spec.md-writing step, so the A1 confidence-report refresh
    # fires and intentionally rewrites `confidence-report_technical-spec.md` from
    # whatever CURRENT technical-spec.md content is on disk (always-regenerate, never
    # a staleness detector). This fixture pins ONE companion
    # (`F001_Auth/confidence-report_technical-spec.md`) as deliberately stale
    # relative to its sibling `technical-spec.md` -- see README.md "F001_Auth stale
    # confidence-report companion" -- so this run has something real to fix. Every
    # other file, and every other companion, must stay byte-identical.
    before_excl = {k: v for k, v in before.items() if "confidence-report_" not in k}
    after_excl = {k: v for k, v in after.items() if "confidence-report_" not in k}
    assert after_excl == before_excl, (
        "audience-split itself (and everything except the A1 sidecar) must write nothing "
        "on an already-sealed corpus"
    )
    confidence_report_keys = [k for k in before if "confidence-report_" in k]
    assert confidence_report_keys, "fixture must carry confidence-report companions"
    changed = [k for k in confidence_report_keys if before[k] != after.get(k)]
    assert changed == ["features/F001_Auth/confidence-report_technical-spec.md"], (
        "expected the A1 refresh to regenerate exactly the one companion this fixture "
        "deliberately staged as stale, and no other"
    )


# --------------------------------------------------------------------------- #
# `screen-sot` -- phase-06: screen-spec-only, never in the A1 confidence-report set
# --------------------------------------------------------------------------- #
def _satisfy_a3_screens(docs_root: Path, project_root: Path) -> None:
    """`post-small` (this file's POST fixture) is sealed for `audience-split` only --
    `a3-screens` still has real pending work on it (see the dry-run test's own
    documented pending=3 above). Run it for real so `screen-sot`'s prerequisite is
    genuinely satisfied, rather than relying on a fixture shape that doesn't exist.
    (Phase-09: `a3-screens`'s own prerequisite is `audience-split` directly now, so
    this fixture -- already sealed for `audience-split` -- needs no separate step
    run first the way it needed the now-retired `a3-b4` step before.)"""
    _run(docs_root, project_root, "--only", "a3-screens")


def test_only_screen_sot_composes_real_corpus_and_exits_4_for_needs_llm_fill(tmp_path, capsys):
    docs_root = _copy_corpus(_POST_FIXTURE, tmp_path)
    _satisfy_a3_screens(docs_root, tmp_path)
    capsys.readouterr()  # discard the setup runs' own output

    exit_code = _run(docs_root, tmp_path, "--only", "screen-sot")

    assert exit_code == 4  # needs_llm_fill forces INERT -- correct, not a failure
    out = capsys.readouterr().out
    assert "step=screen-sot" in out and "needs_llm_fill=true" in out
    composed = list((docs_root / "screens").glob("*/spec.md"))
    assert composed, "fixture must carry screen specs"
    assert all("## 2. Screen Layout" in p.read_text(encoding="utf-8") for p in composed), (
        "every screen spec must be composed to the SOT shape"
    )


def test_only_screen_sot_second_run_reports_already_and_writes_nothing(tmp_path, capsys):
    docs_root = _copy_corpus(_POST_FIXTURE, tmp_path)
    _satisfy_a3_screens(docs_root, tmp_path)
    _run(docs_root, tmp_path, "--only", "screen-sot")
    after_first = _fingerprint(docs_root)
    capsys.readouterr()

    exit_code = _run(docs_root, tmp_path, "--only", "screen-sot")

    assert exit_code == 0  # ALREADY, no needs_llm_fill on the second pass
    out = capsys.readouterr().out
    assert "step=screen-sot category=already" in out
    assert _fingerprint(docs_root) == after_first, "second run must write nothing"


def test_screen_sot_refuses_while_a3_screens_still_pending(tmp_path, capsys):
    docs_root = _copy_corpus(_POST_FIXTURE, tmp_path)
    before = _fingerprint(docs_root)

    exit_code = _run(docs_root, tmp_path, "--only", "screen-sot")

    assert exit_code == 4
    err = capsys.readouterr().err
    assert "[REFUSED] step=screen-sot prerequisite=a3-screens pending=3" in err
    assert _fingerprint(docs_root) == before, "a refused step must write nothing"


def test_screen_sot_never_joins_the_technical_spec_step_set(tmp_path, capsys):
    # Negative test that reaches the real branch: satisfy the prerequisite so
    # `screen-sot` ACTUALLY RUNS (not merely refused, which trivially touches
    # nothing) and prove NO confidence-report companion was touched -- the only way
    # that could happen is if `screen-sot` triggered the A1 refresh, which
    # `_TECH_SPEC_STEPS` must never allow.
    assert "screen-sot" not in cli._TECH_SPEC_STEPS
    docs_root = _copy_corpus(_POST_FIXTURE, tmp_path)
    _satisfy_a3_screens(docs_root, tmp_path)
    before = _fingerprint(docs_root)
    capsys.readouterr()

    _run(docs_root, tmp_path, "--only", "screen-sot")

    after = _fingerprint(docs_root)
    before_cr = {k: v for k, v in before.items() if "confidence-report_" in k}
    after_cr = {k: v for k, v in after.items() if "confidence-report_" in k}
    assert before_cr == after_cr, (
        "screen-sot must never touch confidence-report_technical-spec.md companions"
    )


# --------------------------------------------------------------------------- #
# `feature-sot` -- phase-10: DOES join the A1 confidence-report step set (the
# opposite rule from `screen-sot`, paired test below)
# --------------------------------------------------------------------------- #
def _satisfy_screen_sot(docs_root: Path, project_root: Path) -> None:
    """`feature-sot`'s own prerequisite is `screen-sot`, whose prerequisite chain
    runs through `a3-screens` first (mirrors `_satisfy_a3_screens` above, one hop
    further)."""
    _satisfy_a3_screens(docs_root, project_root)
    _run(docs_root, project_root, "--only", "screen-sot")


def test_only_feature_sot_composes_real_corpus_and_exits_4_for_needs_llm_fill(tmp_path, capsys):
    docs_root = _copy_corpus(_POST_FIXTURE, tmp_path)
    _satisfy_screen_sot(docs_root, tmp_path)
    capsys.readouterr()

    exit_code = _run(docs_root, tmp_path, "--only", "feature-sot")

    assert exit_code == 4  # needs_llm_fill forces INERT -- correct, not a failure
    out = capsys.readouterr().out
    assert "step=feature-sot" in out and "needs_llm_fill=true" in out
    func_specs = list((docs_root / "features").glob("*/functional-spec.md"))
    tech_specs = list((docs_root / "features").glob("*/technical-spec.md"))
    assert func_specs and tech_specs, "fixture must carry feature spec pairs"
    assert all("## 2. Functional Capabilities" in p.read_text(encoding="utf-8") for p in func_specs)
    assert all(
        "## 2. Functional → Technical Mapping" in p.read_text(encoding="utf-8") for p in tech_specs
    )


def test_only_feature_sot_second_run_reports_already_and_writes_nothing(tmp_path, capsys):
    docs_root = _copy_corpus(_POST_FIXTURE, tmp_path)
    _satisfy_screen_sot(docs_root, tmp_path)
    _run(docs_root, tmp_path, "--only", "feature-sot")
    after_first = _fingerprint(docs_root)
    capsys.readouterr()

    exit_code = _run(docs_root, tmp_path, "--only", "feature-sot")

    assert exit_code == 0  # ALREADY, no needs_llm_fill on the second pass
    out = capsys.readouterr().out
    assert "step=feature-sot category=already" in out
    assert _fingerprint(docs_root) == after_first, "second run must write nothing"


def test_feature_sot_refuses_while_screen_sot_still_pending(tmp_path, capsys):
    docs_root = _copy_corpus(_POST_FIXTURE, tmp_path)
    before = _fingerprint(docs_root)

    exit_code = _run(docs_root, tmp_path, "--only", "feature-sot")

    assert exit_code == 4
    err = capsys.readouterr().err
    assert "[REFUSED] step=feature-sot prerequisite=screen-sot pending=3" in err
    assert _fingerprint(docs_root) == before, "a refused step must write nothing"


def test_feature_sot_and_screen_sot_are_on_opposite_sides_of_the_tech_spec_step_set():
    # Paired test (phase-10 Requirements): feature-sot IN, screen-sot OUT -- getting
    # either backwards is silent (companions go stale, or an unrelated companion
    # rewrite fires for a screen-spec-only step).
    assert "feature-sot" in cli._TECH_SPEC_STEPS
    assert "screen-sot" not in cli._TECH_SPEC_STEPS


def test_feature_sot_actually_running_does_trigger_the_confidence_refresh(tmp_path, monkeypatch):
    # Negative-of-the-negative: screen-sot's own test proves it does NOT trigger the
    # refresh; this proves feature-sot (the opposite rule) DOES, by satisfying its
    # prerequisite for real so `run()` actually fires rather than being refused.
    docs_root = _copy_corpus(_POST_FIXTURE, tmp_path)
    _satisfy_screen_sot(docs_root, tmp_path)
    calls = []
    monkeypatch.setattr(
        cli._confidence_refresh, "refresh",
        lambda *a, **k: calls.append((a, k)) or cli._confidence_refresh.RefreshResult(count=0),
    )

    exit_code = _run(docs_root, tmp_path, "--only", "feature-sot")

    assert exit_code == 4
    assert len(calls) == 1, "feature-sot actually running must trigger the A1 refresh exactly once"


# --------------------------------------------------------------------------- #
# `action-thread` -- phase-06 of plans/260824-1128-rebuild-spec-action-thread-v27-7:
# the v27 (5-bucket) -> v27.7 (action-thread) technical-spec.md reshape, inserted
# between `cap-map` and `mirror-skew` (`mirror-skew`'s prerequisite moves from
# `cap-map` to `action-thread`). DOES join the A1 confidence-report step set --
# it writes technical-spec.md, same rule as `feature-sot`.
#
# The committed `post-small`/`pristine-small` corpora can never reach a satisfied
# `cap-map` (its own fill_pending needs a researcher pass no test can perform), so
# `action-thread` can never actually RUN against them -- see the three-consecutive-
# full-runs idempotency test above, where `action-thread` stays perpetually refused.
# These tests instead stage the dedicated, real (never hand-authored --
# `tests/fixtures/action_thread/README.md`), already-`cap-map`-satisfied F011/F017
# corpus fixtures phase 05 committed for `compose_action_thread` itself.
# --------------------------------------------------------------------------- #
_ACTION_THREAD_FIXTURES = _TESTS_DIR / "fixtures" / "action_thread"
assert _ACTION_THREAD_FIXTURES.is_dir(), f"committed fixture missing: {_ACTION_THREAD_FIXTURES}"

_ACTION_THREAD_FEATURES = (
    ("F011", "F011_ListingModeration"),
    ("F017", "F017_TransportAndCookieSecurity"),
)

# Hand-built minimal shape (same precedent `test_doc_migration_cap_map_step.py`
# documents for its own "widened but empty" fixture) -- carries `## 2. Functional
# Capabilities` but every cell blank, so `cap-map`'s own `count_pending` reports it
# `fill_pending` (never 0). Used ONLY to prove action-thread's own prerequisite
# refusal path; never fed to `compose_action_thread` itself.
_CAP_MAP_UNFILLED_FUNC_TEXT = (
    "# Functional\n\n## 2. Functional Capabilities\n\n"
    "| ID | Capability | What the user can do | User Stories | Requirements | "
    "Business Rules | Screens |\n"
    "|---|---|---|---|---|---|---|\n"
    "| CAP-01 |  |  |  |  |  |  |\n"
)


def _stage_action_thread_corpus(tmp_path: Path) -> Path:
    """Stage the dedicated, real F011/F017 action-thread fixtures as a docs_root.
    Both features' `functional-spec.md` are already SOT-shaped AND already
    `claim_state == "filled"` (verified directly against `_cap_map_table_widen_lib.
    analyze` during implementation), so `cap-map`'s own `count_pending` is 0 here and
    `action-thread`'s real prerequisite is genuinely satisfied without running the
    entire upstream chain."""
    docs_root = tmp_path / "docs"
    for slug, dirname in _ACTION_THREAD_FEATURES:
        feature_dir = docs_root / "features" / dirname
        feature_dir.mkdir(parents=True)
        for kind in ("technical-spec.md", "functional-spec.md"):
            src = _ACTION_THREAD_FIXTURES / f"{slug}_{kind}"
            (feature_dir / kind).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    return docs_root


def test_action_thread_joins_the_technical_spec_step_set():
    # `action-thread` writes technical-spec.md (the v27 -> v27.7 reshape) -- omitting
    # it here is this phase's own named top risk: silent, no error, no warning, the
    # A1 companions just go stale.
    assert "action-thread" in cli._TECH_SPEC_STEPS


def test_mirror_skew_refuses_while_action_thread_still_pending(tmp_path, capsys):
    # Ordering test: mirror-skew must not run before action-thread. Both fixtures'
    # technical-spec.md are still layer-first-shaped ("## 3. System Design"), so
    # action-thread itself has real, genuine pending work -- pending=2.
    docs_root = _stage_action_thread_corpus(tmp_path)
    before = _fingerprint(docs_root)

    exit_code = _run(docs_root, tmp_path, "--only", "mirror-skew")

    assert exit_code == 4
    err = capsys.readouterr().err
    assert "[REFUSED] step=mirror-skew prerequisite=action-thread pending=2" in err
    assert _fingerprint(docs_root) == before, "a refused step must write nothing"


def test_only_action_thread_composes_real_fixtures_and_exits_4_for_needs_llm_fill(tmp_path, capsys):
    docs_root = _stage_action_thread_corpus(tmp_path)

    exit_code = _run(docs_root, tmp_path, "--only", "action-thread")

    assert exit_code == 4  # needs_llm_fill forces INERT -- correct, not a failure
    out = capsys.readouterr().out
    assert "step=action-thread" in out and "needs_llm_fill=true" in out
    for _, dirname in _ACTION_THREAD_FEATURES:
        text = (docs_root / "features" / dirname / "technical-spec.md").read_text(encoding="utf-8")
        assert "## 2. Action Index" in text
        assert "## 3. System Design" not in text, "the old layer-first heading must be gone"


def test_only_action_thread_second_run_is_a_no_op(tmp_path, capsys):
    # Idempotence (merge blocker #4): `--migrate --only action-thread` on an
    # already-migrated file writes nothing on the second pass.
    docs_root = _stage_action_thread_corpus(tmp_path)
    _run(docs_root, tmp_path, "--only", "action-thread")
    after_first = _fingerprint(docs_root)
    capsys.readouterr()

    exit_code = _run(docs_root, tmp_path, "--only", "action-thread")

    assert exit_code == 4  # unresolved rule ownership never auto-clears itself
    out = capsys.readouterr().out
    # ALREADY + needs_llm_fill=True prints via the `[HANDOFF]` branch, not the
    # `[INFO] ... category=already` one (`_doc_migration_registry_lib.execute`) --
    # both F011 (DEC-only unresolved) and F017 (BR-only unresolved) still carry
    # unresolved rule ownership after the first run, so this is the correct branch.
    assert "[HANDOFF] step=action-thread" in out and "needs_llm_fill=true" in out
    assert _fingerprint(docs_root) == after_first, "second run must write nothing"


def test_action_thread_refuses_while_cap_map_still_pending(tmp_path, capsys):
    docs_root = tmp_path / "docs"
    feature_dir = docs_root / "features" / "F011_ListingModeration"
    feature_dir.mkdir(parents=True)
    (feature_dir / "technical-spec.md").write_text(
        (_ACTION_THREAD_FIXTURES / "F011_technical-spec.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (feature_dir / "functional-spec.md").write_text(_CAP_MAP_UNFILLED_FUNC_TEXT, encoding="utf-8")
    before = _fingerprint(docs_root)

    exit_code = _run(docs_root, tmp_path, "--only", "action-thread")

    assert exit_code == 4
    err = capsys.readouterr().err
    assert "[REFUSED] step=action-thread prerequisite=cap-map pending=1" in err
    assert _fingerprint(docs_root) == before, "a refused step must write nothing"


def test_action_thread_actually_running_triggers_the_confidence_refresh(tmp_path, monkeypatch):
    # Merge blocker #1: prove the A1 companion refresh ACTUALLY RAN for this step --
    # not merely that the step ran. `_TECH_SPEC_STEPS` membership failing silently is
    # this phase's own named top risk.
    docs_root = _stage_action_thread_corpus(tmp_path)
    calls = []
    monkeypatch.setattr(
        cli._confidence_refresh, "refresh",
        lambda *a, **k: calls.append((a, k)) or cli._confidence_refresh.RefreshResult(count=0),
    )

    exit_code = _run(docs_root, tmp_path, "--only", "action-thread")

    assert exit_code == 4
    assert len(calls) == 1, "action-thread actually running must trigger the A1 refresh exactly once"


def test_action_thread_actually_running_refreshes_confidence_report_on_disk(tmp_path):
    # Real (non-mocked) corroboration of the test above: the refresh call produces a
    # real artifact on disk, not merely an invocation the mock recorded.
    docs_root = _stage_action_thread_corpus(tmp_path)

    exit_code = _run(docs_root, tmp_path, "--only", "action-thread")

    assert exit_code == 4
    for _, dirname in _ACTION_THREAD_FEATURES:
        cr_path = docs_root / "features" / dirname / "confidence-report_technical-spec.md"
        assert cr_path.is_file(), (
            f"{dirname}: A1 confidence-report companion must be generated for a step "
            "in _TECH_SPEC_STEPS"
        )


def test_action_thread_refused_never_calls_the_confidence_refresh(tmp_path, monkeypatch):
    docs_root = tmp_path / "docs"
    feature_dir = docs_root / "features" / "F011_ListingModeration"
    feature_dir.mkdir(parents=True)
    (feature_dir / "technical-spec.md").write_text(
        (_ACTION_THREAD_FIXTURES / "F011_technical-spec.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (feature_dir / "functional-spec.md").write_text(_CAP_MAP_UNFILLED_FUNC_TEXT, encoding="utf-8")
    calls = []
    monkeypatch.setattr(
        cli._confidence_refresh, "refresh",
        lambda *a, **k: calls.append((a, k)) or cli._confidence_refresh.RefreshResult(count=0),
    )

    exit_code = _run(docs_root, tmp_path, "--only", "action-thread")

    assert exit_code == 4
    assert calls == [], "a refused step must never trigger the A1 confidence-report refresh"


# --------------------------------------------------------------------------- #
# phase-06 ADDENDUM -- the A1 refresh must fire on ACTUALLY RAN, never on merely
# requested-but-refused
# --------------------------------------------------------------------------- #
def test_refused_technical_spec_step_never_calls_the_confidence_refresh(tmp_path, monkeypatch):
    # Reaches the REFUSED branch (feature-sot's own prerequisite, screen-sot, is
    # still pending on this fixture -- pending=3, see the dry-run test's own
    # documented count above) -- proves the refresh function itself is never
    # invoked, independent of whether its output happens to be byte-identical.
    #
    # Phase-09 successor of this test's original version, which reached the REFUSED
    # branch via the now-retired `a3-b4` step refusing on the pristine fixture
    # (a3-b4's own prerequisite, audience-split, was pending there, and a3-b4 -- like
    # feature-sot below -- was a `_TECH_SPEC_STEPS` member). a3-b4 retired without a
    # like-for-like replacement in this exact scenario: `a3-screens` was never a
    # `_TECH_SPEC_STEPS` member (screen-spec-only), so it is not a candidate here
    # regardless of whether it refuses. `feature-sot` (a real `_TECH_SPEC_STEPS`
    # member) genuinely refuses on this POST fixture instead -- its own prerequisite,
    # `screen-sot`, still has real pending work here.
    docs_root = _copy_corpus(_POST_FIXTURE, tmp_path)
    calls = []
    monkeypatch.setattr(
        cli._confidence_refresh, "refresh",
        lambda *a, **k: calls.append((a, k)) or cli._confidence_refresh.RefreshResult(count=0),
    )

    exit_code = _run(docs_root, tmp_path, "--only", "feature-sot")

    assert exit_code == 4
    assert calls == [], "a refused step must never trigger the A1 confidence-report refresh"


def test_step_that_actually_ran_does_call_the_confidence_refresh(tmp_path, monkeypatch):
    # audience-split has no prerequisite, so it always actually runs (never refused) --
    # even though its category is ALREADY (sealed corpus), `ran` must still include it.
    docs_root = _copy_corpus(_POST_FIXTURE, tmp_path)
    calls = []
    monkeypatch.setattr(
        cli._confidence_refresh, "refresh",
        lambda *a, **k: calls.append((a, k)) or cli._confidence_refresh.RefreshResult(count=0),
    )

    exit_code = _run(docs_root, tmp_path, "--only", "audience-split")

    assert exit_code == 0
    assert len(calls) == 1, "a step that actually ran must trigger the A1 refresh exactly once"


# --------------------------------------------------------------------------- #
# Idempotency -- three consecutive full runs settle and then stay byte-identical
# --------------------------------------------------------------------------- #
def test_three_consecutive_full_runs_are_byte_identical_and_stable_exit_code(tmp_path):
    docs_root = _copy_corpus(_POST_FIXTURE, tmp_path)
    before = _fingerprint(docs_root)

    first = _run(docs_root, tmp_path, "--migrate")
    after_first = _fingerprint(docs_root)
    second = _run(docs_root, tmp_path, "--migrate")
    after_second = _fingerprint(docs_root)
    third = _run(docs_root, tmp_path, "--migrate")
    after_third = _fingerprint(docs_root)

    # FIRST run: a3-screens/screen-sot/feature-sot all have real, genuine
    # pending work and scaffold-or-compose it (needs_llm_fill=true forces INERT).
    # feature-sot's own compose already writes a 7-column §2 skeleton (phase-04), so
    # cap-map finds nothing to WIDEN here -- but its §2 has zero data rows
    # (`claim_state` == "absent"), which is still `!= "filled"` (AD-1), so cap-map
    # itself settles ALREADY+needs_llm_fill=true (folds to INERT) and `mirror-skew`
    # stays refused on cap-map's own fill_pending. This fixture registers no
    # secondary languages (README.md), so mirror-skew's OWN pending is genuinely 0 --
    # it is the prerequisite refusal, not mirror-skew's own work, keeping it INERT
    # (unlike the full real corpus, where retained v26 satellites ALSO keep it
    # permanently INERT -- see the opportunistic sibling test at the bottom of this
    # file for that full-scale behavior).
    #
    # SECOND and THIRD runs: every mechanical step (audience-split..feature-sot)
    # settles ALREADY; cap-map settles ALREADY+needs_llm_fill=true again (the §2 row
    # count never changes without a researcher/phase-07b fill -- nothing in this test
    # ever performs that fill); mirror-skew stays refused. So the run-level category
    # mix keeps at least one INERT forever -- exit 4 on EVERY run, not just the first.
    # This is intended and must be communicated, not softened (phase-07.md Risk
    # Assessment, AD-1 row): `--migrate` cannot exit 0 while any feature's §2 claim
    # cells are unfilled, by design. What idempotency actually guarantees here is
    # BYTES, not the exit code: nothing further is EVER written once the mechanical
    # steps have run once -- disk state is stable from after_first onward, forever.
    assert (first, second, third) == (4, 4, 4)
    assert before != after_first, "first run should have scaffolded/composed something"
    assert after_first == after_second == after_third


# =========================================================================== #
# OPPORTUNISTIC -- real-scale (66 features / 182 screens) re-assertions of the
# same properties above, against a previous session's scratch corpus copy. Each
# test below is individually skipif-guarded with a reason string that reads
# nothing like a load-bearing failure. Absence of `_OPPORTUNISTIC_POST_SRC` on
# this machine (a fresh checkout, CI, or `/tmp` cleared) skips ONLY these two
# tests -- every test above this line still runs and still proves the same
# behavior against the committed fixtures.
# =========================================================================== #
@pytest.mark.skipif(not _OPPORTUNISTIC_POST_SRC.is_dir(), reason=_OPPORTUNISTIC_SKIP_REASON)
def test_opportunistic_full_scale_corpus_dry_run_reports_real_pending_counts(tmp_path, capsys):
    docs_root = _copy_corpus(_OPPORTUNISTIC_POST_SRC, tmp_path)
    before = _fingerprint(docs_root)

    exit_code = _run(docs_root, tmp_path, "--migrate", "--dry-run")

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "[DRY-RUN] step=audience-split pending=0 prerequisite=none status=ready" in out
    # a3-screens's prerequisite repointed straight to audience-split in phase 09 (the
    # now-retired a3-b4 step used to sit between them) -- audience-split has nothing
    # pending on this corpus, so a3-screens reads status=ready here, not blocked.
    assert "[DRY-RUN] step=a3-screens pending=182 prerequisite=audience-split status=ready" in out
    assert "[DRY-RUN] step=screen-sot pending=182 prerequisite=a3-screens status=blocked" in out
    assert "[DRY-RUN] step=feature-sot pending=66 prerequisite=screen-sot status=blocked" in out
    # cap-map: pending=0 -- this scratch corpus is still pre-SOT (st-post is NOT
    # sealed; every functional-spec.md still carries `## 2. Open Decisions`, not
    # `## 2. Functional Capabilities`), so cap-map correctly reports "not my problem
    # yet" for all 66 (AD-1: never double-counts a file feature-sot still owns).
    # action-thread: pending=0 for the identical reason, one file over -- this
    # corpus's technical-spec.md is also still pre-SOT (no `## 3. System Design`,
    # feature-sot's own output shape), so action-thread correctly defers too.
    # mirror-skew's prerequisite is now action-thread (0) rather than feature-sot
    # (66) or cap-map, so its status reads "ready" here even though the corpus is
    # nowhere near done end to end -- each step gates only on its OWN immediate
    # prerequisite, never the whole transitive chain (true of every step, not new to
    # cap-map or action-thread). mirror-skew's own pending=2 is unaffected -- that
    # count comes from its real stale-mirror scan.
    assert "[DRY-RUN] step=cap-map pending=0 prerequisite=feature-sot status=blocked" in out
    assert "[DRY-RUN] step=action-thread pending=0 prerequisite=cap-map status=ready" in out
    assert "[DRY-RUN] step=mirror-skew pending=2 prerequisite=action-thread status=ready" in out
    assert _fingerprint(docs_root) == before, "--dry-run must write NOTHING"


@pytest.mark.skipif(not _OPPORTUNISTIC_POST_SRC.is_dir(), reason=_OPPORTUNISTIC_SKIP_REASON)
def test_opportunistic_full_scale_corpus_three_runs_are_byte_identical(tmp_path):
    docs_root = _copy_corpus(_OPPORTUNISTIC_POST_SRC, tmp_path)
    before = _fingerprint(docs_root)

    first = _run(docs_root, tmp_path, "--migrate")
    after_first = _fingerprint(docs_root)
    second = _run(docs_root, tmp_path, "--migrate")
    after_second = _fingerprint(docs_root)
    third = _run(docs_root, tmp_path, "--migrate")
    after_third = _fingerprint(docs_root)

    # On the FULL real corpus, mirror-skew never settles to ALREADY across these
    # three runs: 66 feature dirs retain v26 satellites pending human review, so the
    # translate handoff stays refused and mirror-skew reports INERT every time --
    # exit 4, identically, all three runs (unlike the small committed fixture above,
    # which registers no secondary languages and settles after run one).
    assert first == second == third == 4
    assert before != after_first, "first run should have scaffolded/composed something"
    assert after_first == after_second == after_third
