# GREEN evidence — Dropdown list hashtag

Full compose suite: `npm run test:e2e -- e2e/viet-kudo.spec.ts --project=kudos-authed`
→ **64 passed, exit 0 (1.6m)**. Every RED assertion above is now green, and no previously-green
test went red.

## The two first-test failures, and why they are not this change

Two earlier runs each failed on their FIRST test only:

- `-g "ID-15|…"` → 8 passed, 1 failed: ID-15 timed out on `getByTestId('hashtag-add')`.
- full suite (first attempt) → 63 passed, 1 failed: ID-0 resolved `<h1>This page couldn't load</h1>`.

Both were contradicted by green re-runs: `-g "ID-14|ID-15|ID-16"` exit 0 with ID-15 green in 2.1s,
and the full-suite re-run at 64 passed exit 0.

Cause is structural, not behavioral. `playwright.config.ts` sets `reuseExistingServer: false` and
waits only on `http://127.0.0.1:3000`, so the first navigation to `/kudos/new` pays Next dev's cold
compile against a 30s test timeout. A genuine defect in the component would have taken down the
other 63 tests, which all load the same page. Recorded as a deferred finding against the harness.

## Visual validation

`npm run test:e2e -- --project=hashtag-dropdown-visual-capture` → exit 0, three states captured at
1440px, clipped to the menu box so the whole list is in frame:

- `hashtag-dropdown-empty-1440.png` — all rows unselected, check slots empty, no reflow.
- `hashtag-dropdown-one-selected-1440.png` — one row lifted with the circular check at its right;
  the other twelve full-brightness and enabled.
- `hashtag-dropdown-at-cap-1440.png` — five selected with checks, eight unselected dimmed and
  `disabled` (asserted before capture, not merely photographed), order still `hashtags.position`.

Checked against the MoMorph frame image for `p9zO-c4a4x`: row height, 16px padding, selected fill,
check-at-right placement and the `#00070C` menu all match. Data is the real local Supabase
`public.hashtags` (13 rows), not the frame's mock labels.
