#!/usr/bin/env python3
# layout-exempt: rebuild-spec validator — docs/generated|features paths are managed targets
"""FR-3/FR-6 (phase-01, rebuild-spec 27.11.0) — Traceability Matrix WARN-first validator.

WARN-first by design (NFR): a missing optional column or an unresolvable ID is a WARN,
never a pass failure — this validator never returns a non-zero exit code and never emits
"critical". Two checks:

  1. Re-projection invariant (FR-3): every ID printed in generated/traceability-matrix.md
     must already exist in its source-of-record inventory (screen-list.md/user-stories.md/
     behavior-logic.md/route-list.md/permissions-matrix.md/that feature's own
     test-cases.md). An unresolvable ID WARNs — the matrix is never authoritative for
     existence, only for the thread.
  2. Crosswalk staleness fallback (FR-6/RT-3):
     Both optional passes (`--test-cases`, `--api-contracts`) DO invoke
     `build_navigation.py` at their promote step — FR-6's PREFERRED fix, wired in
     `pipeline-test-cases.md` and `pipeline-api-contracts.md`. The staleness WARN in
     `_crosswalk_staleness_lib.py` remains as a BACKSTOP (hand-run script, interrupted pass,
     or a future pass that forgets the nav call), not as the primary defence it once was.

Stdlib only. Exit 0 always.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _crosswalk_staleness_lib import check_crosswalk_staleness  # noqa: E402
from _lang_lib import resolve_docs_root  # noqa: E402
from _md_scan_lib import mask_fenced, split_table_row  # noqa: E402
from _slug_lib import parse_feature_list_fallback  # noqa: E402
from _summary_lib import atomic_write, derive_overall_status, load_summary, recalculate_totals  # noqa: E402
from _traceability_matrix_lib import parse_feature_details, ID_PATTERNS, inventory  # noqa: E402

VALIDATOR = "traceability_matrix"

_MATRIX_HEADING_RE = re.compile(r"^#+\s*Matrix\s*$", re.IGNORECASE)


def _issue(sev: str, rid: str, msg: str) -> dict:
    return {"validator": VALIDATOR, "severity": sev, "rule_id": rid, "message": msg}


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def parse_matrix_table(text: str) -> tuple[list[str], list[dict]]:
    """Return (column headers, rows) from the '## Matrix' table. Best-effort."""
    lines = mask_fenced(text).splitlines()
    start = None
    for i, ln in enumerate(lines):
        if _MATRIX_HEADING_RE.match(ln.strip()):
            start = i + 1
            break
    if start is None:
        return [], []
    table: list[str] = []
    seen = False
    for ln in lines[start:]:
        s = ln.strip()
        if s.startswith("|"):
            table.append(s)
            seen = True
        elif seen:
            break
    if len(table) < 2:
        return [], []
    header = split_table_row(table[0])
    rows = []
    for raw in table[2:]:
        cells = split_table_row(raw)
        if len(cells) != len(header):
            continue
        rows.append(dict(zip(header, cells)))
    return header, rows


def _cell_ids(cell: str) -> list[str]:
    cell = (cell or "").strip()
    if not cell or cell == "—":
        return []
    return [c.strip() for c in cell.split(",") if c.strip()]


_COL_FAMILY = {
    "SCR###": "scr", "US###": "us", "BL###": "bl", "ROUTE###": "route",
    "PERM###": "perm", "TC###": "tc",
}


def validate_reprojection(docs_root: Path) -> list[dict]:
    """FR-3 — every printed ID must resolve in its source-of-record artifact."""
    issues: list[dict] = []
    matrix_path = docs_root / "generated" / "traceability-matrix.md"
    if not matrix_path.is_file():
        issues.append(_issue("warning", "TraceabilityMatrix.missing",
                             "generated/traceability-matrix.md not found"))
        return issues

    header, rows = parse_matrix_table(_read(matrix_path))
    if not header:
        issues.append(_issue("warning", "TraceabilityMatrix.unparseable",
                             "'## Matrix' table not found or unparseable"))
        return issues

    # An all-header, zero-row matrix over a corpus that HAS features is the exact failure
    # this artifact exists to prevent: it reads as authoritative absence ("this project has
    # no traceable features") when the truth is that the join found nothing to join.
    # Real cause seen in practice: the row set comes from feature-list.md's hierarchy table
    # via FEATURE_LIST_ROW_RE, which requires a leading `| F###_Slug |` cell. A feature-list
    # whose table carries a bare `| F### |` first cell parses to zero features while its
    # '## Feature Details' sections still list every one of them — so the matrix renders
    # empty and, before this check, validated clean.
    if not rows:
        fl_features = len(parse_feature_details(_read(
            docs_root / "generated" / "feature-list.md")))
        if fl_features:
            issues.append(_issue(
                "warning", "TraceabilityMatrix.empty_but_features_exist",
                f"matrix has 0 rows but feature-list.md describes {fl_features} feature(s) — "
                "the F### row set is parsed from the hierarchy table's leading `| F###_Slug |` "
                "cell; a bare `| F### |` cell yields an empty matrix that reads as "
                "authoritative absence"))
        return issues

    inventories = {
        "scr": inventory(_read(docs_root / "generated" / "screen-list.md"), "scr"),
        "us": inventory(_read(docs_root / "generated" / "user-stories.md"), "us"),
        "bl": inventory(_read(docs_root / "generated" / "behavior-logic.md"), "bl"),
        "route": inventory(_read(docs_root / "generated" / "route-list.md"), "route"),
        "perm": inventory(_read(docs_root / "generated" / "permissions-matrix.md"), "perm"),
    }
    feature_slugs = {f["fcode"]: f["slug"]
                     for f in parse_feature_list_fallback(docs_root / "generated" / "feature-list.md")}

    # A column this validator does not know about is unverifiable, not absent. The
    # reprojection loop below walks _COL_FAMILY (the registry), not the matrix header, so a
    # column retired from the registry while still present in a consumer's generated matrix
    # would otherwise be skipped in silence — checked by nothing, reported by nothing. That
    # is exactly what happened to JOB### in 28.0.0, and no migration ships to remove it.
    # Reported once per matrix, not once per row.
    unknown_cols = sorted(
        {c for row in rows for c in row} - set(_COL_FAMILY) - {"F###"})
    for col in unknown_cols:
        issues.append(_issue(
            "warning", "TraceabilityMatrix.unknown_column",
            f"column '{col}' is not a known ID family — it is re-projected by nothing and "
            f"verified by nothing. Retired in a newer rebuild-spec? Drop the column."))

    for row in rows:
        fcode = row.get("F###", "").strip()
        for col, family in _COL_FAMILY.items():
            if col not in row:
                continue
            ids = _cell_ids(row[col])
            if not ids:
                continue
            if family == "tc":
                slug = feature_slugs.get(fcode)
                tc_inv = (inventory(_read(docs_root / "features" / slug / "test-cases.md"), "tc")
                          if slug else set())
                for tc in ids:
                    if tc not in tc_inv:
                        issues.append(_issue(
                            "warning", "TraceabilityMatrix.tc_unresolved",
                            f"{fcode}: '{tc}' not found in features/{slug or '?'}/test-cases.md"))
                continue
            known = inventories.get(family)
            if known is None:
                continue
            for code in ids:
                if not ID_PATTERNS[family].fullmatch(code) or code not in known:
                    issues.append(_issue(
                        "warning", f"TraceabilityMatrix.{family}_unresolved",
                        f"{fcode}: '{code}' not found in its source-of-record artifact"))
    return issues


def main() -> int:
    p = argparse.ArgumentParser(description="WARN-first validator for traceability-matrix.md")
    p.add_argument("--docs-root", default=None)
    p.add_argument("--summary-out", default=None)
    args = p.parse_args()

    docs_root = Path((args.docs_root or resolve_docs_root(None))).resolve()
    issues = validate_reprojection(docs_root) + check_crosswalk_staleness(docs_root)
    warning = sum(1 for i in issues if i["severity"] == "warning")
    result = {
        "validator": VALIDATOR,
        "timestamp": _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "WARN" if warning else "PASS",
        "summary": {"critical": 0, "warning": warning},
        "issues": issues,
    }
    print(json.dumps(result, indent=2, sort_keys=True))

    if args.summary_out:
        sp = Path(args.summary_out).resolve()
        try:
            summary = load_summary(sp, docs_root.name)
            summary["validators"][VALIDATOR] = {
                "status": result["status"], "summary": result["summary"], "issues": issues,
            }
            recalculate_totals(summary)
            summary["overall_status"] = derive_overall_status(summary)
            atomic_write(sp, summary)
        except OSError as exc:
            print(f"[ERROR] failed to merge summary: {exc}", file=sys.stderr)
    return 0  # WARN-first — never a pass failure (NFR)


if __name__ == "__main__":
    sys.exit(main())
