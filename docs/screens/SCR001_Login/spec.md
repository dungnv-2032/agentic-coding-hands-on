---
status: implemented
fcode: F001
authored_by: takumi
created: 2026-09-04
---

# SCR001_Login — Screen Spec

**Screen**: SCR001_Login: Login
**Feature**: F001_Login
**Type**: atomic
**Route**: `/login`
**Generated**: 2026-09-04

## 1. Overview

**Purpose:** Màn hình duy nhất để vào ứng dụng SAA 2025 — khách chưa đăng nhập gặp màn hình này để xác thực bằng Google.
**Actors:** Khách truy cập chưa đăng nhập
**Entry Conditions:** Truy cập trực tiếp `/login`, hoặc bị hệ thống điều hướng về đây khi chưa đăng nhập mà cố vào `/todo`, hoặc quay lại đây sau khi Google OAuth thất bại/huỷ.
**Exit Conditions:** Xác thực Google thành công → rời màn hình này tới `/todo`. Người đã đăng nhập vào lại URL này bị điều hướng thẳng đi, không thấy màn hình.

## 2. Screen Layout

### Layout Sketch

Bố cục toàn màn hình (canvas thiết kế 1440×1024): header cố định trên cùng, một vùng nội dung chính choán toàn bộ phần còn lại với ảnh nền hero phủ full-bleed và khối giới thiệu + nút đăng nhập nằm bên trái, footer cố định dưới cùng. Không cuộn — mọi thứ vừa trong một viewport (design node `662:14387`).

```
┌──────────────────────────────────────────────────────┐
│  R1: Header (fixed-top) — logo trái · ngôn ngữ phải  │
├──────────────────────────────────────────────────────┤
│  R2: Hero (static, full-bleed background)             │
│  ┌──────────────────┐                                 │
│  │ ROOT FURTHER      │        (ảnh nền trừu tượng      │
│  │ subtitle/tagline  │         phủ toàn bộ phía sau)   │
│  │ [LOGIN With G]    │                                 │
│  └──────────────────┘                                 │
├──────────────────────────────────────────────────────┤
│  R3: Footer (fixed-bottom) — bản quyền, căn giữa       │
└──────────────────────────────────────────────────────┘
```

### Layout Regions

| Region ID | Name | Position | Scrollable | Key Components |
|-----------|------|----------|------------|----------------|
| R1 | Header | fixed-top | no | Logo, LanguageSelector — `TBD (draft)` |
| R2 | Hero content | static | no | HeroBackground, RootFurtherWordmark, IntroText, GoogleSignInButton — `TBD (draft)` |
| R3 | Footer | fixed-bottom | no | CopyrightText — `TBD (draft)` |

## 3. UI Elements

| ID | Element | Type | Required | Default | Visibility | Action | Source | Format | Empty Behavior | Cross-ref |
|----|---------|------|----------|---------|------------|--------|--------|--------|-----------------|-----------|
| E01 | Logo SAA 2025 | image | — | static | Always | — *(không tương tác — xác nhận bởi test case)* | static | raw | — | R1 |
| E02 | Bộ chọn ngôn ngữ | button (dropdown) | no | `vi` | Always | Mở dropdown chọn VN/EN (yêu cầu E02) | store state (cookie `NEXT_LOCALE`) | raw | — | binding: `NEXT_LOCALE` |
| E03 | Ảnh nền hero | image | — | static | Always | — | static | raw | — | *(asset chưa export — xem RISK-01 functional-spec.md)* |
| E04 | Wordmark "ROOT FURTHER" | image | — | static | Always | — | static | raw | — | N/A |
| E05 | Dòng giới thiệu "Bắt đầu hành trình của bạn cùng SAA 2025." | display field | — | static | Always | — | static | raw | — | N/A |
| E06 | Dòng "Đăng nhập để khám phá!" | display field | — | static | Always | — | static | raw | — | N/A |
| E07 | Nút "LOGIN With Google" | button | — | Enabled | Always | Khởi tạo luồng Google OAuth (yêu cầu không có input) | — | — | — | N/A |
| E08 | Footer bản quyền "Bản quyền thuộc về Sun* © 2025" | display field | — | static | Always | — *(không tương tác — xác nhận bởi test case)* | static | raw | — | N/A |

**Ghi chú asset:** `IconFlagEn` (cờ Anh trong E02) không có node MoMorph tương ứng — thiết kế trước nay chỉ vẽ trạng thái mặc định VN. Cờ VN (`IconFlagVn`) có node MoMorph; cờ EN được vẽ tay để khớp hình học với cờ VN — xem comment trong `app/login/_components/icons.tsx`.

## 4. User Actions

### Available Actions

| Action | Element | Trigger | Condition | Result on this screen | Source |
|--------|---------|---------|-----------|------------------------|--------|
| Đăng nhập Google | E07 | click | — | Nút chuyển sang disabled + hiện loader; sau đó rời màn hình (chuyển hướng ra ngoài) | `TBD (draft)` |
| Mở/đóng dropdown ngôn ngữ | E02 | click trigger | — | Toggle panel; chevron xoay 180° khi mở | `design 721:4942` |
| Chọn ngôn ngữ | E02 | click / Enter / Space trên mục | panel đang mở | Đổi ngôn ngữ toàn màn hình, panel đóng, focus về trigger | `design 721:4942` |
| Di chuyển trong panel | E02 | ArrowDown / ArrowUp / Home / End | panel đang mở | Focus chạy vòng trong danh sách mục (wrap) | `clarifications.md` |
| Đóng bằng Escape | E02 | Escape | panel đang mở | Panel đóng, locale không đổi, focus về trigger | `clarifications.md` |
| Đóng bằng click ngoài | E02 | click ngoài panel | panel đang mở | Panel đóng, locale không đổi, KHÔNG trả focus về trigger (cố ý — người dùng đã hướng thao tác ra chỗ khác) | `language-selector.tsx` |

### Happy Path

1. Khách vào `/login`, thấy màn hình với ngôn ngữ mặc định VN.
2. Khách bấm "LOGIN With Google" (E07) — nút chuyển sang trạng thái loading/disabled.
3. Khách xác thực ở Google, quay lại thành công, rời màn hình này tới `/todo`.

### Branches

| Decision point | Condition | Outcome on this screen | Source |
|----------------|-----------|------------------------|--------|
| Bước 2-3 | Xác thực Google thất bại hoặc bị huỷ | Quay lại màn hình này, hiện banner lỗi phía trên nút, nút trở lại trạng thái sẵn sàng | `TBD (draft)` |

### Interaction Notes

- **Bấm nút đăng nhập nhiều lần trong lúc đang xử lý không có tác dụng thêm** — nút đã ở trạng thái disabled sau lần bấm đầu tiên — source: `TBD (draft)`.
- **Hover vào nút đăng nhập hiện hiệu ứng shadow/nổi** — source: `TBD (draft)`.
- **Hover vào bộ chọn ngôn ngữ đổi con trỏ thành pointer và làm nổi bật vùng chọn** — source: `TBD (draft)`.

## 5. UI States

| State | Trigger | Visual Behavior | User Action Available | Source |
|-------|---------|----------------|-----------------------|--------|
| idle | tải trang lần đầu, hoặc quay lại sau lỗi | Nút đăng nhập ở trạng thái sẵn sàng, không banner lỗi | Bấm đăng nhập, đổi ngôn ngữ | `TBD (draft)` |
| loading | vừa bấm "LOGIN With Google" | Nút disabled + hiện loader | không | `TBD (draft)` |
| error | quay lại từ Google với lỗi/huỷ | Banner "Đăng nhập không thành công. Vui lòng thử lại." hiện phía trên nút; nút trở lại sẵn sàng | Bấm lại đăng nhập | `TBD (draft)` |
| success (redirect) | xác thực Google thành công | Màn hình này biến mất, người dùng đã ở `/todo` | không (đã rời màn hình) | `TBD (draft)` |

## 6. Validation & Feedback

| Element | Rule | Feedback | Trigger |
|---------|------|----------|---------|
| E07 | Xác thực Google phải thành công để rời màn hình | "Đăng nhập không thành công. Vui lòng thử lại." | server response *(quay lại từ `/auth/callback` với cờ lỗi)* |

## 7. Conditional UI

| Condition | Type | Element(s) | Visible when | Hidden when | Notes |
|-----------|------|------------|--------------|-------------|-------|
| Banner lỗi đăng nhập hiện khi quay lại từ Google có lỗi | hardcoded-id | E07 *(vùng banner ngay phía trên)* | query `error` có mặt trên URL | không có `error` trên URL | `[NEEDS_DOMAIN_CONFIRMATION]` không áp dụng — hành vi đã chốt trong `clarifications.md`; ghi `hardcoded-id` vì điều kiện dựa trên query param, không phải feature-flag |

## 8. Navigation

### Entry Points

| From | Trigger there | Condition | Source |
|------|----------------|-----------|--------|
| external | truy cập URL `/login` trực tiếp | — | `TBD (draft)` |
| SCR-todo *(placeholder)* | route guard chặn truy cập `/todo` | chưa có phiên đăng nhập | `TBD (draft)` |
| external (Google) | quay lại từ màn hình xác thực Google | xác thực thất bại hoặc bị huỷ | `TBD (draft)` |

### Exits

| Action | Element | Condition | Destination | Result | Source |
|--------|---------|-----------|-------------|--------|--------|
| Đăng nhập Google | E07 | — | external (Google OAuth consent) | redirect (toàn trang) | `TBD (draft)` |
| Xác thực Google thành công | — | callback nhận `code` hợp lệ | SCR-todo *(placeholder)* | redirect | `TBD (draft)` |

## 9. Accessibility

| Aspect | Status | Notes |
|--------|--------|-------|
| ARIA roles/labels | [PARTIAL] | Dropdown ngôn ngữ (E02) xác nhận trong code: trigger `aria-haspopup="listbox"` + `aria-expanded` + `aria-controls` + `aria-label` động theo locale hiện tại; panel `role="listbox"` + `aria-label`; mỗi mục `role="option"` + `aria-selected`. Nút đăng nhập Google (E07) vẫn `[EXPECTED]` — chưa có code xác nhận. |
| Keyboard navigation | [PARTIAL] | Dropdown ngôn ngữ (E02) xác nhận trong code: ArrowDown/ArrowUp (vòng), Home/End, Enter/Space chọn, Escape đóng + trả focus về trigger. Nút đăng nhập Google (E07) vẫn `[EXPECTED]`. |
| Focus management | [PARTIAL] | Mở panel: focus vào mục đang chọn. Chọn mục hoặc Escape: trả focus về trigger. Click ra ngoài: đóng panel nhưng KHÔNG trả focus về trigger (cố ý — xem known limitations bên dưới). |
| Screen reader compatibility | [EXPECTED] | Banner lỗi cần được đọc ra ngay khi xuất hiện — chưa có code xác nhận (ngoài phạm vi dropdown ngôn ngữ). |
| Error announcement | [EXPECTED] | Banner lỗi nên dùng `aria-live` để trình đọc màn hình thông báo ngay khi xuất hiện — chưa có code xác nhận (ngoài phạm vi dropdown ngôn ngữ). |

**Known limitations (dropdown ngôn ngữ, xác nhận từ code):**

- Tab ra khỏi panel đang mở KHÔNG tự đóng panel (popup mồ côi) — user quyết định hoãn xử lý ("để lần sau"), xem `clarifications.md`.
- `aria-controls` trên trigger trỏ tới id không tồn tại khi panel đang đóng, vì listbox chỉ render khi panel mở (điều kiện render). Tồn tại từ trước, không phải lỗi mới của thay đổi này.

## 10. Responsive Behavior

N/A — no responsive behavior found in source.
