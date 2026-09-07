"""Phase 08 (citation-coverage integrity) — plans/260824-1128-rebuild-spec-action-thread-v27-7.

The real deliverable here is not a label rename; it is proof, against the REAL regex in
`derive_confidence_report.CITATION_RE`, that:

1. the settled `**Source:**` action-rung form (D3, wire-format-contract.md § 3 rule 2) is
   counted as a cited claim;
2. the B-v sample rev2's original candidate (`**Source** · ...`, no colon inside the bold,
   a middot before the citation) is NOT counted — proving the exact silent-failure class
   this phase exists to prevent, by running the parser, not by reading the regex;
3. `## Source Walkthrough`'s `**File:**` label stays excluded, unchanged;
4. `build_source_to_fcode.py` still maps cited paths to F### once `## DB Impact per Event`
   and `### 5.4 Source References` each gain a new `Action` column;
5. citation coverage on a migrated feature is >= coverage on its v27 original — the
   no-regression assertion nothing else in this repo currently makes.

All fixtures under tests/fixtures/citation_coverage_no_regression/ are SYNTHETIC (a fictional
F900_SyntheticThing feature) — never real corpus content, per the phase's "work on a copy,
never commit corpus content into agent-kit" constraint. Their shape mirrors the real
F011_ListingModeration technical-spec.md (BR blocks with **Source:** lines, an [INFERRED]
BR block, a bare-backtick § 5.4 Source References table, a bare-backtick DB Impact table,
and a **File:**-labelled Source Walkthrough) closely enough that the assertions below
generalize to the real corpus.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SCRIPTS_DIR))

from derive_confidence_report import CITATION_RE, compute_stats, extract_claims  # noqa: E402
from build_source_to_fcode import _parse_citations, build_index  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "citation_coverage_no_regression"
ORIGINAL = FIXTURES / "original.md"
MIGRATED_CORRECT = FIXTURES / "migrated_correct.md"
MIGRATED_BUGGY_LABEL = FIXTURES / "migrated_buggy_label.md"


def _coverage(text: str) -> tuple[int, int, float | None]:
    """(claims_total, claims_with_evidence, confidence_derived) via the real deterministic parser."""
    return compute_stats(extract_claims(text))


# ---------------------------------------------------------------------------
# 1-2. Settle the rung label against CITATION_RE itself (not against prose).
# ---------------------------------------------------------------------------

class TestSourceRungAgainstRealRegex:
    def test_settled_form_is_counted(self):
        """`**Source:**` (colon inside the bold) directly followed by whitespace then a
        backticked `path:line`, with NO middot before the first citation, is what
        `CITATION_RE` requires — and is the form migrated_correct.md's action rungs use."""
        line = "**Source:** `app/services/thing_service.rb:10-20` -> `app/controllers/thing_controller.rb:5`"
        matches = list(CITATION_RE.finditer(line))
        assert len(matches) == 1
        assert matches[0].group(1) == "app/services/thing_service.rb"
        assert matches[0].group(2) == "10"
        assert matches[0].group(3) == "20"

    def test_bv_sample_candidate_no_colon_is_silently_invisible(self):
        """The B-v sample rev2's original rung head, `**Source** · ...` (bold closes BEFORE
        any colon) — CITATION_RE requires the literal token `**Source:**`, colon included
        inside the double-asterisks. This candidate produces ZERO matches: exactly the
        'drop A1 coverage corpus-wide with no signal' failure the phase file describes."""
        line = "**Source** · `app/services/thing_service.rb:10-20` -> `app/controllers/thing_controller.rb:5`"
        assert list(CITATION_RE.finditer(line)) == []

    def test_colon_alone_is_not_sufficient_if_a_middot_still_separates(self):
        """Adding the colon is NOT the whole fix: `**Source:** · \\`path:line\\`` (colon
        present, but the ` · ` separator every OTHER rung uses is kept immediately after
        the label) ALSO produces zero matches, because `\\s+` stops at the non-whitespace
        middot and the mandatory literal `:` can never be reached before the `` ` `` that
        blocks the character class. The settled form must drop the middot for this rung
        specifically — this is the non-obvious half of D3 this phase had to prove, not
        just assert."""
        line = "**Source:** · `app/services/thing_service.rb:10-20`"
        assert list(CITATION_RE.finditer(line)) == []

    def test_settled_form_accepts_a_bare_unbacktick_path_too(self):
        """CITATION_RE's leading backtick is optional — confirms the settled form is robust
        to an author dropping the backticks, matching the regex's own tolerance."""
        line = "**Source:** app/services/thing_service.rb:10-20 -> more"
        matches = list(CITATION_RE.finditer(line))
        assert len(matches) == 1


# ---------------------------------------------------------------------------
# 3. `**File:**` in Source Walkthrough stays excluded (unchanged behavior).
# ---------------------------------------------------------------------------

class TestFileLabelStaysExcluded:
    def test_file_label_never_matches_citation_re(self):
        line = "**File:** `app/models/thing.rb:1-20` -- start here: defines the entity."
        assert list(CITATION_RE.finditer(line)) == []

    def test_source_walkthrough_section_contributes_zero_claims(self):
        text = (
            "## Source Walkthrough\n\n"
            "1. **File:** `app/models/thing.rb:1-20` -- start here.\n"
            "2. **File:** `app/controllers/thing_controller.rb:1-40` -- next.\n"
        )
        claims = extract_claims(text)
        assert claims == []

    def test_real_fixture_source_walkthrough_lines_are_not_counted(self):
        """Both fixture files carry two `**File:**` lines under `## Source Walkthrough`;
        neither contributes to claims_total in the real parser run (see the full-file
        counts asserted in TestNoRegressionOnMigratedFeature below)."""
        for path in (ORIGINAL, MIGRATED_CORRECT):
            text = path.read_text(encoding="utf-8")
            walkthrough = text.split("## Source Walkthrough", 1)[1].split("## DB Impact", 1)[0]
            assert "**File:**" in walkthrough
            assert list(CITATION_RE.finditer(walkthrough)) == []


# ---------------------------------------------------------------------------
# 4. build_source_to_fcode.py survives (and still maps) once § 5.4 / DB Impact
#    gain an Action column.
# ---------------------------------------------------------------------------

class TestBuildSourceToFcodeSurvivesActionColumn:
    def test_direct_parse_citations_unaffected_by_extra_column(self):
        """`_parse_citations` picks up the § 3 action rungs' `**Source:**` citations via its
        document-wide INLINE_SOURCE_RE scan -- a scan that never looks at table columns at
        all, so it cannot be broken by inserting `Action` into § 5.4 / DB Impact's header."""
        paths = _parse_citations(MIGRATED_CORRECT.read_text(encoding="utf-8"))
        assert paths == {
            "app/services/thing_service.rb:10-20",
            "app/services/thing_service.rb:25-27",
        }

    def test_build_index_still_maps_migrated_feature_to_its_fcode(self):
        with tempfile.TemporaryDirectory() as td:
            specs_root = Path(td) / "features"
            fdir = specs_root / "F900_SyntheticThing"
            fdir.mkdir(parents=True)
            (fdir / "technical-spec.md").write_text(
                MIGRATED_CORRECT.read_text(encoding="utf-8"), encoding="utf-8"
            )
            index = build_index(specs_root)
        assert index == {"app/services/thing_service.rb": ["F900"]}

    def test_section_scoped_table_cells_are_pre_existing_gap_not_a_new_regression(self):
        """§ 5.4's `Path` column and DB Impact's `Source` column both hold BARE backtick
        paths with no `**Source:**` label (matching the real corpus shape, e.g.
        F011_ListingModeration) -- `_parse_citations`'s section-scoped branch only fires
        under the RETIRED `## Source Code References` H2, which no longer exists in the
        v27 SOT shape (it is `### 5.4 Source References`, an H3). So neither table's cells
        were ever reachable by this script, identically in original.md AND
        migrated_correct.md -- the Action column changes nothing about that pre-existing
        gap either way. Documented here as an observed condition, out of this phase's
        file-ownership scope to fix (build_source_to_fcode.py is read-only for phase 08)."""
        before = _parse_citations(ORIGINAL.read_text(encoding="utf-8"))
        after = _parse_citations(MIGRATED_CORRECT.read_text(encoding="utf-8"))
        # Table-only cell paths absent from both -- e.g. the § 5.4 `thing_controller.rb:1-40`
        # symbol-table row is never picked up before OR after the Action column lands.
        assert "app/controllers/thing_controller.rb:1-40" not in before
        assert "app/controllers/thing_controller.rb:1-40" not in after


# ---------------------------------------------------------------------------
# 5. The phase's actual deliverable: coverage must not regress.
# ---------------------------------------------------------------------------

class TestNoRegressionOnMigratedFeature:
    def test_original_baseline_coverage(self):
        total, with_evidence, confidence = _coverage(ORIGINAL.read_text(encoding="utf-8"))
        assert (total, with_evidence, confidence) == (2, 1, 0.5)

    def test_migrated_correct_does_not_regress(self):
        """The settled `**Source:**` rung form: coverage on the migrated feature is >= the
        v27 original's -- the no-regression assertion the phase file names as its real
        deliverable. It in fact IMPROVES here because each action gained an explicit
        Source rung the pre-migration BR blocks didn't uniformly carry.

        Phase 03b (D10) update: A1's line 37 rung is a 2-hop CHAINED citation
        (`app/services/thing_service.rb:10-20` -> `app/controllers/thing_controller.rb:5`).
        Before the chained-citation fix, `extract_claims` only ever saw hop 1 (the
        `**Source:**`-prefixed one) -- the same structural blindness this phase exists
        to fix. Post-fix both hops count: 4 claims total (2 hops + 1 [INFERRED] + 1
        single-hop rung), 3 with evidence -- confidence 0.75, still >= the original's 0.5."""
        before_total, before_evidence, before_conf = _coverage(ORIGINAL.read_text(encoding="utf-8"))
        after_total, after_evidence, after_conf = _coverage(MIGRATED_CORRECT.read_text(encoding="utf-8"))

        assert (after_total, after_evidence, after_conf) == (4, 3, 0.75)
        assert after_conf >= before_conf
        assert after_evidence >= before_evidence

    def test_buggy_label_would_have_regressed_negative_control(self):
        """Negative control, never shipped: if the composer had used the B-v sample's
        original `**Source** · ...` rung head instead of the settled `**Source:**` form,
        coverage would have SILENTLY fallen from 0.5 to 0.0 -- both Source rungs vanish
        from the count, leaving only the one [INFERRED] marker claim. This is the exact
        failure this phase's no-regression test exists to catch before it ships."""
        before_total, before_evidence, before_conf = _coverage(ORIGINAL.read_text(encoding="utf-8"))
        buggy_total, buggy_evidence, buggy_conf = _coverage(
            MIGRATED_BUGGY_LABEL.read_text(encoding="utf-8")
        )

        assert (buggy_total, buggy_evidence, buggy_conf) == (1, 0, 0.0)
        assert buggy_conf < before_conf  # confirms it WOULD regress -- the point of the control
