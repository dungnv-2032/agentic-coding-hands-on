# Phase 07 — UI: the board (filters, carousel, feed, toast)

**Track:** A (presentational UI) · **Owner:** `momorph-ui-implementer` (activates
`momorph-implement-design`) · **Depends:** 06 · **Effort:** 3h · **test_policy:** `e2e-red-first`

## MoMorph refs:
- Sun* Kudos - Live board: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/MaZUn5xHXZ
- Dropdown Hashtag filter: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/JWpsISMAaM
- Dropdown Phòng ban: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/WXK5AYB_rG
- Clarifications: plans/260906-1945-kudos-live-board/clarifications.md
- testPolicy: e2e-red-first

**Goal** One client boundary holding the filter state that drives both the HIGHLIGHT carousel and
the ALL KUDOS feed, plus the heart and copy-link interactions.

## Context Links

- [plan.md](plan.md) · [phase-01](phase-01-foundation-and-integration-contract.md) (contract) · [phase-06](phase-06-ui-kudos-card-family.md) (cards)
- [test-contract.md](test-contract.md) § Filters, § "Highlight carousel", § "Copy link", § "Supabase amendment"
- [clarifications.md](clarifications.md) filter-semantics decision, top-5 decision, assumption A4
- `e2e/kudos-live-board.spec.ts:218-349` (K-2…K-8), `:394-434` (K-24, K-11), `:520-542` (K-17)
- Patterns to copy: `app/_components/use-dismiss-on-outside.ts`, `app/awards-information/_components/use-award-scroll-spy.ts` (hook split at the 200-line line, hydration rule at `award-category-nav.tsx:24-29`)

## Overview

**Priority:** P1 · **Status:** delivered. The largest phase in Track A and the one that owns the
screen's whole interaction model: filters, paging, infinite scroll, optimistic hearts, toast.

## Key Insights

1. **One client boundary, because one filter drives two sections.** Selecting a hashtag must
   re-filter the carousel *and* the feed and reset paging (settled decision, FR-203), so
   `kudos-board.tsx` is the single `"use client"` component holding
   `{ hashtag, department, slide, pageCount, toast }`. Everything below it inherits the boundary;
   nothing below it needs its own `"use client"`.
2. **DOM order equals data order, and the active slide starts at index 0.** K-4 asserts
   `slides.nth(0)` carries `aria-current="true"` and `slides.nth(count-1)` carries
   `aria-hidden="true"`. So slides render in `pickHighlight` order, the active index starts at 0,
   `aria-current="true"` sits on the active slide only, and **every** non-active slide carries
   `aria-hidden="true"`. The frame's centred-card look is a CSS transform over that fixed DOM
   order, not a reordering.
3. **Pagination text must match `/^\d+\/\d+$/` with no whitespace** (K-5) and must read `1/…`
   immediately after a filter selection (K-8). Render `{current}/{total}` in a single text node
   with the current index clamped to a minimum of 1, so an empty filter result still reads `1/0`
   rather than throwing K-8's `textContent` read. The element renders unconditionally.
4. **`Toàn diện` — the first hashtag option — matches at least three seeded kudos** (phase 03
   § Key Insight 8), so K-8's filtered carousel is genuinely non-empty. Do not add a fallback that
   ignores the filter when the result is empty; render `kudos-empty` instead.
5. **Copy Link needs a failure path.** `technical-spec.md § 5.3` left blocked-clipboard behavior
   open; it is closed here: wrap `navigator.clipboard.writeText` in try/catch, show the success
   toast on resolve and the dictionary's failure toast on reject. Both use
   `data-testid="toast"` — K-11 grants clipboard permission, so it asserts the success text. The
   URL is built in the click handler from `window.location.origin`, never during render (a render
   read of `location` would hydration-mismatch).
6. **The heart needs an optimistic update, or K-10 is flaky.** K-10 reads `aria-pressed` right
   after `click()`. Wrap the call in `startTransition` with `useOptimistic` over
   `{ likedByViewer, hearts }`; because the action calls `refresh()` server-side, the transition
   resolves on the re-rendered tree and the optimistic value never flashes back (phase 04 § Key
   Insight 1).
7. **`aria-expanded` must be present on both filter buttons** (K-2 asserts the attribute exists),
   so it is `"true"`/`"false"`, never omitted. Menus are **conditionally rendered** — K-3 asserts
   `toBeVisible()` after a click, so a permanently mounted hidden menu would need CSS hiding; the
   simpler and less fragile choice is to mount on open.
8. **Options carry `aria-selected` and re-clicking the selected option clears the filter**
   (dropdown spec A.1, toggle semantics). The department menu holds 50 options and must scroll
   inside a bounded box; all 50 stay in the DOM because K-3 counts them.
9. **Both sections need `kudos-empty`.** Scoped locators keep them from colliding: K-17 looks
   inside `all-kudos-section` only.
10. **Infinite scroll is client-side paging over data already fetched** (A4): reveal
    `FEED_PAGE_SIZE` (10, frozen) more rows when `feed-sentinel` enters view, then stop silently at
    the end. `IntersectionObserver` lives in an effect, never in the render body.

## Requirements

**Functional:** FR-202 (carousel, 60px arrows disabled at each end, `2/5` pager with its own 28px
arrows), FR-203 (AND-combined filters over both sections, reset to slide 1, toggle to clear),
FR-206 (feed + infinite scroll + empty state), FR-401 (heart toggle through the action),
FR-402 (copy link + toast), FR-403 (hashtag chip sets the filter).

**Non-functional:** exactly one `"use client"` file in this phase; first client render byte-matches
SSR; every file ≤200 lines with the hook split out like `use-award-scroll-spy.ts` did; no external
state library, no carousel dependency; `mm:{nodeId}` on every arbitrary value.

## Architecture

**Integration contract consumed** (frozen): `KudosBoardViewModel`, `KudosCardView`,
`FilterOptionView`, `ToggleKudosLike`, and from `derive.ts` — `pickHighlight`, `matchesFilters`,
`FEED_PAGE_SIZE`. Nothing added, nothing edited.

```
kudos-board.tsx  "use client"   props { board, copy, toggleLike }
   state { hashtag: number|null, department: number|null, slide: number, pages: number, toast }
   filtered = board.kudos.filter(c => matchesFilters(c, {hashtag, department}))
   ├─ kudos-filter-bar.tsx      buttons + aria-expanded, opens →
   │     └─ kudos-filter-menu.tsx   role="listbox", role="option", aria-selected
   ├─ highlight-carousel.tsx    pickHighlight(filtered) → ≤5 slides, active index, arrows, pager
   │     └─ kudos-card (highlight variant, isActive)         ← phase 06
   ├─ all-kudos-feed.tsx        filtered.slice(0, pages * FEED_PAGE_SIZE) + feed-sentinel
   │     └─ kudos-card (feed variant)                        ← phase 06
   ├─ use-infinite-feed.ts      IntersectionObserver → pages + 1
   └─ kudos-toast.tsx           data-testid="toast"
```

Any filter change sets `slide = 0` and `pages = 1` in the same state update — one reducer-free
handler, so the two sections can never disagree.

**Hooks emitted:** `highlight-section`, `all-kudos-section`, `filter-hashtag`,
`filter-department`, `filter-menu-hashtag`, `filter-menu-department`, `highlight-carousel`,
`highlight-slide`, `carousel-prev`, `carousel-next`, `pager-prev`, `pager-next`,
`carousel-pagination`, `feed-sentinel`, `kudos-empty`, `toast`. Section `h2`s are
`HIGHLIGHT KUDOS` and `ALL KUDOS`, each with a single-leaf `Sun* Annual Awards 2025` eyebrow (K-2
and K-17 use `getByText(exact: true)` scoped to the section, so the eyebrow must be one leaf node).

**Out of scope:** spotlight (08), hero and sidebar (05), the card internals (06), the page shell
and any data read (09), the `SPOTLIGHT BOARD` section wrapper.

## Related Code Files

**Create:** `app/kudos/_components/kudos-board.tsx` · `kudos-filter-bar.tsx` ·
`kudos-filter-menu.tsx` · `highlight-carousel.tsx` · `all-kudos-feed.tsx` ·
`use-infinite-feed.ts` · `kudos-toast.tsx`
**Modify:** none
**Read only:** `lib/kudos/view-model.ts`, `lib/kudos/derive.ts` (frozen), phase 06's card files,
phase 05's icons + dictionary, `app/_components/use-dismiss-on-outside.ts` (reused, not copied)
**Delete:** none

## Implementation Steps

1. Read the two dropdown frames (`JWpsISMAaM`, `WXK5AYB_rG`) plus the carousel and feed nodes of
   the main frame for every visual value.
2. `kudos-filter-menu.tsx` — `role="listbox"` with one `role="option"` per `FilterOptionView`,
   `aria-selected` on each, click handler toggling selection. Bounded height with internal scroll
   for the 50-entry department list; all options stay mounted.
3. `kudos-filter-bar.tsx` — the two `#1A2527` buttons labelled `Hashtag` and `Phòng ban` with
   chevrons and `aria-expanded`; reuse `use-dismiss-on-outside` for outside clicks.
4. `highlight-carousel.tsx` — slides in `pickHighlight` order per Key Insight 2; centre card
   prominent and flanks faded via transform + opacity + `pointer-events-none`; 60px
   `carousel-prev`/`carousel-next` disabled at each end; 28px `pager-prev`/`pager-next` with the
   same rule; `carousel-pagination` as a single clamped text node.
5. `use-infinite-feed.ts` — `"use client"`, `IntersectionObserver` on the sentinel inside an
   effect, increments `pages`, disconnects at the end of the data.
6. `all-kudos-feed.tsx` — the sliced feed, `feed-sentinel` at the tail, `kudos-empty` when the
   filtered set is empty.
7. `kudos-toast.tsx` — one `data-testid="toast"` element, auto-dismissing, rendering whichever
   message the board's state holds.
8. `kudos-board.tsx` — the single `"use client"` file: state, the shared filter handler
   (slide → 0, pages → 1), the heart handler (`useOptimistic` + `startTransition` + `toggleLike`),
   the copy handler (Key Insight 5), the hashtag-chip handler (FR-403), and the two `<section>`
   wrappers with their `h2`s and eyebrows.
9. `npm run typecheck && npm run lint`.

## Todo List

- [ ] Exactly one `"use client"` file in this phase (`kudos-board.tsx`), plus the hook file
- [ ] Slides in data order; `aria-current="true"` on the active slide only; `aria-hidden="true"` on every other slide
- [ ] `carousel-pagination` is one text node matching `^\d+\/\d+$`, current clamped to ≥ 1, rendered unconditionally
- [ ] Filter change sets slide 0 **and** pages 1 in one update; both sections re-filter
- [ ] Re-clicking a selected option clears that filter; `aria-selected` on every option
- [ ] `aria-expanded` always present on both filter buttons; menus mount on open
- [ ] 13 and 50 options respectively, in `position` order
- [ ] Heart: `useOptimistic` inside `startTransition`, `toggleLike` awaited, no local source of truth
- [ ] Copy Link: URL built in the handler from `window.location.origin`; success and failure toasts
- [ ] `feed-sentinel` + `IntersectionObserver` in an effect; stops silently at the end
- [ ] `kudos-empty` in both sections; eyebrow is a single leaf node per section
- [ ] Files ≤200 lines; `mm:{nodeId}` on every arbitrary value
- [ ] `npm run typecheck && npm run lint` clean

## Success Criteria

- Typecheck and lint exit 0.
- With `board.kudos` of 50 rows: 5 slides, pagination `1/5`, `carousel-prev` disabled,
  `carousel-next` enabled; clicking next reads `2/5`.
- Selecting `Toàn diện` leaves both sections filtered, pagination back at `1/…`, and the feed
  showing at most `FEED_PAGE_SIZE` rows.
- The sentinel fires four times over 50 rows and then stops.
- No import from `lib/kudos/queries.ts`, `board-data.ts`, `app/kudos/_actions/**`, or
  `@/lib/supabase/*` — the action arrives only as the `toggleLike` prop.
- First client render matches SSR: no hydration warning in `next dev`.

## Risk Assessment

| Risk | L×I | Countermeasure |
|---|---|---|
| Visual centring implemented by reordering the DOM → K-4's `nth(0)` assertion fails | **High** × High | Key Insight 2 fixes DOM order to data order; centring is a transform only |
| `carousel-pagination` absent when a filter empties the carousel → K-8's `textContent` throws | Med × High | Rendered unconditionally with the current index clamped to ≥ 1 |
| Optimistic value reverts before the refreshed tree arrives → K-10 reads a stale attribute | Med × **High** | `refresh()` inside the action (phase 04) plus `useOptimistic` inside `startTransition`; if flakiness persists, the fix is to await the action's returned `KudosLikeResult` and set state from it — never to weaken the assertion |
| `location.origin` read during render → hydration mismatch | Med × High | Read only inside the click handler, per `award-category-nav.tsx:24-29` |
| `kudos-board.tsx` exceeds 200 lines | **High** × Low | Handlers extracted into `use-infinite-feed.ts` and, if still over, a second `use-kudos-filters.ts` hook in this phase's file set |
| A second `"use client"` creeps in and fragments the filter state | Med × High | One boundary is stated as a requirement; children inherit it |
| 50 department options rendered but visually overflowing the frame's menu | Med × Low | Bounded height with internal scroll; all options stay in the DOM for K-3's count |

**Rollback:** delete the seven files. Nothing mounts them until phase 09.

## Security Considerations

- No data access; the board renders `board` and calls the `toggleLike` prop.
- The clipboard write is a same-origin URL composed from `window.location.origin` and a numeric id;
  no database string reaches a URL position, and the write is wrapped in try/catch so a denied
  permission cannot throw into the render tree.
- The heart handler passes only `card.id`; the server derives the user (phase 04 § Security). An
  optimistic UI must never be treated as proof the write succeeded — the refreshed tree is.
- Filter values are internal numeric ids compared in memory; nothing is interpolated into a query
  from this phase.
- No `dangerouslySetInnerHTML`, no `eval`, no dynamic import of a user-controlled path.

## Next Steps

Track A's interaction surface is complete. Phase 09 mounts `kudos-board.tsx` and hands it
`getKudosBoard()`'s output plus `toggleKudosLike`. Phase 08 may still be running in parallel.
