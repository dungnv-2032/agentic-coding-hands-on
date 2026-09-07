"""Outcome tally for the v26 -> v27 audience-split migration run (phase-06, B2/B3).

`categorize()` is the ONLY place an outcome's `action` string is mapped to a run-level
category -- both the sentinel-write decision (B2) and the printed summary (B3) read
through this one function, so they cannot drift apart the way `_run_migration`'s old
`all_ok = features_ok and business_rules_ok and screens_ok` (B2's bug) silently did.

The map below is verified EXHAUSTIVE against the real source (phase-00 § U1: every
action string `_audience_split_orchestrate_bc_lib.py` and `migrate_feature_audience_split.py`
can emit). An action not in the map still resolves -- `categorize()` never raises -- but
to FAILED, the fail-closed default, with a loud stderr warning from `Tally.add()`, so a
future action added elsewhere can never silently re-open B2 by falling through to
PROGRESS or ALREADY.

`UnrecognizedShapeError` (I6) is RAISED, not returned as an outcome -- there is no
action string for it. Callers record it directly via `Tally.add_refused()`.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).parent))
from _audience_split_review_gate_lib import (  # noqa: E402
    DEFAULT_MINIMUM, DEFAULT_RATIO, required_sample_size,
)
from _audience_split_shape_lib import V26_SATELLITE_FILES  # noqa: E402

PROGRESS = "progress"  # this run advanced a unit
ALREADY = "already"    # a prior run already finished it
INERT = "inert"        # left behind in pre-v27 shape -- the corpus is NOT migrated
FAILED = "failed"      # errored or refused

# String-value-matches _audience_split_probe_lib.CLEAN / CLEAN_LEGACY, deliberately not
# imported from there -- this module reports on verdicts, it does not own probing, and a
# by-value match keeps that boundary an explicit contract rather than an import coupling.
CLEAN = "clean"
CLEAN_LEGACY = "clean-legacy"

_ACTION_CATEGORY: dict[str, str] = {
    "migrated": PROGRESS,
    "migrated-originals-retained": PROGRESS,
    # REWORK (adversarial review finding 4, LOW): phase-00 § U1's settled table
    # (see plans/260817-1420-rebuild-spec-v27-migrate-legacy-docs/
    # phase-00-verified-context.md) maps `confirmed-v27` -> ALREADY, not
    # PROGRESS -- the action means "already in the target shape; sentinel
    # written" (migrate_feature_audience_split.py:200), which is semantically
    # "a prior run already finished it", not "this run advanced a unit".
    # Verified to affect neither `sentinel_worthy` nor `exit_code()` (both key
    # only off failed/inert) nor the common idempotency path -- the only
    # observable effect was the printed [SUMMARY] line misreporting
    # progress=N for units that advanced nothing.
    "confirmed-v27": ALREADY,
    "no-op": ALREADY,
    "skipped-hand-edited": INERT,
    "rejected-bad-slug": INERT,
    "skipped-no-target": INERT,
    "failed-validation": FAILED,
    "refused-invalid-v27": FAILED,
}


def categorize(action: str) -> str:
    """Map an outcome's `action` string to its run-level category. Unknown action ->
    FAILED (fail-closed default) -- never raises, never silently becomes PROGRESS/
    ALREADY/INERT. See `Tally.add()` for the accompanying stderr warning."""
    return _ACTION_CATEGORY.get(action, FAILED)


@dataclass
class Tally:
    """Accumulates one run's outcomes. `sentinel_worthy` and `exit_code()` are the
    single source of truth for B2 (never seal an unmigrated corpus) and the new exit-4
    contract (phase-06)."""

    units: int = 0
    progress: int = 0
    already: int = 0
    inert: int = 0
    failed: int = 0
    clean: int = 0
    clean_legacy: int = 0
    retained: int = 0
    inert_by_action: dict[str, int] = field(default_factory=dict)

    def record(self, category: str, *, action: str = "", provenance: str = "") -> None:
        """Low-level recorder, used when the category is already known (e.g. a raised
        exception, or a `--dry-run` preview that never produced a real outcome)."""
        self.units += 1
        if category == PROGRESS:
            self.progress += 1
            # phase-05: this run's own count of "migrated but originals retained"
            # outcomes -- reported in [SUMMARY] as history of THIS run. It is NOT
            # the source of truth for the [ACTION REQUIRED] affordance -- a re-run
            # over an already-hybrid corpus resolves to `confirmed-v27` (ALREADY),
            # never re-touching this counter, even though satellites are still on
            # disk. See `count_retained_satellite_dirs` for the artifact-derived
            # count that stays correct on that path.
            if action == "migrated-originals-retained":
                self.retained += 1
        elif category == ALREADY:
            self.already += 1
        elif category == INERT:
            self.inert += 1
            if action:
                self.inert_by_action[action] = self.inert_by_action.get(action, 0) + 1
        else:
            self.failed += 1
        if provenance == CLEAN:
            self.clean += 1
        elif provenance == CLEAN_LEGACY:
            self.clean_legacy += 1

    def add(self, action: str, *, provenance: str = "") -> str:
        """Record one real outcome by its action string (U1's exhaustive map, verified
        against the source above). T10: an action not in the map is FAILED, fail-closed,
        with a loud warning here -- this is the one place that fallback happens."""
        if action not in _ACTION_CATEGORY:
            print(
                f"[WARN] unrecognized migration action {action!r} -- treating as FAILED "
                f"(fail-closed default; categorize() in _audience_split_tally_lib.py has "
                f"no entry for it)",
                file=sys.stderr,
            )
        category = categorize(action)
        self.record(category, action=action, provenance=provenance)
        return category

    def add_refused(self, action: str = "refused-unrecognized-shape") -> None:
        """`UnrecognizedShapeError` (I6) is raised, not returned -- record it directly as
        FAILED without a `categorize()` lookup (U1)."""
        self.record(FAILED, action=action)

    @property
    def sentinel_worthy(self) -> bool:
        """B2 fix: write the run sentinel iff FAILED == 0 and INERT == 0 -- an all-skip
        run (249/249 `skipped-hand-edited`, the original B2 defect) is INERT=249 and
        never seals."""
        return self.failed == 0 and self.inert == 0

    def exit_code(self) -> int:
        """FAILED outranks INERT (T6): something breaking is always worse than nothing
        having moved yet."""
        if self.failed:
            return 1
        if self.inert:
            return 4
        return 0

    def to_dict(self) -> dict:
        """The tally payload the JSON run sentinel carries (phase-06 sentinel contract).
        `format_version`/`written_at` are added by the sentinel writer, not here."""
        return {
            "units": self.units, "progress": self.progress, "already": self.already,
            "inert": self.inert, "failed": self.failed,
            "clean": self.clean, "clean_legacy": self.clean_legacy,
            "retained": self.retained,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Tally":
        """Reconstruct a Tally from an honored run sentinel's payload, so the honored
        path prints the exact same `[SUMMARY]` shape a live run would (B3). `.get(k, 0)`
        means an old sentinel written before `retained` existed restores it as 0 rather
        than raising -- self-healing, not a breaking format change."""
        return cls(**{k: int(data.get(k, 0)) for k in
                       ("units", "progress", "already", "inert", "failed", "clean",
                        "clean_legacy", "retained")})

    def summary_line(self, *, sentinel_state: str, retained_on_disk: int | None = None) -> str:
        """B3: printed on every exit path (T15) -- a run that accomplished nothing must
        say so, never just exit silently. `retained` (phase-05) is appended AFTER the
        existing units/progress/already/inert/failed run -- `_doc_migration_audience_
        split_step_lib._SUMMARY_RE` only captures through `failed=(\\d+)` and never
        anchors to end-of-string, so appending here is additive, not a format break.

        `retained_on_disk` is the artifact-derived count from
        `count_retained_satellite_dirs`. PREFER IT. `self.retained` only counts the
        `migrated-originals-retained` ACTION, which a re-run over an already-hybrid
        corpus never emits (it reports `confirmed-v27`/ALREADY) -- so on any re-run the
        action tally reads 0 while satellites are still sitting on disk. Printing that
        next to an `[ACTION REQUIRED]` block that correctly says 59 is two numbers for
        one fact, disagreeing on adjacent lines: the same two-sources-of-truth shape as
        the sentinel-vs-artifact bugs this pipeline has already shipped twice. Callers
        that can reach the feature dirs MUST pass this; the fallback exists only for
        callers with no corpus in hand (e.g. `Tally.from_dict` on a stored sentinel)."""
        retained = self.retained if retained_on_disk is None else retained_on_disk
        return (
            f"[SUMMARY] units={self.units} progress={self.progress} already={self.already} "
            f"inert={self.inert} failed={self.failed} retained={retained} | "
            f"provenance: authored_by={self.clean} marker={self.clean_legacy} | "
            f"run sentinel: {sentinel_state}"
        )

    def inert_breakdown_lines(self) -> list[str]:
        """Per-reason breakdown (phase-06: 'the operator gets the cause, not just the
        count') -- one line per INERT action, sorted for deterministic output."""
        return [
            f"[INFO] inert breakdown: {action}={count}"
            for action, count in sorted(self.inert_by_action.items())
        ]

    def accomplished_nothing_message(self) -> str:
        """The `[ERROR]` line for the exit-4 case specifically (FAILED == 0, INERT > 0) --
        the defining failure shape this phase fixes (B2/B3)."""
        reasons = ", ".join(f"{a}={c}" for a, c in sorted(self.inert_by_action.items()))
        return (
            f"[ERROR] migration accomplished nothing: {self.progress} of {self.units} "
            f"units advanced; {self.inert} left in pre-v27 shape ({reasons}). Exit 4."
        )


# --------------------------------------------------------------------------- #
# Retained-satellite affordance (phase-05, GAP 2(a)) -- reporting only, the
# `--reviewed` delete gate itself (_audience_split_review_gate_lib.py) is untouched.
# --------------------------------------------------------------------------- #
def count_retained_satellite_dirs(feature_dirs: Iterable[Path]) -> int:
    """Artifact-derived count of feature dirs that CURRENTLY hold at least one v26
    satellite file on disk -- read fresh every call, never taken from a `Tally`. A dir
    can hold satellites for a reason this run's tally never recorded (e.g. the
    `SHAPE_V27_HYBRID` confirm-and-seal branch reports `confirmed-v27`/ALREADY, never
    `migrated-originals-retained`), so this is the only truthful source for the
    `[ACTION REQUIRED]` block below -- including on the honored-sentinel path, where no
    real migration ran this invocation at all."""
    return sum(
        1 for fd in feature_dirs
        if any((fd / name).is_file() for name in V26_SATELLITE_FILES)
    )


def action_required_block(retained: int, *, script_path: Path, docs_root: Path,
                           project_root: Path) -> str | None:
    """The GAP 2(a) next-step affordance. `None` when *retained* is 0 -- printed only
    when there is a real action to take. Never emits a pre-filled `--reviewed`
    manifest (a file the operator could hand straight back would turn a human review
    into one keystroke); it names the count, the required sample size (via
    `required_sample_size`, never a literal), and the exact command to run once that
    review is done."""
    if retained <= 0:
        return None
    required = required_sample_size(retained)
    satellites = ", ".join(V26_SATELLITE_FILES)
    return (
        f"[ACTION REQUIRED] {retained} feature dir(s) still hold v26 satellites "
        f"({satellites}). They are retained pending human review -- nothing is lost. "
        f"Review at least {required} of them (>={DEFAULT_RATIO:.0%}, minimum "
        f"{DEFAULT_MINIMUM}), list the reviewed slugs one per line in a file, then "
        f"re-run:\n"
        f"    python3 {script_path} --docs-root {docs_root} --project-root "
        f"{project_root} --reviewed <that-file>\n"
        f"Secondary-language mirrors cannot be regenerated until this is done -- see "
        f"references/migration-audience-split.md."
    )
