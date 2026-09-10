# Tester — phase 02, e2e-red-first gate for Thể lệ (SCR007)

Date: 2026-09-09 · Branch `main` · Policy `e2e-red-first`

## Verdict

Valid assertion RED produced. The gate is OPEN for phases 03–07.

```
redTestFiles: ["e2e/the-le.spec.ts", "e2e/fixtures/the-le-constants.ts"]
redCommand:   npx playwright test e2e/the-le.spec.ts --project=anon
redExitCode:  1
redFailure:   expect(locator).toHaveText(expected) failed
              Locator:  getByRole('heading', { level: 1 })
              Expected: "Thể lệ"
              Received: "Coming soon"
              at e2e/the-le.spec.ts:61
redEvidence:  plans/260909-0838-the-le-rules-panel/evidence/red-run.txt
```

Result line: `9 failed / 2 skipped / 1 passed (2.8m)`. The 1 passed is the `setup`
project dependency, not a test of this screen.

## What was built

| File | Action | Notes |
|---|---|---|
| `e2e/fixtures/the-le-constants.ts` | create | 93 lines, copy only, no logic |
| `e2e/the-le.spec.ts` | create | 9 live tests + 2 `test.skip` |
| `playwright.config.ts` | modify | one word — `the-le` into the `anon` `testMatch` regex |

Nothing under `app/standards/`, `lib/rules/`, `lib/i18n/` or `supabase/` was touched.

## Test map (all 9 source cases accounted for)

| Source case | Here | Fate |
|---|---|---|
| `TC_THELE_GUI_001` | `GUI_001` / `GUI_002` / `GUI_005` / `GUI_006` | live — split by requirement (FR-201/202/203/204) |
| `TC_THELE_GUI_002` | `FUN_003` + `FUN_004` | live for structure/behaviour; button *styling* is visual-contract |
| `TC_THELE_GUI_003` | `GUI_003` | `test.skip`, DEC-002 reason in the title |
| `TC_THELE_GUI_004` | — | hover restyle; `clarifications.md` assigns hover to the visual pass, not strict E2E |
| `TC_THELE_FUN_001` | `FUN_001` | live |
| `TC_THELE_FUN_002` | `FUN_002` | live |
| `TC_THELE_FUN_003` | `FUN_003` + `FUN_003b` | live — history-return and deep-link fallback |
| `TC_THELE_FUN_004` | `FUN_004` | live — DEC-001, href assertion |
| `TC_THELE_FUN_005` | `FUN_005` | `test.skip`, DEC-002 reason in the title |

## The two problems the phase plan flagged, and how they were settled

**FUN_002 — where does "content shorter than the panel" come from?** Not from
deleting seed rows (that tests an empty panel, not this requirement). The test
walks the viewport ladder `1440×2400 → 3200 → 4000`, stopping at the first height
where `scrollHeight <= clientHeight`, and then asserts UNCONDITIONALLY on the last
measurement — so if no height on the ladder ever fits, the test fails loudly with
the real numbers instead of quietly passing. Every measurement is attached to the
run as `fun_002-viewport-ladder`, which is better than a guessed number in a
comment: at RED the panel does not exist, so no honest figure could be written
today. Phase 08 will have the real one in the attachment.

**FUN_003 — where does a real history entry come from?** The homepage floating
widget (`app/_components/floating-widget.tsx`) carries a genuine
`<Link href="/standards">` labelled `home.widget.standards` = `Thể lệ SAA`
(`vi-home.ts:79`), and it is `fixed` bottom-right, so it needs no scrolling.
Selector used: `page.getByRole("link", { name: WIDGET_STANDARDS_LABEL })`.
No `page.goBack()` (that tests the browser, not the button) and no faked
`history.pushState`. **This path is proven working already**: in the RED run
FUN_003 clicked the link, passed its `toHaveURL(/\/standards$/)` check, and only
then failed on the missing `rules-close-button`. The navigation half of the test
will not surprise anyone at GREEN.

## Why this is a RED and not an infrastructure failure

All 9 failures are `expect()` diffs against the running app — `/standards` still
renders `ComingSoon`, so the `<h1>` reads "Coming soon" and no `rules-*` testid
exists. Grep over the full log finds none of the four disqualifying signatures
(browser shared-libraries, webServer start/timeout, missing env, ECONNREFUSED /
signUp failed). Positive health proof on the same run: the `setup` project signed
up a real user against local GoTrue, the dev server booted and warmed bundles, and
FUN_003's homepage navigation succeeded.

## Supporting gates

- `npx tsc --noEmit -p tsconfig.json` → 0
- `npm run typecheck` → 0
- `npm run lint` → 0 (29 pre-existing warnings elsewhere; none in the new files)
- Registration proof: `--project=anon --list` went `81 tests in 9 files` →
  `92 tests in 10 files`. Exactly +1 file, +11 tests.
- **Typecheck trustworthiness re-verified after the run.** The Playwright run kills
  the dev server at the end, which is the exact condition that previously corrupted
  `.next/dev/types/routes.d.ts` and masked every error repo-wide. A canary type
  error in the constants fixture produced exit 2; removing it produced exit 0.
  Typecheck is genuinely catching errors on the tree phases 03–07 inherit.

## Read-only handoff for the implementation agents

The seven `data-testid` values in `clarifications.md § "Test contract"` are now
load-bearing in an executable test. The UI must render, on `/standards`:

- `rules-panel` ×1, carrying `role="dialog"` and `aria-modal="true"`
- `rules-panel-content` ×1, the only thing that scrolls (the PAGE must not —
  FUN_001 asserts `document.documentElement` is not scrollable)
- `rules-section` ×3, `rules-hero-tier` ×4, `rules-collectible-icon` ×6 —
  in `position` order; the i-th rendered element is compared to the i-th designed
  string, so a permutation fails
- each hero tier and each icon contains exactly one `<img>`
- `rules-close-button` ×1 containing `Đóng`; `rules-write-kudos-link` ×1 that is an
  anchor with `href="/kudos/new"` and contains `Viết KUDOS`
- the page `<h1>` reads exactly `Thể lệ`

Copy is asserted from `e2e/fixtures/the-le-constants.ts`. Two values in it look
like typos and are deliberate — the EN DASH in `Có 10–20 người gửi Kudos cho bạn`
and the spelling `ROOT FUTHER`. The seed (phase 03/04) must match them
byte-for-byte or GREEN will not come.

Phase 08 reruns the identical `redCommand`. Do not change the command, relax an
assertion, or delete a test. Only `tester` may edit these files.

## Unresolved

- `TC_THELE_GUI_004` (hover restyle) has no executable coverage in this suite by
  design — `clarifications.md` routes hover to the visual-contract pass. Whoever
  owns the phase-08 visual validation must actually capture the two hover states,
  or that source test case ends up covered by nobody.
- `FUN_002`'s real viewport ladder result is unknown until the panel exists. If
  the seeded content exceeds 4000px at 553px wide, the ladder's top rung will not
  be enough and the constant will need raising at phase 08 — a viewport change,
  never an assertion change.
- FUN_001 asserts the page itself is not scrollable. The `ComingSoon` shell it
  replaces is `min-h-svh`; if the real screen's shell ends up taller than the
  viewport for an unrelated reason (header + footer + drawer), that assertion is
  the one that will complain first. It is asserting FR-403 correctly — treat a
  failure as a layout bug, not a test to loosen.
