---
status: implemented
authored_by: takumi
created: 2026-09-06
---

# SCR-KudosLiveBoard — Screen Spec

**Screen**: SCR-KudosLiveBoard (draft — SCR### allocated at promote)
**Feature**: KudosLiveBoard (fcode allocated at promote)
**Type**: composite
**Route**: `/kudos`
**Generated**: 2026-09-06

## Purpose

**Purpose:** Màn hình công khai nơi bất kỳ ai — đã đăng nhập hay ẩn danh — thấy được hoạt động ghi nhận Kudos đang diễn ra trong Sun*, lọc theo hashtag/phòng ban, và (nếu đã đăng nhập) thả tim cho một lời cảm ơn.
**Actors:** Sunner (đã đăng nhập), Khách ẩn danh
**Entry Conditions:** Vào trực tiếp URL `/kudos`, bấm mục "Sun* Kudos" trên nav trang chủ, hoặc bấm CTA của khối `KudosPromo` — không yêu cầu đăng nhập.
**Exit Conditions:** Rời màn hình qua bốn CTA điều hướng (soạn Kudos, Mở Secret Box, Xem chi tiết một kudos, hồ sơ Sunner/tìm Sunner) — mỗi CTA dẫn tới một route thật hiển thị `ComingSoon`; hoặc rời qua nav chung sang màn khác.

## Screen Layout

### Layout Sketch

Màn hình xếp dọc một cột theo thứ tự: header dùng chung (`HomeHeader`) → hero (nền KV + tiêu đề + wordmark KUDOS + thanh soạn Kudos + ô tìm Sunner) → khu vực HIGHLIGHT KUDOS (bộ lọc + carousel 5 card) → khu vực SPOTLIGHT BOARD (word-cloud + ticker + tìm kiếm) → hàng ngang gồm khu vực ALL KUDOS (feed cuộn vô hạn, cột chính) và sidebar cá nhân (cột phụ, cố định theo chiều cao nội dung) → footer dùng chung (`SiteFooter`). Không có modal/drawer nào trên màn hình này — bốn CTA điều hướng đều là link thật, không phải dialog.

```
┌──────────────────────────────────────────────┐
│  R1: Header (HomeHeader, sticky-top)          │
├──────────────────────────────────────────────┤
│  R2: Hero (KV background, static)             │
├──────────────────────────────────────────────┤
│  R3: Highlight Kudos (filters + carousel)     │
├──────────────────────────────────────────────┤
│  R4: Spotlight Board (word-cloud + ticker)    │
├───────────────────────────────┬──────────────┤
│  R5: All Kudos (scrollable)   │ R6: Sidebar   │
│                                │  (static)     │
├───────────────────────────────┴──────────────┤
│  R7: Footer (SiteFooter, static)              │
└──────────────────────────────────────────────┘
```

### Layout Regions

| Region ID | Name | Position | Scrollable | Key Components |
|-----------|------|----------|------------|----------------|
| R1 | Header | sticky-top | no | `HomeHeader` |
| R2 | Hero | static | no | tiêu đề, wordmark KUDOS, `kudos-compose`, `sunner-search` |
| R3 | Highlight Kudos | static | no | `highlight-section`, `filter-hashtag`, `filter-department`, `highlight-carousel` |
| R4 | Spotlight Board | static | no | `spotlight-section`, `spotlight-board`, `spotlight-search`, `spotlight-ticker` |
| R5 | All Kudos | yes (cuộn vô hạn) | yes | `all-kudos-section`, danh sách `kudos-card`, `feed-sentinel` |
| R6 | Sidebar | static | no | `kudos-sidebar`, `sidebar-stat` ×5, `secret-box-button`, `gift-leaderboard` |
| R7 | Footer | static | no | `SiteFooter` |

## User Flow

1. Người dùng vào R2 Hero, thấy tiêu đề, wordmark KUDOS, thanh soạn Kudos và ô tìm Sunner.
2. Người dùng cuộn xuống R3, thấy carousel Highlight 5 kudos nhiều tim nhất và hai nút lọc `Hashtag`/`Phòng ban`.
3. Người dùng bấm `filter-hashtag`, chọn một option trong `filter-menu-hashtag` — R3 và R5 lọc lại đồng thời, carousel quay về slide 1.
4. Người dùng cuộn xuống R4, gõ vào `spotlight-search` — word-cloud thu hẹp còn các node tên khớp.
5. Người dùng cuộn xuống R5, feed tải thêm card mỗi khi `feed-sentinel` lọt vào khung nhìn, tới khi hết dữ liệu.
6. Người dùng (đã đăng nhập) bấm `kudos-heart` trên một card — số đếm và `aria-pressed` đổi ngay, còn nguyên sau khi tải lại trang.
7. Người dùng bấm `kudos-copy-link` — URL được chép vào clipboard, `toast` "Link copied — ready to share!" hiện ra.
8. Người dùng nhìn sang R6, thấy 5 dòng `sidebar-stat` và `gift-leaderboard` của chính mình (hoặc của Sunner mẫu nếu đang ẩn danh).
9. Người dùng bấm một trong bốn CTA điều hướng (soạn Kudos, Mở Secret Box, Xem chi tiết, avatar/tên Sunner) — trình duyệt điều hướng sang route thật, hiển thị `ComingSoon`.

## UI States

| State | Trigger | Visual Behavior | User Action Available | Source |
|-------|---------|----------------|-----------------------|--------|
| loading | Server Component đang render lần đầu | Next.js dùng render server-side mặc định, không có skeleton riêng — trang chỉ xuất hiện khi dữ liệu đã sẵn | none | TBD (draft) |
| open (`filter-menu-hashtag` / `filter-menu-department`) | Bấm nút lọc (component `KudosFilterMenu`, dùng chung cho cả hai) | Option căn giữa, hover đổi con trỏ pointer + nền nhạt; khối Phòng ban cuộn trong hộp cao tối đa 348px (6 dòng), không đẩy layout trang | chọn option (đóng dropdown ngay), hoặc chọn lại option đang chọn để bỏ lọc | `app/kudos/_components/kudos-filter-menu.tsx` |
| empty (Highlight/All Kudos) | Bộ lọc hiện tại không khớp kudos nào | "Hiện tại chưa có Kudos nào." | bỏ lọc | TBD (draft) |
| empty (Spotlight) | Tìm kiếm không khớp tên nào | `spotlight-empty` hiện ra, ẩn hết node | xoá từ khoá tìm kiếm | TBD (draft) |
| empty (Gift leaderboard) | Không có dòng quà tặng nào | "Chưa có dữ liệu" | none | TBD (draft) |
| loading-more (All Kudos) | `feed-sentinel` lọt vào khung nhìn, còn dữ liệu để tải | trang tiếp theo của feed nối vào cuối danh sách | none | TBD (draft) |
| liked (kudos-heart) | Đã thả tim thành công | `aria-pressed="true"`, màu đỏ (`#D4271D`), số đếm tăng 1 | gỡ tim | TBD (draft) |
| disabled (kudos-heart) | Chưa đăng nhập hoặc viewer là người gửi | nút `disabled`, không đổi màu khi hover | none | TBD (draft) |
| success (copy link) | Copy link thành công | `toast` "Link copied — ready to share!" hiện rồi tự ẩn | none | TBD (draft) |

## Validation & Error Feedback

| Element | Rule | Feedback | Trigger |
|---------|------|----------|---------|
| `sunner-search` | Tối đa 100 ký tự (`maxlength="100"`) | Không nhập thêm được ký tự thứ 101 | change |
| `spotlight-search` | Tối đa 100 ký tự (`maxlength="100"`) | Không nhập thêm được ký tự thứ 101; không khớp tên nào → `spotlight-empty` | change |
| `kudos-heart` | Chỉ nhận click khi có session VÀ viewer không phải người gửi kudos đó | Nút `disabled` — không có thông báo lỗi riêng, trạng thái nút tự nói lên | submit |
| `filter-hashtag` / `filter-department` | Chỉ một option được chọn tại một thời điểm cho mỗi bộ lọc; chọn lại option đang chọn để bỏ | `aria-selected` đổi tương ứng; không có thông báo lỗi | change |

## Accessibility

| Aspect | Status | Notes |
|--------|--------|-------|
| ARIA roles/labels | [EXPECTED] | `filter-menu-hashtag`/`filter-menu-department` mang `role="listbox"`, các option mang `role="option"` + `aria-selected`; `kudos-heart` mang `aria-pressed`; `highlight-slide` giữa mang `aria-current="true"`, hai bên mang `aria-hidden="true"` |
| Keyboard navigation | [EXPECTED] | Toàn bộ filter, carousel, heart, copy-link, spotlight search, sentinel-triggered feed phải thao tác được bằng bàn phím — chưa có code để xác nhận |
| Focus management | [EXPECTED] | Mở `filter-menu-hashtag`/`filter-menu-department` nên chuyển focus vào option đầu tiên; không có modal/drawer nào cần focus trap trên màn hình này |
| Screen reader compatibility | [EXPECTED] | `kudos-sender`/`kudos-receiver` mang accessible name là tên người đó; `sunner-badge` mang `title` là câu tooltip hoa-thị đầy đủ |
| Error announcement | [EXPECTED] | `toast` sau khi copy link nên mang `role="status"` hoặc `aria-live="polite"` để trình đọc màn hình thông báo được — chưa có code để xác nhận |
