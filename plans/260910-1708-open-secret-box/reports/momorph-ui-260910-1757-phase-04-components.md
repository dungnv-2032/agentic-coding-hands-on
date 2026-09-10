# Phase 04 report — Track A presentational components (Open Secret Box)

## What was built

`app/kudos/secret-box/_components/`:

- `secret-box-panel.tsx` (112 lines, Server Component) — the card shell: `<h1>`
  (the page's only heading, FR-101), close-glyph slot, both hairlines, the
  `canOpen`-conditional instruction line / `showSignIn`-conditional sign-in
  prompt sharing that same row, the box slot, and the footer counter via
  `formatBoxCount`.
- `secret-box-opener.tsx` (140 lines, `"use client"`) — the clickable box:
  local `status`/`badge` state (not prop-keyed, per the plan's badge-survival
  risk), real `disabled` + `aria-busy` guard, box art, the glow overlay, and
  the DEC-01 badge overlay on success. Inline error text on failure.
- `secret-box-dismiss.tsx` (55 lines, `"use client"`) — the close glyph,
  reusing `rules-panel-dismiss.tsx`'s `hasHistoryToReturnTo()` idiom verbatim,
  fallback `/kudos` instead of `/`.

`design/geometry.md`'s glow row updated (the one permitted edit outside owned
files) with node `1466:7685`'s re-read offsets and CSS fill values.

## Design evidence

- `plans/260910-1708-open-secret-box/design/geometry.md` (prompt-provided,
  equivalent node-tree artifact) for every other measured value.
- `mcp__momorph__get_node(screenId="J3-4YFIpMM", nodeId="1466:7685")` — one
  live call, re-reading the glow's offsets as the phase file required:
  `546.535 × 546.535`, frame-absolute `x142–651 / y260–806`, background
  `url(...) -102.944px -102.487px / 138.527% 138.527% no-repeat`. Confirms
  `+95 / +108` from the box slot's own origin.
- Assets on disk, verified with `ls`: `box-unopened.png`, `box-glow.png`,
  `close-icon.svg` (all pre-existing, none downloaded by this phase).

## Judgment calls (not measured values — flagged per instructions)

1. **Glow overlay reproduced as raw CSS `background-image`/`size`/`position`**,
   not `next/image` with `object-cover`. Found and followed an existing
   precedent for exactly this class of problem —
   `app/awards-information/_components/award-system-hero.tsx`'s keyvisual —
   which reproduces a Figma non-uniform fill crop with the same technique
   because `object-fit` can't express a scaled, off-center crop. This
   reproduces the measured `138.527%` / `-102.944px -102.487px` values
   exactly rather than approximating with `object-cover`.
2. **Glow overlay kept, not omitted.** The task flagged that
   `box-unopened.png` may already bake in a podium glow, and offered omission
   as an option with reasoning. I could not render/screenshot in this leaf
   session (no browser, no dev server ownership under `visual-contract`), so
   I followed the authoritative design data as instructed ("never guess a
   visual value") rather than guess it should be dropped. **This is the one
   item phase 07's visual diff should specifically check** — if the two glows
   visibly fight, the fix is deleting the `1466:7685` `<div>` block in
   `secret-box-opener.tsx`, nothing else changes.
3. **Box art `alt` reuses `copy.openerLabel`** ("Mở Secret Box") instead of a
   new string. SB-02/SB-A4 both assert `getByAltText(/box|hộp/i)` inside the
   panel, but the dictionary (frozen, phase 02, not touched) has no key for
   it. `openerLabel` already contains the loanword "Box", so the existing
   resolved prop satisfies the regex without inventing new copy or editing
   `lib/i18n/messages/*`.
5. **`canOpen`/`showSignIn` share the instruction row.** The frame draws no
   separate node for the anonymous sign-in prompt (unauthored, per
   clarifications.md), and the two states are mutually exclusive, so one
   conditional slot carries both rather than adding unmeasured geometry.
4. **`copy.badgeAltPrefix` left unconsumed.** Its own docblock says it is for
   an *optional* auxiliary sr-only caption, distinct from the badge `alt`
   (which must equal `rule_items.label` verbatim, and does). Nothing in the
   requirements or e2e spec calls for that caption, so it was left unbuilt
   (YAGNI) rather than inventing a UI element with no test or spec behind it.

## Compile/typecheck

`npm run typecheck` → exit 0, no output.

## Lint

`npm run lint` → exit 0, 30 pre-existing warnings, all in unrelated `e2e/*.spec.ts`
files (unused test vars) — none in owned files, none newly introduced.

## Asset coverage

Manual verification (no `assets.md`/`validate_coverage.py` plan exists for this
phase — assets were pre-downloaded by an earlier phase, not planned by this
one): `ls` confirmed all three referenced paths exist
(`box-unopened.png`, `box-glow.png`, `close-icon.svg`). No new asset was
downloaded or invented.

## TEST_IDS coverage

All seven fixed IDs from `e2e/fixtures/secret-box-constants.ts` present, no
extras: `secret-box-panel`, `secret-box-opener`, `secret-box-badge`,
`secret-box-count`, `secret-box-instruction`, `secret-box-close`,
`secret-box-signin`.

## File sizes

`secret-box-panel.tsx` 112, `secret-box-opener.tsx` 140, `secret-box-dismiss.tsx`
55 — all under the 200-line budget.

## Visual evidence

Not produced by this phase — `testPolicy: visual-contract` for this phase, and
per the phase contract `tester` (phase 07) owns Playwright capture and the
MoMorph-vs-actual comparison. No dev server was started here (another phase
may hold port 3000), and the fixed Playwright command was deliberately not
run, per the task's explicit instruction.

## RED evidence

`not-applicable (visual-contract)` for this phase's own work. The screen's
overall `redEvidence` (`plans/260910-1708-open-secret-box/evidence/red-evidence.md`,
`redExitCode` non-zero on `main h1` locator timeout) was produced by phase 01
and is read-only context here — this phase implemented against it without
re-deriving or re-running it.

## GREEN handoff

`npx playwright test e2e/secret-box.spec.ts --project=secret-box-authed` and
`npx playwright test e2e/secret-box-anon.spec.ts --project=anon`, once phase 06
composes these three components into `app/kudos/secret-box/page.tsx` and
phase 05 supplies `openAction`/`canOpen`/`showSignIn`/`unopenedCount`. These
components alone cannot turn the suite green — they have no page to render
from yet.

## Files changed

- `app/kudos/secret-box/_components/secret-box-panel.tsx` (new)
- `app/kudos/secret-box/_components/secret-box-opener.tsx` (new)
- `app/kudos/secret-box/_components/secret-box-dismiss.tsx` (new)
- `plans/260910-1708-open-secret-box/design/geometry.md` (glow row only, per
  phase instructions — the one permitted edit outside owned files)

**Status:** DONE_WITH_CONCERNS
**Summary:** Built the three owned presentational components exactly to the
measured geometry, with the glow overlay re-read live from `1466:7685` and
reproduced via the codebase's existing Figma-fill-crop CSS technique;
typecheck, lint, all seven testids, and every referenced asset all verify
clean. Marked `DONE_WITH_CONCERNS` rather than `DONE` only because this phase
cannot itself produce visual evidence (no page composed yet, `tester` owns
that in phase 07) and because the glow-vs-baked-in-artwork question genuinely
needs eyes on a render, not another guess from me.
**Concerns/Blockers:** (1) Glow overlay may visually double up with
`box-unopened.png`'s own artwork — flagged above for phase 07's visual diff,
one-line fix if so. (2) These components are inert until phase 05 (action +
booleans) and phase 06 (page composition) land; no GREEN is possible from this
phase alone.
