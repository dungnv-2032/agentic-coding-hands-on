---
authored_by: rebuild-spec (Core pass, generated layer)
---

# Permissions Matrix

**Project**: my-app (SAA 2025)
**Generated**: 2026-09-05
**Analysis Scope**: `proxy.ts`, `app/_page-context.ts`, `app/_components/account-menu.tsx`, `app/_components/home-header.tsx`, `supabase/migrations/20260906140914_kudos_live_board.sql` (F004), `supabase/migrations/20260907025909_viet_kudo_write_path.sql` (F005, added below), `supabase/migrations/20260909093000_the_le_rules_content.sql` (F007, PERM014/PERM015 below)

> Raw PERM### inventory (code-derived). The curated plain-language view is the forward-draft
> `docs/system/permissions.md` — that file predates this Core pass and should be reconciled
> against this one, not restated here.

**Authorization model**: `hybrid` as of F004/F005 (was "effectively none"). App layer, unchanged: one
role signal (`user.app_metadata.role === "admin"`) gates one menu link; no route and no server
action checks it, so anyone can navigate to `/admin` or `/profile` directly. Database layer:
Postgres RLS on every `public.*` table the Kudos Live Board owns — `select` open to
`anon`+`authenticated` on all ten tables (PERM006), `insert`/`delete` on `kudos_likes` restricted
to `authenticated` matching `(select auth.uid()) = user_id`, with `insert` additionally rejecting
the kudos's own sender (PERM007). **F005 adds:** the first route-level auth guard since F001
(`/kudos/new`, PERM008); the project's first content-**write** authorization — `insert` policies on
`kudos`, `kudos_hashtags`, `kudos_attachments` and `sunners`, all bridging
`sender_id`/`kudos_id`/`auth_user_id` back to `sunners.auth_user_id = (select auth.uid())`, with
deliberately no `update`/`delete` policy anywhere (PERM009); and the first Supabase Storage
authorization boundary — authenticated-write/public-read on the `kudos-attachments` bucket
(PERM010). The multi-table write itself runs through a `security invoker` Postgres function
(`create_kudos`, confirmed live via `pg_proc.prosecdef = f`) that takes no `sender_id` parameter at
all — the caller has no argument in which to put someone else's id, so forgery is unrepresentable,
not merely rejected by a check.

## Permissions Index

| Code | Name | Type | Enforced At |
|------|------|------|--------------|
| PERM001 | Todo + Viết-Kudo route guard | route-guard | `proxy.ts:51-58` |
| PERM002 | Login route bounce | route-guard | `proxy.ts:60-62` |
| PERM003 | Auth callback deliberate no-guard exemption | route-guard | `proxy.ts:11-13` (reasoning), matcher config `:67-72` |
| PERM004 | Admin Dashboard menu-link visibility | screen-permission | `app/_page-context.ts:40` + `app/_components/account-menu.tsx:99-107` |
| PERM005 | Authenticated-only header controls | screen-permission | `app/_components/home-header.tsx:66,75` |
| PERM006 | Kudos public read (RLS) | data-permission | `supabase/migrations/20260906140914_kudos_live_board.sql:161-170,194` |
| PERM007 | Kudos like write ownership + anti-self-like (RLS) | resource-ownership | `supabase/migrations/20260906140914_kudos_live_board.sql:174-184,195` |
| PERM008 | Viết Kudo route guard (`/kudos/new`) | route-guard | `proxy.ts:51-58` |
| PERM009 | Kudos content-write ownership, no update/delete (RLS + `create_kudos` RPC) | resource-ownership | `supabase/migrations/20260907025909_viet_kudo_write_path.sql:41-75,120-235` |
| PERM010 | Kudos attachment Storage bucket (authenticated write / public read) | data-permission | `supabase/migrations/20260907025909_viet_kudo_write_path.sql:89-101` |
| PERM014 | Rules sections public read (RLS) | data-permission | `supabase/migrations/20260909093000_the_le_rules_content.sql:59,63,77` |
| PERM015 | Rules items public read (RLS) | data-permission | `supabase/migrations/20260909093000_the_le_rules_content.sql:60,64,78` |

> **PERM011–PERM013 are deliberately unallocated here.** `docs/system/permissions.md`
> § "Mã `PERM###` dự kiến của vòng F006" reserves those three numbers for F006's boundaries
> (the `/profile` route guard, the `kudos` revoke + `kudos_readable` grant, and the self-scoped
> "Đã gửi" list). Those boundaries have shipped and been measured, but no entry has been written
> for them in this registry yet — F007 takes the next free numbers rather than stepping on the
> reservation. Run `/tkm:rebuild-spec --artifact permissions-matrix` to close the gap.

---

## PERM001: Todo + Viết-Kudo route guard

**Type**: route-guard
**Enforced At**: `proxy.ts:51-58`

### Description

`!user && isGuarded` → redirect to `/login`, carrying forward any rotated session cookies from
`updateSession()` (BL003 in `behavior-logic.md` — a bare `NextResponse.redirect()` here would drop
single-use refresh tokens and silently log the user out on the next request). `isGuarded` is one
shared boolean (`proxy.ts:51-56`) covering **three** independent route conditions:
`pathname.startsWith("/todo")`, `pathname === "/kudos/new" || pathname.startsWith("/kudos/new/")`
(added by F005 — see PERM008 for the route-specific detail), and `pathname === "/profile" ||
pathname.startsWith("/profile/")` (added by F006 — **no PERM### written for it yet**, reserved as
PERM011). All three are OR-combined in one `if`, not separate guard rules, which is why these
entries cite the same line range.

### Related Routes

- (GET/any) `/todo`
- (GET/any) `/kudos/new` — see PERM008

### Related Screens

- SCR001_Login — the bounce target
- SCR005_VietKudo — the bounce target (F005)

### Permission Rules

| Role | Allow | Conditions |
|------|-------|------------|
| Anonymous | ✗ | Redirected to `/login` |
| Authenticated | ✓ | — |
| Admin | ✓ | Same as authenticated — no extra check |

---

## PERM002: Login route bounce

**Type**: route-guard
**Enforced At**: `proxy.ts:60-62`

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
**Enforced At**: `proxy.ts:11-13` (reasoning comment), matcher config `:67-72`

### Description

`/auth/callback` is deliberately **not** matched by either guard rule in `proxy.ts:51-62`.
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

## PERM008: Viết Kudo route guard (`/kudos/new`)

**Type**: route-guard
**Enforced At**: `proxy.ts:51-58`

### Description

`!user && pathname === "/kudos/new" || pathname.startsWith("/kudos/new/")` (OR-combined into the
same `isGuarded` check as PERM001) → redirect to `/login`. This is the first route guard added
since F001 — writing a Kudos needs a resolvable identity, unlike the public read surface. The
match is **exact-path-or-subpath on `/kudos/new`**, never a bare `pathname.startsWith("/kudos")`:
the rest of the Kudos surface (`/kudos`, `/kudos/[id]`, `/kudos/secret-box`) is a ratified F004
public-read path and must stay reachable without a session.

### Related Routes

- (GET/any) `/kudos/new` — ROUTE010

### Related Screens

- SCR005_VietKudo — the bounce target

### Permission Rules

| Role | Allow | Conditions |
|------|-------|------------|
| Anonymous | ✗ | Redirected to `/login` |
| Authenticated | ✓ | — |
| Admin | ✓ | Same as authenticated — no extra check |

---

## PERM009: Kudos content-write ownership, no update/delete (RLS + `create_kudos` RPC)

**Type**: resource-ownership
**Enforced At**: `supabase/migrations/20260907025909_viet_kudo_write_path.sql:41-75` (policies
`kudos_insert_own`, `kudos_hashtags_insert_own`, `kudos_attachments_insert_own`,
`sunners_insert_own` + their `grant insert`) + `:120-235` (`create_kudos` function + `grant execute`)

### Description

The project's **first content-write authorization boundary** — previously only `kudos_likes`
(PERM007) had an `insert`/`delete` policy; every other Kudos table was `select`-only. Four new
`insert` policies, all `to authenticated`, all bridging back to the caller through
`sunners.auth_user_id = (select auth.uid())`:

- `kudos_insert_own` — `sender_id` must resolve to a `sunners` row owned by the caller.
- `kudos_hashtags_insert_own` / `kudos_attachments_insert_own` — bridge through the **parent**
  `kudos` row's `sender_id`, same ownership chain.
- `sunners_insert_own` — a caller may only insert a `sunners` row with their own `auth_user_id`
  (backs the auto-provisioning described in `behavior-logic.md`).

The actual write path (`createKudos` → `supabase.rpc("create_kudos", ...)`) does not call these
tables directly — it calls the `create_kudos` Postgres function, confirmed live as
**`security invoker`** (`pg_proc.prosecdef = f`), which runs as the caller so all four policies
above still apply; the function exists to make the `kudos` + `kudos_hashtags` +
`kudos_attachments` insert transactional, not to bypass RLS. **The function takes no `sender_id`
argument at all** — it resolves the actor from `auth.uid()` internally and auto-provisions a
`sunners` row on first write (`on conflict (auth_user_id) do nothing`, then re-select — a
double-submit cannot create two rows). A forged sender is therefore **unrepresentable**, not
merely a value that gets rejected by a check.

**Deliberately no `update` or `delete` policy anywhere in this migration** — editing
(`Màn Sửa bài viết`) and moderating/deleting (`Admin - Review content`) a Kudos are separate,
not-yet-built commissions. Silence stays the deny for both verbs, same as every other table
this app owns.

### Related Routes

- (server action, no route) `createKudos` — writes reached only through `/kudos/new`

### Related Screens

- SCR005_VietKudo

### Permission Rules

| Role | Allow | Conditions |
|------|-------|------------|
| Anonymous | ✗ | No `insert` grant on any of the four tables for `anon`; `create_kudos` also raises `28000` when `auth.uid()` is null |
| Authenticated | ✓ (insert only) | Ownership resolved server-side from the session — no client-supplied `sender_id`/`auth_user_id` is ever trusted |
| Authenticated | ✗ (update/delete) | No policy exists for either verb on any of the four tables |
| Admin | ✓ / ✗ | Same rule as authenticated — the admin role is not read by any Kudos RLS policy or by `create_kudos` |

### Related Modules

- `app/kudos/new/_actions/create-kudos.ts`
- `lib/kudos/validate-compose.ts`

---

## PERM010: Kudos attachment Storage bucket (authenticated write / public read)

**Type**: data-permission
**Enforced At**: `supabase/migrations/20260907025909_viet_kudo_write_path.sql:89-101`
(bucket insert + policies `kudos_attachments_object_insert`, `kudos_attachments_object_read`)

### Description

The app's **first Supabase Storage integration**. Bucket `kudos-attachments` is created
`public: true` — reads are open to `anon`+`authenticated` because the Kudos board is public and
attachment URLs render permanently server-side (a signed URL would expire mid-render). Writes
(`storage.objects` `insert`) are restricted to `authenticated`, and further scoped by path: `with
check ((storage.foldername(name))[1] = (select auth.uid())::text)` — a caller can only write
under a first path segment equal to their own uid, so one user cannot write into another's folder.
No `update`/`delete` policy exists on `storage.objects` for this bucket — an uploaded object is
permanent from the app's perspective (F005 clarifications: removing a thumbnail in the compose UI
only clears client state, it does not delete the Storage object).

### Related Routes

- (server action, no route) `uploadKudosImage` — writes reached only through `/kudos/new`

### Related Screens

- SCR005_VietKudo (upload); SCR004_KudosLiveBoard (read, once a Kudos with an attachment is on the board)

### Permission Rules

| Role | Allow | Conditions |
|------|-------|------------|
| Anonymous | ✓ (read only) | Public bucket — object URLs resolve for anyone |
| Anonymous | ✗ (write) | No `insert` grant for `anon` |
| Authenticated | ✓ (write, own folder only) | Path's first segment must equal `(select auth.uid())::text` |
| Authenticated | ✗ (another user's folder) | Path check fails |
| Admin | ✓ / ✗ | Same rule as authenticated — the admin role is not read by this policy |

### Related Modules

- `app/kudos/new/_actions/upload-kudos-image.ts`
- `lib/kudos/validate-compose.ts` (MIME allow-list + magic-byte signature check, defense-in-depth beneath this policy)

---

## PERM014: Rules sections public read (RLS)

**Type**: data-permission
**Enforced At**: `supabase/migrations/20260909093000_the_le_rules_content.sql:59` (RLS on), `:63` (policy), `:77` (grant)
**Owner F###**: F007

### Description

`public.rule_sections` holds the three ordered prose sections of the Thể lệ screen. RLS is enabled
and the table carries exactly one policy — `rule_sections_select_all`,
`for select to anon, authenticated using (true)` — with an explicit
`grant select on public.rule_sections to anon, authenticated`. There is **no** `insert`, `update`
or `delete` policy: RLS denies by default, so the silence is the deny. No Server Action exists on
`/standards`, so the application exposes no write path either. Editing the rules copy today means
editing a migration or the seed.

Verified live (`pg_policies`, `pg_class.relrowsecurity`): RLS is on, exactly one `SELECT` policy
with `qual = true` for `{anon,authenticated}`.

### Related Routes

- (GET) `/standards` — the only reader

### Related Screens

- SCR007_TheLe

### Permission Rules

| Principal | Allowed | Notes |
|-----------|---------|-------|
| Anonymous | ✓ read | Same copy as everyone else — the rules carry no per-viewer variation |
| Authenticated | ✓ read | Identical |
| Admin | ✓ read | Identical — the admin role unlocks nothing here |
| Any principal | ✗ write | No `insert`/`update`/`delete` policy exists on the table |

### Related Modules

- `lib/rules/queries.ts` (`fetchRuleSections`)
- `lib/rules/rules-data.ts`

---

## PERM015: Rules items public read (RLS)

**Type**: data-permission
**Enforced At**: `supabase/migrations/20260909093000_the_le_rules_content.sql:60` (RLS on), `:64` (policy), `:78` (grant)
**Owner F###**: F007

### Description

`public.rule_items` holds the four Hero tiers and the six collectible icons in one table,
discriminated by `kind`. Identical boundary to PERM014 — one `rule_items_select_all` policy,
`for select to anon, authenticated using (true)`, explicit `grant select`, no write policy. The
`kind` discriminator is a schema concern, not an authorization one: both kinds are equally public,
and no policy branches on it.

Verified live: RLS on, one `SELECT` policy with `qual = true` for `{anon,authenticated}`, 10 rows
(4 `hero_tier` + 6 `collectible_icon`).

### Related Routes

- (GET) `/standards` — the only reader

### Related Screens

- SCR007_TheLe

### Permission Rules

| Principal | Allowed | Notes |
|-----------|---------|-------|
| Anonymous | ✓ read | Both `kind` values, no distinction |
| Authenticated | ✓ read | Identical |
| Admin | ✓ read | Identical |
| Any principal | ✗ write | No `insert`/`update`/`delete` policy exists on the table |

### Related Modules

- `lib/rules/queries.ts` (`fetchRuleItems`, `RULE_ITEM_KIND`)
- `lib/rules/rules-data.ts`

---

### Note on the grant set behind PERM014/PERM015 (applies repo-wide, not new in F007)

The migration's explicit `grant select … to anon, authenticated` is belt-and-braces, not the thing
that stops a write. Measured on the running database, `anon` and `authenticated` in fact hold
`SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER` on both new tables — and on every
pre-existing `public` table too (`hashtags`, `departments`, `gift_awards` show the identical set).
That comes from the Supabase stack's own `alter default privileges` on schema `public`
(`pg_default_acl`: `anon=arwdDxtm`, `authenticated=arwdDxtm`), applied to every new table
automatically. **RLS is what actually denies the writes**, which is why "enable RLS on every
`public` table" is stated as a binding precedent in `docs/system/permissions.md` rather than a
nicety. One privilege is outside that backstop — `TRUNCATE` is not governed by RLS — but PostgREST
exposes no path to it, so no client-reachable surface uses it. Recorded because it is measurably
true, not because F007 introduced it.

---

## Principal × Resource Matrix

| Route | Anonymous | Authenticated | Admin | Enforced by |
|-------|-----------|----------------|-------|--------------|
| `/` | Allow | Allow | Allow | None — no gate exists; `proxy.ts` only matches `/todo`, `/login` and `/kudos/new` |
| `/login` | Allow | Redirect → `/todo` | Redirect → `/todo` | PERM002 |
| `/todo` | Redirect → `/login` | Allow | Allow | PERM001 |
| `/auth/callback` | Allow (required) | Allow | Allow | PERM003 (deliberate exemption) |
| `/awards-information` | Allow | Allow | Allow | None — public, no gate |
| `/kudos` | Allow (read only) | Allow (read + heart write) | Allow (read + heart write) | Route: none — public, no gate. Data: PERM006 (read, all roles) + PERM007 (heart write, `authenticated` only, not on own kudos) |
| `/kudos/new` | Redirect → `/login` | Allow (compose + submit) | Allow (compose + submit) | Route: PERM001/PERM008 (session required). Data: PERM009 (content write, `authenticated` only, no update/delete) + PERM010 (Storage attachment write, own-folder only) |
| `/kudos/secret-box` | Allow | Allow | Allow | None — public, no gate (declared `ComingSoon` placeholder) |
| `/kudos/[id]` | Allow | Allow | Allow | None — public, no gate (declared `ComingSoon` placeholder; `params.id` never read) |
| `/standards` | Allow (read) | Allow (read) | Allow (read) | Route: none — public, no gate, deliberately (F007). Data: PERM014 + PERM015 (read, all roles; no write policy on either table) |
| `/profile` | Redirect → `/login` | Allow | Allow | Route: session required (`proxy.ts:51-57`, exact-path guard on `/profile`/`/profile/*`, shipped with F006), plus a second session re-check inside the page. **No PERM### allocated yet** — reserved as `PERM011`, see the note under the Permissions Index. |
| `/admin` | Allow | Allow | Allow | None — public, no gate. **The admin role controls only the menu link (PERM004), not this route.** |

## Summary

- **Total Permission Items**: 12 (PERM001–PERM010, PERM014, PERM015 — PERM011–PERM013 reserved for
  F006 and not yet written, see the note under the Permissions Index)
- **By Type**: route-guard: 4, screen-permission: 2, action-permission: 0, data-permission: 4, role-based: 0, resource-ownership: 2, field-permission: 0, api-scope: 0, feature-flag: 0, experiment: 0, env-gate: 0, locale-gate: 0

## Cross-Reference Validation

- [x] All PERM### codes are unique
- [x] All related route references are valid (ROUTE### in `route-list.md`)
- [x] All related screen references are valid (SCR001_Login, SCR002_Homepage, SCR004_KudosLiveBoard, SCR005_VietKudo, SCR007_TheLe per `docs/generated/screen-list.md`)
- [x] No orphaned permission references
- [ ] **PERM### numbering is contiguous** — it is not, and the gap is deliberate: PERM011–PERM013
      are reserved for F006's shipped boundaries, which have no entry in this registry yet
