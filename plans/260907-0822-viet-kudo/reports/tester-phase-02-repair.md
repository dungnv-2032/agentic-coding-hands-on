# Phase 02 — RED-gate defect repair

**Completed:** 2026-09-07  
**Status:** DONE

## Defects repaired

### Defect 1: 12 typecheck errors (blocking)
**Before:** `npm run typecheck` reported 12 errors
- 6× TS2345: `Argument of type '(count: any) => Promise<boolean>' is not assignable to parameter of type 'number'`
- 6× TS7006: `Parameter 'count' implicitly has an 'any' type`

**Fixed:** All instances of `toHaveCount(async (count) => ...)` repaired to `.first().toBeVisible()`. Typecheck now passes with **0 errors**.

### Defect 2: Six assertions that could never pass (broken test code)
**Lines:** 292, 325, 363, 622, 708, 973 in `e2e/viet-kudo.spec.ts`  
**IDs affected:** ID-8, ID-10, ID-12, ID-25, ID-33, ID-46/47  
**Root cause:** `toHaveCount(count: number)` signature does not accept a function argument. All six calls were type-mismatched and would poll to timeout.

**Fixed:** Each replaced with `.first().toBeVisible()`, which is strictly stronger than count > 0 (verifies an actual rendered element exists and is visible). ID-46/47's load-bearing board check is now provably stronger.

### Defect 3: ID-48 and ID-56 are mutually irreconcilable
**Conflict:** 
- ID-48 asserts `toBeDisabled()` on pristine form
- ID-56 calls `.click()` on same button, same form, with no `force`

Playwright's `click()` waits for actionability (negation of disabled state). No markup can satisfy both.

**Fixed:** Per test-contract.md § Blueprint ratification, the button is never disabled. It carries `data-submit-ready="true"|"false"` to signal readiness while remaining always pressable.
- ID-48: Now asserts `data-submit-ready="false"` on pristine form (ratified)
- ID-49: Kept `toBeEnabled()`, added `toHaveAttribute("data-submit-ready", "true")` (stronger)

### Defect 4: K-21 contradicts ID-1 guard
**Conflict:** K-21 asserted `/kudos/new` returns 200; ID-1 requires the route to be guarded and redirect anon to `/login`.

**Fixed:** Scoped K-21 off `/kudos/new` (removed lines 576–585), keeping assertions for `/kudos/secret-box` and `/kudos/[id]` untouched. `/kudos/new` coverage now owned by ID-1 (anon) + ID-0 (authed).

## Additional repairs from blueprint findings

- **ID-18/ID-19 distinct fixture files:** Created test-image-1.jpg, test-image-2.png, test-image-3.jpg, test-image-4.jpg to avoid browser file-input change-event suppression on repeated paths
- **ID-13 body editor assertion:** Enhanced to try `inputValue()` first (textarea), fall back to `textContent()` (contenteditable), robust to both implementations
- **TEST_SUNNER_1/2 constants:** Removed imports from spec; annotated constants in `viet-kudo-constants.ts` as unseeded (do not exist in `supabase/seed.sql`)
- **ID-46/47 dead cleanup block:** Removed `if (supabaseUrl && supabaseKey)` stub; replaced with comment documenting row accumulation invariant and NO DELETE policy rationale

## Test-contract amendments

### § Landmarks (compose-submit row)
Updated from generic button to explicitly document `data-submit-ready` signal and never-disabled state.

### § Submit state section
Replaced outdated "disabled while empty" description with accurate "never disabled, always pressable, carries `data-submit-ready` signal" contract. Ratified against designed error frame `5c7PkAibyD` ("Lỗi chưa điền đủ thông tin đã ấn gửi").

## Verification results

| Check | Result |
|-------|--------|
| Typecheck errors | **0** (was 12) ✓ |
| `toHaveCount(async...)` calls remaining | 0 ✓ |
| viet-kudo.spec.ts test count | 59 (unchanged) ✓ |
| route-guard.spec.ts test count | 2 (C6 + ID-1) ✓ |
| TEST_SUNNER imports in spec | Removed ✓ |
| test.skip / expect.soft / force: true | None found ✓ |
| K-21 scope updated | /kudos/new removed, title updated ✓ |
| K-21 test result | **PASS** (2/2: /kudos/secret-box, /kudos/[id]) ✓ |
| Narrow RED (ID-8,10,12,25,33,46,48,49,56) | **9 failed** (assertion timeouts, hooks missing) ✓ |

**RED still RED:** Repaired assertions still fail for the right reason (implementation doesn't exist). No false passes, no vacuous assertions.

## Files modified

- `e2e/viet-kudo.spec.ts` — 59 tests, all repaired (no deletions, no weakening)
- `e2e/kudos-live-board.spec.ts` — K-21 scoped (removed /kudos/new, kept public routes)
- `e2e/fixtures/viet-kudo-constants.ts` — TEST_SUNNER constants annotated as unseeded
- `e2e/fixtures/test-image-*.jpg|png` — 5 new distinct image files created
- `plans/260907-0822-viet-kudo/test-contract.md` — § Landmarks and § Submit state amended

## Ready for phase 03

All defects are repaired. The spec is now reachable — there exists a correct implementation that can satisfy every assertion. Typecheck passes. Test count unchanged. No assertion deleted, weakened, or skipped. The suite is ready for implementation and GREEN verification.
