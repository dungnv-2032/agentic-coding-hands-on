"""Mode A -- § 5 Screens and § 2 Open Decisions renderers (phase-05, B4c).

Split out of `_audience_split_render_func_sections_lib.py` to keep each module under
the repo's 200-line guidance (adding the SCR### resolution ladder pushed that module
over). `render_screens` used to read `cells[1]` POSITIONALLY as the SCR column --
wrong on every real v26 3-column table, where `cells[1]` is *What User Sees* -- this
module fixes that with header-driven column detection plus the L0-L3 resolution
ladder (`_audience_split_screen_bind_lib.resolve_row`).

Degradation contract: an L3 (unresolved) row is NEVER emitted as a `—` placeholder
table row -- that would reproduce a per-row `func.screens_scr_unresolved` critical in
a new shape. It goes to a `### Unbound Screens` sub-block instead, and the caller
threads the same list into `render_open_decisions` so every unbound screen gets
exactly one § 2 Open Decisions row, numbered in the SAME D### series as any
`[NEEDS_DOMAIN_CONFIRMATION]`-promoted marker.

Stdlib only.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _audience_split_screen_bind_lib import resolve_row  # noqa: E402


def render_open_decisions(markers: list[str], unbound_screens: list[dict] | None = None) -> str:
    """§ 2 Open Decisions: one continuous D### series across BOTH sources -- markers
    promoted from `[NEEDS_DOMAIN_CONFIRMATION]` AND screens that fell to L3 in the
    SCR### resolution ladder. A single counter, not two, so a screen row added while
    markers already exist keeps numbering unambiguous."""
    unbound_screens = unbound_screens or []
    if not markers and not unbound_screens:
        return "None — no unresolved domain confirmations."
    lines = ["| D### | Decision | Default proposal | Rationale | Blocks work |",
             "|------|----------|-------------------|-----------|--------------|"]
    i = 0
    for marker in markers:
        i += 1
        lines.append(
            f"| D{i:03d} | {marker} | Ship with current inferred behavior; revisit if "
            f"incorrect. | Promoted from a domain-confirmation marker found during v26 "
            f"migration. | no |"
        )
    for screen in unbound_screens:
        i += 1
        name = screen["name"]
        lines.append(
            f'| D{i:03d} | Screen "{name}" has no SCR### binding | Bind manually against '
            f"`generated/screen-list.md`, or confirm the screen no longer exists | No exact "
            f"or normalized name match in the Screen Index during v26→v27 migration | no |"
        )
    return "\n".join(lines)


def _screen_column_indices(header: list[str]) -> tuple[int, int | None, int | None]:
    """Header-driven column detection. Falls back to positional 0/1/2 only when
    the header itself is missing/unrecognized."""
    hc = [h.casefold().strip() for h in header]
    name_idx = 0
    for i, h in enumerate(hc):
        if "screen" in h and "scr" not in h.replace("screen", ""):
            name_idx = i
            break
    sees_idx = next((i for i, h in enumerate(hc) if "sees" in h), 1 if len(hc) > 1 else None)
    can_do_idx = next((i for i, h in enumerate(hc) if "can do" in h), 2 if len(hc) > 2 else None)
    return name_idx, sees_idx, can_do_idx


def render_screens(screens: dict, index: dict[str, str]) -> tuple[str, list[dict]]:
    """Render § 5 Screens. Each row is resolved against `index` (generated/
    screen-list.md's Screen Index) via the L0-L3 ladder (`resolve_row`). Resolved
    rows land in the 4-column table; L3 residue goes to a `### Unbound Screens`
    sub-block instead of a table row.

    Returns (body_text, unbound_screens) -- unbound_screens is `[]` when every row
    resolved (or the feature is background/table-less)."""
    if screens["background"] or not screens["rows"]:
        return "N/A — background feature (no screens).", []
    name_idx, sees_idx, can_do_idx = _screen_column_indices(screens.get("header") or [])
    lines = ["| Screen Name | SCR### | What User Sees | What User Can Do |",
             "|-------------|--------|-----------------|-------------------|"]
    unbound: list[dict] = []
    for row in screens["rows"]:
        name = row[name_idx] if name_idx < len(row) else (row[0] if row else "")
        sees = row[sees_idx] if sees_idx is not None and sees_idx < len(row) else ""
        can_do = row[can_do_idx] if can_do_idx is not None and can_do_idx < len(row) else ""
        code, _rung = resolve_row(row, index)
        if code:
            lines.append(f"| {name} | {code} | {sees} | {can_do} |")
        else:
            unbound.append({"name": name, "sees": sees, "can_do": can_do})
    body = "\n".join(lines)
    if unbound:
        body += (
            "\n\n### Unbound Screens\n\n"
            "These screens were named in the pre-v27 source but could not be bound to a "
            "SCR### code during migration. Each has an Open Decision row in § 2.\n\n"
        )
        body += "\n".join(
            f"- **{u['name']}** — {u['sees'] or 'N/A'} *(User can: {u['can_do'] or 'N/A'}.)*"
            for u in unbound
        )
    body += "\n\n### User Journey\n\n" + (screens["user_journey"] or "N/A")
    return body, unbound
