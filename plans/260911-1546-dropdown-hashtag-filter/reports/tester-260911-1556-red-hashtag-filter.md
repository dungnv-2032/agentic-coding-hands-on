# RED Evidence — Hashtag Dropdown Filter (e2e-red-first)

**Phase**: 01 — RED e2e for the hashtag dropdown
**MoMorph screen**: JWpsISMAaM (Dropdown Hashtag filter)
**Test files**: e2e/kudos-live-board.spec.ts
**Test policy**: e2e-red-first
**Date**: 2026-09-11

## Command & Exit Code

```bash
npm run test:e2e -- e2e/kudos-live-board.spec.ts --project=anon -g "K-31|K-32|K-33|K-34|K-35"
```

**redExitCode**: `1` (non-zero, genuine test failure)

## Test Results Summary

| Test | Status | Type | Notes |
|------|--------|------|-------|
| K-31 | FAILED | RED (genuine) | Bounding box 742px, not 348px; max-height not set |
| K-32 | FAILED | RED (genuine) | text-shadow is `none`, not containing `rgb(250, 226, 135)` |
| K-33 | PASSED | Regression guard | Filter narrowing to #Wasshoi works end-to-end |
| K-34 | PASSED | Regression guard | Selection retention via aria-selected works after reopen |
| K-35 | PASSED | Regression guard | Toggle-off via re-click works, href baseline restored |

**Summary**: 4 passed, 2 failed (E2E suite runs 6 including [setup]).

## Per-Test Failure Details

### K-31 — hashtag filter menu max-height is 348px and contains all 13 options

**Failure reason**: Bounding box height assertion failed.

```
Error: expect(received).toBe(expected) // Object.is equality

Expected: 348
Received: 742

  847 |       expect(boundingBox.height).toBe(348);
      |                                  ^
```

**Root cause (from phase insights)**: `max-h-[348px] overflow-y-auto` sits behind `scrollable` flag in `kudos-filter-menu.tsx`; `kudos-filter-bar.tsx` only passes that flag to department menu, not hashtag menu. Computed `max-height` on `filter-menu-hashtag` is currently `none`.

**Expected after phase 02**: Box clamped to 348px, with `overflow-y-auto` enabled and scroll proof (`scrollHeight > clientHeight`).

---

### K-32 — hashtag option shows focus glow with correct color on keyboard focus

**Failure reason**: text-shadow style assertion failed.

```
Error: expect(received).toContain(expected) // indexOf

Expected substring: "rgb(250, 226, 135)"
Received string:    "none"

  896 |     expect(shadowStyle).toContain("rgb(250, 226, 135)");
      |                         ^
```

**Root cause (from phase insights)**: Option button has no `focus-visible:` Tailwind rule; computed `text-shadow` under keyboard focus is `none` (no custom glow, only browser outline).

**Expected after phase 02**: Option gains `focus-visible:shadow-[0_0_6px_#FAE287]` rule; computed `text-shadow` carries `rgb(250, 226, 135)` signature.

---

## Regression Guards (Passing)

### K-33 — clicking hashtag option closes menu and filters both sections

**Status**: ✓ PASSED (1.2s)
**Assertion**: Click `Wasshoi` option → menu closes → every visible card in `highlight-section` and `all-kudos-section` carries `#Wasshoi` hashtag chip.

**Proof**: Already works — `kudos-board.tsx` wires `hashtagFilterId` into `matchesFilters()`, and the trigger closes the menu on click. This test locks in the behavior.

---

### K-34 — hashtag option retains aria-selected and styling after reopen

**Status**: ✓ PASSED (1.3s)
**Assertion**: After selecting `Wasshoi`, reopen menu → option has `aria-selected="true"` and `text-shadow` contains the glow color.

**Proof**: State retention already works. K-32 fails on *focus* glow, but K-34 checks *selected* state glow (which exists via the selected-state rule `[text-shadow:0_0_6px_#FAE287]`). This test confirms selection persistence across reopen.

---

### K-35 — re-clicking hashtag option clears filter and restores full board

**Status**: ✓ PASSED (1.3s)
**Assertion**: Capture baseline receiver hrefs → select `Wasshoi` → verify narrowed → click `Wasshoi` again → verify restored hrefs deep-equal baseline.

**Proof**: Toggle-off already works. `hashtagFilterId` state machine is correctly implemented. This test proves the round-trip without relying on seed order or count.

---

## Test Ownership & Continuity

- **redTestFiles**: `e2e/kudos-live-board.spec.ts`
- **redCommand**: `npm run test:e2e -- e2e/kudos-live-board.spec.ts --project=anon -g "K-31|K-32|K-33|K-34|K-35"`
- **redExitCode**: `1`
- **Typecheck**: ✓ clean (`npm run typecheck` succeeded before RED run)
- **Environment**: Supabase local running at http://127.0.0.1:54321 with 13 hashtag rows seeded
- **Read-only handoff**: Phase 02 (`momorph-ui-implementer`) receives these values and must rerun the same command GREEN. Phase 02 must not modify any file under `e2e/`.

---

## Next Steps

1. Phase 02 adds `max-h-[348px] overflow-y-auto` styling to hashtag listbox and `focus-visible:shadow-[0_0_6px_#FAE287]` to option buttons.
2. Phase 02 reruns the exact RED command and confirms GREEN (all 5 tests pass).
3. Tester validates visual state post-GREEN against the Figma frame (separate `capture-hashtag-dropdown-visual.spec.ts`).

---

**Status:** DONE  
**Summary:** Two genuine RED failures (K-31, K-32) and three regression guards locked in (K-33, K-34, K-35). RED evidence captured with real exit code 1 and per-test failure text recorded.

