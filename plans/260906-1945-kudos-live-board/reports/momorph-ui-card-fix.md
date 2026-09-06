# Card fix — chip overflow, justification check, attachment wrap

Mode: section. Policy: e2e-red-first — pre-established GREEN preserved, no
new behavior/hooks.

## Files

- `sunner-chip.tsx` — chip is `w-full max-w-xs` (stacked) below a
  container-query threshold, `w-[235px] shrink-0` (frame-exact) at/above it.
- `kudos-card.tsx` — `<article>` is now `@container`; the Info-user row and
  glyph wrapper switch on `@[630px]:` (card's own width), not a viewport
  breakpoint.
- `kudos-attachments.tsx` — row gained `flex-wrap`.

## Defect 1 — chip overflow

Measured (`get_node`/`query_component`, `MaZUn5xHXZ`): sender/receiver chip
`I3127:21871;256:4858` = 235px fixed; glyph `256:5161` = 32px; row
`I3127:21871;256:4857` = 600px, `gap:24px`. Minimum content to avoid overlap:
235+235+32+2×24 = **550px**. Feed card padding (measured, `sm:px-10`) = 80px
→ **630px** card-width switch point.

Used a Tailwind v4 native `@container` query (`container-type: inline-size`,
confirmed in `node_modules/tailwindcss/dist/lib.js`) on the card `<article>`
instead of a viewport breakpoint (`sm:`/`lg:`). Reason: the two-column ALL
KUDOS row (`all-kudos-section.tsx`, off-limits) applies `lg:shrink` to the
feed column, so the feed card's *rendered* width dips well below 630px in a
range of viewports between `lg` (1024px) and roughly 1281px — a fixed
viewport breakpoint would still overflow there. A container query reads the
card's actual box, so it can't miss that window. Below 630px card width, the
row stacks (`flex-col`, centered) and each chip goes full-width capped at
`max-w-xs` — name/department/badge wrap normally, no `nowrap` on any of them
except the badge (short text, doesn't hit the cap). 1440px is unaffected:
feed card content there is 600px, well past the switch.

`kudos-attachments.tsx`: 5×88px + 4×16px gap = 504px fits the corrected
680px feed column's 600px content in one row (unchanged, matches the frame).
Added `flex-wrap` only as a safety net for narrower card widths — confirmed
needed: at 375px viewport the attachment row also wraps into 2 columns
rather than clipping.

## Defect 2 — justification: investigated, NOT changed

The task's premise ("frame sets ragged-right body copy") is contradicted by
direct measurement. Queried the frame's own message-body node,
`I3127:21871;256:5156` (feed instance) and its highlight-carousel
counterparts (`I2940:1346{4,5,6};662:12223`) via `get_node`/
`query_component` — **all** carry `textAlignHorizontal: JUSTIFIED`, not
LEFT. Per `code-rules.md` rule 3 ("`JUSTIFIED` → `text-align: justify` ...
DO NOT default to left/start"), the existing `text-justify` in
`kudos-card.tsx` is pixel-correct to the frame. Per the MoMorph rule "never
guess a visual value — MCP data is authoritative," I left it unchanged
rather than remove it on the readability argument alone. Flagged below.

## Verification

- `npm run typecheck` — exit 0.
- `npm run lint` — exit 0 (same pre-existing 21 `e2e/*.spec.ts` warnings,
  none in owned files).
- `npx playwright test e2e/kudos-live-board.spec.ts e2e/kudos-live-board-authed.spec.ts --reporter=list`
  — **27 passed**, 0 failed (killed a stray leftover `next dev` holding
  port 3000 first so the config's own `webServer` could start it).
- Overflow proof (`scratchpad/verify-overflow.mjs`, real page, `npx supabase db reset` run first):
  - `375×800` → `scrollWidth=375 clientWidth=375` (equal, zero overflow).
  - `1440×900` → `scrollWidth=1440 clientWidth=1440` (equal, zero overflow);
    feed box `{x:144,width:680}`, sidebar box `{x:874,width:422}` — exact
    match to nodes `2940:13482`/`2940:13488`, unchanged.
- Screenshots overwritten on the reset DB: `evidence/all-kudos-sidebar-row-desktop.png`
  (sender + receiver both fully visible, badges legible, 5 attachments in
  one row) and `evidence/all-kudos-sidebar-row-mobile.png` (chips stacked,
  fully legible, attachments wrap 2-per-row, no clipping).

## Unresolved / concerns

1. **Defect 2 not applied** — see above. If the orchestrator wants ragged-
   right despite the frame specifying justified, that's a deliberate
   deviation from measured design data and should be recorded in
   `clarifications.md` (out of my authority to add unilaterally), not
   silently coded.
2. **Heart count is 52, not 1.000, on the frame-verbatim card** (same
   sender/receiver/message text as the design) in the ALL KUDOS feed, even
   on a freshly reset DB (`npx supabase db reset` run before this suite and
   before the screenshots). This isn't defect 1/2 and isn't in an owned
   file — `heart_baseline`/seed values live in `supabase/seed.sql` and
   `lib/kudos/*`, both off-limits here. Recorded, not touched.
3. Pre-existing React "unique key" console warning (noted by the prior
   layout-fix report) still appears in the dev console during this run —
   unrelated to owned files, not re-investigated.
