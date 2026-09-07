#!/usr/bin/env python3
"""Wave TC.2 — test-cases.md deterministic validator.

Checks per-feature test-cases.md per test-cases-researcher-contract.md: TC### regex +
per-feature uniqueness, Type in {UT, IT, UAT}, Traces-to presence + citation-source-family
match, coverage-gap WARN vs technical-spec.md BR/SM/DEC/DISC codes.
Regex only, stdlib only. Exit codes: 0 (no critical), 1 (critical), 2 (internal).
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
from _slug_lib import assert_under, resolve_project_root  # noqa: E402
from _spec_block_lib import DEC_BLOCK_RE, find_blocks  # noqa: E402
from _summary_lib import atomic_write, load_summary, merge_validator_result, recalculate_totals, derive_overall_status  # noqa: E402

VALIDATOR = "test_cases"

TC_CODE_RE = re.compile(r"^TC\d{3}$")
VALID_TYPES = {"UT", "IT", "UAT"}
_TABLE_ROW_RE = re.compile(r"^\|(.+)\|\s*$")
_SEP_ROW_RE = re.compile(r"^\|[\s:|-]+\|\s*$")
# The trailing \b never matches past a slugged code's `_` (e.g. `BR-001_Slug`) — `_` is a
# word char, so \b (a word/non-word transition) fails right where the digits end. That
# silently dropped every slugged citation from both the coverage-gap set-builder and the
# citation-family check below. Note the direction: both consumers use the match to SUPPRESS
# a finding (`gaps = known - traced - noted`; `_citation_family_ok` returns True on a hit),
# so this failed CLOSED — a critical citation_source_mismatch and a phantom coverage gap on
# every correctly-slugged code — not open.
# (?!\d) ("not followed by another digit") is the correct end-of-code anchor: it accepts
# `BR-001_Slug` and still rejects a genuinely longer numeric run (`BR-0012`).
#
# THE FOUR-FAMILY SCOPE IS DELIBERATE — DO NOT WIDEN IT. This pass covers the BEHAVIOR-RULE
# group (BR/SM/DEC/DISC) and nothing else. Widening it to FR/ALG/INT has been tried once and
# REVERTED: it makes `citation_source_mismatch` stop firing, which reads like a fix and is
# not one. Read a firing on an FR/ALG/INT code the other way round — the validator is right
# and THE SPEC IS MISSING A CITATION. Widening the regex here does not add coverage; it
# deletes the finding that was telling you to add one. If the scope itself should genuinely
# change, that is a contract decision (see the coverage-family note below and the
# test-cases researcher contract), not a regex edit.
CODE_FAMILY_RE = re.compile(r"\b(BR|SM|DEC|DISC)-\d{3}(?!\d)")
# Minor fix: bare `Note:1` shaped tokens (no path/extension) previously matched `\S+:\d+`
# and were wrongly accepted as a `file:line` citation. Now requires an actual path shape —
# contains a `/`, OR has a `.<ext>` immediately before the `:<line>`.
FILE_LINE_RE = re.compile(r"(?:\S*/\S+|\S+\.\w+):\d+")
NO_TEST_CASE_RE = re.compile(r"\[NO_TEST_CASE\]", re.IGNORECASE)

# Coverage-gap tracked code families (per plan scope — excludes ALG/INT/FR/SC).
# "Per plan scope" is a decision, not an oversight — see the DO-NOT-WIDEN note above
# CODE_FAMILY_RE for why an FR/ALG/INT citation miss is a spec defect, not a regex bug.
# v27.0.0 (Phase 04): BR/SM detection repointed at _spec_block_lib.find_blocks (single-sourced
# canonical trailing-tag heading parser) instead of a locally re-typed regex. The old local
# BR/SM heading-scan regex (line-anchored on the retired "###/#### <CODE>-NNN_" slug prefix)
# matched only that RETIRED anchored-slug heading form and silently matched ZERO blocks against
# the v27.0.0 canonical heading (`### {plain sentence} (BR-001)`) — a pattern matching nothing
# reports nothing, so the coverage-gap WARN below would have gone quietly dark on any migrated
# technical-spec.md. DEC detection is repointed at the canonical `DEC_BLOCK_RE` for the same
# reason (its old local regex, anchored the same retired way, had the identical defect).
# DISC keeps its own regex here — DISC-### headings never had an anchored-slug form to retire
# (see code-formats.md: format is bare `DISC-###`, no `_Slug` suffix, unaffected by this change).
_DISC_H3_RE = re.compile(r"^###\s+DISC-(\d{3})\b", re.MULTILINE)


def _issue(sev: str, rid: str, file_: str, line: int | None, msg: str) -> dict:
    return {"validator": VALIDATOR, "severity": sev, "rule_id": rid,
            "location": {"file": file_, "line": line}, "message": msg}


def _parse_rows(text: str) -> list[dict]:
    """Extract Test Cases table rows: Test-ID | Type | Given | When | Then | Traces-to.

    I1 fix: rows inside a fenced code block (e.g. a "here's a malformed row to avoid"
    illustration) are skipped — they are never live table content (attack/t7_testcases_fence).
    """
    rows: list[dict] = []
    for i, line, in_fence in iter_lines_with_fence(text):
        if in_fence:
            continue
        m = _TABLE_ROW_RE.match(line.strip())
        if not m or _SEP_ROW_RE.match(line.strip()):
            continue
        cells = [c.strip() for c in m.group(1).split("|")]
        if len(cells) < 6:
            continue
        tc_id = cells[0].strip("{}")
        if not tc_id or tc_id.lower() in ("test-id",):
            continue  # header row or placeholder
        rows.append({"line": i, "tc_id": tc_id, "type": cells[1].strip("{}").upper(),
                     "traces_to": cells[5].strip("{}")})
    return rows


def _known_codes(tech_spec_text: str) -> set[str]:
    codes = {b["code"] for b in find_blocks(tech_spec_text) if b["prefix"] in ("BR", "SM")}
    for line in tech_spec_text.splitlines():
        if DEC_BLOCK_RE.match(line):
            codes.add(line.rsplit("(", 1)[-1].rstrip(") \t"))
    codes |= {f"DISC-{n}" for n in _DISC_H3_RE.findall(tech_spec_text)}
    return codes


def _citation_family_ok(row_type: str, traces_to: str) -> bool:
    # v27.0.0 (Phase 04): the 4-file feature dir (business-context.md/screens.md/edge-cases.md)
    # collapsed into functional-spec.md — UAT's screen/business-context source AND UT/IT's
    # edge-case source are now the SAME single file, so both citation families target it.
    if row_type == "UAT":
        return "functional-spec.md" in traces_to.lower()
    if row_type in ("UT", "IT"):
        return bool(CODE_FAMILY_RE.search(traces_to) or FILE_LINE_RE.search(traces_to)
                    or "functional-spec.md" in traces_to.lower())
    return False  # unknown type already flagged separately


def _rel(p: Path, root: Path) -> str:
    try:
        return str(p.relative_to(root))
    except ValueError:
        return str(p)


def _check_one(tc_path: Path, tech_spec_path: Path, root: Path) -> list[dict]:
    issues: list[dict] = []
    rel = _rel(tc_path, root)

    if not tc_path.is_file():
        # SIDECAR: absence is advisory only, never critical — mirrors the sidecar contract.
        issues.append(_issue("warning", "TestCases.file_missing", rel, None,
                             "test-cases.md not found (sidecar — not a promotion blocker)"))
        return issues

    text = tc_path.read_text(encoding="utf-8", errors="replace")
    rows = _parse_rows(text)
    seen: dict[str, int] = {}

    for row in rows:
        tc_id, line = row["tc_id"], row["line"]
        if not TC_CODE_RE.match(tc_id):
            issues.append(_issue("critical", "TestCases.code_format", rel, line,
                                 f"Test-ID '{tc_id}' does not match ^TC\\d{{3}}$"))
        if tc_id in seen:
            issues.append(_issue("critical", "TestCases.no_dup_tc", rel, line,
                                 f"Duplicate Test-ID '{tc_id}' (first seen at line {seen[tc_id]})"))
        else:
            seen[tc_id] = line

        if row["type"] not in VALID_TYPES:
            issues.append(_issue("critical", "TestCases.type_invalid", rel, line,
                                 f"Type '{row['type']}' not one of UT/IT/UAT"))
            continue  # citation-family check needs a known type

        if not row["traces_to"]:
            issues.append(_issue("critical", "TestCases.traces_missing", rel, line,
                                 f"Test case '{tc_id}' has an empty Traces-to column"))
        elif not _citation_family_ok(row["type"], row["traces_to"]):
            issues.append(_issue("critical", "TestCases.citation_source_mismatch", rel, line,
                                 f"Test case '{tc_id}' (Type={row['type']}) Traces-to "
                                 f"'{row['traces_to']}' does not match the expected citation "
                                 "family (UT/IT: code/file:line/functional-spec.md; "
                                 "UAT: functional-spec.md section)"))

    # Coverage-gap WARN — cross-ref technical-spec.md's BR/SM/DEC/DISC codes.
    if tech_spec_path.is_file():
        known = _known_codes(tech_spec_path.read_text(encoding="utf-8", errors="replace"))
        traced = {m.group(0) for m in CODE_FAMILY_RE.finditer(text)}
        noted = set()
        for ln in text.splitlines():
            if NO_TEST_CASE_RE.search(ln):
                noted |= {m.group(0) for m in CODE_FAMILY_RE.finditer(ln)}
        gaps = sorted(known - traced - noted)
        if gaps:
            issues.append(_issue("warning", "TestCases.coverage_gap", rel, None,
                                 f"{len(gaps)} code(s) with no tracing test case and no "
                                 f"[NO_TEST_CASE] note: {', '.join(gaps)}"))
    return issues


def validate(plan_dir: Path, root: Path, fcodes: list[str] | None) -> dict:
    features_root = plan_dir / "artifacts" / "features"
    per_spec: dict[str, dict] = {}
    if features_root.is_dir():
        targets = fcodes or sorted(d.name for d in features_root.iterdir() if d.is_dir())
        for fcode_dir in targets:
            fdir = features_root / fcode_dir
            tc_path = fdir / "test-cases.md"
            per_spec[fcode_dir] = {"spec_path": _rel(tc_path, root),
                                   "issues": _check_one(tc_path, fdir / "technical-spec.md", root)}
    return {"validator": VALIDATOR, "timestamp": _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "plan_dir": str(plan_dir), "specs": per_spec}


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="rebuild-spec Wave TC.2 test-cases validator")
    p.add_argument("--plan-dir", required=True)
    p.add_argument("--fcodes", default=None, help="Comma-separated fcode dir names to scope (default: all)")
    p.add_argument("--project-root", default=None)
    p.add_argument("--summary-out", default=None)
    args = p.parse_args(argv)
    root = resolve_project_root(args.project_root)

    plan_dir = Path(args.plan_dir).resolve()
    if not plan_dir.is_dir():
        print(f"[ERROR] --plan-dir is not a directory: {plan_dir}", file=sys.stderr)
        return 2
    try:
        assert_under(plan_dir, root)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    fcodes = [f.strip() for f in (args.fcodes or "").split(",") if f.strip()] or None
    try:
        result = validate(plan_dir, root, fcodes)
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] validator crashed: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2, sort_keys=True))
    crit = sum(1 for s in result["specs"].values() for i in s["issues"] if i["severity"] == "critical")

    if args.summary_out:
        sp = Path(args.summary_out).resolve()
        try:
            assert_under(sp.parent, root)
            summary = load_summary(sp, plan_dir.name)
            merge_validator_result(summary, VALIDATOR, result)
            recalculate_totals(summary)
            summary["overall_status"] = derive_overall_status(summary)
            atomic_write(sp, summary)
        except Exception as exc:  # noqa: BLE001
            print(f"[ERROR] failed to merge summary: {exc}", file=sys.stderr)
            return 2

    return 1 if crit else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
