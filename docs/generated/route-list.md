---
authored_by: rebuild-spec (Core pass, generated layer)
---

# Route List

**Project**: my-app (SAA 2025)
**Generated**: 2026-09-05
**Nguồn**: `plans/260905-1153-homepage-saa/artifacts/scout-report.md` §2, §3

> Bản nháp code-derived (Core pass). Không phải forward-draft SDD — đối chiếu với
> `docs/system/permissions.md` (forward-draft) khi reconcile.
>
> **Cập nhật 2026-09-06 (F003 promote):** `/awards-information` không còn là placeholder — nó render
> màn hình Hệ thống giải thật và chuyển quyền sở hữu từ F002 sang F003. Số route tổng không đổi (9);
> số placeholder `ComingSoon` còn lại là **4**.
>
> **Cập nhật 2026-09-07 (F004 promote):** `/kudos` không còn là placeholder — nó render màn hình
> Kudos Live Board thật (đọc Postgres qua Supabase) và chuyển quyền sở hữu từ F002 sang F004. Ba
> route mới, mỗi route một placeholder `ComingSoon` khai báo thay vì lỗi 404, sinh ra từ bốn CTA
> trên màn hình: `/kudos/new`, `/kudos/secret-box`, `/kudos/[id]`. Route tổng 9 → **12**; placeholder
> `ComingSoon` còn lại 4 → **6**; đây là route đầu tiên của repo có dynamic segment.
>
> **Cập nhật 2026-09-07 (F005 promote):** `/kudos/new` không còn là placeholder — nó render màn
> hình Viết Kudo thật (`KudosComposePage`) và chuyển quyền sở hữu từ F004 sang F005. Đây cũng là
> **route được gác đăng nhập đầu tiên kể từ F001**: `proxy.ts` thêm một nhánh `pathname ===
> "/kudos/new" || pathname.startsWith("/kudos/new/")` (exact-path, không phải
> `startsWith("/kudos")`) — phần còn lại của bề mặt Kudos (`/kudos`, `/kudos/[id]`,
> `/kudos/secret-box`) vẫn công khai, không đổi. Hai Server Action mới (`createKudos`,
> `uploadKudosImage`) được thêm vào bảng Server Actions bên dưới. Route tổng vẫn **12** (route đã
> tồn tại, chỉ đổi từ placeholder sang thật); placeholder `ComingSoon` còn lại 6 → **5**.
>
> **Cập nhật 2026-09-09 (F006 — đính chính, không phải thay đổi code mới):** `/profile` đã hết là
> placeholder từ vòng F006 (`app/profile/page.tsx` render `SCR006_ProfileBanThan` thật) và đã được
> `proxy.ts` gác từ đó (`pathname === "/profile" || pathname.startsWith("/profile/")`,
> `proxy.ts:55-56`), nhưng bảng dưới vẫn ghi nó là `ComingSoon` công khai thuộc F002. Dòng
> `ROUTE008` được sửa ở lần cập nhật này — đây là đính chính một phát biểu sai, không phải ghi
> nhận một thay đổi mới.
>
> **Cập nhật 2026-09-09 (F007 promote):** `/standards` không còn là placeholder — nó render drawer
> Thể lệ thật (`SCR007_TheLe`, đọc `rule_sections`/`rule_items` mỗi request) và chuyển quyền sở
> hữu từ F002 sang F007. Không route mới, không Server Action mới, không route handler mới. Route
> tổng vẫn **12**; placeholder `ComingSoon` còn lại 5 → **3**: `/admin`, `/kudos/secret-box`,
> `/kudos/[id]` — đếm bằng `grep -rn "ComingSoon" app/`, đúng ba file import và render component
> đó.

Mười hai route: 11 page + 1 route handler. **Một dynamic segment** — `app/kudos/[id]/page.tsx`, xem
`ROUTE012` bên dưới (`app/kudos/[id]/page.tsx` — deliberately ignores `params`, xem `docs/features/F004_KudosLiveBoard/`).

## Backend Routes

| Method | Path | Code | Owner F### | Handler | Middleware |
|--------|------|------|------------|---------|------------|
| GET | /auth/callback | ROUTE001 | F001 | `app/auth/callback/route.ts:74` (`GET`) | none — deliberately excluded from `proxy.ts` matcher-guard logic; guarding it would make the OAuth round-trip structurally impossible (`proxy.ts:11-13`) |

## Frontend Routes/Pages

| Path | Component | Code | Owner F### | Rendering | Auth Requirement |
|------|-----------|------|------------|-----------|-------------------|
| / | `HomePage` (`app/page.tsx`) | ROUTE002 | F002 | ƒ dynamic | Public |
| /login | `LoginPage` (`app/login/page.tsx`) | ROUTE003 | F001 | ƒ dynamic | Public — but bounced to `/todo` when a session already exists (`proxy.ts:52-53`) |
| /todo | `TodoPage` (`app/todo/page.tsx`) | ROUTE004 | F001 | ƒ dynamic | **Auth required** — bounced to `/login` when no session (`proxy.ts:47-50`) |
| /awards-information | `AwardsInformationPage` (`app/awards-information/page.tsx:55`) | ROUTE005 | F003 | ƒ dynamic | Public — `proxy.ts` không chặn route này (`proxy.ts:47-53`); quyết định có chủ đích, xem `docs/features/F003_AwardSystem/functional-spec.md` § 3 D001 |
| /kudos | `KudosPage` (`app/kudos/page.tsx`) | ROUTE006 | F004 | ƒ dynamic | Public — anonymous reads everything, heart button disabled without a session (see `permissions-matrix.md` PERM006/PERM007) |
| /standards | `StandardsPage` (`app/standards/page.tsx:34`) | ROUTE007 | F007 | ƒ dynamic | Public — `proxy.ts` không chặn route này (`proxy.ts:51-57`); có chủ đích, thể lệ là thứ người chưa đăng nhập cần đọc trước khi tham gia (xem `docs/features/F007_TheLe/functional-spec.md` § 1) |
| /profile | `ProfilePage` (`app/profile/page.tsx:52`) | ROUTE008 | F006 | ƒ dynamic | **Auth required** — bounced to `/login` when no session (`proxy.ts:51-57`, exact-path guard on `/profile`/`/profile/*`), and the page re-resolves the session itself as a second layer |
| /admin | `Page` → `<ComingSoon />` (`app/admin/page.tsx`) | ROUTE009 | F002 | ƒ dynamic | **Public — no role check at the route.** `app/admin/page.tsx:8-12`: the role-gated Admin Dashboard *menu link* points here, but the route itself performs no admin check — it is a placeholder, not a stand-in that pretends to enforce the role. |
| /kudos/new | `KudosComposePage` (`app/kudos/new/page.tsx`) | ROUTE010 | F005 | ƒ dynamic | **Auth required** — bounced to `/login` when no session (`proxy.ts:47-50`, exact-path guard on `/kudos/new`/`/kudos/new/*`, not a `/kudos` prefix — the rest of `/kudos/*` stays public per F004) |
| /kudos/secret-box | `Page` → `<ComingSoon />` (`app/kudos/secret-box/page.tsx`) | ROUTE011 | F004 | ƒ dynamic | Public — declared placeholder for the sidebar's "Mở Secret Box" CTA |
| /kudos/[id] | `Page` → `<ComingSoon />` (`app/kudos/[id]/page.tsx`) | ROUTE012 | F004 | ƒ dynamic | Public — declared placeholder for "Xem chi tiết"/card-body/Spotlight-node links; `params.id` is deliberately never read or echoed (no reflected-content surface) |

**Why every route is ƒ dynamic**: the three remaining `ComingSoon` placeholders (`/admin`,
`/kudos/secret-box`, `/kudos/[id]`) call `getPageContext()`
(`app/_components/coming-soon.tsx:18`), which calls `cookies()` (`app/_page-context.ts:28`) —
`cookies()` opts a route out of static generation. `/`, `/awards-information`, `/kudos`,
`/kudos/new`, `/profile` and `/standards` reach the same call directly (`app/page.tsx:24-25`,
`app/awards-information/page.tsx:56`, `app/kudos/page.tsx:50`, `app/kudos/new/page.tsx:33`,
`app/profile/page.tsx:52`, `app/standards/page.tsx:35-38` —
`getKudosBoard()`/`getSpotlightTotal()`/`getComposeOptions()`/`getProfileData()`/`getRulesContent()`
also each open their own Supabase server client per request, an independent reason these routes can
never be static).
`/login` and `/todo` call `cookies()` directly (`app/login/page.tsx:32`, `app/todo/page.tsx:19`).
So **no route in this app is statically prerendered**. This is inferred from `cookies()` usage,
not read off a build manifest — `next build` was not run and no build output is committed
(scout-report.md §2).

## Server Actions (not routes — third callable surface)

Next.js Server Actions are not URL-routable, so they get no `ROUTE###` code, but they are the
only other way the client reaches server code in this app:

| Action | File | Called from |
|--------|------|-------------|
| `signInWithGoogle()` | `app/login/actions.ts:16` | `/login`'s `<form action={signInAction}>` |
| `setLocale(locale)` | `app/_actions/locale.ts:13` | `LanguageSelector` (`language-selector.tsx:81-83`), inside `startTransition` |
| `signOut()` | `app/_actions/auth.ts:17` | `/todo`'s sign-out form (`app/todo/page.tsx:31`); `AccountMenu`'s sign-out form (`account-menu.tsx:108`) |
| `toggleKudosLike(kudosId)` | `app/kudos/_actions/toggle-kudos-like.ts:59` | Every card's heart button on `/kudos`, passed down as the `toggleLike` prop from `KudosPage` → `KudosBoard` (F004) |
| `createKudos(prevState, payload)` | `app/kudos/new/_actions/create-kudos.ts:73` | `ComposeForm`'s submit (`useActionState`) on `/kudos/new` (F005) — passed down as a prop from `KudosComposePage`, never imported directly by a Track A component; validates server-side, then calls the `create_kudos` Postgres RPC (`security invoker`, no `sender_id` parameter — see `api-map.md`) and redirects to `/kudos` on success |
| `uploadKudosImage(file)` | `app/kudos/new/_actions/upload-kudos-image.ts:47` | `ImagePicker` on `/kudos/new` (F005) — one call per selected file; writes to Supabase Storage (`kudos-attachments` bucket), not Postgres; signals failure by rejecting with a typed `UploadKudosImageError`, not a returned `{error}` field |

`toggleKudosLike`, `createKudos`, and `uploadKudosImage` are now the three Server Actions in the app
that write (Postgres or Storage) rather than to auth/cookies.

## Summary

| Category | Count |
|----------|-------|
| Backend Routes (route handlers) | 1 |
| Frontend Pages | 11 |
| Server Actions (non-routable) | 6 |
| Total routes | 12 |
