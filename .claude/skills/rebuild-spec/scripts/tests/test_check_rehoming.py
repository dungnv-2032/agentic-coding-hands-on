"""Phase 03c (C15) — regression coverage for the SECOND silent-gate defect
class C15 found: phase 03b fixed the DEC pair (C13), then audited for siblings
and found four more hardcoded retired-heading literals gating whole clusters
of checks silently dead under the action-thread shape:

  `## 3. System Design`                      -> missing_client_behavior_anchor,
                                                 polymorphic_behavior_present,
                                                 disc_boolean
  `## 4. Technical Behavior by Capability`   -> capability_buckets_missing,
                                                 decision_logic_section_present,
                                                 capability_twin_skew

Six rule_ids total (the `## 2. Functional -> Technical Mapping` line already
has a shipped successor from phase 02 and is explicitly out of this phase's
scope). Each ends in one of exactly two states:

  RE-HOMED — disc_boolean, capability_buckets_missing, capability_twin_skew,
    polymorphic_behavior_present, missing_client_behavior_anchor. Every one of
    these classes proves the SAME planted defect fires the SAME rule_id under
    BOTH the old heading and the new one (the regression test C13/C15 exist to
    make impossible to reintroduce), plus the mirror "well-formed is silent"
    proof under both shapes.

  RETIRED — decision_logic_section_present. No new-shape home added; see the
    code comment in validate_feature_spec.py (next to `_check_technical_spec`'s
    capability_buckets_missing block) for the full justification. Proven here
    only to the extent that matters for a green suite: the old-shape check
    stays fully functional and undegraded, and the new shape's total absence of
    a "**Decision Logic**" marker never spuriously fires it.

Every test calls `vfs._check_technical_spec` directly (no subprocess), mirroring
test_dec_rehoming.py's and test_action_index_validation.py's pattern: a baseline
proven clean, mutated by exactly one `.replace()` per test.
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

import validate_feature_spec as vfs  # noqa: E402

_REHOMED_IDS = {
    "FeatureSpec.disc_boolean",
    "FeatureSpec.capability_buckets_missing",
    "FeatureSpec.capability_twin_skew",
    "FeatureSpec.decision_logic_section_present",
    "FeatureSpec.polymorphic_behavior_present",
    "FeatureSpec.missing_client_behavior_anchor",
}


def _rehomed_issues(issues: list[dict]) -> list[dict]:
    return [i for i in issues if i["rule_id"] in _REHOMED_IDS]


def _rehomed_rule_ids(issues: list[dict]) -> list[str]:
    return [i["rule_id"] for i in _rehomed_issues(issues)]


def _rule_ids(issues: list[dict]) -> list[str]:
    return [i["rule_id"] for i in issues]


def _critical_rule_ids(issues: list[dict]) -> list[str]:
    return [i["rule_id"] for i in issues if i["severity"] == "critical"]


def _write_pair(tmp_path: Path, tech_text: str, func_text: str) -> Path:
    feat_dir = tmp_path / "docs" / "features" / "F900_Test"
    feat_dir.mkdir(parents=True)
    (feat_dir / "technical-spec.md").write_text(tech_text, encoding="utf-8")
    (feat_dir / "functional-spec.md").write_text(func_text, encoding="utf-8")
    return feat_dir / "technical-spec.md"


# ---------------------------------------------------------------------------
# OLD-shape baseline pair — a clean layer-first technical-spec.md + twin.
# Faithful copy of test_technical_spec_sot_validation.py's proven-clean
# `_GOOD_TECH_SPEC`/`_GOOD_FUNC_TWIN` (self-contained per this repo's per-file
# fixture convention — not imported, to keep the two test files independent).
# ---------------------------------------------------------------------------

_OLD_FUNC_TWIN = """\
# F900_Test — SOT Validation Test

## 1. Overview

**Problem:** Users need to log in.
**Solution:** Login form.
**Scope:** Login.
**Non-Scope:** None called out.

## 2. Functional Capabilities

| ID | Capability | What the user can do | Requirements | Screens |
|----|------------|------------------------|---------------|---------|
| CAP-01 | Login | Log in with email and password | FR-001 | SCR001_LoginForm |

## 3. Open Decisions

None — no unresolved domain confirmations.

## 4. Requirements

- **FR-001** Validate credentials.

## 5. Business Rules

## 6. Screens

N/A — background feature; no user-facing screens.

## 7. User Stories

## 8. Scenarios

## 9. Edge Cases

| Scenario | What Happens | User-Facing Message |
|----------|--------------|----------------------|
| Bad password | Reject the attempt | "Invalid credentials." |

## 10. Edge Behaviours to Verify

## 11. Risks & Known Issues

N/A — none found.

## 12. Dependencies

N/A — none found.

## 13. Configuration

N/A — no user-facing configuration constants for this feature.
"""

_OLD_SHAPE_TECH = """\
# F900_Test — SOT Validation Test

## 1. Technical Overview

Overview text.

## 2. Functional → Technical Mapping

| Code | Name | Where it is implemented | Technical notes | Source |
|------|------|--------------------------|------------------|--------|
| FR-001 | Validate credentials | `POST /login` via `LoginController::store` | | `app/auth.rb:1-5` |

## 3. System Design

### 3.1 Components

None.

### 3.2 Data Model

#### Key Entities

None.

#### Polymorphic Behavior

N/A — no discriminator fields in Key Entities.

### 3.3 State Management

None.

### 3.4 API & Endpoints

None.

### 3.5 Algorithms & Processing Logic

None.

### 3.6 Integrations

None.

### 3.7 Configuration

None.

**Client behavior:** see behavior-logic.md, permissions.md, architecture.md

## 4. Technical Behavior by Capability

### 4.1 Login

**Business Rules**

None.

**Decision Logic**

N/A — no user-facing decision logic beyond DISC-### Polymorphic Behavior.

#### Edge Cases

None.

## 5. Verification & Technical Notes

### 5.1 Technical Verification

None.

### 5.2 Assumptions

None.

### 5.3 Unresolved Questions

None.

### 5.4 Source References

**Source:** `app/auth.rb:1-5`

### 5.5 Artifact References

None.
"""


# ---------------------------------------------------------------------------
# NEW-shape baseline pair — a clean action-thread technical-spec.md + twin,
# with the SAME codes/capability so both fixtures exercise the exact same
# defect concepts. Extends test_action_index_validation.py's
# `_GOOD_ACTION_THREAD_SPEC` shape with the § 4.2 Data Model / Polymorphic
# Behavior / Client behavior anchor content that fixture never needed (phase
# 02 didn't own those checks) — this file does, so the baseline must be
# genuinely clean against all six rule_ids, not just phase 02's.
# ---------------------------------------------------------------------------

_NEW_FUNC_TWIN = """\
# F900_Test — Action Thread Rehoming Test

## 1. Overview

**Problem:** Admins need to browse listings.
**Solution:** A listing table.
**Scope:** Browse only.
**Non-Scope:** None called out.

## 2. Functional Capabilities

| ID | Capability | What the user can do | Requirements | Screens |
|----|------------|------------------------|---------------|---------|
| CAP-01 | Browse & filter the listing table | Search and filter listings | FR-201 | SCR001_ManageListings |

## 3. Open Decisions

None — no unresolved domain confirmations.

## 4. Requirements

- **FR-201** Filter and search listings.
- **FR-601** Scope every action to the current org.
"""

_NEW_SHAPE_TECH = """\
# F900_Test — Action Thread Rehoming Test

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

#### Key Entities

None.

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

# Neither baseline has a "**Decision Logic**" marker requirement issue: the OLD
# fixture legitimately HAS one (below), the NEW fixture legitimately has NONE
# anywhere — proving the RETIRED verdict doesn't spuriously fire on a perfectly
# valid new-shape file.
assert "**Decision Logic**" in _OLD_SHAPE_TECH
assert "**Decision Logic**" not in _NEW_SHAPE_TECH


class TestBaselineIsCleanForRehomedCodes:
    def test_old_shape_baseline_fires_no_rehomed_code(self, tmp_path):
        spec = _write_pair(tmp_path, _OLD_SHAPE_TECH, _OLD_FUNC_TWIN)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert _rehomed_rule_ids(issues) == [], _rehomed_issues(issues)

    def test_new_shape_baseline_fires_no_rehomed_code(self, tmp_path):
        spec = _write_pair(tmp_path, _NEW_SHAPE_TECH, _NEW_FUNC_TWIN)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert _rehomed_rule_ids(issues) == [], _rehomed_issues(issues)


# ---------------------------------------------------------------------------
# FeatureSpec.missing_client_behavior_anchor — RE-HOMED
# ---------------------------------------------------------------------------

class TestMissingClientBehaviorAnchor:
    def test_fires_under_old_shape(self, tmp_path):
        broken = _OLD_SHAPE_TECH.replace(
            "**Client behavior:** see behavior-logic.md, permissions.md, "
            "architecture.md\n\n",
            "",
        )
        spec = _write_pair(tmp_path, broken, _OLD_FUNC_TWIN)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = [i for i in issues if i["rule_id"] == "FeatureSpec.missing_client_behavior_anchor"]
        assert matching, issues
        assert matching[0]["severity"] == "critical"
        assert "(_pre_thread)" not in matching[0]["message"]

    def test_same_defect_fires_identically_under_new_shape(self, tmp_path):
        """THE regression test: same removed anchor, only the shape differs.
        Before C15's fix this was silent forever under the new shape (the
        anchor check was keyed on the retired '## 3. System Design' bound)."""
        broken = _NEW_SHAPE_TECH.replace(
            "**Client behavior:** see behavior-logic.md, permissions.md, "
            "architecture.md\n\n",
            "",
        )
        spec = _write_pair(tmp_path, broken, _NEW_FUNC_TWIN)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = [i for i in issues if i["rule_id"] == "FeatureSpec.missing_client_behavior_anchor"]
        assert matching, issues
        assert matching[0]["severity"] == "critical"
        assert "(_pre_thread)" not in matching[0]["message"]

    def test_well_formed_is_silent_under_old_shape(self, tmp_path):
        spec = _write_pair(tmp_path, _OLD_SHAPE_TECH, _OLD_FUNC_TWIN)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert "FeatureSpec.missing_client_behavior_anchor" not in _rule_ids(issues)

    def test_well_formed_is_silent_under_new_shape(self, tmp_path):
        spec = _write_pair(tmp_path, _NEW_SHAPE_TECH, _NEW_FUNC_TWIN)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert "FeatureSpec.missing_client_behavior_anchor" not in _rule_ids(issues)


# ---------------------------------------------------------------------------
# FeatureSpec.polymorphic_behavior_present — RE-HOMED
# ---------------------------------------------------------------------------

class TestPolymorphicBehaviorPresent:
    def test_fires_under_old_shape(self, tmp_path):
        broken = _OLD_SHAPE_TECH.replace(
            "#### Polymorphic Behavior\n\n"
            "N/A — no discriminator fields in Key Entities.\n\n",
            "",
        )
        spec = _write_pair(tmp_path, broken, _OLD_FUNC_TWIN)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = [i for i in issues if i["rule_id"] == "FeatureSpec.polymorphic_behavior_present"]
        assert matching, issues
        assert matching[0]["severity"] == "critical"

    def test_same_defect_fires_identically_under_new_shape(self, tmp_path):
        broken = _NEW_SHAPE_TECH.replace(
            "#### Polymorphic Behavior\n\n"
            "N/A — no discriminator fields in Key Entities.\n\n",
            "",
        )
        spec = _write_pair(tmp_path, broken, _NEW_FUNC_TWIN)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = [i for i in issues if i["rule_id"] == "FeatureSpec.polymorphic_behavior_present"]
        assert matching, issues
        assert matching[0]["severity"] == "critical"

    def test_well_formed_is_silent_under_old_shape(self, tmp_path):
        spec = _write_pair(tmp_path, _OLD_SHAPE_TECH, _OLD_FUNC_TWIN)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert "FeatureSpec.polymorphic_behavior_present" not in _rule_ids(issues)

    def test_well_formed_is_silent_under_new_shape(self, tmp_path):
        spec = _write_pair(tmp_path, _NEW_SHAPE_TECH, _NEW_FUNC_TWIN)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert "FeatureSpec.polymorphic_behavior_present" not in _rule_ids(issues)


# ---------------------------------------------------------------------------
# FeatureSpec.disc_boolean — RE-HOMED
# ---------------------------------------------------------------------------

_DISC_BOOLEAN_BLOCK = """\
##### DISC-001 — Listing.flag

| Value | Render | Validation | Persistence |
|---|---|---|---|
| true | shown | none | set by A2 |
| false | hidden | none | default |

**Source:** docs/generated/entities.md § listings > Discriminator Fields

"""


class TestDiscBoolean:
    def test_fires_under_old_shape(self, tmp_path):
        broken = _OLD_SHAPE_TECH.replace(
            "N/A — no discriminator fields in Key Entities.\n\n",
            _DISC_BOOLEAN_BLOCK,
        )
        spec = _write_pair(tmp_path, broken, _OLD_FUNC_TWIN)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = [i for i in issues if i["rule_id"] == "FeatureSpec.disc_boolean"]
        assert matching, issues
        assert matching[0]["severity"] == "warning"
        assert "(_pre_thread)" not in matching[0]["message"]

    def test_same_defect_fires_identically_under_new_shape(self, tmp_path):
        broken = _NEW_SHAPE_TECH.replace(
            "N/A — no discriminator fields in Key Entities.\n\n",
            _DISC_BOOLEAN_BLOCK,
        )
        spec = _write_pair(tmp_path, broken, _NEW_FUNC_TWIN)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = [i for i in issues if i["rule_id"] == "FeatureSpec.disc_boolean"]
        assert matching, issues
        assert matching[0]["severity"] == "warning"
        assert "(_pre_thread)" not in matching[0]["message"]

    def test_well_formed_is_silent_under_old_shape(self, tmp_path):
        spec = _write_pair(tmp_path, _OLD_SHAPE_TECH, _OLD_FUNC_TWIN)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert "FeatureSpec.disc_boolean" not in _rule_ids(issues)

    def test_well_formed_is_silent_under_new_shape(self, tmp_path):
        spec = _write_pair(tmp_path, _NEW_SHAPE_TECH, _NEW_FUNC_TWIN)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert "FeatureSpec.disc_boolean" not in _rule_ids(issues)


# ---------------------------------------------------------------------------
# FeatureSpec.capability_buckets_missing — RE-HOMED
# ---------------------------------------------------------------------------

class TestCapabilityBucketsMissing:
    def test_fires_under_old_shape(self, tmp_path):
        broken = _OLD_SHAPE_TECH.replace("### 4.1 Login\n\n", "")
        spec = _write_pair(tmp_path, broken, _OLD_FUNC_TWIN)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = [i for i in issues if i["rule_id"] == "FeatureSpec.capability_buckets_missing"]
        assert matching, issues
        assert matching[0]["severity"] == "critical"
        assert "(_pre_thread)" not in matching[0]["message"]

    def test_same_defect_fires_identically_under_new_shape(self, tmp_path):
        """THE regression test: the SAME concept (no capability bucket heading
        left under the actions section), expressed in new-shape terms. Before
        C15's fix this was silent forever under the new shape ('## 4.
        Technical Behavior by Capability' no longer exists to bound on)."""
        broken = _NEW_SHAPE_TECH.replace(
            "### 3.1 CAP-01 — Browse & filter the listing table\n\n", ""
        )
        spec = _write_pair(tmp_path, broken, _NEW_FUNC_TWIN)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = [i for i in issues if i["rule_id"] == "FeatureSpec.capability_buckets_missing"]
        assert matching, issues
        assert matching[0]["severity"] == "critical"
        assert "(_pre_thread)" not in matching[0]["message"]

    def test_well_formed_is_silent_under_old_shape(self, tmp_path):
        spec = _write_pair(tmp_path, _OLD_SHAPE_TECH, _OLD_FUNC_TWIN)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert "FeatureSpec.capability_buckets_missing" not in _rule_ids(issues)

    def test_well_formed_is_silent_under_new_shape(self, tmp_path):
        spec = _write_pair(tmp_path, _NEW_SHAPE_TECH, _NEW_FUNC_TWIN)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert "FeatureSpec.capability_buckets_missing" not in _rule_ids(issues)


# ---------------------------------------------------------------------------
# FeatureSpec.capability_twin_skew — RE-HOMED
# ---------------------------------------------------------------------------

class TestCapabilityTwinSkew:
    def test_fires_under_old_shape(self, tmp_path):
        broken = _OLD_SHAPE_TECH.replace(
            "#### Edge Cases\n\nNone.\n\n## 5.",
            "#### Edge Cases\n\nNone.\n\n"
            "### 4.2 Extra Capability\n\n**Business Rules**\n\nNone.\n\n"
            "**Decision Logic**\n\nN/A — no user-facing decision logic beyond "
            "DISC-### Polymorphic Behavior.\n\n#### Edge Cases\n\nNone.\n\n## 5.",
        )
        spec = _write_pair(tmp_path, broken, _OLD_FUNC_TWIN)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = [i for i in issues if i["rule_id"] == "FeatureSpec.capability_twin_skew"]
        assert matching, issues
        assert matching[0]["severity"] == "warning"
        assert "(_pre_thread)" not in matching[0]["message"]

    def test_same_defect_fires_identically_under_new_shape(self, tmp_path):
        """THE regression test: an extra capability bucket with no matching
        twin CAP- row, expressed in new-shape terms (an extra ### 3.N CAP-NN
        bucket under '## 3. Actions' instead of an extra ### 4.N under
        '## 4.'). Before C15's fix this was silent forever under the new
        shape."""
        broken = _NEW_SHAPE_TECH.replace(
            "## 4. Shared Foundation",
            "### 3.2 CAP-02 — Extra capability\n\nNone.\n\n## 4. Shared Foundation",
        )
        spec = _write_pair(tmp_path, broken, _NEW_FUNC_TWIN)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = [i for i in issues if i["rule_id"] == "FeatureSpec.capability_twin_skew"]
        assert matching, issues
        assert matching[0]["severity"] == "warning"
        assert "(_pre_thread)" not in matching[0]["message"]

    def test_no_extra_bucket_is_silent_under_old_shape(self, tmp_path):
        spec = _write_pair(tmp_path, _OLD_SHAPE_TECH, _OLD_FUNC_TWIN)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert "FeatureSpec.capability_twin_skew" not in _rule_ids(issues)

    def test_no_extra_bucket_is_silent_under_new_shape(self, tmp_path):
        spec = _write_pair(tmp_path, _NEW_SHAPE_TECH, _NEW_FUNC_TWIN)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert "FeatureSpec.capability_twin_skew" not in _rule_ids(issues)


# ---------------------------------------------------------------------------
# FeatureSpec.decision_logic_section_present — RETIRED (no new-shape home)
# ---------------------------------------------------------------------------

class TestDecisionLogicSectionPresentRetired:
    """RETIRED for the new shape (C15 verdict) — no successor added. See the
    code comment in validate_feature_spec.py (`_check_technical_spec`, right
    after the capability_buckets_missing new-shape block) for the full
    justification: the new template has no "**Decision Logic**" marker
    anywhere, and what this check's underlying concern actually needs
    (a DEC present and well-formed) is already fully covered by phase 03b's
    `_check_dec_blocks` row scan (test_dec_rehoming.py)."""

    def test_old_shape_still_fires_unchanged_and_undegraded(self, tmp_path):
        broken = _OLD_SHAPE_TECH.replace(
            "**Decision Logic**\n\n"
            "N/A — no user-facing decision logic beyond DISC-### Polymorphic "
            "Behavior.\n\n",
            "",
        )
        spec = _write_pair(tmp_path, broken, _OLD_FUNC_TWIN)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = [i for i in issues if i["rule_id"] == "FeatureSpec.decision_logic_section_present"]
        assert matching, issues
        assert matching[0]["severity"] == "critical"
        assert "(_pre_thread)" not in matching[0]["message"]

    def test_new_shape_baseline_never_fires_it_despite_no_decision_logic_marker(self, tmp_path):
        # _NEW_SHAPE_TECH legitimately has no "**Decision Logic**" marker
        # anywhere in it (asserted at module load above) — proves this rule_id
        # does not spuriously fire on a perfectly valid new-shape file just
        # because the marker concept itself is gone from the template.
        spec = _write_pair(tmp_path, _NEW_SHAPE_TECH, _NEW_FUNC_TWIN)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert "FeatureSpec.decision_logic_section_present" not in _rule_ids(issues)


# ---------------------------------------------------------------------------
# D4 degradation — new-shape findings WARN-first while the OLD § 3 sentinel is
# present (mirrors `_thread_sev_msg`'s treatment of every other action-thread
# check, reused here not re-derived); old-shape findings are NEVER degraded
# (merge blocker #4/#5). One representative check (missing_client_behavior_
# anchor) proves the mechanism; all six new-shape emit sites route through the
# same `_thread_sev_msg` call, so this is not six independent claims.
# ---------------------------------------------------------------------------

class TestDegradationWindow:
    """Representative check: `capability_buckets_missing`, deliberately NOT
    `missing_client_behavior_anchor`/`polymorphic_behavior_present`/
    `disc_boolean`. `_TECH_PRE_THREAD_SENTINEL` IS the literal
    '## 3. System Design' — inserting it to flip `is_pre_thread` to True also,
    unavoidably, makes `b_design` truthy (same string), which would make the
    UNTOUCHED old-shape check for those three ALSO fire on the placeholder's
    empty section — correctly, but as a second, different-severity finding
    that would confuse this specific assertion. `capability_buckets_missing`'s
    old-shape gate is a different literal ('## 4. Technical Behavior by
    Capability'), so it has no such collision and isolates the mechanism
    cleanly. All six new-shape emit sites route through the same
    `_thread_sev_msg` call, so this is one proof of the mechanism, not six
    independent claims."""

    def test_new_shape_finding_degrades_to_warning_while_pre_thread_sentinel_present(self, tmp_path):
        broken = _NEW_SHAPE_TECH.replace(
            "### 3.1 CAP-01 — Browse & filter the listing table\n\n", ""
        )
        degraded = broken.replace(
            "## 1. Technical Overview\n\nOverview text.\n",
            "## 1. Technical Overview\n\nOverview text.\n\n"
            "## 3. System Design\n\n(placeholder — pre-thread migration sentinel)\n",
        )
        spec = _write_pair(tmp_path, degraded, _NEW_FUNC_TWIN)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = [i for i in issues if i["rule_id"] == "FeatureSpec.capability_buckets_missing"]
        assert matching, issues
        assert matching[0]["severity"] == "warning"
        assert "(_pre_thread)" in matching[0]["message"]

    def test_old_shape_finding_is_never_degraded(self, tmp_path):
        """Merge blocker #4 guard: the OLD-shape checks (keyed on the literal
        headings, unconditionally undegraded) must never gain a `_pre_thread`
        suffix — every pre-existing fixture already carries '## 3. System
        Design' and expects `critical`/`warning` unconditionally. Already
        implicit in every `test_fires_under_old_shape` test above; asserted
        explicitly here as the dedicated guard."""
        broken = _OLD_SHAPE_TECH.replace("### 4.1 Login\n\n", "")
        spec = _write_pair(tmp_path, broken, _OLD_FUNC_TWIN)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = [i for i in issues if i["rule_id"] == "FeatureSpec.capability_buckets_missing"]
        assert matching, issues
        assert matching[0]["severity"] == "critical"
        assert "(_pre_thread)" not in matching[0]["message"]
