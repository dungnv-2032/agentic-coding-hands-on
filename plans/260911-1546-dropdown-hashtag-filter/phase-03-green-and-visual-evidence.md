# Phase 03 — GREEN rerun + visual evidence

test_policy: e2e-red-first
owner: tester · status: done · priority: P2 · effort: 1h · depends on: phase 02

## MoMorph refs

- Dropdown Hashtag filter: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/JWpsISMAaM
- fileKey `9ypp4enmFmdK3YAFJLIu6C` · screenId `JWpsISMAaM`
- Clarifications: `plans/260911-1546-dropdown-hashtag-filter/clarifications.md`
- testPolicy: `e2e-red-first`

## Context links

- `plan.md`, `phase-01-red-e2e-hashtag-dropdown.md` (RED evidence), `phase-02-ui-hashtag-dropdown-scroll-box.md`
- Capture precedent to mirror: `e2e/capture-department-dropdown-visual.spec.ts`
- Sibling precedent: `plans/260911-1348-dropdown-phong-ban/phase-03-green-and-visual-evidence.md`

## Overview

Close the `e2e-red-first` loop: rerun phase 01's exact command GREEN, prove the whole `anon` file still
passes (K-0..K-35 — the shared-component change is the thing being regression-tested), and capture the
three hashtag listbox states as evidence. No source edits in this phase — any red goes back to phase 02 as
a bounded class-level fix, never a weakened assertion.

## Key insights

1. The GREEN command must be byte-identical to phase 01's, `-g` filter included, or the RED/GREEN pair
   proves nothing.
2. `kudos-filter-menu.tsx` is shared, so the full-file rerun is the real regression gate — **K-27** (the
   department 348px box and its 50 options) and **K-3**/**K-8** are the tripwires for the prop removal.
3. `e2e/capture-hashtag-dropdown-visual.spec.ts` already exists and belongs to a **different frame** (F005
   `/kudos/new` picker, MoMorph `p9zO-c4a4x`, evidence under `plans/260911-0707-dropdown-list-hashtag/`).
   Do not open, rename, or overwrite it. This phase creates `e2e/capture-hashtag-filter-visual.spec.ts`.
4. `/kudos` is public, so the new capture project needs **no** `storageState` — unlike the existing
   `hashtag-dropdown-visual-capture` project, which rides the kudos-authed session for `/kudos/new`.
5. `fullyParallel: false` and `reuseExistingServer: false` — each run boots its own dev server; local
   Supabase (`http://127.0.0.1:54321`) must already be up before any command.
6. Geometry must be *proven*, not just photographed: rows are flex children of a scroll container and can
   shrink without the container resizing. Assert `menu.boundingBox().height === 348` and
   `option.boundingBox().height === 56` in the capture spec, exactly as the department capture does.

## Requirements

1. `npm run test:e2e -- e2e/kudos-live-board.spec.ts --project=anon -g "K-31|K-32|K-33|K-34|K-35"` → exit 0.
2. `npm run test:e2e -- e2e/kudos-live-board.spec.ts --project=anon` → exit 0 (K-0..K-35 inclusive).
3. `npm run lint` and `npm run typecheck` → exit 0.
4. Three screenshots at 1440px on `/kudos`, clipped to the listbox plus margin, compared to the frame.

## Architecture

Verification only. A new on-demand Playwright project isolates the capture from the default suite, matching
how every other capture spec in this repo is wired.

## Related code files

- Create: `e2e/capture-hashtag-filter-visual.spec.ts`,
  `evidence/hashtag-filter-closed.png`, `evidence/hashtag-filter-open-unselected.png`,
  `evidence/hashtag-filter-open-selected-scrolled.png`, `reports/tester-green-hashtag-filter.md`
- Modify: `playwright.config.ts` (one new project entry)
- Delete: none

## Implementation steps

1. Rerun phase 01's scoped command verbatim; record the exit code and per-test results.
2. Run the full `kudos-live-board.spec.ts` on `--project=anon`; record the exit code. Confirm K-3, K-8 and
   K-26..K-30 are in the pass list by name, not just by total count.
3. `npm run lint`, `npm run typecheck`.
4. Add to `playwright.config.ts`, directly after the `department-dropdown-visual-capture` entry:
   `{ name: "hashtag-filter-visual-capture", testMatch: /capture-hashtag-filter-visual\.spec\.ts/,
   use: { ...devices["Desktop Chrome"] } }` — no `storageState`, no `dependencies`.
5. Write `e2e/capture-hashtag-filter-visual.spec.ts` mirroring `capture-department-dropdown-visual.spec.ts`
   (same clip helper, same 80px margin, `EVIDENCE_DIR =
   "plans/260911-1546-dropdown-hashtag-filter/evidence"`), capturing at 1440px:
   a. `hashtag-filter-closed.png` — both filter triggers closed.
   b. `hashtag-filter-open-unselected.png` — hashtag menu open, nothing selected; assert
      `menuBox.height === 348` and `rowBox.height === 56` before the shot.
   c. `hashtag-filter-open-selected-scrolled.png` — scroll the box to `Wasshoi` (position 8, below the
      fold), click it, reopen, assert `aria-selected="true"`, then shoot. This frame is the proof that the
      box scrolls rather than cutting options.
6. Run `npx playwright test --project=hashtag-filter-visual-capture` and confirm all three files land.
7. Compare each capture against the `JWpsISMAaM` frame: 348px box height, six visible rows, centred labels,
   selected-row glow. A material mismatch is a bounded fix back to phase 02, never a test edit.
8. `wc -l` on both phase-02 files — confirm the 200-line rule holds.
9. Write `reports/tester-green-hashtag-filter.md`: the RED→GREEN pair with both exit codes, the full-file
   result, and the evidence paths.

## Todo list

- [x] Scoped rerun GREEN, command byte-identical to the RED (6/6 passed, K-31..K-35 all green)
- [x] Full `kudos-live-board.spec.ts` (`anon`) GREEN, K-0..K-35 included (35/35 passed; K-3, K-8, K-26..K-30 verified in pass list)
- [x] lint + typecheck clean (0 errors, 31 pre-existing warnings; typecheck exit 0)
- [x] `hashtag-filter-visual-capture` project added to `playwright.config.ts` (new project entry after department-dropdown-visual-capture)
- [x] `e2e/capture-hashtag-filter-visual.spec.ts` created and passing (1/1 spec passed)
- [x] Three evidence screenshots captured and compared to the frame (three PNGs verified against frame spec: geometry exact, colors/styling match)
- [x] 200-line rule verified on both phase-02 files (59 lines, 112 lines confirmed < 200)
- [x] GREEN report written (tester-260911-1610-green-hashtag-filter.md) with evidence artifacts, post-review fixes recorded

## Success criteria

Every FR-214..FR-219 acceptance criterion is demonstrated by a passing test or a screenshot, the GREEN
command matches the RED command exactly, and no assertion was relaxed to get there.

## Risk assessment

| Risk | L×I | Countermove |
|------|-----|-------------|
| `capture-hashtag-dropdown-visual.spec.ts` (F005 frame) opened or overwritten by mistake | Med × High | Insight 3 — the new file is `capture-hashtag-filter-visual.spec.ts`; the old one is not in this phase's ownership list |
| New project entry collides with the existing `hashtag-dropdown-visual-capture` testMatch | Low × Med | The regexes differ (`-filter-` vs `-dropdown-`); verify with `npx playwright test --list --project=hashtag-filter-visual-capture` |
| Prop removal silently breaks the department box and only the scoped run is executed | Med × High | The full-file run is mandatory, not optional; the fix belongs in phase 02 |
| A test "fixed" by relaxing an assertion (dropping `exact: true`, widening the shadow match) | Low × High | Assertions are frozen after phase 01; red goes back to phase 02 as a code fix |
| `Wasshoi` not reachable in the capture because Playwright does not auto-scroll a clipped shot | Med × Med | Click through the locator (auto-scrolls), then reopen and shoot the reopened, selected state |
| Flake from dev-server/Supabase boot under contention | Med × Low | Rerun the single failing test once; a second failure is real, not flake |
| WSL2 missing Chromium libs read as a test failure | Low × High | `.playwright-libs/` shim in `playwright.config.ts` covers it — verify before calling any result RED or GREEN |

## Security considerations

None. Screenshots show seeded hashtag names and public board content only; no session, no personal data.

## Next steps

On GREEN: promote FR-214..FR-219 from `spec-delta.md` into `docs/features/F004_KudosLiveBoard/` and
`docs/screens/SCR004_KudosLiveBoard/` (doc-writer), then commit on `feat/dropdown-hashtag-filter`.
