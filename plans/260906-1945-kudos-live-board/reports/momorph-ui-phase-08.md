# Phase 08 — Spotlight board (section mode)

**Status:** DONE_WITH_CONCERNS (see Concerns) · files ≤200 lines · typecheck 0 errors · lint 0 errors

## Files (all new, ownedFiles only)

- `app/kudos/_components/spotlight-layout.ts` (62 lines) — pure, zero imports
- `app/kudos/_components/spotlight-word-cloud.tsx` (55 lines)
- `app/kudos/_components/spotlight-ticker.tsx` (34 lines)
- `app/kudos/_components/spotlight-board.tsx` (162 lines) — the one `"use client"` file

## MoMorph calls (real, this session)

`get_overview` ×1 · `get_node` ×7 (`2940:14174`, `2940:14178`, `2940:14181`, `2940:14173`, `3007:17482`, `2940:14833`, `2995:15926`, `3004:15999`, `2940:13476`, `2940:14170` — 10 total) · `get_node_context` ×1 · `query_component` ×1 · `get_figma_image` ×1 (500, same as phase 05's documented failure).

## mm:{nodeId} map

`2940:14170` (Frame 552 wrapper) · `2940:13476`/`2940:13477`/`2940:13480` (eyebrow + `SPOTLIGHT BOARD` h2, gold `#FFEA9E`, fontSize 57/36) · `2940:14174` (canvas panel, 1157×548, border `#998C5F`, radius 47px) · `2940:14173` (background image + `linear-gradient(0deg, rgba(0,0,0,.70) 0%, rgba(0,0,0,.70) 100%)` dark wash, reproduced as a literal overlay div, not an opacity hack) · `3007:17482` (`388 KUDOS`, 36px/700, white) · `2940:14833`+`I2940:14833;186:2758` (search pill, same `186:2757` component family as the hero search — same border/bg tokens) · `2995:15926` (name-text typography source: Montserrat 700) · `3004:15999` (ticker row) · `3007:17479` (Pan/Zoom, 30×30, bottom area) · expand glyph (no distinct node — B.7.2 sibling, bottom-right per clarifications).

## Test hooks emitted

`spotlight-section` (`<section>`, h2 `SPOTLIGHT BOARD`, eyebrow) · `spotlight-board` · `spotlight-count` (`{total} KUDOS`) · `spotlight-search` (`maxlength={100}`, placeholder `Tìm kiếm`) · `spotlight-node` (×N, `<a href="/kudos/<id>">`) · `spotlight-ticker` · `spotlight-panzoom` (`aria-pressed` + `title="Pan/Zoom"`) · `spotlight-expand` (`aria-pressed`) · `spotlight-empty`. Verified against `e2e/kudos-live-board.spec.ts` K-13…K-16 and `e2e/fixtures/kudos-constants.ts` (`SPOTLIGHT_COUNT_TEXT`, `SPOTLIGHT_SEARCH_PLACEHOLDER`) — exact string match, no invented copy.

## SSR/hydration parity

`spotlight-layout.ts` is pure and import-free: `layoutSpotlightNodes(ids)` takes only the node id array, uses a fixed-constant LCG seeded per-id (never the array index alone, never `Math.random`/`Date.now`/`window`), and returns identical `{xPct, yPct, tier}` for identical input — verified by inspection (deterministic arithmetic only, no environment read). `spotlight-board.tsx` calls it inside `useMemo(() => layoutSpotlightNodes(nodes.map(n => n.id)), [nodes])`, so a re-render from search/pan/expand state never reshuffles it. `spotlight-word-cloud.tsx` and `spotlight-ticker.tsx` take pre-computed positions as props and hold no hooks, so they carry no client/server divergence risk of their own.

## Contract gap resolved as directed

`lib/kudos/view-model.ts` (frozen, read-only) has no field for the seeded `388` total — `KudosBoardViewModel.spotlight` is `{ nodes, ticker }` only. Per this task's explicit instruction ("Take it as a prop"), `SpotlightBoard` declares its own `total: number` prop, independent of the frozen shape. Phase 09 (page wiring) will need to source that number from wherever Track B lands it (the seed/board-stats value test-contract.md's ratification 2026-09-06c describes) — flagging this now rather than silently hardcoding `388` in this component.

## Concerns

1. **`spotlight-canvas.png` is unverified against the frame crop.** `get_figma_image` still 500s on this node (`2940:14174`), same failure phase 05 recorded. I viewed the committed file — it's the same root/swirl motif family used for the KV background, thematically plausible (dark corner for text legibility, matches the frame's own `Root further mo rong 1` node name and its 70% black gradient wash, which I did reproduce exactly as a separate overlay div). But I cannot confirm it is the *correct* crop pixel-for-pixel — this needs a follow-up visual pass once MoMorph asset export recovers, or a direct designer check. Not silently accepted; flagged per instruction.
2. **Word-cloud tier sizes (28/20/14px) are an inferred adaptation, not a measured value.** The frame's own ~90 name instances are all a uniform ~6.65px decorative tiling texture (filler, not 7 distinct interactive elements) — there is no literal 3-tier size in the source data to copy. Per clarifications' explicit direction ("seven names... at three size tiers"), I chose three legible, clickable sizes myself. Reasonable but a designer eyeball would be worth it once phase 09 mounts this.
3. **Ticker fade direction assumes `ticker` array is oldest-first.** `SpotlightTickerRowView[]` order isn't specified by the frozen contract; I render row `i`'s opacity as `(i+1)/total` so the *last* array item is fully opaque (newest, per plan.md "fading upward"). If Track B emits newest-first instead, the fade will read backwards — a one-line fix (`.reverse()` or flip the formula) once real data is wired in phase 09.
4. **Pan-vs-click drag threshold (4px) is untested against real pointer events** — implemented per the Risk Assessment mitigation but not exercised, since these components aren't mounted yet.

None of these are guesses presented as fact — each is called out above rather than silently shipped.

## Unresolved questions

- Should `spotlight-canvas.png` be re-exported once `get_figma_image` recovers, or is the current keyvisual-family reuse acceptable long-term? (orchestrator/design call)
- Confirm `ticker` array order (oldest-first vs newest-first) with whoever implements the Track B spotlight query, so the fade direction is provably correct rather than assumed.
