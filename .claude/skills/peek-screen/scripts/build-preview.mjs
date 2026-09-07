// Builds one self-contained HTML deck that overlays translations on Figma screenshots.
//
// Usage: node build-preview.mjs <data.json> [out.html]
//
// Every frame becomes a slide. The screenshots are inlined as data URIs, so the single html file is
// the whole deliverable: it opens from disk and can be handed to someone else with nothing attached.
//
// A slide shows the original screenshot untouched. Hovering any text reveals its translation in a
// tooltip; switching language veils the screenshot and draws every translated label in place, so the
// whole screen reads at a glance while the original layout stays visible underneath.
//
// Nothing here reflows. Labels float above the image and may be wider than the text they cover, so
// no anchor ever needs correcting. That is the entire point of this renderer.
//
// The text also comes back out: a click on a label copies it in every language at once, the menu
// copies a frame or the whole deck as TSV, and select mode hands the drag over to the selection for
// marking part of a phrase. See the copy section in the page script.
//
// It also goes back in. One query searches the source and every translation of every frame at once,
// ignoring case and diacritics, and the walk through the matches lands in whichever language matched.
// See the find section in the page script.
//
// data.json:
//   {
//     "sourceLang": "ja",               // any code, or "src" for a neutral "Original" label
//     "langs": ["vi"],
//     "figmaUrl": "https://…",          // optional deck-wide fallback for a frame without its own
//     "frames": [
//       {
//         "frame": "Checkout_01",
//         "figmaUrl": "https://…",
//         "png": "Checkout_01.png",         // relative to data.json, covers renderBounds
//         "box": { "w": 1280, "h": 898 },   // absoluteBoundingBox, the frame itself
//         "render": { "w": 1336, "h": 917 },// absoluteRenderBounds, the png's extent
//         "offset": { "x": 28, "y": 19 },   // box.xy - render.xy, i.e. the shadow bleed
//         "items": [
//           { "x": 1068, "y": 17, "w": 56, "h": 22, "cw": 128, "size": 14, "style": "Regular",
//             "src": "お支払い方法", "t": { "vi": "Phương thức thanh toán" } }
//         ]
//       }
//     ]
//   }
//
// A single-frame file that carries "items" at the root, with no "frames", is still accepted and
// becomes a one-slide deck.
//
// "w"/"h" are the text node's own box; "cw" is its parent container's width, which is what the
// overflow warning measures against. See SKILL.md step 2 for why that distinction matters.
import { readFileSync, writeFileSync, statSync } from "node:fs";
import { dirname, resolve } from "node:path";

const [dataPath, outArg] = process.argv.slice(2);
if (!dataPath) {
  console.error("usage: node build-preview.mjs <data.json> [out.html]");
  process.exit(1);
}

const d = JSON.parse(readFileSync(dataPath, "utf8"));
const dataDir = dirname(resolve(dataPath));
const out = outArg ?? resolve(dataDir, "preview.html");

const frames = d.frames ?? (d.items ? [d] : null);
if (!frames?.length) {
  console.error("data.json has neither a non-empty 'frames' array nor a root-level 'items'");
  process.exit(1);
}
// Both accommodations for older files live here, at the boundary, so nothing downstream has to know
// two shapes exist: a root-level "items" is the pre-deck single frame, and an item without "cw"
// predates the container-width overflow check, for which its own box is the closest thing.
for (const f of frames) for (const it of f.items) it.cw ??= it.w;

const LANG_NAMES = {
  src: "Original",
  ja: "日本語",
  ko: "한국어",
  zh: "中文",
  th: "ไทย",
  en: "English",
  vi: "Tiếng Việt",
  fr: "Français",
  de: "Deutsch",
  es: "Español",
  pt: "Português",
  id: "Bahasa",
};
const WEIGHTS = { Thin: 100, Light: 300, Regular: 400, Medium: 500, Semibold: 600, Bold: 700, Black: 900 };
const esc = (s) =>
  String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");

const langs = d.langs ?? [];
const src = d.sourceLang ?? "src";
const missing = [];

// A frame can come back as one flat colour, and every other check here still passes: the item
// count is right and no translation is missing, so the run looks clean while the deck shows empty
// blocks. It happens when the screenshot caught a canvas layer lying over the frame and rendered
// that instead of the screen. Catching it costs no pixels, because a flat png compresses about an
// order of magnitude harder than a real screen and the two do not overlap: measured over one
// eighteen-frame deck, real frames ran 0.048 to 0.115 bytes per pixel and flat ones 0.0057 to
// 0.0061. A sparse-but-real frame compresses well too, so this is a prompt to look rather than a
// verdict, and it does not fail the build.
const FLAT_BYTES_PER_PIXEL = 0.02;
const flat = [];

// Inlining is what makes the output one file. The bytes never pass through the agent's context:
// they are read from disk here and written straight back out.
const inline = (f) => {
  const p = resolve(dataDir, f.png);
  let buf;
  try {
    buf = readFileSync(p);
  } catch {
    console.error(`frame ${f.frame}: cannot read png at ${p}`);
    process.exit(1);
  }
  const density = buf.length / (f.render.w * f.render.h);
  if (density < FLAT_BYTES_PER_PIXEL) {
    flat.push(
      `${f.frame} · ${f.png}: ${density.toFixed(4)} bytes/px, looks like a flat fill;` +
        ` re-shoot that frame with contentsOnly`,
    );
  }
  return `data:image/png;base64,${buf.toString("base64")}`;
};

const slides = frames
  .map((f) => {
    const url = f.figmaUrl ?? d.figmaUrl;
    const items = f.items
      .map((it) => {
        const weight = WEIGHTS[it.style] ?? 400;
        // A translation missing for one language must not silently render as the original.
        const t = Object.fromEntries(
          langs.map((l) => {
            const v = it.t?.[l];
            if (v === undefined) missing.push(`${f.frame} · ${l}: ${JSON.stringify(it.src)}`);
            return [l, v ?? it.src];
          }),
        );
        const label = langs.map((l) => `<span class="v" data-for="${l}">${esc(t[l])}</span>`).join("");
        // data-cw is the container's width, not the text node's. Comparing against the text node's
        // own box would flag every translation longer than the original, which is nearly all of
        // them; the container is what actually constrains the component.
        return `<div class="t" data-cw="${it.cw}" style="left:${it.x}px;top:${it.y}px;min-width:${it.w}px;height:${it.h}px;font-size:${it.size}px;font-weight:${weight}"
><span class="v" data-for="${src}">${esc(it.src)}</span>${label}</div>`;
      })
      .join("\n");

    return `<section class="slide" data-name="${esc(f.frame)}"${url ? ` data-url="${esc(url)}"` : ""}
  data-w="${f.box.w}" data-h="${f.box.h}">
  <div class="stage" style="width:${f.box.w}px;height:${f.box.h}px">
    <div class="shot">
      <img src="${inline(f)}" alt="${esc(f.frame)}" draggable="false"
           style="left:${-f.offset.x}px;top:${-f.offset.y}px;width:${f.render.w}px;height:${f.render.h}px">
      <div class="veil"></div>
    </div>
${items}
  </div>
</section>`;
  })
  .join("\n");

const thumbs = frames
  .map(
    (f, fi) =>
      `<button class="th" data-go="${fi}"><span class="thn">${fi + 1}. ${esc(f.frame)}</span
><span class="thb"></span></button>`,
  )
  .join("");

const buttons = [src, ...langs]
  .map(
    (l, i) =>
      `<button data-lang="${l}"${i === 0 ? ' class="on"' : ""}>${esc(LANG_NAMES[l] ?? l.toUpperCase())}</button>`,
  )
  .join("");

const multi = frames.length > 1;
const title = multi ? `${frames[0].frame} +${frames.length - 1} peek` : `${frames[0].frame} peek`;

// 16px line art on a 16 grid, inlined at each use site. A <symbol> sprite would cost an id namespace,
// a <use> indirection and ~500 bytes more than this, with only the copy icon drawn twice.
// How opaque the veil starts, as a percent. Heavy enough that dark-on-light labels stay readable
// over any screenshot, light enough that the design shows through; the slider owns it from there.
const VEIL = 88;

// One magnifier, worn by three controls: find keeps it bare, zoom out crosses it with a minus, zoom
// in adds the second stroke. Sharing the glass is what stops the three drifting apart.
const GLASS = '<circle cx="7" cy="7" r="4.6"/><path d="M10.4 10.4 14 14"/>';
const LENS = GLASS + '<path d="M5 7h4"/>';
const ICON = {
  find: GLASS,
  zo: LENS,
  zi: `${LENS}<path d="M7 5v4"/>`,   // same lens, one stroke more: the pair cannot drift apart
  fit: '<path d="M6 2H2v4M10 2h4v4M6 14H2v-4M10 14h4v-4"/>',
  chev: '<path d="M6.5 3.5 11 8l-4.5 4.5"/>',
  grid: '<rect x="2" y="2" width="5" height="5" rx="1"/><rect x="9" y="2" width="5" height="5" rx="1"/>'
      + '<rect x="2" y="9" width="5" height="5" rx="1"/><rect x="9" y="9" width="5" height="5" rx="1"/>',
  menu: '<path d="M2.5 4.5h11M2.5 8h11M2.5 11.5h7"/>',
  veil: '<circle cx="8" cy="8" r="5.6"/><path d="M8 2.4a5.6 5.6 0 0 1 0 11.2z" fill="currentColor" stroke="none"/>',
  ext: '<path d="M9 2h5v5M13.5 2.5 7.5 8.5M12 9.5V13a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1h3.5"/>',
  box: '<rect x="2.5" y="4" width="11" height="8" rx="1" stroke-dasharray="3 2.2"/>',
  copy: '<rect x="5.5" y="5.5" width="8" height="8" rx="1.2"/>'
      + '<path d="M10.5 3.5h-6a1 1 0 0 0-1 1v6"/>',
  caret: '<path d="M8 3.5v9M5.5 3.5h5M5.5 12.5h5"/>',   // the I-beam of a text cursor
  x: '<path d="M4.5 4.5 11.5 11.5M11.5 4.5 4.5 11.5"/>',
};
const svg = (k, cls = "") => `<svg class="i${cls}" viewBox="0 0 16 16">${ICON[k]}</svg>`;
// An icon-only control needs the same words twice, as tooltip and as accessible name. Written once.
const ico = (id, label, k, cls) =>
  `<button id="${id}" title="${label}" aria-label="${label}">${svg(k, cls)}</button>`;

const navKeys = multi
  ? `
        <dt><kbd>&larr;</kbd><kbd>&rarr;</kbd></dt><dd>slide</dd>
        <dt><kbd>G</kbd></dt><dd>grid</dd>`
  : "";

const html = `<!doctype html>
<html lang="${esc(src === "src" ? "en" : src)}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)}</title>
<style>
  :root { --bar: #1c1f26; --fg: #e8eaed; --accent: #7c8cff; --warn: #ff2d55; --barh: 44px;
          --veil: ${VEIL / 100}; }
  * { box-sizing: border-box; }
  body { margin: 0; height: 100vh; overflow: hidden; background: #6b7280;
         font: 14px/1.5 Inter, "SF Pro Text", -apple-system, "Segoe UI", Roboto, sans-serif; }

  /* The bar holds one line at every width. Nothing here may wrap its own text, and anything that
     would need a second line lives in the popover: a taller bar steals the height the frame needs,
     and the frames this page is for are taller than the window already. */
  .bar { position: sticky; top: 0; z-index: 100; display: flex; gap: 14px;
         align-items: center; padding: 8px 16px; min-height: var(--barh);
         background: var(--bar); color: var(--fg); }
  /* The frame name gives way first: it is also in the tab title and on every thumbnail, while the
     overflow tally beside it is the finding the reader came for, so that one keeps a floor. */
  .bar .name, #fit { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .bar .name { font-weight: 600; max-width: 26ch; }
  #fit:not(:empty) { min-width: 6ch; }   /* a floor only when there is a count to keep */
  /* A language named in its own language ("Tiếng Việt") is two words, and wrapping it inside the
     button is what made the bar two lines tall. The menu button wears the same skin. */
  .bar button, .menu > summary { display: inline-flex; align-items: center; padding: 4px 12px;
                border: 1px solid #3a3f4b; background: #24283190; color: var(--fg);
                border-radius: 6px; cursor: pointer; font: inherit; white-space: nowrap; }
  .bar button.on, .menu[open] > summary { background: var(--accent); border-color: var(--accent);
                color: #10131a; font-weight: 600; }
  kbd { padding: 1px 5px; border: 1px solid #ffffff30; border-radius: 4px; font-size: 11px;
        font-family: inherit; }

  /* Line art at 16px, inheriting the button's colour so the active state needs no second icon. */
  .i { width: 16px; height: 16px; flex: none; fill: none; stroke: currentColor; stroke-width: 1.7;
       stroke-linecap: round; stroke-linejoin: round; }
  .i.rev { transform: scaleX(-1); }   /* one chevron serves both directions */

  /* Everything a reader does not need on every glance: the Figma link, the box outlines, the keys. */
  .menu { position: relative; flex: none; }
  /* display:inline-flex above already drops the marker everywhere but older Safari. */
  .menu > summary::-webkit-details-marker { display: none; }
  /* Scrolls rather than running off the bottom: with the key list this is a tall popover, and a
     short window would otherwise put the last row somewhere the reader cannot reach it. */
  .pop { position: absolute; right: 0; top: calc(100% + 8px); z-index: 110; width: max-content;
         min-width: 232px; max-width: min(340px, 84vw); padding: 6px;
         max-height: calc(100vh - var(--barh) - 24px); overflow-y: auto;
         border: 1px solid #3a3f4b; border-radius: 10px; background: #171b23fa;
         box-shadow: 0 12px 34px #0009; }
  /* One row shape for every action, so the link stops looking like body text with an underline. */
  .pop .row { display: flex; align-items: center; gap: 9px; padding: 7px 9px; border-radius: 7px;
              color: var(--fg); text-decoration: none; cursor: pointer; font-size: 13px; }
  .pop .row:hover { background: #ffffff12; }
  /* The popover lives inside the bar, so the .bar button rule reaches these rows and they have to be
     undressed again: only what .pop .row does not already outrank, which is the frame, the fill, the
     refusal to wrap, and a button's own centring. Type is left alone: a font shorthand here would
     outrank .pop .row's own font-size and make these two rows a pixel taller than their neighbours. */
  .pop button.row { width: 100%; border: 0; background: none; white-space: normal; text-align: left; }
  .pop .row input { margin: 0 0 0 auto; accent-color: var(--accent); cursor: pointer; }
  .pop hr { margin: 5px 9px; border: 0; border-top: 1px solid #ffffff14; }
  /* Keys in their own column: the pairs line up vertically instead of drifting with the wording. */
  .pop .keys { display: grid; grid-template-columns: max-content 1fr; gap: 6px 10px;
               padding: 3px 9px 7px; font-size: 12px; }
  .pop .keys dt { display: flex; gap: 3px; justify-content: flex-end; }
  .pop .keys dd { margin: 0; opacity: .62; }
  .pop .note { margin: 0; padding: 0 9px 5px; font-size: 12px; opacity: .45; }

  .nav { display: ${multi ? "flex" : "none"}; flex: none; gap: 6px; align-items: center; }
  .nav .at { min-width: 6ch; text-align: center; font-variant-numeric: tabular-nums; opacity: .85; }
  .nav button, .zm button, #fb, .menu > summary { padding: 5px 8px; }
  #fb { flex: none; }
  .nav button:disabled { opacity: .35; cursor: default; }
  /* auto here is what pins the veil, zoom, slide and menu controls to the right edge. */
  .vl { display: flex; flex: none; gap: 7px; align-items: center; margin-left: auto; cursor: pointer; }
  .vl input { width: 76px; margin: 0; accent-color: var(--accent); cursor: ew-resize; }
  /* In the source language there is no veil to adjust, so the control says so rather than lying. */
  body:not(.translated) .vl { opacity: .35; }
  .zm { display: flex; flex: none; gap: 6px; align-items: center; }
  .zm .pc { min-width: 5ch; text-align: center; font-variant-numeric: tabular-nums; opacity: .85; }

  /* The name shrinks on its own, so a narrow window only needs the gaps tightened and, past the
     point where that runs out, the zoom readout dropped. Below roughly 600px the right-hand controls
     leave the viewport and the document scrolls sideways to reach them, which is a width where a
     1280px frame is unreadable anyway. */
  @media (max-width: 900px) { .bar { gap: 9px; padding: 8px 10px; } .vl input { width: 54px; } }
  @media (max-width: 680px) { .zm .pc, .vl { display: none; } }

  /* The deck is a fixed window onto a pannable canvas, so a frame larger than the screen is reached
     by moving the view rather than by shrinking it until the text is unreadable. */
  /* Selection is off by default because every drag starts on top of a label, and a half-selected
     paragraph trailing the cursor is worse than the copy gesture it costs. Getting the text out does
     not depend on it: a click copies the whole pair, and select mode below hands the drag back. */
  .deck { position: relative; overflow: hidden; cursor: grab; touch-action: none; user-select: none; }
  body.panning .deck { cursor: grabbing; }
  /* Hit-testing a label mid-drag would pop a tooltip under the cursor the user is dragging with. */
  body.panning .t { pointer-events: none; }

  /* Select mode: the drag selects text instead of panning, which the wheel still does. Marking a
     partial phrase is the one thing a whole-label copy cannot do, so it earns a mode of its own. */
  body.sel .deck { cursor: auto; user-select: text; }
  body.sel .t { cursor: text; }
  /* Translucent, because in the source language the label is transparent and the words being marked
     are the screenshot's own pixels underneath. An opaque highlight would hide them. */
  ::selection { background: #7c8cff59; }

  /* Slides are stacked and hidden with visibility, never display:none. A display:none slide measures
     zero, and the label spreading below has to measure every slide, not only the visible one. */
  .slide { position: absolute; inset: 0; visibility: hidden; }
  .slide.on { visibility: visible; }
  /* The stage does not clip. Only the screenshot inside it does. A translated label that runs past
     the frame's right edge has to stay readable; clipping it is what used to force the layout to
     drag whole rows leftwards, damaging labels that were sitting exactly where they belonged. */
  .stage { position: absolute; left: 0; top: 0; background: #fff; box-shadow: 0 8px 40px #0006;
           transform-origin: 0 0; }
  .shot { position: absolute; inset: 0; overflow: hidden; }
  /* The png covers renderBounds, which is larger than the frame whenever an effect bleeds past it.
     Offsetting by that difference puts the frame's own origin at the stage origin. */
  .shot img { position: absolute; }

  /* Veiling the screenshot leaves the original layout readable as a ghost behind the labels, which
     is what makes an in-place overlay legible without knowing each background colour. How much veil
     is the reader's call: a heavy one reads like a document, a light one keeps the design visible. */
  .veil { position: absolute; inset: 0; background: #fff; opacity: var(--veil);
          pointer-events: none; display: none; }
  body.translated .veil { display: block; }

  /* "pre" keeps the hard line breaks a Figma paragraph carries and still refuses to wrap, so a label
     is exactly as wide as its longest line and never reflows into its neighbour's row. */
  .t { position: absolute; white-space: pre; line-height: 1.57; display: flex; align-items: center;
       color: #262626; cursor: copy; }
  .t .v { display: none; }
  /* In the source language the screenshot already shows the text, so the layer is only a hotspot. */
  body:not(.translated) .t { color: transparent; }
  /* The rule revealing the current language is injected at runtime by show(). */

  body.outline .t { outline: 1px solid #ff2d55a0; background: #ff2d5518; }
  /* A search hit, and the one the walk is standing on. Outline rather than box-shadow, because the
     overflow underline below is a box-shadow and a hit label is often also the label that overflows:
     two different findings about the same string, and both have to stay visible. */
  .t.hit { outline: 2px solid var(--accent); background: #7c8cff2b; }
  .t.now { outline-color: #ffd166; background: #ffd16640; z-index: 55; }
  /* A translation wider than its Figma container: a real constraint for whoever builds the screen. */
  body.translated .t.tight { box-shadow: inset 0 -2px 0 var(--warn); }

  .t:hover { z-index: 60; }
  .t::after { content: attr(data-tip); position: absolute; left: 0; top: 100%; margin-top: 4px;
              padding: 6px 9px; border-radius: 6px; background: #10131aef; color: #fff;
              font: 400 13px/1.4 inherit; white-space: pre; letter-spacing: 0;
              box-shadow: 0 4px 16px #0005; opacity: 0; pointer-events: none; transition: opacity .08s; }
  .t:hover::after { opacity: 1; }

  /* Overview. Reuses each slide's own img, scaled down, purely to jump: the overlay is unreadable at
     thumbnail size, so nothing tries to render it here. */
  .grid { position: fixed; inset: var(--barh) 0 0; z-index: 90; display: none; overflow: auto;
          /* --barh is only an estimate of the bar's real height, so sizeDeck() measures and re-sets it */
          padding: 20px; gap: 18px; background: #10131af2;
          grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); }
  body.gridon .grid { display: grid; }
  .th { position: relative; padding: 0; border: 2px solid transparent; border-radius: 8px;
        background: #fff; cursor: pointer; overflow: hidden; font: inherit; text-align: left; }
  .th.on { border-color: var(--accent); }
  .th canvas, .th img { display: block; width: 100%; }
  .thn { display: block; padding: 6px 9px; background: var(--bar); color: var(--fg); font-size: 12px;
         white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .thb { position: absolute; top: 6px; right: 6px; padding: 1px 7px; border-radius: 10px;
         background: var(--warn); color: #fff; font-size: 11px; font-weight: 600; display: none; }
  .thb.on { display: block; }

  /* A copy leaves no trace on the page, so it has to say so somewhere. Bottom centre, out of the way
     of both the bar and the label just clicked, and it never takes the pointer. */
  .ts { position: fixed; left: 50%; bottom: 22px; z-index: 120; transform: translate(-50%, 6px);
        max-width: 76vw; padding: 8px 14px; border-radius: 8px; background: #10131aef; color: #fff;
        font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        box-shadow: 0 6px 22px #0007; opacity: 0; pointer-events: none;
        transition: opacity .12s, transform .12s; }
  .ts.on { opacity: 1; transform: translate(-50%, 0); }

  /* Find. A floating panel rather than a field in the bar: the bar may not grow a second line, and a
     search box wide enough to read a Vietnamese phrase in would cost more width than it has. Left
     edge, because the bar's own controls are gathered at the right. sizeDeck() sets the real top. */
  .find { position: fixed; left: 16px; top: calc(var(--barh) + 8px); z-index: 108;
          display: flex; flex-direction: column; width: min(380px, calc(100vw - 32px));
          border: 1px solid #3a3f4b; border-radius: 10px; background: #171b23fa; color: var(--fg);
          box-shadow: 0 12px 34px #0009; }
  .find[hidden] { display: none; }   /* a display of our own outranks the hidden attribute */
  .fh { display: flex; gap: 6px; align-items: center; padding: 6px; }
  .fh input { flex: 1; min-width: 0; padding: 5px 8px; border: 1px solid #3a3f4b; border-radius: 6px;
              background: #0f1218; color: var(--fg); font: inherit; }
  .fh input:focus { outline: none; border-color: var(--accent); }
  .fh button { display: inline-flex; flex: none; padding: 4px 6px; border: 1px solid #3a3f4b;
               background: #242831; color: var(--fg); border-radius: 6px; cursor: pointer; }
  .fh button:disabled { opacity: .35; cursor: default; }
  .fs { margin: 0; padding: 0 9px 7px; font-size: 12px; opacity: .55; }
  /* The list is capped and scrolls: a common word across eighteen frames would otherwise run the
     panel off the bottom of the window, taking its own scrollbar out of reach. */
  .fl { max-height: min(46vh, 420px); overflow-y: auto; padding: 0 6px 6px; }
  .fl:empty { display: none; }
  .fg { padding: 6px 9px 3px; font-size: 11px; letter-spacing: .04em; text-transform: uppercase;
        opacity: .45; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .fi { display: flex; gap: 8px; align-items: baseline; width: 100%; padding: 5px 9px; border: 0;
        border-radius: 6px; background: none; color: var(--fg); font: inherit; font-size: 13px;
        text-align: left; cursor: pointer; }
  .fi:hover { background: #ffffff12; }
  .fi.on { background: #7c8cff2e; }
  .fk { flex: none; min-width: 3.5ch; font-size: 11px; opacity: .5; }
  .ft { flex: 1; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .ft mark { background: var(--accent); color: #10131a; border-radius: 2px; }
</style>
</head>
<body>
<div class="bar">
  <span class="name" id="nm"></span>
  ${buttons}
  <span id="fit"></span>
  <label class="vl" title="veil over the screenshot: drag left to see the design through the labels">
    ${svg("veil")}<input type="range" id="vl" min="0" max="100" step="2" value="${VEIL}"
      aria-label="veil over the screenshot"></label>
  ${ico("fb", "find text in every language", "find")}
  <div class="zm">
    ${ico("zo", "zoom out", "zo")}
    <span class="pc" id="zpc"></span>
    ${ico("zi", "zoom in", "zi")}
    ${ico("zf", "fit to window", "fit")}
  </div>
  <div class="nav">
    ${ico("pv", "previous slide", "chev", " rev")}
    <span class="at" id="at"></span>
    ${ico("nx", "next slide", "chev")}
    ${ico("gd", "grid of all frames", "grid")}
  </div>
  <details class="menu" id="mu">
    <summary title="more" aria-label="more">${svg("menu")}</summary>
    <div class="pop">
      <a class="row" id="fg" href="#" target="_blank" rel="noreferrer" hidden
        >${svg("ext")}Open this frame in Figma</a>
      <button class="row" id="fm">${svg("find")}Find text in every language</button>
      <button class="row" id="cf">${svg("copy")}Copy this frame's text</button>
      ${multi ? `<button class="row" id="cd">${svg("copy")}Copy every frame's text</button>` : ""}
      <label class="row">${svg("caret")}Select text with the mouse
        <input type="checkbox" id="sx"></label>
      <label class="row">${svg("box")}Text box outlines
        <input type="checkbox" id="ol"></label>
      <hr>
      <dl class="keys">
        <dt><kbd>T</kbd></dt><dd>language</dd>
        <dt><kbd>/</kbd><kbd>F</kbd></dt><dd>find, in every language at once</dd>
        <dt><kbd>C</kbd></dt><dd>copy the label under the cursor</dd>
        <dt><kbd>S</kbd></dt><dd>select text</dd>
        <dt><kbd>O</kbd></dt><dd>text boxes</dd>
        <dt><kbd>0</kbd><kbd>1</kbd></dt><dd>fit / 100%</dd>
        <dt><kbd>+</kbd><kbd>&minus;</kbd></dt><dd>zoom step</dd>
        <dt><kbd>[</kbd><kbd>]</kbd></dt><dd>veil</dd>${navKeys}
      </dl>
      <p class="note">drag to pan &middot; ctrl+scroll to zoom &middot; click a label to copy the pair</p>
    </div>
  </details>
</div>
<div class="deck" id="deck">
${slides}
</div>
<div class="grid" id="grid">${thumbs}</div>
<div class="find" id="fd" hidden>
  <div class="fh">
    ${svg("find")}
    <input type="text" id="fq" placeholder="find in every language" autocomplete="off"
           spellcheck="false" aria-label="find text in every language">
    ${ico("fp", "previous match", "chev", " rev")}
    ${ico("fn", "next match", "chev")}
    ${ico("fx", "close find", "x")}
  </div>
  <p class="fs" id="fs" hidden></p>
  <div class="fl" id="fl"></div>
</div>
<div class="ts" id="ts" role="status" aria-live="polite"></div>
<script>
const SRC = ${JSON.stringify(src)};
const LANGS = ${JSON.stringify(langs)};
const style = document.createElement("style");
document.head.append(style);

const ALL = [SRC, ...LANGS];   // every language the deck holds, in the order T cycles them
const deck = document.getElementById("deck");
const slides = [...document.querySelectorAll(".slide")];
const stages = slides.map((s) => s.querySelector(".stage"));
const thumbs = [...document.querySelectorAll(".th")];
const zpcEl = document.getElementById("zpc");
const fitEl = document.getElementById("fit");
let current = SRC;
let at = 0;

const GAP = 8;   // breathing room to keep between two labels sharing a line
const PAD = 24;  // margin left around the frame when fitting
const KEEP = 120;// how much of the frame must stay on screen however far the view is dragged
const MINZ = 0.05, MAXZ = 8;

// The view: one scale and one pan, shared by every slide. Shared is the point: walking a flow at a
// fixed zoom keeps the same region of each screen under the eye, which is how two frames get
// compared. A fit-only viewer cannot do that on a laptop, where fitting a 1280px frame already
// shrinks the text past reading size.
let z = 1, tx = 0, ty = 0;

const boxOf = (i) => ({ w: Number(slides[i].dataset.w), h: Number(slides[i].dataset.h) });
// A label's versions, in the order the builder emitted them: source first, then one per target. The
// tooltip and every copy path read a label through this, so the markup is described in one place.
const vals = (el) => [...el.querySelectorAll(".v")];

function apply() {
  const b = boxOf(at);
  // Clamp rather than free-pan: the frame can always be dragged back into view.
  tx = Math.max(KEEP - b.w * z, Math.min(deck.clientWidth - KEEP, tx));
  ty = Math.max(KEEP - b.h * z, Math.min(deck.clientHeight - KEEP, ty));
  // Every slide carries the transform, not only the visible one: relayout() measures them all, and
  // a hidden slide left at a different scale would measure wrong when its turn comes.
  const t = "translate(" + tx.toFixed(1) + "px," + ty.toFixed(1) + "px) scale(" + z + ")";
  for (const st of stages) st.style.transform = t;
  zpcEl.textContent = Math.round(z * 100) + "%";
}

function fitView() {
  const b = boxOf(at);
  z = Math.min(1, (deck.clientWidth - 2 * PAD) / b.w, (deck.clientHeight - 2 * PAD) / b.h);
  tx = (deck.clientWidth - b.w * z) / 2;
  ty = Math.max(PAD, (deck.clientHeight - b.h * z) / 2);
  apply();
}

// Zoom about a point, so the pixel under the cursor stays under the cursor.
function zoomAt(f, cx, cy) {
  const nz = Math.max(MINZ, Math.min(MAXZ, z * f));
  tx = cx - (cx - tx) * (nz / z);
  ty = cy - (cy - ty) * (nz / z);
  z = nz;
  apply();
}

const mid = () => [deck.clientWidth / 2, deck.clientHeight / 2];

function sizeDeck() {
  const bar = document.querySelector(".bar").offsetHeight;
  deck.style.height = innerHeight - bar + "px";
  document.getElementById("grid").style.top = bar + "px";
  document.getElementById("fd").style.top = bar + 8 + "px";
}

// Translations often run 1.5x to 2.5x longer than the original, so labels that sat side by side now
// collide. The browser is the only place the real text widths are known, so the spreading happens
// here rather than in hand-written per-frame corrections: group labels into rows, then push each
// row's later labels right until nothing overlaps.
function relayout(si) {
  const slide = slides[si];
  const els = [...slide.querySelectorAll(".t")];
  for (const e of els) {
    e.style.transform = "";
    e.classList.remove("tight");
  }
  if (!document.body.classList.contains("translated")) {
    slide.dataset.tight = 0;
    return;
  }

  // Every measurement below is a scaled rect, so divide back into the frame's own pixels: data-cw
  // and the frame width are unscaled, and the shifts are written back as unscaled translateX.
  const sr = stages[si].getBoundingClientRect();
  let tight = 0;
  const boxes = els.map((e) => {
    const r = e.getBoundingClientRect();
    // Flag before any shifting: overflowing its own container is a property of the string, not of
    // where it ends up sitting.
    if (r.width / z > Number(e.dataset.cw) + 2) {
      e.classList.add("tight");
      tight++;
    }
    return {
      e,
      l: (r.left - sr.left) / z, r: (r.right - sr.left) / z,
      t: (r.top - sr.top) / z, b: (r.bottom - sr.top) / z,
    };
  });

  // Two labels belong to the same row when they overlap vertically by more than half the shorter
  // one, which keeps a tall paragraph from swallowing the line above it.
  const rows = [];
  for (const b of boxes.sort((p, q) => p.t - q.t || p.l - q.l)) {
    const row = rows.find((r) =>
      r.some((o) => Math.min(o.b, b.b) - Math.max(o.t, b.t) > Math.min(o.b - o.t, b.b - b.t) / 2),
    );
    if (row) row.push(b);
    else rows.push([b]);
  }

  for (const row of rows) {
    row.sort((p, q) => p.l - q.l);
    const wide = row.map((b) => b.r - b.l);

    // Left to right: push each label right until it clears the one before it.
    const pos = [];
    for (let i = 0; i < row.length; i++) {
      pos[i] = i === 0 ? row[i].l : Math.max(row[i].l, pos[i - 1] + wide[i - 1] + GAP);
    }

    // That is the whole layout. Pushing right from the anchors is already the leftmost arrangement
    // that keeps every label readable and on its own mark, so there is nothing left to pull back:
    // any further move would put a label left of where the design put it, for no gain. A row that
    // runs past the frame's right edge simply spills over it, which the stage no longer clips.
    row.forEach((b, i) => {
      const sh = pos[i] - b.l;
      if (Math.abs(sh) > 0.5) b.e.style.transform = "translateX(" + sh.toFixed(1) + "px)";
    });
  }
  slide.dataset.tight = tight;
}

// Every slide is measured, not only the visible one, so the grid can badge the frames that cannot
// hold this language before the reader has walked to them.
function relayoutAll() {
  slides.forEach((_, i) => relayout(i));
  for (const t of thumbs) {
    const n = Number(slides[Number(t.dataset.go)].dataset.tight);
    const b = t.querySelector(".thb");
    b.textContent = n;
    b.classList.toggle("on", n > 0);
  }
  report();
}

function report() {
  const n = Number(slides[at].dataset.tight) || 0;
  fitEl.textContent = n ? n + (n === 1 ? " label overflows" : " labels overflow") : "";
  fitEl.style.color = n ? "#ff8a94" : "";
  fitEl.title = n ? "Wider than its Figma container: the component cannot hold this language" : "";
}

function go(i) {
  at = Math.max(0, Math.min(slides.length - 1, i));
  slides.forEach((s, j) => s.classList.toggle("on", j === at));
  thumbs.forEach((t, j) => t.classList.toggle("on", j === at));
  const s = slides[at];
  apply();  // the new frame may be a different size, so the pan clamp changes with it
  document.getElementById("nm").textContent = s.dataset.name;
  document.getElementById("at").textContent = at + 1 + " / " + slides.length;
  document.getElementById("pv").disabled = at === 0;
  document.getElementById("nx").disabled = at === slides.length - 1;
  const fg = document.getElementById("fg");
  fg.hidden = !s.dataset.url;
  if (s.dataset.url) fg.href = s.dataset.url;
  report();
  mark();
}

function show(lang) {
  document.body.classList.toggle("translated", lang !== SRC);
  // One injected rule beats toggling a class on every label.
  style.textContent = '.t .v[data-for="' + lang + '"]{display:inline}';
  for (const b of document.querySelectorAll(".bar button[data-lang]")) {
    b.classList.toggle("on", b.dataset.lang === lang);
  }
  // The tooltip always shows the other sides of the pair.
  for (const t of document.querySelectorAll(".t")) {
    t.dataset.tip = vals(t)
      .filter((v) => v.dataset.for !== lang)
      .map((v) => v.dataset.for + "  " + v.textContent)
      .join("\\n");
  }
  current = lang;
  // show() owns which language is on screen, so it owns saying so: a screen reader or an automatic
  // translator reading a stale lang would be told the wrong thing from the first T onwards.
  document.documentElement.lang = lang === "src" ? "en" : lang;
  relayoutAll();
  paintHits();   // the rings belong to the language on screen, and it just changed
  mark();
}

// A link carries both the language and the slide, so a finding can be pointed at directly.
function mark() {
  const q = new URLSearchParams();
  if (current !== SRC) q.set("lang", current);
  if (at) q.set("f", at + 1);
  history.replaceState(null, "", q.toString() ? "?" + q : location.pathname);
}

// Getting the text back out. Three ways, because they answer three questions: one label with every
// language beside it, one frame as a table, or the whole deck. A plain selection can never hand over
// a pair, since only one language is on screen at a time and the tooltip is a pseudo-element that
// cannot be selected at all. Click-to-copy is the answer to that; select mode below covers the one
// thing a whole-label copy cannot do, which is marking part of a phrase.
const ts = document.getElementById("ts");
let tsT;
function toast(msg) {
  ts.textContent = msg;
  ts.classList.add("on");
  clearTimeout(tsT);
  tsT = setTimeout(() => ts.classList.remove("on"), 1800);
}

// This page is opened from a file:// URL as often as not. Chrome and Firefox count that as a secure
// context and hand over navigator.clipboard; a browser that does not has to fall back to the hidden
// textarea, or the copy fails with nothing on screen to say it did.
function copy(text, note) {
  const ok = () => toast(note);
  const legacy = () => {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("style", "position:fixed;top:-2000px;opacity:0");
    document.body.append(ta);
    ta.select();
    const done = document.execCommand("copy");
    ta.remove();
    if (done) ok();
    else toast("the browser refused the copy");
  };
  if (navigator.clipboard?.writeText) navigator.clipboard.writeText(text).then(ok, legacy);
  else legacy();
}

const langOf = (l) => (l === "src" ? "original" : l);
// One label: one line per language, source first, which is the order the builder emits the spans in.
// No language codes on the lines, because with the usual single target this is exactly the pair,
// ready to paste, and the order says which is which. The toast is trimmed by its own CSS, so the
// whole source string goes in and the box decides where to cut it.
function copyLabel(el) {
  const parts = vals(el).map((v) => v.textContent);
  // A Figma paragraph brings its own line breaks along, and then one line per language runs the
  // versions together with nothing marking where each begins. A blank line between them is the fix.
  const sep = parts.some((p) => p.includes("\\n")) ? "\\n\\n" : "\\n";
  copy(parts.join(sep), "copied \\u00b7 " + parts[0]);
}

// A tab or a newline inside a cell would tear the row apart, and a Figma paragraph carries real
// newlines, so they travel as the two characters \\n and the row stays one row in a spreadsheet.
const cell = (s) => s.replace(/\\t/g, " ").replace(/\\n/g, "\\\\n");
// The frame column earns its place only once there is more than one frame to tell apart, so the
// caller does not have to say: asking for several frames is what asks for the column.
function tsvOf(indexes) {
  const named = indexes.length > 1;
  const rows = [(named ? ["frame"] : []).concat(ALL.map(langOf)).join("\\t")];
  let n = 0;
  for (const i of indexes) {
    const name = cell(slides[i].dataset.name);
    for (const t of slides[i].querySelectorAll(".t")) {
      const cols = vals(t).map((v) => cell(v.textContent));
      rows.push((named ? [name, ...cols] : cols).join("\\t"));
      n++;
    }
  }
  return { text: rows.join("\\n"), n };
}
const copyRows = (indexes, where) => {
  const { text, n } = tsvOf(indexes);
  copy(text, "copied " + n + (n === 1 ? " string \\u00b7 " : " strings \\u00b7 ") + where);
};
const copyFrame = () => copyRows([at], slides[at].dataset.name);
const copyDeck = () => copyRows(slides.map((_, i) => i), slides.length + " frames");

// Finding a string. The deck holds every language of every frame, and the reader knows the phrase in
// one of them, not necessarily the one on screen: an implementer searches the source, a reviewer
// searches the translation they were sent. So one query runs over all of them at once, and the walk
// lands on whichever language the match came from, since in any other one that label is either the
// untouched screenshot or a different string entirely.
//
// The browser's own ctrl+F is left alone, and cannot do this job: only one language is in the layout
// at a time, and the labels of the other slides are hidden from it.
const fd = document.getElementById("fd");
const fq = document.getElementById("fq");
const fs = document.getElementById("fs");
const fl = document.getElementById("fl");
const fb = document.getElementById("fb");
const fp = document.getElementById("fp");
const fnx = document.getElementById("fn");

const escH = (s) => s.replace(/[&<>]/g, (c) => (c === "&" ? "&amp;" : c === "<" ? "&lt;" : "&gt;"));

// Folding, per character, so "phuong thuc" finds "Phương thức" and case never matters: a reader
// types a Vietnamese phrase without its diacritics far more often than with them. Combining marks
// strip out under NFD; đ carries no mark and needs saying. The map is what lets a result row mark
// the matched span in the original string, since one character can fold to a different length and
// the two sets of positions cannot be assumed to line up.
const foldc = (c) => c.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/g, "d");
function foldOf(s) {
  let f = "";
  const map = [];
  for (let i = 0; i < s.length; i++) {
    const c = foldc(s[i]);
    for (let j = 0; j < c.length; j++) { f += c[j]; map.push(i); }
  }
  map.push(s.length);   // so a match ending at the last character has an end to slice to
  return { f, map };
}

// Built once, on the first search, and good for the rest of the session: nothing edits a label.
let index = null;
let hits = [];
let cur = -1;
function buildIndex() {
  index = [];
  slides.forEach((sl, si) => {
    for (const el of sl.querySelectorAll(".t")) {
      for (const v of vals(el)) {
        const text = v.textContent;
        const { f, map } = foldOf(text);
        index.push({ si, el, lang: v.dataset.for, text, f, map });
      }
    }
  });
}

const shortLang = (l) => (l === "src" ? "orig" : l);
// A one-letter query on an eighteen-frame deck matches about fifteen hundred strings, and drawing a
// row for each of them costs a visible stutter on the keystroke that does it. Measured on such a
// deck: 126ms for the whole list, 30ms for this many. Nobody reads past a few dozen rows anyway, and
// the walk is unaffected, since it steps through every match rather than through the drawn rows. The
// status line says when a query has more than this, so a short list never reads as the whole answer.
const MAXROWS = 300;

function runFind() {
  for (const h of hits) h.el.classList.remove("hit", "now");
  hits = [];
  cur = -1;
  const q = foldOf(fq.value.trim()).f;
  // A query of nothing but diacritics folds away to nothing, which would otherwise match every
  // label at position 0.
  if (!q) {
    fs.hidden = true;
    fl.textContent = "";
    fp.disabled = fnx.disabled = true;
    return;
  }
  if (!index) buildIndex();
  for (const e of index) {
    // Every occurrence, not only the first: the row is how the reader reads the string back, and a
    // second hit inside it is part of what they asked for. The walk still stops once per label, since
    // the ring covers the whole label and a second stop on it would land in the same place.
    const spans = [];
    for (let a = e.f.indexOf(q); a >= 0; a = e.f.indexOf(q, a + q.length)) {
      spans.push([e.map[a], e.map[a + q.length]]);
    }
    if (spans.length) hits.push({ si: e.si, el: e.el, lang: e.lang, text: e.text, spans });
  }
  paintFind();
}

// A ring means "the words you asked for are here, on this screen". So only a label whose matching
// language is the one being displayed gets one: in any other language that label is a different
// string, and ringing it would point at words that are not there. The panel still lists every match
// with its language, which is how a match in a language that is not up is found at all.
function paintHits() {
  for (const h of hits) h.el.classList.remove("hit", "now");
  hits.forEach((h, i) => {
    if (h.lang !== current) return;
    h.el.classList.add("hit");
    if (i === cur) h.el.classList.add("now");
  });
}

// The list is grouped by frame and in slide order, so it doubles as a map of where the term lives
// across the flow: which screens carry it, and how often.
function paintFind() {
  const frameCount = new Set(hits.map((h) => h.si)).size;
  const n = hits.length;
  fs.hidden = false;
  fs.textContent = n
    ? n + (n === 1 ? " match in " : " matches in ") + frameCount +
      (frameCount === 1 ? " frame" : " frames") +
      (n > MAXROWS ? " \u00b7 first " + MAXROWS + " listed, enter walks them all"
                   : " \u00b7 enter walks them")
    : "no match";
  let html = "";
  let last = -1;
  hits.forEach((h, i) => {
    if (i >= MAXROWS) return;
    if (h.si !== last) {
      last = h.si;
      html += '<div class="fg">' + escH(h.si + 1 + ". " + slides[h.si].dataset.name) + "</div>";
    }
    let text = "";
    let from = 0;
    for (const [a, b] of h.spans) {
      text += escH(h.text.slice(from, a)) + "<mark>" + escH(h.text.slice(a, b)) + "</mark>";
      from = b;
    }
    text += escH(h.text.slice(from));
    html += '<button class="fi" data-h="' + i + '"><span class="fk">' + escH(shortLang(h.lang)) +
      '</span><span class="ft">' + text + "</span></button>";
  });
  fl.innerHTML = html;
  fp.disabled = fnx.disabled = !n;
  markHit();
}

function markHit() {
  paintHits();
  for (const r of fl.querySelectorAll(".fi")) r.classList.toggle("on", Number(r.dataset.h) === cur);
  const row = fl.querySelector('.fi[data-h="' + cur + '"]');
  if (row) row.scrollIntoView({ block: "nearest" });
}

// Bring a label to the middle of the window without touching the zoom: the reader set that, and a
// find is no reason to throw it away. Measured rather than computed, so the runtime spreading and
// the pan clamp are both already accounted for.
function center(el) {
  const dr = deck.getBoundingClientRect();
  const r = el.getBoundingClientRect();
  // Horizontally the target is the middle of what the panel leaves, not the middle of the window: at
  // 380px of panel in a 768px window those are 200px apart, which is enough to land every match the
  // walk visits underneath the panel. The clamp is for a window narrower than the panel itself.
  const clear = fd.hidden ? dr.left : Math.min(fd.getBoundingClientRect().right + 12, dr.right - 80);
  tx += (Math.max(dr.left, clear) + dr.right) / 2 - (r.left + r.width / 2);
  ty += dr.top + deck.clientHeight / 2 - (r.top + r.height / 2);
  apply();
}

function goHit(i) {
  if (!hits.length) return;
  cur = (i + hits.length) % hits.length;
  const h = hits[cur];
  if (h.lang !== current) show(h.lang);
  document.body.classList.remove("gridon");
  go(h.si);
  center(h.el);
  markHit();
}

const openFind = () => {
  fd.hidden = false;
  fb.classList.add("on");
  fq.focus();
  fq.select();
};
// Closing clears: the highlights are the query made visible, and leaving them on a page with no
// query showing is a puzzle. One keystroke brings the panel, and the field, straight back.
const closeFind = () => {
  fd.hidden = true;
  fb.classList.remove("on");
  fq.value = "";
  runFind();
};
const toggleFind = () => (fd.hidden ? openFind() : closeFind());

// Stepping the walk. From a walk that has not started cur is -1, so going back has to be told to
// reach the last match: cur - 1 would be -2, which wraps to the one before it.
const nextHit = () => goHit(cur + 1);
const prevHit = () => goHit(cur < 0 ? -1 : cur - 1);

fq.oninput = runFind;
fq.addEventListener("keydown", (e) => {
  if (e.key === "Enter") { (e.shiftKey ? prevHit : nextHit)(); e.preventDefault(); }
  if (e.key === "Escape") closeFind();
});
fb.onclick = toggleFind;
document.getElementById("fx").onclick = closeFind;
fp.onclick = prevHit;
fnx.onclick = nextHit;
// Focus goes back to the field after a row: the walk continues from there on enter, and the row that
// was clicked stays marked in the list, which is where the reader can see their place.
fl.addEventListener("click", (e) => {
  const row = e.target.closest(".fi");
  if (!row) return;
  goHit(Number(row.dataset.h));
  fq.focus();
});

deck.addEventListener("click", (e) => {
  const t = e.target.closest(".t");
  // A pan never reaches here as a click on a label: mid-drag the labels take no pointer events, so
  // the browser resolves the click against the deck instead. Two things do have to be skipped: the
  // second click of the double click that toggles zoom, which would otherwise copy the same label
  // twice, and a click ending a selection in select mode, which would copy over what was just marked.
  // Only a repeat click is refused, never a first one: a click carrying no count at all comes from a
  // script or an assistive tool, and that is still somebody asking for this label.
  if (t && e.detail < 2 && getSelection().isCollapsed) copyLabel(t);
});

const sx = document.getElementById("sx");
sx.onchange = (e) => document.body.classList.toggle("sel", e.target.checked);
document.getElementById("fm").onclick = () => { menu.open = false; openFind(); };
document.getElementById("cf").onclick = copyFrame;
const cd = document.getElementById("cd");
if (cd) cd.onclick = copyDeck;

for (const b of document.querySelectorAll(".bar button[data-lang]")) b.onclick = () => show(b.dataset.lang);
for (const t of thumbs) {
  t.onclick = () => {
    document.body.classList.remove("gridon");
    go(Number(t.dataset.go));
  };
  // The thumbnail is the slide's own inlined png, reused rather than embedded a second time.
  const img = slides[Number(t.dataset.go)].querySelector("img").cloneNode();
  img.removeAttribute("style");
  t.prepend(img);
}
document.getElementById("ol").onchange = (e) =>
  document.body.classList.toggle("outline", e.target.checked);
document.getElementById("pv").onclick = () => go(at - 1);
document.getElementById("nx").onclick = () => go(at + 1);
document.getElementById("gd").onclick = () => document.body.classList.toggle("gridon");
document.getElementById("zi").onclick = () => zoomAt(1.25, ...mid());
document.getElementById("zo").onclick = () => zoomAt(0.8, ...mid());
document.getElementById("zf").onclick = fitView;

// The veil is one CSS variable, so the slider writes it and nothing has to be relaid out.
const veil = document.getElementById("vl");
const setVeil = (pc) => {
  veil.value = Math.min(100, Math.max(0, pc));
  document.documentElement.style.setProperty("--veil", veil.value / 100);
};
veil.oninput = () => setVeil(Number(veil.value));
// A pointer drag ends by releasing focus, or the arrow keys would steer the slider instead of the
// deck. A keyboard user keeps focus, and never needs it anyway: [ and ] work from anywhere.
veil.addEventListener("pointerup", () => veil.blur());

// details stays open on an outside click by default, and this one floats over the frame.
const menu = document.getElementById("mu");
addEventListener("pointerdown", (e) => { if (!menu.contains(e.target)) menu.open = false; }, true);
// Same reason the slider gives focus back: the key handler steps aside for a focused input, so a
// checkbox left focused by a click swallows every shortcut the rows above it advertise. It has to be
// the click and not the release, because clicking a row's words is the label's own activation moving
// focus into the box, which happens after pointerup. A detail of 0 is a keyboard activation, and a
// keyboard user keeps their place, exactly as they do on the slider.
menu.addEventListener("click", (e) => {
  if (e.detail && document.activeElement?.type === "checkbox") document.activeElement.blur();
});

// Scroll pans, ctrl or cmd with it zooms. That is the convention every design tool uses, and a
// trackpad pinch arrives as exactly this ctrl+wheel, so pinch works without a second code path.
deck.addEventListener("wheel", (e) => {
  e.preventDefault();
  const r = deck.getBoundingClientRect();
  if (e.ctrlKey || e.metaKey) zoomAt(Math.exp(-e.deltaY / 260), e.clientX - r.left, e.clientY - r.top);
  else { tx -= e.deltaX; ty -= e.deltaY; apply(); }
}, { passive: false });

// Drag anywhere to pan. The threshold keeps a plain click on a label, and its tooltip, intact.
//
// Every way a drag can end has to arrive here, because a drag whose end is missed keeps following the
// cursor with no button held down, and the grabbing cursor stays on. Three of them:
//   - pointerup, the ordinary one;
//   - pointercancel, which is what fires instead when the pointer is taken away. The screenshot used
//     to cause exactly that: an <img> is draggable by default, so a drag beginning on it started a
//     native image drag, the pointer was cancelled, and no pointerup ever came. draggable="false" on
//     the image is the real fix for that one, and this listener is the guard behind it;
//   - the button coming up somewhere the page never hears about, released outside the window. The
//     next move is the first news of it, so pointermove checks e.buttons before moving anything.
let drag = null;
const endDrag = () => {
  drag = null;
  document.body.classList.remove("panning");
};
deck.addEventListener("pointerdown", (e) => {
  // In select mode the drag belongs to the selection, and the wheel is left to move the view.
  if (e.button === 0 && !document.body.classList.contains("sel")) {
    drag = { x: e.clientX, y: e.clientY, tx, ty, on: false };
  }
});
addEventListener("pointermove", (e) => {
  if (!drag) return;
  if (!e.buttons) return endDrag();
  const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
  if (!drag.on && Math.hypot(dx, dy) < 3) return;
  if (!drag.on) { drag.on = true; document.body.classList.add("panning"); }
  tx = drag.tx + dx;
  ty = drag.ty + dy;
  apply();
});
for (const ev of ["pointerup", "pointercancel"]) addEventListener(ev, endDrag);

deck.addEventListener("dblclick", (e) => {
  const r = deck.getBoundingClientRect();
  if (z === 1) fitView();
  else zoomAt(1 / z, e.clientX - r.left, e.clientY - r.top);
});

addEventListener("keydown", (e) => {
  if (e.target.tagName === "INPUT") return;
  // Every shortcut here is unmodified, and ctrl+C has to stay the copy the reader expects while a
  // selection is up. Bailing on any modifier keeps both true with one line.
  if (e.ctrlKey || e.metaKey || e.altKey) return;
  const k = e.key.toLowerCase();
  if (k === "t") {
    show(ALL[(ALL.indexOf(current) + 1) % ALL.length]);
  }
  // Which label the pointer is on is something the browser already tracks, and scoping the query to
  // the visible slide is also what keeps a label of the slide just walked away from out of it.
  if (k === "c") {
    const on = slides[at].querySelector(".t:hover");
    if (on) copyLabel(on);
    else copyFrame();
  }
  // Firefox opens its own quick-find on a bare slash, which would take the keystrokes this panel
  // wants. F is the same door for anyone who reaches for a letter.
  if (k === "/" || k === "f") { toggleFind(); e.preventDefault(); }
  if (k === "s") sx.click();
  if (k === "o") document.getElementById("ol").click();
  if (k === "g") document.body.classList.toggle("gridon");
  if (k === "escape") { document.body.classList.remove("gridon"); menu.open = false; closeFind(); }
  if (k === "0" || k === "z") fitView();
  if (k === "1") zoomAt(1 / z, ...mid());
  if (k === "+" || k === "=") zoomAt(1.25, ...mid());
  if (k === "-" || k === "_") zoomAt(0.8, ...mid());
  if (k === "[") setVeil(Number(veil.value) - 8);
  if (k === "]") setVeil(Number(veil.value) + 8);
  if (e.key === "ArrowRight" || e.key === "PageDown" || e.key === " ") { go(at + 1); e.preventDefault(); }
  if (e.key === "ArrowLeft" || e.key === "PageUp") go(at - 1);
});
// Resizing keeps the reader's zoom; only the clamp is recomputed. Refitting here would throw away a
// view they had just set up.
addEventListener("resize", () => { sizeDeck(); apply(); });

// ?lang=vi&f=3 (or #vi) opens straight into that language and slide.
const p = new URLSearchParams(location.search);
const want = p.get("lang") ?? location.hash.slice(1);
sizeDeck();
go(Number(p.get("f") || 1) - 1);
fitView();
show(ALL.includes(want) ? want : SRC);
// Inter may still be loading, and a label measured in the fallback face reports the wrong width.
if (document.fonts?.ready) document.fonts.ready.then(relayoutAll);
</script>
</body>
</html>
`;

writeFileSync(out, html, "utf8");
console.log(
  JSON.stringify(
    {
      html: out,
      frames: frames.map((f) => ({ frame: f.frame, items: f.items.length })),
      items: frames.reduce((n, f) => n + f.items.length, 0),
      langs,
      selfContained: true,
      bytes: statSync(out).size,
      missingTranslations: [...new Set(missing)],
      flatFrames: flat,
      open: `file://${out}`,
    },
    null,
    2,
  ),
);
if (missing.length) process.exitCode = 1;
