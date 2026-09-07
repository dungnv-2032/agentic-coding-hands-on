"""Integration tests for validate_feature_spec.py.
Runs script as subprocess with --spec <path>, parses stdout JSON,
asserts specific rule_ids present/absent per fixture.
Coverage per phase-05 test matrix.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SCRIPTS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[5]
SCRIPT = SCRIPTS_DIR / "validate_feature_spec.py"


def _run(spec_path: Path) -> tuple[int, dict]:
    """Run the spec validator against a single spec and return (exit_code, json)."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT),
         "--spec", str(spec_path),
         "--project-root", str(REPO_ROOT)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = json.loads(result.stdout)
    return result.returncode, output


def _issues(data: dict) -> list[dict]:
    """Flatten all issues across all spec entries."""
    all_issues = []
    for entry in data.get("specs", {}).values():
        all_issues.extend(entry.get("issues", []))
    return all_issues


def _rule_ids(data: dict) -> list[str]:
    return [i["rule_id"] for i in _issues(data)]


def _critical_rule_ids(data: dict) -> list[str]:
    return [i["rule_id"] for i in _issues(data) if i["severity"] == "critical"]


# ---------------------------------------------------------------------------
# spec-pass.md: well-formed spec — no critical issues expected
# ---------------------------------------------------------------------------

class TestSpecPass:
    def test_exit_code_zero(self):
        code, _ = _run(FIXTURES / "specs" / "spec-pass.md")
        assert code == 0

    def test_no_critical_issues(self):
        _, data = _run(FIXTURES / "specs" / "spec-pass.md")
        criticals = _critical_rule_ids(data)
        assert criticals == [], f"unexpected critical issues: {criticals}"

    def test_output_has_specs_key(self):
        _, data = _run(FIXTURES / "specs" / "spec-pass.md")
        assert "specs" in data


# ---------------------------------------------------------------------------
# spec-missing-h2.md: ## Business Workflow omitted
# ---------------------------------------------------------------------------

class TestSpecMissingH2:
    def test_exit_code_one(self):
        code, _ = _run(FIXTURES / "specs" / "spec-missing-h2.md")
        assert code == 1

    def test_required_sections_rule_id_present(self):
        _, data = _run(FIXTURES / "specs" / "spec-missing-h2.md")
        assert "FeatureSpec.required_sections" in _critical_rule_ids(data)

    def test_issue_is_critical(self):
        _, data = _run(FIXTURES / "specs" / "spec-missing-h2.md")
        matching = [i for i in _issues(data) if i["rule_id"] == "FeatureSpec.required_sections"]
        assert all(i["severity"] == "critical" for i in matching)


# ---------------------------------------------------------------------------
# spec-deprecated-heading.md: top-level ## Requirements present
# ---------------------------------------------------------------------------

class TestSpecDeprecatedHeading:
    def test_exit_code_one(self):
        code, _ = _run(FIXTURES / "specs" / "spec-deprecated-heading.md")
        assert code == 1

    def test_deprecated_headings_rule_id_present(self):
        _, data = _run(FIXTURES / "specs" / "spec-deprecated-heading.md")
        assert "FeatureSpec.deprecated_headings" in _critical_rule_ids(data)

    def test_issue_is_critical(self):
        _, data = _run(FIXTURES / "specs" / "spec-deprecated-heading.md")
        matching = [i for i in _issues(data) if i["rule_id"] == "FeatureSpec.deprecated_headings"]
        assert all(i["severity"] == "critical" for i in matching)


# ---------------------------------------------------------------------------
# spec-placeholder.md: contains {ROUTE_PATH} literal
# ---------------------------------------------------------------------------

class TestSpecPlaceholder:
    def test_exit_code_one(self):
        code, _ = _run(FIXTURES / "specs" / "spec-placeholder.md")
        assert code == 1

    def test_no_placeholder_rule_id_present(self):
        _, data = _run(FIXTURES / "specs" / "spec-placeholder.md")
        assert "Universal.no_placeholder" in _critical_rule_ids(data)

    def test_issue_is_critical(self):
        _, data = _run(FIXTURES / "specs" / "spec-placeholder.md")
        matching = [i for i in _issues(data) if i["rule_id"] == "Universal.no_placeholder"]
        assert all(i["severity"] == "critical" for i in matching)

    def test_message_mentions_placeholder(self):
        _, data = _run(FIXTURES / "specs" / "spec-placeholder.md")
        matching = [i for i in _issues(data) if i["rule_id"] == "Universal.no_placeholder"]
        assert any("ROUTE_PATH" in i["message"] for i in matching)


# ---------------------------------------------------------------------------
# spec-placeholder-evasion.md: placeholder wrapped in <!-- a --> {X} <!-- b -->
# Regression for stage-3 finding F1 (comment net-depth evasion).
# Old per-line net-depth logic suppressed this; new strip_html_comments detects.
# ---------------------------------------------------------------------------

class TestSpecPlaceholderEvasion:
    def test_exit_code_one(self):
        code, _ = _run(FIXTURES / "specs" / "spec-placeholder-evasion.md")
        assert code == 1

    def test_no_placeholder_rule_id_present(self):
        _, data = _run(FIXTURES / "specs" / "spec-placeholder-evasion.md")
        assert "Universal.no_placeholder" in _critical_rule_ids(data)


# ---------------------------------------------------------------------------
# spec-sm-fence-far.md: SM-001 heading + 50+ lines of intro before mermaid fence.
# Regression for stage-3 finding S1 (legacy 50-line window false positive).
# ---------------------------------------------------------------------------

class TestSpecSmFenceFar:
    def test_exit_code_zero(self):
        code, _ = _run(FIXTURES / "specs" / "spec-sm-fence-far.md")
        assert code == 0

    def test_sm_mermaid_not_flagged(self):
        _, data = _run(FIXTURES / "specs" / "spec-sm-fence-far.md")
        assert "FeatureSpec.sm_mermaid" not in _critical_rule_ids(data)


# ---------------------------------------------------------------------------
# spec-sm-no-fence.md: SM-001 heading but no mermaid fence anywhere.
# Regression: sm_mermaid must still fire when the fence is genuinely missing.
# ---------------------------------------------------------------------------

class TestSpecSmNoFence:
    def test_exit_code_one(self):
        code, _ = _run(FIXTURES / "specs" / "spec-sm-no-fence.md")
        assert code == 1

    def test_sm_mermaid_rule_id_present(self):
        _, data = _run(FIXTURES / "specs" / "spec-sm-no-fence.md")
        assert "FeatureSpec.sm_mermaid" in _critical_rule_ids(data)


# ---------------------------------------------------------------------------
# spec-dec-missing-field.md: DEC block missing **subtype:** field → CRITICAL
# ---------------------------------------------------------------------------

class TestSpecDecMissingField:
    def test_exit_code_one(self):
        code, _ = _run(FIXTURES / "specs" / "spec-dec-missing-field.md")
        assert code == 1

    def test_dec_blocks_well_formed_rule_id_present(self):
        _, data = _run(FIXTURES / "specs" / "spec-dec-missing-field.md")
        assert "FeatureSpec.dec_blocks_well_formed" in _critical_rule_ids(data)

    def test_issue_is_critical(self):
        _, data = _run(FIXTURES / "specs" / "spec-dec-missing-field.md")
        matching = [i for i in _issues(data) if i["rule_id"] == "FeatureSpec.dec_blocks_well_formed"]
        assert all(i["severity"] == "critical" for i in matching)

    def test_message_mentions_subtype(self):
        _, data = _run(FIXTURES / "specs" / "spec-dec-missing-field.md")
        matching = [i for i in _issues(data) if i["rule_id"] == "FeatureSpec.dec_blocks_well_formed"]
        assert any("**subtype:**" in i["message"] for i in matching)


# ---------------------------------------------------------------------------
# spec-dec-invalid-subtype.md: DEC block with invalid subtype value → CRITICAL
# ---------------------------------------------------------------------------

class TestSpecDecInvalidSubtype:
    def test_exit_code_one(self):
        code, _ = _run(FIXTURES / "specs" / "spec-dec-invalid-subtype.md")
        assert code == 1

    def test_dec_blocks_well_formed_rule_id_present(self):
        _, data = _run(FIXTURES / "specs" / "spec-dec-invalid-subtype.md")
        assert "FeatureSpec.dec_blocks_well_formed" in _critical_rule_ids(data)

    def test_message_mentions_invalid_subtype(self):
        _, data = _run(FIXTURES / "specs" / "spec-dec-invalid-subtype.md")
        matching = [i for i in _issues(data) if i["rule_id"] == "FeatureSpec.dec_blocks_well_formed"]
        assert any("invalid" in i["message"].lower() for i in matching)


# ---------------------------------------------------------------------------
# spec-dec-missing-source.md: DEC block missing **Source:** → CRITICAL. D-f dropped
# **user_visible_outcome:** from the 4 required fields but the fixture still carries
# it (forward-compatible, not itself an error) — isolates Source as the one field
# whose absence still fails the block (hard gate: exactly 4 remaining fields).
# ---------------------------------------------------------------------------

class TestSpecDecMissingSource:
    def test_exit_code_one(self):
        code, _ = _run(FIXTURES / "specs" / "spec-dec-missing-source.md")
        assert code == 1

    def test_dec_blocks_well_formed_rule_id_present(self):
        _, data = _run(FIXTURES / "specs" / "spec-dec-missing-source.md")
        assert "FeatureSpec.dec_blocks_well_formed" in _critical_rule_ids(data)

    def test_message_mentions_source(self):
        _, data = _run(FIXTURES / "specs" / "spec-dec-missing-source.md")
        matching = [i for i in _issues(data) if i["rule_id"] == "FeatureSpec.dec_blocks_well_formed"]
        assert any("**Source:**" in i["message"] for i in matching)

    def test_user_visible_outcome_presence_not_flagged(self):
        """The block carries **user_visible_outcome:** (dropped from required fields
        by D-f) — its presence must not itself produce a dec_blocks_well_formed hit;
        only the missing **Source:** field should."""
        _, data = _run(FIXTURES / "specs" / "spec-dec-missing-source.md")
        matching = [i for i in _issues(data) if i["rule_id"] == "FeatureSpec.dec_blocks_well_formed"]
        assert len(matching) == 1
        assert "user_visible_outcome" not in matching[0]["message"]


# ---------------------------------------------------------------------------
# spec-dec-lazy-na.md: Decision Logic N/A but JSX ternary in spec body → WARNING
# ---------------------------------------------------------------------------

class TestSpecDecLazyNa:
    def test_exit_code_zero(self):
        # warnings do not cause non-zero exit
        code, _ = _run(FIXTURES / "specs" / "spec-dec-lazy-na.md")
        assert code == 0

    def test_dec_lazy_na_rule_id_present(self):
        _, data = _run(FIXTURES / "specs" / "spec-dec-lazy-na.md")
        rule_ids = [i["rule_id"] for i in _issues(data)]
        assert "FeatureSpec.dec_lazy_na" in rule_ids

    def test_issue_is_warning(self):
        _, data = _run(FIXTURES / "specs" / "spec-dec-lazy-na.md")
        matching = [i for i in _issues(data) if i["rule_id"] == "FeatureSpec.dec_lazy_na"]
        assert all(i["severity"] == "warning" for i in matching)


# ---------------------------------------------------------------------------
# spec-missing-client-anchor.md: missing **Client behavior:** anchor → CRITICAL
# ---------------------------------------------------------------------------

class TestSpecMissingClientAnchor:
    def test_exit_code_one(self):
        code, _ = _run(FIXTURES / "specs" / "spec-missing-client-anchor.md")
        assert code == 1

    def test_missing_client_behavior_anchor_rule_id_present(self):
        _, data = _run(FIXTURES / "specs" / "spec-missing-client-anchor.md")
        assert "FeatureSpec.missing_client_behavior_anchor" in _critical_rule_ids(data)

    def test_issue_is_critical(self):
        _, data = _run(FIXTURES / "specs" / "spec-missing-client-anchor.md")
        matching = [i for i in _issues(data) if i["rule_id"] == "FeatureSpec.missing_client_behavior_anchor"]
        assert all(i["severity"] == "critical" for i in matching)


# ---------------------------------------------------------------------------
# spec-linked-fr-missing.md: BR-001 missing **Linked FR:** → CRITICAL
# ---------------------------------------------------------------------------

class TestSpecLinkedFrMissing:
    def test_exit_code_one(self):
        code, _ = _run(FIXTURES / "specs" / "spec-linked-fr-missing.md")
        assert code == 1

    def test_linked_fr_missing_rule_id_present(self):
        _, data = _run(FIXTURES / "specs" / "spec-linked-fr-missing.md")
        assert "FeatureSpec.linked_fr_missing" in _critical_rule_ids(data)

    def test_issue_is_critical(self):
        _, data = _run(FIXTURES / "specs" / "spec-linked-fr-missing.md")
        matching = [i for i in _issues(data) if i["rule_id"] == "FeatureSpec.linked_fr_missing"]
        assert all(i["severity"] == "critical" for i in matching)

    def test_message_mentions_br_code(self):
        _, data = _run(FIXTURES / "specs" / "spec-linked-fr-missing.md")
        matching = [i for i in _issues(data) if i["rule_id"] == "FeatureSpec.linked_fr_missing"]
        assert any("BR-001" in i["message"] for i in matching)

    def test_present_linked_fr_not_flagged(self):
        # BR-002 has **Linked FR:** → should NOT appear in linked_fr_missing issues
        _, data = _run(FIXTURES / "specs" / "spec-linked-fr-missing.md")
        matching = [i for i in _issues(data) if i["rule_id"] == "FeatureSpec.linked_fr_missing"]
        assert not any("BR-002" in i["message"] for i in matching)


# ---------------------------------------------------------------------------
# spec-disc-boolean-values.md: DISC subsection with only true/false → WARNING
# ---------------------------------------------------------------------------

class TestSpecDiscBooleanValues:
    def test_exit_code_zero(self):
        # warnings do not cause non-zero exit
        code, _ = _run(FIXTURES / "specs" / "spec-disc-boolean-values.md")
        assert code == 0

    def test_disc_boolean_rule_id_present(self):
        _, data = _run(FIXTURES / "specs" / "spec-disc-boolean-values.md")
        rule_ids = [i["rule_id"] for i in _issues(data)]
        assert "FeatureSpec.disc_boolean" in rule_ids

    def test_issue_is_warning(self):
        _, data = _run(FIXTURES / "specs" / "spec-disc-boolean-values.md")
        matching = [i for i in _issues(data) if i["rule_id"] == "FeatureSpec.disc_boolean"]
        assert all(i["severity"] == "warning" for i in matching)


# ---------------------------------------------------------------------------
# spec-disc-enum-values.md: DISC subsection with enum values → no disc_boolean warning
# ---------------------------------------------------------------------------

class TestSpecDiscEnumValues:
    def test_exit_code_zero(self):
        code, _ = _run(FIXTURES / "specs" / "spec-disc-enum-values.md")
        assert code == 0

    def test_disc_boolean_not_flagged(self):
        _, data = _run(FIXTURES / "specs" / "spec-disc-enum-values.md")
        rule_ids = [i["rule_id"] for i in _issues(data)]
        assert "FeatureSpec.disc_boolean" not in rule_ids


# ---------------------------------------------------------------------------
# spec-alg-file-schema-missing.md: ALG-001 matches file-exchange vocab but has
# no populated **File Schema** table → WARNING (does not flip exit code)
# ---------------------------------------------------------------------------

def test_alg_file_schema_missing_warns():
    code, data = _run(FIXTURES / "specs" / "spec-alg-file-schema-missing.md")
    assert code == 0  # warning severity — never flips PASS→FAIL / exit code
    rule_ids = [i["rule_id"] for i in _issues(data)]
    assert "FeatureSpec.alg_file_schema_missing" in rule_ids
    matching = [i for i in _issues(data) if i["rule_id"] == "FeatureSpec.alg_file_schema_missing"]
    assert all(i["severity"] == "warning" for i in matching)


# ---------------------------------------------------------------------------
# spec-alg-file-schema-present.md: ALG-001 has a populated **File Schema** table
# → no alg_file_schema_missing warning
# ---------------------------------------------------------------------------

def test_alg_file_schema_present_passes():
    code, data = _run(FIXTURES / "specs" / "spec-alg-file-schema-present.md")
    assert code == 0
    rule_ids = [i["rule_id"] for i in _issues(data)]
    assert "FeatureSpec.alg_file_schema_missing" not in rule_ids


# ---------------------------------------------------------------------------
# spec-alg-non-file-exchange.md: ALG block has no import/export vocabulary
# (includes an "important" substring guard) → no alg_file_schema_missing warning
# ---------------------------------------------------------------------------

def test_alg_non_file_exchange_no_warn():
    code, data = _run(FIXTURES / "specs" / "spec-alg-non-file-exchange.md")
    assert code == 0
    rule_ids = [i["rule_id"] for i in _issues(data)]
    assert "FeatureSpec.alg_file_schema_missing" not in rule_ids


# ---------------------------------------------------------------------------
# disc_boolean: header/separator normalization (H2 fix)
# Ensures lowercase "| value |" headers and "| --- | --- |" spaced separators
# are excluded from non_bool_table so the boolean detection still fires.
# ---------------------------------------------------------------------------

class TestDiscBooleanHeaderNormalization:
    def test_lowercase_value_header_triggers_disc_boolean(self):
        # spec-disc-bool-lowercase-header.md: boolean DISC with lowercase "| value |" header
        _, data = _run(FIXTURES / "specs" / "spec-disc-bool-lowercase-header.md")
        rule_ids = [i["rule_id"] for i in _issues(data)]
        assert "FeatureSpec.disc_boolean" in rule_ids

    def test_spaced_separator_triggers_disc_boolean(self):
        # spec-disc-bool-spaced-sep.md: boolean DISC with "| --- | --- |" spaced separator
        _, data = _run(FIXTURES / "specs" / "spec-disc-bool-spaced-sep.md")
        rule_ids = [i["rule_id"] for i in _issues(data)]
        assert "FeatureSpec.disc_boolean" in rule_ids

    def test_enum_values_with_spaced_separator_not_flagged(self):
        # spec-disc-enum-spaced-sep.md: enum DISC with spaced separator → no false positive
        _, data = _run(FIXTURES / "specs" / "spec-disc-enum-spaced-sep.md")
        rule_ids = [i["rule_id"] for i in _issues(data)]
        assert "FeatureSpec.disc_boolean" not in rule_ids
# ---------------------------------------------------------------------------
# F2 guard parity: --plan-dir at a file and --spec at a directory both exit 2.
# ---------------------------------------------------------------------------

def _run_plan(plan_dir: Path) -> tuple[int, dict]:
    """Run spec validator with --plan-dir."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT),
         "--plan-dir", str(plan_dir),
         "--project-root", str(REPO_ROOT)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = json.loads(result.stdout)
    return result.returncode, output


# ---------------------------------------------------------------------------
# v27.0.0 (audience split): functional-spec.md with a dev-token (file:line)
# outside a fence → CRITICAL func.dev_token (renamed/split from bc.forbidden_token)
# ---------------------------------------------------------------------------

class TestFunctionalSpecForbiddenToken:
    def test_exit_code_one(self):
        code, _ = _run_plan(FIXTURES / "plan-forbidden-bc")
        assert code == 1

    def test_dev_token_rule_id_present(self):
        _, data = _run_plan(FIXTURES / "plan-forbidden-bc")
        assert "func.dev_token" in _critical_rule_ids(data)

    def test_issue_is_critical(self):
        _, data = _run_plan(FIXTURES / "plan-forbidden-bc")
        matching = [i for i in _issues(data) if i["rule_id"] == "func.dev_token"]
        assert all(i["severity"] == "critical" for i in matching)

    def test_message_mentions_file_line_token(self):
        _, data = _run_plan(FIXTURES / "plan-forbidden-bc")
        matching = [i for i in _issues(data) if i["rule_id"] == "func.dev_token"]
        assert any("LoginController.php:45" in i["message"] for i in matching)


# ---------------------------------------------------------------------------
# feature dir layout: --spec pointing at a feature dir runs both file checks
# ---------------------------------------------------------------------------

class TestSpecAsFeatureDir:
    def test_feature_dir_runs_all_checks(self):
        feature_dir = FIXTURES / "plan-forbidden-bc" / "artifacts" / "features" / "F001_Auth"
        code, data = _run(feature_dir)
        # func.dev_token should be present (file:line in functional-spec.md § 1)
        assert "func.dev_token" in _critical_rule_ids(data)


# ---------------------------------------------------------------------------
# v27.0.0 Phase 01 — the 4 mandatory negative probes (Constraint 2 / Test Matrix).
# Every fixture's technical-spec.md declares FR-001 + BR-001 (see
# plan-func-probes/artifacts/features/*/technical-spec.md); each functional-spec.md
# variant breaks exactly one contract so the corresponding critical rule_id is the
# ONLY thing that differs from a clean pass. Each must exit non-zero (Constraint 2 —
# a passing test at a non-zero exit is not itself sufficient; the rule_id must be
# the asserted cause).
# ---------------------------------------------------------------------------

_PROBES_PLAN = FIXTURES / "plan-func-probes"


class TestNegativeProbeOldHeadingRejected:
    """Probe 1a (pass B's original, kept — covers a DIFFERENT surface than 1b below):
    functional-spec.md § 4 uses the OLD '### BR-001_Slug' heading form instead of a
    one-line bullet — the old form must be REJECTED, not silently ignored. BR-001 is
    declared in technical-spec.md but never surfaced as a proper § 4 one-liner →
    func.code_unsurfaced (the silent-pass guard). This exercises functional-spec.md's
    own bullet/tag parsing (_FUNC_RULE_TAG_RE), not _spec_block_lib's block-heading
    regexes — see TestNegativeProbeLegacyTechnicalSpecHeadingRejected for the genuine
    Test Matrix row 1 probe (a technical-spec.md carrying the retired heading form)."""

    def test_exit_code_one(self):
        code, _ = _run(_PROBES_PLAN / "artifacts" / "features" / "F001_Auth")
        assert code == 1

    def test_code_unsurfaced_rule_id_present(self):
        _, data = _run(_PROBES_PLAN / "artifacts" / "features" / "F001_Auth")
        assert "func.code_unsurfaced" in _critical_rule_ids(data)

    def test_message_names_br_001(self):
        _, data = _run(_PROBES_PLAN / "artifacts" / "features" / "F001_Auth")
        matching = [i for i in _issues(data) if i["rule_id"] == "func.code_unsurfaced"]
        assert any("BR-001" in i["message"] for i in matching)


class TestNegativeProbeLegacyTechnicalSpecHeadingRejected:
    """Probe 1b (the genuine Test Matrix row 1): a technical-spec.md carrying the
    OLD '### BR-001_Slug' heading form. This is the actual silent-pass risk named in
    phase-01's Key Insight — BLOCK_HEADING_PREFIX_RE/DEC_BLOCK_RE (the new trailing-tag
    regexes) simply don't match this shape, so `_check_dec_blocks`, `_check_linked_fr`,
    and the per-block Source gate would ALL silently skip the block and report zero
    issues if nothing else caught it. FeatureSpec.legacy_block_heading is the dedicated
    catch: the fixture's BR-001 block otherwise has Linked FR + Source both present, so
    this rule_id is the ONLY thing that should fire — proving the old form is REJECTED,
    not ignored."""

    _FIXTURE = FIXTURES / "specs" / "spec-legacy-block-heading.md"

    def test_exit_code_one(self):
        code, _ = _run(self._FIXTURE)
        assert code == 1

    def test_legacy_block_heading_rule_id_present(self):
        _, data = _run(self._FIXTURE)
        assert "FeatureSpec.legacy_block_heading" in _critical_rule_ids(data)

    def test_message_names_br_001(self):
        _, data = _run(self._FIXTURE)
        matching = [i for i in _issues(data) if i["rule_id"] == "FeatureSpec.legacy_block_heading"]
        assert any("BR-001_MaxLoginAttempts" in i["message"] for i in matching)

    def test_isolated_no_other_criticals(self):
        """The fixture's BR-001 block has both Linked FR and Source — the only
        expected critical is the legacy-heading rejection itself, proving this probe
        isolates the exact contract under test."""
        _, data = _run(self._FIXTURE)
        assert _critical_rule_ids(data) == ["FeatureSpec.legacy_block_heading"]


class TestNegativeProbeEmptyBlockFails:
    """Probe 2: § 4 present but literally zero BR one-liners ('None.') — an
    empty-block file must FAIL, proving the surfacing check still matches
    something real rather than vacuously passing on an empty section."""

    def test_exit_code_one(self):
        code, _ = _run(_PROBES_PLAN / "artifacts" / "features" / "F002_Empty")
        assert code == 1

    def test_code_unsurfaced_rule_id_present(self):
        _, data = _run(_PROBES_PLAN / "artifacts" / "features" / "F002_Empty")
        assert "func.code_unsurfaced" in _critical_rule_ids(data)


class TestNegativeProbeDevTokenLive:
    """Probe 3: functional-spec.md contains a bare 'src/auth.ts:42' file:line
    citation outside a fence — the dev-token scan must be live."""

    def test_exit_code_one(self):
        code, _ = _run(_PROBES_PLAN / "artifacts" / "features" / "F003_DevToken")
        assert code == 1

    def test_dev_token_rule_id_present(self):
        _, data = _run(_PROBES_PLAN / "artifacts" / "features" / "F003_DevToken")
        assert "func.dev_token" in _critical_rule_ids(data)

    def test_code_surfacing_unaffected(self):
        """BR-001/FR-001 ARE properly surfaced in this fixture — only the dev-token
        scan should fire, proving the probes are isolated (no incidental noise)."""
        _, data = _run(_PROBES_PLAN / "artifacts" / "features" / "F003_DevToken")
        crit = _critical_rule_ids(data)
        assert "func.code_unsurfaced" not in crit
        assert "func.code_orphan" not in crit


class TestNegativeProbeSecretShapeLive:
    """Probe 4: functional-spec.md carries a DSN-shaped string
    (postgres://user:hunter2@db.internal:5432/app) AND an API_KEY= value outside a
    fence — the secret-shape scan (H-SEC4) must be live, using BOTH
    scrub_generic_secret and scrub_credentials (the fixture covers both families)."""

    def test_exit_code_one(self):
        code, _ = _run(_PROBES_PLAN / "artifacts" / "features" / "F004_SecretShape")
        assert code == 1

    def test_secret_shape_rule_id_present(self):
        _, data = _run(_PROBES_PLAN / "artifacts" / "features" / "F004_SecretShape")
        assert "func.secret_shape" in _critical_rule_ids(data)

    def test_both_secret_families_flagged(self):
        """At least 2 func.secret_shape hits — one per scrubber family (DSN via
        scrub_credentials, API_KEY= via scrub_generic_secret)."""
        _, data = _run(_PROBES_PLAN / "artifacts" / "features" / "F004_SecretShape")
        matching = [i for i in _issues(data) if i["rule_id"] == "func.secret_shape"]
        assert len(matching) >= 2, matching


class TestInputGuards:
    def test_plan_dir_is_file_exits_two(self, tmp_path):
        bogus = tmp_path / "not-a-dir.txt"
        bogus.write_text("x")
        result = subprocess.run(
            [sys.executable, str(SCRIPT),
             "--plan-dir", str(bogus),
             "--project-root", str(tmp_path)],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 2
        assert "not a directory" in result.stderr.lower()

    def test_spec_is_directory_exits_two(self, tmp_path):
        # A dir whose plan_dir (parent.parent) lies outside project_root triggers exit 2.
        # Note: --spec <dir> is valid for 4-file feature dirs; the guard here is assert_under.
        result = subprocess.run(
            [sys.executable, str(SCRIPT),
             "--spec", str(tmp_path),
             "--project-root", str(tmp_path)],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 2


class TestScrCodeBoundaryRegression:
    """The SCR### cell match must accept the documented `SCR###_Slug` form.

    Regression guard: the original `\\bSCR\\d{3}\\b` anchor never matched
    "SCR001_Login" — "_" is a word character, so there is no boundary after the
    digits. Every correctly-authored Screens table row using the slug form would
    have raised a false-positive `func.screens_scr_unresolved` critical. Same
    boundary class as the `_TECH_CODE_RE` trailing-\\b bug fixed alongside it.
    """

    import re as _re

    SCR_CELL_RE = _re.compile(r"\bSCR\d{3}(?!\d)")

    def test_bare_code_matches(self):
        assert self.SCR_CELL_RE.search("SCR001")

    def test_slug_suffixed_code_matches(self):
        # The exact form the old anchor rejected.
        assert self.SCR_CELL_RE.search("SCR001_Login")

    def test_slug_suffixed_code_in_table_cell_matches(self):
        assert self.SCR_CELL_RE.search("| SCR012_Checkout |")

    def test_four_digit_code_still_rejected(self):
        # (?!\d) must keep rejecting an over-long code rather than matching a prefix.
        assert not self.SCR_CELL_RE.search("SCR0012")

    def test_validator_uses_the_fixed_anchor(self):
        """The production source must not regress to a trailing \\b."""
        src = (SCRIPTS_DIR / "validate_feature_spec.py").read_text(encoding="utf-8")
        assert r"\bSCR\d{3}\b" not in src, "trailing \\b anchor reintroduced"
        assert r"\bSCR\d{3}(?!\d)" in src


# ---------------------------------------------------------------------------
# Phase 03 (B4a) — func.dev_token becomes inline-code aware. A dev token
# wrapped in a backtick-delimited span (`` `x` ``, or a longer run like
# ``x`y`` whose content itself contains a backtick) is a deliberate markdown
# fence around a quoted token, not prose leakage, and must stop firing.
# func.secret_shape is explicitly OUT of this exemption — a secret inside
# backticks is still a leaked secret (T6 is the standing guard for that).
# See plans/260817-1420-rebuild-spec-v27-migrate-legacy-docs/
# phase-03-validator-inline-code-awareness.md for the full test matrix (T1-T9).
# ---------------------------------------------------------------------------

_FENCED_TOKEN_PLAN = FIXTURES / "plan-func-fenced-token"


class TestInlineCodeDevTokenExempt:
    """T1/T3/T8/T9: the full-pass fixture — every dev token on the page is
    inside a recognized inline-code span, so the whole feature dir must exit
    0 with zero criticals. Covers a single-backtick span (T1), a second
    single-backtick span later in the same file (T3), and a double-backtick
    span whose content itself contains a literal backtick (T8)."""

    _DIR = _FENCED_TOKEN_PLAN / "artifacts" / "features" / "F001_Fenced"

    def test_t9_full_file_pass_exit_zero(self):
        code, data = _run(self._DIR)
        assert code == 0
        assert _critical_rule_ids(data) == []

    def test_t1_backtick_wrapped_http_verb_no_dev_token(self):
        _, data = _run(self._DIR)
        assert "func.dev_token" not in _rule_ids(data)

    def test_t3_backtick_wrapped_file_line_no_dev_token(self):
        # Same run as above — asserted separately per the T3 matrix row: a
        # `src/auth.ts:42` shaped token inline must not fire either.
        _, data = _run(self._DIR)
        assert "func.dev_token" not in _rule_ids(data)

    def test_t8_double_backtick_span_with_interior_backtick_no_dev_token(self):
        # The fixture's third Overview line is ``the endpoint was POST
        # `secured` behind a gateway`` — a double-backtick delimiter whose
        # content contains a nested single backtick around "secured". If the
        # stripper mismatched the delimiter length, "POST" inside would leak
        # through and fire — it must not.
        _, data = _run(self._DIR)
        assert "func.dev_token" not in _rule_ids(data)


class TestInlineCodeDevTokenRuleStillLive:
    """T2: a BARE HTTP verb outside any fence must still fire — the inline-
    code exemption is granular to actual spans, not a blanket relaxation."""

    def test_t2_bare_http_verb_still_fires(self):
        _DIR = _FENCED_TOKEN_PLAN / "artifacts" / "features" / "F002_BareVerb"
        _, data = _run(_DIR)
        matching = [i for i in _issues(data) if i["rule_id"] == "func.dev_token"]
        assert any("POST" in i["message"] for i in matching)


class TestInlineCodeMixedLineIsolatesRealToken:
    """T5: one line carries both a fenced token and a bare one — exactly one
    func.dev_token for that line, naming the bare (real) token, at the
    correct line number."""

    _DIR = _FENCED_TOKEN_PLAN / "artifacts" / "features" / "F003_MixedLine"

    def test_exactly_one_dev_token_issue(self):
        _, data = _run(self._DIR)
        matching = [i for i in _issues(data) if i["rule_id"] == "func.dev_token"]
        assert len(matching) == 1, matching

    def test_reports_the_bare_token_not_the_fenced_one(self):
        _, data = _run(self._DIR)
        matching = [i for i in _issues(data) if i["rule_id"] == "func.dev_token"]
        assert "DELETE" in matching[0]["message"]

    def test_line_number_is_the_overview_line(self):
        _, data = _run(self._DIR)
        matching = [i for i in _issues(data) if i["rule_id"] == "func.dev_token"]
        func_spec = (self._DIR / "functional-spec.md").read_text(encoding="utf-8").splitlines()
        expected_line = next(
            i + 1 for i, ln in enumerate(func_spec) if "then DELETE /y" in ln
        )
        assert matching[0]["location"]["line"] == expected_line


class TestInlineCodeUnclosedBacktickFailsClosed:
    """T7: an opening backtick with no matching close on the line must NOT
    swallow the rest of the line into an exemption — the bare token after it
    still fires. A false negative here would hide a real dev token."""

    def test_unclosed_backtick_still_fires(self):
        _DIR = _FENCED_TOKEN_PLAN / "artifacts" / "features" / "F004_Unclosed"
        _, data = _run(_DIR)
        matching = [i for i in _issues(data) if i["rule_id"] == "func.dev_token"]
        assert any("POST" in i["message"] for i in matching)


class TestInlineCodeSecretShapeNotExempted:
    """T6: the scope guard's standing test — a secret inside backticks must
    still raise func.secret_shape. The dev-token exemption must never be
    extended to the secret scan."""

    def test_secret_in_backticks_still_fires(self):
        _DIR = _FENCED_TOKEN_PLAN / "artifacts" / "features" / "F005_SecretInBackticks"
        _, data = _run(_DIR)
        assert "func.secret_shape" in _critical_rule_ids(data)


class TestInlineCodeBareFileLineStillFires:
    """T4: a bare `path/file.ext:N` shaped token (no backticks) still fires.
    Restates the phase-00 regression guard already covered by
    TestNegativeProbeDevTokenLive against the SAME unmodified fixture, to
    make the T4 test-matrix row explicit in this phase's own test class
    rather than adding a duplicate fixture for an already-proven case."""

    def test_bare_file_line_token_still_fires(self):
        _DIR = _PROBES_PLAN / "artifacts" / "features" / "F003_DevToken"
        _, data = _run(_DIR)
        assert "func.dev_token" in _critical_rule_ids(data)


class TestDocsRootModeMismatchRejectedLoudly:
    """Defect 2 (p14-migration-report.md § Risks item 2): this script's own
    `--docs-root` help text says "project_root" mode, but
    validate_reading_guide_db_impact.py / validate_feature_screen_link.py /
    run_doc_migrations.py all use the identical flag name to mean the `docs/`
    folder itself. Passing THIS script's `--docs-root` the `docs/` folder (the
    other three scripts' convention) used to silently return `{"specs": {}}` at
    exit 0 -- a clean bill of health over zero files examined, because
    `iter_docs_technical_specs` then looked for the non-existent
    `<docs>/docs/features`. Fixed by refusing loudly on the tell-tale shape
    (a `features/` dir sitting directly under the given path) rather than
    guessing which directory was intended."""

    @staticmethod
    def _make_feature_dir(project_root: Path) -> None:
        feat_dir = project_root / "docs" / "features" / "F001_Test"
        feat_dir.mkdir(parents=True)
        (feat_dir / "technical-spec.md").write_text("# F001_Test\n", encoding="utf-8")
        (feat_dir / "functional-spec.md").write_text("# F001_Test\n", encoding="utf-8")

    @staticmethod
    def _run_docs_root(docs_root: Path, project_root: Path) -> tuple[int, str, str]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT),
             "--docs-root", str(docs_root),
             "--project-root", str(project_root)],
            capture_output=True, text=True, timeout=30,
        )
        return result.returncode, result.stdout, result.stderr

    def test_docs_folder_itself_is_rejected_not_silently_empty(self, tmp_path):
        """Reaches the exact reported branch: pass `<project>/docs` (the docs/
        folder itself, matching the OTHER 3 scripts' convention) as this
        script's --docs-root. Pre-fix this returned exit 0 / `{"specs": {}}`;
        post-fix it must refuse loudly instead of reporting a clean pass over
        zero files examined."""
        self._make_feature_dir(tmp_path)
        code, out, err = self._run_docs_root(tmp_path / "docs", tmp_path)
        assert code != 0, (
            f"must not exit 0 when the docs/ folder itself was passed; "
            f"stdout={out!r} stderr={err!r}"
        )
        assert "docs" in err.lower() and "project root" in err.lower()

    def test_correct_project_root_still_scans_normally(self, tmp_path):
        """Regression guard: the EXISTING, tested convention (--docs-root =
        project root containing docs/features/, per
        test_draft_provenance.py::_run_feature_spec_docs_root) must keep working
        unchanged -- this fix only rejects the mismatched case, it does not
        change what --docs-root means for a correctly-formed call."""
        self._make_feature_dir(tmp_path)
        code, out, err = self._run_docs_root(tmp_path, tmp_path)
        data = json.loads(out)
        assert "F001_Test" in data.get("specs", {}), f"stderr={err!r}"
