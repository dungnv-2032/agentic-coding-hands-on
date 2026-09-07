"""`compose_functional_sot` -- the SOLE source of the SOT target section order for
functional-spec.md (phase-10, plans/260818-1332-rebuild-spec-human-readable-sot).
Sibling of `_screen_sot_compose_lib.compose_screen_sot`. content-preservation-map.md
§ B (F-01..F-08), target-shape-spec.md § 2 (normative).

The old (v27.0, `audience-split`-produced) functional-spec.md is a flat 10-section
document, numbered 1-10 (`_audience_split_compose_a_lib.render_functional_spec`'s own
`numbered` list is the producer-side proof of this exact shape). This reshapes it to
the 13-section SOT order by a pure heading renumber (F-03) plus 3 net-new scaffolded
sections (F-04/F-05/F-06) and one field relabel inside `## 1. Overview` (F-01/F-02).
Nothing here reshapes technical-spec.md -- that is
`_feature_sot_technical_lib.compose_technical_sot`'s job, which reads THIS module's
output as its twin.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _audience_split_md_sections_lib import split_sections  # noqa: E402
from _md_scan_lib import iter_lines_with_fence  # noqa: E402
from _spec_constants import (  # noqa: E402
    FUNC_CAPABILITIES_SKELETON, FUNC_DEPS_SKELETON, FUNC_RISKS_SKELETON, REQUIRED_H2_FUNC,
)

# F-03: the OLD (v27.0) flat 1-10 numbering -- title text after the number is
# UNCHANGED by the renumber (target-shape-spec.md § 2). Verified against the real
# producer (`_audience_split_compose_a_lib.render_functional_spec`'s `numbered` list)
# and against the real corpus (st-post/docs/features/F001_Auth/functional-spec.md).
_OLD_TITLES = {
    1: "Overview", 2: "Open Decisions", 3: "Requirements", 4: "Business Rules",
    5: "Screens", 6: "User Stories", 7: "Scenarios", 8: "Edge Cases",
    9: "Edge Behaviours to Verify", 10: "Configuration",
}
_OLD_ORDER = [f"## {n}. {t}" for n, t in _OLD_TITLES.items()]
# old N -> new N -- target-shape-spec.md § 2's own renumber map, load-bearing.
_RENUMBER = {1: 1, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9, 9: 10, 10: 13}

_SECTION_REF_RE = re.compile(r"§\s*(\d+)\b")
_LABEL_LINE_RE = re.compile(r"^\*\*([A-Za-z][A-Za-z /-]*):\*\*\s*(.*)$")
_LABEL_RENAME = {"Goals": "Scope", "Non-Goals": "Non-Scope"}

# Sentinel unique to SOT output -- absent from every old (v27.0) functional-spec.md,
# since "## 2." there is "Open Decisions", never "Functional Capabilities".
_SOT_SENTINEL = "## 2. Functional Capabilities"

_SCAFFOLD_SKELETONS = {
    "## 2. Functional Capabilities": FUNC_CAPABILITIES_SKELETON.strip(),
    "## 11. Risks & Known Issues": FUNC_RISKS_SKELETON.strip(),
    "## 12. Dependencies": FUNC_DEPS_SKELETON.strip(),
}


@dataclass(frozen=True)
class ComposeResult:
    text: str
    needs_llm_fill: bool
    moved: int
    scaffolded: int


def _has_scaffold(text: str) -> bool:
    _, h2 = split_sections(text, 2)
    return any(h2.get(name, "").strip() == body for name, body in _SCAFFOLD_SKELETONS.items())


def _rewrite_section_refs(text: str) -> str:
    """F-03's in-body half: `§ N` cross-references rewritten by the SAME renumber map
    that moves the headings -- fence-aware, so a pseudocode fence's own literal `§`
    (if any) is never touched. A number outside the old 1-10 range is left alone."""
    def _sub_line(line: str) -> str:
        def _sub(m: "re.Match[str]") -> str:
            new_n = _RENUMBER.get(int(m.group(1)))
            return f"§ {new_n}" if new_n is not None else m.group(0)
        return _SECTION_REF_RE.sub(_sub, line)
    return "\n".join(
        line if in_fence else _sub_line(line)
        for _, line, in_fence in iter_lines_with_fence(text)
    )


def _split_labeled_fields(body: str) -> tuple[str, list[tuple[str, str]]]:
    """Split *body* into (preamble-before-first-label, [(label, content), ...]).
    *content* is the label's own inline text plus every continuation line up to the
    next `**Label:**` line -- real corpus `**Users:**`/`**Goals:**` values are
    multi-line bulleted/numbered blocks (verified against
    st-post/docs/features/F001_Auth/functional-spec.md), not single-line values."""
    preamble_lines: list[str] = []
    fields: list[list] = []
    for line in body.splitlines():
        m = _LABEL_LINE_RE.match(line)
        if m:
            fields.append([m.group(1).strip(), [m.group(2)] if m.group(2) else []])
            continue
        if fields:
            fields[-1][1].append(line)
        else:
            preamble_lines.append(line)
    parsed = [(label, "\n".join(content).strip("\n")) for label, content in fields]
    return "\n".join(preamble_lines).strip("\n"), parsed


def _render_field(label: str, content: str) -> str:
    if not content:
        return f"**{label}:**"
    if "\n" in content:
        return f"**{label}:**\n\n{content}"
    return f"**{label}:** {content}"


def _relabel_overview(body: str) -> str:
    """F-01 (Goals/Non-Goals -> Scope/Non-Scope label rename, body verbatim) + F-02's
    [M] half: the old `**Users:**` block is preserved byte-for-byte inside an HTML
    comment right above a scaffolded `Actors` table -- splitting it into per-actor
    rows is a researcher's judgment call, never guessed here."""
    preamble, fields = _split_labeled_fields(body)
    out_parts = [preamble] if preamble else []
    users_block: str | None = None
    for label, content in fields:
        if label == "Users":
            users_block = _render_field(label, content)
            continue
        out_parts.append(_render_field(_LABEL_RENAME.get(label, label), content))

    actors_parts = ["**Actors**"]
    if users_block:
        actors_parts.append(f"<!-- carried from the old block:\n{users_block}\n-->")
    actors_parts.append(
        "| Actor | Description | Primary goal |\n|-------|--------------|---------------|"
    )
    out_parts.append("\n\n".join(actors_parts))
    return "\n\n".join(p for p in out_parts if p)


def compose_functional_sot(old_text: str) -> ComposeResult:
    """Reshape a v27.0-shaped functional-spec.md into the 13-section SOT shape.

    Idempotent: text already carrying `## 2. Functional Capabilities` is returned
    unchanged -- re-deriving the SOT numbering from already-SOT text is not a defined
    transform (mirrors `compose_screen_sot`'s own idempotency rationale)."""
    if _SOT_SENTINEL in old_text:
        return ComposeResult(old_text, _has_scaffold(old_text), 0, 0)

    text = _rewrite_section_refs(old_text)
    preamble, h2 = split_sections(text, 2)
    moved = 0
    scaffolded = 0

    overview_old = h2.get("## 1. Overview", "")
    sections: dict[str, str] = {"## 1. Overview": _relabel_overview(overview_old)}
    moved += bool(overview_old.strip())  # F-01
    scaffolded += 1  # Actors table split is a researcher judgment call (F-02)

    for old_n, new_n in _RENUMBER.items():
        if old_n == 1:
            continue
        old_heading = f"## {old_n}. {_OLD_TITLES[old_n]}"
        new_heading = f"## {new_n}. {_OLD_TITLES[old_n]}"
        body = h2.get(old_heading, "")
        sections[new_heading] = body
        moved += bool(body.strip())  # F-03

    sections["## 2. Functional Capabilities"] = FUNC_CAPABILITIES_SKELETON.strip()
    scaffolded += 1  # F-04
    sections["## 11. Risks & Known Issues"] = FUNC_RISKS_SKELETON.strip()
    scaffolded += 1  # F-05
    sections["## 12. Dependencies"] = FUNC_DEPS_SKELETON.strip()
    scaffolded += 1  # F-06

    unknown = [(name, body) for name, body in h2.items() if name not in _OLD_ORDER]
    moved += len(unknown)

    parts = [preamble.rstrip("\n")]
    for name in REQUIRED_H2_FUNC:
        parts.append(name + "\n\n" + sections[name].strip("\n"))
    for uname, ubody in unknown:
        parts.append(uname + "\n\n" + ubody.strip("\n"))
    result_text = "\n\n".join(parts).rstrip("\n") + "\n"
    return ComposeResult(result_text, True, moved, scaffolded)
