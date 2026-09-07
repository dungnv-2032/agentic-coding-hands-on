# F001_Auth — Authentication

**Priority**: P0
**Type**: ui
**Generated**: 2026-05-16

## 1. Technical Overview

Authentication allows registered users to sign in with email and password.

## 2. Functional → Technical Mapping

| Code | Name | Where it is implemented | Technical notes | Source |
|------|------|--------------------------|------------------|--------|
| FR-001 | Validates credentials | `POST /login` via `LoginController::store` | | `app/Http/Controllers/LoginController.php:1-80` |

## 3. System Design

### 3.1 Components

None.

### 3.2 Data Model

#### Key Entities

| Entity | Table | Key Columns | Purpose |
|--------|-------|-------------|---------|
| User | users | id, email, password_hash | Credential lookup |
| Session | sessions | id, user_id, token | Token storage |
| LoginAttempt | login_attempts | id, email, ip | Brute-force tracking |

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

| Scenario | Behavior |
|----------|----------|
| Empty password | HTTP 422: "The password field is required." |
| Invalid email | HTTP 422: "The email must be a valid email address." |
| Unknown email | HTTP 401: "Invalid credentials." |

## Requirements

<!-- v27.0.0: this top-level ## Requirements is a retired 9-section-shape H2 —
must trigger FeatureSpec.deprecated_headings even though the rest of this
fixture is otherwise on the new 5-bucket shape. -->

- FR-001: System validates credentials
- FR-002: System issues session token

## 5. Verification & Technical Notes

### 5.1 Technical Verification

- **SC-001** login succeeds (covers FR-001)

#### US001_Login

**Independent Test:** POST /login with valid credentials returns 200.

**Acceptance Scenarios:**

1. **Given** a registered user, **When** they POST valid credentials, **Then** they receive HTTP 200.
2. **Given** invalid credentials, **When** they POST to /login, **Then** they receive HTTP 401.
3. **Given** empty password, **When** they POST to /login, **Then** they receive HTTP 422.

### 5.2 Assumptions

- Password hashing uses bcrypt.
- Sessions expire after 24 hours.

### 5.3 Unresolved Questions

1. **Token expiry**: Is 24h session lifetime configurable per environment?

### 5.4 Source References

| Symbol | Path | Purpose |
|--------|------|---------|
| LoginController | `app/Http/Controllers/LoginController.php:1-80` | Credential validation |
| User | `app/Models/User.php:1-50` | User entity |
| Session | `app/Models/Session.php:1-30` | Session storage |

### 5.5 Artifact References

| Artifact | File | Codes Used | Reviewed |
|----------|------|------------|----------|
| System Overview | [system-overview.md](../../system-overview.md) | — | [x] |
| Feature List | [feature-list.md](../../feature-list.md) | F001_Auth | [x] |
| Route List | [route-list.md](../../route-list.md) | POST /login | [ ] |
| Data Model | [data-model.md](../../data-model.md) | User | [ ] |
| Screen List | [screen-list.md](../../screen-list.md) | SCR001_LoginForm | [ ] |

**Rule:** Every code listed MUST exist in its source artifact. Orphan refs = reviewer critical.
