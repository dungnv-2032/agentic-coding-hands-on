---
status: implemented
authored_by: takumi
created: 2026-09-04
lang: vi
---

**Priority**: P0
**Type**: ui

## 1. Overview

**Problem:** Người tham gia SAA 2025 (Sun* Annual Awards 2025) cần một cách vào ứng dụng nhanh, không phải nhớ thêm mật khẩu riêng cho hệ thống.
**Solution:** Màn hình `/login` chỉ có một lựa chọn đăng nhập — tài khoản Google — qua Supabase Auth (local stack). Xác thực xong, người dùng vào thẳng `/todo`.
**Scope:** Đăng nhập bằng Google (mọi tài khoản Google hợp lệ, không giới hạn domain); gác cổng `/login` và `/todo` theo trạng thái đăng nhập; chọn ngôn ngữ hiển thị VN/EN; đăng xuất.
**Non-Scope:** Không có đăng nhập email/mật khẩu, không có đăng ký tài khoản, không có trang hồ sơ hay trang quản trị. Nội dung to-do thật không thuộc phạm vi — `/todo` chỉ là trang placeholder tối thiểu để chứng minh điều hướng sau đăng nhập và trước đăng xuất.

**Actors**

| Actor | Description | Primary goal |
|-------|--------------|---------------|
| Khách truy cập chưa đăng nhập | Người vào ứng dụng lần đầu, hoặc quay lại sau khi đăng xuất | Đăng nhập bằng Google để vào ứng dụng |
| Người dùng đã đăng nhập | Người đã xác thực Google thành công | Không bị đưa lại màn hình đăng nhập; đăng xuất được khi cần |

## 2. Functional Capabilities

| ID | Capability | What the user can do | User Stories | Requirements | Business Rules | Screens |
|----|------------|------------------------|-----------------|---------------|-------------------|---------|
| CAP-01 | Đăng nhập bằng Google | Bấm một nút để xác thực qua Google và vào ứng dụng | US001 | FR-001, FR-002, FR-201, FR-202, FR-401, FR-402, FR-601 | BR-001, DEC-001, DEC-002, SM-001 | SCR-login |
| CAP-02 | Kiểm soát truy cập theo trạng thái đăng nhập | Được tự động điều hướng đúng màn hình theo việc đã đăng nhập hay chưa | US002 | FR-101, FR-102, FR-602 | BR-002 | — |
| CAP-03 | Chọn ngôn ngữ hiển thị | Đổi giao diện giữa Tiếng Việt và English | US003 | FR-203 | BR-003 | — |
| CAP-04 | Đăng xuất | Kết thúc phiên đăng nhập | US004 | FR-403 | — | — |

## 3. Open Decisions

None — no unresolved domain confirmations.

## 4. Requirements

### Foundation (0xx)

- **FR-001** Hệ thống phải cấu hình Supabase Auth với Google provider ở local stack (client id/secret qua biến môi trường) trước khi luồng đăng nhập hoạt động được.
- **FR-002** Route callback `/auth/callback` phải nằm trong danh sách redirect được phép của Supabase Auth.

### Navigation (1xx)

- **FR-101** Người dùng chưa đăng nhập truy cập `/todo` được điều hướng tới `/login`.
- **FR-102** Người dùng đã đăng nhập truy cập `/login` được điều hướng tới `/todo`.

### Login Screen (2xx)

- **FR-201** Màn hình `/login` hiển thị header (logo + bộ chọn ngôn ngữ), khối giới thiệu "ROOT FURTHER", nút "LOGIN With Google", và footer bản quyền.
- **FR-202** Bấm nút đăng nhập Google chuyển nút sang trạng thái loading/disabled và khởi tạo luồng Google OAuth.
- **FR-203** Bộ chọn ngôn ngữ cho đổi giữa VN và EN, lưu lựa chọn vào cookie `NEXT_LOCALE`; mặc định là VN khi chưa chọn.
  - **FR-203.a** Panel mở hiển thị đầy đủ danh sách locale (VN, EN), mỗi mục có cờ + nhãn.
  - **FR-203.b** Mục ứng với locale đang chọn có nền phân biệt rõ so với mục còn lại.
  - **FR-203.c** Panel thao tác được bằng bàn phím: ArrowDown/ArrowUp di chuyển giữa các mục, Home/End nhảy đầu/cuối, Enter hoặc Space chọn, Escape đóng và trả focus về trigger.

### Interaction (4xx)

- **FR-401** Xác thực Google thành công thì hệ thống lấy phiên đăng nhập và điều hướng người dùng tới `/todo`.
- **FR-402** Xác thực thất bại hoặc bị người dùng huỷ thì hệ thống hiện thông báo "Đăng nhập không thành công. Vui lòng thử lại." và cho phép bấm lại.
- **FR-403** Người dùng đã đăng nhập đăng xuất được; sau khi đăng xuất, hệ thống điều hướng về `/login`.

### Security (6xx)

- **FR-601** Không giới hạn domain Google — mọi tài khoản Google hợp lệ đều được phép đăng nhập.
- **FR-602** `/todo` không truy cập được nếu không có phiên đăng nhập hợp lệ.

## 5. Business Rules

- Mọi tài khoản Google hợp lệ đều được phép đăng nhập, không áp dụng domain allow-list (BR-001)
- Người dùng chưa xác thực bị điều hướng khỏi `/todo` về `/login`; người dùng đã xác thực bị điều hướng khỏi `/login` về `/todo` (BR-002)
- Khi chưa có cookie `NEXT_LOCALE`, ngôn ngữ mặc định là VN (BR-003)
- Khi xác thực Google thất bại hoặc bị huỷ, màn hình hiện thông báo lỗi cố định và nút đăng nhập trở lại trạng thái sẵn sàng để bấm lại (DEC-001)
- Kết quả callback OAuth (thành công hay lỗi) quyết định điều hướng tới `/todo` hoặc quay lại `/login` kèm cờ lỗi (DEC-002)
- Nút đăng nhập Google chuyển từ trạng thái sẵn sàng sang đang xử lý khi bấm, và trở lại sẵn sàng nếu xác thực thất bại (SM-001)

## 6. Screens

| Screen Name | SCR### | What User Sees | What User Can Do |
|-------------|--------|-----------------|-------------------|
| Login | SCR-login *(draft — mã chính thức cấp khi promote)* | Header (logo + bộ chọn ngôn ngữ VN mặc định), hero nền trừu tượng, wordmark "ROOT FURTHER", dòng giới thiệu SAA 2025, nút "LOGIN With Google", footer bản quyền cố định | Bấm đăng nhập Google; đổi ngôn ngữ VN/EN |

### User Journey

1. Khách truy cập `/login`, thấy màn hình như trên với ngôn ngữ mặc định VN.
2. Khách bấm "LOGIN With Google" — nút chuyển sang trạng thái loading, trình duyệt được đưa sang trang xác thực Google.
3. Xác thực thành công: khách được đưa tới `/todo`. Xác thực thất bại hoặc huỷ: khách quay lại `/login`, thấy thông báo lỗi, nút trở lại trạng thái sẵn sàng.
4. Từ `/todo`, người dùng đăng xuất được — hệ thống đưa họ về `/login`.

## 7. User Stories

### US001_GoogleSignIn — Đăng nhập bằng Google

**Actor:** Khách truy cập chưa đăng nhập
**Goal:** Đăng nhập bằng tài khoản Google để vào ứng dụng SAA 2025.
**Business value:** Vào ứng dụng nhanh, không phải tạo hay nhớ thêm mật khẩu riêng.

**Acceptance Criteria:**
- [ ] Bấm nút đăng nhập khởi tạo luồng Google OAuth và hiện trạng thái loading/disabled.
- [ ] Xác thực thành công đưa người dùng tới `/todo`.
- [ ] Xác thực thất bại hoặc bị huỷ hiện đúng thông báo "Đăng nhập không thành công. Vui lòng thử lại." và cho bấm lại.

### US002_RouteGuard — Điều hướng theo trạng thái đăng nhập

**Actor:** Khách truy cập chưa đăng nhập / Người dùng đã đăng nhập
**Goal:** Luôn được đưa tới đúng màn hình dựa trên việc đã đăng nhập hay chưa.
**Business value:** Tránh hiện lại màn hình đăng nhập cho người đã đăng nhập, và bảo vệ nội dung sau đăng nhập khỏi người chưa xác thực.

**Acceptance Criteria:**
- [ ] Đã đăng nhập mà vào `/login` thì bị đưa tới `/todo`.
- [ ] Chưa đăng nhập mà vào `/todo` thì bị đưa tới `/login`.

### US003_LanguageSelection — Chọn ngôn ngữ hiển thị

**Actor:** Khách truy cập
**Goal:** Đổi giao diện giữa Tiếng Việt và English trước khi đăng nhập.
**Business value:** Nội dung dễ tiếp cận hơn theo ngôn ngữ người dùng quen dùng.

**Acceptance Criteria:**
- [ ] Mặc định hiện VN (cờ Việt Nam + "VN" + mũi tên xuống) khi chưa có cookie ngôn ngữ.
- [ ] Chọn ngôn ngữ khác cập nhật toàn bộ nội dung trang và lưu vào cookie `NEXT_LOCALE`.
- [ ] Panel mở phân biệt được mục đang chọn bằng nền, không chỉ bằng thuộc tính ẩn.
- [ ] Mở panel rồi bấm lại trigger thì panel đóng (toggle).
- [ ] Điều hướng được toàn bộ panel bằng bàn phím, không cần chuột.

### US004_SignOut — Đăng xuất

**Actor:** Người dùng đã đăng nhập
**Goal:** Kết thúc phiên đăng nhập của mình.
**Business value:** Đảm bảo phiên đăng nhập kết thúc được một cách an toàn khi không còn dùng nữa.

**Acceptance Criteria:**
- [ ] Đăng xuất xoá phiên đăng nhập hiện tại.
- [ ] Sau khi đăng xuất, hệ thống điều hướng về `/login`.

## 8. Scenarios

### US001_GoogleSignIn — Happy Path

**Given** khách chưa đăng nhập đang ở `/login`, **When** bấm "LOGIN With Google" và xác thực Google thành công, **Then** khách được điều hướng tới `/todo`.

### US001_GoogleSignIn — Error: Xác thực thất bại hoặc bị huỷ

**Given** khách chưa đăng nhập đang ở `/login`, **When** bấm "LOGIN With Google" nhưng huỷ hoặc xác thực thất bại ở phía Google, **Then** khách quay lại `/login` và thấy thông báo "Đăng nhập không thành công. Vui lòng thử lại.", nút đăng nhập trở lại trạng thái sẵn sàng.

### US002_RouteGuard — Happy Path

**Given** người dùng đã đăng nhập, **When** người dùng truy cập `/login` (ví dụ dán lại URL), **Then** hệ thống điều hướng ngay tới `/todo`, không hiện lại form đăng nhập.

### US002_RouteGuard — Error: Truy cập trái phép

**Given** khách chưa đăng nhập, **When** khách truy cập trực tiếp `/todo`, **Then** hệ thống điều hướng ngay tới `/login`.

### US003_LanguageSelection — Happy Path

**Given** khách đang ở `/login` với ngôn ngữ mặc định VN, **When** khách chọn EN từ bộ chọn ngôn ngữ, **Then** toàn bộ nội dung trang chuyển sang English và cookie `NEXT_LOCALE` lưu giá trị `en`.

### US003_LanguageSelection — Error: Giá trị ngôn ngữ không hợp lệ

**Given** cookie `NEXT_LOCALE` bị thiếu hoặc chứa giá trị không phải `vi`/`en`, **When** khách tải `/login`, **Then** hệ thống hiển thị mặc định VN thay vì lỗi trắng trang.

### US004_SignOut — Happy Path

**Given** người dùng đã đăng nhập đang ở `/todo`, **When** người dùng bấm đăng xuất, **Then** phiên đăng nhập kết thúc và người dùng được điều hướng về `/login`.

### US004_SignOut — Error: Đăng xuất khi phiên đã hết hạn

**Given** phiên đăng nhập của người dùng đã hết hạn trước khi bấm đăng xuất, **When** người dùng bấm đăng xuất, **Then** hệ thống vẫn điều hướng về `/login` mà không báo lỗi cho người dùng.

## 9. Edge Cases

| Scenario | What Happens | User-Facing Message |
|----------|--------------|----------------------|
| Người dùng huỷ ở màn hình consent của Google | Callback nhận cờ lỗi, điều hướng về `/login`, nút đăng nhập trở lại trạng thái sẵn sàng | "Đăng nhập không thành công. Vui lòng thử lại." |
| Bấm nút đăng nhập nhiều lần liên tiếp trong lúc đang xử lý | Nút đã disabled nên không gửi thêm yêu cầu OAuth thứ hai | "None — silent handling" |
| Người dùng đã đăng nhập cố truy cập lại `/login` | Bị chặn trước khi màn hình đăng nhập kịp render, điều hướng thẳng `/todo` | "None — silent handling" |
| Người dùng chưa đăng nhập cố truy cập thẳng `/todo` | Bị chặn, điều hướng thẳng `/login` | "None — silent handling" |

## 10. Edge Behaviours to Verify

- **FR-101** → Truy cập `/todo` khi chưa đăng nhập phải luôn bị đưa về `/login`.
- **FR-102** → Truy cập `/login` khi đã đăng nhập phải luôn bị đưa về `/todo`.
- **FR-201** → Header, hero, khối "ROOT FURTHER", nút đăng nhập và footer đều hiển thị đúng vị trí; logo và footer không có tương tác.
- **FR-202** → Nút đăng nhập hiện loading/disabled trong lúc xử lý; hiện hiệu ứng shadow khi hover.
- **FR-203** → Bộ chọn ngôn ngữ mặc định VN (cờ trái, mũi tên phải), mở dropdown khi bấm, đổi ngôn ngữ toàn trang khi chọn.
- **FR-401** → Xác thực Google thành công trả về thông tin người dùng và điều hướng `/todo`.
- **FR-402** → Xác thực thất bại/huỷ hiện đúng nguyên văn thông báo lỗi.
- **FR-403** → Đăng xuất điều hướng về `/login`.
- **FR-601** → Tài khoản Google bất kỳ (không chỉ domain nội bộ) đăng nhập được.

## 11. Risks & Known Issues

| ID | Type | Description | Impact | Status |
|----|------|--------------|--------|--------|
| RISK-01 | risk | Ảnh nền hero (node MoMorph `662:14389`) chưa export được trong phiên nghiên cứu này — endpoint render trả 500/401 trên mọi cách thử. File `public/images/login/hero.png` chưa tồn tại. | Màn hình chưa thể khớp pixel với thiết kế cho tới khi ảnh được export lại (thử lại endpoint render, hoặc export tay từ Figma) — có thể cần nền tạm thời khi implement. | [UNVERIFIED] |

## 12. Dependencies

| Dependency | Type | Why this feature needs it | Evidence |
|------------|------|-----------------------------|----------|
| Supabase Auth — Google provider (local stack) | external-service | Cần bật `auth.external.google` trong `supabase/config.toml` với client id/secret hợp lệ để khởi tạo OAuth | FR-001 |
| Google Cloud OAuth Client (bên ngoài) | external-service | Cần client ID/secret thật để Supabase phát hành URL xác thực Google | FR-001 |
| `@playwright/test` | infrastructure | Cần bổ sung vào dự án để tester chạy `e2e-red-first` theo quyết định trong `clarifications.md` | testPolicy: e2e-red-first |
| Ảnh nền hero (`public/images/login/hero.png`) | data | Chưa export được từ MoMorph — cần trước khi UI khớp thiết kế | RISK-01 |

## 13. Configuration

```text
NEXT_LOCALE = vi | en   # ngôn ngữ hiển thị màn hình đăng nhập, mặc định vi khi cookie chưa có giá trị
GOOGLE_ACCOUNT_RESTRICTION = none   # mọi tài khoản Google hợp lệ đều được phép đăng nhập, không có domain allow-list
```
