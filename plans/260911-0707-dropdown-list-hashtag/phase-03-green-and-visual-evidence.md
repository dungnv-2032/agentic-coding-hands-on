# Phase 03 — GREEN rerun + visual evidence

test_policy: e2e-red-first
owner: tester · status: pending · priority: P2 · effort: 1h · depends on: phase 02

## Context links

- `plan.md`, `phase-01-red-e2e-hashtag-dropdown.md` (RED evidence), `phase-02-ui-stateful-hashtag-rows.md`
- MoMorph: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/p9zO-c4a4x

## Overview

Close the `e2e-red-first` loop: rerun phase 01's exact command GREEN, prove nothing else regressed,
and capture the three menu states as visual evidence. No source edits in this phase — a failure goes
back to phase 02's owner as a bounded fix, never as a weakened test.

## Key insights

- The full `viet-kudo.spec.ts` run is long (~25 min). Run the scoped `-g` command first; only then
  the whole file.
- ID-15 and ID-16 are the regression tripwires for the toggle change and for the label markup.
- `fullyParallel: false` and `reuseExistingServer: false` mean each run boots its own dev server —
  local Supabase must already be up.

## Requirements

1. `npm run test:e2e -- e2e/viet-kudo.spec.ts --project=kudos-authed -g "ID-17|ID-53|ID-57|ID-58|ID-59|ID-60"` → exit 0.
2. `npm run test:e2e -- e2e/viet-kudo.spec.ts --project=kudos-authed` → exit 0 (ID-15/ID-16 included).
3. `npm run lint` and `npm run typecheck` → exit 0.
4. Visual evidence of E13 open, against the frame.

## Architecture

Verification only. Evidence lands in `plans/260911-0707-dropdown-list-hashtag/evidence/`.

## Related code files

- Modify: none
- Create: `evidence/hashtag-menu-empty.png`, `evidence/hashtag-menu-one-selected.png`,
  `evidence/hashtag-menu-at-cap.png`, `reports/tester-green-report.md`
- Delete: none

## Implementation steps

1. Rerun the scoped command; record exit code and per-test results.
2. Run the full spec file; record exit code.
3. `npm run lint`, `npm run typecheck`.
4. With Playwright MCP at 1440px on `/kudos/new`: open the menu and capture (a) nothing selected,
   (b) one row selected — check icon visible, list not reflowed, (c) five selected — unselected rows
   dimmed and inert, `hashtag-error` reading "Tối đa 5 hashtag".
5. Compare each capture against the frame for the selected background `rgba(255,234,158,0.2)`, the
   24×24 check, and `position` row order. Material mismatch → bounded fix back to phase 02.
6. `wc -l app/kudos/new/_components/*.tsx` — confirm the 200-line rule holds.
7. Write `reports/tester-green-report.md`: RED→GREEN pair, both exit codes, evidence paths.

## Todo list

- [ ] Scoped rerun GREEN (same command as the RED)
- [ ] Full `viet-kudo.spec.ts` GREEN, ID-15/ID-16 included
- [ ] lint + typecheck clean
- [ ] Three evidence screenshots captured and compared to the frame
- [ ] 200-line rule verified
- [ ] GREEN report written

## Success criteria

Every acceptance criterion in `spec-delta.md` is demonstrated by a passing test or a screenshot, the
GREEN command is byte-identical to the RED command, and no test was edited to make it pass.

## Risk assessment

| Risk | L×I | Countermove |
|------|-----|-------------|
| A test is "fixed" by relaxing an assertion | Low × High | Any red goes back to phase 02 as a code fix; assertions are frozen after phase 01 |
| `text=<tag>` ambiguity from the new label markup breaks ID-16 | Med × Med | Full-file run is mandatory, not optional; fix belongs in phase 02's markup |
| Flake from the 15s server round trip under contention | Med × Low | Rerun the single test once; a second failure is real, not flake |
| WSL2 missing Chromium libs | Low × High | `.playwright-libs/` shim in `playwright.config.ts` already covers it; verify before calling a failure a RED/GREEN result |

## Security considerations

None. Screenshots show seeded hashtag names only — no personal data beyond the existing test account.

## Next steps

On GREEN: promote `spec-delta.md` into `docs/features/F005_VietKudo/` and
`docs/screens/SCR005_VietKudo/` (doc-writer), then commit on `feat/dropdown-list-hashtag` branched
from `main`.
