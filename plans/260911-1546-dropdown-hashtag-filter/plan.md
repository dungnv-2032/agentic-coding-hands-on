---
title: "Dropdown Hashtag filter — default scroll box, focus glow + lock-in tests (F004/SCR004)"
description: "Make the 348px bounded scroll box the shared listbox default (drop the scrollable prop), add the #FAE287 focus-visible glow, and write the e2e that locks in the hashtag filter behavior that already works but is untested."
status: completed
priority: P2
effort: 3h
branch: feat/dropdown-hashtag-filter
work_type: feature
spec: docs/features/F004_KudosLiveBoard/
tags: [momorph, F004, kudos, ui, e2e]
created: 2026-09-11
completed: 2026-09-11
---

# Dropdown Hashtag filter (MoMorph `JWpsISMAaM`)

The hashtag twin of `260911-1348-dropdown-phong-ban`. Same shared component, one genuine frame deviation
(the hashtag listbox has no scroll box — 13 × 56px = 740px spills past the viewport), one unbuilt state
(`focus-visible` glow), and four behaviors that already run in `kudos-board.tsx` but no test has ever
asserted on the hashtag side.

- Spec delta (requirement source, frozen): `spec/dropdown-hashtag-filter/spec-delta.md` — FR-214..FR-219
- Clarifications (resolved, do not re-open): `clarifications.md`
- MoMorph: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/JWpsISMAaM
- testPolicy: `e2e-red-first`

## Phases

| # | Phase | Owner | Status | Evidence |
|---|-------|-------|--------|----------|
| 01 | [RED e2e — hashtag dropdown](phase-01-red-e2e-hashtag-dropdown.md) | tester | done | [report](reports/tester-260911-1556-red-hashtag-filter.md) |
| 02 | [UI — hashtag scroll box + focus glow](phase-02-ui-hashtag-dropdown-scroll-box.md) | momorph-ui-implementer | done | commit c4bf487 |
| 03 | [GREEN + visual evidence](phase-03-green-and-visual-evidence.md) | tester | done | [report](reports/tester-260911-1610-green-hashtag-filter.md) |

## Data flow (read/filter path unchanged — BR-216)

```
public.hashtags (13 rows, ORDER BY position)
  → fetchFilterOptions()                                   [untouched]
  → kudos-board.tsx  hashtagFilterId / matchesFilters()     [untouched]
  → KudosFilterBar → KudosFilterMenu (348px box now DEFAULT) [phase 02 only]
  → click option → onSelect → setOpenMenu(null) + resetPaging() → filteredKudos
    → HighlightCarousel (max 5 slides) + AllKudosFeed (10/page) both re-render
  → click the same option again → hashtagFilterId → null → board restored
```

## Key decisions carried in

- `scrollable` prop is **removed**, not defaulted-on: both frames need the box and its only caller is
  `kudos-filter-bar.tsx` (department branch). A flag both call sites set is a dead condition — KISS/DRY.
- Department rendering must stay byte-identical: `max-h-[348px] overflow-y-auto` moves from the ternary
  into the base className, so K-27 (348px, 50 options) stays green untouched.
- FR-215 glow reuses the selected-state token verbatim — `[text-shadow:0_0_6px_#FAE287]` under
  `focus-visible:`. Hover background `rgba(255,234,158,0.05)` and the selected tokens are untouched.
- e2e assertion hashtag: `Wasshoi` — 8 of 69 seeded kudos, and **position 8**, i.e. outside the 6 visible
  rows, so selecting it also proves the box scrolls rather than cuts options.
- Seed gives every kudos 1–3 hashtags (`1 + id % 3`, `supabase/seed.sql`) vs the card's 5-chip cap, so the
  `#Wasshoi` chip is never truncated away — per-card chip assertion is safe.
- FR-219 (13 options in `position` order) is already asserted by K-3 `toHaveText(HASHTAG_OPTIONS)`; the new
  tests only re-prove all 13 stay **mounted inside the bounded box**. No duplicate name list.
- No route, table, migration, Server Action, or URL param change.

## File ownership (no overlap between phases)

| Phase | Owns |
|-------|------|
| 01 | `e2e/kudos-live-board.spec.ts`, `e2e/fixtures/kudos-constants.ts` |
| 02 | `app/kudos/_components/kudos-filter-menu.tsx`, `app/kudos/_components/kudos-filter-bar.tsx` |
| 03 | `e2e/capture-hashtag-filter-visual.spec.ts`, `playwright.config.ts`, `evidence/*` |

Strictly sequential — 02 consumes 01's RED evidence; 03 consumes 02's code. `e2e/capture-hashtag-dropdown-visual.spec.ts`
belongs to a different frame (F005 `/kudos/new` picker, `p9zO-c4a4x`) and is **off-limits to every phase**.

## Done when

- [x] `npm run test:e2e -- e2e/kudos-live-board.spec.ts --project=anon -g "K-31|K-32|K-33|K-34|K-35"` exit 0. (5/5 passed + setup)
- [x] Full `kudos-live-board.spec.ts` (`anon`) green — K-3, K-8 and K-26..K-30 included, nothing regressed. (35/35 passed; K-27 department tripwire passed)
- [x] `npm run lint` and `npm run typecheck` exit 0. (0 errors, 31 pre-existing warnings; typecheck clean)
- [x] `kudos-filter-menu.tsx` under 200 lines and free of the `scrollable` prop. (59 lines; prop removed)
- [x] Evidence screenshots: closed, open-unselected, open-selected-scrolled. (three PNGs in `evidence/`; geometry assertions verified: 348px, 56px rows)
- [x] Post-review fixes applied: K-32 hover assertion replaced with positive `toHaveCSS` assertions (focused-unselected: `rgba(0,0,0,0)`, hover: `rgba(255,234,158,0.05)`); re-verified 6/6 and 35/35 green. Docs updated for spec.md UI-states row. Native focus outline regression guard comment added to component.
