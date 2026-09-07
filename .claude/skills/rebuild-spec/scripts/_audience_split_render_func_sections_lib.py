"""Mode A -- per-section renderers for functional-spec.md's 10 fixed H2 sections.

Split out of `_audience_split_compose_a_lib.py` to keep each module under the repo's
200-line guidance. Each function takes whatever `_audience_split_parse_v26_lib.py`
parsed out of the v26 files and returns the section's BODY text (no heading) -- the
composer assembles the 10 bodies into the full document.

§ 5 Screens and § 2 Open Decisions render in the sibling
`_audience_split_render_screens_lib.py` instead (phase-05, B4c) -- adding the SCR###
resolution ladder here would have pushed this module back over the 200-line guidance.

`[NEEDS_DOMAIN_CONFIRMATION]` markers are promoted to § 2 Open Decisions rows and MUST
NOT survive inline anywhere else (Requirement 4) -- `_sanitize`/`_field_block` are the
enforcement point for every section built from raw copied v26 prose.

Stdlib only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _audience_split_fence_lib import fence_dev_tokens  # noqa: E402
from _audience_split_parse_v26_lib import sentence_for_block, unique_by_code  # noqa: E402

_NEEDS_CONFIRM_RE = re.compile(r"\[NEEDS_DOMAIN_CONFIRMATION\]")
_NA_TEXT = "N/A — inferred from code; domain confirmation needed."
_BAND_ORDER = ["Foundation (0xx)", "Navigation (1xx)", "Screen-Related (2xx-3xx)",
               "Interaction (4xx)", "Security (6xx)"]
_BAND_BY_DIGIT = {"0": _BAND_ORDER[0], "1": _BAND_ORDER[1], "2": _BAND_ORDER[2],
                   "3": _BAND_ORDER[2], "4": _BAND_ORDER[3], "6": _BAND_ORDER[4]}


def sanitize(text: str) -> str:
    """Final safety net (Requirement 4): a `[NEEDS_DOMAIN_CONFIRMATION]` marker must
    never survive into functional-spec.md inline -- every occurrence is promoted to a
    § 2 Open Decisions row instead. `parse_needs_confirmation` already builds those rows
    from the marker's context; this strips the literal token from whatever raw v26
    prose got copied verbatim elsewhere (Overview, Screens, etc.) so it can never
    double-report via `_check_open_decisions`'s inline-marker scan.

    Also the single choke point for dev-token fencing (phase-04, B4b): reached by
    both `_field_block` (per section) and final document assembly, so wiring
    `fence_dev_tokens` in here -- rather than at each call site -- is what makes the
    idempotency guarantee (running twice is a no-op) actually hold in practice."""
    return fence_dev_tokens(_NEEDS_CONFIRM_RE.sub("", text))


def _field_block(label: str, content: str) -> str:
    """A multi-line value (bullets/numbered steps) gets its own paragraph after the
    label; a single-line sentence stays inline -- either way the label is unambiguous.
    Sanitized here (not just at the final assembly pass) so a marker stripped out of
    the middle of a copied v26 line doesn't leave a double-space behind."""
    content = "\n".join(re.sub(r"[ \t]{2,}", " ", ln) for ln in sanitize(content).splitlines())
    content = content.strip() or _NA_TEXT
    return f"**{label}:**\n\n{content}" if "\n" in content else f"**{label}:** {content}"


def render_overview(bc: dict, tech_overview: str) -> str:
    return "\n\n".join([
        _field_block("Problem", bc["why_it_matters"]),
        _field_block("Solution", tech_overview),
        _field_block("Users", bc["who_uses_it"]),
        _field_block("Goals", bc["what_they_do"]),
        "**Non-Goals:** None called out.",
    ])


def render_requirements(fr_items: dict[str, str]) -> str:
    if not fr_items:
        return "No functional requirements are declared for this fixture."
    bands: dict[str, list[tuple[str, str]]] = {}
    for code, desc in sorted(fr_items.items()):
        digit = code.split("-")[1][0]
        bands.setdefault(_BAND_BY_DIGIT.get(digit, "Other"), []).append((code, desc))
    parts: list[str] = []
    for title in [*_BAND_ORDER, "Other"]:
        if title not in bands:
            continue
        parts.append(f"### {title}\n")
        for code, desc in bands[title]:
            parts.append(f"- **{code}** {desc}")
        parts.append("")
    return "\n".join(parts).strip()


def render_business_rules(blocks: list[dict]) -> str:
    relevant = [b for b in unique_by_code(blocks) if b["prefix"] in ("BR", "DEC", "SM")]
    if not relevant:
        return "No business rules are declared for this fixture."
    return "\n".join(f"- {sentence_for_block(b)} ({b['code']})" for b in relevant)


def render_user_stories(stories: list[dict]) -> str:
    if not stories:
        return "No user stories are declared for this fixture."
    parts: list[str] = []
    for s in stories:
        parts.append(f"### {s['code']} — {s['title']}\n")
        parts.append(s["narrative"] or "N/A")
        parts.append("\n**Acceptance Criteria:**")
        if s["scenarios"]:
            parts += [f"- [ ] {sc['then']}" for sc in s["scenarios"]]
        else:
            parts.append("- [ ] Observable outcome not derivable from source scenarios.")
        parts.append("")
    return "\n".join(parts).strip()


def render_scenarios(stories: list[dict]) -> str:
    if not any(s["scenarios"] for s in stories):
        return "No scenarios are declared for this fixture."
    parts: list[str] = []
    for s in stories:
        for i, sc in enumerate(s["scenarios"]):
            label = "Happy Path" if i == 0 else f"Scenario {i + 1}"
            parts.append(f"### {s['code']} — {label}\n")
            parts.append(f"**Given** {sc['given']}, **When** {sc['when']}, **Then** {sc['then']}.")
            parts.append("")
    return "\n".join(parts).strip()


def render_edge_cases(rows: list[list[str]]) -> str:
    if not rows:
        return "No edge cases are declared for this fixture."
    lines = ["| Scenario | What Happens | User-Facing Message |",
             "|----------|--------------|----------------------|"]
    for row in rows:
        cells = (row + [""] * 3)[:3]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def render_edge_behaviours(fr_verification: dict[str, list[str]]) -> str:
    if not fr_verification:
        return "Behaviours are verified through the scenarios above."
    lines = []
    for code in sorted(fr_verification):
        lines += [f"- **{code}** → {cond}" for cond in fr_verification[code]]
    return "\n".join(lines)
