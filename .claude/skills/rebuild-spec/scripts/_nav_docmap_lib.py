"""Document Map — FR-1 crosswalk renderer (rebuild-spec 27.11.0, plan phase-01).

Presence-driven, waterfall-ordered (Requirements -> External Design -> Internal Design ->
Test Spec) 4-bucket index, spliced into the generated zone of the top-level docs/README.md
(or docs/<primary>/README.md in per-lang mode) alongside the existing numbered reading-order
table. Kept in its own module — not inlined into build_navigation.py — to hold that file to
the same < 200-LOC discipline every other nav concern in this skill already follows
(_nav_lib.py, _nav_index.py, _nav_feature_lib.py, _nav_aggregate_lib.py, ...).

Re-projection only: scans docs/ for on-disk presence and links to files/dirs that already
exist. Never invents an artifact, never lists an absent one — an absent optional pass
(--api-contracts, --test-cases) simply omits its row.

Prose (bucket labels, "who reads it" lines, per-entry one-liners) is localized via
_nav_strings.get_strings(lang)["document_map"]; structure (bucket order, entry -> on-disk
target mapping) is language-independent and lives here, mirroring the READING_ORDER/locale
split already used by _nav_strings.py / _nav_strings_<lang>.py.

Stdlib only.
"""
from __future__ import annotations

import glob as _glob
import os

from _nav_lib import GEN_END
from _nav_strings import get_strings

# Waterfall order (R6 decision — neutral labels; structure carries the "bài bản" signal,
# not the vocabulary). Fixed, language-independent — never reordered per locale.
_BUCKET_ORDER = ["requirements", "external_design", "internal_design", "test_spec"]

# bucket -> [(entry_key, kind, target-relative-to-docs_root)], per the FR-1 table.
# kind "file"  -> presence = os.path.isfile(docs_root/target)
# kind "glob"  -> presence = any(glob(docs_root/target)); links to the directory before
#                 the first "*" segment (always "features/" for this table).
_BUCKET_ENTRIES: dict[str, list[tuple[str, str, str]]] = {
    "requirements": [
        ("functional_spec", "glob", "features/*/functional-spec.md"),
    ],
    "external_design": [
        ("screen_list", "file", "generated/screen-list.md"),
        ("screen_flow", "file", "generated/screen-flow.md"),
        ("entities", "file", "generated/entities.md"),
        ("api_map", "file", "generated/api-map.md"),
        ("feature_list", "file", "generated/feature-list.md"),
        ("architecture", "file", "system/architecture.md"),
    ],
    "internal_design": [
        ("technical_spec", "glob", "features/*/technical-spec.md"),
        ("behavior_logic", "file", "generated/behavior-logic.md"),
        ("crud_matrix", "file", "generated/crud-matrix.md"),
        ("api_contracts", "file", "generated/api-contracts.md"),
    ],
    "test_spec": [
        ("test_cases", "glob", "features/*/test-cases.md"),
    ],
}

# The one cross-cutting artifact this map points to but does not itself bucket (FR-3) — it
# threads all four tiers at once, so it earns a pointer line rather than a 5th bucket.
TRACEABILITY_MATRIX_REL = "generated/traceability-matrix.md"


def _entry_present(docs_root: str, kind: str, target: str) -> bool:
    if kind == "file":
        return os.path.isfile(os.path.join(docs_root, target))
    return bool(_glob.glob(os.path.join(docs_root, target)))


def _entry_link(kind: str, target: str) -> str:
    return target.split("*")[0] if kind == "glob" else target


def build_document_map(docs_root: str, lang: str | None) -> str:
    """Render the '## Document Map' block, or '' when nothing is present yet.

    Presence-driven at every level: a bucket with zero present entries is omitted
    entirely; an absent optional artifact simply never gets a row (never a broken
    link) — FR-1 / NFR. Never touches disk beyond read-only existence checks.
    """
    s = get_strings(lang)
    dm = s.get("document_map")
    if not dm:
        return ""
    lines = [f"## {dm['heading']}", "", dm["intro"]]
    rendered_any = False
    for bucket_key in _BUCKET_ORDER:
        bucket = dm["buckets"].get(bucket_key, {})
        rows = []
        for entry_key, kind, target in _BUCKET_ENTRIES[bucket_key]:
            if not _entry_present(docs_root, kind, target):
                continue
            link = _entry_link(kind, target)
            desc = dm["entries"].get(entry_key, entry_key)
            rows.append(f"- [{link}]({link}) — {desc}")
        if not rows:
            continue
        rendered_any = True
        lines += ["", f"### {bucket.get('label', bucket_key)}", "", bucket.get("who", ""), "", *rows]
    if not rendered_any:
        return ""
    if os.path.isfile(os.path.join(docs_root, TRACEABILITY_MATRIX_REL)):
        pointer = dm.get("trace_pointer", "")
        if pointer:
            lines += ["", pointer.format(link=TRACEABILITY_MATRIX_REL)]
    return "\n".join(lines)


def insert_document_map(content: str, docs_root: str, lang: str | None) -> str:
    """Splice the Document Map block into `content` right before GEN_END.

    No-op (returns content unchanged) when there is nothing to show — an all-empty
    corpus never gets a dangling '## Document Map' heading with zero rows under it.
    `.replace(..., 1)` targets the FIRST GEN_END, which is always the real generated-zone
    close (a hand-written user tail below it is never mistaken for a second one, since the
    tail only begins after that first marker).
    """
    block = build_document_map(docs_root, lang)
    if not block:
        return content
    return content.replace(GEN_END, block + "\n\n" + GEN_END, 1)
