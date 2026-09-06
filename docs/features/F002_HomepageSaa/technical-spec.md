---
status: implemented
fcode: F002
authored_by: takumi
created: 2026-09-05
lang: vi
---

# F002_HomepageSaa — Technical Spec

**Priority**: P0
**Type**: ui
**Generated**: 2026-09-05

**See also:** [`functional-spec.md`](./functional-spec.md) — plain-language overview, open decisions,
requirements/business rules stated in one-liners, screens, user stories, scenarios, edge cases, and
configuration for a BA/QA audience.

**How to read this file:** § 2 is the index — pick the action you care about and read its block in
§ 3 straight through. § 4 is the shared appendix — jump in only when a § 3 block points you there.

## 1. Technical Overview

Trang chủ công khai SAA 2025 tại `/`, thay thế trang boilerplate `create-next-app`. Server Component đọc cookie `NEXT_LOCALE` (tái dùng cơ chế của F001_Login) và phiên đăng nhập (nếu có) để render header/hero/nội dung tĩnh; countdown và hai menu header (thông báo, tài khoản) là tương tác phía client, không có round-trip HTTP mới. Bốn route placeholder (`/kudos`, `/standards`, `/profile`, `/admin`) dùng chung một `ComingSoon` component để không có liên kết gãy. *(cập nhật 2026-09-06: `/awards-information` đã rời nhóm placeholder — nay là màn hình thật của F003.)*

## 2. Action Index

| # | Action (handler) | Method · Path | Codes | Writes | Detail |
|---|---|---|---|---|---|
| **A0** | *cross-cutting — belongs to no single action* | — | FR-001, BR-001 | — | § 4.4 |
| **A1** | `HomePage#render` | `GET` `/` | FR-101, FR-102, FR-201, FR-202, FR-203, FR-204, FR-205, FR-206, FR-207, FR-401, FR-402, FR-405, DEC-001, US005 | — *(read-only)* | § 3.1 |
| **A2** | header notification/account menu *(client-only)* | *(client state — no HTTP)* | FR-403, FR-404, FR-601, BR-002, DEC-002, US006 | — *(client state only)* | § 3.1 |
| **A3** | `ComingSoon#render` | `GET` `/kudos`, `/standards`, `/profile`, `/admin` | FR-002, US005 | — *(read-only)* | § 3.1 |

## 3. Actions

### 3.1 CAP-01 — Xem và tương tác với trang chủ SAA 2025

#### A1 · Render trang chủ
`GET` `/` → `` `HomePage#render` ``
`FR-101` `FR-102` `FR-201` `FR-202` `FR-203` `FR-204` `FR-205` `FR-206` `FR-207` `FR-401` `FR-402` `FR-405` `DEC-001` `US005` · `SCR002_Homepage`

**Who** · Khách truy cập (đã đăng nhập hay chưa đều xem được)
**FE** · Server Component render 7 khối theo thứ tự thiết kế: header (logo, 3 mục nav, bộ chọn ngôn ngữ tái dùng F001_Login), hero (keyvisual "ROOT FURTHER", nhãn "Coming soon", 3 ô đếm ngược DAYS/HOURS/MINUTES, thông tin sự kiện, 2 CTA), khối nội dung "Root Further", lưới 6 thẻ giải thưởng, khối quảng bá Sun* Kudos, nút widget nổi, footer. Bộ đếm ngược là Client Component con (`CountdownTimer`): server render ô `00` placeholder, client tự tính lại trong `useEffect` sau mount (tránh lệch giờ server/client, không cần `suppressHydrationWarning`). `getPageContext()` (`app/_page-context.ts:27-41`) là điểm đọc locale + session duy nhất; chỉ hai boolean `isAuthenticated`/`isAdmin` được truyền sang `HomeHeader` (Client Component) — object `user` của Supabase không bao giờ qua ranh giới đó.
**Request** · không có tham số — trang tĩnh, không dùng `searchParams`/`cookies()` ngoài cookie ngôn ngữ đã có ở F001_Login.
**BE** · không có — thuần render phía server, nội dung giải thưởng/Kudos là dữ liệu tĩnh lấy từ thiết kế (mock data source theo clarifications.md, không phải bảng DB — 6 hạng mục hằng cứng trong `lib/awards.ts:27-42`).
**Rule** · Quyết định cuộn lên đầu hay điều hướng khi bấm mục nav:

| DEC | subtype | Condition | What the user sees | Source |
|---|---|---|---|---|
| **DEC-001** | interaction | `navItem.isSelected` (mục "About SAA 2025" đang ở trang chủ) | Bấm mục đang chọn → cuộn mượt lên đầu trang thay vì điều hướng lại | `app/_components/home-nav.tsx:57-71`, `use-scroll-to-top-if-current.ts:18-21` |

**BR-001 — Trang chủ luôn công khai, không có guard mới.** `proxy.ts` hiện có (route guard của F001_Login) tiếp tục cho qua nguyên trạng route `/` — không có logic mới ở action này. *(§ 4.4)*
**BR-003 — Bộ đếm ngược tick mỗi giây từ đồng hồ hệ thống (`Date.now()`), tự sửa lỗi lệch giờ (self-correcting), giữ nguyên `00` và ẩn "Coming soon" khi đã qua thời điểm sự kiện.** Tính từ `NEXT_PUBLIC_EVENT_START_AT` qua `ALG-001` — {tick mỗi giây, so sánh với thời điểm hiện tại, ẩn nhãn khi hiệu số ≤ 0} *(§ 4.5)*
**BR-004 — Giá trị cấu hình thời gian sự kiện không hợp lệ (thiếu hoặc sai định dạng ISO-8601) thì hiện `00/00/00`, ẩn "Coming soon", ghi một dòng cảnh báo console, không bao giờ throw.** Bắt lỗi parse ngay ở `ALG-001`. *(§ 4.5)*
**Result** · Chỉ render — không ghi dữ liệu. Bấm thẻ giải thưởng điều hướng `/awards-information#<slug>` (FR-405, mapping tĩnh 1-1 theo 6 hạng mục, không phải một quyết định rẽ nhánh). Bấm CTA/widget/footer điều hướng tới route tương ứng (FR-206, FR-207) — không có `DISC-###` nào chi phối màn hình này.
**Source:** `app/page.tsx:24-48`, `app/_components/home-hero.tsx`, `app/_components/awards-grid.tsx`, `app/_components/award-card.tsx`

<!-- Không cần sequence diagram: dưới ngưỡng — read-only, không ghi ≥2 bảng, không phải background/async action. -->

---

#### A2 · Chuông thông báo và menu tài khoản *(client-only)*
*(client state — no HTTP)* → header notification/account menu
`FR-403` `FR-404` `FR-601` `BR-002` `DEC-002` `US006`

**Who** · Người dùng đã đăng nhập (không hiện với khách chưa đăng nhập)
**FE** · Chuông thông báo (`NotificationBell`, Client Component) toggle một panel hiển thị "Không có thông báo mới" khi bấm; biểu tượng tài khoản (`AccountMenu`, Client Component) toggle một menu Profile / Sign out / Admin Dashboard (điều kiện). Cả hai đều là state cục bộ (`useState`), không gọi API, và dùng chung hook `useDismissOnOutside` (outside-pointerdown đóng không trả focus; Escape đóng và trả focus về trigger).
**Request** · không có — không có HTTP request nào phát sinh từ hai tương tác này.
**BE** · không có — Sign out gọi lại server action đăng xuất hiện có của F001_Login (`app/_actions/auth.ts`), không phải logic mới của action này.
**Rule** · Quyết định hiện mục Admin Dashboard:

| DEC | subtype | Condition | What the user sees | Source |
|---|---|---|---|---|
| **DEC-002** | render | `isAdmin` (`user.app_metadata.role === "admin"`, tính ở `app/_page-context.ts:40`) | Thêm mục "Admin Dashboard" (`href="/admin"`) vào cuối menu tài khoản | `app/_components/account-menu.tsx:99-107` |

**BR-002 — Chuông thông báo và biểu tượng tài khoản chỉ render khi có phiên đăng nhập hợp lệ.** Không có state ẩn/hiện dựa trên props — hai phần tử này hoàn toàn không có trong cây component khi `isAuthenticated` là `false` (`app/_components/home-header.tsx:66,75-81`). *(§ 4.4)*
**Result** · Chỉ toggle state cục bộ — không ghi dữ liệu, không gọi API. Không có huy hiệu chưa đọc trên chuông vì chưa có nguồn dữ liệu thông báo (RISK-01 ở functional-spec.md § 11). Bấm Sign out gọi lại action đăng xuất có sẵn (F001_Login) — điều hướng về `/login`, không thuộc phạm vi action này.
**Source:** `app/_components/notification-bell.tsx`, `app/_components/account-menu.tsx`, `app/_components/use-dismiss-on-outside.ts`

<!-- Không cần sequence diagram: hai toggle state cục bộ, không ghi bảng, không phải background action. -->

---

#### A3 · Render route placeholder
`GET` `/kudos` \| `/standards` \| `/profile` \| `/admin` → `` `ComingSoon#render` ``
`FR-002` `US005`

**Who** · Bất kỳ ai điều hướng ra từ trang chủ (nav, CTA, thẻ giải thưởng, widget, footer, mục "Admin Dashboard" role-gated)
**FE** · Một component `ComingSoon` (`app/_components/coming-soon.tsx`) dùng chung cho cả 4 route, tái dùng `HomeHeader`/`SiteFooter` thật (không phải trang tĩnh cô lập) để giữ trải nghiệm điều hướng nhất quán — kể cả bộ chọn ngôn ngữ và (nếu đã đăng nhập) chuông/tài khoản.
**Request** · không có tham số.
**BE** · không có — render tĩnh, không có nội dung thật (ngoài phạm vi tính năng này — xem functional-spec.md § 1 Non-Scope). `/admin` không có kiểm tra role phía server (chỉ gating hiển thị ở menu, FR-601) — xác nhận đúng thiết kế vì màn hình đích chưa có nội dung cần bảo vệ (`app/admin/page.tsx:7-15`, `docs/system/permissions.md` § Reconciliation Note).
**Rule** · Không có decision logic — 4 route này là shell placeholder theo tuyên bố (`clarifications.md` ORCH-11), không mô phỏng hành vi màn hình đích thật. *(cập nhật 2026-09-06: `/awards-information` đã rời nhóm placeholder — nay là màn hình thật của F003.)*
**Result** · Chỉ render — không ghi dữ liệu.
**Source:** `app/_components/coming-soon.tsx`, `app/kudos/page.tsx`, `app/standards/page.tsx`, `app/profile/page.tsx`, `app/admin/page.tsx`

<!-- Không cần sequence diagram: read-only, một hop, không phải background action. -->

### 3.2 Edge cases

| Action | Scenario | Behavior |
|---|---|---|
| A1 | Biến `NEXT_PUBLIC_EVENT_START_AT` thiếu hoặc sai định dạng | `ALG-001` bắt lỗi parse, hiện `00/00/00`, ẩn "Coming soon", ghi cảnh báo console, không throw (BR-004) |
| A1 | Thời điểm sự kiện đã qua khi tải trang | Bộ đếm giữ `00` ở cả 3 ô, "Coming soon" ẩn, không có cờ lỗi (BR-003) |
| A2 | Người dùng chưa đăng nhập | Chuông thông báo và biểu tượng tài khoản không render trong DOM (BR-002) |
| A2 | Người dùng đã đăng nhập nhưng không phải admin | Mục Admin Dashboard không hiện trong menu (DEC-002); route đích vẫn là `A3` công khai — chưa có nội dung thật cần bảo vệ |
| A3 | Người dùng bấm liên kết ra khỏi trang chủ (nav/CTA/thẻ/widget/footer/menu tài khoản) | Luôn tới một route thật — `/awards-information` (màn hình F003) hoặc một trong 4 shell `ComingSoon` — không có liên kết 404 (test ID-59) |

## 4. Shared Foundation

### 4.1 Components

| Component | Responsibility | Used in | File |
|---|---|---|---|
| `HomeHeader` | Logo, `HomeNav`, chuông + tài khoản (điều kiện), bộ chọn ngôn ngữ (tái dùng) | A1, A2, A3 | `app/_components/home-header.tsx` |
| `HomeNav` | 3 mục nav, item đang chọn cuộn lên đầu thay vì điều hướng lại (DEC-001) | A1 | `app/_components/home-nav.tsx` |
| `LanguageSelector` (reused từ F001_Login, đã promote) | Dropdown chọn ngôn ngữ VN/EN | A1, A3 | `app/_components/language-selector.tsx` (di chuyển khỏi `app/login/_components/`) |
| `HomeHero` | Keyvisual, wordmark, `CountdownTimer`, thông tin sự kiện, 2 CTA | A1 | `app/_components/home-hero.tsx` |
| `CountdownTimer` | Tick mỗi giây, tính từ `NEXT_PUBLIC_EVENT_START_AT` qua `ALG-001` | A1 | `app/_components/countdown-timer.tsx` |
| `RootFurtherBlock` | Watermark ROOT/FURTHER + đoạn giới thiệu chủ đề | A1 | `app/_components/root-further-block.tsx` |
| `AwardsGrid` / `AwardCard` | Lưới 6 thẻ giải thưởng, responsive 3/2 cột (1 link/thẻ, FR-405) | A1 | `app/_components/awards-grid.tsx`, `app/_components/award-card.tsx` |
| `KudosPromo` | Khối quảng bá Sun* Kudos | A1 | `app/_components/kudos-promo.tsx` |
| `FloatingWidget` | Nút nổi 2 link (viết Kudos / thể lệ) | A1 | `app/_components/floating-widget.tsx` |
| `SiteFooter` | Footer 4 liên kết + bản quyền | A1, A3 | `app/_components/site-footer.tsx` |
| `NotificationBell` | Toggle panel "Không có thông báo mới" | A2 | `app/_components/notification-bell.tsx` |
| `AccountMenu` | Toggle menu Profile / Sign out / Admin Dashboard (điều kiện) | A2 | `app/_components/account-menu.tsx` |
| `useDismissOnOutside` | Outside-pointerdown + Escape dismissal dùng chung cho `NotificationBell`/`AccountMenu` | A2 | `app/_components/use-dismiss-on-outside.ts` |
| `ComingSoon` | Shell placeholder dùng chung cho 4 route đích | A3 | `app/_components/coming-soon.tsx` |
| `getPageContext` | Điểm đọc locale + session (`isAuthenticated`/`isAdmin`) dùng chung cho A1/A3 | A1, A3 | `app/_page-context.ts` |

### 4.2 Data Model

#### Key Entities

| Entity | Table | Key Columns | Purpose |
|--------|-------|-------------|---------|
| Supabase Auth User *(tái dùng từ F001_Login, không thuộc migration của tính năng này)* | `auth.users` *(do Supabase quản lý)* | `app_metadata.role` | Nguồn `role` để gating mục Admin Dashboard (A2, DEC-002) |

Nội dung giải thưởng/Kudos/hero là dữ liệu tĩnh lấy từ thiết kế (mock data source, theo clarifications.md — không phải bảng DB, không có entity riêng).

#### Polymorphic Behavior

N/A — no discriminator fields in Key Entities.

### 4.3 State Management

None. *(Toggle mở/đóng của panel thông báo và menu tài khoản là state cục bộ 2 trạng thái/1 transition mỗi cái — dưới ngưỡng `kind: ui` yêu cầu ≥3 state HOẶC ≥2 transition, nên không tách thành SM-### riêng.)*

### 4.4 Shared Rules

#### Bin 3 — cross-cutting, belongs to no single action

**A0 · FR-001 / BR-001 — Trang chủ (`/`) không có guard mới.** `proxy.ts` (route guard hiện có của F001_Login, xem `docs/features/F001_Login/technical-spec.md § 4.4`) tiếp tục cho qua route `/` nguyên trạng — không có middleware/before-action riêng cho tính năng này.
**Source:** `proxy.ts:41-46` · route guard đã cite ở F001_Login § 4.4

### 4.5 Algorithms & Integrations

### Tính toán bộ đếm ngược sự kiện (ALG-001)
**Linked FR:** FR-401
**Used in:** A1
**Source:** `app/_components/countdown-timer.tsx:43-63,77-95`
**Input:** `NEXT_PUBLIC_EVENT_START_AT` (chuỗi ISO-8601) · thời điểm hiện tại (`Date.now()`, tick mỗi giây) · **Output:** `{days, hours, minutes}` đã pad `00`, hoặc cờ "đã qua sự kiện" · **Complexity:** O(1) mỗi tick
**Description:** Parse biến cấu hình thành `Date`; nếu parse thất bại hoặc thiếu, dùng nhánh lỗi (BR-004). Mỗi giây tính lại hiệu số giữa thời điểm sự kiện và `Date.now()` (không cộng dồn từ tick trước — tự sửa lỗi lệch giờ do tab bị treo/throttle). Hiệu số ≤ 0 → giữ `00` ở cả 3 ô và trả cờ ẩn "Coming soon" (BR-003).

**Pseudocode:**
```text
target = parseISO8601(env.NEXT_PUBLIC_EVENT_START_AT)
if (parse failed or env missing):
  log.warn("invalid NEXT_PUBLIC_EVENT_START_AT")
  return { days: "00", hours: "00", minutes: "00", isPast: true, hideComingSoon: true }

every 1s:
  diffMs = target.getTime() - Date.now()
  if diffMs <= 0:
    return { days: "00", hours: "00", minutes: "00", isPast: true, hideComingSoon: true }
  return { days: pad(diffMs / 1d), hours: pad(diffMs % 1d / 1h), minutes: pad(diffMs % 1h / 1min), isPast: false, hideComingSoon: false }
```

### 4.6 Configuration

```text
NEXT_PUBLIC_EVENT_START_AT = 2025-12-26T18:30:00+07:00   # thời điểm sự kiện SAA 2025 (ISO-8601), đọc bởi ALG-001 (A1)
```

**Client behavior:** tính năng này không có debounce/optimistic UI/polling/upload/realtime pattern — countdown tick bằng `setInterval` đơn giản, không phải polling API. Cổng chạy thời gian chạy là role-gate (`app_metadata.role`, A2) — xem `permissions.md`. Route guard tái dùng của F001_Login — xem `architecture.md`.

## 5. Verification & Technical Notes

### 5.1 Technical Verification

- **SC-001** *(A1)* Tải `/` khi thời điểm sự kiện chưa tới → 3 ô đếm ngược hiện giá trị khác `00` và tick mỗi giây (covers FR-401)
- **SC-002** *(A1)* Tải `/` với `NEXT_PUBLIC_EVENT_START_AT` sai định dạng → hiện `00/00/00`, ẩn "Coming soon", không có lỗi hiển thị (covers FR-402)
- **SC-003** *(A2)* Đăng nhập rồi tải `/` → chuông thông báo và biểu tượng tài khoản hiện; đăng xuất rồi tải lại → cả hai biến mất (covers FR-403, FR-404)
- **SC-004** *(A2)* Đăng nhập với tài khoản role admin → menu tài khoản có thêm Admin Dashboard; tài khoản thường → không có mục đó (covers FR-404, FR-601)
- **SC-005** *(A1)* Bấm từng thẻ trong 6 thẻ giải thưởng → điều hướng đúng `/awards-information#<slug>` tương ứng (covers FR-405)
- **SC-006** *(A3)* Tải cả 4 route placeholder → không có lỗi 404, mỗi route render `ComingSoon` với header/footer thật (covers FR-002)

#### US005_BrowseHomepage *(A1, A3)*

**Independent Test:** Tải `/` không cần đăng nhập, xác nhận đủ 7 khối theo đúng thứ tự và mọi liên kết dẫn tới một route thật (kể cả 5 placeholder).

**Acceptance Scenarios:**

1. **Given** khách chưa đăng nhập truy cập `/`, **When** trang tải xong, **Then** đủ 7 khối hiển thị đúng thứ tự, bộ đếm ngược đang tick.
2. **Given** khách bấm một thẻ giải thưởng, **When** điều hướng hoàn tất, **Then** URL đích là `/awards-information#<slug>` đúng với hạng mục đã bấm.

#### US006_AccountNotificationMenu *(A2)*

**Independent Test:** Seed session hợp lệ trực tiếp vào Supabase local (cùng cách F001_Login đã làm), gán `app_metadata.role` để kiểm cả hai nhánh admin/không-admin.

**Acceptance Scenarios:**

1. **Given** người dùng đã đăng nhập không có role admin, **When** bấm biểu tượng tài khoản, **Then** menu hiện Profile và Sign out, không có Admin Dashboard.
2. **Given** người dùng đã đăng nhập có role admin, **When** bấm biểu tượng tài khoản, **Then** menu hiện thêm mục Admin Dashboard.

### 5.2 Assumptions

- *(A1)* Nội dung giải thưởng/Kudos/hero là dữ liệu tĩnh biên soạn từ thiết kế MoMorph, đặt trong `lib/awards.ts` (identity: slug/key/image) + dictionary `lib/i18n/messages/*-home.ts` (copy) — không có API/bảng DB thật đứng sau; nếu sau này cần dữ liệu động, đây là một tính năng khác.
- *(A2)* Role admin đọc từ `app_metadata.role` (`app/_page-context.ts:40`) vì Supabase local chưa có bảng role riêng — nếu dự án sau này thêm bảng phân quyền, action này cần đọc lại nguồn khác. `/admin` không có kiểm tra role phía server (chỉ gating hiển thị menu) — xem A3.
- *(A3)* `ComingSoon` là shell thật (không phải stub) — mọi assertion trên trang chủ chạy trên code thật của A1/A2, không phụ thuộc vào nội dung của A3. *(cập nhật 2026-09-06: `/awards-information` đã rời nhóm placeholder — nay là màn hình thật của F003.)*

### 5.3 Unresolved Questions

Không còn câu hỏi treo cho các action đã lên code (A1-A3) — tên file/component đã chốt như liệt kê ở § 4.1. Câu hỏi thật sự còn mở: nguồn dữ liệu tĩnh cho 6 thẻ giải thưởng/Kudos đã chốt là hằng số TypeScript (`lib/awards.ts` + dictionary), không phải file JSON riêng — không còn là quyết định treo.

### 5.4 Source References

| Action | File | Lines |
|---|---|---|
| A1 | `app/page.tsx` | 24-48 |
| A1 | `app/_page-context.ts` | 27-41 |
| A1 | `app/_components/{home-header,home-nav,home-hero,countdown-timer,root-further-block,awards-grid,award-card,kudos-promo,floating-widget,site-footer}.tsx` | toàn file |
| A1 | `lib/awards.ts` | 27-42 |
| A2 | `app/_components/{notification-bell,account-menu,use-dismiss-on-outside}.ts(x)` | toàn file |
| A3 | `app/_components/coming-soon.tsx`, `app/{kudos,standards,profile,admin}/page.tsx` | toàn file |

#### Data Flow

N/A — không có luồng dữ liệu ghi; A1/A3 chỉ render, A2 chỉ toggle state cục bộ (xem § 4.2, § 4.3).

### 5.5 Artifact References

| Artifact | File | Codes Used | Reviewed |
|----------|------|------------|----------|
| Feature List | [feature-list.md](../../generated/feature-list.md) | F002 | [x] |
| Architecture | [architecture.md](../../system/architecture.md) | — (narrative, no per-code cite) | [x] |
| Permissions | [permissions.md](../../system/permissions.md) | — (narrative, no per-code cite) | [x] |
| Screens | [functional-spec.md § 6](./functional-spec.md#6-screens) | SCR002_Homepage | [x] |
