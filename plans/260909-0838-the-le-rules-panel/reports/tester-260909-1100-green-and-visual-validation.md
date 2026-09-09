# tester — phase 08: GREEN + full-suite regression + visual validation (F007 Thể lệ, SCR007)

**Date**: 2026-09-09 · **Branch**: `main` · **Policy**: `e2e-red-first` · **Screen**: `/standards`
**Verdict**: **DONE_WITH_CONCERNS** — GREEN is real and reproduced; two visual deltas need a
bounded UI fix or explicit acceptance; the full-suite regression check is **inconclusive on this
machine** for reasons proven to be independent of this feature.

---

## 1. GREEN — confirmed, exit 0, twice

```
npx playwright test e2e/the-le.spec.ts --project=anon
  10 passed, 2 skipped (1.0m)   exit 0     # 11:20
  10 passed, 2 skipped (1.7m)   exit 0     # 11:19
```

Byte-identical to the phase-02 RED command. The spec was **not** weakened: all 11 assertion source
lines quoted in `evidence/red-run-full-output.txt` were matched verbatim against the current
`e2e/the-le.spec.ts` — every one still present. Both DEC-002 `test.skip` entries still print with
their reasons (`GUI_003`, `FUN_005`). `redExitCode 1 → greenExitCode 0`.

Full output: `evidence/green-run.txt`.

### The four aborted attempts before it — recorded, not hidden

Attempts at 11:01, 11:05, 11:11 and 11:17 all exited **1** without running a single screen test:
the shared `[setup]` project (`e2e/auth.setup.ts`) blew its own 30s test timeout while the gate's
cold `next dev` compiled `/login` and `/todo`, and all 11 screen tests reported "did not run".
Those are **environment aborts, not app results**, and I only classified them that way after
measuring:

| Probe | Result |
|---|---|
| Instrumented `/todo` navigation with the captured auth cookies, warm server | HTTP 200, networkidle in **1.38–1.60s**, no redirect loop (run twice, 80 min apart) |
| `chromium.launch()` overhead | 81–133ms — not the cost |
| `npx playwright test --project=setup --timeout=180000` | **exit 0**, the same setup test passing in **3.9s** |
| `npx playwright test --project=setup` (default timeout, isolation) | **exit 0**, **5.0s** |
| `git log -- e2e/auth.setup.ts` | unchanged since `8a02795`, weeks before F007 |
| `git diff playwright.config.ts` | one line — `the-le` added to the anon `testMatch` regex |

## 2. Full-suite regression — exit 1, and honestly inconclusive

```
npm run test:e2e        →  exit 1
70 passed · 26 failed · 1 skipped · 94 did not run   (29.5m, 6 workers)
```

Every one of the 26 is a **30s/35s timeout**, not an assertion mismatch — there is no
expected-vs-received diff anywhere in the log. The head of the list is `[setup] auth.setup.ts`,
and its failure is *why* 94 tests never ran: the whole `anon` project (this feature's own spec
included) depends on it.

**Is any of it an F007 regression? No — and here is the proof rather than the assurance:**

I ran all nine `anon` specs one file at a time
(`evidence/regression-anon-per-spec.txt`). **All nine fail identically on the same
`auth.setup.ts` 30s timeout — including `e2e/smoke.spec.ts`**, which predates this feature by
weeks and touches nothing F007 changed. A failure that reproduces on `smoke.spec.ts` cannot be
caused by `/standards`, by the appended seed rows, or by an added `testMatch` alternative.

Corroborating, on the two shared surfaces named in the brief:

- **`supabase/seed.sql`** — append-only. It adds `rule_sections` / `rule_items` rows to two
  tables created by this feature's own migration. No existing row, table or count is touched, so
  no spec that asserts against seed data can see it.
- **`app/standards/page.tsx`** — `/standards` stopped rendering `ComingSoon`, but `ComingSoon`
  itself is untouched and still serves `/admin`, `/kudos/secret-box` and `/kudos/[id]`. No spec
  outside `the-le.spec.ts` asserts on `/standards`.

**What I cannot claim:** I could not produce one clean full-suite pass on this box. After 11:24
*no* whole-project invocation cleared the setup gate — four `--project=anon` attempts (cold, after
warming the Turbopack cache under the gate's pinned env, with `--workers=1`, and after a graceful
dev-server stop) all aborted the same way, while `--project=setup` alone passed in 5.0s minutes
later. So the 94 tests that never ran are **unverified**, not verified-good. That gap is real and
I am not rounding it up.

**Two failures worth a second look by someone (not F007's doing, but not obviously environmental
either):** `kudos-live-board-authed.spec.ts` **K-10** and **K-25** (heart toggle / heart persists)
failed at 20.6s and 24.5s — *below* the 30s ceiling, which is a different signature from the rest.
F006's `reports/implementer-phase-04.md` records K-10 passing in 4.1s. The local DB has since
accumulated hearts and kudos from many suite runs, so a data-state sensitivity is the likely
cause. Flagging, not diagnosing — out of this phase's scope.

## 3. Visual validation — `/standards` at 1440×1796, anon

Playwright MCP is unusable in this repo (no system Chromium; `.playwright-libs` is vendored for
the project's own runner), so capture ran through the project's Playwright with the vendored libs
on `LD_LIBRARY_PATH`. That also bought exact DOM geometry instead of eyeballing.
Pointer parked at (5,5) and focus cleared before the reference capture.

Evidence: `visual-panel.png`, `visual-panel-viewport.png`, `visual-compare-design-vs-actual.png`
(side-by-side), `visual-icon-grid.png`, `visual-footer-strip.png`, `visual-panel-390.png`,
`visual-measurements.json`.

### What matches the frame

| Check | Design (`the-le.png`, measured in pixels) | Actual (DOM) | |
|---|---|---|---|
| Drawer left edge / width | x=887, 553 wide | x=887, w=553 | ✅ |
| Content padding | text starts x=928 | x=927 (`px-10` → 887+40) | ✅ |
| `<h1>` Thể lệ | gold glyphs from y=33, `#FFEA9E` | 45px/52px, `rgb(255,234,158)`, y=24 box | ✅ |
| Section heading 1 | 2 lines, y 106–149 | 22px/28px, y=100 h=56 | ✅ |
| `KUDOS QUỐC DÂN` | larger heading | 24px/32px | ✅ |
| Section order / count | 3 | 3 | ✅ |
| Hero tiers | 4, pill 128px wide | 4, `<img>` 128×22 | ✅ |
| Collectible icons | 6, two rows of three, 64px discs | 6, `grid-cols-3`, 80×64 boxes | ✅ |
| **Doubled captions** | — | **none** — the `object-cover object-top` crop works exactly as phase 06 intended | ✅ |
| Footer row | buttons y 1314–1369 (56 tall), 16px gap | h=56, gap=16 | ✅ |
| **Pen on the gold button** | dark pen on `#FFEA9E` | **clearly visible**, `/images/rules/pen-icon.svg`, 24×24, `#00070C` on `rgb(255,234,158)` | ✅ |
| Dialog semantics | — | `role=dialog`, `aria-modal=true`, `aria-labelledby=rules-panel-title` | ✅ |
| Page does not scroll | — | `scrollHeight 1796 == innerHeight 1796` | ✅ |
| 390px responsive | — | panel x=0 w=390, `scrollWidth 390 == innerWidth 390`, **no horizontal scrollbar** | ✅ |

### TC_THELE_GUI_004 — hover, captured (nobody else covers this)

Both states captured and diffed against a rest-state crop of the same element, deterministically:

| Control | Rest | Hover | Measured change |
|---|---|---|---|
| `Đóng` | `rgba(255,234,158,0.10)` fill, border `rgb(153,140,95)` = `#998C5F` | fill flips to white/10 (`oklab(0.999994…/0.1)`), border unchanged | **88.8% of pixels changed**, max channel Δ10 |
| `Viết KUDOS` | `rgb(255,234,158)` = `#FFEA9E` | `rgb(240,217,138)` = `#F0D98A` | **97.8% of pixels changed**, max channel Δ20 |

Both visibly restyle. `Đóng`'s change is subtle to the eye (both fills are 10% alpha; the hue goes
gold→white) but it is a real, measurable restyle, not a no-op. Border and rest fill match the
clarified spec exactly.
Files: `visual-rest-close-el.png` / `visual-hover-close-el.png`,
`visual-rest-write-kudos-el.png` / `visual-hover-write-kudos-el.png`, plus the wider
`visual-hover-close.png` and `visual-hover-write-kudos.png`.

### Discrepancies — MATERIAL (need a bounded fix or explicit acceptance)

**V-1 — collectible captions are not width-constrained; 4 of 6 wrap differently from the frame.**
The frame constrains each icon's caption to roughly the 80px artwork width, so captions stack:

| | Design | Actual |
|---|---|---|
| REVIVAL | 1 line | 1 line ✅ |
| TOUCH OF LIGHT | **2 lines** (max text width 64px) | 1 line ❌ |
| STAY GOLD | 1 line | 1 line ✅ |
| FLOW TO HORIZON | **2 lines** (56px) | 1 line ❌ |
| BEYOND THE BOUNDARY | **3 lines** (70px) | 2 lines ❌ |
| ROOT … | **2 lines** (56px) | 1 line ❌ |

Cause: `rules-collectible-grid.tsx` puts the caption in a full grid cell — measured **147px wide**
against the frame's ~80px — so it never wraps where the design wraps. Visible in
`visual-compare-design-vs-actual.png`: the design's grid reads as three narrow stacks, the build
as three wide single lines. Bounded fix for `momorph-ui-implementer`: constrain the caption (and
therefore the item) to the 80px artwork width. **I did not touch the component.**

**V-2 — the hero-tier block is missing its ~19px left indent.**
In the frame every tier pill starts at **x=946** and every tier description at **x=947**, while
section paragraphs start at 928 — the tier list is indented ~19px inside the content column. The
build renders the whole tier block flush at **x=927**. Knock-on: the description column is 473px
instead of ~449px, so tier 3's description sets in 2 lines where the frame sets 3, and the tier row
pitch comes out **80px against the frame's 88px** (measured pill tops: design 259/347/436/523,
actual 261/341/421/501). Bounded fix: indent the tier list ~20px. **Not touched.**

### Discrepancies — MINOR (recorded, per the plan; not returned for fix)

- **Icon column pitch 163px vs the frame's 149px.** Middle column lands exactly (1163 both); the
  outer two sit ~14px further out (design disc centres 1014/1163/1311, actual 1000.5/1163.5/1326.5).
  Same root cause as V-1 — the grid distributes across the full 473px column.
- **Cumulative vertical compression, ~57px over the column.** Heading 1 aligns to the pixel;
  heading 2 sits 27px high; `KUDOS QUỐC DÂN` sits ~57px high. Entirely explained by V-2's tighter
  tier rows and V-1's shorter caption stacks.
- **Pill→label gap 12px vs the frame's ~8px.**
- **`Đóng` measures 115px wide** — vs 94px in the frame render and the 112px the node's own CSS
  sums to. This is the known, documented frame self-contradiction; phase 05 followed the declared
  CSS and left width to content. `Viết KUDOS` absorbs the difference (342px vs the frame's 363px).
  Expected, per the brief. Not a defect.
- **Footer sits at the viewport bottom, not directly under the content.** The frame's drawer is
  1410px tall (measured — the artboard's own content height); the build's is `h-svh`. Correct
  behaviour for a fixed full-height drawer, and `FUN_001`/`FUN_002` both assert it.

### Copy discrepancy — needs an explicit decision

**V-3 — `ROOT FUTHER` vs `ROOT FURTHER`.** The seed, the constants fixture and `clarifications.md`
all deliberately carry `ROOT FUTHER`, justified as "the caption text node reads FUTHER, and the
text node is what ships". The **frame render disagrees**: `design/the-le.png` at that caption reads
**`ROOT FURTHER`**, in the caption's own position and type style (verified by cropping the design
PNG). The exported asset `public/images/rules/icon-root-further.png` does bake `ROOT FUTHER`, so
the two MoMorph artifacts contradict each other.

I am not calling this resolved and I did not change it — but the recorded rationale ("the artwork
reads FURTHER, the text node reads FUTHER") is not what I measured: the *design render* reads
FURTHER too. Someone with MoMorph access should re-read node `I3204:6088;737:20392` and either
confirm the typo ships or correct the seed. It is user-visible copy on a public page.

### Not verifiable from this capture

- **The ❤️ emoji renders monochrome** in every screenshot; the frame shows it red. This headless
  Chromium has no colour-emoji font installed, so the capture cannot judge it. **Indeterminate** —
  needs a look on a real desktop browser before anyone calls it a defect or a pass.
- **Comparison method**: no deterministic full-frame metric is available (the frame's drawer is
  1410px tall, the build's is viewport-height, so a whole-panel pixel diff would be meaningless).
  Everything above is either an exact pixel measurement of a named landmark or, where stated, a
  qualitative judgment. The only zero-baseline numeric comparisons I ran are the two hover diffs.

## 4. Security re-verified by measurement (FR-601)

```
set role anon; insert into public.rule_items ... → ERROR: new row violates row-level security policy
set role anon; update public.rule_sections ...  → UPDATE 0
set role anon; select count(*) from public.rule_sections; → 3
```
Read-only for anon, exactly as required. Screenshots were taken anonymous — no personal data in
`evidence/*.png`.

## 5. Not fixed by me, by design

No source file was touched in this phase. V-1 and V-2 are bounded Track A fixes for
`momorph-ui-implementer`; V-3 is a data/clarification decision.

One stale comment for whoever reviews the diff: `rules-panel.tsx` still says
`copy.panelAriaLabel` "is left in the dictionary", and `rules-hero-tier-list.tsx` says
`heroTierImageAlt` "is unused; removing the key belongs to phase 01" — both keys have since been
removed. Comments only; harmless, but they now describe a state that no longer exists.

## Unresolved questions

1. **V-1 and V-2 — fix or accept?** Both are real deviations from the frame and both are cheap to
   fix (one width constraint, one indent). I recommend the fix; if the call is to accept, it should
   be written into `clarifications.md` so the next visual pass does not re-raise it.
2. **V-3 — does `ROOT FUTHER` really ship?** The frame render contradicts the recorded rationale.
3. **The 94 unverified tests.** A clean full-suite pass could not be produced on this box today.
   The `auth.setup.ts` 30s budget is too tight for a cold `next dev` here, and that is a harness
   problem worth its own commission — it is not mine to widen mid-gate, and I did not.
4. **K-10 / K-25** heart tests fail below the timeout ceiling; F006 recorded K-10 passing at 4.1s.
   Possible accumulated-data sensitivity in the local DB.
