---
status: draft
authored_by: takumi
created: 2026-09-07
lang: vi
---

# SCR-VietKudo — Screen Spec

**Screen**: SCR-VietKudo: Viết Kudo
**Feature**: F000_VietKudo
**Type**: atomic
**Route**: `/kudos/new`
**Generated**: 2026-09-07

## 1. Overview

**Purpose:** Sunner đã đăng nhập soạn và gửi một Kudos cho đồng nghiệp — chọn người nhận, đặt Danh hiệu, viết nội dung có định dạng, gắn hashtag, đính kèm ảnh, và tuỳ chọn gửi ẩn danh.
**Actors:** Sunner (đã đăng nhập)
**Entry Conditions:** Phiên đăng nhập hợp lệ. Chưa đăng nhập → chuyển hướng sang `/login` trước khi màn hình này render (route guard, không phải một trạng thái của chính màn hình).
**Exit Conditions:** Gửi thành công (Kudos mới được ghi và hiển thị trên bảng tin) hoặc bấm Hủy — cả hai đưa trình duyệt về `/kudos`.

## 2. Screen Layout

### Layout Sketch

Trang một cột, không phải modal chồng route — thẻ soạn Kudos căn giữa trên nền trang đã làm mờ nhẹ, đúng hình ảnh trong frame (`design/viet-kudo.png`, 1440×1024). Từ trên xuống: tiêu đề trang, khối trường Người nhận, khối Danh hiệu, khối soạn nội dung (toolbar + textarea + hint), khối Hashtag, khối Image, checkbox ẩn danh (kèm ô tên hiển thị khi bật), rồi footer chứa hai nút Hủy/Gửi căn phải.

```
┌───────────────────────────────────────────┐
│  R1: Tiêu đề trang (static)                │
├───────────────────────────────────────────┤
│  R2: Người nhận (static)                   │
│  R3: Danh hiệu (static)                    │
│  R4: Soạn nội dung — toolbar + textarea    │
│      (static, mention-menu nổi khi gõ @)   │
│  R5: Hashtag — nút thêm + chip (static)    │
│  R6: Image — nút thêm + thumbnail (static) │
│  R7: Checkbox ẩn danh (- - ô tên hiện có   │
│       điều kiện - -)                       │
├───────────────────────────────────────────┤
│  R8: Footer Hủy/Gửi (static, căn phải)     │
└───────────────────────────────────────────┘
```

### Layout Regions

| Region ID | Name | Position | Scrollable | Key Components |
|-----------|------|----------|------------|----------------|
| R1 | Tiêu đề trang | static | no | TBD (draft) |
| R2 | Người nhận | static | no | TBD (draft) |
| R3 | Danh hiệu | static | no | TBD (draft) |
| R4 | Soạn nội dung | static | no | TBD (draft) |
| R5 | Hashtag | static | no | TBD (draft) |
| R6 | Image | static | no | TBD (draft) |
| R7 | Checkbox ẩn danh | static | no | TBD (draft) |
| R8 | Footer hành động | static | no | TBD (draft) |

## 3. UI Elements

| ID | Element | Type | Required | Default | Visibility | Action | Source | Format | Empty Behavior | Cross-ref |
|----|---------|------|----------|---------|------------|--------|--------|--------|-----------------|-----------|
| E01 | Người nhận | text input | yes | Empty | Always | Gõ để tìm, chọn từ danh sách gợi ý (requires E02) | — | raw | placeholder "Tìm kiếm" | `data-testid: recipient-input` |
| E02 | Danh sách gợi ý người nhận | list | — | Hidden | Conditional | Chọn một người điền vào E01 | — | raw | — | `data-testid: recipient-menu`, role listbox |
| E03 | Không tìm thấy người nhận | message | — | Hidden | Conditional | — | — | raw | — | `data-testid: recipient-empty` |
| E04 | Danh hiệu | text input | yes | Empty | Always | Gõ tiêu đề Kudos | — | raw | placeholder "Dành tặng một danh hiệu cho đồng đội" | `data-testid: title-input` |
| E05 | Gợi ý Danh hiệu | message | — | — | Always | — | — | raw | — | `data-testid: title-hint`; text "Ví dụ: Người truyền động lực cho tôi." + "Danh hiệu sẽ hiển thị làm tiêu đề Kudos của bạn." |
| E06 | Ô soạn nội dung | textarea | yes | Empty | Always | Gõ nội dung, bôi đen để áp định dạng (requires E08) | — | raw | placeholder "Hãy gửi gắm lời cám ơn và ghi nhận đến đồng đội tại đây nhé!" | `data-testid: body-editor` |
| E07 | Gợi ý mention | message | — | — | Always | — | — | raw | — | `data-testid: body-hint`; text "Bạn có thể "@ + tên" để nhắc tới đồng nghiệp khác" |
| E08 | Toolbar định dạng {đậm, nghiêng, gạch ngang, danh sách đánh số, liên kết, trích dẫn} | button {x6} | — | Enabled | Always | Áp/gỡ định dạng cho phần đang bôi đen trong E06; nút liên kết mở E09 | — | — | — | `data-testid: toolbar-bold/italic/strike/ordered-list/link/quote`; nút đậm/nghiêng carry `aria-pressed` |
| E09 | Hộp thoại nhập liên kết | dialog | — | Hidden | Conditional | Nhập URL, xác nhận để chèn liên kết vào E06 | — | raw | — | `data-testid: link-dialog` (chứa `link-url-input`) |
| E10 | Danh sách gợi ý mention | list | — | Hidden | Conditional | Gõ `@ + tên` mở ra; chọn một người chèn vào E06 | — | raw | — | `data-testid: mention-menu` (role listbox), `mention-option` (role option) |
| E11 | Tiêu chuẩn cộng đồng | link | — | Enabled | Always | Mở trang tiêu chuẩn cộng đồng | — | — | — | `data-testid: community-standards-link` |
| E12 | Nút thêm Hashtag | button | — | Enabled | Always | Mở E13 (requires E13) | — | — | — | `data-testid: hashtag-add`; label chứa "Hashtag" và "Tối đa 5" |
| E13 | Danh sách chọn Hashtag | list | — | Hidden | Conditional | Chọn một hashtag thêm vào E14 | — | raw | — | `data-testid: hashtag-menu` (role listbox); nguồn dữ liệu companion frame `p9zO-c4a4x` |
| E14 | Chip hashtag đã chọn {chip_1..5} | display field {x1-5} | — | Hidden | Conditional | Bấm nút xoá trên một chip để gỡ đúng chip đó (requires E12) | — | raw | không hiện chip nào | `data-testid: hashtag-chip`, `hashtag-chip-remove` |
| E15 | Lỗi tối đa hashtag | message | — | Hidden | Conditional | — | — | raw | — | `data-testid: hashtag-error`; text "Tối đa 5 hashtag" |
| E16 | Nút thêm Image | button | — | Enabled | Conditional | Mở file picker (requires E17) | — | — | — | `data-testid: image-add`; label chứa "Image" và "Tối đa 5"; ẩn hoàn toàn khi đã đủ 5 ảnh |
| E17 | Input chọn file ảnh | file input | — | Empty | Always | Chọn 1+ file ảnh | — | raw | — | `data-testid: image-input`, `accept` giới hạn kiểu ảnh, `multiple` |
| E18 | Thumbnail ảnh đã chọn {thumb_1..5} | image {x1-5} | — | Hidden | Conditional | Bấm nút xoá trên một thumbnail để gỡ đúng ảnh đó (requires E16) | — | raw | không hiện thumbnail nào | `data-testid: image-thumb`, `image-thumb-remove` |
| E19 | Lỗi định dạng ảnh | message | — | Hidden | Conditional | — | — | raw | — | `data-testid: image-error` |
| E20 | Checkbox gửi ẩn danh | checkbox | — | Unchecked | Always | Bật/tắt (requires E21 khi bật) | — | — | — | `data-testid: anonymous-checkbox`; label "Gửi lời cám ơn và ghi nhận ẩn danh" |
| E21 | Tên hiển thị ẩn danh | text input | no | Empty | Conditional | Gõ tên hiển thị tuỳ chọn | — | raw | — | `data-testid: anonymous-name-input`; ẩn khi E20 chưa bật |
| E22 | Lỗi trường bắt buộc {Người nhận, Danh hiệu, Nội dung, Hashtag} | message {x1-4} | — | Hidden | Conditional | — | — | raw | — | `data-testid: field-error-recipient/title/body/hashtag`; text "Không được để trống" |
| E23 | Hủy | button | — | Enabled | Always | Đóng form ngay, không lưu, điều hướng `/kudos` | — | — | — | `data-testid: compose-cancel`; label "Hủy" |
| E24 | Gửi | button | — | Disabled | Always | Validate rồi ghi Kudos, điều hướng `/kudos` khi thành công | — | — | — | `data-testid: compose-submit`; label "Gửi"; `disabled` khi Người nhận/Danh hiệu/Nội dung/Hashtag còn thiếu |

## 4. User Actions

> **Scope:** tương tác trong-màn-hình. Điều hướng rời màn hình xem `## 8. Navigation`.

### Available Actions

| Action | Element | Trigger | Condition | Result on this screen | Source |
|--------|---------|---------|-----------|------------------------|--------|
| Tìm và chọn người nhận | E01, E02, E03 | gõ, click một option | — | E01 điền tên đã chọn, E02 đóng | TBD (draft) |
| Áp định dạng văn bản | E08 | bôi đen rồi click một nút | có phần văn bản đang bôi đen trong E06 | Định dạng áp lên đúng phần đã bôi đen | TBD (draft) |
| Chèn liên kết | E08 (nút liên kết), E09 | click nút liên kết, nhập URL, xác nhận | — | Liên kết được chèn vào E06, E09 đóng | TBD (draft) |
| Mention đồng nghiệp | E06, E10 | gõ `@` rồi tiếp tục gõ tên, click một option | — | Tên được chèn vào đúng vị trí trong E06 | TBD (draft) |
| Thêm hashtag | E12, E13, E14 | click E12, chọn một hashtag | tổng số hashtag đã chọn < 5 | E14 thêm một chip mới | TBD (draft) |
| Thêm hashtag khi đã đủ 5 | E12, E13 | chọn một hashtag thứ 6 | tổng số hashtag đã chọn = 5 | E15 hiện, không có chip nào được thêm | TBD (draft) |
| Xoá hashtag | E14 | click nút xoá trên một chip | — | Đúng chip đó biến mất, các chip khác giữ nguyên | TBD (draft) |
| Thêm ảnh hợp lệ | E16, E17, E18 | click E16, chọn 1+ file ảnh đúng định dạng | tổng số ảnh đã đính kèm < 5 | Mỗi file hợp lệ hiện thành một thumbnail mới trong E18 | TBD (draft) |
| Chọn ảnh sai định dạng | E16, E17 | chọn một file không phải ảnh | — | E19 hiện, không có thumbnail nào được thêm | TBD (draft) |
| Xoá ảnh | E18 | click nút xoá trên một thumbnail | — | Đúng thumbnail đó biến mất; nếu vừa xuống dưới 5 thì E16 hiện lại | TBD (draft) |
| Bật ẩn danh | E20 | click checkbox (đang tắt) | — | E21 hiện ra ngay dưới E20 | TBD (draft) |
| Tắt ẩn danh | E20 | click checkbox (đang bật) | — | E21 ẩn đi | TBD (draft) |
| Submit rỗng | E24 | click khi thiếu trường bắt buộc | Người nhận/Danh hiệu/Nội dung/Hashtag còn thiếu | E22 hiện đồng thời cho mọi trường thiếu; không gửi đi | TBD (draft) |

### Happy Path

1. Sunner gõ vào E01 (Người nhận), chọn một người từ E02.
2. Sunner gõ vào E04 (Danh hiệu).
3. Sunner gõ nội dung vào E06, áp định dạng qua E08 nếu muốn, có thể mention một đồng nghiệp qua E10.
4. Sunner bấm E12, chọn 1–5 hashtag từ E13 — mỗi lựa chọn thêm một chip vào E14.
5. (Tuỳ chọn) Sunner bấm E16, chọn tối đa 5 ảnh hợp lệ — mỗi ảnh hiện thành một thumbnail trong E18.
6. (Tuỳ chọn) Sunner bật E20 — E21 hiện ra, có thể gõ tên hiển thị hoặc để trống.
7. Khi cả bốn trường bắt buộc đã đủ, E24 chuyển sang trạng thái có thể bấm. Sunner bấm E24 — form hiện trạng thái đang xử lý rồi trình duyệt rời màn hình (xem `## 8. Navigation`).

### Branches

| Decision point | Condition | Outcome on this screen | Source |
|----------------|-----------|------------------------|--------|
| Bước 4 | Đã chọn đủ 5 hashtag, cố chọn thêm | E15 hiện "Tối đa 5 hashtag"; chip không tăng thêm | TBD (draft) |
| Bước 5 | Đã đính kèm đủ 5 ảnh | E16 ẩn hoàn toàn cho tới khi một ảnh bị xoá | TBD (draft) |
| Bước 5 | File chọn không phải ảnh hợp lệ | E19 hiện lỗi định dạng; không có thumbnail nào được thêm | TBD (draft) |
| Bước 7 | Bấm E24 khi còn thiếu trường bắt buộc | E22 hiện đồng thời cho mọi trường thiếu; không rời màn hình | TBD (draft) |

## 5. UI States

| State | Trigger | Visual Behavior | User Action Available | Source |
|-------|---------|----------------|-----------------------|--------|
| loading | Trang vừa render, đang đọc danh sách Sunner/Hashtag | TBD (draft) — chưa quyết định skeleton hay chỉ hiện form rỗng | Chờ | TBD (draft) |
| empty | Gõ vào E01 không khớp Sunner nào | E03 hiện, E02 rỗng | Sửa lại chuỗi tìm | TBD (draft) |
| error | Submit thiếu trường / file sai định dạng / vượt quá 5 hashtag hoặc ảnh | E22 / E19 / E15 hiện đúng lỗi tương ứng | Sửa lại rồi thử lại | TBD (draft) |
| saving | Đã bấm E24 với dữ liệu hợp lệ, đang chờ server | E24 hiện trạng thái đang xử lý, không bấm được lần hai | Chờ | TBD (draft) |
| success | Server ghi Kudos thành công | Trình duyệt rời `/kudos/new`, về `/kudos` với Kudos mới đã hiển thị | — | TBD (draft) |

## 6. Validation & Feedback

| Element | Rule | Feedback | Trigger |
|---------|------|----------|---------|
| E01 | Bắt buộc, phải chọn từ danh sách Sunner có sẵn | "Không được để trống" (E22, `field-error-recipient`), viền đỏ trên E01, `aria-invalid="true"` | submit |
| E04 | Bắt buộc | "Không được để trống" (E22, `field-error-title`) | submit |
| E06 | Bắt buộc | "Không được để trống" (E22, `field-error-body`) | submit |
| E14 | Tối thiểu 1, tối đa 5 hashtag | Thiếu: "Không được để trống" (`field-error-hashtag`, submit). Vượt quá: "Tối đa 5 hashtag" (E15, change) | submit (thiếu) / change (vượt quá) |
| E17 | Chỉ nhận file đúng định dạng ảnh | Thông báo lỗi định dạng (E19) | change |

## 7. Conditional UI

| Condition | Type | Element(s) | Visible when | Hidden when | Notes |
|-----------|------|------------|--------------|-------------|-------|
| Ô tên hiển thị ẩn danh chỉ hiện khi đã bật gửi ẩn danh | configuration | E21 | E20 đang bật | E20 đang tắt | Trường tuỳ chọn, không có validation riêng |
| Nút thêm ảnh ẩn khi đã đủ 5 ảnh | configuration | E16 | tổng số ảnh đính kèm < 5 | tổng số ảnh đính kèm = 5 | Ẩn hoàn toàn, không phải disabled — khác hành vi giới hạn hashtag (E12 luôn hiện) |

## 8. Navigation

### Entry Points

| From | Trigger there | Condition | Source |
|------|----------------|-----------|--------|
| Kudos Live Board (`/kudos`) | Bấm thanh soạn Kudos | đã đăng nhập (không thì bị chuyển hướng `/login` trước khi tới đây) | TBD (draft) |

### Exits

| Action | Element | Condition | Destination | Result | Source |
|--------|---------|-----------|-------------|--------|--------|
| Hủy | E23 | — | `/kudos` | điều hướng thẳng, không lưu gì | TBD (draft) |
| Gửi thành công | E24 | tất cả trường bắt buộc hợp lệ, server ghi thành công | `/kudos` | điều hướng thẳng, Kudos mới đã hiển thị trên bảng tin | TBD (draft) |

## 9. Accessibility

| Aspect | Status | Notes |
|--------|--------|-------|
| ARIA roles/labels | [EXPECTED] | E02/E10/E13 dùng `role="listbox"` + `role="option"`; E01 mang `aria-invalid="true"` khi lỗi; E08 (đậm/nghiêng) mang `aria-pressed` |
| Keyboard navigation | [EXPECTED] | Toàn bộ trường và nút thao tác được bằng bàn phím, kể cả mở/đóng E09/E13 |
| Focus management | [EXPECTED] | E09 (hộp thoại liên kết) bẫy focus khi mở, trả focus lại đúng vị trí khi đóng |
| Screen reader compatibility | [EXPECTED] | Mỗi input có label liên kết đúng; E22/E15/E19 được đọc ra khi xuất hiện |
| Error announcement | [EXPECTED] | E22/E15/E19 dùng vùng `aria-live` để trình đọc màn hình thông báo lỗi ngay khi hiện ra |

## 10. Responsive Behavior

N/A — no responsive behavior found in source.
