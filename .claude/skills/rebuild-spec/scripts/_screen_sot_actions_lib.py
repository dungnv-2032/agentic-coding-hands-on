"""content-preservation-map.md § A: `## 4. User Actions`, `## 7. Conditional UI`,
`## 8. Navigation` (S-10 through S-16). Split out of `_screen_sot_compose_lib.py` to
hold the 200-line guidance.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _screen_sot_table_lib import build_table, cell, col_index, split_around_first_table  # noqa: E402

AVAILABLE_ACTIONS_HEADER = ["Action", "Element", "Trigger", "Condition", "Result on this screen", "Source"]
CONDITIONAL_UI_HEADER = ["Condition", "Type", "Element(s)", "Visible when", "Hidden when", "Notes"]
ENTRY_POINTS_HEADER = ["From", "Trigger there", "Condition", "Source"]
EXITS_HEADER = ["Action", "Element", "Condition", "Destination", "Result", "Source"]

# D3 (target-shape-spec.md § 1.4) -- verbatim, replaces whatever v27 scope prose (if
# any) preceded `### Happy Path`. The old text was a generic "cross-screen navigation
# belongs elsewhere" scope note; this is its SOT-numbered restatement (S-12: KEEP+edit,
# the one deliberate content edit the preservation map names as such).
USER_ACTIONS_INTRO = (
    "> **Scope:** within-screen interactions only. Cross-screen navigation belongs in "
    "`## 8. Navigation` (which projects `screen-flow.md § Screen Access Paths` — see "
    "the D3 note in target-shape-spec.md § 1.4). Reference region names from "
    "`### Layout Regions` (§2, above) when describing where actions occur."
)
AVAILABLE_ACTIONS_NA = "N/A — no elements carry a discrete user-triggered action."
NAV_POINTER_COMMENT = (
    "<!-- Projection of screen-flow.md § Screen Access Paths for this screen -- "
    "needs_llm_fill: do not invent a destination, project it from screen-flow.md. -->"
)
ENTRY_POINTS_NA = "N/A — this screen has no other entry points beyond the ones enumerated in screen-flow.md."
EXITS_NA = "N/A — this screen has no exits (terminal screen)."


@dataclass
class ConditionalUiResult:
    table_text: str
    # (Condition raw expression, Type) pairs -- feed `## Implementation Mapping`.
    raw_expressions: list[tuple[str, str]] = field(default_factory=list)
    row_count: int = 0


def build_user_actions(happy_path_body: str, branches_body: str, interaction_notes_body: str) -> str:
    """S-10 (Happy Path, KEEP) + S-11 (Branches, KEEP) + S-12 (intro, KEEP+edit) +
    S-13 (Available Actions, new -- scaffolded, needs_llm_fill) + S-14 (Interaction
    Notes, MOVE from the retired `## Interaction Patterns`)."""
    parts = [
        USER_ACTIONS_INTRO, "",
        "### Available Actions", "",
        build_table(AVAILABLE_ACTIONS_HEADER, [["{action name}", "E{##}", "{gesture}", "{condition, or —}", "{within-screen outcome only}", "`{file}:{line}`"]]),
        "", AVAILABLE_ACTIONS_NA, "",
        "### Happy Path", "",
        happy_path_body.strip() or "N/A",
        "", "### Branches", "",
        branches_body.strip() or "N/A", "",
        "### Interaction Notes", "",
        interaction_notes_body.strip() or "N/A",
    ]
    return "\n".join(parts)


def build_conditional_ui(conditional_rendering_body: str) -> ConditionalUiResult:
    """S-15 [M] part only: `Condition`->`Condition` (raw, unrewritten -- the
    user-visible-behavior restatement is [L], a researcher's job), `Type`->`Type`,
    `Renders`->`Visible when`, `Hidden`->`Hidden when`, `Notes`->`Notes`. `Element(s)`
    is seeded `{TBD}` -- binding a condition to specific E## elements is a judgment
    call, never guessed. Raw expressions are ALSO handed back for
    `## Implementation Mapping` (S-15's [M]+[L] split), so today's mechanical Condition
    text is never the only copy of that information once the [L] rewrite lands."""
    prefix, header, rows, suffix = split_around_first_table(conditional_rendering_body)
    if header is None:
        text = conditional_rendering_body.strip() or "N/A — no conditional UI detected."
        return ConditionalUiResult(text, [], 0)
    header_cf = [h.casefold() for h in header]
    col = col_index(header_cf, "condition", "type", "renders", "hidden", "notes")
    new_rows = []
    raw_expressions: list[tuple[str, str]] = []
    for cells in rows:
        condition = cell(cells, col, "condition")
        ctype = cell(cells, col, "type")
        new_rows.append([
            condition, ctype, "{TBD}",
            cell(cells, col, "renders"), cell(cells, col, "hidden"), cell(cells, col, "notes"),
        ])
        if condition and condition not in ("—", "-", "N/A"):
            raw_expressions.append((condition, ctype))
    out = []
    if prefix.strip():
        out.append(prefix.strip())
        out.append("")
    out.append(build_table(CONDITIONAL_UI_HEADER, new_rows))
    if suffix.strip():
        out.append("")
        out.append(suffix.strip())
    return ConditionalUiResult("\n".join(out), raw_expressions, len(new_rows))


def build_navigation() -> str:
    """S-16: absent in v27 -- scaffolded with header rows + a pointer comment to
    `screen-flow.md § Screen Access Paths` (D3). The step must NEVER guess a
    destination (feedback §8), so this is always a pure scaffold, needs_llm_fill."""
    entry_row = ["{SCR###_Name \\| external}", "{gesture/event on the origin screen}", "{condition, or —}", "`{file}:{line}`"]
    exit_row = ["{action name}", "E{##}", "{condition, or —}", "{SCR###_Name \\| external URL \\| (stays on screen)}", "{redirect \\| new tab \\| modal \\| toast then redirect}", "`{file}:{line}`"]
    return "\n".join([
        NAV_POINTER_COMMENT, "",
        "### Entry Points", "",
        build_table(ENTRY_POINTS_HEADER, [entry_row]), "", ENTRY_POINTS_NA, "",
        "### Exits", "",
        build_table(EXITS_HEADER, [exit_row]), "", EXITS_NA,
    ])
