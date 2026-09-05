---
status: draft
authored_by: takumi
created: 2026-09-05
---

# SCR-homepage — Screen Spec

**Screen**: SCR-homepage *(draft — mã chính thức cấp khi promote)*: Homepage SAA 2025
**Feature**: F000_HomepageSaa
**Type**: atomic
**Route**: `/`
**Generated**: 2026-09-05

## 1. Overview

**Purpose:** Trang chủ công khai SAA 2025 — khách truy cập hiểu chủ đề "Root Further", biết hệ thống giải thưởng, và tìm đường vào Award Information / Sun* Kudos; người dùng đã đăng nhập còn xem thông báo và quản lý tài khoản ngay từ header.
**Actors:** Khách truy cập, Người dùng đã đăng nhập
**Entry Conditions:** Không yêu cầu gì — route công khai, mọi khách đều vào được trực tiếp.
**Exit Conditions:** Khách rời trang qua một trong các liên kết điều hướng (nav, CTA, thẻ giải thưởng, widget, footer, hoặc menu tài khoản/Sign out với người đã đăng nhập); không có trạng thái "hoàn tất" bắt buộc — đây là trang duyệt tự do.

## 2. Screen Layout

### Layout Sketch

Một trang cuộn dọc liên tục, không có tab/wizard. R1 header cố định trên cùng (sticky), các khối còn lại xếp dọc trong luồng cuộn chính, R7 nút widget nổi (fixed) đè lên góc phải màn hình xuyên suốt quá trình cuộn. *(design/homepage-saa.png, 1512×4480)*

```
┌──────────────────────────────────────────────────┐
│  R1: Header (sticky-top)                          │
├──────────────────────────────────────────────────┤
│  R2: Hero — keyvisual + Coming soon + countdown   │
│      + event info + 2 CTA (static)                │
├──────────────────────────────────────────────────┤
│  R3: Root Further content block (static)          │
├──────────────────────────────────────────────────┤
│  R4: Awards grid — 6 cards (static, scrollable    │
│      with page)                            - - -  │
│                                             ┆ R7 ┆ │ ← floating widget (fixed, overlays R4-R6)
├──────────────────────────────────────────────────┤
│  R5: Sun* Kudos promo block (static)              │
├──────────────────────────────────────────────────┤
│  R6: Footer (static)                              │
└──────────────────────────────────────────────────┘
```

### Layout Regions

| Region ID | Name | Position | Scrollable | Key Components |
|-----------|------|----------|------------|----------------|
| R1 | Header | sticky-top | no | `TBD (draft)` |
| R2 | Hero | static | yes (part of page scroll) | `TBD (draft)` |
| R3 | Root Further content | static | yes | `TBD (draft)` |
| R4 | Awards grid | static | yes | `TBD (draft)` |
| R5 | Sun* Kudos promo | static | yes | `TBD (draft)` |
| R6 | Footer | static | yes | `TBD (draft)` |
| R7 | Floating widget button | fixed | no | `TBD (draft)` |

## 3. UI Elements

| ID | Element | Type | Required | Default | Visibility | Action | Source | Format | Empty Behavior | Cross-ref |
|----|---------|------|----------|---------|------------|--------|--------|--------|-----------------|-----------|
| E01 | Logo | image | — | visible | Always | — | static | raw | — | N/A |
| E02 | Nav — About SAA 2025 | link | — | selected | Always | Cuộn lên đầu (đã ở trang này) | static | raw | — | N/A |
| E03 | Nav — Award Information | link | — | not selected | Always | Điều hướng `/awards-information` | static | raw | — | N/A |
| E04 | Nav — Sun* Kudos | link | — | not selected | Always | Điều hướng `/kudos` | static | raw | — | N/A |
| E05 | Notification bell | button | — | closed | Conditional (đã đăng nhập) | Toggle panel E06 | store state | raw | hidden khi chưa đăng nhập | N/A |
| E06 | Notification panel | message | — | closed | Conditional (E05 đang mở) | — | static | raw | luôn hiện "Không có thông báo mới" | N/A |
| E07 | Account icon | button | — | closed | Conditional (đã đăng nhập) | Toggle menu E08-E10 | store state | raw | hidden khi chưa đăng nhập | N/A |
| E08 | Account menu — Profile | link | — | — | Conditional (E07 đang mở) | Điều hướng `/profile` | static | raw | — | N/A |
| E09 | Account menu — Sign out | button | — | — | Conditional (E07 đang mở) | Đăng xuất, điều hướng `/login` | static | raw | — | N/A |
| E10 | Account menu — Admin Dashboard | link | — | — | Conditional (E07 đang mở AND role admin) | Điều hướng `/profile` (placeholder) | computed (role) | raw | ẩn hoàn toàn khi không phải admin | N/A |
| E11 | Language selector | button + panel | — | VN | Always | Đổi ngôn ngữ (tái dùng F001_Login) | store state | raw | — | binding: `cookie NEXT_LOCALE` |
| E12 | Hero keyvisual "ROOT FURTHER" | image | — | visible | Always | — | static | raw | — | N/A |
| E13 | "Coming soon" label | display field | — | visible | Conditional (chưa qua thời điểm sự kiện) | — | computed | raw | hidden khi đã qua sự kiện | N/A |
| E14 | Countdown — Days | display field | — | "00" | Always | — | computed | raw (2 chữ số, pad 0) | giữ "00" khi đã qua sự kiện | N/A |
| E15 | Countdown — Hours | display field | — | "00" | Always | — | computed | raw (2 chữ số, pad 0) | giữ "00" khi đã qua sự kiện | N/A |
| E16 | Countdown — Minutes | display field | — | "00" | Always | — | computed | raw (2 chữ số, pad 0) | giữ "00" khi đã qua sự kiện | N/A |
| E17 | Event info block | display field | — | visible | Always | — | static | raw | — | N/A |
| E18 | CTA "ABOUT AWARDS" | button | — | enabled | Always | Điều hướng `/awards-information` | static | — | — | N/A |
| E19 | CTA "ABOUT KUDOS" | button | — | enabled | Always | Điều hướng `/kudos` | static | — | — | N/A |
| E20 | Root Further content block | display field | — | visible | Always | — | static | raw | — | N/A |
| E21 | Awards section heading | region label | — | visible | Always | — | static | raw | — | N/A |
| E22 | Award card *(nhóm lặp 6 lần: Top Talent, Top Project, Top Project Leader, Best Manager, Signature 2025 - Creator, MVP)* | link | — | visible | Always | Bấm bất kỳ đâu trên thẻ → điều hướng `/awards-information#<slug>` | static | truncate 2 dòng + ellipsis | — | N/A |
| E23 | Sun* Kudos promo block | display field | — | visible | Always | "Chi tiết" điều hướng `/kudos` | static | raw | — | N/A |
| E24 | Floating widget button | link *(nhóm 2 icon)* | — | visible | Always | Icon "viết kudos" → `/kudos`; icon "thể lệ SAA" → `/standards` | static | raw | — | N/A |
| E25 | Footer links + copyright | link | — | visible | Always | Điều hướng theo từng link (About SAA 2025, Award Information, Sun* Kudos, Tiêu chuẩn chung) | static | raw | — | N/A |

## 4. User Actions

> **Scope:** within-screen interactions only. Điều hướng ra ngoài màn hình xem ở `## 8. Navigation`.

### Available Actions

| Action | Element | Trigger | Condition | Result on this screen | Source |
|--------|---------|---------|-----------|------------------------|--------|
| Cuộn lên đầu | E02 | click | mục đang được chọn | Cuộn mượt lên đầu trang | `TBD (draft)` |
| Mở/đóng panel thông báo | E05 | click | đã đăng nhập | Toggle hiện/ẩn E06 | `TBD (draft)` |
| Mở/đóng menu tài khoản | E07 | click | đã đăng nhập | Toggle hiện/ẩn E08-E10 | `TBD (draft)` |
| Đổi ngôn ngữ | E11 | click | — | Toàn bộ nội dung chuyển ngôn ngữ đã chọn *(tái dùng F001_Login)* | `TBD (draft)` |

### Happy Path

1. Khách truy cập `/`, thấy header (R1) và toàn bộ nội dung trang chủ (R2-R6) theo ngôn ngữ mặc định VN.
2. Khách cuộn qua hero (đếm ngược đang tick), nội dung Root Further, lưới giải thưởng, khối Kudos, tới footer.
3. Khách bấm một liên kết (nav/CTA/thẻ/widget/footer) — rời màn hình này sang route đích tương ứng.

### Branches

N/A — display/navigation screen; các điều kiện hiện/ẩn (chuông, menu, Admin Dashboard, "Coming soon") đã liệt kê ở `## 7. Conditional UI`, không phải rẽ nhánh trong một luồng hành động.

### Interaction Notes

- **Bấm mục nav "About SAA 2025" khi đang ở trang chủ cuộn lên đầu thay vì điều hướng lại** — source: `TBD (draft)`
- **Countdown tự tick mỗi giây, không cần tương tác người dùng** — source: `TBD (draft)`
- **Bấm ngoài panel/menu đang mở (chuông, tài khoản, ngôn ngữ) đóng lại panel đó** *(tái dùng hành vi outside-click của `LanguageSelector` ở F001_Login)* — source: `TBD (draft)`

## 5. UI States

| State | Trigger | Visual Behavior | User Action Available | Source |
|-------|---------|----------------|-----------------------|--------|
| loading | N/A — không có async op nào khi mount (phiên đã có sẵn từ cookie/middleware, nội dung tĩnh) | — | — | `TBD (draft)` |
| empty (panel thông báo) | Bấm chuông thông báo | Hiện "Không có thông báo mới" | Bấm ra ngoài hoặc bấm lại chuông để đóng | `TBD (draft)` |
| empty (countdown đã qua sự kiện) | `now ≥` thời điểm sự kiện | Giữ `00` ở cả 3 ô, ẩn "Coming soon" | — | `TBD (draft)` |
| error | N/A — không có async op nào có thể lỗi ở màn hình này | — | — | `TBD (draft)` |
| saving | N/A — không có form submit/mutation ở màn hình này | — | — | `TBD (draft)` |
| success | N/A — không có mutation nên không có trạng thái thành công riêng | — | — | `TBD (draft)` |
| custom — cấu hình đếm ngược không hợp lệ | `NEXT_PUBLIC_EVENT_START_AT` thiếu/sai định dạng | Hiện `00/00/00`, ẩn "Coming soon", ghi cảnh báo console (dev only) | — | `TBD (draft)` |

## 6. Validation & Feedback

N/A — no validation rules or submit-side error feedback detected. *(Không có form input nào ở màn hình này — thuần hiển thị + điều hướng.)*

## 7. Conditional UI

| Condition | Type | Element(s) | Visible when | Hidden when | Notes |
|-----------|------|------------|--------------|-------------|-------|
| Chuông thông báo và biểu tượng tài khoản chỉ hiện với người đã đăng nhập | auth | E05, E07 | có phiên đăng nhập hợp lệ | chưa đăng nhập | Ẩn hoàn toàn khỏi DOM, không phải chỉ ẩn CSS |
| Mục Admin Dashboard chỉ hiện trong menu tài khoản với role admin | auth | E10 | `session != null` AND `role === "admin"` | đã đăng nhập nhưng không phải admin, hoặc chưa đăng nhập | Gating chỉ ở UI — trang đích thật (khi được xây) phải tự kiểm tra quyền, không dựa vào việc ẩn mục menu này |
| "Coming soon" và bộ đếm hoạt động chỉ hiện trước thời điểm sự kiện | configuration | E13, E14-E16 | `now <` `NEXT_PUBLIC_EVENT_START_AT` | đã qua thời điểm sự kiện | Bộ đếm vẫn hiện `00` khi ẩn nhãn, không biến mất hoàn toàn |

## 8. Navigation

> `## 8. Navigation` is the per-screen projection of `screen-flow.md § Screen Access Paths` — greenfield draft has no `screen-flow.md` yet; every row below is intent-derived and `Source` is `TBD (draft)` until reconciled at promote.

### Entry Points

| From | Trigger there | Condition | Source |
|------|----------------|-----------|--------|
| external \| direct URL | truy cập `/` trực tiếp hoặc bookmark | — | `TBD (draft)` |
| SCR *(Award Information placeholder)* | bấm logo hoặc mục nav "About SAA 2025" | — | `TBD (draft)` |
| SCR *(Sun* Kudos placeholder)* | bấm logo hoặc mục nav "About SAA 2025" | — | `TBD (draft)` |
| SCR *(Tiêu chuẩn chung placeholder)* | bấm logo hoặc mục nav "About SAA 2025" | — | `TBD (draft)` |

### Exits

| Action | Element | Condition | Destination | Result | Source |
|--------|---------|-----------|-------------|--------|--------|
| Xem Award Information | E03, E18 | — | *(Award Information placeholder)* | redirect | `TBD (draft)` |
| Xem Sun* Kudos | E04, E19, E23, E24 (icon viết kudos) | — | *(Sun* Kudos placeholder)* | redirect | `TBD (draft)` |
| Xem Tiêu chuẩn chung | E24 (icon thể lệ SAA), footer link | — | *(Tiêu chuẩn chung placeholder)* | redirect | `TBD (draft)` |
| Xem chi tiết một hạng mục giải thưởng | E22 | — | *(Award Information placeholder)*`#<slug>` | redirect | `TBD (draft)` |
| Xem Profile / Admin Dashboard | E08, E10 | E10 chỉ khi role admin | *(Profile placeholder)* | redirect | `TBD (draft)` |
| Đăng xuất | E09 | đã đăng nhập | `/login` | redirect *(tái dùng F001_Login sign-out)* | `TBD (draft)` |

## 9. Accessibility

| Aspect | Status | Notes |
|--------|--------|-------|
| ARIA roles/labels | [EXPECTED] | Chuông/menu tài khoản/ngôn ngữ dùng `aria-haspopup`/`aria-expanded`/`aria-controls`/`role="listbox"` như `LanguageSelector` hiện có ở F001_Login |
| Keyboard navigation | [EXPECTED] | ArrowDown/ArrowUp/Home/End/Enter/Space/Escape cho cả 3 panel (thông báo, tài khoản, ngôn ngữ) — cùng mẫu hình `LanguageSelector` đã triển khai |
| Focus management | [EXPECTED] | Mở panel chuyển focus vào phần tử đầu tiên; Escape trả focus về trigger — cùng mẫu hình `LanguageSelector` |
| Screen reader compatibility | [EXPECTED] | Tên truy cập (`aria-label`) của mỗi trigger phải phản ánh đúng nhãn hiển thị (Label in Name — WCAG 2.5.3), tương tự cách `LanguageSelector` xây `aria-label` từ nhãn hiện tại |
| Error announcement | [EXPECTED] | N/A — màn hình không có validation/error message cần công bố qua `aria-live` |

## 10. Responsive Behavior

| Breakpoint | Region / Element | Behavior | Source |
|------------|-------------------|----------|--------|
| ≥1024px (desktop) | R4 / E22 (lưới thẻ giải thưởng) | 3 cột | clarifications.md — "Follow the test cases" (test ID-16) |
| <1024px (tablet + mobile) | R4 / E22 (lưới thẻ giải thưởng) | 2 cột | clarifications.md — "Follow the test cases" (test ID-16), ghi đè spec item C2 (English row nói 1 cột mobile) |
