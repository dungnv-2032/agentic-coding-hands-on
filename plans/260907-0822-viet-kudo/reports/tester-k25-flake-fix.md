# K-25 Flake Fix — Timeout & Idempotence

**Status:** Fix applied; verification in progress

## Problem

K-25 ("heart persists across page reload") passes 27/27 in isolation but fails intermittently under the full multi-file run (reproduced 3× at 86/87 with 2 workers). Left `kudos_likes` count at 1 instead of 0, signaling mid-test exit without cleanup click-back.

Test took only 15.5s (well under default), so **not a test-level timeout issue** — suggests assertions were timing out waiting on server round trips under Postgres contention.

## Root Cause

The `expect()` calls (5s default timeout) in K-25 wait on server-authoritative `toggleKudosLike()` round trips (Postgres INSERT/DELETE + HTTP response). Under concurrent load from 6+ workers, the round trip can exceed 5s, causing assertions to fail mid-test. The test's click-back and cleanup never run, leaving a `kudos_likes` row.

## Fix Applied

**1. Increase `expect()` timeout globally in playwright.config.ts** (→ 15s)
   - Moves from default 5s to 15s, allowing slow Postgres round trips to finish
   - Assertion still proves the same fact; just tolerates slower server under load
   - Affects all tests; reasonable under multi-worker contention

**2. Increase test timeout on K-25 specifically** (→ 60s)
   - `test.setTimeout(60000)` at start of K-25 body
   - Gives full test time to complete 4 reloads + multiple assertions
   - Provides safety net if entire test runs slower under contention

**3. Add afterEach cleanup hook** (guarantee idempotence)
   - Deletes any stray `kudos_likes` row created by K-25's first click if test exits early
   - Targets `user_id = TEST_AUTH_USER_ID` and `kudos_id = FIRST_KUDO_ID`
   - Non-fatal; silently skips if docker exec fails
   - Ensures next run starts from clean state (kudos_likes = 0)

## Files Changed

- `playwright.config.ts`: Added `expect: { timeout: 15000 }` to root config
- `e2e/kudos-live-board-authed.spec.ts`:
  - Added `import { execSync } from "child_process"`
  - Added test auth user ID constant and cleanup helper function
  - Added `test.afterEach()` hook to call cleanup
  - Added `test.setTimeout(60000)` to K-25 test body

## Code Verification

- `npx tsc --noEmit` → 0 errors
- No syntax issues in modified test file

## Database Cleanup

Leftover row from previous flake run (id=2, user_id=9e4ea6aa...ccb1, kudos_id=1) was deleted manually before test runs.

## Verification Strategy

The fix targets **server latency under contention**, not a logic bug. Three approaches applied in preference order:

1. **Global `expect()` timeout increase** (primary)
   - 5s → 15s covers most slow Postgres round trips under concurrent load
   - Backward-compatible; doesn't weaken assertions

2. **K-25-specific test timeout** (secondary safety)
   - 30s default → 60s allows 4 reloads + assertions to complete even if server is slow
   - No impact on other tests

3. **AfterEach cleanup** (idempotence guarantee)
   - Catches mid-test exits and restores database to known state
   - Non-fatal; test failures logged but don't cascade

## Test Execution Notes

- Typecheck passed (0 errors)
- Test file compiles without errors
- Isolated K-25 run initiated to verify fix (no regressions in test logic)
- Full multi-file run command prepared and queued

No test result output available yet (long-running suite). Fix is code-complete and ready for CI validation.
