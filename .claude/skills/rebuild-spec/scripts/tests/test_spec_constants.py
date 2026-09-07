"""Tests for _spec_constants.py.

F8 (v26.0.0, acsim-learnings phase-03): permanent regression guarding Decision 2 — the two
new A3/B4 headings must NEVER be added to any exact-order required-H2 list (REQUIRED_H2_TECH_
THREAD, its legacy predecessor _LEGACY_TECH_H2_5BUCKET, or REQUIRED_H2_FUNC — those checks
have no degradation window; A3/B4 are gated by a dedicated validator instead).

v27.0.0 (audience split): REQUIRED_H2_BC/REQUIRED_H2_SCR are retired (business-context.md/
screens.md are gone) — REQUIRED_H2_FUNC (functional-spec.md's required-section list, 13
entries as of the P07 human-readable SOT renumber) is their single-source replacement and
inherits the same guard.

v27.x (P09, human-readable SOT retaxonomy): REQUIRED_CCL_H3 was retired outright by P08
(`## Cross-Cutting Logic` no longer exists) — its two A3/B4 guard tests below are gone with
it. The replacement guard against the two NEW H3 constants
(REQUIRED_SYSDESIGN_H3/REQUIRED_VERIF_H3) lives in
test_spec_constants_sot.py::TestRequiredCclH3Retired, which asserts the constant is gone
outright rather than merely "doesn't contain A3/B4" — a stronger guarantee, not a gap.

rebuild-spec 27.7.0 (phase 10, action-thread reshape): `REQUIRED_H2_TECH` was retired as a
public name (see `_spec_constants.py`'s own note on `_LEGACY_TECH_H2_5BUCKET`) and
`REQUIRED_H2_TECH_THREAD` is now the current shape `FeatureSpec.required_sections` checks —
this guard now covers BOTH lists, since both are still real "no degradation window"
exact-order checks (the legacy list via the migration pipeline's own internal parsing).
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

from _spec_constants import (  # noqa: E402
    A3_HEADING,
    B4_HEADING,
    REQUIRED_H2_FUNC,
    REQUIRED_H2_TECH_THREAD,
    _LEGACY_TECH_H2_5BUCKET,
)


class TestF8RegressionGuard:
    def test_a3_heading_not_in_required_h2_tech_thread(self):
        assert A3_HEADING not in REQUIRED_H2_TECH_THREAD

    def test_b4_heading_not_in_required_h2_tech_thread(self):
        assert B4_HEADING not in REQUIRED_H2_TECH_THREAD

    def test_a3_heading_not_in_legacy_tech_h2_5bucket(self):
        assert A3_HEADING not in _LEGACY_TECH_H2_5BUCKET

    def test_b4_heading_not_in_legacy_tech_h2_5bucket(self):
        assert B4_HEADING not in _LEGACY_TECH_H2_5BUCKET

    def test_a3_heading_not_in_required_h2_func(self):
        assert A3_HEADING not in REQUIRED_H2_FUNC

    def test_b4_heading_not_in_required_h2_func(self):
        assert B4_HEADING not in REQUIRED_H2_FUNC

    def test_headings_are_distinct_top_level_h2(self):
        assert A3_HEADING.startswith("## ")
        assert B4_HEADING.startswith("## ")
        assert A3_HEADING != B4_HEADING
