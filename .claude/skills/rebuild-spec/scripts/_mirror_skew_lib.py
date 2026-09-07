#!/usr/bin/env python3
"""_mirror_skew_lib.py -- the `mirror-skew` `--migrate` registry step (phase-06,
plans/260818-0758-rebuild-spec-post-migration-completion). Skew detection itself
lives in `_mirror_skew_detect_lib.py` (split out to keep this file under the
repo's 200-line guidance); this module re-exports it and adds the registry
`count_pending`/`run` wiring plus the translate handoff.

This module writes NOTHING to the primary or the mirrors. The narrow, destructive
prune lives in `prune_mirror_v26_satellites.py`, a separate standalone script the
operator runs explicitly -- this module only detects, refuses-or-reads, and hands
off (never spawns the TR.2 translator fan-out itself, per the plan's "--migrate
spawns nothing").

The primary is not ready to be translated from while any feature dir is still
`SHAPE_V27_HYBRID` (satellites retained pending human review) -- translating then
would mirror the retained v26 satellites into every secondary language. `run()`
refuses the translate handoff in that case and names the exact `--reviewed`
follow-up command via `_audience_split_tally_lib.action_required_block` (imported,
never re-derived -- one message for both the audience-split CLI's own next-step
affordance and this refusal).
"""
from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _audience_split_tally_lib import (  # noqa: E402
    ALREADY, FAILED, INERT, PROGRESS, action_required_block,
)
from _doc_migration_registry_lib import StepResult, handoff_line  # noqa: E402
from _mirror_skew_detect_lib import (  # noqa: E402
    MirrorSkew, count_hybrid_primary_dirs, detect_skew, render_skew_lines,
)

__all__ = [
    "MirrorSkew", "detect_skew", "render_skew_lines", "count_pending", "run",
]

FeatureFilter = "frozenset[str] | None"

# The pass fed to `translation_sync_gate.py --mode plan` -- GAP 1's scope (phase-00)
# is the feature-specs family; flows/glossary/screen-specs etc. are a follow-up.
TRANSLATE_PASS = "feature-specs"

_AUDIENCE_SPLIT_SCRIPT = Path(__file__).parent / "migrate_feature_audience_split.py"


def count_pending(docs_root: Path, project_root: Path, features: "FeatureFilter") -> int:
    """Registry `count_pending`: number of registered secondary languages still
    stale. 0 iff every registered mirror already matches the primary's v27 shape
    and translate cursor -- the done predicate. `project_root`/`features` are part
    of the registry's fixed `CountPendingFn` signature and are unused here (this
    step is lang-scoped, not feature-scoped -- matching the `audience-split`
    step's own precedent of accepting the fixed signature without using every
    parameter)."""
    return sum(1 for s in detect_skew(docs_root) if s.stale)


def _invoke_translation_sync_plan(docs_root: Path, project_root: Path) -> tuple[int, str]:
    """In-process call into `translation_sync_gate.py --mode plan` (read-only: see
    `_run_plan` in that module -- no lock, no write, pure JSON worklist to
    stdout). Captures and returns its REAL exit code and stdout so the caller
    echoes the output verbatim, never re-composed (references/pipeline-
    translate.md forbids hand-composing any of this script's canonical output),
    and can treat a non-zero exit (e.g. a state file outside *project_root*) as a
    real failure rather than silently swallowing it."""
    import translation_sync_gate as _translate_gate

    argv = [
        "--mode", "plan", "--pass", TRANSLATE_PASS,
        "--state", str(docs_root / ".rebuild-state.json"),
        "--primary-docs-root", str(docs_root),
        "--project-root", str(project_root),
    ]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exit_code = _translate_gate.main(argv)
    return exit_code, buf.getvalue()


def run(docs_root: Path, project_root: Path, features: "FeatureFilter") -> StepResult:
    """Registry `run`: print the skew report, refuse the translate handoff while
    the primary is hybrid (naming the exact `--reviewed` follow-up), else invoke
    the existing translate-sync plan (read-only) and print a `[HANDOFF]` for the
    orchestrator to run TR.2/TR.3/TR.4. This function never deletes a file and
    never spawns the translator fan-out itself."""
    if features is not None:
        print(
            "[WARN] --features does not scope the mirror-skew step (it operates "
            "on registered secondary languages, not individual features) -- it "
            "ran unscoped this invocation",
            file=sys.stderr,
        )

    skews = detect_skew(docs_root)
    for line in render_skew_lines(skews):
        print(line)

    if not skews:
        return StepResult(
            category=ALREADY,
            message="no secondary languages registered -- nothing to translate",
        )

    hybrid = count_hybrid_primary_dirs(docs_root)
    if hybrid > 0:
        block = action_required_block(
            hybrid, script_path=_AUDIENCE_SPLIT_SCRIPT,
            docs_root=docs_root, project_root=project_root,
        )
        if block:
            print(block)
        return StepResult(
            category=INERT,
            message=(
                f"{hybrid} primary feature dir(s) still v27 hybrid -- translate "
                "handoff refused until the --reviewed satellite delete clears them"
            ),
        )

    gate_exit_code, gate_stdout = _invoke_translation_sync_plan(docs_root, project_root)
    sys.stdout.write(gate_stdout)
    if gate_stdout and not gate_stdout.endswith("\n"):
        print()
    if gate_exit_code != 0:
        return StepResult(
            category=FAILED,
            message=f"translation_sync_gate.py --mode plan exited {gate_exit_code} -- see stdout/stderr above",
        )

    stale_langs = [s.lang for s in skews if s.stale]
    if not stale_langs:
        return StepResult(category=ALREADY, message="all registered mirrors already in sync")

    print(handoff_line(
        "mirror-skew",
        f"secondary language(s) {', '.join(stale_langs)} still need translating -- "
        "run the TR.2 translator fan-out (subagent_type=\"translator\", Haiku) + "
        "TR.3 skeleton gate + TR.4 promote per lang, per "
        "references/pipeline-translate.md. --migrate itself spawns nothing.",
    ))
    return StepResult(
        category=PROGRESS,
        message=f"translate worklist computed, handoff issued for {', '.join(stale_langs)}",
        needs_llm_fill=True,
    )
