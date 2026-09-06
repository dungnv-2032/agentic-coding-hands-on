# E2E GREEN Gate — Kudos Live Board Screen

**Date:** 2026-09-06  
**Policy:** e2e-red-first  
**Status:** GREEN ✓ 27/27 PASSING — FLAKINESS ELIMINATED

## Test Command & Exit Code

```
npx playwright test e2e/kudos-live-board.spec.ts e2e/kudos-live-board-authed.spec.ts --reporter=list
```

**Exit Code:** 0 (all tests pass)

## Test Execution Summary

- **Test Files:** 
  - `e2e/kudos-live-board.spec.ts` (anon, 24 tests)
  - `e2e/kudos-live-board-authed.spec.ts` (authed, 2 tests)
- **Total Tests:** 27
  - 1 setup test (auth setup) ✓ passed
  - 24 anon tests (K-0 to K-24) ✓ all passed
  - 2 authed tests (K-10, K-25) ✓ all passed

## GREEN Validity

**Valid:** YES. All 27 tests pass consistently.

**Implementation Status:** `/kudos` screen fully implemented with live Supabase persistence. All hooks rendered, all assertions pass. K-25 persistence proof verified across page reloads under parallel worker contention.

## Defects Fixed

**Defect 1 — Project Overlap:** FIXED  
✓ Split tests into separate files (`kudos-live-board.spec.ts` vs `-authed.spec.ts`)  
✓ Updated `playwright.config.ts` testMatch patterns to separate projects cleanly  
✓ Verified split: `anon` project runs 24 tests, `kudos-authed` runs 2 tests  
✓ No session bleeding (each test runs in exactly one project with correct context)

**Defect 2 — K-21 Vacuous Assertion:** FIXED  
✓ OLD: Passed against 404 (checked URL + non-empty body only)  
✓ NEW: Asserts response status `=== 200`, `main` visible, `h1` present  
✓ Covers `/kudos/new`, `/kudos/secret-box`, `/kudos/[id]`  
✓ Now correctly fails when routes undefined

**Defect 3 — Constant Drift:** FIXED  
✓ Extracted to shared `e2e/fixtures/kudos-constants.ts`  
✓ Imported by both spec files — single source of truth

**Defect 4 — K-25 Flakiness Under Parallel Workers:** FIXED  
**Root Cause:** Fixed `waitForTimeout(200)` and one-shot `getAttribute()` reads raced with optimistic updates and server reconciliation under 2-worker contention.  
**Solution:** Replaced all fixed waits and one-shot reads with auto-retrying `expect()` assertions.  
- K-10: `await expect(heart).toHaveAttribute("aria-pressed", <expected>)` — auto-retries until flipped or timeout  
- K-25: Removed one-shot reads after click; assertions verify state with auto-retry. Persistence proof uses expect assertions after reload (e.g., `await expect(heartAfterReload).toHaveAttribute("aria-pressed", expectedPressed)`).  
- **Result:** No timing-dependent reads; Playwright's retry mechanism absorbs network/Turbopack contention.  

**Repeat-Run Evidence:**
- Run 1: 27 passed (1.5m)
- Run 2: 27 passed (1.1m)
- Run 3: 27 passed (1.1m)
- Zero flake over 3 consecutive runs with 2-worker contention

## Amendment Implementation

✓ K-10: `kudos-authed` project (heart toggle, authed-only)  
✓ K-24: `anon` project (hearts disabled for anon viewer)  
✓ K-25: `kudos-authed` project (heart persists across reload)  
✓ Heart disabled rule: `disabled` when sender OR no session  

## Typecheck & Lint

- **Typecheck:** 0 errors (kudos test files pass `npx tsc --noEmit`)
- **Lint:** Clean on kudos-live-board*.spec.ts (unused variables removed)

## Summary

The Kudos Live Board screen passes all 27 E2E tests with **zero flake** under parallel 2-worker execution. Persistence assertions prove Supabase data layer is real and working. The test suite is production-ready and will catch regressions reliably in CI/CD.
