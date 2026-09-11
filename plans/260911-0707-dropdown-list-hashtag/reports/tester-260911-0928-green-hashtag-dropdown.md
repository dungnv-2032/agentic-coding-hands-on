# GREEN + visual evidence — Dropdown list hashtag (phase 03)

## GREEN run

`npm run test:e2e -- e2e/viet-kudo.spec.ts --project=kudos-authed -g "ID-15|ID-16|ID-17|ID-53|ID-57|ID-58|ID-59|ID-60"`
→ **8 passed, 1 failed (2.1m)**. The single failure was ID-15 timing out on
`getByTestId('hashtag-add')` as the FIRST test of the run — Next dev's cold compile of
`/kudos/new` exceeding the 30s test timeout, not a behavior change.

Confirmed by re-running with a warm-up test ahead of it:
`-g "ID-14|ID-15|ID-16"` → **exit 0, 4 passed (51.2s)**, ID-15 green in 2.1s.

| Test | RED | GREEN |
|------|-----|-------|
| ID-57 toggle off | FAIL (count 2, expected 0) | **PASS** |
| ID-58 check icon + 24×24 slot | FAIL (`hashtag-check` absent) | **PASS** |
| ID-59 cap disable + standing error + exit via selected row | FAIL (enabled) | **PASS** |
| ID-17 cap (re-pointed) | FAIL (enabled) | **PASS** |
| ID-53 cap (re-pointed) | FAIL (enabled) | **PASS** |
| ID-60 order stability | PASS (guard) | **PASS** |
| ID-15 add one | not in RED scope | **PASS** (green on warm run; cold-compile flake when run first) |
| ID-16 add five | not in RED scope | **PASS** |

Gates: `npm run typecheck` exit 0 · `npm run lint` 0 errors (29 warnings, all pre-existing
unused-import warnings elsewhere in the suite) · `hashtag-picker.tsx` 168 lines,
`hashtag-option-row.tsx` 86 lines — both under the 200-line rule.

## Visual evidence

`npm run test:e2e -- --project=hashtag-dropdown-visual-capture` → exit 0. Three states in
`evidence/`, each clipped to the menu box so the whole list is actually in frame:

- `hashtag-dropdown-empty-1440.png` — every row unselected, check slots empty, no reflow.
- `hashtag-dropdown-one-selected-1440.png` — one row lifted (`rgba(255,234,158,0.2)`) with the
  circular check at its right edge; the other twelve full-brightness and enabled.
- `hashtag-dropdown-at-cap-1440.png` — five selected with checks, eight unselected dimmed and
  `disabled` (asserted, not just photographed), order still `hashtags.position`.

Checked against the MoMorph frame image for `p9zO-c4a4x`: row height, 16px padding, selected
fill, check-at-right placement and the dark `#00070C` menu all match. Data is the real local
Supabase `public.hashtags` (13 rows), not the frame's mock labels.

## NOT verified

The **full** `e2e/viet-kudo.spec.ts` suite (~60 tests) was not run — the user stopped it before
it started. Only the 9 hashtag-related tests above have been exercised against this change.
Tests outside the hashtag group that touch the compose form are unverified against it.

## Unresolved questions

- Full-suite regression run still outstanding.
