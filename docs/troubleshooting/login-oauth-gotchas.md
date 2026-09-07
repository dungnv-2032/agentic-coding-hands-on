---
status: active
authored_by: doc-writer
created: 2026-09-04
lang: vi
---

# Login/OAuth — lỗi hay tái phát và trạng thái chưa xác nhận

Ghi lại những chỗ dễ vô tình sửa hỏng trong `proxy.ts` / `app/auth/callback/route.ts`, cộng với hai điểm
đang mở (RISK-01, A3). Hành vi tính năng nói chung xem
`docs/features/F001_Login/technical-spec.md` — trang này chỉ giữ đúng phần "vì sao code viết như vậy,
đừng đơn giản hoá nó".

## 1. `redirect()` trong `proxy.ts` phải kế thừa cookie đã rotate

`updateSession()` (`lib/supabase/update-session.ts`) tạo một `NextResponse` mới và ghi `Set-Cookie` của
token vừa được GoTrue rotate lên đó, mỗi khi access token hết hạn giữa các request. `proxy.ts` sau đó
quyết định có redirect hay không (`/todo` → `/login` khi chưa đăng nhập, `/login` → `/todo` khi đã đăng
nhập). Nếu chỗ redirect đó chỉ đơn giản gọi `NextResponse.redirect(url)`, đây là **response thứ ba**,
không hề mang theo cookie đã rotate ở trên — token cũ vừa rotate xong đã bị coi là dùng rồi (Supabase
refresh token dùng một lần), nên request kế tiếp trình duyệt gửi lên token đã "chết", và user bị đăng
xuất một cách âm thầm ngay sau khi vừa được redirect thành công.

Code hiện tại xử lý đúng bằng helper `redirectWithSessionCookies` trong `proxy.ts` — copy toàn bộ
`response.cookies.getAll()` sang response redirect trước khi trả về:

```ts
const redirectWithSessionCookies = (pathname: string) => {
  const url = request.nextUrl.clone();
  url.pathname = pathname;
  url.search = "";
  const redirectResponse = NextResponse.redirect(url);
  for (const cookie of response.cookies.getAll()) {
    redirectResponse.cookies.set(cookie);
  }
  return redirectResponse;
};
```

**Đừng "dọn dẹp" đoạn copy cookie này đi** — nhìn thì như code thừa nhưng nó là toàn bộ lý do route
guard không làm rớt session. Có test case bảo vệ hành vi này: `e2e/authenticated.spec.ts` case
`C8 [SC-001, proxy-cookie-rotation]`.

## 2. Không được lấy origin redirect từ `request.nextUrl.origin`

`app/auth/callback/route.ts` build URL redirect từ `NEXT_PUBLIC_SITE_URL` (hàm `resolveSiteOrigin`),
**không** từ request. Hai lý do, cả hai đều đã xác nhận trong code:

- Next.js 16 rewrite mọi hostname loopback (`127.0.0.1`, `[::1]`) thành chuỗi `"localhost"` bên trong
  `nextUrl.origin` (xem `REGEX_LOCALHOST_HOSTNAME` ở
  `node_modules/next/dist/server/web/next-url.js`). Dự án này ghim cookie session và
  allow-list redirect của Supabase vào `127.0.0.1` (xem `docs/setup/local-development.md` § 4) — dùng
  `nextUrl.origin` sẽ đưa user sang host không mang session của họ.
- Header `Host` (hoặc `x-forwarded-host`) né được lỗi rewrite ở trên, nhưng route này **không yêu cầu
  đăng nhập** để gọi được — build redirect từ header do client set là open redirect (CWE-644):
  `Host: evil.com` ở nhánh lỗi sẽ đẩy nạn nhân thẳng sang `evil.com`.

`NEXT_PUBLIC_SITE_URL` là đúng biến `app/login/actions.ts` dùng để build `redirectTo` khi gọi
`signInWithOAuth` — dùng lại ở callback giữ cả vòng round-trip ghim vào một origin duy nhất, do cấu
hình deployment chọn chứ không phải do request quyết định. Test bảo vệ:
`e2e/callback-security.spec.ts` (`Host: evil.com`, `x-forwarded-host: evil.com`, `next` tuyệt đối/
protocol-relative/backslash).

Tham số `next` trên URL callback cũng được parse lại qua `new URL(rawNext, origin)` rồi so `origin` với
nhau (`resolveNextPath`) — không dùng `startsWith("//")` hay so chuỗi thô, vì URL parser của WHATWG
chuẩn hoá biến thể backslash (`/\evil.com`) thành `//evil.com` mà cách so chuỗi thô bỏ sót.

## 3. RISK-01 — ảnh nền hero chưa export được

`public/images/login/hero.png` chưa tồn tại — endpoint render của MoMorph trả lỗi 500/401 suốt phiên
làm tính năng này (xem RISK-01 trong `functional-spec.md`). `HeroBackground`
(`app/login/_components/hero-background.tsx`) đã build đúng hình học Figma (`background-position`,
`background-size` theo node `662:14389`) trỏ vào `/images/login/hero.png`, phủ trên nền màu đặc
`#00101A` làm fallback. `background-color` chỉ hiện khi `background-image` chưa load được — nghĩa là
khi ảnh thật được thêm vào đúng path này, nó tự hiện ra, **không cần sửa code**. Việc còn lại chỉ là
export lại ảnh (thử lại endpoint MoMorph, hoặc export tay từ Figma) rồi bỏ vào đúng chỗ.

## 4. A3 — `skip_nonce_check = true` chưa kiểm chứng với Google thật

`supabase/config.toml` → `[auth.external.google]` có `skip_nonce_check = true`, kèm comment gốc của
Supabase "Required for local sign in with Google auth". Giá trị này lấy theo tài liệu Supabase, **chưa
có phiên nào test round-trip với Google thật** để xác nhận — bộ E2E hiện tại seed session thẳng vào
Supabase local, không đăng nhập Google thật (xem Assumption A1,
`docs/features/F001_Login/technical-spec.md` § 5.2). Nếu sau này có phiên test với tài khoản Google
thật mà đăng nhập không qua được ở bước exchange code, đây là chỗ đầu tiên nên nhìn lại.

## 5. "Access blocked: Authorization Error" ở màn Google — credential còn là placeholder

**Triệu chứng:** bấm "LOGIN With Google", trình duyệt nhảy sang Google rồi dựng màn
`Access blocked: Authorization Error`. Không có lỗi nào trong log Next.js, không có request nào quay
lại `/auth/callback`.

**Nguyên nhân:** `.env` ở repo root đang giữ credential placeholder:

```
SUPABASE_AUTH_EXTERNAL_GOOGLE_CLIENT_ID=local-placeholder.apps.googleusercontent.com
SUPABASE_AUTH_EXTERNAL_GOOGLE_SECRET=local-placeholder
```

Supabase CLI thay `env(...)` trong `supabase/config.toml` bằng đúng chuỗi này lúc `supabase start`, nên
GoTrue đẩy người dùng sang Google với một `client_id` không tồn tại. Google không nói rõ lý do — nó chỉ
chặn. Đây **không phải lỗi code**: `app/login/actions.ts`, `app/auth/callback/route.ts` và
`site_url`/`additional_redirect_urls` đều đúng.

**Chẩn đoán trong 5 giây** — không cần mở trình duyệt, hỏi thẳng GoTrue nó đang gửi `client_id` nào:

```bash
curl -s -i "http://127.0.0.1:54321/auth/v1/authorize?provider=google&redirect_to=http://127.0.0.1:3000/auth/callback" \
  | grep -i '^location' | grep -oE 'client_id=[^&]*'
```

Ra `client_id=local-placeholder.apps.googleusercontent.com` là dính đúng lỗi này. Ra một client id thật
(`<số>-<chuỗi>.apps.googleusercontent.com`) thì nguyên nhân nằm chỗ khác — đọc tiếp mục 1–4.

**Cách sửa:**

1. Google Cloud Console → APIs & Services → Credentials → Create credentials → OAuth client ID →
   Application type **Web application**.
2. Trong **Authorized redirect URIs**, thêm đúng URI của **Supabase**, không phải của Next.js:

   ```
   http://127.0.0.1:54321/auth/v1/callback
   ```

   Đây là chỗ hay sai nhất. Google gọi về GoTrue (cổng 54321), rồi GoTrue mới chuyển tiếp về
   `http://127.0.0.1:3000/auth/callback` của app — cái sau khai trong `additional_redirect_urls` của
   `supabase/config.toml`, **không** khai với Google. Khai nhầm cái sau sẽ ra `redirect_uri_mismatch`,
   một lỗi khác hẳn lỗi ở trang này.
3. Dán client id + secret thật vào `.env` ở repo root (file này gitignored — không phải `.env.local`,
   vì `.env.local` chỉ Next.js đọc, còn `.env` mới là file Supabase CLI đọc).
4. **Khởi động lại Supabase**: `npx supabase stop && npx supabase start`. Chỉ sửa `.env` là chưa đủ —
   `env(...)` chỉ được thay lúc container khởi động, nên stack đang chạy vẫn giữ giá trị placeholder cũ.
5. Chạy lại lệnh `curl` ở trên để xác nhận `client_id` đã đổi trước khi thử lại trên trình duyệt.

**Vì sao repo để placeholder:** cố ý. Không có Google Cloud project nào gắn với repo này (Assumption A3,
`plans/260904-1714-login-page-supabase-google-oauth/clarifications.md`), và bộ E2E seed session thẳng vào
Supabase local nên không cần credential thật để chạy xanh — xem thêm mục 4 ở trên.
