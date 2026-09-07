"""Phase 03 (rule bins + diagram contract) — the 2 new
`FeatureSpec.rule_bin_misplaced`/`FeatureSpec.crosscutting_unlabelled` checks wired
into `validate_feature_spec._check_rule_bins_and_diagrams`.

Same pattern as `test_action_index_validation.py` (phase 02): every test calls
`vfs._check_technical_spec` directly against a hand-built, action-thread-shaped
technical-spec.md, and assertions are SCOPED to this phase's own rule_id prefixes
(`_bin_rule_ids`) rather than the full issues list. Phase 10 closed the
`REQUIRED_H2_TECH`/mapping-table gap this note used to name (`required_sections`
now accepts the thread shape; `mapping_table_missing`/`sysdesign_subsections` are
retired outright) — the scoped assertion is kept here regardless, since it is this
file's own established pattern and still correctly isolates the rule_ids this phase
owns from every OTHER check `_check_technical_spec` runs.
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

import validate_feature_spec as vfs  # noqa: E402

_BIN_PREFIXES = ("FeatureSpec.rule_bin_", "FeatureSpec.crosscutting_")


def _bin_rule_ids(issues: list[dict]) -> list[str]:
    return [i["rule_id"] for i in issues if i["rule_id"].startswith(_BIN_PREFIXES)]


def _bin_issues(issues: list[dict]) -> list[dict]:
    return [i for i in issues if i["rule_id"].startswith(_BIN_PREFIXES)]


# ---------------------------------------------------------------------------
# Clean baseline — Bin 1 (A2's rule, inline in § 3, no `Used in:`), Bin 2 (BR-001,
# § 4.4, `Used in: A2, A3` naming 2 actions), Bin 3 (FR-601, § 4.4, cross-cutting
# labeled heading, no `Used in:`). Faithful to wire-format-contract.md § 4.4.
# ---------------------------------------------------------------------------

_GOOD_SPEC = """\
# F901_Test — Rule Bin Test

## 1. Technical Overview

Overview text.

## 2. Action Index

| # | Action (handler) | Method · Path | Codes | Writes | Detail |
|---|---|---|---|---|---|
| **A0** | *cross-cutting — belongs to no single action* | — | FR-601 | — | § 4.4 |
| **A1** | `WidgetsController#index` | `GET` `.../widgets` | FR-101, US101 | — *(read-only)* | § 3.1 |
| **A2** | `WidgetsController#update` | `PATCH` `.../update` | FR-102, BR-001 | `widgets` | § 3.1 |
| **A3** | `WidgetsController#close` | `PATCH` `.../close` | FR-103, BR-001 | `widgets` | § 3.1 |

## 3. Actions

### 3.1 CAP-01 — Manage widgets

#### A1 · List widgets

`GET .../widgets` → `WidgetsController#index`
`FR-101` `US101`

**Who** · Admin
**Result** · read-only — **no DB write**.
**Source:** `widgets_controller.rb:5-10`

#### A2 · Update a widget

`PATCH .../update` → `WidgetsController#update`
`FR-102`

**Who** · Admin
**Result** · updates `widgets.state`.
**Source:** `widgets_controller.rb:12-18`

#### A3 · Close a widget

`PATCH .../close` → `WidgetsController#close`
`FR-103`

**Who** · Admin
**Result** · updates `widgets.state`.
**Source:** `widgets_controller.rb:20-25`

## 4. Shared Foundation

### 4.1 Components

None.

### 4.2 Data Model

None.

### 4.3 State Management

None.

### 4.4 Shared Rules

#### Bin 3 — cross-cutting, belongs to no single action

**FR-601** applies globally: every widget action requires an admin session.

#### Bin 2 — used by ≥ 2 named actions

**BR-001 — A widget update must not change a closed widget.**
The service checks `widget.closed?` before applying any column change.
Used in: A2, A3
**Source:** `widgets_service.rb:5-20`

### 4.5 Algorithms & Integrations

None.

### 4.6 Configuration

None.
"""


def _write_spec(tmp_path: Path, tech_text: str, feature: str = "F901_Test") -> Path:
    feat_dir = tmp_path / "docs" / "features" / feature
    feat_dir.mkdir(parents=True)
    spec = feat_dir / "technical-spec.md"
    spec.write_text(tech_text, encoding="utf-8")
    return spec


class TestBaselineIsCleanForRuleBinCodes:
    def test_good_fixture_fires_no_rule_bin_code(self, tmp_path):
        spec = _write_spec(tmp_path, _GOOD_SPEC)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert _bin_rule_ids(issues) == [], _bin_issues(issues)


# ---------------------------------------------------------------------------
# FeatureSpec.rule_bin_misplaced
# ---------------------------------------------------------------------------

class TestRuleBinMisplaced:
    def test_multi_action_used_in_inline_in_section3_fires(self, tmp_path):
        """Reaches: `_in(b_actions, i) and len(ids) >= 2` — A2's inline rule
        carries a `Used in: A2, A3` list (2 actions) instead of being promoted to
        § 4.4 Bin 2. SILENT input: an inline § 3 rule with no `Used in:` marker
        at all (Bin 1's normal shape)."""
        broken = _GOOD_SPEC.replace(
            "**Who** · Admin\n**Result** · updates `widgets.state`.\n"
            "**Source:** `widgets_controller.rb:12-18`",
            "**Who** · Admin\n**Rule** · BR-777 — inline rule, mistakenly shared.\n"
            "Used in: A2, A3\n**Result** · updates `widgets.state`.\n"
            "**Source:** `widgets_controller.rb:12-18`",
            1,
        )
        spec = _write_spec(tmp_path, broken)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = [i for i in issues if i["rule_id"] == "FeatureSpec.rule_bin_misplaced"]
        assert matching, issues
        assert matching[0]["severity"] == "warning"
        assert "A2, A3" in matching[0]["message"]
        assert _bin_rule_ids(issues) == ["FeatureSpec.rule_bin_misplaced"]

    def test_single_action_used_in_inside_section44_fires(self, tmp_path):
        """Reaches: `_in(b_44, i) and len(ids) == 1` — Bin 2's `Used in:` list
        shrinks to name only A2, which belongs inline in § 3 (Bin 1), not § 4.4.
        SILENT input: every § 4.4 `Used in:` list names >=2 actions."""
        broken = _GOOD_SPEC.replace("Used in: A2, A3\n", "Used in: A2\n")
        spec = _write_spec(tmp_path, broken)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = [i for i in issues if i["rule_id"] == "FeatureSpec.rule_bin_misplaced"]
        assert matching, issues
        assert matching[0]["severity"] == "warning"
        assert "A2" in matching[0]["message"]
        assert _bin_rule_ids(issues) == ["FeatureSpec.rule_bin_misplaced"]

    def test_correctly_placed_bins_are_silent(self, tmp_path):
        spec = _write_spec(tmp_path, _GOOD_SPEC)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert "FeatureSpec.rule_bin_misplaced" not in _bin_rule_ids(issues)


# ---------------------------------------------------------------------------
# FeatureSpec.crosscutting_unlabelled
# ---------------------------------------------------------------------------

class TestCrosscuttingUnlabelled:
    def test_bin3_heading_without_crosscutting_wording_fires(self, tmp_path):
        """Reaches: `heading is not None and "cross-cutting" in heading.lower()`
        evaluating False — Bin 3's heading drops the word "cross-cutting" while
        its rule (FR-601, no `Used in:`) stays exactly as-is. SILENT input: every
        `Used in:`-less § 4.4 rule sits under a heading that says "cross-cutting"
        (Bin 3's own heading, as the wire-format contract mandates)."""
        broken = _GOOD_SPEC.replace(
            "#### Bin 3 — cross-cutting, belongs to no single action",
            "#### Bin 3 — global, belongs to no single action",
        )
        spec = _write_spec(tmp_path, broken)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = [i for i in issues if i["rule_id"] == "FeatureSpec.crosscutting_unlabelled"]
        assert matching, issues
        assert matching[0]["severity"] == "warning"
        assert _bin_rule_ids(issues) == ["FeatureSpec.crosscutting_unlabelled"]

    def test_bin2_rule_with_used_in_is_never_flagged_even_without_crosscutting_wording(self, tmp_path):
        """Bin 2's own heading ("used by >=2 named actions") never carries the
        word "cross-cutting" either — but its rule HAS a `Used in:` list, so it
        must never be mistaken for an unlabeled Bin-3 candidate."""
        spec = _write_spec(tmp_path, _GOOD_SPEC)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert "FeatureSpec.crosscutting_unlabelled" not in _bin_rule_ids(issues)

    def test_labeled_bin3_is_silent(self, tmp_path):
        spec = _write_spec(tmp_path, _GOOD_SPEC)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert "FeatureSpec.crosscutting_unlabelled" not in _bin_rule_ids(issues)
