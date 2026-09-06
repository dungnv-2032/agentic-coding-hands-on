# Phase 07 — board shell (filters, carousel, feed, toast)

Mode: section. Policy: e2e-red-first — RED validated before editing (redExitCode 1,
25 failed/2 passed, K-0 shows `<h1>Coming soon</h1>` vs expected page title;
`kudos-compose` "element(s) not found" — assertion-caused, page.tsx still the
placeholder. Log read at `evidence/kudos-red-run.log`).

## Files created (all owned, none touched outside the list)
- `kudos-board.tsx` (165L) — the phase's one `"use client"` file: filter state
  (hashtagFilterId/departmentFilterId), activeSlide, pages, toast; the shared
  filter handler (reset slide→0, pages→1 in one update); hashtag-chip handler
  (FR-403); copy handler; renders `highlight-section` + `all-kudos-section` +
  `KudosToast`.
- `kudos-filter-bar.tsx` (113L) — two trigger buttons, `useDismissOnOutside`
  (reused, not copied) for both, single `openMenu` state closes the other on open.
- `kudos-filter-menu.tsx` (60L) — pure listbox, `role="option"` + `aria-selected`.
- `highlight-carousel.tsx` (153L) — `pickHighlight` inside, centre-mode track
  transform (528px slide + 24px gap, measured), 60px + 28px arrow pairs, single
  clamped pagination string.
- `all-kudos-feed.tsx` (67L) — slice by `pages * FEED_PAGE_SIZE`, sentinel
  unmounts once `hasMore` is false.
- `use-infinite-feed.ts` (41L) — `"use client"`, IntersectionObserver in an effect.
- `kudos-toast.tsx` (39L) — auto-dismiss 3s, `role="status"`.

Total 638 lines, all ≤200. Zero imports from `queries.ts`/`board-data.ts`/
`app/kudos/_actions/**`/`@/lib/supabase/*` — verified by grep before writing.

## mm: coverage
kudos-board.tsx ×9, kudos-filter-bar.tsx ×5, kudos-filter-menu.tsx ×3,
highlight-carousel.tsx ×10, all-kudos-feed.tsx ×3, kudos-toast.tsx ×1 (comment
explaining no frame node — same precedent as `IconFlame`/`IconExpand`),
use-infinite-feed.ts ×0 (pure behavior hook, no visual node — matches
`use-award-scroll-spy.ts`).

## Test hooks emitted
`highlight-section`, `all-kudos-section`, `filter-hashtag`, `filter-department`
(both `aria-expanded` always present), `filter-menu-hashtag`, `filter-menu-department`
(`role="listbox"` + `role="option"` + `aria-selected`), `highlight-carousel`,
`highlight-slide` (×≤5, `aria-current="true"` on active only, `aria-hidden="true"`
on the rest, DOM order = `pickHighlight` order, never reordered),
`carousel-prev`/`carousel-next` (60px, disabled at ends), `pager-prev`/`pager-next`
(28px, same disabled rule), `carousel-pagination` (single string `${current}/${total}`,
renders unconditionally, `1/0` when the highlight set empties), `feed-sentinel`,
`kudos-empty` (both sections — HIGHLIGHT: inside the carousel viewport when 0
slides, pager stays mounted; ALL KUDOS: replaces the feed), `toast`.

## MoMorph calls
`get_frame` ×1, `query_section` ×2, `query_component` ×4, `get_node` ×7,
`get_frame_node_tree` (dropdown frame `JWpsISMAaM`) ×1. `get_figma_image` not
called (rule 2 reserves it for missing media-node lookups only; nothing here
needed a raster/SVG export). Design evidence: live MCP node data for the filter
buttons (`2940:13459/60`), dropdown list (`563:8026` + one tag item, `JWpsISMAaM`),
carousel arrows (`2940:13470/68`) and section headers (`2940:13451..458`,
`2940:14221..225`); `clarifications.md` for the 13/50 filter option strings,
palette, and dictionary copy; `design/kudos-live-board.png` for overall layout
context.

**Discrepancy noted, not guessed around:** clarifications.md's palette summary
lists filter button `#1A2527`; the measured node (`2940:13459`) actually carries
`background: rgba(255,234,158,0.10)` + `border: 1px solid #998C5F`. Used the
measured MCP value per rule 1 ("never guess"); flagging in case `#1A2527` was
meant for a different state (hover/focus) not captured in this static frame.

## Prop contract `kudos-board.tsx` expects from phase 09
```ts
import { KudosBoard } from "./_components/kudos-board";
// board: KudosBoardViewModel        — from getKudosBoard()
// copy: {
//   eyebrow: string;                              // dictionary.kudos.eyebrow
//   sections: { highlight: string; allKudos: string }; // dictionary.kudos.sections (spotlight key unused here)
//   filters: dictionary.kudos.filters;             // { hashtag, department }
//   card: dictionary.kudos.card;                   // { copyLink, viewDetail, empty }
//   toast: dictionary.kudos.toast;                 // { copySuccess, copyFailure }
// }
// toggleLike: ToggleKudosLike                     — toggleKudosLike from Track B
<KudosBoard board={board} copy={{ eyebrow: dictionary.kudos.eyebrow, sections: dictionary.kudos.sections, filters: dictionary.kudos.filters, card: dictionary.kudos.card, toast: dictionary.kudos.toast }} toggleLike={toggleKudosLike} />
```
Render `<KudosBoard>` between the hero and the spotlight/sidebar section (page
order: hero → HIGHLIGHT KUDOS → SPOTLIGHT BOARD → ALL KUDOS + sidebar → footer),
so `SpotlightBoard` stays in between the two `<section>`s this component emits —
phase 09 will need to interleave, not just append.

## Verification
- `npm run typecheck` — exit 0, 0 errors repo-wide.
- `npx eslint <7 files>` — clean, 0 warnings/errors.
- `npm run lint` (repo-wide) — 0 errors; 21 pre-existing warnings, all in
  `e2e/*.spec.ts` (tester-owned, unused locator helpers) — none in my files.
- Asset coverage: no new media assets in this phase (icons reused from
  `kudos-icons.tsx`, phase 05).
- `git status --short app/kudos/` shows only new files under `_components/`;
  no phase 05/06/08 file or `page.tsx` touched.
- Suite stays RED after this phase (expected — nothing mounts these components
  until phase 09). Not rerun; tester owns GREEN + visual evidence post-wiring.

## Unresolved questions
1. Filter button color discrepancy above (`#1A2527` vs measured
   `rgba(255,234,158,0.10)`) — used measured value, flag for review.
2. Carousel "centre card prominent, flanks faded" is implemented as a
   translateX track (528px slide + 24px gap, both measured) with flanks at
   opacity-40 + pointer-events-none. The frame's static export shows three
   full-opacity 528px cards side by side (no visible scale/opacity difference
   in the mockup itself), so the faded-flank treatment follows the
   clarifications prose, not a directly observable node value — worth a
   visual check against `kudos-live-board.png` once mounted.
3. No MoMorph node exists for the toast or either empty state — both use
   spec-verbatim copy with hand-picked styling consistent with the frame
   palette; flagged inline with `mm:` comments explaining the absence.
