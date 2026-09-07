#!/usr/bin/env python3
"""The 7-section end-user content contract (phase-02 § "The contract" — table of record).

`build(files, profile, audience)` turns the audience-kept file list into an ordered section
list the renderer consumes: every REQUIRED section is either `filled`, or carries an explicit
`gap` advisory naming the export path — nothing is silently omitted (FR-5). `optional` is never
required, so its only non-`filled` state is `omitted`.

Match order != emit order (red-team F2): the usage catch-all (`docs/user-guide/*`) would
otherwise claim `docs/user-guide/screens.md` before the screens section ever looks, producing a
false gap. Matching runs specificity-first (`MATCH_ORDER`); emission runs in contract order
(`EMIT_ORDER`).

`docs/screens/**` (rebuild-spec's dev-coded, promoted per-screen specs — `SCR###` codes, layer
notes) stays EXCLUDED from `SCREENS_GLOBS` (red-team F7) and from the audience keep-set, so a
repo whose only screen material lives there still reports a screens gap.

F7 did cut too wide, though: `docs/generated/screen-list.md` is the generated screen INVENTORY
(one row per screen — name + route), which is precisely what the screens section asks for. It is
accepted here, and `audience_filter.KEEP_PATTERNS` carves it out of the blanket
`docs/generated/**` drop the same way `feature-list.md` is already carved out. Without BOTH
halves the glob is dead: the audience filter would drop the file before this module ever saw it.
"""
import fnmatch
from typing import NamedTuple, Optional

from discovery import SECTION_ORDER

INSTALL_GLOBS = ("*/install*", "*getting-started*", "*quickstart*", "readme.md")
USAGE_GLOBS = ("docs/user-guide/*", "*/guides/*", "*tutorial*", "*usage*")
SCREENS_GLOBS = ("docs/user-guide/screens*", "docs/generated/screen-list.md")  # NOT docs/screens/** — F7
FEATURES_GLOBS = ("docs/generated/feature-list.md", "docs/features/*")
API_GLOBS = ("docs/api/*", "*mcp*", "openapi*", "swagger*")
OPTIONAL_GLOBS = ("*faq*", "changelog*", "*polic*")


class Section(NamedTuple):
    id: str
    title: str
    required: object  # True | False | "surface" — three-valued, see _api_state (F6c)
    globs: tuple

    def render(self, status: str, hits: list, advisory: Optional[str]) -> dict:
        return {
            "id": self.id, "title": self.title, "required": self.required,
            "status": status, "entries": list(hits),
            "sources": [h["rel"] for h in hits],
            "advisory": advisory if status == "gap" else None,
        }


# id, title, required, fnmatch globs (matched against the lowercased repo-relative path).
CONTRACT = (
    Section("intro", "General Introduction", True, ()),           # profile-driven, see _intro_section
    Section("install", "Installation", True, INSTALL_GLOBS),
    Section("usage", "Usage Guide", True, USAGE_GLOBS),
    Section("screens", "Screens", True, SCREENS_GLOBS),
    Section("features", "Features", True, FEATURES_GLOBS),
    Section("api", "API & MCP Guide", "surface", API_GLOBS),
    Section("optional", "Optional", False, OPTIONAL_GLOBS),
)
_BY_ID = {s.id: s for s in CONTRACT}

THIN_THRESHOLD = 2  # this many required gaps makes the artifact "thin" — the SKILL.md preflight stops there

MATCH_ORDER = ("intro", "install", "screens", "features", "api", "usage", "optional")  # specific -> catch-all
EMIT_ORDER = ("intro", "install", "usage", "screens", "features", "api", "optional")  # the contract, F2

ADVISORY = {
    "intro": "Product metadata missing. Run `product_profile.py --init` and fill `docs/product-profile.md`.",
    "install": "No installation guide found. Export it into `docs/user-guide/install.md` and re-run.",
    "usage": "No usage guide found. Export the user guide into `docs/user-guide/` and re-run.",
    "screens": ("No screen list found. Run `/tkm:rebuild-spec` (generates "
                "`docs/generated/screen-list.md`) or export an end-user screen tour into "
                "`docs/user-guide/screens.md`, then re-run."),
    "features": "No feature list found. Run `/tkm:rebuild-spec` or add `docs/features/` and re-run.",
    "api": ("OpenAPI specs found but `docs/product-profile.md` does not state the product's "
            "surfaces. Fill `Surfaces` — add `api`/`mcp` if the API is a product surface — and re-run."),
}


def _matches(rel: str, globs: tuple) -> bool:
    lowered = rel.lower()
    return any(fnmatch.fnmatch(lowered, g) for g in globs)


def _has_openapi(files, dropped_rels=()) -> bool:
    """True if any KEPT entry is a REAL detected OpenAPI/Swagger spec — signalled by the unique
    title `discovery.openapi_entries()` assigns ("API Reference…"), distinguishing a genuine
    spec from any doc merely keyword-classified into the API section — OR any DROPPED rel (a
    plain string; the audience filter already discarded its file dict) looks like one by name.
    A name-based check is the best signal available for the dropped side."""
    if any(f.get("title", "").startswith("API Reference") for f in files):
        return True
    return any(rel.rsplit("/", 1)[-1].lower().startswith(("openapi", "swagger")) for rel in dropped_rels)


def _api_state(profile: dict, files, dropped=()) -> str:
    """Three-valued — absent is NOT the same as unknown (red-team F6c)."""
    surfaces = profile.get("fields", {}).get("surfaces") or []
    if {"api", "mcp"} & set(surfaces):
        return "required"
    if not surfaces and _has_openapi(files, dropped):
        return "unknown"  # profile never filled in AND real specs exist -> gap, not silence
    return "opt"  # surfaces stated and API not among them -> genuinely omit


def _intro_section(spec: Section, profile: dict) -> dict:
    """Profile-driven, not glob-driven: `spec.globs` is empty by design, so status comes from
    `product_profile.load()`'s own status, not file hits."""
    ok = profile.get("status") == "ok"
    path = profile.get("path")
    return {
        "id": spec.id, "title": spec.title, "required": spec.required,
        "status": "filled" if ok else "gap",
        "entries": [], "sources": [str(path)] if ok and path else [],
        "advisory": None if ok else ADVISORY["intro"],
    }


def _legacy_sections(files) -> list:
    """v1's SECTION_ORDER grouping, unchanged — used for `--audience dev` so render.py produces
    byte-identical output to the pre-v2 script."""
    groups = {}
    for f in files:
        groups.setdefault(f["section"], []).append(f)
    sections = []
    for sec in SECTION_ORDER:
        hits = groups.get(sec)
        if not hits:
            continue
        sections.append({"id": sec, "title": sec, "required": False, "status": "filled",
                          "entries": hits, "sources": [h["rel"] for h in hits], "advisory": None})
    return sections


def readiness(sections) -> dict:
    """Derived preflight summary: gate on the OUTCOME (which required sections are still a gap),
    never on whether some upstream tool has run. Requiring `/tkm:rebuild-spec` up front would be
    a proxy gate — it fills `features` and `screens` but can never fill `intro` (human-entered
    metadata) or `usage` (human-written guide), so it would block the run and still ship a thin
    file. `gaps` carries only ids; each one's fixer is already named in that section's own
    `advisory` (no duplication). Under `--audience dev` no section is required, so a dev run is
    trivially not thin — the contract does not govern it."""
    required = [s for s in sections if s["required"]]
    gaps = [s["id"] for s in required if s["status"] == "gap"]
    return {"required_total": len(required), "filled": len(required) - len(gaps),
            "gaps": gaps, "thin": len(gaps) >= THIN_THRESHOLD}


def build(files, profile: dict, audience: str, dropped=()):
    """(sections, unclaimed). `dropped` (audience_filter's dropped list) lets `_api_state` see
    OpenAPI specs the filter withheld for an unfilled `surfaces` field — the fail-closed drop
    must not also blind the gap-vs-silent-omit signal (F6c)."""
    if audience == "dev":
        return _legacy_sections(files), []

    by_id, claimed = {}, set()
    for sid in MATCH_ORDER:
        spec = _BY_ID[sid]
        hits = [f for f in files if f["rel"] not in claimed and _matches(f["rel"], spec.globs)]
        claimed.update(f["rel"] for f in hits)  # first section wins — no duplicate inlining
        by_id[sid] = (spec, hits)

    unclaimed = [f for f in files if f["rel"] not in claimed]  # kept by audience, matched no section
    by_id["optional"][1].extend(unclaimed)  # folded in, never silently dropped — F6b

    sections = []
    for sid in EMIT_ORDER:  # contract order — F2
        spec, hits = by_id[sid]
        if sid == "intro":
            sections.append(_intro_section(spec, profile))
            continue
        # the openapi-presence probe (_api_state) must see filter-dropped specs too — F6c
        state = _api_state(profile, files, dropped) if spec.required == "surface" else (
            "required" if spec.required else "opt")
        if hits:
            status = "filled"
        elif state == "unknown":
            status = "gap"  # profile unfilled but specs exist — F6c
        elif state == "required":
            status = "gap"
        else:
            status = "omitted"
        sections.append(spec.render(status, hits, ADVISORY.get(sid)))
    return sections, unclaimed
