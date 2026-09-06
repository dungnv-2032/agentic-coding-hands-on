# Tester — Award System screen, final verdict

- **Screen:** Hệ thống giải — `https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/zFYDgyj_pD`
- **Route:** `/awards-information` · **testPolicy:** `e2e-red-first` · **Date:** 2026-09-06
- **Supersedes:** the visual section of `tester-260906-0824-award-system-green.md`. That report's
  gate results stand; its three material mismatches and its ragged-right finding do not — see below.

## VERDICT: the screen is visually complete.

All four fixes hold under measurement. No material mismatch remains. Everything still open is either
faithful to the frame, pre-existing outside this screen, or accepted by the coordinator on the record.

---

## Gates

| # | Command | Exit | Result |
|---|---|---|---|
| 1 | `npx playwright test e2e/award-system.spec.ts --project=anon` | **0** | **13 passed, 0 failed** (1.2m) |
| 2 | `npx playwright test e2e/homepage.spec.ts --project=anon` | **0** | **22 passed, 0 failed** (1.0m) |
| 3 | `npx playwright test e2e/award-system.spec.ts --project=anon` *(with the new ID-7 assertion)* | **0** | **13 passed, 0 failed** (1.1m) |
| 4 | `npx playwright test --project=anon` *(full project)* | **0** | **53 passed, 0 failed** (1.2m) |

Nothing was weakened, skipped or relaxed to reach any of these. Run 4 was not asked for — I added it
because my `playwright.config.ts` `testMatch` edit widened that project, and its blast radius deserved
a check rather than an assumption. Logs in `evidence/`.

**One aborted run, disclosed.** My first attempt at gate 3 exited `1` with
`Process from config.webServer was not able to start` — my own capture server was squatting port 3100
and Next refused to start a second dev server for the same directory. That is an environment failure,
not a test failure, and it is not counted as a result. I killed the server and reran; that rerun is
gate 3 above. The orphan on 3111 never interfered.

### Gate 2 is the real check on `kudos-promo.tsx` — and it needed more than a green suite

The homepage suite asserts *behaviour*, not the Kudos block's width, so "22 passed" alone would not
have proved the shared component is untouched. I measured it directly on `/`:

```
sectionClass = "mx-auto w-full max-w-[1224px] px-6 py-8 sm:px-12 lg:px-36"
section 108, width 1224 · card 252 → 1188, width 936
```

Identical to the pre-change numbers recorded in `visual-measurements-award-system.json`. The default
prop is a true no-op for the homepage. **Change cleared on measurement, not on inference.**

---

## Fixes 1–4, per item

**Fix 1 — badge geometry: PASS.** Hard measured, all six:

| award | before | now | natural |
|---|---|---|---|
| top-talent | 336×550 | **336×336** | 336×336 |
| top-project | 336×598 | **336×336** | 336×336 |
| top-project-leader | 336×574 | **336×336** | 336×336 |
| best-manager | 336×562 | **336×336** | 336×336 |
| signature-2025-creator | 336×966 | **336×336** | 336×336 |
| mvp | 336×658 | **336×336** | 336×336 |

`align-self: flex-start`, `aspect-ratio: 1 / 1`. Independent pixel scan of the capture puts the image
block at **438→783** against the frame's **439→782** — 1 px, border antialiasing. Every image was
forced eager and every section scrolled through before measuring, so none of these are undecoded
zeros.

**Fix 2 — Kudos width: PASS.** Card at **144 → 1296, width 1152**; pixel scan of the capture reads
**144 → 1295** across the whole band against the frame's **144 → 1295**. Body copy now ends at x 665,
the logo starts at x 868 — `textUnderLogo: false`. The overlap is gone, not merely narrowed.

**Fix 3 — icon colour: PASS.** All four card icons `rgb(255,255,255)`, matching the frame's sampled
`#FFFFFF`. Menu unregressed and confirmed against the frame: active gold `#FFEA9E` label + icon +
underline, inactive white `#FFFFFF`. Side-by-side in `visuals/cmp-final-nav-2x.png`.

**Fix 4 — left edge: PASS.** nav **144 → 322**, card column **443 → 1296**, badge **443 → 779**, text
column **821** against the frame's **819**. Your predicted edges, landed.

---

## Two corrections to my own record

**Fix 6 — you were right, I was wrong, and I checked rather than took your word for it.** I measured
the frame's D.2 description block myself: left holds at **443–445** and the right edge holds flush
across **ten consecutive lines**, ragged only on the final line at 878. That is justified text.
`text-justify` stays. My earlier ragged-right call was a qualitative eyeball of the Signature crop
against a differently-sized actual column — it was wrong, and it is retracted, not carried forward.
(My right-edge figures read 963/999 where yours read 921, likely a different brightness threshold or
sub-block; the conclusion is identical, which is what matters.)

**Fix 5 — recorded as an accepted known transient, with your corrected cause.** Measured:
`[[0,"award-nav-top-talent"],[290,"award-nav-mvp"]]`. The cause is **hydration latency** — a URL
fragment is never sent to the server, so the SSR HTML necessarily ships `items[0]` active and the
correction lands at hydration; 290 ms is this route's time-to-interactive. My smooth-scroll diagnosis
was wrong; the deep-link path was already `behavior: "auto"`. That also explains why `--repeat-each=10`
was stable rather than jittery — it is a fixed cost, not a race. **ACCEPTED, no code change, closed.**

---

## Task 4 — ID-7 strengthened

Added to `e2e/award-system.spec.ts` ID-7, at a pinned 1440×900 viewport:

```ts
const box = await image.boundingBox();
expect(
  { slug: award.slug, w: Math.round(box!.width), h: Math.round(box!.height) },
  "award badge must render undistorted at its intrinsic 336x336",
).toEqual({ slug: award.slug, w: 336, h: 336 });
```

The slug rides on both sides of the comparison so a failure names the award and its real measured
size instead of just "expected 336". Viewport is pinned because 336×336 is a statement about the
design width, not about Playwright's default 1280. `tsc --noEmit` clean; gate 3 exits **0** with it in
place — it passes on real geometry, not by relaxation. Against the pre-fix numbers in the table above
it would have failed on all six awards, Signature by 630 px. Fix 1 can no longer regress silently.

---

## A false alarm I raised and killed myself

`visuals/final-full-1440.png` shows **MVP** active in the menu at the top of the page, which looks
like a scroll-spy defect. It is not. `fullPage` capture scrolls the document to stitch tiles, which
drives the IntersectionObserver. Probed directly instead:

```
fresh load @top      -> top-talent
scrolled back to top -> top-talent
scrollY 4500 -> mvp · 3200 -> best-manager · 2000 -> top-project-leader · 1000/400/0 -> top-talent
```

The spy is correct in both directions. Recording it so the screenshot does not get re-litigated by
whoever opens it next. (Aside: an instantaneous jump to the absolute page bottom lands past the last
section, so nothing intersects and the observer holds its previous value. Unreachable by real
scrolling — noted, not filed.)

---

## Still open — none of it blocking

- **`Hoặc` at 1.64:1 contrast.** Faithful to the frame, which is itself inaccessible. A designer
  question, not a dev fix. Unchanged from my last report.
- **Kudos CTA glyph** — frame draws ↗, actual renders a rotated chevron. Pre-existing in the shared
  `KudosPromo`, already shipped on the homepage, out of this screen's scope.
- **Homepage Kudos body copy overlaps its own logo by ~13 px.** Pre-existing shipped behaviour on `/`,
  untouched by fix 2 — the award screen's wider card is what cleared it there. Worth a ticket for the
  homepage; not this phase's work, and not a regression.
- **Menu label wrap:** frame breaks `Signature 2025 / Creator`, actual breaks `Signature / 2025
  Creator`. Cosmetic, inside the 178 px column.
- **Document height 6342 vs 6410** (1.1%) — cumulative line-height rounding, no single visible offset.
- **Test case ID-14** (Chi tiết → friendly 404) still unexercisable: `/kudos` is a declared
  `ComingSoon` placeholder, so the link resolves and there is no 404 path to fail against. Carried
  from RED, unchanged.

## Honest limits on this verdict

There is no deterministic pixel-diff metric here — the reference is a Figma export, not a rendered
baseline, so I cannot and do not call any of this "exact". What is stated as a number above was
measured (DOM `getBoundingClientRect` / `getComputedStyle`, cross-checked against PIL pixel scans of
the frame). Layout fidelity beyond those numbers is a qualitative judgment from the side-by-side
composites. Playwright MCP was unavailable throughout — it wants the `chrome` channel at
`/opt/google/chrome/chrome`, which is absent and out of scope to install — so all capture ran through
the project's own Chromium.

## Evidence

`evidence/`: `award-system-final-run-prefix-assertion.log`, `award-system-final-run-with-assertion.log`,
`homepage-regression-final.log`, `anon-project-full-run.log`,
`raw-temper-runs-award-system-final.json`, `visual-measurements-award-system-final.json`
(every number above), plus the RED/first-GREEN artifacts.

`visuals/`: `final-full-1440.png`, `final-kudos.png`, `final-nav.png`, `final-section-<slug>.png` ×6,
`cmp-final-design-vs-actual.png`, `cmp-final-top-talent.png`, `cmp-final-kudos.png`,
`cmp-final-nav-2x.png`, and the pre-fix set for comparison.

Files I own and changed this phase: `e2e/award-system.spec.ts` (ID-7 strengthened only).
`playwright.config.ts` unchanged since RED. Nothing under `app/`, `lib/`, `public/`, `proxy.ts` touched.
