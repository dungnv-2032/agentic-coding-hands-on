---
status: draft
authored_by: takumi
created: 2026-09-07
lang: vi
---

# Architecture

**Project**: my-app (SAA 2025) — forward-draft cho màn Viết Kudo, viết trước khi code (SDD).

## System Architecture

Next.js 16 App Router, mọi route render động (`ƒ`) vì đụng `cookies()` — không route nào
prerender tĩnh. Không có API layer riêng của ứng dụng ngoài route handler OAuth callback.

**Thay đổi lớn nhất so với bản trước:** repo giờ **có** database do mình quản. Trước Kudos Live
Board, Supabase chỉ được dùng cho `auth.*` — không schema, không migration, không SQL. Màn hình
này mang vào lớp Postgres đầu tiên: migration trong `supabase/migrations/`, seed
`supabase/seed.sql`, và RLS policy đầu tiên của dự án. Từ đây, "không có database" không còn
đúng, và mọi tính năng sau đều thừa hưởng tiền lệ RLS mà nó đặt ra.

**Thay đổi của vòng này (Viết Kudo):** trước màn này, mọi thứ repo làm với database là **đọc**,
cộng đúng một thao tác ghi nhỏ (thả tim). Viết Kudo là **form ghi đầu tiên của người dùng**, và nó
mang vào ba thứ mới:
- **Supabase Storage** — object storage đầu tiên. Ảnh đính kèm là file thật của người dùng, upload
  lên bucket riêng, không phải ảnh mẫu committed trong repo.
- **Một tài liệu rich-text** thay cho chuỗi phẳng: `kudos.message` giữ nguyên kiểu `text`, nhưng
  cột mới `kudos.message_format` (`'plain' | 'doc'`) cho biết nội dung là chuỗi thường hay là một
  document JSON. Nhờ discriminator này, 57 dòng seed của F004 vẫn là `'plain'` và thẻ Kudos đã
  ship không phải đổi cách render chúng.
- **Tự cấp `sunners` row khi ghi lần đầu.** Seed để `auth_user_id` NULL trên mọi dòng, nên một
  người vừa đăng nhập Google chưa có danh tính người gửi. Action tự tạo dòng đó (upsert theo
  `auth_user_id`, vốn đã `unique`) trước khi insert kudos.

```mermaid
graph TB
    subgraph Browser
        BR[Trình duyệt]
    end
    subgraph "Next.js App Router (my-app)"
        PX["proxy.ts — session refresh + route guard"]
        PC["app/_page-context.ts — điểm đọc duy nhất: locale + dictionary + isAuthenticated + isAdmin"]
        SC["Server Components — app/page.tsx, /awards-information, /kudos, /login, /todo, placeholder pages"]
        SA["Server Actions — signOut(), setLocale(), signInWithGoogle(), toggleKudosLike()"]
        CB["app/auth/callback/route.ts — Route Handler GET (OAuth callback)"]
        CC["Client Components — home-header, language-selector, account-menu, countdown-timer, kudos filters/carousel/heart/spotlight"]
        DICT["lib/i18n — dictionaries tĩnh (vi/en), không dùng thư viện i18n nào"]
        KQ["lib/kudos — query layer + logic thuần (badge, filter, top-N)"]
        DT["lib/supabase/database.types.ts — type sinh từ schema (supabase gen types)"]
    end
    subgraph Supabase
        SSR["@supabase/ssr — createServerClient / createBrowserClient"]
        AUTH["GoTrue Auth — auth.users, session, refresh token"]
        PG["Postgres — public schema: sunners, kudos, kudos_likes, hashtags, departments, gift_awards, spotlight_events"]
        RLS["RLS — select cho anon+authenticated; insert/delete kudos_likes chỉ auth.uid()"]
        GOOGLE["Google OAuth (qua GoTrue)"]
    end

    BR -->|request| PX
    PX -->|refresh + guard| SSR
    PX -->|cho qua hoặc redirect| SC
    SC --> PC
    PC --> SSR
    SC --> DICT
    SC --> KQ
    KQ --> DT
    KQ -->|read qua server client| SSR
    SC -->|props tối thiểu| CC
    CC -->|form action / startTransition| SA
    SA --> SSR
    SSR --> AUTH
    SSR -->|PostgREST| PG
    PG --- RLS
    AUTH --> GOOGLE
    BR -->|OAuth redirect| CB
    CB --> SSR
```

**Vẫn không có API layer riêng của ứng dụng** ngoài `app/auth/callback/route.ts`. Kudos không
thêm REST endpoint nào: Server Component đọc thẳng qua `lib/supabase/server.ts`, và thao tác ghi
duy nhất (thả tim) đi qua Server Action. Không có `/api/kudos`.

## Tech Stack

| Layer | Technology | Version | Nguồn |
|-------|------------|---------|-------|
| Frontend framework | Next.js (App Router) | 16.3.4 | `package.json` |
| UI runtime | React | 19.2.8 | `package.json` |
| Ngôn ngữ | TypeScript (strict) | theo `tsconfig.json` | `tsconfig.json` |
| Styling | Tailwind CSS v4 (`@tailwindcss/postcss`) | v4 | `postcss.config.mjs` |
| Auth / session | `@supabase/ssr` + `@supabase/supabase-js` (GoTrue) | 0.12.5 | `package.json` |
| Rich text | **Tự viết** — document JSON render ra React element, **không** `dangerouslySetInnerHTML`, không thư viện sanitize (repo không có `dompurify`/`sanitize-html`/`marked`) | — | `lib/kudos/` |
| **Database** | **Postgres qua Supabase local stack** — migration + seed + RLS do repo quản | theo `supabase/config.toml` | `supabase/config.toml`, `supabase/migrations/` |
| **DB types** | **Sinh bằng `supabase gen types typescript --local`**, commit vào repo | — | `lib/supabase/database.types.ts` |
| **Object storage** | **Supabase Storage** — bucket riêng cho ảnh đính kèm Kudos, có policy riêng | theo `supabase/config.toml` | `supabase/config.toml` (`storage.enabled = true`) |
| i18n | Tự viết — cookie `NEXT_LOCALE` + dictionary tĩnh, **không dùng thư viện** | — | `lib/i18n/locales.ts` |
| E2E test | Playwright | 1.62 | `package.json` |
| Cache | **Không có** cache layer riêng — route động, đọc mỗi request | N/A | — |
| Queue | **Không có** | N/A | — |
| ORM / query builder | **Không có** — dùng trực tiếp `supabase-js` (PostgREST), không Prisma/Drizzle | N/A | `lib/kudos/` |
| State/data-fetching lib | **Không có** (không Redux/Zustand, không SWR/TanStack Query) — state là `useState` cục bộ | N/A | — |
| Validation lib | **Không có** (không Zod/Yup) — predicate tự viết trong `lib/kudos/`, kiểm **cả ở server** trong Server Action, không tin client | N/A | `lib/kudos/` |
| Unit test runner | **Không có** — Playwright E2E là harness kiểm thử duy nhất | N/A | `package.json` |

## Data Flow

**Route-guard đổi ở vòng này.** `proxy.ts` vẫn chạy trên mọi request trừ asset tĩnh và vẫn gọi
`updateSession()`, nhưng danh sách guard không còn là hai route: `/kudos/new` được thêm vào cùng
`/todo`. Đây là guard đầu tiên kể từ F001. Lý do đơn giản — viết một lời cảm ơn cần có danh tính,
nên ở đây thật sự có thứ cần bảo vệ, khác với bảng đọc công khai. Bề mặt đọc của Kudos (`/kudos`,
`/kudos/[id]`, `/kudos/secret-box`) **không đổi**, vẫn công khai có chủ đích.

Sơ đồ dưới là luồng riêng của Kudos Live Board: đọc khi render, và ghi khi thả tim.

```mermaid
sequenceDiagram
    participant B as Browser
    participant PG2 as "app/kudos/page.tsx (Server Component)"
    participant PC as "_page-context.ts"
    participant KQ as "lib/kudos (query layer)"
    participant S as "Supabase server client"
    participant DB as "Postgres + RLS"
    participant SA as "Server Action toggleKudosLike()"

    B->>PG2: GET /kudos (không bị guard)
    PG2->>PC: getPageContext()
    PC-->>PG2: { locale, dictionary, isAuthenticated, isAdmin }
    PG2->>KQ: đọc kudos + hashtags + departments + sidebar + spotlight
    KQ->>S: createClient() rồi .from(...).select(...)
    S->>DB: PostgREST query, mang JWT (hoặc anon key nếu chưa đăng nhập)
    DB-->>S: chỉ những row RLS cho phép select
    S-->>KQ: rows
    KQ-->>PG2: view model (đã cộng heart_baseline + count(likes))
    PG2-->>B: HTML (ƒ dynamic, không cache)

    B->>SA: thả tim (startTransition)
    alt chưa đăng nhập
        SA-->>B: nút heart disabled — không có request nào được gửi
    else đã đăng nhập
        SA->>S: insert/delete kudos_likes
        S->>DB: ghi — RLS with check (select auth.uid()) = user_id
        DB-->>S: ok hoặc bị từ chối ở tầng DB
        SA-->>B: revalidate, count đọc lại từ DB
    end
```

Sơ đồ dưới là luồng ghi của màn Viết Kudo — form ghi đầu tiên của người dùng trong repo.

```mermaid
sequenceDiagram
    participant B as Browser
    participant PX as "proxy.ts (guard)"
    participant PG as "app/kudos/new/page.tsx"
    participant CF as "compose form (Client Component)"
    participant SA as "Server Action createKudos()"
    participant ST as "Supabase Storage"
    participant DB as "Postgres + RLS"

    B->>PX: GET /kudos/new
    alt chưa đăng nhập
        PX-->>B: 307 redirect /login
    else đã đăng nhập
        PX->>PG: cho request đi tiếp
        PG-->>B: HTML (dialog, ƒ dynamic)
        B->>CF: nhập người nhận / danh hiệu / nội dung / hashtag / ảnh
        CF->>ST: upload từng ảnh (validate type ở client TRƯỚC)
        ST-->>CF: URL của file thật
        CF->>SA: submit form (useActionState)
        SA->>SA: validate lại TOÀN BỘ ở server — client không phải biên
        alt thiếu field bắt buộc
            SA-->>CF: trả về lỗi theo từng field, không ghi gì
        else hợp lệ
            SA->>DB: upsert sunners (nếu người gửi chưa có dòng)
            SA->>DB: insert kudos + kudos_hashtags + kudos_attachments
            DB-->>SA: ok, hoặc RLS từ chối nếu sender_id không thuộc session
            SA-->>B: refresh() rồi điều hướng về /kudos
        end
    end
```

**Ghi chú kiến trúc quan trọng**:
- `_page-context.ts` vẫn là **điểm đọc duy nhất** cho locale + dictionary + hai cờ suy ra. Object
  `user` gốc của Supabase **không bao giờ** vượt biên sang Client Component. Kudos không phá lệ
  này: sidebar và trạng thái tim được Server Component giải quyết xong rồi mới truyền xuống dưới
  dạng dữ liệu thuần.
- **Số tim = `kudos.heart_baseline` + `count(kudos_likes)`.** Seed không được ghi vào
  `auth.users` (GoTrue sở hữu schema đó), nên số `1.000` trên frame sống ở cột baseline, còn
  `kudos_likes` chỉ chứa like thật của người dùng thật. Nhờ vậy ràng buộc "một người một like
  trên mỗi kudos" vẫn cưỡng chế được ở tầng DB.
- **Sunner ẩn danh đọc được hết, ghi thì không.** RLS mở `select` cho `anon` và `authenticated`;
  `insert`/`delete` trên `kudos_likes` chỉ mở cho `authenticated` và khớp `auth.uid()`. Nút tim
  disabled ở UI chỉ là lớp thứ hai — chặn thật nằm ở DB.
- **Không cache.** Route đụng `cookies()` nên render động mỗi request; trạng thái tim theo từng
  người xem, nên cache trang sẽ sai. Đây là lý do không dùng `use cache` ở đây.
- **`db reset` là bước trước khi chạy test, không bao giờ giữa phiên.** Nó truncate cả schema
  `auth`, nên gọi giữa lúc suite đang chạy sẽ làm `getUser()` trả null và đẩy browser đã đăng
  nhập về `/login`.
- **Người gửi luôn suy từ session, không bao giờ nhận từ client.** `createKudos()` không có tham số
  actor, giống `toggleKudosLike()`. RLS chốt lại điều đó ở tầng DB: `sender_id` phải nằm trong
  `select id from sunners where auth_user_id = (select auth.uid())`. Đây là thứ chặn việc mạo danh
  người gửi, và nó phải đúng ở tầng DB chứ không chỉ ở tầng app.
- **Validate hai lớp, nhưng chỉ một lớp là biên.** Client validate để hiện lỗi ngay và để disable
  nút `Gửi`; server validate lại toàn bộ vì client không đáng tin. Kiểu file ảnh cũng vậy.
- **Ẩn danh che người gửi, không che người nhận.** `is_anonymous` chỉ đổi cách thẻ Kudos hiển thị
  phía người gửi; `sender_id` vẫn được lưu thật để còn truy được khi cần kiểm duyệt.
- **Không có policy UPDATE/DELETE nào cho `kudos`.** Sửa và xoá bài là commission khác
  (`Màn Sửa bài viết`, `Admin - Review content`). Không mở sẵn quyền chưa có màn nào dùng.

## Deployment View

> Derived from repository infrastructure-as-code — not verified against production.

**N/A — không tìm thấy infrastructure-as-code nào trong repo.**

Không `Dockerfile`, không `docker-compose.yml`, không manifest Kubernetes, không Terraform, không
`vercel.json`/`netlify.toml`, không CI workflow. `supabase/config.toml` chỉ mô tả **local dev
stack** của Supabase CLI, không phải hạ tầng production — không dùng để suy ra deployment
topology.

Một điểm mới cần ghi lại: từ nay việc triển khai **có** bước schema. `supabase/migrations/` phải
được apply vào database đích trước khi bản build đọc được gì, và `supabase/seed.sql` là dữ liệu
dev/test, **không** phải dữ liệu production. Repo hiện chưa có nơi nào mô tả bước đó cho môi
trường thật — vẫn là khoảng trống, không suy diễn thêm ở đây.
