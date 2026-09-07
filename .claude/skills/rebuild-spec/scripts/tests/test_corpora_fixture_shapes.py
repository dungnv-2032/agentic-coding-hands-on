"""Regression pin for the `sot-shapes/` corpus fixtures (phase 00 of
plans/260819-1016-rebuild-spec-capability-map) against the REAL `cap.*` checks phase 05
implemented (`_check_capabilities_section` in `validate_feature_spec.py`, built on
`_cap_table_lib`).

Phase 00 built these four fixtures with a 5-column `## 2. Functional Capabilities`
header — one column ahead of phase 04's widened, 7-column shape (`| ID | Capability |
What the user can do | User Stories | Requirements | Business Rules | Screens |`). That
left `F902_CapabilitiesEmptyCells` unable to exercise the "claim cells present but
EMPTY" branch it is named for — there were no claim cells at all — a fixture that
synthesizes a signal the real producer/check never actually reads. This module is the
backstop: it locks each fixture's `claim_state` AND the exact `cap.*` issue set the
real validator produces, so a future header/column-schema change cannot silently let
these four drift out of sync with the checks they exist to pin again.

Every assertion below calls the real code — `_cap_table_lib.data_rows`/`claim_state`
and `validate_feature_spec._check_functional_spec` — against the committed fixture
files on disk. No hand-computed expectations; each was verified by actually running
the validator (see the implementer report for the raw output).
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import validate_feature_spec as vfs  # noqa: E402
import _cap_table_lib as ctl  # noqa: E402

_TESTS_DIR = Path(__file__).resolve().parent
_SOT_SHAPES = _TESTS_DIR / "fixtures" / "corpora" / "sot-shapes"
_ROOT = SCRIPTS_DIR


def _fixture(name: str) -> Path:
    return _SOT_SHAPES / name


def _claim_state(func_path: Path) -> tuple[str, int]:
    """(claim_state, n_data_rows) for a fixture's § 2 table, via the real
    `_cap_table_lib` contract — the same functions the validator itself calls."""
    lines = func_path.read_text(encoding="utf-8").splitlines()
    headings, _ = vfs.parse_headings_and_blocks(lines)
    h2 = [(i, h) for i, h in headings if h.startswith("## ") and not h.startswith("### ")]
    b2 = vfs._func_h2_bounds(h2, "## 2. Functional Capabilities", len(lines))
    header_cells, rows = ctl.data_rows(lines, b2)
    return ctl.claim_state(header_cells, rows), len(rows)


def _cap_issues(feature_dir: Path) -> list[dict]:
    issues = vfs._check_functional_spec(
        feature_dir / "functional-spec.md", feature_dir / "technical-spec.md", _ROOT,
        is_draft=False,
    )
    return [i for i in issues if i["rule_id"].startswith("cap.")]


class TestF900CapabilitiesPopulated:
    """The clean baseline: every US###/BR-###|DEC-###|SM-###/FR-###/SCR### declared in
    §§ 4-7 is claimed by exactly one § 2 row. If this fires ANY `cap.*` issue, it is
    not a baseline — something is unclaimed, double-claimed, or the header regressed."""

    def test_claim_state_is_filled(self):
        state, n_rows = _claim_state(_fixture("F900_CapabilitiesPopulated") / "functional-spec.md")
        assert state == "filled"
        assert n_rows == 5

    def test_zero_cap_issues(self):
        assert _cap_issues(_fixture("F900_CapabilitiesPopulated")) == []


class TestF901CapabilitiesHeaderOnly:
    """SA-2 shape (reports/red-team-260819-1300-adjudication.md): header + zero data
    rows. `claim_state` must resolve `"absent"`, NOT `"unfilled"` — those are different
    findings (`cap.code_unclaimed` per declared code vs. a single muting
    `cap.claims_unfilled`) and only one may fire here."""

    def test_claim_state_is_absent(self):
        state, n_rows = _claim_state(_fixture("F901_CapabilitiesHeaderOnly") / "functional-spec.md")
        assert state == "absent"
        assert n_rows == 0

    def test_code_unclaimed_fires_for_every_declared_code(self):
        issues = _cap_issues(_fixture("F901_CapabilitiesHeaderOnly"))
        rule_ids = {i["rule_id"] for i in issues}
        assert rule_ids == {"cap.code_unclaimed"}
        # 10 FR + 11 BR-family (6 BR + 3 DEC + 2 SM) + 3 SCR + 5 US = 29.
        assert len(issues) == 29
        assert all(i["severity"] == "critical" for i in issues)

    def test_claims_unfilled_does_not_fire(self):
        rule_ids = {i["rule_id"] for i in _cap_issues(_fixture("F901_CapabilitiesHeaderOnly"))}
        assert "cap.claims_unfilled" not in rule_ids


class TestF902CapabilitiesEmptyCells:
    """FM-4 shape: >=1 data row, every claim cell empty — the post-`cap-map`/pre-fill
    window. `claim_state` must resolve `"unfilled"`, which mutes `cap.code_unclaimed`/
    `cap.double_claimed` for the whole file in favor of one `cap.claims_unfilled`."""

    def test_claim_state_is_unfilled(self):
        state, n_rows = _claim_state(_fixture("F902_CapabilitiesEmptyCells") / "functional-spec.md")
        assert state == "unfilled"
        assert n_rows == 2

    def test_exactly_one_claims_unfilled_warning(self):
        issues = _cap_issues(_fixture("F902_CapabilitiesEmptyCells"))
        assert len(issues) == 1
        assert issues[0]["rule_id"] == "cap.claims_unfilled"
        assert issues[0]["severity"] == "warning"


class TestF903DuplicateOpenDecisions:
    """SA-3 mute-abuse shape: a stray, out-of-position `## 2. Open Decisions` heading
    alongside the real `## 2. Functional Capabilities` section must NOT resolve
    `is_pre_sot` to True (that would silently mute every section-bound check, `cap.*`
    included). Content mirrors F900 except DEC-002 is deliberately left unclaimed, so
    `cap.code_unclaimed` has something concrete to fire on — proving the check actually
    reached this file rather than merely being absent because nothing was wrong."""

    def test_is_pre_sot_resolves_false(self):
        func_path = _fixture("F903_DuplicateOpenDecisions") / "functional-spec.md"
        lines = func_path.read_text(encoding="utf-8").splitlines()
        headings, _ = vfs.parse_headings_and_blocks(lines)
        h2_names = [h for _, h in headings if h.startswith("## ") and not h.startswith("### ")]
        is_pre_sot = (vfs._FUNC_PRE_SOT_SENTINEL in h2_names
                      and "## 2. Functional Capabilities" not in h2_names)
        assert is_pre_sot is False

    def test_claim_state_is_filled(self):
        state, n_rows = _claim_state(_fixture("F903_DuplicateOpenDecisions") / "functional-spec.md")
        assert state == "filled"
        assert n_rows == 5

    def test_code_unclaimed_reachable_for_dec_002(self):
        issues = _cap_issues(_fixture("F903_DuplicateOpenDecisions"))
        assert len(issues) == 1
        assert issues[0]["rule_id"] == "cap.code_unclaimed"
        assert issues[0]["severity"] == "critical"
        assert "DEC-002" in issues[0]["message"]

    def test_sections_pre_sot_is_not_emitted(self):
        issues = vfs._check_functional_spec(
            _fixture("F903_DuplicateOpenDecisions") / "functional-spec.md",
            _fixture("F903_DuplicateOpenDecisions") / "technical-spec.md",
            _ROOT, is_draft=False,
        )
        assert not any(i["rule_id"] == "func.sections_pre_sot" for i in issues)
