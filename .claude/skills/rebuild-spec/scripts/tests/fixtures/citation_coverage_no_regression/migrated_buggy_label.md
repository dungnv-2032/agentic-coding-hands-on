---
authored_by: rebuild-spec
---
<!-- Synthetic fixture (phase-08 citation-coverage integrity) — NEGATIVE CONTROL, never
authored by the shipped template. Same as migrated_correct.md except the two Source rungs
use the B-v sample rev2's original candidate shape (`**Source** · ...`, no colon inside
the bold, middot before the citation) instead of the settled `**Source:**` form. This file
exists ONLY to prove, by running the real regex, that shipping that shape would silently
drop citation coverage corpus-wide — it must never be copied into a template or composer. -->

# Technical Spec — F900_SyntheticThing

## 1. Technical Overview

A single controller backs the whole screen.

## 2. Action Index

| # | Action (handler) | Method · Path | Codes | Writes | Detail |
|---|---|---|---|---|---|
| **A1** | `ThingController#update` | `PATCH` `.../update` | FR-001, BR-001 | `things` | § 3.1 |
| **A2** | `ThingController#close` | `PATCH` `.../close` | FR-002, BR-002 | `things` | § 3.1 |

## 3 Actions

### 3.1 CAP-01 — Manage the thing

#### A1 · Update the thing
`PATCH .../update` → `ThingController#update`
`FR-001` `BR-001`

**Who** · Marketplace admin
**FE** · `index.haml:1-10` renders the update form.
**Request** · param `value`
**BE** · `ThingController#update` calls `ThingService#apply`.
**Rule** · update only applies while pending (BR-001).
**Result** · updates `things.value`.
**Source** · `app/services/thing_service.rb:10-20` → `app/controllers/thing_controller.rb:5`

#### A2 · Close the thing
`PATCH .../close` → `ThingController#close`
`FR-002` `BR-002`

**Who** · Marketplace admin
**FE** · `index.haml:12-18` renders the close button.
**Request** · none
**BE** · `ThingController#close` calls `ThingService#close`.
**Rule** · [INFERRED] the exact close write site could not be pinpointed from static reading alone (BR-002).
**Result** · closes the thing.
**Source** · `app/services/thing_service.rb:25-27`

## 5. Verification & Technical Notes

### 5.4 Source References

| Action | Order | Symbol | Path | Purpose |
|--------|-------|--------|------|---------|
| A1, A2 | 1 | ThingController | `app/controllers/thing_controller.rb:1-40` | HTTP entry points |
| A1, A2 | 2 | ThingService | `app/services/thing_service.rb:1-60` | business logic |

## Source Walkthrough

1. **File:** `app/models/thing.rb:1-20` — start here: defines the entity.
2. **File:** `app/controllers/thing_controller.rb:1-40` — next: the entry point.

## DB Impact per Event

| Action | Event/Endpoint | Table | Columns | Operation | Value Derivation | Source |
|--------|----------------|-------|---------|-----------|-------------------|--------|
| A1 | PATCH .../update | `things` | value | UPDATE | literal from param | `app/services/thing_service.rb:10-20` |
| A2 | PATCH .../close | `things` | closed | UPDATE | literal true | `app/services/thing_service.rb:25-27` |
