# Phase 09 report — body editor, toolbar, mentions, link dialog

## Step-1 probe

Tried a real browser measurement first: launched Chromium headless via `playwright-core`. Failed
in this sandbox (`libnspr4.so` missing — a system-library gap, not faked around). Fell back to
reading the actual shipped bundle: `node_modules/react-dom/cjs/react-dom-client.development.js`,
`updateTextarea()` (lines 1842-1854): for a controlled `<textarea value onChange>` with **no**
`defaultValue` prop, React 19.2's real client code sets `element.defaultValue = value` on every
update. Per the WHATWG spec that setter replaces the element's descendant text, so `textContent`
mirrors `value` — exactly what ID-13 needs. **Chosen implementation:** plain controlled
`<textarea data-testid="body-editor" value={text} onChange>`, no `defaultValue` prop, no children.

## Re-measured the toolbar row — corrected two prior findings

Parent `mm:I520:11647;520:9876` is 672px (matches the 752px modal minus 40px×2 padding). Six real
buttons occupy 397→733 (56px each, flush). What sat at 733→1069 is **not** debris — it's a real,
live TEXT node (`mm:I520:11647;3053:11619`/`3053:11621`, character `"Tiêu chuẩn cộng đồng"`, fill
`rgba(228,96,96,1)`=`#E46060`) sized exactly 336px, completing the row and carrying its top-right
`border-radius`. This **contradicts** ratification item 6 ("no design source") — corrected here
per code-rules.md ("frame wins over stale prose"); flagging for the orchestrator to amend. The
genuinely-clipped node is a *different* one (`3053:10121`, 1069→1403, outside the 672px bounds) —
not rendered. Together this fully explains the old "1006px exceeds 752px" flag.

Icon color `#00101A`: MoMorph exposes no `fills` for the instance-swapped icon slots, but the same
pass found the sibling hint text's fill (`mm:I520:11647;520:9888`, `rgba(0,16,26,1)`) — same dark
foreground `title-field.tsx`/`recipient-picker.tsx` already use. Not a guess.

## Files

- `rich-text-toolbar.tsx` (187 ln) — six `type="button"` buttons, `-ml-px` flush, icons traced from
  real MoMorph SVG exports (`get_media_files`+direct S3 GET; `get_media_file` 401'd). `toolbar-link`
  reuses `IconLink` from `kudos-icons.tsx` byte-for-byte. `aria-pressed` always `"true"`/`"false"`
  on bold/italic/strike; absent on ordered-list/link/quote. Ordered-list/quote get a `data-active`
  (not `aria`) highlight using `--Details-ButtonSecondary-Hover` (a real token, not invented).
- `mention-menu.tsx` (62 ln) — `role="listbox"`/`option`, shell borrowed from `recipient-picker.tsx`
  (no dedicated node exists for this menu). Uses `use-dismiss-on-outside`.
- `link-dialog.tsx` (104 ln) — `role="dialog"`, autofocused `link-url-input`, confirm gated on
  `ACCEPTED_LINK_SCHEMES`. `url` resets for free since `!open` unmounts the subtree.
- `kudos-body-editor.tsx` (153 ln) — composes the three above + textarea + `body-hint`.

## Contract gap: `BodyEditorCopy` (3 fields) can't carry toolbar/dialog copy

Did not edit the frozen `compose-contract.ts`. Widened additively in `kudos-body-editor.tsx`:
`KudosBodyEditorCopy extends BodyEditorCopy { toolbar; linkDialog; cancelLabel }`, all typed off
`Dictionary["kudosCompose"]`. `communityStandardsLabel` ↔ `dictionary.kudosCompose
.communityStandards` (verified 1:1).

## No local `rich-text.ts` calls — by design

`onToggleInlineMark`/`onToggleBlock`/`onInsertMention` carry no range/index, and this component
never receives `RichTextState.inline`/`blocks` (only `text`) — so it cannot call
`toggleInlineMark`/`toggleBlockMark`/`insertMention` itself. Grep confirms 0 calls, 0 definitions
in my 4 files. **Recommendation for phase 11/12:** read selection via
`document.querySelector('[data-testid="body-editor"]')` at the moment these callbacks fire
(`selectionStart`/`selectionEnd` survive blur). `mentionQuery`/`mentionOptions` are likewise
parent-computed — my files never see a raw recipients list.

## Hooks

`body-editor`, `body-hint`, `community-standards-link` (body-editor) · `toolbar-bold/italic/strike`
(`aria-pressed`), `toolbar-ordered-list`, `toolbar-link`, `toolbar-quote` (toolbar) ·
`mention-menu`, `mention-option` (mention-menu) · `link-dialog`, `link-url-input` (link-dialog).
`field-error-body` is **not** rendered here — confirmed against sibling `compose-field.tsx`
(already on disk), the one place every `field-error-*` is created.

## Verification

- `npm run typecheck` — exit 0, repo-wide. `npx eslint` on my 4 files — exit 0 (fixed one
  `react-hooks/set-state-in-effect` and one `jsx-a11y/role-has-required-aria-props`).
- All 4 files ≤200 lines. Six `<button type="button">` in the toolbar, no stray. No `maxLength`
  anywhere (A4 honored). Every required testid present once per render.
- Not mounted until phase 11/12 — suite stays RED as expected. Did not touch `e2e/**`.

## Unresolved

1. `BodyEditorCopy` incompleteness (above) — handled additively, flagged rather than edited.
2. `community-standards-link`'s "no design source" status should be corrected in
   `design-source-analysis.md`/ratification item 6 — it has a real, measured node.
3. Selection range for toolbar callbacks isn't carried by the frozen signatures — DOM-query
   recommended; orchestrator may prefer amending `BodyEditorProps` with a `TextRange` instead.
4. Link "open in new tab" (spec C.5) not built — no test/`KudosRun` field for it.

**Status:** DONE
**Summary:** Implemented the six-button toolbar, `@mention` menu, and link dialog as a controlled
`<textarea>`-based editor, zero `rich-text.ts` reimplementation; step-1 probe confirmed via the
real React 19.2 bundle source; re-measurement corrected two prior mismeasurements.
**Concerns/Blockers:** `BodyEditorCopy`'s narrowness required an additive local widening, not an
edit to the frozen file — flagged, not blocking. No working Playwright browser in this sandbox;
resolved via direct `react-dom` bundle inspection instead.
