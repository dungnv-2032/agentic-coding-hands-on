"""Integration test for phase-05 (B4c): `compose_mode_a` derives `docs_root` from
`feature_dir` itself (`feature_dir.parent.parent`), builds the SCR### index from a
REAL `generated/screen-list.md` Screen Index, and threads resolved/unbound screens
through to `validate_feature_spec.py` with the expected result -- zero
`func.screens_scr_unresolved` criticals, an Unbound Screens block for the L3 residue,
and one continuous § 2 Open Decisions series. Self-contained fixtures (own tmp_path
tree) so this never touches the shared `v26-valid-content`/`real-corpus-f001-auth`
fixtures other phases' tests own. See
plans/260817-1420-rebuild-spec-v27-migrate-legacy-docs/phase-05-screen-binding-degradation.md
(T18: "real F001_Auth compose -> validate: zero criticals of any class").
"""
from __future__ import annotations

import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _TESTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from _audience_split_compose_a_lib import compose_mode_a  # noqa: E402

_TECH_SPEC = """---
authored_by: rebuild-spec
---
# F900_ScreenBindTest

**Priority**: P2
**Type**: ui
**Generated**: 2026-01-01

## Overview

A minimal feature exercising the screen-binding ladder end to end.

## Polymorphic Behavior

None.

## Cross-Cutting Logic

**Client behavior:** N/A.

### Requirements

| Code | Description | Endpoint/Handler | Verifiable |
|------|-------------|------------------|------------|
| FR-001 | The system shows a login form. | LoginController.show | yes |

### Business Rules

None.

### Decision Logic

None.

### State Machines

None.

### Algorithms

None.

### External Integrations

None.

### Verification

- **SC-001** login form renders (covers FR-001)

---

## User Stories

### US001_SignIn — Sign in (Priority: P1)

**What happens:** A user signs in.

**Acceptance Scenarios:**

1. **Given** a user, **When** they submit, **Then** they sign in.

**Requirements fulfilled:**
- **FR-001** The system shows a login form. — `GET /login` via `LoginController::show`
  **Source:** `app/Controllers/LoginController.php:10-18`

## Key Entities

| Entity | Table | Key Columns | Purpose |
|--------|-------|-------------|---------|
| Account | `accounts` | id | credentials |

## Artifact References

| Artifact | File | Codes Used | Reviewed |
|----------|------|------------|----------|
| System Overview | [system-overview.md](../../docs/system/system-overview.md) | — | [x] |

## Assumptions

None.

## Source Code References

| Order | Symbol | Path | Purpose |
|-------|--------|------|---------|
| 1 | LoginController | `app/Controllers/LoginController.php:1-20` | handles sign-in |

## Unresolved Questions

None.
"""

_BUSINESS_CONTEXT = """---
authored_by: rebuild-spec
---
# Business Context — F900_ScreenBindTest

## Why It Matters

Users need to sign in.

## Who Uses It

- **Member** — signs in

## What They Do

1. User submits credentials.

## Unresolved Questions

None.
"""

_EDGE_CASES = """---
authored_by: rebuild-spec
---
# Edge Cases — F900_ScreenBindTest

| Scenario | What Happens | User-Facing Message |
|----------|--------------|----------------------|
| Empty password | Rejected | "Password required." |
| Wrong password | Rejected | "Invalid credentials." |
| Unknown email | Rejected | "Invalid credentials." |
"""

# Real-shape v26 screens.md: 3-column, no SCR code -- one L1-resolvable row, one
# L3-unresolvable row (mirrors the real F001_Auth "Access Denied" case: same literal
# text as a differently-scoped Screen Index entry must NOT collide).
_SCREENS = """---
authored_by: rebuild-spec
---
# Screens — F900_ScreenBindTest

## Screen List

| Screen Name | What User Sees | What User Can Do |
|-------------|-----------------|-------------------|
| Login Page | An email and password form | Submit credentials |
| Access Denied | Message explaining denial | Read explanation |

## User Journey

User arrives at Login Page, submits, lands on dashboard.
"""

_SCREEN_INDEX = """# Screen List

## Screen Index

| Code | Name | Auth | Controller#Action | Route |
|------|------|------|--------------------|-------|
| SCR020_LoginPage | Login Page | pub | sessions#new | GET /login |
| SCR028_AccessDenied | Access Denied (invite-only) | pub | community_memberships#access_denied | GET /community_memberships/access_denied |
"""


def _write_feature(docs_root: Path) -> Path:
    feature_dir = docs_root / "features" / "F900_ScreenBindTest"
    feature_dir.mkdir(parents=True)
    (feature_dir / "business-context.md").write_text(_BUSINESS_CONTEXT, encoding="utf-8")
    (feature_dir / "screens.md").write_text(_SCREENS, encoding="utf-8")
    (feature_dir / "edge-cases.md").write_text(_EDGE_CASES, encoding="utf-8")
    (feature_dir / "technical-spec.md").write_text(_TECH_SPEC, encoding="utf-8")
    (docs_root / "generated").mkdir(parents=True, exist_ok=True)
    (docs_root / "generated" / "screen-list.md").write_text(_SCREEN_INDEX, encoding="utf-8")
    return feature_dir


def test_compose_resolves_login_page_and_degrades_access_denied(tmp_path):
    docs_root = tmp_path / "docs"
    feature_dir = _write_feature(docs_root)

    composed = compose_mode_a(feature_dir)
    func_spec = composed["functional-spec.md"]

    assert "| Login Page | SCR020 |" in func_spec
    assert "### Unbound Screens" in func_spec
    assert "**Access Denied**" in func_spec
    # The anti-fuzzy / asymmetric-fold guarantee: Access Denied must NOT have picked
    # up SCR028 (that would be a wrong binding to a different, invite-only screen).
    screens_section = func_spec.split("## 5. Screens")[1].split("## 6.")[0]
    assert "SCR028" not in screens_section
    assert '| D001 | Screen "Access Denied" has no SCR### binding |' in func_spec


def test_compose_then_validate_zero_screens_criticals(tmp_path):
    from _audience_split_migrate_lib import validate_feature_dir

    docs_root = tmp_path / "docs"
    feature_dir = _write_feature(docs_root)
    composed = compose_mode_a(feature_dir)

    staged = tmp_path / "_staging" / "F900_ScreenBindTest"
    staged.mkdir(parents=True)
    for name, content in composed.items():
        (staged / name).write_text(content, encoding="utf-8")

    _ok, issues = validate_feature_dir(staged, tmp_path)
    critical = [i for i in issues if i.get("severity") == "critical"]
    rule_ids = {i["rule_id"] for i in critical}
    assert "func.screens_scr_unresolved" not in rule_ids, critical
