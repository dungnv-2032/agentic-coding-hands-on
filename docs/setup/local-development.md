---
status: active
authored_by: doc-writer
created: 2026-09-04
lang: vi
---

# Chạy dự án ở máy local

Hướng dẫn này để chạy được `/login` (Google OAuth qua Supabase local) và bộ test E2E trên máy dev.
Chi tiết hành vi tính năng xem `docs/features/F001_Login/functional-spec.md` — tài liệu này chỉ nói
"làm sao chạy được", không lặp lại "nó làm gì".

## 1. Bật Supabase local

```bash
npx supabase start
```

Lệnh này khởi động Postgres + GoTrue (Supabase Auth) trong Docker và in ra một loạt URL/key. Đợi nó
chạy xong rồi mới sang bước 2 — các biến môi trường ở bước 2 lấy trực tiếp từ output này (hoặc chạy lại
`npx supabase status` để xem lại).

## 1.1. Áp dụng schema + seed cho các màn hình đọc database

Từ F004, repo có schema Postgres riêng (`supabase/migrations/`) và dữ liệu chép nguyên văn từ
frame Figma (`supabase/seed.sql`) — không có cả hai thì `/kudos`, `/kudos/new`, `/profile` và
`/standards` không có gì để đọc, và mọi bảng (`kudos`, `sunners`, `kudos_likes`, `rule_sections`,
...) chưa tồn tại.

**Từ F007, `seed.sql` không còn thuần dữ liệu dev/test.** Nó chứa cả nội dung sản phẩm — toàn bộ
chữ thể lệ mà `/standards` hiển thị (`rule_sections`/`rule_items`). Bỏ qua seed thì `/standards`
vẫn render bình thường nhưng panel rỗng: không lỗi, không màn trắng, chỉ là không có nội dung —
nên triệu chứng dễ bị hiểu nhầm thành bug UI. `supabase start` chỉ tự áp dụng migration +
seed trên một Docker volume **mới tinh**; nếu bạn đã chạy `supabase start` trước khi pull tính năng
này, chạy thêm:

```bash
npx supabase db reset
```

Lệnh này apply lại toàn bộ `supabase/migrations/` rồi chạy `supabase/seed.sql` — **luôn chạy trước
khi mở `/kudos`, `/profile`, `/standards` hoặc chạy `npm run test:e2e`, không bao giờ giữa lúc dev
server/test đang chạy**: nó
truncate cả schema `auth`, nên chạy giữa phiên sẽ đá một session đã đăng nhập về `/login`.

Kiểu dữ liệu TypeScript sinh từ schema (`lib/supabase/database.types.ts`) đã được commit sẵn, nên
`npm run build`/`npm run typecheck` không cần database sống. Chỉ cần sinh lại khi bạn tự sửa
migration:

```bash
npm run db:types
```

## 2. Tạo `.env.local`

Copy `.env.example` thành `.env.local` (đã có trong `.gitignore`, không commit) rồi điền theo output ở
bước 1:

```bash
cp .env.example .env.local
```

| Biến | Lấy từ đâu |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | field "API URL" trong output `supabase status` (mặc định `http://127.0.0.1:54321`) |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | field "Publishable key" (định dạng mới `sb_publishable_...`) |
| `NEXT_PUBLIC_SITE_URL` | `http://127.0.0.1:3000` — xem mục 4 vì sao phải đúng y hệt |
| `NEXT_PUBLIC_EVENT_START_AT` | Thời điểm sự kiện SAA 2025 (ISO-8601) dùng cho bộ đếm ngược trên trang chủ `/` (F002_HomepageSaa). Mặc định trong `.env.example` (`2025-12-26T18:30:00+07:00`) đã ở quá khứ — muốn thấy đếm ngược đang chạy khi dev local thì đặt một ngày tương lai trong `.env.local`. Thiếu hoặc sai định dạng thì trang không lỗi — chỉ hiện `00/00/00` và ẩn "Coming soon" (FR-402) |

`service_role` key **không** đưa vào đây — key đó bỏ qua Row Level Security nên không được lộ ra
browser, không được commit. Đây là biến build-time (Next.js inline vào bundle client lúc khởi động dev
server/build, không đọc lại theo từng request) nên không mang giá trị bí mật, an toàn để commit
`.env.example`.

## 3. Google OAuth cần credentials thật

Nút "LOGIN With Google" gọi `supabase.auth.signInWithOAuth({ provider: 'google', ... })`
(`app/login/actions.ts`). Để Supabase Auth phát hành được URL xác thực thật, `supabase/config.toml`
đọc hai biến qua cú pháp `env(...)`:

```toml
# supabase/config.toml → [auth.external.google]
client_id = "env(SUPABASE_AUTH_EXTERNAL_GOOGLE_CLIENT_ID)"
secret = "env(SUPABASE_AUTH_EXTERNAL_GOOGLE_SECRET)"
```

Hai biến này **không** để trong `.env.local` — CLI `supabase` đọc chúng từ file `.env` ở **repo root**
tại thời điểm chạy `npx supabase start`, còn `.env.local` chỉ Next.js đọc. Tạo file `.env` (gitignored)
ở root:

```bash
SUPABASE_AUTH_EXTERNAL_GOOGLE_CLIENT_ID=<client-id-thật>.apps.googleusercontent.com
SUPABASE_AUTH_EXTERNAL_GOOGLE_SECRET=<client-secret-thật>
```

Lấy client id/secret từ Google Cloud Console (OAuth 2.0 Client ID, loại Web application). Redirect URI
đăng ký bên Google phải khớp `additional_redirect_urls` trong `supabase/config.toml`:
`http://127.0.0.1:3000/auth/callback`.

Thiếu credentials thật: `npx supabase start` vẫn chạy được, nhưng bấm "LOGIN With Google" sẽ hỏng ở
phía Google (client id không tồn tại) — không phải lỗi ở code Next.js.

## 4. Mọi thứ ghim vào `127.0.0.1`, không phải `localhost`

`site_url` và `additional_redirect_urls` trong `supabase/config.toml`, biến `NEXT_PUBLIC_SITE_URL`, và
`baseURL` trong `playwright.config.ts` đều dùng `127.0.0.1`. Đây không phải chọn tuỳ ý — session cookie
Supabase set cho domain `127.0.0.1` **không** được trình duyệt gửi kèm khi bạn mở `localhost:3000`
(và ngược lại), vì trình duyệt coi hai host này khác nhau dù cùng trỏ về máy mình. Mở nhầm
`localhost:3000` khi dev sẽ thấy đăng nhập xong vẫn bị đá về `/login` — không phải bug, chỉ là cookie
domain lệch. Luôn chạy và mở `http://127.0.0.1:3000`.

```bash
npm run dev -- --hostname 127.0.0.1 --port 3000
```

## 5. Chạy bộ test E2E

```bash
npm run test:e2e
```

Chạy `playwright test` — chia **10** project trong `playwright.config.ts` (đo 2026-09-09:
`npx playwright test --list` → 191 test trong 19 file; chạy lại lệnh đó để lấy con số hiện tại, vì
bộ test đang được bổ sung thường xuyên). Nhớ chạy bước 1.1 (`supabase db reset`) trước — các bộ
test Kudos, Profile và Thể lệ đều cần schema + seed đã áp dụng:

| Project | Vai trò | Phụ thuộc |
|---|---|---|
| `setup` | Seed session F001_Login thẳng vào Supabase local, không qua Google thật (Assumption A1, `docs/features/F001_Login/technical-spec.md`) | — |
| `anon` | `smoke`, `login-screen`, `route-guard`, `callback-security`, `homepage`, `award-system`, `profile-anon`, `the-le` (F007) và `kudos-live-board` (chưa đăng nhập) | `setup` |
| `authed` | `authenticated.spec.ts` — route guard đã đăng nhập + sign-out (C9 là **global** sign-out, dùng `storageState` seed riêng) | `setup` |
| `kudos-auth-setup` | Seed một session **độc lập** cho `kudos-authed`, tách khỏi session của `authed` vì test sign-out C9 thu hồi session dùng chung | — |
| `kudos-authed` | `kudos-live-board-authed.spec.ts` (F004) + `viet-kudo.spec.ts` (F005) — thả tim khi đã đăng nhập, và luồng soạn Kudos | `kudos-auth-setup` |
| `profile-auth-setup` | Seed một session **độc lập** cho `profile-authed`, cùng lý do như trên | — |
| `profile-authed` | `profile.spec.ts` (F006) — hai mặt self/other, đổi chiều feed, phân trang keyset | `profile-auth-setup` |
| `homepage-auth-setup` | Seed một session **độc lập** cho các test homepage-authed, tách khỏi session của `authed` để không bị ảnh hưởng bởi test sign-out C9 | — |
| `homepage-authed` | Chuông thông báo, menu tài khoản, gating Admin Dashboard trên `/` | `homepage-auth-setup` |
| `visual-capture` | Chụp ảnh màn hình desktop/mobile của `/` — chạy theo yêu cầu, **không** nằm trong bộ mặc định | `homepage-auth-setup` |

`webServer` tự chạy `npm run dev` cho bạn trên `127.0.0.1:3000`, ghim `NEXT_PUBLIC_EVENT_START_AT` vào
một ngày tương lai cố định (45 ngày kể từ lúc chạy) qua `webServer.env` để bộ test luôn thấy đếm ngược
đang chạy, bất kể `.env.local` đặt gì — không cần mở server tay trước.

### Riêng máy WSL2 thiếu thư viện hệ thống

Chromium headless của Playwright cần vài thư viện hệ thống (`libnspr4`, `libnss3`, `libasound2`, ...).
Trên máy dev không có sudo không cần mật khẩu, `npx playwright install --with-deps` sẽ không cài được.
Cách vòng — không cần root: giải nén các gói `.deb` thiếu bằng `dpkg-deb -x` vào thư mục
`.playwright-libs/` ở repo root (đã có trong `.gitignore` — máy-cụ-thể, không commit), sao cho có đường
dẫn `.playwright-libs/usr/lib/x86_64-linux-gnu/`. `playwright.config.ts` tự kiểm tra thư mục này bằng
`fs.existsSync` và set `LD_LIBRARY_PATH` nếu có — không tồn tại thì bỏ qua, không ảnh hưởng máy đã có
đủ thư viện hệ thống hoặc CI chạy `--with-deps`.

## 6. Kiểm tra nhanh trước khi báo "xong"

```bash
npm run typecheck
npm run lint
npm run test:e2e
```

Xem thêm gotcha khi sửa `proxy.ts` hoặc `app/auth/callback/route.ts` ở
`docs/troubleshooting/login-oauth-gotchas.md` — hai lỗi ở đó không lộ ra khi typecheck/lint pass mà chỉ
lộ khi chạy thật.
