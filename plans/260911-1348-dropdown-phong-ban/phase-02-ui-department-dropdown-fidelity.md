# Phase 02 — UI: dropdown listbox fidelity (centered text, pointer, 348px box)

test_policy: e2e-red-first
owner: momorph-ui-implementer · status: completed · priority: P1 · effort: 30m · depends on: phase 01 (valid RED)

**Shipped:** Commit c174d6f. Three class fixes to `app/kudos/_components/kudos-filter-menu.tsx`: removed `gap-1`, changed `text-left` → `text-center`, added `cursor-pointer`, changed `max-h-80` → `max-h-[348px]` on scrollable branch (department only). File: 61 lines.

## Context links

- `spec/dropdown-phong-ban/spec-delta.md` — FR-208, FR-209, FR-213 (the only FRs this phase touches)
- `clarifications.md` — resolved decisions, especially the 348px/56px/gap-1 math and the "shared component,
  fix applies to both listboxes" decision
- MoMorph: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/WXK5AYB_rG (specs A, A.1/A.2/A.3) —
  design data is authoritative, invent no visual values
- Phase 01's RED evidence (read-only; do not modify `e2e/`)

## Overview

Three class-level changes to one file. FR-210/211/212 (click → select → close → filter; toggle-off;
persistent highlight) need **zero code change** — that logic already lives in `kudos-board.tsx` and
`kudos-filter-bar.tsx`, both off-limits and both already correct. Do not touch selection/toggle/close
logic; touch only presentation classes.

**Owns:** `app/kudos/_components/kudos-filter-menu.tsx` only (currently ~60 lines).

## Key insights

1. Row height is already exactly 56px: `p-4` (16px×2) + `text-base leading-6` (24px line-height) = 56px.
   Nothing to change there.
2. 6 rows × 56px + 6px top padding + 6px bottom padding = 348px exactly (clarifications' own math) — this
   only balances if the row `gap-1` (4px × 5 gaps between 6 rows) is removed. Leaving `gap-1` in place
   would overshoot 348px and misalign with the frame.
3. The listbox container is shared by hashtag and department (`testId` prop only changes which
   `data-testid` is stamped) — FR-208/209 (center + pointer) and the `gap-1` removal apply to the shared
   row container/button classes, not conditionally on `scrollable`. FR-213's `max-h-[348px]` stays gated
   on `scrollable` (department only) exactly as `max-h-80` is gated today — do not widen it to hashtag.
4. Selected/hover background tokens are correct today (clarifications confirmed) — do not touch
   `bg-[rgba(255,234,158,0.10)]`, the text-shadow, or the hover background.

## Requirements

Functional (all presentational, all in `kudos-filter-menu.tsx`):

- FR-208: every option's text is centered.
- FR-209: every option shows `cursor: pointer` (not the default `<button>` cursor).
- FR-213: the department (`scrollable`) listbox's bounded box is 348px tall, no gap between rows.

Non-functional: file stays under 200 lines; no new props, no new testids, no behavior change.

## Architecture

Pure CSS-class edit, one component, no data flow change (see plan.md § Data flow — untouched below the
listbox).

## Related code files

- Modify: `app/kudos/_components/kudos-filter-menu.tsx`
- Create: none · Delete: none

## Implementation steps

1. Container `<div role="listbox">` className: remove `gap-1`; change the scrollable branch from
   `"max-h-80 overflow-y-auto"` to `"max-h-[348px] overflow-y-auto"`.
2. Option `<button>` className: change `text-left` to `text-center`; add `cursor-pointer`.
3. Update the header comment's `scrollable` note to cite the 348px/56px/6px-padding math (so the next
   reader doesn't have to re-derive it from clarifications.md).
4. `npm run lint` && `npm run typecheck` — must be clean.
5. `wc -l app/kudos/_components/kudos-filter-menu.tsx` — confirm still under 200 lines (it will be; this
   changes 2 lines of classNames).

Explicitly OUT of scope: `onSelect`, `selectedId`, `aria-selected` wiring, `scrollable` prop signature,
`kudos-filter-bar.tsx`, `kudos-board.tsx`, anything in `e2e/`. FR-210/211/212 need no edit here — do not
"helpfully" refactor working selection logic.

## Todo list

- [ ] `gap-1` removed from the row container
- [ ] `max-h-80` → `max-h-[348px]` on the scrollable branch only
- [ ] `text-left` → `text-center` on option buttons
- [ ] `cursor-pointer` added to option buttons
- [ ] Header comment updated with the 348px math
- [ ] lint + typecheck clean
- [ ] File still under 200 lines

## Success criteria

`npm run lint` and `npm run typecheck` pass; the file's diff touches only the container/option className
strings and the header comment. Phase 03 owns the GREEN rerun and visual evidence — do not claim GREEN
here.

## Risk assessment

| Risk | L×I | Countermove |
|------|-----|-------------|
| Removing `gap-1` visually tightens the hashtag listbox too (13 short rows, uncapped height) | Low × Low | Confirmed intentional by clarifications — shared component, shared fix |
| `max-h-[348px]` accidentally applied to the non-scrollable branch | Low × High | Keep the ternary structure exactly as-is; only change the string inside the `scrollable` branch |
| Centered text plus long department names (e.g. "OPDC - HRD - HRBP") wraps oddly | Low × Low | Row already has fixed 56px height + no wrap in the frame; no change needed if it already fits at `w-64` |

## Security considerations

None. Presentational-only change, no new data surface.

## Next steps

Hand off to phase 03 for the GREEN rerun (K-26..K-30 + full anon suite) and visual evidence capture.
