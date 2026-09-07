---
name: tkm:peek-screen
category: figma
roles: [engineer, qa]
description: >
  Read one Figma screen, or a whole flow of them, in another language fast. Produces a single
  self-contained HTML deck that overlays translations on screenshots: arrow keys walk the flow,
  hover any string for the pair, one key to switch language. Use when the goal is to understand
  what a screen says and where each string sits, not to produce a localized image. Triggers on:
  "what does this screen say", "peek at this Figma", "xem nhanh màn hình Figma",
  "dịch nhanh cái screen này", "dịch cả flow này", "この画面を訳して見せて",
  "translate these Figma frames so I can read them", "explain this mockup", or any Figma frame URL
  handed over with no deliverable named.
  Not for pixel-accurate localized exports, and not for screen specification documents.
argument-hint: "<figma-url> [<figma-url> …] [--nodes a-b,c-d] [--langs en,vi] [--source ja] [--self] [--out <dir>]"
metadata:
  author: takumi-agent-kit
  version: "1.2.0"
---

# Peek Screen

## What this is for

You want to know what a screen says and where each string sits. Nothing more. The output is
disposable, so expect it to be deleted the same day it is made.

A screen rarely stands alone, so the page is a deck: pass several frames and each becomes a slide in
one HTML file, walked with the arrow keys. The screenshots are inlined, so that file is the whole
deliverable. It opens from disk with no server and can be handed to someone else with nothing
attached.

**As few read calls as the 20 KB response ceiling allows, one screenshot per frame, one build. Do not
exceed that.** Every extra step costs the user minutes they did not ask to spend. Concretely, do not
export a frame as SVG, do not re-render the page to check it, do not measure text widths, and do not
write a report.

The cost comes from two places, and this skill avoids both:

| Avoided | Why it is expensive |
| --- | --- |
| Moving an SVG export through context | tens of KB read out, then written back byte for byte |
| Correcting text anchors by hand | SVG text cannot reflow, so every longer translation collides |

Here the pixels arrive by `curl` and are base64'd into the page by the build script, so they never
enter context. Labels float above the image, so collisions are spread apart by the page itself at
runtime.

One id for the board covers every candidate in it, and the screenshots are cheap because their bytes
go straight to disk. The text read is the one thing that does grow, and only because the response is
capped near 20 KB: a screen of ~130 strings runs about 9 KB, so two frames per call is safe and three
truncate. Seventeen screens is nine calls, not seventeen.

If the user needs a picture to hand to someone else, or a crisp export, this is the wrong skill.
Say so and stop rather than approximating it.

## Scope

Handles: reading the visible text out of one or more Figma frames, translating it, and emitting one
self-contained HTML deck that overlays the translations on screenshots of those frames.

Does NOT handle: writing anything back to Figma, pixel-accurate localized exports, screen
specification documents, or implementing the design as code. It is read-only against Figma, which is
worth stating plainly: every call it makes is a read, so it cannot disturb a file other people have
open.

The Figma MCP asks for its `figma-use` skill before any `use_figma` call. That guards writes. Step 2
only reads, and its code is given here in full, so do not spend a call loading it.

One safety note: `get_screenshot` returns a short-lived signed URL. Treat it as a secret, `curl` it
straight to disk, and do not paste it into a report or a commit.

## Invocation

```
tkm:peek-screen <figma-url> [<figma-url> …] [--nodes <a-b,c-d>] [--langs en,vi] [--source ja] [--self] [--out <dir>]
```

| Argument | Default | Meaning |
| --- | --- | --- |
| `<figma-url>` | required | One or more URLs, each pointing at a frame **or** at a board holding several. Slide order is the order given |
| `--nodes` | none | Extra node ids for the *last* URL's file, as `a-b,c-d`. Shorthand for same-file frames |
| `--langs` | `vi` | Comma-separated target languages. `--lang` is accepted too |
| `--source` | `src` | Language of the design, for the button label. Omit for a neutral "Original" |
| `--self` | off | Read each id as exactly one slide. Turns off the container expansion in step 2 |
| `--out` | `./peek/<first-slide>/` | Output directory. From a board id the first slide is only known once step 2 expands it, so name the directory then. When the deck is a whole board, name it after the board (`./peek/checkout/`) rather than slide 1. When the slides share no name stem, name it after what the set is for (`./peek/signup-and-profile/`), since slide 1 then describes none of it |

## Step 1: resolve the frames

From `https://www.figma.com/design/<fileKey>/<name>?node-id=<a>-<b>`: `fileKey` is the segment after
`/design/`, `nodeId` is `<a>:<b>` (the URL separates with `-`, the API with `:`). With no `node-id`,
stop and ask for a URL that names something.

An id does not have to be one screen. Selecting the section or the group that holds a flow gives one
id for the whole set, and step 2 expands it into one slide per child frame, so `--nodes` is only
needed for frames that do not share a parent. Nothing here has to be decided in advance: pass the id
the user gave and read what comes back.

When `--nodes` names frames explicitly and the URL's own `node-id` turns out to be a page or a board,
the explicit list is the deck: keep the URL for its `fileKey` and drop its id rather than spending a
read on a manifest nobody will choose from.

Group the ids by `fileKey`. Step 2 reads one file per call, so frames from two files cost two reads;
frames from one file cost one, however many there are, and a whole board costs one.

Skip `get_metadata`. `getNodeByIdAsync` in step 2 resolves each id directly and returns the frame
name, which is all that is needed. If one returns `null`, that id did not resolve: list the pages
with `figma.root.children.map((p) => ({ id: p.id, name: p.name }))`, then query each page by frame
name in parallel, one `setCurrentPageAsync` per call.

## Step 2: read the text, two frames per call

Run the code in `references/read-frames.md` verbatim as the `use_figma` code, with `IDS` set to that
file's ids in slide order, and `SELF` true when `--self` was passed **or when these ids came from
expanding a board**, since an expanded id is already exactly one slide. Pass at most two ids per call once
the ids are known frames, one for a frame past ~170 strings. A board manifest costs one call however
many candidates it lists, because it carries no text.

Per id it returns either a frame — its name, `box`, `render`, `offset`, and an `items` array of
`[x, y, w, h, cw, size, style, characters]` tuples — or, when the id holds several text-bearing
frames and is far too large to be a screen, a board manifest carrying `holds` instead of `items`.

`cw` is the width of the text node's **parent**, which is what makes the overflow warning worth
having; the reference explains why, along with the tuple encoding and the recursion.

A response can be truncated. If one is, re-read only the frames that did not arrive, never the
whole file.

**An entry with `holds` instead of `items` is a board, and choosing from it is yours to do.** The
manifest gives each candidate's name, size and string count and no text at all, so it stays small
whether the board holds three screens or sixty. Pick the ones the request is actually about. A flow
usually shares a name stem, while `texts: 0`, a stray `Component`, or a size unlike every other
candidate is noise. Then run this same call again with those ids as `IDS`. That second read is the
cost of having linked a board instead of a frame. A candidate that is itself board-sized costs a
third read to expand; say so before spending it, and stop there. Boards are
common enough that a page-level id can list a hundred entries: if the pick is not obvious from the
names, ask the user rather than guessing at a deck they will have to check frame by frame.

## Step 3: one screenshot per frame

Now that the ids are known, one `get_screenshot` per frame in the read's order, all in one message,
each with **`maxDimension` at least that frame's `render.w`**. The default of 1024 downscales any
wider frame and blurs it. `maxDimension` only caps and never upscales, so pass a value comfortably
above any frame width, such as 4096, and the result is 1:1.

Then `curl` every returned URL in a single command, and prefix each filename with its slide number so
two frames sharing a name cannot overwrite each other:

```bash
curl -sL -o 01-Checkout_01.png "<url-1>" -o 02-Checkout_02.png "<url-2>"
```

The pixels must not pass through context.

`get_screenshot` renders what the canvas shows, so a layer lying over the frame is rendered instead
of the frame. Where a board carries a dimming layer across its screens, every png comes back as one
flat colour, and nothing later in this skill notices: the item counts are right and no translation
is missing. Step 5 measures each png and names the flat ones; re-shoot only those, passing
`contentsOnly: true` to render the frame in isolation. Do not pass it on the first attempt or as a
blanket default, because it also drops arrows and connectors parented to the page, which is exactly
what a diagram frame is made of.

Keep slide number, node id, frame name and png filename together as one record from here on. Once the
reads arrive in batches that quadruple is the only thing tying a png to its frame, and no later step
can detect a mismatch.

## Step 4: write `<out>/data.json`

Expand each tuple back into an object under the names step 2's `item` key gives, keeping each frame's
`box`, `render` and `offset` as they came. Drop `count` and `id`, add each frame's `png` and its
`figmaUrl` (the node id with `:` written as `-`), and wrap the array with `sourceLang` and `langs`.
Every item gains a `t` object:

```json
{
  "sourceLang": "ja",
  "langs": ["vi"],
  "frames": [
    {
      "frame": "Checkout_01",
      "figmaUrl": "https://www.figma.com/design/…?node-id=1-234",
      "png": "01-Checkout_01.png",
      "box": { "w": 1280, "h": 898 },
      "render": { "w": 1336, "h": 917 },
      "offset": { "x": 28, "y": 19 },
      "items": [
        { "x": 1068, "y": 17, "w": 56, "h": 22, "cw": 128, "size": 14, "style": "Regular",
          "src": "お支払い方法", "t": { "vi": "Phương thức thanh toán" } }
      ]
    }
  ]
}
```

A single frame is a one-slide deck, written the same way. A file that carries `items` at the root
with no `frames` is the older single-frame shape and is still accepted.

Past roughly 400 items, do not hand-write the `t` objects. A flow repeats itself hard: a couple of
thousand items across a dozen-odd screens routinely collapse to a hundred-odd distinct strings, with
a single form marker such as `必須` accounting for hundreds of them. Write each read's payload
to `<out>/raw/<n>.json` as it arrives, translate the distinct strings once into `<out>/dict.json` as
`{"<src>": {"<lang>": "…"}}`, and join the two with a short script that stamps `png` and `figmaUrl`
and reports any `src` the dict misses. The dictionary is also what makes a recurring string identical
across frames rather than merely intended to be, and it is the one part of the output worth keeping:
leave `raw/`, `dict.json` and the join script beside the deck rather than clearing them.

Translating:

- Keep `{...}` runtime placeholders including the braces, brand and product names, dates, and sample
  values exactly as they are. One exception, and the test is mechanical: translate inside the braces
  only when what they hold carries source-script characters — kana or kanji for Japanese, as in
  `{選択した項目}`. That is a designer's stand-in, not a code token, and left alone it makes an empty
  state read as untranslated in the one place the reader is looking. Braces holding plain ASCII,
  `{userName}` or `{count}`, are a real runtime token: keep them byte for byte.
- Look for a glossary or screen index the repository already owns before coining a term, and prefer
  its wording. A screen's official name usually already exists somewhere in the docs. Across a flow
  this matters more than on one screen: the same string recurs in a header, a breadcrumb and a
  button, and it must read identically in all three.
- Romanize personal names (Japanese `佐藤 花子` becomes `Hanako Sato` in English, `Sato Hanako` in
  Vietnamese and other family-name-first conventions).
- Follow whatever house style the user has set for the target language.
- **Do not shorten to fit.** The page spreads labels itself and marks anything that overflows its
  container, so a constraint stays visible instead of being hidden inside a compromise. This is the
  opposite of what a fixed-layout renderer demands.

## Step 5: build

```bash
# <skill-dir> is the directory holding this SKILL.md. When that path is not already known, one find
# resolves it wherever the skill was installed from, which is not always under ~/.claude:
#   find ~/.claude ~/.config/claude ~/develop -name build-preview.mjs -path '*peek-screen*' 2>/dev/null | head -1
node <skill-dir>/scripts/build-preview.mjs <out>/data.json
```

It prints the `file://` URL to open, the per-frame item counts, and `missingTranslations`, which must
be empty. Hand the user the URL and stop.

## Changing the renderer

Not part of a run. `node <skill-dir>/scripts/make-fixture.mjs` builds a deck from synthetic frames,
with no Figma call, and prints what to check; its header comment says which cases it covers.

## The page

- One slide per frame on a pannable canvas, opened fitted to the window. Drag anywhere to move,
  scroll to move, ctrl or cmd with scroll to zoom about the cursor, and a trackpad pinch does the
  same. <kbd>0</kbd> refits, <kbd>1</kbd> goes to 100%, <kbd>+</kbd> and <kbd>-</kbd> step, and a
  double click flips between the two. This is what makes a laptop usable: fitting a 1280px frame
  into a 900px-tall window shrinks the text below reading size, and the answer is to move the view
  rather than to squint.
- <kbd>&larr;</kbd> <kbd>&rarr;</kbd> walk the flow, <kbd>G</kbd> opens a grid of all frames. Zoom and
  pan are shared across slides, so stepping through a flow holds the same region of each screen under
  the eye, which is how two frames get compared.
- Buttons, or <kbd>T</kbd>, switch language. `?lang=vi&f=3` opens straight into one language and
  slide, so a link carries the finding.
- The source language shows the untouched screenshot. Hover any string for its translation.
- A target language veils the screenshot and draws every label in place, so the whole screen reads at
  once with the original layout still visible underneath as a ghost.
- The veil slider, or <kbd>[</kbd> and <kbd>]</kbd>, sets how much of the screenshot that ghost keeps.
  Drag it left and the design comes back through the labels, colours and all, which is how a reader
  judges the layout rather than only the words. All the way left is the bare screenshot with the
  translation floating over it.
- The text comes back out. A click on a label copies the original and every translation of it at
  once, which is the shape a ticket or a glossary wants; <kbd>C</kbd> does the same for the label
  under the cursor, and with the cursor off any label it copies the whole frame. The menu copies one
  frame or the whole deck as TSV, one row per string, one column per language. <kbd>S</kbd>, or the
  same menu, hands the drag over to text selection for the one thing a whole-label copy cannot do,
  which is marking part of a phrase.
- <kbd>/</kbd> or <kbd>F</kbd> finds a string in every language at once, which the browser's own find
  cannot: one language is in the layout at a time and the other slides are hidden from it. Case and
  diacritics are ignored, so `phuong thuc` finds `Phương thức`. A match is ringed in place only in the
  language that matched; the panel lists all of them, grouped by frame, and <kbd>Enter</kbd> walks
  them, centring each at the reader's own zoom.
- Labels that would collide are spread apart at runtime, always rightwards: a label never moves left
  of the anchor the design gave it, and one that runs past the frame's right edge spills over it
  rather than being clipped or dragging its neighbours along. No anchor is corrected by hand.
- A red underline marks a translation wider than its Figma container. The bar counts them for the
  current slide, and the grid badges every frame with a count, so the frames that cannot hold this
  language are visible before the reader walks to them. That count is the finding an implementer
  needs.
- <kbd>O</kbd> outlines every text box, for confirming the overlay lines up with the image.

## Verification

Five checks, all free:

- `missingTranslations` is empty, and each frame's printed item count matches its `count` from step 2.
- `flatFrames` is empty. An entry there is a png that compressed like a solid fill, which is usually
  a frame that rendered as an overlay rather than as itself: re-shoot it per step 3. A frame that is
  genuinely near-blank, an empty state, lands there too and is fine once you have looked at it.
- Every frame's `offset` equals `box.xy` minus `render.xy`. `{0,0}` with `render` equal to `box` is a
  frame with no effect bleed and is correct; `{0,0}` while `render` is larger than `box` means the png
  and the overlay are in different coordinate spaces and every label will sit low and left.
- The printed `frames` array is in the order the user asked for. Slide order is data order; nothing
  sorts it.
- The slide count matches what the ids should have resolved to. An expansion that returned one slide
  for a board, or a screen's own parts as several slides, is visible here and nowhere later.

Then stop. The page reports its own layout findings, and the user is about to look at it.

## Known gotchas

Eleven of them, one line each, in `references/gotchas.md`. Read it when the output looks wrong: stale
layer names, duplicate frame names, mixed-style text, labels sitting outside the frame, page size,
or a target language the default font does not cover.
