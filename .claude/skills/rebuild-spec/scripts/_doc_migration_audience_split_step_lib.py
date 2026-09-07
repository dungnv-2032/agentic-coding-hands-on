#!/usr/bin/env python3
"""_doc_migration_audience_split_step_lib.py -- the `audience-split` registry step's
real body (phase-01). Split out of `run_doc_migrations.py` to keep that file under the
repo's 200-line guidance once this wiring (summary parsing + in-process invocation)
was added -- a sibling extraction, not a new subsystem.

Wraps the existing, already-shipped `migrate_feature_audience_split.py` in-process
(imported, not subprocess -- that script's own test suite already calls `cli.main()`
the same way, so this is a supported call shape, not a hack). `count_pending` reuses
the sibling's own per-feature sentinel predicate (`has_feature_sentinel`) rather than
re-deriving "already migrated" from shape detection -- one presence predicate, read
from the file, imported everywhere it is needed (phase-00 CORRECTION 2's lesson,
applied here to the sibling step even though CORRECTION 2 itself is about A3/B4).
"""
from __future__ import annotations

import contextlib
import io
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import migrate_feature_audience_split as _cli  # noqa: E402
from _audience_split_cli_lib import split_valid_slugs as _split_valid_slugs  # noqa: E402
from _audience_split_migrate_lib import (  # noqa: E402
    has_feature_sentinel as _has_feature_sentinel,
    staging_feature_dir as _staging_feature_dir,
)
from _audience_split_tally_lib import ALREADY, FAILED, INERT, PROGRESS  # noqa: E402
from _doc_migration_registry_lib import StepResult  # noqa: E402

_SUMMARY_RE = re.compile(
    r"\[SUMMARY\] units=(\d+) progress=(\d+) already=(\d+) inert=(\d+) failed=(\d+)"
)


def count_pending(docs_root: Path, project_root: Path,
                   features: "frozenset[str] | None") -> int:
    """A candidate feature dir is pending iff it has no per-feature migration
    sentinel yet -- the same predicate the sibling script itself uses to decide
    "already migrated" (imported, never reimplemented)."""
    candidates, _rejected = _split_valid_slugs(docs_root)
    if features is not None:
        candidates = [fd for fd in candidates if fd.name in features]
    return sum(
        1 for fd in candidates
        if not _has_feature_sentinel(_staging_feature_dir(docs_root, fd.name))
    )


def run(docs_root: Path, project_root: Path,
        features: "frozenset[str] | None") -> StepResult:
    """Runs the sibling script in-process and folds ITS OWN printed `[SUMMARY]` line
    back into a `StepResult` category -- every exit path of that script prints one
    (its documented, stable output contract), so parsing it is reading a contract, not
    scraping an implementation detail."""
    if features is not None:
        print(
            "[WARN] --features does not scope the audience-split step (the underlying "
            "script has no such flag) -- it ran unscoped this invocation",
            file=sys.stderr,
        )
    argv = ["--docs-root", str(docs_root), "--project-root", str(project_root)]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exit_code = _cli.main(argv)
    captured = buf.getvalue()
    sys.stdout.write(captured)
    m = _SUMMARY_RE.search(captured)
    if "run sentinel: WRITTEN (honored)" in captured:
        # A previously-sealed run sentinel was honored -- nothing ran THIS
        # invocation. The embedded summary reflects the run that SEALED the
        # sentinel, not this call, so its progress count must never be read as
        # "this run advanced something" (that misread the sibling's own honored-path
        # summary as PROGRESS on every subsequent invocation, breaking idempotency
        # reporting).
        category = ALREADY
    elif exit_code == 1 or (m and int(m.group(5)) > 0):
        category = FAILED
    elif exit_code == 4 or (m and int(m.group(4)) > 0):
        category = INERT
    elif m and int(m.group(2)) > 0:
        category = PROGRESS
    else:
        category = ALREADY
    return StepResult(category=category, message=f"exit_code={exit_code}")
