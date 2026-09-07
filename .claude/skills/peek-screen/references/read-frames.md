# Step 2: the read call

One `use_figma` call per file. Set `IDS` to that file's ids in slide order, and `SELF` to true only
when `--self` was passed. Everything else runs as written.

```js
const IDS = ["1:234"];   // as given, in slide order
const SELF = false;            // true when --self was passed
const r2 = (v) => Math.round(v * 100) / 100;
const HOLDS = new Set(["FRAME", "COMPONENT", "INSTANCE", "SECTION"]);

const holders = (n) =>
  (n.children ?? []).filter(
    (c) => c.visible !== false && HOLDS.has(c.type) && c.absoluteBoundingBox,
  );
const hasText = (n) => {
  if (n.visible === false) return false;
  if (n.type === "TEXT") return n.characters.trim() !== "";
  return (n.children ?? []).some(hasText);
};
// A group holding one frame is packaging, not a screen boundary, and its name is usually the stale
// "Group 1321". Descend through it so the slide carries the frame's own name.
const unwrap = (n) => {
  let f = n;
  while (f.type === "GROUP") {
    const h = holders(f);
    if (h.length !== 1) break;
    f = h[0];
  }
  return f;
};
// No screen mock is three thousand points wide. A node that big holding several text-bearing frames
// is a board, and the frames inside it are the screens. This is the one thing geometry decides: which
// of those frames the user wants is a judgement about their names, made in SKILL.md, not here.
const screenish = (b) => b && b.width <= 2600 && b.height <= 9000;

const out = [];
for (const id of IDS) {
  const n0 = await figma.getNodeByIdAsync(id);
  if (!n0) { out.push({ id, error: "null" }); continue; }
  // A page that is not the open one has unloaded children, and reading them throws.
  if (n0.type === "PAGE") await n0.loadAsync();
  const n = unwrap(n0);
  // A page is not an object on the canvas, so it has no box and no render bounds. Every geometry
  // test below has to survive that, and a page is a board by definition anyway.
  const nb = n.absoluteBoundingBox;
  const kids = holders(n).map(unwrap).filter(hasText);
  const board = !SELF && kids.length >= 2 && !screenish(nb);

  if (board) {
    out.push({
      id: n.id, board: n.name, type: n.type,
      box: nb ? { w: nb.width, h: nb.height } : null,
      holds: kids.map((c) => {
        let t = 0;
        const count = (x) => {
          if (x.visible === false) return;
          if (x.type === "TEXT") { if (x.characters.trim()) t++; return; }
          (x.children ?? []).forEach(count);
        };
        count(c);
        return { id: c.id, name: c.name, type: c.type,
          w: r2(c.absoluteBoundingBox.width), h: r2(c.absoluteBoundingBox.height), texts: t };
      }),
    });
    continue;
  }

  // Boxless and not a board: one text-bearing child under a page, or a node type with no geometry.
  // Report it rather than reading x off undefined further down.
  if (!nb) { out.push({ id: n.id, name: n.name, type: n.type, error: "no bounding box" }); continue; }
  const bb = nb;
  const rb = n.absoluteRenderBounds;   // includes effect bleed: this is what the png covers
  const items = [];
  const walk = (x, parent) => {
    if (x.visible === false) return;   // an invisible ancestor hides its whole subtree
    if (x.type === "TEXT") {
      const b = x.absoluteBoundingBox;
      // Mixed-style text returns figma.mixed, a symbol, rather than throwing: reading .style off it
      // gives undefined, and a mixed fontSize serializes to null and lands in the css as
      // `font-size:nullpx`. Check the value, not just the access.
      let style = "Regular", size = 14;
      try { if (typeof x.fontName?.style === "string") style = x.fontName.style; } catch {}
      try { if (typeof x.fontSize === "number") size = x.fontSize; } catch {}
      items.push([r2(b.x - bb.x), r2(b.y - bb.y), r2(b.width), r2(b.height),
        r2(parent?.absoluteBoundingBox?.width ?? b.width), size, style, x.characters]);
      return;
    }
    if (x.children) x.children.forEach((c) => walk(c, x));
  };
  walk(n, null);

  out.push({
    id: n.id, frame: n.name, box: { w: bb.width, h: bb.height },
    render: { w: rb.width, h: rb.height },
    offset: { x: r2(bb.x - rb.x), y: r2(bb.y - rb.y) },
    count: items.length, items,
  });
}
return { item: "[x, y, w, h, cw, size, style, characters]", frames: out };
```

## Why it is shaped this way

Recurse rather than using `query('TEXT')`: a flat query also returns text inside collapsed or hidden
blocks, which is not on screen.

Each item is a tuple, not an object. A flow runs to several hundred strings, and the keys repeated on
every one of them are what push the response past the size it gets truncated at.

`cw` is the width of the node's **parent**, and it is the whole reason the overflow warning is worth
having. A TEXT node's own box hugs its glyphs, so measuring against that flags every translation
longer than the original, which is nearly all of them. The parent is what actually constrains the
component: a fixed-width tab, a role chip, a button. Measured against the parent, the warning fires
only where a real component cannot hold the language.
