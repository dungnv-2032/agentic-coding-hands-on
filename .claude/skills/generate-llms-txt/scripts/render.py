#!/usr/bin/env python3
"""Render llms.txt (index) and llms-full.txt (inlined body) from content-contract sections.

Moved out of build-llms-skeleton.py (phase 2) so the CLI file has room for v2 orchestration:
`build_url`, `inline_body`, `_heading_len` are the v1 functions, unchanged. `skeleton()`/`full()`
replace v1's `build_skeleton`/`build_full` — both now drive off a `sections` list shaped by
content_contract.build() (also works for the legacy `--audience dev` grouping — see its
`_legacy_sections()`), not a raw file/section-name grouping.

Self-containment (red-team F8/F9): `rewrite_links()` strips or downgrades every relative
link/image so `llms-full.txt` ships with nothing load-bearing outside the file itself. `full()`
re-derives `inlined_rels` from the `sections` it is handed on EVERY call — never cached — so a
section dropped by a later budget trim reclassifies its links to citations instead of leaving a
dangling reference (F9).

Profile prose (URL, department, owner, support contact) renders ONLY in `full()`'s intro
section — never in `skeleton()` — because `analyze-llms-txt.js` harvests the first bare http(s)
URL on any non-heading line, and a product URL in the index blockquote would be mis-parsed as a
documentation link (F8). `skeleton()` keeps v1's shape: H1, one placeholder (or profile-summary)
blockquote, then link sections.
"""
import re
from pathlib import Path, PurePosixPath

from md_parse import read_text

_BLOCKQUOTE_TODO = "> <TODO: one or two sentences — what the product is, who it's for, its core value>"

_IMG_RE = re.compile(r'!\[([^\]]*)\]\([^)]+\)')
_LINK_RE = re.compile(r'(?<!!)\[([^\]]+)\]\(([^)]+)\)')
_REL_LINK_RE = re.compile(r'(?<!!)\[[^\]]+\]\((?!https?://)[^)]+\)')
_IMG_ANY_RE = re.compile(r'!\[[^\]]*\]\([^)]+\)')


def build_url(rel: str, base_url: str) -> str:
    """Link target: repo-relative path, or an absolute web URL when --base-url is set
    (web routes usually drop the doc extension)."""
    if not base_url:
        return rel
    path = PurePosixPath(rel)
    if path.suffix in (".md", ".mdx"):
        path = path.with_suffix("")
    return f"{base_url.rstrip('/')}/{path}"


def _heading_len(stripped: str) -> int:
    """Number of leading '#' if the line is an ATX heading (`# ` … `###### `), else 0."""
    n = len(stripped) - len(stripped.lstrip("#"))
    return n if 1 <= n <= 6 and stripped[n:n + 1] == " " else 0


def inline_body(content: str) -> str:
    """Prepare a doc for inlining under `### {title}`: drop YAML frontmatter and the leading H1,
    then demote every remaining heading by two levels (fence-aware) so the inlined outline nests
    correctly instead of colliding with the wrapper headings."""
    lines = content.splitlines()
    if lines and lines[0].strip() == "---":
        close = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
        if close is not None:
            lines = lines[close + 1:]
    out, in_fence, h1_dropped = [], False, False
    for line in lines:
        st = line.lstrip()
        if st.startswith("```"):
            in_fence = not in_fence
            out.append(line)
            continue
        m = None if in_fence else _heading_len(st)
        if m:
            if m == 1 and not h1_dropped:
                h1_dropped = True
                continue
            out.append("#" * min(m + 2, 6) + st[m:])
            continue
        out.append(line)
    return "\n".join(out).strip()


def rewrite_links(body: str, inlined_rels: set) -> str:
    """Self-containment pass (F8/F9), applied after inline_body(). Per the phase-02 table: a
    link into an inlined target collapses to bare text; a link to a target NOT inlined becomes a
    plain-text citation; an image becomes a bracketed alt tag; an anchor collapses to bare text;
    an absolute http(s) link is left alone (agents with fetch may use it)."""
    body = _IMG_RE.sub(lambda m: f"[image: {m.group(1)}]", body)

    def _link(m):
        text, target = m.group(1), m.group(2).strip()
        if target.startswith(("http://", "https://")):
            return m.group(0)
        if target.startswith("#"):
            return text
        rel = target.split("#", 1)[0]  # drop an in-doc anchor suffix from a relative target
        if rel in inlined_rels:
            return text
        return f"{text} (source: {rel})"

    return _LINK_RE.sub(_link, body)


def _entry_body(entry: dict) -> str:
    """The body to inline for one entry — a budget-ladder override (`_body_override`) when the
    section was collapsed/tightened, else the file re-read fresh (never cached, per F9)."""
    override = entry.get("_body_override")
    if override is not None:
        return override
    return inline_body(read_text(Path(entry["abs"])))


def _blockquote(summary):
    return f"> {summary}" if summary else _BLOCKQUOTE_TODO


def skeleton(name: str, sections, base_url: str, summary=None) -> str:
    """The llms.txt index: H1 + blockquote + link sections. No profile prose beyond `summary`
    (plain text, no raw URL — F8); the `intro` section never gets its own heading here — it IS
    the H1 + blockquote, matching v1's shape exactly."""
    lines = [f"# {name}", "", _blockquote(summary), ""]
    for sec in sections:
        if sec["id"] == "intro" or sec["status"] == "omitted":
            continue
        lines += [f"## {sec['title']}", ""]
        if sec["status"] == "gap":
            lines += [f"> {sec['advisory']}", ""]
            continue
        for f in sec["entries"]:
            lines.append(f"- [{f['title']}]({build_url(f['rel'], base_url)}): {f.get('desc') or '<TODO desc>'}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _intro_prose(profile: dict) -> list:
    """Profile fields as plain prose — this is the ONLY place a product URL/owner/department/
    support contact are ever rendered (F8: never in skeleton())."""
    fields = profile.get("fields", {})
    lines = []
    if fields.get("name_meaning"):
        lines.append(f"**Name meaning**: {fields['name_meaning']}")
    for url in fields.get("urls") or []:
        lines.append(f"**URL**: {url}")
    for label, key in (("Department", "department"), ("Owner", "owner"), ("Support contact", "support")):
        if fields.get(key):
            lines.append(f"**{label}**: {fields[key]}")
    if fields.get("surfaces"):
        lines.append(f"**Surfaces**: {', '.join(fields['surfaces'])}")
    if fields.get("summary"):
        lines += ["", fields["summary"]]
    return lines


def full(name: str, sections, profile: dict, base_url: str) -> str:
    """llms-full.txt: H1 + blockquote + every section's H2, each inlined (self-contained) or
    carrying a gap advisory. `inlined_rels` is re-derived from `sections` on EVERY call — never
    cached — so a later budget trim correctly reclassifies a dropped section's links to
    citations instead of leaving a dangling reference (F9)."""
    profile = profile or {}
    inlined_rels = {rel for sec in sections if sec["status"] == "filled" and sec["id"] != "intro"
                     for rel in sec.get("sources", [])}
    lines = [f"# {name}", "", _blockquote(profile.get("fields", {}).get("summary")), ""]
    for sec in sections:
        if sec["status"] == "omitted":
            continue
        lines += [f"## {sec['title']}", ""]
        if sec["id"] == "intro":
            lines += _intro_prose(profile) if sec["status"] == "filled" else [f"> {sec['advisory']}"]
            lines.append("")
            continue
        if sec["status"] == "gap":
            lines += [f"> {sec['advisory']}", ""]
            continue
        for f in sec["entries"]:
            body = rewrite_links(_entry_body(f), inlined_rels)
            lines += [f"### {f['title']}", "", body, ""]
    return "\n".join(lines).rstrip() + "\n"


def self_containment_counts(sections, text: str) -> dict:
    """Post-trim tally for the manifest (measured AFTER budget trimming, per F9). `rewritten`
    counts relative link/image occurrences in the raw bodies of sections that made it into the
    final render; `remaining` scans the final text itself and must be 0 once the gate holds."""
    rewritten = 0
    for sec in sections:
        if sec["status"] != "filled" or sec["id"] == "intro":
            continue
        for f in sec["entries"]:
            raw = _entry_body(f)
            rewritten += len(_REL_LINK_RE.findall(raw)) + len(_IMG_ANY_RE.findall(raw))
    remaining = len(_REL_LINK_RE.findall(text)) + len(_IMG_ANY_RE.findall(text))
    return {"rewritten": rewritten, "remaining": remaining}
