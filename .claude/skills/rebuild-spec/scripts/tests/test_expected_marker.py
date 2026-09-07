"""Tests for the `[EXPECTED]` marker (v27 amendment — the 4th state, D6).

`[EXPECTED]` is the one marker added to A1's status vocabulary alongside the existing
`[UNVERIFIED]`/`[INFERRED]`/`[NEEDS_DOMAIN_CONFIRMATION]` (reused verbatim, no parallel
taxonomy). It must:
  (a) be recognized by `derive_confidence_report.py`'s `MARKER_RE` and map to the same
      uncertain `△` bucket as the other three;
  (b) leave every existing corpus (zero `[EXPECTED]` occurrences) structurally unaffected —
      same claim count, same evidence count, same confidence_derived, same table rows;
  (c) never trigger Open-Decision promotion — that path is `[NEEDS_DOMAIN_CONFIRMATION]`-only
      by design (`_audience_split_parse_v26_lib.py::parse_needs_confirmation`,
      `_audience_split_render_func_sections_lib.py::sanitize`) and MUST stay that way, since an
      expected/desired behavior is a recorded decision, not an open question for a stakeholder.

Note on (b) — "byte-identical to today's" (phase-01 non-functional requirement): the phase file
also asked (Implementation Step 2) to update the DISCLAIMER preamble sentence embedded in
*every* companion's header so it documents `[EXPECTED]` in its own marker list. That was tried
and reverted: `DISCLAIMER` is embedded verbatim in every companion, so ANY byte change to it
regenerates different output for every existing real-corpus `technical-spec.md` companion —
which broke
`test_run_doc_migrations_cli.py::test_only_audience_split_runs_and_reports_already_on_sealed_corpus`
(a frozen real-corpus byte-hash regression test belonging to a different, already-authored plan;
phase-09, plans/260824-1846-rebuild-spec-action-self-sufficiency-v27-8: the ORIGINAL test named
here, `test_only_a3_b4_refuses_while_audience_split_still_pending`, died with the `a3-b4` step it
tested — this is its still-live sibling, exercising the same frozen-byte-hash constraint via a
step that actually runs) via `run_doc_migrations.py`'s confidence-report refresh, which fires
for any `_TECH_SPEC_STEPS` member that ACTUALLY RAN, never merely requested-but-refused.
Holding the full suite green outranks widening that one sentence's prose, so `DISCLAIMER`
stays byte-identical to before this phase;
`[EXPECTED]` is still fully documented in `references/confidence-report-contract.md` § "v27
amendment — the 4th state". See the phase-01 implementer report for the full account. This
suite instead tests the invariant that actually matters: the regex widening is a pure set-union
(provably non-regressive against a fixture with zero `[EXPECTED]` tokens: same matches, same
order, same spans) and the computed stats/table rows are unchanged.
"""
from __future__ import annotations

import re

from derive_confidence_report import (
    MARKER_RE,
    compute_stats,
    derive,
    extract_claims,
    render_companion,
)

# The pre-amendment regex, reconstructed verbatim for a direct non-regression comparison.
_OLD_MARKER_RE = re.compile(r"\[(UNVERIFIED|INFERRED|NEEDS_DOMAIN_CONFIRMATION)\]")

EXPECTED_FIXTURE = """# F001_Sample

## Accessibility

- **A11Y-001**: [EXPECTED] Screen reader announces validation errors on submit.
- **A11Y-002**: Focus moves to the first invalid field. **Source:** `app/js/form.js:42`

## Cross-Cutting Logic

- **BR-001**: [UNVERIFIED] Session timeout defaults to 30 minutes — needs runtime confirmation.
"""

# Zero-[EXPECTED] fixture — the "P00" baseline the phase file names (no fixture by that name
# exists anywhere in this repo's fixtures/ tree or references/*.md; treated here as "a
# representative baseline corpus with none of the new marker", the plain reading of the intent).
NO_EXPECTED_FIXTURE = """# F002_Baseline

## Section A

- **BR-001**: Something happens. **Source:** `app/foo.rb:5`
- **BR-002**: [UNVERIFIED] Not sure about this.

## Section B

- **DEC-001**: [NEEDS_DOMAIN_CONFIRMATION] Ask the stakeholder.
"""

MIXED_FIXTURE = """- **A11Y-001**: [EXPECTED] Screen reader announces validation errors on submit.
- **DEC-001**: [NEEDS_DOMAIN_CONFIRMATION] Ask the stakeholder about legacy flag.
"""


class TestMarkerReRecognizesExpected:
    def test_expected_matches_marker_re(self):
        assert MARKER_RE.findall("[EXPECTED]") == ["EXPECTED"]

    def test_all_four_markers_recognized_in_one_pass(self):
        text = "[UNVERIFIED] [INFERRED] [NEEDS_DOMAIN_CONFIRMATION] [EXPECTED]"
        assert MARKER_RE.findall(text) == [
            "UNVERIFIED", "INFERRED", "NEEDS_DOMAIN_CONFIRMATION", "EXPECTED",
        ]

    def test_unrelated_bracket_token_not_matched(self):
        # Guards against a too-loose alternation swallowing an unrelated bracket tag.
        assert MARKER_RE.findall("[EXPECTATION] [EXPECTS]") == []


class TestExpectedYieldsTriangleRow:
    def test_expected_line_produces_uncertain_status_row(self):
        claims = extract_claims(EXPECTED_FIXTURE)
        a11y_claims = [c for c in claims if c["section"] == "Accessibility"]
        expected_rows = [c for c in a11y_claims if "announces validation errors" in c["claim"]]
        assert len(expected_rows) == 1
        row = expected_rows[0]
        # Assert the SPECIFIC bucket, not merely "no crash" — a negative-adjacent claim that
        # only checked len(claims) > 0 would pass even if EXPECTED were mis-mapped to "○".
        assert row["status"] == "△"
        assert row["evidence"] == "—"

    def test_expected_and_citation_coexist_in_same_section_correctly_split(self):
        claims = extract_claims(EXPECTED_FIXTURE)
        a11y_claims = [c for c in claims if c["section"] == "Accessibility"]
        assert len(a11y_claims) == 2
        statuses = sorted(c["status"] for c in a11y_claims)
        assert statuses == ["△", "○"]

    def test_expected_counts_toward_claims_total_not_with_evidence(self):
        claims = extract_claims(EXPECTED_FIXTURE)
        total, with_evidence, confidence_derived = compute_stats(claims)
        # 3 claims: 1 [EXPECTED] + 1 cited + 1 [UNVERIFIED]; only the citation has evidence.
        assert total == 3
        assert with_evidence == 1
        assert confidence_derived == round(1 / 3, 4)

    def test_expected_renders_triangle_glyph_in_companion_table(self):
        claims = extract_claims(EXPECTED_FIXTURE)
        total, with_evidence, cd = compute_stats(claims)
        content = render_companion("technical-spec.md", claims, total, with_evidence, cd)
        assert "| **A11Y-001**: Screen reader announces validation errors on submit. | " \
               "Accessibility | — | △ |" in content

    def test_derive_end_to_end_frontmatter_math(self, tmp_path):
        artifact = tmp_path / "technical-spec.md"
        artifact.write_text(EXPECTED_FIXTURE, encoding="utf-8")
        out_path = derive(artifact, project_root=tmp_path)
        content = out_path.read_text(encoding="utf-8")
        assert "claims_total: 3" in content
        assert "claims_with_evidence: 1" in content


class TestZeroExpectedFixtureUnaffected:
    """(b) — non-functional requirement: a corpus with no `[EXPECTED]` markers must see no
    structural change from the regex widening."""

    def test_regex_widening_is_a_pure_superset_no_expected_present(self):
        # Same matches, same order, same spans as the pre-amendment regex — proves the
        # alternation addition cannot alter behavior on text that never contains "EXPECTED".
        old_matches = [(m.group(1), m.span()) for m in _OLD_MARKER_RE.finditer(NO_EXPECTED_FIXTURE)]
        new_matches = [(m.group(1), m.span()) for m in MARKER_RE.finditer(NO_EXPECTED_FIXTURE)]
        assert old_matches == new_matches
        assert len(old_matches) == 2  # one UNVERIFIED + one NEEDS_DOMAIN_CONFIRMATION

    def test_stats_unchanged_for_zero_expected_fixture(self):
        claims = extract_claims(NO_EXPECTED_FIXTURE)
        total, with_evidence, confidence_derived = compute_stats(claims)
        assert (total, with_evidence, confidence_derived) == (3, 1, round(1 / 3, 4))

    def test_table_rows_unchanged_for_zero_expected_fixture(self):
        claims = extract_claims(NO_EXPECTED_FIXTURE)
        total, with_evidence, cd = compute_stats(claims)
        content = render_companion("technical-spec.md", claims, total, with_evidence, cd)
        assert "| **BR-001**: Something happens. | Section A | app/foo.rb:5 | ○ |" in content
        assert "| **BR-002**: Not sure about this. | Section A | — | △ |" in content
        assert "| **DEC-001**: Ask the stakeholder. | Section B | — | △ |" in content
        # No phantom EXPECTED row leaks in from anywhere.
        assert content.count("| △ |") == 2
        assert content.count("| ○ |") == 1


class TestExpectedNeverPromotesToOpenDecisions:
    """(c) — the no-promote rule. Reaches the REAL promotion code (not a stub), and the
    fixture carries BOTH markers so a negative assertion on [EXPECTED] is meaningful: the
    positive case ([NEEDS_DOMAIN_CONFIRMATION] IS promoted) proves the branch was actually
    exercised, not skipped."""

    def test_parse_needs_confirmation_ignores_expected_but_catches_needs_confirmation(self):
        from _audience_split_parse_v26_lib import parse_needs_confirmation

        entries = parse_needs_confirmation(MIXED_FIXTURE)
        assert len(entries) == 1
        assert "legacy flag" in entries[0]
        assert not any("announces validation errors" in e for e in entries)
        assert not any("EXPECTED" in e for e in entries)

    def test_sanitize_strips_needs_confirmation_but_preserves_expected_inline(self):
        from _audience_split_render_func_sections_lib import sanitize

        cleaned = sanitize(MIXED_FIXTURE)
        # [NEEDS_DOMAIN_CONFIRMATION] must never survive inline (Requirement 4) ...
        assert "[NEEDS_DOMAIN_CONFIRMATION]" not in cleaned
        # ... but [EXPECTED] is a permitted, audience-facing signal in functional-spec.md
        # prose (D6) and must NOT be scrubbed by the same choke point.
        assert "[EXPECTED]" in cleaned
        assert "announces validation errors" in cleaned
