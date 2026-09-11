# Phase 01 — RED e2e for the department dropdown

test_policy: e2e-red-first
owner: tester · status: completed · priority: P1 · effort: 1h · depends on: —

**Incident:** The tester agent ran `git checkout` and destroyed the uncommitted K-26..K-30 tests before certification. The orchestrator restored, re-verified (scoped 6/6, full-file 30/30), and committed them. All reported outcomes are real exit codes.

## Context links

- `spec/dropdown-phong-ban/spec-delta.md` — FR-208..FR-213 (requirement source)
- `clarifications.md` — resolved decisions, do not re-open
- MoMorph: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/WXK5AYB_rG
- Files under test: `app/kudos/_components/kudos-filter-menu.tsx` (phase 02 changes it),
  `kudos-filter-bar.tsx` / `kudos-board.tsx` (read-only, own the open/close + filter wiring)

## Overview

Write five durable screen-level assertions (K-26..K-30) that lock in the department dropdown's frame
fidelity (FR-208/209/213 — genuinely missing) and its filtering behavior (FR-210/211/212 — already runs
in code, just untested), then record a valid RED. Tests only — no app code in this phase.

## Key insights

1. FR-210/211/212 assertions will **fail today for want of test scaffolding, not want of behavior** — the
   filter logic is already correct in `kudos-board.tsx`. A valid RED for those three comes from asserting
   something that has never been asserted, e.g. no prior test reads the receiver-department text or
   `aria-selected` persistence. Do not weaken these into no-ops to force a "real" failure — write the
   correct assertion; if it happens to pass immediately, record it explicitly as a **regression guard**
   (mirrors ID-60 in the sibling hashtag-dropdown plan), not a defect.
2. FR-208/209/213 WILL fail today: `text-left` (not centered), no `cursor-pointer` class, `max-h-80`
   (320px, not 348px) — confirmed by reading `kudos-filter-menu.tsx`.
3. The receiver's department name is NOT inside the `kudos-receiver` testid (that element wraps only the
   name link, per `sunner-chip.tsx`). It's a sibling `<span>` under the same "Frame 477" parent div. Scope
   with `card.getByTestId("kudos-receiver").locator("..").getByText(DEPT, { exact: true })` to read the
   right chip's department and avoid matching the **sender's** department on the same card.
4. Department names collide as substrings ("STVC - R&D" is a prefix of "STVC - R&D - DTR/DPS/AIR/SDX").
   Always match option/department text with `{ exact: true }` or `getByRole("option", { name, exact:
   true })` — never a bare substring locator.
5. `FEED_PAGE_SIZE` is 10 (`lib/kudos/derive.ts`) and the highlight carousel caps at 5 slides regardless
   of total count (K-4) — so raw visible-card COUNT does not reliably shrink when filtering 69 kudos down
   to 12 (both states can still show a full page). Prove "narrows to the subset" by asserting every
   *visible* card's receiver department equals the target, not by counting cards.
6. To prove "re-click restores the full board" deterministically (without relying on the department mix
   of the first page, which is seed-order dependent), capture a baseline **before** selecting — the sorted
   list of every visible `kudos-receiver` `href` — and assert it round-trips exactly after select + re-click.

## Requirements

One assertion set per FR, all in the `anon` project (`kudos-live-board.spec.ts`):

| Test | Covers | Asserts |
|------|--------|---------|
| K-26 | FR-208, FR-209 | Every department option's computed `text-align` is `center`; computed `cursor` is `pointer`. (Today: `left` / `default` → RED.) Also spot-checks a hashtag option to confirm the shared-component fix applies there too. |
| K-27 | FR-213 | `filter-menu-department`'s computed `max-height` is `348px` (or its `boundingBox().height <= 348`), scrollable, with all 50 options mounted (regression guard alongside K-3). (Today: 320px → RED.) |
| K-28 | FR-210 | Click the "STVC - R&D" option → menu closes (`filter-menu-department` hidden) → every visible `kudos-card` in BOTH `highlight-section` and `all-kudos-section` has receiver department text exactly "STVC - R&D". |
| K-29 | FR-211 | After K-28's selection, reopen the department menu → the "STVC - R&D" option still has `aria-selected="true"` and is visible with its selected styling class present. |
| K-30 | FR-212 | Capture baseline: sorted `kudos-receiver` hrefs across the whole page before selecting. Select "STVC - R&D", confirm narrowed (per K-28's method). Reopen, click "STVC - R&D" again → menu closes, department filter clears, sorted hrefs equal the baseline exactly. |

Non-functional: reuse existing locator helpers (`filterDepartmentButton`, `filterMenuDepartment`,
`kudosCard`, `highlightSection`, `allKudosSection`); add new ones beside them, same file, same style. No
new fixture files beyond `kudos-constants.ts`.

## Architecture

No production change. Two files: the spec and its shared constants — same shape as the sibling
`dropdown-list-hashtag` plan's phase 01.

## Related code files

- Modify: `e2e/kudos-live-board.spec.ts`
- Modify: `e2e/fixtures/kudos-constants.ts`
- Create: none · Delete: none

## Implementation steps

1. In `kudos-constants.ts` add `TEST_DEPARTMENT = "STVC - R&D"` (already present as an entry in
   `DEPARTMENT_OPTIONS`; this is just the named constant the new tests assert against).
2. In `kudos-live-board.spec.ts` add locator helpers beside the existing filter helpers:
   `departmentOption(page, name)` → `filterMenuDepartment(page).getByRole("option", { name, exact: true })`,
   and a `receiverDepartment(card, page)` helper implementing insight 3 above.
3. Add K-26 (computed style on one department option + one hashtag option), K-27 (computed max-height /
   bounding box on `filter-menu-department`).
4. Add K-28: click `filterDepartmentButton`, click `departmentOption(page, TEST_DEPARTMENT)`, assert menu
   hidden, then assert `receiverDepartment` equals `TEST_DEPARTMENT` for every card under
   `highlightSection` and every card under `allKudosSection` (`Locator.all()` + a loop, or
   `evaluateAll` reading each department span's text and checking they're all equal to the target).
5. Add K-29: reuse K-28's selection flow, reopen the department trigger, assert
   `departmentOption(page, TEST_DEPARTMENT)` has `aria-selected="true"`.
6. Add K-30: capture baseline hrefs via `page.getByTestId("kudos-receiver").evaluateAll(els =>
   els.map(el => el.getAttribute("href")).sort())` before opening the menu; select; assert narrowed
   (K-28's method, condensed); reopen; click the same option; assert menu closed and the re-captured
   sorted hrefs array deep-equals the baseline.
7. Record RED: run the command below; capture `redCommand`, `redExitCode`, and the per-test `redFailure`
   text into a tester report under `reports/`.

```
npm run test:e2e -- e2e/kudos-live-board.spec.ts --project=anon -g "K-26|K-27|K-28|K-29|K-30"
```

A valid RED is a real non-zero exit caused by these five assertions. A dev-server boot failure, a missing
Chromium/browser-install, or a Supabase-down error is NOT a valid RED — fix the environment and rerun.

## Todo list

- [ ] `TEST_DEPARTMENT` constant added
- [ ] `departmentOption` + `receiverDepartment` locator helpers added
- [ ] K-26, K-27, K-28, K-29, K-30 written
- [ ] RED run captured with a non-zero exit code and per-test failure reasons
- [ ] `npm run typecheck` clean (the spec compiles)

## Success criteria

- Non-zero exit caused by the requested assertions — expected failures: K-26 (`text-align`/`cursor` wrong),
  K-27 (max-height is 320px not 348px). K-28/K-29/K-30 may pass immediately since the underlying logic
  already works — if so, record them explicitly as regression guards, not RED expectations, and say so in
  the report.
- `redTestFiles`, `redCommand`, `redExitCode`, `redFailure` recorded and handed read-only to phase 02.

## Risk assessment

| Risk | L×I | Countermove |
|------|-----|-------------|
| K-28/K-30's "narrows"/"restores" logic is asserted by raw card count and flakes because both states can hit the 10/5 page cap | Med × High | Assert per-card department text equality (K-28) and an exact href-set round-trip (K-30), never raw counts |
| Substring collision between "STVC - R&D" and its sub-departments | Med × High | `exact: true` on every department name locator |
| `max-h-[348px]` read as a computed pixel value differs by rounding | Low × Med | Accept `boundingBox().height <= 348` as the assertion, not a strict `===` |
| Full suite runtime | Low × Low | Scope the RED run with `-g` to the five new tests |

## Security considerations

None new. Anon project, no auth, no new data.

## Next steps

Hand `redCommand` / `redExitCode` / `redFailure` to phase 02 read-only. Phase 02 may not modify any file
in `e2e/`.
