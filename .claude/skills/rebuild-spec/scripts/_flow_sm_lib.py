#!/usr/bin/env python3
"""Scan feature technical-specs for entity-kind SM-### state machines.

Used by validate_process_flow.py (B3 — SM/FLOW DRY cross-ref enforcement).
A FLOW### that re-documents an entity state machine already captured as an
SM-### in a feature spec MUST cross-reference it instead of duplicating the
transition table. This module surfaces the candidate SMs for that check.

v27.0.0 (Phase 04): SM heading detection is repointed at `_spec_block_lib.find_blocks`
(the single-sourced BR/SM/ALG/INT block parser) instead of a locally re-typed regex.
The old local `_SM_HEADING_RE` matched only the RETIRED anchored form
(`### SM-001_Name` / `#### SM-001_Name`) and silently matched ZERO blocks against the
canonical v27.0.0 trailing-tag heading (`### {plain sentence} (SM-001)`) — a pattern
matching nothing reports nothing, so this validator's SM/FLOW DRY cross-ref (B3) would
have gone quietly dark on any migrated technical-spec.md. `find_blocks` also skips
fenced code blocks (an improvement over the old full-text scan — a `### ... (SM-001)`
line inside a mermaid/code fence is no longer mistakenly picked up).

Stdlib only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _spec_block_lib import find_blocks  # noqa: E402

_KIND_RE = re.compile(r"\*\*kind:\*\*\s*(\w+)", re.IGNORECASE)
_STATES_RE = re.compile(r"\*\*States:\*\*\s*(.+)")


def _parse_states(block: str) -> set[str]:
    m = _STATES_RE.search(block)
    if not m:
        return set()
    states: set[str] = set()
    for tok in re.split(r"[,→]", m.group(1)):
        s = tok.strip().strip("`").strip()
        if s:
            states.add(s)
    return states


def scan_entity_state_machines(features_dir: Path) -> list[dict]:
    """Return entity-kind SMs as [{code, feature, states:set[str]}].

    Only SMs with `**kind:** entity` and >=2 declared states are returned —
    UI/polling SMs are irrelevant to the FLOW### DRY boundary.
    """
    results: list[dict] = []
    if not features_dir.is_dir():
        return results
    for tspec in sorted(features_dir.glob("*/technical-spec.md")):
        text = tspec.read_text(encoding="utf-8", errors="replace")
        feature = tspec.parent.name
        lines = text.splitlines()
        for b in find_blocks(text):
            if b["prefix"] != "SM":
                continue
            block = "\n".join(lines[b["heading_line"] + 1 : b["block_end"]])
            kind_m = _KIND_RE.search(block)
            if not kind_m or kind_m.group(1).strip().lower() != "entity":
                continue
            states = _parse_states(block)
            if len(states) >= 2:
                results.append({"code": b["code"], "feature": feature, "states": states})
    return results
