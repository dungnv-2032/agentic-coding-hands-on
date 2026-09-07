#!/usr/bin/env python3
"""_doc_migration_feature_sot_step_lib.py -- the `feature-sot` `--migrate` registry
step (phase-10, plans/260818-1332-rebuild-spec-human-readable-sot).

THIN DRIVER over `_feature_sot_functional_lib.compose_functional_sot` and
`_feature_sot_technical_lib.compose_technical_sot` -- the sole authorities on the SOT
target orders. This module owns no reshaping logic of its own; it discovers
`features/*/functional-spec.md` + its sibling `technical-spec.md`, composes
functional FIRST, then technical (reading the freshly-composed functional text as
its twin -- the Architecture diagram in phase-10.md: "reads the composed functional
text for CAP-N list / US### set"), and writes BOTH atomically, or neither.

`count_pending` is artifact-derived (never a marker file): a feature dir is pending
when its `functional-spec.md` lacks `"## 2. Functional Capabilities"` OR its sibling
`technical-spec.md` lacks `"## 2. Functional → Technical Mapping"` -- either
composer's own idempotency sentinel, imported nowhere here (duplicated as two
literal headings) to avoid a runtime import cycle with the compose modules; both
literals are the exact strings `REQUIRED_H2_FUNC[1]` / `REQUIRED_H2_TECH[1]` name.

`feature-sot` DOES write `technical-spec.md` -- `run_doc_migrations.py` MUST add it
to `_writes_technical_spec`/`_TECH_SPEC_STEPS` so the A1 confidence-report refresh
fires. This is the opposite of `screen-sot`'s rule (screen-spec-only, never in that
set) -- getting it backwards is silent: the companions just go stale.

Per-feature-dir isolation, matching `_doc_migration_screen_sot_step_lib.py`'s
precedent: a read/write failure on one feature dir is recorded and the loop
continues; every other in-scope feature dir is still composed before the step
reports FAILED overall.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _audience_split_tally_lib import ALREADY, FAILED, PROGRESS  # noqa: E402
from _doc_migration_registry_lib import StepResult  # noqa: E402
from _feature_sot_functional_lib import compose_functional_sot  # noqa: E402
from _feature_sot_technical_lib import compose_technical_sot  # noqa: E402

FeatureFilter = "frozenset[str] | None"

_FILL_COMMAND = "run_doc_migrations.py --migrate --only feature-sot"

# The literal 2nd-required-heading each composer emits -- see module docstring for
# why these are inlined rather than imported.
_FUNC_PENDING_HEADING = "## 2. Functional Capabilities"
_TECH_PENDING_HEADING = "## 2. Functional → Technical Mapping"


def _iter_feature_dirs(docs_root: Path, features: "FeatureFilter" = None) -> list[Path]:
    """Every feature dir under *docs_root* that carries a `functional-spec.md` --
    keyed off THAT file (not `technical-spec.md`) since content-preservation-map's
    Key Insight is explicit: the pair is created together by `audience-split`, so a
    `functional-spec.md` with no sibling is the anomaly `run()` reports FAILED for,
    not a shape `count_pending`/`run` silently skip."""
    dirs = sorted(p.parent for p in docs_root.glob("features/*/functional-spec.md"))
    if features is not None:
        dirs = [d for d in dirs if d.name in features]
    return dirs


def _is_pending(func_text: str, tech_text: str | None) -> bool:
    if _FUNC_PENDING_HEADING not in func_text:
        return True
    return tech_text is None or _TECH_PENDING_HEADING not in tech_text


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def count_pending(docs_root: Path, project_root: Path, features: "FeatureFilter") -> int:
    """Registry `count_pending`: number of feature dirs not yet composed to the SOT
    shape -- pure read, never a marker file. An unreadable `functional-spec.md` is
    skipped here (not counted either way); `run()` is where it surfaces as FAILED."""
    del project_root
    pending = 0
    for feature_dir in _iter_feature_dirs(docs_root, features):
        func_text = _read(feature_dir / "functional-spec.md")
        if func_text is None:
            continue
        tech_text = _read(feature_dir / "technical-spec.md")
        if _is_pending(func_text, tech_text):
            pending += 1
    return pending


def _cleanup(tmp_path: str) -> None:
    try:
        os.unlink(tmp_path)
    except OSError:
        pass


def _atomic_write_pair(path_a: Path, text_a: str, path_b: Path, text_b: str) -> None:
    """Write functional-spec.md then technical-spec.md, each via its own staged
    temp-file-then-rename. Both files are staged to their own tmp file FIRST -- a
    failure during either temp write (disk full, permissions) leaves neither real
    file touched, which is real.

    NOT guaranteed (reviewer-260819-0858-inspection.md M1): the two `os.replace`
    calls below are independent syscalls, not one shared transaction -- a kill
    between them, or the SECOND one raising (cross-device rename, disk full mid-
    run), leaves `path_a` already renamed while `path_b` is not. Recoverable, not
    silent: `_is_pending` still reports the pair pending next run, and both
    composers are idempotent on already-SOT input, so `--migrate` self-heals it.
    This writes A, then independently writes B -- never claim more."""
    fd_a, tmp_a = tempfile.mkstemp(dir=path_a.parent, suffix=".tmp")
    try:
        with os.fdopen(fd_a, "w", encoding="utf-8") as fh:
            fh.write(text_a)
    except Exception:
        _cleanup(tmp_a)
        raise
    try:
        fd_b, tmp_b = tempfile.mkstemp(dir=path_b.parent, suffix=".tmp")
    except Exception:
        _cleanup(tmp_a)
        raise
    try:
        with os.fdopen(fd_b, "w", encoding="utf-8") as fh:
            fh.write(text_b)
    except Exception:
        _cleanup(tmp_a)
        _cleanup(tmp_b)
        raise
    os.replace(tmp_a, path_a)
    try:
        os.replace(tmp_b, path_b)
    except Exception:
        # path_a is already renamed at this point (see docstring: not a shared
        # transaction) -- that is accepted and self-heals next run. What must NOT
        # happen is tmp_b's now-orphaned temp file surviving forever on disk.
        _cleanup(tmp_b)
        raise


def run(docs_root: Path, project_root: Path, features: "FeatureFilter") -> StepResult:
    """Registry `run`: compose functional then technical (technical reads the
    freshly-composed functional text as its twin), write atomically per feature
    dir. A read/write failure or a missing sibling is recorded and the loop
    continues (isolation); `needs_llm_fill=True` on any real progress, which the
    driver's fail-closed override forces to INERT -- both composers scaffold
    `[L]`/`{...}` content a researcher must still fill."""
    del project_root
    changed = 0
    failures: list[str] = []
    for feature_dir in _iter_feature_dirs(docs_root, features):
        func_path = feature_dir / "functional-spec.md"
        tech_path = feature_dir / "technical-spec.md"
        func_text = _read(func_path)
        if func_text is None:
            failures.append(f"{func_path}: read failed")
            continue
        if not tech_path.exists():
            if _FUNC_PENDING_HEADING not in func_text:
                failures.append(
                    f"{feature_dir}: functional-spec.md has no sibling technical-spec.md "
                    "-- feature-sot needs the pair"
                )
            continue
        tech_text = _read(tech_path)
        if tech_text is None:
            failures.append(f"{tech_path}: read failed")
            continue
        if not _is_pending(func_text, tech_text):
            continue
        func_result = compose_functional_sot(func_text)
        tech_result = compose_technical_sot(tech_text, func_result.text)
        try:
            _atomic_write_pair(func_path, func_result.text, tech_path, tech_result.text)
        except OSError as exc:
            failures.append(f"{feature_dir}: write failed ({exc})")
            continue
        changed += 1

    if failures:
        return StepResult(
            category=FAILED,
            message=f"{len(failures)} feature dir(s) failed ({changed} composed before "
                     f"the failure(s)): {'; '.join(failures)} -- fix the error(s) then "
                     f"re-run `{_FILL_COMMAND}`",
        )
    if changed == 0:
        return StepResult(
            category=ALREADY,
            message="all in-scope features/*/{functional,technical}-spec.md pairs "
                     "already carry the SOT shape",
        )
    return StepResult(
        category=PROGRESS,
        message=f"composed {changed} feature-spec pair(s) to the SOT shape -- "
                 "researcher fill pass still required for scaffolded content",
        needs_llm_fill=True,
    )
