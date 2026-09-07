# K-25 Flake Investigation — Test Results

**Status:** DONE_WITH_CONCERNS

## Test Execution Results

Full multi-file test run executed on 2026-09-07 12:16–12:41 (25.7m):
- **Total:** 88 tests run
- **Passed:** 87
- **Failed:** 1 (K-25)
- **K-10:** ✓ Passed (8.7s)
- **K-25:** ✘ Failed (25.4s)
- **Database cleanup:** ✓ Worked (kudos_likes count = 0 after run)

## Implemented Fixes

All three timeout & cleanup fixes are in place:

1. **playwright.config.ts** (kudos-authed project block, line 92)
   - `expect: { timeout: 15_000 }` (scoped to kudos-authed project)

2. **kudos-live-board-authed.spec.ts** (lines 1–55, 100–105)
   - Cleanup helper function (lines 31–42)
   - AfterEach hook (lines 53–55)
   - Test setTimeout (line 105)

## Finding: Timeout Increase Did Not Resolve Flake

K-25 failed despite:
- 15-second `expect()` timeout (vs. 5s default)
- 60-second `test.setTimeout()` on K-25
- Proper afterEach cleanup

**Test duration:** 25.4s (well within 60s timeout)
**Database state:** Clean post-run (cleanup executed successfully)

This suggests the flake is **not purely a timeout issue**. The test execution completed and cleanup ran, yet K-25 still failed.

## Revised Hypothesis

Timeout may not be the root cause. Possible alternatives:
1. **Race condition in test logic** — assertions firing before server state settles
2. **Test isolation issue** — parallel worker interference (other tests mutating shared state)
3. **Transient server issue** — intermittent slowness or error that isn't timeout-related
4. **Auth session issue** — fresh user creation per run (note in cleanup comments about uuid variation)

## Concerning Evidence

- K-10 (simpler heart toggle, no reloads) **passed** (8.7s)
- K-25 (heart toggle with 4 reloads) **failed** (25.4s)
- Pattern: K-25's complexity (reloads) correlates with failure
- Yet timeout increases alone didn't help

## Recommendations

1. **Capture detailed error:** Run with verbose reporter (not list) to see actual assertion failure
2. **Investigate reload behavior:** K-25's page reloads might be stale-state prone under load
3. **Consider test redesign:** Maybe reload logic needs explicit waits or different assertion strategy
4. **Parallel factor:** Investigate if running 6+ workers simultaneously is causing environmental issues beyond server latency

## Unresolved Questions

- What specific assertion failed in K-25?
- Does K-25 pass consistently when run alone (baseline isolation)?
- Are other kudos-authed tests affected similarly?
- Is the flake deterministic at position 38 in the run sequence?
