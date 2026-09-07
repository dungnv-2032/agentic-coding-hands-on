# F001_Auth — Authentication

## Overview
Auth feature.

## Polymorphic Behavior
N/A — no discriminator fields in Key Entities.

## Cross-Cutting Logic

### Requirements
None.

### Business Rules
See BR-001 below.

### Passwords are hashed before storage (BR-001)
**Linked FR:** FR-001
**Source:** `claude/skills/rebuild-spec/scripts/tests/fixtures/cited-source.py:1-3`
**Applies to:** User

**Pseudocode:**
```text
hash(password)
```

### Decision Logic
N/A — no user-facing decision logic beyond DISC-### Polymorphic Behavior.

### State Machines
None.

### Algorithms
None.

### External Integrations
None.

### Verification
None.

---

**Client behavior:** see behavior-logic.md, permissions.md, screen-flow.md

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
**Source:** `claude/skills/rebuild-spec/scripts/tests/fixtures/cited-source.py:1-3`

## Unresolved Questions
None.
