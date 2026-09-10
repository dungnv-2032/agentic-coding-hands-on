# Measured geometry — Open secret box (chưa mở)

Source: MoMorph `get_node` on file `9ypp4enmFmdK3YAFJLIu6C`, screen `J3-4YFIpMM`, frame `1466:7676`.
**This file is the only source of visual values for phases 04 and 07.** A value not written here
is not known; re-read the node rather than inventing it.

## Frame `1466:7676` (mms_Open secret box)

| Property | Value |
|----------|-------|
| Size | `651.5 × 822.6` |
| Background | `#00101A` |
| Border radius | `12.73` |
| Padding | `23.87` vertical · `12.73` horizontal (651.5 − 2×12.73 = 626.04 = the child width) |
| Layout | column, `gap: 22.28`, children `626` wide |

## Children

| Node | Name | Measurement |
|------|------|-------------|
| `1466:7678` | A_Title | text `KHÁM PHÁ SECRET BOX CỦA BẠN` · Montserrat 700 · `25.46/31.82` · centered · `#FFEA9E` · width `626` |
| `1466:7679` | close glyph | `19 × 19`, top-right, x `606–625`, y `39–58` |
| `1466:7680` | hairline (upper) | `626 × 1`, `#2E3940`, y `86` |
| `1466:7683` | instruction | text `Click vào box để mở` · Montserrat 700 · `12.73/19.09` · letter-spacing `0.398` · white |
| `1466:7684` | C_Box image | `557 × 557` square, x `47–603`, y `152–708` |
| `1466:7685` | glow overlay | asset `public/images/secret-box/box-glow.png`, intrinsic `463 × 449`. Re-read via `get_node` (phase 04): `546.535 × 546.535`, frame-absolute `x 142–651` / `y 260–806`, i.e. `+95 / +108` from the box slot's own origin (`142 − 47`, `260 − 152`). CSS fill: `background: url(box-glow.png) -102.944px -102.487px / 138.527% 138.527% no-repeat` (Figma's own fill scale/offset, reproduced verbatim — the `award-system-hero.tsx` keyvisual technique). |
| `1466:7688` | hairline (lower) | `626 × 1`, `#2E3940`, y `731` |
| `1466:7689` | D_Số box chưa mở | row, `gap: 6.36`, `174 × 35`, centered |
| `1466:7692` | count label | text `Secretbox chưa mở` · Montserrat 700 · `12.73/19.09` · letter-spacing `0.398` · white |
| `1466:7693` | count value | text `05` · Montserrat 700 · `28.64/35.0` · `#FFEA9E` |

## Assets already downloaded

- `public/images/secret-box/box-unopened.png` — `1000 × 1000`, the full composed gift-box-on-podium
  artwork. It fills the `557 × 557` slot; the podium is part of the artwork, not a separate node.
- `public/images/secret-box/box-glow.png` — `463 × 449` sparkle overlay (node `1466:7685`).
- `public/images/rules/close-icon.svg` — reused byte-identical for `1466:7679`; no second copy.
- The six badge images ship already at `public/images/rules/icon-*.png` and arrive from
  `rule_items.image_path`; no badge asset is authored in this commission.

## Values the frame does NOT state (do not invent)

- The awarded-badge overlay size and placement — the *đã mở* frame is `in_progress` with no spec.
  The plan's DEC-01 fixes a rule for it; anything beyond that rule is `NEEDS_CONTEXT`.
- Page-level placement of the `651.5` card inside a `1440` viewport (the frame is the card alone).
  Plan DEC-02 fixes centering; no margin is asserted against the design.
- Responsive behaviour below `651.5px` wide. Plan DEC-03: the card's width is a maximum, its
  internals scale with it; geometry is asserted at `1440 × 1024` only.
