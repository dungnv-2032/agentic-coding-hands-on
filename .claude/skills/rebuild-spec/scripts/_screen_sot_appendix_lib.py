"""content-preservation-map.md § A: S-19 (marker rewrite) + `## Implementation Mapping`
assembly from S-07's async checks, S-08's server blocks, and S-15's raw expressions.
Split out of `_screen_sot_compose_lib.py` to hold the 200-line guidance.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _screen_sot_table_lib import build_table  # noqa: E402

# S-19: DEV_APPENDIX_MARKER (Mode C's `---` + italic sentence) is REWRITTEN into a real
# H2 divider (target-shape-spec.md § 1.2). `_audience_split_mode_c_lib.DEV_APPENDIX_MARKER`
# is intentionally NOT imported here -- Mode C stays untouched and this module only
# needs to know the literal marker text to split on, which `_screen_sot_compose_lib`
# passes in (kept there so the BA/dev split logic has one home).
TECHNICAL_APPENDIX_HEADING = "## Technical Appendix"
TECHNICAL_APPENDIX_BODY = (
    "> Implementation detail below — controller/class names, framework specifics, "
    "helper methods, JavaScript wiring, API implementation, session state, security "
    "implementation, source citations and code-reading order. PO/BA/QA/Designer "
    "readers can stop at § 10."
)

IMPLEMENTATION_MAPPING_HEADER = ["Refers to", "Kind", "Implementation", "Source"]
IMPLEMENTATION_MAPPING_NA = (
    "N/A — no implementation-level detail beyond what is already cited inline above."
)


def build_implementation_mapping(
    async_checks: list[tuple[str, str]],
    raw_expressions: list[tuple[str, str]],
    server_side_body: str,
) -> str:
    """Absorbs everything demoted out of §§1-10 (target-shape-spec.md § 1.4):

    - S-07's `Async Check` cells -> one `endpoint` row per E## field.
    - S-15's raw Conditional-UI expressions -> one row per condition, `Refers to`
      the section (the Element(s) binding is still `{TBD}` at this point).
    - S-08's whole `### B) Server-side` block(s) -> MOVED verbatim (never reformatted
      into the table -- the block's own Endpoint/Request/Success/Errors/Trigger/Source
      bullets already ARE the content; forcing them into 4 flat columns would lose
      structure without any preservation benefit).
    """
    rows: list[list[str]] = []
    for eid, check in async_checks:
        rows.append([eid, "endpoint", check, "—"])
    for condition, ctype in raw_expressions:
        rows.append(["## 7. Conditional UI", ctype or "guard", condition, "—"])

    parts: list[str] = []
    if rows:
        parts.append(build_table(IMPLEMENTATION_MAPPING_HEADER, rows))
    moved_server_body = server_side_body.strip()
    if moved_server_body:
        parts.append(
            "### B) Server-side (moved from the retired `## Validation & Error Feedback`)\n\n"
            + moved_server_body
        )
    if not parts:
        return IMPLEMENTATION_MAPPING_NA
    return "\n\n".join(parts)


def extract_unknown_h2(h2: dict[str, str], known: set[str]) -> list[tuple[str, str]]:
    """`[(heading, body), ...]` for every H2 in *h2* not in *known*, preserving the
    order they appeared in the source (dict insertion order, per
    `_audience_split_md_sections_lib.split_sections`). Nothing is ever dropped here --
    this is the unknown-heading fallback S-25 carries forward from Mode C."""
    return [(name, body) for name, body in h2.items() if name not in known]


def assemble_document(
    preamble: str,
    ba_order: list[str],
    ba_sections: dict[str, str],
    appendix_order: list[str],
    appendix_sections: dict[str, str],
    unknown: list[tuple[str, str]],
) -> str:
    """Emit the final SOT document: *preamble*, then every `## N.` BA section in
    *ba_order*, the `## Technical Appendix` divider, then every appendix section in
    *appendix_order* that is actually present -- with S-25's unknown H2s inserted
    immediately before `## Source Walkthrough` (HARD CONSTRAINT: that heading must stay
    the literal last section, target-shape-spec.md § 1.3)."""
    parts = [preamble.rstrip("\n")]
    for name in ba_order:
        parts.append(name + "\n\n" + ba_sections[name].strip("\n"))
    parts.append(TECHNICAL_APPENDIX_HEADING + "\n\n" + TECHNICAL_APPENDIX_BODY)
    for name in appendix_order:
        if name == "## Source Walkthrough":
            for uname, ubody in unknown:
                parts.append(uname + "\n\n" + ubody.strip("\n"))
        if name in appendix_sections:
            parts.append(name + "\n\n" + appendix_sections[name].strip("\n"))
    return "\n\n".join(parts).rstrip("\n") + "\n"
