# MoMorph Visual Study — Profile bản thân (`mm:362:5037`)

Section-mode artifact persistence + measurement only. No application code was written for
this task. All values below cite the exact `mm:{nodeId}` they came from; nothing is guessed.

## Frame

| Fact | Value | Source |
|---|---|---|
| Total size | 1440 × 4660 px | `mm:362:5037` |
| Page background | `rgba(0,16,26,1)` = `#00101A` | `mm:362:5037` |
| Content container width | 680px, centered (margins ~380px each side at 1440) | `mm:362:5073`, `mm:362:5091` (both startX 380 / endX 1060) |
| Header content width | 968px outer, 680px inner (padding 144px each side) | `mm:362:5084` |
| Hero/name block width | full 1440px, `flex-column, align-items:center` | `mm:362:5052` |

**Reuse:** `#00101A` is already `body`'s implicit dark theme in this repo only via
`kudos-hero.tsx` inline literals (`bg-[#00101A]`, gradient stop `#00101A`) — it is **not** in
`app/globals.css` (`--background:#ffffff` light default). Every hex/color/radius token below is
a Tailwind arbitrary-value literal already scattered across `app/kudos/_components/*.tsx`, none
is a `@theme` CSS variable.

## `mms_3_Keyvisual` — hero banner (`mm:I1210:12622;2167:5140`)

| Fact | Value | Source |
|---|---|---|
| Group size/position | 1440×512, absolute top 0 | `mm:I1210:12622;2167:5140` |
| Image fill | `mm:I1210:12622;2167:5141`, background-position `-0.163px -909.862px`, size `101.245% 393.038% no-repeat` (i.e. `object-cover`-style crop of a taller source image) | `mm:I1210:12622;2167:5141` |
| Overlay ("Cover") | Sibling rect 1440×957, `linear-gradient(8deg, #00101A 8.6%, rgba(0,19,32,0) 37.25%)`, positioned y445→1402 (extends **below** the 512px banner into the page body) | `mm:I1210:12622;1210:12612` |

**Reuse — exact prior art:** `kudos-hero.tsx` already implements this precise pattern: a `next/image`
absolute `h-[512px] w-full object-cover` banner + an `aria-hidden` gradient wash div. Only the
gradient's angle/stops differ (`kudos-hero.tsx` uses `25deg, #00101A 14.74%, ... 47.8%`; this
frame measures `8deg, 8.6%, 37.25%`). The banner **is not** an `MM_MEDIA_*` named asset — it's an
inline Figma fill, so it is not resolvable via `list_media_nodes`/`get_media_files`; treat as a
static background image asset the same way `kudos-hero.tsx` treats `kv-background.png`.

## `mms_A_Info` — hero identity block (`mm:362:5052`)

Frame: 1440×468, `flex-column, gap:32px, align-items:center, justify-content:center`.

### `mms_A.1_Avatar` (`mm:362:5053`)

| Fact | Value |
|---|---|
| Size | 200×200, `border-radius:200px` (circle) |
| Ring | `border: 4px solid #FFF` (var `--Details-Text-Secondary-1`) |
| Fill | inline Figma image fill, `background-position -77.778px -83.333px`, size `177.778% 158.333% no-repeat` (cover-crop) |
| Position | x620–820 → centered on the 1440 frame (center 720) |

Not an `MM_MEDIA_*` node — same caveat as the keyvisual, inline fill only.

### `mms_A.2_Name` (`mm:362:5054`) — 473×80, `flex-column gap:8`

| Element | mm id | Value |
|---|---|---|
| Name text | `362:5055` | `fontSize:36 / lineHeight:44 / weight:700 / Montserrat`, color `rgba(255,234,158,1)` = **`#FFEA9E` gold**. Sample text "Huỳnh Dương Xuân Nhật" |
| Detail row | `362:5056` | contains department + tier badge + dot, flex row |
| Department text | `362:5057` | `fontSize:22 / lineHeight:28 / weight:700 / Montserrat`, color white. Sample "CEVC3 " |
| Separator dot | `362:5060` | 4×4 ellipse, `bg #999`, `opacity:0.4` |
| Tier badge instance | `3053:6061` "danh hiệu" | 109×19, `border:0.5px solid #FFEA9E`, `border-radius:48px` (pill); inner text "Legend Hero" `fontSize:12.821 / weight:700`, color white with `text-shadow:0 0 1.3px #FFF`; badge also layers two glow image rectangles (`image 26`/`image 27`) behind the text |

**Reuse — very close prior art:** `sunner-chip.tsx` already implements name + department + dot +
tier-badge pill for the board's Kudo cards (`text-sm text-[#999]` department, `h-1 w-1 bg-[#999]
opacity-40` dot, `border-[#FFEA9E]/70 bg-black/30 rounded-full text-[11px]` badge pill). The
**measurements differ** (hero badge is 109×19 @ 12.8px font vs. the card chip's smaller pill,
and the hero badge border is solid `#FFEA9E` not `/70` alpha) — same component family, not a
literal reuse without resizing.

**Gap:** the spec/test-cases call for "hoa-thị stars" alongside the tier badge on this row (TC
`GUI_001`), but no separate star node exists under `mms_A.2_Name` in the tree — only the name,
department, dot, and the one tier-badge instance were found. The stars are either baked into the
tier-badge component's own image layers (`image 26`/`image 27`) or are a data-driven element not
present in this static export. Flag for the implementer/orchestrator to resolve via
clarifications, not to invent.

### `mms_A.3_Huy Hiệu` — 6 badge slots (`mm:362:5064` → `mm:362:5065` "Danh hiệu")

Outer `362:5064`: 1440×64, `flex-row, gap:16, padding:0 800px, justify-content:space-between,
align-items:center`. Inner `362:5065` "Danh hiệu": `flex-row, gap:16, border:1px solid #000`.

| Slot | mm id | Circle child (`Ảnh Huy hiệu`) mm id | X range |
|---|---|---|---|
| B2 (`mms_B2.1_Ảnh Huy hiệu`) | `362:5066` | `I362:5066;3053:10046` | 440–520 |
| B3 | `362:5067` | `I362:5067;3053:10046` | 536–616 |
| B4 | `362:5068` | `I362:5068;3053:10046` | 632–712 |
| B5 | `362:5069` | `I362:5069;3053:10046` | 728–808 |
| B6 | `362:5070` | `I362:5070;3053:10046` | 824–904 |
| B7 | `362:5071` | `I362:5071;3053:10046` | 920–1000 |

Each slot instance: 80×64 outer, `flex-column, gap:8, align/justify:center`. Circle: 64×64,
`border:2px solid #FFF`, `background:#323231` (dark-grey placeholder — no image), `border-radius:
100px`. Gap between adjacent circle slots = 16px (matches parent `gap`). Order is fixed left→right
B2→B7, matching TC `GUI_002`'s "6 slots, fixed order, all locked/desaturated."

**No image asset exists for any badge** — every slot in this frame renders the same flat `#323231`
grey fill, no `MM_MEDIA_*` icon attached (`list_media_nodes` found 30 media nodes on this frame;
none of them are these 6 badge slots). This matches TC `GUI_002`'s expectation of desaturated
real artwork, but the artwork itself is **not present in this frame** — the "real badge image
desaturated" implied by the spec description on `mms_A_Info` cannot be sourced from this screen;
flag as a gap for clarifications (locked badges may need a separate badge-artwork source).

## Statistics card — `mms_B_Thống kê` (`mm:362:5073` → `362:5074` "Thống kê" → `362:5075` "Nội dung")

| Fact | Value | Source |
|---|---|---|
| Outer region | `362:5073`, 680×437, `flex-column gap:24` | `mm:362:5073` |
| Card container | `362:5074` "Thống kê": 680px wide, `padding:40px`, `border:1px solid #998C5F` (var `--Details-Border`), `background:#00070C` (var `--Details-Container-2`), `border-radius:17px`, `flex-column gap:10` | `mm:362:5074` |
| Rows wrapper | `362:5075` "Nội dung": 600×357, `flex-column gap:16, align/justify:center` | `mm:362:5075` |

**Reuse — near-identical prior art:** `kudos-sidebar.tsx`'s `D.1_Thống kê tổng quat` card uses the
**exact same tokens**: `border-[#998C5F] bg-[#00070C] rounded-[17px]`. Only the padding and width
differ — sidebar is `p-6` (24px) at `max-w-[422px]`, this profile card is `padding:40px` at
`width:680px` (the "own profile, full stats" variant vs. the board's compact sidebar variant).

| Row | mm id | Number style | Number color | Label style | Label sample |
|---|---|---|---|---|---|
| B.1 Kudos received | `362:5076` | `fontSize:32/lineHeight:40/weight:700 Montserrat`, textAlign center | `#FFEA9E` | `fontSize:22/lineHeight:28/weight:700`, textAlign right, white | "Số Kudos bạn nhận được:" |
| B.2 Kudos sent | `362:5077` | same | `#FFEA9E` | same | "Số Kudos bạn đã gửi:" |
| B.3 Hearts received | `362:5078` | same | `#FFEA9E` | same | "Số tim bạn nhận được:" |
| — divider | `362:5079` "Rectangle 14" | 600×1, `bg rgba(46,57,64,1)` = `#2E3940` | — | — | sits between B.3 and B.4 |
| B.4 Boxes opened | `362:5080` | same | `#FFEA9E` | same | "Số Secret Box bạn đã mở:" |
| B.5 Boxes unopened | `362:5081` | same | `#FFEA9E` | same | "Số Secret Box chưa mở:" |
| B.6 Open-gift button | `362:5082` | 600×60, `padding:16px`, `border-radius:8px`, `bg #FFEA9E`, `flex-row center gap:8` | text `fontSize:22/weight:700`, color `#00101A` (dark, on gold bg); label "Mở Secret Box" + 24×24 icon instance | | |

Each row (`B.1`–`B.5`) is `600px wide, height:40px, flex-row, gap:8, justify-content:space-between,
align-items:center` — number cell is fixed ~46px wide right/center-aligned, label cell flexes.

**Reuse — exact prior art for every row and the button:** `kudos-sidebar.tsx`'s `sidebar-stat` rows
use `text-[22px] leading-7 font-bold text-white` (label) + `text-[32px] leading-10 font-bold
text-[#FFEA9E]` (value) and its divider is `h-px w-full bg-[#2E3940]` — all identical tokens. The
"Mở Secret Box" button is **already implemented verbatim**: `bg-[#FFEA9E] text-[#00101A] rounded-lg
px-4 py-4`, same label, same `IconGift`. The implementer can reuse this row/button shape directly,
only changing width (680 vs 422) and the row set (this card ends after 5 rows + divider, no flame
"x2" row, no gift-leaderboard below it).

## KUDOS section header — `mms_C_Header Giải thưởng` (`mm:362:5084`)

Outer: 968×129, `padding:0 144px, flex-column align/justify:center`. Inner content 680px wide.

| Element | mm id | Value |
|---|---|---|
| `mms_C.1_title` | `362:5085` | 680×32, `fontSize:24/lineHeight:32/weight:700`, white; text "Sun* Annual Awards 2025" |
| Divider | `362:5086` "Rectangle 26" | 680×1, `bg #2E3940` |
| `mms_C.2_KUDOS title` | `362:5088` | 218×64, `fontSize:57/lineHeight:64/weight:700, letter-spacing:-0.25px`, color `#FFEA9E` gold; text "KUDOS" |
| `mms_C.3_Button` (direction dropdown trigger) | `362:5089` | `border:1px solid #998C5F`, `padding:16px 24px`, `background:rgba(255,234,158,0.10)` (var `--Details-SecondaryButton-Normal`), `border-radius:4px`, `flex-row align-center gap:8`; label `fontSize:16/weight:700, letter-spacing:0.15px`, white (sample text "Đã gửi (5)" — this is the frame's captured mock state, not necessarily the default selection); trailing "Button down" chevron icon instance |

**Reuse:** `#FFEA9E` at `KUDOS` 57px is new to this screen (biggest gold text on the site so far).
The dropdown trigger's `border-[#998C5F] bg-[rgba(255,234,158,0.10)] rounded` shell matches the
same secondary-button family used by `mms_1_Button`/`mms_7.4_Button-IC` below (all three share
Figma `componentSetId 186:1426`) — i.e. one shared button component, several instances/variants.
`kudos-filter-menu.tsx`'s dropdown-panel styling (`border-[#998C5F] bg-[#00070C] rounded-lg`) is
the adjacent, already-built listbox this trigger would open — reuse that panel, not a new one.

## `mms_D_Post all` — feed container (`mm:362:5091`)

| Fact | Value |
|---|---|
| Container | 680×2956 (this frame's captured content height), `flex-column, gap:24, align-items:flex-start` — **single column**, no grid |
| Card width | 680px fixed (matches container, no responsive breakpoint visible in this static frame) |
| Card style | `padding:40px 40px 16px 40px`, `border-radius:24px`, `background:rgba(255,248,225,1)` = `#FFF8E1` (light cream) |
| Card variants present | 2× "KUDO spam" (`3127:24169`, `3127:24455`, height 701, includes the Status chip) + 2× "KUDO" (`1949:12834`, `3127:22945`, height 741, no chip) — component ids `3127:24099` vs `1949:12832`, i.e. two Figma component variants, chip presence is the only structural difference found |

**Note:** `#FFF8E1` cream card background is **new** to this screen — the board's Kudo cards
(`kudos-card.tsx`, not read in full here) may use a different card token; the implementer should
diff against the live board's card background before assuming reuse.

## `mms_D.3.1_Status` — Spam chip (measured only, NOT to be rendered per task)

| Fact | Value | Source |
|---|---|---|
| Outer | 72×40, `background:rgba(255,129,4,1)` = `#FF8104` (orange), `border-radius:4px` | `mm:I3127:24169;3127:24095` |
| Inner frame | `padding:8px 16px`, `border:1px solid #EAEAEA`, `border-radius:4px`, center-aligned | same |
| Text | "Spam", `fontSize:16/weight:700, letter-spacing:0.5px`, white | same |

Two instances found (`I3127:24169;3127:24095`, `I3127:24455;3127:24095`), both on the "KUDO spam"
card variant only. Per task and TC `GUI_007`, this must never render in the implementation.

## `mms_1_Button` (header icon) and `mms_7.4_Button-IC` (footer link)

| Node | mm id | Value |
|---|---|---|
| `mms_1_Button` | `I362:5041;186:1597` | 40×40, `border:1px solid #998C5F`, `padding:10px`, `border-radius:4px`, `flex center`; contains one `IC` icon instance. Header-right icon button, componentId `186:1467` |
| `mms_7.4_Button-IC` | `I435:3154;1161:9487` | 182×56, `padding:16px, gap:4px, flex-row align-center`; contains a text-label frame ("Awards Information Navigation Links" placeholder text). Footer nav link, componentId `186:1433` |

Both share `componentSetId 186:1426` with the `mms_C.3_Button` dropdown trigger and the `mms_B.6`
"Mở Secret Box" button — one shared Figma button component family across the whole screen, several
variants (primary/secondary/icon-only/text-link).

## Design tokens — already in repo vs. new to this screen

| Token | Value | Status |
|---|---|---|
| Page/body bg | `#00101A` | **Reuse** — `kudos-hero.tsx` literal (not in `globals.css` `@theme`) |
| Card container bg | `#00070C` | **Reuse** — `kudos-sidebar.tsx`, `kudos-filter-menu.tsx` |
| Border/gold-brown | `#998C5F` | **Reuse** — `kudos-hero.tsx`, `kudos-sidebar.tsx` (implied), `kudos-filter-menu.tsx` |
| Gold accent | `#FFEA9E` | **Reuse** — used everywhere (`kudos-hero.tsx`, `kudos-sidebar.tsx`, `sunner-chip.tsx`) |
| Divider grey | `#2E3940` | **Reuse** — `kudos-sidebar.tsx` |
| Muted grey (dept text / dot) | `#999` | **Reuse** — `sunner-chip.tsx` |
| Dark text-on-gold | `#00101A` | **Reuse** — `kudos-sidebar.tsx` secret-box button |
| Card cream bg | `#FFF8E1` | **New to this screen** (feed card bg) — verify against `kudos-card.tsx` before assuming identical |
| Spam-chip orange | `#FF8104` | **New**, and per task, unused (never rendered) |
| Font family | Montserrat, weight 700 throughout | **Reuse** — `--font-montserrat` already in `app/globals.css` `@theme inline` |
| Border radius 17px (card) | — | **Reuse** — `kudos-sidebar.tsx` `rounded-[17px]` |
| Border radius 24px (feed card) | — | **New** to this screen |
| Border radius 200px (avatar) / 100px (badge circle) | — | circle shapes, standard `rounded-full` |

`app/globals.css` itself defines no dark-theme tokens beyond the OS-level `prefers-color-scheme`
fallback (`--background:#0a0a0a`) — every dark-navy/gold value actually used across the kudos
screens, including this one, is a Tailwind arbitrary-value literal, not a `@theme` variable. No
new CSS custom properties are required to match existing convention.

**Status:** DONE
**Files changed:**
- `/mnt/c/Users/nguyen.van.dungc/Desktop/project/my-app/plans/260908-0854-profile-ban-than/design/specs.csv` (29 lines = 1 header + 28 spec rows, 3510 bytes)
- `/mnt/c/Users/nguyen.van.dungc/Desktop/project/my-app/plans/260908-0854-profile-ban-than/design/test-cases.csv` (30 test-case records + 1 header, verified via `grep -c '^(ACCESSING|FUNCTION|GUI),TC_WEB_PROFILE'` = 30; raw `wc -l` reads 70 because several `Steps`/`Precondition` fields contain embedded newlines inside quoted CSV cells — 20859 bytes)
- `/mnt/c/Users/nguyen.van.dungc/Desktop/project/my-app/plans/260908-0854-profile-ban-than/design/profile.png` (1440×4660 PNG, 1,886,332 bytes, verified with `file`)
- `/mnt/c/Users/nguyen.van.dungc/Desktop/project/my-app/plans/260908-0854-profile-ban-than/reports/momorph-visual-study.md` (this file)
