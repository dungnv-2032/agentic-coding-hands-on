"""Phase 04 (rebuild-spec 27.7.0, action-thread reshape) — the scaffold/template
drift gap named in phase-04-scaffold.md's Key Insights: `scaffold_spec.py`
renders `technical-spec.md` from `_spec_constants` constants, not from
`templates/technical-spec-template.md` itself (scaffold_spec.py, around the
import block) — so the two can silently disagree with nothing to catch it.

This test parses BOTH the scaffold's actual rendered output and the template
FILE (never the constants twice — that coverage already lives in
test_spec_constants_sot.py::TestTemplateAntiDrift, which compares the template
against `_spec_constants`, not against what the scaffolder actually emits) and
asserts their H2/H3 heading sequences agree. Every comparison below is paired
with a self-check proving it would actually FAIL on a real mismatch — the
convention `test_spec_constants_sot.py::TestTemplateAntiDrift` already
established, and the plan's own success criterion for this phase.
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
TEMPLATE = SCRIPTS_DIR.parent / "templates" / "technical-spec-template.md"

sys.path.insert(0, str(SCRIPTS_DIR))

from _spec_constants import (  # noqa: E402
    A3_HEADING,
    ACTION_HEADING_RE,
    B4_HEADING,
    REQUIRED_APPENDIX_H3,
    REQUIRED_H2_TECH_THREAD,
    REQUIRED_VERIF_H3,
)
from _spec_parse import parse_headings_and_blocks  # noqa: E402
from scaffold_spec import _render_frontmatter, _render_technical_spec  # noqa: E402

import re


def _headings(text: str) -> list[tuple[int, str]]:
    return parse_headings_and_blocks(text.splitlines())[0]


def _h2_sequence(text: str) -> list[str]:
    return [h for _, h in _headings(text) if h.startswith("## ") and not h.startswith("### ")]


def _h3_sequence_in(text: str, h2_name: str) -> list[str]:
    """All H3s inside *h2_name*'s bounds — includes non-required sibling
    headings (e.g. a real block heading), same convention as
    test_spec_constants_sot.py's `_h3_sequence_in`."""
    lines = text.splitlines()
    headings = _headings(text)
    h2 = [(i, h) for i, h in headings if h.startswith("## ") and not h.startswith("### ")]
    bounds = None
    for i, (idx, h) in enumerate(h2):
        if h == h2_name:
            bounds = (idx + 1, h2[i + 1][0] if i + 1 < len(h2) else len(lines))
            break
    assert bounds is not None, f"{h2_name!r} not found"
    h3 = [(idx, h) for idx, h in headings if h.startswith("### ") and not h.startswith("#### ")]
    return [h for idx, h in h3 if bounds[0] <= idx < bounds[1]]


def _members_in_order(seq: list[str], required: list[str]) -> list[str]:
    """Membership-filtered order check — mirrors test_spec_constants_sot.py's
    `_required_members_in_order`: § 4 legitimately carries extra example H3s
    (ALG-###/INT-### blocks) that are not part of REQUIRED_APPENDIX_H3."""
    return [h for h in seq if h in required]


def _scaffold_text() -> str:
    frontmatter = _render_frontmatter(
        status="draft", authored_by="takumi", created="2026-01-01",
        lang="en", fcode="F001",
    )
    return _render_technical_spec("my-feature", frontmatter, "F001")


def _template_text() -> str:
    return TEMPLATE.read_text(encoding="utf-8")


# ===========================================================================
# § H2 sequence — scaffold vs template, parsed from the file, not the constant
# ===========================================================================

class TestScaffoldMatchesTemplateH2Sequence:
    def test_scaffold_h2_sequence_matches_template_file(self):
        """THE test this phase exists to add: the scaffolder's own rendered
        output, parsed independently, must equal the template FILE's own H2
        sequence, parsed independently — not two views of the same constant."""
        assert _h2_sequence(_scaffold_text()) == _h2_sequence(_template_text())

    def test_anti_drift_h2_comparison_actually_discriminates(self):
        """Self-check: a scaffold missing one required H2 must NOT compare
        equal to the template — proves the assertion above would fail loudly
        on a real drift, rather than trivially passing because both sides were
        built from the same source."""
        drifted = [h for h in _h2_sequence(_scaffold_text()) if h != "## 3. Actions"]
        assert drifted != _h2_sequence(_template_text())

    def test_scaffold_h2_sequence_is_exactly_the_thread_shape(self):
        """Documents what is being compared: the scaffold carries no extra
        top-level H2 beyond the 5 thread sections — the template's only
        top-level H2s too (unlike H3s, which legitimately carry extra example
        blocks). A3 (`## Source Walkthrough`) / B4 (`## DB Impact per Event`)
        RETIRED from this shape (phase 08, self-sufficiency v27.8) -- neither
        heading is appended after the loop any more."""
        assert _h2_sequence(_scaffold_text()) == REQUIRED_H2_TECH_THREAD
        assert A3_HEADING not in _h2_sequence(_scaffold_text())
        assert B4_HEADING not in _h2_sequence(_scaffold_text())


# ===========================================================================
# § 4 Shared Foundation — appendix H3 members, scaffold vs template
# ===========================================================================

class TestScaffoldMatchesTemplateAppendixH3:
    def test_scaffold_appendix_h3_members_match_template(self):
        scaffold_h3 = _members_in_order(
            _h3_sequence_in(_scaffold_text(), "## 4. Shared Foundation"), REQUIRED_APPENDIX_H3
        )
        template_h3 = _members_in_order(
            _h3_sequence_in(_template_text(), "## 4. Shared Foundation"), REQUIRED_APPENDIX_H3
        )
        assert scaffold_h3 == template_h3 == REQUIRED_APPENDIX_H3

    def test_anti_drift_appendix_h3_comparison_actually_discriminates(self):
        scaffold_h3 = _members_in_order(
            _h3_sequence_in(_scaffold_text(), "## 4. Shared Foundation"), REQUIRED_APPENDIX_H3
        )
        drifted = [h for h in scaffold_h3 if h != "### 4.4 Shared Rules"]
        assert drifted != REQUIRED_APPENDIX_H3


# ===========================================================================
# § 5 Verification & Technical Notes — H3 members, scaffold vs template
# ===========================================================================

class TestScaffoldMatchesTemplateVerifH3:
    def test_scaffold_verif_h3_members_match_template(self):
        scaffold_h3 = _members_in_order(
            _h3_sequence_in(_scaffold_text(), "## 5. Verification & Technical Notes"), REQUIRED_VERIF_H3
        )
        template_h3 = _members_in_order(
            _h3_sequence_in(_template_text(), "## 5. Verification & Technical Notes"), REQUIRED_VERIF_H3
        )
        assert scaffold_h3 == template_h3 == REQUIRED_VERIF_H3

    def test_anti_drift_verif_h3_comparison_actually_discriminates(self):
        scaffold_h3 = _members_in_order(
            _h3_sequence_in(_scaffold_text(), "## 5. Verification & Technical Notes"), REQUIRED_VERIF_H3
        )
        drifted = [h for h in scaffold_h3 if h != "### 5.5 Artifact References"]
        assert drifted != REQUIRED_VERIF_H3


# ===========================================================================
# § 2 Action Index header row — wire-format-contract.md: "Header, exactly"
# ===========================================================================

class TestActionIndexHeaderRowMatchesTemplate:
    def _header_and_sep(self, text: str) -> list[str]:
        return [ln for ln in text.splitlines() if ln.startswith("| # |") or ln.startswith("|---|")]

    def test_scaffold_header_row_byte_identical_to_template(self):
        scaffold_rows = self._header_and_sep(_scaffold_text())
        template_rows = self._header_and_sep(_template_text())
        assert scaffold_rows, "scaffold has no '## 2. Action Index' header row"
        assert template_rows, "template has no '## 2. Action Index' header row"
        assert scaffold_rows[:2] == template_rows[:2]

    def test_anti_drift_header_row_comparison_actually_discriminates(self):
        scaffold_rows = self._header_and_sep(_scaffold_text())
        drifted = [scaffold_rows[0].replace("Codes", "Tags")] + scaffold_rows[1:]
        template_rows = self._header_and_sep(_template_text())
        assert drifted != template_rows[:2]

    def test_scaffold_has_the_mandatory_a0_row(self):
        """C2/D2 — A0 is never optional; a fresh scaffold with only A0 (or A0 +
        A1) must still carry it verbatim."""
        assert "| **A0** |" in _scaffold_text()


# ===========================================================================
# § 3 Actions — the A1 skeleton's heading shape stays a real ACTION_HEADING_RE
# match (sanity: the scaffold's H4 spine is not accidentally malformed).
# ===========================================================================

class TestActionSkeletonHeadingShape:
    def test_a1_heading_matches_action_heading_re(self):
        heading_line = next(
            ln for ln in _scaffold_text().splitlines() if ln.startswith("#### A1")
        )
        assert re.match(ACTION_HEADING_RE, heading_line)
