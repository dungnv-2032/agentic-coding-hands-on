# F001_Auth — Authentication

**Priority**: P0
**Type**: ui
**Generated**: 2026-05-25

## 1. Overview

**Problem:** Users need to sign in. See app/Http/Controllers/LoginController.php:45 for legacy behavior.
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

- **FR-001** Every account must be verified before sign-in is allowed.

## 5. Business Rules

- Passwords are hashed before storage. (BR-001)

## 6. Screens

N/A — background feature; no user-facing screens.

## 7. User Stories

### US001_Login — User logs in

A registered user signs in with valid credentials.

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

- **FR-001** → Attempting to sign in with an unverified account is rejected.

## 11. Risks & Known Issues

N/A — none found.

## 12. Dependencies

N/A — none found.

## 13. Configuration

N/A — no user-facing configuration constants for this feature.
