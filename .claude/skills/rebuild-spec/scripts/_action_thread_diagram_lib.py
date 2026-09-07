"""Diagram-contract parsing for the action-thread reshape (D2/D4). Phase 03 of
plans/260824-1128-rebuild-spec-action-thread-v27-7 (§ 8.5, § 10.2 Đ3).

`validate_feature_spec.py` wires 3 diagram checks (`FeatureSpec.diagram_*`) plus 2
rule-bin checks against what this module parses/computes. Mirrors phase 02's split:
the parsing lives HERE exactly once, the wiring file never re-derives it.

Fence extraction reuses `_id_schemes_lib.segment_text` — the ONLY fence classifier
in this codebase (it already tells a ```mermaid``` fence apart from any other
fenced code block) — rather than writing a second fence parser. NOTE for the
handback: the phase file names this function `iter_regions()`; no such name exists
anywhere in the codebase (grepped clean). The real, and only, fence classifier is
`_id_schemes_lib.segment_text`, used the same way `validate_id_contiguity.py` and
`renumber_artifact_ids.py` already use it. Deviation reported, not silently
patched around.
"""
from __future__ import annotations

import re

from _id_schemes_lib import segment_text
from validate_source_citations import CITATION_RE

# Arrow line / `alt` block-opener heuristics — fixed by the phase spec, not tuned.
# Heuristic on purpose: a `Note over` line or a wrapped arrow can miscount, which is
# exactly why `diagram_over_cap` (the only check that uses these) stays a WARNING,
# never critical (a miscount must never block a build).
_ARROW_RE = re.compile(r"-?->>?|-\.->")
_ALT_RE = re.compile(r"^\s*alt\b")

# `path:line`-in-fence scan. DERIVED from `CITATION_RE`, not hand-copied: the two
# regexes must never drift apart (the phase file: "reuse the citation regex ... a
# single change site is the point"). `CITATION_RE` requires a `**Source:**` prefix
# that never occurs inside a mermaid fence, so this strips that prefix off the
# COMPILED pattern's own source string and recompiles the bare `path:line` suffix —
# if `CITATION_RE`'s suffix shape ever changes, this changes with it; it is not a
# second regex someone edited once and left to rot.
_CITATION_PREFIX = r"\*\*Source:\*\*\s+"
assert CITATION_RE.pattern.startswith(_CITATION_PREFIX), (
    "CITATION_RE's shape changed — _action_thread_diagram_lib derives its "
    "file:line-in-fence regex from it and must be re-checked"
)
FILE_LINE_RE = re.compile(CITATION_RE.pattern[len(_CITATION_PREFIX):])

# D2's background/no-FE handler-cell suffix (wire-format-contract.md § 2 column
# rules) — the second of the two threshold-(b)/(c) signals alongside `method ==
# "queue"`. Only the English wire-format suffix is matched; a translated document's
# own suffix text is out of scope for this phase (the `method == "queue"` signal
# already catches every queue-driven action regardless of language, which is why
# the corpus's own background action, `ExportListingsJob#perform`, is caught by
# BOTH signals independently).
_BACKGROUND_SUFFIX = "*(background, no FE)*"

# Fill-pending degradation window (D4-diagram, plans/260824-1128-rebuild-spec-
# action-thread-v27-7 follow-up: "add a degradation window so a legitimately
# mid-pipeline file is not reported as critical"). `diagram_required_missing`
# fires the moment a file crosses the diagram threshold, but a freshly composed
# `action-thread` file cannot possibly carry a diagram yet — diagrams need
# judgment and are authored in the SAME researcher fill pass that resolves rule
# ownership (`compose_action_thread`, `_feature_sot_technical_lib.py`, is
# mechanical-only and never invents one).
#
# SAME tag as `_doc_migration_action_thread_step_lib._UNVERIFIED_MARKER` (the
# rollback sidecar's own fill-pending signal, and the literal
# `ThreadComposeResult.needs_llm_fill` is computed from — see that module's
# docstring). Deliberately duplicated as a literal, NOT imported: importing
# `_doc_migration_action_thread_step_lib` here would invert the dependency
# direction — a read-only diagram-parsing lib pulling in a mutating migrate-
# step registry module's json/atomic-write machinery — the same reasoning that
# keeps `_TECH_PRE_THREAD_SENTINEL` a single `_spec_constants` import rather
# than a cross-layer one. Both sites cite wire-format-contract.md § 4.4 as the
# shared source of truth for the tag's shape.
#
# Measured honest on the real 43-feature corpus (scratch-migrated copy, not the
# original): every one of the 28 features that fires `diagram_required_missing`
# today also carries >=1 `[UNVERIFIED]` marker — 0 mismatches. `needs_llm_fill`
# itself cannot be read here (it is a `compose_action_thread` return value, gone
# the moment the migrate process exits); this marker is the artifact-derived
# (AD-1) stand-in that survives on disk for the validator to read later, same
# convention as `_TECH_PRE_THREAD_SENTINEL`.
#
# NOT assumed total coverage: per preflight C11, a feature with zero DEC blocks
# and every BR `Applies to:` resolved may legitimately carry zero markers even
# before a researcher ever looks at it. Such a file is treated as already past
# the window — correctly: it has nothing left for a fill pass to resolve, so a
# real diagram gap in it is a real defect, not a mid-pipeline artifact.
_UNVERIFIED_MARKER = "[UNVERIFIED]"


def is_fill_pending(text: str) -> bool:
    """True while *text* (a whole `technical-spec.md`, action-thread shaped)
    still carries the fill-pending marker — the researcher pass that authors
    diagrams has not resolved every rule yet. See the module-level comment
    above `_UNVERIFIED_MARKER` for the corpus evidence and why this is the
    honest signal rather than an invented one."""
    return _UNVERIFIED_MARKER in text


def mermaid_fences(lines: list[str]) -> list[dict]:
    """Every ```mermaid``` fence in *lines*.

    Each entry: `{start, end, body}`. `start`/`end` are 0-indexed line bounds
    (end exclusive) covering the WHOLE fence including its delimiter lines —
    matching every other `_bounds`-shaped tuple in this codebase, so a caller can
    directly test fence/bucket overlap with plain integer comparison. `body` is
    the fence's content lines with the two delimiter lines stripped; nothing
    downstream (arrow/alt counting, file:line scanning) needs them.
    """
    text = "\n".join(lines) + "\n"
    fences: list[dict] = []
    line_no = 0
    for kind, content in segment_text(text):
        content_lines = content.splitlines()
        n = len(content_lines)
        if kind == "mermaid":
            fences.append({
                "start": line_no,
                "end": line_no + n,
                "body": content_lines[1:-1] if n >= 2 else [],
            })
        line_no += n
    return fences


def capability_buckets(headings: list[tuple[int, str]], bounds: tuple[int, int]) -> list[tuple[int, int]]:
    """`[(start, end), ...]` for every `### ` heading (a `§ 3.<n> CAP-...`
    capability bucket) inside `bounds` (§ 3 Actions' own bounds). Heading-text
    agnostic — bucket titles vary per capability — unlike `_bounds`/`_bounds_at`
    which match an exact heading string.

    Exists because the wire-format contract lets ONE diagram sit at the bucket
    level and cover every handler under it (§ 3.3's A5/A6/A9 in the B-v sample:
    the fence trails the `### 3.3` heading, BEFORE any of the three actions' own
    `#### ` headings — so a fence-presence check scoped to a single action's own
    H4 block would never see it). `diagram_required_missing` checks bucket scope,
    not block scope, for exactly this reason.
    """
    start, end = bounds
    h3 = sorted(idx for idx, h in headings if h.startswith("### ") and start <= idx < end)
    return [(idx, h3[i + 1] if i + 1 < len(h3) else end) for i, idx in enumerate(h3)]


def count_arrows_and_alts(body: list[str]) -> tuple[int, int]:
    """`(arrow_line_count, alt_line_count)` inside one fence's body — the raw
    inputs `diagram_over_cap` compares against its 12/2 caps."""
    arrows = sum(1 for ln in body if _ARROW_RE.search(ln))
    alts = sum(1 for ln in body if _ALT_RE.match(ln))
    return arrows, alts


def file_line_tokens(body: list[str]) -> list[str]:
    """Every `path:line`-shaped token found inside one fence's body — the shape
    rung rule 5 (wire-format-contract.md) forbids inside a diagram: rungs carry
    facts (including `file:line`), diagrams carry order and branching only."""
    return [m.group(0) for ln in body for m in FILE_LINE_RE.finditer(ln)]


def is_over_threshold(row: dict) -> bool:
    """True when a § 2 Action Index row (as `_action_thread_lib.parse_action_index`
    returns it) crosses the diagram-required threshold: writes >=2 tables, OR is
    background/async (`method == "queue"`, or the handler cell carries the
    `*(background, no FE)*` suffix).

    Criterion (a) `>=2 BR/DEC per action` is DELIBERATELY not implemented — the
    pre-flight measured it at 4.4% on the real corpus purely because the
    action<->rule binding this phase-set builds did not exist yet at measurement
    time; phase 11 re-measures it against the real binding and decides whether it
    belongs at all. Building it in now would be gating on a number that cannot
    yet mean anything.
    """
    if len(row.get("tables") or []) >= 2:
        return True
    method = (row.get("method") or "").strip().lower()
    if method == "queue":
        return True
    return _BACKGROUND_SUFFIX in (row.get("key") or "")
