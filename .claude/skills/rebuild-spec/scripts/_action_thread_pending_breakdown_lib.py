#!/usr/bin/env python3
"""_action_thread_pending_breakdown_lib.py -- the structured pending breakdown for
the action-thread auto fill-pass (phase 07,
plans/260824-1846-rebuild-spec-action-self-sufficiency-v27-8).

WHAT THIS ANSWERS. `_doc_migration_action_thread_step_lib.run()` already knows a
feature dir is pending (`_is_pending`) but not WHY, at the granularity an operator
or an orchestrator dispatch loop needs: which of the 5 registered detectors
(`_action_thread_reopen_lib.REOPEN_RULE_IDS`) fire, how many times, and which
`#### A<n>` action blocks the eventual fill unit is actually allowed to touch.
Sidecar I/O (reading/writing the JSON file, preserving the orchestrator's own
`gated` bookkeeping) stays in the step lib, which already owns every other sidecar
write -- this module is a pure builder, no filesystem writes of its own.

REAL DETECTORS, NEVER GREP (requirement 2). `build_breakdown` calls
`validate_feature_spec._check_feature_dir` -- the SAME function
`_action_thread_reopen_lib.firing_reopen_rule_ids` already calls (D7: one firing
predicate, never a second one re-derived here) -- and counts its own issue list by
`rule_id`. The diagram count in particular is NOT an `[UNVERIFIED]`-marker proxy: it
comes from `_check_rule_bins_and_diagrams`, which calls
`_action_thread_diagram_lib.is_over_threshold`/`mermaid_fences`/`capability_buckets`
directly -- a feature can carry a missing-diagram finding with ZERO `[UNVERIFIED]`
markers anywhere in it (see `test_action_thread_pending_breakdown.py`'s
`test_diagram_count_is_independent_of_the_unverified_proxy`).

THE `[UNVERIFIED]` TAG IS NOT A RULE_ID (requirement 6 / C1's generalization). It is
the composer's own fill-pending signal (`_feature_sot_technical_lib.
build_a0_writeup`), counted by the shared TAG per C14's lesson (both the "carried
from **Applies to:**" and "no resolvable owner" sentences share this one tag --
counting either sentence alone silently zeroes the count on the other shape's
features). `rule_id_counts`'s key set is `frozenset(REOPEN_RULE_IDS)` BY
CONSTRUCTION -- imported, never a second hand-copied list -- so it is structurally
impossible for the breakdown to count a rule_id the reopen registry does not know
about, or to omit one the registry does. Every registered rule_id is present even
at count 0, so a caller can always tell "checked, found zero" from "never checked".

`dispatched_action_ids` -- THE D13 DISPATCHED SET, DERIVED HERE, NEVER INVENTED
TWICE. Phase 04 rebuilt `evaluate_fill`'s per-action bound as a SET the wave gate
must pass explicitly (`allowed_actions`) rather than a bare count, precisely so a
feature with pending rungs in several actions does not get every honest wave
reverted. This function computes that set the ONLY structurally sound way: every
firing issue's own reported line number is mapped back to its enclosing `#### A<n>`
block via `_action_thread_lib.action_blocks` -- the SAME block parse
`_check_action_thread`/`_check_rule_bins_and_diagrams` themselves walk -- never by
parsing an issue's free-text message. A `[UNVERIFIED]` marker always lives inside §
4.4 Bin 3's `A0` entry (`build_a0_writeup` never places one anywhere else), so its
presence structurally implies `"A0"` is dispatched too -- not inferred, a fact about
where the composer places that text.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _action_thread_lib  # noqa: E402
import validate_feature_spec  # noqa: E402
from _action_thread_reopen_lib import REOPEN_RULE_IDS  # noqa: E402
from _spec_parse import parse_headings_and_blocks  # noqa: E402

_UNVERIFIED_MARKER = "[UNVERIFIED]"


def _read_text(path: Path) -> str:
    """`""` on anything unreadable -- a missing/unreadable technical-spec.md has
    nothing pending to report, never a crash."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def build_breakdown(feature_dir: Path, root: Path) -> dict:
    """`{"unverified_tag_count": int, "rule_id_counts": {rule_id: int, ...}}` for
    one feature dir. `rule_id_counts` always carries exactly `REOPEN_RULE_IDS`'s
    keys (see module docstring) -- a rule_id present at count 0 means "checked,
    nothing firing", never "not checked"."""
    text = _read_text(feature_dir / "technical-spec.md")
    issues = validate_feature_spec._check_feature_dir(feature_dir, root)
    counts = Counter(
        issue["rule_id"] for issue in issues if issue.get("rule_id") in REOPEN_RULE_IDS
    )
    return {
        "unverified_tag_count": text.count(_UNVERIFIED_MARKER),
        "rule_id_counts": {rid: counts.get(rid, 0) for rid in REOPEN_RULE_IDS},
    }


def dispatched_action_ids(feature_dir: Path, root: Path) -> "frozenset[str]":
    """The `_rung_map`-shaped keys (`"/".join(block['ids'])`, e.g. `"A3"` or
    `"A7/A8"`) a fill unit dispatched to THIS feature dir may legitimately touch --
    `evaluate_fill`'s `allowed_actions` bound (D13). See module docstring for why
    this is derived from each firing issue's own reported line, not its message
    text, and why a `[UNVERIFIED]` marker always contributes `"A0"`."""
    text = _read_text(feature_dir / "technical-spec.md")
    if not text:
        return frozenset()
    lines = text.split("\n")
    headings, _ = parse_headings_and_blocks(lines)
    blocks = _action_thread_lib.action_blocks(headings, len(lines))
    issues = validate_feature_spec._check_feature_dir(feature_dir, root)
    dispatched: set[str] = set()
    for issue in issues:
        if issue.get("rule_id") not in REOPEN_RULE_IDS:
            continue
        line = issue.get("location", {}).get("line")
        if not isinstance(line, int):
            continue
        line0 = line - 1
        for block in blocks:
            if block["heading_line"] <= line0 < block["end"]:
                dispatched.add("/".join(block["ids"]) or f"__line{block['heading_line']}")
                break
    if _UNVERIFIED_MARKER in text:
        dispatched.add("A0")
    return frozenset(dispatched)


def _short_rule_id(rid: str) -> str:
    return rid.rsplit(".", 1)[-1]


def summarize_breakdown(feature_name: str, breakdown: dict) -> str:
    """One compact `feature=<name> ...` line -- every nonzero count, `unverified`
    first, short rule_id names (the part after `FeatureSpec.`)."""
    parts = []
    if breakdown["unverified_tag_count"]:
        parts.append(f"unverified={breakdown['unverified_tag_count']}")
    for rid in REOPEN_RULE_IDS:
        n = breakdown["rule_id_counts"].get(rid, 0)
        if n:
            parts.append(f"{_short_rule_id(rid)}={n}")
    body = " ".join(parts) if parts else "nothing pending"
    return f"feature={feature_name} {body}"


def summarize_breakdowns(pairs: "list[tuple[str, dict]]") -> str:
    """The full `[HANDOFF]` detail suffix across every feature dir this run found
    still pending: aggregate totals first, then one compact line per feature.
    `""` on empty input (never called when nothing is pending)."""
    if not pairs:
        return ""
    totals: "Counter[str]" = Counter()
    for _, breakdown in pairs:
        totals["unverified"] += breakdown["unverified_tag_count"]
        for rid in REOPEN_RULE_IDS:
            totals[_short_rule_id(rid)] += breakdown["rule_id_counts"].get(rid, 0)
    total_str = " ".join(f"{k}={v}" for k, v in totals.items() if v) or "nothing pending"
    per_feature = "; ".join(summarize_breakdown(name, bd) for name, bd in pairs)
    return f"pending breakdown totals: {total_str} -- {per_feature}"
