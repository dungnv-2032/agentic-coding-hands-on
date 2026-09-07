---
authored_by: rebuild-spec
---
<!-- Contract: references/feature-spec-researcher-contract.md -->

# F999_BackfillPending — Functional Spec

**Priority**: P2

**See also:** [`technical-spec.md`](./technical-spec.md) — implementation detail for an
engineering audience.

## 1. Overview

A moderator approves or rejects a pending listing. Hand-authored SYNTHETIC twin for the
`backfill-pending` fixture (C1 proof obligation #1) — minimal, not corpus-derived; every
`FeatureSpec.*` finding it produces is out of scope for this fixture's purpose (only
`FeatureSpec.state_rung_missing` on the technical-spec.md twin matters).

## 2. Functional Capabilities

### CAP-01 — Moderate a listing

Approve or reject a pending listing.

## 3. Open Decisions

None.

## 4. Requirements

- **FR-001** Only a moderator can reach the moderation screen.
- **FR-201** A pending listing can be approved by a moderator.

## 5. Business Rules

- **BR-001** Approve only applies while the listing is pending.

## 6. Screens

### SCR001_ListingModeration

The moderation queue screen.

## 7. User Stories

None declared for this synthetic fixture.

## 8. Scenarios

1. **Given** a pending listing, **When** a moderator approves it, **Then** its state
   becomes `approved`.

## 9. Edge Cases

| Scenario | Behavior |
|----------|----------|
| Listing is already approved | Approve is a no-op guard raises `InvalidTransition` |

## 10. Edge Behaviours to Verify

- Approving a non-pending listing must not silently succeed.

## 11. Risks & Known Issues

None.

## 12. Dependencies

None.

## 13. Configuration

N/A — no technical configuration beyond framework defaults.
