#!/usr/bin/env python3
"""run_doc_migrations.py -- `--migrate` CLI: finish what a rebuild-spec version
upgrade leaves behind (phase-01, plans/260818-0758-rebuild-spec-post-migration-completion).

    run_doc_migrations.py --docs-root docs [--migrate] [--dry-run]
                           [--only STEP ...] [--features F001,F002]
                           [--project-root PATH] [--rollback STEP]

`--only STEP` is repeatable; omit it to run every registered step in dependency order
(`_doc_migration_registry_lib.STEP_ORDER`). `--dry-run` prints per-step pending counts
and writes NOTHING. Exit codes are `Tally.exit_code()` verbatim: 0 ok/no-op, 1 any step
FAILED, 4 nothing advanced (refused or unimplemented, nothing broken), 2 bad invocation.

Flag composition: any generation flag (`--feature-specs`, `--flows`, `--glossary`,
`--test-cases`, `--screen-specs`, `--api-contracts`, `--overview`, `--api-doc`,
`--artifact`) combined with `--migrate`, or `--lang` naming
anything other than the resolved primary language, is a bad invocation -- exit 2.
`--full`/`--since` are warned about and ignored.

`--rollback STEP` (phase-07, plans/260819-1016-rebuild-spec-capability-map; joined by
`action-thread` in phase-06, plans/260824-1128-rebuild-spec-action-thread-v27-7): undo
a step's own write, for the two steps that ship one. Any other STEP name exits 2
naming the supported values (YAGNI: no generic rollback registry beyond the steps
that actually implement one). Exits non-zero if anything was refused (`cap-map`: a
feature whose claim cells a human already filled; `action-thread`: a feature whose
unresolved-marker count has dropped since migrate ran) or failed; 0 on a clean
restore or "nothing to roll back". Never combined with `--migrate`/`--dry-run`/
`--only` -- checked before those are read.

`audience-split`, `a3-screens`, `screen-sot`, `feature-sot`, `cap-map`,
`action-thread`, `mirror-skew` all have real bodies, each split into its own
`_doc_migration_<name>_step_lib.py` (or a same-family sibling module) to keep this
file under the repo's 200-line guidance. phase-06 ADDENDUM: the A1 confidence-report
refresh fires only for a technical-spec step that ACTUALLY RAN (`registry.execute`'s
`ran` set), never merely requested -- a refused step never calls `run()` and must not
trigger a companion rewrite either. phase-09 (plans/260824-1846-rebuild-spec-action-
self-sufficiency-v27-8) RETIRED the `a3-b4` step that used to sit between
`audience-split` and `a3-screens` -- A3/B4 left `technical-spec.md`'s target shape in
phase 08, leaving `a3-b4` nothing left to scaffold; `a3-screens`'s own prerequisite
repointed straight to `audience-split`.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _a3_screens_step_lib as _a3_screens_step  # noqa: E402
import _cap_map_rollback_lib as _cap_map_rollback  # noqa: E402
import _confidence_report_refresh_lib as _confidence_refresh  # noqa: E402
import _doc_migration_action_thread_step_lib as _action_thread_step  # noqa: E402
import _doc_migration_audience_split_step_lib as _audience_split_step  # noqa: E402
import _doc_migration_cap_map_step_lib as _cap_map_step  # noqa: E402
import _doc_migration_feature_sot_step_lib as _feature_sot_step  # noqa: E402
import _doc_migration_registry_lib as registry  # noqa: E402
import _doc_migration_screen_sot_step_lib as _screen_sot_step  # noqa: E402
import _mirror_skew_lib as _mirror_skew_step  # noqa: E402
from _audience_split_cli_lib import (  # noqa: E402
    git_toplevel as _git_toplevel, mirror_refusal_reason as _mirror_refusal_reason,
    resolve_project_root_for_docs as _resolve_project_root_for_docs,
)
from _audience_split_tally_lib import FAILED as _ROLLBACK_FAILED  # noqa: E402
from _slug_lib import assert_under as _assert_under  # noqa: E402

# `--rollback STEP`: "cap-map" (phase-07) and "action-thread" (phase-06,
# plans/260824-1128-rebuild-spec-action-thread-v27-7 -- the SECOND step to ship a
# rollback) are implemented -- YAGNI, no generic rollback registry beyond steps that
# actually ship one. `action-thread`'s `rollback` lives in its own step-lib module
# (this phase's single-file ownership), not a `_action_thread_rollback_lib.py`
# sibling the way `cap-map`'s does.
_ROLLBACK_STEPS = {"cap-map": _cap_map_rollback, "action-thread": _action_thread_step}

# Flags owned by other rebuild-spec passes -- accepted only to validate composition.
_GENERATION_FLAGS = (
    "feature_specs", "flows", "glossary", "test_cases",
    "screen_specs", "api_contracts", "overview", "api_doc", "artifact",
)

# Steps that can write `features/*/technical-spec.md` -- the only ones worth an A1
# confidence-report refresh. `screen-sot` is screen-spec-only, never added here;
# `feature-sot` (phase-10) DOES write technical-spec.md -- getting this backwards is
# silent (the A1 companions just go stale). `cap-map` (phase-07) is DELIBERATELY
# absent too -- it writes ONLY `functional-spec.md` §2, never technical-spec.md; do
# not "fix" this by adding it, that would trigger a pointless refresh of a file this
# step never touches. `action-thread` (phase-06, plans/260824-1128-rebuild-spec-
# action-thread-v27-7) DOES write technical-spec.md (the v27 -> v27.7 reshape) --
# omitting it here is exactly this set's own documented failure mode: silent, no
# error, no warning, the A1 companions just go stale. `a3-b4` carried this same
# membership until phase-09 (plans/260824-1846-rebuild-spec-action-self-sufficiency-
# v27-8) retired it -- A3/B4 left technical-spec.md's target shape in phase 08,
# leaving nothing there for it to refresh a companion over.
_TECH_SPEC_STEPS = frozenset({"audience-split", "feature-sot", "action-thread"})

# (name, prerequisite, module), in STEP_ORDER order. phase-10 inserted `feature-sot`
# between `screen-sot` and `mirror-skew`; phase-07 (capability-map plan) inserted
# `cap-map` between `feature-sot` and `mirror-skew`; phase-06 (action-thread-v27-7
# plan) inserted `action-thread` between `cap-map` and `mirror-skew` (which now
# depends on `action-thread`, not `cap-map`, directly). phase-09 (action-self-
# sufficiency-v27-8 plan) RETIRED `a3-b4`, which used to sit between
# `audience-split` and `a3-screens` -- `a3-screens`'s own prerequisite repoints
# straight to `audience-split` now.
_STEP_MODULES = (
    ("audience-split", None, _audience_split_step),
    ("a3-screens", "audience-split", _a3_screens_step),
    ("screen-sot", "a3-screens", _screen_sot_step),
    ("feature-sot", "screen-sot", _feature_sot_step),
    ("cap-map", "feature-sot", _cap_map_step),
    ("action-thread", "cap-map", _action_thread_step),
    ("mirror-skew", "action-thread", _mirror_skew_step),
)


def _build_registry() -> registry.StepRegistry:
    reg = registry.StepRegistry()
    for name, prerequisite, module in _STEP_MODULES:
        reg.register(registry.StepSpec(
            name=name, prerequisite=prerequisite,
            count_pending=module.count_pending, run=module.run,
        ))
    return reg


def _parse_features(raw: str | None) -> "frozenset[str] | None":
    if not raw:
        return None
    return frozenset(s.strip() for s in raw.split(",") if s.strip())


def _resolve_primary_lang(docs_root: Path) -> str | None:
    """Boundary read: a malformed/absent state file falls back to `None`, never raises."""
    state_path = docs_root / ".rebuild-state.json"
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    lang = data.get("primary_lang") if isinstance(data, dict) else None
    return str(lang) if lang else None


def _validate_composition(args: argparse.Namespace, docs_root: Path) -> str | None:
    """Error message (bad invocation, exit 2) or None. `--full`/`--since` handled
    separately (warn-and-ignore)."""
    for flag in _GENERATION_FLAGS:
        if getattr(args, flag, None):
            return f"--migrate is incompatible with --{flag.replace('_', '-')}"
    if args.lang:
        primary = _resolve_primary_lang(docs_root)
        if primary is None or args.lang != primary:
            return (
                f"--migrate is incompatible with --lang {args.lang!r} (a secondary "
                f"language) -- migrate operates on the primary tree only"
            )
    return None


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--docs-root", required=True)
    p.add_argument("--project-root", default=None)
    p.add_argument("--migrate", action="store_true", help="accepted for CLI-shape parity; this script is migrate-only")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--only", action="append", default=None, metavar="STEP")
    p.add_argument("--rollback", default=None, metavar="STEP")
    p.add_argument("--features", default=None, metavar="F001,F002")
    p.add_argument("--full", action="store_true")
    p.add_argument("--since", default=None)
    p.add_argument("--lang", default=None)
    for flag in _GENERATION_FLAGS:
        if flag == "artifact":
            p.add_argument("--artifact", default=None)
        else:
            p.add_argument(f"--{flag.replace('_', '-')}", action="store_true")
    args = p.parse_args(argv)

    docs_root = Path(args.docs_root).resolve()
    if not docs_root.is_dir():
        print(f"[ERROR] --docs-root is not a directory: {docs_root}", file=sys.stderr)
        return 2

    mirror_reason = _mirror_refusal_reason(docs_root)
    if mirror_reason:
        print(f"[ERROR] {mirror_reason}", file=sys.stderr)
        return 2

    project_root = _resolve_project_root_for_docs(args.project_root, docs_root)
    try:
        _assert_under(docs_root, project_root)
    except ValueError as exc:
        toplevel = _git_toplevel(docs_root) or "<none detected>"
        print(f"[ERROR] {exc} Pass --project-root <repo root>. Detected git toplevel: "
              f"{toplevel}.", file=sys.stderr)
        return 2

    # `--rollback STEP` (phase-07): a wholly separate mode, dispatched before any
    # `--migrate`/`--dry-run`/`--only` composition is even read -- rollback undoes a
    # single named step's own write, it never runs the ordered chain.
    if args.rollback is not None:
        module = _ROLLBACK_STEPS.get(args.rollback)
        if module is None:
            supported = ", ".join(sorted(_ROLLBACK_STEPS))
            print(f"[ERROR] --rollback {args.rollback!r} has no rollback implemented -- "
                  f"only {supported} does", file=sys.stderr)
            return 2
        features = _parse_features(args.features)
        result = module.rollback(docs_root, project_root, features)
        print(f"[INFO] rollback step={args.rollback} category={result.category} -- "
              f"{result.message}")
        return 1 if result.category == _ROLLBACK_FAILED else 0

    bad = _validate_composition(args, docs_root)
    if bad:
        print(f"[ERROR] {bad}", file=sys.stderr)
        return 2

    if args.full or args.since:
        print("[WARN] --full/--since are ignored under --migrate (artifact-derived "
              "pending state has no cursor to force or rebase)", file=sys.stderr)

    reg = _build_registry()
    if args.only:
        unknown = [n for n in args.only if n not in registry.STEP_ORDER]
        if unknown:
            print(f"[ERROR] unknown --only step(s) {unknown} -- valid steps: "
                  f"{', '.join(registry.STEP_ORDER)}", file=sys.stderr)
            return 2
        step_names = tuple(n for n in registry.STEP_ORDER if n in args.only)
    else:
        step_names = registry.STEP_ORDER

    features = _parse_features(args.features)

    # A1 confidence-report refresh -- best-effort, advisory, never gates exit code.
    _requests_technical_spec = bool(_TECH_SPEC_STEPS & set(step_names))

    if args.dry_run:
        for line in registry.preview(reg, step_names, docs_root, project_root, features):
            print(line)
        if _requests_technical_spec:
            pending = _confidence_refresh.count_pending(docs_root, project_root, features)
            print(f"[DRY-RUN] confidence-report pending={pending} -- would regenerate "
                  f"confidence-report_technical-spec.md (writes nothing under --dry-run)")
        return 0

    # Gate on ACTUALLY RAN (`ran`, never populated for a refused step) -- see docstring.
    ran_steps: set[str] = set()
    exit_code, tally = registry.execute(
        reg, step_names, docs_root, project_root, features, ran=ran_steps,
    )
    if _TECH_SPEC_STEPS & ran_steps:
        result = _confidence_refresh.refresh(docs_root, project_root, features)
        print(f"[INFO] confidence-report refreshed count={result.count} "
              f"(best-effort, always-regenerate, never gates)")
    print(tally.summary_line(sentinel_state="N/A (artifact-derived; no driver sentinel)"))
    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
