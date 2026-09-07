#!/usr/bin/env python3
"""Deployment View validator (rebuild-spec 27.13.0, phase-03).

Checks the `## Deployment View` section of architecture.md against
`references/deployment-source-patterns.md` and the FR-5/FR-6/FR-7 contract in
plans/.../phase-03-deployment-view.md. WARN-first by design — absence of the
section, of IaC, or of an individual citation never fails the run (FR-5: the
`N/A` degradation must still pass). The ONE hard gate is a credential leak
(`assert_no_secrets`). THE RULE: a rendered artifact must never echo a literal
secret, even when everything else about it is otherwise fine. A missing citation
degrades the doc's usefulness and can be fixed later; a published credential
cannot be un-published, so it is the one finding that outranks the WARN-first
posture and fails the run outright.

Reuses `_md_scan_lib.py` for fence/comment-aware scanning — no hand-rolled
markdown parsing.

Exit codes: 0 (no critical), 1 (critical), 2 (internal).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _md_scan_lib import iter_lines_with_fence, strip_comments  # noqa: E402
from _slug_lib import assert_under, resolve_project_root  # noqa: E402
from _summary_lib import atomic_write, load_summary, recalculate_totals, derive_overall_status  # noqa: E402
from _credential_scrub_lib import assert_no_secrets  # noqa: E402

VALIDATOR = "deployment_view"

H2_RE = re.compile(r"^##\s+Deployment View\s*$")
NEXT_H2_RE = re.compile(r"^##\s+\S")
HONESTY_LABEL = (
    "> Derived from repository infrastructure-as-code — not verified against production."
)
NA_LINE = "N/A — no infrastructure-as-code found in repository."
MERMAID_OPEN_RE = re.compile(r"^```\s*mermaid\s*$", re.IGNORECASE)
FENCE_CLOSE_RE = re.compile(r"^```\s*$")
SUBGRAPH_RE = re.compile(r"^\s*subgraph\b", re.IGNORECASE)
# Node id followed by a shape delimiter: `ID[Label]` / `ID(Label)` / `ID{Label}`.
NODE_DECL_RE = re.compile(r"\b([A-Za-z_]\w*)\s*(?:\[[^\]\n]*\]|\([^)\n]*\)|\{[^}\n]*\})")
# Either side of a mermaid edge arrow (`-->`, `-.->`, `==>`, with an optional `|label|`).
EDGE_RE = re.compile(
    r"\b([A-Za-z_]\w*)\s*(?:-{1,2}|\.{1,2}-|={1,2})[-o<>x.=]*>\s*(?:\|[^|\n]*\|\s*)?([A-Za-z_]\w*)\b"
)
SOURCE_CITE_RE = re.compile(r"`[^`\n]+:\d+`")


def _issue(sev: str, rid: str, file_path: str, line_num: int | None, msg: str) -> dict:
    return {
        "validator": VALIDATOR,
        "severity": sev,
        "rule_id": rid,
        "location": {"file": file_path, "line": line_num},
        "message": msg,
    }


def _extract_section(text: str) -> tuple[list[tuple[str, bool]], int] | None:
    """Return `([(line, in_fence), ...], heading_lineno)` for `## Deployment View`.

    Fence/comment aware (`strip_comments` + `iter_lines_with_fence`): the heading
    match and the "next H2 closes this section" check both ignore fenced content,
    so an illustrative `## Deployment View` shown inside a worked-example fence
    can never be mistaken for the real section, nor prematurely close it.
    """
    stripped = strip_comments(text)
    all_lines = list(iter_lines_with_fence(stripped))
    start = None
    for lineno, line, in_fence in all_lines:
        if not in_fence and H2_RE.match(line.strip()):
            start = lineno
            break
    if start is None:
        return None
    body: list[tuple[str, bool]] = []
    for lineno, line, in_fence in all_lines:
        if lineno <= start:
            continue
        if not in_fence and NEXT_H2_RE.match(line.strip()):
            break
        body.append((line, in_fence))
    return body, start


def _mermaid_blocks(lines: list[str]) -> list[list[str]]:
    """Extract the content lines of each ```mermaid ... ``` fence in `lines`."""
    blocks: list[list[str]] = []
    current: list[str] | None = None
    for line in lines:
        if current is None:
            if MERMAID_OPEN_RE.match(line.strip()):
                current = []
            continue
        if FENCE_CLOSE_RE.match(line.strip()):
            blocks.append(current)
            current = None
            continue
        current.append(line)
    return blocks


def _collect_node_ids(block: list[str]) -> tuple[set[str], int]:
    """Return `(node_ids, subgraph_count)` found in one mermaid block."""
    node_ids: set[str] = set()
    subgraph_count = 0
    for line in block:
        if SUBGRAPH_RE.match(line):
            subgraph_count += 1
        for m in NODE_DECL_RE.finditer(line):
            node_ids.add(m.group(1))
        for m in EDGE_RE.finditer(line):
            node_ids.add(m.group(1))
            node_ids.add(m.group(2))
    return node_ids, subgraph_count


def validate(arch_path: Path, root: Path) -> dict:
    issues: list[dict] = []
    try:
        rel_path = str(arch_path.relative_to(root))
    except ValueError:
        rel_path = str(arch_path)

    if not arch_path.is_file():
        issues.append(_issue("warning", "DeploymentView.file_missing", rel_path, 0,
                             "architecture.md not found"))
        return _build_result(issues)

    text = arch_path.read_text(encoding="utf-8", errors="replace")
    section = _extract_section(text)
    if section is None:
        issues.append(_issue(
            "warning", "DeploymentView.section_missing", rel_path, 0,
            "No '## Deployment View' section found (WARN-only — expected for legacy corpora "
            "and stacks whose profile carries no deployment_sources)",
        ))
        return _build_result(issues)

    body, heading_line = section
    body_lines = [ln for ln, _ in body]
    non_fenced_lines = [ln for ln, in_fence in body if not in_fence]
    body_text = "\n".join(body_lines)

    # Security — the ONE hard gate. A leaked secret is never acceptable regardless of
    # this validator's WARN-first posture toward everything else: every other defect here
    # is recoverable by a later edit, but a credential rendered into the docs tree is
    # already disclosed to everyone who can read it. Hence critical, not warning.
    for warn_msg in assert_no_secrets(body_text):
        issues.append(_issue("critical", "DeploymentView.secret_leak", rel_path, heading_line, warn_msg))

    # FR-6 — honesty label, immediately under the H2, verbatim.
    first_content = next((ln for ln in body_lines if ln.strip()), "")
    if first_content.strip() != HONESTY_LABEL:
        issues.append(_issue(
            "warning", "DeploymentView.label_missing", rel_path, heading_line,
            f"Deployment View is missing the mandatory honesty label immediately under its "
            f"heading (expected verbatim: {HONESTY_LABEL!r})",
        ))

    has_na = NA_LINE in body_text
    mermaid_blocks = _mermaid_blocks(body_lines)

    if has_na:
        # FR-5 degradation contract: always a WARN — never silent, never a FAIL.
        issues.append(_issue(
            "warning", "DeploymentView.no_iac", rel_path, heading_line,
            "No infrastructure-as-code found in repository — Deployment View degraded to the "
            "N/A line (expected behavior, not a defect)",
        ))
        if mermaid_blocks:
            issues.append(_issue(
                "warning", "DeploymentView.na_with_diagram", rel_path, heading_line,
                "Both the N/A degradation line and a mermaid diagram are present in the same "
                "section — these two states are mutually exclusive",
            ))
        return _build_result(issues)

    if not mermaid_blocks:
        issues.append(_issue(
            "warning", "DeploymentView.no_diagram", rel_path, heading_line,
            "Deployment View has neither the N/A degradation line nor a mermaid diagram",
        ))
        return _build_result(issues)

    if len(mermaid_blocks) > 1:
        # Key insight 2 / success criterion 4: infra + network placement come from
        # the same source file and must render as ONE combined diagram, not two.
        issues.append(_issue(
            "warning", "DeploymentView.split_diagram", rel_path, heading_line,
            f"Found {len(mermaid_blocks)} mermaid diagrams in Deployment View — infra placement "
            "and network connectivity must be ONE combined flowchart, not split",
        ))

    for block in mermaid_blocks:
        type_line = next((ln.strip() for ln in block if ln.strip()), "")
        if type_line and not type_line.lower().startswith("flowchart"):
            issues.append(_issue(
                "warning", "DeploymentView.diagram_type", rel_path, heading_line,
                f"Deployment View diagram should be a mermaid 'flowchart' per FR-3, found: {type_line!r}",
            ))

    all_node_ids: set[str] = set()
    total_subgraphs = 0
    for block in mermaid_blocks:
        node_ids, subgraph_count = _collect_node_ids(block)
        all_node_ids |= node_ids
        total_subgraphs += subgraph_count

    if all_node_ids and total_subgraphs == 0:
        issues.append(_issue(
            "warning", "DeploymentView.no_subgraph", rel_path, heading_line,
            "Deployment View diagram has nodes but no 'subgraph' blocks — FR-3 requires one "
            "subgraph per host/node/runtime",
        ))

    # FR-7 citation invariant: every node/edge id must appear alongside a `file:line`
    # citation somewhere in the section body OUTSIDE the fenced diagram itself.
    cited_lines = [ln for ln in non_fenced_lines if SOURCE_CITE_RE.search(ln)]
    for node_id in sorted(all_node_ids):
        if not any(node_id in ln for ln in cited_lines):
            issues.append(_issue(
                "warning", "DeploymentView.node_uncited", rel_path, heading_line,
                f"Node/edge '{node_id}' has no matching '`file:line`' citation — a node with no "
                "citable source must not appear in the diagram (FR-7)",
            ))

    return _build_result(issues)


def _build_result(issues: list[dict]) -> dict:
    critical = sum(1 for i in issues if i["severity"] == "critical")
    warning = sum(1 for i in issues if i["severity"] == "warning")
    return {
        "validator": VALIDATOR,
        "timestamp": _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "FAIL" if critical else ("WARN" if warning else "PASS"),
        "summary": {"critical": critical, "warning": warning},
        "issues": issues,
    }


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="rebuild-spec Deployment View validator (27.13.0)")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--plan-dir")
    g.add_argument("--architecture-file")
    p.add_argument("--project-root", default=None)
    p.add_argument("--summary-out", default=None)
    args = p.parse_args(argv)
    root = resolve_project_root(args.project_root)

    if args.plan_dir:
        plan_dir = Path(args.plan_dir).resolve()
        if not plan_dir.is_dir():
            print(f"[ERROR] --plan-dir is not a directory: {plan_dir}", file=sys.stderr)
            return 2
        arch_path = plan_dir / "artifacts" / "architecture.md"
    else:
        arch_path = Path(args.architecture_file).resolve()
        plan_dir = arch_path.parent.parent

    try:
        assert_under(plan_dir, root)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    try:
        result = validate(arch_path, root)
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] validator crashed: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2, sort_keys=True))
    crit = result["summary"]["critical"]

    if args.summary_out:
        sp = Path(args.summary_out).resolve()
        try:
            assert_under(sp.parent, root)
            summary = load_summary(sp, plan_dir.name)
            summary["validators"][VALIDATOR] = {
                "status": result["status"],
                "summary": result["summary"],
                "issues": result["issues"],
            }
            recalculate_totals(summary)
            summary["overall_status"] = derive_overall_status(summary)
            atomic_write(sp, summary)
        except Exception as exc:  # noqa: BLE001
            print(f"[ERROR] failed to merge summary: {exc}", file=sys.stderr)
            return 2

    return 1 if crit else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
