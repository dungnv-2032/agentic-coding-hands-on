# F008 Floating Action Button — a passing gate that wasn't, and three hidden defects

**Date**: 2026-09-10 (session 2026-09-10 08:00 → 2026-09-10 16:22 +07)
**Severity**: high
**Component**: `app/_components/floating-widget.tsx`, `e2e/floating-action-button.spec.ts`, accessibility & focus handling
**Status**: resolved

## What Happened

Delivered F008 Floating Action Button — the homepage's fixed bottom-right pill converted from two direct links into a disclosure trigger revealing a three-item menu: Thể lệ, Viết KUDOS, and a red `Hủy` close button. The design's own navigation edge (`313:9138` → `313:9139`) settles it: the pill is a trigger, not a pair of destinations. Five phases, test policy `e2e-red-first`, all reported passing and gates green. Then the post-review session (same calendar day, afternoon) ran a second pass and caught three things the first session had missed — and one real behavior defect the test suite never caught.

Final state after corrections: `npx playwright test e2e/floating-action-button.spec.ts --project=anon` → **9 passed** (8 FAB acceptance + 1 setup), exit 0; regression suites green (`the-le.spec.ts` 10 passed / 2 skipped, `homepage.spec.ts` 22 passed); `npm run typecheck` exit 0 with **no output** (verified, not assumed); `npm run lint` 0 errors, 29 warnings pre-existing.

## The Brutal Truth

The same typecheck-masking failure as F007, one week later, in the same repo. **`npm run typecheck` reported exit 0 while it was compiling broken code.** Sixty-four TypeScript errors, every line from `e2e/capture-fab-visuals.spec.ts` — throwaway capture scaffolding that was compiled by `tsc` but never selected by the Playwright suite runner. It was invisible to the test, fatal to the gate. This is genuinely maddening because the F007 entry was written *seven days ago* with the exact lesson: *"On this repo, a green typecheck after any dev-server crash or Playwright run is suspect. Re-prove it with a canary."* And it happened again. The canary test was not run.

The second one cut deeper because it is the same class of falsified contract as F005's `toHaveCount(async fn)` mess: **an assertion that is grammatically sound but semantically broken.** FAB-08's twelve geometry checks read `expect(Math.round(x)).toBeCloseTo(expected, BOX_TOLERANCE_PX)`, and `toBeCloseTo`'s second argument is a **count of decimal places**, not a tolerance budget. With `BOX_TOLERANCE_PX = 1` it asserts `|diff| < 0.05`, which on already-rounded integers is exact equality. The tests passed because the geometry *happened* to be pixel-perfect. One platform shift, one fractional render, and the suite would have turned red — but the documented `±1px tolerance` never existed anywhere in the code.

The third is quieter but belongs in the log: **a guard that cannot fail.** FAB-08's four typography assertions sat inside `if (labelStyles) { … }`, so a label element that refused to resolve would have skipped the whole block and the test would report green. Nothing asserted the label was even there.

## Technical Details

### 1. `npm run typecheck` reported clean on 64 TS errors

**Symptom:** Phase 05 claimed `npm run typecheck` → exit 0 on 2026-09-10 afternoon. A canary type error (`Dictionary` typed incorrectly on purpose) produced no error.

**Cause:** Two files, `e2e/capture-fab-visuals.spec.ts` and `e2e/collect-fab-measurements.spec.ts`, lived outside the `playwright.config.ts` project list so the test runner never selected them. But `tsc` still compiled them as part of the whole repo, and both had broken imports, missing dependencies, and invalid types. The actual error output:

```
e2e/capture-fab-visuals.spec.ts:24:16 - error TS2345: Argument of type 'string' is not assignable to parameter of type 'number'
e2e/capture-fab-visuals.spec.ts:31:14 - error TS2694: ...
[62 more TS errors, all in these two files]
```

64 lines total. Invisible to the suite (which never tried to run them), fatal to the gate (the compile abort silenced the whole type check). AC8 claimed green. It was not green.

**Repair:** Both files deleted (their actual content already lived in `e2e/floating-action-button.spec.ts`, lines 200–220). Evidence capture moved to a proper `e2e/capture-fab-visual.spec.ts` behind a `fab-visual-capture` project, following the existing `capture-homepage-visual.spec.ts` convention so the next session has a blueprint and no reason to write scaffolding.

**Verification:** `npm run typecheck` re-run: exit 0, **no output at all**, verified by re-running it three times. Not assumed this time.

### 2. The "±1px tolerance" never existed

**The code:**
```typescript
const BOX_TOLERANCE_PX = 1;
// Twelve assertions like this:
expect(Math.round(actual)).toBeCloseTo(expected, BOX_TOLERANCE_PX);
```

**Why it's wrong:** `toBeCloseTo(received, precision)` compares `|received - expected| < 10^(-precision)`. With `precision = 1`, that's `|received - expected| < 0.1`. On integers rounded to the nearest whole number, this means exact equality — `Math.round(100.4) === 100` and `Math.round(99.6) === 100`, so no value of `actual` within 0.5 pixels would satisfy `toBeCloseTo(100, 1)`. The tests passed because the geometry is exact. **The documented tolerance was fiction.**

Documented assertion: FAB-08 in the phase-05 evidence declared *"measured geometry with ±1px tolerance"* — a lie told in advance of the implementation.

**Repair:** Replaced with a real helper:
```typescript
function expectWithinTolerance(actual: number, expected: number, tolerancePx: number = BOX_TOLERANCE_PX) {
  expect(Math.abs(actual - expected)).toBeLessThanOrEqual(tolerancePx);
}
```

All twelve geometry assertions now actually assert the documented tolerance.

### 3. Typography assertions inside a guard that could fail

**The code:** (`e2e/floating-action-button.spec.ts`, lines 210-221 before correction):
```typescript
const labelStyles = await fabClose.evaluate((el) => window.getComputedStyle(el));
if (labelStyles) {
  expect(labelStyles.fontSize).toStrictEqual("32px"); // text-2xl
  expect(labelStyles.lineHeight).toStrictEqual("32px"); // leading-8
  // … two more
}
```

**Why it's risky:** If `labelStyles === null` or the `.evaluate()` failed (network glitch, element evaporated), the whole `if` block skips and the test reports green. The assertion is **conditional on success**, which is backwards — the failure case should be what we test.

**Repair:** `expect(labelStyles).not.toBeNull()` runs first, then all four typography assertions run unconditionally after.

### 4. Focus management defect — three dismissal paths, one callback

**The finding:** When a keyboard user activates `Hủy` (the close button), `onClick={close}` unmounts the `fab-menu` DOM subtree. Focus was sitting on the `<button>` that just disappeared, so the browser reverted focus to `document.body` — no visible focus indicator anywhere on the page. Meanwhile, activating Escape — three lines away in `useDismissOnOutside` — *did* restore focus to the trigger via `triggerRef.current?.focus()` at line 31.

**Why the test didn't catch it:** FAB-05 (`e2e/floating-action-button.spec.ts:138-158`) asserts the menu is gone and the trigger is visible/`aria-expanded=false`, but never asserts `document.activeElement`. FAB-06 (Escape path) does assert focus — so the two paths diverged without the suite noticing.

**The contract:** `clarifications.md` is explicit: "Escape returns focus to the trigger; an outside click does not move focus." So Hủy should also return focus — it's a deliberate dismissal, not a misdirected click.

**The code before:**
```typescript
const close = useCallback(() => setOpen(false), []);
// ... fab-close button:
<button ... onClick={close} ...>Hủy</button>
```

**The fix:**
```typescript
const close = useCallback(() => setOpen(false), []);
const closeAndRestoreFocus = useCallback(() => {
  setOpen(false);
  triggerRef.current?.focus();
}, []);
// ... fab-close button:
<button ... onClick={closeAndRestoreFocus} ...>Hủy</button>
// ... useDismissOnOutside keeps `close` so outside-click doesn't move focus
useDismissOnOutside(open, rootRef, triggerRef, close);
```

**RED proof:** The fix was made, then FAB-05 was run alone:
```
npx playwright test e2e/floating-action-button.spec.ts --project=anon -g "FAB-05"
  1 failed  FAB-05 … (spec line 181: expect(focused).toBe(FAB_TRIGGER_TESTID))
  1 passed  (FAB-06, the Escape path, unaffected)
```

Then `closeAndRestoreFocus` was applied to `fab-close`, and FAB-05 went GREEN.

## What We Tried

1. **Reported `npm run typecheck` clean without re-proving it** — same assumption that failed in F007. Learned better; did not repeat the error the third time.
2. **Documented a tolerance that the assertion never implemented** — both the phase file and the evidence file claimed ±1px, but `toBeCloseTo`'s decimal-precision parameter made it exact-equality. Replaced with a real helper that does what was promised.
3. **Left typography assertions conditional on a possibly-null value** — no assertion guarded the guard. Added `expect(labelStyles).not.toBeNull()` first.
4. **Shared a dismissal callback across three paths with divergent focus contracts** — `useDismissOnOutside` was correct to not restore focus on pointerdown, but the Hủy button needed its own handler. Split into `close` (reused for outside-click, no focus) and `closeAndRestoreFocus` (Hủy and Escape, with focus).

## Root Cause Analysis

**The same three families as F007 and F005:**

1. **A written claim was trusted instead of a measurement.** The phase file and evidence declared a tolerance without checking the assertion implemented it. A test can pass even when it's not actually testing what the code claims.

2. **An assertion with a confusing API was read wrong.** `toBeCloseTo` takes a decimal-precision argument, not a tolerance in the problem domain. The name is not wrong, but it's easy to misread when you're thinking in pixel units.

3. **A guard condition can hide a failure.** FAB-08's typography block inside `if (labelStyles)` is defensive, but defensiveness is not testing. The guard should be an assertion, not a silent skip.

4. **A shared callback is the wrong shape when the callers' contracts diverge.** The `useDismissOnOutside` hook was correct: outside clicks should not move focus. But `Hủy` and `Escape` are deliberate dismissals from inside the menu, so they should. One callback cannot serve both — the fix is two callables with different postconditions.

## Lessons Learned

1. **Do not trust a typecheck result reported before a canary is run.** F007 taught this seven days ago. It happened again because phase 05 did not re-read F007's entry. Every `npm run typecheck` claim now gets a canary proof: introduce a type error, confirm exit ≠ 0, remove it, confirm exit 0 again. This takes 30 seconds and costs nothing. Not running it is betting the canary is unnecessary — bet lost twice now.

2. **When an assertion implementation looks different from its name, read the type signature.** `toBeCloseTo(expected, precision)` takes a precision in decimal places, not a tolerance budget. Grep the test runner's own `.d.ts` before trusting what a method does.

3. **Assertions inside guards are not assertions.** `if (labelStyles) { expect(...) }` is shorthand for *"assuming this value exists, here is what I expect."* It is never a test of the assumption itself. Prefix with `expect(labelStyles).not.toBeNull()` so the assumption becomes a checked precondition, not a silent skip.

4. **Shared dismissal callbacks are fragile.** When a popover has three separate dismissal triggers (outside-click, Escape, a close button) and they have different postconditions — especially focus behavior — give each its own handler. `useDismissOnOutside` documented that pointerdown "does not move focus", so the hook's internal `close` should never move focus. Hủy-click and Escape are different operations and should have different outcomes. Two callbacks cost nothing and prevent a gap.

5. **The focus gap is exactly the kind of thing that only RED-first catches.** FAB-05 and FAB-06 both passed the suite's original assertions, but they gave conflicting answers about where focus goes. Splitting the callbacks and asserting focus restored is not a "nice to have" — it's table stakes for keyboard navigation. A code review can reason about it, but only a drove browser can prove it works.

## Next Steps

### Immediate (done)

- [x] Delete `e2e/capture-fab-visuals.spec.ts` and `e2e/collect-fab-measurements.spec.ts` (64 TS errors, unselected by runner).
- [x] Create `e2e/capture-fab-visual.spec.ts` behind `fab-visual-capture` project (follows convention).
- [x] Replace twelve `toBeCloseTo(expected, BOX_TOLERANCE_PX)` calls with `expectWithinTolerance(actual, expected)` helper.
- [x] Add `expect(labelStyles).not.toBeNull()` before the typography block in FAB-08.
- [x] Split dismissal callbacks: `close` (no focus) for `useDismissOnOutside`, `closeAndRestoreFocus` (with focus) for `fab-close`.
- [x] Run FAB-05 alone to confirm it RED-ed on the old code, GREEN on the fix.
- [x] Full suite: FAB 9 passed, the-le 10 passed / 2 skipped, homepage 22 passed, typecheck exit 0, lint 0 errors.

### Documentation (deferred, not blocking)

- `use-dismiss-on-outside.ts` is used by three other components (notification bell, account menu, language selector). Check if they share the same focus gap (likely, if they have close buttons).

---

**Status:** DONE
**Summary:** F008 delivered with all gates passing a second time, after corrections. Unearthed three defects hidden by the first-pass gates: `npm run typecheck` did not actually compile clean (64 TS errors in throwaway capture specs unselected by runner), a documented tolerance that never existed in the assertion (toBeCloseTo with decimal precision instead of pixel budget), and an assertion inside a guard that could silently skip (label styles unguarded). Plus one real keyboard-focus regression discovered by the reviewer: `fab-close` dropped focus to `document.body` while Escape returned it to the trigger. All corrected; typecheck, lint, and E2E gates re-proven. Two conventional commits staged locally; not pushed.
**Concerns/Blockers:** None. This is the second occurrence of the same typecheck-masking pattern (F007 week ago, F008 today). The lesson needs teeth: introduce a project-wide convention that `npm run typecheck` is never claimed without a canary re-proof.
