"""[AD-6] Pinning test — `_cap_map_lib.py` (this skill's SANCTIONED second § 2 parser, phase 09
of plans/260819-1016-rebuild-spec-capability-map) must agree with rebuild-spec's
`_cap_table_lib.py` on the same input. A divergence here is a FAILING TEST, never two silently
different answers in two reports.

Fixture header is byte-identical to rebuild-spec's
`scripts/tests/test_cap_table_lib.py::_HEADER`. The two-row claim shape mirrors
`scripts/tests/test_functional_spec_sot_sections.py::TestDoubleClaimed
.test_fires_when_code_claimed_twice` (a code claimed by two rows) plus a multi-US cell, so the
comparison exercises per-row grouping, not just single-code presence.

Style follows the existing `test_citation_lib_parity.py` precedent for this skill: a
`skipif`-guarded class so the suite still passes when rebuild-spec is not installed alongside
this skill, even though in THIS repo it always is.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SCRIPTS))
import _cap_map_lib as cap_map  # noqa: E402

_REBUILD_SPEC_SCRIPTS = _SCRIPTS.parent.parent / "rebuild-spec" / "scripts"

# Byte-identical to rebuild-spec's test_cap_table_lib.py::_HEADER.
_HEADER = (
    "| ID | Capability | What the user can do | User Stories | Requirements | "
    "Business Rules | Screens |\n"
    "|----|------------|------------------------|-----------------|---------------|"
    "-------------------|---------|\n"
)

_FIXTURE = (
    "## 2. Functional Capabilities\n\n"
    + _HEADER
    + "| CAP-01 | Sign in | Do it | US001, US002, US012 | FR-101 | BR-001 | SCR001 |\n"
    + "| CAP-02 | Also sign in | Do it too | US012, US030 | FR-102 | BR-002 | SCR002 |\n"
    + "\n## 3. Open Decisions\n"
)


@pytest.mark.skipif(not (_REBUILD_SPEC_SCRIPTS / "_cap_table_lib.py").is_file(),
                     reason="rebuild-spec not installed alongside this skill")
class TestCapMapAgreesWithCapTableLib:
    # Mirrors: rebuild-spec/scripts/tests/test_functional_spec_sot_sections.py::
    #          TestDoubleClaimed.test_fires_when_code_claimed_twice (same claim-cell shape).
    def test_per_cap_us_claim_sets_agree(self):
        if str(_REBUILD_SPEC_SCRIPTS) not in sys.path:
            sys.path.insert(0, str(_REBUILD_SPEC_SCRIPTS))
        import _cap_table_lib as ctl  # noqa: E402  (rebuild-spec's single § 2 contract, AD-6)

        lines = _FIXTURE.splitlines()
        h2 = [(i, ln.rstrip()) for i, ln in enumerate(lines) if ln.startswith("## ")]
        b2 = None
        for i, (idx, h) in enumerate(h2):
            if h == "## 2. Functional Capabilities":
                b2 = (idx + 1, h2[i + 1][0] if i + 1 < len(h2) else len(lines))
        assert b2 is not None

        # "Expected" derived from rebuild-spec's OWN shared contract (data_rows/claim_columns) —
        # not a re-implementation, the same functions `_cap_claims` itself builds on.
        header_cells, rows = ctl.data_rows(lines, b2)
        us_col = ctl.claim_columns(header_cells)["US"]
        us_code_re = re.compile(r"\bUS\d{3}(?!\d)")
        expected = [set(us_code_re.findall(row[us_col])) for row in rows]

        ours = cap_map.us_claim_sets(_FIXTURE)
        assert ours == expected
        assert ours == [{"US001", "US002", "US012"}, {"US012", "US030"}]

    def test_max_per_row_matches_rebuild_specs_cap_claims_grouping(self):
        """Cross-check via `_cap_claims` too (the function rebuild-spec's own validator calls) —
        invert its code->[cap_ids] map back to per-CAP-row US sets and compare."""
        if str(_REBUILD_SPEC_SCRIPTS) not in sys.path:
            sys.path.insert(0, str(_REBUILD_SPEC_SCRIPTS))
        sys.path.insert(0, str(_REBUILD_SPEC_SCRIPTS))
        import validate_feature_spec as vfs  # noqa: E402

        lines = _FIXTURE.splitlines()
        h2 = [(i, ln.rstrip()) for i, ln in enumerate(lines) if ln.startswith("## ")]
        b2 = next(((idx + 1, h2[i + 1][0] if i + 1 < len(h2) else len(lines))
                   for i, (idx, h) in enumerate(h2) if h == "## 2. Functional Capabilities"), None)
        claims = vfs._cap_claims(lines, b2)  # code -> [cap_ids] across every family
        us_code_re = re.compile(r"\bUS\d{3}(?!\d)")
        by_cap: dict[str, set[str]] = {"CAP-01": set(), "CAP-02": set()}
        for code, cap_ids in claims.items():
            if not us_code_re.fullmatch(code):
                continue
            for cap_id in cap_ids:
                by_cap[cap_id].add(code)
        expected_widest = max(len(s) for s in by_cap.values())

        ours = cap_map.us_claim_sets(_FIXTURE)
        ours_widest = max(len(s) for s in ours)
        assert ours_widest == expected_widest == 3
