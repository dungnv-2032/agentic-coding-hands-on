"""Characterization tests pinning Mode C's two silent-breakage traps (blast-radius
report §1/§3): the `migrate_screen` re-entry predicate and `resolve_layout_rule_ids`'s
marker-based BA/dev split. Neither is validator-backed today -- if either literal
string drifts, the failure is SILENT (wrong classification, no exception, no exit
code), which is exactly why Phase 02 pins them as explicit assertions before Phase 03
(new marker text) and Phase 05 (new section order) touch this area.

Two invariants, in the words of the phase file:

  1. `migrate_screen`'s re-entry guard is the literal substring test
     `"## Screen Layout" not in old_text`. The upcoming SOT shape numbers this heading
     `## 2. Screen Layout`, which does NOT contain that substring -- so a SOT-shaped
     document takes the `confirmed-v27` no-op branch (declines to re-reorder) under the
     CURRENT code, with no change needed to reach that outcome. This must be an
     assertion, not a comment, because Phase 05 changes section order and a silent
     regression here would either loop forever re-migrating SOT docs or corrupt them.

  2. `resolve_layout_rule_ids` splits `new_text` on the literal `DEV_APPENDIX_MARKER`
     text to decide which half of the document is BA and which is dev appendix. This
     coupling is exact-substring-based and unenforced by any validator: a near-miss
     (wrong split point, or no split point) does not raise -- it silently reclassifies
     BA content as dev-appendix-body-not-found (or vice versa).

All fixtures used where the phase file calls for real corpus input come from
`fixtures/sot-corpus/corpus-g1/` (v26 shape, `## Screen Layout` present) and
`corpus-g2/` (v27 shape, already reordered) -- both are real generated output, not
hand-typed substitutes. They were copied out of
`plans/260818-1332-rebuild-spec-human-readable-sot/evidence/` because `plans/` is
gitignored and the module-level reads below then failed collection on every CI run;
see `fixtures/sot-corpus/README.md` for provenance.
"""
from __future__ import annotations

import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from _audience_split_mode_c_lib import (  # noqa: E402
    DEV_APPENDIX_MARKER,
    LAYOUT_REGIONS_H3,
    LAYOUT_SKETCH_H3,
    compose_mode_c,
    resolve_layout_rule_ids,
)
from _audience_split_orchestrate_bc_lib import migrate_screen  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[5]  # agent-kit/
_SOT_CORPUS = Path(__file__).resolve().parent / "fixtures" / "sot-corpus"
"""Real generated corpus, git-tracked. Lived under `plans/` (gitignored) until it took
the whole CI suite down at collection time — see fixtures/sot-corpus/README.md."""
EVIDENCE_DIR = (
    _SOT_CORPUS
)
CORPUS_G1 = EVIDENCE_DIR / "corpus-g1"
CORPUS_G2 = EVIDENCE_DIR / "corpus-g2"

_G1_V26_TEXT = (CORPUS_G1 / "SCR001_Login.spec.md").read_text(encoding="utf-8")
_G2_TEXTS = {
    "SCR020_LoginPage.spec.md": (CORPUS_G2 / "SCR020_LoginPage.spec.md").read_text(encoding="utf-8"),
    "SCR012_ErrorNotFound.spec.md": (CORPUS_G2 / "SCR012_ErrorNotFound.spec.md").read_text(encoding="utf-8"),
}


# --------------------------------------------------------------------------- #
# Invariant 1a -- the substring fact itself, on real fixtures of each shape.
# --------------------------------------------------------------------------- #
def test_v26_real_fixture_contains_screen_layout_heading():
    assert "## Screen Layout" in _G1_V26_TEXT


def test_v27_real_fixtures_do_not_contain_screen_layout_heading():
    for name, text in _G2_TEXTS.items():
        assert "## Screen Layout" not in text, name


def test_sot_numbered_heading_does_not_contain_the_reentry_substring():
    # The core substring fact this invariant depends on: "## Screen Layout" is not a
    # substring of "## 2. Screen Layout" because of the inserted "2. " -- this is what
    # lets a future SOT-numbered document take the confirmed-v27 (decline) branch
    # under the CURRENT predicate, with zero code changes.
    assert "## Screen Layout" not in "## 2. Screen Layout"


# --------------------------------------------------------------------------- #
# Invariant 1b -- compose_mode_c's own output satisfies the re-entry guard (the
# guard this module's docstring calls "the whole point": prevents an infinite
# re-migration loop).
# --------------------------------------------------------------------------- #
def test_compose_mode_c_output_no_longer_contains_screen_layout_heading():
    new_text = compose_mode_c(_G1_V26_TEXT)
    assert "## Screen Layout" not in new_text


def test_compose_mode_c_output_on_real_fixture_resolves_both_rule_ids_clean():
    new_text = compose_mode_c(_G1_V26_TEXT)
    assert resolve_layout_rule_ids(new_text) == []


def test_real_v27_fixtures_resolve_both_rule_ids_clean():
    # Sanity check that the invariant holds on independently-produced real output too,
    # not just on this module's own compose_mode_c() round-trip.
    for name, text in _G2_TEXTS.items():
        assert resolve_layout_rule_ids(text) == [], name


# --------------------------------------------------------------------------- #
# Invariant 2 -- migrate_screen's re-entry predicate, exercised end-to-end against a
# minimal SOT-shaped document containing BOTH the numbered heading and the (as yet
# unbuilt) second marker `## Technical Appendix` this plan will introduce later.
# `migrate_screen` takes the `confirmed-v27` branch (its guard is checked before the
# hand-edit probe runs), so no git repo is required for this test.
# --------------------------------------------------------------------------- #
_SOT_SHAPED_DOC = """---
authored_by: rebuild-spec
---
# SCR999_Sample — Screen Spec

## 1. Purpose

A future SOT-numbered screen spec.

## 2. Screen Layout

### Layout Sketch

A sketch that lives under the numbered heading.

## 3. User Flow

1. User does a thing.

---

## Technical Appendix

### Layout Regions

| Region ID | Name | Position | Scrollable | Key Components | Responsive Behavior |
|-----------|------|----------|------------|----------------|---------------------|
| R1 | Header | fixed-top | no | Header | always |
"""


def test_migrate_screen_declines_sot_shaped_doc_via_confirmed_v27(tmp_path):
    docs_root = tmp_path / "docs"
    screen_dir = docs_root / "screens" / "SCR999_Sample"
    screen_dir.mkdir(parents=True)
    spec_path = screen_dir / "spec.md"
    spec_path.write_text(_SOT_SHAPED_DOC, encoding="utf-8")
    before = spec_path.read_bytes()

    outcome = migrate_screen(screen_dir, tmp_path, docs_root)

    assert outcome.action == "confirmed-v27", outcome.message
    assert outcome.exit_ok
    after = spec_path.read_bytes()
    assert before == after  # byte-identical: migrate_screen never rewrote the file


# --------------------------------------------------------------------------- #
# Invariant 2 continued -- resolve_layout_rule_ids on well-formed vs. broken bodies,
# asserting the SPECIFIC rule_id string that fires (not just truthiness), derived by
# mutating a real fixture rather than hand-building a document from scratch.
# --------------------------------------------------------------------------- #
_BASE_TEXT = _G2_TEXTS["SCR020_LoginPage.spec.md"]


def test_resolve_layout_rule_ids_clean_on_well_formed_reordered_doc():
    assert resolve_layout_rule_ids(_BASE_TEXT) == []


def test_resolve_layout_rule_ids_fires_sketch_missing_when_h3_absent():
    mutated = _BASE_TEXT.replace(LAYOUT_SKETCH_H3, "### Renamed Sketch")
    assert resolve_layout_rule_ids(mutated) == ["screen.layout_sketch_missing"]


def test_resolve_layout_rule_ids_fires_sketch_missing_when_body_bare_na():
    idx = _BASE_TEXT.index(LAYOUT_SKETCH_H3)
    idx_next = _BASE_TEXT.index("## User Flow")
    mutated = _BASE_TEXT[:idx] + LAYOUT_SKETCH_H3 + "\n\nN/A\n\n" + _BASE_TEXT[idx_next:]
    assert resolve_layout_rule_ids(mutated) == ["screen.layout_sketch_missing"]


def test_resolve_layout_rule_ids_fires_regions_missing_when_h3_absent():
    mutated = _BASE_TEXT.replace(LAYOUT_REGIONS_H3, "### Renamed Regions")
    assert resolve_layout_rule_ids(mutated) == ["screen.layout_regions_missing"]


def test_resolve_layout_rule_ids_fires_regions_missing_when_body_bare_na():
    idx = _BASE_TEXT.index(LAYOUT_REGIONS_H3)
    idx_next = _BASE_TEXT.index("## Security Surface")
    mutated = _BASE_TEXT[:idx] + LAYOUT_REGIONS_H3 + "\n\nN/A\n\n" + _BASE_TEXT[idx_next:]
    assert resolve_layout_rule_ids(mutated) == ["screen.layout_regions_missing"]


def test_resolve_layout_rule_ids_fires_regions_missing_when_marker_absent_entirely():
    # Reaches the branch where DEV_APPENDIX_MARKER is not in new_text at all: dev_text
    # becomes "" (per the `if DEV_APPENDIX_MARKER in new_text else ""` fallback), so
    # Layout Regions -- which is real and populated in the base fixture -- can never be
    # found. This is the "marker moves, function splits into the wrong halves" trap
    # from the blast-radius report, in its most direct form: no marker, no dev half.
    mutated = _BASE_TEXT.replace(DEV_APPENDIX_MARKER, "")
    assert resolve_layout_rule_ids(mutated) == ["screen.layout_regions_missing"]


def test_resolve_layout_rule_ids_misreads_split_when_marker_appears_twice():
    # Reaches the same trap from its OTHER direction: `str.split()` on a marker that
    # occurs twice yields 3 parts; `[-1]` (the code the function itself uses) is
    # everything after the SECOND occurrence, not the first -- silently losing the
    # real Layout Regions section that lived between the two markers.
    mutated = _BASE_TEXT + "\n\n" + DEV_APPENDIX_MARKER
    assert resolve_layout_rule_ids(mutated) == ["screen.layout_regions_missing"]


# --------------------------------------------------------------------------- #
# Invariant 2 continued -- the marker-drift trap in its most literal form: a
# near-miss on `DEV_APPENDIX_MARKER`'s exact text (e.g. a future rewording of the
# italic dev-appendix sentence somewhere upstream, WITHOUT updating this constant)
# causes a SILENT misclassification, not an error. This test pins that today's
# coupling is exact-substring, so it starts failing the moment the coupling is
# loosened -- which is the point: it is itself the regression detector.
# --------------------------------------------------------------------------- #
def test_marker_near_miss_causes_silent_misdetection_not_an_error():
    near_miss_marker = DEV_APPENDIX_MARKER.replace("BA/QA readers", "BA readers")
    assert near_miss_marker != DEV_APPENDIX_MARKER
    mutated = _BASE_TEXT.replace(DEV_APPENDIX_MARKER, near_miss_marker)
    # No exception is raised; the split silently fails to find the real marker, and
    # the populated Layout Regions section (present in `mutated`) is reported missing.
    assert resolve_layout_rule_ids(mutated) == ["screen.layout_regions_missing"]


# --------------------------------------------------------------------------- #
# Marker-disjointness -- DEV_APPENDIX_MARKER and the plan's second, forthcoming
# marker `## Technical Appendix` must never be substrings of each other, so a
# document carrying both (as Phase 03+ corpora will) can never confuse either
# splitter into finding one where the other lives.
# --------------------------------------------------------------------------- #
def test_dev_appendix_marker_and_technical_appendix_marker_are_disjoint():
    technical_appendix_marker = "## Technical Appendix"
    assert technical_appendix_marker not in DEV_APPENDIX_MARKER
    assert DEV_APPENDIX_MARKER not in technical_appendix_marker
