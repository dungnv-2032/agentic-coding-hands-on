"""Phase 11 (B4e), class 2 — `backfill_source_references`.

The real sharetribe corpus's `## Source Code References` section is sometimes a
boilerplate pointer ("See source citations in cross-cutting logic sections
above.") instead of citations, byte-identical across F017_ListingVerification,
F062_AnalyticsIntegration, F063_MaintenanceOps, F064_AdminPlanView, and
F065_AdminSearchSettings — every one of these documents' real inline
`**Source:**` citations are sitting elsewhere in the same file. This backfills
them; it must never fabricate a citation for a spec that genuinely has none.
"""
from __future__ import annotations

import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from _audience_split_compose_a_lib import compose_mode_a  # noqa: E402
from _audience_split_migrate_lib import validate_feature_dir  # noqa: E402
from _audience_split_source_refs_lib import backfill_source_references  # noqa: E402

FIXTURES = _TESTS_DIR / "fixtures" / "migrate_feature_audience_split"
V26_VALID = FIXTURES / "v26-valid-content"

_BOILERPLATE = "See source citations in cross-cutting logic sections above."


# ---------------------------------------------------------------------------
# Unit tests — backfill_source_references directly
# ---------------------------------------------------------------------------

def test_replaces_boilerplate_body_with_aggregated_citations():
    text = (
        "# F001_Test\n\n"
        "### A rule (BR-001)\n**Source:** `app/services/thing.rb:10-20`\n\n"
        "### Another rule (BR-002)\n**Source:** `app/services/other.rb:5-9`\n\n"
        "## Source Code References\n\n"
        f"{_BOILERPLATE}\n\n"
        "## Unresolved Questions\nNone.\n"
    )
    out = backfill_source_references(text)
    assert _BOILERPLATE not in out
    assert "**Source:** `app/services/thing.rb:10-20`" in out.split(
        "## Source Code References"
    )[1]
    assert "**Source:** `app/services/other.rb:5-9`" in out.split(
        "## Source Code References"
    )[1]


def test_deduplicates_repeated_citations():
    text = (
        "# F001_Test\n\n"
        "### A rule (BR-001)\n**Source:** `app/services/thing.rb:10-20`\n\n"
        "### Another rule (BR-002)\n**Source:** `app/services/thing.rb:10-20`\n\n"
        "## Source Code References\n\n"
        f"{_BOILERPLATE}\n\n"
        "## Unresolved Questions\nNone.\n"
    )
    out = backfill_source_references(text)
    section = out.split("## Source Code References")[1].split("## Unresolved")[0]
    assert section.count("app/services/thing.rb:10-20") == 1


def test_no_op_when_section_already_has_real_content():
    """Control: a section that ALREADY carries a real citation is untouched —
    this is not a blind rewrite of the whole section on every run."""
    text = (
        "# F001_Test\n\n"
        "### A rule (BR-001)\n**Source:** `app/services/thing.rb:10-20`\n\n"
        "## Source Code References\n\n"
        "**Source:** `app/services/thing.rb:10-20`\n\n"
        "## Unresolved Questions\nNone.\n"
    )
    assert backfill_source_references(text) == text


def test_no_op_when_zero_citations_exist_anywhere():
    """Negative test: the boilerplate is present, but the document has NO real
    inline **Source:** citation to aggregate — must NOT fabricate one. The
    section is left as the (still-failing) boilerplate."""
    text = (
        "# F001_Test\n\n"
        "### A rule (BR-001)\nNo source line in this block at all.\n\n"
        "## Source Code References\n\n"
        f"{_BOILERPLATE}\n\n"
        "## Unresolved Questions\nNone.\n"
    )
    out = backfill_source_references(text)
    assert out == text
    assert _BOILERPLATE in out


def test_no_op_when_heading_absent():
    text = "# F001_Test\n\n### A rule (BR-001)\n**Source:** `x.rb:1-2`\n"
    assert backfill_source_references(text) == text


# ---------------------------------------------------------------------------
# Integration — compose_mode_a + validate_feature_dir on a real-shaped v26 dir
# ---------------------------------------------------------------------------

def _write_boilerplate_feature_dir(tmp_path: Path) -> Path:
    """Copy the v26-valid-content fixture, but replace its populated
    ## Source Code References table with the real corpus's boilerplate
    pointer — the exact byte-identical sentence found in all 5 affected
    units, so real inline citations (BR-001/DEC-001/SM-001/FR bullets, all
    already present in this fixture) are the only source to aggregate from."""
    feat_dir = tmp_path / "F001_Auth"
    feat_dir.mkdir(parents=True)
    for name in ("business-context.md", "screens.md", "edge-cases.md"):
        (feat_dir / name).write_text(
            (V26_VALID / name).read_text(encoding="utf-8"), encoding="utf-8"
        )
    tech_text = (V26_VALID / "technical-spec.md").read_text(encoding="utf-8")
    old_section_start = tech_text.index("## Source Code References")
    old_section_end = tech_text.index("## Unresolved Questions")
    tech_text = (
        tech_text[:old_section_start]
        + "## Source Code References\n\n"
        + f"{_BOILERPLATE}\n\n"
        + tech_text[old_section_end:]
    )
    (feat_dir / "technical-spec.md").write_text(tech_text, encoding="utf-8")
    return feat_dir


def test_integration_compose_then_validate_resolves_source_refs_empty(tmp_path):
    feature_dir = _write_boilerplate_feature_dir(tmp_path)
    composed = compose_mode_a(feature_dir)

    project_root = tmp_path / "project"
    staged = project_root / "_staging" / "features" / "F001_Auth"
    staged.mkdir(parents=True)
    for name, content in composed.items():
        (staged / name).write_text(content, encoding="utf-8")

    assert _BOILERPLATE not in composed["technical-spec.md"]

    _ok, issues = validate_feature_dir(staged, project_root)
    critical = [i for i in issues if i.get("severity") == "critical"]
    rule_ids = {i["rule_id"] for i in critical}
    assert "FeatureSpec.source_refs_empty" not in rule_ids, critical
