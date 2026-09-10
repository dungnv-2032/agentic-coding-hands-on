---
phase: 04
title: "Adapt the-le FUN_003 to the new click path"
status: complete
owner: tester
track: gate
test_policy: e2e-red-first
effort: 0.5h
depends_on: [01]
---

# Phase 04 — Adapt `the-le.spec.ts` FUN_003

## Context Links

- [clarifications.md](clarifications.md) § "Late finding — an existing test is coupled to the old shape"
- `e2e/the-le.spec.ts` lines 198-217 (FUN_003) · `e2e/fixtures/the-le-constants.ts` lines 85-91
- [phase-03](phase-03-floating-widget-disclosure.md) — supplies the markup this test now needs
- F007 plan: `plans/260909-0838-the-le-rules-panel/`

## Overview

- **Priority:** P1 — without it, a shipped test fails for a reason that is not a defect.
- **Status:** pending
- FUN_003 clicks the homepage widget as a `role=link` named "Thể lệ SAA" to earn a genuine
  client-side history entry before testing `Đóng`. After the conversion there is no such link on
  `/` until the FAB is opened. Adapt the *route to* the assertion; the assertion itself is
  untouched.

## Key Insights

- This is an adaptation, not a weakening: FUN_003 still needs a real history entry created by a
  real user click, then asserts `Đóng` returns to `/`. Only the path there gains one step.
- Preserving a hidden link purely to keep the old locator passing was explicitly rejected — it
  would leave two affordances for one destination, which is exactly what the conversion removes.
- `WIDGET_STANDARDS_LABEL = "Thể lệ SAA"` survives untouched: phase 03 keeps it as the
  `aria-label` of `fab-standards`, so `getByRole("link", { name: WIDGET_STANDARDS_LABEL })` still
  resolves — *after* the menu is open. Only the two-step path changes.
- FUN_003b (deep link, no history) is unaffected — it never touches the homepage.
- This phase may be written in parallel with phase 03 (disjoint files) but cannot pass until 03
  lands. Do not use that as a reason to soften an assertion.

## Requirements

Functional:
- FUN_003 opens the FAB (`fab-trigger`), then clicks `fab-standards`, then runs the unchanged
  assertions: URL matches `/standards$`, `rules-close-button` visible and containing `Đóng`,
  click it, URL back to `http://127.0.0.1:3000/`.
- No other test in `e2e/the-le.spec.ts` changes.

Non-functional:
- `npx playwright test e2e/the-le.spec.ts --project=anon` exits 0 once phase 03 has landed.
- Vietnamese copy still comes from the constants file, never inlined.

## Architecture

```
before:  goto("/") → click link[name="Thể lệ SAA"] → /standards → Đóng → /
after:   goto("/") → click testid=fab-trigger → click testid=fab-standards → /standards → Đóng → /
                     ^^^^^^^^^^^^^^^^^^^^^^^^ the only added step
```

Locator choice: use `getByTestId("fab-standards")` for the click (stable, fixed by the test
contract) and keep an `expect(...).toHaveAccessibleName(WIDGET_STANDARDS_LABEL)` assertion so the
constant stays load-bearing rather than becoming dead weight.

## Related Code Files

Modify:
- `e2e/the-le.spec.ts` — FUN_003 body and its comment block only.
- `e2e/fixtures/the-le-constants.ts` — the `WIDGET_STANDARDS_LABEL` docblock (lines 85-91) now
  describes the two-step path. **Value unchanged.**

Create: none. Delete: none. Not touched: any `app/`, `lib/`, `public/` file;
`e2e/floating-action-button.spec.ts`; `playwright.config.ts`.

## Implementation Steps

1. Replace FUN_003's comment block: state that the homepage shortcut now sits behind the FAB
   trigger, and cite `clarifications.md` § "Late finding".
2. Insert the open step: `const trigger = page.getByTestId("fab-trigger"); await expect(trigger).toBeVisible(); await trigger.click();`
3. Swap the shortcut locator to `page.getByTestId("fab-standards")`, keep the visibility
   expectation, add the accessible-name expectation against `WIDGET_STANDARDS_LABEL`.
4. Leave every assertion after the click byte-identical.
5. Update the constants docblock to describe the new path.
6. After phase 03 lands: `npx playwright test e2e/the-le.spec.ts --project=anon` → exit 0.

## Todo List

- [ ] FUN_003 opens the FAB before clicking the shortcut
- [ ] Post-click assertions unchanged (URL, `Đóng`, return to `/`)
- [ ] `WIDGET_STANDARDS_LABEL` still asserted, value unchanged
- [ ] FUN_003b and all other tests in the file untouched
- [ ] Constants docblock reflects the two-step path
- [ ] `the-le` suite green in `anon` once phase 03 lands

## Success Criteria

- `git diff e2e/the-le.spec.ts` touches only FUN_003 and its comment.
- `git diff e2e/fixtures/the-le-constants.ts` shows comment lines only — no value line.
- `npx playwright test e2e/the-le.spec.ts --project=anon` exits 0 (verified in phase 05).

## Risk Assessment

| Risk | L×I | Countermeasure |
|------|-----|----------------|
| Assertions weakened to make the test pass sooner | M×H | Post-click block must be byte-identical; the diff review in phase 05 checks it |
| Someone adds a hidden `/standards` link to keep the old locator | L×H | Explicitly rejected in clarifications; phase 03's success criteria cap the testid set |
| `WIDGET_STANDARDS_LABEL` deleted as "unused" after the locator swap | M×M | Kept load-bearing via the accessible-name assertion |
| Written before phase 03 and mistaken for a regression when red | M×L | Dependency stated: red until 03 lands is expected, not a defect |

## Security Considerations

- Test-only change; no product code, no auth surface, no data written.
- Runs anonymously in `anon`; `/standards` is a public route, so no credential is introduced.

## Next Steps

- Feeds phase 05, which reruns this suite as the regression half of the GREEN evidence.
- Rollback: revert together with phase 03.
