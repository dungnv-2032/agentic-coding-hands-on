#!/usr/bin/env python3
"""_action_thread_owner_plausibility_lib.py -- the missing reverse of
`FeatureSpec.action_unclaimed` (phase 04,
plans/260824-1846-rebuild-spec-action-self-sufficiency-v27-8).

Sibling of `_action_thread_fill_guard_lib.py`, split out to keep that module
under the repo's 200-line guidance -- same precedent
`_a3_b4_citation_target_lib.py` set when it was split from
`_a3_b4_fill_guard_lib.py` for the identical reason.

`action_unclaimed` already proves every code DECLARED in § 3/§ 4 is CLAIMED by
some § 2 row. Nothing in `validate_feature_spec.py` proves the reverse: that
every action ID a fill unit WRITES into a `Used in:` list actually NAMES a row
that exists. Grepped for an existing claimed-ID-exists check before writing
this (phase report records the result) -- none exists, so this is net-new, not
a duplicate.

Resolving an `[UNVERIFIED]` rule owner INLINE (Bin 1, straight into an
existing action's own Rule rung) needs no check here: it is physically placed
inside an already-existing `#### A<n>` heading, whose id already exists in §
2 by construction, since headings are outside `_action_thread_fill_guard_lib`'s
declared editable surface. Only the `Used in:` list shape (Bin 2/3) can name an
ID that does not exist.

No filesystem access, so no traversal surface: this only ever compares strings
already parsed out of the post-fill text and the § 2 Action Index rows
`_action_thread_lib.parse_action_index` returns. Stdlib only.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import validate_feature_spec  # noqa: E402


def check_owner_plausibility(post: str, action_index_rows: list[dict]) -> list[str]:
    """Every action ID a fill unit writes into a `Used in:` list must name a
    row that exists in `action_index_rows` (this feature's own § 2 Action
    Index). Reuses `validate_feature_spec._USED_IN_RE`/`_ACTION_ID_IN_TEXT_RE`
    (the same regexes `FeatureSpec.rule_bin_misplaced` already scans with) so
    this check can never disagree with the validator about what a `Used in:`
    marker or an action-id token looks like."""
    known = {r["id"] for r in action_index_rows}
    violations: list[str] = []
    for i, ln in enumerate(post.split("\n")):
        m = validate_feature_spec._USED_IN_RE.search(ln)
        if not m:
            continue
        for action_id in validate_feature_spec._ACTION_ID_IN_TEXT_RE.findall(m.group(1)):
            if action_id not in known:
                violations.append(
                    f"line {i + 1}: 'Used in:' names {action_id!r}, which is not "
                    "a row in this feature's own § 2 Action Index"
                )
    return violations
