---
phase: 03
title: "Disclosure conversion — floating-widget.tsx"
status: complete
owner: momorph-ui-implementer
track: A
test_policy: e2e-red-first
effort: 1.5h
depends_on: [01, 02]
momorph_screens: ["_hphd32jN2", "Sv7DFwBw1h"]
momorph_file_key: 9ypp4enmFmdK3YAFJLIu6C
---

# Phase 03 — Disclosure conversion (`floating-widget.tsx`)

## Context Links

- MoMorph collapsed: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/_hphd32jN2 (node `313:9138`)
- MoMorph expanded: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/Sv7DFwBw1h (node `313:9140`)
- [design/geometry.md](design/geometry.md) — **the only source of visual values**
- [clarifications.md](clarifications.md) — resolved decisions; `get_frame_image` misrenders both
  FAB frames, so never validate against a thumbnail
- [technical-spec](spec/floating-action-button/technical-spec.md) § 3.1-3.4 ·
  [functional-spec](spec/floating-action-button/functional-spec.md) FR-201..FR-205, FR-401, FR-601
- RED contract: [phase-01](phase-01-red-e2e-gate.md) · copy source: [phase-02](phase-02-i18n-and-icon-assets.md)
- Disclosure precedent in-repo: `app/_components/language-selector.tsx`

## Overview

- **Priority:** P1 — this is the feature.
- **Status:** pending
- Turn the server-rendered pill into a `"use client"` disclosure: `open` state, `aria-expanded` /
  `aria-controls`, three buttons at measured geometry, dismissal via `Hủy` / Escape /
  outside-pointerdown through the existing `use-dismiss-on-outside.ts`.

## Key Insights

- The design's own navigation edge settles the shape: node `313:9138` → `313:9139`, i.e. the pill
  points at the *expanded state*, not at a destination. The two icons and the `/` become the
  trigger's content, not two hit targets.
- `app/page.tsx` needs no edit: it already passes `dictionary.home.widget`, and the prop type
  `Dictionary["home"]["widget"]` simply grew. Do not touch it.
- `use-dismiss-on-outside.ts` already encodes the exact contract required (Escape closes and
  returns focus to the trigger; outside pointerdown closes without moving focus). Reuse it
  as-is — do not re-implement, do not modify it.
- Container size is emergent, not hard-coded: `64 + 20 + 64 + 20 + 56 = 224` tall and `214` wide
  from the widest child. A flex column with `items-end gap-5` produces both.
- The measured right/bottom page margins differ between the two frames (endX 1297 vs 1302) and
  clarifications freeze the current anchor. Keep `fixed right-6 bottom-6` exactly as shipped;
  measured numbers govern the component's internals only.
- Montserrat is inherited: `app/page.tsx`'s root div carries `font-montserrat` and the widget is
  its DOM child even though it is `fixed`. No font class needed on the widget.
- The kudos glyph is authored `20×19` but the design calls a `24×24` slot. Scale to width 24 with
  the authored aspect preserved (`24×23`) inside a `h-6 w-6` centred box — the slot matches the
  measurement and the artwork is not distorted. This also corrects the shipped pill, whose
  `106px` design width only adds up with a 24px glyph: `16+42+8+24+16 = 106`.

## Requirements

Functional (FR → behaviour):
- FR-201 pill is a real `<button type="button">` with `aria-expanded={open}` and `aria-controls`
  bound to the menu's `useId()` id; content stays pen + `/` + glyph.
- FR-202 clicking reveals `Thể lệ`, `Viết KUDOS`, `Hủy` at the geometry below.
- FR-203 `Thể lệ` is a `<Link href="/standards">`; FR-204 `Viết KUDOS` is a `<Link href="/kudos/new">`.
- FR-205 `Hủy` closes; FR-401 Escape and outside pointerdown close identically.
- FR-601 no auth logic here — `proxy.ts` handles the anonymous redirect. The item is never hidden
  or disabled for anonymous users.
- BR-005 below `1024px` the two main buttons shrink to content; widths are minimums, not hard sizes.
- BR-006 `open` is client-local; a reload resets it to `false`.

Non-functional: no new dependency, file stays under 200 lines, `npm run typecheck` and
`npm run lint` exit 0.

## Architecture

```
FloatingWidget ("use client")
├─ state: open (useState<boolean>), menuId (useId), rootRef, triggerRef
├─ useDismissOnOutside(open, rootRef, triggerRef, () => setOpen(false))   [existing hook, as-is]
├─ open === false → <button data-testid="fab-trigger" aria-expanded={false} aria-controls={menuId}>
│                     pen 24 · "/" · glyph 24        (106×64 pill, radius 100px, #FFEA9E)
└─ open === true  → <div id={menuId} data-testid="fab-menu">   flex-col items-end gap-5
                    ├─ <Link href="/standards"  data-testid="fab-standards">    149×64
                    ├─ <Link href="/kudos/new"  data-testid="fab-write-kudos">  214×64
                    └─ <button data-testid="fab-close">                          56×56 round #D4271D
```

Both states live inside one `fixed right-6 bottom-6 z-30` root, so `rootRef` covers whichever is
rendered and outside-detection works in both.

Visual contract — every value from `design/geometry.md`, none invented:

| Element | Size | Radius | Background | Padding · gap | Content |
|---------|------|--------|-----------|---------------|---------|
| `fab-trigger` | 106×64 | `100px` (full) | `#FFEA9E` | `p-4` · `gap-2` | pen 24×24, `/` (700/24/32, `#00101A`), glyph 24×24 slot |
| `fab-menu` | 214×224 emergent | — | none | `gap-5` (20px), `items-end` | the three buttons |
| `fab-standards` | `lg:w-[149px] h-16` | `4px` | `#FFEA9E` | `p-4` · `gap-2` | glyph 24×24 slot + `menuStandards` |
| `fab-write-kudos` | `lg:w-[214px] h-16` | `4px` | `#FFEA9E` | `p-4` · `gap-2` | pen 24×24 + `menuWriteKudos` |
| `fab-close` | 56×56 | full round | `#D4271D` | `p-4` | `/images/rules/close-icon.svg` 24×24 |

Labels: `font-bold text-2xl leading-8 text-[#00101A] text-center` (Montserrat 700 · 24/32 ·
`#00101A`). Trigger keeps the shipped shadow
`0 4px 4px rgba(0,0,0,0.25), 0 0 6px #FAE287`.

Accessible names: trigger `widget.trigger`; `fab-standards` `aria-label={widget.standards}`
("Thể lệ SAA" — what phase 04's constant matches); `fab-write-kudos`
`aria-label={widget.writeKudos}`; `fab-close` `aria-label={widget.close}`. Icons stay
`alt="" aria-hidden`.

## Related Code Files

Modify: `app/_components/floating-widget.tsx` (sole owned file).

Read for context: `app/_components/use-dismiss-on-outside.ts`, `app/_components/language-selector.tsx`,
`lib/i18n/messages/dictionary.ts`, `design/geometry.md`, `e2e/floating-action-button.spec.ts`.

Create: none. Delete: none. Not modified: `app/page.tsx`, `use-dismiss-on-outside.ts`, `proxy.ts`,
any asset, any i18n file, any spec file.

## Implementation Steps

1. Add `"use client"`; import `useId`, `useRef`, `useState`, `useDismissOnOutside`.
2. Rewrite the docblock: the old one asserts "two direct links … no quick-action menu". Replace it
   with the current reading (navigation edge `313:9138` → `313:9139`, clarifications.md) so the
   file stops documenting the superseded design.
3. Build the root: `<div ref={rootRef} className="fixed right-6 bottom-6 z-30">`.
4. Collapsed branch: the trigger button with the three inline marks and the fixed testid.
5. Expanded branch: the menu container plus the two `<Link>`s and the close button.
6. Wire `useDismissOnOutside(open, rootRef, triggerRef, close)` — one `useCallback`-stable
   `close` so the hook's effect does not resubscribe every render.
7. Keep `mm:` node-id comments next to each element, matching the file's existing convention.
8. `npm run typecheck && npm run lint`.
9. Run the fixed command locally for signal only — phase 05 owns the official GREEN.

## Todo List

- [ ] `"use client"` + `open`/`useId`/refs in place
- [ ] Trigger: testid, `aria-expanded`, `aria-controls`, 106×64 pill preserved
- [ ] Menu: `items-end gap-5`, the three buttons with fixed testids
- [ ] All measured sizes/colours/radii applied from `design/geometry.md`
- [ ] Glyph rendered in a 24×24 slot without distortion; pen renders dark
- [ ] `useDismissOnOutside` reused unmodified
- [ ] Responsive: widths are `lg:` minimums, buttons shrink below 1024px
- [ ] Stale docblock replaced
- [ ] typecheck + lint exit 0; file under 200 lines

## Success Criteria

- FAB-01..FAB-08 from phase 01 pass locally (official verdict is phase 05).
- `app/page.tsx` shows no diff.
- `git diff --stat` lists exactly one changed source file.
- No `data-testid` other than the five fixed ones is introduced.

## Risk Assessment

| Risk | L×I | Countermeasure |
|------|-----|----------------|
| Guessing a visual value the CSV/geometry does not state | M×H | Every value comes from the table above; anything absent is a `NEEDS_CONTEXT`, never an invention |
| Validating against a MoMorph frame image | M×M | `get_frame_image` misrenders both FAB frames (clarifications); validate against numbers only |
| Re-implementing dismissal instead of reusing the hook → focus contract drifts from the other popovers | M×M | Hook reuse is a requirement; FAB-06/FAB-07 assert the focus difference |
| Unstable `onDismiss` identity causes listener churn / missed pointerdown | L×M | `useCallback` for `close`, mirroring the hook's documented usage |
| Hard-coding 214/149 breaks narrow viewports | M×M | `lg:` prefixed widths per BR-005; geometry asserted at 1440 only |
| Moving the page anchor to the measured 138/120px margins | M×M | Anchor frozen at `right-6 bottom-6` by clarifications; the two frames disagree anyway |
| Menu markup rendered while `open === false` (hidden) | L×M | FAB-01 asserts `fab-menu` is absent, not merely invisible |

## Security Considerations

- No new auth logic: `Viết KUDOS` is a plain `<Link>`; the `proxy.ts` guard remains the single
  source of truth for who may reach `/kudos/new` (BR-003). Do not hide or disable the item.
- Becoming a client component adds no data to the client bundle — the props are already-public
  UI copy; no session, token or Supabase key crosses the boundary.
- No `dangerouslySetInnerHTML`; SVGs are served as `<Image>` sources, not inlined.

## Next Steps

- Unblocks the verification of phase 04 and the GREEN run in phase 05.
- Rollback note: reverting this file alone leaves phase 04's adapted FUN_003 red — revert 03 and
  04 together.
