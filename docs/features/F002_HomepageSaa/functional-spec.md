---
status: implemented
authored_by: takumi
created: 2026-09-05
lang: vi
---

**Priority**: P0
**Type**: ui

## 1. Overview

**Problem:** Khách truy cập SAA 2025 (Sun* Annual Awards 2025) cần một trang chủ công khai để hiểu chủ đề "Root Further" của mùa giải, biết hệ thống giải thưởng gồm những hạng mục nào, và tìm đường vào Sun* Kudos — trước khi có tài khoản hay đăng nhập.
**Solution:** Trang chủ công khai tại `/` — thay thế trang boilerplate `create-next-app` hiện tại — trình bày header điều hướng, hero với bộ đếm ngược sự kiện, khối nội dung chủ đề "Root Further", lưới 6 thẻ giải thưởng, khối quảng bá Sun* Kudos, nút widget nổi và footer. Người dùng đã đăng nhập thấy thêm chuông thông báo và menu tài khoản trên header.
**Scope:** Hiển thị đầy đủ nội dung trang chủ theo thiết kế; điều hướng ra các trang đích (kể cả 5 route placeholder tối thiểu để không có liên kết gãy); chuông thông báo + menu tài khoản cho người dùng đã đăng nhập (role admin thấy thêm mục Admin Dashboard); bộ đếm ngược tự tính từ biến cấu hình.
**Non-Scope:** Không bao gồm nội dung thật của Sun* Kudos / Tiêu chuẩn chung / Profile — các route đó chỉ có shell `ComingSoon` dùng chung, không phải trang đích thật. *(Award Information cũng nằm trong nhóm này khi F002 ship; từ 2026-09-06 `/awards-information` là màn hình thật của F003_AwardSystem.)* Không có huy hiệu thông báo chưa đọc (chưa có backend thông báo — xem § 11 RISK-01). Không re-specify cơ chế cookie ngôn ngữ / Google OAuth — đã có ở F001_Login.

**Actors**

| Actor | Description | Primary goal |
|-------|--------------|---------------|
| Khách truy cập | Người vào `/` chưa đăng nhập (đa số lượt truy cập) | Hiểu chủ đề Root Further, xem hệ thống giải thưởng, tìm đường vào Award Information / Sun* Kudos |
| Người dùng đã đăng nhập | Người đã xác thực Google qua F001_Login (có thể có role admin) | Xem thông báo, mở menu tài khoản (Profile / Sign out / Admin Dashboard nếu có quyền) |

## 2. Functional Capabilities

<!-- Một outcome duy nhất theo .intent-enum.json: "one screen, one user-facing outcome" — countdown,
     awards grid, Kudos block là các SECTION của cùng một outcome duyệt trang chủ, không phải capability
     riêng. #CAP == 1, US count = 2 (dưới ngưỡng warn 3-4 của type=ui) nên không cần rationale line. -->

| ID | Capability | What the user can do | User Stories | Requirements | Business Rules | Screens |
|----|------------|------------------------|-----------------|---------------|-------------------|---------|
| CAP-01 | Xem và tương tác với trang chủ SAA 2025 | Duyệt hero/nội dung Root Further/hệ thống giải thưởng/Sun* Kudos, điều hướng ra các trang liên quan, và (nếu đã đăng nhập) xem thông báo + mở menu tài khoản | US005, US006 | FR-001, FR-002, FR-101, FR-102, FR-201, FR-202, FR-203, FR-204, FR-205, FR-206, FR-207, FR-401, FR-402, FR-403, FR-404, FR-405, FR-601 | BR-001, BR-002, BR-003, BR-004, DEC-001, DEC-002 | SCR002_Homepage |

> **Đánh số lại (traceability)**: hai user story của tính năng này soạn cục bộ là `US001_BrowseHomepage`/`US002_AccountNotificationMenu`, nhưng `US###` là mã global toàn dự án (`code-formats.md`) và `US001`/`US002` đã bị F001_Login chiếm trước. `docs/generated/user-stories.md` đã cấp lại mã global `US005`/`US006` cho hai story này; file này cập nhật theo, giữ nguyên slug gốc trong tiêu đề (`US005_BrowseHomepage`, `US006_AccountNotificationMenu`) để không mất traceability với slug cũ.

## 3. Open Decisions

None — no unresolved domain confirmations. (`/tkm:takumi --auto` đã giải quyết toàn bộ gap ở `clarifications.md`; không có `[NEEDS_DOMAIN_CONFIRMATION]` nào phát sinh khi soạn spec này.)

## 4. Requirements

### Foundation (0xx)

- **FR-001** Trang chủ (`/`) phải công khai, không yêu cầu đăng nhập; `proxy.ts` hiện có (route guard của F001_Login) tiếp tục cho qua nguyên trạng, tính năng này không thêm guard mới. *(clarifications.md — "proxy.ts already lets `/` through untouched", test ID-0)*
- **FR-002** Mọi route đích của trang chủ phải tồn tại để không có liên kết gãy (kể cả mục "Admin Dashboard" role-gated trong menu tài khoản). Khi F002 ship, cả năm — `/awards-information`, `/kudos`, `/standards`, `/profile`, `/admin` — dùng chung một component `ComingSoon` có header/footer thật. Từ 2026-09-06, `/awards-information` render màn hình thật của F003_AwardSystem và **bốn** route còn lại vẫn dùng `ComingSoon`. *(clarifications.md ORCH-11, test ID-59; xác nhận code: `app/admin/page.tsx`, `app/awards-information/page.tsx:55`. Comment "the five ComingSoon placeholders" ở `app/_components/use-scroll-to-top-if-current.ts:14` nay đếm thừa một — comment thôi, hành vi không phụ thuộc vào route nào.)*

### Navigation (1xx)

- **FR-101** Header có 3 mục điều hướng: "About SAA 2025" (đang chọn trên trang chủ), "Award Information", "Sun* Kudos". *(spec item A1, frame header)*
- **FR-102** Bấm mục nav đang được chọn thì cuộn lên đầu trang thay vì điều hướng lại; bấm mục nav khác điều hướng sang route tương ứng. *(spec item A1.2)*

### Homepage Screen (2xx)

- **FR-201** Header hiển thị logo, 3 mục nav, và (chỉ khi đã đăng nhập) chuông thông báo + biểu tượng tài khoản, cộng bộ chọn ngôn ngữ VN/EN tái dùng từ F001_Login. *(spec item A1; ngôn ngữ — clarifications.md "Promote to shared")*
- **FR-202** Hero hiển thị keyvisual "ROOT FURTHER", nhãn "Coming soon", bộ đếm ngược DAYS/HOURS/MINUTES, thông tin sự kiện (thời gian 26/12/2025, địa điểm Âu Cơ Art Center, tường thuật qua Livestream), và hai nút CTA "ABOUT AWARDS" + "ABOUT KUDOS". *(spec item B1, B2 — frame ghi đè copy cũ trong B2, xem clarifications.md "Resolved from source data")*
- **FR-203** Khối nội dung "Root Further" hiển thị watermark ảnh ROOT/FURTHER cùng đoạn giới thiệu chủ đề mùa giải. *(spec item B4)*
- **FR-204** Hệ thống giải thưởng hiển thị tiêu đề "Hệ thống giải thưởng" và lưới 6 thẻ: Top Talent, Top Project, Top Project Leader, Best Manager, Signature 2025 - Creator, MVP (Most Valuable Person) — mỗi thẻ có ảnh, tên, mô tả cắt tối đa 2 dòng kèm dấu ba chấm, và liên kết "Chi tiết". *(spec item C1, C2, C2.1.3)*
- **FR-205** Khối quảng bá Sun* Kudos hiển thị tiêu đề, mô tả, và nút "Chi tiết" điều hướng `/kudos`. *(spec item D1, D2)*
- **FR-206** Nút widget nổi hiển thị hai biểu tượng phân tách bởi dấu "/": biểu tượng "viết kudos" điều hướng `/kudos`, biểu tượng "thể lệ SAA" điều hướng `/standards`. Từ 2026-09-10, F008_FloatingActionButton thay hình dạng hai-liên-kết-trực-tiếp này bằng một cần mở (disclosure trigger) — bấm mở menu ba lựa chọn `Thể lệ`/`Viết KUDOS`/`Hủy`, đích viết Kudos đổi thành `/kudos/new`. *(spec item, node "icon viết kudos" / "icon thể lệ saa" — clarifications.md; xem `docs/features/F008_FloatingActionButton/functional-spec.md`)*
- **FR-207** Footer hiển thị 4 liên kết (About SAA 2025, Award Information, Sun* Kudos, Tiêu chuẩn chung) và dòng bản quyền "Bản quyền thuộc về Sun* © 2025". *(spec item — footer, 5 phần tử)*

### Interaction (4xx)

- **FR-401** Bộ đếm ngược tự tính lại mỗi giây từ đồng hồ hệ thống (không dựa vào giá trị server render), giữ nguyên các ô ở `00` và ẩn "Coming soon" một khi đã qua thời điểm sự kiện. *(spec item B1.2; test ID-39, ID-41, ID-42, ID-43)*
- **FR-402** Khi biến cấu hình thời gian sự kiện thiếu hoặc sai định dạng, hệ thống hiện `00/00/00`, ẩn "Coming soon", ghi một dòng cảnh báo console, và không bao giờ làm sập trang. *(test ID-60)*
- **FR-403** Bấm chuông thông báo (chỉ hiện khi đã đăng nhập) mở panel hiển thị "Không có thông báo mới"; không có huy hiệu vì chưa có nguồn dữ liệu chưa đọc. *(clarifications.md — chuông thông báo; test ID-29, ID-28 deferred)*
- **FR-404** Bấm biểu tượng tài khoản mở menu gồm Profile và Sign out (Sign out tái dùng server action đăng xuất hiện có của F001_Login, đã chuyển tới `app/_actions/auth.ts`); mục Admin Dashboard chỉ xuất hiện khi `user.app_metadata.role === "admin"`. *(clarifications.md — menu tài khoản; test ID-37, ID-38)*
- **FR-405** Bấm vào bất kỳ phần nào của thẻ giải thưởng (ảnh, tên, hoặc "Chi tiết") đều điều hướng tới `/awards-information#<slug>` tương ứng với hạng mục đó. *(test ID-47, ID-48, ID-49)*

### Security (6xx)

- **FR-601** Mục "Admin Dashboard" chỉ hiển thị với người dùng có role admin; đây là gating hiển thị ở UI — trang đích `/profile`/Admin Dashboard thật (khi được xây sau này) phải tự kiểm tra quyền, không được chỉ dựa vào việc ẩn mục menu này. *(test ID-37, ID-38)*

## 5. Business Rules

- Trang chủ luôn công khai, không có guard mới ngoài route guard hiện có của F001_Login (FR-001)
- Chuông thông báo và biểu tượng tài khoản chỉ hiện khi có phiên đăng nhập hợp lệ; khách chưa đăng nhập không thấy hai phần tử này (FR-201, FR-403, FR-404)
- Bộ đếm ngược tick mỗi giây từ đồng hồ hệ thống; khi thời điểm sự kiện đã qua, giữ nguyên `00` và ẩn nhãn "Coming soon" (FR-401)
- Biến cấu hình thời gian sự kiện không hợp lệ thì hiện `00/00/00`, ẩn "Coming soon", ghi cảnh báo console, không throw lỗi (FR-402)
- Bấm mục nav đang chọn thì cuộn lên đầu trang thay vì điều hướng lại (DEC-001)
- Mục Admin Dashboard trong menu tài khoản chỉ hiện khi vừa đã đăng nhập vừa có role admin (DEC-002)

## 6. Screens

| Screen Name | SCR### | What User Sees | What User Can Do |
|-------------|--------|-----------------|-------------------|
| Homepage | SCR002_Homepage | Header (logo, 3 mục nav, chuông + tài khoản nếu đã đăng nhập, bộ chọn ngôn ngữ), hero với keyvisual + "Coming soon" + đếm ngược + thông tin sự kiện + 2 CTA, khối nội dung Root Further, lưới 6 thẻ giải thưởng, khối quảng bá Sun* Kudos, nút widget nổi, footer | Điều hướng ra Award Information / Sun* Kudos / Tiêu chuẩn chung / từng thẻ giải thưởng; đổi ngôn ngữ; (nếu đã đăng nhập) xem thông báo, mở menu tài khoản, đăng xuất |

### User Journey

1. Khách truy cập `/`, thấy header với "About SAA 2025" đang chọn, và toàn bộ nội dung trang chủ theo ngôn ngữ mặc định VN.
2. Khách đọc hero — thấy "Coming soon" và bộ đếm ngược tới sự kiện 26/12/2025, hoặc (nếu đã qua ngày) không thấy nhãn đó và bộ đếm giữ `00`.
3. Khách cuộn xuống đọc nội dung "Root Further", rồi tới lưới 6 thẻ giải thưởng — bấm một thẻ để xem "Chi tiết" (điều hướng sang trang Award Information placeholder).
4. Khách cuộn tới khối Sun* Kudos, bấm "Chi tiết" để sang trang Kudos placeholder, hoặc dùng nút widget nổi để đi thẳng tới Kudos/Tiêu chuẩn chung.
5. Người dùng đã đăng nhập bấm chuông thông báo — thấy "Không có thông báo mới"; bấm biểu tượng tài khoản — thấy menu Profile / Sign out / (nếu admin) Admin Dashboard; bấm Sign out kết thúc phiên và quay về `/login`.

## 7. User Stories

### US005_BrowseHomepage — Duyệt trang chủ SAA 2025 *(was US001_BrowseHomepage, local)*

**Actor:** Khách truy cập
**Goal:** Hiểu chủ đề "Root Further" của mùa giải, biết hệ thống giải thưởng gồm những hạng mục nào, và tìm đường vào Award Information / Sun* Kudos / Tiêu chuẩn chung.
**Business value:** Truyền thông đúng chủ đề mùa giải SAA 2025 tới toàn bộ Sunner mà không cần đăng nhập, và dẫn họ đi sâu vào thông tin chi tiết khi cần.

**Acceptance Criteria:**
- [ ] Trang chủ hiển thị đầy đủ 7 khối theo đúng thứ tự thiết kế: header, hero, nội dung Root Further, hệ thống giải thưởng, quảng bá Sun* Kudos, widget nổi, footer.
- [ ] Mọi liên kết trên trang (nav, CTA, thẻ giải thưởng, widget, footer) đều điều hướng tới một đích hợp lệ — không có liên kết gãy.
- [ ] Bộ đếm ngược tick đúng, và ẩn "Coming soon" đúng lúc khi qua thời điểm sự kiện.

### US006_AccountNotificationMenu — Xem thông báo và quản lý tài khoản *(was US002_AccountNotificationMenu, local)*

**Actor:** Người dùng đã đăng nhập
**Goal:** Kiểm tra thông báo và truy cập nhanh Profile / Admin Dashboard (nếu có quyền) / Sign out ngay từ header trang chủ.
**Business value:** Không phải rời trang chủ để quản lý tài khoản; admin nhận diện được lối vào Admin Dashboard mà người dùng thường không thấy.

**Acceptance Criteria:**
- [ ] Chuông thông báo và biểu tượng tài khoản chỉ hiện khi đã đăng nhập.
- [ ] Bấm chuông mở panel "Không có thông báo mới", không có huy hiệu đỏ.
- [ ] Bấm biểu tượng tài khoản mở menu Profile / Sign out; Admin Dashboard chỉ thêm vào khi role là admin.
- [ ] Bấm Sign out kết thúc phiên và điều hướng về `/login`.

## 8. Scenarios

### US005_BrowseHomepage — Happy Path

**Given** khách truy cập `/` lần đầu, **When** trang tải xong, **Then** khách thấy đầy đủ 7 khối nội dung theo đúng thứ tự thiết kế, với bộ đếm ngược đang tick.

### US005_BrowseHomepage — Error: Biến cấu hình thời gian sự kiện sai định dạng

**Given** `NEXT_PUBLIC_EVENT_START_AT` bị thiếu hoặc không đúng định dạng ISO-8601, **When** khách truy cập `/`, **Then** bộ đếm hiện `00/00/00`, "Coming soon" bị ẩn, và trang vẫn tải bình thường không có lỗi hiển thị cho khách.

### US006_AccountNotificationMenu — Happy Path

**Given** người dùng đã đăng nhập đang ở `/`, **When** bấm biểu tượng tài khoản, **Then** menu mở ra với Profile và Sign out (thêm Admin Dashboard nếu role admin).

### US006_AccountNotificationMenu — Error: Bấm Sign out khi phiên đã hết hạn

**Given** phiên đăng nhập của người dùng đã hết hạn trước khi bấm Sign out, **When** người dùng vẫn bấm Sign out, **Then** hệ thống vẫn điều hướng về `/login` mà không báo lỗi cho người dùng.

## 9. Edge Cases

| Scenario | What Happens | User-Facing Message |
|----------|--------------|----------------------|
| Biến cấu hình thời gian sự kiện thiếu hoặc sai định dạng | Bộ đếm hiện `00/00/00`, ẩn "Coming soon", ghi cảnh báo console (dev), không sập trang | "None — silent handling, không có lỗi hiển thị cho người dùng" |
| Thời điểm sự kiện đã qua khi tải trang | Bộ đếm giữ nguyên `00` ở cả 3 ô, "Coming soon" ẩn, không có cờ lỗi | "None — silent handling" |
| Người dùng không phải admin thử truy cập thẳng URL đích Admin Dashboard | Mục đó không hiện trong menu; route đích hiện tại vẫn là `ComingSoon` công khai — chưa có nội dung thật cần bảo vệ | "None — silent handling ở giai đoạn hiện tại (xem FR-601)" |
| Khách chưa đăng nhập | Chuông thông báo và biểu tượng tài khoản không render trong DOM | "N/A — phần tử không tồn tại" |

## 10. Edge Behaviours to Verify

- **FR-401** → Bộ đếm ngược phải tick đúng mỗi phút và giữ `00` sau khi qua thời điểm sự kiện.
- **FR-402** → Giá trị cấu hình sai định dạng phải luôn hiện `00/00/00` và không làm sập trang.
- **FR-403** → Chuông thông báo chỉ hiện khi đã đăng nhập, và không bao giờ có huy hiệu đỏ ở giai đoạn hiện tại.
- **FR-404** → Mục Admin Dashboard chỉ hiện đúng với tài khoản có role admin.
- **FR-405** → Bấm bất kỳ phần nào của thẻ giải thưởng đều điều hướng đúng slug tương ứng.
- **FR-002** → Cả 5 route placeholder (kể cả `/admin`) phải tải được, không có liên kết gãy trên trang chủ.

## 11. Risks & Known Issues

| ID | Type | Description | Impact | Status |
|----|------|--------------|--------|--------|
| RISK-01 | risk | Chưa có nguồn dữ liệu thông báo chưa đọc — huy hiệu đỏ trên chuông thông báo (test ID-28) không triển khai được cho tới khi có backend thông báo thật. | Người dùng không có tín hiệu trực quan khi có thông báo mới (khi backend đó tồn tại). | [EXPECTED] |
| RISK-02 | risk | 35 node `MM_MEDIA_*` (keyvisual hero, ảnh thẻ giải thưởng composite, nền khối Kudos) chưa được xác nhận export thành công trong phiên nghiên cứu này. | Màn hình có thể chưa khớp pixel với thiết kế cho tới khi toàn bộ ảnh được export và đặt vào `public/images/`. | [RESOLVED] — toàn bộ ảnh tham chiếu trong code (6 thẻ giải thưởng, 2 watermark Root/Further, keyvisual, nền + logo Kudos, 2 icon widget, logo footer) đã có mặt tại `public/images/home/` và được component dùng trực tiếp; xem `app/_components/{awards-grid,award-card,root-further-block,kudos-promo,floating-widget,site-footer}.tsx`. |

## 12. Dependencies

| Dependency | Type | Why this feature needs it | Evidence |
|------------|------|-----------------------------|----------|
| F001_Login | feature | Tái dùng header/ngôn ngữ chọn ngôn ngữ (`app/_components/language-selector.tsx`, đã promote khỏi `app/login/_components/`) và server action đăng xuất/đổi ngôn ngữ (`app/_actions/auth.ts`, `app/_actions/locale.ts`) — không re-specify ở đây | code hiện tại — không re-specify |
| Supabase Auth | external-service | Nguồn `user.app_metadata.role` để gating mục Admin Dashboard (FR-601) | FR-601 |
| `@playwright/test` | infrastructure | Cần cho `testPolicy: e2e-red-first` — màn hình có nhiều state transition (menu mở/đóng, đếm ngược, điều hướng) | clarifications.md — "Test policy" |
| MM_MEDIA image assets (35 node) | data | Ảnh hero/thẻ giải thưởng/nền Kudos là ảnh composite; đã export và có mặt tại `public/images/home/` (RISK-02 resolved) | RISK-02 |

## 13. Configuration

```text
NEXT_PUBLIC_EVENT_START_AT = 2025-12-26T18:30:00+07:00   # thời điểm sự kiện SAA 2025 (ISO-8601); sai định dạng thì bộ đếm hiện 00/00/00 và ẩn "Coming soon"
```
