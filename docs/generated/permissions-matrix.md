---
authored_by: rebuild-spec (Core pass, generated layer)
---

# Permissions Matrix

**Project**: my-app (SAA 2025)
**Generated**: 2026-09-05
**Analysis Scope**: `proxy.ts`, `app/_page-context.ts`, `app/_components/account-menu.tsx`, `app/_components/home-header.tsx`, `supabase/migrations/20260906140914_kudos_live_board.sql` (F004, added below)

> Raw PERM### inventory (code-derived). The curated plain-language view is the forward-draft
> `docs/system/permissions.md` — that file predates this Core pass and should be reconciled
> against this one, not restated here.

**Authorization model**: `hybrid` as of F004 (was "effectively none"). App layer, unchanged: one
role signal (`user.app_metadata.role === "admin"`) gates one menu link; no route and no server
action checks it, so anyone can navigate to `/admin` or `/profile` directly. Database layer, new:
Postgres RLS on every `public.*` table the Kudos Live Board owns — `select` open to
`anon`+`authenticated` on all ten tables (PERM006), `insert`/`delete` on `kudos_likes` restricted
to `authenticated` matching `(select auth.uid()) = user_id`, with `insert` additionally rejecting
the kudos's own sender (PERM007). This is the project's first data-level authorization boundary —
the first place a Postgres role, not just app code, refuses a request.

## Permissions Index

| Code | Name | Type | Enforced At |
|------|------|------|--------------|
| PERM001 | Todo route guard | route-guard | `proxy.ts:41-43` |
| PERM002 | Login route bounce | route-guard | `proxy.ts:44-46` |
| PERM003 | Auth callback deliberate no-guard exemption | route-guard | `proxy.ts:11-13` (reasoning), matcher config `:51-56` |
| PERM004 | Admin Dashboard menu-link visibility | screen-permission | `app/_page-context.ts:40` + `app/_components/account-menu.tsx:99-107` |
| PERM005 | Authenticated-only header controls | screen-permission | `app/_components/home-header.tsx:66,75` |
| PERM006 | Kudos public read (RLS) | data-permission | `supabase/migrations/20260906140914_kudos_live_board.sql:161-170,194` |
| PERM007 | Kudos like write ownership + anti-self-like (RLS) | resource-ownership | `supabase/migrations/20260906140914_kudos_live_board.sql:174-184,195` |

---

## PERM001: Todo route guard

**Type**: route-guard
**Enforced At**: `proxy.ts:41-43`

### Description

`!user && pathname.startsWith("/todo")` → redirect to `/login`, carrying forward any rotated
session cookies from `updateSession()` (BL003 in `behavior-logic.md` — a bare
`NextResponse.redirect()` here would drop single-use refresh tokens and silently log the user
out on the next request).

### Related Routes

- (GET/any) `/todo`

### Related Screens

- SCR001_Login — the bounce target

### Permission Rules

| Role | Allow | Conditions |
|------|-------|------------|
| Anonymous | ✗ | Redirected to `/login` |
| Authenticated | ✓ | — |
| Admin | ✓ | Same as authenticated — no extra check |

---

## PERM002: Login route bounce

**Type**: route-guard
**Enforced At**: `proxy.ts:44-46`

### Description

`user && pathname.startsWith("/login")` → redirect to `/todo`, same cookie-preserving mechanism
as PERM001. Prevents an already-authenticated session from re-seeing the login form.

### Related Routes

- (GET/any) `/login`

### Related Screens

- SCR001_Login — the route this rule bounces *away from*

### Permission Rules

| Role | Allow | Conditions |
|------|-------|------------|
| Anonymous | ✓ | — |
| Authenticated | ✗ | Redirected to `/todo` |
| Admin | ✗ | Same as authenticated |

---

## PERM003: Auth callback deliberate no-guard exemption

**Type**: route-guard
**Enforced At**: `proxy.ts:11-13` (reasoning comment), matcher config `:51-56`

### Description

`/auth/callback` is deliberately **not** matched by either guard rule in `proxy.ts:41-46`.
This is a documented decision, not an oversight: guarding the OAuth callback would make the
Google → app round-trip structurally impossible, since the request arrives with no session yet.
Origin-pinning and open-redirect defence are handled inside the handler itself
(`app/auth/callback/route.ts:31-64` — see BL005 in `behavior-logic.md`), not by `proxy.ts`.

### Related Routes

- (GET) `/auth/callback`

### Permission Rules

| Role | Allow | Conditions |
|------|-------|------------|
| Anonymous | ✓ | Required — this is how anonymous visitors become authenticated |
| Authenticated | ✓ | — |
| Admin | ✓ | — |

---

## PERM004: Admin Dashboard menu-link visibility

**Type**: screen-permission
**Enforced At**: `app/_page-context.ts:40` (`isAdmin = user?.app_metadata?.role === "admin"`) + `app/_components/account-menu.tsx:99-107` (`{isAdmin && <Link href="/admin">...}`)

### Description

**This gates one thing only: whether the "Admin Dashboard" `<Link>` renders inside the account
menu.** It is presentation gating, not authorization. `/admin` itself (`app/admin/page.tsx:8-12`)
performs **no** check of its own — the file's own comment says outright it "doesn't pretend to
check the admin role." Hiding the link does not protect the route: any principal who navigates
to `/admin` directly gets the same `ComingSoon` placeholder a non-admin would, because there is
no real content behind it yet. **Do not describe this as a route boundary in any downstream
artifact.**

### Related Routes

- (any) `/admin` — **not enforced here**; see the "no route check" note in `route-list.md`

### Related Screens

- SCR002_Homepage — the account menu lives in the homepage header

### Permission Rules

| Role | Allow (menu link render) | Conditions |
|------|---------------------------|------------|
| Anonymous | ✗ | Account menu itself does not render for anonymous (see PERM005) |
| Authenticated (non-admin) | ✗ | Menu renders (Profile, Sign out) but no Admin Dashboard link |
| Admin | ✓ | `app_metadata.role === "admin"`, a value **never written by this codebase** — assumed provisioned out-of-band in Supabase |

### Related Modules

- `app/_components/account-menu.tsx`
- `app/_page-context.ts`

---

## PERM005: Authenticated-only header controls

**Type**: screen-permission
**Enforced At**: `app/_components/home-header.tsx:66,75`

### Description

The notification bell and account-menu trigger are conditionally *rendered* — absent from the
DOM entirely when anonymous, not hidden with CSS. This is the mechanism that makes PERM004 moot
for anonymous visitors: there is no account menu to open at all.

### Related Screens

- SCR002_Homepage

### Permission Rules

| Role | Allow | Conditions |
|------|-------|------------|
| Anonymous | ✗ | Bell + account icon absent from DOM |
| Authenticated | ✓ | Both render |
| Admin | ✓ | Same as authenticated, plus PERM004's extra link |

### Related Modules

- `app/_components/home-header.tsx`
- `app/_components/notification-bell.tsx`
- `app/_components/account-menu.tsx`

---

## PERM006: Kudos public read (RLS)

**Type**: data-permission
**Enforced At**: `supabase/migrations/20260906140914_kudos_live_board.sql:161-170` (ten identical
`for select to anon, authenticated using (true)` policies) + `:194` (`grant select on all tables
in schema public to anon, authenticated`)

### Description

Every table the Kudos Live Board owns — `departments`, `hashtags`, `sunners`, `kudos`,
`kudos_hashtags`, `kudos_attachments`, `kudos_likes`, `gift_awards`, `spotlight_ticker_events`,
`board_stats` — grants `select` to both `anon` and `authenticated` with an unconditional `true`
predicate. This is public thank-you data; no row is scoped to a viewer. Backs `FR-601`
(`functional-spec.md`): "khách ẩn danh có toàn quyền đọc mọi khu vực của màn hình."

### Related Routes

- (GET) `/kudos` — ROUTE006

### Related Screens

- SCR004_KudosLiveBoard

### Permission Rules

| Role | Allow | Conditions |
|------|-------|------------|
| Anonymous | ✓ | Full read on all ten tables |
| Authenticated | ✓ | Same — no additional rows or columns unlocked |
| Admin | ✓ | Same as authenticated — the admin role signal never appears in any Kudos RLS policy |

---

## PERM007: Kudos like write ownership + anti-self-like (RLS)

**Type**: resource-ownership
**Enforced At**: `supabase/migrations/20260906140914_kudos_live_board.sql:174-184` (policies
`kudos_likes_insert_own`, `kudos_likes_delete_own`) + `:195` (`grant insert, delete on
public.kudos_likes to authenticated`)

### Description

`insert` requires `(select auth.uid()) = user_id` **and** a `not exists` subquery rejecting the
row when the kudos's `sender_id` resolves to a `sunners` row whose `auth_user_id` is the caller
(BR-003, the anti-self-like rule — re-enforced here beneath the UI-level `disabled` heart button
in `toggleKudosLike`, not trusted to the UI alone). `delete` requires only `(select auth.uid()) =
user_id` — unliking your own row. **No `update` policy exists anywhere on `kudos_likes`**: a like
flips by delete-then-insert, never an in-place flag flip. `anon` has no `insert`/`delete` grant at
all — an unauthenticated direct call is rejected by Postgres regardless of what the UI renders.

### Related Routes

- (server action, no route) `toggleKudosLike` — writes reached only through `/kudos`

### Related Screens

- SCR004_KudosLiveBoard

### Permission Rules

| Role | Allow | Conditions |
|------|-------|------------|
| Anonymous | ✗ | No `insert`/`delete` grant on `kudos_likes` for `anon` — the disabled UI button is a second, non-authoritative layer |
| Authenticated (not the sender) | ✓ | `(select auth.uid()) = user_id`; insert only, also requires the kudos's sender is not the caller |
| Authenticated (is the sender) | ✗ | Insert's `not exists` subquery rejects the row (BR-003) |
| Admin | ✓ / ✗ | Same rule as authenticated — the admin role is not read by any Kudos RLS policy |

### Related Modules

- `app/kudos/_actions/toggle-kudos-like.ts`
- `lib/kudos/viewer.ts`

---

## Principal × Resource Matrix

| Route | Anonymous | Authenticated | Admin | Enforced by |
|-------|-----------|----------------|-------|--------------|
| `/` | Allow | Allow | Allow | None — no gate exists; `proxy.ts` only matches `/todo` and `/login` prefixes |
| `/login` | Allow | Redirect → `/todo` | Redirect → `/todo` | PERM002 |
| `/todo` | Redirect → `/login` | Allow | Allow | PERM001 |
| `/auth/callback` | Allow (required) | Allow | Allow | PERM003 (deliberate exemption) |
| `/awards-information` | Allow | Allow | Allow | None — public, no gate |
| `/kudos` | Allow (read only) | Allow (read + heart write) | Allow (read + heart write) | Route: none — public, no gate. Data: PERM006 (read, all roles) + PERM007 (heart write, `authenticated` only, not on own kudos) |
| `/kudos/new` | Allow | Allow | Allow | None — public, no gate (declared `ComingSoon` placeholder) |
| `/kudos/secret-box` | Allow | Allow | Allow | None — public, no gate (declared `ComingSoon` placeholder) |
| `/kudos/[id]` | Allow | Allow | Allow | None — public, no gate (declared `ComingSoon` placeholder; `params.id` never read) |
| `/standards` | Allow | Allow | Allow | None — public, no gate |
| `/profile` | Allow | Allow | Allow | None — public, no gate. **Explicitly documented as deliberate** (`app/profile/page.tsx:9-11`): no protected content exists yet. |
| `/admin` | Allow | Allow | Allow | None — public, no gate. **The admin role controls only the menu link (PERM004), not this route.** |

## Summary

- **Total Permission Items**: 7
- **By Type**: route-guard: 3, screen-permission: 2, action-permission: 0, data-permission: 1, role-based: 0, resource-ownership: 1, field-permission: 0, api-scope: 0, feature-flag: 0, experiment: 0, env-gate: 0, locale-gate: 0

## Cross-Reference Validation

- [x] All PERM### codes are unique
- [x] All related route references are valid (ROUTE### in `route-list.md`)
- [x] All related screen references are valid (SCR001_Login, SCR002_Homepage, SCR004_KudosLiveBoard per `docs/generated/screen-list.md`)
- [x] No orphaned permission references
