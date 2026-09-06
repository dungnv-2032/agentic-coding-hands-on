---
status: implemented
authored_by: takumi
created: 2026-09-06
lang: vi
---

# SCR003_AwardSystem — Screen Spec

**Screen**: SCR003_AwardSystem: Hệ thống giải
**Feature**: F003_AwardSystem
**Type**: atomic
**Route**: `/awards-information`
**Generated**: 2026-09-06

## 1. Overview

**Purpose:** Màn hình công khai trình bày đầy đủ hệ thống giải thưởng SAA 2025 — sáu hạng mục, mỗi hạng mục vinh danh ai, có bao nhiêu giải và giá trị bao nhiêu — thay chỗ shell "Coming soon" mà mọi thẻ giải thưởng trên trang chủ từng dẫn tới.
**Actors:** Khách truy cập, Người dùng đã đăng nhập
**Entry Conditions:** Không yêu cầu gì — route công khai. Phần lớn lượt vào đi từ trang chủ, thường kèm `#<slug>` của hạng mục vừa bấm.
**Exit Conditions:** Khách rời trang qua một liên kết điều hướng (header, footer, hoặc nút `Chi tiết` của khối Sun* Kudos). Không có trạng thái "hoàn tất" bắt buộc — đây là trang đọc.

## 2. Screen Layout

### Layout Sketch

Một trang cuộn dọc liên tục. R1 header dính trên cùng. R3 là phần chính, chia hai cột từ breakpoint `lg`: menu danh mục (R3a) dính bên trái, sáu thẻ giải thưởng (R3b) xếp dọc bên phải với ảnh đảo trái/phải theo chỉ số chẵn/lẻ. Dưới `lg` hai vùng gộp về một cột và menu thành một hàng cuộn ngang. Không có widget nổi trên màn hình này. *(design/award-system.png, 1440×6410)*

```
┌──────────────────────────────────────────────────┐
│  R1: Header (sticky-top) — "Award Information"    │
│      đang chọn                                    │
├──────────────────────────────────────────────────┤
│  R2: Hero — keyvisual + ROOT FURTHER wordmark     │
│      + eyebrow / divider / <h1> vàng (giữa)       │
├───────────────┬──────────────────────────────────┤
│  R3a: Menu    │  R3b: 6 thẻ chi tiết giải thưởng │
│  danh mục     │   D.1 [ảnh trái ] ...            │
│  (sticky ≥lg) │   D.2 [... ảnh phải]             │
│   • Top Talent│   D.3 [ảnh trái ] ...            │
│   • Top Proj. │   D.4 [... ảnh phải]             │
│   • ... (6)   │   D.5 [ảnh trái ] ...            │
│               │   D.6 [... ảnh phải]             │
├───────────────┴──────────────────────────────────┤
│  R4: Sun* Kudos promo block (tái dùng)            │
├──────────────────────────────────────────────────┤
│  R5: Footer (tái dùng)                            │
└──────────────────────────────────────────────────┘
```

### Layout Regions

| Region ID | Name | Position | Scrollable | Key Components |
|-----------|------|----------|------------|----------------|
| R1 | Header | sticky-top | no | `HomeHeader` (`app/_components/home-header.tsx`) — tái dùng của SCR002_Homepage |
| R2 | Hero | static | yes (part of page scroll) | `AwardSystemHero` (`app/awards-information/_components/award-system-hero.tsx`) |
| R3a | Menu danh mục | sticky từ `lg` (`top: var(--award-header-offset)`); dưới `lg` là hàng cuộn ngang | horizontal dưới `lg` | `AwardCategoryNav` (`app/awards-information/_components/award-category-nav.tsx`) |
| R3b | Cột sáu thẻ giải thưởng | static | yes | `AwardDetailCard` × 6 (`app/awards-information/_components/award-detail-card.tsx`) |
| R4 | Khối Sun* Kudos | static | yes | `KudosPromo` (`app/_components/kudos-promo.tsx`) — tái dùng, truyền `maxWidthClass="max-w-[1440px]"` |
| R5 | Footer | static | yes | `SiteFooter` (`app/_components/site-footer.tsx`) — tái dùng của SCR002_Homepage |

## 3. UI Elements

| ID | Element | Type | Required | Default | Visibility | Action | Source | Format | Empty Behavior | Cross-ref |
|----|---------|------|----------|---------|------------|--------|--------|--------|-----------------|-----------|
| E01 | Header *(tái dùng nguyên trạng)* | region | — | visible | Always | Điều hướng theo từng mục; mục "Award Information" mang `aria-current="page"` trên route này | static | raw | — | binding: `usePathname()` (`home-nav.tsx:59`) |
| E02 | Hero keyvisual | image | — | visible | Always | — | static | CSS background, crop riêng của frame | — | N/A |
| E03 | Chữ hình "ROOT FURTHER" | image | — | visible | Always | — | static | 451×200, hiển thị 200/280/338px theo breakpoint | — | N/A |
| E04 | Eyebrow "Sun* Annual Awards 2025" | display field | — | visible | Always | — | static | raw (trắng, canh giữa) | — | N/A |
| E05 | Đường kẻ mảnh dưới eyebrow | display field | — | visible | Always | — | static | raw `#2E3940` | — | N/A |
| E06 | Tiêu đề "Hệ thống giải thưởng SAA 2025" | display field | — | visible | Always | — | static | `<h1>` duy nhất của trang, vàng `#FFEA9E`, canh giữa | — | N/A |
| E07 | Mục menu danh mục *(nhóm lặp 6 lần theo thứ tự: Top Talent, Top Project, Top Project Leader, Best Manager, Signature 2025 Creator, MVP)* | link | — | mục đầu tiên đang sáng | Always | Bấm → cuộn tới thẻ tương ứng, địa chỉ đổi thành `#<slug>` | computed (vị trí cuộn / cú bấm) | `<a href="#slug">` thật, có biểu tượng 24×24 phía trước; mục sáng mang `aria-current="true"` | — | binding: `#<slug>` của thẻ tương ứng |
| E08 | Thẻ chi tiết giải thưởng *(nhóm lặp 6 lần, D.1–D.6)* | region | — | visible | Always | — | static | `<section id="<slug>">` có `aria-labelledby`; ảnh đảo trái/phải theo chỉ số chẵn/lẻ; thẻ cuối không có đường kẻ đóng | — | binding: `#<slug>` (đích của E07 và của deep link từ trang chủ) |
| E09 | Ảnh giải thưởng | image | — | visible | Always | — | static | 336×336, bo góc 24px, viền vàng; `alt` = tiêu đề giải | — | N/A |
| E10 | Tiêu đề giải | display field | — | visible | Always | — | static | `<h2 id="<slug>-title">`, vàng, có biểu tượng trắng phía trước | — | N/A |
| E11 | Mô tả giải | display field | — | visible | Always | — | static | một hoặc hai đoạn — Signature và MVP có hai đoạn, bốn giải còn lại một đoạn | — | N/A |
| E12 | Dòng "Số lượng giải thưởng:" + giá trị | display field | — | visible | Always | — | static | nhãn vàng có biểu tượng; số và đơn vị là hai phần tử lá riêng biệt | — | N/A |
| E13 | Dòng "Giá trị giải thưởng:" + danh sách mức giải | display field | — | visible | Always | — | static | nhãn lặp lại cho từng mức, đúng như frame vẽ; hai mức nối bằng dòng `Hoặc` + đường kẻ | dòng ghi chú không render khi giải không có ghi chú | N/A |
| E14 | Khối Sun* Kudos *(tái dùng)* | region | — | visible | Always | — | static | `<section>` riêng, khung `max-w-[1440px]` | — | N/A |
| E15 | Nút "Chi tiết" của khối Kudos | link | — | enabled | Always | Điều hướng `/kudos` | static | — | — | N/A |
| E16 | Footer *(tái dùng nguyên trạng)* | region | — | visible | Always | Điều hướng theo từng liên kết | static | raw | — | N/A |

## 4. User Actions

> **Scope:** within-screen interactions only. Điều hướng ra ngoài màn hình xem ở `## 8. Navigation`.

### Available Actions

| Action | Element | Trigger | Condition | Result on this screen | Source |
|--------|---------|---------|-----------|------------------------|--------|
| Nhảy tới một hạng mục | E07 | click | không có phím bổ trợ, nút chuột chính | Cuộn tới thẻ E08 tương ứng, mục vừa bấm sáng lên, địa chỉ trang đổi thành `#<slug>` mà không thêm bước lùi lịch sử | `award-category-nav.tsx:41-52`, `use-award-scroll-spy.ts:176-193` |
| Mở hạng mục ở tab mới | E07 | click + Ctrl/Cmd/Shift/Alt, hoặc nút chuột khác | — | Không nuốt sự kiện — trình duyệt xử lý `href="#<slug>"` như liên kết thường | `award-category-nav.tsx:46-47` |
| Cuộn đọc trang | E08 | scroll | — | Mục menu sáng tự đổi theo hạng mục đang trong dải đo; luôn đúng một mục sáng | `use-award-scroll-spy.ts:81-105,149-165` |
| Ghi đè cú bấm đang cuộn | — | wheel / touchstart / keydown trong 700ms sau cú bấm | đang trong khoảng khoá | Khoá nhả ngay, mục sáng trả về hạng mục thật sự trên màn hình | `use-award-scroll-spy.ts:114-136` |
| Đổi ngôn ngữ | E01 | click | — | Toàn bộ nội dung màn hình chuyển sang ngôn ngữ đã chọn *(tái dùng, không phải hành vi riêng của màn hình này)* | `app/_components/language-selector.tsx` |

### Happy Path

1. Khách tới `/awards-information` từ trang chủ, thường kèm `#<slug>` của hạng mục vừa bấm; trang dừng ở đúng thẻ đó và mục menu tương ứng sáng lên sau khi hydrate.
2. Khách cuộn đọc lần lượt sáu thẻ; menu bên trái chạy theo, luôn chỉ một mục sáng.
3. Khách bấm một mục menu để nhảy thẳng tới hạng mục quan tâm; địa chỉ trang đổi theo.
4. Cuối trang, khách bấm `Chi tiết` ở khối Sun* Kudos để đi tiếp, hoặc dùng header/footer.

### Branches

N/A — màn hình đọc; các điều kiện hiện/ẩn đã liệt kê ở `## 7. Conditional UI`, không phải rẽ nhánh trong một luồng hành động.

### Interaction Notes

- **Menu danh mục dính theo trang cuộn từ `lg` và luôn có đúng một mục sáng; cú bấm khoá quyền ghi tối đa 700ms, sau đó vị trí cuộn quyết định** — source: `use-award-scroll-spy.ts:25,156-165,176-193`
- **Bấm mục menu thay thế mục lịch sử hiện tại chứ không thêm mới, để nút Back quay về trang trước chứ không lùi qua từng hạng mục vừa xem** — source: `use-award-scroll-spy.ts:186`
- **Người dùng bật chế độ giảm chuyển động thì cú nhảy là tức thì, không cuộn mượt** — source: `use-award-scroll-spy.ts:180,184,189`
- **Deep link chỉ điều khiển vị trí, không điều khiển mục sáng** — hash được đối chiếu với danh sách slug cố định rồi `scrollIntoView({ behavior: "auto" })`; mục sáng do phép đo vị trí sửa lại sau khi hydrate — source: `use-award-scroll-spy.ts:143-147`
- **Một hằng số CSS `--award-header-offset` là nguồn duy nhất cho `top` của menu dính, `scroll-margin-top` của thẻ, và đỉnh dải đo** — ghim `112px` ở `lg`, đo chiều cao header thật + 40px ở dưới `lg` — source: `page.tsx:32`, `use-award-scroll-spy.ts:19-22,57-73`

## 5. UI States

| State | Trigger | Visual Behavior | User Action Available | Source |
|-------|---------|----------------|-----------------------|--------|
| loading | N/A — không có thao tác bất đồng bộ nào lúc mở trang; nội dung do server render | — | — | `page.tsx:55-125` |
| empty | N/A — sáu hạng mục là hằng số, không có danh sách nào có thể rỗng | — | — | `lib/awards.ts:27-42` |
| error | N/A — không có thao tác bất đồng bộ nào có thể lỗi | — | — | — |
| saving | N/A — không có form hay thao tác ghi | — | — | — |
| success | N/A — không có thao tác ghi nên không có trạng thái thành công riêng | — | — | — |
| default | Mở `/awards-information` không kèm hash | Trang mở từ hero, mục menu đầu tiên (Top Talent) sáng | Cuộn, bấm mục menu | `use-award-scroll-spy.ts:31` |
| hash-seeded (deep link) | Mở trang với `#<slug>` khớp một hạng mục | Trang dừng ở thẻ tương ứng tức thì; mục menu đó sáng sau khi hydrate (~290ms — ORCH-04) | Cuộn tiếp, bấm mục menu khác | `use-award-scroll-spy.ts:143-147` |
| hash không khớp | Mở trang với hash lạ | Không cuộn, mục đầu tiên sáng, không có lỗi console | Cuộn tiếp, bấm mục menu | `use-award-scroll-spy.ts:145` |
| reduced-motion | Hệ điều hành báo `prefers-reduced-motion: reduce` | Bấm mục menu nhảy tức thì tới thẻ, không có hiệu ứng cuộn | Như thường | `use-award-scroll-spy.ts:180,184` |
| pre-hydration | Trang đã hiện nhưng client chưa hydrate | Sáu thẻ và menu vẫn đọc được (server render); mục sáng chưa tự đổi theo cuộn | Cuộn đọc bình thường | `award-category-nav.tsx:19-35` |

## 6. Validation & Feedback

N/A — no validation rules or submit-side error feedback detected. *(Không có ô nhập nào trên màn hình này — thuần đọc và điều hướng.)*

## 7. Conditional UI

| Condition | Type | Element(s) | Visible when | Hidden when | Notes |
|-----------|------|------------|--------------|-------------|-------|
| Mục menu ở trạng thái đang sáng | state | E07 | mục đó là hạng mục đang đọc | các mục còn lại | Chữ vàng + gạch chân vàng + `aria-current="true"`; tại mọi thời điểm chỉ đúng một mục ở trạng thái này |
| Mức giải thứ hai của một hạng mục | data | E13 | hạng mục có nhiều hơn một mức giải (chỉ Signature 2025 - Creator) | năm hạng mục còn lại | Hai mức nối bằng dòng `Hoặc` kèm đường kẻ |
| Dòng ghi chú dưới số tiền giải | data | E13 | hạng mục có ghi chú (`cho mỗi giải thưởng`, `cho giải cá nhân`, `cho giải tập thể`) | Best Manager, MVP | Khoá `note` vắng mặt ở từ điển, không phải chuỗi rỗng — nên không có phần tử rỗng nào được render |
| Đường kẻ đóng dưới thẻ | data | E08 | thẻ không phải thẻ cuối | thẻ MVP (D.6) | Frame không vẽ đường kẻ dưới thẻ cuối |
| Chuông thông báo và biểu tượng tài khoản trên header | auth | E01 | có phiên đăng nhập hợp lệ | chưa đăng nhập | Hành vi tái dùng nguyên trạng của header, không phải quy tắc riêng của màn hình này |

## 8. Navigation

### Entry Points

| From | Trigger there | Condition | Source |
|------|----------------|-----------|--------|
| SCR002_Homepage | bấm bất kỳ phần nào của một thẻ giải thưởng → tới `/awards-information#<slug>` | — | `app/_components/award-card.tsx` |
| SCR002_Homepage | bấm mục nav "Award Information", hoặc nút "ABOUT AWARDS" ở hero, hoặc liên kết "Award Information" ở footer | — | `app/_components/{home-nav,home-hero,site-footer}.tsx` |
| external \| direct URL | mở thẳng `/awards-information` (có hoặc không kèm `#<slug>`) | — | `app/awards-information/page.tsx` |
| SCR *(các màn hình khác dùng chung header/footer)* | bấm mục nav hoặc liên kết footer "Award Information" | — | `app/_components/{home-nav,site-footer}.tsx` |

### Exits

| Action | Element | Condition | Destination | Result | Source |
|--------|---------|-----------|-------------|--------|--------|
| Xem Sun* Kudos | E15 | — | `/kudos` *(vẫn là shell `ComingSoon`)* | redirect | `app/_components/kudos-promo.tsx` |
| Về trang chủ | E01 (logo, mục nav "About SAA 2025"), E16 | — | SCR002_Homepage | redirect | `app/_components/{home-nav,site-footer}.tsx` |
| Xem Sun* Kudos / Tiêu chuẩn chung qua chrome dùng chung | E01, E16 | — | `/kudos`, `/standards` *(placeholder)* | redirect | `app/_components/{home-nav,site-footer}.tsx` |
| Xem Profile / Admin Dashboard / đăng xuất | E01 | đã đăng nhập; Admin Dashboard chỉ khi có quyền admin | `/profile`, `/admin`, `/login` | redirect | `app/_components/account-menu.tsx` |

## 9. Accessibility

| Aspect | Status | Notes |
|--------|--------|-------|
| ARIA roles/labels | [VERIFIED] | Menu danh mục là `<nav>` có tên truy cập riêng ("Danh mục giải thưởng"), tách khỏi hai landmark điều hướng còn lại (header, footer); mục đang sáng mang `aria-current="true"`, các mục khác không có thuộc tính đó |
| Keyboard navigation | [VERIFIED] | Sáu mục là `<a href>` thật nên tới được bằng Tab và kích hoạt bằng Enter; vành tiêu điểm vàng `focus-visible` hiện rõ trên nền tối |
| Focus management | [EXPECTED] | Cú nhảy không cướp tiêu điểm về đầu trang. Tiêu điểm **không** được chuyển sang thẻ đích sau khi cuộn — người dùng bàn phím vẫn ở mục menu vừa kích hoạt và tiếp tục bằng Tab. Đây là hành vi đã ship, chưa được đánh giá riêng bằng test |
| Screen reader compatibility | [VERIFIED] | Đúng một `<h1>`; thứ tự tiêu đề `h1` → sáu `h2` → `h2` của khối Kudos; mỗi thẻ là `<section aria-labelledby="{slug}-title">` nên đọc lên đúng tên hạng mục. Ảnh giải thưởng dùng tiêu đề giải làm `alt` |
| Error announcement | [VERIFIED] | N/A — màn hình không có thông báo lỗi nào cần công bố |
| Motion | [EXPECTED] | Tôn trọng `prefers-reduced-motion`: nhảy tức thì thay vì cuộn mượt. Đã code, chưa có test tự động (F003 § 11 RISK-05) |

> `[VERIFIED]` = được khẳng định bởi test `W-3` trong `e2e/award-system.spec.ts` và ảnh chụp cây a11y ở
> `plans/260906-0719-award-system-screen/evidence/aria-snapshot-award-system.yaml`.

## 10. Responsive Behavior

| Breakpoint | Region / Element | Behavior | Source |
|------------|-------------------|----------|--------|
| ≥1024px (`lg`) | R3a / R3b | Hai cột `justify-between`: menu 178px dính bên trái, cột thẻ basis 853px bên phải; ảnh trong thẻ đảo trái/phải theo chỉ số chẵn/lẻ (Top Talent trái, Top Project phải, …) | `page.tsx:86-110`, `award-category-nav.tsx:64` |
| <1024px (tablet + mobile) | R3a / R3b | Gộp về một cột; menu thành hàng cuộn ngang phía trên; trong mỗi thẻ ảnh lên trước phần chữ | `page.tsx:86`, `award-detail-card.tsx:64`, `award-category-nav.tsx:64` |
| <1024px | R1 / offset cuộn | Header xuống nhiều dòng (`flex-wrap`), nên chiều cao thật của nó được đo và công bố vào `--award-header-offset` (+40px thở); ở 375px đo được 245px → offset 285px | `use-award-scroll-spy.ts:57-73` |
| ≥1024px | R2 hero | Khung nội dung hero cap ở 1152px, thẳng mép với cột thẻ ở mọi bề rộng ≥1440 | `award-system-hero.tsx:54` |
