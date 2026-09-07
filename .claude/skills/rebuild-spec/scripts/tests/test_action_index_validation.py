"""Phase 02 (action-thread reshape, D2/D4) — the 5 live FeatureSpec.action_*/
rung_* checks wired into `validate_feature_spec._check_action_thread`. A 6th,
`action_double_claimed`, shipped here and was retired after phase 11's
real-corpus measurement — see the retirement block below `TestActionUnclaimed`
for the corpus numbers and rationale.

Every test calls `vfs._check_technical_spec` directly (no subprocess) against a
hand-built B-v-shaped technical-spec.md, mirroring
test_technical_spec_sot_validation.py's baseline-plus-one-mutation pattern.

CLEARED (phase 10, action-thread reshape): a prior scoping note here documented that
`_GOOD_ACTION_THREAD_SPEC` below, while genuinely thread-shaped (## 2. Action Index /
## 3. Actions / ## 4. Shared Foundation), still tripped `FeatureSpec.required_sections`
because `REQUIRED_H2_TECH` was not yet repointed to that shape (pre-flight finding C1) —
so "the B-v fixture passes clean" was asserted SCOPED to the 6 new action-thread
rule_ids (`_action_rule_ids`) rather than the full issues list. Phase 10 repointed
`required_sections` (now `REQUIRED_H2_TECH_THREAD`, accepting either the current thread
shape or the legacy 5-bucket shape) and retired `mapping_table_missing`/
`sysdesign_subsections` outright, closing that gap. The fixture also needed two small
additions — `#### Polymorphic Behavior` under `### 4.2 Data Model` and the
`**Client behavior:** see ...` anchor at the tail of `## 4. Shared Foundation` — to
satisfy phase 03c's re-homed `polymorphic_behavior_present`/`missing_client_behavior_
anchor` checks, which this fixture predates. `TestBaselineIsCleanForActionThreadCodes`
now asserts the FULL issues list is empty, not merely the action-thread-scoped subset.
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

import validate_feature_spec as vfs  # noqa: E402
from _summary_lib import (  # noqa: E402
    derive_overall_status, load_summary, merge_validator_result, recalculate_totals,
)

_ACTION_PREFIX = "FeatureSpec.action_"
_RUNG_PREFIX = "FeatureSpec.rung_"


def _action_rule_ids(issues: list[dict]) -> list[str]:
    return [i["rule_id"] for i in issues
            if i["rule_id"].startswith(_ACTION_PREFIX) or i["rule_id"].startswith(_RUNG_PREFIX)]


# ---------------------------------------------------------------------------
# B-v baseline — a clean, hand-built thread-shaped technical-spec.md. Faithful to
# wire-format-contract.md, including its corrected Source-rung shape
# ("**Source:** `path:N-M`", not the middot shape the contract originally gave).
# ---------------------------------------------------------------------------

_GOOD_ACTION_THREAD_SPEC = """\
# F900_Test — Action Thread Test

## 1. Technical Overview

Overview text.

## 2. Action Index

| # | Action (handler) | Method · Path | Codes | Writes | Detail |
|---|---|---|---|---|---|
| **A0** | *cross-cutting — belongs to no single action* | — | FR-601 | — | § 4.4 |
| **A1** | `ManageListingsController#index` | `GET` `.../manage-listings` | FR-201, US127 | — *(read-only)* | § 3.1 |

## 3. Actions

### 3.1 CAP-01 — Browse & filter the listing table

#### A1 · View, search and filter the listing table

`GET .../manage-listings` → `ManageListingsController#index`
`FR-201` `US127` · `SCR001_ManageListings`

**Who** · Marketplace admin
**FE** · `index.haml:1-23` renders the table via `Listing::ListPresenter#listings`.
**Request** · param `q` *(text)* and `status[]` *(multi-value)*
**BE** · `ListPresenter#resource_scope` — `q` matches title/category via SQL `LIKE`.
**Rule** · no per-row conditional logic for this read-only listing.
**Result** · read-only — **no DB write**. Paginated table.
**Source:** `index.haml:1-29` → `manage_listings_controller.rb:5` → `list_presenter.rb:1-142`

## 4. Shared Foundation

### 4.1 Components

None.

### 4.2 Data Model

#### Polymorphic Behavior

N/A — no discriminator fields in Key Entities.

### 4.3 State Management

None.

### 4.4 Shared Rules

#### Bin 3 — cross-cutting, belongs to no single action

**FR-601** applies globally: every listing action is scoped to the current org.

### 4.5 Algorithms & Integrations

None.

### 4.6 Configuration

None.

**Client behavior:** see behavior-logic.md, permissions.md, architecture.md

## 5. Verification & Technical Notes

### 5.1 Technical Verification

None.

### 5.2 Assumptions

None.

### 5.3 Unresolved Questions

None.

### 5.4 Source References

**Source:** `manage_listings_controller.rb:5`

### 5.5 Artifact References

None.
"""


def _write_spec(tmp_path: Path, tech_text: str) -> Path:
    feat_dir = tmp_path / "docs" / "features" / "F900_Test"
    feat_dir.mkdir(parents=True)
    spec = feat_dir / "technical-spec.md"
    spec.write_text(tech_text, encoding="utf-8")
    return spec


class TestBaselineIsCleanForActionThreadCodes:
    def test_good_bv_fixture_fires_nothing_at_all(self, tmp_path):
        """Phase 10 (item 8): re-scoped from an action-thread-only assertion
        (`_action_rule_ids(issues) == []`) to the full issues list —
        `required_sections`/`mapping_table_missing`/`sysdesign_subsections` no longer
        gate on the legacy 5-bucket shape alone, so a genuinely well-formed thread-shaped
        file must now validate with ZERO findings of ANY kind, not just zero
        action-thread findings. Strictly stronger than the old assertion (a subset
        check), so it replaces rather than supplements it."""
        spec = _write_spec(tmp_path, _GOOD_ACTION_THREAD_SPEC)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert issues == []


# ---------------------------------------------------------------------------
# FeatureSpec.action_index_missing
# ---------------------------------------------------------------------------

class TestActionIndexMissing:
    def test_zero_data_rows_fires(self, tmp_path):
        """Reaches: `if not rows:` in `_check_action_thread` — both A0 and A1 rows
        deleted, leaving only the header + separator."""
        broken = _GOOD_ACTION_THREAD_SPEC.replace(
            "| **A0** | *cross-cutting — belongs to no single action* | — | FR-601 | — | § 4.4 |\n"
            "| **A1** | `ManageListingsController#index` | `GET` `.../manage-listings` | FR-201, US127 | — *(read-only)* | § 3.1 |\n",
            "",
        )
        spec = _write_spec(tmp_path, broken)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = [i for i in issues if i["rule_id"] == "FeatureSpec.action_index_missing"]
        assert matching, issues
        assert matching[0]["severity"] == "critical"
        assert _action_rule_ids(issues) == ["FeatureSpec.action_index_missing"]

    def test_zero_action_feature_with_only_a0_row_is_silent(self, tmp_path):
        """SILENT input (merge blocker #3): a feature that resolves zero real
        actions (corpus-measured: F016/F017/F029) still has the mandatory A0 row —
        that alone must keep the table non-empty and this check silent."""
        broken = _GOOD_ACTION_THREAD_SPEC.replace(
            "| **A1** | `ManageListingsController#index` | `GET` `.../manage-listings` | FR-201, US127 | — *(read-only)* | § 3.1 |\n",
            "",
        )
        # Also strip the now-orphaned A1 action block and its declared codes so
        # action_unclaimed has nothing left to complain about either.
        broken = broken.split("### 3.1 CAP-01")[0] + "## 4. Shared Foundation" + broken.split("## 4. Shared Foundation", 1)[1]
        spec = _write_spec(tmp_path, broken)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert "FeatureSpec.action_index_missing" not in _action_rule_ids(issues)


# ---------------------------------------------------------------------------
# FeatureSpec.action_unclaimed
# ---------------------------------------------------------------------------

class TestActionUnclaimed:
    def test_declared_code_missing_from_index_row_fires(self, tmp_path):
        """Reaches: `declared - set(claims)` — US127 stays declared in § 3's
        context line but is deleted from A1's Codes column in § 2."""
        broken = _GOOD_ACTION_THREAD_SPEC.replace(
            "| **A1** | `ManageListingsController#index` | `GET` `.../manage-listings` | FR-201, US127 | — *(read-only)* | § 3.1 |",
            "| **A1** | `ManageListingsController#index` | `GET` `.../manage-listings` | FR-201 | — *(read-only)* | § 3.1 |",
        )
        spec = _write_spec(tmp_path, broken)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = [i for i in issues if i["rule_id"] == "FeatureSpec.action_unclaimed"]
        assert matching, issues
        assert matching[0]["severity"] == "critical"
        assert matching[0]["message"].startswith("family=")
        assert "US127" in matching[0]["message"]
        assert _action_rule_ids(issues) == ["FeatureSpec.action_unclaimed"]

    def test_every_declared_code_claimed_is_silent(self, tmp_path):
        spec = _write_spec(tmp_path, _GOOD_ACTION_THREAD_SPEC)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert "FeatureSpec.action_unclaimed" not in _action_rule_ids(issues)


# ---------------------------------------------------------------------------
# FeatureSpec.action_double_claimed — RETIRED.
#
# Shipped in phase 02, retired here after phase 11's real-corpus run (43
# features, sharetribe) showed the rule was modelling the wrong relation: it
# copied `cap.double_claimed`'s partition assumption ("every code belongs to
# exactly one row") from § 2 Functional Capabilities, where codes genuinely
# partition. Action Index rows do not partition their codes — one requirement
# fanning out to several handling actions is the normal shape (measured: 127
# firings across 31/43 features, 85% of them a claim-width of exactly 2,
# including on the plan's own hand-authored B-v reference sample, e.g.
# FR-203 legitimately spanning "request export"/"poll status"/"generate
# file"). No natural cutoff separates "implausible fan-out" from "a feature
# with a few more handlers" in the measured distribution (widths 2-10 form one
# continuous tail), so demoting to a threshold-gated warning would just
# reintroduce the same modelling error at a different width. Removed outright,
# code and tests together — see `validate_feature_spec.py::_check_action_thread`
# and `docs/decisions/ADR-0006.md`'s addendum. `action_unclaimed` above is
# unaffected: it enforces completeness (every code claimed by AT LEAST one
# row), which is the real binding and stays exactly as it was.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# FeatureSpec.action_key_not_handler
# ---------------------------------------------------------------------------

class TestActionKeyNotHandler:
    def test_bare_method_path_handler_fires(self, tmp_path):
        """Reaches: `_action_thread_lib.is_handler_fallback` returning True for a
        non-A0 row — A1's handler cell becomes the bare fallback shape."""
        broken = _GOOD_ACTION_THREAD_SPEC.replace(
            "| **A1** | `ManageListingsController#index` |",
            "| **A1** | `GET /manage-listings` |",
        )
        spec = _write_spec(tmp_path, broken)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = [i for i in issues if i["rule_id"] == "FeatureSpec.action_key_not_handler"]
        assert matching, issues
        assert matching[0]["severity"] == "warning"
        assert _action_rule_ids(issues) == ["FeatureSpec.action_key_not_handler"]

    def test_a0_row_is_never_checked_for_handler_shape(self, tmp_path):
        """A0's cell is an italic cross-cutting label, never a handler — even if it
        were rewritten to look verb-like, A0 must be excluded from this check."""
        broken = _GOOD_ACTION_THREAD_SPEC.replace(
            "*cross-cutting — belongs to no single action*",
            "`GET /nowhere`",
        )
        spec = _write_spec(tmp_path, broken)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert "FeatureSpec.action_key_not_handler" not in _action_rule_ids(issues)

    def test_class_method_handlers_are_silent(self, tmp_path):
        spec = _write_spec(tmp_path, _GOOD_ACTION_THREAD_SPEC)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert "FeatureSpec.action_key_not_handler" not in _action_rule_ids(issues)


# ---------------------------------------------------------------------------
# FeatureSpec.rung_order
# ---------------------------------------------------------------------------

class TestRungOrder:
    def test_rungs_out_of_relative_order_fires(self, tmp_path):
        """Reaches: `present != expected` — Who/FE swapped."""
        broken = _GOOD_ACTION_THREAD_SPEC.replace(
            "**Who** · Marketplace admin\n"
            "**FE** · `index.haml:1-23` renders the table via `Listing::ListPresenter#listings`.\n",
            "**FE** · `index.haml:1-23` renders the table via `Listing::ListPresenter#listings`.\n"
            "**Who** · Marketplace admin\n",
        )
        spec = _write_spec(tmp_path, broken)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = [i for i in issues if i["rule_id"] == "FeatureSpec.rung_order"]
        assert matching, issues
        assert matching[0]["severity"] == "critical"
        assert _action_rule_ids(issues) == ["FeatureSpec.rung_order"]

    def test_state_rung_out_of_order_fires(self, tmp_path):
        """The 8th rung (phase 01, self-sufficiency v27.8) is covered by the SAME
        generic `present != expected` check — `State` placed AFTER `Source` (its
        contract position is BEFORE Source) must fire exactly like any other
        misordered rung."""
        broken = _GOOD_ACTION_THREAD_SPEC.replace(
            "**Source:** `index.haml:1-29` → `manage_listings_controller.rb:5` → `list_presenter.rb:1-142`\n",
            "**Source:** `index.haml:1-29` → `manage_listings_controller.rb:5` → `list_presenter.rb:1-142`\n"
            "**State** · pending to approved (§ 4.3)\n",
        )
        spec = _write_spec(tmp_path, broken)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = [i for i in issues if i["rule_id"] == "FeatureSpec.rung_order"]
        assert matching, issues
        assert matching[0]["severity"] == "critical"
        assert "State" in matching[0]["message"]
        assert _action_rule_ids(issues) == ["FeatureSpec.rung_order"]

    def test_partial_subset_in_correct_relative_order_is_silent(self, tmp_path):
        """SILENT input: presence of every rung is never required, only the
        relative order of whichever ARE present — drop Request/BE entirely."""
        broken = _GOOD_ACTION_THREAD_SPEC.replace(
            "**Request** · param `q` *(text)* and `status[]` *(multi-value)*\n"
            "**BE** · `ListPresenter#resource_scope` — `q` matches title/category via SQL `LIKE`.\n",
            "",
        )
        spec = _write_spec(tmp_path, broken)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert "FeatureSpec.rung_order" not in _action_rule_ids(issues)


# ---------------------------------------------------------------------------
# FeatureSpec.rung_empty_rendered
# ---------------------------------------------------------------------------

class TestRungEmptyRendered:
    def test_na_stub_fires(self, tmp_path):
        """Reaches: `_RUNG_EMPTY_RE.match(body)` — Result's real body replaced with
        the literal stub 'N/A'."""
        broken = _GOOD_ACTION_THREAD_SPEC.replace(
            "**Result** · read-only — **no DB write**. Paginated table.",
            "**Result** · N/A",
        )
        spec = _write_spec(tmp_path, broken)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = [i for i in issues if i["rule_id"] == "FeatureSpec.rung_empty_rendered"]
        assert matching, issues
        assert matching[0]["severity"] == "critical"
        assert _action_rule_ids(issues) == ["FeatureSpec.rung_empty_rendered"]

    def test_real_rendered_content_is_silent(self, tmp_path):
        spec = _write_spec(tmp_path, _GOOD_ACTION_THREAD_SPEC)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert "FeatureSpec.rung_empty_rendered" not in _action_rule_ids(issues)

    def test_state_rung_na_stub_fires(self, tmp_path):
        """Phase 01 (self-sufficiency v27.8) — the 8th rung must be covered by this
        check too, not just `rung_order`. `rung_empty_rendered` iterates `RUNG_LABELS`
        generically, so `State` rides along for free — but "rides along for free" is
        exactly the claim that regresses silently the day someone spells the label set
        literally somewhere. Pinned here so a State-blind `_RUNG_LINE_RE` (the
        two-place-edit defect this phase exists to prevent) fails a test instead of
        quietly disabling a critical gate on the newest rung."""
        broken = _GOOD_ACTION_THREAD_SPEC.replace(
            "**Source:**", "**State** · N/A\n**Source:**", 1
        )
        assert broken != _GOOD_ACTION_THREAD_SPEC, "fixture shape changed"
        spec = _write_spec(tmp_path, broken)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = [
            i for i in issues if i["rule_id"] == "FeatureSpec.rung_empty_rendered"
        ]
        assert matching, issues
        assert matching[0]["severity"] == "critical"
        assert "State" in matching[0]["message"]
        assert _action_rule_ids(issues) == ["FeatureSpec.rung_empty_rendered"]


# ---------------------------------------------------------------------------
# D4 degradation window — the SAME defect, sentinel toggled, per merge blocker #4.
# ---------------------------------------------------------------------------

class TestDegradationWindow:
    _BROKEN = _GOOD_ACTION_THREAD_SPEC.replace(
        "| **A1** | `ManageListingsController#index` | `GET` `.../manage-listings` | FR-201, US127 | — *(read-only)* | § 3.1 |",
        "| **A1** | `ManageListingsController#index` | `GET` `.../manage-listings` | FR-201 | — *(read-only)* | § 3.1 |",
    )
    _BROKEN_PRE_THREAD = _BROKEN.replace(
        "## 1. Technical Overview\n\nOverview text.\n",
        "## 1. Technical Overview\n\nOverview text.\n\n"
        "## 3. System Design\n\n(placeholder — pre-thread migration sentinel)\n",
    )

    def test_critical_without_sentinel(self, tmp_path):
        spec = _write_spec(tmp_path, self._BROKEN)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = [i for i in issues if i["rule_id"] == "FeatureSpec.action_unclaimed"]
        assert matching, issues
        assert matching[0]["severity"] == "critical"
        assert "_pre_thread" not in matching[0]["message"]

    def test_warning_with_sentinel_present(self, tmp_path):
        spec = _write_spec(tmp_path, self._BROKEN_PRE_THREAD)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = [i for i in issues if i["rule_id"] == "FeatureSpec.action_unclaimed"]
        assert matching, issues
        assert matching[0]["severity"] == "warning"
        assert "_pre_thread" in matching[0]["message"]


# ---------------------------------------------------------------------------
# Aggregator reachability — the codes must actually move the counted totals, not
# silently fall through an allowlist hole (prior incident: 3 of 23 validators
# counted, 17 criticals -> PASS).
# ---------------------------------------------------------------------------

class TestAggregatorReachability:
    def test_action_thread_critical_fails_the_aggregate_run(self, tmp_path):
        broken = _GOOD_ACTION_THREAD_SPEC.replace(
            "| **A0** | *cross-cutting — belongs to no single action* | — | FR-601 | — | § 4.4 |\n"
            "| **A1** | `ManageListingsController#index` | `GET` `.../manage-listings` | FR-201, US127 | — *(read-only)* | § 3.1 |\n",
            "",
        )
        spec = _write_spec(tmp_path, broken)
        issues = vfs._check_technical_spec(spec, tmp_path)
        action_issues = [i for i in issues if i["rule_id"] == "FeatureSpec.action_index_missing"]
        assert action_issues, issues

        summary = load_summary(tmp_path / "validation-summary.json", "test-plan")
        result = {"specs": {"F900_Test": {
            "spec_path": "docs/features/F900_Test/technical-spec.md",
            "issues": action_issues,
        }}}
        merge_validator_result(summary, "feature_spec", result)
        recalculate_totals(summary)
        assert summary["totals"]["critical"] >= 1
        assert derive_overall_status(summary) == "FAIL"
