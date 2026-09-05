# Phase 02 — Implement open-state visual contract + listbox keyboard nav

## Context Links

- Plan overview: [plan.md](plan.md)
- RED evidence: [phase-01-red-e2e-open-state-and-keyboard.md](phase-01-red-e2e-open-state-and-keyboard.md)
- Spec (authoritative tokens): [spec/language-dropdown/spec-delta.md](spec/language-dropdown/spec-delta.md) §3
- Decisions: [clarifications.md](clarifications.md)
- Design: MoMorph `hUyaaugye2` — https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/hUyaaugye2 (fileKey `9ypp4enmFmdK3YAFJLIu6C`, node `721:4942`)

## Overview

- **Priority:** P1
- **Status:** completed
- **Owner:** `momorph-ui-implementer` (mode: `screen`, testPolicy: `e2e-red-first`)
- **Effort:** 1h30
- **Description:** Replace the invented open-panel styling with the measured design tokens
  and add full listbox keyboard navigation. One file, edited in place.

## Key Insights

- **Tokens are already measured.** spec-delta §3 is the contract. Do **not** re-open the
  Figma node to re-derive values, and do not round them.
- **The drop-below position is settled.** The design shares componentId `186:1692` between
  the VN row and the trigger, which *looks* like an overlay. The user explicitly ruled that
  out. `absolute top-full` stays. Do not revisit (clarifications.md).
- **Container shape should change from `ul`/`li` to a `div role="listbox"` with
  `button role="option"` children.** Three reasons: (1) an `option` must be owned directly
  by its `listbox` — today a `listitem` sits between them; (2) keeping `<button>` gives
  Enter **and** Space activation for free, so only Arrow/Home/End/Escape need code (KISS);
  (3) the e2e tests select by role, so C3/C3b survive the change.
- **Escape already exists** as a document-level listener. Add focus-return there rather than
  writing a second Escape path in the panel handler (DRY).
- **The design draws no focus indicator.** Moving real DOM focus into options without one is
  a WCAG 2.4.7 regression. Use a `ring` in the panel's own border color `#998C5F` — no new
  color is invented, and a ring does not collide with the selected background.

## Requirements

**Functional**

- FR-203.a — panel lists VN and EN, each with its own flag (already true; must not regress).
- FR-203.b — selected option carries `rgba(255,234,158,0.2)`; unselected is transparent.
- FR-203.c — ArrowDown/ArrowUp (wrapping), Home/End, Enter/Space select, Escape closes and
  returns focus to the trigger. Focus lands on the **selected** option when the panel opens.
- Hover on an unselected option → `rgba(255,234,158,0.08)`.
- Click-outside close and chevron 180° rotation keep working.

**Non-functional**

- File stays under 200 lines (see split rule below).
- No new dependency. No headless-UI / radix / floating-ui (YAGNI — two static options).
- `npm run typecheck` and `npm run lint` clean.
- Locale persistence mechanism untouched: cookie `NEXT_LOCALE` via the existing `setLocale`
  server action.

## Architecture

```
LanguageSelector (client component)
  state: open:boolean · activeIndex:number
  refs:  rootRef (outside-click)  triggerRef (focus return)  optionRefs[] (roving focus)

  trigger <button aria-haspopup="listbox" aria-expanded aria-controls>
        └ CurrentFlag + label + IconChevronDown (rotate-180 when open)

  open && panel <div role="listbox" onKeyDown={handleListKeyDown}>
        └ OPTIONS.map → <button role="option" aria-selected tabIndex={active?0:-1}>
                             <Flag aria-hidden /> label
```

**Data flow**

```
click trigger ──▶ setOpen(true), setActiveIndex(indexOf(locale))
                     │
                     └─▶ effect: optionRefs[activeIndex].focus()
key Arrow/Home/End ─▶ setActiveIndex(next) ─▶ effect re-focuses
click | Enter | Space on option ─▶ handleSelect(value)
                     ├─ setOpen(false); triggerRef.focus()
                     └─ startTransition(setLocale(value)) ─▶ cookie NEXT_LOCALE ─▶ re-render
Escape (document listener) ─▶ setOpen(false); triggerRef.focus()
pointerdown outside ────────▶ setOpen(false)   [no focus return — the user aimed elsewhere]
```

**Visual contract (verbatim from spec-delta §3 — Tailwind v4 arbitrary values)**

| Element | Property | Value | Class |
|---|---|---|---|
| Panel | background | `#00070C` | `bg-[#00070C]` |
| Panel | border | `1px solid #998C5F` | `border border-[#998C5F]` |
| Panel | radius | `8px` | `rounded-lg` |
| Panel | padding | `6px` | `p-1.5` |
| Panel | layout | flex column | `flex flex-col` |
| Option | size | `108 × 56` | `w-[108px] h-14` |
| Option | radius | `2px` | `rounded-[2px]` |
| Option | content | flag 24px + gap 4px + label, centered | `flex items-center justify-center gap-1` |
| Option (selected) | background | `rgba(255,234,158,0.2)` | `bg-[rgba(255,234,158,0.2)]` |
| Option (unselected) | background | transparent | *(no bg class)* |
| Option (hover, unselected only) | background | `rgba(255,234,158,0.08)` | `hover:bg-[rgba(255,234,158,0.08)]` |
| Label | font | Montserrat 700, 16px/24px, ls 0.15px, white | `text-base font-bold leading-6 tracking-[0.15px] text-white` |
| Option (focus) | ring | `#998C5F` — a11y addition, not a design token change | `focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[#998C5F]` |

Retained from current code (not invented anew): `absolute right-0 top-full z-30 mt-1`.
Removed: `bg-[#0B0F12]`, `overflow-hidden`, `shadow-lg`, `py-1`, `min-w-[108px]`,
`hover:bg-white/10` on options, `px-4 py-2` on options.

## Related Code Files

**Modify (in place — no "enhanced" copy)**

- `app/login/_components/language-selector.tsx`

**Read only**

- `app/login/_components/icons.tsx` — reuse `IconFlagVn`, `IconFlagEn`, `IconChevronDown`. Add nothing.
- `app/login/_components/login-header.tsx` — confirms the props contract is unchanged.
- `e2e/login-screen.spec.ts` — the tests to satisfy. **Do not edit.**

**Create — only if the split rule fires**

- `app/login/_components/language-option-list.tsx` — the panel: `role="listbox"` container,
  the `OPTIONS` array, option refs, and `handleListKeyDown`. Props:
  `{ id, locale, labels, onSelect(value), onRequestClose() }`.

**Split rule (deterministic, not a judgment call):** after the edit, run
`wc -l app/login/_components/language-selector.tsx`. If it is **> 200**, extract the panel
to the exact path above and rerun. If it is ≤ 200, do **not** split (YAGNI).

**Delete:** none.

## Delivery (2026-09-05)

Implementation complete:

- **File size:** 186 lines (no split needed; ≤ 200 rule honored)
- **All tokens verbatim:** `#00070C`, `#998C5F`, `rgba(255,234,158,0.2)`, `rgba(255,234,158,0.08)` present as specified; old invented values (`#0B0F12`, `hover:bg-white/10`, etc.) removed
- **Container migration:** `ul`/`li` → `div role="listbox"` + direct `button role="option"` children; C3b assertion (SVG count per option) still passes
- **Keyboard nav:** ArrowDown/Up/Home/End with wrapping, Escape with focus return, Enter/Space select — all working
- **Focus authority:** Single `useEffect` on `[open, activeIndex]` drives focus; no competing `.focus()` calls elsewhere
- **Tests:** All 10/10 on `--project=anon` pass (C1–C5, C10, C3c–C3e); no flakes, no retries
- **Quality:** `npm run typecheck` + `npm run lint` both clean
- **Post-review fix applied:** Medium finding #1 (setActiveIndex purity issue in click handler) was addressed by orchestrator — click handler now reads `open` directly instead of functional updater form
- **Known gap deferred:** Medium finding #2 (Tab-to-close orphaned popup pattern) logged as a follow-up, per user decision; not in FR-203.c or C3e, so not blocking

## Implementation Steps

1. Read the RED evidence. Run `redCommand` once yourself and confirm it still fails the same way.
2. Add `triggerRef` (`useRef<HTMLButtonElement>`) and `optionRefs`
   (`useRef<Array<HTMLButtonElement | null>>([])`), plus `activeIndex` state.
3. On the trigger's `onClick`, when opening, set `activeIndex` to
   `OPTIONS.findIndex((o) => o.value === locale)`. Attach `triggerRef`.
4. Add `useEffect` keyed on `[open, activeIndex]`: when `open`, call
   `optionRefs.current[activeIndex]?.focus()`. This is the single focus authority — no
   `autoFocus`, no focus call scattered in the key handler.
5. Extend the existing document `keydown` listener: on `Escape`, `setOpen(false)` **and**
   `triggerRef.current?.focus()`. Leave the `pointerdown` outside-click path as is (no focus
   return — the user is aiming somewhere else).
6. Replace `<ul>` with `<div role="listbox" aria-label={labels.language} id={listboxId}>`,
   keeping `absolute right-0 top-full z-30 mt-1`, and apply the panel classes from the table.
7. Replace `<li><button …>` with a direct `<button role="option">` child. Apply the option
   classes; make the selected background and the hover background **mutually exclusive** —
   selected gets `bg-[rgba(255,234,158,0.2)]` and no hover class, unselected gets the hover
   class and no background. A ternary on `option.value === locale` is enough.
8. Set `tabIndex={index === activeIndex ? 0 : -1}` on each option (roving tabindex) and
   `ref={(el) => { optionRefs.current[index] = el; }}`.
9. Add `handleListKeyDown` on the panel container:
   - `ArrowDown` → `(activeIndex + 1) % OPTIONS.length`, `preventDefault()`
   - `ArrowUp` → `(activeIndex - 1 + OPTIONS.length) % OPTIONS.length`, `preventDefault()`
   - `Home` → `0`, `End` → `OPTIONS.length - 1`, `preventDefault()`
   - **Nothing else.** Do not intercept `Enter` or `Space` — the native `<button>` already
     fires `onClick` for both, and intercepting Space would double-fire the selection.
10. In `handleSelect`, add `triggerRef.current?.focus()` after `setOpen(false)`, before the
    early return, so selecting the already-active locale also returns focus.
11. Keep the flags `aria-hidden` (the sibling label already names the locale) and keep one
    `<svg>` per option — C3b asserts exactly one, and that the two differ.
12. Update the stale JSDoc at the top of `OPTIONS`: the design *now* has an open state.
    Point the comment at `spec-delta.md §3` and MoMorph `hUyaaugye2`.
13. Run `npm run typecheck` and `npm run lint`.
14. Run `wc -l` and apply the split rule.
15. Run `redCommand`. Report the exit code honestly. Do **not** edit `e2e/login-screen.spec.ts`
    under any circumstance — if a test looks wrong, report it, do not weaken it.

## Todo List

- [x] Rerun `redCommand`, confirm RED is reproducible
- [x] Add `triggerRef`, `optionRefs`, `activeIndex`
- [x] Focus effect on `[open, activeIndex]`
- [x] Escape → close + focus return (in the existing document listener)
- [x] `ul`/`li` → `div role="listbox"` + direct `button role="option"` children
- [x] Apply panel tokens: `#00070C`, `1px solid #998C5F`, `rounded-lg`, `p-1.5`, `flex flex-col`
- [x] Apply option tokens: `w-[108px] h-14 rounded-[2px]`, centered flag + gap 4px + label
- [x] Selected `rgba(255,234,158,0.2)` / hover `rgba(255,234,158,0.08)` — mutually exclusive
- [x] Roving `tabIndex`
- [x] `handleListKeyDown` — Arrow/Home/End only
- [x] `handleSelect` returns focus to trigger
- [x] Focus ring `#998C5F`
- [x] Refresh the stale "design never drew the open dropdown" comment
- [x] `npm run typecheck` clean
- [x] `npm run lint` clean
- [x] `wc -l` ≤ 200, else split to `language-option-list.tsx`
- [x] `redCommand` rerun — report exit code (GREEN on same command)

## Success Criteria

| Criterion | How it is observed |
|---|---|
| Tokens are verbatim | `grep -o '#00070C\|#998C5F\|rgba(255,234,158,0.2)\|rgba(255,234,158,0.08)' app/login/_components/language-selector.tsx` finds all four |
| Invented values gone | `grep -c '#0B0F12\|hover:bg-white/10' app/login/_components/language-selector.tsx` → 0 inside the panel markup |
| Drop-below preserved | `absolute` + `top-full` still present on the panel |
| File size honored | `wc -l` ≤ 200 for every file under `app/login/_components/` |
| Types and lint clean | `npm run typecheck` and `npm run lint` both exit 0 |
| Tests satisfied | `npx playwright test e2e/login-screen.spec.ts --project=anon` exits 0 |
| Spec file untouched | `git diff --name-only` does not list `e2e/login-screen.spec.ts` |

## Risk Assessment

| Risk | Likelihood | Impact | Countermeasure |
|---|---|---|---|
| C3b breaks when `ul`/`li` becomes `div`/`button` | Medium | High | C3b selects by `getByRole("option")` and counts `svg` per option — both survive. Verify C3b explicitly in the phase-02 run, not just at phase 03. |
| Space both scrolls the page and selects | Medium | Medium | Do not handle `Space` in `handleListKeyDown`; the native button consumes it. If the page still scrolls, `preventDefault()` on `Space` in the container **without** calling select. |
| Selected + hover background fight over CSS ordering | Medium | Medium | Never emit both classes on the same element — branch on `option.value === locale`. |
| Focus effect loops (effect sets focus, focus triggers state, re-runs) | Low | High | The effect depends only on `[open, activeIndex]` and calls `.focus()`; no `onFocus` handler sets state. Do not add one. |
| Extracting the panel creates prop-drilling sprawl | Low | Medium | Only split if `wc -l` > 200, and keep the prop surface to the five named props. |
| Chevron accidentally added to panel rows | Low | Low | Design node tree for the VN row is IC + TEXT only (clarifications.md). Chevron belongs to the trigger alone. |
| Turning `aria-hidden` off on flags to "help" a reader | Low | Medium | Labels already name the locale; duplicating it is noise. Leave `aria-hidden`. |
| `p-1.5` / `h-14` mis-mapped in Tailwind v4 | Low | Medium | `p-1.5` = 6px, `h-14` = 56px on the default scale. If the project overrides the scale, fall back to `p-[6px]` / `h-[56px]`. |

## Security Considerations

- Client component with no user-supplied input; `labels` come from the server dictionary, so
  no injection surface is added. Do not introduce `dangerouslySetInnerHTML`.
- The locale value must stay constrained to the `OPTIONS` union (`"vi" | "en"`) so the
  existing `setLocale` server action keeps rejecting anything else — do not widen the type
  to `string`.
- No change to cookie name, scope, or attributes. `NEXT_LOCALE` handling is out of scope.
- No new dependency means no new supply-chain surface.

## Next Steps

- **Depends on:** phase 01 RED evidence.
- **Blocks:** phase 03 (GREEN + visual validation + doc sync).
- **Hand off to phase 03:** the exit code of the final `redCommand` run, the `wc -l` result,
  and whether the split file was created.
