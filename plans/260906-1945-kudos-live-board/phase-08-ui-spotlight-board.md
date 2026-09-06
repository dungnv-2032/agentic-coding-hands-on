# Phase 08 — UI: the Spotlight board

**Track:** A (presentational UI) · **Owner:** `momorph-ui-implementer` (activates
`momorph-implement-design`) · **Depends:** 05 · **Effort:** 2h · **test_policy:** `e2e-red-first`

## MoMorph refs:
- Sun* Kudos - Live board: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/MaZUn5xHXZ
- Clarifications: plans/260906-1945-kudos-live-board/clarifications.md
- testPolicy: e2e-red-first

**Goal** The `SPOTLIGHT BOARD` section: a deterministic word cloud with search, pan/zoom, expand,
and the live activity ticker — no new dependency.

## Context Links

- [plan.md](plan.md) · [phase-01](phase-01-foundation-and-integration-contract.md) (contract) · [phase-05](phase-05-ui-foundation-i18n-icons-hero-sidebar.md) (dictionary + icons)
- [test-contract.md](test-contract.md) § "Spotlight board"
- [clarifications.md](clarifications.md) word-cloud decision (hand-rolled, seeded PRNG, memoised), § "SPOTLIGHT BOARD (B.6/B.7)"
- [technical-spec.md § 4.5 ALG-002](spec/kudos-live-board/technical-spec.md) (the layout algorithm)
- `e2e/kudos-live-board.spec.ts:451-518` (K-13…K-16)
- Hydration rule precedent: `app/awards-information/_components/award-category-nav.tsx:24-29`

## Overview

**Priority:** P1 · **Status:** delivered. Independent of the card and board phases — its file set is
disjoint, so it runs concurrently with 06 and 07.

## Key Insights

1. **The layout must be deterministic or the section hydration-mismatches.** A seeded PRNG places
   each node once, memoised, so the server's first render and the browser's byte-match (ALG-002).
   No `Math.random`, no `Date.now`, no `window` read in the render body. The seed is a constant in
   this phase's `spotlight-layout.ts`, and the node list is the input — same input, same layout,
   every time.
2. **No word-cloud library.** Seven names do not justify the project's first runtime chart
   dependency (settled decision, YAGNI). Placement is arithmetic over three size tiers.
3. **`388 KUDOS` comes from the dictionary, not from a count.** Phase 05 § Key Insight 1 holds the
   reasoning; this phase just renders `copy.spotlight.count`, and K-13 asserts the exact string.
4. **Pan/zoom is a CSS `transform` on a wrapper.** Drag to pan, the `Pan/Zoom` control toggles the
   mode with `aria-pressed`, and the expand glyph toggles a full-bleed view with its own
   `aria-pressed`. K-15 asserts both attributes exist plus `title="Pan/Zoom"`, so both are
   `"true"`/`"false"`, never omitted, and the title is on the button itself.
5. **Every spotlight node is `<a href="/kudos/<id>">`** with the recipient's name as its accessible
   name and `title` = name + time received. `SpotlightNodeView.kudosId` exists precisely so the
   href can be real; nodes must not link to `#`.
6. **Search filters the rendered node set, and `spotlight-empty` appears when nothing matches.**
   K-14 types `Nguyễn` and asserts the count did not grow, so filtering must be case- and
   diacritic-faithful to the seeded names (a plain `includes` on the raw string is correct here —
   do not normalise diacritics away, the seeded names carry them).
7. **The just-updated node renders red.** `isJustUpdated` is already resolved by the view model
   (the most recent ticker event's sunner); this phase only styles it.
8. **The ticker holds six rows fading upward**, each composed from the dictionary's sentence
   template plus `timeLabel` and `name` — the sentence is copy, the values are data.
9. **`h2` only.** The section heading is `SPOTLIGHT BOARD`; no `h1` anywhere (K-0 counts exactly
   one page-wide, owned by the hero).

## Requirements

**Functional:** FR-205 (word cloud, deterministic layout, pan/zoom, expand, ticker, search capped
at 100 characters), FR-601 (fully readable with no session).

**Non-functional:** one `"use client"` file for the interactive shell; the layout function is pure
and testable by inspection; every file ≤200 lines; `mm:{nodeId}` on every arbitrary value; no new
runtime dependency in `package.json` (this phase does not own `package.json` and must not touch it).

## Architecture

**Integration contract consumed** (frozen): `SpotlightNodeView`, `SpotlightTickerRowView`, and the
`kudos.spotlight` dictionary slice. Nothing added.

```
spotlight-board.tsx  "use client"   props { nodes, ticker, copy }
   state { query, panZoomOn, expanded, pan: {x,y} }
   ├─ spotlight-layout.ts        pure: (nodes, seed) → [{ id, x, y, tier }]   memoised
   ├─ spotlight-word-cloud.tsx   the transform wrapper + one <a> per visible node
   └─ spotlight-ticker.tsx       six rows, fading upward
```

**Hooks emitted:** `spotlight-section` (with `h2` `SPOTLIGHT BOARD` and a single-leaf
`Sun* Annual Awards 2025` eyebrow), `spotlight-board`, `spotlight-count`, `spotlight-search`
(`maxlength="100"`, placeholder `Tìm kiếm`), `spotlight-node`, `spotlight-ticker`,
`spotlight-panzoom`, `spotlight-expand`, `spotlight-empty`.

**Out of scope:** the hero's separate Sunner search (05, different placeholder and destination),
kudos cards (06), filters and feed (07), any data read (04/09), the real-time push behind the
"live" ticker — the ticker renders seeded events, and clarifications claims nothing more.

## Related Code Files

**Create:** `app/kudos/_components/spotlight-board.tsx` · `spotlight-word-cloud.tsx` ·
`spotlight-ticker.tsx` · `spotlight-layout.ts`
**Modify:** none
**Read only:** `lib/kudos/view-model.ts` (frozen), phase 05's icons + dictionary,
`app/awards-information/_components/award-category-nav.tsx` (hydration-safety precedent)
**Delete:** none

## Implementation Steps

1. Read the spotlight nodes from the frame (`get_frame` on `MaZUn5xHXZ`): canvas background, three
   name size tiers, the red just-updated colour, ticker row treatment, the 16px search icon, the
   expand glyph, and the `Pan/Zoom` control.
2. `spotlight-layout.ts` — a small seeded PRNG (a fixed-constant LCG is enough) mapping the node
   list to `{ x, y, tier }` within the canvas box. Pure, deterministic, no imports.
3. `spotlight-word-cloud.tsx` — the transform wrapper plus one `<a data-testid="spotlight-node">`
   per visible node, with the name as text, `title` = name + received time, `href` =
   `` `/kudos/${kudosId}` ``, and the red style when `isJustUpdated`.
4. `spotlight-ticker.tsx` — six rows from the dictionary template, fading upward.
5. `spotlight-board.tsx` — the `"use client"` shell: the section wrapper with `h2` and eyebrow,
   `spotlight-count`, the search input (`maxlength="100"`), the memoised layout, pan state and
   drag handlers, `spotlight-panzoom` and `spotlight-expand` (both with `aria-pressed`),
   `spotlight-empty` when the filtered node list is empty.
6. `npm run typecheck && npm run lint`, and open `/kudos` in `next dev` only after phase 09 lands —
   until then confirm hydration safety by inspection: nothing outside an effect or handler reads
   `window`, `document`, `Math.random`, or the clock.

## Todo List

- [ ] `spotlight-layout.ts` pure and seeded; identical output for identical input
- [ ] `useMemo` over the layout so a re-render cannot reshuffle it
- [ ] No `Math.random` / `Date.now` / `window` in any render body
- [ ] `spotlight-count` renders `copy.spotlight.count` (`388 KUDOS`), not a computed count
- [ ] `spotlight-search` has `maxlength="100"` and placeholder `Tìm kiếm`
- [ ] Every `spotlight-node` is a real `<a href="/kudos/<id>">` with name + time `title`
- [ ] `spotlight-panzoom` carries `aria-pressed` **and** `title="Pan/Zoom"`; `spotlight-expand` carries `aria-pressed`
- [ ] Six ticker rows from the dictionary template
- [ ] `spotlight-empty` on no match; red styling on the just-updated node
- [ ] `h2` only; single-leaf eyebrow
- [ ] Files ≤200 lines; `mm:{nodeId}` on every arbitrary value; `package.json` untouched
- [ ] `npm run typecheck && npm run lint` clean

## Success Criteria

- Typecheck and lint exit 0.
- Given the 7 seeded nodes: 7 `spotlight-node` links; typing `Nguyễn` narrows the set and leaves
  `spotlight-empty` hidden; typing a non-matching string shows `spotlight-empty`.
- Calling the layout twice with the same nodes returns identical coordinates.
- `spotlight-count` reads exactly `388 KUDOS`.
- No import from `lib/kudos/queries.ts`, `board-data.ts`, `app/kudos/_actions/**`, or
  `@/lib/supabase/*`; no new dependency in `package.json`.

## Risk Assessment

| Risk | L×I | Countermeasure |
|---|---|---|
| Non-deterministic layout → hydration mismatch that can break unrelated assertions on the same page | Med × **High** | Seeded PRNG + `useMemo`; Key Insight 1 forbids every non-deterministic source, and step 6 checks by inspection |
| Diacritics normalised away, so `Nguyễn` matches nothing | Med × Med | Filter on the raw seeded strings with `includes`; the seed and the test share the same transcription |
| A node with no `kudosId` falls back to `href="#"` and silently violates the contract | Low × Med | `kudosId` is non-optional in the contract; a missing value is a phase 04 bug, escalated rather than papered over |
| Drag-to-pan swallows the click on a node, making the links unreachable | Med × Med | Pan only while the pan/zoom mode is on; below a small movement threshold the gesture stays a click |
| `spotlight-board.tsx` exceeds 200 lines | Med × Low | Pre-split into four files; a `use-spotlight-pan.ts` hook is the next split if needed, inside this phase's file set |
| Overlapping node boxes make some names unclickable | Med × Low | The tier boxes are laid out on a coarse grid with padding; overlap is a layout bug the tester's visual pass catches |

**Rollback:** delete the four files. Nothing mounts them until phase 09.

## Security Considerations

- No data access, no session read, no Server Action; props only.
- Node `href`s are built from a numeric `kudosId`, so no database string reaches a URL position.
- Node names and ticker text render as text nodes; no `dangerouslySetInnerHTML`.
- The search input is client-local — it filters an in-memory array and never becomes a query,
  so there is no injection surface, and `maxlength="100"` bounds it regardless.
- Pan/zoom transforms are numeric state; no style string is assembled from user input.

## Next Steps

Phase 09 mounts `spotlight-board.tsx` beside the hero, board, and sidebar. Nothing else depends on
this phase.
