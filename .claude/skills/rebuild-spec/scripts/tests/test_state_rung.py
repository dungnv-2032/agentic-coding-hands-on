"""Phase 01 (self-sufficiency v27.8) — `FeatureSpec.state_rung_missing`, wired into
`validate_feature_spec._check_action_thread`'s existing per-block loop (the SAME
loop `rung_order`/`rung_empty_rendered` already run in — D7 forbids a second,
bespoke `would_fire`-shaped entry point).

D8 re-anchor (post phase-00 measurement, plans/260824-1846-rebuild-spec-action-
self-sufficiency-v27-8/plan.md): the original anchor (an SM-### code in THIS
action's own § 2 Codes cell) fired on 1 action across the whole 43-feature corpus
— SM-### codes sit almost entirely on the cross-cutting A0 row, not on individual
writing actions. The re-anchored condition is DOCUMENT-LEVEL: does the feature
carry a real `### <sentence> (SM-###)` heading block anywhere (§ 4.3's own shape,
confirmed on the real corpus) AND does this action's own § 2 Writes cell say
something was written. Measured population: 95 actions / 14 features.

Mirrors `test_action_thread_diagrams.py`'s pattern: a hand-built, action-thread-shaped
technical-spec.md, scoped assertions via `_state_rule_ids` (this file's own rule_id
prefix) rather than the full issues list — a mutation aimed at `state_rung_missing`
can incidentally trip an unrelated check (e.g. `action_unclaimed` on a code no longer
claimed anywhere), and that collateral noise is not this file's concern.

D3 discipline: the SM heading's existence is a structural fact, never inferred from
prose. No fixture ever asks the check to infer a FROM state from a method name or a
boolean flip.
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

_STATE_PREFIX = "FeatureSpec.state_"


def _state_rule_ids(issues: list[dict]) -> list[str]:
    return [i["rule_id"] for i in issues if i["rule_id"].startswith(_STATE_PREFIX)]


def _state_issues(issues: list[dict]) -> list[dict]:
    return [i for i in issues if i["rule_id"].startswith(_STATE_PREFIX)]


# ---------------------------------------------------------------------------
# Baseline — the feature carries a real `### ... (SM-001)` heading block under
# § 4.3 (the corpus's own shape), A1 writes `listings`, and ALREADY renders a
# `**State**` rung. This is itself SILENT input (a): a writing action inside an
# SM-modelled feature that already carries its State rung must never fire.
# ---------------------------------------------------------------------------

_GOOD_SPEC = """\
# F903_Test — State Rung Test

## 1. Technical Overview

Overview text.

## 2. Action Index

| # | Action (handler) | Method · Path | Codes | Writes | Detail |
|---|---|---|---|---|---|
| **A0** | *cross-cutting — belongs to no single action* | — | FR-601 | — | § 4.4 |
| **A1** | `ListingsController#approve` | `PATCH` `.../approve` | FR-101, SM-001 | `listings` | § 3.1 |

## 3. Actions

### 3.1 CAP-01 — Approve listing

#### A1 · Approve a listing

`PATCH .../approve` → `ListingsController#approve`
`FR-101` `SM-001`

**Who** · Marketplace admin
**Result** · updates `listings.state`.
**State** · `SM-001`: `pending` → `approved` *(§ 4.3)*
**Source:** `listings_controller.rb:10-15`

## 4. Shared Foundation

### 4.1 Components

None.

### 4.2 Data Model

None.

### 4.3 State Management

### Listing approval lifecycle (SM-001)

**kind:** entity
**Linked FR:** FR-101
**Source:** `listing.rb:10-20`

```mermaid
stateDiagram-v2
    [*] --> pending
    pending --> approved: admin approves (#approve)
```

### 4.4 Shared Rules

#### Bin 3 — cross-cutting, belongs to no single action

**FR-601** applies globally: every listing action requires an admin session.

### 4.5 Algorithms & Integrations

None.

### 4.6 Configuration

None.
"""


def _write_spec(tmp_path: Path, tech_text: str, feature: str = "F903_Test") -> Path:
    feat_dir = tmp_path / "docs" / "features" / feature
    feat_dir.mkdir(parents=True)
    spec = feat_dir / "technical-spec.md"
    spec.write_text(tech_text, encoding="utf-8")
    return spec


class TestBaselineIsCleanForStateRung:
    def test_sm_coded_writing_action_with_state_rung_is_silent(self, tmp_path):
        """SILENT input (a), named: an SM-modelled feature's writing action that
        ALREADY renders a `**State**` rung."""
        spec = _write_spec(tmp_path, _GOOD_SPEC)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert _state_rule_ids(issues) == [], _state_issues(issues)


# ---------------------------------------------------------------------------
# FeatureSpec.state_rung_missing — firing test
# ---------------------------------------------------------------------------

class TestStateRungMissingFires:
    def test_writing_action_in_sm_modelled_feature_without_state_rung_fires(self, tmp_path):
        """Reaches: `needs_state and "State" not in present` — the ONLY difference
        from the clean baseline is the deleted `**State**` line. `has_sm_block`
        (document-level, § 4.3's real `### ... (SM-001)` heading) stays True."""
        broken = _GOOD_SPEC.replace(
            "**State** · `SM-001`: `pending` → `approved` *(§ 4.3)*\n", "",
        )
        spec = _write_spec(tmp_path, broken)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = [i for i in issues if i["rule_id"] == "FeatureSpec.state_rung_missing"]
        assert matching, issues
        assert matching[0]["severity"] == "warning"
        assert _state_rule_ids(issues) == ["FeatureSpec.state_rung_missing"]


# ---------------------------------------------------------------------------
# FeatureSpec.state_rung_missing — non-firing tests, one per named SILENT input
# ---------------------------------------------------------------------------

class TestStateRungMissingSilentInputs:
    def test_read_only_action_is_silent(self, tmp_path):
        """SILENT input (b), named: a read-only action (`Writes` = `—`) inside an
        SM-modelled feature (§ 4.3's heading block still present) — even with no
        `**State**` rung rendered, this must never fire."""
        broken = _GOOD_SPEC.replace(
            "| **A1** | `ListingsController#approve` | `PATCH` `.../approve` | FR-101, SM-001 | `listings` | § 3.1 |",
            "| **A1** | `ListingsController#approve` | `PATCH` `.../approve` | FR-101, SM-001 | — *(read-only)* | § 3.1 |",
        ).replace(
            "**State** · `SM-001`: `pending` → `approved` *(§ 4.3)*\n", "",
        )
        spec = _write_spec(tmp_path, broken)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert _state_rule_ids(issues) == [], _state_issues(issues)

    def test_no_sm_heading_block_at_all_is_silent(self, tmp_path):
        """SILENT input (c), named and most important (D8): a feature with NO
        `### ... (SM-###)` heading block anywhere — even though this action
        writes `listings` and renders no `**State**` rung, this must never fire.
        This is what keeps the check off the 29 of 43 corpus features that model
        no state machine at all, and is the entire reason the measured
        population is 95 (not the wider 180-action reading)."""
        broken = _GOOD_SPEC.replace(
            "**State** · `SM-001`: `pending` → `approved` *(§ 4.3)*\n", "",
        ).replace(
            """### Listing approval lifecycle (SM-001)

**kind:** entity
**Linked FR:** FR-101
**Source:** `listing.rb:10-20`

```mermaid
stateDiagram-v2
    [*] --> pending
    pending --> approved: admin approves (#approve)
```
""",
            "None.\n",
        )
        assert "(SM-001)" not in broken  # sanity: no SM heading survives the mutation
        spec = _write_spec(tmp_path, broken)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert _state_rule_ids(issues) == [], _state_issues(issues)


# ---------------------------------------------------------------------------
# D4/D5 degradation window — same shape `diagram_required_missing` already uses.
# ---------------------------------------------------------------------------

class TestStateRungMissingDegradation:
    def test_degrades_to_warning_with_pre_thread_suffix_while_old_shape(self, tmp_path):
        broken = _GOOD_SPEC.replace(
            "**State** · `SM-001`: `pending` → `approved` *(§ 4.3)*\n", "",
        ).replace(
            "## 1. Technical Overview",
            "## 1. Technical Overview\n\n## 3. System Design",
        )
        spec = _write_spec(tmp_path, broken)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = [i for i in issues if i["rule_id"] == "FeatureSpec.state_rung_missing"]
        assert matching, issues
        assert matching[0]["severity"] == "warning"
        assert "(_pre_thread)" in matching[0]["message"]

    def test_degrades_to_warning_with_pre_fill_suffix_while_unverified(self, tmp_path):
        broken = _GOOD_SPEC.replace(
            "**State** · `SM-001`: `pending` → `approved` *(§ 4.3)*\n", "",
        ).replace(
            "**Result** · updates `listings.state`.",
            "**Result** · updates `listings.state`. [UNVERIFIED] owner unresolved.",
        )
        spec = _write_spec(tmp_path, broken)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = [i for i in issues if i["rule_id"] == "FeatureSpec.state_rung_missing"]
        assert matching, issues
        assert matching[0]["severity"] == "warning"
        assert "(_pre_fill)" in matching[0]["message"]


# ---------------------------------------------------------------------------
# Aggregator reachability — `_summary_lib.recalculate_totals` counts by PRESENCE,
# never an allowlist (`_summary_lib.py:57-64`). Assert it, per
# `TestAggregatorReachability` in test_action_index_validation.py.
# ---------------------------------------------------------------------------

class TestAggregatorReachability:
    def test_state_rung_missing_warning_reaches_the_aggregate_totals(self, tmp_path):
        broken = _GOOD_SPEC.replace(
            "**State** · `SM-001`: `pending` → `approved` *(§ 4.3)*\n", "",
        )
        spec = _write_spec(tmp_path, broken)
        issues = vfs._check_technical_spec(spec, tmp_path)
        state_issues = [i for i in issues if i["rule_id"] == "FeatureSpec.state_rung_missing"]
        assert state_issues, issues

        summary = load_summary(tmp_path / "validation-summary.json", "test-plan")
        result = {"specs": {"F903_Test": {
            "spec_path": "docs/features/F903_Test/technical-spec.md",
            "issues": state_issues,
        }}}
        merge_validator_result(summary, "feature_spec", result)
        recalculate_totals(summary)
        assert summary["totals"]["warning"] >= 1
        assert derive_overall_status(summary) == "WARN"
