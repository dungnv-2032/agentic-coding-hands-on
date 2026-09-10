---
phase: 04
title: "Track A — presentational screen components"
status: complete
owner: momorph-ui-implementer
track: A
test_policy: e2e-red-first
effort: 2h
depends_on: [01, 02]
momorph_screens: ["J3-4YFIpMM"]
momorph_file_key: 9ypp4enmFmdK3YAFJLIu6C
---

# Phase 04 — Track A: presentational screen components

## MoMorph refs

- Open secret box- chưa mở: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/J3-4YFIpMM
  (frame `1466:7676`)
- Clarifications: `plans/260910-1708-open-secret-box/clarifications.md`
- testPolicy: **e2e-red-first** — the RED was taken in phase 01; this phase does **not** own
  executable tests or browser evidence. `tester` owns both (phase 07).
- RED contract (read-only): `redTestFiles: ["e2e/secret-box.spec.ts", "e2e/secret-box-anon.spec.ts"]`,
  `redCommand: npx playwright test e2e/secret-box.spec.ts --project=secret-box-authed`,
  `redExitCode`/`redFailure`/`redEvidence`: see `evidence/red-evidence.md` written by phase 01.

## Context Links

- [design/geometry.md](design/geometry.md) — **the only source of visual values**
- [clarifications.md](clarifications.md) · [functional-spec](spec/open-secret-box/functional-spec.md)
  FR-101..FR-105, FR-203, FR-301, SM-001
- [phase-02](phase-02-shared-contract.md) — `SecretBoxCopy`, `OpenSecretBoxResult`, `formatBoxCount`
- Dismiss idiom to reuse: `app/standards/_components/rules-panel-dismiss.tsx`
- Component style precedent: `app/profile/_components/profile-stats-card.tsx` (mm: comments, tokens)

## Overview

- **Priority:** P1 — this is the screen.
- **Status:** pending
- Three presentational files under `app/kudos/secret-box/_components/`: the card shell, the client
  box control, and the close glyph. They receive **already-resolved props** — numbers, booleans,
  strings and one injected action — and read nothing from Supabase. Phase 06 composes them.

## Key Insights

- **Use the Figma design content as the mock data source. Do NOT invent data.** Anything the frame
  does not state is `NEEDS_CONTEXT`, not a judgement call — except the three decisions the plan
  already fixed (DEC-01 badge overlay, DEC-02 page shell, DEC-03 is not this phase's).
- **Node `1466:7685`'s offsets are not in `design/geometry.md`.** Re-read that node with `get_node`
  before positioning the glow. Do not eyeball it against the artwork.
- `box-unopened.png` is the *full composed* artwork (podium included) at `1000×1000`; it fills the
  `557×557` slot. Do not compose a podium separately.
- The `<h1>` must sit **inside `<main>`** (K-21 asserts `main h1`), so the panel renders the title
  as the page's only `h1`, and phase 06 wraps the panel in `<main>`.
- This is a **route**, not a modal: no `role="dialog"`, no focus trap, no `aria-modal`. The close
  glyph is a navigation control, matching `rules-panel-dismiss.tsx`.
- The inert state has three causes (anonymous, no `sunners` row, zero boxes) and one appearance,
  differing only by the sign-in link. Model it as two booleans in props (`canOpen`,
  `showSignIn`) — never re-derive identity inside a component.
- After a successful open, `revalidatePath` refreshes the server props while the client component
  keeps its badge in local state. That state must **not** be keyed off a prop, or the refresh will
  wipe the badge the user just won.
- Counter formatting comes from `formatBoxCount` (phase 02). Do not re-implement padding here.

## Requirements

Functional:
- FR-101 title `KHÁM PHÁ SECRET BOX CỦA BẠN` as the sole `<h1>`, `data-testid="secret-box-panel"` on
  the card.
- FR-102 instruction line rendered **only** when `canOpen` is true (`secret-box-instruction`).
- FR-103 box slot shows `box-unopened.png` plus the `box-glow.png` overlay; after a successful open
  it additionally shows the awarded badge per DEC-01 (`secret-box-badge`, `alt` = the label).
- FR-104 footer row: label + `formatBoxCount(unopenedCount)` (`secret-box-count`).
- FR-105 when `showSignIn`, a link to `/login` (`secret-box-signin`); the opener is not operable.
- FR-203 while the action is in flight the opener is `disabled` and `aria-busy="true"`; a second
  click cannot start a second call.
- FR-301 close glyph (`secret-box-close`, 19×19, `/images/rules/close-icon.svg`):
  `navigation.canGoBack` with the `history.length > 1` fallback → `router.back()`, else
  `router.push("/kudos")`.
- A failed open surfaces `copy.errorGeneric` inline and re-enables the opener; `reason: "no-boxes"`
  sets the count to `0` from the server's answer rather than guessing.

Non-functional: every file under 200 lines, kebab-case names, `mm:<nodeId>` comments beside each
element, no new dependency, `npm run typecheck` and `npm run lint` exit 0.

## Architecture

```
SecretBoxPanel  (server-safe, presentational)          mm:1466:7676
├─ <h1 data-testid=… >{copy.title}</h1>                mm:1466:7678
├─ {closeSlot}   ← SecretBoxDismiss injected by page   mm:1466:7679
├─ <div hairline/>                                     mm:1466:7680
├─ {canOpen && <p data-testid="secret-box-instruction">} mm:1466:7683
├─ {boxSlot}     ← SecretBoxOpener injected by page    mm:1466:7684
├─ <div hairline/>                                     mm:1466:7688
└─ footer row: label + formatBoxCount(unopenedCount)   mm:1466:7689/7692/7693

SecretBoxOpener ("use client")
├─ props: { canOpen, copy, openAction: () => Promise<OpenSecretBoxResult> }
├─ state: status "idle" | "pending" | "error", badge: SecretBoxBadge | null   (local, not prop-keyed)
└─ <button disabled={!canOpen || status==="pending"} aria-busy={status==="pending"}>
     box art + glow (+ badge overlay once won)

SecretBoxDismiss ("use client") — canGoBack → back(), else push("/kudos")
```

Visual contract — every value from [design/geometry.md](design/geometry.md), none invented:

| Element | Value |
|---------|-------|
| card | `651.5 × 822.6` max, radius `12.73`, bg `#00101A`, padding `23.87 / 12.73`, column, gap `22.28` |
| title | Montserrat 700, `25.46/31.82`, centered, `#FFEA9E`, width `626` |
| close glyph | `19 × 19`, top-right (x `606–625`, y `39–58` within the card) |
| hairlines | `626 × 1`, `#2E3940` |
| instruction / count label | Montserrat 700, `12.73/19.09`, letter-spacing `0.398`, white |
| box slot | `557 × 557` |
| footer row | row, gap `6.36`, `174 × 35`, centered |
| count value | Montserrat 700, `28.64/35.0`, `#FFEA9E` |
| badge overlay (DEC-01) | 50% of the slot width, centered, box art retained beneath |

## Related Code Files

Create: `app/kudos/secret-box/_components/secret-box-panel.tsx`,
`app/kudos/secret-box/_components/secret-box-opener.tsx`,
`app/kudos/secret-box/_components/secret-box-dismiss.tsx`.

Read for context: `design/geometry.md`, `lib/secret-box/contract.ts`,
`lib/i18n/messages/vi-secret-box.ts`, `app/standards/_components/rules-panel-dismiss.tsx`,
`app/profile/_components/profile-stats-card.tsx`, `e2e/fixtures/secret-box-constants.ts` (the fixed
testids).

Modify / Delete: none. **Not** this phase: `page.tsx` (phase 06), the action and queries (phase 05),
any i18n file (phase 02), any asset (already downloaded), `playwright.config.ts` or any spec.

## Implementation Steps

1. `get_node` on `1466:7685` for the glow's offsets; record them in `design/geometry.md`'s glow row
   (the one edit this phase makes outside its owned files — it is the shared visual source).
2. Write `secret-box-panel.tsx`: card, title, hairlines, instruction, box slot, footer. Slots for
   the close control and the box control come in as props so the panel stays server-safe.
3. Write `secret-box-dismiss.tsx`, copying the `hasHistoryToReturnTo()` logic from
   `rules-panel-dismiss.tsx` (fallback destination `/kudos`, not `/`).
4. Write `secret-box-opener.tsx`: the button, the two images, the pending guard, the badge overlay,
   the inline error. Every branch driven by props + local state only.
5. Keep `mm:` comments next to each element and state, in the docblock, that the frame's text beats
   the spec CSV (clarifications).
6. `npm run typecheck && npm run lint`.
7. Run the fixed command locally for signal only — phase 07 owns the official GREEN and all visual
   evidence.

## Todo List

- [x] `1466:7685` offsets re-read and recorded before the glow is positioned
- [x] Panel renders the sole `<h1>` and both hairlines at measured values
- [x] Instruction line conditional on `canOpen`
- [x] Opener disabled + `aria-busy` while pending; second click impossible
- [x] Badge state local and not prop-keyed (survives the post-action refresh)
- [x] Close glyph reuses the `canGoBack` idiom, falls back to `/kudos`
- [x] Sign-in link rendered only when `showSignIn`
- [x] `formatBoxCount` imported, not re-implemented
- [x] All seven fixed testids present, no extra ones
- [x] typecheck + lint exit 0; every file under 200 lines
- [x] **DEVIATION RECORDED:** Glow overlay (node `1466:7685`) deliberately not rendered; initial render showed it as an opaque near-black rectangle occluding the box, hairline, and counter; removed per visual capture verdict

## Success Criteria

- SB-01, SB-02, SB-06, SB-09, SB-A1, SB-A2, SB-A4 pass locally once phase 06 has composed the page
  (official verdict is phase 07).
- No file outside `app/kudos/secret-box/_components/**` changes, except the glow row in
  `design/geometry.md`.
- No component imports `@/lib/supabase/*`, `next/headers`, or the Server Action module directly.
- Every measured value in the rendered DOM traces to a row of `design/geometry.md`.

## Risk Assessment

| Risk | L×I | Countermeasure |
|------|-----|----------------|
| Glow positioned by eye because its offsets are absent | **H**×M | Step 1 re-reads `1466:7685` first; guessing is forbidden by rule 1 |
| Badge overlay size invented beyond DEC-01 | M×M | DEC-01 is the whole licence; anything more is `NEEDS_CONTEXT` |
| Badge wiped by the post-action RSC refresh (state keyed off a prop) | M×**H** | Local state rule above; SB-03 and SB-05 both assert the badge survives |
| Double submit slips through because the guard is CSS-only | M×**H** | Real `disabled` attribute plus a status check inside the handler; SB-04 asserts one decrement |
| `<h1>` placed outside `<main>` (the `/standards` shape) → K-21 breaks | M×**H** | DEC-02 and the FR-101 wording; SB-A1 asserts `main h1` |
| Component reaches for the session to decide the inert state | L×**H** | `canOpen` / `showSignIn` arrive as props; no Supabase import allowed here |
| A file crosses 200 lines as the states pile up | M×L | Three files already; split the footer row out before padding one of them |
| Validating against a MoMorph frame thumbnail instead of the numbers | M×M | The verdict is numeric (phase 07); thumbnails are never the reference |

## Security Considerations

- These components receive no session object, no token and no `userId` — only resolved primitives
  and one injected action, which is `app/_page-context.ts`'s boundary rule held exactly.
- The close control's destinations are two fixed literals; nothing is read from the URL, so no
  open-redirect surface (the difference from `/auth/callback`).
- Images are served through `<Image>` with `alt=""`/`aria-hidden` for decoration; the badge image
  carries a real `alt`. No `dangerouslySetInnerHTML` anywhere.
- A failed open must not print the raw error to the user: `copy.errorGeneric` only.

## Deviations from Plan (Recorded in Delivery)

### Glow Overlay Removal (Node 1466:7685)
The plan flagged that the glow offsets (node `1466:7685`) were absent and should be re-read before positioning. They were re-read and the glow was rendered at `+95/+108` with `138.527%` scale. The captured render revealed the `box-glow.png` asset is a dark-backed RGBA image, not a transparent sparkle. At rendered scale it painted an opaque near-black rectangle that overflowed the 557 slot and completely occluded the gift box art, lower hairline, and counter row, making the screen unusable.

The full composed `box-unopened.png` (1000×1000) already includes the sparkle burst as baked-in artwork — re-rendering the glow on top was redundant and destructive. The glow asset is kept on disk (decision is re-checkable) but not rendered.

**Success criterion impact:** Visual-contract testing confirms the card, box art, counter, and badge overlay all render at correct geometry (see `evidence/visual-validation.md`). The omitted glow overlay strengthens rather than weakens the visual contract — the screen is now usable.

### Three Fidelity Fixes (Post-Capture)
After visual capture revealed pixel-level mismatches, three CSS adjustments were made to the `SecretBoxPanel`:

1. **Card height (mm:1466:7676):** The frame declares 822.587px height. Content-driven layout produced 804.11px (six children + five gaps + padding = 804.11). Added `min-h-[822.59px] justify-center` to the card div to hit the exact design height and center content vertically within it — a fixed-size modal rather than a shrink-wrapped box. This closes the 18.48px gap between the measured-content height and the frame's fixed height (SB-A4 validates this).

2. **Box slot responsiveness (mm:1466:7684):** Changed from hard dimensions to `aspect-square w-full max-w-[557px]` — the frame draws 557×557 pixels at the design viewport (1440px), but a hard width on phones (390px) would force horizontal scrolling. Aspect ratio keeps the box square and centered at every width while still measuring exactly 557px at design viewport where tests validate it.

3. **Counter row label wrapping (mm:1466:7689):** The frame's footer row declares 174px width, but the two children (label + value + gap) need 180px total. Figma allows overflow within a frame; CSS flex layout does not. A literal `w-[174px]` wrapped "Secretbox chưa mở" onto two lines. Changed to `flex` with `mx-auto` centering and added `whitespace-nowrap` to the label span to keep it on one line — the row now sizes to its content while staying centered under the box (the 174 was a visual expression of center-alignment, not a rigid constraint).

## Next Steps

- With phase 05, unblocks phase 06 (integration).
- Rollback: these three files are unreferenced until phase 06 lands, so reverting them alone is
  clean; after 06 they must be reverted together.
