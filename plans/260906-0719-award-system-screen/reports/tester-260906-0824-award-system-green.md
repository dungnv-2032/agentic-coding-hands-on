# Tester — Award System screen, phase 03 (GREEN + visual validation)

- **Screen:** Hệ thống giải — `https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/zFYDgyj_pD`
- **Route:** `/awards-information` · **testPolicy:** `e2e-red-first`
- **Date:** 2026-09-06 · **Owner of `e2e/**`:** tester (unchanged since RED)
- **Verdict:** **GREEN gate PASSES. Visual validation INCOMPLETE** — three material mismatches against the frame.

---

## Task 1 — GREEN rerun

```
npx playwright test e2e/award-system.spec.ts --project=anon
```

**Exit code: `0`** · **13 passed, 0 failed (1.2m)**

Same command, same spec file, byte-for-byte unchanged since the RED run (exit `1`, 11 failed).
No assertion was weakened, skipped, relaxed, or edited. Log: `evidence/award-system-green-run.log`.

| Test | RED | GREEN |
|---|---|---|
| ID-0/2 route + header nav aria-current | pass | pass |
| ID-3 structure + document order | fail | pass |
| ID-4 hero title block | fail | pass |
| ID-5 menu, 6 items, design order | fail | pass |
| ID-6 titles/quantities/prizes/notes | fail | pass |
| ID-7 card images + alt | fail | pass |
| ID-8 Kudos block | fail | pass |
| ID-9/11 click → scroll + exclusive active | fail | pass |
| ID-10 hover | fail | pass |
| ID-12 Chi tiết → /kudos | fail | pass |
| ID-13 invalid hash, no page errors | fail | pass |
| Deep link `#mvp` | fail | pass |

**ID-13 note:** zero `pageerror` and zero console errors on the finished screen. Nothing was filtered
beyond the resource-load noise already declared in the RED report. Next dev emits no console errors here.

### Flake check on the async-seeded deep link (asked for explicitly)

```
npx playwright test e2e/award-system.spec.ts --project=anon -g "Deep link|ID-9/11|ID-13" --repeat-each=10
```

**Exit code: `0`** · **31 passed, 0 failed (1.1m)** — 10 repeats each of the three
IntersectionObserver-dependent tests. **Not flaky. This is a real pass, not a lucky one.**

But the honest detail behind that pass — measured, not inferred. Sampling the active nav item every
16 ms from navigation commit on `/awards-information#mvp`:

```
DEEPLINK_TRACE=[[0,"award-nav-top-talent"],[290,"award-nav-mvp"]]
```

The menu shows **Top Talent active for the first ~290 ms**, then corrects to MVP. The end state is
right and my assertion (which retries) is honest about what it checks — the *settled* state. But
clarifications wanted the nav "not stuck on Top Talent after a deep link", and for ~0.3 s it visibly
is. Filed as a low-priority fix below, not as a gate failure.

---

## Task 2 — Regression

```
npx playwright test e2e/homepage.spec.ts --project=anon
```

**Exit code: `0`** · **22 passed, 0 failed (1.0m)** · log: `evidence/homepage-regression-run.log`

Every test that touches this route still passes against the real screen: ID-18, ID-19, ID-2/3/4/20,
ID-47/48/49/50/52, ID-55/59. Replacing `ComingSoon` broke nothing.

---

## Task 3 — Visual validation

**Method.** Playwright MCP was unavailable — it requires the `chrome` channel at
`/opt/google/chrome/chrome`, which is not installed, and installing is out of scope. Capture instead
ran through the project's own working Chromium at a 1440×900 viewport, `deviceScaleFactor: 1`, with
the pointer parked at (1430, 5) and focus blurred before every shot so the reference state carries no
stray hover or focus ring. Artifacts in `visuals/`; numbers in
`evidence/visual-measurements-award-system.json`.

**On the metric.** There is no deterministic pixel-diff available — the reference is a Figma frame
export, not a rendered baseline. Geometry and colour findings below are **measured** (DOM
`getBoundingClientRect` / `getComputedStyle` against PIL pixel sampling of the frame). Everything else
is a **qualitative** judgment and is labelled as such. Nothing here is "exact".

### Verdict by region

| Region | Verdict |
|---|---|
| Header + nav chrome | match |
| Hero (keyvisual, wordmark, eyebrow, divider, gold h1) | match |
| Left category menu | match — measured colours identical |
| Card layout, alternation, copy, labels, quantities, prizes | match |
| **Award badge images** | **MISMATCH — material** |
| **Card icons (Target / Diamond / License)** | **MISMATCH — colour** |
| **Sun\* Kudos block width** | **MISMATCH — material** |
| Card content left edge | minor (−42 px) |
| Award description text alignment | minor |
| `Hoặc` separator | holds up — the frame really is like that |
| Footer | match |

### The three questions I was asked to judge

**1. Container width — the inset is a defect, not an acceptable trade.**
Design Kudos card: x **144 → 1295, width 1152**, flush with the award body's left edge.
Actual: x **252 → 1188, width 936** — left edge +108 px, width −216 px (−18.75%).
This is not only an alignment nit. The narrower card squeezes the text column so the body copy runs
**underneath the KUDOS logo** ("…tháng 11/2025, khuyến khích…" passes behind the wordmark). The frame
keeps them cleanly apart. See `visuals/cmp-kudos.png`. Composing `KudosPromo` unchanged is the
clarifications mandate, so the fix belongs in the *wrapper* on this screen, not in the shared
component — see the bounded fix below.

**2. `Hoặc` separator — holds up. The frame genuinely renders it that way.**
Actual `#2E3940` on effective background `#00101A`. The frame carries the same near-invisible slate
tone next to the hairline rule (visible in `visuals/cmp-signature.png`, top half). Node `313:8499`
confirmed. Not a deviation.
Separate observation, not a deviation: the measured contrast is **1.64:1** — far below WCAG 3:1.
It faithfully reproduces the design, and the design is inaccessible. Worth raising with the designer;
not something to fix unilaterally against an authoritative frame.

**3. Icons — shape confirmed, colour wrong.**
Shape holds: all three are filled `path` elements, no stroke, 24×24 viewBox. The diamond is a filled
gem exactly as the frame draws it.
Colour does not. Measured in the frame, the Diamond, License and Target glyphs are pure
**`#FFFFFF`**, sampled at `(821,709)-(829,728)`, `(821,4190)-(839,4209)`, `(823,4311)-(838,4331)` —
while the label text right beside them is gold `#FFEA9E (255,234,158)`. The implementation renders the
icons gold. The frame's own menu proves the rule: inactive menu icons are white, active is gold, and
the card icons follow the white branch. See `visuals/cmp-icons-6x.png`.

### The one nobody flagged — award badge images are stretched

Every award image is a **336×336** source rendered with `object-fit: fill` into a box stretched to the
height of the text column:

| award | rendered | distortion |
|---|---|---|
| top-talent | 336×550 | 1.64× |
| top-project | 336×598 | 1.78× |
| top-project-leader | 336×574 | 1.71× |
| best-manager | 336×562 | 1.67× |
| **signature-2025-creator** | **336×966** | **2.88×** |
| mvp | 336×658 | 1.96× |

The design renders each badge as a **336×336 square** — spec item D.1.1's mandated dimension, and the
reason clarifications reused the shipped assets untouched. In the running page the circular badge is
visibly ovalised; on Signature it is nearly a 3:1 ellipse. Plainly visible in
`visuals/cmp-full-design-vs-actual.png` and `visuals/cmp-signature.png`.
My ID-7 asserts the image and its alt text, not its geometry, so the suite is green and the artwork is
still wrong. That gap is mine to close once the fix lands.

### Minor differences (reported, not blocking)

- **Card content left edge:** actual image column starts x 397, design x 439 (−42 px); text column 778
  vs 819. Right edges flush at ~1296. The gap between menu and card is 37 px tighter than the frame.
- **Description alignment:** actual body copy is justified (flush both edges, visible rivers, a
  stretched "T rong" in the Signature paragraph); the frame is ragged-right. Qualitative read from
  `visuals/cmp-signature.png`.
- **Kudos CTA glyph:** frame draws a ↗ arrow, actual renders a rotated chevron. This is the composed
  `KudosPromo`, already shipped on the homepage — pre-existing, out of this screen's scope, noted only
  because it is a difference against this frame.
- **Header bell/avatar:** absent in the anon capture, present in the frame. Correct — the frame was
  captured authenticated. Not a defect.

---

## Bounded fixes for `momorph-ui-implementer`

Ordered heaviest first. All are in `app/awards-information/_components/**` — no test file changes.

1. **Un-stretch the award badge** — `award-detail-card.tsx`. The `<img>` is a direct flex child of a
   row with default `align-items: stretch`, so it inherits the text column's height and `object-fit:
   fill` distorts the 336×336 source. Pin the square (`aspect-square` / explicit 336×336) or stop the
   stretch (`self-start` on the image, or `items-start` on the row). Verify: rendered box is 336×336
   for all six.
2. **Kudos block width** — the wrapper on `app/awards-information/page.tsx`, not `KudosPromo` itself
   (clarifications mandates composing it unchanged). Today it renders 936 px at x 252; the frame wants
   1152 px at x 144, flush with the award body. Fixing the width also clears the body-copy/KUDOS-logo
   overlap. If the shared component cannot widen without touching it, escalate — do not leave the
   overlap in.
3. **Icon fill white** — `award-system-icons.tsx`. Target, Diamond and License go `#FFEA9E` → `#FFFFFF`.
   Shape and 24×24 sizing are already right; colour only.
4. **Card content left edge** — `award-detail-card.tsx`, +42 px on the card column's left offset (or
   widen the menu column's right gap) to seat the image at x 439 as the frame does. Cosmetic.
5. **Deep-link active-state flash** — `award-category-nav.tsx`. `#mvp` shows Top Talent active for
   ~290 ms before correcting. `react-hooks/set-state-in-effect` blocked the synchronous seed; a lazy
   `useState` initialiser reading `location.hash` (or seeding from the hash inside the observer's first
   delivery) closes it without the lint violation. Cosmetic; the end state is already correct.
6. **Description alignment** — drop `text-justify` on the award description if the ragged-right frame
   is intended. Lowest priority; confirm with design first, since the project uses justified body copy
   elsewhere.

After fixes 1–4 land, send it back to me: I rerun the same GREEN command and re-capture. I will also
add an aspect-ratio assertion to ID-7 at that point so the badge geometry cannot silently regress —
deliberately **not** added now, because adding a failing assertion mid-gate would misreport the state
of the GREEN run.

---

## Evidence

- `evidence/award-system-green-run.log` — exit 0, 13 passed
- `evidence/homepage-regression-run.log` — exit 0, 22 passed
- `evidence/award-system-flake-check.log` — exit 0, 31 passed
- `evidence/raw-temper-runs-award-system-green.json` — raw command/exitCode/summary triples
- `evidence/visual-measurements-award-system.json` — every number quoted above
- `visuals/actual-full-1440.png`, `actual-hero-viewport.png`, `actual-kudos.png`,
  `actual-nav-and-first-card.png`, `actual-section-<slug>.png` ×6
- `visuals/cmp-full-design-vs-actual.png`, `cmp-hero.png`, `cmp-top-talent.png`,
  `cmp-signature.png`, `cmp-kudos.png`, `cmp-icons-6x.png`

## Unresolved

- **Kudos width vs "compose unchanged".** The frame wants 1152 px; `KudosPromo` is hard-coded to a
  936 px inner card. Whether that is fixed by a wrapper override on this screen or by parameterising
  the shared component is an ownership call I do not get to make — flagging, not deciding.
- **`Hoặc` at 1.64:1 contrast** is faithful to the design and fails WCAG. Needs a designer, not a dev.
- **Test case ID-14** (Chi tiết → friendly 404) still unexercisable: `/kudos` remains a declared
  `ComingSoon` placeholder. The link resolves, so ID-12 passes; the 404 path has no destination to
  fail against yet. Carried over from RED, unchanged.

---
**Superseded (2026-09-06 08:51):** the visual section of this report — the three material mismatches and the ragged-right finding — is superseded by `tester-260906-0851-award-system-final-verdict.md`. All four fixes landed and were re-measured; the ragged-right call was wrong and is retracted there. The gate results in this report stand as recorded.
