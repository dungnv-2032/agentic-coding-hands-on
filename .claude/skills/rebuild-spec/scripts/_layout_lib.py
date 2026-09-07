"""Shared layout constants for the v4 docs layout.

Single source of truth for the draft-artifact → promoted-path map, imported by
promote_drafts.py. Stdlib only.

v4 layout:
  docs/system/      ← system-overview, permissions, glossary
  docs/generated/   ← route-list, api-map, entities(data-model), screen-list,
                       screen-flow, behavior-logic, user-stories, feature-list
  docs/flows/       ← all flows/*.md
  docs/features/{slug}/ ← 4 per-feature files
  docs/screens/{SCR}/   ← screen specs
"""
# layout-exempt: rebuild-spec script — all docs/system|features|generated|flows paths are this skill's own managed targets
from __future__ import annotations

# ---------------------------------------------------------------------------
# v4 canonical layered paths per docs-canonical-mapping.md
# Keys are draft artifact filenames; values are relative paths under docs/.
# ---------------------------------------------------------------------------
LAYERED_PATH_MAP: dict[str, str] = {
    "system-overview.md": "system/overview.md",
    "architecture.md": "system/architecture.md",
    "permissions.md": "system/permissions.md",
    "glossary.md": "system/glossary.md",
    "route-list.md": "generated/route-list.md",
    "api-map.md": "generated/api-map.md",
    "api-contracts.md": "generated/api-contracts.md",
    "permissions-matrix.md": "generated/permissions-matrix.md",
    "data-model.md": "generated/entities.md",
    "screen-list.md": "generated/screen-list.md",
    "screen-flow.md": "generated/screen-flow.md",
    "behavior-logic.md": "generated/behavior-logic.md",
    "user-stories.md": "generated/user-stories.md",
    "feature-list.md": "generated/feature-list.md",
    # Stack-specific (extractor-digest-derived) core artifacts — Delphi/Oracle et al.
    "crud-matrix.md": "generated/crud-matrix.md",
    "db-objects.md": "generated/db-objects.md",
    # v27.11.0 W6 traceability matrix. DERIVED, not drafted-then-promoted:
    # build_traceability_matrix.py writes it straight into docs/generated/ by re-projecting
    # already-promoted artifacts. Registered here for path resolution + README-index
    # consistency ONLY — deliberately absent from CORE_ARTIFACTS and every --scope list in
    # promote_drafts.py, which iterate explicit artifact lists, never LAYERED_PATH_MAP.keys().
    "traceability-matrix.md": "generated/traceability-matrix.md",
}
