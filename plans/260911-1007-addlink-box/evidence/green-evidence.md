# GREEN evidence — Addlink Box (`OyDLDuSGEa`)

## Result

`npm run test:e2e -- e2e/viet-kudo.spec.ts --project=kudos-authed` → **exit 0, 72 passed (3.2m)**.

Every one of the nine tests that was RED is now green, and no previously-green test regressed —
the suite went from 63 green + 9 red to 72 green, with the same test count before and after.

| Command | Exit | Result |
|---|---|---|
| `npm run test:e2e -- e2e/viet-kudo.spec.ts --project=kudos-authed` | 0 | 72 passed (3.2m) |
| `... -g "ID-31\|ID-68"` | 0 | 3 passed (2.1m) |
| `npx tsc --noEmit` | 0 | clean tree-wide |
| `npm run lint` | 0 | 0 errors, 31 pre-existing warnings |
| `npm run test:e2e -- --project=addlink-box-visual-capture` | 0 | 2 passed, 3 PNGs |

## One failure was a test defect, not an implementation bug

The first GREEN attempt reported ID-68 failing and attributed it to "outside-click dismiss not
working" in `link-dialog.tsx` / `use-body-editor-controller.ts`. That diagnosis was wrong.

The test called `await page.click(".fixed")`. Playwright aims at an element's **centre**, and the
overlay's centre is exactly where the centred dialog panel sits — so the click landed *on* the
dialog, inside `rootRef`. `useDismissOnOutside` then correctly declined to dismiss. The
implementation was right; the test was asking the wrong question.

Fixed by clicking a genuine outside point (`page.mouse.click(20, 20)` — over the overlay, clear of
the panel), with the reason recorded in a comment so nobody re-introduces it. ID-68 passed in
1.0s on the very next run, no implementation change of any kind.

The same attempt also flagged ID-31 as a "JWT clock skew transient". ID-31 has since passed in two
independent runs, so nothing was left outstanding there.

## Visual evidence

Three states at 1440px, clipped to the panel, each **asserting** its state before the screenshot:

| File | Asserted before capture |
|---|---|
| `addlink-box-empty-1440.png` | both inputs visible, both `toHaveValue("")` |
| `addlink-box-errors-1440.png` | `link-text-error` AND `link-url-error` both visible |
| `addlink-box-filled-1440.png` | valid text + URL entered, neither error visible |

The error shot confirms the state the frame never drew: both fields red-bordered with
"Không được để trống" beneath each, the dialog still open, and `Lưu` still clickable — which is the
whole point of dropping the disabled-button gate.

## Rework after inspection (2026-09-11)

The `reviewer` returned **REWORK, score 6.5, 0 critical, 2 High**. Both were real and both are fixed:

1. **No focus trap, so the captured range could go stale.** `aria-modal="true"` promises focus is
   confined, but only pointer-outside and `Escape` were handled — Shift+Tab from the first input
   reached the live `body-editor` behind the dialog, letting a user edit the body and then confirm
   against a range captured against different text. Fixed by trapping `Tab`/`Shift+Tab` inside the
   panel (`link-dialog.tsx`), and by clamping the captured range to the current text length at
   confirm (`use-body-editor-controller.ts`) as defense behind the trap.
2. **FR-213's focus lift was never implemented.** Both inputs carried `outline-none` with nothing
   put back — an unmet acceptance criterion and a WCAG 2.4.7 regression. Fixed with a
   `focus:border-[#00101A] focus:ring-2 focus:ring-[#FFEA9E]` treatment, flagged unauthored
   because the frame draws no focus state.

The Medium finding — no test ever asserted the link **run**, only its plain text — was also closed
rather than deferred: **ID-69** now inserts a link through the dialog, submits, and asserts the
board renders `a[href="https://www.example.com/"]` with that text. A regression collapsing
`insertLink` to plain concatenation now fails a test instead of passing one.

The fix pushed `link-dialog.tsx` to 214 lines, over the repo's 200-line rule. The two field rows
were near-identical, so they were extracted into `link-dialog-field.tsx` — DRY and the size fix in
one move. `link-dialog.tsx` 183, `link-dialog-field.tsx` 81.

| Command | Exit | Result |
|---|---|---|
| `npm run test:e2e -- e2e/viet-kudo.spec.ts --project=kudos-authed` | 0 | **73 passed (2.5m)** |
| `npx tsc --noEmit` | 0 | clean |
| `npm run lint` | 0 | 0 errors, 31 pre-existing warnings |

ID-31 failed once in a `-g` filtered run (`toolbar-link` never appeared within 30s) and passes in
526ms inside the full suite. That is Next dev's cold compile landing on whichever test runs first
in a filtered run — the same flake the hashtag-dropdown plan documented for ID-15 — not a
regression.

### Known gap

The three PNGs in this directory were captured BEFORE the focus-ring fix, so they do not show the
new focus treatment. Every other assertion in them still holds. Re-run
`npm run test:e2e -- --project=addlink-box-visual-capture` to refresh them.
