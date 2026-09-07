# F001_Auth — Authentication

**Priority**: P0
**Type**: ui
**Generated**: 2026-05-18

## 1. Technical Overview

Authentication allows registered users to sign in.

## 2. Functional → Technical Mapping

| Code | Name | Where it is implemented | Technical notes | Source |
|------|------|--------------------------|------------------|--------|
| FR-001 | Validates credentials | `POST /login` via `LoginController::store` | | `app/Http/Controllers/LoginController.php:1-80` |

## 3. System Design

### 3.1 Components

None.

### 3.2 Data Model

#### Key Entities

| Entity | Table | Purpose |
|--------|-------|---------|
| User | users | Credential lookup |

#### Polymorphic Behavior

N/A — no discriminator fields in Key Entities.

### 3.3 State Management

See SM-001 below.

### The login state machine (SM-001)

The login state machine governs session transitions but the diagram fence has
been forgotten — this is the failure case that sm_mermaid must still catch.

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
| Empty password | HTTP 422 |

## 5. Verification & Technical Notes

### 5.1 Technical Verification

None.

#### US001_Login

**Independent Test:** POST /login returns 200.

**Acceptance Scenarios:**

1. **Given** valid credentials, **When** POST /login, **Then** token returned.

### 5.2 Assumptions

- bcrypt hashing.

### 5.3 Unresolved Questions

None.

### 5.4 Source References

| Symbol | Path | Purpose |
|--------|------|---------|
| LoginController | `app/Http/Controllers/LoginController.php:1-80` | Validation |

### 5.5 Artifact References

| Artifact | File | Codes Used | Reviewed |
|----------|------|------------|----------|
| System Overview | [system-overview.md](../../system-overview.md) | — | [x] |
| Feature List | [feature-list.md](../../feature-list.md) | F001_Auth | [x] |
| Route List | [route-list.md](../../route-list.md) | — | [ ] |
| Data Model | [data-model.md](../../data-model.md) | — | [ ] |
| Screen List | [screen-list.md](../../screen-list.md) | SCR001_LoginForm | [ ] |

**Rule:** Every code listed MUST exist in its source artifact. Orphan refs = reviewer critical.
