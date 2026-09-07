#!/usr/bin/env python3
"""Audience filter (`--audience user|dev`) — end-user content vs build-side content.

The sharp line: exclude HOW the product is built, include HOW the product is used. Matching is
`fnmatch`-style glob against the lowercased repo-relative path throughout (red-team F12 — NOT
`discovery.section_for`'s exact-token scheme, which has no wildcard support and cannot express
`docs/user-guide/**`).

`--audience dev` disables the filter entirely: `kept = all`, `dropped = []` — v1's full file
set, unchanged.

A file matching NO pattern drops fail-closed (red-team F6a): an unknown doc is more likely
build-side than user-facing, and a wrong drop is visible and recoverable (`dropped_unmatched`)
while a wrong include would silently poison the deliverable. Every dropped file — matched or
unmatched — is reported so nothing disappears without a name.

`deploy*`/`hosting*` are dropped under `user` and kept under `dev`, unconditionally — there is
no self-hosted carve-out (red-team F13): no such value exists in the frozen `surfaces`
vocabulary (`web, extension, desktop, mobile, cli, api, mcp`).
"""
import fnmatch

from content_contract import (API_GLOBS, FEATURES_GLOBS, INSTALL_GLOBS, OPTIONAL_GLOBS,
                              SCREENS_GLOBS, USAGE_GLOBS)

# "ci"/"cicd"/"pipeline" get narrower, separator-anchored patterns on purpose: a bare "*ci*"
# would false-positive on e.g. "docs/policies.md" (substring "ci" inside "poli-ci-es"), silently
# dropping content the Optional contract section explicitly wants kept.
DROP_PATTERNS = (
    "*contributing*", "*dev-setup*", "*development*",
    "*techstack*", "*tech-stack*", "*architecture*",
    "*/ci.*", "*/ci/*", "ci.*", "*-ci.*", "*_ci.*", "*cicd*", "*pipeline*",
    "*repo-layout*",
    "docs/system/**", "docs/flows/**", "docs/decisions/**", "docs/screens/**",  # F7: dev-coded specs
    "deploy*", "*/deploy*", "hosting*", "*/hosting*",
    "docs/generated/**",
)

# Reuses the CONTRACT's own glob sets so a doc the contract can legitimately claim is never
# dropped by the audience filter before content_contract.build() ever sees it. KEEP is tested
# BEFORE DROP in apply(), which is what carves `docs/generated/{feature-list,screen-list}.md`
# out of the blanket `docs/generated/**` drop above — the two named inventories are end-user
# material; the rest of that directory is dev-derived.
KEEP_PATTERNS = INSTALL_GLOBS + USAGE_GLOBS + SCREENS_GLOBS + FEATURES_GLOBS + OPTIONAL_GLOBS

# Kept ONLY when the product declares an api/mcp surface — an unfilled or api-less `surfaces`
# drops these, fail-closed on disclosure (raw OpenAPI specs, generated api/route maps, docs/api
# guides, MCP guide docs).
_SURFACE_CONDITIONAL = ("docs/generated/api-map.md", "docs/generated/route-list.md") + API_GLOBS


def _match_any(rel_lower: str, patterns: tuple) -> bool:
    return any(fnmatch.fnmatch(rel_lower, p) for p in patterns)


def _surfaces_declare_api(profile: dict) -> bool:
    surfaces = (profile or {}).get("fields", {}).get("surfaces") or []
    return bool({"api", "mcp"} & set(surfaces))


def apply(files, audience: str, profile: dict):
    """(kept, dropped, dropped_unmatched). `dropped`/`dropped_unmatched` are lists of `rel`
    strings (not file dicts) — every one of them is reported in the manifest, matched or not."""
    if audience == "dev":
        return list(files), [], []

    kept, dropped, dropped_unmatched = [], [], []
    for f in files:
        rel_lower = f["rel"].lower()
        if _match_any(rel_lower, _SURFACE_CONDITIONAL):
            if _surfaces_declare_api(profile):
                kept.append(f)
            else:
                dropped.append(f["rel"])
            continue
        if _match_any(rel_lower, KEEP_PATTERNS):
            kept.append(f)
            continue
        if _match_any(rel_lower, DROP_PATTERNS):
            dropped.append(f["rel"])
            continue
        dropped.append(f["rel"])
        dropped_unmatched.append(f["rel"])
    return kept, dropped, dropped_unmatched
