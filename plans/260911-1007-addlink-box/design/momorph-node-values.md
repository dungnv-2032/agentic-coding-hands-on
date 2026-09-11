# MoMorph node values — Addlink Box (`OyDLDuSGEa`)

Read from `get_node` this session. **These are the authoritative visual values.** Anything not
listed here is unauthored and must be flagged as such in a code comment, never invented silently.

## Panel — `mm:1002:12682` ("Add link box")

| Property | Value |
|---|---|
| size | 752 × 388 |
| padding | 40px |
| gap (column) | 32px |
| border-radius | 24px |
| background | `rgba(255,248,225,1)` = `#FFF8E1` |
| layout | `flex`, column, `align-items: flex-start` |

Vertical rhythm this produces (y, inside the 40px padding): title 40–80 · Text row 112–168 ·
Link row 200–256 · button row 288–348. Content column width is 672px throughout.

## A — Title `mm:I1002:12682;1002:12500`

`"Thêm đường dẫn"` · Montserrat 700 · 32px / 40px line-height · letter-spacing 0 · `#00101A` ·
width 672 · text-align left.

## B — Text row `mm:I1002:12682;1002:12501`

Row frame: 672 × 56 · `flex`, row · gap 16px · `align-items: center`.

- **B.1 label** `mm:I1002:12682;1002:12502;416:5534` — `"Nội dung"` · Montserrat 700 · 22px / 28px ·
  `#00101A` · intrinsic width 107px (x 40→147).
- **B.2 input** `mm:I1002:12682;1002:12503` — `flex: 1 0 0` · height 56 · border `1px solid #998C5F` ·
  background `#FFF` · padding `16px 24px` · border-radius 8px · `justify-content: space-between`.
  Occupies x 163→712.

## C — Link row `mm:I1002:12682;1002:12652`

Same row shape as B (672 wide, 56 tall, gap 16, centered).

- **C.1 label** `mm:I1002:12682;1002:12653;416:5534` — `"URL"` · Montserrat 700 · 22px / 28px ·
  `#00101A` · intrinsic width 47px (x 40→87).
- **C.2 input** `mm:I1002:12682;1002:12654` — same box treatment as B.2.

**The labels are NOT a fixed-width column.** 107px vs 47px are intrinsic text widths, and the two
inputs therefore start at different x — visible in the frame image. Reproduce that (plain flex row
with a 16px gap), do not invent an aligned label column.

## D — Button row `mm:I1002:12682;1002:12543`

Row frame: 672 × 60 · `flex`, row · gap 24px · `align-items: flex-start`.

- **D.1 `Hủy`** `mm:I1002:12682;1002:12544` — width 146 (x 40→186) · padding `16px 40px` ·
  gap 8px · border `1px solid #998C5F` · background `rgba(255,234,158,0.10)` ·
  **border-radius 4px** · icon `MM_MEDIA_Close` (`mm:I1002:12682;1002:12544;186:2761`) after the label.
- **D.2 `Lưu`** `mm:I1002:12682;1002:12545` — width 502 × 60 (x 210→712) · padding 16px · gap 8px ·
  `justify-content: center` · background `rgba(255,234,158,1)` = `#FFEA9E` ·
  **border-radius 8px** · icon `MM_MEDIA_Link` (`mm:I1002:12682;1002:12545;186:1766`) after the label.

The two radii genuinely differ in the design (4px vs 8px). Reproduce both; do not normalise them.
`Lưu` takes the remaining width — 502 of 672 after `Hủy`'s 146 and the 24px gap — so `flex-1` on
`Lưu` with `Hủy` at its intrinsic width reproduces it responsively.

## Not in the design (unauthored — flag in code)

- Error message styling and placement. The frame has no error state. Follow the screen's existing
  error convention (`#CF1322`, small text under the field) and say so in a comment.
- Focus ring colour. Item B.2's `description` says only "Focus: Hiện viền nổi".
- Hover states for either button.
- The overlay behind the dialog — the frame is the panel alone. Keep the shipped
  `fixed inset-0 bg-black/40` scrim.
