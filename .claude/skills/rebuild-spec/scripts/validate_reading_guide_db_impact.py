#!/usr/bin/env python3
# layout-exempt: rebuild-spec validator — docs/features|screens|generated paths are managed targets
"""v26.0.0 — A3 Source Walkthrough deterministic validator (B4 DB Impact per Event
RETIRED, phase 08, self-sufficiency v27.8).

A3 `## Source Walkthrough` covers BOTH technical-spec.md AND screen-spec spec.md
(the shared check below). B4 `## DB Impact per Event` USED TO be technical-spec.md's
own half of this module (Decision 2); it retired from technical-spec.md this
release along with its `db_impact.*` rule_ids and `check_db_impact()` itself --
`FeatureSpec.retired_section_present` (validate_feature_spec.py) is what now flags a
technical-spec.md still carrying either retired heading, feeding the same C1 reopen
mechanism the other action-thread detectors use. Degradation contract for the A3
half that remains (mirrors validate_feature_screen_link.py's v24 WARN-first shape —
never break un-migrated repos): (1) absent -> WARN `*.pre_migration`; (2) present,
empty body -> CRITICAL `*.malformed`; (3) present, unfilled scaffold placeholder ->
WARN `*.unmapped`. Never added to `_spec_constants.REQUIRED_H2_TECH_THREAD` (Decision
2 — no degradation window there); this validator is the ONLY gate for A3.

Stdlib only. Exit codes: 0 (PASS/WARN), 1 (FAIL critical), 2 (internal).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _md_scan_lib import iter_lines_with_fence  # noqa: E402
from _md_scan_lib import strip_comments as _strip_comments  # noqa: E402
from _slug_lib import assert_under, resolve_project_root  # noqa: E402
from _spec_constants import A3_HEADING  # noqa: E402
from _summary_lib import (  # noqa: E402
    atomic_write, derive_overall_status, load_summary, recalculate_totals,
)

VALIDATOR = "reading_guide_db_impact"

_BRACE_RE = re.compile(r"\{[^{}]*\}")
# `_NA_RE` (the whole-section `N/A` escape) REMOVED (phase-09,
# plans/260824-1846-rebuild-spec-action-self-sufficiency-v27-8): its only importer,
# `_a3_b4_fill_guard_lib.check_b4_row_shape`, was B4-only and retired with that
# step's B4 arm -- `_a3_fill_guard_lib.py` (the A3-only rescope for `a3-screens`)
# never had a B4 table to escape, so it does not need this predicate.


def _issue(sev: str, rid: str, file_path: str, msg: str) -> dict:
    return {"validator": VALIDATOR, "severity": sev, "rule_id": rid,
            "location": {"file": file_path}, "message": msg}

def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""

def _section_body(text: str, heading: str) -> str | None:
    """Body of `heading`'s section, bounded by the next H1/H2 heading or EOF. None if
    absent. C1 fix: walks `iter_lines_with_fence` so the closing boundary is recognized
    ONLY when `in_fence` is False — a fenced `# Note:`/`## X`-shaped line inside the
    section (e.g. a code sample) can no longer truncate the body early and hide a
    trailing unfilled `{placeholder}` scaffold."""
    heading_pat = re.compile(r"^" + re.escape(heading) + r"[ \t]*$")
    boundary_pat = re.compile(r"^#{1,2}[ \t]")
    body_lines: list[str] | None = None
    for _, line, in_fence in iter_lines_with_fence(text):
        if body_lines is None:
            if not in_fence and heading_pat.match(line):
                body_lines = []
            continue
        if not in_fence and boundary_pat.match(line):
            break
        body_lines.append(line)
    return "\n".join(body_lines) if body_lines is not None else None


def check_source_walkthrough(text: str, file_path: str) -> list[dict]:
    """A3 — shared check for technical-spec.md and screen-spec spec.md."""
    body = _section_body(text, A3_HEADING)
    if body is None:
        return [_issue("warning", "reading_guide.pre_migration", file_path,
                        f"{A3_HEADING!r} section missing (pre-migration); run "
                        "run_doc_migrations.py --migrate --only a3-screens")]
    stripped = _strip_comments(body)
    if not stripped.strip():
        return [_issue("critical", "reading_guide.malformed", file_path,
                        f"{A3_HEADING!r} present but body is empty")]
    if _BRACE_RE.search(stripped):
        return [_issue("warning", "reading_guide.unmapped", file_path,
                        f"{A3_HEADING!r} still carries an unfilled `{{...}}` template "
                        "placeholder")]
    return []


# check_db_impact RETIRED (phase 08, self-sufficiency v27.8): B4 (`## DB Impact per
# Event`) left technical-spec.md's target shape this release. Its `db_impact.*`
# rule_ids (`pre_migration`/`malformed`/`unmapped`/`uncited`) retired with it --
# deleted outright, not left as a predicate that can no longer match (see the module
# docstring). `FeatureSpec.retired_section_present` (validate_feature_spec.py) is
# what now flags a technical-spec.md still carrying the `## DB Impact per Event`
# heading.


def validate(root: Path) -> dict:
    """Walk a docs/ or artifacts/ root and aggregate A3 issues for SCREEN specs.

    `features/*/technical-spec.md` is deliberately NOT walked: phase 08 retired
    A3 (`## Source Walkthrough`) from technical-spec.md entirely, so a technical
    spec no longer HAS an A3 section to check. Keeping that loop made
    `reading_guide.pre_migration` fire on every technical-spec of every corpus
    -- measured 43/43 on the real snapshot -- each one telling the operator to
    run `migrate-reading-guide-db-impact.py`, which phase 09 DELETED. A warning
    that fires on correct output and points at a script that no longer exists is
    worse than no warning: it trains operators to ignore the validator.

    Phase 08 requirement 3 called for exactly this ("drop ... the A3 call for
    technical-specs only") and it was missed there; closed here.
    `check_source_walkthrough` itself is UNCHANGED and still shared -- screens
    are its only remaining caller.
    """
    issues: list[dict] = []
    for spec in sorted((root / "screens").glob("*/spec.md")):
        text = _read(spec)
        issues += check_source_walkthrough(text, str(spec))

    critical = sum(1 for i in issues if i["severity"] == "critical")
    warning = sum(1 for i in issues if i["severity"] == "warning")
    return {
        "validator": VALIDATOR,
        "timestamp": _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "root": str(root),
        "status": "FAIL" if critical else ("WARN" if warning else "PASS"),
        "summary": {"critical": critical, "warning": warning},
        "issues": issues,
    }


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        description="rebuild-spec v26 A3 Source Walkthrough validator "
                    "(B4 DB Impact per Event retired, phase 08 self-sufficiency v27.8)")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--docs-root", help="docs/ (or docs/<lang>/) root to validate")
    g.add_argument("--plan-dir", help="plan dir; validates <plan>/artifacts/")
    p.add_argument("--project-root", default=None)
    p.add_argument("--summary-out", default=None)
    args = p.parse_args(argv)
    proj = resolve_project_root(args.project_root)

    root = (Path(args.docs_root) if args.docs_root
            else Path(args.plan_dir) / "artifacts").resolve()
    if not root.is_dir():
        print(f"[ERROR] root is not a directory: {root}", file=sys.stderr)
        return 2
    try:
        assert_under(root, proj)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    try:
        result = validate(root)
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] validator crashed: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2, sort_keys=True))
    if args.summary_out:
        sp = Path(args.summary_out).resolve()
        try:
            assert_under(sp.parent, proj)
            summary = load_summary(sp, root.name)
            summary["validators"][VALIDATOR] = {
                "status": result["status"], "summary": result["summary"],
                "issues": result["issues"],
            }
            recalculate_totals(summary)
            summary["overall_status"] = derive_overall_status(summary)
            atomic_write(sp, summary)
        except Exception as exc:  # noqa: BLE001
            print(f"[ERROR] failed to merge summary: {exc}", file=sys.stderr)
            return 2
    return 1 if result["summary"]["critical"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
