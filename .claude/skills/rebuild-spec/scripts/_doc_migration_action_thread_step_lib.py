#!/usr/bin/env python3
"""_doc_migration_action_thread_step_lib.py -- the `action-thread` `--migrate`
registry step (phase-06, plans/260824-1128-rebuild-spec-action-thread-v27-7):
`count_pending`, `run`, AND `rollback` in one module (this phase's file ownership
grants exactly one CREATE, so all three live here rather than split cap-map-style
across io/rollback/table-widen siblings).

THIN DRIVER over `_feature_sot_technical_lib.compose_action_thread` -- the sole
authority on the v27 (5-bucket) -> v27.7 (action-thread) technical-spec.md reshape
(phase 05, NET-NEW, never a rename of the still-live `compose_technical_sot` the
`feature-sot` step depends on -- preflight C4). This module owns no reshaping logic
of its own: it discovers `features/*/technical-spec.md`, reads the sibling
`functional-spec.md` as the composer's twin input, composes, and writes atomically.

PLACEMENT. `action-thread` sits BETWEEN `cap-map` and `mirror-skew` in `STEP_ORDER`;
`mirror-skew`'s prerequisite moves from `cap-map` to `action-thread` (the fourth move
across four plans -- see `_doc_migration_registry_lib.py`'s own docstring). Forgetting
the rewire lets `mirror-skew` prune mirrors against a technical-spec.md shape that has
not actually converted yet.

PENDING PREDICATE -- artifact-derived (AD-1, non-negotiable), read from the file,
never a marker file: `_spec_constants._TECH_PRE_THREAD_SENTINEL` ("## 3. System
Design") present means the file is still the OLD (layer-first) shape
`compose_technical_sot` produces. A file already reshaped but still carrying an
`[UNVERIFIED]` marker (a rule the composer could not bind to an action --
wire-format-contract.md § 4.4) ALSO counts as pending, mirroring `cap-map`'s own
`shape_pending + fill_pending` split: `mirror-skew` must not proceed past a corpus
with unresolved rule ownership, or the vi/jp translate handoff mirrors an incomplete
bind and re-skews the moment a researcher resolves it.

ROLLBACK -- THE NAIVE PREDICATE IS WRONG (red-team, phase-06.md). Copying `cap-map`'s
own stance ("refuse if the target's claims are filled") would refuse EVERY successful
migration here, because `compose_action_thread` itself is what fills those claims (or
marks them `[UNVERIFIED]`) -- rollback could then never run at all. The correct
predicate instead compares an `[UNVERIFIED]`-marker COUNT across time: `run()` records
the count present in the text it just wrote to a JSON sidecar next to the `.bak`;
`rollback()` refuses ONLY when the LIVE file's current count is LOWER than the
recorded one -- that drop is the signature of a researcher having resolved rules by
hand since migrate ran, and restoring the `.bak` would throw that work away. A count
that stayed the same or rose is safe to restore -- nothing has been resolved since.

`_UNVERIFIED_MARKER` counts the "[UNVERIFIED]" TAG, not one literal sentence --
`compose_action_thread` emits two distinct sentences under that tag (measured against
the real `scripts/tests/fixtures/action_thread/` corpus fixtures): "carried from
**Applies to:**" for a BR rule whose field text failed to resolve, and "no resolvable
owner" for a DEC rule with no `**Applies to:**` field at all (preflight C11: DEC
blocks carry NO such field anywhere in the 43-feature corpus, so every DEC lands in
this second shape, by construction, not by parser weakness). Counting only the first
sentence -- the literal phrase named in the phase brief -- would silently zero out the
sidecar for every DEC-only feature (F011, the plan's own acceptance fixture, is
exactly this shape: 3 DEC blocks, 0 hits for the first sentence) and disable the
rollback protection precisely where DEC-heavy features need it most.

`.bak` and the sidecar live under `<docs_root>/.migrate-v27/action-thread/<feature>/`,
the same convention `_cap_map_io_lib.py` established -- never inside `docs/` proper,
where a later pass could publish them. `atomic_write`/`assert_under` are imported,
not re-copied, from the shared helpers `_cap_map_io_lib.py` / `_slug_lib.py` already
establish for exactly this precedent-write pattern.

C1 (self-sufficiency v27.8, plans/260824-1846-...) -- THE GENERALIZED REOPEN
PREDICATE. The pending predicate above only ever asked "is this file still the OLD
shape?" or "does it carry an [UNVERIFIED] marker?". A feature that finished the
27.7.0 fill pass answers NO to both FOREVER, so a detector registered AFTER that
fill pass (`FeatureSpec.state_rung_missing`, phase 01) fires with no remediation
path: `run()` never even counts it. `needs_reopen`/`firing_reopen_rule_ids`
(`_action_thread_reopen_lib.py`) close this generically -- see that module's
docstring for the mandated invocation contract (D7/F1): this module never
re-implements a firing predicate, it only asks the validator.

Reopen bookkeeping (`_write_reshape`'s `reopened_rule_ids` sidecar field): a
detector like `state_rung_missing` has no in-Python remediation in this phase --
only a researcher fill pass (dispatched by the ORCHESTRATOR, D4, outside this
module) can actually add the missing content -- so the underlying condition keeps
firing run after run. Without bookkeeping, `run()` would reopen and rewrite the
same feature dir on every single invocation forever. The sidecar instead records
which rule_ids a reopen already surfaced; a run whose firing set is already a
subset of what's recorded treats the feature as "already surfaced this finding,
nothing new" (no write) rather than reopening again -- the write only happens once
per NEW finding, not once per invocation.

PENDING BREAKDOWN (phase 07, self-sufficiency v27.8) -- a SECOND sidecar,
`pending-breakdown.json`, lives beside `unverified-count.json` (never merged into
it -- `test_doc_migration_action_thread_step.py`'s exact-equality assertions on
that file's shape are load-bearing and off this phase's file-ownership list).
`_action_thread_pending_breakdown_lib.build_breakdown`/`dispatched_action_ids`
compute its content from the real validator, never grep; `run()` here only owns
writing it and merging in the orchestrator's own `gated` bookkeeping (below).

F2 -- THE FILL-WAVE CRASH WINDOW, disclosed in phase-07.md's risk table and
closed in its STRONGER form where cheap. The wave gate that checks a fill unit's
output runs in the ORCHESTRATOR, strictly AFTER that unit's write has already
landed on disk (D4: Python never dispatches, never gates). Kill the orchestrator
in the gap between the write landing and the gate call, and the artifact-derived
pending predicate above sees content that LOOKS fully resolved (no `[UNVERIFIED]`,
no firing detector) and would otherwise call it done FOREVER, with no record that
the wave gate never actually ran on it. `pending-breakdown.json`'s `gated` field
(bool, orchestrator-owned -- `run()` only ever preserves it, never sets it True)
closes this: `_needs_regate` treats a feature that has a `.migrate-v27` staging
dir (meaning `run()` wrote to it at least once) but whose sidecar's `gated` is
still `False` as STILL PENDING, even once every other signal says done -- forcing
it back into the next fan-out rather than letting an ungated write vanish
silently. A feature `run()` has never touched (no staging dir) is exempt; nothing
here for a gate to have missed. This does not retroactively re-verify the
crashed write's content (that would need the orchestrator's transient pre-fill
snapshot, which no artifact preserves -- inventing a new marker file to persist
it was explicitly rejected, see plan.md phase 07); it converts a SILENT gap into
a PERSISTENTLY SURFACED one, which is the stated bar (D6/H2/C16: name inherited
risk, never carry it silently) applied to a gap this phase can actually move on
cheaply.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _action_thread_pending_breakdown_lib import (  # noqa: E402
    build_breakdown, dispatched_action_ids, summarize_breakdowns,
)
from _action_thread_reopen_lib import firing_reopen_rule_ids, needs_reopen  # noqa: E402
from _audience_split_tally_lib import ALREADY, FAILED, PROGRESS  # noqa: E402
from _cap_map_io_lib import atomic_write  # noqa: E402
from _doc_migration_registry_lib import StepResult  # noqa: E402
from _feature_sot_technical_lib import compose_action_thread  # noqa: E402
from _slug_lib import assert_under  # noqa: E402
from _spec_constants import _TECH_PRE_THREAD_SENTINEL  # noqa: E402

FeatureFilter = "frozenset[str] | None"

_FILL_COMMAND = "run_doc_migrations.py --migrate --only action-thread"
_BACKUP_DIRNAME = "action-thread"

# Phase 08 (self-sufficiency v27.8) -- the subset of REOPEN_RULE_IDS whose
# remediation is MECHANICAL (compose_action_thread's own idempotent strip),
# never a researcher fill pass. `run()` must not gate this remediation behind
# marker-pending bookkeeping the way it correctly does for every other
# registered detector -- see `run()`'s own docstring/comment for why.
_MECHANICAL_REOPEN_RULE_IDS: frozenset[str] = frozenset({"FeatureSpec.retired_section_present"})

# The FAMILY tag, not one literal sentence -- see module docstring for why counting
# only the "carried from **Applies to:**" phrase would blind the sidecar to every
# DEC-only unresolved rule (the "no resolvable owner" sentence).
_UNVERIFIED_MARKER = "[UNVERIFIED]"


def _iter_feature_dirs(docs_root: Path, features: "FeatureFilter" = None) -> list[Path]:
    """Keyed off `technical-spec.md` (this step's own file), matching
    `_doc_migration_feature_sot_step_lib.py`'s precedent of keying off the file the
    step itself owns."""
    dirs = sorted(p.parent for p in docs_root.glob("features/*/technical-spec.md"))
    if features is not None:
        dirs = [d for d in dirs if d.name in features]
    return dirs


def _read(path: Path) -> "str | None":
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _backup_path(docs_root: Path, feature_name: str) -> Path:
    return docs_root / ".migrate-v27" / _BACKUP_DIRNAME / feature_name / "technical-spec.md.bak"


def _sidecar_path(docs_root: Path, feature_name: str) -> Path:
    return docs_root / ".migrate-v27" / _BACKUP_DIRNAME / feature_name / "unverified-count.json"


def _breakdown_sidecar_path(docs_root: Path, feature_name: str) -> Path:
    """The pending-breakdown sidecar (phase 07) -- next to, never merged into,
    `_sidecar_path`'s `unverified-count.json` (see module docstring)."""
    return docs_root / ".migrate-v27" / _BACKUP_DIRNAME / feature_name / "pending-breakdown.json"


def _staging_dir(docs_root: Path, feature_name: str) -> Path:
    return docs_root / ".migrate-v27" / _BACKUP_DIRNAME / feature_name


def _unverified_count(text: str) -> int:
    return text.count(_UNVERIFIED_MARKER)


def _needs_regate(feature_dir: Path, docs_root: Path) -> bool:
    """[F2, stronger resumability] True when this feature's content shows nothing
    pending via every OTHER signal, YET the crash-window gap (module docstring)
    may still apply: `run()` has written to this feature dir before (a staging
    dir exists) and the pending-breakdown sidecar's `gated` field is not `True`.
    A feature `run()` has never touched (no staging dir -- nothing was ever
    dispatched for a gate to have missed) is exempt, matching the regression
    guard `test_over_broad_reopen_regression_guard_skips_a_file_with_nothing_
    firing` already pins for a hand-authored, never-run() fixture."""
    if not _staging_dir(docs_root, feature_dir.name).is_dir():
        return False
    data = _read_sidecar_json(_breakdown_sidecar_path(docs_root, feature_dir.name))
    return not bool(data.get("gated", False))


def _write_breakdown_sidecar(
    docs_root: Path, project_root: Path, feature_dir: Path, *, reset_gated: bool,
) -> "tuple[dict | None, str | None]":
    """Write/refresh `pending-breakdown.json` for `feature_dir`: fresh counts +
    the D13 dispatched-action-id set, ALWAYS computed from the artifact on disk
    right now (never cached across calls). `gated` is preserved from whatever is
    already recorded UNLESS `reset_gated` -- a real compose/reopen write always
    needs a fresh gate cycle (`reset_gated=True`); a call that wrote nothing this
    invocation preserves whatever the orchestrator already recorded
    (`reset_gated=False`), so this module NEVER sets `gated` True itself -- only
    the orchestrator does, after a wave gate actually passes.

    Returns `(breakdown, None)` on success -- the caller folds `breakdown` into
    the `[HANDOFF]` summary without recomputing it -- or `(None, error)` on
    failure, the same contract `_write_reshape` uses, folded into the same
    `failures` list by the caller."""
    path = _breakdown_sidecar_path(docs_root, feature_dir.name)
    existing = _read_sidecar_json(path)
    gated = False if reset_gated else bool(existing.get("gated", False))
    breakdown = build_breakdown(feature_dir, project_root)
    data = {
        "unverified_tag_count": breakdown["unverified_tag_count"],
        "rule_id_counts": breakdown["rule_id_counts"],
        "dispatched_action_ids": sorted(dispatched_action_ids(feature_dir, project_root)),
        "gated": gated,
    }
    try:
        assert_under(path, docs_root)
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(path, json.dumps(data) + "\n")
    except (OSError, ValueError) as exc:
        return None, f"{feature_dir}: pending-breakdown sidecar write failed ({exc})"
    return breakdown, None


def _is_pending(feature_dir: Path, root: Path) -> bool:
    """[AD-1] shape_pending + fill_pending + C1's reopen check + F2's regate check
    -- Path-based, not text-based (F1): the reopen half needs the whole feature
    dir (the validator reads the functional-spec.md twin too), so this reads
    `technical-spec.md` itself rather than taking pre-read text, keeping every
    caller on ONE shape. Pure read: never writes. `_needs_regate` (F2, module
    docstring) DOES read the pending-breakdown sidecar -- still never the `.bak`
    itself, and never a write."""
    text = _read(feature_dir / "technical-spec.md")
    if text is None:
        return False
    if _TECH_PRE_THREAD_SENTINEL in text:
        return True
    if _unverified_count(text) > 0:
        return True
    # C1: a file with zero [UNVERIFIED] markers and the new shape is NOT
    # automatically done -- a registered detector (`state_rung_missing`) may still
    # be firing on it, and that gap has no other counted signal.
    if needs_reopen(feature_dir, root):
        return True
    # F2: every other signal says done -- but a fill unit's write may be sitting
    # in the crash window between landing and its (never-ran) wave gate. docs_root
    # is feature_dir's own grandparent (`<docs_root>/features/<name>`), derived
    # rather than threaded through, since every caller of `_is_pending` already
    # has `docs_root` in scope one frame up but this function's signature is
    # shared with `needs_reopen`'s `(feature_dir, root)` shape.
    docs_root = feature_dir.parent.parent
    return _needs_regate(feature_dir, docs_root)


def count_pending(docs_root: Path, project_root: Path, features: "FeatureFilter") -> int:
    pending = 0
    for feature_dir in _iter_feature_dirs(docs_root, features):
        if _is_pending(feature_dir, project_root):
            pending += 1
    return pending


def _read_sidecar_json(path: Path) -> dict:
    """`{}` on anything not cleanly a JSON object -- missing, unreadable, or
    malformed -- so callers treat an unreadable sidecar as "nothing recorded"
    (never refuse/reopen on corrupt sidecar data; never crash)."""
    text = _read(path)
    if text is None:
        return {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _read_sidecar_count(path: Path) -> "int | None":
    count = _read_sidecar_json(path).get("unverified_count")
    return count if isinstance(count, int) else None


def _read_sidecar_reopened_ids(path: Path) -> "frozenset[str]":
    """The rule_ids a PRIOR `run()` invocation already recorded as having reopened
    this feature dir for -- see the module docstring's "reopen bookkeeping" note.
    Empty (never a crash) on anything not cleanly a list of strings."""
    ids = _read_sidecar_json(path).get("reopened_rule_ids")
    if not isinstance(ids, list):
        return frozenset()
    return frozenset(i for i in ids if isinstance(i, str))


def _write_reshape(
    docs_root: Path, feature_dir: Path, tech_path: Path, original_text: str,
    new_text: str, *, reopened_rule_ids: "frozenset[str] | None" = None,
) -> "str | None":
    """Write-before-destroy (FM-3), shared by the legacy pre-thread compose and the
    C1 reopen path: back up `original_text` FIRST, record the post-write
    `[UNVERIFIED]` count in the sidecar, THEN write `new_text`. A reopened write
    with no `.bak` would be unrollbackable data loss on a user corpus, so the
    reopen path reuses this exact sequence rather than a second one.

    `reopened_rule_ids`, only given by the reopen path, is ALSO recorded in the
    sidecar so a future `run()` can tell "already surfaced this exact finding set"
    apart from "newly firing" (see module docstring). `None` (the legacy path's
    default) keeps the sidecar's original two-key shape unchanged.

    Returns an error string on failure, `None` on success."""
    bak = _backup_path(docs_root, feature_dir.name)
    sidecar = _sidecar_path(docs_root, feature_dir.name)
    try:
        assert_under(bak, docs_root)
        assert_under(sidecar, docs_root)
        assert_under(tech_path, docs_root)
        bak.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(bak, original_text)  # write-before-destroy (FM-3)
    except (OSError, ValueError) as exc:
        return f"{feature_dir}: backup failed ({exc})"
    sidecar_data: dict = {"unverified_count": _unverified_count(new_text)}
    if reopened_rule_ids is not None:
        sidecar_data["reopened_rule_ids"] = sorted(reopened_rule_ids)
    try:
        atomic_write(sidecar, json.dumps(sidecar_data) + "\n")
    except OSError as exc:
        return f"{feature_dir}: sidecar write failed ({exc})"
    try:
        atomic_write(tech_path, new_text)
    except OSError as exc:
        return f"{feature_dir}: write failed ({exc})"
    return None


def run(docs_root: Path, project_root: Path, features: "FeatureFilter") -> StepResult:
    """Registry `run`: reshape each pending `technical-spec.md` via
    `compose_action_thread`, reading the sibling `functional-spec.md` as the twin.
    Per-feature-dir isolation: one bad pair does not abort the rest; `run()` never
    raises (`execute()` has no try/except of its own, and a raised exception would
    replace the documented exit codes {0,1,2,4} with a traceback).

    C1: a file already in the new shape is no longer assumed done just because it
    carries zero `[UNVERIFIED]` markers -- `needs_reopen`/`firing_reopen_rule_ids`
    (D7/F1) may still find a registered detector firing on it. Reopening recomposes
    it in place via the SAME `compose_action_thread` call the legacy path uses
    (verified idempotent on its own output), then persists the identical
    write-before-destroy backup/sidecar/write sequence -- see `_write_reshape`."""
    changed = 0
    fill_pending_remaining = 0
    failures: list[str] = []
    # phase 07: `(feature_name, breakdown)` for every feature dir this run leaves
    # pending, in iteration order -- folded into the `[HANDOFF]` line's summary
    # (`summarize_breakdowns`) below. Never populated for a feature that ends this
    # run with nothing pending (its breakdown would be all zeros anyway).
    pending_breakdowns: list[tuple[str, dict]] = []
    # Phase 05 (defect 3 sweep, plans/260825-1010-...): `compose_action_thread`
    # already COUNTS actions capability-bucketing couldn't trace to the twin's §
    # 2 table (`ThreadComposeResult.unbound_action_count`, phase 03) -- landed
    # but never SURFACED anywhere an operator could see it, which made the
    # "count it, don't tag it" decision only half-built (a count nobody reads is
    # not a signal). Summed across every feature dir freshly composed THIS run
    # only -- a feature this run leaves untouched (already action-thread-shaped,
    # not reopened) was not recomposed, so it contributes nothing here, same as
    # `changed`/`fill_pending_remaining` already only count fresh work.
    unbound_action_total = 0

    def _refresh_breakdown(feature_dir: Path, *, reset_gated: bool) -> None:
        breakdown, error = _write_breakdown_sidecar(
            docs_root, project_root, feature_dir, reset_gated=reset_gated,
        )
        if error:
            failures.append(error)
            return
        pending_breakdowns.append((feature_dir.name, breakdown))

    for feature_dir in _iter_feature_dirs(docs_root, features):
        tech_path = feature_dir / "technical-spec.md"
        text = _read(tech_path)
        if text is None:
            failures.append(f"{tech_path}: read failed")
            continue

        if _TECH_PRE_THREAD_SENTINEL not in text:
            marker_pending = _unverified_count(text) > 0
            # [C1] Already Action-Index-shaped -- ask the generalized predicate
            # (never a second, re-implemented one -- D7/F1) whether any REGISTERED
            # detector fires on this feature dir, regardless of marker_pending:
            # phase 08's `retired_section_present` needs this even when
            # marker_pending is true (see below), so it is computed unconditionally
            # rather than only in the zero-markers branch the pre-phase-08 code used.
            firing = firing_reopen_rule_ids(feature_dir, project_root)
            retired_firing = bool(firing & _MECHANICAL_REOPEN_RULE_IDS)
            sidecar = _sidecar_path(docs_root, feature_dir.name)
            already_surfaced = firing <= _read_sidecar_reopened_ids(sidecar)
            # A write is warranted when there is a NEW finding to act on AND
            # (a) it is mechanically strippable (retired_firing -- runs regardless
            # of marker_pending, see the comment below), OR (b) marker_pending is
            # false and something in REOPEN_RULE_IDS fires (the original C1 path).
            should_write = not already_surfaced and (
                retired_firing or (not marker_pending and bool(firing))
            )

            if should_write:
                func_path = feature_dir / "functional-spec.md"
                func_text = _read(func_path)
                if func_text is None:
                    failures.append(
                        f"{feature_dir}: functional-spec.md read failed -- action-thread "
                        "needs the twin"
                    )
                    continue
                result = compose_action_thread(text, func_text)
                unbound_action_total += result.unbound_action_count
                error = _write_reshape(
                    docs_root, feature_dir, tech_path, text, result.text,
                    reopened_rule_ids=firing,
                )
                if error:
                    failures.append(error)
                    continue
                changed += 1
                # A detector fired; only a researcher fill pass (or, for
                # retired_firing, nothing further at all beyond this mechanical
                # strip) resolves the rest -- `result.needs_llm_fill` alone (the
                # `[UNVERIFIED]`-marker signal) would miss this family of gap
                # entirely.
                fill_pending_remaining += 1
                _refresh_breakdown(feature_dir, reset_gated=True)
                continue

            if marker_pending or firing:
                # Either the pre-existing [UNVERIFIED] marker path (BR/DEC rule
                # ownership, unaffected by C1) -- reason enough for a researcher
                # fill pass to revisit this feature dir on its own, so there is
                # nothing NEW to reopen for on this run -- OR a registered
                # detector already surfaced this exact finding set on a prior run
                # (reopening again would rewrite identical bytes every invocation
                # forever). Phase 08 note: `retired_firing and already_surfaced`
                # (the strip already ran) also lands here when marker_pending is
                # still true -- correctly `already`, not a fresh write, mirroring
                # `test_third_run_reports_already_and_stays_byte_identical`.
                fill_pending_remaining += 1
                _refresh_breakdown(feature_dir, reset_gated=False)
                continue

            # [F2] Every signal is silent -- but this may be the crash window
            # itself: a fill unit's write landed and looks fully resolved, yet the
            # wave gate that was supposed to check it never got the chance to run.
            # Stay pending until the orchestrator records a passed gate (module
            # docstring) rather than let an ungated write vanish as "done" with
            # nobody having checked it.
            if _needs_regate(feature_dir, docs_root):
                fill_pending_remaining += 1
                _refresh_breakdown(feature_dir, reset_gated=False)
            continue  # regression guard: nothing firing -- stays untouched

        func_path = feature_dir / "functional-spec.md"
        func_text = _read(func_path)
        if func_text is None:
            failures.append(
                f"{feature_dir}: functional-spec.md read failed -- action-thread needs "
                "the twin"
            )
            continue
        result = compose_action_thread(text, func_text)
        unbound_action_total += result.unbound_action_count
        error = _write_reshape(docs_root, feature_dir, tech_path, text, result.text)
        if error:
            failures.append(error)
            continue
        changed += 1
        if result.needs_llm_fill:
            fill_pending_remaining += 1
            _refresh_breakdown(feature_dir, reset_gated=True)

    if failures:
        return StepResult(
            category=FAILED,
            message=f"{len(failures)} feature dir(s) failed ({changed} composed before "
                     f"the failure(s)): {'; '.join(failures)} -- fix the error(s) then "
                     f"re-run `{_FILL_COMMAND}`",
        )
    summary = summarize_breakdowns(pending_breakdowns)
    # Phase 05: the count is a visibility signal, not a marker -- it never gates
    # `needs_llm_fill` and never becomes an `[UNVERIFIED]`-style tag (deliberately
    # -- see the accumulator comment above). It only ever appends to a message a
    # human/orchestrator already reads.
    unbound_suffix = (
        f" -- {unbound_action_total} action(s) landed in the fallback capability "
        "bucket this run (uncertain bucketing, not missing content)"
        if unbound_action_total > 0 else ""
    )
    if changed > 0:
        if fill_pending_remaining > 0:
            message = (
                f"composed {changed} feature dir(s) to the action-thread shape -- "
                f"researcher fill pass still required for {fill_pending_remaining} "
                f"feature dir(s) with unresolved rule ownership -- {summary}"
                f"{unbound_suffix}"
            )
        else:
            message = f"composed {changed} feature dir(s) to the action-thread shape{unbound_suffix}"
        return StepResult(category=PROGRESS, message=message,
                           needs_llm_fill=fill_pending_remaining > 0)
    if fill_pending_remaining > 0:
        return StepResult(
            category=ALREADY,
            message=f"all in-scope technical-spec.md already action-thread-shaped; "
                     f"{fill_pending_remaining} still carry unresolved rule ownership -- "
                     f"researcher fill pass still required -- {summary}",
            needs_llm_fill=True,
        )
    return StepResult(
        category=ALREADY,
        message="all in-scope technical-spec.md already carry the action-thread shape "
                 "with every rule bound to an action",
    )


def rollback(docs_root: Path, project_root: Path, features: "FeatureFilter") -> StepResult:
    """[FM-3] Restore `.bak`; refuse (print + skip, never destroy) any feature whose
    LIVE unresolved-marker count has dropped below the sidecar's recorded value -- see
    module docstring for why this, and not `cap-map`'s "refuse if filled" stance, is
    the correct predicate here. A count that stayed the same or rose is safe: nothing
    has been resolved since migrate ran. Never raises (`--rollback` dispatch has no
    try/except of its own, matching `run()`'s contract).

    `project_root` is accepted (not discarded, per C1/F1's registry-signature
    consequence -- `RollbackFn` is the same `Callable[[Path, Path, FeatureFilter]]`
    shape as `run`/`count_pending`) but genuinely unused here: rollback restores
    from the `.bak`/sidecar tree alone and never consults `needs_reopen`."""
    restored = 0
    refused = 0
    failures: list[str] = []
    for feature_dir in _iter_feature_dirs(docs_root, features):
        bak = _backup_path(docs_root, feature_dir.name)
        if bak.is_symlink():
            failures.append(f"{bak}: refusing a symlinked backup")
            continue
        if not bak.is_file():
            continue  # nothing staged for this feature -- nothing to roll back
        tech_path = feature_dir / "technical-spec.md"
        live_text = _read(tech_path)
        if live_text is None:
            failures.append(f"{tech_path}: read failed")
            continue
        sidecar = _sidecar_path(docs_root, feature_dir.name)
        recorded = _read_sidecar_count(sidecar)
        current = _unverified_count(live_text)
        if recorded is not None and current < recorded:
            print(
                f"[REFUSED] action-thread rollback: {feature_dir.name} unverified "
                f"count dropped {recorded} -> {current} -- a researcher has resolved "
                "rule ownership by hand since migrate ran; restoring the pre-migration "
                "file would destroy that work. Reverse through the customer's own VCS "
                "instead.",
                file=sys.stderr,
            )
            refused += 1
            continue
        backup_text = _read(bak)
        if backup_text is None:
            failures.append(f"{bak}: read failed")
            continue
        try:
            assert_under(tech_path, docs_root)
            atomic_write(tech_path, backup_text)
            bak.unlink()
        except (OSError, ValueError) as exc:
            failures.append(f"{feature_dir.name}: rollback write failed ({exc})")
            continue
        try:
            if sidecar.is_file():
                sidecar.unlink()
        except OSError:
            pass  # sidecar cleanup is best-effort -- a stray sidecar file is inert
        restored += 1

    if failures:
        return StepResult(
            category=FAILED,
            message=f"{len(failures)} feature dir(s) failed to roll back ({restored} "
                     f"restored, {refused} refused before the failure(s)): "
                     f"{'; '.join(failures)} -- re-run `run_doc_migrations.py "
                     f"--docs-root <docs> --rollback action-thread`",
        )
    if refused:
        return StepResult(
            category=FAILED,
            message=f"{refused} feature dir(s) refused (unresolved-rule count dropped "
                     f"since migrate ran; restored the other {restored}) -- reverse "
                     "those through the customer's own VCS instead",
        )
    if restored == 0:
        return StepResult(category=ALREADY,
                           message="no action-thread .bak backups found to restore")
    return StepResult(category=PROGRESS, message=f"restored {restored} feature dir(s) from .bak")
