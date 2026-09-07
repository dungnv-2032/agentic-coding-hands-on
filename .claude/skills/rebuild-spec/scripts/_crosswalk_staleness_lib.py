"""FR-6/RT-3 fallback — crosswalk staleness WARN check (rebuild-spec 27.11.0, plan phase-01).

Extracted out of validate_traceability_matrix.py to keep that script under the 200-LOC
convention.

HISTORY (matters for reading this file's posture): when first written, NONE of the
optional passes invoked `build_navigation.py` at completion — only core W9.6, feature-specs
FS.7, screen-specs SS.3 and translate Step 3.5 did. That made a stale crosswalk the normal
case, and this WARN the only defence. FR-6 named wiring the invocation as the PREFERRED fix
and this check as the accepted fallback; the fallback shipped first because those pipeline
docs sat outside phase-01's file-ownership list.

CURRENT STATE: the optional passes — `--test-cases` and `--api-contracts` — DO now invoke
`build_navigation.py` at their promote step, so the crosswalk is normally fresh. This check
is therefore a BACKSTOP, not the primary defence: it still earns its place for a hand-run
script, an interrupted pass, or a pass added later that forgets the nav call.

What it does: WARN when an optional artifact is present on disk but absent from the current
top-level README's '## Document Map'. A crosswalk that omits an artifact the corpus has is
worse than no crosswalk — it reads as authoritative absence.

Stdlib only, best-effort.
"""
from __future__ import annotations

import json
from pathlib import Path

from _nav_strings import get_strings

VALIDATOR = "traceability_matrix"


def _issue(msg: str) -> dict:
    return {"validator": VALIDATOR, "severity": "warning",
            "rule_id": "TraceabilityMatrix.crosswalk_stale", "message": msg}


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def check_crosswalk_staleness(docs_root: Path) -> list[dict]:
    """WARN when a present optional artifact is unlisted in the README's Document Map."""
    issues: list[dict] = []
    readme_path = docs_root / "README.md"
    if not readme_path.is_file():
        return issues  # nothing to compare against — not this check's concern
    readme = _read(readme_path)

    lang = "en"
    try:
        data = json.loads((docs_root / ".rebuild-state.json").read_text(encoding="utf-8"))
        lang = str(data.get("primary_lang") or "en")
    except (OSError, json.JSONDecodeError, ValueError):
        pass
    entries = get_strings(lang).get("document_map", {}).get("entries", {})

    # api-contracts.md — a unique on-disk link target; a plain substring check on the
    # rendered markdown link target is unambiguous.
    for rel in ("generated/api-contracts.md",):
        if (docs_root / rel).is_file() and f"]({rel})" not in readme:
            issues.append(_issue(
                f"{rel} exists but is not listed in the README's Document Map — rerun "
                "build_navigation.py (no pass currently re-invokes it after this one)"))

    # test-cases.md shares its link target ("features/") with functional-spec.md /
    # technical-spec.md, which are always present once any feature exists — grep the
    # test_cases entry's own localized description text instead, which is unique.
    tc_present = (docs_root / "features").is_dir() and \
        any((docs_root / "features").glob("*/test-cases.md"))
    tc_desc = entries.get("test_cases")
    if tc_present and tc_desc and tc_desc not in readme:
        issues.append(_issue(
            "a features/*/test-cases.md exists but the Test Spec bucket does not "
            "mention it in the README's Document Map — rerun build_navigation.py"))
    return issues
