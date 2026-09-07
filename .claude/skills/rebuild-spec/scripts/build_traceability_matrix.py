#!/usr/bin/env python3
# layout-exempt: rebuild-spec generator — all docs/generated|features paths here are this
# skill's own output targets or read sources.
"""FR-3 (phase-01, rebuild-spec 27.11.0) — Traceability Matrix generator.

Emits `docs/generated/traceability-matrix.md`: one row per `F###` threading it to every
other ID family (SCR###/US###/BL###/ROUTE###/PERM###, plus optional TC###). This is
a RE-PROJECTION, not a re-detection — every cell is read from an existing source-of-record
artifact under docs/, never from source code, and never invents an ID. See
_traceability_matrix_lib.py for the join graph and the fence/comment-aware parsers.

Deterministic, stdlib only. Exit 0 always (advisory generator, mirrors build_navigation.py);
WARN-first cross-checking against the source-of-record inventories is
validate_traceability_matrix.py's job, not this script's.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lang_lib import resolve_docs_root  # noqa: E402
from _nav_components_io import _atomic_write  # noqa: E402
from _path_lib import _resolve_guarded  # noqa: E402
from _slug_lib import parse_feature_list_fallback  # noqa: E402
from _traceability_matrix_lib import (  # noqa: E402
    inventory, parse_feature_details, parse_route_owners,
)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _cell(ids: list[str]) -> str:
    return ", ".join(ids) if ids else "—"


def build_rows(docs_root: Path) -> tuple[list[dict], bool]:
    """Return (rows, test_cases_present)."""
    flist_path = docs_root / "generated" / "feature-list.md"
    features = parse_feature_list_fallback(flist_path)
    details = parse_feature_details(_read(flist_path))
    route_owners = parse_route_owners(_read(docs_root / "generated" / "route-list.md"))

    features_dir = docs_root / "features"
    tc_present = features_dir.is_dir() and any(features_dir.glob("*/test-cases.md"))

    rows: list[dict] = []
    for feat in features:
        fcode, slug = feat["fcode"], feat["slug"]
        det = details.get(fcode, {"scr": [], "us": [], "bl": [], "perm": []})
        row = {
            "fcode": fcode,
            "scr": det["scr"],
            "us": det["us"],
            "bl": det["bl"],
            "route": route_owners.get(fcode, []),
            "perm": det["perm"],
        }
        if tc_present:
            tc_path = features_dir / slug / "test-cases.md"
            row["tc"] = sorted(inventory(_read(tc_path), "tc")) if tc_path.is_file() else []
        rows.append(row)
    return rows, tc_present


def render(project_name: str, scope: str, rows: list[dict], tc_present: bool,
           timestamp: str) -> str:
    cols = ["F###", "SCR###", "US###", "BL###", "ROUTE###", "PERM###"]
    if tc_present:
        cols.append("TC###")

    lines = [
        "# Traceability Matrix", "",
        f"**Project**: {project_name}",
        f"**Generated**: {timestamp}",
        f"**Scope**: {scope}", "",
        "> **Re-projection, not detection.** Every ID below already exists in its "
        "source-of-record artifact — this file invents nothing, and is never the first "
        "place an ID appears. Source of record per column: `F###` <- "
        "`generated/feature-list.md`; `SCR###` <- `generated/screen-list.md`; `US###` <- "
        "`generated/user-stories.md`; `BL###` <- `generated/behavior-logic.md`; "
        "`ROUTE###` <- `generated/route-list.md` (`Owner F###` column); `PERM###` <- "
        "`generated/permissions-matrix.md`"
        + (" ; `TC###` <- `features/*/test-cases.md`" if tc_present else "")
        + ".", "",
    ]
    if tc_present:
        lines += [
            "> **Note:** `TC###` resets per feature (test-cases.md's own scope is the "
            "reset boundary) — the same code appearing in two rows is not a collision.",
            "",
        ]
    lines += [
        "---", "", "## Matrix", "",
        f"| {' | '.join(cols)} |",
        f"|{'---|' * len(cols)}",
    ]
    for row in rows:
        cells = [row["fcode"], _cell(row["scr"]), _cell(row["us"]), _cell(row["bl"]),
                 _cell(row["route"]), _cell(row["perm"])]
        if tc_present:
            cells.append(_cell(row.get("tc", [])))
        lines.append(f"| {' | '.join(cells)} |")
    lines += [
        "", "---", "", "## Cross-Reference Validation", "",
        "- [x] Every `SCR###`/`US###`/`BL###`/`PERM###` cell is projected from "
        "`generated/feature-list.md`'s own per-feature `**Related X**:` bullets",
        "- [x] Every `ROUTE###` cell is projected from `generated/route-list.md`'s own "
        "`Owner F###` column",
        "- [x] No ID in this matrix is invented — see `validate_traceability_matrix.py` "
        "for the WARN-first cross-check against each source-of-record inventory",
    ]
    if tc_present:
        lines.append("- [x] Every `TC###` cell is read from that feature's own "
                     "`test-cases.md` (never another feature's)")
    return "\n".join(lines) + "\n"


def run(docs_root_arg: str | None, project_name: str, scope: str) -> int:
    docs_root = Path(os.path.realpath(os.path.abspath(
        docs_root_arg or resolve_docs_root(None))))
    if not docs_root.is_dir():
        print(f"[WARN] docs root not found: {docs_root}", file=sys.stderr)
        return 0
    if not (docs_root / "generated" / "feature-list.md").is_file():
        print("[WARN] generated/feature-list.md not found — nothing to re-project; "
              "skipping traceability-matrix.md", file=sys.stderr)
        return 0

    rows, tc_present = build_rows(docs_root)
    timestamp = _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    content = render(project_name, scope, rows, tc_present, timestamp)

    if content.count("\n") > 800:
        print("[WARN] traceability-matrix.md exceeds 800 lines — see "
              "references/artifact-sharding.md", file=sys.stderr)

    out_dir = docs_root / "generated"
    out_dir.mkdir(parents=True, exist_ok=True)
    raw = str(out_dir / "traceability-matrix.md")
    try:
        guarded = _resolve_guarded(raw, str(docs_root))
    except ValueError as e:
        print(f"[ERROR] write-safety violation: {e}", file=sys.stderr)
        return 0
    try:
        _atomic_write(guarded, content)
    except OSError as e:
        print(f"[ERROR] cannot write traceability-matrix.md: {e}", file=sys.stderr)
    return 0


def main() -> None:
    p = argparse.ArgumentParser(
        description="Build docs/generated/traceability-matrix.md (F###-keyed re-projection)."
    )
    p.add_argument("--docs-root", default=None,
                   help="Path to docs root (default: resolved via _lang_lib)")
    p.add_argument("--project-name", default="Project")
    p.add_argument("--scope", default="Full codebase")
    args = p.parse_args()
    sys.exit(run(args.docs_root, args.project_name, args.scope))


if __name__ == "__main__":
    main()
