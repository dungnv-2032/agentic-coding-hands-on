"""Phase 11 (B4e) — the four residual precision criticals.

P01 classified `FeatureSpec.block_source_missing`, `FeatureSpec.source_refs_empty`,
`func.code_unsurfaced`, and `func.secret_shape` as pre-existing corpus content gaps
out of migration scope. Re-measurement against the real sharetribe corpus showed
that classification was wrong on all four counts — in every case the content
EXISTS and the failure is a precision bug in the validator (classes 1/3/4) or in
composition (class 2). See phase-11-residual-precision-criticals.md for the full
real-corpus evidence this module's fixtures are drawn from verbatim.

Every relaxation below carries a paired NEGATIVE test proving the underlying rule
still fires on a genuine defect — a relaxation that cannot fail anything is a hole,
not a fix.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
SCRIPT_FEATURE_SPEC = SCRIPTS_DIR / "validate_feature_spec.py"


def _run_script(args: list[str]) -> tuple[int, str, str]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT_FEATURE_SPEC)] + args,
        capture_output=True, text=True, timeout=30,
    )
    return result.returncode, result.stdout, result.stderr


def _rule_ids(spec: Path, root: Path) -> list[str]:
    _, out, err = _run_script(["--spec", str(spec), "--project-root", str(root)])
    data = json.loads(out.strip())
    return [i["rule_id"] for entry in data["specs"].values() for i in entry["issues"]]


def _messages_for(spec: Path, root: Path, rule_id: str) -> list[str]:
    _, out, _ = _run_script(["--spec", str(spec), "--project-root", str(root)])
    data = json.loads(out.strip())
    return [
        i["message"]
        for entry in data["specs"].values()
        for i in entry["issues"]
        if i["rule_id"] == rule_id
    ]


# ===========================================================================
# Class 1 — FeatureSpec.block_source_missing: widened **Source:** recognizer
# + a `**kind:** ui` State Machine exemption. Real strings verbatim from
# F002_OAuthLogin, F011_ListingCreate, F026_StripeConnect, F054_DataExportJobs,
# F025_PaymentSettings, F065_AdminSearchSettings, F018_TransactionInitiate.
# ===========================================================================

# v27.x (P09, human-readable SOT retaxonomy): _CCL_TAIL/_TAIL were the fixed
# "everything after Business Rules/State Machines" tail of the old 9-section CCL
# shape — always the SAME literal text at every call site (never parameterized).
# The 5-bucket shape splits that tail across three different H2s (## 3./## 4./
# ## 5.), so _write_tech_spec below places each piece directly rather than
# concatenating one shared blob; _CCL_TAIL/_TAIL keep only the two pieces still
# referenced standalone elsewhere in this file.
_CCL_TAIL = """\
**Decision Logic**

N/A — no user-facing decision logic beyond DISC-### Polymorphic Behavior.
"""

_TAIL = """\

## 5. Verification & Technical Notes

### 5.1 Technical Verification
None.

### 5.2 Assumptions
None.

### 5.3 Unresolved Questions
None.

### 5.4 Source References
None.

### 5.5 Artifact References
None.
"""


def _write_tech_spec(tmp_path: Path, ccl_body: str) -> tuple[Path, Path]:
    """Write docs/features/F900_P11/technical-spec.md (v27.x — 5-bucket
    retaxonomy) and return (spec, project_root).

    `ccl_body` keeps its historical shape unchanged — every `_ccl()` helper in
    this file still emits a `'### Business Rules\\n...'` block immediately
    followed by a `'### State Machines\\n...'` block, exactly as it did for the
    old `## Cross-Cutting Logic` shape. This function is the ONLY thing that
    changed: it splits `ccl_body` on the `'### State Machines'` marker and
    places the two halves in their new, SEPARATE homes — Business Rules under
    `## 4.`'s `### 4.1` bucket (`**Business Rules**`), State Machines under
    `## 3.3 State Management` — so every existing `_ccl()`-built string below
    keeps exercising the exact same BR-001/SM-001 block content it always did.
    """
    marker = "### State Machines\n"
    br_part, _, sm_part = ccl_body.partition(marker)
    br_part = br_part.replace("### Business Rules\n", "", 1).strip("\n") or "None."
    sm_part = sm_part.strip("\n") or "None."
    feat_dir = tmp_path / "artifacts" / "features" / "F900_P11"
    feat_dir.mkdir(parents=True)
    spec = feat_dir / "technical-spec.md"
    spec.write_text(
        "# F900_P11 — Precision Criticals\n\n"
        "## 1. Technical Overview\nOverview text.\n\n"
        "## 2. Functional → Technical Mapping\n\n"
        "| Code | Name | Where it is implemented | Technical notes | Source |\n"
        "|------|------|--------------------------|------------------|--------|\n\n"
        "## 3. System Design\n\n"
        "### 3.1 Components\nNone.\n\n"
        "### 3.2 Data Model\n\n"
        "#### Key Entities\nNone.\n\n"
        "#### Polymorphic Behavior\nN/A — no discriminator fields in Key Entities.\n\n"
        "### 3.3 State Management\n\n"
        + sm_part + "\n\n"
        + "### 3.4 API & Endpoints\nNone.\n\n"
        "### 3.5 Algorithms & Processing Logic\nNone.\n\n"
        "### 3.6 Integrations\nNone.\n\n"
        "### 3.7 Configuration\nNone.\n\n"
        "**Client behavior:** see behavior-logic.md\n\n"
        "## 4. Technical Behavior by Capability\n\n"
        "### 4.1 Precision Criticals\n\n"
        "**Business Rules**\n\n"
        + br_part + "\n\n"
        + _CCL_TAIL
        + _TAIL,
        encoding="utf-8",
    )
    return spec, tmp_path


class TestBlockSourceMissingWidenedShapes:
    """Each real shape must satisfy the Source-evidence gate — no
    FeatureSpec.block_source_missing for its own BR/SM code."""

    def _ccl(self, source_line: str, sm_kind: str | None = None) -> str:
        if sm_kind is not None:
            return (
                "### Business Rules\nNone.\n\n"
                "### State Machines\n\n"
                "### Checkout form submission status (SM-001)\n"
                f"**kind:** {sm_kind}\n**Linked FR:** FR-001\n"
                + (f"{source_line}\n" if source_line else "")
                + "\n```mermaid\nstateDiagram-v2\n    [*] --> idle\n    idle --> done\n```\n\n"
            )
        return (
            "### Business Rules\n\n"
            "### A rule under test (BR-001)\n"
            f"**Linked FR:** FR-001\n{source_line}\n**Applies to:** Everything\n\n"
            "### State Machines\nNone.\n\n"
        )

    def test_multi_path_first_lacks_line_second_has_it(self, tmp_path):
        spec, root = _write_tech_spec(tmp_path, self._ccl(
            "**Source:** `config/initializers/` (not read — implied by omniauth "
            "gem setup), `app/services/persons/omniauth_service.rb:229-270`"
        ))
        assert "FeatureSpec.block_source_missing" not in _rule_ids(spec, root)

    def test_bare_path_no_line_numbers_with_annotation(self, tmp_path):
        spec, root = _write_tech_spec(tmp_path, self._ccl(
            "**Source:** `app/services/listing_form_view_utils.rb` "
            "(exact lines unconfirmed — file not read)"
        ))
        assert "FeatureSpec.block_source_missing" not in _rule_ids(spec, root)

    def test_directory_path_no_line_numbers(self, tmp_path):
        spec, root = _write_tech_spec(tmp_path, self._ccl(
            "**Source:** `app/services/stripe_service/` "
            "(via `StripeService::API::API.accounts`)"
        ))
        assert "FeatureSpec.block_source_missing" not in _rule_ids(spec, root)

    def test_non_path_permission_id_citation(self, tmp_path):
        spec, root = _write_tech_spec(tmp_path, self._ccl(
            "**Source:** PERM029_ManagePaymentSettings (EnsureCanAccessPerson)"
        ))
        assert "FeatureSpec.block_source_missing" not in _rule_ids(spec, root)

    def test_doc_path_with_section_symbol(self, tmp_path):
        spec, root = _write_tech_spec(tmp_path, self._ccl(
            "**Source:** `plans/260604-0713-rebuild-spec/artifacts/"
            "permissions-matrix.md` § PERM037"
        ))
        assert "FeatureSpec.block_source_missing" not in _rule_ids(spec, root)

    def test_kind_ui_state_machine_exempt_from_source(self, tmp_path):
        spec, root = _write_tech_spec(tmp_path, self._ccl("", sm_kind="ui"))
        assert "FeatureSpec.block_source_missing" not in _rule_ids(spec, root)


class TestBlockSourceMissingStillFires:
    """Negative tests — the widening must not have hollowed the rule out."""

    def _ccl(self, source_line: str, sm_kind: str | None = None) -> str:
        if sm_kind is not None:
            return (
                "### Business Rules\nNone.\n\n"
                "### State Machines\n\n"
                "### Entity lifecycle under test (SM-001)\n"
                f"**kind:** {sm_kind}\n**Linked FR:** FR-001\n**States:** A, B\n"
                + (f"{source_line}\n" if source_line else "")
                + "\n```mermaid\nstateDiagram-v2\n    [*] --> A\n    A --> B\n```\n\n"
            )
        return (
            "### Business Rules\n\n"
            "### A rule under test (BR-001)\n"
            f"**Linked FR:** FR-001\n{source_line}\n**Applies to:** Everything\n\n"
            "### State Machines\nNone.\n\n"
        )

    def test_contentless_source_still_fires(self, tmp_path):
        """The literal required negative test: nothing after **Source:**."""
        spec, root = _write_tech_spec(tmp_path, self._ccl("**Source:**"))
        assert "FeatureSpec.block_source_missing" in _rule_ids(spec, root)

    def test_na_placeholder_source_still_fires(self, tmp_path):
        spec, root = _write_tech_spec(tmp_path, self._ccl("**Source:** N/A"))
        assert "FeatureSpec.block_source_missing" in _rule_ids(spec, root)

    def test_kind_entity_state_machine_missing_source_still_fires(self, tmp_path):
        """The kind:ui exemption must NOT leak to kind:entity (persisted,
        DB-backed) State Machines — those still require a real Source."""
        spec, root = _write_tech_spec(tmp_path, self._ccl("", sm_kind="entity"))
        assert "FeatureSpec.block_source_missing" in _rule_ids(spec, root)

    def test_no_source_line_at_all_still_fires(self, tmp_path):
        """No **Source:** line at all (not even a blank one) — `self._ccl("")`
        already produces exactly that shape: '**Linked FR:** FR-001\\n\\n**Applies
        to:** ...' with nothing where a Source line would sit."""
        spec, root = _write_tech_spec(tmp_path, self._ccl(""))
        assert "FeatureSpec.block_source_missing" in _rule_ids(spec, root)


# ===========================================================================
# REWORK (adversarial review finding 3, MEDIUM) — the widened bare-filename
# shape used to accept ANY prose sentence ending in a `word.ext`-shaped
# token. It is now anchored (must BE the citation, not embedded in a
# sentence) and requires a hyphen/underscore stem (a real repo filename
# shape). The real corpus shape `feature-list.md (PERM051_AdminExportData)`
# must keep passing.
# ===========================================================================

class TestBlockSourceMissingBareFilenameTightened:
    def _ccl(self, source_line: str) -> str:
        return (
            "### Business Rules\n\n"
            "### A rule under test (BR-001)\n"
            f"**Linked FR:** FR-001\n{source_line}\n**Applies to:** Everything\n\n"
            "### State Machines\nNone.\n\n"
        )

    def test_prose_sentence_ending_in_word_dot_ext_still_fires(self, tmp_path):
        """`This is fine.txt` is a full prose sentence, not a citation — the
        bare-filename shape must not accept a token merely embedded at the
        end of it."""
        spec, root = _write_tech_spec(tmp_path, self._ccl("**Source:** This is fine.txt"))
        assert "FeatureSpec.block_source_missing" in _rule_ids(spec, root)

    def test_short_common_word_with_extension_still_fires(self, tmp_path):
        """`ok.md` is a plain short word coincidentally followed by an
        extension, not a real repo filename (no hyphen/underscore stem) —
        must still fail the traceability gate."""
        spec, root = _write_tech_spec(tmp_path, self._ccl("**Source:** ok.md"))
        assert "FeatureSpec.block_source_missing" in _rule_ids(spec, root)

    def test_real_corpus_hyphenated_bare_filename_with_annotation_passes(self, tmp_path):
        """Real corpus shape (F054_DataExportJobs) — must NOT regress: a
        hyphenated bare filename with a parenthetical permission-ID
        annotation is a legitimate non-path citation."""
        spec, root = _write_tech_spec(
            tmp_path,
            self._ccl("**Source:** feature-list.md (PERM051_AdminExportData)"),
        )
        assert "FeatureSpec.block_source_missing" not in _rule_ids(spec, root)


# ===========================================================================
# Class 3 — func.code_unsurfaced: cross-feature reference vs. local
# declaration. Real strings verbatim from F052_EmailNotifications ("in
# F051_TransactionStateMachine") and F055_PayPalWebhook ("(F051_...)").
# ===========================================================================

def _write_owner_feature(tmp_path: Path, slug: str, code: str) -> Path:
    """Write a minimal sibling feature dir under docs/features/{slug}/ whose
    technical-spec.md genuinely declares `code` (e.g. 'SM-001'). Used to prove
    finding 2's fix actually VERIFIES ownership against the named feature's
    own technical-spec.md rather than trusting an adjacent tag blindly."""
    other_dir = tmp_path / "docs" / "features" / slug
    other_dir.mkdir(parents=True, exist_ok=True)
    (other_dir / "technical-spec.md").write_text(
        f"# {slug} — Owner Feature\n\n"
        "## Overview\nOwner feature.\n\n"
        "## Cross-Cutting Logic\n\n"
        "**Client behavior:** see behavior-logic.md\n\n"
        "### State Machines\n\n"
        f"### Local transitions ({code})\n"
        "**Linked FR:** FR-001\n**Source:** `some/other.rb:1-3`\n"
        "**Applies to:** Transaction\n\n",
        encoding="utf-8",
    )
    return other_dir


def _write_feature_pair(tmp_path: Path, tech_extra: str, func_body: str,
                         owner_feature: tuple[str, str] | None =
                         ("F051_TransactionStateMachine", "SM-001")) -> Path:
    """`owner_feature`, when given, writes a sibling feature dir that genuinely
    declares the given code — the real-corpus default (SM-001 IS owned by
    F051_TransactionStateMachine) so existing cross-feature-reference tests
    keep exercising the "verified, may be exempted" path under finding 2's
    fix. Pass `owner_feature=None` (or a mismatched code/slug) to test the
    fail-closed paths instead."""
    feat_dir = tmp_path / "docs" / "features" / "F900_CrossRef"
    feat_dir.mkdir(parents=True)
    (feat_dir / "technical-spec.md").write_text(
        "# F900_CrossRef — Cross Reference Test\n\n"
        "## Overview\n" + tech_extra + "\n\n"
        "## Polymorphic Behavior\nNone.\n\n"
        "## Cross-Cutting Logic\n\n"
        "**Client behavior:** see behavior-logic.md\n\n"
        "### Requirements\nNone.\n\n"
        "### Business Rules\n\n"
        "### Passwords are hashed before storage (BR-001)\n"
        "**Linked FR:** FR-001\n**Source:** `some/path.rb:1-3`\n"
        "**Applies to:** User\n\n"
        "### Decision Logic\nN/A\n\n"
        "### State Machines\nNone.\n\n"
        + _CCL_TAIL + _TAIL,
        encoding="utf-8",
    )
    (feat_dir / "functional-spec.md").write_text(func_body, encoding="utf-8")
    if owner_feature is not None:
        _write_owner_feature(tmp_path, *owner_feature)
    return tmp_path


_FUNC_NO_SURFACING = """\
# F900_CrossRef — Cross Reference Test

## 1. Overview

**Problem:** Users need this feature.
**Solution:** It does the thing.
**Users:** Registered User.
**Goals:** Let a user do the thing.
**Non-Goals:** None called out.

## 2. Functional Capabilities

| ID | Capability | What the user can do | Requirements | Screens |
|----|------------|------------------------|---------------|---------|

## 3. Open Decisions

None — no unresolved domain confirmations.

## 4. Requirements

### Foundation (0xx)

## 5. Business Rules

## 6. Screens

N/A — background feature; no user-facing screens.

## 7. User Stories

## 8. Scenarios

## 9. Edge Cases

| Scenario | What Happens | User-Facing Message |
|----------|--------------|----------------------|
| Network failure | Request retried | "Something went wrong, try again." |

## 10. Edge Behaviours to Verify

## 11. Risks & Known Issues

N/A — none found.

## 12. Dependencies

N/A — none found.

## 13. Configuration

N/A — no user-facing configuration constants for this feature.
"""


class TestCodeUnsurfacedCrossFeatureReference:
    def test_paren_tagged_cross_feature_sm_not_counted_as_declaration(self, tmp_path):
        """F055_PayPalWebhook shape: 'SM-001 (F051_TransactionStateMachine)'."""
        root = _write_feature_pair(
            tmp_path,
            "F900 drives the following transitions in SM-001 "
            "(F051_TransactionStateMachine) via `TransactionService#update`.",
            _FUNC_NO_SURFACING,
        )
        spec = root / "docs" / "features" / "F900_CrossRef"
        rules = _rule_ids(spec, root)
        assert "func.code_unsurfaced" not in rules or not any(
            "SM-001" in m for m in _messages_for(spec, root, "func.code_unsurfaced")
        )

    def test_in_keyword_cross_feature_reference_not_counted_as_declaration(self, tmp_path):
        """F052_EmailNotifications shape: 'SM-001 in F051_TransactionStateMachine'."""
        root = _write_feature_pair(
            tmp_path,
            "Transaction state changes that trigger emails are managed by "
            "SM-001 in F051_TransactionStateMachine.",
            _FUNC_NO_SURFACING,
        )
        spec = root / "docs" / "features" / "F900_CrossRef"
        messages = _messages_for(spec, root, "func.code_unsurfaced")
        assert not any("SM-001" in m for m in messages)


class TestCodeUnsurfacedStillFiresOnGenuineGap:
    def test_local_declaration_without_surfacing_still_fires(self, tmp_path):
        """Negative test: BR-001 is declared LOCALLY (own block, no cross-feature
        tag) and never surfaced in func-spec § 3/§ 4 — must still fire."""
        root = _write_feature_pair(tmp_path, "No cross references here.", _FUNC_NO_SURFACING)
        spec = root / "docs" / "features" / "F900_CrossRef"
        messages = _messages_for(spec, root, "func.code_unsurfaced")
        assert any("BR-001" in m for m in messages), \
            "a genuinely unsurfaced LOCAL code must still fire"

    def test_self_reference_same_feature_still_counts_as_declaration(self, tmp_path):
        """Ambiguous-but-same-feature: the owner tag names THIS feature
        (F900_CrossRef) itself — must still be treated as a local declaration
        (fail closed), so an unsurfaced SM-002 still fires."""
        root = _write_feature_pair(
            tmp_path,
            "See SM-002 (F900_CrossRef) for local UI transitions.",
            _FUNC_NO_SURFACING,
        )
        spec = root / "docs" / "features" / "F900_CrossRef"
        messages = _messages_for(spec, root, "func.code_unsurfaced")
        assert any("SM-002" in m for m in messages), \
            "a same-feature owner tag must not be treated as a cross-feature reference"


# ===========================================================================
# REWORK (adversarial review finding 2, HIGH) — a cross-feature owner tag must
# be VERIFIED against the named feature's own technical-spec.md before it is
# trusted to exclude a code from "declared here". The two tests above
# (paren-tagged / in-keyword) now pass a REAL owner (F051_TransactionStateMachine
# genuinely declares SM-001, via _write_feature_pair's default) — they prove
# the "verified, may be exempted" path. These four prove every fail-closed path.
# ===========================================================================

class TestCodeUnsurfacedCrossFeatureReferenceVerified:
    def test_nonexistent_owner_feature_fails_closed(self, tmp_path):
        """The tag names a feature that has NO directory at all (F999_GhostFeature
        need not exist) — unverifiable, so BR-005 stays a local declaration and
        still fires unsurfaced, exactly as if no tag were present."""
        root = _write_feature_pair(
            tmp_path,
            "F900 relies on BR-005 (F999_GhostFeature) to gate the callback.",
            _FUNC_NO_SURFACING,
        )
        # Re-declare BR-005 locally too (the fixture's own BR-001 block stays;
        # add BR-005's own block heading so it is a real local declaration
        # candidate, matching the reproduction in the review finding).
        tech = root / "docs" / "features" / "F900_CrossRef" / "technical-spec.md"
        tech.write_text(
            tech.read_text(encoding="utf-8").replace(
                "### Passwords are hashed before storage (BR-001)",
                "### Gate the callback (BR-005)\n"
                "**Linked FR:** FR-001\n**Source:** `some/other2.rb:1-3`\n"
                "**Applies to:** Callback\n\n"
                "### Passwords are hashed before storage (BR-001)",
            ),
            encoding="utf-8",
        )
        spec = root / "docs" / "features" / "F900_CrossRef"
        messages = _messages_for(spec, root, "func.code_unsurfaced")
        assert any("BR-005" in m for m in messages), \
            "an owner tag naming a NONEXISTENT feature must fail closed (still local)"

    def test_owner_feature_exists_but_does_not_declare_code_fails_closed(self, tmp_path):
        """F051_TransactionStateMachine exists but its technical-spec.md declares
        only SM-002, not the tagged SM-001 — the tag is WRONG, so SM-001 must
        fail closed (stay local) rather than being silently exempted."""
        root = _write_feature_pair(
            tmp_path,
            "F900 drives the following transitions in SM-001 "
            "(F051_TransactionStateMachine) via `TransactionService#update`.",
            _FUNC_NO_SURFACING,
            owner_feature=("F051_TransactionStateMachine", "SM-002"),
        )
        spec = root / "docs" / "features" / "F900_CrossRef"
        messages = _messages_for(spec, root, "func.code_unsurfaced")
        assert any("SM-001" in m for m in messages), \
            "a tag naming a real feature that does NOT declare the code must fail closed"

    def test_owner_feature_declares_code_is_the_only_exempt_case(self, tmp_path):
        """Sanity restatement: when the named feature genuinely declares the
        tagged code (the default fixture — F051 really owns SM-001), the
        cross-reference IS exempted and SM-001 does not fire as unsurfaced."""
        root = _write_feature_pair(
            tmp_path,
            "F900 drives the following transitions in SM-001 "
            "(F051_TransactionStateMachine) via `TransactionService#update`.",
            _FUNC_NO_SURFACING,
        )
        spec = root / "docs" / "features" / "F900_CrossRef"
        messages = _messages_for(spec, root, "func.code_unsurfaced")
        assert not any("SM-001" in m for m in messages), \
            "a tag naming a feature that genuinely declares the code IS exemptable"

    def test_no_features_root_available_fails_closed(self):
        """Unit-level: features_root=None (no docs_root context at all) must
        never exclude a cross-feature-tagged code, regardless of what the tag
        names — the function-level fail-closed default, independent of any
        filesystem fixture."""
        import sys as _sys
        from pathlib import Path as _Path
        _scripts_dir = _Path(__file__).resolve().parent.parent
        if str(_scripts_dir) not in _sys.path:
            _sys.path.insert(0, str(_scripts_dir))
        import validate_feature_spec as vfs  # noqa: E402

        tech_text = (
            "# F900_CrossRef\n\n"
            "F900 drives transitions in SM-001 (F051_TransactionStateMachine).\n"
        )
        declared = vfs._func_declared_codes(tech_text, own_fcode="F900", features_root=None)
        assert "SM-001" in declared["SM"], \
            "with no features_root to verify against, the tag must never be trusted"


# ===========================================================================
# Class 4 — func.secret_shape: placeholder-value exemption. Real strings
# verbatim from F003_EmailConfirmation (ellipsis, code-symbol reference) and
# F064_AdminPlanView (bracket placeholder).
# ===========================================================================

_FUNC_PREAMBLE = """\
# F900_Secret — Secret Shape Test

**Priority**: P2
**Type**: ui
**Generated**: migrated

## 1. Overview

**Problem:** {overview_line}
**Solution:** Users authenticate with email and password.
**Users:** Registered User.
**Goals:** Let a registered user sign in.
**Non-Goals:** None called out.

## 2. Functional Capabilities

| ID | Capability | What the user can do | Requirements | Screens |
|----|------------|------------------------|---------------|---------|
| CAP-01 | Sign in | Authenticate with email and password | FR-001 | N/A |

## 3. Open Decisions

None — no unresolved domain confirmations.

## 4. Requirements

### Foundation (0xx)

- **FR-001** Every password must be hashed before storage.

## 5. Business Rules

- Passwords are hashed before storage. (BR-001)

## 6. Screens

N/A — background feature; no user-facing screens.

## 7. User Stories

## 8. Scenarios

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


_MINIMAL_TECH_SPEC_FOR_SECRET_TEST = """\
# F900_Secret — Secret Shape Test

## Overview
Overview text.

## Polymorphic Behavior
None.

## Cross-Cutting Logic

**Client behavior:** see behavior-logic.md

### Requirements
None.

### Business Rules

### Passwords are hashed before storage (BR-001)
**Linked FR:** FR-001
**Source:** `some/path.rb:1-3`
**Applies to:** User

### Decision Logic
N/A

### State Machines
None.

### Algorithms
None.

### External Integrations
None.

### Verification
None.

## User Stories

### Edge Cases
None.

## Key Entities
None.

## Artifact References
None.

## Assumptions
None.

## Source Code References
None.

## Unresolved Questions
None.
"""


def _write_func_spec(tmp_path: Path, overview_line: str) -> Path:
    """Write a full F900_Secret feature dir (both files) — functional-spec.md
    carries `overview_line` in § 1 Overview, technical-spec.md is a minimal
    valid companion declaring the SAME FR-001/BR-001 the func-spec surfaces,
    so only func.secret_shape is exercised (no code_unsurfaced noise)."""
    feat_dir = tmp_path / "artifacts" / "features" / "F900_Secret"
    feat_dir.mkdir(parents=True)
    (feat_dir / "functional-spec.md").write_text(
        _FUNC_PREAMBLE.format(overview_line=overview_line), encoding="utf-8",
    )
    (feat_dir / "technical-spec.md").write_text(
        _MINIMAL_TECH_SPEC_FOR_SECRET_TEST, encoding="utf-8",
    )
    return feat_dir / "functional-spec.md"


class TestSecretShapePlaceholderNotFlagged:
    def test_ellipsis_value_not_flagged(self, tmp_path):
        spec = _write_func_spec(
            tmp_path,
            "`show` (`GET` /people/confirmation?confirmation_token=…) "
            "processes the token and approves the membership.",
        )
        assert "func.secret_shape" not in _rule_ids(spec, tmp_path)

    def test_bracket_placeholder_value_not_flagged(self, tmp_path):
        spec = _write_func_spec(
            tmp_path,
            "Admin visiting `/admin/plan` when configured is redirected to "
            "external URL with `?token=<jwt>`.",
        )
        assert "func.secret_shape" not in _rule_ids(spec, tmp_path)

    def test_dotted_code_symbol_reference_not_flagged(self, tmp_path):
        spec = _write_func_spec(
            tmp_path,
            "Valid confirmation token: Email.confirmed_at set, "
            "CommunityMembership.status = accepted.",
        )
        assert "func.secret_shape" not in _rule_ids(spec, tmp_path)


class TestSecretShapeStillFiresOnRealCredential:
    def test_real_dsn_credential_still_flagged(self, tmp_path):
        spec = _write_func_spec(
            tmp_path,
            "This feature talks to postgres://user:hunter2@db.internal:5432/app "
            "at boot.",
        )
        assert "func.secret_shape" in _rule_ids(spec, tmp_path)

    def test_real_api_key_still_flagged(self, tmp_path):
        spec = _write_func_spec(
            tmp_path,
            "It reads API_KEY=sk-abc123def456 from the environment at startup.",
        )
        assert "func.secret_shape" in _rule_ids(spec, tmp_path)

    def test_uppercase_dotted_value_that_is_not_a_code_ref_still_flagged(self, tmp_path):
        """A value that merely CONTAINS a dot but is not a Model.attribute
        shape (both sides uppercase-leading, unlike a real snake_case
        attribute) must not be swept into the code-symbol-reference exemption."""
        spec = _write_func_spec(
            tmp_path,
            "It stores token: AWS.SECRET_ACCESS_KEY_abc123XYZ in config.",
        )
        assert "func.secret_shape" in _rule_ids(spec, tmp_path)


class TestSecretShapeLongOpaqueDottedValueStillFlagged:
    """REWORK (adversarial review finding 1, CRITICAL): these three strings are
    the exact reproduction from the review — `_CODE_SYMBOL_REF_RE` matched
    `Upper.lower_snake` structurally identically for a harmless attribute
    citation (`Email.confirmed_at`) and an opaque real secret literal
    (`Rails.application_secret_...`), so all three were being silently
    neutralized before scrub_generic_secret/scrub_credentials ever saw them.
    Each MUST fire func.secret_shape after the length-cap + digit-run fix."""

    def test_secret_key_rails_application_secret_still_flagged(self, tmp_path):
        spec = _write_func_spec(
            tmp_path,
            "Config sets SECRET_KEY=Rails.application_secret_20260817abcdef1234567890 "
            "at boot.",
        )
        assert "func.secret_shape" in _rule_ids(spec, tmp_path)

    def test_stripe_secret_colon_assignment_still_flagged(self, tmp_path):
        spec = _write_func_spec(
            tmp_path,
            "Config sets stripe_secret: Stripe.sk_live_51H8xJ2KG3fN0aBcDeFgHiJKLMNOP12345 "
            "for billing.",
        )
        assert "func.secret_shape" in _rule_ids(spec, tmp_path)

    def test_db_password_settings_prod_password_still_flagged(self, tmp_path):
        spec = _write_func_spec(
            tmp_path,
            "The job reads db_password=Settings.prod_password_hunter2_deadbeef_cafe "
            "from vault.",
        )
        assert "func.secret_shape" in _rule_ids(spec, tmp_path)


# ===========================================================================
# Class 4 REWORK (round 2) — a second adversarial review found the
# length+digit-run discriminator on the post-dot segment still bypassable:
# a plausible high-entropy secret typed as `ClassName.<opaque-value>` dodges
# both the length cap and the digit-run rule by interleaving digits with
# letters, or (in the third case) needs no digits at all — a snake_case
# consonant cluster with zero vowels. Length/digit-run says nothing about
# English-identifier-ness vs opaque-blob-ness; that was the actual flaw.
#
# The fix replaces the digit-run check with two structural properties on
# the post-dot segment:
#   1. strict lowercase snake_case (`^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$`) —
#      kills the two mixed-case bypasses outright;
#   2. a run of 3+ consecutive ASCII letters containing a vowel — a cheap
#      word-likeness proxy that kills the fully-lowercase, digit-interleaved
#      or consonant-cluster bypasses that (1) alone lets through.
# The length cap is kept only as defense-in-depth (raised 20 -> 30, so it
# no longer collides with the two longer legitimate attribute references
# below — 26 and 28 chars) — it is NOT what closes this hole; properties
# 1+2 are.
#
# Each test asserts the INTERMEDIATE neutralized value from
# `_neutralize_placeholder_assignments` directly (unit-level, real check
# path), NOT just the eventual verdict — a verdict-only assertion is what
# let this hole survive one full adversarial round already. Each fire case
# is also re-proven end-to-end through the subprocess harness
# (`_write_func_spec` / `_rule_ids`), since the prior round's unit tests
# passed while the end-to-end path was still holed.
# ===========================================================================

import sys as _sys3  # noqa: E402
from pathlib import Path as _Path3  # noqa: E402

_scripts_dir3 = _Path3(__file__).resolve().parent.parent
if str(_scripts_dir3) not in _sys3.path:
    _sys3.path.insert(0, str(_scripts_dir3))
import validate_feature_spec as _vfs  # noqa: E402


def _neutralized(line: str) -> str:
    return _vfs._neutralize_placeholder_assignments(line)


def _is_still_secret_shaped(neutralized: str) -> bool:
    """Mirrors the exact verdict computation at the func.secret_shape call
    site (validate_feature_spec.py, `_check_functional_spec`)."""
    secret_hit = _vfs.scrub_generic_secret(neutralized) != neutralized
    _, cred_hit = _vfs.scrub_credentials(neutralized)
    return secret_hit or cred_hit


class TestSecretShapeWordLikenessQuadrantUnit:
    """Unit-level, real check path: _neutralize_placeholder_assignments ->
    scrub_generic_secret / scrub_credentials. Asserts the intermediate
    neutralized value for every case, not just the final verdict."""

    # --- round-2 bypasses reproduced verbatim from the adversarial review ---

    def test_bypass_1_mixed_case_interleaved_digits_survives_neutralization(self):
        line = "It reads token: Vault.kX9qM2wR7tY4bN1cL8 from the config store."
        neutralized = _neutralized(line)
        assert neutralized == line, f"must NOT be neutralized, got {neutralized!r}"
        assert _is_still_secret_shaped(neutralized), "must still read as secret-shaped"

    def test_bypass_2_mixed_case_assignment_survives_neutralization(self):
        line = "Config sets api_secret=Store.a1B2c3D4e5F6g7H8i9 at boot."
        neutralized = _neutralized(line)
        assert neutralized == line, f"must NOT be neutralized, got {neutralized!r}"
        assert _is_still_secret_shaped(neutralized), "must still read as secret-shaped"

    def test_bypass_3_lowercase_digit_interleaved_survives_neutralization(self):
        line = "secret_key=Store.a1b2c3d4e5f6g7h8i9"
        neutralized = _neutralized(line)
        assert neutralized == line, f"must NOT be neutralized, got {neutralized!r}"
        assert _is_still_secret_shaped(neutralized), "must still read as secret-shaped"

    # --- 3 more invented short/digit-poor secrets proving the quadrant is
    # genuinely covered, not just the 3 examples from the review ---

    def test_invented_1_all_consonant_no_digits_survives_neutralization(self):
        """Zero digits at all -- proves the fix does not secretly still rely
        on a digit signal; a pure consonant cluster has no vowel-bearing run."""
        line = "Config sets session_token=Cache.zxcvbnmqwrty for rate limiting."
        neutralized = _neutralized(line)
        assert neutralized == line, f"must NOT be neutralized, got {neutralized!r}"
        assert _is_still_secret_shaped(neutralized), "must still read as secret-shaped"

    def test_invented_2_digit_interleaved_consonants_survives_neutralization(self):
        line = "The worker reads api_secret=Node.k7x9q2z4m8w1r5t3 from the queue."
        neutralized = _neutralized(line)
        assert neutralized == line, f"must NOT be neutralized, got {neutralized!r}"
        assert _is_still_secret_shaped(neutralized), "must still read as secret-shaped"

    def test_invented_3_underscore_chunked_consonants_survives_neutralization(self):
        line = "The service checks auth_password=Db.grpxznwqtlyk before connecting."
        neutralized = _neutralized(line)
        assert neutralized == line, f"must NOT be neutralized, got {neutralized!r}"
        assert _is_still_secret_shaped(neutralized), "must still read as secret-shaped"

    # --- real code-symbol references (word-like, short) must stay exempt ---

    def test_time_now_is_neutralized(self):
        line = "e.confirmed_at = Time.now"
        neutralized = _neutralized(line)
        assert neutralized == "e.confirmed_at ", f"got {neutralized!r}"
        assert not _is_still_secret_shaped(neutralized)

    def test_person_confirmation_token_assignment_is_neutralized(self):
        line = "token=Person.confirmation_token"
        neutralized = _neutralized(line)
        assert neutralized == "token", f"got {neutralized!r}"
        assert not _is_still_secret_shaped(neutralized)

    def test_community_approve_pending_membership_is_neutralized(self):
        """26-char post-dot segment -- above the OLD 20-char cap, must stay
        exempt under the new 30-char cap since word-likeness (not length)
        is the primary discriminator here."""
        line = "field=Community.approve_pending_membership"
        neutralized = _neutralized(line)
        assert neutralized == "field", f"got {neutralized!r}"
        assert not _is_still_secret_shaped(neutralized)

    def test_transaction_payment_gateway_reference_id_is_neutralized(self):
        """28-char post-dot segment -- the longest legitimate reference in
        this matrix; must clear the 30-char defense-in-depth cap."""
        line = "attr=Transaction.payment_gateway_reference_id"
        neutralized = _neutralized(line)
        assert neutralized == "attr", f"got {neutralized!r}"
        assert not _is_still_secret_shaped(neutralized)

    def test_person_confirmation_token_no_assignment_untouched(self):
        """No `=`/`:` at all -- _neutralize_placeholder_assignments has
        nothing to erase, and the line was never secret-shaped to begin
        with (no api_key/token/secret/password keyword before an operator)."""
        line = "uses Person.confirmation_token to look up"
        neutralized = _neutralized(line)
        assert neutralized == line
        assert not _is_still_secret_shaped(neutralized)

    def test_email_confirmed_at_no_assignment_untouched(self):
        line = "reads Email.confirmed_at for the check"
        neutralized = _neutralized(line)
        assert neutralized == line
        assert not _is_still_secret_shaped(neutralized)

    def test_community_membership_status_assignment_untouched(self):
        """The dotted symbol is on the LHS, not captured as the assignment
        VALUE at all (`accepted` is) -- never secret-shaped regardless of
        the exemption logic; included as standing regression coverage."""
        line = "CommunityMembership.status = accepted"
        neutralized = _neutralized(line)
        assert not _is_still_secret_shaped(neutralized)


class TestSecretShapeWordLikenessQuadrantEndToEnd:
    """Integration-level: the real subprocess harness (_write_func_spec /
    _rule_ids), proving the fix holds through the full CLI path, not just
    in isolation (see the class-level REWORK comment: the prior round's
    tests passed in isolation while the end-to-end path stayed holed)."""

    def test_bypass_1_still_flagged_end_to_end(self, tmp_path):
        spec = _write_func_spec(
            tmp_path,
            "It reads token: Vault.kX9qM2wR7tY4bN1cL8 from the config store.",
        )
        assert "func.secret_shape" in _rule_ids(spec, tmp_path)

    def test_bypass_2_still_flagged_end_to_end(self, tmp_path):
        spec = _write_func_spec(
            tmp_path,
            "Config sets api_secret=Store.a1B2c3D4e5F6g7H8i9 at boot.",
        )
        assert "func.secret_shape" in _rule_ids(spec, tmp_path)

    def test_bypass_3_still_flagged_end_to_end(self, tmp_path):
        spec = _write_func_spec(
            tmp_path,
            "secret_key=Store.a1b2c3d4e5f6g7h8i9",
        )
        assert "func.secret_shape" in _rule_ids(spec, tmp_path)

    def test_invented_1_still_flagged_end_to_end(self, tmp_path):
        spec = _write_func_spec(
            tmp_path,
            "Config sets session_token=Cache.zxcvbnmqwrty for rate limiting.",
        )
        assert "func.secret_shape" in _rule_ids(spec, tmp_path)

    def test_invented_2_still_flagged_end_to_end(self, tmp_path):
        spec = _write_func_spec(
            tmp_path,
            "The worker reads api_secret=Node.k7x9q2z4m8w1r5t3 from the queue.",
        )
        assert "func.secret_shape" in _rule_ids(spec, tmp_path)

    def test_invented_3_still_flagged_end_to_end(self, tmp_path):
        spec = _write_func_spec(
            tmp_path,
            "The service checks auth_password=Db.grpxznwqtlyk before connecting.",
        )
        assert "func.secret_shape" in _rule_ids(spec, tmp_path)

    def test_community_approve_pending_membership_not_flagged_end_to_end(self, tmp_path):
        spec = _write_func_spec(
            tmp_path,
            "The admin sets field=Community.approve_pending_membership on save.",
        )
        assert "func.secret_shape" not in _rule_ids(spec, tmp_path)

    def test_transaction_payment_gateway_reference_id_not_flagged_end_to_end(self, tmp_path):
        spec = _write_func_spec(
            tmp_path,
            "The report cites attr=Transaction.payment_gateway_reference_id inline.",
        )
        assert "func.secret_shape" not in _rule_ids(spec, tmp_path)


# ===========================================================================
# Class 4 REWORK (round 3) — a third adversarial review found the round-2
# word-likeness discriminator (strict snake_case + 3+-letter vowel-bearing
# run + 30-char cap) STILL bypassable, 8/8, by two techniques:
#   - prefixing a real word onto a digit-bearing blob so the word-like run
#     is satisfied by the PREFIX, laundering the digit-bearing suffix
#     riding along with it (`token_a1b2c3d4e5f6`, `pass_9f8e7d6c5b4a`,
#     `bearer_abc123def456`, `session_ff00ee11dd22`, `hunter2_seed`);
#   - a hex-only blob that reads as pure letters, since every hex digit
#     character is also a lowercase ASCII letter, so no digit ever
#     appears (`deadbeefcafebabe`, `facadedecadebead`, `key_deadbeefcafe`).
#
# Two more structural properties on the post-dot segment close both:
#   4. no digit anywhere in the segment at all;
#   5. no UNDERSCORE-SEPARATED TOKEN inside the segment is hex-only (every
#      char in `[a-f]`) AND >= 8 chars — checked PER TOKEN. Checking the
#      WHOLE segment for "not hex-only" does not work: `key_deadbeefcafe`
#      as a whole is not hex-only (`k`/`y` sit outside `[a-f]`), even
#      though the token `deadbeefcafe` riding inside it is a pure 12-char
#      hex blob — this is the trap a prior pass into this exact predicate
#      already walked into and had to back out of.
#
# Every attack is asserted at the PREDICATE level first
# (`_is_non_secret_value` must return False) — the strongest, most direct
# check that the shape itself is rejected, independent of which keyword
# scrub_generic_secret/scrub_credentials happen to recognize. Six of the
# eight are ALSO re-proven end-to-end through the real neutralize -> scrub
# path and the subprocess harness. See TestSecretShapeRound3KeywordFamilyGap
# below for why the remaining two ("auth=", bare "key=") cannot be
# re-proven end-to-end — that gap sits in a file this task does not own.
# ===========================================================================


class TestSecretShapeRound3DigitAndHexTokenRulesUnit:
    """Unit-level, predicate itself: `_is_non_secret_value` must reject
    every one of the 8 round-3 review attacks (rule 4 or rule 5), while
    every legitimate code-symbol reference measured in the real corpus
    still passes. `core` here is the FULL `ClassName.attr` value, matching
    `_is_non_secret_value`'s actual input shape at its real call site."""

    # --- the 8 verbatim round-3 review attacks — must NOT be exempted ---

    def test_attack_1_word_prefixed_digit_blob_underscore(self):
        assert _vfs._is_non_secret_value("Store.token_a1b2c3d4e5f6") is False

    def test_attack_2_word_prefixed_hex_only_blob_underscore(self):
        """The trap: `key_deadbeefcafe` as a WHOLE string is not hex-only
        (`k`/`y` fall outside `[a-f]`) -- only a PER-TOKEN split catches
        the `deadbeefcafe` blob riding inside it."""
        assert _vfs._is_non_secret_value("Config.key_deadbeefcafe") is False

    def test_attack_3_pass_prefixed_digit_blob(self):
        assert _vfs._is_non_secret_value("Settings.pass_9f8e7d6c5b4a") is False

    def test_attack_4_bearer_prefixed_digit_blob(self):
        assert _vfs._is_non_secret_value("Vault.bearer_abc123def456") is False

    def test_attack_5_session_prefixed_digit_blob(self):
        assert _vfs._is_non_secret_value("Store.session_ff00ee11dd22") is False

    def test_attack_6_pure_hex_only_blob_no_underscore(self):
        assert _vfs._is_non_secret_value("Store.deadbeefcafebabe") is False

    def test_attack_7_pure_hex_only_blob_no_underscore_2(self):
        assert _vfs._is_non_secret_value("Config.facadedecadebead") is False

    def test_attack_8_hunter2_seed_digit_word(self):
        assert _vfs._is_non_secret_value("Store.hunter2_seed") is False

    # --- legitimate references measured in the real corpus must still pass ---

    def test_legit_email_confirmed_at(self):
        assert _vfs._is_non_secret_value("Email.confirmed_at") is True

    def test_legit_cafe_id_length_floor_protects_short_hex_word(self):
        """`cafe` is 4 chars, entirely `[a-f]` -- below the 8-char floor,
        so rule 5 must NOT reject it. This is the case the floor exists
        to protect."""
        assert _vfs._is_non_secret_value("Store.cafe_id") is True

    def test_legit_person_confirmation_token(self):
        assert _vfs._is_non_secret_value("Person.confirmation_token") is True

    def test_legit_community_approve_pending_membership(self):
        assert _vfs._is_non_secret_value("Community.approve_pending_membership") is True

    def test_legit_transaction_payment_gateway_reference_id(self):
        assert _vfs._is_non_secret_value("Transaction.payment_gateway_reference_id") is True

    def test_legit_listing_availability(self):
        assert _vfs._is_non_secret_value("Listing.availability") is True

    def test_legit_community_membership_status(self):
        assert _vfs._is_non_secret_value("CommunityMembership.status") is True

    def test_legit_time_now(self):
        assert _vfs._is_non_secret_value("Time.now") is True


class TestSecretShapeRound3EndToEndSixOfEight:
    """Integration-level: the real subprocess harness, for the 6 of the 8
    round-3 attacks whose keyword (`token`/`secret`/`password`/`api_secret`)
    IS a member of the family scrub_generic_secret/scrub_credentials
    recognize, so the full pipeline verdict is provable end-to-end. Each
    asserts the INTERMEDIATE neutralized value too, not only the verdict —
    a verdict-only assertion is what let rounds 1 and 2 both survive one
    full adversarial pass apiece."""

    def test_attack_1_word_prefixed_digit_blob_fires(self, tmp_path):
        line = "LEAKED secret_key=Store.token_a1b2c3d4e5f6"
        assert _neutralized(line) == line
        spec = _write_func_spec(tmp_path, line)
        assert "func.secret_shape" in _rule_ids(spec, tmp_path)

    def test_attack_3_pass_prefixed_digit_blob_fires(self, tmp_path):
        line = "LEAKED password=Settings.pass_9f8e7d6c5b4a"
        assert _neutralized(line) == line
        spec = _write_func_spec(tmp_path, line)
        assert "func.secret_shape" in _rule_ids(spec, tmp_path)

    def test_attack_5_session_prefixed_digit_blob_fires(self, tmp_path):
        line = "LEAKED token=Store.session_ff00ee11dd22"
        assert _neutralized(line) == line
        spec = _write_func_spec(tmp_path, line)
        assert "func.secret_shape" in _rule_ids(spec, tmp_path)

    def test_attack_6_pure_hex_only_blob_no_underscore_fires(self, tmp_path):
        line = "LEAKED secret=Store.deadbeefcafebabe"
        assert _neutralized(line) == line
        spec = _write_func_spec(tmp_path, line)
        assert "func.secret_shape" in _rule_ids(spec, tmp_path)

    def test_attack_8_hunter2_seed_digit_word_fires(self, tmp_path):
        line = "LEAKED secret_key=Store.hunter2_seed"
        assert _neutralized(line) == line
        spec = _write_func_spec(tmp_path, line)
        assert "func.secret_shape" in _rule_ids(spec, tmp_path)

    def test_attack_2_word_prefixed_hex_blob_fires_via_api_secret(self, tmp_path):
        """Same shape as review attack 2 (`Config.key_deadbeefcafe`,
        keyword `api_secret`, a real member of the recognized family) --
        the bare-`key=` keyword variant is covered separately in
        TestSecretShapeRound3KeywordFamilyGap, since bare `key` itself
        never reaches the scrubber regardless of this exemption."""
        line = "LEAKED api_secret=Config.key_deadbeefcafe"
        assert _neutralized(line) == line
        spec = _write_func_spec(tmp_path, line)
        assert "func.secret_shape" in _rule_ids(spec, tmp_path)


class TestSecretShapeRound3KeywordFamilyGap:
    """Two of the 8 verbatim round-3 review attacks
    (`auth=Vault.bearer_abc123def456`, `key=Config.facadedecadebead`) use a
    keyword that is NOT a member of the secret keyword family
    scrub_generic_secret/scrub_credentials recognize at all:
    `_content_sniff_signals_lib.py`'s literal-assignment fingerprint only
    fires on `api[_-]?key|apikey|token|secret|password`, and its `Bearer`
    fingerprint requires a literal `Bearer` token followed by WHITESPACE
    (`\\bBearer\\s+\\S+`) -- `bearer_abc123def456` has no whitespace after
    "bearer", and bare "key" is not "api_key"/"apikey". Confirmed directly
    below: running the two scrubbers on the RAW, un-neutralized line (no
    exemption logic involved at all) never flags either one.

    This is a pre-existing gap in the keyword family itself -- orthogonal
    to the code-symbol-reference exemption these three rounds have
    hardened, and out of this task's file ownership
    (`_content_sniff_signals_lib.py` is not `validate_feature_spec.py`).
    What IS this predicate's responsibility, and IS proven here: rules 4/5
    correctly refuse to exempt these two shapes regardless -- the
    end-to-end miss is entirely the scrubber's, not laundered by this
    exemption.
    """

    def test_raw_scrubbers_never_recognize_bare_auth_keyword(self):
        line = "auth=Vault.bearer_abc123def456"
        assert _vfs.scrub_generic_secret(line) == line
        _, cred_hit = _vfs.scrub_credentials(line)
        assert cred_hit is False

    def test_raw_scrubbers_never_recognize_bare_key_keyword(self):
        line = "key=Config.facadedecadebead"
        assert _vfs.scrub_generic_secret(line) == line
        _, cred_hit = _vfs.scrub_credentials(line)
        assert cred_hit is False

    def test_predicate_still_refuses_to_exempt_bare_auth_attack(self):
        assert _vfs._is_non_secret_value("Vault.bearer_abc123def456") is False
        line = "auth=Vault.bearer_abc123def456"
        assert _neutralized(line) == line, "predicate must not erase this value"

    def test_predicate_still_refuses_to_exempt_bare_key_attack(self):
        assert _vfs._is_non_secret_value("Config.facadedecadebead") is False
        line = "key=Config.facadedecadebead"
        assert _neutralized(line) == line, "predicate must not erase this value"


class TestSecretShapeRound3InventedAttacks:
    """4 attacks invented beyond the review's 8, probing the exact edges of
    rules 4/5. Two die cleanly (boundary confirmation); two SURVIVE and are
    reported honestly as confirmed residual gaps (see the RESIDUAL
    LIMITATION note above `_PLACEHOLDER_LITERAL_RE` in
    validate_feature_spec.py) -- neither is closed by this rework, and
    closing them is explicitly out of scope ("do not redesign")."""

    def test_invented_1_boundary_exactly_8_char_hex_token_dies(self, tmp_path):
        """No word prefix, no digit, single token exactly at the 8-char
        floor -- must die (>= 8, not > 8)."""
        line = "api_secret=Cache.deadbeef"
        assert _neutralized(line) == line
        assert _vfs._is_non_secret_value("Cache.deadbeef") is False
        spec = _write_func_spec(tmp_path, "LEAKED " + line)
        assert "func.secret_shape" in _rule_ids(spec, tmp_path)

    def test_invented_2_digit_smuggled_into_hex_blob_dies_via_rule_4(self, tmp_path):
        """A single digit riding inside an otherwise-hex-only-looking blob
        -- rule 4 (no digits at all) catches it even where rule 5's
        hex-only-token test alone would not (the digit breaks the
        hex-only match too, but this proves rule 4 is pulling real
        weight, not just rule 5 alone)."""
        line = "api_secret=Vault.decade0deadbeef"
        assert _neutralized(line) == line
        assert _vfs._is_non_secret_value("Vault.decade0deadbeef") is False
        spec = _write_func_spec(tmp_path, "LEAKED " + line)
        assert "func.secret_shape" in _rule_ids(spec, tmp_path)

    def test_invented_3_survives_word_glued_directly_to_hex_blob_no_underscore(self, tmp_path):
        """CONFIRMED RESIDUAL GAP: gluing a real word directly onto a
        16-char hex blob with NO underscore between them means the whole
        segment is a single token by the `_` split -- and that single
        token is not hex-only as a WHOLE (the word's non-`[a-f]` letters
        mask the blob riding on it), so rule 5 never fires. This is the
        same "trap" that defeats a whole-segment hex-only test, just
        without an underscore for rule 5's per-token split to exploit."""
        line = "secret_key=Store.tokendeadbeefcafebabe"
        neutralized = _neutralized(line)
        assert neutralized == "secret_key", (
            "documents the survival: the exemption incorrectly erases this "
            f"real secret, got {neutralized!r}"
        )
        assert _vfs._is_non_secret_value("Store.tokendeadbeefcafebabe") is True
        spec = _write_func_spec(tmp_path, "LEAKED " + line)
        assert "func.secret_shape" not in _rule_ids(spec, tmp_path), (
            "confirmed survivor -- see RESIDUAL LIMITATION note"
        )

    def test_invented_4_survives_hex_blob_chunked_under_the_8char_floor(self, tmp_path):
        """CONFIRMED RESIDUAL GAP: the same 16-char hex secret as
        `deadbeefcafebabe` (attack 6, which dies), but pre-chunked into
        four 4-char all-`[a-f]` underscore-joined tokens
        (`deaf`/`bead`/`face`/`cafe`) -- none individually reaches the
        8-char floor, so rule 5 misses every one of them even though the
        reassembled secret is a real 16-char hex blob."""
        line = "secret_key=Vault.deaf_bead_face_cafe"
        neutralized = _neutralized(line)
        assert neutralized == "secret_key", (
            "documents the survival: the exemption incorrectly erases this "
            f"real secret, got {neutralized!r}"
        )
        assert _vfs._is_non_secret_value("Vault.deaf_bead_face_cafe") is True
        spec = _write_func_spec(tmp_path, "LEAKED " + line)
        assert "func.secret_shape" not in _rule_ids(spec, tmp_path), (
            "confirmed survivor -- see RESIDUAL LIMITATION note"
        )
