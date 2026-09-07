#!/usr/bin/env python3
"""_doc_migration_registry_lib.py -- the `--migrate` step registry + driver core.

Phase 01 of plans/260818-0758-rebuild-spec-post-migration-completion. `--migrate` is
ONE ordered registry of version-upgrade backfill steps, not several flags (plan.md
Decision 1). STEP_ORDER fixes the chain: audience-split -> a3-screens ->
screen-sot -> feature-sot -> cap-map -> action-thread -> mirror-skew (`screen-sot`/
`feature-sot` inserted by phase-06/phase-10 of
plans/260818-1332-rebuild-spec-human-readable-sot; `cap-map` inserted by phase-07 of
plans/260819-1016-rebuild-spec-capability-map; `action-thread` inserted by phase-06 of
plans/260824-1128-rebuild-spec-action-thread-v27-7 -- mirror-skew now depends on
`action-thread`, not `cap-map` or `feature-sot` directly, and stays last). `a3-b4`
(the step that used to sit between `audience-split` and `a3-screens`) RETIRED in
phase-09 of plans/260824-1846-rebuild-spec-action-self-sufficiency-v27-8: A3/B4 left
`technical-spec.md`'s target shape in phase 08, leaving `a3-b4` nothing left to
scaffold, and `a3-screens`'s own prerequisite repointed straight to
`audience-split`. This module is the registry/driver mechanics only --
`run_doc_migrations.py::_build_registry()` wires the real `count_pending`/`run`
bodies.

Idempotency is ARTIFACT-derived (phase-00 CORRECTION 2): `count_pending` must read the
OUTPUT a step produces, never a marker file the driver writes itself -- this module
persists no state of its own; `count_pending` doubles as the "already done?" predicate.

Outcome bookkeeping reuses `_audience_split_tally_lib.Tally` BY IMPORT -- PROGRESS/
ALREADY/INERT/FAILED and `Tally.exit_code()` are that module's contract, not a second
copy -- a second copy is how the category-drift bug shipped last time.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from _audience_split_tally_lib import FAILED, INERT, Tally  # noqa: F401

# Fixed dependency chain (plan.md table): each step's prerequisite is the one before it.
# phase-07 (plans/260819-1016-rebuild-spec-capability-map) inserted "cap-map" between
# "feature-sot" and "mirror-skew" -- see _doc_migration_cap_map_step_lib.py. phase-06
# (plans/260824-1128-rebuild-spec-action-thread-v27-7) inserted "action-thread" between
# "cap-map" and "mirror-skew" -- see _doc_migration_action_thread_step_lib.py. phase-09
# (plans/260824-1846-rebuild-spec-action-self-sufficiency-v27-8) RETIRED "a3-b4" --
# it used to sit here, between "audience-split" and "a3-screens" -- and repointed
# "a3-screens"'s own prerequisite straight to "audience-split".
STEP_ORDER: tuple[str, ...] = (
    "audience-split", "a3-screens", "screen-sot", "feature-sot", "cap-map",
    "action-thread", "mirror-skew",
)

FeatureFilter = "frozenset[str] | None"
CountPendingFn = Callable[[Path, Path, "FeatureFilter"], int]
RunFn = Callable[[Path, Path, "FeatureFilter"], "StepResult"]


@dataclass(frozen=True)
class StepResult:
    """One step's outcome for THIS invocation. `category` MUST be one of
    `_audience_split_tally_lib`'s PROGRESS/ALREADY/INERT/FAILED -- `execute()` folds it
    into the run's `Tally`, subject to the two fail-closed overrides below.

    `needs_llm_fill`: the deterministic part ran (e.g. a `{...}` scaffold was written)
    but real content still needs an LLM researcher pass (`handoff_line()`).
    `not_implemented`: this step's real body isn't registered yet (`not_implemented_
    line()`). Either flag forces the effective category to INERT (unless already
    FAILED) -- `--migrate` can never exit 0 while work is incomplete."""
    category: str
    message: str
    needs_llm_fill: bool = False
    not_implemented: bool = False


@dataclass(frozen=True)
class StepSpec:
    """One registry entry. `prerequisite` names another registered step (or None for
    the chain's first); `count_pending`/`run` are pure functions of (docs_root,
    project_root, features). `count_pending` NEVER writes; `run` is never called under
    `--dry-run`."""
    name: str
    prerequisite: str | None
    count_pending: CountPendingFn
    run: RunFn


class UnknownStepError(ValueError):
    """Raised for a `--only` value naming no registered step -- bad-invocation (exit 2),
    distinct from a registered-but-not-yet-implemented stub step."""


class StepRegistry:
    """Ordered collection of `StepSpec`s, keyed by name. Registration order must
    satisfy STEP_ORDER -- prerequisites must already be registered."""

    def __init__(self) -> None:
        self._specs: dict[str, StepSpec] = {}

    def register(self, spec: StepSpec) -> None:
        if spec.name not in STEP_ORDER:
            raise ValueError(f"{spec.name!r} is not one of the fixed STEP_ORDER names {STEP_ORDER}")
        if spec.prerequisite is not None and spec.prerequisite not in self._specs:
            raise ValueError(
                f"step {spec.name!r} declares prerequisite {spec.prerequisite!r}, which "
                f"is not registered yet -- register steps in STEP_ORDER order"
            )
        self._specs[spec.name] = spec

    def get(self, name: str) -> StepSpec:
        try:
            return self._specs[name]
        except KeyError:
            raise UnknownStepError(
                f"unknown migration step {name!r} -- valid steps: {', '.join(STEP_ORDER)}"
            ) from None

    def names(self) -> tuple[str, ...]:
        """Registered names in canonical STEP_ORDER (not insertion order)."""
        return tuple(n for n in STEP_ORDER if n in self._specs)


def handoff_line(step_name: str, detail: str) -> str:
    """The one `[HANDOFF]` format every step needing an LLM fill pass MUST print --
    later phases import this rather than hand-rolling the tag, one shape to grep for."""
    return f"[HANDOFF] step={step_name} needs_llm_fill=true -- {detail}"


def not_implemented_line(step_name: str, detail: str) -> str:
    """Tag for a registered-but-stub step -- distinct from `[HANDOFF]`: no real body
    registered yet at all, vs. a real pass that ran and awaits an LLM to finish it."""
    return f"[NOT-IMPLEMENTED] step={step_name} -- {detail}"


def make_stub_step(name: str, prerequisite: str | None, owner_phase: str) -> StepSpec:
    """A real, working registration for a step whose body a LATER phase owns -- safe to
    call, never raises. `count_pending` reports a nonzero sentinel (1, count unknown) so
    preview and prerequisite gating fail closed, never a false 0."""

    def _count_pending(_docs_root: Path, _project_root: Path, _features: "FeatureFilter") -> int:
        return 1

    def _run(_docs_root: Path, _project_root: Path, _features: "FeatureFilter") -> StepResult:
        return StepResult(
            category=INERT,
            message=f"owner={owner_phase}; no real work done this run -- registry seam only",
            not_implemented=True,
        )

    return StepSpec(name=name, prerequisite=prerequisite, count_pending=_count_pending, run=_run)


def prerequisite_pending(registry: StepRegistry, step: StepSpec, docs_root: Path,
                          project_root: Path, features: "FeatureFilter") -> int:
    """0 if *step* has no prerequisite, or its prerequisite has nothing pending. A
    fresh read every time (never cached), so a step just finished this run is seen."""
    if step.prerequisite is None:
        return 0
    return registry.get(step.prerequisite).count_pending(docs_root, project_root, features)


def preview(registry: StepRegistry, step_names: tuple[str, ...], docs_root: Path,
            project_root: Path, features: "FeatureFilter") -> list[str]:
    """`--dry-run`: read-only per-step pending counts. Never calls `run()` -- pure
    reads only, so this writes NOTHING (no lock, no staging, no marker)."""
    lines: list[str] = []
    for name in step_names:
        step = registry.get(name)
        pending = step.count_pending(docs_root, project_root, features)
        blocked = prerequisite_pending(registry, step, docs_root, project_root, features)
        status = "blocked" if blocked > 0 else "ready"
        lines.append(
            f"[DRY-RUN] step={name} pending={pending} "
            f"prerequisite={step.prerequisite or 'none'} status={status}"
        )
    return lines


def _effective_category(result: StepResult) -> str:
    """Fail-closed override: a step that still needs an LLM fill, or has no real body
    registered yet, can never read as complete -- see `StepResult`'s docstring."""
    if result.category == FAILED:
        return FAILED
    if result.needs_llm_fill or result.not_implemented:
        return INERT
    return result.category


def execute(registry: StepRegistry, step_names: tuple[str, ...], docs_root: Path,
            project_root: Path, features: "FeatureFilter",
            ran: "set[str] | None" = None) -> "tuple[int, Tally]":
    """Real run: dependency order, prerequisite refusal, `Tally` bookkeeping. Reuses
    `Tally.exit_code()` verbatim -- never reimplemented. `ran` (phase-06 ADDENDUM,
    optional, backward compatible): if given a `set`, every step name whose `run()`
    was ACTUALLY invoked is added -- never a refused one -- so a caller can tell
    "requested" from "actually ran" (`run_doc_migrations.py`'s A1 refresh needs it)."""
    tally = Tally()
    for name in step_names:
        step = registry.get(name)
        blocked = prerequisite_pending(registry, step, docs_root, project_root, features)
        if blocked > 0:
            print(
                f"[REFUSED] step={name} prerequisite={step.prerequisite} pending={blocked} "
                f"-- run --only {step.prerequisite} first (or a full --migrate)",
                file=sys.stderr,
            )
            tally.record(INERT, action=f"refused-prereq-pending:{name}")
            continue
        if ran is not None:
            ran.add(name)
        result = step.run(docs_root, project_root, features)
        category = _effective_category(result)
        if result.not_implemented:
            print(not_implemented_line(name, result.message))
        elif result.needs_llm_fill:
            print(handoff_line(name, result.message))
        else:
            print(f"[INFO] step={name} category={category} -- {result.message}")
        tally.record(category, action=f"step:{name}")
    return tally.exit_code(), tally
