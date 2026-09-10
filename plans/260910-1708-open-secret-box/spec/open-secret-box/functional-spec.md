---
status: draft
authored_by: takumi
created: 2026-09-10
lang: vi
fcode: F009
---

**Priority**: P1
**Type**: ui+api

## 1. Overview

**Problem:** Sidebar của Kudos Live Board và thẻ thống kê trong Profile đều đã in ra "Số Secret Box chưa mở", và nút `Mở Secret Box` đã trỏ sang `/kudos/secret-box` — nhưng route đó vẫn là `ComingSoon`, còn nút bên Profile thì `disabled`. Người dùng thấy mình có hộp nhưng không mở được cái nào.
**Solution:** Dựng màn `Open secret box - chưa mở` (MoMorph `J3-4YFIpMM`) tại `/kudos/secret-box`: tiêu đề, dòng hướng dẫn, khung hộp quà bấm được, và bộ đếm hộp chưa mở lấy từ database. Bấm vào hộp gọi một hàm Postgres duy nhất `open_secret_box()`: hàm này rút ngẫu nhiên một huy hiệu theo tỷ lệ đã định, trừ một hộp chưa mở, cộng một hộp đã mở, và ghi lại lần mở đó.
**Scope:** Route `/kudos/secret-box` thay `ComingSoon`; migration mới (bảng `secret_box_openings`, bảng tỷ lệ `secret_box_badge_odds`, hàm `open_secret_box()`); Server Action gọi hàm; khối copy `secretBox` trong `Dictionary` (vi + en); mở khoá nút Secret Box trên profile của chính mình; bộ E2E RED-first `e2e/secret-box.spec.ts` cùng setup cấp hộp cho user test.
**Non-Scope:** Không dựng màn *đã mở* / *action bấm mở* (MoMorph còn `in_progress`, chưa có spec). Không định nghĩa cách **kiếm** được hộp — đó là commission riêng. Không đổi `proxy.ts`, không đụng bảng `rule_items` hay `gift_awards`.

**Actors**

| Actor | Description | Primary goal |
|-------|--------------|---------------|
| Sunner có hộp chưa mở | Đã đăng nhập, có dòng `sunners`, `secret_box_unopened_count > 0` | Mở hộp và nhận một huy hiệu ngẫu nhiên |
| Sunner hết hộp | Đã đăng nhập, `secret_box_unopened_count = 0` | Thấy rõ mình không còn hộp nào, không bấm nhầm |
| Khách vãng lai | Chưa đăng nhập — route công khai | Xem được màn, hiểu là cần đăng nhập mới mở được |

## 2. Functional Capabilities

| ID | Capability | What the user can do | User Stories | Requirements | Business Rules | Screens |
|----|------------|------------------------|-----------------|---------------|-------------------|---------|
| CAP-01 | Xem màn Secret Box | Mở `/kudos/secret-box`, thấy tiêu đề, hộp quà và số hộp chưa mở của mình | US001 | FR-001, FR-101, FR-102, FR-103, FR-104 | BR-001, BR-005 | SCR009_OpenSecretBox |
| CAP-02 | Mở một hộp | Bấm vào khung hộp để nhận một huy hiệu ngẫu nhiên | US002 | FR-201, FR-202, FR-203 | BR-002, BR-003, BR-004 | SCR009_OpenSecretBox |
| CAP-03 | Đóng màn | Bấm `X` để quay về nơi vừa đến | US003 | FR-301 | BR-006 | SCR009_OpenSecretBox |

## 3. User Stories

- **US001** — Là một Sunner, tôi muốn thấy còn bao nhiêu Secret Box chưa mở, để biết mình có gì để mở.
- **US002** — Là một Sunner có hộp, tôi muốn bấm vào hộp và nhận một huy hiệu, để góp vào bộ sưu tập của mình.
- **US003** — Là một Sunner, tôi muốn đóng màn Secret Box và quay lại chỗ cũ, để không bị kẹt.

## 4. Requirements

### Hiển thị
- **FR-001** — Route `/kudos/secret-box` trả về `200` cho mọi khách, kể cả chưa đăng nhập.
- **FR-101** — Tiêu đề `KHÁM PHÁ SECRET BOX CỦA BẠN` là `<h1>` duy nhất của trang (mm:1466:7678).
- **FR-102** — Dòng `Click vào box để mở` chỉ hiện khi số hộp chưa mở `> 0` (mm:1466:7683).
- **FR-103** — Khung hộp quà (mm:1466:7684) hiện ảnh hộp chưa mở; sau khi mở thành công, hiện thêm huy hiệu vừa nhận.
- **FR-104** — Chân màn in nhãn `Secretbox chưa mở` và con số, định dạng hai chữ số có số 0 đứng đầu (`05`, `00`) đúng như thiết kế (mm:1466:7692, mm:1466:7693).
- **FR-105** — Chưa đăng nhập: bộ đếm là `00`, hộp không bấm được, và có một liên kết đăng nhập.

### Hành vi
- **FR-201** — Bấm vào khung hộp khi còn hộp: nhận đúng một huy hiệu, số chưa mở giảm 1, số đã mở tăng 1.
- **FR-202** — Khung hộp bị vô hiệu hoá khi số hộp chưa mở bằng 0, khi không có phiên đăng nhập, hoặc khi phiên đó chưa có dòng `sunners`.
- **FR-203** — Trong lúc chờ máy chủ trả lời, khung hộp không nhận thêm cú bấm thứ hai.
- **FR-301** — Nút `X` góc trên phải đóng màn, quay về trang trước; không có lịch sử thì về `/kudos`.

### Phi chức năng
- **FR-601** — Việc rút huy hiệu và trừ hộp chỉ xảy ra trên máy chủ; không giá trị nào từ trình duyệt tham gia vào quyết định đó.
- **FR-602** — Toàn bộ thay đổi của một lần mở nằm trong một transaction: không có trạng thái nửa vời (trừ hộp mà không có huy hiệu, hoặc ngược lại).

## 5. Business Rules

- **BR-001** — Số hộp chưa mở luôn đọc từ `sunners.secret_box_unopened_count` của chính người đang đăng nhập; không cache, không nhận từ client.
- **BR-002** — Mỗi lần mở nhận **đúng một** huy hiệu.
- **BR-003** — Tỷ lệ rút: Stay Gold 30, Flow to Horizon 25, Touch of Light 20, Beyond the Boundary 10, Revival 10, Root Further 5 (trọng số tương đối).
- **BR-004** — Không còn hộp thì không mở được; máy chủ từ chối, không phải chỉ giao diện làm mờ nút.
- **BR-005** — Sáu huy hiệu lấy từ `rule_items` (`kind = 'collectible_icon'`) — cùng nguồn với màn Thể lệ, không tạo danh mục thứ hai.
- **BR-006** — Màn này không phán xét quyền truy cập ở tầng route; `proxy.ts` giữ nguyên.

## 6. State Model

- **SM-001** — Khung hộp có ba trạng thái: `sẵn sàng` (còn hộp, có phiên) → `đang mở` (đã bấm, chờ máy chủ) → `sẵn sàng` hoặc `hết hộp`. Trạng thái `khoá` (chưa đăng nhập / chưa có dòng `sunners`) nằm ngoài chuỗi đó và không chuyển đi đâu.

## 7. Screens

| ID | Screen | Route | MoMorph |
|----|--------|-------|---------|
| SCR009_OpenSecretBox | Open secret box - chưa mở | `/kudos/secret-box` | `J3-4YFIpMM` (`1466:7676`) |

## 8. Open Questions

Không còn — xem `clarifications.md`.
