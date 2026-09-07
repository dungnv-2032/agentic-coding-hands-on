#!/usr/bin/env python3
"""_cap_map_rollback_lib.py -- `--rollback cap-map` (phase-07,
plans/260819-1016-rebuild-spec-capability-map). Split out of
`_doc_migration_cap_map_step_lib.py` to keep both files under the repo's 200-line
guidance (the `_mirror_skew_lib` / `_mirror_skew_detect_lib` precedent).

Restores every `.bak` `run()` wrote (write-before-destroy), REFUSING -- never
destroying -- any feature whose live `claim_state` is `"filled"` or `"partial"`: a
human did modelling work in those claim cells, and restoring the narrow table would
throw it away. Mirrors `_audience_split_migrate_lib.rollback_feature`'s sentinel
refusal verbatim ("migration COMPLETE, not partial -- reversed through the customer's
own VCS, not this tool"). An atomic write is crash-safety, not undo (see the step
lib's docstring) -- this module is the actual undo path, and it stops rather than
guesses whenever completed human work is in front of it.

Never raises out of `rollback()` -- `run_doc_migrations.py`'s `--rollback` dispatch
has no try/except of its own, matching `run()`'s contract in the step lib.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _audience_split_tally_lib import ALREADY, FAILED, PROGRESS  # noqa: E402
from _cap_map_io_lib import (  # noqa: E402
    atomic_write, backup_path as _backup_path, iter_feature_dirs, read_text,
)
from _cap_map_table_widen_lib import analyze  # noqa: E402
from _doc_migration_registry_lib import StepResult  # noqa: E402
from _slug_lib import assert_under  # noqa: E402

FeatureFilter = "frozenset[str] | None"


def rollback(docs_root: Path, project_root: Path, features: "FeatureFilter") -> StepResult:
    """[FM-3] Restore `.bak`s; refuse (print + skip, never destroy) filled/partial
    features; exit non-zero (via FAILED category) whenever anything was refused or a
    real I/O error occurred."""
    del project_root
    restored = 0
    refused = 0
    failures: list[str] = []
    for feature_dir in iter_feature_dirs(docs_root, features):
        bak = _backup_path(docs_root, feature_dir.name)
        if bak.is_symlink():
            failures.append(f"{bak}: refusing a symlinked backup")
            continue
        if not bak.is_file():
            continue  # nothing staged for this feature -- nothing to roll back
        func_path = feature_dir / "functional-spec.md"
        text = read_text(func_path)
        if text is None:
            failures.append(f"{func_path}: read failed")
            continue
        a = analyze(text.splitlines())
        if a.state in ("filled", "partial"):
            print(
                f"[REFUSED] cap-map rollback: {feature_dir.name} claim_state={a.state} "
                "-- a human filled claim cells here; restoring the narrow table would "
                "destroy that work. Reverse through the customer's own VCS instead.",
                file=sys.stderr,
            )
            refused += 1
            continue
        backup_text = read_text(bak)
        if backup_text is None:
            failures.append(f"{bak}: read failed")
            continue
        try:
            assert_under(func_path, docs_root)
            atomic_write(func_path, backup_text)
            bak.unlink()
        except (OSError, ValueError) as exc:
            failures.append(f"{feature_dir.name}: rollback write failed ({exc})")
            continue
        restored += 1

    if failures:
        return StepResult(
            category=FAILED,
            message=f"{len(failures)} feature dir(s) failed to roll back ({restored} "
                     f"restored, {refused} refused before the failure(s)): "
                     f"{'; '.join(failures)} -- re-run `run_doc_migrations.py "
                     f"--docs-root <docs> --rollback cap-map`",
        )
    if refused:
        return StepResult(
            category=FAILED,
            message=f"{refused} feature dir(s) refused (filled/partial claim cells; "
                     f"restored the other {restored}) -- reverse those through the "
                     "customer's own VCS instead",
        )
    if restored == 0:
        return StepResult(category=ALREADY, message="no cap-map .bak backups found to restore")
    return StepResult(category=PROGRESS, message=f"restored {restored} feature dir(s) from .bak")
