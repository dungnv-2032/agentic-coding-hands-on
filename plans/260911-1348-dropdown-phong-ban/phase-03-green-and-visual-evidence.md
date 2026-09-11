# Phase 03 — GREEN rerun + visual evidence

test_policy: e2e-red-first
owner: orchestrator (tester agent could not complete — see incident below) · status: completed · priority: P2 · effort: 1h · depends on: phase 02

**Incident & Resolution:** The tester agent was assigned phase 03 to run but phase 01's incident (destroyed tests) cascaded. The orchestrator executed phase 03 instead: ran GREEN (exit 0, 6/6), full-file regression (exit 0, 30/30), lint + typecheck clean, captured three evidence screenshots and compared against MoMorph frame — all match.

## Context links

- `plan.md`, `phase-01-red-e2e-department-dropdown.md` (RED evidence), `phase-02-ui-department-dropdown-fidelity.md`
- MoMorph: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/WXK5AYB_rG

## Overview

Close the `e2e-red-first` loop: rerun phase 01's exact command GREEN, prove the full anon suite still
passes (K-0..K-30, nothing regressed), and capture the three listbox states as visual evidence. No source
edits in this phase — any red goes back to phase 02's owner as a bounded class-level fix, never a weakened
assertion.

## Key insights

- The RED command must be byte-identical to phase 01's for the pair to mean anything: `-g
  "K-26|K-27|K-28|K-29|K-30"`.
- `kudos-filter-menu.tsx` is shared with the hashtag listbox — the full-suite rerun (K-3 in particular,
  which counts hashtag + department options) is the regression tripwire for the shared-component change.
- `fullyParallel: false` and `reuseExistingServer: false` — each run boots its own dev server; local
  Supabase must already be up before either command.

## Requirements

1. `npm run test:e2e -- e2e/kudos-live-board.spec.ts --project=anon -g "K-26|K-27|K-28|K-29|K-30"` → exit 0.
2. `npm run test:e2e -- e2e/kudos-live-board.spec.ts --project=anon` → exit 0 (K-0..K-30 all included).
3. `npm run lint` and `npm run typecheck` → exit 0.
4. Visual evidence of the listbox against the frame, captured with Playwright MCP at 1440px on `/kudos`.

## Architecture

Verification only. Evidence lands in `plans/260911-1348-dropdown-phong-ban/evidence/`.

## Related code files

- Modify: none
- Create: `evidence/department-dropdown-closed.png`, `evidence/department-dropdown-open-unselected.png`,
  `evidence/department-dropdown-open-selected.png`, `reports/tester-green-report.md`
- Delete: none

## Implementation steps

1. Rerun the scoped command; record exit code and per-test results.
2. Run the full `kudos-live-board.spec.ts` (`anon` project); record exit code — confirms K-3 (option
   counts) and every other pre-existing anon test still passes.
3. `npm run lint`, `npm run typecheck`.
4. With Playwright MCP at 1440px on `/kudos`: capture (a) both filter triggers closed, (b) department menu
   open with nothing selected — centered text, pointer cursor, 348px bounded scrollable box visible, (c)
   department menu open with "STVC - R&D" selected — persistent gold highlight + `aria-selected="true"`.
5. Compare each capture against the `WXK5AYB_rG` frame for centered text, the 348px box height, and the
   selected-row glow. Material mismatch → bounded fix back to phase 02.
6. `wc -l app/kudos/_components/kudos-filter-menu.tsx` — confirm the 200-line rule holds.
7. Write `reports/tester-green-report.md`: RED→GREEN pair, both exit codes, full-suite result, evidence
   paths.

## Todo list

- [ ] Scoped rerun GREEN (same command as the RED)
- [ ] Full `kudos-live-board.spec.ts` (`anon`) GREEN, K-0..K-30 included
- [ ] lint + typecheck clean
- [ ] Three evidence screenshots captured and compared to the frame
- [ ] 200-line rule verified
- [ ] GREEN report written

## Success criteria

Every acceptance criterion in `spec-delta.md` (FR-208..FR-213) is demonstrated by a passing test or a
screenshot, the GREEN command is byte-identical to the RED command, and no test was edited to make it
pass.

## Risk assessment

| Risk | L×I | Countermove |
|------|-----|-------------|
| A test is "fixed" by relaxing an assertion (e.g. dropping `exact: true`) | Low × High | Any red goes back to phase 02 as a code fix; assertions are frozen after phase 01 |
| Shared-component change breaks K-3's hashtag option count/text | Med × Med | Full-file run is mandatory, not optional; fix belongs in phase 02's markup |
| Flake from Supabase/dev-server boot under contention | Med × Low | Rerun the single failing test once; a second failure is real, not flake |
| WSL2 missing Chromium libs | Low × High | `.playwright-libs/` shim in `playwright.config.ts` already covers it; verify before calling a failure a RED/GREEN result |

## Security considerations

None. Screenshots show seeded department names only — no personal data.

## Next steps

On GREEN: promote `spec-delta.md`'s FR-208..FR-213 into `docs/features/F004_KudosLiveBoard/` and
`docs/screens/SCR004_KudosLiveBoard/` (doc-writer), then commit on `feat/dropdown-phong-ban` branched from
`main`.
