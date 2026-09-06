# Tester — Award System screen, delivery verification

- **Screen:** Hệ thống giải — `https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/zFYDgyj_pD`
- **Route:** `/awards-information` · **testPolicy:** `e2e-red-first` · **Date:** 2026-09-06
- **Round:** post-reviewer-fixes (W-1, W-2, W-3, S-5, S-7, S-8, S-9, S-11)

# VERDICT: SHIP.

All three gates green. W-1, W-2 and W-3 verified by direct measurement, including the two paths the
E2E suite cannot reach. Desktop geometry is unmoved. Two findings, neither blocking: one minor
cosmetic in the spy's hero state, one pre-existing defect in shared chrome that this screen did not
introduce and does not own.

---

## Gates — real exit codes

| Command | Exit | Result |
|---|---|---|
| `npx playwright test e2e/award-system.spec.ts --project=anon` | **0** | **13 passed, 0 failed** (1.2m) — ID-7's 336×336 assertion live |
| `npx playwright test e2e/homepage.spec.ts --project=anon` | **0** | **22 passed, 0 failed** (1.0m) |
| `npx playwright test --project=anon` | **0** | **53 passed, 0 failed** (1.2m) |

No assertion touched this round. `e2e/award-system.spec.ts` is byte-identical to the file that passed
the last gate; `playwright.config.ts` unchanged since RED. The new `awardSystem.navAriaLabel` key on
the shared `Dictionary` leaves the homepage untouched.

---

## Task 4 — desktop geometry: nothing moved

| | measured | design | |
|---|---|---|---|
| nav | 144 → 322 | — | ✓ |
| card column | 443 → 1296 | 439 → 1296 | ✓ |
| badge | 443 → 779 | 439 → 782 | ✓ 1px |
| description text left | **819** | **819** | ✓ exact |
| Kudos (DOM / pixel scan) | 144 → 1296 / **144 → 1295** | **144 → 1295** | ✓ |
| six badges | all **336×336** | 336×336 | ✓ |
| card icons | `rgb(255,255,255)` ×4 | `#FFFFFF` | ✓ |
| menu | active gold `#FFEA9E`, five inactive white | same | ✓ |

**S-5 hero cap — desktop-neutral, verified at three widths rather than assumed.** Hero block measures
1152 wide at every one, staying flush with the card column's right edge: 1440 → `144–1296` (card right
1296); 1728 → `288–1440` (1440); 1920 → `384–1536` (1536). The 144px-a-side overhang above ~1728 is
gone and 1440 is exactly the geometry pinned last round.

**W-1 desktop pin — verified, not assumed.** At 1440 the `<html>` var publishes `117px` (measured
header 77 + 40 breathing room) while the effective value inside the subtree resolves to `112px`. The
wrapper's `lg:[--award-header-offset:112px]` shadows the measurement, so nothing at runtime can move
the desktop geometry. That is the design working exactly as described.

---

## Task 5 — W-1 mobile, the path only I can exercise

**Measured header height at 375px: `245px`.** The reviewer's arithmetic said ~235 — off by 10, which
is precisely why this needed a browser.

The offset is live and tracks in both directions, not a one-shot:

| viewport | header | effective offset |
|---|---|---|
| 1440 | 77 | **112px** (cascade pin) |
| 900 | 77 | 117px |
| 600 | 125 | 165px |
| **375** | **245** | **285px** |
| 320 | 301 | 341px |
| 1440 (back) | 77 | **112px** restored |

Clearance at 375, all three cases pass — deep link and taps alike:

| case | title top | header bottom | clears |
|---|---|---|---|
| `/awards-information#mvp` | 652 | 245 | ✓ |
| tap Best Manager | 652 | 245 | ✓ |
| tap Top Project Leader | 652 | 245 | ✓ |

`scroll-margin-top` resolves to 285px = measured 245 + 40 breathing room, so the section top lands 40px
clear of the header; the title sits further down because below `lg` the card stacks image-first, as
clarifications specify. **The card title does not sit behind the header.** W-1 is fixed.

---

## Task 6 — W-2, and a harness limitation I had to work around

**First, the audit you asked for.** Playwright's `click()` and `hover()` fire **only `scroll`** — no
`wheel`, no `touchstart`, no `keydown`. Confirmed empirically with listeners installed on `window`.
So the lock-release listeners really are inert during the suite, and my E2E spec genuinely never
exercised this. Your suspicion was right.

**A false negative I caught in myself.** My first attempt drove the interrupt with `mouse.wheel()` and
appeared to fail — the nav stayed on MVP. It hadn't failed: `scrollY` was still 4683, the MVP landing
position. Synthetic CDP wheel events **do not abort Chrome's programmatic smooth scroll**, so the
interruption never happened and the nav was correctly reporting the card that was actually on screen.
I reran with trusted keyboard input instead. Reporting the dead end because a future run will hit the
same wall.

With a real interruption staged, every release path passes:

| probe | result |
|---|---|
| **Your criterion** — click MVP, interrupt at 73ms, rest with Top Talent in band | active **`top-talent`**, count 1 ✓ |
| wheel event inside the 700ms window, sampled at 250ms | active **`top-project-leader`** = in-band card ✓ |
| **control**, no interrupt | `mvp` at 250ms (lock held) → `top-project-leader` at 1150ms (lock expired, geometry took over) ✓ |
| touchstart | active `top-project` = in-band card ✓ |
| resting accuracy, 8 positions | nav matched the in-band card every time, exactly-one-active held ✓ |
| fast flick, 26 wheel steps | distinct active counts `[1]`, trail walked all six in order ✓ |

The control matters: it proves the interrupt result is real rather than coincidence, **and** that the
old stuck-forever bug is gone — the lock now expires and hands back to geometry on its own.

---

## Task 7 — W-3 accessible tree

Exactly one `<h1>`. Heading order clean: `h1` → six `h2` (each with a `{slug}-title` id) → Kudos `h2`.
All six `<section>` elements carry `aria-labelledby` at their own heading and every reference
resolves, so each announces as "Top Talent", "Top Project", … "MVP (Most Valuable Person)".
The category menu is a `<nav>` labelled **"Danh mục giải thưởng"** — S-7 landed. Full tree saved to
`evidence/aria-snapshot-award-system.yaml`.

---

## Findings

**OBS-1 — minor, not blocking. At the hero, the menu retains an arbitrary previous item.**
Scroll down to a card and back to the very top and the menu stays lit on whatever was last in the
band — `top-project` on one run, `signature-2025-creator` on another. The frame shows **Top Talent**
lit at that position. Root cause is the deliberate, commented rule in `resolveActive()`: when no
section intersects the band, keep the current item rather than clear it, so exactly-one-active never
drops to zero. Sound reasoning — clearing would break the invariant my ID-9/11 asserts.
*Bounded fix, if you want it:* when nothing is in the band, fall back to the first slug when `scrollY`
is above the first section's top, else keep current. One condition, invariant preserved.
Not a ship blocker: it needs a scroll to the hero to see, and the nav self-corrects the moment a card
re-enters the band.

**OBS-2 — pre-existing, not this screen's, not blocking.** The sticky header is
`rgba(16, 20, 23, 0.8)` with `backdrop-filter: none`, so page content scrolls visibly through it —
at 375 the gold "8.000.000 VNĐ" lands on top of the nav labels. I checked whether this screen caused
it: the computed background is **identical on `/` and `/awards-information` at both 375 and 1440**,
and the header band's non-background pixel share at 375 is *higher* on the homepage (22%) than here
(10%). It is `home-header.tsx`, shared chrome, ORCH-03 read-only, and worse on a page that already
shipped. This screen only makes it noticeable, because large gold prize text now scrolls under a
245px wrapped header. Follow-up ticket against the shared header — an opaque fill or a
`backdrop-blur` — not this phase's work. Evidence: `visuals/header-{award,home}-{375,1440}.png`.

---

## Accepted, not re-opened

The ~290ms deep-link hydration transient (ORCH-04); the W-2 residual where a ~5,000px hop walks
intermediate cards before settling; `text-justify`; `Hoặc` at 1.64:1; ID-1; S-10.

## Honest limits

No deterministic pixel-diff metric exists — the reference is a Figma export, not a rendered baseline —
so nothing here is called "exact" except the specific numbers I measured. Playwright MCP remains
unavailable (`chrome` channel absent at `/opt/google/chrome/chrome`); all capture ran through the
project's own Chromium. Synthetic wheel cannot interrupt a smooth scroll, so the wheel path was
verified at the event level rather than end-to-end; the keyboard path was verified end-to-end with
trusted input.

## Offered, deliberately not done unbidden

W-3's structure (one `h1`, six `h2`, `aria-labelledby`, the nav label) is exactly the kind of thing
that regresses silently, and it is cheap to lock in `e2e/award-system.spec.ts`. I did not add it: this
is the final gate and I will not mutate the artifact under test without being asked. Say the word and
it costs one 1.2-minute rerun.

## Evidence

`evidence/`: `delivery-award-system-run.log`, `delivery-homepage-run.log`, `delivery-anon-full-run.log`,
`delivery-verification-probe.log`, `delivery-w2-probe-round1.log` (the dead end),
`delivery-w2-probe-round2.log`, `raw-temper-runs-award-system-delivery.json`,
`delivery-verification-award-system.json` (every number above), `aria-snapshot-award-system.yaml`.

`visuals/`: `delivery-full-1440.png`, `cmp-delivery-design-vs-actual.png`,
`mobile-375-deeplink-mvp.png`, `mobile-375-tap-best-manager.png`,
`header-{award,home}-{375,1440}.png`, plus the prior rounds' captures.

Files I own: `e2e/award-system.spec.ts` and `playwright.config.ts` — **neither changed this round**.
Nothing under `app/`, `lib/`, `public/`, `proxy.ts` touched.

## Unresolved

- OBS-1's fallback: your call whether the hero should relight Top Talent or keep the retention rule.
- OBS-2 needs a ticket against `home-header.tsx`; it affects the already-shipped homepage more than
  this screen.
- Test case ID-14 remains unexercisable while `/kudos` is a `ComingSoon` placeholder.

---

# Seal round — OBS-1 fix verified, W-3 locked (2026-09-06 09:54)

## FINAL VERDICT: SHIP. SEALED.

## Gates

| Command | Exit | Result |
|---|---|---|
| `npx tsc --noEmit` | **0** | clean with the new assertions |
| `npx playwright test e2e/award-system.spec.ts --project=anon` | **1** | **first run — my assertion was wrong, see below** |
| `npx playwright test e2e/award-system.spec.ts --project=anon` | **0** | **14 passed, 0 failed** (13 + the W-3 lock) |
| `npx playwright test --project=anon` | **0** | **54 passed, 0 failed** |
| `npx playwright test e2e/homepage.spec.ts --project=anon` | **0** | **22 passed, 0 failed** |

## 1. OBS-1 — verified at both ends, probed not inferred

**Hero fallback is now deterministic.** Returning to the top from every one of the five lower cards,
by real wheel input and again by programmatic scroll, lands on **`top-talent`**, count 1, every time.
Before the fix this was arbitrary — I recorded `top-project` on one run and `signature-2025-creator`
on another.

**The footer branch still keeps the current item.** At page bottom (scrollY 5442, max scroll) with no
section in the band, active stays `mvp`, count 1 — not cleared, not reset to Top Talent. The asymmetry
you wrote is exactly the asymmetry that runs.

**The invariant holds end to end.** Boundary sweep 0→1400 in 100px steps: distinct active counts `[1]`,
one clean transition to `top-project` at y=1000, no flicker. Full sweep 0→6300 and back in 300px
steps: distinct counts `[1]`, never `NONE`, ends on `top-talent`.

**ID-9/11 is not regressed.** By hand, all six menu items still click to their own section with count 1;
in the suite, ID-9/11 passed in every run including six repeats. Nothing to revert.

## 2. W-3 — locked, and the lock caught me first

New test: `W-3 — one h1, h1 → six h2 → Kudos h2, each award section accessibly named, category nav
labelled`. It asserts one `<h1>`; the complete heading list compared as an **ordered array** (h1 + six
h2 in design order + Kudos h2); each section's `aria-labelledby` → `{slug}-title`, that heading's text,
and the section resolving as `role=region` with that accessible name; and the menu resolving as
`role=navigation` named `Danh mục giải thưởng` with six links.

**Its first run failed — and the fault was mine, not the code.** I asserted `award-nav` as a
*descendant* of the labelled `<nav>`. It is not: `award-category-nav.tsx:59-62` puts `data-testid` and
`aria-label` on the same element. The product was right; my assertion was wrong. Corrected to assert
identity — `expect(categoryNav).toHaveAttribute("data-testid", "award-nav")` — which is a stronger
claim than containment, plus a six-link count. Recording the red run in the evidence rather than
quietly amending it, because a first-try assertion bug is exactly the thing that gets buried.

## 3. A flake I found, chased down, and will not wave through

The six-repeat flake check came back **1 failed, 24 passed**. I did not accept that as noise.

The failure is `page.goto` timing out at **30.1s**, on the **first** test in the filtered batch —
a cold `next dev` route compile of `/awards-information` on WSL2. Every later repeat of that same
test ran in ~5.1s, and an identical rerun passed **25/25 in 50.4s**.

It is not the screen, and it is not the suite's assertions:

- **Zero** `Test timeout of` occurrences across **all 14 unfiltered gate runs** in this entire task.
- The gate command runs ID-0/2 first, which navigates the route in 1.3–1.4s and warms it. `-g`
  filtering excludes ID-0/2 and hands the cold compile to whichever test happens to run first.

**Recommendation, not applied:** raise `timeout` in `playwright.config.ts` if you want CI headroom
against a cold compile. A timeout is not an assertion, so raising it weakens nothing — but it is a
change at the seal and no unfiltered gate run has ever hit this, so I left it alone. Your call.

## Not in scope, as agreed

OBS-2 untouched — `home-header.tsx`, ORCH-03 read-only, worse on the already-shipped homepage
(22% vs 10% non-background pixels at 375). Recorded as your follow-up ticket. The 290ms deep-link
transient (ORCH-04), the W-2 mid-flight transit residual, `text-justify`, `Hoặc` at 1.64:1, ID-1 and
S-10 all stay accepted.

## Final state

`e2e/award-system.spec.ts` — 14 tests, ID-7's 336×336 geometry lock and the W-3 structure lock both
live. `playwright.config.ts` unchanged since RED. Nothing under `app/`, `lib/`, `public/`, `proxy.ts`
touched at any point by me.

Evidence: `seal-award-system-run-failed-assertion.log` (kept on purpose), `seal-award-system-run.log`,
`seal-anon-full-run.log`, `seal-homepage-run.log`, `seal-flake-check-round{1,2}.log`,
`seal-obs1-probe.log`, `raw-temper-runs-award-system-seal.json`, `seal-obs1-w3-verification.json`.

## Unresolved

- Whether to raise the Playwright per-test `timeout` for cold-compile headroom in CI (my
  recommendation above; not applied).
- OBS-2 ticket against `home-header.tsx`.
- ID-14 stays unexercisable while `/kudos` is a `ComingSoon` placeholder.
