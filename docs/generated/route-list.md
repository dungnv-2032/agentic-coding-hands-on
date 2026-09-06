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

Chín route: 8 page + 1 route handler. **Không có dynamic segment nào** — không có
thư mục `[param]` trong `app/` (`scout-report.md` §2).

## Backend Routes

| Method | Path | Code | Owner F### | Handler | Middleware |
|--------|------|------|------------|---------|------------|
| GET | /auth/callback | ROUTE001 | F001 | `app/auth/callback/route.ts:74` (`GET`) | none — deliberately excluded from `proxy.ts` matcher-guard logic; guarding it would make the OAuth round-trip structurally impossible (`proxy.ts:11-13`) |

## Frontend Routes/Pages

| Path | Component | Code | Owner F### | Rendering | Auth Requirement |
|------|-----------|------|------------|-----------|-------------------|
| / | `HomePage` (`app/page.tsx`) | ROUTE002 | F002 | ƒ dynamic | Public |
| /login | `LoginPage` (`app/login/page.tsx`) | ROUTE003 | F001 | ƒ dynamic | Public — but bounced to `/todo` when a session already exists (`proxy.ts:44-46`) |
| /todo | `TodoPage` (`app/todo/page.tsx`) | ROUTE004 | F001 | ƒ dynamic | **Auth required** — bounced to `/login` when no session (`proxy.ts:41-43`) |
| /awards-information | `AwardsInformationPage` (`app/awards-information/page.tsx:55`) | ROUTE005 | F003 | ƒ dynamic | Public — `proxy.ts` không chặn route này (`proxy.ts:41-46`); quyết định có chủ đích, xem `docs/features/F003_AwardSystem/functional-spec.md` § 3 D001 |
| /kudos | `Page` → `<ComingSoon />` (`app/kudos/page.tsx`) | ROUTE006 | F002 | ƒ dynamic | Public |
| /standards | `Page` → `<ComingSoon />` (`app/standards/page.tsx`) | ROUTE007 | F002 | ƒ dynamic | Public |
| /profile | `Page` → `<ComingSoon />` (`app/profile/page.tsx`) | ROUTE008 | F002 | ƒ dynamic | **Public — explicitly not guarded.** `app/profile/page.tsx:9-11` states outright: no protected content exists yet, and `proxy.ts` only guards `/todo` and `/login`. |
| /admin | `Page` → `<ComingSoon />` (`app/admin/page.tsx`) | ROUTE009 | F002 | ƒ dynamic | **Public — no role check at the route.** `app/admin/page.tsx:8-12`: the role-gated Admin Dashboard *menu link* points here, but the route itself performs no admin check — it is a placeholder, not a stand-in that pretends to enforce the role. |

**Why every route is ƒ dynamic**: the four remaining `ComingSoon` placeholders (`/kudos`,
`/standards`, `/profile`, `/admin`) call `getPageContext()`
(`app/_components/coming-soon.tsx:18`), which calls `cookies()` (`app/_page-context.ts:28`) —
`cookies()` opts a route out of static generation. `/` and `/awards-information` reach the same call
directly (`app/page.tsx:24-25`, `app/awards-information/page.tsx:56`).
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

## Summary

| Category | Count |
|----------|-------|
| Backend Routes (route handlers) | 1 |
| Frontend Pages | 8 |
| Server Actions (non-routable) | 3 |
| Total routes | 9 |
