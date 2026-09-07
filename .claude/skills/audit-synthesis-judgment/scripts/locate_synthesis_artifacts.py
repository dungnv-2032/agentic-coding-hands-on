#!/usr/bin/env python3
"""Phase 01 — synthesis-tier artifact locator.

Resolves the lang-mapped docs root (via the copied `_citation_lib.resolve_docs_root`),
then emits a JSON manifest of every in-scope synthesis artifact present on disk. Feeds
Engine 1 (coverage), Engine 2 (boundary), Engine 3 (judgment).

Absence is normal, not an error: a missing artifact is recorded `present: false` (feeds the
phase-02 gap accounting). The tool never reads outside the resolved docs root.

Stdlib only. Always exits 0 unless the docs root itself cannot be resolved (exit 2).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _citation_lib import resolve_docs_root, resolve_project_root  # noqa: E402

# phase 09 (capability-map) — registered rather than globbed by judgment_engine.py directly, so
# resolve_docs_root's per-language fallback (below) applies to it the same as every other
# artifact, and so the locator stays the ONE authoritative answer to "was § 2 found?".
KIND_FEATURE_SPEC_FUNCTIONAL = "feature-spec-functional"

# Canonical layered paths relative to the resolved docs_root (v4 layout).
# Mirrors build_source_to_fcode.ARTIFACT_LAYERED + the feature/flows dirs.
_SCOPE_ARTIFACTS: dict[str, list[tuple[str, str, str]]] = {
    # scope -> [(kind, tier, rel_path_or_glob)]
    "feature-list": [
        ("feature-list", "generated", "generated/feature-list.md"),
        ("feature-spec", "features", "features/*/technical-spec.md"),
        (KIND_FEATURE_SPEC_FUNCTIONAL, "features", "features/*/functional-spec.md"),
    ],
    "user-stories": [
        ("user-stories", "generated", "generated/user-stories.md"),
    ],
    "system": [
        ("glossary", "system", "system/glossary.md"),
        ("entities", "generated", "generated/entities.md"),
        # v27.0.0: system/business-rules.md is DELETED — its curated per-rule content is absorbed
        # into generated/behavior-logic.md (see _shared/docs-canonical-mapping.md's Disambiguation
        # note). Repointed here rather than left as a dead locator row that always resolves absent.
        ("behavior-logic", "generated", "generated/behavior-logic.md"),
        ("system-overview", "system", "system/overview.md"),
        ("architecture", "system", "system/architecture.md"),
        ("flows", "flows", "flows/*.md"),
    ],
}


def _expand(docs_root: Path, kind: str, tier: str, rel: str) -> list[dict]:
    """Resolve one artifact spec (literal path or glob) to manifest entries."""
    entries: list[dict] = []
    if "*" in rel:
        matches = sorted(docs_root.glob(rel))
        if not matches:
            entries.append({"artifact": rel, "kind": kind, "tier": tier,
                            "path": str(docs_root / rel), "present": False})
        for m in matches:
            entries.append({"artifact": m.name, "kind": kind, "tier": tier,
                            "path": str(m), "present": m.is_file()})
    else:
        p = docs_root / rel
        entries.append({"artifact": Path(rel).name, "kind": kind, "tier": tier,
                        "path": str(p), "present": p.is_file()})
    return entries


def locate(project_root: Path, scope: str, docs_root_override: str | None,
           plan_dir: str | None) -> dict:
    """Manifest of every in-scope artifact. Every artifact resolves under the docs root.

    `plan_dir` is accepted (and ignored) so the four `--scope` CLIs keep one call shape. It was
    the only input of the retired plan-dir locator; the surviving consumer of `--plan-dir` is
    `coverage_engine.py`'s plan-dir validator subset, which reads the flag directly.
    """
    docs_root = (Path(docs_root_override).resolve() if docs_root_override
                 else resolve_docs_root(project_root))

    scopes = ["feature-list", "user-stories", "system"] if scope == "all" else [scope]

    artifacts: list[dict] = []
    seen_paths: set[str] = set()

    for sc in scopes:
        for kind, tier, rel in _SCOPE_ARTIFACTS.get(sc, []):
            for entry in _expand(docs_root, kind, tier, rel):
                key = entry.get("path") or f"{entry['kind']}:{entry['artifact']}"
                if key in seen_paths:
                    continue
                seen_paths.add(key)
                artifacts.append(entry)

    return {
        "project_root": str(project_root),
        "docs_root": str(docs_root),
        "scope": scope,
        "artifacts": artifacts,
    }


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Locate rebuild-spec synthesis-tier artifacts")
    p.add_argument("--project-root", default=None, help="Project root (default: git toplevel)")
    p.add_argument("--docs-root", default=None, help="Override the resolved docs root")
    p.add_argument("--scope", default="all",
                   choices=["feature-list", "user-stories", "system", "all"])
    p.add_argument("--plan-dir", default=None,
                   help="Plan dir (accepted for CLI parity; not read by the locator)")
    args = p.parse_args(argv)

    project_root = resolve_project_root(args.project_root)
    if not project_root.is_dir():
        print(f"[ERROR] project root not found: {project_root}", file=sys.stderr)
        return 2

    result = locate(project_root, args.scope, args.docs_root, args.plan_dir)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
