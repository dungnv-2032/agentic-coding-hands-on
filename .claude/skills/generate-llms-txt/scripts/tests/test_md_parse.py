"""Unit tests for md_parse.py's pure parsers: `bold_fields` (fence-awareness + first-wins) and
`project_field` (parity against a fixture, plus the fenced-block regression pinned by red-team F4).

This repo has no docs/system/overview.md of its own, so the parity check reads the fixture's
copy instead of this repo's (there isn't one) — that is the point of F4's fix.
"""
from pathlib import Path

import md_parse

FIXTURE_OVERVIEW = Path(__file__).resolve().parent / "fixtures" / "rich-repo" / "docs" / "system" / "overview.md"


def test_bold_fields_is_fence_aware_and_first_wins():
    content = (
        "**Key**: first value\n"
        "```\n"
        "**Key**: value inside a fence, must be ignored\n"
        "```\n"
        "**Key**: second value, must be ignored (first wins)\n"
        "**Other**: kept\n"
    )
    fields = md_parse.bold_fields(content)
    assert fields["Key"] == "first value"
    assert fields["Other"] == "kept"


def test_project_field_parity_against_fixture():
    """v1 used to run this parity check against THIS repo's docs/system/overview.md; this repo
    has none, so the fixture stands in (red-team F4)."""
    content = FIXTURE_OVERVIEW.read_text(encoding="utf-8")
    assert md_parse.project_field(content) == "Acme Portal"


def test_project_field_ignores_unfilled_placeholder():
    content = "# System Overview\n\n**Project**: {{PROJECT_NAME}}\n"
    assert md_parse.project_field(content) == ""


def test_project_field_fenced_block_regression():
    """Documented behavior change from v1 (red-team F4): v1's raw regex search was NOT
    fence-aware, so a `**Project**: X` line shown inside a fenced code example would match.
    project_field() now delegates to bold_fields(), which skips fenced lines — this pins that
    the fenced occurrence is ignored and only the real, non-fenced field is read."""
    content = (
        "# System Overview\n\n"
        "Example doc-writing snippet:\n\n"
        "```markdown\n"
        "**Project**: Ignored Example\n"
        "```\n\n"
        "**Project**: Real Project\n"
    )
    assert md_parse.project_field(content) == "Real Project"
