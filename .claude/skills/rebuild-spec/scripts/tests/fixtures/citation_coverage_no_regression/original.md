---
authored_by: rebuild-spec
---
<!-- Synthetic fixture (phase-08 citation-coverage integrity). NOT real corpus content —
structurally mirrors the real F011_ListingModeration technical-spec.md shape (pre
action-thread) with fictional names/paths, per "work on a copy, never commit corpus
content" from plans/260824-1128-rebuild-spec-action-thread-v27-7/phase-08. -->

# Technical Spec — F900_SyntheticThing

## 1. Technical Overview

A single controller backs the whole screen.

## 2. Functional → Technical Mapping

| Code | Name | Where it is implemented | Technical notes | Source |
|------|------|--------------------------|-------------------|--------|
| FR-001 | Admin updates the thing | `ThingController#update` | guarded | `app/controllers/thing_controller.rb:5` |
| FR-002 | Admin closes the thing | `ThingController#close` | no soft-delete | `app/controllers/thing_controller.rb:12` |

## 4. Technical Behavior by Capability

### 4.1 Manage the thing

**Business Rules**

### Update only applies while pending (BR-001)
**Linked FR:** FR-001
**Source:** `app/services/thing_service.rb:10-20`
**Applies to:** `#update` action

### Close write-site not pinned down (BR-002)
**Linked FR:** FR-002
[INFERRED] the exact close write site could not be pinpointed from static reading alone
**Applies to:** `#close` action

## 5. Verification & Technical Notes

### 5.4 Source References

| Order | Symbol | Path | Purpose |
|-------|--------|------|---------|
| 1 | ThingController | `app/controllers/thing_controller.rb:1-40` | HTTP entry points |
| 2 | ThingService | `app/services/thing_service.rb:1-60` | business logic |

## Source Walkthrough

1. **File:** `app/models/thing.rb:1-20` — start here: defines the entity.
2. **File:** `app/controllers/thing_controller.rb:1-40` — next: the entry point.

## DB Impact per Event

| Event/Endpoint | Table | Columns | Operation | Value Derivation | Source |
|----------------|-------|---------|-----------|-------------------|--------|
| PATCH .../update | `things` | value | UPDATE | literal from param | `app/services/thing_service.rb:10-20` |
| PATCH .../close | `things` | closed | UPDATE | literal true | `app/services/thing_service.rb:25-27` |
