"""Phase 09 (human-readable SOT) — technical-spec.md 5-bucket retaxonomy validator
coverage: the 8 new/changed rule_ids the phase's Requirements table lists, plus the
`FeatureSpec.tech_sections_pre_sot` degradation window against the real corpus-g2
evidence fixture.

Every test below calls `vfs._check_technical_spec` directly (no subprocess) against
a well-formed baseline pair (`_GOOD_TECH_SPEC` / `_GOOD_FUNC_TWIN`), each mutated by
exactly ONE `.replace()` to plant a single violation — mirroring
test_functional_spec_sot_sections.py's `_FULL_NEW_SHAPE_OK` pattern. Each negative
test states, in its own comment, the exact branch it plants a defect in and reaches;
`TestBaselineIsClean` proves the baseline itself carries zero findings, so a positive
test failing means the ONE planted defect, not incidental baseline noise.
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[5]
_SOT_CORPUS = Path(__file__).resolve().parent / "fixtures" / "sot-corpus"
"""Real generated corpus, git-tracked. Lived under `plans/` (gitignored) until it took
the whole CI suite down at collection time — see fixtures/sot-corpus/README.md."""
F010_FIXTURE = (
    _SOT_CORPUS / "corpus-g2" / "F010_FollowSystem.technical-spec.md"
)

sys.path.insert(0, str(SCRIPTS_DIR))
import validate_feature_spec as vfs  # noqa: E402
from _spec_constants import REQUIRED_H2_FUNC  # noqa: E402

# ---------------------------------------------------------------------------
# Baseline pair — a clean new-shape technical-spec.md + its functional-spec.md
# twin. FR-001 and CAP-01 are declared on the twin side and mapped/bucketed on
# the tech side so mapping_table_missing/capability_twin_skew stay silent on
# the unmodified baseline.
# ---------------------------------------------------------------------------

_GOOD_FUNC_TWIN = """\
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

_GOOD_TECH_SPEC = """\
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


def _write_pair(tmp_path: Path, tech_text: str, func_text: str = _GOOD_FUNC_TWIN) -> Path:
    feat_dir = tmp_path / "docs" / "features" / "F900_Test"
    feat_dir.mkdir(parents=True)
    (feat_dir / "technical-spec.md").write_text(tech_text, encoding="utf-8")
    (feat_dir / "functional-spec.md").write_text(func_text, encoding="utf-8")
    return feat_dir / "technical-spec.md"


def _rule_ids(issues: list[dict]) -> list[str]:
    return [i["rule_id"] for i in issues]


def _critical_rule_ids(issues: list[dict]) -> list[str]:
    return [i["rule_id"] for i in issues if i["severity"] == "critical"]


class TestBaselineIsClean:
    def test_good_pair_has_zero_findings(self, tmp_path):
        """Control: proves every positive test below fails for its ONE planted
        reason, not incidental baseline noise."""
        spec = _write_pair(tmp_path, _GOOD_TECH_SPEC)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert issues == [], issues


# ---------------------------------------------------------------------------
# FeatureSpec.tech_sections_pre_sot — degradation window against the REAL
# corpus-g2 evidence fixture (still the old 9-section shape).
# ---------------------------------------------------------------------------

class TestTechSectionsPreSot:
    def test_real_g2_fixture_yields_exactly_one_finding(self):
        """Reaches: _check_technical_spec's `if is_pre_sot: ... return out`
        early-return branch. F010_FollowSystem.technical-spec.md is real
        corpus-g2 evidence still carrying '## Cross-Cutting Logic' — every
        new-shape rule (sysdesign_subsections, mapping_table_missing, ...)
        must be muted, leaving exactly the one warning for THIS shape check.

        Phase 08 (self-sufficiency v27.8) adds two MORE findings here, by
        design: this same real fixture also still carries both retired
        headings (`## Source Walkthrough`, `## DB Impact per Event`) —
        `FeatureSpec.retired_section_present` fires regardless of shape (no
        transition window, same as `legacy_artifact_sections`), so a genuinely
        un-migrated file correctly shows all three: two retirement warnings
        plus the pre-SOT shape warning."""
        assert F010_FIXTURE.is_file(), f"fixture missing: {F010_FIXTURE}"
        issues = vfs._check_technical_spec(F010_FIXTURE, REPO_ROOT)
        assert _rule_ids(issues) == [
            "FeatureSpec.retired_section_present",
            "FeatureSpec.retired_section_present",
            "FeatureSpec.tech_sections_pre_sot",
        ]
        assert all(i["severity"] == "warning" for i in issues)

    def test_new_shape_file_never_fires_it(self, tmp_path):
        """Reaches: the `else` side of `is_pre_sot` — a file with no
        '## Cross-Cutting Logic' heading anywhere must never see this rule_id."""
        spec = _write_pair(tmp_path, _GOOD_TECH_SPEC)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert "FeatureSpec.tech_sections_pre_sot" not in _rule_ids(issues)


# ---------------------------------------------------------------------------
# FeatureSpec.sysdesign_subsections — RETIRED (phase 10, action-thread reshape).
# No new-shape successor (C15 verdict: § 3 is "## 3. Actions" now, not a
# System-Design-shaped section with 7 fixed H3 subsections, and no equivalent
# per-H3 structural check was specified for § 4 Shared Foundation's appendix —
# see validate_feature_spec.py's own retirement note next to `b_design`). The
# 3 tests that used to live here (test_missing_h3_fires, test_blank_required_
# h3_fires, test_populated_container_with_promoted_block_not_blank) are removed
# together with the check, per the repo's "retire loudly, check and tests
# together" rule — a passing negative test against a rule_id that can no longer
# fire would prove nothing.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# FeatureSpec.verification_subsections (new, no predecessor)
# ---------------------------------------------------------------------------

class TestVerificationSubsections:
    def test_out_of_order_h3_fires(self, tmp_path):
        """Reaches: the order/membership check inside `if b_verif:` — swaps
        5.2 and 5.3."""
        broken = _GOOD_TECH_SPEC.replace(
            "### 5.2 Assumptions\n\nNone.\n\n### 5.3 Unresolved Questions\n\nNone.\n\n",
            "### 5.3 Unresolved Questions\n\nNone.\n\n### 5.2 Assumptions\n\nNone.\n\n",
        )
        spec = _write_pair(tmp_path, broken)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert "FeatureSpec.verification_subsections" in _critical_rule_ids(issues)


# ---------------------------------------------------------------------------
# FeatureSpec.capability_buckets_missing / capability_twin_skew
# ---------------------------------------------------------------------------

class TestCapabilityBuckets:
    def test_no_bucket_fires_missing(self, tmp_path):
        """Reaches: `if not cap_ns:` inside `if b_cap:` — '### 4.1 Login' is
        replaced by plain prose with no ### 4.N heading at all."""
        broken = _GOOD_TECH_SPEC.replace("### 4.1 Login\n\n", "")
        spec = _write_pair(tmp_path, broken)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert "FeatureSpec.capability_buckets_missing" in _critical_rule_ids(issues)

    def test_twin_skew_fires_on_extra_bucket(self, tmp_path):
        """Reaches: the `if extra or missing_ns:` branch — tech declares
        ### 4.2 with no matching CAP-02 in the twin's ## 2."""
        broken = _GOOD_TECH_SPEC.replace(
            "#### Edge Cases\n\nNone.\n\n## 5.",
            "#### Edge Cases\n\nNone.\n\n"
            "### 4.2 Extra Capability\n\n**Business Rules**\n\nNone.\n\n"
            "**Decision Logic**\n\nN/A — no user-facing decision logic beyond "
            "DISC-### Polymorphic Behavior.\n\n#### Edge Cases\n\nNone.\n\n## 5.",
        )
        spec = _write_pair(tmp_path, broken)
        issues = vfs._check_technical_spec(spec, tmp_path)
        skew = [i for i in issues if i["rule_id"] == "FeatureSpec.capability_twin_skew"]
        assert skew, issues
        assert skew[0]["severity"] == "warning"

    def test_no_twin_declared_caps_does_not_skew(self, tmp_path):
        """Reaches: `if twin_ns:` guard failing closed — an isolated tech spec
        with NO sibling functional-spec.md has nothing to skew against."""
        feat_dir = tmp_path / "docs" / "features" / "F900_Test"
        feat_dir.mkdir(parents=True)
        spec = feat_dir / "technical-spec.md"
        spec.write_text(_GOOD_TECH_SPEC, encoding="utf-8")
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert "FeatureSpec.capability_twin_skew" not in _rule_ids(issues)


# ---------------------------------------------------------------------------
# FeatureSpec.mapping_table_missing — RETIRED (phase 10, action-thread reshape).
# Successor: FeatureSpec.action_index_missing (`_check_action_thread`, phase 02) — "## 2."
# is now "## 2. Action Index", not a mapping table. The 3 tests that used to live here
# (test_missing_section_fires, test_twin_declared_code_missing_from_table_fires,
# test_isolated_fixture_with_no_twin_never_fires) are removed together with the check.
#
# FeatureSpec.mapping_restates_story is a DIFFERENT, still-live concern (a Name cell
# restating the user story as a GWT narrative) with no analogous column in the new § 2
# Action Index shape either, but its own check keeps running for a file still in the
# legacy 5-bucket shape — see validate_feature_spec.py's own note next to `b_map`. Its
# test (below, renamed out of the retired TestMappingTable class) stays: retiring a test
# alongside a check that is NOT retired would discard real coverage for no reason.
# ---------------------------------------------------------------------------

class TestMappingRestatesStory:
    def test_name_cell_restating_story_fires(self, tmp_path):
        """Reaches: the `if len(name) > _MAPPING_NAME_MAX_LEN or _GWT_WORD_RE...`
        branch — the Name cell is rewritten as a Given/When/Then narrative,
        exactly the duplication this rule exists to forbid."""
        broken = _GOOD_TECH_SPEC.replace(
            "| FR-001 | Validate credentials |",
            "| FR-001 | Given a user, When they submit valid credentials, "
            "Then a session token is issued |",
        )
        spec = _write_pair(tmp_path, broken)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = [i for i in issues if i["rule_id"] == "FeatureSpec.mapping_restates_story"]
        assert matching, issues
        assert matching[0]["severity"] == "warning"


# ---------------------------------------------------------------------------
# FeatureSpec.us_narrative_present
# ---------------------------------------------------------------------------

class TestUsNarrativePresent:
    def test_what_happens_field_fires(self, tmp_path):
        """Reaches: the `_WHAT_HAPPENS_RE.search` scan over the whole document."""
        broken = _GOOD_TECH_SPEC.replace(
            "### 5.1 Technical Verification\n\nNone.\n\n",
            "### 5.1 Technical Verification\n\n"
            "**What happens:** A logged-in user submits the form.\n\n",
        )
        spec = _write_pair(tmp_path, broken)
        issues = vfs._check_technical_spec(spec, tmp_path)
        matching = [i for i in issues if i["rule_id"] == "FeatureSpec.us_narrative_present"]
        assert matching, issues
        assert matching[0]["severity"] == "warning"

    def test_baseline_has_no_narrative_field(self, tmp_path):
        """Reaches: the same scan on the non-firing path."""
        spec = _write_pair(tmp_path, _GOOD_TECH_SPEC)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert "FeatureSpec.us_narrative_present" not in _rule_ids(issues)


# ---------------------------------------------------------------------------
# FeatureSpec.polymorphic_behavior_present / decision_logic_section_present /
# missing_client_behavior_anchor — retained rule_ids, re-homed (D8) under the
# new shape.
# ---------------------------------------------------------------------------

class TestRetainedRehomedRules:
    def test_polymorphic_behavior_present_fires_when_absent(self, tmp_path):
        """Reaches: `if b_design and not b_poly:` — '#### Polymorphic Behavior'
        is deleted from ### 3.2."""
        broken = _GOOD_TECH_SPEC.replace(
            "#### Polymorphic Behavior\n\n"
            "N/A — no discriminator fields in Key Entities.\n\n",
            "",
        )
        spec = _write_pair(tmp_path, broken)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert "FeatureSpec.polymorphic_behavior_present" in _critical_rule_ids(issues)

    def test_decision_logic_section_present_fires_when_absent(self, tmp_path):
        """Reaches: `if "**Decision Logic**" not in cap_text:` — the bold
        marker is deleted from the only capability bucket."""
        broken = _GOOD_TECH_SPEC.replace(
            "**Decision Logic**\n\n"
            "N/A — no user-facing decision logic beyond DISC-### Polymorphic "
            "Behavior.\n\n",
            "",
        )
        spec = _write_pair(tmp_path, broken)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert "FeatureSpec.decision_logic_section_present" in _critical_rule_ids(issues)

    def test_missing_client_behavior_anchor_fires_when_absent_from_section_3(self, tmp_path):
        """D8: the anchor is checked against ## 3. System Design's bounds now
        (was ## Cross-Cutting Logic). Reaches: `if "**Client behavior:** see"
        not in design_text:`."""
        broken = _GOOD_TECH_SPEC.replace(
            "**Client behavior:** see behavior-logic.md, permissions.md, "
            "architecture.md\n\n",
            "",
        )
        spec = _write_pair(tmp_path, broken)
        issues = vfs._check_technical_spec(spec, tmp_path)
        assert "FeatureSpec.missing_client_behavior_anchor" in _critical_rule_ids(issues)


# ---------------------------------------------------------------------------
# DEPRECATED_H2 — the 8 retired 9-section-shape H2s, minus "## Overview"
# (D-note in validate_feature_spec.py: excluded so it can never collide with
# functional-spec.md's own "## 1. Overview" heading if the two sets are ever
# shared).
# ---------------------------------------------------------------------------

class TestDeprecatedH2ExcludesOverview:
    def test_overview_not_in_deprecated_set(self):
        assert "## Overview" not in vfs.DEPRECATED_H2

    def test_functional_spec_overview_heading_never_collides(self):
        """The functional-spec.md § 1 heading is '## 1. Overview' — a
        DIFFERENT literal string from the retired tech-side '## Overview'
        (no numeral). Confirms there is no shared-set collision today even
        though DEPRECATED_H2 is scoped to technical-spec.md headings only."""
        func_overview_heading = REQUIRED_H2_FUNC[0]
        assert func_overview_heading == "## 1. Overview"
        assert func_overview_heading not in vfs.DEPRECATED_H2

    def test_retired_headings_still_present(self):
        """The 8 retired 9-section-shape H2s (full-set replacement minus
        '## Overview') are all still guarded."""
        expected = {
            "## Polymorphic Behavior", "## Cross-Cutting Logic", "## User Stories",
            "## Key Entities", "## Artifact References", "## Assumptions",
            "## Source Code References", "## Unresolved Questions",
        }
        assert expected <= vfs.DEPRECATED_H2
