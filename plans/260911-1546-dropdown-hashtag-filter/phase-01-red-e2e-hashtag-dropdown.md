# Phase 01 — RED e2e for the hashtag dropdown

test_policy: e2e-red-first
owner: tester · status: done · priority: P1 · effort: 1h · depends on: —

## MoMorph refs

- Dropdown Hashtag filter: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/JWpsISMAaM
- fileKey `9ypp4enmFmdK3YAFJLIu6C` · screenId `JWpsISMAaM`
- Clarifications: `plans/260911-1546-dropdown-hashtag-filter/clarifications.md`
- testPolicy: `e2e-red-first`

## Context links

- `spec/dropdown-hashtag-filter/spec-delta.md` — FR-214..FR-219 (requirement source)
- `clarifications.md` — resolved, do not re-open
- Sibling precedent: `plans/260911-1348-dropdown-phong-ban/phase-01-red-e2e-department-dropdown.md` (K-26..K-30)
- Files under test: `app/kudos/_components/kudos-filter-menu.tsx` (phase 02 changes it),
  `kudos-filter-bar.tsx` (phase 02, prop removal), `kudos-board.tsx` (read-only, owns filter state)

## Overview

Write five durable screen-level assertions (K-31..K-35) covering the hashtag listbox: the missing 348px
scroll box (FR-214) and focus glow (FR-215) are real RED; the select/close/filter/toggle behavior
(FR-216..FR-218) already runs and is being locked in. Tests only — no app code in this phase.

## Key insights

1. FR-216/217/218 will likely **pass on first run** — `kudos-board.tsx` already wires `hashtagFilterId`
   correctly. Do not weaken an assertion to force a failure. Write the correct assertion; if it passes
   immediately, record it in the report as a **regression guard**, not a RED expectation (same call the
   sibling plan made for K-28..K-30).
2. FR-214 WILL fail today: `max-h-[348px] overflow-y-auto` sits behind `scrollable`, and
   `kudos-filter-bar.tsx` passes that flag only to the department menu. Computed `max-height` on
   `filter-menu-hashtag` is `none` right now.
3. FR-215 WILL fail today: the option button has no `focus-visible:` rule, so its computed `text-shadow`
   under keyboard focus is `none`.
4. **Focus must arrive by keyboard**, not `locator.focus()` — `:focus-visible` does not match a purely
   programmatic focus on a `<button>` in Chromium. Open the menu with `filterHashtagButton.press("Enter")`
   then `page.keyboard.press("Tab")`; the listbox renders after the trigger in DOM order, so Tab lands on
   the first option.
5. The **contract for the glow is `text-shadow` carrying `rgb(250, 226, 135)`** (= `#FAE287`). Phase 02 is
   bound to that; assert `toContain("rgb(250, 226, 135)")`, never an exact full shorthand string (Chromium
   serializes shadow order/units inconsistently across versions).
6. Card chips render as `#{tag}` — the option label is `Wasshoi`, the card chip text is `#Wasshoi`. Do not
   reuse one string for both.
7. Chip truncation is not a hazard: seed gives each kudos `1 + id % 3` hashtags (max 3) and the card caps
   visible chips at 5 (`kudos-hashtag-row.tsx`), so a matching card always shows its `#Wasshoi` chip.
8. FR-219's "13 options in position order" is already asserted by K-3 (`toHaveText(HASHTAG_OPTIONS)`).
   K-31 only re-proves all 13 stay mounted *inside the bounded box* — do not restate the name list.
9. Card COUNT is not a filter proof: `FEED_PAGE_SIZE` is 10 and the carousel caps at 5, so filtered and
   unfiltered states can both show a full page. Prove narrowing per-card, and prove restoration with an
   exact `kudos-receiver` href round-trip (K-30's method).

## Requirements

All in the `anon` project, appended to `e2e/kudos-live-board.spec.ts` after K-30:

| Test | Covers | Asserts |
|------|--------|---------|
| K-31 | FR-214, FR-219 | `filter-menu-hashtag` computed `max-height` is `348px`, `boundingBox().height` is 348, `scrollHeight > clientHeight` (it really scrolls), and all 13 options are mounted. (Today: `max-height: none` → RED.) |
| K-32 | FR-215 | With keyboard focus on an option (insight 4): computed `text-shadow` contains `rgb(250, 226, 135)`. Hover on a non-selected option still yields `background-color: rgba(255, 234, 158, 0.05)` — unchanged. (Today: `text-shadow: none` → RED.) |
| K-33 | FR-216 | Click the `Wasshoi` option → `filter-menu-hashtag` hidden → every visible `kudos-card` in BOTH `highlight-section` and `all-kudos-section` carries a `kudos-hashtag` with exact text `#Wasshoi`. |
| K-34 | FR-217 | After K-33's selection, reopen the hashtag menu → the `Wasshoi` option has `aria-selected="true"` and its computed `text-shadow` carries the selected glow. |
| K-35 | FR-218 | Baseline sorted `kudos-receiver` hrefs before selecting; select `Wasshoi`, confirm narrowed (K-33's method, condensed); reopen, click `Wasshoi` again → menu closes and the re-captured sorted hrefs deep-equal the baseline. |

Non-functional: reuse the existing helpers (`filterHashtagButton`, `filterMenuHashtag`, `kudosCard`,
`highlightSection`, `allKudosSection`); add new ones beside them in the same file and style. No new fixture
file beyond `kudos-constants.ts`.

## Architecture

No production change. Two files: the spec and its shared constants — identical shape to the sibling plan's
phase 01.

## Related code files

- Modify: `e2e/kudos-live-board.spec.ts`, `e2e/fixtures/kudos-constants.ts`
- Create: none · Delete: none

## Implementation steps

1. In `kudos-constants.ts` add `TEST_HASHTAG = "Wasshoi"` (already entry 8 of `HASHTAG_OPTIONS`; this is
   the named constant the new tests assert against) with a one-line comment recording *why* it was chosen:
   8/69 seeded kudos, position 8 — outside the 6 visible rows.
2. In `kudos-live-board.spec.ts` add locator helpers beside `departmentOption`:
   `hashtagOption(page, name)` → `filterMenuHashtag(page).getByRole("option", { name, exact: true })`, and
   `cardHashtag(card, name)` → `card.getByTestId("kudos-hashtag").filter({ hasText: ... })` matched exactly
   on `#${name}`.
3. Add a section banner comment mirroring the K-26 block, citing `JWpsISMAaM` and FR-214..FR-219.
4. Write K-31 and K-32 (the two genuine REDs).
5. Write K-33, K-34, K-35 (lock-in; mirror K-28/K-29/K-30 structure so the two blocks read alike).
6. `npm run typecheck` — the spec must compile before the RED run counts.
7. Record RED: run the command below; capture `redTestFiles`, `redCommand`, `redExitCode`, and the per-test
   `redFailure` text into a report under `reports/`.

```
npm run test:e2e -- e2e/kudos-live-board.spec.ts --project=anon -g "K-31|K-32|K-33|K-34|K-35"
```

A valid RED is a real non-zero exit caused by these assertions. A dev-server boot failure, a missing
Chromium/browser-install, or Supabase being down is NOT a valid RED — fix the environment and rerun.

Explicitly OUT of scope: any file under `app/`, and `e2e/capture-hashtag-dropdown-visual.spec.ts` (a
different frame — F005 `/kudos/new`).

## Todo list

- [x] `TEST_HASHTAG` constant added with its rationale comment
- [x] `hashtagOption` + `cardHashtag` helpers added
- [x] K-31, K-32, K-33, K-34, K-35 written
- [x] `npm run typecheck` clean
- [x] RED run captured with a real non-zero exit code and per-test failure reasons (K-31, K-32 genuine RED; K-33, K-34, K-35 regression guards)
- [x] `redTestFiles` / `redCommand` / `redExitCode` / `redFailure` written into the report (tester-260911-1556-red-hashtag-filter.md)

## Success criteria

- Non-zero exit caused by the requested assertions — expected failures: K-31 (`max-height` is `none`) and
  K-32 (`text-shadow` is `none` on focus). K-33/K-34/K-35 may pass immediately; if so, the report says so
  explicitly and labels them regression guards.
- RED evidence handed read-only to phase 02. Never `git checkout`/`git stash` in this phase — the sibling
  plan lost its uncommitted tests that way.

## Risk assessment

| Risk | L×I | Countermove |
|------|-----|-------------|
| `locator.focus()` used instead of keyboard Tab, so `:focus-visible` never matches and K-32 stays red after phase 02 | High × High | Insight 4 — drive focus with `press("Enter")` + `keyboard.press("Tab")`; verify the option is `:focus-visible` before asserting the shadow |
| Glow asserted as an exact computed-shadow string and breaking on a Chromium serialization difference | Med × Med | `toContain("rgb(250, 226, 135)")` only |
| Chip assertion matches `#Wasshoi` as a substring of another tag | Low × Med | Exact match on `#${TEST_HASHTAG}`; no bare `hasText` substring |
| K-33/K-35 asserted by raw card count and flaking against the 10/5 page caps | Med × High | Per-card chip equality (K-33) and exact href round-trip (K-35) |
| A green K-33/K-34/K-35 read as "no RED, phase invalid" | Med × Low | Report labels them regression guards; K-31/K-32 carry the RED |
| Uncommitted new tests destroyed before certification | Low × High | No git state commands in this phase; commit the spec before phase 02 starts |

## Security considerations

None new. Anon project, public route, seeded data only.

## Next steps

Hand `redTestFiles` / `redCommand` / `redExitCode` / `redFailure` to phase 02 read-only. Phase 02 may not
modify any file under `e2e/`.
