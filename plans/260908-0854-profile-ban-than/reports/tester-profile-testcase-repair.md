# Testcase repair — F006 profile E2E self-contradicting assertions

**Date:** 2026-09-08 · **Agent:** `tester` · **Scope:** pre-work for phase 10
**File ownership exercised:** `e2e/profile.spec.ts` only. No other file was created, edited or deleted.

Repairs the three assertions phase 10's "Carry-over defects" items 1 and 5 flagged as
unsatisfiable-as-written. All three diagnoses were **confirmed before editing**, then repaired,
then verified. A **fourth instance of the same defect class** was found and is NOT fixed
(out of mandate) — see § Handed back to the orchestrator.

## Environment note — the browser DOES launch here

Phase 08 reported `browserType.launch` failing in this WSL2 sandbox and could not execute its
diagnosis. That blocker is not real. The missing system libraries (`libnspr4.so`, `libnss3.so`,
`libnssutil3.so`, `libasound.so.2`, `libsmime3.so` — all genuinely absent, confirmed via `ldd`)
are vendored, gitignored, under `.playwright-libs/usr/lib/x86_64-linux-gnu`, and
`playwright.config.ts:12-20` puts them on `LD_LIBRARY_PATH`. So `npx playwright test` works
unmodified; only a **standalone** Node script needs the variable exported by hand:

```
LD_LIBRARY_PATH=<repo>/.playwright-libs/usr/lib/x86_64-linux-gnu node <script>
# -> LAUNCH_OK 151.0.7922.34   (exit 0)
```

Everything below is real browser output. Nothing is reconstructed.

## Why the spec run alone cannot show the before/after change

The prompt expected the BEFORE run to show a `click()` timeout and two strict-mode violations.
It does not, and cannot: `app/profile/page.tsx` still returns `<ComingSoon />` (phase 09 unwired),
so in all three tests an **earlier** assertion fails element-absent and the defective line is never
reached. The three defects are **latent** — they would have detonated on phase 10's first GREEN
attempt, exactly as the carry-over note predicted, which is what this pre-work exists to prevent.

To prove the mechanism and the fix, a **DOM-equivalence harness** was used: a `page.setContent()`
fixture reproducing only the markup the three assertions touch, copied from
`app/profile/_components/profile-stats-card.tsx:74-84` and
`app/profile/_components/profile-direction-menu.tsx:97-130`. Real Chromium, real Playwright, real
exit codes. It is a harness, not the app — stated plainly so it is not mistaken for spec evidence.

Harness: `<scratchpad>/locator-harness.js` (throwaway, outside the repo).

## Defect 1 — `TC_WEB_PROFILE_GUI_005` (e2e/profile.spec.ts:273)

Asserted `toBeDisabled()` then called bare `click()`. Both route through the same predicate
(`elementState` → `getAriaDisabled` = `isNativelyDisabled(el) || hasExplicitAriaDisabled(el)`), so
satisfying the assertion guarantees the click times out. `profile-stats-card.tsx:76` carries the
native `disabled` attribute — the spec requires it, so the **test** was wrong, not the button.

**Before**
```ts
    // Clicking the disabled button does nothing
    await button.click();
    // Should still be on the same page
    expect(page.url()).toContain(ROUTE);
```
**After**
```ts
    const urlBeforeClick = page.url();
    await button.click({ force: true });
    // No navigation, and the button is still disabled after being clicked.
    expect(page.url()).toBe(urlBeforeClick);
    expect(page.url()).toContain(ROUTE);
    await expect(button).toBeDisabled();
```
**Strictly stronger:** the old code asserted only `url` *contains* `ROUTE`. The new code pins the
url to its exact pre-click value AND re-asserts the disabled state survives the click. The intent
("clicking the disabled button does nothing") is preserved and now actually observable.

## Defects 2 and 3 — `FUN_009` (:355) and `FUN_011` (:417)

`DIRECTION_LABELS.received` is `"Đã nhận"` (`e2e/fixtures/profile-constants.ts:31`), but the
rendered copy is `"Đã nhận ({count})"` (`lib/i18n/messages/vi-profile.ts:31`) and appears in BOTH
the trigger (`profile-direction-menu.tsx:105`, via `triggerLabel`) and the active option (`:130`).
`getByText` defaults to `exact: false` → 2 matches → strict-mode violation. Making the strings
differ is unavailable: SCR006 § 3 binds one `direction.receivedLabel` key to both C.3 and C.3.1,
and DEC-002 requires the active option to stay listed.

**FUN_009 before / after**
```ts
- await expect(page.getByTestId("profile-direction-option")).toHaveCount(2);
- await expect(page.getByText(DIRECTION_LABELS.received)).toBeVisible();
- await expect(page.getByText(DIRECTION_LABELS.sent)).toBeVisible();
+ const options = page.getByTestId("profile-direction-option");
+ await expect(options).toHaveCount(2);
+ await expect(options.filter({ hasText: DIRECTION_LABELS.received })).toBeVisible();
+ await expect(options.filter({ hasText: DIRECTION_LABELS.sent })).toBeVisible();
```
**FUN_011 before / after**
```ts
- const receivedOption = page.getByText(DIRECTION_LABELS.received);
+ const receivedOption = page
+   .getByTestId("profile-direction-option")
+   .filter({ hasText: DIRECTION_LABELS.received });
+ await expect(receivedOption).toHaveCount(1);
```
**Strictly stronger:** the label must now be on an *option*, not merely somewhere on the page —
the old locator would have been satisfied by the trigger alone. FUN_011 additionally pins the
option count to 1 before clicking.

`FUN_010` (:409), `FUN_012` (:457) and `SEC_002` (:643) match `"Đã gửi"` while the trigger reads
`"Đã nhận"` — one match each. Verified unaffected, left untouched.

## Evidence

### A. Harness — BEFORE (defects reproduced)
`LD_LIBRARY_PATH=<repo>/.playwright-libs/usr/lib/x86_64-linux-gnu node <scratchpad>/locator-harness.js before`
→ **exit 1**, `1 passed, 3 failed`
```
[PASS] GUI_005 toBeDisabled() holds
[FAIL] GUI_005 BEFORE: bare click() on the disabled button
    -> locator.click: Timeout 3000ms exceeded. / Call log: /  - waiting for getByTestId('profile-secret-box-button')
       /  - locator resolved to <button disabled type="button" ... data-testid="profile-secret-box-button">…</button>
[FAIL] FUN_009 BEFORE: getByText(received).toBeVisible()
    -> expect(locator).toBeVisible() failed / Locator: getByText('Đã nhận') / Expected: visible
       / Error: strict mode violation: getByText('Đã nhận') resolved to 2 elements:
[FAIL] FUN_011 BEFORE: getByText(received).click()
    -> locator.click: Error: strict mode violation: getByText('Đã nhận') resolved to 2 elements:
       1) <button ... data-testid="profile-direction-trigger">…</button> aka getByTestId('profile-direction-trigger')
       2) <button ... role="option" aria-selected="true" data-testid="profile-direction-option">Đã nhận (0)</button>
```
Both predicted failure modes reproduced verbatim, including the disabled-element click timeout and
the two-element strict-mode resolution naming the trigger and the option.

### B. Harness — AFTER (defects gone)
`... node <scratchpad>/locator-harness.js after` → **exit 0**, `4 passed, 0 failed`
```
[PASS] GUI_005 toBeDisabled() holds
[PASS] GUI_005 AFTER: click({force:true}) on the disabled button
[PASS] FUN_009 AFTER: option.filter({hasText:received}).toBeVisible()
[PASS] FUN_011 AFTER: option.filter({hasText:received}).click()
```

### C. Real spec, BEFORE the edit — honest RED, no self-contradiction surfaced
`npx playwright test --project=profile-authed -g "GUI_005|FUN_009|FUN_011"` → **exit 1**,
`3 failed, 1 passed (2.7m)` (the 1 pass is the `profile-auth-setup` dependency, which `-g` does not
filter out).
```
GUI_005  profile.spec.ts:281  expect(locator).toContainText(expected) failed
         Locator: getByTestId('profile-stats-card')   Expected substring: "Số Secret Box bạn đã mở:"
         Timeout: 15000ms   Error: element(s) not found
FUN_009  profile.spec.ts:352  expect(locator).toContainText(expected) failed
         Locator: getByTestId('profile-direction-trigger')   Expected substring: "Đã nhận"
         Timeout: 15000ms   Error: element(s) not found
FUN_011  profile.spec.ts:407  Test timeout of 30000ms exceeded.
         Error: locator.textContent: Test timeout of 30000ms exceeded.
         Call log:  - waiting for getByTestId('profile-direction-trigger')
```

### D. Real spec, AFTER the edit — identical honest RED
Same command → **exit 1**, `3 failed, 1 passed (2.6m)`. Same three failures, same three causes,
line numbers shifted by the added comments (`:281`, `:361`, `:423`):
```
GUI_005  profile.spec.ts:281  getByTestId('profile-stats-card')      element(s) not found
FUN_009  profile.spec.ts:361  getByTestId('profile-direction-trigger') element(s) not found
FUN_011  profile.spec.ts:423  Test timeout of 30000ms exceeded (waiting for the trigger)
```
The repair changed nothing about the current RED — which is the correct outcome. The defect it
removes only becomes reachable once phase 09 renders the real screen.

### E. Static gates
| Command | Exit | Result |
|---|---|---|
| `npm run typecheck` | 0 | clean |
| `npm run lint` | 0 | 0 errors, 30 warnings — all pre-existing; the 2 in `profile.spec.ts` (`cleanupAnonymousKudo` :91, `card` :519) predate this change |
| `npx playwright test --project=profile-authed -g "..." --list` | 0 | selects exactly the 3 intended tests + the setup dependency |

Diff is exactly the three hunks. Test count unchanged at 26. No `.skip`, no `.only`, no early
return, no try/catch, no removed check, no widened matcher, no renumbered ID.

## Handed back to the orchestrator — a FOURTH instance, not fixed

**`TC_WEB_PROFILE_SEC_001` at `e2e/profile.spec.ts:392`** carries the identical defect and the
carry-over note does not list it. On another's profile the menu opens with one option, but the
trigger *also* renders `"Đã nhận (N)"` — so `getByText` still resolves to 2 elements.
Proven in the same harness against SEC_001's own one-option DOM (`<scratchpad>/sec001-harness.js`,
**exit 1**):
```
[PASS] toHaveCount(1) on the option — holds
[FAIL] SEC_001 as-written: getByText(received).toBeVisible()
    -> strict mode violation: getByText('Đã nhận') resolved to 2 elements:
       1) <button ... data-testid="profile-direction-trigger">…</button>
       2) <button ... role="option" aria-selected="true" data-testid="profile-direction-option">Đã nhận (3)</button>
```
**Not fixed** — the mandate named three defects and forbade touching the other tests. The one-line
repair, identical in shape and equally strict:
```ts
-    await expect(page.getByText(DIRECTION_LABELS.received)).toBeVisible();
+    await expect(
+      page.getByTestId("profile-direction-option").filter({ hasText: DIRECTION_LABELS.received })
+    ).toBeVisible();
```
SEC_001's other assertion (`expect(body).not.toContainText(DIRECTION_LABELS.sent)`) is sound and
needs no change. Leaving this in place costs phase 10 the wasted GREEN cycle this pre-work was
meant to avoid — recommend extending the mandate by one line.

## Still on phase 10

- Nothing about these three tests is resolved by this repair — they remain RED until phase 09 wires
  `app/profile/page.tsx`. The repair only guarantees they *can* go green.
- Phase 10 item 1 and item 5 can be struck from "Carry-over defects"; item 5 should gain SEC_001.
- Phase 10's step 1 `supabase db reset` was deliberately **not** run: another agent is working
  against the local database. Phase 10 still owns that reset.
- Phase 10's own note that the browser cannot launch in WSL2 should be corrected — see the
  environment note above. Full-suite runs cost ~2.6 min each because of `reuseExistingServer: false`.

## Unresolved questions

1. Extend the mandate to fix `SEC_001:392`? It is the same defect class, one line, already proven.
2. Should the `GUI_005` no-navigation check be strengthened further into a `page.on("framenavigated")`
   assertion? `expect(page.url()).toBe(urlBeforeClick)` cannot catch a navigate-and-return. Judged
   YAGNI for a natively-disabled button with no handler, but noting the gap rather than hiding it.
3. `DIRECTION_LABELS` in `e2e/fixtures/profile-constants.ts` holds bare labels while the UI renders
   `({count})`. Every present use is a substring match and correct, but the mismatch is a trap for
   the next author. A comment there would help — that file is not mine to edit.
