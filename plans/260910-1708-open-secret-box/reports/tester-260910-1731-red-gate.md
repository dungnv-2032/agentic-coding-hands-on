# Tester Report — Phase 01 RED E2E Gate

**Status:** DONE (with valid RED evidence)  
**Date:** 2026-09-10  
**Phase:** 01 — Strict RED e2e gate  
**Test Policy:** `e2e-red-first`

## Summary

Created and executed the screen-level E2E test suite for the Secret Box feature (`/kudos/secret-box`). The test suite collected (9 authed + 4 anon = 13 tests) and ran against the current implementation (which still renders `<ComingSoon />`), producing a **valid RED exit** from screen assertion failures.

## Deliverables Completed

✓ **Test Files Created:**
- `e2e/secret-box.spec.ts` — 9 authed tests (SB-01..SB-09)
- `e2e/secret-box-anon.spec.ts` — 4 anon tests (SB-A1..SB-A4)
- `e2e/secret-box-auth.setup.ts` — Independent session setup
- `e2e/fixtures/secret-box-constants.ts` — Test IDs, strings, geometry
- `e2e/fixtures/secret-box-grant.ts` — Service-role grant fixture (setUnopenedCount, readCounters, ensureSunner)

✓ **Config Updates:**
- `playwright.config.ts` — Added `secret-box-auth-setup` and `secret-box-authed` projects
- `playwright.config.ts` — Updated setup project regex to exclude `(?!secret-box)`
- `playwright.config.ts` — Added `secret-box-anon` to anon project's testMatch alternation
- `e2e/fixtures/supabase-session.ts` — Added `userId` return value (additive, backwards compatible)

✓ **Evidence Recorded:**
- `plans/260910-1708-open-secret-box/evidence/red-evidence.md` — Full RED details with commands, exit codes, and assertion failures

## Test Coverage

### Authed Suite (SB-01..SB-09)

| ID | Test | FR/BR Codes |
|----|------|-------------|
| SB-01 | Render with title, instruction, count 05 | FR-001, FR-101, FR-102, FR-104 |
| SB-02 | Box visible and operable | FR-103, FR-202 |
| SB-03 | Click opens badge, counter decrements | FR-201, BR-002, BR-005 |
| SB-04 | Double-click race rejected | FR-203, SM-001 |
| SB-05 | Persistence after reload | BR-001 |
| SB-06 | At count 0, instruction hides, opener disables | FR-102, FR-202 |
| SB-07 | Concurrent opens resolve to one success | BR-004, FR-602, R1 |
| SB-08 | Direct updates and forged RPC rejected | FR-601, 5cc072ad, 2e7bec78 |
| SB-09 | Close button navigation | FR-301 |

### Anon Suite (SB-A1..SB-A4)

| ID | Test | FR/BR Codes |
|----|------|-------------|
| SB-A1 | Route 200, main h1 visible, title correct | FR-001, FR-101 |
| SB-A2 | Counter 00, instruction hidden, opener disabled, sign-in link | FR-105, FR-202 |
| SB-A3 | Anon RPC refused | PERM018 |
| SB-A4 | Geometry at 1440×1024 | design contract |

## RED Evidence

**Gate Command:** `npx playwright test e2e/secret-box.spec.ts --project=secret-box-authed`

**Exit Code:** Non-zero (tests failed)

**First Failure:** SB-01 — Locator timeout waiting for `main h1` element  
- **Type:** Screen assertion (not environment, not config)
- **Reason:** `/kudos/secret-box` still renders `<ComingSoon />`, which lacks all expected elements
- **Legitimacy:** Valid RED — screen must be implemented before tests pass

**Collection Gate Passed:**
```
Authed suite: 10 tests collected (1 setup + 9 authed) ✓
Anon suite: 5 tests collected (1 setup + 4 anon) ✓
Setup regex fix verified: setup-project runs exactly once per suite ✓
```

## Setup Verification

The `secret-box-auth.setup.ts` successfully:
1. Created an authenticated test user via `createTestSession()`
2. Provisioned a `sunners` row with `Unassigned` department
3. Wrote storageState to `e2e/.auth/secret-box-user.json`
4. Wrote credentials to `e2e/.auth/secret-box-credentials.json`

Test output:
```
✓ Secret Box session created and saved to e2e/.auth/secret-box-user.json
  Test user email: e2e-1789036713738-233724-2vpj8r@example.com
  Test user ID: 3a1f1720-5fe0-44e1-8d4f-71b44470d4e9
  Sunner ID: 14
  Auth token cookie: sb-127-auth-token
```

## Compatibility Check

✓ Ran authed tests against existing suites (smoke, profile, kudos) — no regressions  
✓ `supabase-session.ts` change (added `userId`) is backwards compatible — all existing callers destructure by name  
✓ Config changes are additive — existing projects unchanged  

## Known Limitations (Not Blocking)

- Anon test SB-A3 (RPC permission check) assumes `secret_box_openings` table exists (will be created in phase 03)
- Anon test SB-A4 (geometry) uses `boundingBox()` which may differ slightly under fractional scaling
- Concurrent RPC test (SB-07) assumes batched execution; actual concurrency depends on browser DevTools protocol timing

## Unresolved Questions

None. All 14 clarifications are implemented in the test suite and fixtures.

---

**Phase 01 Status:** COMPLETE  
**Ready for Phase 02:** YES — Product implementation may proceed after this valid RED is recorded.  
**Blocker Status:** None  

Phases 02 and 03 may start immediately. Phase 07 will re-run these exact commands and require GREEN.
