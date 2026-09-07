---
authored_by: rebuild-spec
---
# F001_Auth

## 1. Overview

Authentication lets registered users sign in with an email and a password.

## 2. Open Decisions

None — no unresolved domain confirmations.

## 3. Requirements

No functional requirements are declared for this fixture.

## 4. Business Rules

No business rules are declared for this fixture.

## 5. Screens

N/A — background feature (no screens).

## 6. User Stories

Users sign in with an email and a password to reach the application.

## 7. Scenarios

Given valid credentials, the user signs in successfully.

## 8. Edge Cases

| Scenario | What Happens | User-Facing Message |
|----------|--------------|----------------------|
| Empty password submitted | Sign-in is rejected | "Password is required." |
| Wrong password submitted five times | Account is locked | "Account locked, try later." |
| Unknown email submitted | Sign-in is rejected | "Invalid email or password." |

## 9. Edge Behaviours to Verify

Behaviours are verified through the scenarios above.

## 10. Configuration

No configuration constants for this fixture.
