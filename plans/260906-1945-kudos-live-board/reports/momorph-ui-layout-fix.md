# Layout fix — DOM order + ALL KUDOS/sidebar row

Mode: section. Policy: e2e-red-first — pre-established GREEN preserved, no
new behavior, no hook renamed.

## Files

- `kudos-board.tsx` (174L) — `spotlightSlot`/`sidebarSlot: ReactNode` props;
  `SpotlightBoard` now renders between the two `<section>`s in the DOM (was
  `order-*` CSS). Delegates ALL KUDOS to a new split file.
- `all-kudos-feed.tsx` (73L) — dropped its own `mx-auto max-w-[1152px] px-*`
  wrapper; width now comes from the parent row.
- `page.tsx` (98L) — removed `order-*`; passes `<SpotlightBoard>`/
  `<KudosSidebar>` as slot props instead of separate `<main>` children.
- `all-kudos-section.tsx` (102L, **new**) — split out to stay ≤200 lines;
  owns the ALL KUDOS header + the feed/sidebar row.

## Defect 1 — DOM order

DOM/tab order now === paint order: hero → highlight → spotlight →
all-kudos(+sidebar) → footer. Proof (`scratchpad/dom-order-check.ts`, live
page, 1440×1000): `highlight-section -> spotlight-section -> all-kudos-section`.

## Defect 2 — two-column row

Measured via `get_node` (`get_figma_image` not needed): `2940:13481` row,
padding `0 144px`; `2940:13482` feed `width:680px` (x:144→824); `2940:13488`
sidebar `width:422px` (x:874→1296). Real gap = 874−824 = **50px** (node's
declared `gap:80px` unused, doesn't match measured position).

First attempt (`lg:max-w-[680px] lg:flex-1` + `lg:w-[422px] lg:shrink-0`)
rendered feed at 392px — narrower than the sidebar, backwards. Root cause:
the header this replaced stacked `max-w-[1152px]` **and** `lg:px-36` on the
*same* box, leaving ~864px real width at `lg`+, not 1152px; `shrink-0` froze
the sidebar at 422 and starved the feed. `kudos-hero.tsx` already documents
the fix for this exact problem — padding on an outer box, `max-w-[1152px]`
cap on an inner box, never both on one element (`award-system-hero.tsx`
pattern). Applied that (`GUTTER_CLASS`/`CAP_CLASS`), plus `lg:basis-[680px]`/
`lg:basis-[422px]` with default `shrink` so both columns degrade together
between `lg` and 1440px. At the frame's own 1440px this now reproduces
680/50/422 with zero shrink — re-measured: `feed {x:144,w:680}`,
`sidebar {x:874,w:422}`, exact match to the two nodes.
Screenshot: `evidence/all-kudos-sidebar-row-desktop.png`.

This wasn't just alignment: `sunner-chip.tsx` (off-limits) hard-codes
`w-[235px] shrink-0` on both sender/receiver chips, no wrap — needs ~630px
minimum. At 392–502px the receiver chip visibly overflowed the card. 680px
clears that with room to spare.

Did not touch `kudos-card.tsx`/`sunner-chip.tsx` (off-limits) or
`highlight-section`'s header — its carousel below is intentionally
edge-to-edge/full-bleed (no `max-w` cap), so that header's inset was never
meant to align with it; left as phase 07 shipped it.

Mobile stacks correctly (feed, then sidebar) — confirmed at 375px
(`evidence/all-kudos-sidebar-row-mobile.png`). Sidebar's own scroll
(`gift-leaderboard.tsx`, unowned) is untouched.

## Checks

- `npm run typecheck` — exit 0.
- `npm run lint` — exit 0, same 21 pre-existing `e2e/*.spec.ts` warnings.
- `npx playwright test e2e/kudos-live-board.spec.ts e2e/kudos-live-board-authed.spec.ts --reporter=list`
  — 26 passed / 1 failed (K-25), twice, same phase-09-documented 2-worker
  contention flake. Isolated `kudos-live-board-authed.spec.ts` reruns: 3/3
  pass (4.2s, 5.0s, 4.2s), matching phase-09's own isolated confirmation.

## Unresolved, out of scope

1. **Pre-existing mobile horizontal-scroll, not caused by this diff.** At
   375px, `scrollWidth` 598 > `clientWidth` 375. Cause: `sunner-chip.tsx`'s
   `w-[235px] shrink-0` chips overflow the card below ~630px — already true
   pre-fix (old single-column wrapper used the same `px-6` mobile padding,
   giving the same 327px card width, math-identical). Desktop 1440px:
   `scrollWidth === clientWidth`, no overflow. Both files off-limits here.
2. **Pre-existing React key warning**, present even in single-worker
   isolated runs (not the K-25 flake). Grepped every `.map()`/`Array.from`/
   `.entries()` in `app/kudos/_components/*.tsx` (owned + unowned) — all
   have proper `key`. Not in phase 09's `kudos-green-run.log`; stack trace
   is minified, source unidentifiable. Recommend a debugger pass.
