---
status: implemented
authored_by: doc-writer
created: 2026-09-10
---

# SCR-OpenSecretBox — Screen Spec

**Screen**: SCR-OpenSecretBox: Open secret box - chưa mở
**Feature**: F009_OpenSecretBox
**Type**: standalone
**Route**: `/kudos/secret-box`
**Generated**: 2026-09-10

## 1. Overview

**Purpose:** Sunner đã đăng nhập mở một Secret Box và nhận một huy hiệu ngẫu nhiên trong sáu icon sưu tập; khách vãng lai xem được cùng màn ở trạng thái khoá và biết cần đăng nhập. Trước F009 route này là `ComingSoon`.
**Actors:** Sunner có hộp chưa mở, Sunner hết hộp, Khách vãng lai (chưa đăng nhập)
**Entry Conditions:** Không có. Route công khai — `proxy.ts` không canh `/kudos/secret-box` (chỉ canh `/todo`, `/kudos/new`, `/profile`), hợp đồng đã ratify từ F004.
**Exit Conditions:** Bấm `X` → quay lại trang trước (hoặc `/kudos` nếu không có lịch sử). Không có exit nào khác trong màn — không header, không footer dùng chung.

## 2. Screen Layout

### Layout Sketch

Một thẻ (card) đơn, không shell `HomeHeader`/`SiteFooter`, không scrim — đây là một route thật, không phải modal đè lên nội dung khác (DEC-02, phase-04's Key Insights). `<main>` bọc thẻ để giữ khớp `main h1` mà e2e K-21 đã ratify cho route này. Thẻ cố định `max-w-[651.5px]`, `min-h-[822.59px]`, nội dung căn giữa theo chiều dọc bằng `justify-center` — sáu khối con cộng padding/gap chỉ chiếm 804px trong khung 822.6px, khoảng chênh 18.48px là khoảng trống có chủ đích, không phải lỗi đo.

```
┌────────────────────────────────────────┐
│  <main> nền #00101A, flex center        │
│  ┌────────────────────────────────────┐ │
│  │ E.1 Card (relative, 651.5×822.6)    │ │
│  │  ┌──────────────────────────────┐  │ │
│  │  │ E.2 <h1> Tiêu đề       E.3 X  │  │ │
│  │  ├──────────────────────────────┤  │ │
│  │  │ E.4 Hairline trên               │ │
│  │  │ E.5 Dòng hướng dẫn / đăng nhập  │ │
│  │  │ E.6 Khung hộp 557×557 (+badge)  │ │
│  │  │ E.7 Hairline dưới               │ │
│  │  │ E.8 Nhãn + số hộp chưa mở       │ │
│  │  └──────────────────────────────┘  │ │
│  └────────────────────────────────────┘ │
└────────────────────────────────────────┘
```

### Layout Regions

| Region ID | Name | mm id | Position | Scrollable | States |
|-----------|------|-------|----------|------------|--------|
| R1 | `<main>` | — | `flex min-h-svh items-center justify-center`, nền `#00101A` | no | default |
| R2 | Card (`SecretBoxPanel`) | `1466:7676` | `relative mx-auto`, cố định `651.5×822.6` | no | entitled, sparse (0 hộp), anon, opened |

## 3. UI Elements

| ID | Region | mm id | Element | testid | States | Action | Copy key |
|----|--------|-------|---------|--------|--------|--------|----------|
| E.1 | R2 | `1466:7676` | Card nền `#00101A`, bo góc `12.73`, cố định kích thước | `secret-box-panel` | default | — | — |
| E.2 | R2 | `1466:7678` | `<h1>` tiêu đề, 25.46/31.82 bold `#FFEA9E`, canh giữa — `<h1>` duy nhất của trang | — | default | — | `secretBox.title` |
| E.3 | R2 | `1466:7679` | Nút đóng `X` 19×19, `absolute top-[39px] right-[26.5px]` | `secret-box-close` | default | click → đóng | `secretBox.closeLabel` (aria-label) |
| E.4 | R2 | `1466:7680` | Hairline trên, `626×1`, `#2E3940` | — | default | — | — |
| E.5a | R2 | `1466:7683` | Dòng hướng dẫn `Click vào box để mở` | `secret-box-instruction` | chỉ khi `canOpen` | — | `secretBox.instruction` |
| E.5b | R2 | — *(unauthored, cùng slot với E.5a)* | Lời mời đăng nhập + liên kết `/login` | `secret-box-signin` | chỉ khi `!canOpen && showSignIn` | click → `/login` | `secretBox.signInPrompt` + `secretBox.signInCta` |
| E.6 | R2 | `1466:7684` | Khung hộp bấm được, 557×557 vuông (`aspect-square`) | `secret-box-opener` | idle, pending (`aria-busy`), disabled, error | click → gọi `openSecretBox()` | `secretBox.openerLabel` (aria-label + alt ảnh hộp) |
| E.6.badge | trong E.6 | — | Huy hiệu vừa nhận, 50% bề rộng khung, canh giữa, đè lên ảnh hộp | `secret-box-badge` | chỉ sau khi mở thành công (state cục bộ, không phải prop) | — | alt = `rule_items.label` (BR-005) |
| E.7 | R2 | `1466:7688` | Hairline dưới, `626×1`, `#2E3940` | — | default | — | — |
| E.8a | R2 | `1466:7692` | Nhãn `Secretbox chưa mở` | — | default | — | `secretBox.countLabel` |
| E.8b | R2 | `1466:7693` | Số hộp chưa mở, hai chữ số có số 0 đứng đầu (`formatBoxCount`) | `secret-box-count` | default | — | tính từ `unopenedCount` |

**Không render:** node `1466:7685` (glow overlay riêng) — `box-unopened.png` đã là artwork tổng hợp gồm cả ánh sáng; layer lại một lớp glow riêng phủ kín khung ở tỉ lệ Figma thật (evidence `secret-box-entitled-1440.png`, capture đầu). Asset vẫn nằm trên đĩa (`public/images/secret-box/box-glow.png`) để quyết định này kiểm lại được, nhưng không có DOM node nào vẽ nó.

## 4. User Actions

> **Scope:** tương tác trong-màn-hình. Điều hướng rời màn hình xem `## 8. Navigation`.

### Available Actions

| Action | Element | Trigger | Condition | Result on this screen | Source |
|--------|---------|---------|-----------|------------------------|--------|
| Mở hộp | E.6 | click | `canOpen === true` và `status !== 'pending'` | `status → pending` (nút khoá cú bấm thứ hai) → thành công: hiện huy hiệu, đếm giảm 1; thất bại: hiện `secretBox.errorGeneric` | `_components/secret-box-opener.tsx` |
| Đóng bằng nút X | E.3 | click | — | Rời màn hình (xem § 8) | `_components/secret-box-dismiss.tsx` |
| Đăng nhập (khách vãng lai) | E.5b | click | `!canOpen && showSignIn` | Điều hướng `/login` | `_components/secret-box-panel.tsx` |

### Happy Path

1. Sunner có hộp mở `/kudos/secret-box` → 2. Server Component đọc `unopenedCount` thật, render tiêu đề + dòng hướng dẫn + khung hộp + đếm `05` → 3. Bấm khung hộp → nút chuyển `pending`, gọi Server Action → 4. Server trả huy hiệu, đếm giảm còn `04`, khung hộp hiện thêm huy hiệu đè lên ảnh hộp → 5. Bấm `X` quay lại `/kudos`.

### Branches

| Decision point | Condition | Outcome on this screen | Source |
|----------------|-----------|------------------------|--------|
| Bước 2 | Chưa đăng nhập | Đếm `00`, dòng hướng dẫn ẩn, thay bằng lời mời đăng nhập, khung hộp `disabled` | `page.tsx` (`showSignIn = !viewer.isAuthenticated`) |
| Bước 2 | Đã đăng nhập, chưa có dòng `sunners` | Đếm `00`, khung hộp `disabled`, **không** hiện lời mời đăng nhập (đã đăng nhập rồi, mời đăng nhập là nói dối) | `page.tsx` docblock |
| Bước 2 | Đã đăng nhập, `unopenedCount = 0` | Đếm `00`, dòng hướng dẫn ẩn, khung hộp `disabled`, không lời mời nào | `secret-box-panel.tsx` (nhánh `canOpen ? … : showSignIn ? … : null`) |
| Bước 3 | Hai tab cùng bấm gần như đồng thời | Tab thắng nhận huy hiệu; tab thua nhận `no-boxes` từ RPC (`errcode P0002`), hiện `errorGeneric`, đếm không đổi | `technical-spec.md § 3.2` bước 3 (điều kiện `> 0` trong UPDATE) |
| Bước 3 | RPC trả lỗi khác (mạng, bảng tỷ lệ rỗng) | `reason: 'failed'`, hiện `errorGeneric`, đếm không đổi | `open-secret-box.ts` |

## 5. UI States

| State | Trigger | Visual Behavior | User Action Available | Source |
|-------|---------|----------------|-----------------------|--------|
| entitled | Đã đăng nhập, `unopenedCount > 0` | Dòng hướng dẫn hiện, khung hộp bấm được, đếm thật (ví dụ `05`) | Mở hộp, Đóng | `secret-box-entitled-1440.png` |
| sparse | Đã đăng nhập, `unopenedCount = 0` | Dòng hướng dẫn ẩn, khung hộp `disabled`, đếm `00` | Đóng | `secret-box-panel.tsx` |
| anon | Chưa đăng nhập | Đếm `00`, khung hộp `disabled`, lời mời đăng nhập hiện | Đăng nhập, Đóng | `secret-box-anon-1440.png` |
| opened | Vừa mở thành công (state cục bộ) | Huy hiệu đè lên ảnh hộp, đếm giảm 1 | Đóng (khung hộp có thể mở tiếp nếu còn hộp) | `secret-box-opened-1440.png` |
| pending | Đang chờ Server Action trả lời | `aria-busy="true"`, `disabled` thật, không nhận cú bấm thứ hai | Chờ | `secret-box-opener.tsx` (FR-203) |
| error | RPC trả `ok: false` | Dòng `role="alert"` hiện `errorGeneric` dưới khung hộp, đếm giữ nguyên | Bấm lại (nếu còn hộp), Đóng | `secret-box-opener.tsx` |

Không có state `loading` toàn trang: trang là Server Component, HTML chỉ xuất hiện khi số hộp đã đọc xong.

## 6. Validation & Feedback

Không có trường nhập liệu trên màn hình này. Phản hồi duy nhất là kết quả của hành động "mở hộp": thành công hiện huy hiệu, thất bại hiện `secretBox.errorGeneric` (một chuỗi chung, không phân biệt lý do thất bại trên giao diện — `reason` chỉ dùng nội bộ).

## 7. Conditional UI

| Condition | Type | Element(s) | Visible when | Hidden when | Notes |
|-----------|------|------------|--------------|-------------|-------|
| Dòng hướng dẫn | data | E.5a | `canOpen === true` | `canOpen === false` | FR-102 |
| Lời mời đăng nhập | data | E.5b | `canOpen === false && showSignIn === true` | mọi trường hợp khác | Dùng chung slot với E.5a — hai mục loại trừ nhau |
| Khung hộp bấm được | data | E.6 | `canOpen === true && status !== 'pending'` | hết hộp, chưa đăng nhập, chưa có dòng `sunners`, hoặc đang chờ | FR-202 |
| Huy hiệu trong khung | client state | E.6.badge | sau một lần mở thành công trong phiên hiện tại (state cục bộ, không phải prop) | trước khi mở, hoặc sau khi rời/vào lại trang | `secret-box-opener.tsx` — refresh từ `revalidatePath` không xoá badge vì badge không nằm trong prop |
| Cảnh báo lỗi | client state | dòng `role="alert"` | `status === 'error'` | mọi trạng thái khác | Không đè lên hairline/đếm — overlay tuyệt đối ở đáy khung hộp |

## 8. Navigation

### Entry Points

| From | Trigger there | Condition | Source |
|------|----------------|-----------|--------|
| Sidebar Kudos Live Board | Bấm nút `Mở Secret Box` | — | `app/kudos/_components/kudos-sidebar.tsx` |
| Card thống kê Profile (của chính mình) | Bấm nút `Mở Secret Box` | Chỉ trên hồ sơ của chính mình — hồ sơ người khác không hiện nút này | `app/profile/_components/profile-stats-card.tsx` |
| URL trực tiếp / deep link | Mở `/kudos/secret-box` | — | route công khai |

### Exits

| Action | Element | Condition | Destination | Result | Source |
|--------|---------|-----------|-------------|--------|--------|
| `X` | E.3 | có lịch sử để quay lại | trang trước đó | `router.back()` | `secret-box-dismiss.tsx` |
| `X` | E.3 | không có lịch sử (deep link, tab mới) | `/kudos` | `router.push("/kudos")` | `secret-box-dismiss.tsx` |

## 9. Accessibility

| Aspect | Status | Notes |
|--------|--------|-------|
| ARIA roles/labels | [VERIFIED] | Nút đóng mang `aria-label` = `secretBox.closeLabel`; khung hộp mang `aria-label` = `secretBox.openerLabel` và `aria-busy` theo `status === 'pending'`; huy hiệu vừa nhận dùng `alt` = `rule_items.label` thật (không phải nhãn kỹ thuật `badgeAltPrefix`) |
| Keyboard navigation | [VERIFIED] | Cả hai control (`button`) tự nhiên vào tab order; không có listener `Escape` tuỳ chỉnh — route này không phải overlay (DEC-02) |
| Focus management | [VERIFIED] | Không focus trap — nhất quán với quyết định của `/standards` (F007): route thật, không phải modal đè lên trang khác |
| Screen reader compatibility | [VERIFIED] | Cảnh báo lỗi mang `role="alert"` để trình đọc màn hình công bố ngay khi xuất hiện |
| Error announcement | [VERIFIED] | `role="alert"` trên dòng lỗi; nội dung là `secretBox.errorGeneric`, không lộ chi tiết lỗi Postgres |

## 10. Responsive Behavior

| Breakpoint | Behavior | Source |
|------------|----------|--------|
| ≥ 651.5px | Card đúng `651.5×822.6`, canh giữa viewport | `secret-box-entitled-1440.png` |
| < 651.5px | Card giữ `max-w-[651.5px]` cố định, không co theo viewport — xuất hiện scrollbar ngang; khung hộp bên trong vẫn co theo `aspect-square` để không tràn card | `secret-box-entitled-390.png`, đo tại `390×844` |

Frame chỉ đo được ở một bề ngang (`1440×1024`); hành vi dưới `651.5px` là một chủ đích ghi trong plan (DEC-03: card có bề rộng tối đa, nội dung bên trong co theo), không phải suy diễn.
