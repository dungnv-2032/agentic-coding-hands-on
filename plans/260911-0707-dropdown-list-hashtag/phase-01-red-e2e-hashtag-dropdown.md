# Phase 01 — RED e2e for the stateful hashtag dropdown

test_policy: e2e-red-first
owner: tester · status: pending · priority: P1 · effort: 1h · depends on: —

## Context links

- `spec/dropdown-list-hashtag/spec-delta.md` — FR-207..FR-211 + acceptance criteria (requirement source)
- `clarifications.md` — resolved decisions
- MoMorph: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/p9zO-c4a4x
- Files under test: `app/kudos/new/_components/hashtag-picker.tsx` (phase 02 changes it)

## Overview

Write the durable screen-level E2E assertions for the toggle/selected/cap behavior **before** any UI
code exists, and record a valid RED. Tests only — no app code in this phase.

## Key insights

1. **A `disabled` button cannot be clicked in Playwright.** `.click()` on it waits for actionability
   and fails on timeout (15s in the `kudos-authed` project) with a misleading error. The cap tests
   must therefore **assert `toBeDisabled()`**, not click-and-expect-nothing.
2. `data-selected="true"` is already emitted for selected rows, so
   `[role="option"]:not([data-selected="true"])` is a stable "unselected row" locator today.
3. Seed order is fixed and known: positions 1..13 starting `Toàn diện, Giỏi chuyên môn, Hiệu suất
   cao, Truyền cảm hứng, Cống hiến, Aim High, …`. `TEST_HASHTAG_1..5` are positions 1..5, so at the
   cap `options.first()` is a *selected* row — the exact reason ID-17/ID-53 must be re-pointed.
4. ID-16 clicks rows via `hashtagOptions.locator("text=<name>")`. Phase 02 may wrap the label in a
   `<span>`; the text engine matches the element owning the text node, so the locator still resolves
   to one element. ID-16 is the regression tripwire for that.

## Requirements

Functional — one assertion set per FR:

| Test | Covers | Asserts |
|------|--------|---------|
| ID-57 | FR-208 | Click an unselected row → 1 chip. Reopen, click the same row → 0 chips, row no longer `data-selected`. (Today the second click adds a duplicate → RED.) |
| ID-58 | FR-207 | Selected row has `data-selected="true"` and contains `[data-testid="hashtag-check"]`; an unselected row has **no** check but does render `[data-testid="hashtag-check-slot"]` whose bounding box is 24×24. |
| ID-59 | FR-209, FR-210 | At 5 selected: every `[role="option"]:not([data-selected="true"])` is `toBeDisabled()`, `hashtag-error` visible with `HASHTAG_ERROR_FULL`. Then click a **selected** row → 4 chips, `hashtag-error` hidden, unselected rows `toBeEnabled()`. |
| ID-60 | FR-211 | Capture all option labels; toggle one row; reopen; labels identical and equal to `SEEDED_HASHTAG_ORDER`. |
| ID-17 (re-point) | BR-002 | 5 selected, reopen, take the first **unselected** row: `toBeDisabled()`, `hashtag-error` visible + exact text, chips still 5. |
| ID-53 (re-point) | BR-002 | Same as ID-17 at its own location in the error-message suite. |

Non-functional: tests live in the existing `kudos-authed` project, reuse the existing locator
helpers, and add no new fixture files.

**This is a test strengthening, not a weakening.** ID-17/ID-53 previously clicked `options.first()`
— an already-selected row at the cap — which under the frame's toggle semantics means "deselect",
not "add a 6th". Re-pointing them at an unselected row asserts the cap against the row the cap
actually governs, and the new `toBeDisabled()` assertion is strictly additional coverage.

## Architecture

No production change. Two files: the spec and its constants. New locator helpers sit beside the
existing `hashtagMenu` / `hashtagError` helpers at the top of the spec.

## Related code files

- Modify: `e2e/viet-kudo.spec.ts`
- Modify: `e2e/fixtures/viet-kudo-constants.ts`
- Create: none · Delete: none

## Implementation steps

1. In `viet-kudo-constants.ts` add `TEST_HASHTAG_6 = "Aim High"` (seed position 6, always unselected
   in these tests) and `SEEDED_HASHTAG_ORDER` — the 13 seed names in `position` order.
2. In `viet-kudo.spec.ts` add two helpers next to `hashtagError`:
   `hashtagOptionsUnselected(page)` → `hashtagMenu(page).locator('[role="option"]:not([data-selected="true"])')`
   and `hashtagOptionsSelected(page)` → `…locator('[role="option"][data-selected="true"]')`.
3. Add a small `selectTags(page, tags)` helper mirroring the loop ID-16/ID-17/ID-53 already repeat
   (open menu → wait visible → click `text=<tag>`), and use it in the new tests. Do not rewrite the
   existing tests' bodies beyond the re-point in step 5.
4. Add ID-57, ID-58, ID-59, ID-60 in the hashtag describe block, per the table above.
5. Re-point ID-17 and ID-53: replace `hashtagOptions.first().click()` with
   `const blocked = hashtagOptionsUnselected(page).first(); await expect(blocked).toBeDisabled();`
   and keep both existing assertions (error visible + exact text, chips still 5).
6. Leave ID-15 and ID-16 untouched — they are the regression tripwire for phase 02.
7. Record RED: run the command below and capture `redCommand`, `redExitCode`, `redFailure`
   (the failing assertion text), and the report output into `reports/`.

```
npm run test:e2e -- e2e/viet-kudo.spec.ts --project=kudos-authed -g "ID-17|ID-53|ID-57|ID-58|ID-59|ID-60"
```

Prerequisites for a *valid* RED: local Supabase up (API `http://127.0.0.1:54321`) with `seed.sql`
applied, and the Playwright browser available. A failure from a missing browser, a dead dev server,
Supabase being down, or a TypeScript error in the spec is **not** a valid RED — fix the environment
and rerun.

## Todo list

- [ ] Constants added (`TEST_HASHTAG_6`, `SEEDED_HASHTAG_ORDER`)
- [ ] Locator + `selectTags` helpers added
- [ ] ID-57, ID-58, ID-59, ID-60 written
- [ ] ID-17, ID-53 re-pointed with `toBeDisabled()` and existing assertions kept
- [ ] RED run captured with a non-zero exit code and per-test failure reasons
- [ ] `npm run typecheck` clean (the spec compiles)

## Success criteria

- Non-zero exit code caused by the *requested screen assertions* — expected failures:
  ID-57 (second click adds a duplicate chip → count 1 ≠ 0), ID-58 (`hashtag-check-slot` missing),
  ID-59 (unselected rows are enabled; `hashtag-error` absent at the cap), ID-60 (passes today — it is
  a guard against phase 02 introducing hoisting; record it as green and say so),
  ID-17/ID-53 (unselected row is not `disabled`).
- `redTestFiles`, `redCommand`, `redExitCode`, `redFailure` recorded and handed read-only to phase 02.

## Risk assessment

| Risk | L×I | Countermove |
|------|-----|-------------|
| A cap test clicks a disabled row and burns a 15s timeout | Med × Med | Assert `toBeDisabled()`; never click an unselected row at the cap |
| `text=<tag>` becomes ambiguous after phase 02 wraps the label | Low × High | ID-16 left untouched as the tripwire; phase 03 reruns it |
| Suite is slow (~25 min full RED run) | High × Low | Use `-g` to scope the RED run to the six tests |
| ID-60 is green from the start and reads like a no-op | Med × Low | Record it explicitly as a *regression guard*, not a RED expectation |

## Security considerations

None new. Tests run in the existing authenticated `kudos-authed` session; no credentials or data
are added.

## Next steps

Hand `redCommand` / `redExitCode` / `redFailure` to phase 02 read-only. Phase 02 may not modify any
file in `e2e/`.
