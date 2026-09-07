// Builds a fixture deck for checking build-preview.mjs by eye, with no Figma call and no skill run.
//
// Usage: node make-fixture.mjs [--out <dir>]
//
// The output is one throwaway directory holding synthetic screenshots, a data.json and the built
// preview.html, by default under the system temp dir so it never lands in the repo. The path is
// stable, so editing the renderer and running this again is a save-and-reload loop in the browser.
//
// The screenshots are drawn here rather than downloaded: white page, a header band, cards, a 100px
// grid, and a grey bar behind every text item at its own box. There is no font, so the bars stand in
// for the words. That is enough for what the fixture is for, since the bar is drawn at the item's
// frame coordinates plus the render-bounds offset: if the renderer's offset maths breaks, the labels
// stop sitting on their bars, and the grid shows by how much.
//
// What the three frames deliberately cover:
//
// | Frame | Case |
// | --- | --- |
// | Checkout_01 | no effect bleed, offset {0,0}; three labels sharing a row, so spreading has to push them apart; a translation wider than its container, so one label must come out red and the bar must count 1; a two-line paragraph, for `white-space: pre` and for the \n escaping in the TSV copy |
// | Checkout_02_Confirm | a shadow bleeding past the frame on every side, so `offset` is non-zero and the png is larger than the box: the labels only stay on their bars if the renderer shifts the image by that bleed. The bleed itself stays invisible, since the screenshot is clipped to the frame. Also a label at the right edge whose translation runs past it, which must spill rather than clip |
// | Checkout_03_Done | a narrow frame, so switching slides changes the pan clamp and the fit |
//
// Two target languages, so the tooltip has two lines to show, T cycles three ways, and the TSV copy
// has to emit three columns.
import { deflateSync } from "node:zlib";
import { mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const here = dirname(fileURLToPath(import.meta.url));
const argv = process.argv.slice(2);
const at = argv.indexOf("--out");
const out = at >= 0 && argv[at + 1] ? resolve(argv[at + 1]) : join(tmpdir(), "peek-screen-fixture");
// One list of target languages: the deck declares it, and it names the translations `it()` takes.
const LANGS = ["vi", "en"];
mkdirSync(out, { recursive: true });

// ---------------------------------------------------------------- png, written by hand
// A real png so the page can inline it as one, and node ships everything needed: zlib for the pixel
// data, and a crc32 per chunk, which is the only part the standard library does not already have.
const CRC = new Int32Array(256).map((_, n) => {
  let c = n;
  for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
  return c;
});
const crc32 = (buf) => {
  let c = -1;
  // Indexed rather than for-of: a Buffer iterator boxes every one of the ~20 KB of bytes per run.
  for (let i = 0; i < buf.length; i++) c = CRC[(c ^ buf[i]) & 0xff] ^ (c >>> 8);
  return (c ^ -1) >>> 0;
};
const chunk = (type, data) => {
  const len = Buffer.alloc(4);
  len.writeUInt32BE(data.length);
  const body = Buffer.concat([Buffer.from(type, "latin1"), data]);
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(body));
  return Buffer.concat([len, body, crc]);
};

function canvas(w, h) {
  const px = Buffer.alloc(w * h * 3, 0xff);   // starts white, so a white rectangle has nothing to do
  return {
    // Clipped once for the whole rectangle, then one row filled and memcpy'd down the rest. Per-pixel
    // writes cost about six million calls for these three frames, and this costs a few thousand.
    rect(x, y, rw, rh, c) {
      const x0 = Math.max(0, Math.round(x));
      const y0 = Math.max(0, Math.round(y));
      const x1 = Math.min(w, Math.round(x + rw));
      const y1 = Math.min(h, Math.round(y + rh));
      if (x1 <= x0 || y1 <= y0) return;
      const from = (y0 * w + x0) * 3;
      const to = from + (x1 - x0) * 3;
      px.fill(Buffer.from(c), from, to);
      for (let yy = y0 + 1; yy < y1; yy++) px.copy(px, (yy * w + x0) * 3, from, to);
    },
    png() {
      const stride = w * 3 + 1;
      const raw = Buffer.alloc(h * stride);
      for (let y = 0; y < h; y++) {
        raw[y * stride] = 0; // filter: none
        px.copy(raw, y * stride + 1, y * w * 3, (y + 1) * w * 3);
      }
      const ihdr = Buffer.alloc(13);
      ihdr.writeUInt32BE(w, 0);
      ihdr.writeUInt32BE(h, 4);
      ihdr[8] = 8; // bit depth
      ihdr[9] = 2; // truecolour rgb
      return Buffer.concat([
        Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
        chunk("IHDR", ihdr),
        chunk("IDAT", deflateSync(raw, { level: 9 })),
        chunk("IEND", Buffer.alloc(0)),
      ]);
    },
  };
}

const INK = [0x3c, 0x41, 0x4c];
const BAR = [0xc8, 0xcd, 0xd6];
const CARD = [0xf2, 0xf4, 0xf8];
const LINE = [0xe4, 0xe8, 0xef];
const BRAND = [0x7c, 0x8c, 0xff];
const SHADOW = [0xd8, 0xdb, 0xe2];

// ---------------------------------------------------------------- the deck
// x, y, w, h, cw, size, style, src, then one translation per entry of LANGS, in that order. The
// geometry is the frame's own coordinate space, exactly as step 2 of the skill reports it.
const it = (x, y, w, h, cw, size, style, src, ...tr) => ({
  x, y, w, h, cw, size, style, src,
  t: Object.fromEntries(LANGS.map((l, i) => [l, tr[i]])),
});

const frames = [
  {
    frame: "Checkout_01",
    png: "01-Checkout_01.png",
    figmaUrl: "https://www.figma.com/design/FIXTURE/peek-screen-fixture?node-id=1-1",
    box: { w: 1280, h: 900 },
    render: { w: 1280, h: 900 },
    offset: { x: 0, y: 0 },
    items: [
      it(40, 26, 96, 24, 240, 16, "Bold", "お支払い", "Thanh toán", "Payment"),
      it(1064, 24, 72, 22, 96, 14, "Regular", "ログアウト", "Đăng xuất", "Sign out"),
      // Three labels on one line, close together: every translation is longer than its original, so
      // the row cannot hold them at their anchors and spreading has to push the later two right.
      it(40, 120, 40, 20, 200, 14, "Medium", "商品", "Sản phẩm", "Item"),
      it(96, 120, 40, 20, 200, 14, "Medium", "数量", "Số lượng", "Quantity"),
      it(152, 120, 40, 20, 200, 14, "Medium", "小計", "Tạm tính", "Subtotal"),
      // cw is 88 while the Vietnamese runs far past it: this is the label that must come out red and
      // the one the bar has to count.
      it(40, 170, 80, 20, 88, 14, "Regular", "配送方法", "Phương thức vận chuyển", "Shipping method"),
      // A hard line break, for `white-space: pre` on the page and for the \n escape in the TSV copy.
      it(
        40, 230, 420, 44, 600, 13, "Regular",
        "ご注文内容をご確認ください。\n変更する場合は前の画面に戻ってください。",
        "Vui lòng kiểm tra lại đơn hàng.\nMuốn sửa thì quay lại bước trước.",
        "Please review your order.\nGo back to the previous step to change it.",
      ),
      it(40, 780, 200, 48, 240, 16, "Semibold", "注文を確定する", "Xác nhận đặt hàng", "Place order"),
      it(1000, 792, 120, 24, 160, 14, "Regular", "キャンセル", "Huỷ", "Cancel"),
    ],
  },
  {
    frame: "Checkout_02_Confirm",
    png: "02-Checkout_02_Confirm.png",
    figmaUrl: "https://www.figma.com/design/FIXTURE/peek-screen-fixture?node-id=1-2",
    box: { w: 1280, h: 720 },
    // A shadow bleeding past the frame: the png is larger than the box, and offset is the difference.
    render: { w: 1336, h: 758 },
    offset: { x: 28, y: 19 },
    items: [
      it(40, 26, 160, 24, 320, 16, "Bold", "確認", "Xác nhận", "Confirm"),
      it(40, 120, 240, 20, 320, 14, "Regular", "お支払い方法", "Phương thức thanh toán", "Payment method"),
      // Hard against the right edge, with a translation that cannot fit before it: the label has to
      // hang past the white area rather than being clipped or dragging its row leftwards.
      it(1080, 120, 160, 20, 168, 14, "Regular", "クレジットカード", "Thẻ tín dụng quốc tế", "Credit card"),
      it(40, 600, 200, 48, 240, 16, "Semibold", "支払う", "Thanh toán", "Pay"),
    ],
  },
  {
    frame: "Checkout_03_Done",
    png: "03-Checkout_03_Done.png",
    figmaUrl: "https://www.figma.com/design/FIXTURE/peek-screen-fixture?node-id=1-3",
    // Narrow and tall, so walking to this slide changes both the fit and the pan clamp.
    box: { w: 720, h: 900 },
    render: { w: 720, h: 900 },
    offset: { x: 0, y: 0 },
    items: [
      it(40, 300, 280, 28, 640, 20, "Bold", "ありがとうございました", "Xin cảm ơn quý khách", "Thank you"),
      it(40, 360, 360, 20, 640, 14, "Regular", "注文番号: {orderId}", "Mã đơn hàng: {orderId}", "Order number: {orderId}"),
      it(40, 800, 200, 48, 240, 16, "Semibold", "ホームに戻る", "Về trang chủ", "Back to home"),
    ],
  },
];

// Draws the screenshot a frame would have had. Everything sits in png coordinates, which are the
// frame's own shifted by the bleed, so the bars land exactly where the labels will.
function draw(f) {
  const c = canvas(f.render.w, f.render.h);
  const ox = f.offset.x;
  const oy = f.offset.y;
  // The canvas is already white, so a frame with no bleed needs neither of these: only a frame whose
  // png is larger has to be shadowed all over and then have its own white area put back.
  if (ox > 0 || oy > 0) {
    c.rect(0, 0, f.render.w, f.render.h, SHADOW);
    c.rect(ox, oy, f.box.w, f.box.h, [0xff, 0xff, 0xff]);
  }
  // A 100px grid inside the frame, for reading an offset error off the page directly.
  for (let x = 100; x < f.box.w; x += 100) c.rect(ox + x, oy, 1, f.box.h, LINE);
  for (let y = 100; y < f.box.h; y += 100) c.rect(ox, oy + y, f.box.w, 1, LINE);
  c.rect(ox, oy, f.box.w, 72, CARD); // header band
  c.rect(ox, oy + 72, f.box.w, 1, LINE);
  c.rect(ox + 24, oy + 100, f.box.w - 48, f.box.h - 220, CARD); // the content card
  for (const i of f.items) {
    // One bar per line of the string, so a two-line paragraph reads as two.
    const lines = i.src.split("\n").length;
    const lh = i.h / lines;
    const strong = i.size >= 16;
    for (let n = 0; n < lines; n++) {
      c.rect(ox + i.x, oy + i.y + n * lh + lh * 0.18, i.w, Math.max(2, lh * 0.62), strong ? INK : BAR);
    }
  }
  // The primary action, so the veil slider has a saturated colour to be judged against.
  const cta = f.items.find((i) => i.style === "Semibold");
  if (cta) {
    c.rect(ox + cta.x - 12, oy + cta.y - 12, cta.cw, cta.h + 24, BRAND);
    c.rect(ox + cta.x, oy + cta.y + 6, cta.w, 12, [0xff, 0xff, 0xff]);
  }
  writeFileSync(join(out, f.png), c.png());
}

for (const f of frames) draw(f);

const data = {
  sourceLang: "ja",
  langs: LANGS,
  figmaUrl: "https://www.figma.com/design/FIXTURE/peek-screen-fixture",
  frames,
};
writeFileSync(join(out, "data.json"), JSON.stringify(data, null, 2) + "\n", "utf8");
console.log("fixture written to " + out);

const r = spawnSync(process.execPath, [join(here, "build-preview.mjs"), join(out, "data.json")], {
  stdio: "inherit",
});
if (r.status !== 0) process.exit(r.status ?? 1);

// What to look at, in the order the page shows it. Printed rather than documented elsewhere, so it
// stays beside the fixture it describes.
console.log(`
check by eye:
  1  labels sit on their grey bars, on every slide and at every zoom  (O outlines them)
  2  Checkout_01 in Vietnamese: 商品 / 数量 / 小計 spread apart, none moved left of its bar
  3  Checkout_01 reports exactly one overflow in the bar, 配送方法 underlined red, badged on the grid
  4  Checkout_02: labels still on their bars though the png is bigger than the frame, and クレジットカード hangs past the right edge
  5  click any label: toast, and the clipboard holds ja / vi / en on three lines
  6  menu: copy this frame, then the whole deck; the paragraph's line break arrives as \\n, one row
  7  S, then drag across two labels: text marks instead of panning; ctrl+C keeps it; wheel still pans
  8  veil slider and [ ] fade the screenshot back in; the blue button colour returns
  9  / then "thanh toan": 3 matches in 2 frames and no ring yet, since the match is Vietnamese and
     Japanese is on screen; enter switches language, rings all three and walks them; "don hang"
     finds đơn hàng without the diacritics, and "支払" finds the source side from any language

expected here, not a defect:
  flatFrames names all three slides. These pngs are drawn by hand out of solid blocks, so they
  compress like the flat renders that check is looking for. A real screenshot does not, by a
  factor of about eight, which is what makes the check worth having against Figma.`);
