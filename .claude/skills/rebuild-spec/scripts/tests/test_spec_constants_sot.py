"""P08 (human-readable SOT) — technical-spec.md's 5-bucket retaxonomy.

Covers what phase-08-technical-spec-shape.md's Todo List calls for:
  - _LEGACY_TECH_H2_5BUCKET is the exact 5-entry, ordered list from target-shape-spec.md § 3
    (originally public as `REQUIRED_H2_TECH`; retired to a private, migration-pipeline-only
    name in rebuild-spec 27.7.0 phase 10 — see below).
  - REQUIRED_CCL_H3 is retired outright (no longer importable from _spec_constants).
  - _LEGACY_SYSDESIGN_H3 (7) / REQUIRED_VERIF_H3 (5) are the exact, ordered replacements
    (originally public as `REQUIRED_SYSDESIGN_H3`; retired alongside `REQUIRED_H2_TECH`,
    same phase, same reason).
  - A3_HEADING / B4_HEADING stay their EXACT pre-P08 literal values — pinned with a comment
    naming the validator that depends on them staying literal, unnumbered H2s
    (validate_reading_guide_db_impact.py::_section_body does an exact-string match).
  - templates/technical-spec-template.md's own H2 sequence matches
    REQUIRED_H2_TECH_THREAD + [A3_HEADING, B4_HEADING] verbatim (full-sequence equality —
    the template's only top-level H2s; repointed from the legacy 5-bucket list in phase 04/09
    once the template itself moved to the action-thread shape), and its § 3 / § 5 H3
    sequences contain REQUIRED_APPENDIX_H3 / REQUIRED_VERIF_H3 in order (MEMBERSHIP-filtered,
    not raw full-sequence equality — § 3 and § 5 legitimately also carry real SM-###/ALG-###/
    INT-### example blocks as sibling H3s, same convention the old `ccl_subsections`
    check used for `present_ccl = [h for h in names if h in REQUIRED_CCL_H3]`, and the
    same convention § 4's `### {Rule} (BR-001)` example already relies on).
  - The template carries no per-US narrative-description field anywhere (T-12's guarded
    removal — the field this repo used to call "**What happens:**").

This phase does NOT touch validate_feature_spec.py / scaffold_spec.py — those still import
the now-deleted REQUIRED_CCL_H3 (P09's job; see reports/p08-handoff-to-p09.md for the full
importer list and the red suite this deletion knowingly leaves behind until P09 lands).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[5]
TEMPLATE = SCRIPTS_DIR.parent / "templates" / "technical-spec-template.md"

sys.path.insert(0, str(SCRIPTS_DIR))

from _spec_constants import (  # noqa: E402
    ACTION_HEADING_RE,
    ACTION_ID_RE,
    A3_HEADING,
    B4_HEADING,
    REQUIRED_APPENDIX_H3,
    REQUIRED_H2_TECH_THREAD,
    REQUIRED_VERIF_H3,
    RUNG_LABELS,
    _LEGACY_SYSDESIGN_H3,
    _LEGACY_TECH_H2_5BUCKET,
)
from _spec_parse import parse_headings_and_blocks  # noqa: E402

# ---------------------------------------------------------------------------
# target-shape-spec.md § 3 — normative, verbatim (this IS the source of truth
# copied into _spec_constants.py; this literal catches drift in either file).
# ---------------------------------------------------------------------------
_EXPECTED_LEGACY_TECH_H2_5BUCKET = [
    "## 1. Technical Overview",
    "## 2. Functional → Technical Mapping",
    "## 3. System Design",
    "## 4. Technical Behavior by Capability",
    "## 5. Verification & Technical Notes",
]

_EXPECTED_LEGACY_SYSDESIGN_H3 = [
    "### 3.1 Components",
    "### 3.2 Data Model",
    "### 3.3 State Management",
    "### 3.4 API & Endpoints",
    "### 3.5 Algorithms & Processing Logic",
    "### 3.6 Integrations",
    "### 3.7 Configuration",
]

_EXPECTED_REQUIRED_VERIF_H3 = [
    "### 5.1 Technical Verification",
    "### 5.2 Assumptions",
    "### 5.3 Unresolved Questions",
    "### 5.4 Source References",
    "### 5.5 Artifact References",
]

# Pre-P08 literal values — MUST NOT change. validate_reading_guide_db_impact.py::_section_body
# matches these two strings as EXACT, unnumbered H2 headings; numbering or nesting either one
# makes that validator read the section as ABSENT (a silent WARN under the A3/B4 degradation
# contract), which is worse than a loud failure. See target-shape-spec.md § 1.3 / § 3.
_EXPECTED_A3_HEADING = "## Source Walkthrough"
_EXPECTED_B4_HEADING = "## DB Impact per Event"

# ---------------------------------------------------------------------------
# rebuild-spec 27.7.0 (action-thread reshape) — phase-01-shape-constants.md § Requirements,
# normative. `REQUIRED_H2_TECH_THREAD` is now THE required shape (phase 10 repointed
# `FeatureSpec.required_sections` at it and retired the old public name outright — see
# `_spec_constants.py`'s note on `_LEGACY_TECH_H2_5BUCKET`, which is what the layer-first
# list above is called now).
# ---------------------------------------------------------------------------
_EXPECTED_REQUIRED_H2_TECH_THREAD = [
    "## 1. Technical Overview",
    "## 2. Action Index",
    "## 3. Actions",
    "## 4. Shared Foundation",
    "## 5. Verification & Technical Notes",
]

# Replaces `_LEGACY_SYSDESIGN_H3` (§ 3 System Design's layer-first subsections) with § 4
# Shared Foundation's action-thread subsections. `_LEGACY_SYSDESIGN_H3` is NOT deleted —
# `_feature_sot_extract_lib.py`/`_feature_sot_structure_lib.py` still need it forever (the
# `feature-sot` migrate step's own permanent output/input shape) — only retired as a public
# name (phase 10).
_EXPECTED_REQUIRED_APPENDIX_H3 = [
    "### 4.1 Components",
    "### 4.2 Data Model",
    "### 4.3 State Management",
    "### 4.4 Shared Rules",
    "### 4.5 Algorithms & Integrations",
    "### 4.6 Configuration",
]

# Rung order is the contract (validator checks relative order of the rungs that ARE
# present); presence is not (an absent rung is simply not rendered — no "N/A" placeholder).
# "State" (phase 01, self-sufficiency v27.8) sits before "Source" -- Source stays last.
_EXPECTED_RUNG_LABELS = ("Who", "FE", "Request", "BE", "Rule", "Result", "State", "Source")


def _h2_and_headings(lines: list[str]):
    headings, _blocks = parse_headings_and_blocks(lines)
    h2 = [(i, h) for i, h in headings if h.startswith("## ") and not h.startswith("### ")]
    return h2, headings


def _bounds(h2: list[tuple[int, str]], name: str, total: int) -> tuple[int, int] | None:
    for i, (idx, h) in enumerate(h2):
        if h == name:
            return idx + 1, (h2[i + 1][0] if i + 1 < len(h2) else total)
    return None


# ===========================================================================
# Section A — constant shape, exact order, exact count
# ===========================================================================

class TestLegacyTechH2FiveBucketShape:
    """Was `TestRequiredH2TechShape` / `REQUIRED_H2_TECH` — renamed in step with the
    constant's own phase-10 retirement to a private, migration-pipeline-only name.
    Still pinned: `_LEGACY_TECH_H2_5BUCKET` is the `feature-sot` migrate step's permanent
    output shape, not dead code."""

    def test_five_entries_exact_order(self):
        assert _LEGACY_TECH_H2_5BUCKET == _EXPECTED_LEGACY_TECH_H2_5BUCKET

    def test_exactly_five_entries(self):
        assert len(_LEGACY_TECH_H2_5BUCKET) == 5

    def test_old_nine_section_strings_are_gone(self):
        """Full-set replacement, not an incremental rename (phase-08 Key Insights) — every
        one of the 9 old exact strings must be absent from the new list."""
        old = {
            "## Overview",
            "## Polymorphic Behavior",
            "## Cross-Cutting Logic",
            "## User Stories",
            "## Key Entities",
            "## Artifact References",
            "## Assumptions",
            "## Source Code References",
            "## Unresolved Questions",
        }
        assert old.isdisjoint(set(_LEGACY_TECH_H2_5BUCKET))


class TestRequiredCclH3Retired:
    def test_required_ccl_h3_no_longer_importable(self):
        """REQUIRED_CCL_H3 must be gone from the module outright — not renamed, not
        aliased, not left as an empty list. A future re-introduction under any name that
        still equals the old 7-entry CCL set is exactly what TestRequiredH2ListSingleSource
        (test_spec_constants_single_source.py) guards against for the H2 lists; this test
        guards the H3 constant's own removal."""
        import _spec_constants as sc

        assert not hasattr(sc, "REQUIRED_CCL_H3")


class TestLegacySysdesignH3Shape:
    """Was `TestRequiredSysdesignH3Shape` / `REQUIRED_SYSDESIGN_H3` — renamed alongside the
    constant's phase-10 retirement to a private, migration-pipeline-only name."""

    def test_seven_entries_exact_order(self):
        assert _LEGACY_SYSDESIGN_H3 == _EXPECTED_LEGACY_SYSDESIGN_H3

    def test_exactly_seven_entries(self):
        assert len(_LEGACY_SYSDESIGN_H3) == 7


class TestRequiredVerifH3Shape:
    def test_five_entries_exact_order(self):
        assert REQUIRED_VERIF_H3 == _EXPECTED_REQUIRED_VERIF_H3

    def test_exactly_five_entries(self):
        assert len(REQUIRED_VERIF_H3) == 5


class TestA3B4LiteralsUnchanged:
    """Pin — a future edit to either literal has to argue with a red test here, per
    phase-08's explicit Requirements bullet. See validate_reading_guide_db_impact.py's
    own test file for the consumer-side proof these stay untouched end to end."""

    def test_a3_heading_unchanged(self):
        assert A3_HEADING == _EXPECTED_A3_HEADING

    def test_b4_heading_unchanged(self):
        assert B4_HEADING == _EXPECTED_B4_HEADING

    def test_neither_in_required_h2_tech(self):
        assert A3_HEADING not in _LEGACY_TECH_H2_5BUCKET
        assert B4_HEADING not in _LEGACY_TECH_H2_5BUCKET
        assert A3_HEADING not in REQUIRED_H2_TECH_THREAD
        assert B4_HEADING not in REQUIRED_H2_TECH_THREAD


# ===========================================================================
# Section B — template anti-drift
# ===========================================================================

class TestTemplateAntiDrift:
    def _lines(self) -> list[str]:
        return TEMPLATE.read_text(encoding="utf-8").splitlines()

    def _h2_sequence(self) -> list[str]:
        lines = self._lines()
        h2, _ = _h2_and_headings(lines)
        return [h for _, h in h2]

    def _h3_sequence_in(self, h2_name: str) -> list[str]:
        """All H3s inside *h2_name*'s bounds — includes non-required example headings
        (e.g. `### {Algorithm...} (ALG-001)`), same as the real document."""
        lines = self._lines()
        h2, headings = _h2_and_headings(lines)
        b = _bounds(h2, h2_name, len(lines))
        assert b is not None, f"{h2_name!r} not found in template"
        h3 = [(idx, h) for idx, h in headings
              if h.startswith("### ") and not h.startswith("#### ")]
        return [h for idx, h in h3 if b[0] <= idx < b[1]]

    def _required_members_in_order(self, h2_name: str, required: list[str]) -> list[str]:
        """Membership-filtered order check — mirrors how `ccl_subsections` compared
        `present_ccl = [h for h in names if h in REQUIRED_CCL_H3]` against the constant,
        rather than demanding the section contain ONLY required headings. § 3 and § 5
        legitimately also carry real SM-###/ALG-###/INT-### example blocks as extra
        sibling H3s (content-preservation-map T-06/T-07/T-08), exactly as § 4 already
        carries an extra `### {Rule} (BR-001)` example alongside its dynamic `### 4.N`."""
        return [h for h in self._h3_sequence_in(h2_name) if h in required]

    # rebuild-spec 27.7.0 (action-thread reshape, phase 04): the template was rewritten to
    # the action-thread shape (phase 09) — its H2 sequence and § 3/§ 4 no longer match the
    # legacy `_LEGACY_TECH_H2_5BUCKET`/`_LEGACY_SYSDESIGN_H3` (§ 3 is now `## 3. Actions`,
    # not `## 3. System Design`; § 4 Shared Foundation carries the appendix H3s). Checked
    # against `REQUIRED_H2_TECH_THREAD`/`REQUIRED_APPENDIX_H3` — the current shape, since
    # phase 10 repointed `FeatureSpec.required_sections` at the same constant.
    # Phase 08 (self-sufficiency v27.8): A3 (`## Source Walkthrough`) / B4
    # (`## DB Impact per Event`) RETIRED from the template's own shape — the
    # template's H2 sequence is now EXACTLY REQUIRED_H2_TECH_THREAD, no trailing
    # literal headings after it.
    def test_template_h2_sequence_matches_constant(self):
        assert self._h2_sequence() == REQUIRED_H2_TECH_THREAD

    def test_template_no_longer_carries_a3_or_b4(self):
        assert A3_HEADING not in self._h2_sequence()
        assert B4_HEADING not in self._h2_sequence()

    def test_anti_drift_h2_comparison_actually_discriminates(self):
        """Self-test: a template H2 sequence missing one section must NOT compare equal —
        proves the assertion above would fail loudly on a real drift (repo precedent:
        test_functional_spec_sot_sections.py::test_anti_drift_comparison_actually_discriminates)."""
        drifted = [h for h in self._h2_sequence() if h != "## 4. Shared Foundation"]
        assert drifted != REQUIRED_H2_TECH_THREAD

    def test_template_sysdesign_h3_members_present_in_order(self):
        assert self._required_members_in_order(
            "## 4. Shared Foundation", REQUIRED_APPENDIX_H3
        ) == REQUIRED_APPENDIX_H3

    def test_anti_drift_sysdesign_h3_comparison_actually_discriminates(self):
        drifted = [h for h in self._required_members_in_order("## 4. Shared Foundation", REQUIRED_APPENDIX_H3)
                   if h != "### 4.6 Configuration"]
        assert drifted != REQUIRED_APPENDIX_H3

    def test_template_verif_h3_members_present_in_order(self):
        assert self._required_members_in_order(
            "## 5. Verification & Technical Notes", REQUIRED_VERIF_H3
        ) == REQUIRED_VERIF_H3

    def test_anti_drift_verif_h3_comparison_actually_discriminates(self):
        drifted = [h for h in self._required_members_in_order(
            "## 5. Verification & Technical Notes", REQUIRED_VERIF_H3)
                   if h != "### 5.5 Artifact References"]
        assert drifted != REQUIRED_VERIF_H3

    def test_sysdesign_extras_are_real_example_blocks_not_stray_required_lookalikes(self):
        """Documents WHY § 4 has more H3s than REQUIRED_APPENDIX_H3: every extra is a
        genuine SM-###/ALG-###/INT-### example block (content-preservation-map T-06/T-07/
        T-08), not an accidental near-duplicate of a required heading."""
        extras = [h for h in self._h3_sequence_in("## 4. Shared Foundation")
                  if h not in REQUIRED_APPENDIX_H3]
        assert extras, "expected the SM-001/SM-002/ALG-001/INT-001 example blocks"
        for h in extras:
            assert re.search(r"\((SM|ALG|INT)-\d{3}\)\s*$", h), h


class TestNoPerUsNarrativeField:
    """T-12 (content-preservation-map.md): the retired per-US narrative-description field
    (this repo's old '**What happens:**' block opener) must not survive anywhere in the
    template — removal is guarded (twin functional-spec.md § 7 must carry the US### code)
    but the guard is migrate-composer logic (P10), never a static template field."""

    def test_template_has_zero_what_happens_occurrences(self):
        text = TEMPLATE.read_text(encoding="utf-8")
        assert text.count("What happens") == 0

    def test_template_has_zero_bold_what_happens_field(self):
        text = TEMPLATE.read_text(encoding="utf-8")
        assert "**What happens:**" not in text


# ===========================================================================
# Section C — rebuild-spec 27.7.0 action-thread reshape (phase-01-shape-constants.md)
# ===========================================================================

class TestRequiredH2TechThreadShape:
    def test_five_entries_exact_order(self):
        assert REQUIRED_H2_TECH_THREAD == _EXPECTED_REQUIRED_H2_TECH_THREAD

    def test_exactly_five_entries(self):
        assert len(REQUIRED_H2_TECH_THREAD) == 5

    def test_legacy_required_h2_tech_is_byte_identical_and_distinct(self):
        """Phase 10 renamed the legacy list's PUBLIC name (`REQUIRED_H2_TECH` ->
        `_LEGACY_TECH_H2_5BUCKET`), never its VALUE — proves the value stays exactly as it
        already was, and the two lists are genuinely different constants."""
        assert _LEGACY_TECH_H2_5BUCKET == _EXPECTED_LEGACY_TECH_H2_5BUCKET
        assert REQUIRED_H2_TECH_THREAD != _LEGACY_TECH_H2_5BUCKET

    def test_anti_drift_comparison_actually_discriminates(self):
        drifted = [h for h in REQUIRED_H2_TECH_THREAD if h != "## 2. Action Index"]
        assert drifted != _EXPECTED_REQUIRED_H2_TECH_THREAD


class TestRequiredAppendixH3Shape:
    def test_six_entries_exact_order(self):
        assert REQUIRED_APPENDIX_H3 == _EXPECTED_REQUIRED_APPENDIX_H3

    def test_exactly_six_entries(self):
        assert len(REQUIRED_APPENDIX_H3) == 6

    def test_legacy_required_sysdesign_h3_untouched(self):
        """`_LEGACY_SYSDESIGN_H3` (phase 10's private rename of `REQUIRED_SYSDESIGN_H3`) is
        value-preserved, not deleted — `_feature_sot_extract_lib.py`/
        `_feature_sot_structure_lib.py` still need it permanently — proves this test file's
        own earlier TestLegacySysdesignH3Shape assertions still hold unchanged."""
        assert _LEGACY_SYSDESIGN_H3 == _EXPECTED_LEGACY_SYSDESIGN_H3

    def test_anti_drift_comparison_actually_discriminates(self):
        drifted = [h for h in REQUIRED_APPENDIX_H3 if h != "### 4.4 Shared Rules"]
        assert drifted != _EXPECTED_REQUIRED_APPENDIX_H3


class TestRungLabelsShape:
    def test_exact_order_and_length(self):
        assert RUNG_LABELS == _EXPECTED_RUNG_LABELS
        assert len(RUNG_LABELS) == 8

    def test_is_a_tuple_not_a_mutable_list(self):
        assert isinstance(RUNG_LABELS, tuple)

    def test_anti_drift_order_comparison_discriminates(self):
        drifted = tuple(reversed(RUNG_LABELS))
        assert drifted != _EXPECTED_RUNG_LABELS


class TestTechPreThreadSentinel:
    """`_TECH_PRE_THREAD_SENTINEL` mirrors `_TECH_PRE_SOT_SENTINEL`'s design exactly (same
    pattern, not a third one, per phase-01's Requirements): it is the OLD shape's own
    distinguishing heading — never present in the new action-thread shape — not the
    absence of a new heading. `## 3. System Design` is retired outright by the reshape
    (the new § 3 is `## 3. Actions`), so its presence unambiguously marks a still-old-shaped
    file, gating the D4 WARN-first degradation window later phases wire up."""

    def test_sentinel_value(self):
        import _spec_constants as sc

        assert sc._TECH_PRE_THREAD_SENTINEL == "## 3. System Design"

    def test_sentinel_present_only_in_legacy_shape(self):
        import _spec_constants as sc

        assert sc._TECH_PRE_THREAD_SENTINEL in _LEGACY_TECH_H2_5BUCKET
        assert sc._TECH_PRE_THREAD_SENTINEL not in REQUIRED_H2_TECH_THREAD


class TestActionHeadingRe:
    """`ACTION_HEADING_RE` anchors the H4 spine of `## 3. Actions`: `#### A<id> · <name>`."""

    def test_matches_action_heading_and_captures_id(self):
        m = re.match(ACTION_HEADING_RE, "#### A12 · Approve Listing")
        assert m is not None
        assert m.group(1) == "A12"

    def test_does_not_match_without_the_separator(self):
        assert re.match(ACTION_HEADING_RE, "#### A12 Approve Listing") is None

    def test_does_not_match_an_h3(self):
        assert re.match(ACTION_HEADING_RE, "### A12 · Approve Listing") is None

    def test_does_not_match_an_h5(self):
        assert re.match(ACTION_HEADING_RE, "##### A12 · Approve Listing") is None


class TestActionIdReBoundaryHazard:
    """Repo precedent: a trailing `\\b` regex boundary has caused this exact hazard 7 times
    across 3 variants (see agent memory `regex-code-boundary-hazard`) — `_` is a word
    character, so `\\bA\\d+\\b` silently fails to match inside a slug like `A1_Slug`, and
    `(?!\\d)` rejects a *digit* coming next, not a *letter*, so `A1x` still matches `A1`
    (documented, not a bug). One test per variant per the phase file's Risk Assessment.

    Fail-direction trace: ACTION_ID_RE is the single-source pattern later phases will read
    to find bare action-ID tokens quoted in prose or table cells (an Action Index
    cross-reference, or an anchor slug carrying the ID as its prefix). A false NEGATIVE here
    (the regex fails to match a genuine ID) is SILENT: the token simply disappears from
    whatever is counting citations. That fails OPEN for a coverage/binding check (it
    under-counts how much is actually cited, understating the real binding — the exact
    failure this reshape exists to fix, per plan.md's "84% of actions have no attributable
    rule" measurement) while it fails CLOSED for an orphan/unclaimed-ID check built on the
    same miss (it would wrongly flag a genuinely-referenced ID as unclaimed). A trailing
    `\\b` produces precisely that silent miss on any slug-suffixed anchor; `(?!\\d)` does
    not, which is why it — not `\\b` — is this repo's required convention.
    """

    def test_bare_id_matches(self):
        m = re.search(ACTION_ID_RE, "A1")
        assert m is not None
        assert m.group() == "A1"

    def test_does_not_collapse_a10_to_a1(self):
        m = re.search(ACTION_ID_RE, "A10")
        assert m is not None
        assert m.group() == "A10"

    def test_matches_inside_a_slug_where_a_trailing_word_boundary_would_have_missed_it(self):
        m = re.search(ACTION_ID_RE, "A1_Slug")
        assert m is not None
        assert m.group() == "A1"

    def test_naive_trailing_word_boundary_variant_silently_misses_the_slug(self):
        """Proves the hazard ACTION_ID_RE guards against: the naive `\\bA\\d+\\b` variant
        (trailing `\\b` instead of `(?!\\d)`) finds NOTHING inside `A1_Slug`, because `_`
        is a word character and creates no boundary right after the digit."""
        naive_trailing_word_boundary = r"\bA\d+\b"
        assert re.search(naive_trailing_word_boundary, "A1_Slug") is None

    def test_a_following_letter_is_not_rejected_only_a_following_digit_is(self):
        """`(?!\\d)` rejects a *digit* next, not a *letter* — the other half of the
        hazard: `A1x` still matches `A1` (a letter after the digits is fine), unlike a
        digit, which extends the match instead of stopping it (see test above)."""
        m = re.search(ACTION_ID_RE, "A1x")
        assert m is not None
        assert m.group() == "A1"

    def test_no_spurious_match_inside_a_longer_word(self):
        assert re.search(ACTION_ID_RE, "BA12") is None
