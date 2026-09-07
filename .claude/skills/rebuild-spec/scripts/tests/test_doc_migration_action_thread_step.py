"""Tests for `_doc_migration_action_thread_step_lib.py` -- the `action-thread`
`--migrate` step (phase-06, plans/260824-1128-rebuild-spec-action-thread-v27-7):
`count_pending`, `run`, AND `rollback`.

FIXTURE PROVENANCE: `tests/fixtures/action_thread/` (F011/F017) are VERBATIM copies
of real, already-migrated (v27-shaped) corpus output -- see that directory's own
README.md. Never hand-authored, per the plan's own Risk Assessment. This file
exercises the MIGRATE-STEP plumbing (pending predicate, backup/sidecar/write,
rollback) around `compose_action_thread`; the composer's own reshape correctness is
`test_action_thread_composer.py`'s job, not repeated here.

Two composer facts this file's rollback tests lean on directly (measured against the
real fixtures, not assumed): F011 (6 BR + 3 DEC blocks) produces its 3 unresolved
markers as the "no resolvable owner" sentence (DEC blocks carry no `**Applies to:**`
field at all -- preflight C11), while F017 (zero actions) produces its 3 as the
"carried from **Applies to:**" sentence. `_UNVERIFIED_MARKER` in the step lib counts
the shared "[UNVERIFIED]" TAG rather than either literal sentence alone -- exactly so
neither fixture's shape goes uncounted.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import _doc_migration_action_thread_step_lib as lib  # noqa: E402

_FIXTURES = _TESTS_DIR / "fixtures" / "action_thread"
assert _FIXTURES.is_dir(), f"committed fixture missing: {_FIXTURES}"


def _seed(docs_root: Path, slug: str, dirname: str, *, with_functional: bool = True) -> Path:
    feature_dir = docs_root / "features" / dirname
    feature_dir.mkdir(parents=True)
    tech_path = feature_dir / "technical-spec.md"
    tech_path.write_text(
        (_FIXTURES / f"{slug}_technical-spec.md").read_text(encoding="utf-8"), encoding="utf-8",
    )
    if with_functional:
        (feature_dir / "functional-spec.md").write_text(
            (_FIXTURES / f"{slug}_functional-spec.md").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    return feature_dir


def _seed_dir(docs_root: Path, dirname: str, fixture_dir: Path) -> Path:
    """Like `_seed`, but for a fixture stored as its OWN `<dirname>/technical-
    spec.md` + `functional-spec.md` pair (the `backfill-pending/` shape) rather
    than the flat `{slug}_technical-spec.md` naming `_seed` reads."""
    feature_dir = docs_root / "features" / dirname
    feature_dir.mkdir(parents=True)
    for name in ("technical-spec.md", "functional-spec.md"):
        (feature_dir / name).write_text(
            (fixture_dir / name).read_text(encoding="utf-8"), encoding="utf-8",
        )
    return feature_dir


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fingerprint(root: Path) -> dict:
    out = {}
    for f in sorted(root.rglob("*")):
        if f.is_file():
            out[str(f.relative_to(root))] = hashlib.sha256(f.read_bytes()).hexdigest()
    return out


# --------------------------------------------------------------------------- #
# count_pending -- [AD-1] artifact-derived, never a marker file
# --------------------------------------------------------------------------- #
class TestCountPending:
    def test_layer_first_shape_is_pending(self, tmp_path):
        docs = tmp_path / "docs"
        _seed(docs, "F011", "F011_ListingModeration")
        assert lib.count_pending(docs, tmp_path, None) == 1

    def test_two_pending_features_count_both(self, tmp_path):
        docs = tmp_path / "docs"
        _seed(docs, "F011", "F011_ListingModeration")
        _seed(docs, "F017", "F017_TransportAndCookieSecurity")
        assert lib.count_pending(docs, tmp_path, None) == 2

    def test_already_migrated_with_unresolved_rules_still_counts_as_pending(self, tmp_path):
        # A file already reshaped but still carrying an [UNVERIFIED] marker is NOT
        # "done" -- mirrors cap-map's own shape_pending + fill_pending split.
        docs = tmp_path / "docs"
        _seed(docs, "F017", "F017_TransportAndCookieSecurity")
        lib.run(docs, tmp_path, None)
        assert lib.count_pending(docs, tmp_path, None) == 1

    def test_count_pending_never_writes(self, tmp_path):
        docs = tmp_path / "docs"
        feature_dir = _seed(docs, "F011", "F011_ListingModeration")
        before = _sha(feature_dir / "technical-spec.md")
        lib.count_pending(docs, tmp_path, None)
        assert _sha(feature_dir / "technical-spec.md") == before
        assert not (docs / ".migrate-v27").exists(), "count_pending must never touch the .bak tree"

    def test_unreadable_technical_spec_is_skipped_not_counted(self, tmp_path):
        docs = tmp_path / "docs"
        (docs / "features" / "F999_Bad").mkdir(parents=True)
        (docs / "features" / "F999_Bad" / "technical-spec.md").mkdir()  # a dir, not a file
        assert lib.count_pending(docs, tmp_path, None) == 0

    def test_features_filter_scopes_to_named_feature(self, tmp_path):
        docs = tmp_path / "docs"
        _seed(docs, "F011", "F011_ListingModeration")
        _seed(docs, "F017", "F017_TransportAndCookieSecurity")
        assert lib.count_pending(docs, tmp_path, frozenset({"F011_ListingModeration"})) == 1


# --------------------------------------------------------------------------- #
# run() -- reshape + backup + sidecar, per-feature isolation
# --------------------------------------------------------------------------- #
class TestRun:
    def test_composes_to_action_thread_shape_and_backs_up_the_original(self, tmp_path):
        docs = tmp_path / "docs"
        feature_dir = _seed(docs, "F011", "F011_ListingModeration")
        original = (feature_dir / "technical-spec.md").read_text(encoding="utf-8")

        result = lib.run(docs, tmp_path, None)

        assert result.category == "progress"
        new_text = (feature_dir / "technical-spec.md").read_text(encoding="utf-8")
        assert "## 2. Action Index" in new_text
        assert "## 3. System Design" not in new_text
        bak = docs / ".migrate-v27" / "action-thread" / "F011_ListingModeration" / "technical-spec.md.bak"
        assert bak.is_file()
        assert bak.read_text(encoding="utf-8") == original

    def test_bak_and_sidecar_live_outside_docs_features_tree(self, tmp_path):
        # Security Considerations: `.bak`/sidecar must never land where a later pass
        # could publish them.
        docs = tmp_path / "docs"
        _seed(docs, "F011", "F011_ListingModeration")
        lib.run(docs, tmp_path, None)
        staging = docs / ".migrate-v27" / "action-thread"
        assert staging.is_dir()
        assert not any((docs / "features" / "F011_ListingModeration").glob("*.bak"))

    def test_sidecar_records_the_unverified_count_actually_written(self, tmp_path):
        docs = tmp_path / "docs"
        feature_dir = _seed(docs, "F017", "F017_TransportAndCookieSecurity")
        lib.run(docs, tmp_path, None)

        new_text = (feature_dir / "technical-spec.md").read_text(encoding="utf-8")
        expected = new_text.count("[UNVERIFIED]")
        assert expected == 3, "F017 must produce exactly its 3 known unresolved BR rules"
        sidecar = docs / ".migrate-v27" / "action-thread" / "F017_TransportAndCookieSecurity" / "unverified-count.json"
        recorded = json.loads(sidecar.read_text(encoding="utf-8"))
        assert recorded == {"unverified_count": expected}

    def test_dec_only_unresolved_shape_f011_is_also_counted(self, tmp_path):
        # F011's 3 unresolved rules are DEC blocks -- the "no resolvable owner"
        # sentence, NOT "carried from **Applies to:**". A sidecar counting only the
        # latter phrase would silently record 0 here.
        docs = tmp_path / "docs"
        feature_dir = _seed(docs, "F011", "F011_ListingModeration")
        lib.run(docs, tmp_path, None)

        new_text = (feature_dir / "technical-spec.md").read_text(encoding="utf-8")
        assert new_text.count("[UNVERIFIED] no resolvable owner") == 3
        assert new_text.count("[UNVERIFIED] carried from **Applies to:**") == 0
        sidecar = docs / ".migrate-v27" / "action-thread" / "F011_ListingModeration" / "unverified-count.json"
        recorded = json.loads(sidecar.read_text(encoding="utf-8"))
        assert recorded == {"unverified_count": 3}

    def test_needs_llm_fill_true_when_unresolved_rules_remain(self, tmp_path):
        docs = tmp_path / "docs"
        _seed(docs, "F011", "F011_ListingModeration")
        result = lib.run(docs, tmp_path, None)
        assert result.needs_llm_fill is True

    def test_run_never_writes_when_nothing_is_pending(self, tmp_path):
        docs = tmp_path / "docs"
        feature_dir = _seed(docs, "F011", "F011_ListingModeration")
        lib.run(docs, tmp_path, None)  # first pass -- real progress
        after_first = _sha(feature_dir / "technical-spec.md")

        result = lib.run(docs, tmp_path, None)  # second pass -- idempotent no-op

        assert result.category == "already"
        assert result.needs_llm_fill is True  # F011's 3 DEC rules never auto-resolve
        assert _sha(feature_dir / "technical-spec.md") == after_first

    def test_missing_functional_spec_twin_is_reported_failed_not_silently_skipped(self, tmp_path, capsys):
        docs = tmp_path / "docs"
        _seed(docs, "F011", "F011_ListingModeration", with_functional=False)

        result = lib.run(docs, tmp_path, None)

        assert result.category == "failed"
        assert "functional-spec.md" in result.message
        assert "F011_ListingModeration" in result.message

    def test_one_bad_feature_does_not_abort_the_others(self, tmp_path):
        docs = tmp_path / "docs"
        _seed(docs, "F011", "F011_ListingModeration")
        _seed(docs, "F017", "F017_TransportAndCookieSecurity", with_functional=False)

        result = lib.run(docs, tmp_path, None)

        assert result.category == "failed"
        assert "F017_TransportAndCookieSecurity" in result.message
        assert "1 composed before the failure" in result.message
        good_text = (docs / "features" / "F011_ListingModeration" / "technical-spec.md").read_text(
            encoding="utf-8",
        )
        assert "## 2. Action Index" in good_text, "the good feature must still be composed"


# --------------------------------------------------------------------------- #
# rollback() -- the naive "refuse if filled" predicate is WRONG here (merge blocker)
# --------------------------------------------------------------------------- #
class TestRollback:
    def test_fresh_migration_rolls_back_and_succeeds(self, tmp_path):
        # THE case the naive `cap-map`-style predicate broke: `compose_action_thread`
        # itself is what fills/marks the claims, so "refuse if filled" would refuse
        # EVERY successful migration and rollback could never run at all.
        docs = tmp_path / "docs"
        feature_dir = _seed(docs, "F011", "F011_ListingModeration")
        original = (feature_dir / "technical-spec.md").read_text(encoding="utf-8")
        run_result = lib.run(docs, tmp_path, None)
        assert run_result.category == "progress"

        rb_result = lib.rollback(docs, tmp_path, None)

        assert rb_result.category == "progress"
        assert (feature_dir / "technical-spec.md").read_text(encoding="utf-8") == original
        bak = docs / ".migrate-v27" / "action-thread" / "F011_ListingModeration" / "technical-spec.md.bak"
        assert not bak.exists(), "rollback() must remove the .bak it restores from"

    def test_fresh_migration_of_both_fixtures_rolls_back_byte_identical(self, tmp_path):
        docs = tmp_path / "docs"
        before = {}
        for slug, dirname in (("F011", "F011_ListingModeration"), ("F017", "F017_TransportAndCookieSecurity")):
            feature_dir = _seed(docs, slug, dirname)
            before[dirname] = (feature_dir / "technical-spec.md").read_text(encoding="utf-8")
        lib.run(docs, tmp_path, None)

        rb_result = lib.rollback(docs, tmp_path, None)

        assert rb_result.category == "progress"
        for dirname, original in before.items():
            restored = (docs / "features" / dirname / "technical-spec.md").read_text(encoding="utf-8")
            assert restored == original

    def test_refuses_when_unverified_count_has_dropped(self, tmp_path, capsys):
        # THE protection the naive predicate would have destroyed: a researcher
        # resolved one rule's ownership by hand since migrate ran -- restoring the
        # pre-migration file must not be allowed to throw that work away.
        docs = tmp_path / "docs"
        feature_dir = _seed(docs, "F017", "F017_TransportAndCookieSecurity")
        lib.run(docs, tmp_path, None)
        tech_path = feature_dir / "technical-spec.md"
        migrated_text = tech_path.read_text(encoding="utf-8")
        assert migrated_text.count("[UNVERIFIED]") == 3
        resolved_text = migrated_text.replace("[UNVERIFIED]", "[RESOLVED]", 1)  # drop ONE, not all
        tech_path.write_text(resolved_text, encoding="utf-8")

        rb_result = lib.rollback(docs, tmp_path, None)

        assert rb_result.category == "failed"
        err = capsys.readouterr().err
        assert "[REFUSED] action-thread rollback: F017_TransportAndCookieSecurity" in err
        assert "dropped 3 -> 2" in err
        assert tech_path.read_text(encoding="utf-8") == resolved_text, "refused feature must be untouched"
        bak = docs / ".migrate-v27" / "action-thread" / "F017_TransportAndCookieSecurity" / "technical-spec.md.bak"
        assert bak.is_file(), "a refused rollback must not remove the backup either"

    def test_refuses_one_feature_but_still_restores_the_other(self, tmp_path):
        docs = tmp_path / "docs"
        f011 = _seed(docs, "F011", "F011_ListingModeration")
        f017 = _seed(docs, "F017", "F017_TransportAndCookieSecurity")
        lib.run(docs, tmp_path, None)
        f017_tech = f017 / "technical-spec.md"
        lines = [line for line in f017_tech.read_text(encoding="utf-8").splitlines()
                 if "[UNVERIFIED]" not in line]
        f017_tech.write_text("\n".join(lines) + "\n", encoding="utf-8")
        f011_migrated = (f011 / "technical-spec.md").read_text(encoding="utf-8")

        rb_result = lib.rollback(docs, tmp_path, None)

        assert rb_result.category == "failed"
        assert "1 feature dir(s) refused" in rb_result.message
        assert "restored the other 1" in rb_result.message
        assert (f011 / "technical-spec.md").read_text(encoding="utf-8") != f011_migrated, (
            "F011 (count unchanged since migrate) must still be restored"
        )

    def test_a_count_that_only_rose_is_safe_to_restore(self, tmp_path):
        # A count that stayed the same or ROSE is safe -- only a DROP is the signal
        # of hand-resolved work. A researcher (or another tool) appending a fresh
        # unresolved marker is not "resolving" anything.
        docs = tmp_path / "docs"
        feature_dir = _seed(docs, "F017", "F017_TransportAndCookieSecurity")
        lib.run(docs, tmp_path, None)
        tech_path = feature_dir / "technical-spec.md"
        tech_path.write_text(
            tech_path.read_text(encoding="utf-8") + "\n[UNVERIFIED] extra note\n", encoding="utf-8",
        )

        rb_result = lib.rollback(docs, tmp_path, None)

        assert rb_result.category == "progress"

    def test_missing_sidecar_never_refuses(self, tmp_path):
        # A `.bak` with no readable sidecar (e.g. the sidecar was deleted by hand) is
        # treated as "nothing recorded" -- restore proceeds rather than refusing on
        # data that isn't there.
        docs = tmp_path / "docs"
        feature_dir = _seed(docs, "F017", "F017_TransportAndCookieSecurity")
        lib.run(docs, tmp_path, None)
        sidecar = docs / ".migrate-v27" / "action-thread" / "F017_TransportAndCookieSecurity" / "unverified-count.json"
        sidecar.unlink()

        rb_result = lib.rollback(docs, tmp_path, None)

        assert rb_result.category == "progress"

    def test_no_backups_reports_already(self, tmp_path):
        docs = tmp_path / "docs"
        _seed(docs, "F011", "F011_ListingModeration")  # never run() -- no .bak exists
        result = lib.rollback(docs, tmp_path, None)
        assert result.category == "already"

    def test_symlinked_backup_is_refused_not_followed(self, tmp_path):
        docs = tmp_path / "docs"
        feature_dir = _seed(docs, "F011", "F011_ListingModeration")
        lib.run(docs, tmp_path, None)
        bak = docs / ".migrate-v27" / "action-thread" / "F011_ListingModeration" / "technical-spec.md.bak"
        target = tmp_path / "outside.txt"
        target.write_text("evil", encoding="utf-8")
        bak.unlink()
        bak.symlink_to(target)

        result = lib.rollback(docs, tmp_path, None)

        assert result.category == "failed"
        assert "symlinked backup" in result.message
        assert (feature_dir / "technical-spec.md").read_text(encoding="utf-8") != "evil"


# --------------------------------------------------------------------------- #
# Idempotence -- three consecutive run()s settle and stay byte-identical
# --------------------------------------------------------------------------- #
def test_three_consecutive_runs_are_byte_identical(tmp_path):
    docs = tmp_path / "docs"
    _seed(docs, "F011", "F011_ListingModeration")
    _seed(docs, "F017", "F017_TransportAndCookieSecurity")

    lib.run(docs, tmp_path, None)
    after_first = _fingerprint(docs)
    lib.run(docs, tmp_path, None)
    after_second = _fingerprint(docs)
    lib.run(docs, tmp_path, None)
    after_third = _fingerprint(docs)

    assert after_first == after_second == after_third


# --------------------------------------------------------------------------- #
# C1 -- the generalized reopen predicate (self-sufficiency v27.8, phase 02).
# `backfill-pending/` (hand-authored SYNTHETIC, per that fixture's own docstring)
# is already Action-Index-shaped, carries zero [UNVERIFIED] markers, one real
# SM-### block, and one writing action with no State rung -- the exact shape the
# pre-C1 predicate treated as permanently done even once `state_rung_missing`
# (registered in `_action_thread_reopen_lib.REOPEN_RULE_IDS`) started firing on it.
# --------------------------------------------------------------------------- #
_BACKFILL_PENDING = _FIXTURES / "backfill-pending"
assert _BACKFILL_PENDING.is_dir(), f"committed fixture missing: {_BACKFILL_PENDING}"
_CLEAN_MIGRATED = (
    _TESTS_DIR / "fixtures" / "corpora" / "action-thread-shapes" / "F950_CleanMigrated"
)
assert _CLEAN_MIGRATED.is_dir(), f"committed fixture missing: {_CLEAN_MIGRATED}"


def _graduated_backfill_text() -> str:
    """`backfill-pending`'s own text, with a **State** rung inserted by hand (test
    data, never composer logic) so `state_rung_missing` no longer fires -- the
    "researcher already finished the fill pass" end state C1's reopen exists to
    reach. Used ONLY by the over-broad-reopen regression-guard test below."""
    text = (_BACKFILL_PENDING / "technical-spec.md").read_text(encoding="utf-8")
    old = ("**Result** · `listings.state` flips `pending` → `approved`.\n**Source:**")
    new = (
        "**Result** · `listings.state` flips `pending` → `approved`.\n"
        "**State** · `listings.state`: `pending` → `approved`.\n**Source:**"
    )
    assert old in text, "fixture shape changed -- update this derivation"
    return text.replace(old, new)


class TestC1ReopenPredicate:
    def test_count_pending_counts_a_file_a_new_detector_now_flags(self, tmp_path):
        # THE bug, reproduced against the ORIGINAL pre-fix module (git HEAD) before
        # this test asserts the FIXED behaviour below -- see phase-02.md proof
        # obligation #1 ("reproduce BEFORE fixing"). Kept as a live regression
        # guard: if the fix ever regresses, `count_pending` silently returns to 0.
        docs = tmp_path / "docs"
        _seed_dir(docs, "F999_BackfillPending", _BACKFILL_PENDING)
        assert lib.count_pending(docs, tmp_path, None) == 1

    def test_run_reopens_and_reports_progress_without_inventing_content(self, tmp_path):
        docs = tmp_path / "docs"
        feature_dir = _seed_dir(docs, "F999_BackfillPending", _BACKFILL_PENDING)
        original = (feature_dir / "technical-spec.md").read_text(encoding="utf-8")

        result = lib.run(docs, tmp_path, None)

        assert result.category == "progress"
        assert result.needs_llm_fill is True
        # `compose_action_thread` is a guaranteed no-op on text already carrying
        # "## 2. Action Index" -- reopening must never guess a FROM state (D3);
        # the byte content stays identical, only the file's PENDING STATUS moves.
        assert (feature_dir / "technical-spec.md").read_text(encoding="utf-8") == original

    def test_reopened_write_leaves_a_bak_and_rollback_restores_it(self, tmp_path):
        docs = tmp_path / "docs"
        feature_dir = _seed_dir(docs, "F999_BackfillPending", _BACKFILL_PENDING)
        original = (feature_dir / "technical-spec.md").read_text(encoding="utf-8")

        lib.run(docs, tmp_path, None)

        bak = (docs / ".migrate-v27" / "action-thread" / "F999_BackfillPending"
               / "technical-spec.md.bak")
        assert bak.is_file(), "a reopened write with no .bak is unrollbackable data loss"
        assert bak.read_text(encoding="utf-8") == original

        rb_result = lib.rollback(docs, tmp_path, None)

        assert rb_result.category == "progress"
        assert (feature_dir / "technical-spec.md").read_text(encoding="utf-8") == original
        assert not bak.exists(), "rollback() must remove the .bak it restores from"

    def test_third_run_reports_already_and_stays_byte_identical(self, tmp_path):
        docs = tmp_path / "docs"
        feature_dir = _seed_dir(docs, "F999_BackfillPending", _BACKFILL_PENDING)
        lib.run(docs, tmp_path, None)  # first reopen (2nd overall call) -- real progress
        after_first = _sha(feature_dir / "technical-spec.md")

        result = lib.run(docs, tmp_path, None)  # 3rd overall call -- already surfaced

        assert result.category == "already"
        assert result.needs_llm_fill is True  # state_rung_missing has no in-Python fix
        assert _sha(feature_dir / "technical-spec.md") == after_first

    def test_sidecar_records_which_rule_ids_the_reopen_surfaced(self, tmp_path):
        docs = tmp_path / "docs"
        _seed_dir(docs, "F999_BackfillPending", _BACKFILL_PENDING)

        lib.run(docs, tmp_path, None)

        sidecar = (docs / ".migrate-v27" / "action-thread" / "F999_BackfillPending"
                   / "unverified-count.json")
        recorded = json.loads(sidecar.read_text(encoding="utf-8"))
        assert recorded == {
            "unverified_count": 0,
            "reopened_rule_ids": ["FeatureSpec.state_rung_missing"],
        }

    def test_over_broad_reopen_regression_guard_skips_a_file_with_nothing_firing(self, tmp_path):
        # The researcher fill pass finished by hand (State rung present) -- no
        # REOPEN_RULE_IDS member fires any more. Must stay untouched forever, not
        # reopened merely because it is Action-Index-shaped with 0 [UNVERIFIED].
        docs = tmp_path / "docs"
        feature_dir = docs / "features" / "F999_Graduated"
        feature_dir.mkdir(parents=True)
        graduated_text = _graduated_backfill_text()
        (feature_dir / "technical-spec.md").write_text(graduated_text, encoding="utf-8")
        (feature_dir / "functional-spec.md").write_text(
            (_BACKFILL_PENDING / "functional-spec.md").read_text(encoding="utf-8"),
            encoding="utf-8",
        )

        assert lib.count_pending(docs, tmp_path, None) == 0

        result = lib.run(docs, tmp_path, None)

        assert result.category == "already"
        assert result.needs_llm_fill is False
        assert (feature_dir / "technical-spec.md").read_text(encoding="utf-8") == graduated_text
        bak = (docs / ".migrate-v27" / "action-thread" / "F999_Graduated"
               / "technical-spec.md.bak")
        assert not bak.exists(), "nothing NEW firing -- must never be reopened/written"

    def test_over_broad_reopen_regression_guard_never_reopens_a_bare_unverified_marker_file(
        self, tmp_path,
    ):
        # A file already counted pending via the EXISTING [UNVERIFIED]-marker path
        # (unaffected by C1) must not ALSO take the reopen path on the same run --
        # F011 legitimately carries both 3 unresolved DEC markers AND
        # `state_rung_missing` findings; only ONE of the two pending signals may
        # drive `run()`'s write decision, or idempotency breaks (see
        # test_run_never_writes_when_nothing_is_pending).
        docs = tmp_path / "docs"
        feature_dir = _seed(docs, "F011", "F011_ListingModeration")
        lib.run(docs, tmp_path, None)  # legacy pre-thread compose
        after_first = _sha(feature_dir / "technical-spec.md")

        result = lib.run(docs, tmp_path, None)

        assert result.category == "already"
        assert result.needs_llm_fill is True
        assert _sha(feature_dir / "technical-spec.md") == after_first
        sidecar = json.loads(
            (docs / ".migrate-v27" / "action-thread" / "F011_ListingModeration"
             / "unverified-count.json").read_text(encoding="utf-8")
        )
        assert "reopened_rule_ids" not in sidecar, (
            "the marker-pending path and the C1 reopen path must not both fire for "
            "the same file"
        )


# --------------------------------------------------------------------------- #
# Retired-section strip (phase 08, self-sufficiency v27.8) -- the deletion-
# direction twin of C1 above. `FeatureSpec.retired_section_present` registered
# into `REOPEN_RULE_IDS` drives `compose_action_thread`'s one-shot A3/B4 strip
# through the SAME reopen mechanism `state_rung_missing` uses -- never a second
# one. Built on `backfill-pending`'s own (now A3/B4-free) content plus the exact
# trailing sections phase 08 stripped from that committed fixture, reconstructed
# here rather than re-introducing stale A3/B4 content into the fixture the OTHER
# tests in this module rely on staying clean.
# --------------------------------------------------------------------------- #
def _backfill_pending_with_retired_sections() -> str:
    """`backfill-pending/technical-spec.md`'s current (A3/B4-free) content, with
    the exact `## Source Walkthrough` + `## DB Impact per Event` trailing
    sections it carried BEFORE phase 08 stripped them from the committed
    fixture, appended back on verbatim -- lets this test prove the one-shot
    strip fires on an already-action-thread-shaped file without mutating the
    shared fixture other tests in this module depend on."""
    text = (_BACKFILL_PENDING / "technical-spec.md").read_text(encoding="utf-8")
    retired = (
        "\n\n## Source Walkthrough\n\n"
        "1. **File:** `app/controllers/listings/moderation_controller.rb:1-20` — "
        "start here: the\n   `approve`/`reject` member actions.\n"
        "2. **File:** `app/services/listing/moderation_service.rb:1-30` — next: "
        "the pending-only\n   transition guard.\n\n"
        "### Call Hierarchy\n\n"
        "```text\n"
        "POST /listings/:id/approve\n"
        "  -> Listings::ModerationController#approve\n"
        "       -> Listing::ModerationService#approve!  (BR-001)\n"
        "```\n\n"
        "**Related files:** see `### 5.4 Source References` above.\n\n"
        "## DB Impact per Event\n\n"
        "| Action | Event | Table | Operation | Notes |\n"
        "|--------|-------|-------|-----------|-------|\n"
        "| A1 | approve | listings | UPDATE | `state` flips `pending` -> `approved` |\n"
    )
    return text.rstrip("\n") + retired


def _seed_retired_sections(docs: Path) -> Path:
    feature_dir = docs / "features" / "F999_RetiredSections"
    feature_dir.mkdir(parents=True)
    (feature_dir / "technical-spec.md").write_text(
        _backfill_pending_with_retired_sections(), encoding="utf-8",
    )
    (feature_dir / "functional-spec.md").write_text(
        (_BACKFILL_PENDING / "functional-spec.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return feature_dir


class TestRetiredSectionStripReopen:
    def test_count_pending_counts_a_file_still_carrying_a3_or_b4(self, tmp_path):
        docs = tmp_path / "docs"
        _seed_retired_sections(docs)
        assert lib.count_pending(docs, tmp_path, None) == 1

    def test_run_strips_a3_b4_and_leaves_a_bak_rollback_restores_it(self, tmp_path):
        docs = tmp_path / "docs"
        feature_dir = _seed_retired_sections(docs)
        original = (feature_dir / "technical-spec.md").read_text(encoding="utf-8")

        result = lib.run(docs, tmp_path, None)

        assert result.category == "progress"
        stripped = (feature_dir / "technical-spec.md").read_text(encoding="utf-8")
        assert "## Source Walkthrough" not in stripped
        assert "## DB Impact per Event" not in stripped
        assert stripped != original

        bak = (docs / ".migrate-v27" / "action-thread" / "F999_RetiredSections"
               / "technical-spec.md.bak")
        assert bak.is_file(), "a reopened strip with no .bak is unrollbackable data loss"
        assert bak.read_text(encoding="utf-8") == original

        rb_result = lib.rollback(docs, tmp_path, None)
        assert rb_result.category == "progress"
        assert (feature_dir / "technical-spec.md").read_text(encoding="utf-8") == original
        assert not bak.exists(), "rollback() must remove the .bak it restores from"

    def test_second_run_reports_already_and_stays_byte_identical(self, tmp_path):
        # `state_rung_missing` still fires after the strip (unaffected by it --
        # backfill-pending's own condition), so the second run is `already` with
        # fill still owed, never a fully clean file -- mirrors
        # test_third_run_reports_already_and_stays_byte_identical above.
        docs = tmp_path / "docs"
        feature_dir = _seed_retired_sections(docs)

        lib.run(docs, tmp_path, None)  # strips A3/B4 -- real progress
        after_first = _sha(feature_dir / "technical-spec.md")

        result = lib.run(docs, tmp_path, None)

        assert result.category == "already"
        assert _sha(feature_dir / "technical-spec.md") == after_first
        stripped = (feature_dir / "technical-spec.md").read_text(encoding="utf-8")
        assert "## Source Walkthrough" not in stripped
        assert "## DB Impact per Event" not in stripped

    def test_strip_still_fires_when_unverified_markers_are_ALSO_pending(self, tmp_path):
        """THE bug this restructure closes, reproduced then proven fixed: the
        REAL 43-feature corpus measured 43/43 files carrying BOTH unresolved
        [UNVERIFIED] markers (a researcher fill pass still owed) AND A3/B4 --
        the pre-fix `run()` short-circuited on `_unverified_count(text) > 0`
        BEFORE ever computing `firing_reopen_rule_ids`, so `retired_firing`
        never even got a chance to run the mechanical strip until an unrelated
        researcher resolved the markers by hand. Reproduced here directly: a
        fixture with one genuine `[UNVERIFIED]` marker (DEC, no resolvable
        owner) stacked on top of `_backfill_pending_with_retired_sections`'s
        own A3/B4 content."""
        docs = tmp_path / "docs"
        feature_dir = docs / "features" / "F999_MarkerAndRetired"
        feature_dir.mkdir(parents=True)
        text = _backfill_pending_with_retired_sections().replace(
            "**Applies to:** every action on `Listings::ModerationController`.",
            "**Applies to:** every action on `Listings::ModerationController`.\n\n"
            "[UNVERIFIED] no resolvable owner — needs a researcher pass",
        )
        assert "[UNVERIFIED]" in text, "fixture derivation must genuinely inject a marker"
        (feature_dir / "technical-spec.md").write_text(text, encoding="utf-8")
        (feature_dir / "functional-spec.md").write_text(
            (_BACKFILL_PENDING / "functional-spec.md").read_text(encoding="utf-8"),
            encoding="utf-8",
        )

        result = lib.run(docs, tmp_path, None)

        assert result.category == "progress", (
            "marker_pending must NOT block the mechanical A3/B4 strip"
        )
        stripped = (feature_dir / "technical-spec.md").read_text(encoding="utf-8")
        assert "## Source Walkthrough" not in stripped
        assert "## DB Impact per Event" not in stripped
        # The unrelated [UNVERIFIED] marker survives the strip untouched -- the
        # strip is mechanical (section removal only), never content-inventing.
        assert "[UNVERIFIED] no resolvable owner" in stripped

        # Second run: retired_section_present no longer fires (headings gone),
        # but the marker is still there -- `already`, still pending, never a
        # second write for the same finding.
        after_first = _sha(feature_dir / "technical-spec.md")
        result2 = lib.run(docs, tmp_path, None)
        assert result2.category == "already"
        assert _sha(feature_dir / "technical-spec.md") == after_first


# --------------------------------------------------------------------------- #
# Pending breakdown sidecar (phase 07, self-sufficiency v27.8): a SECOND
# sidecar, `pending-breakdown.json`, next to `unverified-count.json` -- never
# merged into it (the exact-equality assertions on that file above are pinned).
# --------------------------------------------------------------------------- #
def _breakdown_sidecar(docs: Path, dirname: str) -> dict:
    path = docs / ".migrate-v27" / "action-thread" / dirname / "pending-breakdown.json"
    return json.loads(path.read_text(encoding="utf-8"))


class TestPendingBreakdownSidecar:
    def test_written_alongside_unverified_count_never_merged_into_it(self, tmp_path):
        docs = tmp_path / "docs"
        _seed(docs, "F017", "F017_TransportAndCookieSecurity")
        lib.run(docs, tmp_path, None)

        staging = docs / ".migrate-v27" / "action-thread" / "F017_TransportAndCookieSecurity"
        unverified = json.loads((staging / "unverified-count.json").read_text(encoding="utf-8"))
        assert unverified == {"unverified_count": 3}, (
            "the existing sidecar's shape must stay exactly what it was -- pinned "
            "by test_sidecar_records_the_unverified_count_actually_written too"
        )
        breakdown = _breakdown_sidecar(docs, "F017_TransportAndCookieSecurity")
        assert breakdown["unverified_tag_count"] == 3
        assert "gated" in breakdown and "dispatched_action_ids" in breakdown

    def test_reopen_records_the_firing_detector_and_its_dispatched_action(self, tmp_path):
        docs = tmp_path / "docs"
        _seed_dir(docs, "F999_BackfillPending", _BACKFILL_PENDING)

        lib.run(docs, tmp_path, None)

        breakdown = _breakdown_sidecar(docs, "F999_BackfillPending")
        assert breakdown["unverified_tag_count"] == 0
        assert breakdown["rule_id_counts"] == {
            "FeatureSpec.state_rung_missing": 1,
            "FeatureSpec.action_ref_unglossed": 0,
            "FeatureSpec.diagram_required_missing": 0,
            "FeatureSpec.rule_bin_misplaced": 0,
            "FeatureSpec.crosscutting_unlabelled": 0,
            # phase 08 (self-sufficiency v27.8): the sixth registered rule_id.
            # `_BACKFILL_PENDING` carries neither retired heading (stripped from
            # the fixture this same phase), so it counts 0 here.
            "FeatureSpec.retired_section_present": 0,
        }
        assert breakdown["dispatched_action_ids"] == ["A1"]
        assert breakdown["gated"] is False, "a fresh reopen always starts ungated"

    def test_rule_id_counts_key_set_equals_reopen_rule_ids(self, tmp_path):
        # Requirement 6: C1's generalization end to end -- the breakdown this
        # step actually persists carries exactly the registry's own key set.
        docs = tmp_path / "docs"
        _seed_dir(docs, "F999_BackfillPending", _BACKFILL_PENDING)
        lib.run(docs, tmp_path, None)
        from _action_thread_reopen_lib import REOPEN_RULE_IDS
        breakdown = _breakdown_sidecar(docs, "F999_BackfillPending")
        assert set(breakdown["rule_id_counts"]) == set(REOPEN_RULE_IDS)

    def test_handoff_message_summarizes_the_breakdown(self, tmp_path):
        docs = tmp_path / "docs"
        _seed_dir(docs, "F999_BackfillPending", _BACKFILL_PENDING)

        result = lib.run(docs, tmp_path, None)

        assert "state_rung_missing=1" in result.message
        assert "feature=F999_BackfillPending" in result.message

    def test_exit4_handoff_contract_is_unaffected(self, tmp_path):
        # The registry's own fail-closed contract (`_effective_category`) reads
        # `needs_llm_fill` alone -- the breakdown text riding along in `message`
        # must never change that.
        docs = tmp_path / "docs"
        _seed_dir(docs, "F999_BackfillPending", _BACKFILL_PENDING)
        result = lib.run(docs, tmp_path, None)
        assert result.needs_llm_fill is True
        assert result.category == "progress"


# --------------------------------------------------------------------------- #
# F2 -- the fill-wave crash window's stronger resumability: "marker gone AND
# this unit was gated at least once", not "marker gone" alone.
# --------------------------------------------------------------------------- #
def _simulate_researcher_fill(tech_path: Path) -> None:
    """Hand-insert the **State** rung `backfill-pending`'s A1 block is missing --
    test data standing in for a researcher's fill, never composer logic. Same
    derivation as `_graduated_backfill_text` above, applied in place on disk."""
    text = tech_path.read_text(encoding="utf-8")
    old = "**Result** · `listings.state` flips `pending` → `approved`.\n**Source:**"
    new = (
        "**Result** · `listings.state` flips `pending` → `approved`.\n"
        "**State** · `listings.state`: `pending` → `approved`.\n**Source:**"
    )
    assert old in text, "fixture shape changed -- update this derivation"
    tech_path.write_text(text.replace(old, new), encoding="utf-8")


def _set_gated(docs: Path, dirname: str, value: bool) -> None:
    path = docs / ".migrate-v27" / "action-thread" / dirname / "pending-breakdown.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["gated"] = value
    path.write_text(json.dumps(data), encoding="utf-8")


class TestF2GatedResumability:
    def test_a_feature_run_never_touched_is_exempt(self, tmp_path):
        # Mirrors test_over_broad_reopen_regression_guard_skips_a_file_with_
        # nothing_firing: a hand-authored, never-run() fixture has no staging
        # dir, so F2's regate check never applies to it.
        docs = tmp_path / "docs"
        feature_dir = docs / "features" / "F999_Graduated"
        feature_dir.mkdir(parents=True)
        text = (_BACKFILL_PENDING / "technical-spec.md").read_text(encoding="utf-8")
        old = "**Result** · `listings.state` flips `pending` → `approved`.\n**Source:**"
        new = (
            "**Result** · `listings.state` flips `pending` → `approved`.\n"
            "**State** · `listings.state`: `pending` → `approved`.\n**Source:**"
        )
        (feature_dir / "technical-spec.md").write_text(text.replace(old, new), encoding="utf-8")
        (feature_dir / "functional-spec.md").write_text(
            (_BACKFILL_PENDING / "functional-spec.md").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        assert lib.count_pending(docs, tmp_path, None) == 0

    def test_ungated_resolved_write_stays_pending_not_silently_done(self, tmp_path):
        # THE crash window: content now looks fully resolved (researcher filled
        # the State rung) but the orchestrator never recorded a passed gate --
        # count_pending/run() must NOT call this done.
        docs = tmp_path / "docs"
        feature_dir = _seed_dir(docs, "F999_BackfillPending", _BACKFILL_PENDING)
        lib.run(docs, tmp_path, None)  # reopens; gated stays False
        _simulate_researcher_fill(feature_dir / "technical-spec.md")

        assert lib.count_pending(docs, tmp_path, None) == 1, (
            "an ungated write must not silently read as done"
        )
        result = lib.run(docs, tmp_path, None)
        assert result.category == "already"
        assert result.needs_llm_fill is True
        # And it must never rewrite content that already looks correct -- F2's
        # safety net surfaces the gap, it never re-guesses at content.
        assert "State" in (feature_dir / "technical-spec.md").read_text(encoding="utf-8")

    def test_gated_resolved_write_reports_done_the_flagship_lifecycle(self, tmp_path):
        # Requirement 6's flagship proof, full lifecycle on ONE feature dir:
        # reopen (C1) -> researcher fill (simulated) -> wave gate passes
        # (simulated by the orchestrator's own `gated: true` bookkeeping) ->
        # a subsequent invocation reports done.
        docs = tmp_path / "docs"
        feature_dir = _seed_dir(docs, "F999_BackfillPending", _BACKFILL_PENDING)

        first = lib.run(docs, tmp_path, None)
        assert first.category == "progress"
        assert first.needs_llm_fill is True

        _simulate_researcher_fill(feature_dir / "technical-spec.md")
        _set_gated(docs, "F999_BackfillPending", True)

        assert lib.count_pending(docs, tmp_path, None) == 0

        second = lib.run(docs, tmp_path, None)
        assert second.category == "already"
        assert second.needs_llm_fill is False

    def test_gated_flag_is_preserved_across_a_no_write_refresh(self, tmp_path):
        # A routine re-run that finds the SAME finding set already surfaced must
        # never clobber a `gated: true` the orchestrator already recorded.
        docs = tmp_path / "docs"
        _seed_dir(docs, "F999_BackfillPending", _BACKFILL_PENDING)
        lib.run(docs, tmp_path, None)  # reopens -- gated False
        _set_gated(docs, "F999_BackfillPending", True)

        lib.run(docs, tmp_path, None)  # same finding set already surfaced -- no write

        breakdown = _breakdown_sidecar(docs, "F999_BackfillPending")
        assert breakdown["gated"] is True, "a no-write refresh must preserve gated"


# --------------------------------------------------------------------------- #
# Phase 05 carry-over (defect sweep, plans/260825-1010-...): phase 03 added
# `ThreadComposeResult.unbound_action_count` (actions capability-bucketing
# couldn't trace to the twin's § 2 table -- they still land, correctly, in the
# LAST bucket per contract § 3) but that phase's file-ownership boundary stopped
# at this module's edge, so the count landed and was computed but surfaced
# NOWHERE an operator could see it. This closes that: `run()`'s message (the
# same string `[HANDOFF]`/`[INFO]` print verbatim) must carry the count.
# --------------------------------------------------------------------------- #
def test_unbound_action_count_reaches_the_operator_facing_message(tmp_path):
    """F002 (real corpus fixture, `tests/fixtures/action_thread/`) measured at 9
    unbound actions via `compose_action_thread` directly -- this proves that same
    number reaches `run()`'s returned message, not just the composer's return
    value. RED against pre-fix code: `unbound_action_count` was read nowhere in
    this module at all, so no message ever mentioned it."""
    docs = tmp_path / "docs"
    _seed(docs, "F002", "F002_AuthenticationAndSession")

    result = lib.run(docs, tmp_path, None)

    assert result.category == "progress"
    assert "9" in result.message
    assert "fallback capability bucket" in result.message


def test_unbound_action_count_is_absent_from_the_message_when_zero(tmp_path):
    """F011 has zero unbound actions (measured) -- the message must not carry a
    dangling "0 action(s)..." clause when there is nothing to report."""
    docs = tmp_path / "docs"
    _seed(docs, "F011", "F011_ListingModeration")
    result = lib.run(docs, tmp_path, None)
    assert "fallback capability bucket" not in result.message
