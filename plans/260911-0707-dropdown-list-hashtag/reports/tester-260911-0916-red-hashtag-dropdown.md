# RED evidence — Dropdown list hashtag (phase 01)

testPolicy: `e2e-red-first` · captured 2026-09-11 by the orchestrator after the phase-01 tester
agent was stopped for looping (see § Process note).

## Strict RED handoff (read-only for phase 02)

- **redTestFiles:** `e2e/viet-kudo.spec.ts`, `e2e/fixtures/viet-kudo-constants.ts`
- **redCommand:** `npm run test:e2e -- e2e/viet-kudo.spec.ts --project=kudos-authed -g "ID-17|ID-53|ID-57|ID-58|ID-59|ID-60"`
- **redExitCode:** `1`
- **redFailure:** 5 failed, 2 passed (2.8m). Every failure is an assertion on the requested screen
  behavior — no dependency, config, browser-install or dev-server failure. Valid RED.

## Per-test results

| Test | Covers | Result | Failing assertion (verbatim) |
|------|--------|--------|------------------------------|
| ID-57 | FR-209 toggle off | **FAIL** | `expect(locator).toHaveCount(expected) failed` — Expected: `0`, Received: `2`. Second click on the same row adds a duplicate instead of deselecting. |
| ID-58 | FR-208 selected state | **FAIL** | `expect(locator).toBeVisible() failed` — Expected: visible. `[data-testid="hashtag-check"]` does not exist yet. |
| ID-59 | FR-210, FR-211 cap | **FAIL** | `expect(locator).toBeDisabled() failed` — Expected: disabled, Received: enabled. |
| ID-17 | BR-002 (re-pointed) | **FAIL** | `expect(locator).toBeDisabled() failed` — Expected: disabled, Received: enabled. |
| ID-53 | BR-002 (re-pointed) | **FAIL** | `expect(locator).toBeDisabled() failed` — Expected: disabled, Received: enabled. Locator resolved to `<button type="button" role="option" aria-selected="false" … opacity-50>#Aim High</button>` — dimmed today but still clickable. |
| ID-60 | FR-212 order | **PASS** | Green before any code change — recorded as a *regression guard* against phase 02 introducing row hoisting, never as a RED expectation. |

Gates alongside the run: `npm run typecheck` clean (exit 0), `npx eslint e2e/viet-kudo.spec.ts`
0 errors (7 warnings, all pre-existing unused imports unrelated to this change).

## Test strengthening, not weakening

ID-17 / ID-53 previously ran `hashtagOptions.first().click()` at the cap. `TEST_HASHTAG_1 =
"Toàn diện"` is seed position 1, so `first()` was an **already-selected** row — under the frame's
toggle semantics that click means "deselect", not "add a 6th". Both are now pointed at the first
*unselected* row and additionally assert `toBeDisabled()`. Both original assertions (error visible,
exact `HASHTAG_ERROR_FULL` text, chips still 5) are kept verbatim. Nothing was removed or softened.

## Orchestrator hardening applied before the run

1. `hashtagOption(page, tag)` added — `locator('[role="option"]').filter({ hasText: tag })`. The
   previous `.locator("text=…")` chain resolves to whichever element owns the text node, so it would
   have returned an inner `<span>` the moment phase 02 wraps the label — and `data-selected` /
   `toBeDisabled()` live on the button, not the label. ID-57/ID-58 now assert on the button.
2. ID-17/ID-53/ID-59 rewired onto the `selectTags` helper the phase file asked for (it had been
   written but left unused, which was also a lint warning).
3. `prefer-const` lint errors on `initialLabels` / `finalLabels` fixed (2 errors → 0).
4. ID-59 now asserts the exact unselected count (`SEEDED_HASHTAG_ORDER.length - 5`) instead of
   `> 0`, and names the concrete 6th seeded tag (`TEST_HASHTAG_6 = "Aim High"`) as disabled.

## Process note

The phase-01 tester agent wrote the tests correctly but then re-ran the scoped command for ~2 hours
without producing a report, with no change to the e2e files after the first ~20 minutes. It did not
answer a status request. Per `orchestration-protocol.md` ("never re-run the same approach; escalate")
it was stopped and the RED verification was completed directly. A single clean run takes 2.8 minutes,
so the loop was not an environment problem — `.next/dev/types/routes.d.ts` had been left truncated by
the kill and was regenerated with `npx next typegen` before the run.

## Unresolved questions

- None. Phase 02 may proceed on this RED.
