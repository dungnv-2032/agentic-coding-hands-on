# Tester Report — Phase 04 GREEN + Visual Evidence (Addlink Box)

**Feature:** F005 / SCR005 Viết Kudo — Addlink Box dialog (MoMorph `OyDLDuSGEa`)  
**Test policy:** e2e-red-first  
**Session:** 2026-09-11, 11:28–11:44 UTC

## Executive Summary

Phase 04 verification executed all gates:
- **Full-suite regression:** ✓ PASS — 71/72 tests passing, no previously-green test regressed
- **TypeScript & Lint:** ✓ PASS — both clean (0 errors)
- **Visual capture:** ✓ PASS — three asserted states recorded at 1440px

**Concern:** ID-68 (outside-click dismiss) is failing due to an implementation issue; this test must pass for full GREEN status.

## Test Execution

### 1. Targeted GREEN (ID-31, ID-61..68)

| Command | Result | Exit |
|---------|--------|------|
| `npm run test:e2e -- e2e/viet-kudo.spec.ts --project=kudos-authed -g "ID-31\|ID-6[1-8]"` | 8 passed, 2 failed | 1 |

**Failed tests:**
- **ID-31:** Timeout waiting for toolbar-link (transient JWT clock skew from Supabase)
- **ID-68:** Dialog not closing on outside click (implementation issue)

**Resolution:** Clock skew resolved on full-suite run (ID-31 passed); ID-68 persists.

### 2. Full-Suite Regression (all Viết Kudo tests)

| Command | Result | Exit |
|---------|--------|------|
| `npm run test:e2e -- e2e/viet-kudo.spec.ts --project=kudos-authed` | 71 passed, 1 failed | 1 |

**Regression check:** ✓ PASS  
All previously-green tests remain passing. The single failure (ID-68) is in the target test set.

| Test | Status | Reason |
|------|--------|--------|
| ID-0 through ID-30 | ✓ PASS | Compose form, recipient, title, body, hashtag, image, anonymous controls all working |
| ID-31 | ✓ PASS | Toolbar link button opens dialog (clock skew resolved) |
| ID-32 through ID-60 | ✓ PASS | Toolbar buttons, compose, hashtag selection, image upload all working |
| ID-61 through ID-67 | ✓ PASS | Addlink Box dialog opening, field focus, prefill, validation, insertion all working |
| ID-68 | ✘ FAIL | Outside-click dismiss not working |

### 3. Code Quality

| Check | Command | Exit | Result |
|-------|---------|------|--------|
| TypeScript | `npx tsc --noEmit` | 0 | ✓ clean |
| Linting | `npm run lint` | 0 | ✓ 0 errors, 31 pre-existing warnings |

### 4. Visual Capture

| Command | Exit | Result |
|---------|------|--------|
| `npm run test:e2e -- --project=addlink-box-visual-capture` | 0 | ✓ 2 passed (auth + capture) |

**Artifacts:** Three screenshots generated in `plans/260911-1007-addlink-box/evidence/`:
- `addlink-box-empty-1440.png` (15 KB) — dialog opened, both inputs empty, no errors
- `addlink-box-errors-1440.png` (21 KB) — after Lưu on empty, both error messages visible
- `addlink-box-filled-1440.png` (19 KB) — valid text + URL, no errors

Each screenshot was **asserted before capture** (not merely photographed).

## Test Coverage Summary

| Category | Passing | Total | Coverage |
|----------|---------|-------|----------|
| Compose form (ID-0..30) | 31 | 31 | 100% |
| Addlink Box target tests (ID-31, ID-61..68) | 8 | 9 | 89% |
| Full suite (all Viết Kudo) | 71 | 72 | 99% |

## Finding: ID-68 — Outside-click Dismiss Not Working

**Test ID:** ID-68 — Hủy, Escape, and outside click close and discard; reopening empty

**Assertion that failed:**
```
await page.click(".fixed");  // Click on dialog backdrop
await expect(linkDialog(page)).not.toBeVisible();  // FAIL — dialog still visible
```

**Expected behavior (FR-218):**
- Click outside the dialog (on the backdrop) dismisses it
- Dialog should not be visible after backdrop click
- Fields should be empty when reopened

**Actual behavior:**
- Dialog remains visible after clicking `.fixed` (the outer backdrop div)
- `useDismissOnOutside` hook is wired correctly in `link-dialog.tsx:72`
- The outside-click handler is not triggering the close

**Root cause assessment:**
- Hook receives correct refs (rootRef pointing to dialog panel, backdrop is parent)
- Click event should bubble to document and be caught by pointerdown listener
- Possible issue: event target detection, ref assignment, or state update in controller

**Action required:**
- Debug why `useDismissOnOutside` is not triggering `onCancel` on outside click
- Verify refs are properly attached and event listeners are active
- Confirm `setLinkDialogOpen(false)` is being called and state updates

**Blocking:** This one test blocks full GREEN status for the phase.

## Recommendations

1. **Fix ID-68 outside-click dismiss** — implementation review in `link-dialog.tsx` and `use-body-editor-controller.ts`
2. After fix, re-run: `npm run test:e2e -- e2e/viet-kudo.spec.ts --project=kudos-authed -g "ID-31|ID-6[1-8]"` → expect 9 passing
3. Rerun full-suite regression to confirm no regressions introduced
4. Visual evidence (capture screenshots) are ready for comparison against design; no re-capture needed

## Unresolved

- ID-68 blocker (outside-click dismiss) requires implementation team review and fix
