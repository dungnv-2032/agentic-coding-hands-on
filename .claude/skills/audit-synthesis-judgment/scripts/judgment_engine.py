#!/usr/bin/env python3
"""Engine 3 — adversarial judgment residue (WARN-only).

The genuinely-subjective residue neither deterministic coverage nor IPE conformance can settle:
inference validity ("why"/"so that"), boundary naming, granularity, and capability intent.
Judged by LLM subagents whose findings must survive a refutation pass. This Python plumbs the
deterministic scaffolding around those LLM judges, in two modes:

  prepare  — extract judge CANDIDATES from the artifacts, each pinned to a computed anchor, plus the
             deterministic granularity-outlier stat. Emits candidates JSON. (No LLM; testable.)
  assemble — read the judged candidates back (verdicts + refutations from the LLM judges) → apply the
             anchor gate + refutation-survival + completion accounting → Engine-3 findings JSON.

The LLM orchestrator (see references/pipeline.md + judgment-rubric.md) runs the judges/refuters
BETWEEN prepare and assemble. Engine 3 emits WARN only — NEVER FAIL, NEVER an Engine-1 count.

Stdlib only. Exit 0 always.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _citation_lib import read_text_safe, resolve_docs_root, resolve_project_root  # noqa: E402
import _cap_map_lib as cap_map  # noqa: E402
import _granularity_lib as gran  # noqa: E402
import _ipe_parse_lib as ipe_parse  # noqa: E402
import locate_synthesis_artifacts as locator  # noqa: E402

# Blast-radius keywords: a WARN touching one of these domains is high-severity (verdict-taxonomy.md).
_BLAST_RADIUS_RE = re.compile(
    r"\b(auth|authz|authn|permission|role|rbac|acl|login|password|token|secret|"
    r"payment|money|price|billing|invoice|charge|refund|"
    r"delete|drop|purge|mutation|persist|encrypt|security)\b", re.I)


def _severity(dimension: str, text: str) -> str:
    """Blast radius, not taste. High only when the WARN touches an auth/data/security/money domain.

    [SA-4] `text` here is whatever the CALLER decided is safe to scan — `assemble()` passes
    `cand.get("severity_text") or cand.get("text", "")`, so `capability-intent` candidates (which
    set `severity_text`) are scanned on a Python-composed string of claimed codes + their twin-spec
    declaration lines, never on the judge-visible prose the assessed party authored. The three
    other dimensions set no `severity_text`, so the `or` falls through to `text` exactly as
    before — byte-identical behaviour, not a refactor of this function's own signature.
    """
    if _BLAST_RADIUS_RE.search(text or ""):
        return "high"
    if dimension in ("inference-validity", "granularity", "capability-intent"):
        return "medium"
    return "low"
_SO_THAT_RE = re.compile(r"so that\s+(.+?)(?:\.|$)", re.I)


# ---------------------------------------------------------------- prepare
def _extract_inference_candidates(artifacts: list[dict]) -> list[dict]:
    cands: list[dict] = []
    idx = 0
    for art in artifacts:
        if not art.get("present") or not art.get("path"):
            continue
        kind = art["kind"]
        if kind != "user-stories":
            continue
        read = read_text_safe(Path(art["path"]))
        if read is None:
            continue
        text, _ = read
        for m in _SO_THAT_RE.finditer(text):
            benefit = m.group(1).strip()
            if len(benefit) > 8:
                cands.append({
                    "id": f"inference-{idx}", "dimension": "inference-validity",
                    "target": kind, "text": f"so that {benefit}",
                    "anchor": "US benefit clause — judge whether the claimed benefit is traceable to evidence"})
                idx += 1
    return cands


def _extract_naming_candidates(artifacts: list[dict]) -> list[dict]:
    cands: list[dict] = []
    for art in artifacts:
        if art.get("kind") != "user-stories" or not art.get("present") or not art.get("path"):
            continue
        read = read_text_safe(Path(art["path"]))
        if read is None:
            continue
        parsed = ipe_parse.parse(read[0])
        for code, title in sorted(parsed.us_titles.items()):
            cands.append({
                "id": f"naming-{code}", "dimension": "naming", "target": code, "text": title,
                "anchor": "IPE Step-4 anti-CRUD — judge only genuinely-ambiguous titles "
                          "(clear violations already deterministic in Engine 2)"})
    return cands


def _feature_metrics(artifacts: list[dict]) -> tuple[dict[str, float], int]:
    """Per-feature granularity metric: `max(US claimed by any single § 2 CAP row)`.

    NOT raw US count, NOT CAP-row count — deliberately re-axised off the old
    Source-citation-count metric (phase 09, capability-map plan):
      - raw US count reproduces the distribution rebuild-spec's `cap.analysis_required`
        already checks deterministically (phase 06) — a second copy of one signal, no new
        information;
      - CAP-row count alone says nothing about coarseness: 10 US spread over 5 rows is a
        well-partitioned feature, 10 US crammed into 1 row is not — row COUNT can't tell them
        apart, only the WIDEST row can;
      - `max(US per CAP row)` measures what Engine 3 uniquely adds: how coarse the widest
        capability in this feature is, relative to the corpus. Do not simplify this back to a
        plain US or CAP-row count — `TestFeatureMetrics.test_per_cap_not_per_feature` in
        test_judgment_engine.py fails against exactly that simplification.
    The old citation-count metric measured spec LENGTH, which the pipeline itself normalises
    (maxLoc, compaction) — it returned 0 outliers across a real 66-feature corpus, a dead
    backstop measuring document uniformity, not scope breadth.

    [AD-3] A feature whose § 2 rows all claim zero US (the post-`cap-map`/pre-fill window,
    § 2 widened but not yet filled) is OMITTED from the returned metrics, never recorded as a
    `0` — a uniform-zero distribution yields 0 outliers, which is the exact failure this phase
    exists to fix, in a new costume. The caller uses the second return value (count of
    `functional-spec.md` artifacts actually present) to word the SKIPPED note differently for
    "no § 2 found" vs. "found but every row's claim cells are empty".

    Reads `functional-spec.md` via the locator's `artifacts` list (registered in
    `_SCOPE_ARTIFACTS`, phase 09) — never a raw `docs_root.glob(...)` — so a non-`en`
    primary-language corpus resolves the same way every other artifact does.
    """
    metrics: dict[str, float] = {}
    n_present = 0
    for art in artifacts:
        if art.get("kind") != locator.KIND_FEATURE_SPEC_FUNCTIONAL or not art.get("present") \
                or not art.get("path"):
            continue
        n_present += 1
        read = read_text_safe(Path(art["path"]))
        if read is None:
            continue
        rows = cap_map.us_claim_sets(read[0])
        if not rows:
            continue  # no § 2 table, or a header-only § 2 with zero data rows
        widest = max(len(s) for s in rows)
        if widest == 0:
            continue  # [AD-3] widened but unfilled -> OMIT, never record as 0
        metrics[Path(art["path"]).parent.name] = float(widest)
    return metrics, n_present


def _extract_granularity_candidates(artifacts: list[dict], docs_root: Path) -> tuple[list[dict], str, str]:
    """Granularity candidates + the non-silent completion status (phase 09).

    Before this phase: an absent/unparseable § 2 silently returned `[]` — indistinguishable
    from "ran clean, nothing to flag". `granularity_status` gives that silence one authoritative
    answer: `"OK"` (>= 3 features yielded a metric, MAD ran) or `"SKIPPED"` (fewer than 3 did,
    whether from absence or an unfilled corpus) — see `_feature_metrics` docstring for the
    OMIT-not-zero rule that makes the unfilled case reach SKIPPED instead of a uniform-zero PASS.
    """
    metrics, n_present = _feature_metrics(artifacts)
    search_path = str(docs_root / "features" / "*" / "functional-spec.md")
    if len(metrics) < 3:
        if n_present == 0:
            note = f"no functional-spec.md located under {search_path} — § 2 granularity axis did not run"
        else:
            note = (f"{n_present} functional-spec.md found under {search_path} but fewer than 3 "
                     "yielded a usable § 2 metric — § 2 is widened but its User Stories cells are "
                     "unfilled; run the fill (not the migration) then re-audit")
        return [], "SKIPPED", note
    stat = gran.find_outliers(metrics)
    note = f"granularity ran on {len(metrics)} features (median {stat['median']}, mad {stat['mad']})"
    candidates = [{
        "id": f"granularity-{o['feature']}", "dimension": "granularity", "target": o["feature"],
        "text": f"{o['feature']} is a {o['direction']} outlier ({o['value']} vs median {stat['median']})",
        "anchor": o["anchor"],
    } for o in stat["outliers"]]
    return candidates, "OK", note


# ---------------------------------------------------------- capability-intent (phase 10)
_CAP_INTENT_MIN_US = 3


def _capability_intent_anchor(row_id: str, resolved_titles: list[tuple[str, str]]) -> str:
    """[Req #2] The computed fact, built BEFORE any model sees the candidate (Iron Law #2). Pure
    Python from the claimed title set alone — the free-text justification line
    `_capability_intent_text` places in judge-visible `text` never reaches this function; a unit
    test asserts this statically, by source inspection, not merely against one fixture."""
    title_list = "; ".join(f"'{t}'" for _, t in resolved_titles)
    return (f"{row_id} claims {len(resolved_titles)} user-story titles: {title_list} "
            f"(computed from § 2 User Stories column + § 7 headings)")


def _capability_intent_text(resolved_titles: list[tuple[str, str]], rationale: str | None) -> str:
    """[Req #3] Judge-visible EVIDENCE only — decides nothing on its own. The rationale line, when
    present, is quoted here and ONLY here (never in the anchor, never in `severity_text`)."""
    title_list = "; ".join(f"'{t}'" for _, t in resolved_titles)
    text = f"Claimed user stories: {title_list}."
    if rationale:
        text += f" **Single-capability rationale:** {rationale}"
    return text


def _declaration_line(tech_lines: list[str], code: str) -> str | None:
    """First line in the twin `technical-spec.md` that declares `code`: a `| CODE | ... |`
    Functional→Technical Mapping table row when present, else the first line mentioning the code
    token anywhere in the twin doc. `None` when the code appears nowhere there."""
    table_re = re.compile(r"^\|\s*" + re.escape(code) + r"\s*\|")
    for line in tech_lines:
        if table_re.match(line.strip()):
            return line.strip()
    # `\b` on the left guards the same digit-boundary hazard `(?!\d)` guards on the right — a
    # standalone code token, never a substring of a longer alphanumeric run either side.
    token_re = re.compile(r"\b" + re.escape(code) + r"(?!\d)")
    for line in tech_lines:
        if token_re.search(line):
            return line.strip()
    return None


def _capability_intent_severity_text(row: dict, tech_text: str) -> str:
    """[SA-4, Req #11] Severity input: the CAP row's claimed FR/BR/SCR codes plus their matching
    declaration line from the twin `technical-spec.md`. NEVER the US titles, and NEVER any of the
    free-text justification `_capability_intent_text` places in judge-visible `text` — composed
    instead from codes the corpus author does not control the wording of, so bland prose cannot
    deflate an auth capability's severity, and vivid prose cannot inflate a settings capability's
    either. A unit test asserts this statically, by source inspection."""
    tech_lines = tech_text.splitlines()
    codes = sorted(row["fr"] | row["br"] | row["scr"])
    if not codes:
        return ""
    parts = []
    for code in codes:
        decl = _declaration_line(tech_lines, code)
        parts.append(f"{code} — {decl}" if decl else code)
    return "; ".join(parts)


def _extract_capability_intent_candidates(artifacts: list[dict]) -> tuple[list[dict], bool]:
    """[Req #1, #4] One candidate per § 2 CAP row claiming >= 3 US, anchored to the Python-
    computed US-title set. Returns `(candidates, any_us_claimed)` — the second value feeds
    `capability_intent_status` (FM-5): it distinguishes "ran, nothing over threshold" from "no §2
    row anywhere claims any US at all" (the half-migrated state), which a candidate count of 0
    cannot tell apart on its own.

    Pairs each `functional-spec.md` with its twin `technical-spec.md` by parent directory (both
    are registered under the "feature-list" locator scope, phase 09/01) to build `severity_text`.
    A feature with no twin technical-spec.md still gets a candidate — `severity_text` is simply
    empty and `_severity()` falls back to `text` for that candidate alone (same `or` fallback that
    keeps the four pre-existing dimensions backward-compatible).
    """
    cands: list[dict] = []
    any_us_claimed = False
    by_dir: dict[str, dict[str, dict]] = {}
    for art in artifacts:
        if not art.get("present") or not art.get("path"):
            continue
        by_dir.setdefault(str(Path(art["path"]).parent), {})[art.get("kind")] = art

    for _parent, kinds in sorted(by_dir.items()):
        func_art = kinds.get(locator.KIND_FEATURE_SPEC_FUNCTIONAL)
        if not func_art or not func_art.get("path"):
            continue
        read = read_text_safe(Path(func_art["path"]))
        if read is None:
            continue
        func_text, _ = read
        rows = cap_map.cap_rows(func_text)
        if not rows:
            continue
        titles = cap_map.section7_us_titles(func_text)
        rationale = cap_map.single_capability_rationale(func_text)

        tech_art = kinds.get("feature-spec")  # technical-spec.md's locator kind (phase 01)
        tech_text = ""
        if tech_art and tech_art.get("path"):
            tech_read = read_text_safe(Path(tech_art["path"]))
            if tech_read is not None:
                tech_text = tech_read[0]

        feature_slug = Path(func_art["path"]).parent.name
        for row in rows:
            if row["us"]:
                any_us_claimed = True
            if len(row["us"]) < _CAP_INTENT_MIN_US:
                continue
            ordered = sorted(row["us"])
            resolved = [(code, titles[code]) for code in ordered if code in titles]
            if len(resolved) != len(ordered):
                # [Step 4] a claimed US with no § 7 title -> anchor unbuildable -> NO candidate,
                # never a placeholder — a dropped candidate here would inflate expected_count.
                continue
            cand = {
                "id": f"capability-intent-{feature_slug}-{row['id']}",
                "dimension": "capability-intent",
                "target": f"{feature_slug}:{row['id']}",
                "text": _capability_intent_text(resolved, rationale),
                "anchor": _capability_intent_anchor(row["id"], resolved),
            }
            severity_text = _capability_intent_severity_text(row, tech_text)
            if severity_text:
                cand["severity_text"] = severity_text
            cands.append(cand)
    return cands, any_us_claimed


def _extract_capability_intent(artifacts: list[dict], docs_root: Path) -> tuple[list[dict], str, str]:
    """capability-intent candidates + the non-silent completion status (FM-5), mirroring
    `_extract_granularity_candidates`'s shape exactly — same `"OK"`/`"SKIPPED"` vocabulary, same
    note-carries-the-reason-and-the-path convention. `"SKIPPED"` fires when NO located § 2 row
    anywhere claims ANY US at all (the half-migrated state: § 2 widened, every cell unfilled) —
    every row otherwise falling below the >= 3 threshold is indistinguishable from a well-
    partitioned corpus without this field.
    """
    n_present = sum(1 for a in artifacts
                     if a.get("kind") == locator.KIND_FEATURE_SPEC_FUNCTIONAL and a.get("present"))
    search_path = str(docs_root / "features" / "*" / "functional-spec.md")
    candidates, any_us_claimed = _extract_capability_intent_candidates(artifacts)
    if not any_us_claimed:
        if n_present == 0:
            note = f"no functional-spec.md located under {search_path} — capability-intent axis did not run"
        else:
            note = (f"{n_present} functional-spec.md found under {search_path} but no § 2 row "
                     "claims any User Stories — § 2 is widened but its User Stories cells are "
                     "unfilled; run the fill (not the migration) then re-audit")
        return [], "SKIPPED", note
    note = (f"capability-intent ran on {n_present} functional-spec.md; {len(candidates)} CAP "
            f"row(s) claim >= {_CAP_INTENT_MIN_US} US")
    return candidates, "OK", note


def prepare(project_root: Path, scope: str, docs_root_override: str | None, plan_dir: str | None) -> dict:
    docs_root = (Path(docs_root_override).resolve() if docs_root_override
                 else resolve_docs_root(project_root))
    loc = locator.locate(project_root, scope, docs_root_override, plan_dir)
    artifacts = loc["artifacts"]
    gran_candidates, gran_status, gran_note = _extract_granularity_candidates(artifacts, docs_root)
    cap_intent_candidates, cap_intent_status, cap_intent_note = _extract_capability_intent(
        artifacts, docs_root)
    candidates = (_extract_inference_candidates(artifacts)
                  + _extract_naming_candidates(artifacts)
                  + gran_candidates
                  + cap_intent_candidates)
    return {"engine": "judgment", "mode": "prepare", "expected_count": len(candidates),
            "candidates": candidates,
            "granularity_status": gran_status, "granularity_note": gran_note,
            "capability_intent_status": cap_intent_status, "capability_intent_note": cap_intent_note}


# ---------------------------------------------------------------- assemble
def _survived_refutation(cand: dict, level: str) -> bool:
    refs = cand.get("refutations", [])
    if not refs:
        return False
    not_refuted = sum(1 for r in refs if not r.get("refuted", True))
    if level == "low":
        return not_refuted >= 1  # single-pass at --level low
    # medium/high/max: ≥2-refuter majority must say NOT refuted
    return len(refs) >= 2 and not_refuted > (len(refs) / 2)


def assemble(judged: dict, level: str) -> dict:
    candidates = judged.get("candidates", [])
    expected = judged.get("expected_count", len(candidates))
    findings: list[dict] = []
    dropped: list[dict] = []
    returned = 0

    for cand in candidates:
        verdict = cand.get("verdict")
        if verdict is None:
            continue  # judge never returned this one (dead subagent) — counts toward PARTIAL
        returned += 1
        if verdict != "WARN":
            continue
        anchor = cand.get("anchor", "")
        if not anchor:
            dropped.append({"id": cand.get("id"), "reason": "no computed anchor (Iron Law #2)"})
            continue
        confidence = cand.get("confidence", 1.0)
        if confidence < 0.5:
            dropped.append({"id": cand.get("id"), "reason": f"confidence {confidence} < 0.5 floor → UNVERIFIABLE"})
            continue
        if not _survived_refutation(cand, level):
            dropped.append({"id": cand.get("id"), "reason": "did not survive refutation pass"})
            continue
        # [SA-4] severity scans `severity_text` when the candidate set one (capability-intent),
        # else falls back to `text` — byte-identical to the pre-phase-10 behaviour for the four
        # existing dimensions, which never set `severity_text`.
        findings.append({
            "engine": "judgment", "kind": _KIND_BY_DIM.get(cand["dimension"], "UNSUPPORTED"),
            "dimension": cand["dimension"], "target": cand.get("target"),
            "severity": _severity(cand["dimension"],
                                   cand.get("severity_text") or cand.get("text", "")),
            "verdict": "WARN", "adjudicated": True, "anchor": anchor,
            "evidence": cand.get("text", ""),
            "confidence": confidence,
        })

    if returned == 0 and expected > 0:
        status = "FAILED"
    elif returned < expected:
        status = "PARTIAL"
    else:
        status = "OK"

    return {"engine": "judgment", "judgment_status": status, "level": level,
            "expected": expected, "returned": returned,
            "findings": findings, "dropped": dropped,
            # Pass-through from prepare() (phase 09/10) — assemble() adjudicates candidates, it
            # does not re-derive either axis's own completion status.
            "granularity_status": judged.get("granularity_status", "OK"),
            "granularity_note": judged.get("granularity_note"),
            "capability_intent_status": judged.get("capability_intent_status", "OK"),
            "capability_intent_note": judged.get("capability_intent_note")}


_KIND_BY_DIM = {
    "inference-validity": "UNSUPPORTED",
    "naming": "NAMING",
    "granularity": "GRANULARITY",
    "capability-intent": "CAP_MULTI_INTENT",
}


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Engine 3 — adversarial judgment residue (WARN-only)")
    p.add_argument("mode", choices=["prepare", "assemble"])
    p.add_argument("--project-root", default=None)
    p.add_argument("--docs-root", default=None)
    p.add_argument("--scope", default="all",
                   choices=["feature-list", "user-stories", "system", "all"])
    p.add_argument("--plan-dir", default=None)
    p.add_argument("--judged", default=None, help="assemble: path to judged-candidates JSON")
    p.add_argument("--level", default="medium", choices=["low", "medium", "high", "max"])
    p.add_argument("--out", default=None)
    args = p.parse_args(argv)

    if args.mode == "prepare":
        project_root = resolve_project_root(args.project_root)
        result = prepare(project_root, args.scope, args.docs_root, args.plan_dir)
    else:
        if not args.judged or not Path(args.judged).is_file():
            print("[ERROR] assemble requires --judged <file>", file=sys.stderr)
            return 2
        judged = json.loads(Path(args.judged).read_text(encoding="utf-8"))
        result = assemble(judged, args.level)

    payload = json.dumps(result, indent=2)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(out.suffix + ".tmp")
        tmp.write_text(payload, encoding="utf-8")
        tmp.replace(out)
        print(f"[judgment_engine] wrote → {out}", file=sys.stderr)
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
