# Review — F008 Floating Action Button (uncommitted)

## Scope
- Files reviewed: `app/_components/floating-widget.tsx` (primary), `app/_components/use-dismiss-on-outside.ts` (unchanged, read for contract), `lib/i18n/messages/{dictionary.ts,vi-home.ts,en-home.ts}`, `public/images/home/widget-pen-icon.svg`, `e2e/floating-action-button.spec.ts`, `e2e/fixtures/floating-action-button-constants.ts`, `e2e/the-le.spec.ts`, `e2e/fixtures/the-le-constants.ts`, `playwright.config.ts`
- Lines: `floating-widget.tsx` 128 lines (well under the 200-line guidance); diff total ~191 insertions / 39 deletions across tracked files
- Depth: recent (uncommitted diff) + targeted read of plan/clarifications/geometry docs for intent
- Verified independently: `npx tsc --noEmit` (clean, no output), `npx eslint` on all seven touched/new TS/TSX files (0 errors, 1 warning), grep sweep for other consumers of `Dictionary["home"]["widget"]` and other e2e specs asserting on the old two-link shape (none found). Did not re-run Playwright — evidence already recorded GREEN and the brief says not to re-run.

## Assessment
Solid piece of work. The disclosure-trigger conversion is well reasoned, cites its own design authority (`313:9138 → 313:9139` navigation edge) instead of guessing, reuses the shared `useDismissOnOutside` hook instead of reinventing outside-click/Escape handling, keeps the trigger mounted through the whole lifecycle for a defensible reason (documented in the docblock), and the geometry/typography values in the component map 1:1 to `design/geometry.md`. Both locale files and the `Dictionary` interface stay in lockstep — no partial i18n. The `the-le.spec.ts` adaptation is a legitimate re-routing of an existing assertion, not a weakening of it. One real keyboard-focus defect below should be fixed before this ships; everything else is small.

## Critical
None.

## High

**1. Keyboard focus is dropped to `<body>` after closing via the Hủy button — inconsistent with the Escape path.**
`app/_components/floating-widget.tsx:119` — `<button data-testid="fab-close" ... onClick={close} ...>`. `close` is `useCallback(() => setOpen(false), [])` (line 40), the same callback passed as `onDismiss` to `useDismissOnOutside`. Clicking (or Enter/Space-activating) `fab-close` unmounts the `fab-menu` subtree on the next render. In Chromium/Firefox (the project's actual Playwright browser, `devices["Desktop Chrome"]`), a button typically receives native focus when clicked/activated — so at the moment of unmount, focus is sitting on a node about to disappear. When a focused DOM node is removed, focus reverts to `document.body` with no restoration, since only the `useDismissOnOutside` hook's own `Escape` branch (`use-dismiss-on-outside.ts:28-33`) calls `triggerRef.current?.focus()`. `close()` itself never does. A keyboard user who dismisses the menu with Hủy is left with no visible focus indicator anywhere on the page — a real regression for exactly the population `aria-expanded`/`aria-controls` were added for.
This gap isn't caught by FAB-05 (`e2e/floating-action-button.spec.ts:138-158`), which asserts the menu is detached and the trigger is visible/`aria-expanded=false`, but never asserts `document.activeElement`. Compare FAB-06, which does assert focus for the Escape path.
Fix: give the close button its own handler that also restores focus, without touching the shared `close`/`onDismiss` used by `useDismissOnOutside` (that one must keep *not* moving focus, per clarifications.md's explicit "outside click does not move focus" rule, and FAB-07 enforces it):
```tsx
onClick={() => {
  setOpen(false);
  triggerRef.current?.focus();
}}
```
This keeps the three dismissal paths behaviorally distinct exactly as clarifications.md intends (Hủy and Escape return focus; outside-pointerdown does not) instead of leaving Hủy unspecified and accidentally broken.

## Medium

**2. `fab-write-kudos`'s `aria-label` diverges from its visible text only by casing, and — unlike `fab-standards` — nothing asserts it.**
`floating-widget.tsx:106` sets `aria-label={widget.writeKudos}` ("Viết kudos" / vi-home.ts) while the button's visible text at line 111 is `widget.menuWriteKudos` ("Viết KUDOS"). This still satisfies WCAG 2.5.3 (case-insensitive substring match) so it's not a defect on its own, but it's inconsistent with the sibling `fab-standards` button, whose `aria-label` reuse of the old `widget.standards` key is deliberate and pinned by an explicit assertion (`e2e/the-le.spec.ts:212`, `toHaveAccessibleName(WIDGET_STANDARDS_LABEL)`). There is no equivalent assertion for `fab-write-kudos`'s accessible name anywhere in `floating-action-button.spec.ts`, so a future edit to either `writeKudos` or `menuWriteKudos` could silently drift further apart with nothing to catch it. Either add a `toHaveAccessibleName` assertion for `fab-write-kudos` (mirroring the standards precedent) or drop the now-redundant `aria-label` and let the visible text stand as the accessible name — the button has clear content, unlike the trigger/close which are icon-only and genuinely need one.

## Low

**3. Dead import in the new spec.** `e2e/floating-action-button.spec.ts:14` imports `COMPOSE_ROUTE` but never uses it (confirmed by `npx eslint`: `'COMPOSE_ROUTE' is defined but never used`). It's a warning, not an error, so `npm run lint` still exits 0 and AC8 technically holds — but FAB-04 (lines 123-136) would be a slightly stronger test if it asserted the URL is *not* `COMPOSE_ROUTE` in addition to matching `LOGIN_ROUTE`, which is presumably what the import was for. Either use it that way or remove it.

**4. Kudos-glyph icon rendered 24×23, not the drawn 24×24.** `floating-widget.tsx:70-76` and `:90-96` render `widget-saa-kudos-glyph.svg` at `width={24} height={23}`, preserving the source asset's 20:19 aspect ratio rather than the flat 24×24 `design/geometry.md:56` calls for. Cosmetic (1px), not covered by AC6's geometry assertions (those check container/button/label boxes, not this inner icon), and arguably the more defensible call visually (avoids distorting the glyph) — flagging only so it's a conscious trade-off rather than an overlooked spec deviation.

## Edge Cases Turned Up (scouting pass, beyond the diff)
- **Painting order vs. `pointer-events`**: while open, the invisible trigger (`position: absolute`) paints after (visually atop) the static-flow `fab-menu` per CSS painting order, but `pointer-events-none` correctly removes it from hit-testing, so clicks reach the real menu buttons underneath. Verified this is intentional (the docblock explains the tabIndex/pointer-events trade-off) — not a bug.
- **Escape-then-focus ordering**: `useDismissOnOutside`'s `onKeyDown` calls `onDismiss()` (schedules the React state update) then synchronously `triggerRef.current?.focus()` *before* React re-renders — this only works because `tabIndex={-1}` still permits programmatic focus on an element not yet visually restored. Confirmed correct; the docblock (lines 24-28) explicitly reasons about this.
- **Pointerdown-vs-click race on internal buttons**: clicking `fab-close`/`fab-standards`/`fab-write-kudos` fires a `pointerdown` on `document` first; `rootRef.current.contains(event.target)` correctly suppresses the outside-dismiss path for all three, so there's no double-toggle or premature close-before-navigate.
- **No other consumer breaks on the widened `Dictionary["home"]["widget"]` type** — grepped for other object literals typed as `Dictionary["home"]["widget"]` or files importing `FloatingWidget`; only `app/page.tsx` and the two locale files exist, both already updated. `tsc --noEmit` confirms.
- **No other e2e spec depended on the old two-`<Link>` shape** — grepped `e2e/` for `home.widget`, `WIDGET_`, and role="link" assertions on the widget; only `the-le.spec.ts` did, and it's already adapted in this diff. `homepage.spec.ts`/`homepage-authed.spec.ts` (named in `study-context.json`'s blastRadius as at-risk) only mention "floating widget" in a comment, no assertion — the blast-radius note was conservative but nothing actually broke.
- `e2e/capture-fab-visuals.spec.ts` and `e2e/collect-fab-measurements.spec.ts`, mentioned in the brief as throwaway scaffolding to delete — confirmed they no longer exist in the working tree (`git status` shows neither); nothing to weigh in on.

## Done Well
- Docblock explains *why*, not just *what* — the tabIndex/pointer-events/focus interplay is genuinely non-obvious and is exactly the kind of thing that would otherwise get "simplified" into a bug later.
- Reused `useDismissOnOutside` rather than re-implementing outside-click/Escape handling a fourth time in the codebase.
- `data-testid` contract fixed in `clarifications.md` before either the RED spec or the component existed, so implementation and test couldn't drift independently.
- Geometry, colors, and typography in the component are traceable line-by-line to `design/geometry.md` — no invented values.
- `the-le.spec.ts` adaptation is a genuine re-routing of the same assertion (open FAB → click `fab-standards`) rather than a weakened or duplicated test, and it upgrades the assertion with an explicit `toHaveAccessibleName` check that wasn't there before.
- i18n stayed disciplined: both `vi-home.ts` and `en-home.ts` got all four new keys, `Dictionary` interface updated in the same commit-to-be, `tsc --noEmit` confirms no drift.

## Actions In Order
1. Fix finding 1 (High) — give `fab-close` its own `onClick` that restores focus to the trigger, leaving the shared `close`/`onDismiss` used by `useDismissOnOutside` untouched.
2. Resolve finding 2 (Medium) — either assert `fab-write-kudos`'s accessible name or drop its now-redundant `aria-label`.
3. Clean up finding 3 (Low) — use or remove the unused `COMPOSE_ROUTE` import.
4. Optional: reconcile finding 4 (Low) — either accept the 24×23 icon rendering as the deliberate choice (recommended) or size it 24×24 to match `geometry.md` literally.

## Numbers
- Type coverage: `npx tsc --noEmit` — 0 errors
- Test coverage: not re-run per instructions; prior evidence (`plans/260910-0907-floating-action-button/evidence/green-evidence.md`) records GREEN for `npx playwright test e2e/floating-action-button.spec.ts --project=anon`
- Lint findings: 1 warning (`no-unused-vars`, `e2e/floating-action-button.spec.ts:14`), 0 errors, across all 7 touched/new TS/TSX files

## Still Unresolved
- Whether finding 1's fix should be applied before or as part of this commit is a judgment call for whoever owns the merge — it's a real defect but scoped to a single `onClick` handler, not a structural problem.

**Status:** DONE_WITH_CONCERNS
**Summary:** One High finding (keyboard focus lost to `<body>` on Hủy-close, `floating-widget.tsx:119`) should be fixed before merge; everything else is Medium/Low polish. Typecheck and lint both clean, no contract or i18n breakage, no other test depends on the old two-link shape.
**Concerns/Blockers:** Finding 1 (High) is a genuine accessibility regression not caught by the existing test suite.
