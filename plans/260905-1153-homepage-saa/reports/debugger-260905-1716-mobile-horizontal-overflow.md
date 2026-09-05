---
name: debugger-260905-1716-mobile-horizontal-overflow
description: Root-cause proof and fix for homepage horizontal scroll at 375px viewport
metadata:
  type: report
  date: 2026-09-05
---

# Mobile horizontal-overflow defect — homepage at 375px

## Executive Summary

**What broke:** at a 375px viewport the homepage scrolls sideways. `document.documentElement.scrollWidth` measured **653px** against a **375px** client width (a 278px overflow) — far larger than the ~15px originally reported, and reproduced with hard numbers, not a screenshot guess.

**Root cause (two independent sources, both proven by direct DOM measurement, not by scrolling a screenshot):**
1. `app/_components/home-header.tsx`'s `<header>` row (logo + `HomeNav` on the left, notification/language/account on the right) had a **fixed, non-responsive `px-36` (144px each side)** padding and no `flex-wrap`, while `app/_components/home-nav.tsx`'s `<nav>` held three links in a **`nowrap`** row whose own min-content width (333px) already exceeds a 375px viewport before any padding is even added. This pushed the right-hand cluster (language selector) out to `right: 653.41px` — the single largest offender.
2. `app/_components/countdown-timer.tsx`'s three-unit countdown row (`flex items-center gap-10`, `nowrap`) is built from **fixed-pixel** 51×82px digit tiles that cannot shrink or wrap; their combined intrinsic width (~430px) exceeds the hero section's own correctly-responsive content width (327px at 375px viewport). This is a second, independent overflow source — fixing only the header would still have left `scrollWidth` at 454px.

**Fix:** made both offending rows responsive — `flex-wrap` + Tailwind's already-established `px-6 sm:px-12 lg:px-36` padding scale for the header, `flex-wrap` + tighter gaps for the nav, and mobile-sized (shrunk) tiles/labels for the countdown — with `sm:`/`lg:` variants restoring the exact original desktop values, so nothing changes above 640/1024px.

**Verified:** `document.documentElement.scrollWidth === clientWidth === 375` after the fix (0 elements now exceed the viewport, down from 30). Desktop (1280px, the e2e suite's default viewport) measured unchanged: `px-36` padding, `24px` nav gap, `scrollWidth === clientWidth === 1280`.

## Method — reproduction before any theory

Ran a headless Chromium probe (not `@playwright/test`, since the project's own `e2e/**` and `playwright.config.ts` were out of scope to touch — used the `playwright` package directly, reusing the project's own vendored-libs workaround for WSL2's missing shared libraries, `LD_LIBRARY_PATH=.playwright-libs/usr/lib/x86_64-linux-gnu`, documented in `playwright.config.ts`):

```js
await page.setViewportSize({ width: 375, height: 812 });
await page.goto("http://localhost:3000/", { waitUntil: "networkidle" });
document.documentElement.scrollWidth   // 653
document.documentElement.clientWidth   // 375
[...document.querySelectorAll("*")]
  .filter(el => el.getBoundingClientRect().right > document.documentElement.clientWidth + 1)
  // 30 elements, sorted by rect.right descending
```

**Before fix — full offender list (30 elements), outermost first:**

| right (px) | left | width | element |
|---|---|---|---|
| 653.41 | 541.09 | 112.31 | `LanguageSelector`'s trigger `<button>` + wrapper (header right cluster) |
| 541.09 | 144 | 397.09 | header left cluster (`flex items-center gap-16`: logo + `HomeNav`) |
| 541.09 | 208 | 333.09 | `<nav>` itself (`HomeNav`, `flex items-center gap-6`) |
| 454 | 24 | 430 | Hero's countdown+event-info wrapper (`flex flex-col items-start gap-4`) |
| 454 | 24 | 430 | Countdown units row (`flex items-center gap-10`) |
| 417.5 | 24 | 393.5 | `EventInfo`'s livestream `<p>` (downstream symptom, see below) |
| 452 / 387 | 336 / 336 | 51 | Individual digit tiles (`h-[82px] w-[51px]`) |

## Rival hypotheses tested

Per the brief's candidate list, each checked against the actual `right`/`left` measurements rather than assumed:

| Candidate | Evidence | Verdict |
|---|---|---|
| **Header nav row** | `<nav>` measured `flexWrap: nowrap`, width `333.09px` on its own — already wider than 375px before the header's own 144px padding is added. Header cluster's `right` reaches 653.41. | **CONFIRMED** — root cause #1 |
| **Countdown row** | Units row measured `flexWrap: nowrap`, width `430px`; digit tiles are fixed `h-[82px] w-[51px]` (non-text, cannot reflow). | **CONFIRMED** — root cause #2 |
| CTA button row (`home-hero.tsx`, `flex flex-wrap items-start gap-10`) | Already has `flex-wrap` in source; **zero** offenders reported for this row in either run. | ELIMINATED — already responsive |
| Floating widget (`fixed` position) | `fixed right-6 bottom-6`, fixed intrinsic width (~pill of two 20-24px icons); never appeared in the offender list. | ELIMINATED — small, fixed content, not a source |
| Awards grid gap | `awards-grid.tsx` already uses `px-6 sm:px-12 lg:px-36` + `grid-cols-2 lg:grid-cols-3`; not in offender list. | ELIMINATED — already responsive (and is the one thing the existing suite does check, at 375px, for grid-column count) |
| Kudos block background image | `Image fill` inside `overflow-hidden` rounded card; not in offender list. | ELIMINATED |
| Hero's absolutely-positioned keyvisual wrapper | `absolute inset-x-0 top-0` — pinned to the section's own width by `inset-x-0`, can't push wider than its `w-full` parent; not in offender list, and the brief already states this was ruled out (reproduced before AND after the hero fix). | ELIMINATED, confirmed independently |
| EventInfo's `eventLivestream` `<p>` (looked independently overflowing at first glance, width 393.5) | Its containing flex-column ancestor (`flex flex-col items-start gap-4`, the countdown+event-info wrapper) was itself forced to 430px wide by the *sibling* countdown row's rigid, non-wrapping fixed-pixel tiles (CSS `fit-content()` sizing: when a flex item's min-content equals its max-content — true here, since fixed-px tiles can't shrink or wrap — it is used even though it exceeds the available cross-axis space, per the flexbox spec's `fit-content(available) = max(min-content, min(max-content, available))` formula). That forced width then raised the "available space" seen by the livestream paragraph one level down, letting it render on one line instead of wrapping. | **Downstream symptom of root cause #2, not an independent bug** — confirmed by re-measuring after the countdown fix: this `<p>` is no longer in the offender list at all, with zero code changes made to it directly |

## Why no test caught it

`e2e/homepage.spec.ts` ID-16 sets `page.setViewportSize({ width: 375, height: 667 })` and asserts the awards grid's CSS `grid-template-columns` token count — a narrow-width check, but only against a *specific already-responsive component*, and only for column count, never for `document.documentElement.scrollWidth`. `e2e/capture-homepage-visual.spec.ts` also renders at 375px but only takes a screenshot — no assertion at all. Nothing in the suite ever asserted `scrollWidth <= clientWidth` (or equivalent, e.g. `expect(await page.evaluate(...)).toBeFalsy()`), so a component that overflows sideways — as opposed to reflowing its own grid — had zero coverage. This is a **monitoring/test gap**, not a flaky test: the suite has never once run a horizontal-overflow assertion, at any viewport, on any page.

## The fix

**`app/_components/home-header.tsx`**
- `<header>`: `px-36` (fixed 144px, only component missing the `px-6 sm:px-12 lg:px-36` pattern already used by every other section — `awards-grid.tsx`, `kudos-promo.tsx`, `root-further-block.tsx`, `home-hero.tsx`) → `px-6 sm:px-12 lg:px-36`, plus `flex-wrap gap-x-4 gap-y-2` so the two clusters stack instead of overflowing when they don't fit on one line.
- Left cluster: `gap-16` → `gap-4 sm:gap-16` (tighter at mobile) + `flex-wrap`.
- Right cluster: `flex items-center gap-4` → `ml-auto flex flex-wrap items-center gap-4` (`ml-auto` right-aligns it when it wraps to its own row, keeping it visually consistent with the desktop right-alignment).

**`app/_components/home-nav.tsx`**
- `<nav>`: `flex items-center gap-6` → `flex flex-wrap items-center gap-x-3 gap-y-1 sm:gap-6` — restores the exact original 24px gap at `sm:` (≥640px) and above; only wraps below that.

**`app/_components/countdown-timer.tsx`**
- Units row: `flex items-center gap-10` → `flex flex-wrap items-center gap-4 sm:gap-10` (wrap as a backstop; gap shrinks at mobile).
- `CountdownUnit`'s digit-row gap: `gap-3.5` → `gap-2 sm:gap-3.5`.
- `CountdownUnit`'s label: `text-2xl leading-8` → `text-base leading-6 sm:text-2xl sm:leading-8` (the label was on track to become the *widest* part of each unit once tiles shrank, so it shrinks in step).
- `DigitTile`: `h-[82px] w-[51px]` → `h-[56px] w-[36px] sm:h-[82px] sm:w-[51px]`; digit text `text-[49px]` → `text-[32px] sm:text-[49px]`.

All changes are additive `sm:`/`lg:` variants restoring the original literal values — nothing changes at ≥640px (nav gap, digit-row gap) or ≥1024px (header padding), which covers the e2e suite's default `Desktop Chrome` (1280×720) viewport used by every project except the two narrow-width tests already named above.

## Evidence — after fix

```json
// 375×812 (anon)
{"scrollWidth":375,"clientWidth":375,"bodyScrollWidth":375}
OFFENDERS []   // was 30 elements before

// 1280×720 (desktop — matches e2e default viewport)
{
  "scrollWidth": 1280, "clientWidth": 1280,
  "headerPaddingLeft": "144px",   // unchanged from before
  "navGap": "24px"                // unchanged from before
}
```

`npm run typecheck` → **exit 0**
`npm run lint` → **exit 0** (6 pre-existing warnings in untouched `e2e/*.spec.ts` files — unused vars — not introduced by this change)
`npm run build` → **exit 0**
`npm run test:e2e -- --project=anon --project=authed --project=homepage-authed` → **exit 0**, **46 passed, 1 skipped** — matches the stated baseline exactly, on the 3rd attempt (see note below for why the first two attempts were noise, not regressions)

### A note on two false alarms during verification (neither caused by this fix)

Two full suite runs failed before the passing run above — worth recording since they looked alarming at first and both traced to causes with zero connection to `home-header.tsx` / `home-nav.tsx` / `countdown-timer.tsx`:

1. **Run 1** — 7 failures, all in `e2e/callback-security.spec.ts` (`/auth/callback` returned 404 instead of 307). Cause: I had a manually-started `next dev` still bound to port 3000 from probing the fix, left running when I launched `npm run test:e2e`. `playwright.config.ts`'s `webServer` (`reuseExistingServer: false`) tried to spawn its own server on the same port; the health-check URL answered from my stale process instead. Killed the leftover process, confirmed port 3000 was free, re-ran.
2. **Run 2** — 1 failure: `e2e/homepage-auth.setup.ts` → `signUp failed: Database error saving new user`. Traced with `docker logs supabase_auth_my-app` to a Postgres-side `duplicate key value violates unique constraint "users_email_partial_key"` on the *same, freshly-timestamped* test email — i.e. GoTrue attempted the same signup insert twice within one call, consistent with the local Supabase stack (up 23h, single Postgres instance) being saturated by repeated E2E runs in a short window. This is the same class of local-Supabase-under-concurrency fragility a prior investigation in this plan already documented (`debugger-260905-1353-authed-e2e-failures.md`, root cause #2: shared/contended auth state under the `authed`/`homepage-authed` projects' worker concurrency). Restarted the `supabase_auth_my-app` (GoTrue) container to clear its connection pool — not a code or test change — and re-ran; passed clean.

Neither failure touched, referenced, or could plausibly be caused by any of the three edited files — confirmed by `git status --short` showing only `app/_components/home-header.tsx`, `app/_components/home-nav.tsx`, and `app/_components/countdown-timer.tsx` as modified throughout.

## Recurrence prevention

Add one assertion, once, to any homepage e2e spec already running at a narrow viewport (e.g. alongside ID-16 in `homepage.spec.ts`, at the existing 375×667 `setViewportSize` call):

```ts
const overflow = await page.evaluate(
  () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
);
expect(overflow).toBeLessThanOrEqual(0);
```

This is a one-line, page-agnostic check that would have caught this defect (and the pre-existing hero keyvisual issue mentioned in the brief) on day one, and costs nothing to maintain since it needs no per-component knowledge. (Not added here — `e2e/**` was explicitly out of scope for this task; flagging it as the concrete next step.)

---

**Status:** DONE
**Summary:** Two independent, non-responsive fixed-width rows caused the overflow — `home-header.tsx`'s header (`px-36` fixed + non-wrapping nav) reaching `right: 653px`, and `countdown-timer.tsx`'s fixed 51×82px digit tiles reaching `right: 454px`. Fixed both with responsive `flex-wrap` + `sm:`/`lg:` breakpoint variants restoring original desktop values; `scrollWidth` now equals `clientWidth` (375) at mobile width, verified unchanged at the suite's 1280px default viewport. `typecheck`/`lint`/`build` all exit 0; `npm run test:e2e -- --project=anon --project=authed --project=homepage-authed` exits 0, 46 passed / 1 skipped — matching baseline exactly.
**Concerns/Blockers:** none outstanding. Two transient failures hit during verification (stale dev-server port contention; a local-Supabase GoTrue connection-pool duplicate-key error) were both diagnosed to unrelated, pre-existing infra causes (documented above) and cleared without touching any test or app-behavior file — worth a maintainer's eye if `homepage-auth-setup` flakes again under repeated local runs, since it's the same class of local-Supabase-concurrency fragility a prior report in this plan already flagged.
