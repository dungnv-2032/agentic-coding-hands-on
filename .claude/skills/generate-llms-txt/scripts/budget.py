#!/usr/bin/env python3
"""Token budget gate (`--budget`, default 50000). Estimate = chars/4, always reported as an
estimate — never billed as an exact count.

Curated+capped is a deliberate choice, not a shortcut: ecosystem full-dumps of comparable
projects run 177k-3.7M tokens (researcher report §2, §6) — unusable as attached context. A
future maintainer tempted to "fix" the cap away should read this before doing so.

`enforce()` OWNS rendering: it calls `render_fn` (== `render.full`) after every trim step, so
`render.full`'s per-call re-derivation of `inlined_rels` (F9) sees each trim's effect
immediately — a link into a section a trim just dropped is reclassified to a citation on the
very next render, never left dangling.
"""
import re
from pathlib import Path

import render as _render
from md_parse import read_text

_HEADING_RE = re.compile(r"#{1,6} ")

TRIM_LADDER = (
    ("optional-dropped", lambda s: _drop_section(s, "optional")),
    ("api-detail-collapsed", lambda s: _collapse(s, "api")),
    ("tighten-screens", lambda s: _tighten(s, "screens")),
    ("tighten-features", lambda s: _tighten(s, "features")),
    ("tighten-usage", lambda s: _tighten(s, "usage")),
)
# intro and install are NEVER trimmed — they are the point of the artifact.


def est_tokens(text: str) -> int:
    """Stated as an ESTIMATE everywhere it is reported."""
    return len(text) // 4


def _drop_section(sections, sid):
    return [s for s in sections if s["id"] != sid]


def _truncate_at_first_heading(body: str) -> str:
    """Keep everything up to the first heading line (a heading can only be recognised outside a
    fence, so this can never cut inside one); if there is no sub-heading, the body is returned
    whole."""
    lines = body.splitlines()
    in_fence, cut = False, len(lines)
    for i, line in enumerate(lines):
        st = line.lstrip()
        if st.startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence and i > 0 and _HEADING_RE.match(st):
            cut = i
            break
    return "\n".join(lines[:cut]).rstrip()


def _map_section(sections, sid, note):
    """Replace `sid`'s filled entries with a truncated body + a trim note, fence-aware. Other
    fields (rel/title/abs) are untouched so self-containment / sources keep working on the
    trimmed entry exactly as on the full one."""
    out = []
    for s in sections:
        if s["id"] != sid or s["status"] != "filled" or not s["entries"]:
            out.append(s)
            continue
        new_entries = []
        for f in s["entries"]:
            raw = _render.inline_body(read_text(Path(f["abs"])))
            trimmed = _truncate_at_first_heading(raw)
            nf = dict(f)
            nf["_body_override"] = f"{trimmed}\n\n…({note} — see `{f['rel']}`)"
            new_entries.append(nf)
        ns = dict(s)
        ns["entries"] = new_entries
        out.append(ns)
    return out


def _collapse(sections, sid):
    """Keep endpoint/tool names, drop schemas & examples — collapses to the lead block."""
    return _map_section(sections, sid, "collapsed")


def _tighten(sections, sid):
    """Keep each entry's own lead paragraph(s) up to its first sub-heading."""
    return _map_section(sections, sid, "trimmed")


def enforce(sections, cap: int, render_fn):
    """(text, report). `render_fn` == `render.full`; called after every trim step so its
    per-call `inlined_rels` re-derivation (F9) tracks each trim immediately. Exceeding the cap
    after the whole ladder is NOT an error — the file is written with `over_cap: true` and the
    caller's report tells the user to raise `--budget` or split the docs."""
    text, trims = render_fn(sections), []
    for name, step in TRIM_LADDER:
        if est_tokens(text) <= cap:
            break
        before = est_tokens(text)
        sections = step(sections)
        text = render_fn(sections)
        trims.append({"step": name, "saved_tokens_est": before - est_tokens(text)})
    over = est_tokens(text) > cap
    report = {"cap_tokens": cap, "est_tokens": est_tokens(text), "est_method": "chars/4 (estimate)",
              "over_cap": over, "trims": trims,
              "self_containment": _render.self_containment_counts(sections, text)}
    return text, report
