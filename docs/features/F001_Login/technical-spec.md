---
status: implemented
fcode: F001
authored_by: takumi
created: 2026-09-04
lang: vi
---

# F001_Login

## 1. Technical Overview

Đăng nhập cho SAA 2025 dùng Google OAuth qua Supabase Auth (local stack). Khách chưa xác thực vào `/login`, bấm "LOGIN With Google", được chuyển hướng ra Google, quay lại qua `/auth/callback`, rồi vào `/todo`. `proxy.ts` (đã có `updateSession`) nhận thêm việc gác cổng route theo trạng thái đăng nhập. Ngôn ngữ hiển thị (VN/EN) lưu qua cookie `NEXT_LOCALE`, không dùng thư viện i18n.

## 2. Action Index

| # | Action (handler) | Method · Path | Codes | Writes | Detail |
|---|---|---|---|---|---|
| **A0** | *cross-cutting — route guard + session refresh* | — | FR-101, FR-102, FR-602, BR-002 | — | § 4.4 |
| **A1** | `LoginPage#render` | `GET` `/login` | FR-201, FR-202, FR-203, DEC-001, US001, US003 | — *(read-only)* | § 3.1 |
| **A2** | `signInWithGoogle` | Server Action · `/login` | FR-202, FR-601, BR-001, US001, SM-001 | — *(external redirect, no local write)* | § 3.1 |
| **A3** | `GET /auth/callback` | `GET` `/auth/callback` | FR-401, FR-402, DEC-002, US001, SM-001 | — *(session held by Supabase Auth, not an app-owned table)* | § 3.1 |
| **A4** | `setLocale` | Server Action · `/login` | FR-203, BR-003, US003 | — *(cookie only, plus `revalidatePath("/", "layout")`)* | § 3.2 |
| **A5** | `TodoPage#render` | `GET` `/todo` | US004 | — *(read-only)* | § 3.3 |
| **A6** | `signOut` | Server Action · `/todo` | FR-403, US004 | — *(session cleared, not an app-owned table)* | § 3.3 |

## 3. Actions

### 3.1 CAP-01 — Đăng nhập bằng Google

#### A1 · Hiển thị màn hình Login
`GET` `/login` → `` `LoginPage#render` ``
`FR-201` `FR-202` `FR-203` `DEC-001` `US001` `US003` · `SCR001_Login`

**Who** · Khách truy cập chưa đăng nhập
**FE** · Server Component (`app/login/page.tsx`) đọc cookie `NEXT_LOCALE` để chọn từ điển VN/EN qua `resolveLocale`, đọc `searchParams.error` (`PageProps<"/login">`, có thể là string hoặc string[]) để quyết định `hasError`, render `HeroBackground` + `LoginHeader` (logo + bộ chọn ngôn ngữ) + `LoginContent` (wordmark, mô tả, banner lỗi điều kiện, nút "LOGIN With Google") + `LoginFooter`.
**Request** · query `error` *(tuỳ chọn — chỉ có khi quay về từ Google với lỗi)*
**BE** · không có — thuần render phía server, không gọi service riêng.
**Rule** · Quyết định hiện banner lỗi khi có tham số `error`:

| DEC | subtype | Condition | What the user sees | Source |
|---|---|---|---|---|
| **DEC-001** | render | `searchParams.error` tồn tại (string không rỗng hoặc mảng không rỗng) | Hiện `ErrorBanner` "Đăng nhập không thành công. Vui lòng thử lại." phía trên nút đăng nhập | `app/login/page.tsx:40-43` |

**Result** · Chỉ render — không ghi dữ liệu. Không có `DISC-###` nào chi phối màn hình này.
**Source:** `app/login/page.tsx:31-59`

<!-- Không cần sequence diagram: dưới ngưỡng — read-only, một hop, đồng bộ. -->

---

#### A2 · Bấm "LOGIN With Google"
Server Action · `/login` → `` `signInWithGoogle` ``
`FR-202` `FR-601` `BR-001` `US001` · `SM-001` · `INT-001`

**Who** · Khách truy cập chưa đăng nhập
**FE** · `GoogleSignInButton` (Client Component, `useFormStatus`) submit Server Action bên trong `<form action={signInWithGoogle}>`; ngay khi bấm, nút chuyển sang `disabled` + hiện loader (SM-001: `idle` → `loading`).
**Request** · không có tham số — hành động không nhận input từ người dùng.
**BE** · `` `signInWithGoogle` `` báo lỗi ngay (throw) nếu thiếu `NEXT_PUBLIC_SITE_URL` (fail-fast, tránh redirectTo `undefined/auth/callback`); ngược lại gọi `supabase.auth.signInWithOAuth({ provider: 'google', options: { redirectTo: '{NEXT_PUBLIC_SITE_URL}/auth/callback' } })`. Nếu có `error` hoặc thiếu `data.url`, redirect về `/login?error=oauth_failed` thay vì crash; ngược lại `redirect(data.url)` ra ngoài ứng dụng.
**Rule** · **BR-001 — Mọi tài khoản Google hợp lệ đều được phép đăng nhập, không áp dụng domain allow-list.** Không có bước kiểm tra domain nào được thêm trước hay sau khi gọi `signInWithOAuth`.
**Result** · Không ghi dữ liệu cục bộ — trình duyệt được chuyển hướng toàn trang sang trang xác thực của Google qua `INT-001` (Supabase Auth phát hành URL authorize) *(§ 4.5)*, hoặc về `/login?error=oauth_failed` nếu bước phát hành URL thất bại.
**State** · `SM-001`: `idle` → `loading` *(§ 4.3)*
**Source:** `app/login/actions.ts:16-35`

<!-- Không cần sequence diagram: một action, redirect ra ngoài, không ghi ≥2 bảng. -->

---

#### A3 · Xử lý callback OAuth *(background, no FE)*
`GET` `/auth/callback` → `` `GET /auth/callback` ``
`FR-401` `FR-402` `DEC-002` `US001` · `SM-001` · `INT-001`

**Who** · *không có thao tác trực tiếp — do Google chuyển hướng về sau khi người dùng xác nhận hoặc huỷ ở màn hình của Google*
**FE** · *không có* — route handler thuần phía server.
**Request** · query `code` *(thành công)*, `error` *(thất bại/huỷ)*, `next` *(tuỳ chọn — đích chuyển hướng sau khi thành công, mặc định `/todo`)*
**BE** · Đọc `request.nextUrl.searchParams`. Origin dùng để build mọi redirect luôn lấy từ `NEXT_PUBLIC_SITE_URL` (`resolveSiteOrigin()`), **không bao giờ** từ `request.nextUrl.origin`/header `Host` — hai lý do bảo mật ghi rõ trong code: (1) Next 16 viết lại hostname loopback (`127.0.0.1`) thành `"localhost"` trong `NextURL`, làm lệch cookie session đã pin vào `127.0.0.1`; (2) `Host`/`x-forwarded-host` do client kiểm soát, dùng trực tiếp là open-redirect (CWE-644). Có `error` → bỏ qua exchange, redirect thẳng lỗi. Có `code` → gọi `supabase.auth.exchangeCodeForSession(code)` trong `try/catch` (lỗi mạng throw thay vì trả `error`, nên phải bọc để không lộ 500 thô). `next` được resolve qua `resolveNextPath()` — parse lại bằng `new URL(next, origin)` và so khớp `origin` để chặn URL tuyệt đối, `//evil.com`, và biến thể backslash.
**Rule** · Quyết định điều hướng theo kết quả OAuth:

| DEC | subtype | Condition | What the user sees | Source |
|---|---|---|---|---|
| **DEC-002** | flow | `code` tồn tại và exchange thành công | Điều hướng tới `next` (mặc định `/todo`) | `app/auth/callback/route.ts:87-100` |
| **DEC-002** | flow | `error` tồn tại, hoặc thiếu cả `code`/`error`, hoặc exchange thất bại (kể cả throw) | Điều hướng về `/login?error=oauth_failed` (mã lỗi cố định, không phản chiếu lỗi thô của Google) | `app/auth/callback/route.ts:74-107` |

**Result** · Không ghi bảng do ứng dụng sở hữu — phiên đăng nhập do Supabase Auth quản lý nội bộ. Nhánh thành công: redirect `next`. Nhánh thất bại: redirect `/login?error=oauth_failed`, khiến A1 render lại với `DEC-001` bật, đồng thời đưa nút đăng nhập về trạng thái sẵn sàng.
**State** · `SM-001`: `loading` → `idle` *(chỉ ở nhánh thất bại)* *(§ 4.3)*
**Source:** `app/auth/callback/route.ts:74-107`

<!-- Không cần sequence diagram: hai nhánh nhưng chỉ một bảng DEC, không ghi ≥2 bảng, không phải background job dạng queue/cron. -->

### 3.2 CAP-02 — Kiểm soát truy cập theo trạng thái đăng nhập

Toàn bộ hành vi của capability này nằm ở hàng cross-cutting **A0** trong § 2 — không có action riêng nào khác. Chi tiết đầy đủ (rule + source) ở **§ 4.4, Bin 3** bên dưới.

### 3.3 CAP-03 — Chọn ngôn ngữ hiển thị

#### A4 · Đổi ngôn ngữ VN/EN
Server Action · `/login` → `` `setLocale` ``
`FR-203` `BR-003` `US003`

**Who** · Khách truy cập
**FE** · `LanguageSelector` (Client Component, đã promote lên `app/_components/`, dùng chung với F002) submit `setLocale(value)` trong `startTransition` khi chọn một option khác locale hiện tại.
**Request** · `locale` = `vi` \| `en` (chuỗi bất kỳ khác cũng được chấp nhận làm tham số — xử lý ở BE)
**BE** · `` `setLocale` `` chuẩn hoá input qua `resolveLocale()` (giá trị lạ/rỗng rơi về `DEFAULT_LOCALE`, không ghi thẳng input người dùng vào cookie), ghi cookie `NEXT_LOCALE` qua `cookieStore.set(..., { path: "/", maxAge: 1 năm, sameSite: "lax" })`, rồi gọi **`revalidatePath("/", "layout")`** — bắt buộc, không phải tự động: action này giờ dùng chung cho cả `/login` và `/` (F002), nên phạm vi revalidate phải phủ toàn bộ layout, không chỉ `/login`.
**Rule** · **BR-003 — Khi chưa có cookie `NEXT_LOCALE`, ngôn ngữ mặc định là `vi` (VN).** Sau khi người dùng chọn, giá trị đã chọn ghi đè mặc định ở các lần render sau.
**Result** · Ghi cookie `NEXT_LOCALE` ← giá trị đã chuẩn hoá, cộng một lời gọi `revalidatePath("/", "layout")` tường minh để mọi route render theo ngôn ngữ mới ngay, không đợi tới lần điều hướng kế tiếp.
**Source:** `app/_actions/locale.ts:13-27`

### 3.4 CAP-04 — Đăng xuất

#### A5 · Hiển thị trang /todo (placeholder)
`GET` `/todo` → `` `TodoPage#render` ``
`US004`

**Who** · Người dùng đã đăng nhập
**FE** · Trang placeholder tối thiểu (`app/todo/page.tsx`), cố ý không có style, với một điều khiển đăng xuất, chỉ để chứng minh luồng `logout → /login`; không thuộc phạm vi tính năng to-do thật. `proxy.ts` đã guard route này — trang chỉ gọi lại `getUser()` để hiển thị email đã đăng nhập, không dùng để tái xác thực (một nguồn thẩm quyền duy nhất).
**Request** · không có
**BE** · không có
**Result** · Chỉ render — không ghi dữ liệu.
**Source:** `app/todo/page.tsx:18-48`

---

#### A6 · Đăng xuất
Server Action · `/todo` → `` `signOut` ``
`FR-403` `US004`

**Who** · Người dùng đã đăng nhập
**FE** · Điều khiển đăng xuất trên `/todo` submit Server Action; cũng được F002 tái dùng cho mục "Sign out" trong menu tài khoản trên `/` (xem `docs/flows/sign-out.md`).
**Request** · không có
**BE** · `` `signOut` `` gọi `supabase.auth.signOut()` **không truyền `options`** — GoTrue áp dụng default của chính SDK, `{ scope: 'global' }` (`node_modules/@supabase/auth-js/dist/module/GoTrueClient.js:3402`), nên đây là sign-out toàn bộ thiết bị/phiên, không chỉ phiên hiện tại. Lỗi `{ error }` trả về bị bỏ qua có chủ đích — một phiên đã hết hạn vẫn phải về `/login` thay vì kẹt ở màn hình lỗi.
**Result** · Không ghi bảng do ứng dụng sở hữu — phiên bị Supabase Auth thu hồi (global scope). Điều hướng về `/login`.
**Source:** `app/_actions/auth.ts:17-21`

### 3.5 Edge cases

| Action | Scenario | Behavior |
|---|---|---|
| A2 | Người dùng huỷ ở màn hình consent Google | A3 nhận `error`, điều hướng `/login?error=oauth_failed`, A1 hiện DEC-001 |
| A2 | Bấm nút đăng nhập nhiều lần liên tiếp trong lúc đang xử lý | Nút đã ở trạng thái disabled (SM-001: loading) nên không gửi thêm yêu cầu OAuth thứ hai |
| A0 | Người dùng đã đăng nhập cố truy cập `/login` trực tiếp (dán URL) | A0 chặn trước khi A1 render, điều hướng `/todo` |
| A0 | Người dùng chưa đăng nhập cố truy cập `/todo` trực tiếp | A0 chặn trước khi A5 render, điều hướng `/login` |
| A1-A6 | Request tới URL ngoài `/login`, `/auth/callback`, `/todo` | Ngoài phạm vi tính năng này — không có hành vi định nghĩa ở đây |

## 4. Shared Foundation

### 4.1 Components

| Component | Responsibility | Used in | File |
|---|---|---|---|
| `LoginPage` | Render màn hình đăng nhập, đọc cookie ngôn ngữ + query lỗi | A1 | `app/login/page.tsx` |
| `HeroBackground` | Lớp nền hero full-bleed (fallback màu đặc, chờ export `hero.png` — RISK-01) | A1 | `app/login/_components/hero-background.tsx` |
| `LoginHeader` / `LoginContent` / `LoginFooter` | 3 vùng còn lại của màn hình (logo+selector / wordmark+form+banner lỗi / copyright) | A1 | `app/login/_components/{login-header,login-content,login-footer}.tsx` |
| `GoogleSignInButton` | Client Component quản lý trạng thái loading/disabled của nút (`useFormStatus`) | A2 | `app/login/_components/google-sign-in-button.tsx` |
| `ErrorBanner` | Banner lỗi `role="alert"` khi `hasError` (DEC-001) | A1 | `app/login/_components/error-banner.tsx` |
| `LanguageSelector` (đã promote — dùng chung với F002) | Dropdown chọn ngôn ngữ, submit `setLocale` | A1, A4 | `app/_components/language-selector.tsx` |
| `TodoPage` | Placeholder trang đích sau đăng nhập | A5, A6 | `app/todo/page.tsx` |

### 4.2 Data Model

```mermaid
erDiagram
    AUTH_USER {
        string id
        string email
        string raw_user_meta_data
    }
```

| Entity | Table | Used for | Action |
|---|---|---|---|
| Supabase Auth User | `auth.users` *(do Supabase quản lý, không thuộc migration của tính năng này)* | Nguồn thông tin người dùng sau khi xác thực Google | A2, A3, A5, A6 |

#### Polymorphic Behavior

N/A — no discriminator fields in Key Entities.

### 4.3 State Management

### Trạng thái nút đăng nhập Google (SM-001)
**kind:** ui
**Linked FR:** FR-202
**Source:** `app/login/_components/google-sign-in-button.tsx:17-18` (`useFormStatus().pending`)

```mermaid
stateDiagram-v2
    [*] --> idle
    idle --> loading : A2 bấm nút
    loading --> idle : A3 nhánh thất bại (redirect kèm error)
```

**Action transitions:** guard + hiệu ứng phụ của mỗi cạnh nằm ở rung **Result** của action tương ứng (A2 cho `idle → loading`, A3 cho `loading → idle`) — không lặp lại ở đây.

### 4.4 Shared Rules

#### Bin 3 — cross-cutting, belongs to no single action

**A0 · FR-101 / FR-102 / FR-602 / BR-002 — Điều hướng theo trạng thái đăng nhập áp dụng cho mọi request, không riêng một action nào.**
`proxy.ts` (mở rộng từ `updateSession` hiện có) kiểm tra: (1) request tới `/todo` mà không có session hợp lệ → redirect `/login`; (2) request tới `/login` mà đã có session hợp lệ → redirect `/todo`. Áp dụng cho toàn bộ route khớp `matcher` hiện tại của `proxy.ts`, không riêng A1 hay A5.
**Source:** `proxy.ts:41-46`

### 4.5 Algorithms & Integrations

### Google OAuth qua Supabase Auth (INT-001)
**Linked FR:** FR-202
**Used in:** A2 → A3
**Source:** `app/login/actions.ts:16-34`, `app/auth/callback/route.ts:74-107`
**Type:** api-call
**Target:** Supabase Auth local (`{SUPABASE_URL}/auth/v1/authorize?provider=google`) → màn hình consent của Google → `/auth/callback`
**Payload:** `provider=google`, `redirectTo={origin}/auth/callback`
**Failure handling:** Google trả `error` qua query khi người dùng từ chối/huỷ; A3 không tự thử lại, chỉ điều hướng về `/login?error=oauth_failed` để A1 hiện thông báo cố định.

### 4.6 Configuration

```text
SUPABASE_AUTH_EXTERNAL_GOOGLE_CLIENT_ID   # Google OAuth client id — dùng trong supabase/config.toml
SUPABASE_AUTH_EXTERNAL_GOOGLE_SECRET      # Google OAuth client secret — không commit
```

**Client behavior:** tính năng này không có debounce/optimistic UI/polling/upload/realtime pattern. Cổng chạy thời gian chạy duy nhất là locale-gate (cookie `NEXT_LOCALE`) — xem `permissions.md`. Guard điều hướng theo trạng thái đăng nhập — xem `architecture.md`.

## 5. Verification & Technical Notes

### 5.1 Technical Verification

- **SC-001** *(A0)* Truy cập `/todo` khi chưa đăng nhập → bị điều hướng `/login` (covers FR-101, FR-602)
- **SC-002** *(A0)* Truy cập `/login` khi đã đăng nhập → bị điều hướng `/todo` (covers FR-102)
- **SC-003** *(A2, A3)* Bấm nút đăng nhập → trình duyệt được điều hướng tới endpoint authorize của Supabase với `provider=google` (covers FR-202, FR-601)
- **SC-004** *(A3)* Callback nhận `error` → điều hướng `/login?error=oauth_failed` và A1 hiện đúng thông báo lỗi (covers FR-402)

#### US001_GoogleSignIn *(A1, A2, A3)*

**Independent Test:** Seed session hợp lệ trực tiếp vào Supabase local (không qua Google thật — xem Assumption bên dưới), xác nhận `/login` điều hướng `/todo`; ngược lại, không có session thì bấm nút xác nhận trình duyệt được điều hướng tới URL authorize của Supabase có `provider=google`.

**Acceptance Scenarios:**

1. **Given** khách chưa đăng nhập ở `/login`, **When** bấm "LOGIN With Google", **Then** nút chuyển sang loading/disabled và trình duyệt được điều hướng ra ngoài tới trang xác thực Google.
2. **Given** callback nhận được `code` hợp lệ, **When** exchange session thành công, **Then** người dùng được điều hướng tới `/todo`.

#### US002_RouteGuard *(A0)*

**Independent Test:** Không cần đăng nhập thật — set/xoá cookie session trực tiếp rồi truy cập `/login` và `/todo`, quan sát điều hướng.

**Acceptance Scenarios:**

1. **Given** đã có session hợp lệ, **When** truy cập `/login`, **Then** bị điều hướng `/todo`.
2. **Given** không có session, **When** truy cập `/todo`, **Then** bị điều hướng `/login`.

### 5.2 Assumptions

- *(A1, A2, A3)* Theo Assumption A1 trong `clarifications.md`: E2E không thể hoàn thành round-trip Google thật (màn hình consent không tự động hoá được, local Supabase không có mock provider). RED/GREEN chỉ xác nhận: màn hình render đúng spec, redirect hướng tới endpoint authorize của Supabase với `provider=google`, và điều hướng theo trạng thái phiên được seed trực tiếp vào Supabase local.
- *(A0)* Logic route-guard được thêm trực tiếp vào `proxy.ts` hiện có (cùng file với `updateSession`), không tách middleware riêng — đúng như quyết định trong `clarifications.md`.
- *(A2, A3)* API `@supabase/ssr` đã chốt và xác nhận khớp code thật: `signInWithOAuth` trả `data.url`, caller tự `redirect`; `exchangeCodeForSession(code)` ở route callback (`researcher-02-supabase-google-oauth.md`).

### 5.3 Unresolved Questions

1. ~~**API chính xác của `@supabase/ssr` cho `signInWithOAuth`/`exchangeCodeForSession`**~~ — **ĐÃ ĐÓNG (2026-09-04).** `researcher-02-supabase-google-oauth.md` đã có và xác nhận cả hai chữ ký khớp với những gì spec này viết. Chốt thêm: dùng **Server Action** (không phải Client Component) để giữ đúng một cookie adapter `lib/supabase/server.ts`; trong `proxy.ts` response redirect **phải** kế thừa `response.cookies.getAll()`, nếu không token vừa xoay bị mất và user bị đăng xuất ở request kế tiếp.
2. ~~**Vị trí file Server Action/Route Handler**~~ — **ĐÃ ĐÓNG.** Toàn bộ tên file đã xác nhận trực tiếp trong code (§ 3, § 4.1): `app/login/actions.ts` (`signInWithGoogle`), `app/auth/callback/route.ts` (`GET`), `app/_actions/locale.ts` (`setLocale`), `app/_actions/auth.ts` (`signOut` — đã chuyển ra khỏi `/todo`-only, dùng chung với F002).
3. **Asset nền hero (`public/images/login/hero.png`)** *(A1)*: vẫn **chưa tồn tại** trong `public/images/login/` — xác nhận lại bằng `ls`, RISK-01 ở `functional-spec.md` vẫn đúng. `HeroBackground` (`app/login/_components/hero-background.tsx:11-24`) đã có fallback màu đặc, không lỗi khi ảnh còn thiếu.

### 5.4 Source References

| Action | File | Lines |
|---|---|---|
| A1 | `app/login/page.tsx` | 31-59 |
| A1 | `app/login/_components/{hero-background,login-header,login-content,login-footer,error-banner,google-sign-in-button}.tsx` | toàn file |
| A2 | `app/login/actions.ts` | 16-35 |
| A3 | `app/auth/callback/route.ts` | 1-108 |
| A0 | `proxy.ts` | 1-56 |
| A4 | `app/_actions/locale.ts` | 13-27 |
| A4 | `app/_components/language-selector.tsx` | 77-84 (gọi `setLocale`) |
| A5 | `app/todo/page.tsx` | 18-48 |
| A6 | `app/_actions/auth.ts` | 17-21 |

#### Data Flow

N/A — A1/A5 chỉ render, A2/A3 điều hướng ra ngoài/callback (không ghi bảng do app sở hữu), A4/A6 chỉ ghi cookie/thu hồi phiên (xem § 4.2, § 4.3).

### 5.5 Artifact References

| Artifact | File | Codes Used | Reviewed |
|----------|------|------------|----------|
| Feature List | [feature-list.md](../../generated/feature-list.md) | F001 | [x] |
| Architecture | [architecture.md](../../system/architecture.md) | — (narrative, no per-code cite) | [x] |
| Permissions | [permissions.md](../../system/permissions.md) | — (narrative, no per-code cite) | [x] |
| Screens | [functional-spec.md § 6](./functional-spec.md#6-screens) | SCR001_Login | [x] |
