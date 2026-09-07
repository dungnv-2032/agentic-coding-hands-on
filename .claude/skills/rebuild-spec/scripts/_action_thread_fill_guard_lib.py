#!/usr/bin/env python3
"""_action_thread_fill_guard_lib.py -- runtime anti-rewrite guard for the
action-thread researcher FILL pass (phase 04,
plans/260824-1846-rebuild-spec-action-self-sufficiency-v27-8).

Mirrors `_a3_b4_fill_guard_lib.evaluate_fill`'s shape (`GuardResult`,
`must_revert`, per-check violation lists) for one orchestrator-runbook shape
across both fill passes -- a NEW, finer-grained module, not an edit to that
one (X3: `_a3_b4_fill_guard_lib` stays alive for `a3-screens`; phase 09
rescopes it). WHY NEW: `_a3_b4_fill_guard_lib.check_scope` strips a whole
section at the next H1/H2 -- here that would put the ENTIRE `## 3. Actions` H2
in scope, defeating the guard. This module strips at RUNG-BODY / MERMAID-FENCE
/ § 4.4-PARAGRAPH granularity, so headings, § 2's table, § 1, § 5, and the
appendix H3s stay visible to byte comparison.

`check_scope` combines two guards: (1) `_skeleton(text)` walks `text` via its
OWN heading structure, folding a rung occurrence to one fixed sentinel per
label, dropping a mermaid fence inside a `### 3.N` bucket, and dropping a
`### 4.4 Shared Rules` paragraph -- everything else passes through verbatim,
so a skeleton mismatch means something outside the declared surface changed;
(2) `_changed_action_blocks` counts how many DISTINCT action blocks had rung
content change, since (1) alone cannot see that -- more than one changing at
once is phase-00's named dangerous case (an LLM rewriting the rest of a file).

`check_owner_plausibility` (reverse of `FeatureSpec.action_unclaimed`) lives in
the sibling `_action_thread_owner_plausibility_lib.py`, split out to keep this
module under the 200-line guidance (same precedent `_a3_b4_citation_target_lib.
py` set). No citation-existence check lives here: D10 (plan.md) corrects this
phase's own key insight -- `**Source:**` existence IS covered corpus-wide as of
phase 03b's fix, so a second guard-local check would be the DRY violation Job 2
warns against. `project_root` stays in the signature, unused, for call-site
parity only. Every function is a pure read; the caller owns the snapshot and
the revert-on-violation write. Stdlib only.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _action_thread_diagram_lib  # noqa: E402
import _action_thread_lib  # noqa: E402
import validate_feature_spec  # noqa: E402
from _action_thread_owner_plausibility_lib import check_owner_plausibility  # noqa: E402,F401
from _spec_parse import parse_headings_and_blocks  # noqa: E402

# Fixed sentinel per rung LABEL (never per body) -- a body growing/shrinking
# never diffs; a LABEL change (renamed or unrecognized) still does.
_RUNG_SENTINEL = "\x00RUNG:{label}\x00"


def _parse(text: str) -> tuple[list[str], list[tuple[int, str]], list[tuple[int, str]]]:
    """`(lines, headings, h2)` for `text`, computed the same way
    `validate_feature_spec.py`'s own checks compute it, so this guard's
    structural read never drifts from the validator's own."""
    lines = text.split("\n")
    headings, _ = parse_headings_and_blocks(lines)
    h2 = [(i, h) for i, h in headings if h.startswith("## ") and not h.startswith("### ")]
    return lines, headings, h2


def _rung_occurrences(lines: list[str], block: dict) -> list[tuple[str, int, int]]:
    """`(label, start, end)` (end exclusive) per rung marker line in `block`,
    via `_match_rung_line` directly (reused, per the phase, not re-derived)."""
    found: list[tuple[str, int]] = []
    for i in range(block["start"], block["end"]):
        matched = _action_thread_lib._match_rung_line(lines[i])
        if matched:
            found.append((matched[0], i))
    occurrences: list[tuple[str, int, int]] = []
    for k, (label, start) in enumerate(found):
        end = found[k + 1][1] if k + 1 < len(found) else block["end"]
        occurrences.append((label, start, end))
    return occurrences


def _skeleton(text: str) -> str:
    """`text` with every editable region folded away: a rung occurrence
    collapses to one fixed sentinel line, a mermaid fence inside a `### 3.N`
    bucket is dropped, a `### 4.4 Shared Rules` paragraph is dropped.
    Everything else is copied through verbatim. Consecutive blank-line runs
    collapse to one, applied identically on both sides of a comparison, so
    the blank line a fence insertion legitimately needs around it (markdown's
    own fencing convention) never reads as a scope violation on its own."""
    lines, headings, h2 = _parse(text)
    total = len(lines)
    drop = [False] * total
    sentinel: dict[int, str] = {}

    b_actions = validate_feature_spec._bounds(h2, "## 3. Actions", total)
    if b_actions:
        for block in _action_thread_lib.action_blocks(headings, total):
            if not (b_actions[0] <= block["heading_line"] < b_actions[1]):
                continue
            for _label, start, end in _rung_occurrences(lines, block):
                # DROP the whole rung region -- do NOT sentinel it per label.
                #
                # WHY (defect found by phase 07, fixed 2026-08-24). Sentinelling
                # per label put the SET and ORDER of a block's rung labels into
                # the immutable skeleton. But rungs are the declared EDITABLE
                # surface, and adding a rung that is genuinely absent from `pre`
                # is the sanctioned edit -- it is precisely how a fill unit
                # resolves `state_rung_missing` (95 findings, the headline work
                # of this release). With a per-label sentinel, `pre` folded to N
                # sentinels and `post` to N+1, so `_skeleton(pre) != _skeleton(
                # post)` and `check_scope` reverted the unit on that ground
                # ALONE -- regardless of `allowed_actions`, even with the block
                # correctly dispatched. The release's core workflow could never
                # have passed its own gate.
                #
                # NO PROTECTION IS LOST. Rung-level change is the OTHER arm's
                # job: `_changed_action_blocks` diffs `{block: {label: body}}`
                # and `allowed_actions` reverts any block outside the dispatched
                # set -- so adding a State rung to a block nobody dispatched is
                # still caught (regression-tested). This arm keeps doing what it
                # is actually for: headings at any level, the § 2 Action Index
                # table, § 1, § 5 and the appendix H3s stay byte-identical.
                for i in range(start, end):
                    drop[i] = True
        fences = _action_thread_diagram_lib.mermaid_fences(lines)
        for bstart, bend in _action_thread_diagram_lib.capability_buckets(headings, b_actions):
            for f in fences:
                if f["start"] >= bstart and f["end"] <= bend:
                    for i in range(f["start"], f["end"]):
                        drop[i] = True

    b_shared = validate_feature_spec._bounds(h2, "## 4. Shared Foundation", total)
    if b_shared:
        b_44 = validate_feature_spec._bounds_at(
            headings, "### ", "### 4.4 Shared Rules", b_shared[1])
        if b_44:
            for p_start, p_end in validate_feature_spec._paragraphs(lines, b_44[0], b_44[1]):
                for i in range(p_start, p_end):
                    drop[i] = True

    out: list[str] = []
    for i, ln in enumerate(lines):
        if drop[i]:
            continue
        ln = sentinel.get(i, ln)
        if not ln.strip() and out and not out[-1].strip():
            continue
        out.append(ln)
    return "\n".join(out)


def _rung_map(lines: list[str], headings: list, h2: list) -> dict[str, dict[str, str]]:
    """`{action_ids_joined: {rung_label: rendered_body}}` per block in
    `## 3. Actions`."""
    total = len(lines)
    b_actions = validate_feature_spec._bounds(h2, "## 3. Actions", total)
    out: dict[str, dict[str, str]] = {}
    if not b_actions:
        return out
    for block in _action_thread_lib.action_blocks(headings, total):
        if not (b_actions[0] <= block["heading_line"] < b_actions[1]):
            continue
        key = "/".join(block["ids"]) or f"__line{block['heading_line']}"
        out[key] = dict(_action_thread_lib.rungs(lines, block))
    return out


def _changed_action_blocks(pre: str, post: str) -> list[str]:
    """Which `#### A<n>` block keys have DIFFERENT rung content between `pre`
    and `post` -- bounds HOW MANY distinct blocks one fill unit may touch."""
    pre_lines, pre_headings, pre_h2 = _parse(pre)
    post_lines, post_headings, post_h2 = _parse(post)
    pre_map = _rung_map(pre_lines, pre_headings, pre_h2)
    post_map = _rung_map(post_lines, post_headings, post_h2)
    keys = set(pre_map) | set(post_map)
    return sorted(k for k in keys if pre_map.get(k) != post_map.get(k))


def check_scope(
    pre: str, post: str, allowed_actions: "frozenset[str] | None" = None
) -> list[str]:
    """Byte equality outside the declared editable surface, plus -- when the
    caller declares one -- a bound on WHICH action blocks' rungs may change.

    `allowed_actions` holds `_rung_map` keys (`"/".join(block["ids"])`, e.g.
    `"A3"` or `"A7/A8"`) the unit was DISPATCHED to fill. Any block changing
    outside that set is the dangerous case phase-00 names: an LLM asked to
    resolve one rung that also rewrites the rest of a 28KB file.

    `None` (the default) means the caller declared no scope, so no per-action
    bound applies -- `_skeleton` equality still holds the line on every heading,
    the § 2 Action Index table, § 1, § 5 and the appendix H3s.

    WHY A SET AND NOT A COUNT (integration seam, settled 2026-08-24). This began
    as `len(changed) > 1 -> revert`, which silently assumed one unit == one
    ACTION. It is not: `references/pipeline-migrate.md:56` fixes the precedent as
    "One researcher unit = ONE feature", and phase 07's requirement 2 clones it
    verbatim ("unit = ONE feature dir"). Under per-feature dispatch a feature
    with pending rungs in four actions changes four blocks on a perfectly honest
    fill, so a count bound reverts every real wave and the pass can never
    complete -- phase 04's own High/High "guard too strict" risk. Note the
    phase's `pre == post -> zero violations` check was structurally blind to
    this: zero blocks change trivially.

    A set is also STRICTLY STRONGER than the count it replaces: it catches
    "touched an action nobody asked about" at any cardinality, including the
    one-for-one swap (fill A3, quietly rewrite A7) that `len(changed) > 1` let
    through. It needs no firing logic of its own, so D7's single-source rule is
    untouched."""
    violations: list[str] = []
    if _skeleton(pre) != _skeleton(post):
        violations.append(
            "content outside the declared editable surface changed -- headings, "
            "the § 2 Action Index table, § 1, § 5, and the appendix H3s must "
            "stay byte-identical"
        )
    changed = _changed_action_blocks(pre, post)
    if allowed_actions is not None:
        stray = sorted(k for k in changed if k not in allowed_actions)
        if stray:
            violations.append(
                f"rung content changed in action block(s) the unit was not "
                f"dispatched to fill ({', '.join(stray)}); dispatched scope was "
                f"({', '.join(sorted(allowed_actions)) or 'none'})"
            )
    return violations


@dataclass(frozen=True)
class GuardResult:
    """One fill unit's guard verdict -- mirrors `_a3_b4_fill_guard_lib.
    GuardResult`'s shape. Both fields here are unconditional reverts."""

    scope: list[str] = field(default_factory=list)
    owner_plausibility: list[str] = field(default_factory=list)

    @property
    def must_revert(self) -> bool:
        return bool(self.scope or self.owner_plausibility)

    @property
    def all_violations(self) -> list[str]:
        return self.scope + self.owner_plausibility


def evaluate_fill(
    pre: str,
    post: str,
    project_root: Path,
    allowed_actions: "frozenset[str] | None" = None,
) -> GuardResult:
    """Run every check the wave gate needs after one fill unit completes.
    `project_root` is accepted, unused -- see the module docstring (D10).

    `allowed_actions` is the set of `_rung_map` keys this unit was dispatched to
    fill; omit it (or pass `None`) to skip the per-action bound. The 3-argument
    call shape a3-b4's runbook uses stays valid, so the orchestrator runbook is
    still ONE shape. Phase 07's wave gate MUST pass the set it dispatched --
    otherwise the "did not touch an action nobody asked about" protection is
    declared but never armed, which is this repo's own dead-gate family."""
    lines, _headings, h2 = _parse(post)
    b_idx = validate_feature_spec._bounds(h2, "## 2. Action Index", len(lines))
    rows = _action_thread_lib.parse_action_index(lines, b_idx)
    return GuardResult(
        scope=check_scope(pre, post, allowed_actions),
        owner_plausibility=check_owner_plausibility(post, rows),
    )
