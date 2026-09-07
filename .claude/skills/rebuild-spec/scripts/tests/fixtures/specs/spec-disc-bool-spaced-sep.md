# F001_Auth — Authentication

**Priority**: P0
**Type**: ui
**Generated**: 2026-05-16

## 1. Technical Overview

Authentication allows registered users to sign in with email and password.
The system validates credentials and issues a session token.
It touches the User model, sessions table, and the login controller.

## 2. Functional → Technical Mapping

| Code | Name | Where it is implemented | Technical notes | Source |
|------|------|--------------------------|------------------|--------|
| FR-001 | System validates credentials | `POST /login` via `LoginController::store` | | `claude/skills/rebuild-spec/scripts/tests/fixtures/cited-source.py:5-10` |

## 3. System Design

### 3.1 Components

None.

### 3.2 Data Model

#### Key Entities

| Entity | Table | Key Columns | Purpose |
|--------|-------|-------------|---------|
| User | users | id, email, password_hash, status | Credential lookup |
| Session | sessions | id, user_id, token, expires_at | Token storage |
| LoginAttempt | login_attempts | id, email, ip, created_at | Brute-force tracking |

#### Polymorphic Behavior

##### DISC-001

| Value | Behavior |
| --- | --- |
| true | Show active banner |
| false | Hide banner |

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
| Empty password submitted | HTTP 422: "The password field is required." |

## 5. Verification & Technical Notes

### 5.1 Technical Verification

- **SC-001** login succeeds with valid credentials (covers FR-001)

#### US001_Login

**Independent Test:** POST /login with valid credentials returns 200 and session token.

**Acceptance Scenarios:**

1. **Given** a registered user with valid credentials, **When** they POST to /login, **Then** they receive HTTP 200.
2. **Given** an unregistered email, **When** they POST to /login, **Then** they receive HTTP 401.
3. **Given** a valid email but wrong password, **When** they POST to /login, **Then** they receive HTTP 401.

### 5.2 Assumptions

- Password hashing uses bcrypt with cost factor 12.
- Session tokens are 64-byte random hex strings.

### 5.3 Unresolved Questions

1. **Token expiry**: Is 24h the intended session lifetime or is it configurable?

### 5.4 Source References

| Symbol | Path | Purpose |
|--------|------|---------|
| authenticate | `claude/skills/rebuild-spec/scripts/tests/fixtures/cited-source.py:5-10` | Credential validation logic |
| find_user_by_email | `claude/skills/rebuild-spec/scripts/tests/fixtures/cited-source.py:13-15` | User lookup by email |
| create_session | `claude/skills/rebuild-spec/scripts/tests/fixtures/cited-source.py:23-27` | Session token generation |

### 5.5 Artifact References

| Artifact | File | Codes Used | Reviewed |
|----------|------|------------|----------|
| System Overview | [system-overview.md](../../system-overview.md) | — | [x] |
| Feature List | [feature-list.md](../../feature-list.md) | F001_Auth | [x] |
| Route List | [route-list.md](../../route-list.md) | POST /login | [ ] |
| Data Model | [data-model.md](../../data-model.md) | User | [ ] |
| Screen List | [screen-list.md](../../screen-list.md) | SCR001_LoginForm | [ ] |
