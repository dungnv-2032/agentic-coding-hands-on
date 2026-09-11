# RED evidence — Addlink Box (`OyDLDuSGEa`)

**redCommand:** `npm run test:e2e -- e2e/viet-kudo.spec.ts --project=kudos-authed -g "ID-31|ID-6[1-8]"`
**redExitCode:** `1`
**Result:** 9 failed, 1 passed (the `kudos-auth-setup` dependency), 5.4m
**Observed:** 2026-09-11, by the orchestrator, against the shipped one-field dialog.

## Why this is a VALID red

Every one of the nine failures is caused by an element the frame requires and the current dialog
does not render. Nothing failed on a missing dependency, a browser install, a dev-server start, or
a syntax error — the `webServer` came up and the one dependency test passed on the same run.

| # | Test | First error (verbatim) | Missing thing |
|---|------|------------------------|---------------|
| 1 | ID-31 | `expect(locator).toBeVisible() failed` → `Error: element(s) not found` | `link-text-input` |
| 2 | ID-61 | `expect(locator).toContainText(expected) failed` | title `Thêm đường dẫn` |
| 3 | ID-62 | `Error: locator.click: Test timeout of 30000ms exceeded.` | the `Nội dung` `<label>` |
| 4 | ID-63 | `expect(locator).toHaveValue(expected) failed` → `Error: element(s) not found` | `link-text-input` (prefill) |
| 5 | ID-64 | `expect(locator).toHaveValue(expected) failed` → `Error: element(s) not found` | `link-text-input` |
| 6 | ID-65 | `Error: locator.fill: Test timeout of 30000ms exceeded.` | `link-text-input` |
| 7 | ID-66 | `expect(locator).toBeVisible() failed` → `Error: element(s) not found` | `link-url-error` |
| 8 | ID-67 | `Error: locator.fill: Test timeout of 30000ms exceeded.` | `link-text-input` |
| 9 | ID-68 | `Error: locator.fill: Test timeout of 30000ms exceeded.` | `link-text-input` |

The four `locator.fill` / `locator.click` timeouts are Playwright waiting out its timeout on a
selector that never appears — the same "does not exist" fact as the explicit
`element(s) not found` assertions, reached through an action rather than an expectation.

## Two test defects found and fixed before this run was accepted

The first run of this gate was not trustworthy and was rejected:

1. **Port 3000 was still held** by a dev server left over from the authoring session, so
   Playwright aborted with `http://127.0.0.1:3000 is already used` — an infrastructure failure,
   not a red. The stale server was killed and the run repeated.
2. **ID-63 referenced a Node-scope variable inside `locator.evaluate`**, producing
   `ReferenceError: selectedText is not defined` — a bug in the test, not a finding about the
   dialog. Rewritten to pass the length in as an argument.
3. **ID-65's third case only re-read the value it had just typed**, which asserts nothing.
   Rewritten so a 1-character display text must actually be ACCEPTED — the dialog closes and no
   text error shows.

A `prefer-const` lint error left in ID-68 was also fixed; `npm run lint` is now 0 errors and
`npx tsc --noEmit` is clean.

## Hooks this red demands

New: `link-text-input`, `link-text-error`, `link-url-error`, `link-confirm`, `link-cancel`.
Frozen and unchanged: `toolbar-link`, `link-dialog`, `link-url-input`, `body-editor`.
