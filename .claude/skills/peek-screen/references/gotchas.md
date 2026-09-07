# Known gotchas

- **Layer names go stale.** A layer often still carries the name of the feature it was duplicated
  from, which can differ entirely from what the frame renders. `characters` is authoritative; flag
  the disagreement to the user rather than trusting the name. The `unwrap` step in step 2 handles the
  most common case, a `Group 1234` wrapped around the frame the user actually linked.
- **Duplicate frame names.** Two frames in a flow are often both called something like `Default`.
  The slide label uses the name as given, so number the pngs and expect the deck to show repeats.
- **Look-alike glyphs.** A circled letter such as U+24C7 reads as the registered-trademark sign at
  screenshot resolution. Always take glyphs from `characters`, never retyped from an image.
- **Mixed-style text** returns `figma.mixed` instead of throwing, so the item falls back to Regular
  14 only because step 2 type-checks the value. The string itself is still complete, and unlike an
  SVG export a mixed-weight paragraph stays one item here instead of splitting into two.
- **A tall paragraph can capture a short neighbour.** Row grouping is by vertical overlap, so a label
  beside a multi-line paragraph joins that paragraph's row. Since spreading only ever pushes right
  and only on a real collision, a label with room to spare stays put; the pairing costs nothing
  unless the two genuinely overlap.
- **Labels may sit outside the frame.** Only the screenshot is clipped to the frame, never the text
  over it, so a long translation at the right edge hangs past the white area. That is deliberate: it
  is the honest picture of a string the layout cannot hold, and it is marked in red as well.
- **The page carries its own pixels.** Every png is base64'd into the html, which runs about 1.35x
  the file size on disk. A dozen frames is a couple of megabytes, which is fine; a hundred is not.
- **The background is a bitmap**, so zooming blurs it, and the original text remains inside the image
  under the veil. For a crisp or shareable picture, render the frame properly instead.
- **A whole board can render as one flat colour.** `get_screenshot` draws what the canvas shows, so
  a dimming layer over a board is rendered in place of the screens under it. Step 5's `flatFrames`
  is what catches it; re-shoot those frames with `contentsOnly: true`, and only those, since it also
  drops page-parented arrows and connectors.
- **`get_screenshot` returns a short-lived URL.** Treat it as a secret and `curl` it immediately.
- **Non-Latin target languages need a font that covers them.** The page asks for Inter first and
  falls back to the system stack, which is fine for Latin and Vietnamese; check the render if the
  target is Thai, Devanagari, or similar.
