---
authored_by: rebuild-spec (Core pass, generated layer)
---

# User Stories

**Project**: my-app (SAA 2025)
**Generated**: 2026-09-05
**Analysis Scope**: `docs/features/F001_Login/functional-spec.md`, `docs/features/F002_HomepageSaa/functional-spec.md`, `docs/features/F003_AwardSystem/functional-spec.md`

> **Renumbering note**: the two feature specs above (SDD forward-drafts) numbered their user
> stories per-feature-locally (`F001` → US001–US004, `F002` → US001–US002 — the same codes
> reused across features). `code-formats.md`'s contiguity invariant requires US### to be
> globally contiguous 001..N across the whole project. This file renumbers F002's two stories to
> US005/US006 and keeps F001's four stories at US001–US004 unchanged. Original per-feature codes
> are recorded under **Was** below for traceability.

## User Story Index

| Code | Was (per-feature) | Title | Type | Priority | Owner F### | Screens |
|------|--------------------|-------|------|----------|------------|---------|
| US001 | US001_GoogleSignIn | Đăng nhập bằng Google | ui | P0 | F001 | SCR001_Login |
| US002 | US002_RouteGuard | Điều hướng theo trạng thái đăng nhập | ui | P0 | F001 | SCR001_Login (bounce target) |
| US003 | US003_LanguageSelection | Chọn ngôn ngữ hiển thị | ui | P0 | F001 | SCR001_Login |
| US004 | US004_SignOut | Đăng xuất | ui | P0 | F001 | SCR001_Login (bounce target) |
| US005 | US001_BrowseHomepage | Duyệt trang chủ SAA 2025 | ui | P0 | F002 | SCR002_Homepage |
| US006 | US002_AccountNotificationMenu | Xem thông báo và quản lý tài khoản | ui | P0 | F002 | SCR002_Homepage |
| US007 | US007_BrowseAwardSystem | Đọc hệ thống giải thưởng SAA 2025 | ui | P1 | F003 | SCR003_AwardSystem |
| US008 | US008_JumpToAwardCategory | Nhảy tới một hạng mục qua menu danh mục | ui | P1 | F003 | SCR003_AwardSystem |

---

## US001: Đăng nhập bằng Google

**Type**: ui
**Interaction**: primary-action
**Priority**: P0
**Owner F###**: F001

### User Story

As a khách truy cập chưa đăng nhập, I want to đăng nhập bằng Google so that vào ứng dụng SAA 2025 mà không cần tạo hay nhớ thêm mật khẩu riêng.

### Acceptance Criteria

- [ ] Bấm nút đăng nhập khởi tạo luồng Google OAuth và hiện trạng thái loading/disabled (`google-sign-in-button.tsx:18`, `useFormStatus()`).
- [ ] Xác thực thành công đưa người dùng tới `/todo`.
- [ ] Xác thực thất bại hoặc bị huỷ hiện "Đăng nhập không thành công. Vui lòng thử lại." và cho bấm lại.

### Technical Notes

- **Endpoint**: server action `signInWithGoogle()` (`app/login/actions.ts:16`) → GET `/auth/callback` (ROUTE001)
- **Data Required**: none beyond the Google OAuth consent response
- **Dependencies**: Supabase Auth Google provider (`supabase/config.toml:336-338`)

### Screens

- SCR001_Login: Login

### Background Logic

- BL005_OAuthCallback (origin pinning, open-redirect defence, error funnel)
- BL003_CookiePreservingRedirect (guarded redirect after the callback lands authenticated)

### Test Scenarios

| Scenario | Given | When | Then |
|----------|-------|------|------|
| Happy Path | Khách chưa đăng nhập ở `/login` | Bấm "LOGIN With Google", xác thực Google thành công | Điều hướng tới `/todo` |
| Error Case | Khách chưa đăng nhập ở `/login` | Bấm nút, huỷ hoặc xác thực thất bại | Quay lại `/login`, thông báo lỗi, nút trở lại sẵn sàng |

---

## US002: Điều hướng theo trạng thái đăng nhập

**Type**: ui
**Interaction**: system-action
**Priority**: P0
**Owner F###**: F001

### User Story

As a khách truy cập / người dùng đã đăng nhập, I want to được điều hướng đúng màn hình theo trạng thái đăng nhập so that không bị hiện lại form đăng nhập khi đã đăng nhập, và không truy cập được nội dung sau đăng nhập khi chưa xác thực.

### Acceptance Criteria

- [ ] Đã đăng nhập mà vào `/login` thì bị đưa tới `/todo` (PERM002).
- [ ] Chưa đăng nhập mà vào `/todo` thì bị đưa tới `/login` (PERM001).

### Technical Notes

- **Endpoint**: N/A — enforced in `proxy.ts:41-46`, not a callable endpoint
- **Data Required**: session presence only (`updateSession()`'s `user` result)
- **Dependencies**: none beyond the Supabase session cookie

### Screens

- SCR001_Login: Login — the only designed screen either bounce direction lands on. **`/todo` has
  no SCR### of its own** — it is a deliberately unstyled placeholder proving the guard, not a
  designed screen (`app/todo/page.tsx:15-17`, scout §1).

### Background Logic

- BL003_CookiePreservingRedirect
- BL004_SessionRefreshCachePoisoningDefence

### Test Scenarios

| Scenario | Given | When | Then |
|----------|-------|------|------|
| Happy Path | Người dùng đã đăng nhập | Dán lại URL `/login` | Điều hướng ngay tới `/todo`, không hiện form đăng nhập |
| Error Case | Khách chưa đăng nhập | Truy cập trực tiếp `/todo` | Điều hướng ngay tới `/login` |

---

## US003: Chọn ngôn ngữ hiển thị

**Type**: ui
**Interaction**: secondary-action
**Priority**: P0
**Owner F###**: F001

### User Story

As a khách truy cập, I want to đổi giao diện giữa Tiếng Việt và English so that nội dung dễ tiếp cận hơn theo ngôn ngữ quen dùng.

### Acceptance Criteria

- [ ] Mặc định hiện VN khi chưa có cookie `NEXT_LOCALE`.
- [ ] Chọn ngôn ngữ khác cập nhật toàn bộ nội dung trang và lưu vào cookie `NEXT_LOCALE`.
- [ ] Panel mở phân biệt mục đang chọn bằng nền, không chỉ bằng thuộc tính ẩn.
- [ ] Panel thao tác được bằng bàn phím (ArrowUp/Down, Home/End, Enter/Space, Escape).

### Technical Notes

- **Endpoint**: server action `setLocale(locale)` (`app/_actions/locale.ts:13`)
- **Data Required**: candidate locale string from the panel selection
- **Dependencies**: none

### Screens

- SCR001_Login: Login

### Background Logic

- BL001_LocaleResolutionFallback
- BL002_DictionarySelection

### Test Scenarios

| Scenario | Given | When | Then |
|----------|-------|------|------|
| Happy Path | Khách ở `/login`, ngôn ngữ mặc định VN | Chọn EN | Toàn bộ nội dung chuyển English, cookie lưu `en` |
| Error Case | Cookie `NEXT_LOCALE` thiếu hoặc giá trị không hợp lệ | Khách tải `/login` | Hiển thị mặc định VN, không lỗi trắng trang |

---

## US004: Đăng xuất

**Type**: ui
**Interaction**: destructive-action
**Priority**: P0
**Owner F###**: F001

### User Story

As a người dùng đã đăng nhập, I want to đăng xuất so that kết thúc phiên đăng nhập của mình một cách an toàn.

### Acceptance Criteria

- [ ] Đăng xuất xoá phiên đăng nhập hiện tại.
- [ ] Sau khi đăng xuất, điều hướng về `/login`.

### Technical Notes

- **Endpoint**: server action `signOut()` (`app/_actions/auth.ts:17`)
- **Data Required**: none
- **Dependencies**: none

### Screens

- SCR001_Login: Login (redirect target). Called from `/todo` (`app/todo/page.tsx:31`) and from
  SCR002_Homepage's account menu (`account-menu.tsx:108`) — this story spans both features'
  screens by call site, though F001 owns the story per `docs/generated/feature-list.md`.

### Background Logic

- None — `signOut()`'s error is deliberately discarded (`app/_actions/auth.ts:17-21`) so an
  already-invalid session still redirects cleanly; this is a design note, not a BL### item.

### Test Scenarios

| Scenario | Given | When | Then |
|----------|-------|------|------|
| Happy Path | Người dùng đã đăng nhập ở `/todo` | Bấm đăng xuất | Phiên kết thúc, điều hướng về `/login` |
| Error Case | Phiên đã hết hạn trước khi bấm | Bấm đăng xuất | Vẫn điều hướng về `/login`, không báo lỗi |

---

## US005: Duyệt trang chủ SAA 2025

**Type**: ui
**Interaction**: navigation
**Priority**: P0
**Owner F###**: F002

### User Story

As a khách truy cập, I want to duyệt trang chủ SAA 2025 so that hiểu chủ đề "Root Further", biết hệ thống giải thưởng, và tìm đường vào Award Information / Sun* Kudos / Tiêu chuẩn chung.

### Acceptance Criteria

- [ ] Trang chủ hiển thị đủ 7 khối theo thứ tự thiết kế: header, hero, Root Further, hệ thống giải thưởng, quảng bá Sun* Kudos, widget nổi, footer.
- [ ] Mọi liên kết (nav, CTA, thẻ giải thưởng, widget, footer) điều hướng tới đích hợp lệ — không có liên kết gãy.
- [ ] Bộ đếm ngược tick đúng, ẩn "Coming soon" đúng lúc sau thời điểm sự kiện.

### Technical Notes

- **Endpoint**: N/A — Server Component render, no fetch
- **Data Required**: `NEXT_PUBLIC_EVENT_START_AT` (env), static `AWARDS` array, static dictionary
- **Dependencies**: F001 (shared header language selector, shared sign-out action)

### Screens

- SCR002_Homepage: Homepage

### Background Logic

- BL001_LocaleResolutionFallback, BL002_DictionarySelection (shared with F001)
- Countdown computation (client-side, see `behavior-logic.md` § Client-Side Logic — no BL### code, no canonical type match)
- Scroll-vs-navigate rule (client-side, same section)

### Test Scenarios

| Scenario | Given | When | Then |
|----------|-------|------|------|
| Happy Path | Khách truy cập `/` lần đầu | Trang tải xong | Đủ 7 khối nội dung, bộ đếm ngược đang tick |
| Error Case | `NEXT_PUBLIC_EVENT_START_AT` thiếu/sai định dạng | Khách truy cập `/` | Đếm hiện `00/00/00`, ẩn "Coming soon", trang vẫn tải bình thường |

---

## US006: Xem thông báo và quản lý tài khoản

**Type**: ui
**Interaction**: secondary-action
**Priority**: P0
**Owner F###**: F002

### User Story

As a người dùng đã đăng nhập, I want to kiểm tra thông báo và mở nhanh menu tài khoản từ header trang chủ so that không phải rời trang chủ để quản lý tài khoản, và (nếu admin) thấy được lối vào Admin Dashboard.

### Acceptance Criteria

- [ ] Chuông thông báo + biểu tượng tài khoản chỉ hiện khi đã đăng nhập (PERM005).
- [ ] Bấm chuông mở panel "Không có thông báo mới", không huy hiệu đỏ (chưa có backend thông báo).
- [ ] Bấm biểu tượng tài khoản mở menu Profile / Sign out; Admin Dashboard chỉ thêm khi role admin (PERM004).
- [ ] Bấm Sign out kết thúc phiên, điều hướng về `/login`.

### Technical Notes

- **Endpoint**: server action `signOut()` (`app/_actions/auth.ts:17`, reused from F001)
- **Data Required**: `isAuthenticated`, `isAdmin` booleans from `getPageContext()`
- **Dependencies**: F001 (`signOut` action); Supabase `app_metadata.role` (never written by this codebase — provisioning is out-of-band)

### Screens

- SCR002_Homepage: Homepage

### Background Logic

- Admin role gating computation (client-side, see `behavior-logic.md` § Client-Side Logic; enforcement side is PERM004)
- Outside/Escape dismissal contract (`use-dismiss-on-outside.ts`)

### Test Scenarios

| Scenario | Given | When | Then |
|----------|-------|------|------|
| Happy Path | Người dùng đã đăng nhập ở `/` | Bấm biểu tượng tài khoản | Menu mở với Profile và Sign out (+ Admin Dashboard nếu admin) |
| Error Case | Phiên đã hết hạn | Bấm Sign out | Vẫn điều hướng về `/login`, không báo lỗi |

---

## US007: Đọc hệ thống giải thưởng SAA 2025

**Type**: ui
**Interaction**: navigation
**Priority**: P1
**Owner F###**: F003

### User Story

As a khách truy cập, I want to đọc chi tiết sáu hạng mục giải SAA 2025 so that biết mỗi hạng mục vinh danh ai, có bao nhiêu giải và giá trị bao nhiêu — thay vì chỉ thấy một dòng mô tả cắt ngắn trên trang chủ.

### Acceptance Criteria

- [x] Trang hiển thị đủ năm khối theo đúng thứ tự thiết kế: header, hero, phần hệ thống giải, khối Sun* Kudos, footer.
- [x] Sáu thẻ giải thưởng hiện đúng thứ tự thiết kế, mỗi thẻ đủ ảnh 336×336, tiêu đề, mô tả, số lượng và giá trị giải.
- [x] Thẻ Signature hiện hai mức giải nối bằng `Hoặc`; Best Manager và MVP không có dòng ghi chú dưới số tiền.
- [ ] Đổi sang EN thì toàn bộ nội dung màn hình đổi theo (đã code, chưa có test tự động — F003 § 11 RISK-05).

### Technical Notes

- **Endpoint**: N/A — Server Component render, no fetch
- **Data Required**: `AWARDS` (`lib/awards.ts`), `AWARD_UNITS` (`lib/award-system.ts`), `dictionary.awardSystem`
- **Dependencies**: F002 (`HomeHeader`, `SiteFooter`, `KudosPromo`, sáu ảnh `award-*.png`); F001 (bộ chọn ngôn ngữ dùng chung)

### Screens

- SCR003_AwardSystem: Hệ thống giải

### Background Logic

- BL001_LocaleResolutionFallback, BL002_DictionarySelection (dùng chung với F001/F002)

### Test Scenarios

| Scenario | Given | When | Then |
|----------|-------|------|------|
| Happy Path | Khách chưa đăng nhập mở `/awards-information` | Trang tải xong | Đủ năm khối đúng thứ tự, sáu thẻ đủ nội dung, không bị đẩy về `/login` |
| Error Case | Khách hoàn toàn chưa có phiên đăng nhập | Mở `/awards-information` | Trang hiện bình thường, không redirect, không thông báo lỗi (cố ý — F003 § 3 D001) |

---

## US008: Nhảy tới một hạng mục qua menu danh mục

**Type**: ui
**Interaction**: secondary-action
**Priority**: P1
**Owner F###**: F003

### User Story

As a khách truy cập, I want to bấm một mục trong menu danh mục để đi thẳng tới hạng mục mình quan tâm so that không phải cuộn hết một trang dài sáu khối, và luôn biết mình đang đọc hạng mục nào.

### Acceptance Criteria

- [x] Bấm một mục menu cuộn tới đúng thẻ tương ứng và đổi địa chỉ trang thành `#<slug>` mà không thêm bước lùi lịch sử.
- [x] Trong lúc cuộn tay, mục menu sáng luôn khớp hạng mục đang trong dải đo, và chỉ có đúng một mục sáng.
- [x] Vào thẳng `/awards-information#mvp` thì trang dừng ở thẻ MVP và mục MVP sáng sau khi hydrate (~290ms — F003 § 11 RISK-04).
- [ ] Bật chế độ giảm chuyển động thì cú nhảy là tức thì (đã code, chưa có test tự động — F003 § 11 RISK-05).

### Technical Notes

- **Endpoint**: N/A — client state only, không phát sinh HTTP request
- **Data Required**: `AWARDS` slug list; `--award-header-offset` (CSS custom property)
- **Dependencies**: bộ slug do F002 cố định (`lib/awards.ts`) — deep link từ trang chủ trỏ vào đúng bộ này

### Screens

- SCR003_AwardSystem: Hệ thống giải

### Background Logic

- Award category scroll-spy + click lock (client-side, xem `behavior-logic.md` § Client-Side Logic — không có mã BL###, không khớp canonical type nào)

### Test Scenarios

| Scenario | Given | When | Then |
|----------|-------|------|------|
| Happy Path | Khách đang ở đầu trang | Bấm mục menu "MVP" | Cuộn tới thẻ MVP, địa chỉ đổi thành `#mvp`, đúng một mục sáng |
| Error Case | Khách mở `/awards-information#khong-ton-tai` | Trang tải xong | Không cuộn, mục đầu tiên sáng, không có lỗi console |

---

## Screen → US Map

| Screen | US Codes |
|--------|----------|
| SCR001_Login | US001, US002, US003, US004 |
| SCR002_Homepage | US005, US006 |
| SCR003_AwardSystem | US007, US008 |

## Cross-Reference Validation

- [x] All US### codes are unique and globally contiguous (US001–US008)
- [x] All acceptance criteria are testable (each ties to an existing FR/AC in the source feature specs — none invented)
- [x] All US### codes are referenced in `docs/generated/feature-list.md` (F001, F002, F003)
- [x] All `ui` US### mapped to SCR001_Login, SCR002_Homepage hoặc SCR003_AwardSystem (cả ba đều có trong `docs/generated/screen-list.md`)
- [x] No `system`-typed US### in this project (no bg-job/hook stories — all eight are user-facing)
