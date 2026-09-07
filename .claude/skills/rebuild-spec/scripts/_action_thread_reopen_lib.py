#!/usr/bin/env python3
"""_action_thread_reopen_lib.py -- the generalized reopen predicate (C1, D7/F1),
plans/260824-1846-rebuild-spec-action-self-sufficiency-v27-8, phase 02.

THE BUG THIS CLOSES. `_doc_migration_action_thread_step_lib.py`'s pending predicate
only ever asked two questions of a `technical-spec.md`: is it still the OLD
(layer-first) shape, or does it carry an `[UNVERIFIED]` marker? A feature that
finished the 27.7.0 fill pass -- already `## 2. Action Index`-shaped, zero
`[UNVERIFIED]` markers -- answered NO to both, so `--migrate --only action-thread`
reported it as nothing pending FOREVER, even after a brand-new detector
(`FeatureSpec.state_rung_missing`, phase 01) started firing on it. New warnings, no
remediation path, through the flagship one-command feature.

THE INVOCATION CONTRACT -- MANDATED VERBATIM (plan.md D7, phase-02.md requirement
5), not left to this module to invent: `needs_reopen(feature_dir, root)` calls
`validate_feature_spec._check_feature_dir(feature_dir, root)` and filters the
returned issues by `rule_id in REOPEN_RULE_IDS`. It NEVER re-implements, copies, or
approximates a firing predicate. Registering a detector = adding its rule_id to
`REOPEN_RULE_IDS` below, and NOTHING else -- no edit to this module's functions, and
no edit to `_doc_migration_action_thread_step_lib.py`'s call sites.

WHY MANDATED RATHER THAN LEFT OPEN. Checks in `validate_feature_spec.py` are
batched, multi-rule_id functions (`_check_action_thread`, `_check_rule_bins_and_
diagrams` each emit 4-5 rule_ids from ONE call) and there is no per-rule
`would_fire(text) -> bool` anywhere in the tree. Under time pressure the tempting
move is to duplicate the firing logic here -- and then detector logic forks from
firing logic silently, the exact split-brain this plan's own D7 exists to forbid.
Consuming `_check_feature_dir`'s own output makes that divergence structurally
impossible rather than merely discouraged. The import direction is one-directional
(this module imports the validator; the validator imports no migrate module), so
there is no circular-import risk.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import validate_feature_spec  # noqa: E402

# Rule_ids whose firing means "this feature dir's action-thread reshape needs
# another pass". Registering a NEW detector (phase 08's "carries A3 or B4") is
# exactly one line appended here -- see the module docstring for why nothing
# else may change. Phase 04 registers its four: `action_ref_unglossed` (phase
# 03 shipped the detector but ran parallel to phase 02, so could not register
# itself), `diagram_required_missing`, `rule_bin_misplaced`,
# `crosscutting_unlabelled` (all three phase 03). Phase 08 registers the sixth:
# `retired_section_present` -- the deletion-direction twin of C1. Its firing
# drives `compose_action_thread`'s one-shot A3/B4 strip on an already-shaped
# file the same way every other detector here drives a researcher fill pass.
REOPEN_RULE_IDS: tuple[str, ...] = (
    "FeatureSpec.state_rung_missing",
    "FeatureSpec.action_ref_unglossed",
    "FeatureSpec.diagram_required_missing",
    "FeatureSpec.rule_bin_misplaced",
    "FeatureSpec.crosscutting_unlabelled",
    "FeatureSpec.retired_section_present",
)


def firing_reopen_rule_ids(feature_dir: Path, root: Path) -> frozenset[str]:
    """The subset of `REOPEN_RULE_IDS` currently firing on `feature_dir`, computed
    EXCLUSIVELY from `validate_feature_spec._check_feature_dir`'s own issue list --
    see module docstring (D7/F1). `root` is threaded straight through to the
    validator call; it is used there only to relativize an issue's reported
    location and never affects which rule_ids fire."""
    issues = validate_feature_spec._check_feature_dir(feature_dir, root)
    return frozenset(
        issue["rule_id"] for issue in issues if issue.get("rule_id") in REOPEN_RULE_IDS
    )


def needs_reopen(feature_dir: Path, root: Path) -> bool:
    """True when ANY registered detector (`REOPEN_RULE_IDS`) currently fires on
    `feature_dir`. Path-based, not text-based (F1): a real reshape may need to
    consult more than the one `technical-spec.md` file the old text-only predicate
    read (the validator itself reads the functional-spec.md twin too), so this
    takes the feature directory rather than a pre-read string -- one shape, never
    two, across every call site in `_doc_migration_action_thread_step_lib.py`."""
    return bool(firing_reopen_rule_ids(feature_dir, root))
