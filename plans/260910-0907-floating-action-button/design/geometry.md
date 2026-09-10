# Measured geometry — MoMorph (authoritative, never guessed)

Canvas both frames: 1440×1024, `bg rgba(0,16,26,1)` (`#00101A`).

## Collapsed — screen `_hphd32jN2`, node `313:9138` (`A_Widget Button`)
- absolute, bounds `(1191,840)-(1297,904)` → **106×64**, bottom-right anchored
- `box-shadow: 0 4px 4px 0 rgba(0,0,0,0.25), 0 0 6px 0 #FAE287`
- children: `MM_MEDIA_Pen` (A.1, viết kudos) · TEXT `/` · `A.2_icon thể lệ saa`
- content block 41×32 per spec description

## Expanded — screen `Sv7DFwBw1h`, node `313:9140` (`Widget Button`)
Container: absolute `(1088,680)-(1302,904)` → **214×224**,
`display:flex; flex-direction:column; align-items:flex-end; gap:20px`.

| # | Node | Size | Bounds | Radius | Background | Content |
|---|------|------|--------|--------|-----------|---------|
| A | `I313:9140;214:3799` `A_Button thể lệ` | 149×64 | (1153,680)-(1302,744) | 4px | `#FFEA9E` | `MM_MEDIA_LOGO` + TEXT `Thể lệ` |
| B | `I313:9140;214:3732` `B_Button viết kudos` | 214×64 | (1088,764)-(1302,828) | 4px | `#FFEA9E` | `MM_MEDIA_Pen` + TEXT `Viết KUDOS` |
| C | `I313:9140;214:3827` `C_Button huỷ` | 56×56 | (1246,848)-(1302,904) | 100px (full) | `#D4271D` | `MM_MEDIA_Close` 24×24 |

A and B: `padding:16px; gap:8px; flex-direction:row; align-items:center; justify-content:flex-start`.
C: `padding:16px`, icon 24×24 centred at (1262,864)-(1286,888).

Label typography (`I313:9140;214:3799;186:1568`, shared component `186:1567`):
`Montserrat 700 · 24px/32px · letter-spacing 0 · text-align center · colour #00101A`.

## Vertical rhythm
744→764 = 20px · 828→848 = 20px (matches container `gap:20px`).
Both states share the bottom-right anchor `endY 904`; the collapsed pill (840-904, h64)
is replaced in place by the round close button (848-904, h56).

## Navigation (from node `specs.navigation.linkedFrameName`)
- A `Thể lệ` → frame `3204:6051` "Thể lệ UPDATE" → repo route **`/standards`** (F007, shipped)
- B `Viết KUDOS` → frame `520:11602` "Viết Kudo" → repo route **`/kudos/new`** (F005, shipped)
- C `Hủy` → no linked frame; closes the group in place

## Collapsed pill — inner measurements (node `I313:9138;214:3839`, `Button`)
`106×64 · padding 16 · gap 8 · border-radius 100px · background #FFEA9E`
(the shared button component `186:1567`, same one A/B/C use — only the radius differs).

| Child | Node | Size | Notes |
|-------|------|------|-------|
| row `A.1_icon viết kudos` | `I313:9138;214:3839;186:1935` | 42×32 | `flex row · gap 8 · align-items center` |
| ├ pen | `…;186:1763` (`MM_MEDIA_Pen`) | 24×24 | |
| └ `/` | `…;186:1568` TEXT | 10×32 | Montserrat 700 · 24/32 · colour `#00101A` |
| glyph `A.2_icon thể lệ saa` | `I313:9138;214:3839;186:1766` | 24×24 | `MM_MEDIA_LOGO` |

Width check: `16 + 42 + 8 + 24 + 16 = 106`. ✓

## Icon colour — measured, and it corrects a shipped bug
Every label and the `/` glyph are `#00101A` on the `#FFEA9E` fill. The icons sit in the same row and
read as the same dark mark. `public/images/home/widget-pen-icon.svg` currently ships `fill="white"`,
which the shipped `floating-widget.tsx` renders **white on light yellow** — near-invisible. This
feature owns that file, so the pen must render dark (`#00101A`) in both states. The kudos glyph
(`widget-saa-kudos-glyph.svg`) is already `#00101A`, but is authored 20×19 and the design calls for
**24×24** in the expanded menu.

`public/images/rules/close-icon.svg` (24×24, `fill="white"`) is exactly `MM_MEDIA_Close` on the red
`#D4271D` button — reuse it, do not author a second copy.
