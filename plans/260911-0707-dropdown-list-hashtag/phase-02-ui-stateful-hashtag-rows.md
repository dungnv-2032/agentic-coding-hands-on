# Phase 02 — UI: stateful hashtag option rows

test_policy: e2e-red-first
owner: momorph-ui-implementer · depends on: phase 01 (valid RED) · status: pending · effort: 1h
Refs: MoMorph `p9zO-c4a4x` (`mm:1002:13102` menu, `mm:1002:13185` selected row, `mm:1002:13104` unselected, `mm:1002:13204` check icon) · `spec/dropdown-list-hashtag/spec-delta.md` FR-207..FR-211 · `clarifications.md`. Design data is authoritative — invent no visual values.

**Goal:** E13's rows become toggleable and selection-aware, and inert-with-a-reason at the cap.
**Owns:** `app/kudos/new/_components/hashtag-picker.tsx` (+ `hashtag-option-row.tsx` only if the picker would pass 200 lines).

1. `handleOptionClick`: `isSelected ? onRemove(option.id) : onAdd(option)`, then close the menu. Reuse the existing `onAdd`/`onRemove` — do not widen the frozen contract.
2. Row: keep `data-selected`; add `disabled={!isSelected && atLimit}`; selected background `bg-[rgba(255,234,158,0.2)]`; dim only unselected rows at the cap.
3. Every row renders a 24×24 `[data-testid="hashtag-check-slot"]` (`h-6 w-6 shrink-0`) at its right; selected rows put `[data-testid="hashtag-check"]` (circular check SVG) inside it. Unselected rows keep the slot empty so the list never reflows.
4. Keep the label as the button's own text node or one `<span>` — nothing that makes `text=<name>` resolve to two elements (ID-16 is the tripwire).
5. `hashtag-error` shows on `selected.length >= MAX_HASHTAGS`, not on the `error` prop: FR-210 needs it gone below 5, and the frozen reducer's `removeHashtag` never clears `hashtagError`, so a stale `"tooMany"` would pin it on screen. Keep `error?:` in the local props for parity, stop destructuring it, one comment line saying why.
6. Replace the stale header comment claiming rows are "add-only and never `disabled`"; cite the frame and this delta.
7. `npm run lint` + `npm run typecheck`, then `wc -l`: past 200 lines, extract the row button and check SVG into `_components/hashtag-option-row.tsx` and re-check both files.

Out of scope: `compose-contract.ts`, `compose-state.ts`, `compose-form.tsx`, everything in `e2e/`, menu open/close behavior, row hoisting, any route/table/action change.
Risk: a `disabled` row also kills hover/focus affordances — acceptable, the frame specifies exactly that. Rollback: revert this one commit; behavior returns to add-only.
Done when: lint + typecheck clean, owned files under 200 lines, no `e2e/` file touched. Phase 03 owns the GREEN rerun and visual evidence — do not claim GREEN here.
