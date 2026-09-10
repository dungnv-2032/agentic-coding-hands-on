---
phase: 05
title: "GREEN rerun + visual validation"
status: complete
owner: tester
track: gate
test_policy: e2e-red-first
effort: 1h
depends_on: [03, 04]
---

# Phase 05 — GREEN rerun + visual validation

## Context Links

- [phase-01](phase-01-red-e2e-gate.md) — the RED this phase must invert, same command
- [design/geometry.md](design/geometry.md) — the numbers visual validation compares against
- [clarifications.md](clarifications.md) — `get_frame_image` misrenders both FAB frames; the
  thumbnail is NOT a reference
- [evidence/study-context.json](evidence/study-context.json) — AC7, AC8
- Precedent for screenshot evidence: `plans/260905-1153-homepage-saa/evidence/`

## Overview

- **Priority:** P1 — the closing gate.
- **Status:** pending
- Rerun the identical fixed command to GREEN, run the regression suites the conversion could
  touch, run typecheck and lint, and validate the rendered geometry against the measured numbers.
  This phase owns evidence files only — it changes no source file.

## Key Insights

- The command must be **identical** to the RED command, character for character, or the
  RED→GREEN pair proves nothing:
  `npx playwright test e2e/floating-action-button.spec.ts --project=anon`
- Visual validation is numeric here, not perceptual. Both MoMorph FAB frames render the Thể lệ
  drawer instead of the FAB, so a thumbnail diff would compare against the wrong artwork.
  Screenshots are captured as human-readable evidence; the *verdict* comes from measured
  boundingBox and computed-style values versus `design/geometry.md`.
- Blast radius beyond the new spec: `e2e/the-le.spec.ts` (adapted in phase 04) and
  `e2e/homepage.spec.ts` (ID-7 counts the widget structurally). Both must be rerun. No homepage
  test currently locates the widget links by role/name, so no further adaptation is expected —
  confirm rather than assume.
- A material mismatch is not "close enough": it goes back to `momorph-ui-implementer` as a
  bounded fix. Tests are never weakened to close the gap.

## Requirements

Functional:
- AC7: the fixed command exits 0.
- AC8: `npm run typecheck` and `npm run lint` exit 0.
- Regression: `e2e/the-le.spec.ts` and `e2e/homepage.spec.ts` green in `anon`.
- Visual: collapsed and expanded states captured at 1440×1024 and measured against the table
  in `design/geometry.md`.

Non-functional: evidence is reproducible — every command, exit code and measurement recorded
verbatim.

## Architecture

```
fixed command ──> exit 0                     ──┐
the-le + homepage regression ──> exit 0        ├──> evidence/green-evidence.md
typecheck + lint ──> exit 0                    │
measurement pass (boundingBox + computed CSS) ─┴──> evidence/visual-validation.md
screenshots ──> evidence/fab-collapsed-1440.png, evidence/fab-expanded-1440.png
```

Measurement checklist (values from `design/geometry.md`; ±1px tolerance, exact on colour):

| Check | Expected |
|-------|----------|
| collapsed pill | 106×64, radius 100px, bg `rgb(255,234,158)`, shadow `0 4px 4px rgba(0,0,0,.25), 0 0 6px #FAE287` |
| pen glyph in pill | renders dark `#00101A`, not white |
| menu container | 214×224, column, right-aligned children |
| `Thể lệ` | 149×64, radius 4px, bg `rgb(255,234,158)` |
| `Viết KUDOS` | 214×64, radius 4px, bg `rgb(255,234,158)` |
| `Hủy` | 56×56, fully round, bg `rgb(212,39,29)`, icon 24×24 |
| vertical rhythm | 20px between each pair |
| labels | weight 700, 24px/32px, `rgb(0,16,26)`, Montserrat family resolved |
| bottom anchor | collapsed pill and `Hủy` share the same bottom edge |

## Related Code Files

Create (evidence only):
- `plans/260910-0907-floating-action-button/evidence/green-evidence.md`
- `plans/260910-0907-floating-action-button/evidence/visual-validation.md`
- `plans/260910-0907-floating-action-button/evidence/fab-collapsed-1440.png`
- `plans/260910-0907-floating-action-button/evidence/fab-expanded-1440.png`

Modify: none. Delete: none. **No source file may change in this phase** — a needed fix is routed
back to the owning phase.

## Implementation Steps

1. `npx playwright test e2e/floating-action-button.spec.ts --project=anon` — record command,
   exit code, per-test result.
2. `npx playwright test e2e/the-le.spec.ts --project=anon` — FUN_003 green through the new path.
3. `npx playwright test e2e/homepage.spec.ts --project=anon` — confirm no widget-shaped
   regression.
4. `npm run typecheck` then `npm run lint`.
5. Visual capture at 1440×1024: screenshot the collapsed pill, click the trigger, screenshot the
   expanded menu. Write both PNGs into `evidence/`.
6. Measurement pass: collect `boundingBox()` and `getComputedStyle` for every row of the
   checklist; write the measured-vs-expected table to `evidence/visual-validation.md` with a
   PASS/FAIL per row.
7. Write `evidence/green-evidence.md`: the RED reference from phase 01 alongside the GREEN run,
   plus the regression, typecheck and lint results.
8. Any FAIL row or red suite → return a bounded fix request to `momorph-ui-implementer`
   (phase 03) or the owning phase, then rerun from step 1. Do not edit the tests.

## Todo List

- [ ] Fixed command exits 0, all 8 tests pass
- [ ] `the-le` suite green
- [ ] `homepage` suite green
- [ ] `npm run typecheck` exits 0
- [ ] `npm run lint` exits 0
- [ ] Both screenshots captured at 1440×1024
- [ ] Measurement table complete, every row PASS
- [ ] `green-evidence.md` + `visual-validation.md` written

## Success Criteria

- The same command string that exited non-zero in phase 01 exits 0 here, and both runs are quoted
  side by side in the evidence file.
- Every geometry row PASSes within tolerance against `design/geometry.md`.
- All eight acceptance criteria in `evidence/study-context.json` are ticked with a named artifact.
- Zero source-file diff attributable to this phase.

## Risk Assessment

| Risk | L×I | Countermeasure |
|------|-----|----------------|
| Command silently altered (extra flag, different project) so GREEN does not match RED | M×H | Command is quoted verbatim in both evidence files and diffed |
| Sub-pixel layout makes an exact-equality geometry check flap | M×M | ±1px tolerance on boxes, exact only on colours |
| Screenshot compared against the misrendered MoMorph thumbnail | M×M | Verdict is numeric; screenshots are evidence, not the reference |
| A homepage regression is attributed to flakiness and waved through | L×H | Any red run is rerun once; a second red is a defect returned to the owning phase |
| Tester edits component code to close a visual gap | L×H | This phase owns evidence files only; fixes are routed back |
| WSL2 Chromium libs missing → run dies before assertions | M×M | `.playwright-libs/` vendoring in `playwright.config.ts`; an install failure is not a GREEN and not a FAIL of the feature |

## Security Considerations

- Anonymous run; no credentials in commands, output or screenshots.
- Screenshots capture the public homepage only — no session UI, no employee data beyond what the
  public page already renders. Check the captures before committing.
- `proxy.ts` behaviour is observed, never modified; the `/login` redirect is asserted as-is.

## Next Steps

- On all-green: the feature is done. Hand to `reviewer`, then update
  `docs/project-changelog.md` and `docs/screens/SCR002_Homepage/spec.md` via `doc-writer`.
- Rollback path if the feature must be pulled: revert phases 03 + 04 together, then 02, then 01
  (reverting 01 alone would orphan the spec file in the testMatch regex).
