---
status: promoted
authored_by: takumi
fcode: F003
created: 2026-09-06
lang: vi
---

> **PROMOTED 2026-09-06** → `docs/screens/SCR003_AwardSystem/spec.md`. Bản này là bản nháp lịch sử của phase 01; bản trong `docs/` là bản có hiệu lực. Đừng sửa file này.

# SCR-award-system — Screen Spec

**Screen**: SCR-award-system *(draft — mã global dự kiến `SCR003_AwardSystem`, cấp chính thức lúc promote)*: Hệ thống giải
**Feature**: F003_AwardSystem
**Type**: atomic
**Route**: `/awards-information`
**Generated**: 2026-09-06

## 1. Overview

**Purpose:** Màn hình công khai trình bày đầy đủ hệ thống giải thưởng SAA 2025 — sáu hạng mục, mỗi hạng mục vinh danh ai, có bao nhiêu giải và giá trị bao nhiêu — thay chỗ shell "Coming soon" mà mọi thẻ giải thưởng trên trang chủ đang dẫn tới.
**Actors:** Khách truy cập, Người dùng đã đăng nhập
**Entry Conditions:** Không yêu cầu gì — route công khai. Phần lớn lượt vào đi từ trang chủ, thường kèm `#<slug>` của hạng mục vừa bấm.
**Exit Conditions:** Khách rời trang qua một liên kết điều hướng (header, footer, hoặc nút `Chi tiết` của khối Sun* Kudos). Không có trạng thái "hoàn tất" bắt buộc — đây là trang đọc.

## 2. Screen Layout

### Layout Sketch

Một trang cuộn dọc liên tục. R1 header dính trên cùng. R3 là phần chính, chia hai cột: menu danh mục (R3a) dính bên trái theo suốt chiều cao của cột thẻ, sáu thẻ giải thưởng (R3b) xếp dọc bên phải với ảnh đảo trái/phải theo thứ tự lẻ/chẵn. Không có widget nổi trên màn hình này. *(design/award-system.png, 1440×6410)*

```
┌──────────────────────────────────────────────────┐
│  R1: Header (sticky-top) — "Award Information"    │
│      đang chọn                                    │
├──────────────────────────────────────────────────┤
│  R2: Hero — keyvisual + ROOT FURTHER wordmark     │
│      + eyebrow / divider / tiêu đề vàng (giữa)    │
├───────────────┬──────────────────────────────────┤
│  R3a: Menu    │  R3b: 6 thẻ chi tiết giải thưởng │
│  danh mục     │   D.1 [ảnh trái ] ...            │
│  (sticky)     │   D.2 [... ảnh phải]             │
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
| R1 | Header | sticky-top | no | `TBD (draft)` — tái dùng header của SCR-homepage |
| R2 | Hero | static | yes (part of page scroll) | `TBD (draft)` |
| R3a | Menu danh mục | sticky (trong R3) | no | `TBD (draft)` |
| R3b | Cột sáu thẻ giải thưởng | static | yes | `TBD (draft)` |
| R4 | Khối Sun* Kudos | static | yes | `TBD (draft)` — tái dùng khối của SCR-homepage |
| R5 | Footer | static | yes | `TBD (draft)` — tái dùng footer của SCR-homepage |

## 3. UI Elements

| ID | Element | Type | Required | Default | Visibility | Action | Source | Format | Empty Behavior | Cross-ref |
|----|---------|------|----------|---------|------------|--------|--------|--------|-----------------|-----------|
| E01 | Header *(tái dùng nguyên trạng)* | region | — | visible | Always | Điều hướng theo từng mục; mục "Award Information" đang chọn trên route này | static | raw | — | binding: đường dẫn hiện tại |
| E02 | Hero keyvisual | image | — | visible | Always | — | static | raw | — | N/A |
| E03 | Chữ hình "ROOT FURTHER" | image | — | visible | Always | — | static | raw | — | N/A |
| E04 | Eyebrow "Sun* Annual Awards 2025" | display field | — | visible | Always | — | static | raw (trắng, canh giữa) | — | N/A |
| E05 | Đường kẻ mảnh dưới eyebrow | display field | — | visible | Always | — | static | raw | — | N/A |
| E06 | Tiêu đề "Hệ thống giải thưởng SAA 2025" | display field | — | visible | Always | — | static | raw (vàng `#FFEA9E`, canh giữa) | — | N/A |
| E07 | Mục menu danh mục *(nhóm lặp 6 lần theo thứ tự: Top Talent, Top Project, Top Project Leader, Best Manager, Signature 2025 Creator, MVP)* | button | — | mục đầu tiên đang sáng | Always | Bấm → cuộn tới thẻ tương ứng, địa chỉ đổi thành `#<slug>` | computed (vị trí cuộn / hash / cú bấm) | raw, có biểu tượng 24×24 phía trước | — | binding: `#<slug>` của thẻ tương ứng |
| E08 | Thẻ chi tiết giải thưởng *(nhóm lặp 6 lần, D.1–D.6)* | region | — | visible | Always | — | static | ảnh đảo trái/phải theo chỉ số lẻ/chẵn | — | binding: `#<slug>` (đích của E07 và của deep link từ trang chủ) |
| E09 | Ảnh giải thưởng | image | — | visible | Always | — | static | 336×336, bo góc, viền vàng | — | N/A |
| E10 | Tiêu đề giải | display field | — | visible | Always | — | static | raw, có biểu tượng phía trước | — | N/A |
| E11 | Mô tả giải | display field | — | visible | Always | — | static | raw; Signature và MVP có hai đoạn, bốn giải còn lại một đoạn | — | N/A |
| E12 | Dòng "Số lượng giải thưởng:" + giá trị | display field | — | visible | Always | — | static | nhãn vàng có biểu tượng; giá trị dạng `<số> <đơn vị>` | — | N/A |
| E13 | Dòng "Giá trị giải thưởng:" + danh sách mức giải | display field | — | visible | Always | — | static | nhãn vàng có biểu tượng; một hoặc hai mức, hai mức nối bằng `Hoặc` | dòng ghi chú không render khi giải không có ghi chú | N/A |
| E14 | Khối Sun* Kudos *(tái dùng nguyên trạng)* | region | — | visible | Always | — | static | raw | — | N/A |
| E15 | Nút "Chi tiết" của khối Kudos | button | — | enabled | Always | Điều hướng `/kudos` | static | — | — | N/A |
| E16 | Footer *(tái dùng nguyên trạng)* | region | — | visible | Always | Điều hướng theo từng liên kết | static | raw | — | N/A |

## 4. User Actions

> **Scope:** within-screen interactions only. Điều hướng ra ngoài màn hình xem ở `## 8. Navigation`.

### Available Actions

| Action | Element | Trigger | Condition | Result on this screen | Source |
|--------|---------|---------|-----------|------------------------|--------|
| Nhảy tới một hạng mục | E07 | click | — | Cuộn tới thẻ E08 tương ứng, mục vừa bấm sáng lên, địa chỉ trang đổi thành `#<slug>` mà không thêm bước lùi lịch sử | `TBD (draft)` |
| Cuộn đọc trang | E08 | scroll | — | Mục menu sáng tự đổi theo hạng mục đang hiện trên màn hình; luôn đúng một mục sáng | `TBD (draft)` |
| Đổi ngôn ngữ | E01 | click | — | Toàn bộ nội dung màn hình chuyển sang ngôn ngữ đã chọn *(tái dùng, không phải hành vi riêng của màn hình này)* | `TBD (draft)` |

### Happy Path

1. Khách tới `/awards-information` từ trang chủ, thường kèm `#<slug>` của hạng mục vừa bấm; trang mở ở đúng thẻ đó và mục menu tương ứng sáng.
2. Khách cuộn đọc lần lượt sáu thẻ; menu bên trái chạy theo, luôn chỉ một mục sáng.
3. Khách bấm một mục menu để nhảy thẳng tới hạng mục quan tâm; địa chỉ trang đổi theo.
4. Cuối trang, khách bấm `Chi tiết` ở khối Sun* Kudos để đi tiếp, hoặc dùng header/footer.

### Branches

N/A — màn hình đọc; các điều kiện hiện/ẩn đã liệt kê ở `## 7. Conditional UI`, không phải rẽ nhánh trong một luồng hành động.

### Interaction Notes

- **Menu danh mục dính theo trang cuộn và luôn có đúng một mục sáng; nguồn quyết định là cú bấm gần nhất, rồi hash lúc mở trang, rồi vị trí cuộn** — source: `TBD (draft)`
- **Bấm mục menu thay thế mục lịch sử hiện tại chứ không thêm mới, để nút Back quay về trang chủ chứ không lùi qua từng hạng mục vừa xem** — source: `TBD (draft)`
- **Người dùng bật chế độ giảm chuyển động thì cú nhảy là tức thì, không cuộn mượt** — source: `TBD (draft)`

## 5. UI States

| State | Trigger | Visual Behavior | User Action Available | Source |
|-------|---------|----------------|-----------------------|--------|
| loading | N/A — không có thao tác bất đồng bộ nào lúc mở trang; nội dung là tĩnh | — | — | `TBD (draft)` |
| empty | N/A — sáu hạng mục là hằng số, không có danh sách nào có thể rỗng | — | — | `TBD (draft)` |
| error | N/A — không có thao tác bất đồng bộ nào có thể lỗi | — | — | `TBD (draft)` |
| saving | N/A — không có form hay thao tác ghi | — | — | `TBD (draft)` |
| success | N/A — không có thao tác ghi nên không có trạng thái thành công riêng | — | — | `TBD (draft)` |
| custom — mở trang bằng deep link | Mở trang với `#<slug>` khớp một hạng mục | Trang dừng ở thẻ tương ứng, mục menu đó sáng ngay | Cuộn tiếp, bấm mục menu khác | `TBD (draft)` |
| custom — hash không khớp | Mở trang với hash lạ hoặc không có hash | Trang mở từ đầu, mục đầu tiên sáng, không có cú nhảy | Cuộn tiếp, bấm mục menu | `TBD (draft)` |
| custom — giảm chuyển động | Hệ điều hành báo `prefers-reduced-motion` | Bấm mục menu nhảy tức thì tới thẻ, không có hiệu ứng cuộn | Như thường | `TBD (draft)` |
| custom — phần tương tác chưa sẵn sàng | Trang đã hiện nhưng client chưa chạy | Sáu thẻ và menu vẫn đọc được; mục sáng chưa tự đổi theo cuộn | Cuộn đọc bình thường | `TBD (draft)` |

## 6. Validation & Feedback

N/A — no validation rules or submit-side error feedback detected. *(Không có ô nhập nào trên màn hình này — thuần đọc và điều hướng.)*

## 7. Conditional UI

| Condition | Type | Element(s) | Visible when | Hidden when | Notes |
|-----------|------|------------|--------------|-------------|-------|
| Mục menu ở trạng thái đang sáng | state | E07 | mục đó là hạng mục đang đọc | các mục còn lại | Chữ vàng + gạch chân vàng; tại mọi thời điểm chỉ đúng một mục ở trạng thái này |
| Mức giải thứ hai của một hạng mục | data | E13 | hạng mục có nhiều hơn một mức giải (chỉ Signature 2025 - Creator) | năm hạng mục còn lại | Hai mức nối bằng dòng `Hoặc` |
| Dòng ghi chú dưới số tiền giải | data | E13 | hạng mục có ghi chú (`cho mỗi giải thưởng`, `cho giải cá nhân`, `cho giải tập thể`) | Best Manager, MVP | Không render dòng rỗng khi không có ghi chú |
| Chuông thông báo và biểu tượng tài khoản trên header | auth | E01 | có phiên đăng nhập hợp lệ | chưa đăng nhập | Hành vi tái dùng nguyên trạng của header, không phải quy tắc riêng của màn hình này |

## 8. Navigation

> `## 8. Navigation` là hình chiếu theo màn hình của `screen-flow.md § Screen Access Paths`. Bản nháp greenfield chưa có `screen-flow.md`, nên mọi dòng dưới đây suy từ ý đồ thiết kế và cột `Source` là `TBD (draft)` cho tới khi đối chiếu lúc promote.

### Entry Points

| From | Trigger there | Condition | Source |
|------|----------------|-----------|--------|
| SCR-homepage | bấm bất kỳ phần nào của một thẻ giải thưởng → tới `/awards-information#<slug>` | — | `TBD (draft)` |
| SCR-homepage | bấm mục nav "Award Information", hoặc nút "ABOUT AWARDS" ở hero, hoặc liên kết "Award Information" ở footer | — | `TBD (draft)` |
| external \| direct URL | mở thẳng `/awards-information` (có hoặc không kèm `#<slug>`) | — | `TBD (draft)` |
| SCR *(các màn hình khác dùng chung header/footer)* | bấm mục nav hoặc liên kết footer "Award Information" | — | `TBD (draft)` |

### Exits

| Action | Element | Condition | Destination | Result | Source |
|--------|---------|-----------|-------------|--------|--------|
| Xem Sun* Kudos | E15 | — | *(Sun* Kudos placeholder)* | redirect | `TBD (draft)` |
| Về trang chủ | E01 (logo, mục nav "About SAA 2025"), E16 | — | SCR-homepage | redirect | `TBD (draft)` |
| Xem Sun* Kudos / Tiêu chuẩn chung qua chrome dùng chung | E01, E16 | — | *(các placeholder tương ứng)* | redirect | `TBD (draft)` |
| Xem Profile / Admin Dashboard / đăng xuất | E01 | đã đăng nhập; Admin Dashboard chỉ khi có quyền admin | *(đích của header tái dùng)* | redirect | `TBD (draft)` |

## 9. Accessibility

| Aspect | Status | Notes |
|--------|--------|-------|
| ARIA roles/labels | [EXPECTED] | Menu danh mục là danh sách điều hướng trong trang: mỗi mục có tên truy cập đúng bằng nhãn hiển thị, mục đang sáng được đánh dấu là mục hiện hành |
| Keyboard navigation | [EXPECTED] | Sáu mục menu phải tới được bằng Tab và kích hoạt được bằng Enter/Space; sau khi nhảy, tiêu điểm chuyển tới thẻ đích để người dùng bàn phím đọc tiếp được ngay |
| Focus management | [EXPECTED] | Cú nhảy không được cướp tiêu điểm về đầu trang; vành tiêu điểm phải thấy rõ trên nền tối |
| Screen reader compatibility | [EXPECTED] | Mỗi thẻ có tiêu đề cấp mục để trình đọc màn hình duyệt được theo tiêu đề; ảnh giải thưởng là ảnh trang trí kèm tiêu đề văn bản nên không cần mô tả lặp lại |
| Error announcement | [EXPECTED] | N/A — màn hình không có thông báo lỗi nào cần công bố |
| Motion | [EXPECTED] | Tôn trọng `prefers-reduced-motion`: nhảy tức thì thay vì cuộn mượt |

## 10. Responsive Behavior

| Breakpoint | Region / Element | Behavior | Source |
|------------|-------------------|----------|--------|
| ≥1024px (desktop) | R3a / R3b | Hai cột: menu dính bên trái, cột thẻ bên phải; ảnh trong thẻ đảo trái/phải theo thứ tự lẻ/chẵn (Top Talent trái, Top Project phải, …) | clarifications.md — "Card layout alternation" |
| <1024px (tablet + mobile) | R3a / R3b | Gộp về một cột, ảnh lên trước phần chữ trong mỗi thẻ | clarifications.md — "Card layout alternation" |
