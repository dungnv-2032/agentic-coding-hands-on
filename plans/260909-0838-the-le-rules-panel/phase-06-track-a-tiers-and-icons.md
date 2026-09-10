# Phase 06 — Track A: bậc Hero, lưới icon, asset bút

## MoMorph refs

- Thể lệ UPDATE: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/b1Filzi9i6
- Clarifications: `plans/260909-0838-the-le-rules-panel/clarifications.md`
- testPolicy: `e2e-red-first`

## Context Links

- `clarifications.md § "Resolved from source data"` — bảng bậc Hero (`3204:6161/6170/6179/6188`) và lưới icon (`3204:6079`)
- `clarifications.md § "Assets pulled during this gate"` — danh sách 12 asset và ghi chú `pen-icon.svg`
- `design/the-le.png` — frame render 1×, **nguồn quyết định màu icon bút**
- `spec/the-le/technical-spec.md § 4.1, § 5.2 (A2)`
- `phase-01-contract-and-i18n.md` — `RulesHeroTierView`, `RulesCollectibleIconView`
- House style: `app/_components/floating-widget.tsx:21` (idiom `<Image src="/images/..." alt="" aria-hidden />`)

## Overview

- **Priority**: P1
- **Status**: **completed** — asset bút giải quyết đúng như dự đoán (Key Insight 2 đứng vững). Nhưng
  **markup của cả hai component đã được viết lại** sau lượt visual của phase 08: `grid-cols-3` +
  `gap-x-4 gap-y-6` + `rounded-full` ở § Architecture đều không tái hiện được frame. Xem § "Sai lệch
  so với kế hoạch".
- **Description**: Hai component danh sách (4 bậc Hero, lưới 6 icon) và giải quyết asset còn thiếu:
  `public/images/rules/pen-icon.svg`. Chạy song song với phase 05 và Track B.

## Key Insights

1. **`pen-icon.svg` KHÔNG có trên đĩa.** `public/images/rules/` chỉ có 11/12 file (đã đếm).
   `clarifications.md` liệt kê nó như đã kéo về — thực tế thì không.
2. **Và giả định A2 của technical-spec KHÔNG đứng vững.** `public/images/home/widget-pen-icon.svg`
   là `fill="white"`. Nút `Viết KUDOS` có nền đặc `#FFEA9E` (vàng nhạt). Bút trắng trên nền vàng nhạt
   là bút vô hình. Frame render (`design/the-le.png`) vẽ bút MÀU TỐI. **Tái dùng nguyên file có sẵn
   là sai**, dù hình học đường path giống hệt. Cách xử lý ở § Architecture — không im lặng copy, cũng
   không im lặng bỏ qua.
3. **Ảnh pill huy hiệu và nhãn nằm CÙNG một hàng**, mô tả xuống dòng dưới (đọc từ frame render, khớp
   FR-203). Không phải ảnh trên - chữ dưới.
4. **Lưới icon là 3 cột cố định**, hai hàng ba, ô 80px, gap ngang 16px, gap dọc 24px. Caption in hoa,
   canh giữa, có thể xuống 2–3 dòng (`TOUCH OF LIGHT`, `BEYOND THE BOUNDARY`) — chiều cao ô phải chịu
   được điều đó mà không lệch hàng.
5. **Cả hai component là Server Component.** Không tương tác, không state.
6. **`caption` là `ROOT FUTHER`, tên file là `icon-root-further.png`.** Hai thứ khác nhau là đúng —
   caption từ node text, tên file do gate đặt. Đừng "đồng bộ" chúng.

## Requirements

- **FR-203** — 4 bậc Hero theo `position`: ảnh pill + nhãn 16/24 bold trắng cùng hàng, mô tả 14/20
  bold trắng dòng dưới
- **FR-204** — 6 icon theo `position`, lưới 3 cột, ô 80px, gap 16/24, artwork tròn + caption in hoa canh giữa
- **FR-205** — ảnh đọc từ `image_path` của row, phục vụ từ `public/images/rules/`
- **Test contract** — `data-testid="rules-hero-tier"` (×4), `data-testid="rules-collectible-icon"` (×6)
- **BR-001** — thứ tự render là thứ tự mảng đến từ `position`; component KHÔNG tự sort lại

## Architecture

### Asset bút — cách xử lý mâu thuẫn

Tạo `public/images/rules/pen-icon.svg`: **cùng đường path** với `widget-pen-icon.svg` (cùng component
MoMorph `186:1763`, nên hình học là một), **khác `fill`** — `#00070C`, màu nền drawer, khớp bút tối
trên nền vàng trong frame render.

```svg
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M20.8067 6.72951C21.1967 6.33951 21.1967 5.68951 20.8067 5.31951L18.4667 2.97951C18.0967 2.58951 17.4467 2.58951 17.0567 2.97951L15.2167 4.80951L18.9667 8.55951M3.09668 16.9395V20.6895H6.84668L17.9067 9.61951L14.1567 5.86951L3.09668 16.9395Z" fill="#00070C"/>
</svg>
```

Đây **không phải** vi phạm DRY: hai file là hai asset khác nhau (khác màu cho khác nền), không phải
hai bản sao của cùng một asset. Doc-comment không đặt được trong SVG dùng bởi `<Image>`, nên lý do
được ghi ở doc-comment của component dùng nó (phase 07) và ở đây.

**Đã cân nhắc và loại**: (a) tái dùng file trắng + CSS `filter: invert()` — mong manh, phụ thuộc
trình duyệt, và `<Image>` với SVG không nhận filter một cách đáng tin; (b) inline SVG thành React
component với `fill="currentColor"` — sạch hơn về lý thuyết nhưng đi ngược idiom `<Image src>` mà cả
`floating-widget.tsx`, `kudos-hero.tsx`, `kudos-promo.tsx` đang dùng. Chọn cách rẻ nhất đúng idiom.

### `rules-hero-tier-list.tsx` (server, ~50 dòng)

```tsx
interface Props { tiers: readonly RulesHeroTierView[]; imageAltTemplate: string; }
```

```
<ul class="flex flex-col gap-3">
  {tiers.map(t => (
    <li data-testid="rules-hero-tier" key={t.position} class="flex flex-col gap-1">
      <div class="flex items-center gap-2">
        <Image src={t.imagePath} alt={altFor(t)} width={128} height={28} class="h-7 w-auto" />
        <span class="text-base/6 font-bold text-white">{t.label}</span>
      </div>
      <p class="text-sm/5 font-bold text-white">{t.description}</p>
    </li>
  ))}
</ul>
```

`imageAltTemplate` là `dictionary.rules.heroTierImageAlt` (`"Huy hiệu {tier}"`); `altFor` thay `{tier}`
bằng tên bậc. Tên bậc KHÔNG có trong view-model (`label` là ngưỡng, không phải "New Hero") — nên
`altFor` lấy từ `imagePath`: `hero-badge-new-hero.png` → `New Hero`. Nếu suy diễn đó thấy mong manh
khi implement, dùng `alt=""` + `aria-hidden` (ảnh trang trí, nhãn đã có bên cạnh dạng text) và ghi
lại lựa chọn — **đó là phương án ưu tiên nếu có nghi ngờ**, vì nhãn text ngay cạnh đã mang trọn nghĩa.

`width`/`height` của `<Image>`: pill trên frame ~128×28. `<Image>` của Next đòi hai con số này;
`h-7 w-auto` để tỉ lệ thật của file quyết định bề rộng hiển thị.

### `rules-collectible-grid.tsx` (server, ~45 dòng)

```tsx
interface Props { icons: readonly RulesCollectibleIconView[]; imageAltTemplate: string; }
```

```
<ul class="grid grid-cols-3 gap-x-4 gap-y-6">
  {icons.map(i => (
    <li data-testid="rules-collectible-icon" key={i.position}
        class="flex flex-col items-center gap-2">
      <Image src={i.imagePath} alt="" aria-hidden width={80} height={80} class="h-20 w-20 rounded-full" />
      <span class="text-center text-xs font-bold uppercase text-white">{i.caption}</span>
    </li>
  ))}
</ul>
```

- `gap-x-4` = 16px, `gap-y-6` = 24px, ô `h-20 w-20` = 80px — đo được từ `3204:6079`.
- `alt=""` + `aria-hidden` vì caption ngay dưới đã là nhãn text; alt lặp lại chỉ làm screen reader
  đọc hai lần. `imageAltTemplate` vẫn nhận vào để dùng nếu quyết định khác lúc implement — nếu không
  dùng, **bỏ prop đó đi** thay vì để tham số chết.
- `uppercase` là an toàn: dữ liệu đã in hoa sẵn từ frame; class chỉ bảo đảm không lệch nếu ai sửa seed.
- KHÔNG `sort()` trong component — mảng đã đúng thứ tự từ `order by position`.

## Related Code Files

**Create**
- `app/standards/_components/rules-hero-tier-list.tsx`
- `app/standards/_components/rules-collectible-grid.tsx`
- `public/images/rules/pen-icon.svg`

**Modify** — không có. **Đặc biệt KHÔNG sửa** `public/images/home/widget-pen-icon.svg` — nó đang phục
vụ `floating-widget.tsx` trên nền tối và phải giữ `fill="white"`.

**Delete** — không có.

## Implementation Steps

1. Xác nhận lại bằng lệnh, không bằng trí nhớ:
   ```
   ls public/images/rules/ | wc -l          # kỳ vọng 11 trước phase này, 12 sau
   cat public/images/home/widget-pen-icon.svg | grep -o 'fill="[^"]*"'
   ```
   Nếu `pen-icon.svg` BẤT NGỜ đã có sẵn: mở ra, kiểm `fill`. Nếu nó tối (`#00070C` hoặc tương đương)
   → dùng luôn, bỏ bước 2. Nếu nó trắng → vẫn phải sửa theo bước 2.
2. Tạo `public/images/rules/pen-icon.svg` theo § Architecture (cùng path, `fill="#00070C"`).
3. Đọc `design/the-le.png` để xác nhận bố cục hàng của bậc Hero (ảnh + nhãn cùng hàng, mô tả dòng dưới)
   trước khi viết markup.
4. Tạo `rules-hero-tier-list.tsx` theo § Architecture. Doc-comment ghi node id
   `3204:6161/6170/6179/6188` và ghi rõ quyết định về `alt`.
5. Tạo `rules-collectible-grid.tsx` theo § Architecture. Doc-comment ghi node `3204:6079` và ghi rõ
   `ROOT FUTHER` (caption) ≠ `root-further` (tên file) là CỐ Ý.
6. Kiểm mọi `image_path` đều trỏ file có thật:
   ```
   for f in hero-badge-new-hero hero-badge-rising-hero hero-badge-super-hero hero-badge-legend-hero \
            icon-revival icon-touch-of-light icon-stay-gold icon-flow-to-horizon \
            icon-beyond-the-boundary icon-root-further; do
     test -f public/images/rules/$f.png || echo "MISSING $f.png"
   done
   ```
   Bất kỳ dòng `MISSING` nào → **BLOCKED**, báo lên, đừng dựng ô rỗng cho qua.
7. `npm run typecheck`, rồi `npm run lint`.

## Todo List

- [x] Xác nhận `pen-icon.svg` thiếu + `widget-pen-icon.svg` là `fill="white"` (đo, không nhớ)
- [x] Tạo `public/images/rules/pen-icon.svg` với `fill="#00070C"`
- [x] KHÔNG sửa `public/images/home/widget-pen-icon.svg`
- [x] Đọc frame render xác nhận bố cục hàng bậc Hero
- [x] `rules-hero-tier-list.tsx` — `<li data-testid="rules-hero-tier">` ×4, ảnh + nhãn cùng hàng
      (**cộng `pl-5`**, xem dưới)
- [x] `rules-collectible-grid.tsx` — ô 80px; ~~`grid-cols-3`, `gap-x-4 gap-y-6`~~ → track literal
      `repeat(3,80px)` + `justify-between` + `gap-y-4` (xem dưới)
- [x] Không `sort()` trong component nào
- [x] Kiểm 10 file ảnh tồn tại (`public/images/rules/` có đủ 12 file)
- [x] `npm run typecheck` + `npm run lint` sạch

## Sai lệch so với kế hoạch (post-phase, `plan.md § PP-4`, `§ PP-5`)

Bốn thứ ở § Architecture không sống sót qua lượt visual của phase 08. Không cái nào là lỗi cẩu thả —
mỗi cái là một giá trị đo được từ frame mà kế hoạch chưa có lúc viết.

**1. Ô caption phải bị ép về đúng 80px thì caption mới xuống dòng (V-1).**
Mọi badge instance trong frame (`3204:6083/6084/6088`) rộng đúng 80px và text node caption cũng 80px,
nên caption **WRAP**. Chiều cao instance đo được: 88px (1 dòng), 104px (2 dòng), 120px (3 dòng).
`grid-cols-3` = `repeat(3, minmax(0,1fr))` bên trong một `<ul>` shrink-to-fit lại resolve mỗi track về
max-content, tức bề rộng của caption dài nhất: **ô 147px, pitch 163px**, mọi caption chạy phẳng một
dòng và mỗi hàng hụt 16px. Bản ship dùng `w-20` trên `<span>` + track literal `repeat(3,80px)` +
`justify-between` trong hàng 377px của frame (`3204:6085`) + `mx-auto`: **ô 80px, pitch 148.5px**, số
dòng và gốc toạ độ con (975 / 1123 / 1272) khớp frame chính xác.

**2. Gap dọc lưới 24px → 16px.** Node `3204:6080` nói 16. `gap-y-6` ở § Architecture là số đọc sai.

**3. Artwork vẽ trong hộp 80×64 `object-cover object-top`, KHÔNG `h-20 w-20 rounded-full`.**
Phát hiện lúc implement: mỗi PNG (80×88 hoặc 80×104) **tự nướng caption của nó vào bitmap** dưới đĩa
tròn. Render nguyên bitmap thì mỗi caption in hai lần — một lần bằng pixel, một lần bằng text node mà
E2E assert và screen reader đọc. Hệ số cover ở hộp 80×64 đúng bằng 1 nên không có resample nào, và
caption nướng sẵn rơi ra ngoài hộp. `rounded-full` bị bỏ vì hộp 80×64 không vuông — bo nó sẽ ép đĩa
thành hình elip; nền quanh đĩa vốn đã là `#00070C` của drawer nên bo tròn cũng không đổi gì về thị giác.

**4. Bậc Hero: `pl-5` trên `<li>` (V-2).** Row frame `3204:6161` bắt đầu ở x=927 nhưng CẢ HAI con của
nó — pill `3204:6163` và mô tả `3204:6168` — bắt đầu ở x=947. Thụt 20px thuộc về bên trong hàng, nên
`pl-5` nằm trên `<li>` chứ không trên `<ul>`. Kèm theo: `<ul>` gap 16px (không phải 12px), pill
128×22 `object-contain object-left`, gap pill↔nhãn 12px — tất cả đo từ node.

**5. `imageAltTemplate` không tồn tại trong bản ship** (`plan.md § PP-5`). § Architecture đã nêu sẵn
`alt="" aria-hidden` là "phương án ưu tiên nếu có nghi ngờ" và dặn "nếu không dùng thì bỏ prop đó đi"
— đúng chuyện đã xảy ra, cho cả pill lẫn icon. Hai key dictionary tương ứng đã bị xoá.

**Lệch còn lại, đã cân nhắc và giữ nguyên** (`plan.md § "Đã biết và chấp nhận"`):
- Pitch hàng bậc Hero 84px so với 88px của frame — 4px chênh là line box của mô tả (40 vs 44), không
  phải khoảng cách hardcode. Ép cho bằng sẽ là hardcode một con số thay vì sửa nguyên nhân.
- Font caption 12px so với 11px frame khai — giữ 12px vì nó tái hiện đúng số dòng và chiều cao instance
  đo được; 11px làm lệch cả hai.

## Success Criteria

- `npm run typecheck` exit 0, `npm run lint` exit 0.
- `ls public/images/rules/ | wc -l` = 12.
- `grep -o 'fill="[^"]*"' public/images/rules/pen-icon.svg` trả `fill="none"` và `fill="#00070C"`.
- `git diff --stat public/images/home/widget-pen-icon.svg` trống — file cũ không bị đụng.
- Cả hai component dưới 200 dòng, không file nào có `"use client"`.
- `grep "sort(" app/standards/_components/rules-*.tsx` trả rỗng (BR-001).
- Vòng lặp kiểm ảnh ở bước 6 không in dòng `MISSING` nào.

## Risk Assessment

| Risk | Likelihood | Impact | Countermove |
|---|---|---|---|
| Copy nguyên `widget-pen-icon.svg` (trắng) sang `rules/` theo đúng chữ clarifications | **Cao** — clarifications bảo thế | **Cao** — bút vô hình trên nút chính | Key Insight 2 + bước 1/2 + kiểm `fill` ở Success Criteria |
| Sửa `widget-pen-icon.svg` thành màu tối để "dùng chung" | Trung bình | Cao — hỏng floating widget trên MỌI trang | § Related Code Files nói thẳng KHÔNG; `git diff --stat` ở Success Criteria |
| `alt` của pill huy hiệu suy từ tên file, sai tên bậc | Trung bình | Thấp | Phương án ưu tiên khi nghi ngờ: `alt="" aria-hidden` |
| Caption 3 dòng (`BEYOND THE BOUNDARY`) làm lệch hàng lưới | Trung bình | Thấp — lệch thị giác | `items-center` + `flex-col` trên `<li>`; phase 08 xác nhận bằng ảnh chụp |
| Ô icon dùng `w-[80px]` cứng làm tràn ở màn hẹp | Trung bình | Trung bình | Drawer đã `w-full max-w-[553px]`; 3×80 + 2×16 = 272px, dư chỗ ngay cả ở 360px |
| Một file ảnh thiếu → ô rỗng lặng lẽ | Trung bình | Trung bình | Bước 6 là gate BLOCKED, không phải cảnh báo |

**Rollback**: `rm app/standards/_components/rules-hero-tier-list.tsx
app/standards/_components/rules-collectible-grid.tsx public/images/rules/pen-icon.svg`. Chưa gì import
chúng trước phase 07 — gỡ ra không cascade.

## Security Considerations

- Cả hai component là Server Component không nhận input người dùng — chỉ view-model đã map.
- `<Image src={t.imagePath} />` nhận đường dẫn **từ database**. Đường dẫn đó do seed đặt (phase 03) và
  không có bề mặt ghi nào cho `anon`/`authenticated` (FR-601), nên không ai chèn được `src` lạ. Nếu
  sau này mở màn quản trị sửa nội dung, `image_path` phải được validate là bắt đầu bằng `/images/rules/`
  — ghi lại đây như một điều kiện cho tương lai, KHÔNG dựng validate đó bây giờ (YAGNI, không có
  đường ghi nào tồn tại).
- SVG được phục vụ như file tĩnh qua `<Image>`, không inline vào DOM — không có đường thực thi script
  từ SVG.

## Next Steps

- **Chặn**: phase 07 (ráp vào `rules-panel.tsx`; `pen-icon.svg` là asset của nút `Viết KUDOS` ở đó).
- **Chạy song song với**: phase 03, 04 (Track B) và phase 05 (Track A).
- Bàn giao sang phase 07: hai chữ ký props, đường dẫn `/images/rules/pen-icon.svg`, và **phát hiện về
  màu bút** — phase 07 phải dùng file mới này, không phải file của `home/`.
