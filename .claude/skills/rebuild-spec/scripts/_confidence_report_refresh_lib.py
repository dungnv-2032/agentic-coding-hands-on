#!/usr/bin/env python3
"""_confidence_report_refresh_lib.py -- the A1 confidence-report companion refresh,
invoked as a POST-STEP after any `--migrate` step that can write
`features/*/technical-spec.md` (`run_doc_migrations.py::_TECH_SPEC_STEPS` --
`audience-split`, `feature-sot`, `action-thread` today; originally written
(phase-04, plans/260818-0758-rebuild-spec-post-migration-completion) against
`audience-split`/`a3-b4`, the latter retired in phase-09,
plans/260824-1846-rebuild-spec-action-self-sufficiency-v27-8).

Every `technical-spec.md` a migration step rewrites owes a fresh
`confidence-report_technical-spec.md` beside it -- the 66-feature scratch corpus
measured in phase-00 CORRECTION 1 carries 66/66 companions dated 07-07 next to
artifacts the v27 migration rewrote on 08-17. The sidecar contract's own word is
"always-regenerate" (`references/confidence-report-contract.md`), so this module
builds NO staleness detector: it regenerates unconditionally, every time it runs.

NOT a `STEP_ORDER` member -- phase-00 CORRECTION 1 settles A1 as an always-regenerate,
never-gated, never-detected sidecar, so it does not belong in
`_doc_migration_registry_lib.STEP_ORDER` or need its own prerequisite chain. That
tuple's exact length is owned and stated once by `_doc_migration_registry_lib.
STEP_ORDER` itself -- never duplicated here as a literal count, so an edit that grows
or shrinks the chain (phase-07 grew it from 6 to 7 by inserting `cap-map`) cannot
leave this docstring stale again. `run_doc_migrations.py` calls this module directly,
in-process, right after `execute()`/`preview()` runs -- the same in-process-import
convention `_doc_migration_audience_split_step_lib.py` already established over a
subprocess call.

Scope is exactly `features/*/technical-spec.md` -- NEVER `functional-spec.md`
(phase-00 CORRECTION 1; `references/confidence-report-contract.md` § "v27.0.0 -- A1
scope"). This is enforced structurally by the glob naming `technical-spec.md`
literally, not by a denylist checked at runtime; the widened guard in
`scripts/tests/test_confidence_report_functional_spec_exclusion.py` additionally
proves it by parsing this module's own docstring-adjacent call site in
`references/pipeline-migrate.md`.

Re-runnable, not run-once-in-order (see phase-04.md "Ordering context", written
against the now-retired `a3-b4` step, and the "action-thread" step's own runbook
section in `references/pipeline-migrate.md` for the live example): a
technical-spec-writing step's own FILL half (real content an LLM researcher writes)
happens across separate LLM-researcher dispatches documented in
`references/pipeline-migrate.md`'s wave fan-out -- outside this Python process, and
typically AFTER this module's own in-process call (fired right after that step's
Python-driven deterministic half returns). So a single in-process call here cannot
see the eventual filled content by construction; the fix is not tighter ordering, it
is exactly what the sidecar contract already prescribes -- always-regenerate, cheaply
and idempotently, as many times as anything touches `technical-spec.md`.
`references/pipeline-migrate.md`'s wave-gate loop calls `derive_confidence_report.py`
again per feature immediately after that feature's fill completes, closing the gap
this module's own single call cannot close alone.

Derivation itself is `derive_confidence_report.derive()`, imported -- never
reimplemented (phase-04.md "Do NOT edit": scripts/derive_confidence_report.py).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from derive_confidence_report import derive  # noqa: E402

FeatureFilter = "frozenset[str] | None"

_TARGET_NAME = "technical-spec.md"


def discover_technical_specs(docs_root: Path, features: "FeatureFilter" = None) -> list[Path]:
    """Every `features/<F>/technical-spec.md` that currently EXISTS under `docs_root`,
    optionally scoped to `features` (a set of feature-dir names, e.g. `F001_Auth`).
    Only existing files are returned -- `derive()` is never invoked for a feature dir
    that has no technical-spec.md yet (a profile-conditional pass may never have
    produced one), matching `derive_confidence_report.py --artifact`'s own
    best-effort "artifact not found, skipping" behavior.
    """
    features_root = docs_root / "features"
    if not features_root.is_dir():
        return []
    paths: list[Path] = []
    for feature_dir in sorted(features_root.iterdir()):
        if not feature_dir.is_dir():
            continue
        if features is not None and feature_dir.name not in features:
            continue
        candidate = feature_dir / _TARGET_NAME
        if candidate.is_file():
            paths.append(candidate)
    return paths


def count_pending(docs_root: Path, project_root: Path, features: "FeatureFilter" = None) -> int:
    """`--dry-run` count -- how many companions WOULD be (re)written this invocation.
    Pure read, writes nothing; `project_root` is accepted (unused) only to mirror
    `_doc_migration_registry_lib.CountPendingFn`'s shape, even though this module is
    not a registered `STEP_ORDER` step."""
    del project_root  # unused: derivation only needs project_root to relativize paths
    return len(discover_technical_specs(docs_root, features))


@dataclass(frozen=True)
class RefreshResult:
    """One refresh invocation's outcome. `paths` are the technical-spec.md files a
    companion was (re)written for -- always the full in-scope set on success, since
    regeneration is unconditional (phase-00 CORRECTION 1: no staleness check gates
    this). A per-artifact failure is swallowed (see `refresh()`) and simply omitted
    from `paths`, never raised -- this sidecar must never fail the pass it rides on."""

    count: int
    paths: "tuple[Path, ...]" = field(default_factory=tuple)


def refresh(docs_root: Path, project_root: Path, features: "FeatureFilter" = None) -> RefreshResult:
    """Regenerate `confidence-report_technical-spec.md` for every in-scope feature,
    unconditionally. Best-effort per artifact: `derive_confidence_report.py`'s own
    `main()` swallows I/O/parse errors when invoked as a subprocess, but calling
    `derive()` directly here bypasses that wrapper, so the same swallow-and-warn
    behavior is reproduced at this call site -- one bad artifact must never abort the
    rest of the batch."""
    targets = discover_technical_specs(docs_root, features)
    written: list[Path] = []
    for artifact in targets:
        try:
            derive(artifact.resolve(), project_root)
            written.append(artifact)
        except Exception as exc:  # noqa: BLE001 -- best-effort sidecar, see module docstring
            print(
                f"[WARN] confidence-report refresh: skipping {artifact} ({exc})",
                file=sys.stderr,
            )
    return RefreshResult(count=len(written), paths=tuple(written))
