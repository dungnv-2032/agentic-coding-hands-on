"""Phase 03 (self-sufficiency v27.8) — `FeatureSpec.action_ref_unglossed`, wired
into `validate_feature_spec._check_action_ref_unglossed`, a sibling function gated
identically to `_check_action_thread`/`_check_rule_bins_and_diagrams` (`## 2.
Action Index` present).

Same pattern as `test_rule_bins.py`: every test calls `vfs._check_technical_spec`
directly against a hand-built, action-thread-shaped technical-spec.md, and
assertions are SCOPED to this check's own rule_id (`_ref_rule_ids`) rather than
the full issues list.

Only the REFINED predicate is exercised here — the naive one ("any bare
occurrence in the H4 context line, ignoring whether the same code is glossed
elsewhere in the block") does not exist anywhere in shipped code; see
`_check_action_ref_unglossed`'s own docstring for the corpus numbers (M1=21
refined vs M2=99 naive, 100% vs 21% precision) that settled this.
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

_REF_RULE_ID = "FeatureSpec.action_ref_unglossed"


def _ref_rule_ids(issues: list[dict]) -> list[str]:
    return [i["rule_id"] for i in issues if i["rule_id"] == _REF_RULE_ID]


def _ref_issues(issues: list[dict]) -> list[dict]:
    return [i for i in issues if i["rule_id"] == _REF_RULE_ID]


# ---------------------------------------------------------------------------
# Clean baseline — four actions, each a named SILENT input:
#   A1: BR-006 sits bare in the H4 context line AND is restated with a real
#       gloss in the BE rung — SILENT (a), the common case (247/266 on the
#       corpus, 93%).
#   A2: read-only, carries no family code at all (only FR-102, excluded from
#       this check's scope) — SILENT (b).
#   A3: BR-008 appears ONLY inside a ```mermaid``` fence's edge label, never
#       in prose — fence-awareness (a variant of SILENT (b): zero non-fenced
#       occurrences means the code is simply never seen by this check).
#   A4 is absent from § 2/§ 3 entirely; BR-009 is declared only in § 4.4 —
#       SILENT (c): a code cited only OUTSIDE any § 3 Actions block is
#       `crosscutting_unlabelled`'s ground, never this check's.
# ---------------------------------------------------------------------------

_GOOD_SPEC = """\
# F904_Test — Action Ref Unglossed Test

## 1. Technical Overview

Overview text.

## 2. Action Index

| # | Action (handler) | Method · Path | Codes | Writes | Detail |
|---|---|---|---|---|---|
| **A0** | *cross-cutting — belongs to no single action* | — | FR-601 | — | § 4.4 |
| **A1** | `ListingsController#index` | `GET` `.../listings` | FR-101, BR-006 | — *(read-only)* | § 3.1 |
| **A2** | `ListingsController#archive` | `PATCH` `.../archive` | FR-102 | `listings` | § 3.1 |
| **A3** | `ListingsController#toggle` | `PATCH` `.../toggle` | FR-103 | `listings` | § 3.1 |

## 3. Actions

### 3.1 CAP-01 — Manage listings

#### A1 · A listing search redirects to the root when no custom landing page is enabled

`GET .../listings` → `ListingsController#index`
`BR-006` `FR-101`

**BE** · **FR-101** Search URL serves results under a custom landing page; redirects to root otherwise per BR-006 — `ListingsController#index`.
**Result** · read-only — **no DB write**.
**Source:** `listings_controller.rb:5-10`

#### A2 · Archive a listing

`PATCH .../archive` → `ListingsController#archive`
`FR-102`

**Who** · Admin
**Result** · updates `listings.archived`.
**Source:** `listings_controller.rb:12-18`

#### A3 · Toggle a listing feature flag

`PATCH .../toggle` → `ListingsController#toggle`
`FR-103`

**Who** · Admin
**Result** · updates `listings.enabled`.
**Source:** `listings_controller.rb:20-25`

```mermaid
stateDiagram-v2
    [*] --> off
    off --> on: admin enables (BR-008)
```

## 4. Shared Foundation

### 4.1 Components

None.

### 4.2 Data Model

None.

### 4.3 State Management

None.

### 4.4 Shared Rules

#### Bin 3 — cross-cutting, belongs to no single action

**FR-601** applies globally: every listing action requires an admin session.

**BR-009 — Listings cannot be archived while a transaction is in flight.**
The service checks `listing.pending_transactions?` before applying any archive.

### 4.5 Algorithms & Integrations

None.

### 4.6 Configuration

None.
"""


def _write_spec(tmp_path: Path, tech_text: str, feature: str = "F904_Test") -> Path:
    feat_dir = tmp_path / "docs" / "features" / feature
    feat_dir.mkdir(parents=True)
    spec = feat_dir / "technical-spec.md"
    spec.write_text(tech_text, encoding="utf-8")
    return spec


class TestBaselineIsCleanForActionRefUnglossed:
    def test_good_fixture_fires_no_action_ref_code(self, tmp_path):
        spec = _write_spec(tmp_path, _GOOD_SPEC)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert _ref_rule_ids(issues) == [], _ref_issues(issues)


# ---------------------------------------------------------------------------
# FeatureSpec.action_ref_unglossed — firing test (the real F001 A4 shape)
# ---------------------------------------------------------------------------

class TestActionRefUnglossedFires:
    def test_bare_code_never_glossed_anywhere_in_block_fires(self, tmp_path):
        """Reaches: `not any(glosses)` for BR-006 — the ONLY difference from the
        clean baseline is that A1's BE rung no longer restates BR-006 with a
        gloss, leaving the H4 context line as BR-006's one and only occurrence
        (the real F001 A4 shape: context-line-only citation, BE/Result/Source
        rungs, no Rule rung, the code never reappears)."""
        broken = _GOOD_SPEC.replace(
            "**BE** · **FR-101** Search URL serves results under a custom landing page; "
            "redirects to root otherwise per BR-006 — `ListingsController#index`.",
            "**BE** · **FR-101** Search URL serves results under a custom landing page; "
            "redirects to root otherwise — `ListingsController#index`.",
        )
        assert "BR-006" not in broken.split("#### A1")[1].split("#### A2")[0].split(
            "`BR-006` `FR-101`", 1)[1]  # sanity: BR-006 gone from A1's block after the heading
        spec = _write_spec(tmp_path, broken)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = _ref_issues(issues)
        assert matching, issues
        assert matching[0]["severity"] == "warning"
        assert "BR-006" in matching[0]["message"]
        assert _ref_rule_ids(issues) == [_REF_RULE_ID]


# ---------------------------------------------------------------------------
# FeatureSpec.action_ref_unglossed — non-firing tests, one per named SILENT input
# ---------------------------------------------------------------------------

class TestActionRefUnglossedSilentInputs:
    def test_code_in_context_line_glossed_elsewhere_in_block_is_silent(self, tmp_path):
        """SILENT input (a), named: BR-006 sits bare in A1's H4 context line but
        is restated with a real gloss sentence in the BE rung — the common case,
        measured at 247/266 (93%) on the corpus. This is the unmodified baseline
        itself."""
        spec = _write_spec(tmp_path, _GOOD_SPEC)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert _ref_rule_ids(issues) == [], _ref_issues(issues)

    def test_block_with_no_family_code_is_silent(self, tmp_path):
        """SILENT input (b), named: A2's block (read-only... no, A2 writes here)
        carries no BR/DEC/SM/ALG/INT/DISC family code at all (only FR-102, out
        of this check's scope) — `occurrences` stays empty, nothing to flag."""
        spec = _write_spec(tmp_path, _GOOD_SPEC)
        issues = vfs._check_technical_spec(spec, tmp_path)
        a2_issues = [i for i in _ref_issues(issues) if "A2" in i["message"]]
        assert a2_issues == []

    def test_code_only_inside_mermaid_fence_is_silent(self, tmp_path):
        """Fence-awareness (a variant of SILENT (b)): BR-008 appears ONLY inside
        A3's ```mermaid``` fence edge label, never in prose. `_md_scan_lib.
        mask_fenced` blanks the fenced line before scanning, so `occurrences`
        never even sees BR-008 — this must never fire, and (to prove the mask is
        actually doing work, not merely absent-by-coincidence) it must still
        fire if the SAME text is moved outside the fence."""
        spec = _write_spec(tmp_path, _GOOD_SPEC)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert "BR-008" not in str(_ref_issues(issues))

        # Prove the mask is load-bearing: move the identical BR-008 mention
        # out of the fence, into a plain, never-glossed context line — it must
        # now fire, confirming the SILENT result above came from fence-masking
        # and not from some other accidental non-match.
        unfenced = _GOOD_SPEC.replace(
            "```mermaid\nstateDiagram-v2\n    [*] --> off\n"
            "    off --> on: admin enables (BR-008)\n```\n\n",
            "",
        ).replace(
            "`PATCH .../toggle` → `ListingsController#toggle`\n`FR-103`",
            "`PATCH .../toggle` → `ListingsController#toggle`\n`FR-103` `BR-008`",
        )
        spec2 = _write_spec(tmp_path, unfenced, feature="F905_Test")
        issues2 = vfs._check_technical_spec(spec2, tmp_path)
        matching2 = [i for i in _ref_issues(issues2) if "BR-008" in i["message"]]
        assert matching2, issues2

    def test_code_declared_only_outside_section3_is_silent(self, tmp_path):
        """SILENT input (c), named: BR-009 is declared only in § 4.4 Shared
        Rules, never inside any § 3 Actions block — `crosscutting_unlabelled`'s
        ground, never this check's. Confirmed by the unmodified baseline."""
        spec = _write_spec(tmp_path, _GOOD_SPEC)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert "BR-009" not in str(_ref_issues(issues))


# ---------------------------------------------------------------------------
# Family-code regex boundary hazard — this repo has hit `\b` vs `(?!\d)` 7
# times in 3 variants. `_ACTION_REF_CODE_RE` uses `(?!\d)`, never a trailing
# `\b` (which never matches past the digits in a `BR-001_Slug` shape, since
# `_` is a word character).
# ---------------------------------------------------------------------------

class TestActionRefCodeReBoundary:
    def test_code_followed_by_underscore_slug_still_matches(self):
        m = vfs._ACTION_REF_CODE_RE.search("BR-001_Slug")
        assert m is not None
        assert m.group(0) == "BR-001"

    def test_four_digit_code_does_not_match(self):
        assert vfs._ACTION_REF_CODE_RE.search("BR-0011") is None


# ---------------------------------------------------------------------------
# D4 degradation window — same `is_pre_thread or is_fill_pending` shape
# `diagram_required_missing`/`state_rung_missing` already use.
# ---------------------------------------------------------------------------

class TestActionRefUnglossedDegradation:
    def _broken(self) -> str:
        return _GOOD_SPEC.replace(
            "**BE** · **FR-101** Search URL serves results under a custom landing page; "
            "redirects to root otherwise per BR-006 — `ListingsController#index`.",
            "**BE** · **FR-101** Search URL serves results under a custom landing page; "
            "redirects to root otherwise — `ListingsController#index`.",
        )

    def test_degrades_to_warning_with_pre_thread_suffix_while_old_shape(self, tmp_path):
        broken = self._broken().replace(
            "## 1. Technical Overview",
            "## 1. Technical Overview\n\n## 3. System Design",
        )
        spec = _write_spec(tmp_path, broken)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = _ref_issues(issues)
        assert matching, issues
        assert matching[0]["severity"] == "warning"
        assert "(_pre_fill_ref)" in matching[0]["message"]

    def test_degrades_to_warning_with_pre_fill_ref_suffix_while_unverified(self, tmp_path):
        broken = self._broken().replace(
            "**Result** · read-only — **no DB write**.",
            "**Result** · read-only — **no DB write**. [UNVERIFIED] owner unresolved.",
        )
        spec = _write_spec(tmp_path, broken)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = _ref_issues(issues)
        assert matching, issues
        assert matching[0]["severity"] == "warning"
        assert "(_pre_fill_ref)" in matching[0]["message"]


# ---------------------------------------------------------------------------
# Aggregator reachability — `_summary_lib.recalculate_totals` counts by
# PRESENCE, never an allowlist. Assert it, not assume it.
# ---------------------------------------------------------------------------

class TestAggregatorReachability:
    def test_action_ref_unglossed_warning_reaches_the_aggregate_totals(self, tmp_path):
        broken = _GOOD_SPEC.replace(
            "**BE** · **FR-101** Search URL serves results under a custom landing page; "
            "redirects to root otherwise per BR-006 — `ListingsController#index`.",
            "**BE** · **FR-101** Search URL serves results under a custom landing page; "
            "redirects to root otherwise — `ListingsController#index`.",
        )
        spec = _write_spec(tmp_path, broken)
        issues = vfs._check_technical_spec(spec, tmp_path)
        ref_issues = _ref_issues(issues)
        assert ref_issues, issues

        summary = load_summary(tmp_path / "validation-summary.json", "test-plan")
        result = {"specs": {"F904_Test": {
            "spec_path": "docs/features/F904_Test/technical-spec.md",
            "issues": ref_issues,
        }}}
        merge_validator_result(summary, "feature_spec", result)
        recalculate_totals(summary)
        assert summary["totals"]["warning"] >= 1
        assert derive_overall_status(summary) == "WARN"
