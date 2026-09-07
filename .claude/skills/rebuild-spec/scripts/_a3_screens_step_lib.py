#!/usr/bin/env python3
"""_a3_screens_step_lib.py -- the `a3-screens` `--migrate` registry step (phase-08,
plans/260818-0758-rebuild-spec-post-migration-completion).

Second APPLICATION of the mechanism P02/P03 already proved on
`features/*/technical-spec.md` -- not a second mechanism. Same family shape, one
substitution: the unit is `screens/<SCR>/spec.md`, and B4 is absent entirely. Screen
specs are UI-scoped by the validator's own module docstring
(`validate_reading_guide_db_impact.py`: "B4 ... technical-spec.md ONLY (screen-spec
stays UI-scoped)") -- this module never constructs or writes a B4 block for any file,
by construction (there is no B4_BLOCK reference anywhere below).

Reuses, never reimplements:
- `_atomic_write_lib._atomic_write` -- the same tmp+os.replace write path (phase 09,
  plans/260824-1846-rebuild-spec-action-self-sufficiency-v27-8: extracted out of the
  now-deleted `_a3_b4_scaffold_lib.py`, which this module used to import it from,
  into a neutral module neither `a3-screens` nor `screen-sot` needs to own).
- `validate_reading_guide_db_impact._section_body` -- the ONE fence-aware presence
  predicate, imported here exactly as P02/P03 import it. A second, hand-rolled
  presence check in this module would repeat the Mode B double-fold bug phase-00
  documents (see "Reusable machinery already in the repo").

`A3_BLOCK` below was deliberately NOT imported from the (now-retired, phase 09)
`a3-b4` step's own scaffold module even though the wording was otherwise identical:
that module's block baked in `--only a3-b4` as the fill command, which was the WRONG
step name for a screen spec (the correct re-run command is `--only a3-screens`).
Importing it verbatim would have shipped every one of the 182 scaffolded screens with
a placeholder that told the operator to run the wrong step. The fix was a same-shaped
local constant here rather than a shared parameter threaded through the module that
owned the other block -- which is exactly why this module survived that module's
deletion with nothing to repoint on the A3_BLOCK side. The brace-placeholder SHAPE
(prose + one `{...}` span, no table) is identical and is proven against the real
validator below.

`--features` narrowing has no natural meaning here: screen dirs are keyed by
`SCR###_Slug`, not by feature slug, and a screen has no recorded owning feature this
module can read cheaply. The registry's `CountPendingFn`/`RunFn` signature is fixed
across all registered steps, so `features` is accepted for shape parity and silently
ignored -- matching how the sibling `_doc_migration_screen_sot_step_lib.py` ignores
the unrelated `project_root` parameter for the same reason.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _atomic_write_lib import _atomic_write  # noqa: E402
from _audience_split_tally_lib import ALREADY, FAILED, PROGRESS  # noqa: E402
from _doc_migration_registry_lib import StepResult  # noqa: E402
from _spec_constants import A3_HEADING  # noqa: E402
from validate_reading_guide_db_impact import _section_body  # noqa: E402

FeatureFilter = "frozenset[str] | None"

_FILL_COMMAND = "run_doc_migrations.py --migrate --only a3-screens"

# Same shape as the (now-retired, phase 09) a3-b4 step's own A3_BLOCK (prose + ONE
# brace placeholder, no `**File:**`, no path, no diagram) -- deliberately a local
# constant, not a shared import; see module docstring for why.
A3_BLOCK = (
    f"{A3_HEADING}\n\n"
    "{UNFILLED SCAFFOLD -- this reading list has not been authored yet; it requires "
    f"reading the screen's source. Fill it by running `{_FILL_COMMAND}`.}}\n"
)


def iter_screen_specs(docs_root: Path, features: "FeatureFilter" = None) -> list[Path]:
    """`features` is accepted for `CountPendingFn`/`RunFn` signature parity and
    ignored -- see module docstring."""
    del features
    return sorted(docs_root.glob("screens/*/spec.md"))


def _needs_a3(text: str) -> bool:
    return _section_body(text, A3_HEADING) is None


def scaffold_text(text: str) -> str | None:
    """A3-only scaffold: append `A3_BLOCK` if missing, else `None` (caller must not
    write). Never appends a B4 block -- screens have no such section."""
    if not _needs_a3(text):
        return None
    return text.rstrip("\n") + "\n\n" + A3_BLOCK.rstrip("\n") + "\n"


def scaffold_file(path: Path) -> bool:
    """Scaffold `path` in place. Returns `True` if A3 was added, `False` if already
    present or unreadable (skip, never raise on a read failure). A WRITE failure
    (disk full, permissions) DOES raise -- the caller decides how to tally that."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    new_text = scaffold_text(text)
    if new_text is None:
        return False
    _atomic_write(path, new_text)
    return True


def scaffold_corpus(
    docs_root: Path, features: "FeatureFilter" = None,
) -> tuple[int, int]:
    """Scaffold every in-scope `screens/*/spec.md` missing A3. Returns
    `(files_changed, write_errors)`."""
    changed = errors = 0
    for spec in iter_screen_specs(docs_root, features):
        try:
            added = scaffold_file(spec)
        except OSError:
            errors += 1
            continue
        if added:
            changed += 1
    return changed, errors


def count_pending(docs_root: Path, project_root: Path, features: "FeatureFilter") -> int:
    """Registry `count_pending`: number of `screens/*/spec.md` still missing A3 --
    the artifact-derived done-predicate (phase-00 CORRECTION 2), never a marker file.
    `project_root` is part of the registry's fixed `CountPendingFn` signature and is
    unused here, matching every sibling step's `count_pending`."""
    del project_root
    pending = 0
    for spec in iter_screen_specs(docs_root, features):
        try:
            text = spec.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if _needs_a3(text):
            pending += 1
    return pending


def run(docs_root: Path, project_root: Path, features: "FeatureFilter") -> StepResult:
    """Registry `run`: scaffold, then report. `needs_llm_fill=True` on any real
    progress -- a scaffold is structure, never content; the driver forces this to
    INERT so `--migrate` can never read as complete from scaffolding alone (the
    screens researcher fill pass, `references/pipeline-migrate.md` § screens, closes
    the gap)."""
    del project_root
    changed, errors = scaffold_corpus(docs_root, features)
    if errors:
        return StepResult(
            category=FAILED,
            message=f"{errors} screen spec(s) failed to write ({changed} scaffolded "
                     "before the failure) -- re-run --only a3-screens after fixing "
                     "the write error",
        )
    if changed == 0:
        return StepResult(category=ALREADY,
                           message="all in-scope screens/*/spec.md already carry A3")
    return StepResult(
        category=PROGRESS,
        message=f"scaffolded {changed} screens/*/spec.md ({A3_HEADING!r} section(s) "
                 "added) -- researcher fill pass still required",
        needs_llm_fill=True,
    )
