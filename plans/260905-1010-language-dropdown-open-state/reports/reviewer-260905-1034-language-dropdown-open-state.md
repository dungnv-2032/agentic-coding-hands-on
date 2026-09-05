# Review — language-selector.tsx open-state restyle + keyboard nav

## Scope
- Files reviewed: `app/login/_components/language-selector.tsx` (full file + diff), `app/login/_components/icons.tsx` (diff only, read-only reference), `e2e/login-screen.spec.ts` (C1–C5, C10), `spec-delta.md`, `clarifications.md`, `phase-02-implement-open-state-and-keyboard.md`
- Lines: 186 (file) / +90/-28 (diff, language-selector.tsx) / +36 (icons.tsx, new `IconFlagEn`)
- Depth: recent (diff-driven, held against full file + acceptance criteria)

## Assessment
The change is sound and matches its acceptance criteria. Every token in spec-delta §3 lands verbatim (`#00070C`, `#998C5F`, `rounded-lg`=8px, `p-1.5`=6px, `w-[108px] h-14`, `rounded-[2px]`, the two `rgba(255,234,158,…)` backgrounds mutually exclusive via ternary), the `ul`/`li` → `div[role=listbox]`/`button[role=option]` migration is correct and keeps C3b's SVG-count assertion satisfied, keyboard nav (Arrow wrap, Home/End, Escape+focus-return) matches FR-203.c and C3e step-by-step, and `npm run typecheck`/`lint`/e2e all confirm green. File stays at 186 lines, under the 200-line rule, no split needed. One real (but non-blocking) React-purity smell and one genuine keyboard-contract gap (Tab) are worth fixing; everything else is polish.

## Critical
None.

## High
None.

## Medium

**1. `setActiveIndex` called inside `setOpen`'s functional updater — a side effect inside what must be a pure function (`language-selector.tsx:129-136`).**
```js
setOpen((prev) => {
  const next = !prev;
  if (next) setActiveIndex(OPTIONS.findIndex((o) => o.value === locale));
  return next;
});
```
React's contract for the updater form is that it must be pure — no side effects, because React (StrictMode double-invoke in dev, and internally for aborted/replayed renders) may call it more than once for the same commit. Here it's *functionally* harmless today: `OPTIONS.findIndex(...)` doesn't depend on `prev`, so a second invocation recomputes the identical index and `setActiveIndex` bails out via `Object.is` on the repeat — no double render, no wrong value. But it's fragile: the moment someone makes that index computation depend on something that isn't idempotent (or the app later adds `<StrictMode>` behavior around this tree, or a compiler that assumes updater purity), this silently breaks. Compare with the same file's own `handleListKeyDown`, which does this correctly (`setActiveIndex((prev) => (prev + 1) % OPTIONS.length)` — pure, no nested setter).

There is also no functional need for the updater form here at all — this is a synchronous click handler, `open` is read fresh off the latest render, no stale-closure risk exists that would justify `prev`.

**Fix:**
```js
onClick={() => {
  const next = !open;
  setOpen(next);
  if (next) setActiveIndex(OPTIONS.findIndex((o) => o.value === locale));
}}
```
Both setters still batch in the same event handler (React 18 auto-batching), so this produces the identical single re-render with no side-effect-in-updater smell.

**2. Tab out of the open panel does not close it (`FR-203.c` gap, not covered by C3e).**
`handleListKeyDown` only handles `ArrowDown`/`ArrowUp`/`Home`/`End`; `Tab` falls through the `default` branch and is not `preventDefault()`-ed, so the browser's native tab order takes over and moves focus past the roving-tabindex option to whatever's next on the page — while the panel stays mounted and visually open. FR-203.c does not explicitly list Tab, and no test (C3e or otherwise) exercises it, so this isn't a broken acceptance criterion, but it is a real listbox-pattern gap: a floating panel that stays open with focus already outside it is the classic "orphaned popup" bug reported by a11y audits and by users tabbing through the page. Not blocking this seal (nothing in the executable contract requires it), but worth a follow-up: close the panel (without stealing focus back) on `Tab`/`Shift+Tab` inside `handleListKeyDown`, mirroring the outside-click "no forced focus return" behavior.

## Low

**3. `aria-controls={listboxId}` on the trigger points at a non-existent DOM node while the panel is closed (`language-selector.tsx:126`, pre-existing).** The panel is conditionally rendered (`{open && (...)}`), so `aria-controls` references a dangling ID except while open. This is unchanged by this diff (present identically before it) — flagging for completeness since it was one of the specific things asked about, not as a regression. `axe-core`/similar linters will flag "aria-controls references non-existent element" whenever closed. Cheapest real fix, if ever picked up: keep the panel always mounted (`display:none`/`hidden` when closed) instead of conditional unmount, or drop `aria-controls` when `!open`. Out of scope for this phase (spec-delta doesn't ask for it); noting for the backlog.

**4. `IconFlagEn` is hand-drawn, not sourced from a MoMorph node, and wasn't run through the clarification protocol (`icons.tsx:69-103`).** The JSDoc is honest about this ("No MoMorph counterpart... Hand-drawn here") and it's a legitimate fix — before this change the trigger showed the VN flag next to the "EN" label (the flag/CurrentFlag JSDoc at `language-selector.tsx:114-116` names exactly this bug). Necessary to satisfy FR-203.a ("each option has its own flag") and C3b (two distinct SVGs). Still, it's a new visual asset invented without a design source, which the momorph-development rules generally want gated through clarification. Low severity because it's honestly labeled, narrowly scoped (geometry matched to `IconFlagVn` deliberately), and doesn't block the visual contract in spec-delta §3 (which only covers the panel, not the flag artwork). Worth a one-line note in `clarifications.md` for traceability, not a rework.

## Edge Cases Turned Up
- **Outside-click while focus sits on an option:** clarifications.md explicitly rules out focus-return on outside-click ("user aimed elsewhere"). If the click lands on a non-focusable area, the option node about to unmount loses focus to `<body>` (standard browser behavior when a focused node is removed) rather than to any visible element. This matches the recorded decision; flagging only so it's a known, not undiscovered, trade-off.
- **Reopening at the same locale:** `activeIndex` gets recomputed to the same value; the focus effect still re-fires correctly because `open` (not just `activeIndex`) changed — no missed refocus.
- **Escape bubbling:** `handleListKeyDown` never calls `stopPropagation()`, so Escape correctly still reaches the document-level listener (single source of truth, per the phase's DRY note) even though it's not handled in the panel's own switch. Verified this isn't accidentally swallowed.
- **Space on a focused `<button>`:** native button behavior already calls `preventDefault()` on the browser's default scroll, so the "Space scrolls the page" risk flagged in the phase file's risk table doesn't materialize — confirmed no extra handling was needed, matching what shipped.

## Done Well
- Visual contract is verbatim from spec-delta §3 — no invented Tailwind values, and the removed classes (`bg-[#0B0F12]`, `hover:bg-white/10`, `shadow-lg`, `overflow-hidden`, `min-w-[108px]`, `py-1`, `px-4 py-2` on options) are exactly the ones the phase file called out to remove.
- Single focus authority (the `[open, activeIndex]` effect) is real — no competing `.focus()` calls scattered in the key handler, and `handleSelect`'s focus-return runs before the effect fires with `open=false`, which short-circuits, so there's no fight for focus.
- Escape handling is genuinely DRY: extended the existing document-level listener instead of adding a second Escape path inside `handleListKeyDown`.
- Roving tabindex (`tabIndex={index === activeIndex ? 0 : -1}`) is the correct alternative to `aria-activedescendant` when real DOM focus moves between options — using both would be redundant/conflicting; using neither would break screen-reader option semantics. This gets it right.
- Selected/hover backgrounds are properly mutually exclusive via a single ternary, avoiding the CSS-ordering fight the phase's own risk table warned about.
- File stayed at 186 lines — no unnecessary split, matching the deterministic split rule (`≤200` ⇒ don't split).
- Locale persistence (`setLocale` server action, `NEXT_LOCALE` cookie) is untouched — confirmed by reading `app/login/actions.ts`; no drift from BR-003.
- C1's selector (`aria-label*="VN"|"EN"`) still resolves correctly since `aria-label` composition on the trigger is unchanged — verified no regression there.

## Actions In Order
1. (Medium) Move `setActiveIndex` out of `setOpen`'s updater in the trigger's `onClick` — read `open` directly instead of the functional form (`language-selector.tsx:128-136`).
2. (Medium) Decide whether `Tab`/`Shift+Tab` should close the panel; if yes, add it to `handleListKeyDown` as a follow-up phase (not blocking — not in FR-203.c or C3e).
3. (Low) Note `IconFlagEn`'s invented-asset status in `clarifications.md` for traceability.
4. (Low, backlog) Consider always-mounted panel or conditional `aria-controls` to close the dangling-ID gap — pre-existing, not introduced here.

## Numbers
- Type coverage: `npm run typecheck` exits 0 (verified state, not re-run)
- Test coverage: 11/11 e2e (`--project=anon`), 10 named scenarios in `login-screen.spec.ts` (C1, C2, C3, C3b, C3c, C3d, C3e, C4, C5, C10) all pass
- Lint findings: 0 (`npm run lint` clean, verified state)

## Still Unresolved
- Whether Tab-to-close is actually wanted (item 2) — FR-203.c doesn't ask for it, so this is a product-scope question, not a defect in what was built.
