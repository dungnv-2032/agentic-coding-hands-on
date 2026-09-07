# Sun* Official Components (Preset #13)

**Brand-locked**, not "inspired by." This is the official Sun* v4 slide design system — exact
palette, exact typography, exact 23-layout catalog — ported from the source template
`Sun Template v4 - standalone.html` (Be Vietnam Pro / Space Grotesk, red-accent brand). Unlike the
other 12 HTML presets, nothing here is a starting point to riff on: colors, fonts, and component
markup are fixed. See `style-presets.md` for the one-paragraph summary and how this preset is offered
to the user; this file is the full component catalog referenced from there.

## Structural note (read before generating)

The source bundle nests every slide as `<section data-label="…"><div class="slide TYPE">…</div></section>`
— the outer `<section>` was bundler/authoring-tool chrome (drag-and-drop screen picker), not part of
the design system. This skill's own controller (`references/html-template.md`) expects **one** element
per slide carrying the `.slide` class directly (that's what gets `scroll-snap-align`, the
`IntersectionObserver`, and the `.visible` class toggle). Every snippet below is already flattened to
match: `<section class="slide TYPE …">…</section>`, `data-label`/`data-screen-label` dropped (they had
no CSS/JS dependency — pure authoring-UI metadata). Where the source used a descendant rule like
`.s-brand .slide { … }` (because `s-brand` sat on the outer wrapper), the CSS below is rewritten as a
compound selector on the one flattened element (`.slide.s-brand { … }`) — same cascade result, one element.

## Setup — paste into every generated `<html>` and `<head><style>`

**`<html>` attribute contract** (all four are boolean toggles the generator sets, matching the source):

| Attribute | Values | Effect |
|---|---|---|
| `data-preset` | `"sun-official"` | **Always required** — every selector below is scoped under it |
| `data-variant` | `"crisp"` (default) \| `"editorial"` | Visual variant. `crisp`: white bg, Be Vietnam Pro throughout. `editorial`: warm-cream bg, Space Grotesk display type, and `.s-brand` slides invert to solid red. Same tokens and same markup — only CSS vars plus a few `.s-brand` overrides differ |
| `data-footerlogo` | `"true"` (default) \| `"false"` | Show/hide the footer wordmark on body slides |
| `data-pageno` | `"true"` \| `"false"` (default) | Show/hide the page-number in the footer |
| `data-artwork` | `"true"` (default) \| `"false"` | Show/hide the `.bg-art` decorative layer |
| `data-anim` | `"true"` (default) \| `"false"` | Enable/disable entrance + chart-bar animation |

```html
<html lang="en" data-preset="sun-official" data-variant="crisp"
      data-footerlogo="true" data-pageno="false" data-artwork="true" data-anim="true">
```

**Fonts** (verified resolving — HTTP 200, correct weight subset):

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap">
```

**Brand asset data URIs — embed verbatim, do not leave the token in shipped output.** The two official
marks (logo wordmark, 8-point asterisk) are preserved from the supplied source asset, not hand-redrawn
(trademark) — losslessly-equivalent recompressed as 32-color indexed PNG (Pillow `FASTOCTREE`, no
dither; both are flat red-on-transparent shapes, visually identical to the 24-bit source). Every
`{{SUN_LOGO}}` and `{{SUN_ASTERISK}}` placeholder in the markup snippets below resolves to the
complete data URI stored once under the shipped skill assets, rather than repeating a multi-KB string
40+ times:

- `{{SUN_LOGO}}` (344×114, source SHA-256 `123a4313f4a13962709995c7b994d24ccdf4ae43209b42d80bb17826f5e60991`) =
  the complete data URI in `assets/sun-official/logo.data-uri.txt`.
- `{{SUN_ASTERISK}}` (1000×1000, source SHA-256 `d001d37adb852ff24f6d0fb0c23affc628100b4ba6e0cf24a81c9d85fb8974d5`) =
  the complete data URI in `assets/sun-official/asterisk.data-uri.txt`.

> Generation step: read the two `.data-uri.txt` files and substitute their full contents for every
> `{{SUN_LOGO}}` / `{{SUN_ASTERISK}}` occurrence in the chosen component snippets before writing the
> final HTML — the placeholder tokens themselves must never appear in delivered output.

**Responsive convention.** Every typographic size below is `clamp(MIN, min(Xvw, Ydvh), MAX)` where
`MAX` equals the source's fixed value at the reference 1920×1080 canvas, `X = px/1920*100`,
`Y = px/1080*100` (the `min(vw, dvh)` fluid term keeps the reference 16:9 proportions even when the
real viewport isn't exactly 16:9), and `MIN = MAX * ratio` using a size-tiered ratio — bigger display
type scales down more, small body/UI text stays closer to its max for legibility:

| Tier | px range | ratio |
|---|---|---|
| display | ≥140px | 0.28 |
| hero | 80–139px | 0.38 |
| title | 50–79px | 0.48 |
| body | 30–49px | 0.60 |
| tiny | <30px | 0.72 |

Spacing tokens (pad-x/pad-top/pad-bottom/gap-title/gap-item) use ratio 0.55–0.65 (padding scales less
aggressively than gaps — large outer padding shouldn't collapse too far on small viewports).
Fine-grained structural values (border-widths, small pill padding, icon diameters) stay literal px —
they're small enough that clamping buys no legibility gain. Multi-column grids get a documented
`@media (max-width: 1024px)` reflow per component instead of an ever-shrinking gap.

### Design tokens

```css
html[data-preset="sun-official"] {
  --red: #FF2200;
  --red-deep: #AD0C00;
  --red-tint: #FFE9E4;
  --ink: #1A1A1A;
  --muted: #6E6A66;
  --line: #E8E4E0;
  --amber: #F2A900;
  --amber-tint: #FCEFD4;
  --teal: #0E7C7B;
  --teal-tint: #DFF0EF;
  --sand: #C9C0B8;
  --sand-tint: #EFEBE5;

  --bg: #FFFFFF;
  --bg-alt: #F7F5F2;

  --font-display: 'Be Vietnam Pro';
  --font-body: 'Be Vietnam Pro';
  --ease-out: cubic-bezier(0.22, 0.61, 0.36, 1);

  /* Typography tokens. --type-hero and --type-quote are defined for completeness but their sole
     source consumers (.cover-title, .quote-text) were overridden by a later template layer to a
     different literal value — those two components clamp their OWN final value below; do not
     expect var(--type-hero) to equal .cover-title's rendered size. */
  --type-hero: clamp(2.66rem, min(5.833vw, 10.37dvh), 7rem);        /* 112px — shadowed, see .cover-title */
  --type-giant: clamp(4.55rem, min(13.542vw, 24.074dvh), 16.25rem); /* 260px */
  --type-title: clamp(2.04rem, min(3.542vw, 6.296dvh), 4.25rem);    /* 68px (v3-final; v1 was 64px) */
  --type-subtitle: clamp(1.5rem, min(2.083vw, 3.704dvh), 2.5rem);   /* 40px */
  --type-quote: clamp(1.68rem, min(2.917vw, 5.185dvh), 3.5rem);     /* 56px — shadowed, see .quote-text */
  --type-body: clamp(1.2rem, min(1.667vw, 2.963dvh), 2rem);         /* 32px */
  --type-small: clamp(1.17rem, min(1.354vw, 2.407dvh), 1.625rem);   /* 26px */
  --type-tiny: clamp(1.08rem, min(1.25vw, 2.222dvh), 1.5rem);       /* 24px */

  --pad-x: clamp(3.781rem, min(5.729vw, 10.185dvh), 6.875rem);      /* 110px */
  --pad-top: clamp(3.3rem, min(5vw, 8.889dvh), 6rem);               /* 96px */
  --pad-bottom: clamp(4.469rem, min(6.771vw, 12.037dvh), 8.125rem); /* 130px */
  --gap-title: clamp(2.1rem, min(2.917vw, 5.185dvh), 3.5rem);       /* 56px */
  --gap-item: clamp(1.137rem, min(1.458vw, 2.593dvh), 1.75rem);     /* 28px */
}

html[data-preset="sun-official"][data-variant="editorial"] {
  --bg: #FAF7F2;
  --bg-alt: #F1ECE3;
  --font-display: 'Space Grotesk';
}
```

### Base slide, header, footer

```css
html[data-preset="sun-official"] .slide {
  /* No width/height here on purpose: the shared viewport-base.css `.slide` rule already sets
     `width: 100vw; height: 100vh; height: 100dvh;` (the dvh is the mobile-Safari dynamic-viewport
     fix). This selector's higher specificity would silently override that with a plain 100%/100%
     if redeclared here, losing the dvh fix for this preset only. */
  position: relative;
  box-sizing: border-box;
  background: var(--bg);
  color: var(--ink);
  font-family: var(--font-body), sans-serif;
  padding: var(--pad-top) var(--pad-x) var(--pad-bottom);
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  isolation: isolate; /* confines .bg-art's z-index:-1 to this slide. Without this, .slide (from the
    shared viewport-base.css) never establishes its own stacking context, so a negative z-index child
    escapes to the document root and can render behind an ADJACENT slide's opaque background instead
    of its own — confirmed missing in a real render before this fix. Scoped here (not in
    viewport-base.css) so the other 12 presets are untouched. */
}

html[data-preset="sun-official"] .kicker {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: var(--type-tiny);
  font-weight: 600;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--red-deep); /* v3-final override of v1's --muted */
  margin: 0;
}
html[data-preset="sun-official"] .kicker .k-sep { display: inline-block; width: 64px; height: 2px; background: var(--line); margin-left: 10px; }
html[data-preset="sun-official"] .ast { width: 22px; height: 22px; display: block; }

html[data-preset="sun-official"] .title {
  font-family: var(--font-display), sans-serif;
  font-size: var(--type-title);
  font-weight: 700;
  line-height: 1.12;
  letter-spacing: -0.022em; /* v3-final override of v1's -0.015em */
  margin: 22px 0 0 0;
}
html[data-preset="sun-official"] .head { margin-bottom: var(--gap-title); }
html[data-preset="sun-official"] .head-row {
  display: flex;
  flex-wrap: wrap; /* lets .badge drop to its own line instead of forcing horizontal overflow —
    only engages when the row genuinely doesn't fit (narrow viewports); invisible at desktop widths */
  row-gap: 16px;
  justify-content: space-between;
  align-items: flex-start;
  width: 100%;
  border-bottom: 2px solid var(--line);
  padding-bottom: 38px;
  margin-bottom: 54px;
}
html[data-preset="sun-official"] .head-row .head { margin-bottom: 0; }

html[data-preset="sun-official"] .body-text { font-size: var(--type-body); line-height: 1.55; margin: 0; color: var(--ink); text-wrap: pretty; }
html[data-preset="sun-official"] .muted { color: var(--muted); }
html[data-preset="sun-official"] .lede { max-width: 1240px; }

html[data-preset="sun-official"] .badge {
  display: inline-flex;
  align-items: baseline;
  gap: 12px;
  border: 2px solid var(--line);
  border-radius: 999px;
  padding: 14px 32px;
  font-size: var(--type-tiny);
  font-weight: 500;
  color: var(--muted);
  white-space: nowrap;
}
html[data-preset="sun-official"] .badge strong { font-weight: 700; color: var(--ink); }

html[data-preset="sun-official"] .foot-logo { position: absolute; left: var(--pad-x); bottom: 52px; height: 34px; }
html[data-preset="sun-official"][data-footerlogo="false"] .foot-logo { display: none; }

html[data-preset="sun-official"] .pageno { position: absolute; right: var(--pad-x); bottom: 52px; font-size: var(--type-tiny); font-weight: 500; color: var(--muted); }
html[data-preset="sun-official"][data-pageno="false"] .pageno { display: none; }
```

### Brand (red) slides in the Editorial variant

`.s-brand` marks a slide as one whose Editorial-variant look is a solid red background with white
text/logo — Cover, Section divider, Thank You. In Crisp (default) this class does nothing.

```css
html[data-preset="sun-official"][data-variant="editorial"] .slide.s-brand { background: var(--red); color: #FFFFFF; }
html[data-preset="sun-official"][data-variant="editorial"] .slide.s-brand .kicker { color: rgba(255, 255, 255, 0.85); }
html[data-preset="sun-official"][data-variant="editorial"] .slide.s-brand .muted { color: rgba(255, 255, 255, 0.75); }
html[data-preset="sun-official"][data-variant="editorial"] .slide.s-brand .ast,
html[data-preset="sun-official"][data-variant="editorial"] .slide.s-brand .foot-logo,
html[data-preset="sun-official"][data-variant="editorial"] .slide.s-brand .brand-logo { filter: brightness(0) invert(1); }
html[data-preset="sun-official"][data-variant="editorial"] .slide.s-brand .pageno { color: rgba(255, 255, 255, 0.75); }
html[data-preset="sun-official"][data-variant="editorial"] .slide.s-brand .badge { border-color: rgba(255, 255, 255, 0.4); color: rgba(255, 255, 255, 0.85); }
html[data-preset="sun-official"][data-variant="editorial"] .slide.s-brand .badge strong { color: #FFFFFF; }
html[data-preset="sun-official"][data-variant="editorial"] .slide.s-brand .bg-art { display: none; }
```

### Decorative background layer (`.bg-art`) — CSS, not raster

The source's 3 decorative background PNGs are NOT embedded (they'd add 60-160KB raster each, and two
of the three are a multi-color gradient ribbon that isn't worth reproducing pixel-for-pixel in CSS).
Reproduced as an on-brand CSS equivalent: a dotted rounded-square motif in `--red-tint`, plus (Section
divider only) a solid red edge bar, matching the source's actual reusable shapes.

```css
html[data-preset="sun-official"] .bg-art { position: absolute; inset: 0; z-index: -1; overflow: hidden; pointer-events: none; }
html[data-preset="sun-official"][data-artwork="false"] .bg-art { display: none; }

html[data-preset="sun-official"] .ba-dot {
  position: absolute;
  border-radius: 20px;
  background-image: radial-gradient(circle, #FFFFFF 2.5px, transparent 2.5px);
  background-size: 20px 20px;
  background-position: 12px 12px;
  background-color: var(--red-tint);
}
/* Divider + Thanks: one small dot-square top-left — confirmed empty there by render check (both are
   bottom/center-anchored layouts). Cover's top-left is NOT used for this — that's where brand-logo
   sits, confirmed colliding on render — Cover relies on the radial wash below instead. An earlier
   bottom-left placement also collided with Divider's running text/footer — moved here instead. */
html[data-preset="sun-official"] .ba-dot-a { width: 170px; height: 170px; left: 3%; top: 6%; }
/* Section divider only: solid red edge bar + a pale wash on the right (empty column in this layout) */
html[data-preset="sun-official"] .bg-art--divider .ba-bar { position: absolute; top: 0; right: 0; width: 14px; height: 100%; background: var(--red); }
html[data-preset="sun-official"] .bg-art--divider::before {
  content: ""; position: absolute; top: 0; right: 14px; bottom: 0; width: 16%;
  background: var(--red-tint); opacity: 0.5;
}
/* Cover / Thank You: add a soft radial wash top-right. The source used a raster multi-color
   gradient "swoosh" ribbon (red/orange/purple, asterisk cutout, ~2048x1152 / 62-163KB per slide).
   Not reproduced: embedding it would blow up deck size for decoration, and a CSS approximation of
   the ribbon shape reads as a botched copy. Reduced instead to this red-tint radial wash, which
   uses only palette colors — on-brand equivalence, not pixel matching. */
html[data-preset="sun-official"] .bg-art--cover::before,
html[data-preset="sun-official"] .bg-art--thanks::before {
  content: ""; position: absolute; top: -10%; right: -6%; width: 46%; height: 60%;
  background: radial-gradient(ellipse at center, var(--red-tint) 0%, transparent 72%);
}
```

### Image contract (`.sun-image-layout`)

The source's `<image-slot>` custom element only existed for the excluded React-based artifact editor.
Replaced with a plain, generation-friendly placeholder pattern: a dashed-border box with a caption by
default; when the user supplies an actual image, swap the `<div>` for an `<img>` with a `data:` URI
(never a local path or remote URL) — same class, so sizing/shape rules keep applying.

```css
html[data-preset="sun-official"] .sun-image-layout {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  background: var(--bg-alt);
  border: 2px dashed var(--sand);
  border-radius: 18px;
  color: var(--muted);
  font-size: var(--type-tiny);
  text-align: center;
  padding: 24px;
  object-fit: cover; /* only applies once swapped for a real <img> */
}
html[data-preset="sun-official"] .sun-image-layout[data-shape="rect"] { border-radius: 0; border: none; }
html[data-preset="sun-official"] img.sun-image-layout { max-height: none; }
```

`.sun-image-layout` is the one documented exception to the skill's generic `max-height: min(50vh,
400px)` image cap — these 6 layout types (Photos, Image + Text, Image Columns, Image Banner, Feature)
size images source-proportionally via their grid/flex container, not the generic cap.

### Animation

Entrance reveal reuses the skill's existing `.reveal` + the shared `.d1`–`.d6` stagger modifiers
(`references/animation-patterns.md`) instead of a bespoke class — apply `class="reveal d2"` etc. in
markup. The chart bar-grow animation is unique to the Data slide and stays Sun*-official-scoped.
`prefers-reduced-motion` is already handled globally by `viewport-base.css` — no extra rule needed here.

```css
html[data-preset="sun-official"][data-anim="true"] .slide.visible .bar {
  transform-origin: bottom;
  animation: sun-official-bar-grow 0.9s var(--ease-out) backwards;
}
html[data-preset="sun-official"][data-anim="false"] .slide .reveal,
html[data-preset="sun-official"][data-anim="false"] .slide .reveal-scale,
html[data-preset="sun-official"][data-anim="false"] .slide .reveal-left,
html[data-preset="sun-official"][data-anim="false"] .slide .reveal-blur {
  opacity: 1;
  transform: none;
  filter: none;
  transition: none;
  animation: none;
}
html[data-preset="sun-official"][data-anim="true"] .slide.visible .bar-group:nth-child(1) .bar { animation-delay: 0.15s; }
html[data-preset="sun-official"][data-anim="true"] .slide.visible .bar-group:nth-child(2) .bar { animation-delay: 0.25s; }
html[data-preset="sun-official"][data-anim="true"] .slide.visible .bar-group:nth-child(3) .bar { animation-delay: 0.35s; }
html[data-preset="sun-official"][data-anim="true"] .slide.visible .bar-group:nth-child(4) .bar { animation-delay: 0.45s; }
html[data-preset="sun-official"][data-anim="true"] .slide.visible .bar-group:nth-child(5) .bar { animation-delay: 0.55s; }

@keyframes sun-official-bar-grow { from { transform: scaleY(0); } }
```

### Component CSS (all 23 layouts)

```css
/* ---- 1. Cover ---- */
html[data-preset="sun-official"] .slide.cover { justify-content: space-between; }
html[data-preset="sun-official"] .brand-logo { height: 64px; }
html[data-preset="sun-official"] .cover-title {
  font-family: var(--font-display), sans-serif;
  font-size: clamp(2.897rem, min(6.354vw, 11.296dvh), 7.625rem); /* 122px, v3-final (v1 var(--type-hero)=112px) */
  font-weight: 700;
  line-height: 1.05;
  letter-spacing: -0.025em; /* v3-final */
  margin: 26px 0 0 0;
  max-width: 1480px;
}
html[data-preset="sun-official"] .cover-sub { font-size: var(--type-subtitle); font-weight: 400; color: var(--muted); margin: 30px 0 0 0; }
html[data-preset="sun-official"][data-variant="editorial"] .slide.s-brand .cover-sub { color: rgba(255, 255, 255, 0.85); }
html[data-preset="sun-official"] .cover-meta {
  display: flex;
  gap: 18px;
  align-items: baseline;
  font-size: var(--type-small);
  color: var(--muted);
  font-weight: 500;
  width: 100%;
  border-top: 2px solid var(--line);
  padding-top: 36px;
  position: relative;
}
html[data-preset="sun-official"] .cover-meta::before { content: ""; position: absolute; top: -2px; left: 0; width: 140px; height: 4px; background: var(--red); }
html[data-preset="sun-official"][data-variant="editorial"] .slide.s-brand .cover-meta { color: rgba(255, 255, 255, 0.85); border-top-color: rgba(255, 255, 255, 0.35); }
html[data-preset="sun-official"][data-variant="editorial"] .slide.s-brand .cover-meta::before { background: #FFFFFF; }

/* ---- 2. Agenda ---- */
html[data-preset="sun-official"] .agenda-grid { display: grid; grid-template-columns: 560px 1fr; gap: 80px; flex: 1; width: 100%; }
html[data-preset="sun-official"] .agenda-list { display: flex; flex-direction: column; margin: 0; padding: 0; list-style: none; }
html[data-preset="sun-official"] .agenda-item {
  display: grid;
  grid-template-columns: 96px 1fr;
  align-items: baseline;
  gap: 24px;
  padding: 34px 0;
  border-bottom: 2px solid var(--line);
  font-size: var(--type-subtitle);
  font-weight: 600;
}
html[data-preset="sun-official"] .agenda-item:first-child { border-top: 2px solid var(--line); }
html[data-preset="sun-official"] .agenda-num { font-family: var(--font-display), sans-serif; font-size: var(--type-small); font-weight: 700; color: var(--muted); letter-spacing: 0.08em; }
@media (max-width: 1024px) {
  html[data-preset="sun-official"] .agenda-grid { grid-template-columns: 1fr; gap: 32px; }
}

/* ---- 3. Section divider ---- */
html[data-preset="sun-official"] .slide.divider { justify-content: flex-end; }
html[data-preset="sun-official"] .divider-num {
  font-family: var(--font-display), sans-serif;
  font-size: var(--type-giant);
  font-weight: 700;
  line-height: 0.9;
  letter-spacing: -0.04em; /* v3-final */
  color: var(--red);
  margin: 0;
}
html[data-preset="sun-official"][data-variant="editorial"] .slide.s-brand .divider-num { color: #FFFFFF; }
html[data-preset="sun-official"] .divider-title {
  font-family: var(--font-display), sans-serif;
  font-size: clamp(1.995rem, min(4.375vw, 7.778dvh), 5.25rem); /* 84px */
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.05;
  margin: 36px 0 0 0;
  max-width: 1400px;
}
html[data-preset="sun-official"] .divider-sub { font-size: var(--type-body); color: var(--muted); margin: 26px 0 0 0; max-width: 1100px; line-height: 1.5; }
html[data-preset="sun-official"] .rule-red { width: 140px; height: 6px; background: var(--red); margin: 44px 0 0 0; }
html[data-preset="sun-official"][data-variant="editorial"] .slide.s-brand .rule-red { background: #FFFFFF; }

/* ---- 4. One Column ---- */
html[data-preset="sun-official"] .bullets { display: flex; flex-direction: column; gap: 0; margin: 44px 0 0 0; padding: 0; list-style: none; }
html[data-preset="sun-official"] .bullets li {
  display: flex;
  gap: 24px;
  align-items: baseline;
  font-size: var(--type-body);
  line-height: 1.45;
  max-width: 1380px;
  width: 100%;
  padding: 30px 0;
  border-bottom: 2px solid var(--line);
}
html[data-preset="sun-official"] .bullets li:first-child { border-top: 2px solid var(--line); }
html[data-preset="sun-official"] .bullet-mark { font-weight: 700; color: var(--red); font-size: 0.8em; flex: none; }

/* ---- 5. Two Column ---- */
html[data-preset="sun-official"] .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 90px; width: 100%; flex: 1; align-content: start; }
html[data-preset="sun-official"] .col { border-top: 4px solid var(--ink); padding-top: 36px; }
html[data-preset="sun-official"] .col-head { font-family: var(--font-display), sans-serif; font-size: var(--type-subtitle); font-weight: 700; margin: 0 0 22px 0; }
html[data-preset="sun-official"] .col p { font-size: var(--type-small); line-height: 1.6; margin: 0; color: var(--muted); }
html[data-preset="sun-official"] .col .col-strong { color: var(--ink); margin-bottom: 18px; font-size: var(--type-body); }
@media (max-width: 1024px) {
  html[data-preset="sun-official"] .two-col { grid-template-columns: 1fr; gap: 40px; }
}

/* ---- 6. Done / Next ---- */
html[data-preset="sun-official"] .retro-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 90px; width: 100%; flex: 1; align-content: start; }
html[data-preset="sun-official"] .retro-col { border-top: 4px solid var(--ink); padding-top: 36px; }
html[data-preset="sun-official"] .retro-col.is-next { border-top-color: var(--red); }
html[data-preset="sun-official"] .retro-col.is-next .retro-h { color: var(--red); }
html[data-preset="sun-official"] .retro-h { font-family: var(--font-display), sans-serif; font-size: var(--type-small); font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; margin: 0 0 34px 0; }
html[data-preset="sun-official"] .retro-list { display: flex; flex-direction: column; gap: 30px; margin: 0; padding: 0; list-style: none; }
html[data-preset="sun-official"] .retro-list li { display: flex; gap: 22px; align-items: baseline; font-size: var(--type-small); line-height: 1.5; }
html[data-preset="sun-official"] .retro-dot { flex: none; font-weight: 700; color: var(--muted); }
html[data-preset="sun-official"] .retro-col.is-next .retro-dot { color: var(--red); }
@media (max-width: 1024px) {
  html[data-preset="sun-official"] .retro-grid { grid-template-columns: 1fr; gap: 40px; }
}

/* ---- 7. Data ---- */
html[data-preset="sun-official"] .data-grid { display: grid; grid-template-columns: 620px 1fr; gap: 110px; flex: 1; width: 100%; }
html[data-preset="sun-official"] .big-number {
  font-family: var(--font-display), sans-serif;
  font-size: clamp(3.325rem, min(9.896vw, 17.593dvh), 11.875rem); /* 190px */
  font-weight: 700;
  line-height: 1;
  letter-spacing: -0.03em;
  color: var(--red);
  margin: 0;
}
html[data-preset="sun-official"] .big-number-caption { font-size: var(--type-body); line-height: 1.5; color: var(--ink); margin: 30px 0 0 0; max-width: 560px; }
html[data-preset="sun-official"] .big-number-note { font-size: var(--type-tiny); color: var(--muted); margin: 22px 0 0 0; }
html[data-preset="sun-official"] .chart { display: flex; flex-direction: column; height: 100%; }
html[data-preset="sun-official"] .bars {
  display: flex;
  align-items: flex-end;
  gap: 44px;
  flex: 1;
  min-height: 0;
  padding: 0 8px;
  background: repeating-linear-gradient(to top, var(--line) 0 2px, transparent 2px calc(25% - 0.5px));
}
html[data-preset="sun-official"] .bar-group { display: flex; flex-direction: column; align-items: center; gap: 16px; flex: 1; height: 100%; justify-content: flex-end; }
html[data-preset="sun-official"] .bar-value { font-size: var(--type-small); font-weight: 700; color: var(--ink); }
html[data-preset="sun-official"] .bar { width: 100%; background: var(--sand-tint); border: 2px solid var(--sand); border-bottom: none; border-radius: 10px 10px 0 0; box-sizing: border-box; }
html[data-preset="sun-official"] .bar.is-accent { background: linear-gradient(180deg, var(--red) 0%, var(--red-deep) 130%); border-color: var(--red-deep); }
html[data-preset="sun-official"] .bar-label { font-size: var(--type-tiny); font-weight: 500; color: var(--muted); }
html[data-preset="sun-official"] .chart-caption { font-size: var(--type-tiny); color: var(--muted); margin: 30px 0 0 0; }
@media (max-width: 1024px) {
  html[data-preset="sun-official"] .data-grid { grid-template-columns: 1fr; gap: 40px; }
}

/* ---- 8. KPI Dashboard ---- */
html[data-preset="sun-official"] .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 40px; width: 100%; flex: 1; align-content: start; }
html[data-preset="sun-official"] .kpi {
  border-radius: 20px;
  padding: 48px 40px 42px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  background: #FFFFFF;
  border: 2px solid var(--line);
  position: relative;
  overflow: hidden;
  box-shadow: 0 2px 0 rgba(26, 26, 26, 0.04);
  box-sizing: border-box;
}
html[data-preset="sun-official"] .kpi::before { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 12px; }
html[data-preset="sun-official"] .kpi.k-red::before { background: var(--red); }
html[data-preset="sun-official"] .kpi.k-amber::before { background: var(--amber); }
html[data-preset="sun-official"] .kpi.k-teal::before { background: var(--teal); }
html[data-preset="sun-official"] .kpi.k-sand::before { background: var(--sand); }
html[data-preset="sun-official"] .kpi-label { font-size: var(--type-tiny); font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: var(--muted); margin: 0; min-height: 64px; }
html[data-preset="sun-official"] .kpi-value {
  font-family: var(--font-display), sans-serif;
  font-size: clamp(2.28rem, min(5vw, 8.889dvh), 6rem); /* 96px, v3-final (v1 88px) */
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1;
  color: var(--ink);
  margin: 18px 0 0 0;
}
html[data-preset="sun-official"] .kpi-delta { display: inline-flex; align-items: center; gap: 10px; font-size: var(--type-tiny); font-weight: 600; margin: 24px 0 0 0; }
html[data-preset="sun-official"] .kpi-delta.up { color: var(--teal); }
html[data-preset="sun-official"] .kpi-delta.down { color: var(--red-deep); }
html[data-preset="sun-official"] .kpi-target { font-size: var(--type-tiny); color: var(--muted); font-weight: 400; margin: 8px 0 0 0; }
@media (max-width: 1200px) {
  html[data-preset="sun-official"] .kpi-grid { grid-template-columns: repeat(2, 1fr); }
}

/* ---- 9. Big Stats ---- */
html[data-preset="sun-official"] .stats-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 80px; width: 100%; flex: 1; align-content: center; }
html[data-preset="sun-official"] .stat { border-left: 6px solid var(--line); padding-left: 52px; }
html[data-preset="sun-official"] .stat.is-accent { border-left-color: var(--red); }
html[data-preset="sun-official"] .stat-value {
  font-family: var(--font-display), sans-serif;
  font-size: clamp(2.73rem, min(8.125vw, 14.444dvh), 9.75rem); /* 156px, v3-final (v1 148px) */
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1;
  margin: 0;
  color: var(--ink);
}
html[data-preset="sun-official"] .stat.is-accent .stat-value { color: var(--red); }
html[data-preset="sun-official"] .stat-label { font-size: var(--type-small); color: var(--muted); line-height: 1.45; margin: 28px 0 0 0; max-width: 440px; }
@media (max-width: 1024px) {
  html[data-preset="sun-official"] .stats-row { grid-template-columns: 1fr; gap: 40px; }
}

/* ---- 10. Table ---- */
html[data-preset="sun-official"] .tbl { width: 100%; border-collapse: collapse; font-size: var(--type-small); }
html[data-preset="sun-official"] .tbl th {
  font-family: var(--font-display), sans-serif;
  text-align: left;
  font-size: var(--type-tiny);
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--muted);
  padding: 0 28px 22px 28px;
  border-bottom: 4px solid var(--ink);
}
html[data-preset="sun-official"] .tbl td { padding: 28px; border-bottom: 2px solid var(--line); font-weight: 400; }
html[data-preset="sun-official"] .tbl td:first-child { font-weight: 600; }
html[data-preset="sun-official"] .tbl .num { font-variant-numeric: tabular-nums; }
html[data-preset="sun-official"] .tbl tr.is-highlight td { background: var(--red-tint); font-weight: 600; }
html[data-preset="sun-official"] .tbl tr.is-highlight td:first-child { border-left: 6px solid var(--red); }
@media (max-width: 1024px) {
  html[data-preset="sun-official"] .tbl { display: block; overflow-x: auto; }
}

/* ---- 11. Quote ---- */
html[data-preset="sun-official"] .slide.s-quote { background: var(--bg-alt); justify-content: center; align-items: center; text-align: center; position: relative; overflow: hidden; }
html[data-preset="sun-official"] .quote-mark { width: 56px; height: 56px; margin-bottom: 48px; }
html[data-preset="sun-official"] .quote-ghost {
  position: absolute;
  right: -60px;
  bottom: -160px;
  font-size: clamp(11.2rem, min(33.333vw, 59.259dvh), 40rem); /* 640px, purely decorative */
  line-height: 1;
  color: var(--red-tint);
  font-family: var(--font-display), sans-serif;
  user-select: none;
  z-index: 0;
}
html[data-preset="sun-official"] .quote-mark, html[data-preset="sun-official"] .quote-text, html[data-preset="sun-official"] .quote-attr { position: relative; z-index: 1; }
html[data-preset="sun-official"] .quote-text {
  font-family: var(--font-display), sans-serif;
  font-size: clamp(1.86rem, min(3.229vw, 5.741dvh), 3.875rem); /* 62px, v3-final (v1 var(--type-quote)=56px) */
  font-weight: 600;
  line-height: 1.35;
  letter-spacing: -0.01em;
  max-width: 1440px;
  margin: 0;
  text-wrap: balance;
}
html[data-preset="sun-official"] .quote-attr { font-size: var(--type-small); color: var(--muted); margin: 52px 0 0 0; font-weight: 500; }

/* ---- 12. Team ---- */
html[data-preset="sun-official"] .team-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 60px; width: 100%; flex: 1; align-content: start; }
html[data-preset="sun-official"] .member { display: flex; flex-direction: column; align-items: flex-start; gap: 0; }
html[data-preset="sun-official"] .avatar {
  width: 168px;
  height: 168px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-display), sans-serif;
  font-size: clamp(1.8rem, min(2.5vw, 4.444dvh), 3rem); /* 48px */
  font-weight: 700;
  margin-bottom: 34px;
  box-shadow: inset 0 0 0 2px rgba(26, 26, 26, 0.06);
}
html[data-preset="sun-official"] .avatar.av-red { background: var(--red-tint); color: var(--red-deep); }
html[data-preset="sun-official"] .avatar.av-amber { background: var(--amber-tint); color: #8A6200; }
html[data-preset="sun-official"] .avatar.av-teal { background: var(--teal-tint); color: var(--teal); }
html[data-preset="sun-official"] .avatar.av-sand { background: var(--sand-tint); color: #6E6358; }
html[data-preset="sun-official"] .member-name { font-size: var(--type-body); font-weight: 700; margin: 0; }
html[data-preset="sun-official"] .member-role { font-size: var(--type-tiny); color: var(--muted); margin: 10px 0 0 0; line-height: 1.45; }
@media (max-width: 1200px) {
  html[data-preset="sun-official"] .team-grid { grid-template-columns: repeat(2, 1fr); }
}

/* ---- 13. Roadmap ---- */
html[data-preset="sun-official"] .timeline { display: grid; grid-template-columns: repeat(4, 1fr); gap: 56px; width: 100%; flex: 1; align-content: start; }
html[data-preset="sun-official"] .phase { position: relative; padding-top: 56px; }
html[data-preset="sun-official"] .phase::before { content: ""; position: absolute; top: 10px; left: 0; right: -56px; height: 4px; background: var(--line); }
html[data-preset="sun-official"] .phase:last-child::before { right: 0; }
html[data-preset="sun-official"] .phase::after { content: ""; position: absolute; top: 0; left: 0; width: 24px; height: 24px; border-radius: 50%; background: var(--bg); border: 5px solid var(--ink); box-sizing: border-box; }
html[data-preset="sun-official"] .phase.is-now::after { background: var(--red); border-color: var(--red); }
html[data-preset="sun-official"] .phase.is-now .phase-q { color: var(--red); }
html[data-preset="sun-official"] .phase-q { font-size: var(--type-tiny); font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: var(--muted); margin: 0; }
html[data-preset="sun-official"] .phase-name { font-family: var(--font-display), sans-serif; font-size: var(--type-body); font-weight: 700; margin: 18px 0 0 0; }
html[data-preset="sun-official"] .phase-desc { font-size: var(--type-tiny); color: var(--muted); line-height: 1.5; margin: 16px 0 0 0; }
html[data-preset="sun-official"] .phase-now-pill {
  display: inline-block;
  background: var(--red);
  color: #FFFFFF;
  font-size: clamp(1.08rem, min(1.25vw, 2.222dvh), 1.5rem); /* 24px */
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  border-radius: 999px;
  padding: 8px 20px;
  margin-top: 20px;
}
@media (max-width: 1024px) {
  html[data-preset="sun-official"] .timeline { grid-template-columns: repeat(2, 1fr); gap: 40px 56px; }
  html[data-preset="sun-official"] .phase::before { display: none; }
}

/* ---- 14. Process Flow ---- */
html[data-preset="sun-official"] .flow { display: flex; width: 100%; flex: 1; min-height: 0; align-items: center; }
html[data-preset="sun-official"] .flow-step { flex: 1; position: relative; display: flex; flex-direction: column; align-items: center; padding-top: 12px; }
html[data-preset="sun-official"] .flow-step::before { content: ""; position: absolute; top: 66px; left: 0; right: 0; height: 3px; background: var(--line); }
html[data-preset="sun-official"] .flow-step:first-child::before { left: 50%; }
html[data-preset="sun-official"] .flow-step:last-child::before { right: 50%; }
html[data-preset="sun-official"] .flow-step::after { content: ""; position: absolute; top: 59px; right: -8.5px; width: 17px; height: 17px; border-top: 3px solid var(--line); border-right: 3px solid var(--line); transform: rotate(45deg); }
html[data-preset="sun-official"] .flow-step:last-child::after { display: none; }
html[data-preset="sun-official"] .flow-node {
  position: relative;
  z-index: 1;
  width: 110px;
  height: 110px;
  border-radius: 50%;
  border: 3px solid var(--ink);
  background: #FFFFFF;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-display), sans-serif;
  font-weight: 700;
  font-size: clamp(1.35rem, min(1.875vw, 3.333dvh), 2.25rem); /* 36px */
  color: var(--ink);
}
html[data-preset="sun-official"] .flow-step.is-accent .flow-node { background: var(--red); border-color: var(--red); color: #FFFFFF; }
html[data-preset="sun-official"] .flow-name {
  font-family: var(--font-display), sans-serif;
  font-size: clamp(1.275rem, min(1.771vw, 3.148dvh), 2.125rem); /* 34px */
  font-weight: 700;
  margin: 34px 0 0;
  text-align: center;
}
html[data-preset="sun-official"] .flow-desc { font-size: var(--type-tiny); color: var(--muted); line-height: 1.45; text-align: center; margin: 14px 0 0; max-width: 82%; }
html[data-preset="sun-official"] .flow-step .phase-now-pill { margin-top: 18px; }
@media (max-width: 1024px) {
  html[data-preset="sun-official"] .flow { flex-direction: column; gap: 32px; align-items: stretch; }
  html[data-preset="sun-official"] .flow-step::before, html[data-preset="sun-official"] .flow-step::after { display: none; }
}

/* ---- 15. Workflow (swimlane) ---- */
html[data-preset="sun-official"] .lanes { display: grid; grid-template-columns: 230px repeat(4, 1fr); gap: 18px; width: 100%; flex: 1; min-height: 0; align-content: center; }
html[data-preset="sun-official"] .lane-phase { font-size: var(--type-tiny); font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: var(--red-deep); border-bottom: 3px solid var(--ink); padding: 0 4px 16px; margin: 0; align-self: end; }
html[data-preset="sun-official"] .lane-corner { border-bottom: 3px solid var(--ink); }
html[data-preset="sun-official"] .lane-role {
  display: flex;
  align-items: center;
  gap: 16px;
  font-family: var(--font-display), sans-serif;
  font-size: clamp(1.125rem, min(1.562vw, 2.778dvh), 1.875rem); /* 30px */
  font-weight: 700;
  margin: 0;
  padding-right: 12px;
}
html[data-preset="sun-official"] .lane-role .dot { width: 16px; height: 16px; border-radius: 50%; background: var(--sand); flex: none; }
html[data-preset="sun-official"] .lane-role .dot.is-red { background: var(--red); }
html[data-preset="sun-official"] .lane-role .dot.is-amber { background: var(--amber); }
html[data-preset="sun-official"] .lane-role .dot.is-teal { background: var(--teal); }
html[data-preset="sun-official"] .lane-cell {
  background: #FFFFFF;
  border: 2px solid var(--line);
  border-radius: 16px;
  padding: 26px 26px 24px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 8px;
  min-height: clamp(4.95rem, min(6.875vw, 12.222dvh), 8.25rem); /* 132px — the only 23-component grid that
    stacks multiple fixed-height rows, so unlike other fixed dimensions (avatar/flow-node circles) this
    one must scale with viewport or it collides with the footer at short heights (confirmed at 1366×768) */
  box-sizing: border-box;
}
html[data-preset="sun-official"] .lane-cell .lc-t { font-size: var(--type-small); font-weight: 600; margin: 0; line-height: 1.3; } /* was a stray un-clamped 26px literal — same value as --type-small, now scales correctly */
html[data-preset="sun-official"] .lane-cell .lc-s { font-size: var(--type-tiny); color: var(--muted); margin: 0; line-height: 1.35; }
html[data-preset="sun-official"] .lane-cell.is-active { border-color: var(--red); background: var(--red-tint); }
html[data-preset="sun-official"] .lane-cell.is-active .lc-t { color: var(--red-deep); }
html[data-preset="sun-official"] .lane-cell.is-empty { background: transparent; border-style: dashed; }
@media (max-width: 1200px) {
  html[data-preset="sun-official"] .lanes { grid-template-columns: 1fr; }
  html[data-preset="sun-official"] .lane-phase { display: none; }
}

/* ---- 16. Diagram (system architecture) ---- */
html[data-preset="sun-official"] .arch { display: flex; flex-direction: column; justify-content: center; width: 100%; flex: 1; min-height: 0; }
html[data-preset="sun-official"] .arch-layer { display: grid; grid-template-columns: 260px 1fr; gap: 44px; align-items: center; }
html[data-preset="sun-official"] .arch-name { font-family: var(--font-display), sans-serif; font-size: clamp(1.2rem, min(1.667vw, 2.963dvh), 2rem); font-weight: 700; margin: 0; } /* 32px */
html[data-preset="sun-official"] .arch-note { font-size: var(--type-tiny); color: var(--muted); margin: 8px 0 0; line-height: 1.4; }
html[data-preset="sun-official"] .arch-blocks { display: flex; gap: 22px; }
html[data-preset="sun-official"] .arch-block {
  flex: 1;
  background: #FFFFFF;
  border: 2px solid var(--line);
  border-radius: 16px;
  padding: 30px 24px;
  font-size: clamp(1.215rem, min(1.406vw, 2.5dvh), 1.688rem); /* 27px */
  font-weight: 600;
  text-align: center;
  line-height: 1.25;
}
html[data-preset="sun-official"] .arch-block.is-accent { border-color: var(--red); background: var(--red-tint); color: var(--red-deep); }
html[data-preset="sun-official"] .arch-block.is-dim { background: var(--sand-tint); border-color: var(--sand); }
html[data-preset="sun-official"] .arch-join { display: grid; grid-template-columns: 260px 1fr; gap: 44px; height: 64px; align-items: center; }
html[data-preset="sun-official"] .arch-join .aj { display: flex; justify-content: space-evenly; color: var(--sand); font-size: clamp(1.125rem, min(1.562vw, 2.778dvh), 1.875rem); font-weight: 700; line-height: 1; } /* 30px */
@media (max-width: 1024px) {
  html[data-preset="sun-official"] .arch-layer, html[data-preset="sun-official"] .arch-join { grid-template-columns: 1fr; gap: 16px; }
  html[data-preset="sun-official"] .arch-blocks { flex-wrap: wrap; }
}

/* ---- 17. Photos (image mosaic) ---- */
html[data-preset="sun-official"] .photo-grid { display: grid; grid-template-columns: 1.4fr 1fr; grid-template-rows: 1fr 1fr; gap: 36px; width: 100%; flex: 1; min-height: 0; }
html[data-preset="sun-official"] .photo-main { grid-row: 1 / 3; }
html[data-preset="sun-official"] .photo-caption { font-size: var(--type-tiny); color: var(--muted); margin: 24px 0 0 0; }
@media (max-width: 1024px) {
  html[data-preset="sun-official"] .photo-grid { grid-template-columns: 1fr; grid-template-rows: none; }
  html[data-preset="sun-official"] .photo-main { grid-row: auto; }
}

/* ---- 18. Image + Text (split) ---- */
html[data-preset="sun-official"] .split-img { display: grid; grid-template-columns: 1.05fr 1fr; gap: 80px; width: 100%; flex: 1; min-height: 0; align-items: stretch; }
html[data-preset="sun-official"] .split-img.is-flip { grid-template-columns: 1fr 1.05fr; }
html[data-preset="sun-official"] .split-img.is-flip .sun-image-layout { order: 2; }
html[data-preset="sun-official"] .split-img.is-flip .split-copy { order: 1; }
html[data-preset="sun-official"] .split-copy { display: flex; flex-direction: column; justify-content: center; }
html[data-preset="sun-official"] .split-copy .eyebrow { font-size: var(--type-tiny); font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: var(--red-deep); margin: 0 0 22px; }
html[data-preset="sun-official"] .split-copy h3 {
  font-family: var(--font-display), sans-serif;
  font-size: clamp(1.56rem, min(2.708vw, 4.815dvh), 3.25rem); /* 52px */
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.12;
  margin: 0;
}
html[data-preset="sun-official"] .split-copy .lead { font-size: var(--type-small); line-height: 1.6; color: var(--muted); margin: 30px 0 0; max-width: 600px; }
html[data-preset="sun-official"] .split-copy .mini-list { list-style: none; margin: 38px 0 0; padding: 0; display: flex; flex-direction: column; gap: 22px; }
html[data-preset="sun-official"] .split-copy .mini-list li { display: flex; gap: 20px; align-items: baseline; font-size: var(--type-small); color: var(--ink); line-height: 1.4; }
html[data-preset="sun-official"] .split-copy .mini-list .m { color: var(--red); font-weight: 700; flex: none; }
@media (max-width: 1024px) {
  html[data-preset="sun-official"] .split-img, html[data-preset="sun-official"] .split-img.is-flip { grid-template-columns: 1fr; gap: 32px; }
  html[data-preset="sun-official"] .split-img.is-flip .sun-image-layout, html[data-preset="sun-official"] .split-img.is-flip .split-copy { order: initial; }
}

/* ---- 19. Image Columns ---- */
html[data-preset="sun-official"] .img-cols { display: grid; grid-template-columns: repeat(3, 1fr); gap: 44px; width: 100%; flex: 1; min-height: 0; }
html[data-preset="sun-official"] .img-card { display: flex; flex-direction: column; min-height: 0; }
html[data-preset="sun-official"] .img-card .sun-image-layout { flex: 1; min-height: 0; margin-bottom: 28px; }
html[data-preset="sun-official"] .img-card .cap-h { font-family: var(--font-display), sans-serif; font-size: var(--type-body); font-weight: 700; margin: 0; display: flex; align-items: baseline; gap: 16px; }
html[data-preset="sun-official"] .img-card .cap-h .idx { color: var(--red); font-size: var(--type-small); }
html[data-preset="sun-official"] .img-card .cap-p { font-size: var(--type-tiny); color: var(--muted); line-height: 1.5; margin: 12px 0 0; }
@media (max-width: 1024px) {
  html[data-preset="sun-official"] .img-cols { grid-template-columns: 1fr; gap: 32px; }
}

/* ---- 20. Image Banner ---- */
html[data-preset="sun-official"] .banner-grid { display: grid; grid-template-rows: 1fr auto; gap: 0; width: 100%; flex: 1; min-height: 0; }
html[data-preset="sun-official"] .banner-strip { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0; border-top: 4px solid var(--ink); }
html[data-preset="sun-official"] .banner-cell { padding: 30px 40px 4px 0; }
html[data-preset="sun-official"] .banner-cell + .banner-cell { padding-left: 40px; border-left: 2px solid var(--line); }
html[data-preset="sun-official"] .banner-cell .bc-k { font-family: var(--font-display), sans-serif; font-size: var(--type-body); font-weight: 700; margin: 0; }
html[data-preset="sun-official"] .banner-cell .bc-p { font-size: var(--type-tiny); color: var(--muted); line-height: 1.5; margin: 10px 0 0; }
@media (max-width: 1024px) {
  html[data-preset="sun-official"] .banner-strip { grid-template-columns: 1fr; }
  html[data-preset="sun-official"] .banner-cell + .banner-cell { border-left: none; border-top: 2px solid var(--line); padding-left: 0; padding-top: 20px; }
}

/* ---- 21. Feature (full-bleed) ---- */
html[data-preset="sun-official"] .slide.s-feature { padding: 0; }
html[data-preset="sun-official"] .slide.s-feature .bg-art { display: none; }
html[data-preset="sun-official"] .feature-img { position: absolute; inset: 0; width: 100%; height: 100%; display: block; z-index: 0; }
html[data-preset="sun-official"] .feature-shade { position: absolute; inset: 0; z-index: 1; background: linear-gradient(0deg, rgba(22, 8, 4, 0.9) 0%, rgba(22, 8, 4, 0.35) 44%, rgba(22, 8, 4, 0) 72%); }
html[data-preset="sun-official"] .feature-cap { position: absolute; left: var(--pad-x); right: var(--pad-x); bottom: 104px; z-index: 2; color: #FFFFFF; }
html[data-preset="sun-official"] .feature-cap .kicker { color: rgba(255, 255, 255, 0.88); }
html[data-preset="sun-official"] .feature-cap .kicker .ast { filter: brightness(0) invert(1); }
html[data-preset="sun-official"] .feature-cap h2 {
  font-family: var(--font-display), sans-serif;
  font-size: clamp(2.09rem, min(4.583vw, 8.148dvh), 5.5rem); /* 88px */
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.04;
  margin: 22px 0 0;
  max-width: 1300px;
}
html[data-preset="sun-official"] .feature-cap .feature-sub { font-size: var(--type-body); color: rgba(255, 255, 255, 0.85); margin: 26px 0 0; max-width: 1040px; line-height: 1.5; }
html[data-preset="sun-official"] .slide.s-feature .foot-logo { filter: brightness(0) invert(1); z-index: 2; }
html[data-preset="sun-official"] .slide.s-feature .pageno { color: rgba(255, 255, 255, 0.82); z-index: 2; }

/* ---- 22. Guide (template/brand reference) ---- */
html[data-preset="sun-official"] .guide-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 110px; width: 100%; flex: 1; align-content: start; }
html[data-preset="sun-official"] .guide-h { font-family: var(--font-display), sans-serif; font-size: var(--type-small); font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; margin: 0 0 30px 0; }
html[data-preset="sun-official"] .swatches { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }
html[data-preset="sun-official"] .swatch { border: 2px solid var(--line); border-radius: 12px; overflow: hidden; }
html[data-preset="sun-official"] .swatch-chip { height: 110px; }
html[data-preset="sun-official"] .swatch-meta { padding: 16px 20px; font-size: var(--type-tiny); font-weight: 600; }
html[data-preset="sun-official"] .swatch-hex { display: block; color: var(--muted); font-weight: 400; margin-top: 4px; }
html[data-preset="sun-official"] .spec { border-top: 4px solid var(--ink); padding-top: 32px; margin-bottom: 44px; }
html[data-preset="sun-official"] .spec-name { font-family: var(--font-display), sans-serif; font-size: var(--type-subtitle); font-weight: 700; margin: 0; }
html[data-preset="sun-official"] .spec-note { font-size: var(--type-tiny); color: var(--muted); margin: 14px 0 0 0; line-height: 1.5; }
@media (max-width: 1024px) {
  html[data-preset="sun-official"] .guide-grid { grid-template-columns: 1fr; gap: 40px; }
}

/* ---- 23. Thank You ---- */
html[data-preset="sun-official"] .slide.thanks { justify-content: center; align-items: center; text-align: center; }
html[data-preset="sun-official"] .thanks-title {
  font-family: var(--font-display), sans-serif;
  font-size: clamp(2.45rem, min(7.292vw, 12.963dvh), 8.75rem); /* 140px */
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin: 0;
}
html[data-preset="sun-official"] .thanks-ast { width: 44px; height: 44px; margin-top: 18px; }
html[data-preset="sun-official"] .thanks-contact { font-size: var(--type-body); color: var(--muted); margin: 56px 0 0 0; }
html[data-preset="sun-official"][data-variant="editorial"] .slide.s-brand .thanks-contact { color: rgba(255, 255, 255, 0.75); }

/* ---- Mobile safety net (phone-portrait, ~390-480px) ---- */
/* CSS Grid/Flex items default to min-width:auto, so a track declared "1fr" (or a repeat(N,1fr)) can
   still be forced wider than the viewport by a child's min-content (e.g. a chart's flex bar-groups, or
   a card's own content) — reset it so every track can actually shrink to its share. This list is every
   multi-column grid/flex container in this file (systematically re-derived from every `display: grid`
   and `display: flex` declaration above with 2+ columns/items, not an empirically-observed subset —
   an earlier pass missed `.timeline` this way and shipped a real ~15% overflow on Roadmap at 390px,
   caught by review, not by the original render check because `.slide`'s own `overflow:hidden` clips
   the visual result while `scrollWidth` still reports it). */
html[data-preset="sun-official"] .data-grid > *,
html[data-preset="sun-official"] .two-col > *,
html[data-preset="sun-official"] .kpi-grid > *,
html[data-preset="sun-official"] .team-grid > *,
html[data-preset="sun-official"] .stats-row > *,
html[data-preset="sun-official"] .retro-grid > *,
html[data-preset="sun-official"] .guide-grid > *,
html[data-preset="sun-official"] .agenda-grid > *,
html[data-preset="sun-official"] .img-cols > *,
html[data-preset="sun-official"] .photo-grid > *,
html[data-preset="sun-official"] .timeline > *,
html[data-preset="sun-official"] .lanes > *,
html[data-preset="sun-official"] .arch-layer > *,
html[data-preset="sun-official"] .arch-join > *,
html[data-preset="sun-official"] .split-img > *,
html[data-preset="sun-official"] .banner-strip > *,
html[data-preset="sun-official"] .swatches > *,
html[data-preset="sun-official"] .bar-group {
  min-width: 0;
}
@media (max-width: 480px) {
  /* Some grids intentionally stay at 2 columns down to tablet width (1024-1200px) — phones need one
     more step to a single column. min-width:0 alone only fixes track-blowout (a grid forced wider
     than its 1fr share); it does NOT fix a 2-column card being too narrow for its own prose to wrap
     without overflowing — that needs an actual column drop. Confirmed by review: .timeline was
     originally left off this list and still overflowed (individual .phase-desc text, not the grid
     track) even after the min-width:0 fix below. */
  html[data-preset="sun-official"] .kpi-grid,
  html[data-preset="sun-official"] .team-grid,
  html[data-preset="sun-official"] .timeline,
  html[data-preset="sun-official"] .swatches {
    grid-template-columns: 1fr;
  }
  /* Chart bar-groups: min-width:0 stops the grid/flex blowout, but 5 groups still need every spare
     px for their number+year labels at this width — reclaim it from the gap rather than the tracks. */
  html[data-preset="sun-official"] .bars {
    gap: 12px;
  }
}
```

## Component Catalog

Same menu logic as the PPTX side's `layouts.md`: this is a picker, not a fixed 23-slide deck. Choose
per content shape; a typical deck uses 8-12 of these. Each entry: when to use it, the classes it needs,
narrow-viewport behavior, and copy-pasteable markup (already flattened per the Structural note above).

**Renumber `.pageno` when generating.** Each snippet's `<span class="pageno">NN</span>` shows its
position in this 23-item catalog (01-23), not a deck page number. When `data-pageno="true"` and the
chosen subset/order differs from the catalog (the normal case — see "8-12 of these" above), replace
each `NN` with its actual 1-based position in the *generated* deck, not the catalog number shown here.

### 1. Cover

**When:** Always the first slide. **Classes:** `.slide.cover.s-brand`. **Narrow-viewport:** cover title
wraps naturally (no grid to reflow).

```html
<section class="slide cover s-brand">
  <div class="bg-art bg-art--cover" aria-hidden="true"></div>
  <img class="brand-logo reveal d1" src="{{SUN_LOGO}}" alt="Sun*">
  <div>
    <p class="kicker reveal d2"><img class="ast" src="{{SUN_ASTERISK}}" alt="">Client Proposal · 12 June 2026</p>
    <h1 class="cover-title reveal d3">Presentation Title Goes Here</h1>
    <p class="cover-sub reveal d4">A one-line description of what this deck covers</p>
  </div>
  <div class="cover-meta reveal d5">
    <span>Presenter Name</span><span>·</span><span>Division / Team</span>
  </div>
</section>
```

### 2. Agenda

**When:** Right after the cover, if the deck has 3+ sections. **Classes:** `.agenda-grid`. **Narrow:**
grid collapses to a single column at ≤1024px.

```html
<section class="slide">
  <div class="head-row">
    <div class="head">
      <p class="kicker reveal d1"><img class="ast" src="{{SUN_ASTERISK}}" alt="">Overview<span class="k-sep"></span></p>
      <h2 class="title reveal d2">Agenda</h2>
    </div>
    <span class="badge reveal d2"><strong>Q1</strong>2026</span>
  </div>
  <div class="agenda-grid">
    <p class="body-text muted reveal d3">Replace these items with the sections of your presentation. Five to six items fit comfortably.</p>
    <ol class="agenda-list">
      <li class="agenda-item reveal d2"><span class="agenda-num">01</span><span>Background &amp; Objectives</span></li>
      <li class="agenda-item reveal d3"><span class="agenda-num">02</span><span>Our Approach</span></li>
      <li class="agenda-item reveal d4"><span class="agenda-num">03</span><span>Results &amp; Key Figures</span></li>
      <li class="agenda-item reveal d5"><span class="agenda-num">04</span><span>Team &amp; Roadmap</span></li>
      <li class="agenda-item reveal d6"><span class="agenda-num">05</span><span>Next Steps</span></li>
    </ol>
  </div>
  <img class="foot-logo" src="{{SUN_LOGO}}" alt="Sun*">
  <span class="pageno">02</span>
</section>
```

### 3. Section (divider)

**When:** Opening a new part of the deck. **Classes:** `.slide.divider.s-brand`. **Narrow:** giant
number/title wrap naturally.

```html
<section class="slide divider s-brand">
  <div class="bg-art bg-art--divider" aria-hidden="true">
    <span class="ba-dot ba-dot-a"></span><span class="ba-bar"></span>
  </div>
  <p class="divider-num reveal d1">01</p>
  <h2 class="divider-title reveal d2">Section Title Goes Here</h2>
  <p class="divider-sub muted reveal d3">An optional one-sentence summary of what this section will cover.</p>
  <div class="rule-red reveal d4"></div>
  <img class="foot-logo" src="{{SUN_LOGO}}" alt="Sun*">
  <span class="pageno">03</span>
</section>
```

### 4. One Column

**When:** A single idea explained in prose, 2-3 supporting bullets. **Classes:** `.bullets`. **Narrow:**
no grid — reflows naturally.

```html
<section class="slide">
  <div class="head-row">
    <div class="head">
      <p class="kicker reveal d1"><img class="ast" src="{{SUN_ASTERISK}}" alt="">Section 01<span class="k-sep"></span></p>
      <h2 class="title reveal d2">One-Column Content Slide</h2>
    </div>
    <span class="badge reveal d2"><strong>Q1</strong>2026</span>
  </div>
  <p class="body-text lede reveal d3">Use this layout for a single idea explained in prose. Keep the paragraph short — two to three lines at most.</p>
  <ul class="bullets">
    <li class="reveal d3"><span class="bullet-mark">✱</span><span>First supporting point, written as one complete and concise sentence.</span></li>
    <li class="reveal d4"><span class="bullet-mark">✱</span><span>Second supporting point — parallel in structure to the first.</span></li>
    <li class="reveal d5"><span class="bullet-mark">✱</span><span>Third supporting point. Three is plenty.</span></li>
  </ul>
  <img class="foot-logo" src="{{SUN_LOGO}}" alt="Sun*">
  <span class="pageno">04</span>
</section>
```

### 5. Two Column

**When:** Before/after, problem/solution, paired comparison. **Classes:** `.two-col`. **Narrow:**
stacks to 1 column at ≤1024px.

```html
<section class="slide">
  <div class="head-row">
    <div class="head">
      <p class="kicker reveal d1"><img class="ast" src="{{SUN_ASTERISK}}" alt="">Section 01<span class="k-sep"></span></p>
      <h2 class="title reveal d2">Two-Column Content Slide</h2>
    </div>
    <span class="badge reveal d2"><strong>Q1</strong>2026</span>
  </div>
  <div class="two-col">
    <div class="col reveal d3">
      <h3 class="col-head">Current State</h3>
      <p class="col-strong">A short bold lead sentence framing this column.</p>
      <p>Body copy for the first column. Use for before/after, problem/solution, or any paired comparison.</p>
    </div>
    <div class="col reveal d4">
      <h3 class="col-head">Proposed State</h3>
      <p class="col-strong">A short bold lead sentence framing this column.</p>
      <p>Body copy for the second column. Keep both columns visually balanced.</p>
    </div>
  </div>
  <img class="foot-logo" src="{{SUN_LOGO}}" alt="Sun*">
  <span class="pageno">05</span>
</section>
```

### 6. Done / Next

**When:** Sprint/quarter retros, status reviews. **Classes:** `.retro-grid`. **Narrow:** stacks to 1
column at ≤1024px.

```html
<section class="slide">
  <div class="head-row">
    <div class="head">
      <p class="kicker reveal d1"><img class="ast" src="{{SUN_ASTERISK}}" alt="">Section 01<span class="k-sep"></span></p>
      <h2 class="title reveal d2">Review &amp; Next Actions</h2>
    </div>
    <span class="badge reveal d2"><strong>Q1</strong>2026</span>
  </div>
  <div class="retro-grid">
    <div class="retro-col reveal d3">
      <h3 class="retro-h">Done This Quarter</h3>
      <ul class="retro-list">
        <li><span class="retro-dot">✱</span><span>Completed action one — state the outcome, not just the activity.</span></li>
        <li><span class="retro-dot">✱</span><span>Completed action two, with the measurable result it produced.</span></li>
        <li><span class="retro-dot">✱</span><span>Completed action three.</span></li>
      </ul>
    </div>
    <div class="retro-col is-next reveal d4">
      <h3 class="retro-h">Next Quarter</h3>
      <ul class="retro-list">
        <li><span class="retro-dot">→</span><span>Planned action one, phrased as a commitment with an owner.</span></li>
        <li><span class="retro-dot">→</span><span>Planned action two — parallel in structure to the Done column.</span></li>
        <li><span class="retro-dot">→</span><span>Planned action three, with its target date or milestone.</span></li>
      </ul>
    </div>
  </div>
  <img class="foot-logo" src="{{SUN_LOGO}}" alt="Sun*">
  <span class="pageno">06</span>
</section>
```

### 7. Data

**When:** One headline metric + a small trend chart. **Classes:** `.data-grid`, `.chart`, `.bars`.
**Narrow:** stacks to 1 column at ≤1024px. **Animated:** bars grow from 0 via `sun-official-bar-grow`
when `data-anim="true"`.

```html
<section class="slide">
  <div class="head-row">
    <div class="head">
      <p class="kicker reveal d1"><img class="ast" src="{{SUN_ASTERISK}}" alt="">Section 02<span class="k-sep"></span></p>
      <h2 class="title reveal d2">Key Figures &amp; Chart</h2>
    </div>
    <span class="badge reveal d2"><strong>Q1</strong>2026</span>
  </div>
  <div class="data-grid">
    <div class="reveal d3">
      <p class="big-number">128%</p>
      <p class="big-number-caption">One sentence explaining what this headline figure means and why it matters.</p>
      <p class="big-number-note">Source: internal data, FY2025</p>
    </div>
    <div class="chart reveal d3">
      <div class="bars">
        <div class="bar-group"><span class="bar-value">42</span><div class="bar" style="height: 30%;"></div><span class="bar-label">2022</span></div>
        <div class="bar-group"><span class="bar-value">58</span><div class="bar" style="height: 42%;"></div><span class="bar-label">2023</span></div>
        <div class="bar-group"><span class="bar-value">76</span><div class="bar" style="height: 55%;"></div><span class="bar-label">2024</span></div>
        <div class="bar-group"><span class="bar-value">98</span><div class="bar" style="height: 71%;"></div><span class="bar-label">2025</span></div>
        <div class="bar-group"><span class="bar-value">138</span><div class="bar is-accent" style="height: 100%;"></div><span class="bar-label">2026</span></div>
      </div>
      <p class="chart-caption">Chart caption — unit, scope, and source in one line.</p>
    </div>
  </div>
  <img class="foot-logo" src="{{SUN_LOGO}}" alt="Sun*">
  <span class="pageno">07</span>
</section>
```

### 8. KPI Dashboard

**When:** 3-4 tracked metrics with deltas/targets. **Classes:** `.kpi-grid`. **Narrow:** 2 columns at
≤1200px.

```html
<section class="slide">
  <div class="head-row">
    <div class="head">
      <p class="kicker reveal d1"><img class="ast" src="{{SUN_ASTERISK}}" alt="">Section 02<span class="k-sep"></span></p>
      <h2 class="title reveal d2">KPI Dashboard</h2>
    </div>
    <span class="badge reveal d2"><strong>Q1</strong>2026</span>
  </div>
  <div class="kpi-grid">
    <div class="kpi k-red reveal d2">
      <p class="kpi-label">Revenue vs Target</p><p class="kpi-value">99.9%</p>
      <p class="kpi-delta up">▲ 4.2% vs last quarter</p><p class="kpi-target">Target: 100%</p>
    </div>
    <div class="kpi k-amber reveal d3">
      <p class="kpi-label">CSS Score</p><p class="kpi-value">93</p>
      <p class="kpi-delta up">▲ 16% vs same period</p><p class="kpi-target">Target: 86</p>
    </div>
    <div class="kpi k-teal reveal d4">
      <p class="kpi-label">Normal KPI Project Ratio</p><p class="kpi-value">88.1%</p>
      <p class="kpi-delta up">▲ 2.1% vs last quarter</p><p class="kpi-target">Target: 86%</p>
    </div>
    <div class="kpi k-sand reveal d5">
      <p class="kpi-label">Projects Applying AI-DD</p><p class="kpi-value">9</p>
      <p class="kpi-delta down">▼ 3 below plan</p><p class="kpi-target">Target: 12</p>
    </div>
  </div>
  <img class="foot-logo" src="{{SUN_LOGO}}" alt="Sun*">
  <span class="pageno">08</span>
</section>
```

### 9. Big Stats

**When:** 3 headline numbers, no chart needed. **Classes:** `.stats-row`. **Narrow:** stacks to 1
column at ≤1024px.

```html
<section class="slide">
  <div class="head-row">
    <div class="head">
      <p class="kicker reveal d1"><img class="ast" src="{{SUN_ASTERISK}}" alt="">Section 02<span class="k-sep"></span></p>
      <h2 class="title reveal d2">Headline Numbers</h2>
    </div>
    <span class="badge reveal d2"><strong>Q1</strong>2026</span>
  </div>
  <div class="stats-row">
    <div class="stat reveal d2"><p class="stat-value">812</p><p class="stat-label">First metric — unit and a short description of what it measures.</p></div>
    <div class="stat is-accent reveal d3"><p class="stat-value">72%</p><p class="stat-label">The hero metric goes in the middle, in Sun* Red.</p></div>
    <div class="stat reveal d4"><p class="stat-value">494</p><p class="stat-label">Third metric — keep all three captions roughly the same length.</p></div>
  </div>
  <img class="foot-logo" src="{{SUN_LOGO}}" alt="Sun*">
  <span class="pageno">09</span>
</section>
```

### 10. Table

**When:** Structured comparison across several rows/columns. **Classes:** `.tbl`. **Narrow:**
horizontal scroll at ≤1024px (never reflows a table into cards — keep it simple).

```html
<section class="slide">
  <div class="head-row">
    <div class="head">
      <p class="kicker reveal d1"><img class="ast" src="{{SUN_ASTERISK}}" alt="">Section 02<span class="k-sep"></span></p>
      <h2 class="title reveal d2">Comparison Table</h2>
    </div>
    <span class="badge reveal d2"><strong>Q1</strong>2026</span>
  </div>
  <table class="tbl reveal d3">
    <thead><tr><th>Item</th><th>Plan A</th><th>Plan B</th><th class="num">Cost</th><th class="num">Timeline</th></tr></thead>
    <tbody>
      <tr><td>Row label one</td><td>Description</td><td>Description</td><td class="num">$12,000</td><td class="num">4 weeks</td></tr>
      <tr class="is-highlight"><td>Recommended row</td><td>Description</td><td>Description</td><td class="num">$18,500</td><td class="num">6 weeks</td></tr>
      <tr><td>Row label three</td><td>Description</td><td>Description</td><td class="num">$24,000</td><td class="num">8 weeks</td></tr>
      <tr><td>Row label four</td><td>Description</td><td>Description</td><td class="num">$31,000</td><td class="num">10 weeks</td></tr>
    </tbody>
  </table>
  <img class="foot-logo" src="{{SUN_LOGO}}" alt="Sun*">
  <span class="pageno">10</span>
</section>
```

### 11. Quote

**When:** Customer quote, guiding principle, one memorable line. **Classes:** `.s-quote`. **Narrow:**
`.quote-ghost` decorative glyph clips via `overflow:hidden` on the slide — safe at any width.

```html
<section class="slide s-quote">
  <span class="quote-ghost">✱</span>
  <img class="quote-mark reveal d1" src="{{SUN_ASTERISK}}" alt="">
  <p class="quote-text reveal d2">"Use this layout for a customer quote, a guiding principle, or the one sentence you want the room to remember."</p>
  <p class="quote-attr reveal d3">Name Surname — Role, Company</p>
  <img class="foot-logo" src="{{SUN_LOGO}}" alt="Sun*">
  <span class="pageno">11</span>
</section>
```

### 12. Team

**When:** Introducing project team / org. **Classes:** `.team-grid`. **Narrow:** 2 columns at ≤1200px.

```html
<section class="slide">
  <div class="head-row">
    <div class="head">
      <p class="kicker reveal d1"><img class="ast" src="{{SUN_ASTERISK}}" alt="">Section 03<span class="k-sep"></span></p>
      <h2 class="title reveal d2">Project Team</h2>
    </div>
    <span class="badge reveal d2"><strong>Q1</strong>2026</span>
  </div>
  <div class="team-grid">
    <div class="member reveal d2"><div class="avatar av-red"><span>NA</span></div><p class="member-name">Name A</p><p class="member-role">Project Manager</p></div>
    <div class="member reveal d3"><div class="avatar av-amber"><span>NB</span></div><p class="member-name">Name B</p><p class="member-role">Tech Lead</p></div>
    <div class="member reveal d4"><div class="avatar av-teal"><span>NC</span></div><p class="member-name">Name C</p><p class="member-role">UI/UX Designer</p></div>
    <div class="member reveal d5"><div class="avatar av-sand"><span>ND</span></div><p class="member-name">Name D</p><p class="member-role">QA Engineer</p></div>
  </div>
  <img class="foot-logo" src="{{SUN_LOGO}}" alt="Sun*">
  <span class="pageno">12</span>
</section>
```

### 13. Roadmap

**When:** Multi-quarter plan with a "we are here" marker. **Classes:** `.timeline`. **Narrow:** 2
columns at ≤1024px (connecting line hidden), 1 column at ≤480px so phase descriptions have room to wrap.

```html
<section class="slide">
  <div class="head-row">
    <div class="head">
      <p class="kicker reveal d1"><img class="ast" src="{{SUN_ASTERISK}}" alt="">Section 03<span class="k-sep"></span></p>
      <h2 class="title reveal d2">Roadmap</h2>
    </div>
    <span class="badge reveal d2"><strong>Q1</strong>2026</span>
  </div>
  <div class="timeline">
    <div class="phase reveal d2"><p class="phase-q">Q3 2026</p><p class="phase-name">Discovery</p><p class="phase-desc">Requirements, user research, and scope definition.</p></div>
    <div class="phase is-now reveal d3"><p class="phase-q">Q4 2026</p><p class="phase-name">Design &amp; Build</p><p class="phase-desc">Design sprints and core feature development.</p><span class="phase-now-pill">We are here</span></div>
    <div class="phase reveal d4"><p class="phase-q">Q1 2027</p><p class="phase-name">Beta Release</p><p class="phase-desc">Closed beta with pilot customers; QA hardening.</p></div>
    <div class="phase reveal d5"><p class="phase-q">Q2 2027</p><p class="phase-name">Launch</p><p class="phase-desc">Public release and handover to operations.</p></div>
  </div>
  <img class="foot-logo" src="{{SUN_LOGO}}" alt="Sun*">
  <span class="pageno">13</span>
</section>
```

### 14. Process Flow

**When:** A linear sequence of steps (discover → deliver). **Classes:** `.flow`. **Narrow:** stacks
vertically at ≤1024px, connector lines hidden.

```html
<section class="slide">
  <div class="head-row">
    <div class="head">
      <p class="kicker reveal d1"><img class="ast" src="{{SUN_ASTERISK}}" alt="">Section 03<span class="k-sep"></span></p>
      <h2 class="title reveal d2">Process Flow</h2>
    </div>
    <span class="badge reveal d2"><strong>Q1</strong>2026</span>
  </div>
  <div class="flow">
    <div class="flow-step reveal d2"><div class="flow-node">01</div><p class="flow-name">Discover</p><p class="flow-desc">Gather requirements and align on goals with stakeholders.</p></div>
    <div class="flow-step reveal d3"><div class="flow-node">02</div><p class="flow-name">Define</p><p class="flow-desc">Scope, estimate, and agree on the delivery plan.</p></div>
    <div class="flow-step is-accent reveal d4"><div class="flow-node">03</div><p class="flow-name">Build</p><p class="flow-desc">Design and develop in short, reviewable sprints.</p></div>
    <div class="flow-step reveal d5"><div class="flow-node">04</div><p class="flow-name">Verify</p><p class="flow-desc">Test against acceptance criteria with QA and the client.</p></div>
    <div class="flow-step reveal d6"><div class="flow-node">05</div><p class="flow-name">Deliver</p><p class="flow-desc">Release, hand over, and agree on the next iteration.</p></div>
  </div>
  <img class="foot-logo" src="{{SUN_LOGO}}" alt="Sun*">
  <span class="pageno">14</span>
</section>
```

### 15. Workflow (swimlane)

**When:** Who-does-what across phases (client/vendor/QA roles). **Classes:** `.lanes`. **Narrow:**
collapses to a single column at ≤1200px (phase header row hidden — rely on the lc-t/lc-s text).

```html
<section class="slide">
  <div class="head-row">
    <div class="head">
      <p class="kicker reveal d1"><img class="ast" src="{{SUN_ASTERISK}}" alt="">Section 03<span class="k-sep"></span></p>
      <h2 class="title reveal d2">Workflow by Role</h2>
    </div>
    <span class="badge reveal d2"><strong>Q1</strong>2026</span>
  </div>
  <div class="lanes">
    <div class="lane-corner reveal d2"></div>
    <p class="lane-phase reveal d2">Kickoff</p><p class="lane-phase reveal d2">Design</p><p class="lane-phase reveal d2">Develop</p><p class="lane-phase reveal d2">Release</p>

    <p class="lane-role reveal d3"><span class="dot is-red"></span>Client</p>
    <div class="lane-cell reveal d3"><p class="lc-t">Brief &amp; requirements</p><p class="lc-s">Share goals and constraints</p></div>
    <div class="lane-cell reveal d3"><p class="lc-t">Review checkpoints</p><p class="lc-s">Feedback on each design round</p></div>
    <div class="lane-cell is-empty reveal d3"><p class="lc-s">—</p></div>
    <div class="lane-cell reveal d3"><p class="lc-t">Acceptance &amp; sign-off</p><p class="lc-s">UAT and go-live approval</p></div>

    <p class="lane-role reveal d4"><span class="dot is-amber"></span>Sun* Team</p>
    <div class="lane-cell reveal d4"><p class="lc-t">Scope &amp; estimate</p><p class="lc-s">Plan, roles, and timeline</p></div>
    <div class="lane-cell reveal d4"><p class="lc-t">UI design &amp; prototype</p><p class="lc-s">Wireframes to hi-fi screens</p></div>
    <div class="lane-cell is-active reveal d4"><p class="lc-t">Sprint development</p><p class="lc-s">Weekly demo to the client</p></div>
    <div class="lane-cell reveal d4"><p class="lc-t">Deploy &amp; handover</p><p class="lc-s">Docs, training, and support</p></div>

    <p class="lane-role reveal d5"><span class="dot is-teal"></span>QA</p>
    <div class="lane-cell reveal d5"><p class="lc-t">Test planning</p><p class="lc-s">Criteria and test design</p></div>
    <div class="lane-cell is-empty reveal d5"><p class="lc-s">—</p></div>
    <div class="lane-cell reveal d5"><p class="lc-t">Test execution</p><p class="lc-s">Per-sprint verification</p></div>
    <div class="lane-cell reveal d5"><p class="lc-t">Regression check</p><p class="lc-s">Full pass before release</p></div>
  </div>
  <img class="foot-logo" src="{{SUN_LOGO}}" alt="Sun*">
  <span class="pageno">15</span>
</section>
```

### 16. Diagram (system architecture)

**When:** Layered technical architecture (client/service/data). **Classes:** `.arch`. **Narrow:**
layer rows stack to 1 column, block rows wrap at ≤1024px.

```html
<section class="slide">
  <div class="head-row">
    <div class="head">
      <p class="kicker reveal d1"><img class="ast" src="{{SUN_ASTERISK}}" alt="">Section 03<span class="k-sep"></span></p>
      <h2 class="title reveal d2">System Diagram</h2>
    </div>
    <span class="badge reveal d2"><strong>Q1</strong>2026</span>
  </div>
  <div class="arch">
    <div class="arch-layer reveal d2">
      <div><p class="arch-name">Client Layer</p><p class="arch-note">What users touch</p></div>
      <div class="arch-blocks"><div class="arch-block">Web App</div><div class="arch-block">Mobile App</div><div class="arch-block">Admin Console</div></div>
    </div>
    <div class="arch-join reveal d3"><div></div><div class="aj"><span>↓</span><span>↓</span><span>↓</span></div></div>
    <div class="arch-layer reveal d3">
      <div><p class="arch-name">Service Layer</p><p class="arch-note">Business logic and APIs</p></div>
      <div class="arch-blocks"><div class="arch-block is-accent">API Gateway</div><div class="arch-block">Auth</div><div class="arch-block">Core Services</div><div class="arch-block">Notifications</div></div>
    </div>
    <div class="arch-join reveal d4"><div></div><div class="aj"><span>↓</span><span>↓</span></div></div>
    <div class="arch-layer reveal d4">
      <div><p class="arch-name">Data Layer</p><p class="arch-note">Storage and analytics</p></div>
      <div class="arch-blocks"><div class="arch-block is-dim">PostgreSQL</div><div class="arch-block is-dim">Object Storage</div></div>
    </div>
  </div>
  <img class="foot-logo" src="{{SUN_LOGO}}" alt="Sun*">
  <span class="pageno">16</span>
</section>
```

### 17. Photos (image mosaic)

**When:** Culture / event photos, 3-up mosaic. **Classes:** `.photo-grid`, `.sun-image-layout`.
**Narrow:** stacks to 1 column at ≤1024px.

```html
<section class="slide">
  <div class="head-row">
    <div class="head">
      <p class="kicker reveal d1"><img class="ast" src="{{SUN_ASTERISK}}" alt="">Section 03<span class="k-sep"></span></p>
      <h2 class="title reveal d2">Image Mosaic</h2>
    </div>
    <span class="badge reveal d2"><strong>Q1</strong>2026</span>
  </div>
  <div class="photo-grid">
    <div class="sun-image-layout photo-main reveal d3" data-shape="rounded">Drop the main event photo</div>
    <div class="sun-image-layout reveal d4" data-shape="rounded">Drop a second photo</div>
    <div class="sun-image-layout reveal d5" data-shape="rounded">Drop a third photo</div>
  </div>
  <img class="foot-logo" src="{{SUN_LOGO}}" alt="Sun*">
  <span class="pageno">17</span>
</section>
```

### 18. Image + Text (split)

**When:** One strong visual + supporting copy (product shot, screenshot). **Classes:** `.split-img`,
`.sun-image-layout`. Add `.is-flip` to mirror image/copy sides. **Narrow:** stacks to 1 column at ≤1024px.

```html
<section class="slide">
  <div class="head-row">
    <div class="head">
      <p class="kicker reveal d1"><img class="ast" src="{{SUN_ASTERISK}}" alt="">Section 03<span class="k-sep"></span></p>
      <h2 class="title reveal d2">Image + Text</h2>
    </div>
    <span class="badge reveal d2"><strong>Q1</strong>2026</span>
  </div>
  <div class="split-img">
    <div class="sun-image-layout reveal d3" data-shape="rounded">Drop a feature image</div>
    <div class="split-copy reveal d4">
      <p class="eyebrow">Use case</p>
      <h3>A headline that frames the image beside it</h3>
      <p class="lead">Pair one strong visual with supporting copy. Ideal for a product shot, a screenshot, or a single hero photo that needs explanation.</p>
      <ul class="mini-list">
        <li><span class="m">✱</span><span>First point that the image illustrates.</span></li>
        <li><span class="m">✱</span><span>Second point — keep each to one line.</span></li>
        <li><span class="m">✱</span><span>Third point that ties back to the visual.</span></li>
      </ul>
    </div>
  </div>
  <img class="foot-logo" src="{{SUN_LOGO}}" alt="Sun*">
  <span class="pageno">18</span>
</section>
```

### 19. Image Columns

**When:** Steps, gallery, or set of options, each with a caption. **Classes:** `.img-cols`,
`.sun-image-layout`. **Narrow:** stacks to 1 column at ≤1024px.

```html
<section class="slide">
  <div class="head-row">
    <div class="head">
      <p class="kicker reveal d1"><img class="ast" src="{{SUN_ASTERISK}}" alt="">Section 03<span class="k-sep"></span></p>
      <h2 class="title reveal d2">Image Columns</h2>
    </div>
    <span class="badge reveal d2"><strong>Q1</strong>2026</span>
  </div>
  <div class="img-cols">
    <div class="img-card reveal d3"><div class="sun-image-layout" data-shape="rounded">Drop image one</div><p class="cap-h"><span class="idx">01</span>First label</p><p class="cap-p">One short caption describing this image and what it shows.</p></div>
    <div class="img-card reveal d4"><div class="sun-image-layout" data-shape="rounded">Drop image two</div><p class="cap-h"><span class="idx">02</span>Second label</p><p class="cap-p">Parallel caption — keep all three roughly the same length.</p></div>
    <div class="img-card reveal d5"><div class="sun-image-layout" data-shape="rounded">Drop image three</div><p class="cap-h"><span class="idx">03</span>Third label</p><p class="cap-p">Use this layout for steps, gallery, or a set of options.</p></div>
  </div>
  <img class="foot-logo" src="{{SUN_LOGO}}" alt="Sun*">
  <span class="pageno">19</span>
</section>
```

### 20. Image Banner

**When:** One wide photo + a 3-cell caption strip below. **Classes:** `.banner-grid`,
`.sun-image-layout`. **Narrow:** caption strip stacks to 1 column at ≤1024px.

```html
<section class="slide">
  <div class="head-row">
    <div class="head">
      <p class="kicker reveal d1"><img class="ast" src="{{SUN_ASTERISK}}" alt="">Section 03<span class="k-sep"></span></p>
      <h2 class="title reveal d2">Image Banner</h2>
    </div>
    <span class="badge reveal d2"><strong>Q1</strong>2026</span>
  </div>
  <div class="banner-grid">
    <div class="sun-image-layout reveal d3" data-shape="rounded">Drop a wide banner image</div>
    <div class="banner-strip reveal d4">
      <div class="banner-cell"><p class="bc-k">Where</p><p class="bc-p">Location or context of the photo above.</p></div>
      <div class="banner-cell"><p class="bc-k">When</p><p class="bc-p">Date or milestone the image captures.</p></div>
      <div class="banner-cell"><p class="bc-k">What</p><p class="bc-p">One line on why this moment matters.</p></div>
    </div>
  </div>
  <img class="foot-logo" src="{{SUN_LOGO}}" alt="Sun*">
  <span class="pageno">20</span>
</section>
```

### 21. Feature (full-bleed)

**When:** Section opener, hero moment, or dramatic break inside the deck. **Classes:** `.s-feature`,
`.sun-image-layout[data-shape="rect"]`. This is the one type where the image fills the ENTIRE slide
(no padding) — the exception the image contract explicitly allows.

```html
<section class="slide s-feature">
  <div class="sun-image-layout feature-img" data-shape="rect">Drop a full-bleed hero image</div>
  <div class="feature-shade"></div>
  <div class="feature-cap">
    <p class="kicker reveal d1"><img class="ast" src="{{SUN_ASTERISK}}" alt="">Feature</p>
    <h2 class="reveal d2">A full-bleed image with the title over it</h2>
    <p class="feature-sub reveal d3">Use this for a section opener, a hero moment, or a cover-style break inside the deck. Text sits in a dark gradient so it stays legible over any photo.</p>
  </div>
  <img class="foot-logo" src="{{SUN_LOGO}}" alt="Sun*">
  <span class="pageno">21</span>
</section>
```

### 22. Guide (brand reference)

**When:** Rare — only if the deck itself is explaining the Sun* brand system (e.g. a design-handoff
deck). Skip for ordinary decks. **Classes:** `.guide-grid`. **Narrow:** `.guide-grid` stacks to 1 column
at ≤1024px; its nested `.swatches` (color chip grid) drops to 1 column at ≤480px so the hex/usage
caption text has room to wrap.

```html
<section class="slide">
  <div class="head-row">
    <div class="head">
      <p class="kicker reveal d1"><img class="ast" src="{{SUN_ASTERISK}}" alt="">Reference<span class="k-sep"></span></p>
      <h2 class="title reveal d2">Template Guide</h2>
    </div>
    <span class="badge reveal d2"><strong>Q1</strong>2026</span>
  </div>
  <div class="guide-grid">
    <div class="reveal d3">
      <h3 class="guide-h">Color Palette</h3>
      <div class="swatches">
        <div class="swatch"><div class="swatch-chip" style="background: #FF2200;"></div><div class="swatch-meta"><span>Sun* Red</span><span class="swatch-hex">#FF2200 · once per slide</span></div></div>
        <div class="swatch"><div class="swatch-chip" style="background: #1A1A1A;"></div><div class="swatch-meta"><span>Ink</span><span class="swatch-hex">#1A1A1A · text</span></div></div>
        <div class="swatch"><div class="swatch-chip" style="background: #F2A900;"></div><div class="swatch-meta"><span>Amber</span><span class="swatch-hex">#F2A900 · charts</span></div></div>
        <div class="swatch"><div class="swatch-chip" style="background: #0E7C7B;"></div><div class="swatch-meta"><span>Teal</span><span class="swatch-hex">#0E7C7B · charts</span></div></div>
        <div class="swatch"><div class="swatch-chip" style="background: #C9C0B8;"></div><div class="swatch-meta"><span>Sand</span><span class="swatch-hex">#C9C0B8 · neutral</span></div></div>
        <div class="swatch"><div class="swatch-chip" style="background: #FFE9E4;"></div><div class="swatch-meta"><span>Red Tint</span><span class="swatch-hex">#FFE9E4 · highlight</span></div></div>
      </div>
    </div>
    <div class="reveal d4">
      <h3 class="guide-h">Typography</h3>
      <div class="spec"><p class="spec-name">Be Vietnam Pro</p><p class="spec-note">Headings and body. Weights 400 / 600 / 700. Supports Vietnamese and English.</p></div>
      <div class="spec"><p class="spec-name">Space Grotesk</p><p class="spec-note">Display font for the Editorial variant headings. Latin only.</p></div>
      <p class="spec-note">Rule of thumb: Sun* Red appears once per slide — in the kicker asterisk, a highlighted bar, or a key number. Never more.</p>
    </div>
  </div>
  <img class="foot-logo" src="{{SUN_LOGO}}" alt="Sun*">
  <span class="pageno">22</span>
</section>
```

### 23. Thank You

**When:** Always the last slide. **Classes:** `.slide.thanks.s-brand`.

```html
<section class="slide thanks s-brand">
  <div class="bg-art bg-art--thanks" aria-hidden="true"><span class="ba-dot ba-dot-a"></span></div>
  <h2 class="thanks-title reveal d1"><span>Thank you</span><img class="thanks-ast" src="{{SUN_ASTERISK}}" alt=""></h2>
  <p class="thanks-contact reveal d2">contact@sun-asterisk.com</p>
  <img class="foot-logo" src="{{SUN_LOGO}}" alt="Sun*">
  <span class="pageno">23</span>
</section>
```
