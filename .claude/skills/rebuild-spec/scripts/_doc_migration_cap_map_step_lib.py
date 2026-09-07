#!/usr/bin/env python3
"""_doc_migration_cap_map_step_lib.py -- the `cap-map` `--migrate` registry step
(phase-07, plans/260819-1016-rebuild-spec-capability-map): `count_pending` + `run`.
`rollback` lives in the sibling `_cap_map_rollback_lib.py`; shared I/O in
`_cap_map_io_lib.py`; table analysis/widening in `_cap_map_table_widen_lib.py` --
split four ways to keep every file under the repo's 200-line guidance (the
`_mirror_skew_lib` / `_mirror_skew_detect_lib` precedent).

WHY THIS STEP EXISTS. Real v27 corpora were fully migrated under the OLDER, 5-column
`## 2. Functional Capabilities` header (`| ID | Capability | What the user can do |
Requirements | Screens |`) before `feature-sot`'s skeleton was widened to 7 columns.
`cap-map` retrofits those corpora: it widens the header + separator and appends empty
cells to every existing data row for the two new families (`User Stories`,
`Business Rules`). It writes NO new rows and assigns NO codes to a row -- partitioning
US/BR codes across CAP rows is modelling judgment a heuristic would get semantically
wrong while still passing `cap.code_unclaimed`; phase-07b does that with a human in
the loop. `cap-map` is a TABLE WIDENER, nothing more (SC-6) -- `needs_llm_fill` below
always reads True on real progress, so `--migrate` can never exit 0 on its work alone.

PLACEMENT + THE AD-1 SKEW FIX. `cap-map` sits BETWEEN `feature-sot` and `mirror-skew`
in `STEP_ORDER`; `mirror-skew`'s prerequisite is `cap-map`, not `feature-sot`, so the
vi/jp translate handoff never fires while a primary's claim cells are still unfilled
-- translating blank cells would just re-skew every mirror the moment phase-07b's fill
lands. `count_pending` is `shape_pending + fill_pending`, where `fill_pending` reuses
`_cap_table_lib.claim_state(...) != "filled"` BY IMPORT (via `_cap_map_table_widen_
lib.analyze`) -- the exact predicate `cap.claims_unfilled` uses, so the validator and
this migration step can never disagree about what "filled" means. A fully-widened-
and-filled corpus still reports ALREADY and writes nothing (byte-identity idempotency
intact); `mirror-skew` stays genuinely refused until a human has populated the cells.

ARTIFACT-DERIVED IDEMPOTENCY -- NON-NEGOTIABLE. `count_pending` reads the header shape
and claim state, never a marker file. The `.bak` this module writes before its first
per-feature write (`_cap_map_io_lib.backup_path`) is ROLLBACK STATE ONLY;
`count_pending` must never read it. Losing `docs/.migrate-v27/` once caused a re-run to
RE-FOLD content (2368 -> 2416 lines) while still reporting success
(`migration-audience-split.md:62-76`) -- a sentinel- or backup-based "already done?"
check is exactly that shipped bug's shape, and this module must not repeat it.

ATOMIC WRITE VS ROLLBACK -- TWO DIFFERENT GUARANTEES. `_cap_map_io_lib.atomic_write`'s
staged-temp-then-`os.replace` is CRASH-SAFETY: a concurrent reader never observes a
half-rewritten table. It guarantees NOTHING about recovering the pre-widen table after
the fact -- that is what the `.bak` (restored by `_cap_map_rollback_lib.rollback`) is
for. Conflating the two is why this step's first draft shipped with no rollback.

`cap-map` is deliberately absent from `run_doc_migrations.py`'s `_TECH_SPEC_STEPS` --
that set triggers the A1 confidence-report refresh for steps writing
`features/*/technical-spec.md`; `cap-map` writes ONLY `functional-spec.md` §2.

Per-feature isolation copies `_doc_migration_feature_sot_step_lib.py:144-183`
literally: one bad `functional-spec.md` out of N is recorded in `failures` and the
loop continues; `run()` never raises, because `execute()`
(`_doc_migration_registry_lib.py`) has no try/except of its own and a raised
exception would replace the documented exit codes {0,1,2,4} with a traceback.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _audience_split_tally_lib import ALREADY, FAILED, PROGRESS  # noqa: E402
from _cap_map_io_lib import (  # noqa: E402
    atomic_write, backup_path as _backup_path, iter_feature_dirs, read_text,
)
from _cap_map_table_widen_lib import analyze, widen_lines  # noqa: E402
from _doc_migration_registry_lib import StepResult  # noqa: E402
from _slug_lib import assert_under  # noqa: E402

FeatureFilter = "frozenset[str] | None"

_FILL_COMMAND = "run_doc_migrations.py --migrate --only cap-map"


def count_pending(docs_root: Path, project_root: Path, features: "FeatureFilter") -> int:
    """[AD-1] shape_pending + fill_pending -- pure read, never writes, never consults
    the `.bak` backup tree or any marker file."""
    del project_root
    pending = 0
    for feature_dir in iter_feature_dirs(docs_root, features):
        text = read_text(feature_dir / "functional-spec.md")
        if text is None:
            continue
        a = analyze(text.splitlines())
        if not a.has_section:
            continue  # no §2 at all -- feature-sot's problem, never double-counted
        if a.shape_pending or a.fill_pending:
            pending += 1
    return pending


def _widened_text(text: str) -> "str | None":
    new_lines = widen_lines(text.splitlines())
    if new_lines is None:
        return None
    return "\n".join(new_lines) + ("\n" if text.endswith("\n") else "")


def run(docs_root: Path, project_root: Path, features: "FeatureFilter") -> StepResult:
    """[FM-3 + FM-6] Widen + backup-before-write (write-before-destroy), isolating
    per-feature failures. Category/`needs_llm_fill` follow the AD-1 table: any
    widening this run -> PROGRESS+True; nothing widened but some feature still
    unfilled -> ALREADY+True; otherwise ALREADY+False."""
    del project_root
    widened = 0
    fill_pending_remaining = 0
    failures: list[str] = []
    for feature_dir in iter_feature_dirs(docs_root, features):
        func_path = feature_dir / "functional-spec.md"
        text = read_text(func_path)
        if text is None:
            failures.append(f"{func_path}: read failed")
            continue
        a = analyze(text.splitlines())
        if not a.has_section:
            continue
        if not a.shape_pending:
            if a.fill_pending:
                fill_pending_remaining += 1
            continue
        new_text = _widened_text(text)
        if new_text is None:
            continue  # §2 heading present but no header+separator pair to widen
        bak = _backup_path(docs_root, feature_dir.name)
        try:
            assert_under(bak, docs_root)
            assert_under(func_path, docs_root)
            bak.parent.mkdir(parents=True, exist_ok=True)
            atomic_write(bak, text)  # write-before-destroy (FM-3)
        except (OSError, ValueError) as exc:
            failures.append(f"{feature_dir}: backup failed ({exc})")
            continue
        try:
            atomic_write(func_path, new_text)
        except OSError as exc:
            failures.append(f"{feature_dir}: write failed ({exc})")
            continue
        widened += 1

    if failures:
        return StepResult(
            category=FAILED,
            message=f"{len(failures)} feature dir(s) failed ({widened} widened before "
                     f"the failure(s)): {'; '.join(failures)} -- fix the error(s) then "
                     f"re-run `{_FILL_COMMAND}`",
        )
    if widened > 0:
        return StepResult(
            category=PROGRESS,
            message=f"widened §2 to 7 columns (User Stories, Business Rules) in "
                     f"{widened} feature dir(s) -- researcher fill pass (phase-07b) "
                     f"still required for the claim cells",
            needs_llm_fill=True,
        )
    if fill_pending_remaining > 0:
        return StepResult(
            category=ALREADY,
            message=f"§2 already 7-column in every in-scope feature dir; "
                     f"{fill_pending_remaining} still await the phase-07b claim-cell fill",
            needs_llm_fill=True,
        )
    return StepResult(
        category=ALREADY,
        message="all in-scope §2 tables already carry the 7-column shape with claims filled",
    )
