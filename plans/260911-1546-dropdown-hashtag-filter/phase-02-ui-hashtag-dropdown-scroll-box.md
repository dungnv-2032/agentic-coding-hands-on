# Phase 02 — UI: scroll box by default + focus-visible glow

test_policy: e2e-red-first
owner: momorph-ui-implementer · status: done · priority: P1 · effort: 30m · depends on: phase 01 (valid RED)

## MoMorph refs

- Dropdown Hashtag filter: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/JWpsISMAaM
- fileKey `9ypp4enmFmdK3YAFJLIu6C` · screenId `JWpsISMAaM`
- Clarifications: `plans/260911-1546-dropdown-hashtag-filter/clarifications.md`
- testPolicy: `e2e-red-first`

## Context links

- `spec/dropdown-hashtag-filter/spec-delta.md` — FR-214, FR-215 (the only FRs this phase touches)
- `clarifications.md` — the "drop the `scrollable` prop" and "reuse `#FAE287`, invent no new token" calls
- Phase 01's RED evidence (read-only; do not modify anything under `e2e/`)
- Sibling precedent: `plans/260911-1348-dropdown-phong-ban/phase-02-ui-department-dropdown-fidelity.md`

## Overview

Two class-level changes across two files. FR-216/217/218/219 need **zero code change** — that logic lives
in `kudos-board.tsx` (off-limits, already correct) and phase 01 only locks it in. Touch presentation and
the prop signature; touch no selection, toggle, or close logic.

**Owns:** `app/kudos/_components/kudos-filter-menu.tsx` (~61 lines) and
`app/kudos/_components/kudos-filter-bar.tsx` — nothing else.

## Key insights

1. The box already exists and is already correct at `max-h-[348px] overflow-y-auto`; it is merely gated
   behind `scrollable`. This is a **gate removal**, not a re-measurement. Do not re-derive 348px and do not
   change the number.
2. Department rendering must come out byte-identical or K-27 breaks. Moving the two classes from the
   ternary into the base className does exactly that — the department listbox ends up with the same class
   set it has today.
3. `max-h` does not truncate a list shorter than 6 rows, so making it the default is visually inert for any
   future short listbox.
4. The row container has no `gap` (removed last session), so the 6 × 56px + 6px padding math still lands on
   348px for the hashtag list too.
5. The glow token is already in the file: `[text-shadow:0_0_6px_#FAE287]` on the selected branch. Reuse it
   verbatim under `focus-visible:`; do not pick a new colour, blur, or `ring-*` utility. Phase 01 asserts
   `text-shadow` carrying `rgb(250, 226, 135)` — a `box-shadow`/`outline` implementation will not satisfy it.
6. The glow must apply on **both** branches (selected and default), so keyboard focus is visible wherever
   it lands — put `focus-visible:[text-shadow:0_0_6px_#FAE287]` on the shared base className, not inside
   the ternary.
7. `scrollable` is the only prop being removed; `testId`, `options`, `selectedId`, `onSelect` stay exactly
   as they are. `kudos-filter-bar.tsx` is in scope for one reason only: deleting the `scrollable` attribute
   from the department `<KudosFilterMenu>` call, which would otherwise be a TypeScript error.

## Requirements

Functional:

- FR-214: both listboxes are bounded to 348px with internal scroll, by default, with no prop to toggle it.
- FR-215: an option under keyboard focus shows the `#FAE287` glow; hover background unchanged.

Non-functional: both files stay under 200 lines; no new props, no new testids, no behavior change, no
change to the selected/hover tokens (clarifications forbid it).

## Architecture

Pure presentation plus one prop removal. No data-flow change — see `plan.md` § Data flow; everything below
the listbox is untouched.

## Related code files

- Modify: `app/kudos/_components/kudos-filter-menu.tsx`, `app/kudos/_components/kudos-filter-bar.tsx`
- Create: none · Delete: none

## Implementation steps

1. `kudos-filter-menu.tsx`: delete `scrollable` from the props destructure and from the props type.
2. Fold `max-h-[348px] overflow-y-auto` into the listbox `<div>`'s base className and drop the ternary
   entirely (the className becomes a plain template-free string).
3. Add `focus-visible:[text-shadow:0_0_6px_#FAE287]` to the option `<button>`'s shared base className
   (alongside `cursor-pointer`), leaving the selected/hover ternary untouched.
4. Update the component's header comment: the box is now the default for both listboxes and no longer a
   department-only concession; keep the 348px = 6 × 56px + 6px math note, and cite FR-214/FR-215.
5. `kudos-filter-bar.tsx`: remove the bare `scrollable` attribute from the department `<KudosFilterMenu>`.
6. `npm run lint` && `npm run typecheck` — both must exit 0.
7. `wc -l` both files — confirm each is still under 200 lines.

Explicitly OUT of scope: `onSelect`/`selectedId`/`aria-selected` wiring, the open/close and outside-dismiss
logic in `kudos-filter-bar.tsx`, `kudos-board.tsx`, `lib/kudos/derive.ts`, anything under `e2e/`, and the
selected/hover colour tokens. FR-216..FR-219 need no edit here — do not "helpfully" refactor working
selection logic.

## Todo list

- [x] `scrollable` removed from the props type and destructure
- [x] `max-h-[348px] overflow-y-auto` moved into the base listbox className, ternary gone
- [x] `focus-visible:[text-shadow:0_0_6px_#FAE287]` added to the option base className
- [x] `scrollable` attribute removed from the department call in `kudos-filter-bar.tsx`
- [x] Header comment updated (default box, FR-214/FR-215)
- [x] lint + typecheck clean (0 errors, 31 pre-existing warnings; typecheck exit 0)
- [x] Both files under 200 lines (59 lines, 112 lines per tester report)

## Success criteria

`npm run lint` and `npm run typecheck` exit 0; the diff touches only the two className strings, the prop
signature, the header comment, and the one removed attribute. No `grep -rn "scrollable" app/` hit remains.
Phase 03 owns the GREEN rerun and the visual evidence — do not claim GREEN here.

## Risk assessment

| Risk | L×I | Countermove |
|------|-----|-------------|
| Department listbox rendering drifts and K-27 (348px / 50 options) goes red | Med × High | Move the two classes verbatim into the base string — the department class set must be identical to today's; phase 03's full-file run is the tripwire |
| Glow implemented as `ring`/`outline`/`box-shadow`, so K-32 stays red | Med × High | Insight 5 — the contract is `text-shadow` with `#FAE287`, nothing else |
| `focus-visible` placed inside the ternary, so a selected option loses its focus cue | Med × Med | Insight 6 — it goes on the shared base className |
| A stale `scrollable={...}` left somewhere fails typecheck | Low × Low | Step 5 plus the `grep` in the success criteria |
| Removing the prop is read as licence to restyle the listbox | Low × Med | Out-of-scope list above; tokens are frozen by clarifications |

## Security considerations

None. Presentational change plus a prop removal; no new data surface, no new user input.

## Next steps

Hand off to phase 03 for the GREEN rerun (K-31..K-35 + the full `anon` file) and the visual capture.
