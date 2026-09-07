"""P07 (human-readable SOT) — functional-spec.md renumber (10 -> 13 sections) and
its pre-SOT degradation window.

Covers what phase-07-functional-spec-shape.md's Todo List calls for:
  - REQUIRED_H2_FUNC is the exact 13-entry, ordered list from target-shape-spec.md § 2.
  - templates/functional-spec-template.md's own H2 sequence matches REQUIRED_H2_FUNC
    verbatim (the anti-drift test — the template is the one consumer not mechanically
    bound to the constant).
  - func.sections_pre_sot fires exactly once against a real pre-SOT corpus fixture and
    mutes every other section-shape rule for that file (WARN-first degradation window).
  - The new/changed rule_ids: func.capabilities_empty, func.capability_fr_dangling,
    func.risk_as_rule, func.user_story_shape.
  - Every re-pointed positional binding (b2..b11) is proven to check the NEW section
    index, not a stale one, via a violation planted in the new-numbered section.

Every negative test states, in its own comment, which branch it reaches — a test whose
input never reaches the code under test proves nothing (this repo has shipped that bug
before; see docs/journals/ for the incident).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[5]
_SOT_CORPUS = Path(__file__).resolve().parent / "fixtures" / "sot-corpus"
"""Real generated corpus, git-tracked. Lived under `plans/` (gitignored) until it took
the whole CI suite down at collection time — see fixtures/sot-corpus/README.md."""
SCRIPT = SCRIPTS_DIR / "validate_feature_spec.py"
TEMPLATE = SCRIPTS_DIR.parent / "templates" / "functional-spec-template.md"
EVIDENCE_G2 = (
    _SOT_CORPUS / "corpus-g2" / "F999_Sample.functional-spec.md"
)

sys.path.insert(0, str(SCRIPTS_DIR))
import validate_feature_spec as vfs  # noqa: E402
from _spec_constants import REQUIRED_H2_FUNC  # noqa: E402

# ---------------------------------------------------------------------------
# target-shape-spec.md § 2 — normative, verbatim (this IS the source of truth
# copied into _spec_constants.py; this literal catches drift in either file).
# ---------------------------------------------------------------------------
_EXPECTED_REQUIRED_H2_FUNC = [
    "## 1. Overview",
    "## 2. Functional Capabilities",
    "## 3. Open Decisions",
    "## 4. Requirements",
    "## 5. Business Rules",
    "## 6. Screens",
    "## 7. User Stories",
    "## 8. Scenarios",
    "## 9. Edge Cases",
    "## 10. Edge Behaviours to Verify",
    "## 11. Risks & Known Issues",
    "## 12. Dependencies",
    "## 13. Configuration",
]


def _run(spec_path: Path, root: Path = REPO_ROOT) -> tuple[int, dict]:
    """`root` MUST be an ancestor of `spec_path` — the script's own `assert_under`
    guard exits 2 (empty stdout) otherwise. Fixtures under a pytest `tmp_path` are
    never under REPO_ROOT, so those callers pass `root=tmp_path`."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--spec", str(spec_path), "--project-root", str(root)],
        capture_output=True, text=True, timeout=30,
    )
    assert result.stdout.strip(), f"empty stdout — stderr was: {result.stderr}"
    return result.returncode, json.loads(result.stdout)


def _issues(data: dict) -> list[dict]:
    out: list[dict] = []
    for entry in data.get("specs", {}).values():
        out.extend(entry.get("issues", []))
    return out


def _rule_ids(data: dict) -> list[str]:
    return [i["rule_id"] for i in _issues(data)]


def _h2_and_headings(lines: list[str]):
    headings, _blocks = vfs.parse_headings_and_blocks(lines)
    h2 = [(i, h) for i, h in headings if h.startswith("## ") and not h.startswith("### ")]
    return h2, headings


# A minimal, clean technical-spec.md (v27.x — human-readable SOT, 5-bucket retaxonomy)
# — declares nothing, so `_check_code_surfacing`'s tech_all is empty and never
# produces incidental func.code_orphan noise on fixtures that don't care about
# code-surfacing. Tests that DO care build their own (see the .replace() calls below,
# which inject a real FR-001/BR-001 pair into ## 2./## 4. instead).
_MINIMAL_TECH_SPEC = """\
# F900_Sot — SOT Test

## 1. Technical Overview
Overview text.

## 2. Functional → Technical Mapping

| Code | Name | Where it is implemented | Technical notes | Source |
|------|------|--------------------------|------------------|--------|

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

### 4.1 SOT Test

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

**Source:** `app/models/placeholder.rb:1-3`

### 5.5 Artifact References
None.
"""


# ===========================================================================
# Section A — REQUIRED_H2_FUNC shape + template anti-drift
# ===========================================================================

class TestRequiredH2FuncShape:
    def test_thirteen_entries_exact_order(self):
        assert REQUIRED_H2_FUNC == _EXPECTED_REQUIRED_H2_FUNC

    def test_scope_non_scope_and_actors_not_promoted_to_h2(self):
        """target-shape-spec.md § 4 Deviations: Scope/Non-Scope/Actors stay FIELDS
        inside § 1 Overview — asserting their absence from the H2 list guards
        against a future 'helpful' promotion the deviation explicitly rejects."""
        for stray in ("## Scope", "## Non-Scope", "## Actors"):
            assert stray not in REQUIRED_H2_FUNC


class TestTemplateAntiDrift:
    def _template_h2_sequence(self) -> list[str]:
        lines = TEMPLATE.read_text(encoding="utf-8").splitlines()
        h2, _ = _h2_and_headings(lines)
        return [h for _, h in h2]

    def test_template_h2_sequence_matches_constant(self):
        assert self._template_h2_sequence() == REQUIRED_H2_FUNC

    def test_anti_drift_comparison_actually_discriminates(self):
        """Self-test of the assertion above: a template sequence missing one
        section must NOT compare equal to REQUIRED_H2_FUNC. Proves
        test_template_h2_sequence_matches_constant would fail loudly on a real
        drift, rather than the comparison being vacuously true (== on two
        identical lists tells you nothing about whether == would ever be False)."""
        drifted = [h for h in self._template_h2_sequence() if h != "## 11. Risks & Known Issues"]
        assert drifted != REQUIRED_H2_FUNC


# ===========================================================================
# Section B — func.sections_pre_sot degradation window
# ===========================================================================

class TestPreSotDegradation:
    def test_real_corpus_g2_fixture_produces_exactly_one_finding(self):
        """The real P00 fixture (10-section shape, '## 2. Open Decisions' present)
        must produce ONLY func.sections_pre_sot — not a wall of func.missing_h2 /
        func.code_unsurfaced noise keyed on headings that don't exist in this shape.
        Direct-import against a nonexistent tech_path (empty tech_text) isolates the
        functional half exactly, matching the phase's own success criterion."""
        assert EVIDENCE_G2.is_file(), f"fixture missing: {EVIDENCE_G2}"
        tech_path = EVIDENCE_G2.parent / "F999_Sample.technical-spec.md"  # deliberately absent
        issues = vfs._check_functional_spec(EVIDENCE_G2, tech_path, REPO_ROOT)
        assert len(issues) == 1, issues
        assert issues[0]["rule_id"] == "func.sections_pre_sot"
        assert issues[0]["severity"] == "warning"

    def test_pre_sot_is_warning_not_critical_end_to_end(self, tmp_path):
        """A pre-SOT-shaped functional-spec.md paired with a clean technical-spec.md
        must exit 0 (warning-only) — the migration window must WARN, never hard-fail."""
        feat_dir = tmp_path / "docs" / "features" / "F900_Sot"
        feat_dir.mkdir(parents=True)
        (feat_dir / "technical-spec.md").write_text(_MINIMAL_TECH_SPEC, encoding="utf-8")
        (feat_dir / "functional-spec.md").write_text(
            EVIDENCE_G2.read_text(encoding="utf-8"), encoding="utf-8"
        )
        code, data = _run(feat_dir, root=tmp_path)
        assert code == 0, _issues(data)
        assert _rule_ids(data) == ["func.sections_pre_sot"]

    def test_new_shape_file_is_not_flagged_pre_sot(self, tmp_path):
        """Negative — reaches the `else` branch of `is_pre_sot` (a genuinely
        13-section file). func.sections_pre_sot must never fire on new-shaped
        content; scaffold_spec.py's own renderer is the real-world instance."""
        sys.path.insert(0, str(SCRIPTS_DIR))
        from scaffold_spec import _render_functional_spec  # noqa: E402
        body = _render_functional_spec("---\nauthored_by: rebuild-spec\n---")
        lines = body.splitlines()
        issues = vfs._check_functional_spec(
            _write_tmp(tmp_path, "functional-spec.md", body),
            tmp_path / "missing-technical-spec.md",
            tmp_path,
        )
        assert "func.sections_pre_sot" not in [i["rule_id"] for i in issues]

    def test_stray_functional_capabilities_heading_unmutes_pre_sot(self, tmp_path):
        """[SA-3 regression] PRE-FIX BEHAVIOUR (recorded, no longer true): this exact
        fixture — a pre-SOT (10-section) file with a stray "## 2. Functional
        Capabilities" heading appended — used to produce ONLY `func.sections_pre_sot`,
        because `is_pre_sot` was a bare `_FUNC_PRE_SOT_SENTINEL in h2_names` membership
        test with no positional/co-occurrence constraint: the sentinel's mere presence
        muted every section-bound critical for the WHOLE file, including the phantom
        FR-999/BR-999/US999 codes sitting right there in the appended § 2 row. That was
        the SA-3 hole this phase closes.

        POST-FIX BEHAVIOUR (asserted here): the co-condition
        (`is_pre_sot = sentinel present AND "## 2. Functional Capabilities" NOT in
        h2_names`) means a file that carries BOTH headings is, by the pre-SOT
        definition itself (a pre-SOT file lacks § 2), no longer pre-SOT — so the
        section-bound checks run for real. Two THINGS follow, both intended, not bugs:
        1. `func.missing_h2` fires (critical) — this file only has 2 of the 13 required
           new-shape headings ("## 1. Overview" and the appended "## 2. Functional
           Capabilities"); the rest are still the OLD numbering (e.g. "## 2. Open
           Decisions", "## 3. Requirements"), which do not match the new required
           strings at all.
        2. `func.capability_fr_dangling` fires (critical) — the appended § 2 row cites
           FR-999, which is declared nowhere `_func_h2_bounds` can find (there is no
           "## 4. Requirements" heading in this file — only the old "## 3.
           Requirements" — so `_func_code_sets`'s FR set is empty and FR-999 is
           unconditionally a phantom).
        This is the co-condition's whole point: an ambiguous/malformed document that
        mixes old and new headings now reads as "needs attention", not as a silently
        muted pass."""
        body = EVIDENCE_G2.read_text(encoding="utf-8") + (
            "\n\n<!-- a stray new-shape-looking fragment, still inside an otherwise "
            "pre-SOT doc — this is what used to defeat the whole-document mute (SA-3) -->\n"
            "## 2. Functional Capabilities\n\n"
            "| ID | Capability | What the user can do | User Stories | Requirements | "
            "Business Rules | Screens |\n"
            "|----|------------|------------------------|-----------------|---------------|"
            "-------------------|---------|\n"
            "| CAP-01 | X | Y | US999 | FR-999 | BR-999 | N/A |\n"
        )
        func_path = _write_tmp(tmp_path, "functional-spec.md", body)
        issues = vfs._check_functional_spec(func_path, tmp_path / "absent.md", tmp_path)
        rule_ids = [i["rule_id"] for i in issues]
        assert "func.sections_pre_sot" not in rule_ids
        assert "func.missing_h2" in rule_ids
        assert any(
            i["rule_id"] == "func.capability_fr_dangling" and "FR-999" in i["message"]
            for i in issues
        )


def _write_tmp(tmp_path: Path, name: str, body: str) -> Path:
    p = tmp_path / name
    p.write_text(body, encoding="utf-8")
    return p


# ===========================================================================
# Section C — new/changed rule_ids
# ===========================================================================

_CAP_HEADER = (
    "| ID | Capability | What the user can do | User Stories | Requirements | "
    "Business Rules | Screens |\n"
    "|----|------------|------------------------|-----------------|---------------|"
    "-------------------|---------|\n"
)


def _combine(*blocks: str) -> tuple[list[str], list[tuple[int, int]]]:
    """Concatenate line-list blocks into ONE combined `lines` array and return
    (combined_lines, [bounds_per_block]) — the shape every _check_* function under
    test actually expects: every bounds tuple indexes into the SAME shared `lines`
    array, never a per-section slice on its own. Building bounds against separate
    small arrays (an earlier draft's bug) silently reads the wrong lines and proves
    nothing."""
    combined: list[str] = []
    bounds: list[tuple[int, int]] = []
    for block in blocks:
        block_lines = block.splitlines()
        start = len(combined)
        combined.extend(block_lines)
        bounds.append((start, len(combined)))
    return combined, bounds


def _check_caps(lines, b2, b4, b5=None, b6=None, b7=None):
    """Thin wrapper pinning the new (phase 05) 8-arg signature to the old 5-arg call
    shape these tests were written against — `b5`/`b6`/`b7` default to `None` when a
    test's fixture only cares about §§ 2/4 (US/BR/SCR then declare nothing, so the
    reverse check has nothing to say about those families; see the phase 05
    `TestMaximalCount`/`TestClaimsUnfilled` classes below for fixtures that populate
    all four)."""
    return vfs._check_capabilities_section(lines, b2, b4, b5, b6, b7, Path("f.md"), Path("."))


class TestCapabilitiesEmpty:
    """func.capabilities_empty (warning): § 2 has 0 data rows while § 4 already
    declares >= 1 real FR-###."""

    def test_fires_when_empty_and_fr_declared(self):
        lines, (b2, b4) = _combine(_CAP_HEADER, "- **FR-101** do the thing\n")
        # Reaches: `if not rows:` True (state "absent"), `elif fr_in_4:` True (1 real FR
        # bullet) -> func.capabilities_empty. [SA-2] cap.code_unclaimed ALSO fires now
        # for FR-101 (declared, claimed by no row) — the reverse check runs
        # unconditionally of the empty-§2 branch; see TestMaximalCount for the dedicated
        # exact-count assertion on this exact restructure.
        issues = _check_caps(lines, b2, b4)
        cap_empty = [i for i in issues if i["rule_id"] == "func.capabilities_empty"]
        assert len(cap_empty) == 1
        assert cap_empty[0]["severity"] == "warning"
        assert any(i["rule_id"] == "cap.code_unclaimed" for i in issues)

    def test_absent_when_empty_and_no_fr_declared(self):
        lines, (b2, b4) = _combine(_CAP_HEADER, "{No FR-### declared yet.}\n")
        # Reaches: `if not rows:` True, `elif fr_in_4:` False (no real FR bullet); no
        # family declares anything (b5/b6/b7 absent), so the reverse check is silent too.
        issues = _check_caps(lines, b2, b4)
        assert issues == []

    def test_absent_when_rows_present(self):
        lines, (b2, b4) = _combine(
            _CAP_HEADER + "| CAP-01 | Sign in | Do the thing | US001 | FR-101 | BR-001 | N/A |\n",
            "- **FR-101** do the thing\n",
        )
        # Reaches: `if rows:` True — short-circuits past the emptiness branch.
        issues = _check_caps(lines, b2, b4)
        assert not any(i["rule_id"] == "func.capabilities_empty" for i in issues)

    def test_absent_when_section_missing(self):
        # Reaches: `if not b2: return []` — the func.missing_h2 check owns this case.
        issues = _check_caps(["x"], None, None)
        assert issues == []


class TestCapabilityFrDangling:
    """func.capability_fr_dangling (critical): a § 2 Requirements cell cites an
    FR-### not declared in § 4."""

    def test_fires_on_phantom_code(self):
        lines, (b2, b4) = _combine(
            _CAP_HEADER + "| CAP-01 | Sign in | Do the thing | US001 | FR-999 | BR-001 | N/A |\n",
            "- **FR-101** do the thing\n",
        )
        # Reaches: rows truthy, req_idx found, FR-999 not in fr_in_4.
        issues = _check_caps(lines, b2, b4)
        assert any(
            i["rule_id"] == "func.capability_fr_dangling" and i["severity"] == "critical"
            and "FR-999" in i["message"]
            for i in issues
        )

    def test_absent_when_code_declared(self):
        lines, (b2, b4) = _combine(
            _CAP_HEADER + "| CAP-01 | Sign in | Do the thing | US001 | FR-101 | BR-001 | N/A |\n",
            "- **FR-101** do the thing\n",
        )
        # Reaches: rows truthy, req_idx found, FR-101 IS in fr_in_4 — no dangling issue;
        # FR-101 is also the only declared code (US/BR/SCR sets empty) and it IS claimed
        # by CAP-01's Requirements cell, so cap.code_unclaimed is silent too -> [].
        issues = _check_caps(lines, b2, b4)
        assert issues == []


class TestRiskAsRule:
    """func.risk_as_rule (warning): a § 5 Business Rules line reading like an
    observed defect, with no § 11 Risks & Known Issues counterpart."""

    def test_fires_on_defect_language_with_no_risk_row(self):
        lines, (b5, b11) = _combine(
            "- Discount codes should not stack, but currently they do. (BR-001)\n",
            "N/A — none found.\n",
        )
        # Reaches: has_risk_row False (N/A fallback), then _FUNC_RISK_LANGUAGE_RE matches
        # "should not" on the BR line.
        issues = vfs._check_risk_as_rule(lines, b5, b11, Path("f.md"), Path("."))
        assert len(issues) == 1
        assert issues[0]["rule_id"] == "func.risk_as_rule"
        assert issues[0]["severity"] == "warning"

    def test_absent_when_risk_row_recorded(self):
        lines, (b5, b11) = _combine(
            "- Discount codes should not stack, but currently they do. (BR-001)\n",
            "| ID | Type | Description | Impact | Status |\n"
            "|----|------|--------------|--------|--------|\n"
            "| RISK-01 | known-issue | Discount stacking bug | Revenue leak | [UNVERIFIED] |\n",
        )
        # Reaches: has_risk_row True (3 table rows > 2) -> early `return []`.
        issues = vfs._check_risk_as_rule(lines, b5, b11, Path("f.md"), Path("."))
        assert issues == []

    def test_absent_when_no_defect_language(self):
        lines, (b5, b11) = _combine(
            "- Passwords are hashed before storage. (BR-001)\n",
            "N/A — none found.\n",
        )
        # Reaches: has_risk_row False, then the regex search finds no match at all.
        issues = vfs._check_risk_as_rule(lines, b5, b11, Path("f.md"), Path("."))
        assert issues == []

    def test_absent_when_business_rules_section_missing(self):
        # Reaches: `if not b5: return []`.
        issues = vfs._check_risk_as_rule(["x"], None, None, Path("f.md"), Path("."))
        assert issues == []


class TestUserStoryShape:
    """func.user_story_shape (warning): every § 7 story block must lead with
    **Actor:**/**Goal:**/**Business value:** fields."""

    def _bounds_for(self, body: str):
        lines = body.splitlines()
        full_lines = ["## 7. User Stories"] + lines + ["## 8. Scenarios"]
        headings, _ = vfs.parse_headings_and_blocks(full_lines)
        return full_lines, headings, (0, len(full_lines) - 1)

    def test_fires_when_fields_missing(self):
        body = (
            "### US001_Login — User logs in\n\n"
            "A registered user signs in with valid credentials.\n\n"
            "**Acceptance Criteria:**\n- [ ] sees the dashboard\n"
        )
        lines, headings, b7 = self._bounds_for(body)
        # Reaches: a matching `### US###` heading with none of the 3 required
        # bold fields anywhere in its block.
        issues = vfs._check_user_story_shape(lines, headings, b7, Path("f.md"), Path("."))
        assert len(issues) == 1
        assert issues[0]["rule_id"] == "func.user_story_shape"
        assert issues[0]["severity"] == "warning"
        assert "**Actor:**" in issues[0]["message"]
        assert "**Goal:**" in issues[0]["message"]
        assert "**Business value:**" in issues[0]["message"]

    def test_absent_when_all_fields_present(self):
        body = (
            "### US001_Login — User logs in\n\n"
            "**Actor:** Registered User\n"
            "**Goal:** Sign in with valid credentials\n"
            "**Business value:** Reach account features\n\n"
            "**Acceptance Criteria:**\n- [ ] sees the dashboard\n"
        )
        lines, headings, b7 = self._bounds_for(body)
        # Reaches: all three field regexes match within the block.
        issues = vfs._check_user_story_shape(lines, headings, b7, Path("f.md"), Path("."))
        assert issues == []

    def test_absent_when_no_story_heading_yet(self):
        body = "{Populated once technical-spec.md declares US### stories.}\n"
        lines, headings, b7 = self._bounds_for(body)
        # Reaches: `us_heads` is empty (fresh-scaffold placeholder, no ### heading).
        issues = vfs._check_user_story_shape(lines, headings, b7, Path("f.md"), Path("."))
        assert issues == []

    def test_absent_when_section_missing(self):
        # Reaches: `if not b7: return []`.
        issues = vfs._check_user_story_shape(["x"], [], None, Path("f.md"), Path("."))
        assert issues == []


# ===========================================================================
# Section D — re-pointed positional bindings: a violation planted in the NEW
# section number must fire. A rule silently checking a stale (old-numbered)
# section would "pass" a clean file for the wrong reason; only a POSITIVE
# violation in the new location proves the binding was actually re-pointed.
# ===========================================================================

_FULL_NEW_SHAPE_OK = """\
# F900_Sot — SOT Test

**Priority**: P1
**Type**: ui
**Generated**: 2026-08-18

## 1. Overview

**Problem:** Users need to sign in.
**Solution:** Users authenticate with email and password.
**Scope:** Let a registered user sign in.
**Non-Scope:** None called out.

**Actors**

| Actor | Description | Primary goal |
|-------|--------------|---------------|
| Registered User | A user with an account | Sign in |

## 2. Functional Capabilities

| ID | Capability | What the user can do | User Stories | Requirements | Business Rules | Screens |
|----|------------|------------------------|-----------------|---------------|-------------------|---------|
| CAP-01 | Sign in | Authenticate with email and password | US001 | FR-001 | BR-001 | SCR001_Login |

## 3. Open Decisions

None — no unresolved domain confirmations.

## 4. Requirements

### Foundation (0xx)

- **FR-001** Every password must be hashed before storage.

## 5. Business Rules

- Passwords are hashed before storage. (BR-001)

## 6. Screens

| Screen Name | SCR### | What User Sees | What User Can Do |
|-------------|--------|-----------------|-------------------|
| Login | SCR001_Login | Email and password fields | Sign in |

## 7. User Stories

### US001_Login — User logs in

**Actor:** Registered User
**Goal:** Sign in with valid credentials
**Business value:** Reach account features

**Acceptance Criteria:**
- [ ] User sees the dashboard after a successful sign-in.

## 8. Scenarios

### US001_Login — Happy Path

**Given** a registered user, **When** they submit valid credentials, **Then** they see the dashboard.

## 9. Edge Cases

| Scenario | What Happens | User-Facing Message |
|----------|--------------|----------------------|
| Empty password submitted | Request rejected | "Password is required." |
| Wrong password 5 times | Account locked | "Too many attempts, try again later." |
| Unregistered email | Login rejected | "Invalid email or password." |

## 10. Edge Behaviours to Verify

- **FR-001** → Attempting to sign in with a weak password is rejected.

## 11. Risks & Known Issues

N/A — none found.

## 12. Dependencies

N/A — none found.

## 13. Configuration

N/A — no user-facing configuration constants for this feature.
"""


class TestRepointedBindingsFireAtNewSectionNumbers:
    def test_baseline_is_clean(self, tmp_path):
        """Control: the full new-shape functional-spec.md fixture above must
        validate with zero criticals ON THE FUNCTIONAL HALF, proving the positive
        fixtures below fail for the ONE planted reason, not incidental noise. The
        paired technical-spec.md here is a throwaway just rich enough to declare
        FR-001/BR-001 (so func.code_orphan doesn't fire) — its OWN structural
        cleanliness is technical-spec.md's half, out of this phase's scope, so
        this assertion is scoped to functional-spec.md's issues only."""
        feat_dir = tmp_path / "docs" / "features" / "F900_Sot"
        feat_dir.mkdir(parents=True)
        (feat_dir / "technical-spec.md").write_text(
            _MINIMAL_TECH_SPEC.replace(
                "**Business Rules**\n\nNone.\n",
                "**Business Rules**\n\n"
                "### Passwords are hashed before storage (BR-001)\n"
                "**Linked FR:** FR-001\n**Source:** `app/models/user.rb:10-20`\n"
                "**Applies to:** User\n",
            ).replace(
                "| Code | Name | Where it is implemented | Technical notes | Source |\n"
                "|------|------|--------------------------|------------------|--------|\n",
                "| Code | Name | Where it is implemented | Technical notes | Source |\n"
                "|------|------|--------------------------|------------------|--------|\n"
                "| FR-001 | Passwords are hashed before storage | `User` model callback | "
                "| `app/models/user.rb:1-5` |\n",
            ),
            encoding="utf-8",
        )
        (feat_dir / "functional-spec.md").write_text(_FULL_NEW_SHAPE_OK, encoding="utf-8")
        _, data = _run(feat_dir, root=tmp_path)
        func_issues = [
            i for i in _issues(data)
            if i["location"]["file"].endswith("functional-spec.md")
        ]
        assert func_issues == [], func_issues

    def test_open_decisions_shape_fires_at_section_3(self):
        body = _FULL_NEW_SHAPE_OK.replace(
            "None — no unresolved domain confirmations.",
            "| D### | Decision | Default proposal |\n|------|----------|-------------------|\n"
            "| D001 | Some question | Some default |\n",
        )
        lines = body.splitlines()
        h2, _ = _h2_and_headings(lines)
        b3 = vfs._func_h2_bounds(h2, "## 3. Open Decisions", len(lines))
        assert b3 is not None
        # Reaches: table present but missing the 'Blocks work' column.
        issues = vfs._check_open_decisions(lines, b3, Path("f.md"), Path("."))
        assert any(i["rule_id"] == "func.open_decisions_shape" for i in issues)

    def test_screens_scr_unresolved_fires_at_section_6(self):
        body = _FULL_NEW_SHAPE_OK.replace(
            "| Login | SCR001_Login | Email and password fields | Sign in |",
            "| Login | BADCODE | Email and password fields | Sign in |",
        )
        lines = body.splitlines()
        h2, _ = _h2_and_headings(lines)
        b6 = vfs._func_h2_bounds(h2, "## 6. Screens", len(lines))
        assert b6 is not None
        # Reaches: the SCR### column exists but the cell has no resolvable SCR### code.
        issues = vfs._check_screens_section(lines, b6, "ui", Path("f.md"), Path("."))
        assert any(i["rule_id"] == "func.screens_scr_unresolved" for i in issues)

    def test_edge_cases_few_rows_fires_at_section_9(self):
        body = _FULL_NEW_SHAPE_OK.replace(
            "| Wrong password 5 times | Account locked | \"Too many attempts, try again later.\" |\n"
            "| Unregistered email | Login rejected | \"Invalid email or password.\" |\n",
            "",
        )
        lines = body.splitlines()
        h2, _ = _h2_and_headings(lines)
        b9 = vfs._func_h2_bounds(h2, "## 9. Edge Cases", len(lines))
        assert b9 is not None
        # Reaches: only 1 data row for a "ui" feature (minimum 3).
        issues = vfs._check_edge_cases_section(lines, b9, "ui", Path("f.md"), Path("."))
        assert any(i["rule_id"] == "func.edge_cases_few_rows" for i in issues)

    def test_rule_density_fires_at_sections_4_and_5(self):
        body = _FULL_NEW_SHAPE_OK.replace(
            "- Passwords are hashed before storage. (BR-001)",
            "- Passwords are hashed before storage, using a slow adaptive hash function,\n"
            "  re-hashed on every successful login to migrate old cost factors,\n"
            "  and never logged or transmitted in cleartext anywhere. (BR-001)",
        )
        lines = body.splitlines()
        h2, _ = _h2_and_headings(lines)
        b4 = vfs._func_h2_bounds(h2, "## 4. Requirements", len(lines))
        b5 = vfs._func_h2_bounds(h2, "## 5. Business Rules", len(lines))
        # Reaches: avg lines/rule across § 4 + § 5 exceeds the 2-line budget.
        issues = vfs._check_rule_density(lines, b4, b5, Path("f.md"), Path("."))
        assert any(i["rule_id"] == "func.rule_density" for i in issues)

    def test_edge_behaviour_dangling_fires_at_section_10(self):
        body = _FULL_NEW_SHAPE_OK.replace(
            "- **FR-001** → Attempting to sign in with a weak password is rejected.",
            "- **FR-999** → Attempting to sign in with a weak password is rejected.",
        )
        lines = body.splitlines()
        h2, _ = _h2_and_headings(lines)
        b10 = vfs._func_h2_bounds(h2, "## 10. Edge Behaviours to Verify", len(lines))
        # Reaches: FR-999 back-ref is not in the fr_codes_in_4 set ({FR-001}).
        issues = vfs._check_edge_behaviours(lines, b10, {"FR-001"}, Path("f.md"), Path("."))
        assert any(
            i["rule_id"] == "func.edge_behaviour_dangling" and "FR-999" in i["message"]
            for i in issues
        )


# ===========================================================================
# Section E — phase 05 (capability-map) reverse exhaustiveness checks:
# cap.code_unclaimed, cap.double_claimed, cap.claims_unfilled, and the SA-2/SA-3
# fail-open holes those checks sit on top of. `TestRepointedBindingsFireAtNewSectionNumbers
# .test_baseline_is_clean` above (an exhaustive, single-CAP-row § 2) is this section's
# own control: it was confirmed silent BEFORE any test below was written, and it stays
# silent after this phase's changes — the new reverse checks add zero noise to an
# already-exhaustive file.
# ===========================================================================

_FR_BODY_2 = "- **FR-101** do thing one\n- **FR-102** do thing two\n"
_BR_BODY_2 = "- Rule one. (BR-001)\n- Rule two. (BR-002)\n"
_SCR_BODY_2 = (
    "| Screen Name | SCR### | What User Sees | What User Can Do |\n"
    "|-------------|--------|-----------------|-------------------|\n"
    "| One | SCR001 | X | Y |\n"
    "| Two | SCR002 | X | Y |\n"
)
_US_BODY_2 = (
    "### US001_One — story one\n\n**Actor:** A\n**Goal:** B\n**Business value:** C\n\n"
    "### US002_Two — story two\n\n**Actor:** A\n**Goal:** B\n**Business value:** C\n\n"
)


class TestCodeUnclaimed:
    """cap.code_unclaimed (critical): a US###/BR-###/FR-###/SCR### declared anywhere in
    §§ 4-7 is claimed by zero § 2 rows. One test per family — each plants exactly one
    unclaimed code in an otherwise-exhaustive table (one mutation per test)."""

    def test_fires_for_unclaimed_fr(self):
        lines, (b2, b4, b5, b6, b7) = _combine(
            _CAP_HEADER + "| CAP-01 | Sign in | Do it | US001, US002 | FR-101 | BR-001, BR-002 | SCR001, SCR002 |\n",
            _FR_BODY_2, _BR_BODY_2, _SCR_BODY_2, _US_BODY_2,
        )
        # Reaches: declared["FR"] = {FR-101, FR-102}; claims only cites FR-101 ->
        # FR-102 - claims = {"FR-102"} -> family=FR fires, every other family exhaustive.
        issues = _check_caps(lines, b2, b4, b5, b6, b7)
        hits = [i for i in issues if i["rule_id"] == "cap.code_unclaimed"]
        assert len(hits) == 1, issues
        assert "family=FR" in hits[0]["message"] and "FR-102" in hits[0]["message"]

    def test_fires_for_unclaimed_br(self):
        lines, (b2, b4, b5, b6, b7) = _combine(
            _CAP_HEADER + "| CAP-01 | Sign in | Do it | US001, US002 | FR-101, FR-102 | BR-001 | SCR001, SCR002 |\n",
            _FR_BODY_2, _BR_BODY_2, _SCR_BODY_2, _US_BODY_2,
        )
        # Reaches: declared["BR"] = {BR-001, BR-002}; claims only cites BR-001 ->
        # BR-002 - claims = {"BR-002"} -> family=BR fires.
        issues = _check_caps(lines, b2, b4, b5, b6, b7)
        hits = [i for i in issues if i["rule_id"] == "cap.code_unclaimed"]
        assert len(hits) == 1, issues
        assert "family=BR" in hits[0]["message"] and "BR-002" in hits[0]["message"]

    def test_fires_for_unclaimed_scr(self):
        lines, (b2, b4, b5, b6, b7) = _combine(
            _CAP_HEADER + "| CAP-01 | Sign in | Do it | US001, US002 | FR-101, FR-102 | BR-001, BR-002 | SCR001 |\n",
            _FR_BODY_2, _BR_BODY_2, _SCR_BODY_2, _US_BODY_2,
        )
        # Reaches: declared["SCR"] = {SCR001, SCR002}; claims only cites SCR001 ->
        # SCR002 - claims = {"SCR002"} -> family=SCR fires.
        issues = _check_caps(lines, b2, b4, b5, b6, b7)
        hits = [i for i in issues if i["rule_id"] == "cap.code_unclaimed"]
        assert len(hits) == 1, issues
        assert "family=SCR" in hits[0]["message"] and "SCR002" in hits[0]["message"]

    def test_fires_for_unclaimed_us(self):
        lines, (b2, b4, b5, b6, b7) = _combine(
            _CAP_HEADER + "| CAP-01 | Sign in | Do it | US001 | FR-101, FR-102 | BR-001, BR-002 | SCR001, SCR002 |\n",
            _FR_BODY_2, _BR_BODY_2, _SCR_BODY_2, _US_BODY_2,
        )
        # Reaches: declared["US"] = {US001, US002}; claims only cites US001 ->
        # US002 - claims = {"US002"} -> family=US fires.
        issues = _check_caps(lines, b2, b4, b5, b6, b7)
        hits = [i for i in issues if i["rule_id"] == "cap.code_unclaimed"]
        assert len(hits) == 1, issues
        assert "family=US" in hits[0]["message"] and "US002" in hits[0]["message"]

    def test_background_feature_never_fires_family_scr(self):
        """Requirement 9: a § 6 replaced by the background N/A fallback yields an
        empty declared SCR set, so family=SCR can never fire even though the § 2 row's
        own Screens cell reads N/A (not a real SCR### claim, but nothing to claim
        either)."""
        lines, (b2, b4, b6, b7) = _combine(
            _CAP_HEADER + "| CAP-01 | Run nightly | Process the batch | US001 | FR-101 | | N/A |\n",
            "- **FR-101** first\n",
            "N/A — background feature; no user-facing screens.\n",
            "### US001_One — story one\n\n**Actor:** A\n**Goal:** B\n**Business value:** C\n",
        )
        # Reaches: `_FUNC_BACKGROUND_RE.match(...)` True in `_func_code_sets` -> SCR set
        # stays empty -> `if family not in cols` is False (column exists) but
        # `declared.get("SCR", set())` is empty -> nothing to subtract -> no family=SCR issue.
        issues = _check_caps(lines, b2, b4, None, b6, b7)
        assert not any(
            i["rule_id"] == "cap.code_unclaimed" and "family=SCR" in i["message"]
            for i in issues
        )


class TestDoubleClaimed:
    """cap.double_claimed (critical): a code claimed by two or more § 2 rows."""

    def test_fires_when_code_claimed_twice(self):
        lines, (b2, b4, b5, b6, b7) = _combine(
            _CAP_HEADER
            + "| CAP-01 | Sign in | Do it | US012 | FR-101 | BR-001 | SCR001 |\n"
            + "| CAP-02 | Also sign in | Do it too | US012 | FR-102 | BR-002 | SCR002 |\n",
            _FR_BODY_2, _BR_BODY_2, _SCR_BODY_2,
            "### US012_Dup — dup story\n\n**Actor:** A\n**Goal:** B\n**Business value:** C\n",
        )
        # Reaches: US012 appears in two § 2 User Stories cells -> claims["US012"] length 2.
        issues = _check_caps(lines, b2, b4, b5, b6, b7)
        cap_issues = [i for i in issues if i["rule_id"].startswith("cap.")]
        assert len(cap_issues) == 1, issues
        assert cap_issues[0]["rule_id"] == "cap.double_claimed"
        assert "US012" in cap_issues[0]["message"]
        assert "CAP-01" in cap_issues[0]["message"] and "CAP-02" in cap_issues[0]["message"]


class TestCompositeScreenClaims:
    """`SCR###/REG###` is a REGION claim, not a claim on the parent screen shell.

    `references/code-formats.md` § Composite cross-ref parsing: "Grep-style validators
    looking for bare `SCR\\d{3}` patterns MUST also match `SCR\\d{3}(/REG\\d{3}_\\w+)?`".
    `verification-checklist-screen-spec.md` CE3: "An F### with only SCR###/REG### refs does
    NOT own the parent SCR." The old `_cap_claims` tokenizer (`\\bSCR\\d{3}(?!\\d)`) collapsed
    every composite to its parent, so two capabilities owning two different regions of one
    screen collided into a false `cap.double_claimed` critical.

    SILENT input for the fix: two rows claiming two DIFFERENT regions of one screen. The
    fix must not go further than that — `test_same_region_claimed_twice_still_fires` and
    `test_bare_parent_claimed_twice_still_fires` are the must-still-fail guards proving
    `cap.double_claimed` was narrowed, not neutered."""

    _SCR_BODY_1 = (
        "| Screen Name | SCR### | What User Sees | What User Can Do |\n"
        "|-------------|--------|-----------------|-------------------|\n"
        "| One | SCR001 | X | Y |\n"
    )
    _US_BODY_1 = (
        "### US001_One — story one\n\n**Actor:** A\n**Goal:** B\n**Business value:** C\n"
    )

    def _build(self, screens_a: str, screens_b: str):
        return _combine(
            _CAP_HEADER
            + f"| CAP-01 | Sign in | Do it | US001 | FR-101 | BR-001 | {screens_a} |\n"
            + f"| CAP-02 | Sign out | Do it too | | FR-102 | BR-002 | {screens_b} |\n",
            _FR_BODY_2, _BR_BODY_2, self._SCR_BODY_1, self._US_BODY_1,
        )

    def test_two_regions_of_one_screen_do_not_collide(self):
        """THE DEFECT. Reaches: `_cap_claims` keys `SCR001/REG002` and `SCR001/REG005`
        separately, so neither reaches `len(caps) >= 2`."""
        lines, (b2, b4, b5, b6, b7) = self._build("SCR001/REG002", "SCR001/REG005")
        issues = _check_caps(lines, b2, b4, b5, b6, b7)
        assert not [i for i in issues if i["rule_id"] == "cap.double_claimed"], issues

    def test_same_region_claimed_twice_still_fires(self):
        """MUST-STILL-FAIL guard: narrowing the tokenizer must not stop a genuine
        collision. Reaches: both rows key `SCR001/REG002` -> `len(caps) >= 2`."""
        lines, (b2, b4, b5, b6, b7) = self._build("SCR001/REG002", "SCR001/REG002")
        hits = [i for i in issues_of(_check_caps(lines, b2, b4, b5, b6, b7))]
        assert len(hits) == 1, hits
        assert "SCR001/REG002" in hits[0]["message"]

    def test_bare_parent_claimed_twice_still_fires(self):
        """MUST-STILL-FAIL guard: the pre-existing bare-screen collision is untouched."""
        lines, (b2, b4, b5, b6, b7) = self._build("SCR001", "SCR001")
        hits = [i for i in issues_of(_check_caps(lines, b2, b4, b5, b6, b7))]
        assert len(hits) == 1, hits
        assert "SCR001" in hits[0]["message"]

    def test_slug_and_bare_spelling_of_one_screen_still_collide(self):
        """`_NameSlug` is cosmetic (`code-formats.md`) — `SCR001_List` and `SCR001` are the
        SAME screen. Without `_normalize_scr_claim` they would key separately and this real
        collision would go quiet, which is the way this fix could silently over-reach."""
        lines, (b2, b4, b5, b6, b7) = self._build("SCR001_List", "SCR001")
        hits = [i for i in issues_of(_check_caps(lines, b2, b4, b5, b6, b7))]
        assert len(hits) == 1, hits

    def test_possessive_mention_is_not_a_claim(self):
        """`SCR001's` in a claim cell is PROSE — a reference to a screen another capability
        owns. Reaches: `_is_possessive` suppresses the token, so CAP-02 registers no SCR claim
        and CAP-01's real `SCR001` claim stands alone."""
        lines, (b2, b4, b5, b6, b7) = self._build("SCR001", "reuses SCR001's list view")
        assert not [i for i in _check_caps(lines, b2, b4, b5, b6, b7)
                    if i["rule_id"] == "cap.double_claimed"]

    def test_composite_possessive_mention_is_not_a_claim(self):
        """REGRESSION (reviewer critical, v27.14.3). The possessive guard was first written
        as a trailing `(?!['’]s\\b)` inside `_SCR_CLAIM_RE`, AFTER its optional
        `(?:/REG\\d{3}...)?` group. Backtracking defeated it: against `SCR001/REG002's` the
        engine took the REG group, failed the lookahead, then backtracked to NOT taking that
        optional group and succeeded on bare `SCR001` — a false `cap.double_claimed`, the
        exact defect the guard exists to prevent, just reached through a composite ref.
        The guard is now a POSITIONAL check (`_is_possessive`) evaluated after the match,
        which backtracking cannot route around."""
        lines, (b2, b4, b5, b6, b7) = self._build(
            "SCR001", "reuses SCR001/REG002's list view")
        assert not [i for i in _check_caps(lines, b2, b4, b5, b6, b7)
                    if i["rule_id"] == "cap.double_claimed"]

    def test_slugged_composite_possessive_is_not_a_claim(self):
        """The same backtracking hole, one level nastier: `_\\w+` backtracked off the final
        letter and produced the MANGLED token `SCR001_List/REG002_Pane`, which then
        normalized straight back into a real-looking `SCR001/REG002` claim."""
        lines, (b2, b4, b5, b6, b7) = self._build(
            "SCR001/REG002", "styled like SCR001_List/REG002_Panel's header")
        assert not [i for i in _check_caps(lines, b2, b4, b5, b6, b7)
                    if i["rule_id"] == "cap.double_claimed"]

    def test_quoted_code_is_still_a_claim(self):
        """The guard is `'s`, never a bare apostrophe — a quoted `'SCR001'` is a real claim.
        Pins the false-negative this narrowing was chosen to avoid."""
        lines, (b2, b4, b5, b6, b7) = self._build("'SCR001'", "SCR001")
        hits = issues_of(_check_caps(lines, b2, b4, b5, b6, b7))
        assert len(hits) == 1, hits

    def test_backticked_and_uppercase_possessives_are_not_claims(self):
        """Two shapes the first guard missed. Codes in these cells are routinely backticked,
        so the possessive reads `` `SCR001`'s `` — the apostrophe is not adjacent to the
        match — and an ALL-CAPS cell writes `'S`. Both are prose; neither is a claim."""
        for prose in ("wraps `SCR001`'s list view", "REUSES SCR001'S LIST VIEW"):
            lines, (b2, b4, b5, b6, b7) = self._build("SCR001", prose)
            assert not [i for i in _check_caps(lines, b2, b4, b5, b6, b7)
                        if i["rule_id"] == "cap.double_claimed"], prose

    def test_region_claim_satisfies_a_declared_parent_screen(self):
        """THE TRAP THIS FIX HAD TO AVOID. `_func_code_sets` still declares the bare parent
        (`SCR001`) from a § 6 row, so keying claims by composite ALONE would make that
        declared screen look unclaimed — swapping the removed false `double_claimed` for a
        brand-new false `code_unclaimed`. `_claim_parents` is what prevents it."""
        lines, (b2, b4, b5, b6, b7) = self._build("SCR001/REG002", "")
        assert not [i for i in _check_caps(lines, b2, b4, b5, b6, b7)
                    if i["rule_id"] == "cap.code_unclaimed"
                    and "family=SCR" in i["message"]], "SCR001 declared in § 6 is claimed"


def issues_of(issues):
    """`cap.double_claimed` hits only — keeps the guard assertions above readable."""
    return [i for i in issues if i["rule_id"] == "cap.double_claimed"]


class TestMaximalCount:
    """[SA-2] The load-bearing regression test for this phase. Against the
    pre-restructure code, a header-only § 2 (no data rows) short-circuited on
    `if not data_rows: ... return issues` BEFORE the reverse check ever ran, producing
    exactly 1 finding (`func.capabilities_empty`) regardless of how many codes were
    declared in §§ 4-7 — verified directly against `HEAD`'s `_check_capabilities_section`
    (see the phase 05 completion report for the recorded command + output). The
    restructure computes `declared`/`claims`/`state` unconditionally, so the SAME
    header-only § 2 now reports the MAXIMAL finding count instead."""

    def test_header_only_section2_with_full_4567_emits_maximal_count(self):
        lines, (b2, b4, b5, b6, b7) = _combine(
            _CAP_HEADER,  # header + separator only — zero data rows
            _FR_BODY_2 + "- **FR-103** do thing three\n",  # 3 FR
            _BR_BODY_2,  # 2 BR
            _SCR_BODY_2,  # 2 SCR
            _US_BODY_2,  # 2 US
        )
        # Reaches: rows == [] -> state "absent" (NOT "unfilled") -> the `else` branch
        # (cap.code_unclaimed / cap.double_claimed) still runs, because state != "unfilled".
        # `# Reaches: data_rows empty -> old code returned here; new order computes
        # declared/claims first.`
        issues = _check_caps(lines, b2, b4, b5, b6, b7)
        unclaimed = [i for i in issues if i["rule_id"] == "cap.code_unclaimed"]
        empty = [i for i in issues if i["rule_id"] == "func.capabilities_empty"]
        unfilled = [i for i in issues if i["rule_id"] == "cap.claims_unfilled"]
        double = [i for i in issues if i["rule_id"] == "cap.double_claimed"]
        assert len(issues) == 10, issues
        assert len(unclaimed) == 9, issues  # 3 FR + 2 BR + 2 SCR + 2 US
        assert len(empty) == 1, issues
        assert unfilled == []
        assert double == []


class TestClaimsUnfilled:
    """[FM-4] cap.claims_unfilled (warning): § 2 has >=1 data row and EVERY row's claim
    cells are empty — the structural, post-`cap-map`/pre-fill window. All-or-nothing:
    a partially-filled table is real signal (cap.code_unclaimed keeps firing), never
    muted by a percentage threshold."""

    def test_all_empty_fires_exactly_one_warning_and_mutes_criticals(self):
        lines, (b2, b4, b7) = _combine(
            _CAP_HEADER
            + "| CAP-01 | Sign in |  |  |  |  |  |\n"
            + "| CAP-02 | Register |  |  |  |  |  |\n"
            + "| CAP-03 | Reset |  |  |  |  |  |\n",
            "- **FR-101** first\n",
            "### US001_One — story\n\n**Actor:** A\n**Goal:** B\n**Business value:** C\n",
        )
        # Reaches: 3 data rows, every row's claim cells empty -> `empties` all True ->
        # state "unfilled" -> cap.claims_unfilled fires, cap.code_unclaimed suppressed.
        issues = _check_caps(lines, b2, b4, None, None, b7)
        assert len(issues) == 1, issues
        assert issues[0]["rule_id"] == "cap.claims_unfilled"
        assert issues[0]["severity"] == "warning"

    def test_one_row_populated_of_three_fires_code_unclaimed_not_unfilled(self):
        lines, (b2, b4, b7) = _combine(
            _CAP_HEADER
            + "| CAP-01 | Sign in | Do it | US001 | FR-101 | BR-001 | SCR001 |\n"
            + "| CAP-02 | Register |  |  |  |  |  |\n"
            + "| CAP-03 | Reset |  |  |  |  |  |\n",
            _FR_BODY_2, _US_BODY_2,
        )
        # Reaches: `empties` = [False, True, True] -> mixed -> "partial", never folded
        # into "unfilled" — cap.code_unclaimed keeps firing for the genuinely unclaimed
        # codes (FR-102, US002) that the other two blank rows never picked up.
        issues = _check_caps(lines, b2, b4, None, None, b7)
        assert not any(i["rule_id"] == "cap.claims_unfilled" for i in issues)
        unclaimed = [i for i in issues if i["rule_id"] == "cap.code_unclaimed"]
        assert any("FR-102" in i["message"] for i in unclaimed)
        assert any("US002" in i["message"] for i in unclaimed)

    def test_all_rows_populated_and_exhaustive_is_silent(self):
        lines, (b2, b4, b7) = _combine(
            _CAP_HEADER
            + "| CAP-01 | Sign in | Do it | US001 | FR-101 | BR-001 | SCR001 |\n"
            + "| CAP-02 | Register | Fill form | US002 | FR-102 | BR-002 | SCR002 |\n",
            _FR_BODY_2, _US_BODY_2,
        )
        # Reaches: `empties` all False -> "filled"; every declared FR/US code is claimed
        # exactly once -> silent.
        issues = _check_caps(lines, b2, b4, None, None, b7)
        assert issues == []


class TestStrayHeadingDoesNotMuteNewShape:
    """[SA-3, step 16] A fully v27-shaped, otherwise-exhaustive functional-spec.md that
    ALSO carries a stray, out-of-position "## 2. Open Decisions" heading (e.g. a
    leftover from a botched edit) must still run its cap.* checks — the sentinel's mere
    presence must never mute a genuinely new-shaped file. See
    TestPreSotDegradation.test_stray_functional_capabilities_heading_unmutes_pre_sot for
    the mirror-image fixture (old-shaped + stray NEW heading)."""

    def test_stray_open_decisions_heading_does_not_mute_cap_code_unclaimed(self, tmp_path):
        body = _FULL_NEW_SHAPE_OK.replace(
            "## 8. Scenarios",
            "### US002_Extra — Uncited story\n\n**Actor:** Registered User\n"
            "**Goal:** Do something else\n**Business value:** Extra value\n\n"
            "**Acceptance Criteria:**\n- [ ] Something else happens.\n\n"
            "## 8. Scenarios",
        ) + (
            "\n<!-- fixture defect below, on purpose: a stray, out-of-position pre-SOT "
            "sentinel heading appended after every real section, proving SA-3's "
            "co-condition (presence of BOTH headings must never resolve to pre-SOT) -->\n"
            "## 2. Open Decisions\n\nN/A — this heading is a fixture defect, not a real "
            "decision list.\n"
        )
        lines = body.splitlines()
        h2_names = [h for _, h in _h2_and_headings(lines)[0]]
        assert "## 2. Open Decisions" in h2_names  # sanity: the stray sentinel is real
        assert "## 2. Functional Capabilities" in h2_names
        func_path = _write_tmp(tmp_path, "functional-spec.md", body)
        # Reaches: sentinel in h2_names True but "## 2. Functional Capabilities" also
        # present -> is_pre_sot False -> section-bound checks (incl. this phase's new
        # ones) run for real. US002_Extra is declared in § 7 but claimed by no § 2 row.
        issues = vfs._check_functional_spec(func_path, tmp_path / "absent.md", tmp_path)
        rule_ids = [i["rule_id"] for i in issues]
        assert "func.sections_pre_sot" not in rule_ids
        assert "func.missing_h2" not in rule_ids  # the 13 real headings are untouched
        assert any(
            i["rule_id"] == "cap.code_unclaimed" and "US002" in i["message"]
            for i in issues
        )


class TestPreSotMutesCapChecks:
    """A genuine pre-SOT fixture (sentinel present, no "## 2. Functional Capabilities"
    anywhere) must never surface a cap.*-prefixed issue — `is_pre_sot`'s early return
    fires before `b2` is ever computed, so the reverse checks never run at all."""

    def test_pre_sot_file_emits_zero_cap_issues(self, tmp_path):
        func_path = _write_tmp(
            tmp_path, "functional-spec.md", EVIDENCE_G2.read_text(encoding="utf-8")
        )
        # Reaches: is_pre_sot early return at the top of _check_functional_spec, before
        # b2 is computed.
        issues = vfs._check_functional_spec(func_path, tmp_path / "absent.md", tmp_path)
        assert not any(i["rule_id"].startswith("cap.") for i in issues)


# ===========================================================================
# Section F — phase 06 (capability-map plan): cap.analysis_required /
# cap.review_advised, the count-based review triggers, and the un-rubber-
# stampable `**Single-capability rationale:**` hatch (SC-1). Idiom (b): direct
# calls into `_check_capability_analysis`; every negative test states which
# branch it reaches. TestRepointedBindingsFireAtNewSectionNumbers.test_baseline_is_clean
# above is this section's own control too — it is a single-CAP, 1-US feature
# (well under every band) and stays silent after this phase's changes.
# ===========================================================================

_OLD_CAP_RATIONALE_RE = re.compile(
    r"^\*\*Single-capability rationale:\*\*\s*\S", re.MULTILINE)


def _us_story_blocks(codes: list[str]) -> str:
    """§ 7-shaped US story headings for each given US### code — only the heading
    matters for `_func_code_sets`'s § 7 declared-US extraction; the rest of the
    block is body text `_check_capability_analysis` never reads."""
    return "".join(
        f"### {code}_Story — story for {code}\n\n**Actor:** A\n**Goal:** B\n"
        f"**Business value:** C\n\n" for code in codes
    )


def _cap_section_block(n_rows: int = 1, rationale: str | None = None,
                       unfilled: bool = False) -> str:
    """A § 2 Functional Capabilities block: header + `n_rows` CAP-## rows, plus an
    optional `**Single-capability rationale:**` line appended INSIDE the same
    block (so it lands inside `b2`'s bounds, matching where the real template
    places it). `unfilled=True` leaves every claim cell blank — `N/A` otherwise
    (a real, non-empty answer per `_cap_table_lib._cell_is_empty`, so `claim_state`
    reads "filled"/"partial", never "unfilled", unless explicitly asked for)."""
    cell = "" if unfilled else "N/A"
    rows = "".join(
        f"| CAP-{i:02d} | X | Y | {cell} | {cell} | {cell} | {cell} |\n"
        for i in range(1, n_rows + 1)
    )
    text = _CAP_HEADER + rows
    if rationale is not None:
        text += f"\n{rationale}\n"
    return text


def _bl_codes_text(codes: list[str]) -> str:
    """A twin technical-spec.md-shaped snippet citing each given BL### code.
    `_check_capability_analysis` reads `tech_text` as a whole string (not a
    parsed section), so this only needs to genuinely contain the codes."""
    return "\n".join(f"- {code}_JobName handles part of the nightly batch." for code in codes)


class TestCapabilityAnalysisBaselineIsClean:
    def test_zero_us_zero_bl_one_cap_is_silent(self):
        lines, (b2,) = _combine(_cap_section_block())
        # Reaches: counts["US"] == counts["BL"] == 0 -> both bands "silent".
        issues = vfs._check_capability_analysis(lines, b2, None, "ui", "", Path("f.md"), Path("."))
        assert issues == []


class TestCapabilityAnalysisUsBandEdges:
    """`ui` type: warn 3-4, critical >= 5 (`_CAP_ANALYSIS_BANDS["ui"]`)."""

    def _run(self, n_us: int, n_cap: int = 1, rationale: str | None = None):
        us_codes = [f"US{i:03d}" for i in range(1, n_us + 1)]
        lines, (b2, b7) = _combine(
            _cap_section_block(n_rows=n_cap, rationale=rationale), _us_story_blocks(us_codes),
        )
        return vfs._check_capability_analysis(lines, b2, b7, "ui", "", Path("f.md"), Path("."))

    def test_two_us_is_silent(self):
        # Reaches: counts["US"]=2 -> _cap_band_state(2, 3, 5) == "silent".
        assert self._run(2) == []

    def test_three_us_is_warning(self):
        # Reaches: counts["US"]=3 -> "warning" (3 <= 3 < 5).
        issues = self._run(3)
        assert len(issues) == 1
        assert issues[0]["rule_id"] == "cap.review_advised"
        assert issues[0]["severity"] == "warning"

    def test_four_us_is_warning(self):
        # Reaches: counts["US"]=4 -> still "warning" (4 < 5).
        issues = self._run(4)
        assert len(issues) == 1
        assert issues[0]["rule_id"] == "cap.review_advised"

    def test_five_us_no_rationale_is_critical(self):
        # Reaches: counts["US"]=5 >= crit_floor 5 -> "critical"; no rationale line
        # anywhere in § 2 -> `m` is None -> ok_1 False -> qualifies False -> fires.
        issues = self._run(5)
        assert len(issues) == 1
        assert issues[0]["rule_id"] == "cap.analysis_required"
        assert issues[0]["severity"] == "critical"

    def test_five_us_qualifying_rationale_is_silent(self):
        rationale = (
            "**Single-capability rationale:** US001 and US002 both serve the single "
            "outcome of getting a user fully authenticated end to end for real."
        )
        # Reaches: "critical" band, but ok_1/ok_2 (>=12 words)/ok_3 (2 real declared
        # codes, subset of declared) all True -> qualifies True -> [].
        issues = self._run(5, rationale=rationale)
        assert issues == []

    def test_five_us_with_two_cap_rows_is_silent(self):
        # Reaches: `len(rows) != 1` guard fires before any band is ever computed —
        # the count never forces a split (D-7).
        issues = self._run(5, n_cap=2)
        assert issues == []


class TestCapabilityAnalysisBackgroundBandEdges:
    """`background` type: warn 5-7, critical >= 8 (`_CAP_ANALYSIS_BANDS["background"]`).
    [SC-7] provisional, ~1.6x the `ui` bands on n=8 — see the constant's own comment."""

    def _run(self, n_bl: int, n_cap: int = 1, rationale: str | None = None):
        bl_codes = [f"BL{i:03d}" for i in range(1, n_bl + 1)]
        tech_text = _bl_codes_text(bl_codes)
        for code in bl_codes:
            # Guard against fixtures-that-synthesize-producer-signals: a fixture
            # whose twin text doesn't genuinely carry the codes makes every
            # background test vacuously green — assert it for real.
            assert code in tech_text
        lines, (b2,) = _combine(_cap_section_block(n_rows=n_cap, rationale=rationale))
        return vfs._check_capability_analysis(lines, b2, None, "background", tech_text,
                                              Path("f.md"), Path("."))

    def test_four_bl_is_silent(self):
        assert self._run(4) == []

    def test_five_bl_is_warning(self):
        issues = self._run(5)
        assert len(issues) == 1
        assert issues[0]["rule_id"] == "cap.review_advised"

    def test_seven_bl_is_warning(self):
        issues = self._run(7)
        assert len(issues) == 1
        assert issues[0]["rule_id"] == "cap.review_advised"

    def test_eight_bl_no_rationale_is_critical(self):
        issues = self._run(8)
        assert len(issues) == 1
        assert issues[0]["rule_id"] == "cap.analysis_required"

    def test_eight_bl_qualifying_rationale_is_silent(self):
        rationale = (
            "**Single-capability rationale:** BL001 and BL002 together own the entire "
            "nightly batch reconciliation pipeline end to end for this feature."
        )
        issues = self._run(8, rationale=rationale)
        assert issues == []


class TestCapabilityAnalysisMixedCrossBand:
    """[SC-7 mixed gap — CLOSED] `mixed` evaluates BOTH bands and takes the
    STRICTER outcome. Both directions used to escape the original US-only rule."""

    def test_low_us_high_bl_is_critical(self):
        us_codes = [f"US{i:03d}" for i in range(1, 3)]  # 2 US, below warn floor 3
        bl_codes = [f"BL{i:03d}" for i in range(1, 10)]  # 9 BL, above crit floor 8
        tech_text = _bl_codes_text(bl_codes)
        lines, (b2, b7) = _combine(_cap_section_block(), _us_story_blocks(us_codes))
        # Reaches: US state "silent" (2 < 3), BL state "critical" (9 >= 8) -> the
        # stricter-of-both comparison picks BL -> fires. Under the original
        # US-only rule this would have stayed silent — the hole SC-7 closes.
        issues = vfs._check_capability_analysis(lines, b2, b7, "mixed", tech_text,
                                                 Path("f.md"), Path("."))
        assert len(issues) == 1
        assert issues[0]["rule_id"] == "cap.analysis_required"
        assert "BL" in issues[0]["message"]

    def test_high_us_low_bl_is_critical(self):
        us_codes = [f"US{i:03d}" for i in range(1, 7)]  # 6 US, above crit floor 5
        bl_codes = [f"BL{i:03d}" for i in range(1, 2)]  # 1 BL, below warn floor 5
        tech_text = _bl_codes_text(bl_codes)
        lines, (b2, b7) = _combine(_cap_section_block(), _us_story_blocks(us_codes))
        # Reaches: US state "critical" (6 >= 5), BL state "silent" (1 < 5) ->
        # picks US -> fires.
        issues = vfs._check_capability_analysis(lines, b2, b7, "mixed", tech_text,
                                                 Path("f.md"), Path("."))
        assert len(issues) == 1
        assert issues[0]["rule_id"] == "cap.analysis_required"
        assert "US" in issues[0]["message"]


class TestCapabilityAnalysisRationaleConditions:
    """[SC-1] The three hatch conditions each fail INDEPENDENTLY — a single
    fixture failing all three would prove only one branch, per the plan's own
    warning against that shortcut."""

    def _run(self, rationale: str, n_us: int = 5):
        us_codes = [f"US{i:03d}" for i in range(1, n_us + 1)]
        lines, (b2, b7) = _combine(
            _cap_section_block(rationale=rationale), _us_story_blocks(us_codes),
        )
        return vfs._check_capability_analysis(lines, b2, b7, "ui", "", Path("f.md"), Path("."))

    def test_empty_label_wrongly_passes_old_regex_but_not_new(self):
        """[SA-1] The red team's exact reproduction: an empty label with a later
        non-whitespace character elsewhere in § 2 (in the real hole, a pipe from
        an unrelated following table row). This test uses plain trailing prose
        instead of a literal `|`-led line: a line starting with `|` would ALSO be
        picked up by `_cap_table_lib.data_rows` as a SECOND § 2 data row (its own,
        orthogonal, already-correct behavior), tripping the `n_cap != 1` guard
        before the rationale regex is ever reached — which would prove nothing
        about SA-1. Plain prose isolates the regex hazard on its own.
        Recorded FIRST against the OLD `\\s*\\S` pattern (which wrongly matches,
        because `\\s*` crosses the blank line to reach that later text) as proof
        the hole was real, then asserted against the actual check, which must
        NOT be silenced."""
        section2 = _cap_section_block() + (
            "\n**Single-capability rationale:**\n\nSee the notes column above.\n"
        )
        old_match = _OLD_CAP_RATIONALE_RE.search(section2)
        assert old_match is not None, "the OLD regex must wrongly match — this IS the SA-1 hole"
        us_codes = [f"US{i:03d}" for i in range(1, 6)]
        lines, (b2, b7) = _combine(section2, _us_story_blocks(us_codes))
        # Reaches: the NEW same-line-anchored regex finds no match at all (the
        # label's own line has nothing after it, and `[^\n]*$` never crosses the
        # blank line to the later prose) -> ok_1 False -> critical still fires.
        issues = vfs._check_capability_analysis(lines, b2, b7, "ui", "", Path("f.md"), Path("."))
        assert len(issues) == 1
        assert issues[0]["rule_id"] == "cap.analysis_required"
        assert "no same-line" in issues[0]["message"]

    def test_short_body_under_word_floor_is_critical(self):
        # Reaches: ok_1 True, ok_3 True (2 real distinct declared codes), ok_2
        # False (4 words < 12) -> qualifies False.
        rationale = "**Single-capability rationale:** US001 and US002 group."
        issues = self._run(rationale)
        assert len(issues) == 1
        assert issues[0]["rule_id"] == "cap.analysis_required"
        assert "needs >= 12" in issues[0]["message"]

    def test_single_cited_code_is_critical(self):
        rationale = (
            "**Single-capability rationale:** US001 alone explains everything this "
            "single capability groups together for the returning user, end to end."
        )
        # Reaches: ok_2 True (>=12 words); cited={US001} -> len(cited) < 2 -> ok_3 False.
        issues = self._run(rationale)
        assert len(issues) == 1
        assert issues[0]["rule_id"] == "cap.analysis_required"
        assert "cites 1 distinct code" in issues[0]["message"]

    def test_fabricated_codes_are_named_in_message(self):
        rationale = (
            "**Single-capability rationale:** US901 and US902 together explain why "
            "this single capability groups every story here, end to end for good."
        )
        # Reaches: cited={US901, US902}, neither in the declared set (US001-US005)
        # -> len(cited) >= 2 but not a subset -> ok_3 False, message names both.
        issues = self._run(rationale)
        assert len(issues) == 1
        msg = issues[0]["message"]
        assert "US901" in msg and "US902" in msg

    def test_positive_qualifying_rationale_is_silent(self):
        rationale = (
            "**Single-capability rationale:** US001 and US002 both serve the single "
            "outcome of getting a user fully authenticated end to end for real."
        )
        # Reaches: ok_1/ok_2/ok_3 all True -> qualifies True -> [].
        assert self._run(rationale) == []


class TestCapabilityAnalysisFillStateGate:
    """[FM-4] Reuses `_cap_table_lib.claim_state` verbatim — a § 2 whose claim
    cells are all empty is a post-`cap-map`/pre-fill window, not a real verdict."""

    def test_all_claim_cells_empty_mutes_the_phase(self):
        us_codes = [f"US{i:03d}" for i in range(1, 7)]  # 6 US declared, well over band
        lines, (b2, b7) = _combine(
            _cap_section_block(n_rows=1, unfilled=True), _us_story_blocks(us_codes),
        )
        # Reaches: `_cap_table_lib.claim_state(...) == "unfilled"` -> early return,
        # before the `len(rows) != 1` guard or any band logic ever runs.
        issues = vfs._check_capability_analysis(lines, b2, b7, "ui", "", Path("f.md"), Path("."))
        assert issues == []


def _extra_us_stories(codes_and_labels: list[tuple[str, str]]) -> str:
    """Full § 7-shaped US story blocks (heading + Actor/Goal/Business value +
    Acceptance Criteria) for splicing into `_FULL_NEW_SHAPE_OK`-derived e2e
    fixtures — richer than `_us_story_blocks` because these run through the
    WHOLE `_check_functional_spec` pipeline, where `func.user_story_shape` would
    otherwise fire as incidental noise."""
    return "".join(
        f"\n### {code}_Extra — {label}\n\n**Actor:** Registered User\n"
        f"**Goal:** {label}\n**Business value:** Reach account features.\n\n"
        "**Acceptance Criteria:**\n- [ ] Something happens.\n"
        for code, label in codes_and_labels
    )


class TestCapabilityAnalysisFuncTypeDefault:
    def test_missing_type_field_defaults_to_ui_band(self, tmp_path):
        extra = _extra_us_stories([(f"US{i:03d}", f"Extra story {i}") for i in range(2, 6)])
        body = _FULL_NEW_SHAPE_OK.replace("**Type**: ui\n", "").replace(
            "## 8. Scenarios", extra + "\n## 8. Scenarios"
        )
        func_path = _write_tmp(tmp_path, "functional-spec.md", body)
        # Reaches: `_func_type` finds no `**Type**:` field in the first 15 lines
        # -> defaults to "ui" (the stricter band) -> 5 US declared, #CAP == 1, no
        # rationale -> critical.
        issues = vfs._check_functional_spec(func_path, tmp_path / "absent.md", tmp_path)
        assert any(i["rule_id"] == "cap.analysis_required" for i in issues)


class TestCapabilityAnalysisPreSotAndStrayInheritance:
    def test_pre_sot_file_emits_neither_new_rule(self, tmp_path):
        func_path = _write_tmp(
            tmp_path, "functional-spec.md", EVIDENCE_G2.read_text(encoding="utf-8")
        )
        # Reaches: is_pre_sot early return in `_check_functional_spec`, before b2
        # is ever computed — structurally the same mute phase 05's rules get, not
        # re-derived for this phase's two new rule ids.
        issues = vfs._check_functional_spec(func_path, tmp_path / "absent.md", tmp_path)
        rule_ids = {i["rule_id"] for i in issues}
        assert "cap.analysis_required" not in rule_ids
        assert "cap.review_advised" not in rule_ids

    def test_stray_open_decisions_heading_does_not_mute_analysis_required(self, tmp_path):
        """[SA-3 inheritance] A genuinely v27-shaped file that ALSO carries a
        stray, out-of-position "## 2. Open Decisions" heading must still run this
        phase's checks — the sentinel's mere presence must never mute a
        genuinely new-shaped file (phase 05 fixed this co-condition; this proves
        phase 06 inherits it rather than assuming it), mirroring
        TestStrayHeadingDoesNotMuteNewShape above."""
        extra = _extra_us_stories([(f"US{i:03d}", f"Extra story {i}") for i in range(2, 6)])
        body = _FULL_NEW_SHAPE_OK.replace(
            "## 8. Scenarios", extra + "\n## 8. Scenarios"
        ) + (
            "\n<!-- stray, out-of-position pre-SOT sentinel — SA-3 co-condition proof -->\n"
            "## 2. Open Decisions\n\nN/A — fixture defect, not a real decision list.\n"
        )
        func_path = _write_tmp(tmp_path, "functional-spec.md", body)
        issues = vfs._check_functional_spec(func_path, tmp_path / "absent.md", tmp_path)
        rule_ids = [i["rule_id"] for i in issues]
        assert "func.sections_pre_sot" not in rule_ids
        assert "cap.analysis_required" in rule_ids


class TestCapabilityAnalysisSummaryOutConsumer:
    """[SC-3] The warning DOES reach a consumer — verified with a real assertion,
    not a plan-time belief. `--summary-out` merges every issue through
    `merge_validator_result` (`_summary_lib.py`) into `fs-validation-summary.json`;
    `buildFsValidatorPreamble` (`references/pipeline-feature-specs.md`) then prints
    EVERY issue, severity-agnostic, into the FS.5 reviewer's prompt. Two honest
    boundaries, also recorded in the checklist registry rows (not just here):
    (a) this path exists only in the AUTHORING pipeline, and only when
    `--summary-out` is passed — a corpus-time run against `docs/features/` has NO
    consumer at all; (b) `buildFsValidatorPreamble` renders exactly
    severity/rule_id/location/message — anything not in the message is invisible."""

    def test_warning_reaches_summary_json_and_exit_code_stays_zero(self, tmp_path):
        feat_dir = tmp_path / "docs" / "features" / "F900_Sot"
        feat_dir.mkdir(parents=True)
        # NOTE: `FeatureSpec.mapping_table_missing` (an UNRELATED, pre-existing
        # technical-spec.md check) requires a "## 2." mapping row for every code
        # the twin functional-spec.md declares — every US/BR/FR code added below
        # needs a matching row here too, or that critical would fire and defeat
        # this test's whole point (isolating cap.review_advised's own exit code).
        (feat_dir / "technical-spec.md").write_text(
            _MINIMAL_TECH_SPEC.replace(
                "**Business Rules**\n\nNone.\n",
                "**Business Rules**\n\n"
                "### Passwords are hashed before storage (BR-001)\n"
                "**Linked FR:** FR-001\n**Source:** `app/models/user.rb:10-20`\n"
                "**Applies to:** User\n",
            ).replace(
                "| Code | Name | Where it is implemented | Technical notes | Source |\n"
                "|------|------|--------------------------|------------------|--------|\n",
                "| Code | Name | Where it is implemented | Technical notes | Source |\n"
                "|------|------|--------------------------|------------------|--------|\n"
                "| FR-001 | Passwords are hashed before storage | `User` model callback | "
                "| `app/models/user.rb:1-5` |\n"
                "| BR-001 | Passwords are hashed before storage | `User` model callback | "
                "| `app/models/user.rb:1-5` |\n"
                "| US001 | User logs in | `SessionsController#create` | "
                "| `app/controllers/sessions_controller.rb:1-20` |\n"
                "| US002 | User logs in again | `SessionsController#create` | "
                "| `app/controllers/sessions_controller.rb:1-20` |\n"
                "| US003 | User logs in a third time | `SessionsController#create` | "
                "| `app/controllers/sessions_controller.rb:1-20` |\n",
            ),
            encoding="utf-8",
        )
        extra = _extra_us_stories([
            ("US002", "User logs in again"), ("US003", "User logs in a third time"),
        ])
        body = _FULL_NEW_SHAPE_OK.replace(
            "| CAP-01 | Sign in | Authenticate with email and password | US001 | FR-001 | "
            "BR-001 | SCR001_Login |",
            "| CAP-01 | Sign in | Authenticate with email and password | US001, US002, "
            "US003 | FR-001 | BR-001 | SCR001_Login |",
        ).replace("## 8. Scenarios", extra + "\n## 8. Scenarios")
        (feat_dir / "functional-spec.md").write_text(body, encoding="utf-8")
        summary_path = tmp_path / "fs-validation-summary.json"
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--spec", str(feat_dir), "--project-root", str(tmp_path),
             "--summary-out", str(summary_path)],
            capture_output=True, text=True, timeout=30,
        )
        assert result.stdout.strip(), f"empty stdout — stderr was: {result.stderr}"
        data = json.loads(result.stdout)
        run_issues = _issues(data)
        # 3 declared US, #CAP == 1 -> the "ui" warning band (3-4) -> cap.review_advised.
        review = [i for i in run_issues if i["rule_id"] == "cap.review_advised"]
        assert len(review) == 1, run_issues
        assert review[0]["severity"] == "warning"
        assert not any(i["rule_id"] == "cap.analysis_required" for i in run_issues)
        # [SC-3] cap.review_advised does not change the exit code.
        assert result.returncode == 0, run_issues

        assert summary_path.is_file()
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        fcode_issues = summary["validators"]["specs"]["F900_Sot"]["issues"]
        hits = [i for i in fcode_issues if i["rule_id"] == "cap.review_advised"]
        assert len(hits) == 1, fcode_issues
        assert hits[0]["severity"] == "warning"
        assert hits[0]["message"]


class TestTemplateCapRationaleExamplePasses:
    """The functional-spec-template.md § 2 HTML comment documents SC-1's hatch
    with a commented EXAMPLE rationale line. An example that would itself FAIL
    the check is the code-formats.md self-contradiction defect phase 02 spent
    its budget removing — rebuilt in a new file if this example ever drifts
    out of sync with the three live conditions."""

    def test_example_rationale_line_qualifies(self):
        text = TEMPLATE.read_text(encoding="utf-8")
        m = vfs._FUNC_CAP_RATIONALE_RE.search(text)
        assert m is not None, "template must carry a real, same-line-anchored example"
        body = m.group("body")
        cited = set(vfs._FAMILY_CODE_RE["US"].findall(body))
        assert len(cited) >= 2, "example must cite >= 2 distinct US codes"
        # Reaches: feeding the example's OWN cited codes as the declared set proves
        # the example would qualify in a real document that actually declares them.
        qualifies, reasons = vfs._cap_rationale_verdict(text, ["US"], cited)
        assert qualifies, reasons


# ===========================================================================
# Section G — phase 08 (capability-map plan): cap.promote_candidate, the
# Tier-1-only promote-eligibility advisory. Idiom (b): direct calls into
# `_check_promote_candidates`; every negative test states which branch/condition
# it reaches. `#CAP` here means the total § 2 data-row count
# (`_cap_table_lib.data_rows`) — the SAME denominator `_check_capability_analysis`
# uses for `#CAP == 1` — never "capabilities that happen to have >=1 claim".
# ===========================================================================

def _promote_cap_table(specs: list[tuple[str, str, int, int, int]]) -> str:
    """A § 2 table for promote-candidate tests. `specs` is a list of
    `(cap_id, name, n_us, n_fr, n_scr)`; each row gets that many DISTINCT
    US###/FR-###/SCR### codes, numbered in a private, globally-increasing block
    per family so no code is ever claimed by two rows in the same fixture (a
    collision would distort the per-CAP counts this test is trying to isolate —
    real § 2 exhaustiveness, phase 05, guarantees this in production; a unit
    fixture has to guarantee it by construction instead)."""
    us_n = fr_n = scr_n = 1
    rows: list[str] = []
    for cap_id, name, n_us, n_fr, n_scr in specs:
        us_codes = [f"US{i:03d}" for i in range(us_n, us_n + n_us)]
        us_n += n_us
        fr_codes = [f"FR-{i:03d}" for i in range(fr_n, fr_n + n_fr)]
        fr_n += n_fr
        scr_codes = [f"SCR{i:03d}_S" for i in range(scr_n, scr_n + n_scr)]
        scr_n += n_scr
        us_cell = ", ".join(us_codes) if us_codes else "N/A"
        fr_cell = ", ".join(fr_codes) if fr_codes else "N/A"
        scr_cell = ", ".join(scr_codes) if scr_codes else "N/A"
        rows.append(f"| {cap_id} | {name} | does things | {us_cell} | {fr_cell} | N/A | {scr_cell} |\n")
    return _CAP_HEADER + "".join(rows)


def _run_promote(specs: list[tuple[str, str, int, int, int]]) -> list[dict]:
    lines, (b2,) = _combine(_promote_cap_table(specs))
    return vfs._check_promote_candidates(lines, b2, Path("f.md"), Path("."))


class TestPromoteCandidateEligible:
    def test_eligible_row_in_two_cap_feature_fires(self):
        # Reaches: len(raw) 2 >= 2, n_us 4 >= 3, n_fr 6 >= 3, n_scr 2 >= 1.
        issues = _run_promote([
            ("CAP-01", "Payout scheduling", 4, 6, 2),
            ("CAP-02", "Sign in", 1, 1, 0),
        ])
        promote = [i for i in issues if i["rule_id"] == "cap.promote_candidate"]
        assert len(promote) == 1, issues
        assert promote[0]["severity"] == "warning"
        msg = promote[0]["message"]
        assert "CAP-01" in msg
        assert "Payout scheduling" in msg
        assert "4" in msg and "6" in msg and "2" in msg
        assert "human decision" in msg
        assert "no automated path" in msg

    def test_does_not_change_exit_code_shape(self):
        """cap.promote_candidate is a warning — never critical — so it alone must
        never be mistaken for a blocking finding. This mirrors the pattern of
        cap.review_advised's own exit-code assertion (TestCapabilityAnalysisSummaryOutConsumer)
        without re-running the full subprocess/summary-out path for a second rule id."""
        issues = _run_promote([
            ("CAP-01", "Payout scheduling", 4, 6, 2),
            ("CAP-02", "Sign in", 1, 1, 0),
        ])
        assert all(i["severity"] != "critical" for i in issues
                   if i["rule_id"] == "cap.promote_candidate")


class TestPromoteCandidateCapCountSuppression:
    def test_single_cap_row_is_silent_even_if_thresholds_met(self):
        # Reaches: len(raw) 1 < 2 -> early return, before any per-CAP counting.
        issues = _run_promote([("CAP-01", "Payout scheduling", 4, 6, 2)])
        assert issues == []


class TestPromoteCandidateBoundaries:
    """[Step 5] Each of the three per-family floors suppresses ON ITS OWN — a
    single fixture failing all three would prove only one branch. Every fixture
    here holds #CAP == 2 and the OTHER two families at their qualifying floor,
    varying only the one family under test."""

    def test_two_us_suppresses(self):
        # Reaches: n_us 2 < 3 (fr=3 >=3, scr=1 >=1 both hold) -> condition fails.
        issues = _run_promote([
            ("CAP-01", "Payout scheduling", 2, 3, 1),
            ("CAP-02", "Sign in", 1, 1, 0),
        ])
        assert not any(i["rule_id"] == "cap.promote_candidate" for i in issues)

    def test_two_fr_suppresses(self):
        # Reaches: n_fr 2 < 3 (us=3 >=3, scr=1 >=1 both hold) -> condition fails.
        issues = _run_promote([
            ("CAP-01", "Payout scheduling", 3, 2, 1),
            ("CAP-02", "Sign in", 1, 1, 0),
        ])
        assert not any(i["rule_id"] == "cap.promote_candidate" for i in issues)

    def test_zero_scr_suppresses(self):
        # Reaches: n_scr 0 < 1 (us=3 >=3, fr=3 >=3 both hold) -> condition fails.
        issues = _run_promote([
            ("CAP-01", "Payout scheduling", 3, 3, 0),
            ("CAP-02", "Sign in", 1, 1, 0),
        ])
        assert not any(i["rule_id"] == "cap.promote_candidate" for i in issues)


class TestPromoteCandidateFillStateGate:
    """[FM-4] Reuses `_cap_table_lib.claim_state` verbatim — a § 2 whose claim
    cells are all empty is a post-`cap-map`/pre-fill window, not a real verdict."""

    def test_all_claim_cells_empty_mutes_the_check(self):
        # Reaches: `_cap_table_lib.claim_state(...) == "unfilled"` -> early return,
        # before `len(raw) < 2` or any per-CAP counting ever runs.
        lines, (b2,) = _combine(_cap_section_block(n_rows=2, unfilled=True))
        issues = vfs._check_promote_candidates(lines, b2, Path("f.md"), Path("."))
        assert issues == []


class TestPromoteCandidatePreSotMute:
    def test_pre_sot_file_emits_no_promote_candidate(self, tmp_path):
        func_path = _write_tmp(
            tmp_path, "functional-spec.md", EVIDENCE_G2.read_text(encoding="utf-8")
        )
        # Reaches: is_pre_sot early return in `_check_functional_spec`, before b2
        # is ever computed — the same structural mute phases 05/06 inherit.
        issues = vfs._check_functional_spec(func_path, tmp_path / "absent.md", tmp_path)
        assert "cap.promote_candidate" not in [i["rule_id"] for i in issues]


class TestPromoteCandidateStrayHeadingDoesNotMute:
    def test_stray_open_decisions_heading_does_not_mute_promote_candidate(self, tmp_path):
        """[SA-3 inheritance] A genuinely v27-shaped file that ALSO carries a
        stray, out-of-position "## 2. Open Decisions" heading must still run this
        phase's check — the sentinel's mere presence must never mute a genuinely
        new-shaped file (phase 05 fixed this co-condition; this proves phase 08
        inherits it rather than assuming it), mirroring
        TestCapabilityAnalysisPreSotAndStrayInheritance above. The fix lives
        upstream (is_pre_sot's own co-condition) — this test is not optional just
        because the fix is someone else's."""
        body = _FULL_NEW_SHAPE_OK.replace(
            "| CAP-01 | Sign in | Authenticate with email and password | US001 | FR-001 | "
            "BR-001 | SCR001_Login |",
            "| CAP-01 | Sign in | Authenticate with email and password | "
            "US001, US002, US003, US004 | FR-001, FR-002, FR-003 | BR-001 | "
            "SCR001_Login, SCR002_Other |\n"
            "| CAP-02 | Manage profile | Edit profile details | US010 | FR-010 | "
            "BR-010 | SCR010_Profile |",
        ) + (
            "\n<!-- stray, out-of-position pre-SOT sentinel — SA-3 co-condition proof -->\n"
            "## 2. Open Decisions\n\nN/A — fixture defect, not a real decision list.\n"
        )
        func_path = _write_tmp(tmp_path, "functional-spec.md", body)
        issues = vfs._check_functional_spec(func_path, tmp_path / "absent.md", tmp_path)
        rule_ids = [i["rule_id"] for i in issues]
        assert "func.sections_pre_sot" not in rule_ids
        assert "cap.promote_candidate" in rule_ids
