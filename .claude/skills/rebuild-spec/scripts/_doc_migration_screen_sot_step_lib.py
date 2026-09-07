#!/usr/bin/env python3
"""_doc_migration_screen_sot_step_lib.py -- the `screen-sot` `--migrate` registry step
(phase-06, plans/260818-1332-rebuild-spec-human-readable-sot).

THIN DRIVER over `_screen_sot_compose_lib.compose_screen_sot` (P05) -- the sole
authority on the SOT target section order. This module owns no reshaping logic of its
own; it only discovers screen specs, calls the composer, and writes the result back
atomically. Two generations reach the composer through this one step: G1 (v26) chains
Mode C (the `audience-split` step) -> G2, `a3-screens` scaffolds A3 onto that G2 text,
THEN this step composes G2 -> G3; a G2 corpus that is already-v27 (Mode-C-reordered)
enters directly here once `a3-screens` is satisfied. Both paths call the SAME
`compose_screen_sot`, so they cannot drift (phase-05's Key Insight, restated in
phase-06.md).

`count_pending` is artifact-derived (never a marker file, per the registry's own
module docstring): a `spec.md` is pending when it lacks `"## 2. Screen Layout"` --
the literal heading `compose_screen_sot` writes via `_screen_sot_compose_lib.
SOT_BA_ORDER` / `_screen_sot_appendix_lib.assemble_document` (`parts.append(name +
"\\n\\n" + ...)` for each name in `ba_order`). That exact string is absent from BOTH
G1 (v26, carries the unnumbered `## Screen Layout` H2) and G2 (Mode-C output -- no
`## Screen Layout` H2 at all; Layout Sketch/Regions live as bare H3s under `## Purpose`
and the dev-appendix preamble) -- the SOT numbering is new in this phase's output, so
its presence is a safe, single, universal pending predicate for both input shapes.

`screen-sot` is screen-spec-only (`docs/screens/*/spec.md`) -- it MUST NOT be added to
`run_doc_migrations.py`'s `_writes_technical_spec`/A1-refresh set. No A1
confidence-report loop fires for this step (`references/pipeline-migrate.md` states
this for `a3-screens`; the same reasoning applies verbatim -- the composer never
touches `features/*/technical-spec.md`).

Unlike `_a3_screens_step_lib.scaffold_file` (which SKIPS an unreadable spec, returning
`False`, and never fails the step for it), this step reports FAILED for any per-file
read or write error, with the offending path named in the message -- phase-06.md's
Requirements are explicit: "FAILED on any unreadable/unwritable spec, with the path in
the message." A failure on one screen never aborts the batch: every other in-scope
screen is still composed and written before the step reports FAILED overall
(Requirements: "Per-screen failure is isolated: one bad spec does not abort the other
181").

Path handling stays within `docs_root` by construction: `_iter_screen_dirs` only ever
globs `docs_root.glob("screens/*/spec.md")` -- there is no user-controlled path
segment threaded into a write target, so no separate guarded-resolver call is needed
here (unlike a step that accepts an operator-supplied slug).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _atomic_write_lib import _atomic_write  # noqa: E402
from _audience_split_tally_lib import ALREADY, FAILED, PROGRESS  # noqa: E402
from _doc_migration_registry_lib import StepResult  # noqa: E402
from _screen_sot_compose_lib import compose_screen_sot  # noqa: E402

FeatureFilter = "frozenset[str] | None"

_FILL_COMMAND = "run_doc_migrations.py --migrate --only screen-sot"

# The literal heading `compose_screen_sot` emits for its 2nd BA section (see module
# docstring for the writer-side grep proof). Its absence is the pending predicate --
# never a driver-written marker file.
_SOT_PENDING_HEADING = "## 2. Screen Layout"


def _iter_screen_dirs(docs_root: Path, features: "FeatureFilter" = None) -> list[Path]:
    """Every `screens/*/spec.md` under *docs_root*. `features` is accepted for
    `CountPendingFn`/`RunFn` signature parity and ignored -- screens are keyed by
    `SCR###_Slug`, not by feature slug, matching `_a3_screens_step_lib.
    iter_screen_specs`'s own precedent."""
    del features
    return sorted(docs_root.glob("screens/*/spec.md"))


def _is_pending(text: str) -> bool:
    return _SOT_PENDING_HEADING not in text


def count_pending(docs_root: Path, project_root: Path, features: "FeatureFilter") -> int:
    """Registry `count_pending`: number of `screens/*/spec.md` not yet composed to the
    SOT shape -- pure read, never a marker file. `project_root` is unused, matching the
    sibling steps' signature parity. An unreadable file is skipped here (not counted
    either way) -- `count_pending` must never raise; `run()` is where an unreadable
    file surfaces as FAILED."""
    del project_root
    pending = 0
    for spec in _iter_screen_dirs(docs_root, features):
        try:
            text = spec.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if _is_pending(text):
            pending += 1
    return pending


def run(docs_root: Path, project_root: Path, features: "FeatureFilter") -> StepResult:
    """Registry `run`: compose every pending screen spec, write atomically. A read or
    write failure on one screen is recorded and the loop continues (isolation);
    `needs_llm_fill=True` on any real progress, which the driver's fail-closed override
    forces to INERT -- the composer scaffolds `[L]`/`{...}` content a researcher must
    still fill (`references/pipeline-migrate.md`'s screens fill pass closes the gap)."""
    del project_root
    changed = 0
    failures: list[str] = []
    for spec in _iter_screen_dirs(docs_root, features):
        try:
            text = spec.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            failures.append(f"{spec}: read failed ({exc})")
            continue
        if not _is_pending(text):
            continue
        composed = compose_screen_sot(text)
        try:
            _atomic_write(spec, composed.text)
        except OSError as exc:
            failures.append(f"{spec}: write failed ({exc})")
            continue
        changed += 1

    if failures:
        return StepResult(
            category=FAILED,
            message=f"{len(failures)} screen spec(s) failed ({changed} composed before "
                     f"the failure(s)): {'; '.join(failures)} -- fix the error(s) then "
                     f"re-run `{_FILL_COMMAND}`",
        )
    if changed == 0:
        return StepResult(
            category=ALREADY,
            message="all in-scope screens/*/spec.md already carry the SOT shape",
        )
    return StepResult(
        category=PROGRESS,
        message=f"composed {changed} screens/*/spec.md to the SOT shape -- researcher "
                 "fill pass still required for scaffolded content",
        needs_llm_fill=True,
    )
