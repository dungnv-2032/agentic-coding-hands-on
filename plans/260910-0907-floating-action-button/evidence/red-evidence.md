# RED Evidence — Floating Action Button (Phase 01)

**Date:** 2026-09-10  
**Phase:** 01 (Strict RED e2e gate)  
**Test Policy:** e2e-red-first  
**Tester:** Claude Haiku 4.5

## Command

```
npx playwright test e2e/floating-action-button.spec.ts --project=anon
```

## Exit Code

**1** (non-zero, valid RED)

## First Failure

```
[anon] › e2e/floating-action-button.spec.ts:61:7 › Floating Action Button (FAB) — anon › FAB-01 — AC1: homepage renders collapsed trigger, aria-expanded=false, no menu 

Error: expect(locator).toBeVisible() failed

Locator: getByTestId('fab-trigger')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for getByTestId('fab-trigger')

      65 |
      66 |     const trigger = page.getByTestId(FAB_TRIGGER_TESTID);
    > 67 |     await expect(trigger).toBeVisible();
         |                           ^
      68 |     await expect(trigger).toHaveAccessibleName(TRIGGER_LABEL);
      69 |     await expect(trigger).toHaveAttribute("aria-expanded", "false");
```

**Failure Classification:** Genuine screen assertion (component doesn't exist).  
**Not a:** Browser install failure, missing dependency, dev-server boot failure, or setup-project error.

## Defect Corrections (Phase 01 Verification)

Three defects were found during verification and corrected BEFORE implementation:

### Defect 1: Broken import (TS2724)
- **Issue:** Spec imported `CLOSE_BUTTON_TESTID`, but constants exported `FAB_CLOSE_TESTID`.
- **Fix:** Changed all three usages (FAB-02, FAB-05, FAB-08) from `CLOSE_BUTTON_TESTID` to `FAB_CLOSE_TESTID`.
- **Verification:** `npx tsc --noEmit` → exit 0 ✓

### Defect 2: FAB-01 aria-label as visible text
- **Issue:** `await expect(trigger).toContainText(TRIGGER_LABEL)` asserted "Hành động nhanh" as visible text, but it is the aria-label only. Visible content is icons + "/" glyph (design/geometry.md § "Collapsed pill": 16+42+8+24+16=106).
- **Fix:** Changed to `await expect(trigger).toHaveAccessibleName(TRIGGER_LABEL)`.
- **Impact:** FAB-01 and FAB-08 would have been self-contradictory; feature could never legitimately go GREEN.

### Defect 3: FAB-02 close button aria-label as visible text
- **Issue:** `await expect(close).toContainText(CLOSE_LABEL)` asserted "Hủy" as visible text, but `fab-close` is icon-only (56×56, p-4 padding = 24×24 slot for `/images/rules/close-icon.svg`). No room for text.
- **Fix:** Changed to `await expect(close).toHaveAccessibleName(CLOSE_LABEL)`.
- **Impact:** Same contradiction; FAB-02 and FAB-08 would have been mutually exclusive, feature could never legitimately go GREEN.

**Note:** `toContainText(MENU_STANDARDS_LABEL)` and `toContainText(MENU_WRITE_KUDOS_LABEL)` remain unchanged — those ARE visible on-button labels per design/geometry.md § "Expanded" node A and B.

## Test Collection (--list output)

```
Listing tests:
  [setup] › auth.setup.ts:60:6 › authenticate and save state
  [anon] › floating-action-button.spec.ts:61:7 › Floating Action Button (FAB) — anon › FAB-01 — AC1: homepage renders collapsed trigger, aria-expanded=false, no menu
  [anon] › floating-action-button.spec.ts:75:7 › Floating Action Button (FAB) — anon › FAB-02 — AC1, AC2: click trigger → menu opens, trigger aria-expanded=true, aria-controls matches menu id
  [anon] › floating-action-button.spec.ts:106:7 › Floating Action Button (FAB) — anon › FAB-03 — AC3: click standards button → navigate to /standards, rules-panel-content visible
  [anon] › floating-action-button.spec.ts:123:7 › Floating Action Button (FAB) — anon › FAB-04 — AC4: anonymous user clicking write-kudos → redirects to /login, not /kudos/new
  [anon] › floating-action-button.spec.ts:138:7 › Floating Action Button (FAB) — anon › FAB-05 — AC5: click close button → menu detached, trigger visible, aria-expanded=false
  [anon] › floating-action-button.spec.ts:160:7 › Floating Action Button (FAB) — anon › FAB-06 — AC5: Escape key → menu closed, fab-trigger is focused
  [anon] › floating-action-button.spec.ts:182:7 › Floating Action Button (FAB) — anon › FAB-07 — AC5: pointerdown on page background → menu closed, fab-trigger NOT focused
  [anon] › floating-action-button.spec.ts:204:7 › Floating Action Button (FAB) — anon › FAB-08 — AC6: geometry at viewport 1440×1024
Total: 9 tests in 2 files
```

**Test count:** 8 FAB tests collected (plus 1 setup test).  
✓ Matches the required 8 tests.

## Test Files

- **Spec file:** `e2e/floating-action-button.spec.ts`
- **Constants file:** `e2e/fixtures/floating-action-button-constants.ts`

## Configuration Changes

- **File:** `playwright.config.ts`
- **Project:** `anon`
- **testMatch:** Added `floating-action-button` to the alternation regex (line 82)

## Summary

All 8 FAB tests failed at the **first assertion** — the screen element `fab-trigger` does not exist. This is a valid RED, confirming the gate is properly positioned before implementation begins. The setup (auth, dev server, Supabase local instance) succeeded, confirming infrastructure is healthy and ready for the implementation phase.

## Readiness for Phase 02

✓ RED established and recorded  
✓ 8 tests collected correctly  
✓ No infrastructure failures  
✓ Ready for implementation (phase 02 onward)
