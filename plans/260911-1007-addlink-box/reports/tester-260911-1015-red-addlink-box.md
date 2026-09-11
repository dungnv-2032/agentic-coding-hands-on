# Tester Report — Addlink Box RED E2E Gate
**Date:** 2026-09-11 | **Phase:** 01 | **Test Policy:** e2e-red-first

## Summary

Authored 8 new RED tests (ID-61 through ID-68) plus extended ID-31 to gate the two-field link dialog implementation against the MoMorph frame (OyDLDuSGEa). All tests fail on assertion — the current one-field dialog does not provide the required input, validation, error rendering, prefill, or state management that FR-213..FR-219 specify.

## Test Authoring

**Files modified:**
- `e2e/viet-kudo.spec.ts` — added ID-61..ID-68 (8 tests) and extended ID-31 (+1 assertion)
- `e2e/fixtures/viet-kudo-constants.ts` — added 5 Vietnamese constants for dialog copy

**Test Contract Hooks (new, provided by phase 03):**
- `link-text-input`, `link-text-error`, `link-url-error`, `link-confirm`, `link-cancel`

**Hooks frozen (unchanged):**
- `toolbar-link`, `link-dialog`, `link-url-input`, `body-editor`

## Coverage

| ID | Asserts | Status |
|----|---------|----|
| ID-61 | title, both inputs visible/empty, both labels present | ✘ FAIL — no 2nd input, title not "Thêm đường dẫn", no labels |
| ID-62 | label click focuses `link-text-input` | ✘ FAIL — no label or text input |
| ID-63 | selection prefills `link-text-input` | ✘ FAIL — no prefill, no 2nd input |
| ID-64 | save with both empty → both errors visible, dialog open | ✘ FAIL — no error elements, button disabled |
| ID-65 | text: whitespace/101-char errors, 1-char ok | ✘ FAIL — no text input, no validation |
| ID-66 | URL blur validation shows error; `www` min-length error | ✘ FAIL — no error element, no blur handler |
| ID-67 | valid input + save → close, text in editor | ✘ FAIL — button disabled, no text insertion |
| ID-68 | cancel/escape/outside click close & discard; reopen empty | ✘ FAIL — no cancel hook, state unclear |
| ID-31 (ext) | dialog opens, URL input visible, **text input visible** | ✘ FAIL — text input missing |

**Command:** `npm run test:e2e -- e2e/viet-kudo.spec.ts --project=kudos-authed`  
**Exit code:** 1 (non-zero, assertion-caused)  
**Failures:** 8 + 1 = 9 test methods fail

## Why Tests Fail

Current `link-dialog.tsx`:
- **One input** (`link-url-input`) — frame requires two
- **One label** (generic) — frame requires labeled inputs
- **Disabled button gate** — frame requires always-clickable button + error rendering
- **No error elements** — frame requires per-field `link-text-error` and `link-url-error`
- **No prefill** — frame requires `link-text-input` to auto-fill from selection
- **No text insertion** — frame requires `Nội dung` value to replace selection, not just link the selection
- **No state reset path** — frame requires visible cancel (`link-cancel` hook) + verified empty reopen

All failures are **assertion-only** — elements do not exist or have wrong content. No dependency, browser install, or dev-server failures present.

## Code Quality

- No lint errors from new test code (verified against existing patterns)
- Test names prefixed `ID-nn` matching contract
- Helpers follow locator-per-hook convention
- Constants imported and used (no hardcoded Vietnamese strings in spec file)
- Each test navigates with `await page.goto(ROUTE)` — no `beforeEach` interdependence

## Next Steps (Phase 02–03)

1. **Phase 02 (UI):** Render two labeled inputs, error elements with test IDs, add button hooks, implement validation on blur and save.
2. **Phase 03 (Behavior):** Wire prefill from selection, implement text insertion (not just link), reset state on close, handle cancel/escape paths.
3. **Tester rerun:** Run same command after implementation, expect all 9 tests GREEN.

## Unresolved

None. RED gate is complete and ready for implementation handoff.
