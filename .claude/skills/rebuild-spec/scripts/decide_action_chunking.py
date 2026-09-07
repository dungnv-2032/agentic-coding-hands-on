#!/usr/bin/env python3
"""decide_action_chunking.py — count-gated capability-chunk decision for feature-spec generation.

Replaces technical-spec-template.md's 400-line "SIZE-ADAPTIVE DRAFTING" note with a semantic,
testable gate: chunk when action count is large AND a capability axis exists to slice on.
`references/pipeline-feature-specs.md` only calls this script now — a rule written solely in a
prose reference read by an orchestrator LLM is "a rule believed to be running" (shipped 6 times).

DENOMINATOR: the action count is the DATA-ROW COUNT of the "## 2. Action Index" table in
technical-spec.md (wire-format-contract.md § "§ 2 Action Index"), row shape `| **A<n>** | ... |`.
`A0` (cross-cutting) is MANDATORY even at zero real actions, so it counts too. This is
deliberately NOT the § 3.4 "Edge cases" row count — F010 counts 28 by § 3.4 but 47 by § 2's
handler-keyed rows on the sharetribe corpus. Count ONLY the § 2 table.

CLAMPING (documented, not implemented): SKILL.md documents REBUILD_MAX_PARALLEL and siblings
(REBUILD_SHARD_MAX_PARALLEL / REBUILD_W8_MAX_PARALLEL / REBUILD_FS_BATCH_SIZE) as an
orchestrator-prose-only convention ("width = min(<sibling>, REBUILD_MAX_PARALLEL)"). Checked
2026-08-24: no scripts/*.py reads any of those env vars — the clamp lives only in the
orchestrating LLM's wave-dispatch prose (FS.1, W8, AC.1), never in code, so there is no code
precedent to mirror. The two are also not the same unit — an action-count gate vs. a subagent
concurrency width — so REBUILD_ACTION_CHUNK_THRESHOLD is NOT clamped against REBUILD_MAX_PARALLEL
here. What SHOULD be wave-chained under that cap, once this script says chunk, is the resulting
one-researcher-per-capability fan-out — the reference file/orchestrator's job, not this script's.

FAIL-OPEN: when the exact § 2 header cannot be found — file missing, section missing, or the
header text does not match the wire contract — this script fails OPEN (chunk=False, the existing
safe single-pass behavior) rather than guessing a count; forcing a chunk would also need a
trustworthy slice list the same malformed doc cannot promise. `reason` always states this
explicitly. A missing/malformed functional-spec.md needs no special case: it yields an empty
capability list, which `decide()`'s ordinary "< 2 capabilities" branch already treats as
single-pass.

Exit code: always 0 — advisory like estimate_artifact_loc.py, never halts the calling pipeline.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

DEFAULT_THRESHOLD = 15
ENV_THRESHOLD = "REBUILD_ACTION_CHUNK_THRESHOLD"

# Wire-format-contract.md § "§ 2 Action Index" — exact, byte-for-byte header row.
ACTION_INDEX_HEADER = "| # | Action (handler) | Method · Path | Codes | Writes | Detail |"

FUNC_CAP_SECTION_RE = re.compile(r"^##\s+2\.\s+Functional Capabilities\s*$")
NEXT_H2_RE = re.compile(r"^##\s+\S")
CAP_CODE_RE = re.compile(r"^CAP-\d+$")


def _read_threshold(explicit: int | None) -> tuple[int, str | None]:
    """Resolve the chunk threshold: --threshold flag > env var > default 15."""
    if explicit is not None:
        return explicit, None
    raw = os.environ.get(ENV_THRESHOLD)
    if raw is None:
        return DEFAULT_THRESHOLD, None
    try:
        value = int(raw)
        if value <= 0:
            raise ValueError("must be positive")
    except ValueError:
        return DEFAULT_THRESHOLD, (
            f"invalid {ENV_THRESHOLD}={raw!r} (must be a positive int); using default "
            f"{DEFAULT_THRESHOLD}"
        )
    return value, None


def count_action_index_rows(text: str) -> tuple[int | None, str | None]:
    """Count § 2 Action Index data rows. (count, None) normally; (None, error) only when the
    exact header (wire-format-contract.md) is missing — see module docstring's FAIL-OPEN note."""
    lines = text.splitlines()
    header_idx = None
    for i, line in enumerate(lines):
        if line.strip() == ACTION_INDEX_HEADER:
            header_idx = i
            break
    if header_idx is None:
        return None, "§ 2 Action Index header not found in technical-spec.md"
    # lines[header_idx] = header, lines[header_idx + 1] = separator row; data rows follow.
    count = 0
    for line in lines[header_idx + 2:]:
        if not line.strip().startswith("|"):
            break
        count += 1
    return count, None


def extract_capability_order(text: str) -> tuple[list[str], str | None]:
    """CAP-### codes, in document order, from functional-spec.md's § 2 Functional Capabilities
    table (the slice axis — wire-format-contract.md § 3). ([], error) when absent; callers treat
    that as "0 capabilities" — no special-casing needed, see module docstring's FAIL-OPEN note."""
    lines = text.splitlines()
    section_idx = None
    for i, line in enumerate(lines):
        if FUNC_CAP_SECTION_RE.match(line.strip()):
            section_idx = i
            break
    if section_idx is None:
        return [], "§ 2 Functional Capabilities header not found in functional-spec.md"

    table_start = None
    for i, line in enumerate(lines[section_idx + 1:], start=section_idx + 1):
        stripped = line.strip()
        if NEXT_H2_RE.match(stripped):
            return [], "§ 2 Functional Capabilities has no capability table"
        if stripped.startswith("|"):
            table_start = i
            break
    if table_start is None:
        return [], "§ 2 Functional Capabilities has no capability table"

    codes: list[str] = []
    for line in lines[table_start + 2:]:
        stripped = line.strip()
        if NEXT_H2_RE.match(stripped) or not stripped.startswith("|"):
            break
        cells = stripped.split("|")
        cell = cells[1].strip() if len(cells) > 1 else ""
        if CAP_CODE_RE.match(cell):
            codes.append(cell)
    return codes, None


def _verdict(chunk: bool, slices: list[str], reason: str) -> dict:
    return {"chunk": chunk, "slices": slices, "reason": reason}


def decide(action_count: int, capabilities: list[str], threshold: int) -> dict:
    """The predicate. Count-based, never line-based (D5/D6)."""
    if action_count < threshold:
        return _verdict(False, [], f"action count {action_count} < threshold {threshold} — single-pass")
    if len(capabilities) < 2:
        return _verdict(False, [], (
            f"action count {action_count} >= threshold {threshold} but only "
            f"{len(capabilities)} capability recognized — no slice axis to chunk on; "
            "single-pass despite exceeding the threshold"
        ))
    return _verdict(True, list(capabilities), (
        f"action count {action_count} >= threshold {threshold} and "
        f"{len(capabilities)} capabilities available — chunking by capability"
    ))


def decide_for_feature_dir(feature_dir: Path, threshold: int) -> dict:
    tech_path = feature_dir / "technical-spec.md"
    func_path = feature_dir / "functional-spec.md"

    if not tech_path.is_file():
        return _verdict(False, [], f"technical-spec.md not found under {feature_dir} — fail-open, single-pass")

    action_count, action_err = count_action_index_rows(tech_path.read_text(encoding="utf-8"))
    if action_err is not None:
        return _verdict(False, [], f"{action_err} — fail-open, single-pass")

    capabilities: list[str] = []
    if func_path.is_file():
        capabilities, _cap_err = extract_capability_order(func_path.read_text(encoding="utf-8"))

    return decide(action_count, capabilities, threshold)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Decide whether technical-spec.md generation should chunk by capability."
    )
    parser.add_argument("--feature-dir", default=None, help="Dir holding technical-spec.md + functional-spec.md")
    parser.add_argument("--actions", type=int, default=None, help="Explicit § 2 Action Index row count (testability)")
    parser.add_argument("--capabilities", type=int, default=None, help="Explicit capability count (testability)")
    parser.add_argument("--threshold", type=int, default=None, help=f"Override {ENV_THRESHOLD} (default {DEFAULT_THRESHOLD})")
    args = parser.parse_args(argv)

    threshold, threshold_warn = _read_threshold(args.threshold)
    if threshold_warn:
        print(f"[WARN] {threshold_warn}", file=sys.stderr)

    if args.feature_dir is not None:
        result = decide_for_feature_dir(Path(args.feature_dir), threshold)
    elif args.actions is not None and args.capabilities is not None:
        placeholder_slices = [f"CAP-{n:02d}" for n in range(1, args.capabilities + 1)]
        result = decide(args.actions, placeholder_slices, threshold)
    else:
        print("error: pass --feature-dir OR both --actions and --capabilities", file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
