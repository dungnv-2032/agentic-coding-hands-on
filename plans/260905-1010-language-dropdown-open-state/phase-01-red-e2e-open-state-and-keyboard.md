# Phase 01 — RED e2e for open-state contract + keyboard nav

## Context Links

- Plan overview: [plan.md](plan.md)
- Spec (authoritative tokens): [spec/language-dropdown/spec-delta.md](spec/language-dropdown/spec-delta.md) §3
- Decisions: [clarifications.md](clarifications.md)
- Design: MoMorph `hUyaaugye2` — https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/hUyaaugye2
- Existing spec file being extended: `e2e/login-screen.spec.ts` (C1, C2, C3, C3b, C4, C5, C10)
- Runner config: `playwright.config.ts`

## Overview

- **Priority:** P1 (gate — nothing else may start until this is RED on a real assertion)
- **Status:** completed
- **Owner:** `tester`
- **Effort:** 45m
- **Description:** Extend the durable login-screen Playwright spec with three new tests
  that assert the real open-state contract and the listbox keyboard behavior. They must
  fail against today's code for the *right* reason, and pass unchanged after phase 02.

## Key Insights

- `testPolicy: e2e-red-first`. A valid RED is a non-zero exit caused by the new screen
  assertions. A dependency, browser-install, config, or dev-server failure is **not** a
  valid RED — if that is what you get, fix the environment and rerun before reporting.
- **Extend `e2e/login-screen.spec.ts`; do not add a new spec file.** `playwright.config.ts`
  matches the `anon` project on `/(?:smoke|login-screen|route-guard|callback-security)\.spec\.ts/`.
  A new filename would need a config change — avoidable churn (KISS).
- Today's panel is `bg-[#0B0F12]`, borderless, no selected-row background, no arrow keys.
  So background, border, selected-background, and ArrowDown-moves-focus all fail naturally.
- Colors must be asserted through `getComputedStyle`, which normalizes to `rgb()`/`rgba()`:
  `#00070C` → `rgb(0, 7, 12)`, `#998C5F` → `rgb(153, 140, 95)`,
  `rgba(255,234,158,0.2)` → `rgba(255, 234, 158, 0.2)`.
- The `anon` project declares `dependencies: ["setup"]`, so `auth.setup.ts` runs first even
  for these tests. A setup failure is an environment failure, not a RED.

## Requirements

**Functional (what the tests must prove):**

- FR-203.a — the open panel lists both locales, each with its own flag (already held by C3b).
- FR-203.b — the selected option is distinguished by **background**, not by a hidden attribute alone.
- FR-203.c — ArrowDown/ArrowUp/Home/End move focus, Enter/Space select, Escape closes and
  returns focus to the trigger.
- Visual contract — panel background, border, radius, padding; option size, radius; selected
  and hover backgrounds. Values from spec-delta §3, verbatim.

**Non-functional:**

- Tests are durable, not throwaway — they stay in the suite after GREEN.
- No `waitForTimeout`; use web-first assertions (`expect(...).toHaveCSS`, `expect.poll`).
- No mock, no stub, no test-only hook in production code.

## Architecture

```
e2e/login-screen.spec.ts  (anon project)
  ├─ C3c  panel visual contract   → locator('[role="listbox"]')  → toHaveCSS × 5
  ├─ C3d  option state contract   → getByRole('option')          → selected/unselected/hover bg
  └─ C3e  keyboard navigation     → keyboard events on the open panel
             ArrowDown/ArrowUp/Home/End → document.activeElement is the expected option
             Escape                     → panel gone, focus back on trigger
             Enter                      → locale switches (NEXT_LOCALE=en)
```

Data flow under test: click trigger → `open=true` → panel renders → focus lands on the
selected option → key events mutate the focused index → Enter/Space fires the option's
click → `setLocale` server action → cookie `NEXT_LOCALE` → page re-renders in the new locale.

## Related Code Files

**Modify**

- `e2e/login-screen.spec.ts` — append C3c, C3d, C3e inside the existing
  `test.describe("Login Screen (anon project)")` block, after C3b.

**Read for context (do not edit)**

- `app/login/_components/language-selector.tsx`
- `playwright.config.ts`
- `plans/260905-1010-language-dropdown-open-state/spec/language-dropdown/spec-delta.md`

**Create / delete:** none.

## Implementation Steps

1. Read `e2e/login-screen.spec.ts` and match its existing style: `// Cn [FR-xxx] — …`
   comment header, `page.locator('button[aria-haspopup="listbox"]')` for the trigger.
2. Add a small local helper inside the describe block (DRY across the three tests):

   ```ts
   const trigger = (page: Page) => page.locator('button[aria-haspopup="listbox"]');
   ```

   Do not export it; do not create a fixtures file for three call sites (YAGNI).
3. **C3c [FR-203, design 721:4942] — open panel matches the visual contract.**
   Open the dropdown, then on `page.getByRole("listbox")` assert:
   - `background-color` → `rgb(0, 7, 12)`
   - `border-width` → `1px`, `border-style` → `solid`, `border-color` → `rgb(153, 140, 95)`
   - `border-radius` → `8px`
   - `padding` → `6px`
   Then on `page.getByRole("option").first()` assert `border-radius` → `2px` and a
   bounding box of `108 × 56` (`toHaveCSS("width", "108px")` / `"height", "56px"`).
4. **C3d [FR-203.b] — selected option is distinguished by background.**
   Open the dropdown at default locale (VN). Assert:
   - `getByRole("option", { name: /^VN$/ })` → `background-color` is `rgba(255, 234, 158, 0.2)`
   - `getByRole("option", { name: /^EN$/ })` → `background-color` is `rgba(0, 0, 0, 0)` (transparent)
   - after `.hover()` on the EN option → `background-color` is `rgba(255, 234, 158, 0.08)`
   - the VN option still reports `aria-selected="true"` (the attribute contract stays, the
     background is the *addition*)
5. **C3e [FR-203.c] — keyboard navigation.**
   Split into clearly-labelled steps inside one test (one open/close cycle per assertion group):
   - open via trigger click → `expect(page.getByRole("option", { name: /^VN$/ })).toBeFocused()`
     (focus moves into the **selected** option on open)
   - `ArrowDown` → EN focused; `ArrowDown` again → wraps to VN
   - `ArrowUp` → wraps to EN; `Home` → VN focused; `End` → EN focused
   - `Escape` → `expect(page.getByRole("listbox")).toHaveCount(0)` **and**
     `expect(trigger(page)).toBeFocused()`
   - reopen, `ArrowDown` to EN, press `Enter` → English copy
     (`page.getByText("Start your journey with SAA 2025.")`) visible and
     `NEXT_LOCALE` cookie is `en` (reuse C3's `expect.poll` cookie pattern)
   - a second sub-case for `Space` selecting is optional; if added, use a fresh
     `page.context().clearCookies()` + reload so it does not depend on C3e's own Enter step.
6. Run the exact command and capture the real exit code:

   ```bash
   npx playwright test e2e/login-screen.spec.ts --project=anon
   ```
7. Confirm the failures are **assertion** failures on C3c/C3d/C3e — not setup, browser, or
   dev-server failures. Confirm C1, C2, C3, C3b, C4, C5, C10 still pass in the same run.
8. Record the RED evidence for phase 02 (write it into this file's Todo section or the
   phase report):
   - `redTestFiles`: `["e2e/login-screen.spec.ts"]`
   - `redCommand`: `npx playwright test e2e/login-screen.spec.ts --project=anon`
   - `redExitCode`: the actual non-zero value
   - `redFailure`: the verbatim first assertion-failure line for each of C3c/C3d/C3e

## Delivery (2026-09-05)

C3c, C3d and C3e were added to `e2e/login-screen.spec.ts`. Valid RED achieved:

- `redCommand`: `npx playwright test e2e/login-screen.spec.ts --project=anon`
- `redExitCode`: 1 (failed, as expected)
- Failures: C3c `Expected "rgb(0, 7, 12)" Received "rgb(11, 15, 18)"` (panel bg), C3d `Expected "rgba(255, 234, 158, 0.2)" Received "rgba(0, 0, 0, 0)"` (selected bg), C3e `Expected focused Received inactive` (keyboard nav)
- Evidence: `evidence/red-evidence.json`
- Tester fixed lint issue (`page: any` → `type Page`) that was left initially
- C1/C2/C3/C3b/C4/C5/C10 still pass in the same run — no regression

## Todo List

- [x] Read `e2e/login-screen.spec.ts` + `playwright.config.ts`
- [x] Replace `page: any` in the `trigger()` helper with the imported `Page` type
- [x] Write C3c (panel visual contract)
- [x] Write C3d (selected / unselected / hover backgrounds)
- [x] Write C3e (ArrowDown/Up/Home/End, Escape + focus return, Enter selects)
- [x] Run `npx playwright test e2e/login-screen.spec.ts --project=anon`
- [x] Verify failures are real assertion failures, not environment failures
- [x] Verify C1/C2/C3/C3b/C4/C5/C10 still pass in the same run
- [x] Record redCommand / redExitCode / redFailure

## Success Criteria

| Criterion | How it is observed |
|---|---|
| Three new durable tests exist | `grep -c "C3c\|C3d\|C3e" e2e/login-screen.spec.ts` ≥ 3 |
| RED is real | Non-zero exit; failure text names `background-color`, `border-color`, or `toBeFocused` on the new tests |
| RED is not environmental | `setup` project passes; no `browserType.launch` / `libnspr4` / `ECONNREFUSED` in output |
| No regression introduced by the test file | C1, C2, C3, C3b, C4, C5, C10 report passed in the same run |
| Evidence captured | `redCommand`, `redExitCode`, `redFailure` recorded verbatim |

## Risk Assessment

| Risk | Likelihood | Impact | Countermeasure |
|---|---|---|---|
| `auth.setup.ts` fails (WSL2 libs, Supabase env) and masks the RED | Medium | High | Run `npx playwright test --project=setup` alone first; if it fails, fix env (`.playwright-libs/`, env vars) before claiming RED. An env failure is **not** RED. |
| `toHaveCSS("padding", "6px")` normalizes to the 4-value form in some engines | Medium | Low | Assert `padding-top`/`padding-left` individually if the shorthand does not match. |
| Transparent background reported as `rgba(0, 0, 0, 0)` vs `transparent` | Medium | Low | Assert `rgba(0, 0, 0, 0)`; that is what Chromium computes. |
| `.hover()` assertion flakes because focus-visible background also applies | Low | Medium | Hover the option **without** clicking; assert only `background-color`. Phase 02 puts focus on a `ring`, not a background, precisely to keep these orthogonal. |
| Test written to today's DOM shape (`ul`/`li`) breaks when phase 02 changes the container | Medium | Medium | Select by **role** (`getByRole("listbox")`, `getByRole("option")`), never by tag or class. |
| C3e's Enter step leaves the locale as EN and pollutes a later test | Low | Medium | Playwright gives each test a fresh context; do not rely on cross-test order. Put the Enter step last within C3e. |

## Security Considerations

- No authentication surface is touched; these tests run in the `anon` project.
- Do not hardcode Supabase keys, tokens, or the test account into the spec — the existing
  `auth.setup.ts` owns credentials, and nothing new is needed here.
- Assert on cookie **value** only (`NEXT_LOCALE=en`); never dump the full cookie jar into
  test output, which would leak the session cookie into CI logs.

## Next Steps

- **Blocks:** phase 02 cannot start until RED evidence is recorded.
- **Hand off to phase 02:** `redTestFiles`, `redCommand`, `redExitCode`, `redFailure` —
  read-only. Phase 02 must not edit this spec file to make it pass.
