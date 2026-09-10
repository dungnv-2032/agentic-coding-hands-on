---
authored_by: rebuild-spec (Core pass, generated layer)
---

# API Map

**Project**: my-app (SAA 2025)
**Generated**: 2026-09-05

## There is no REST/GraphQL API of this app's own

One route handler exists in the whole codebase, and it is the OAuth callback. There is no
`/api/*` directory, no controller layer, no resource endpoints. Anything documented downstream
as a "users API" or "awards API" would be invented — the awards grid and dictionaries are
static TypeScript literals (`lib/awards.ts`, `lib/i18n/messages/*.ts`), never fetched.

**Update (F004, Kudos Live Board):** the app now reads and writes its first real database, but
still through no HTTP endpoint of its own — `lib/kudos/queries.ts` calls Supabase's PostgREST
layer via the `supabase-js` client library (`.from(table).select(...)`), and the one write path
(`toggleKudosLike`) is a Server Action, not a route. See `entities.md`
(regeneration advised — flagged stale below) for the schema and `permissions-matrix.md`
PERM006/PERM007 for the RLS boundary that now gates it.

**Update (F005, Viết Kudo):** the write surface grows to two more Server Actions
(`createKudos`, `uploadKudosImage`) and the app's **first Postgres RPC** — `create_kudos(...)`,
called via `supabase.rpc("create_kudos", {...})` because PostgREST cannot transact an insert
across `kudos` + `kudos_hashtags` + `kudos_attachments` in one call. It also brings in the app's
**first Supabase Storage integration** — a real object-storage bucket (`kudos-attachments`),
not the four SELECT-only PostgREST tables F004 added. Still no `/api/*` route.

**Update (F007, Thể lệ):** two more SELECT-only PostgREST tables — `rule_sections` and
`rule_items` — read through `lib/rules/queries.ts` (`fetchRuleSections`, `fetchRuleItems`), both
with an explicit `.order("position", { ascending: true })`. This feature adds **no** endpoint, no
Server Action, no RPC and no Storage surface: `/standards` is read-only, and its two footer
controls are a `<button>` that calls `router.back()`/`router.push("/")` and a plain
`<a href="/kudos/new">`. Still no `/api/*` route. RLS boundary: `permissions-matrix.md`
PERM014/PERM015.

**Update (F009, Open Secret Box):** one new Server Action (`openSecretBox`) and the app's
**second Postgres RPC** — `open_secret_box()`, the project's first `security definer` function
(confirmed live: `pg_proc.prosecdef = t`, unlike `create_kudos`'s `f`). Unlike `create_kudos`,
this call takes **no parameters at all** — every prior RPC/Server Action at least received
typed payload fields; this one derives everything from the session. Still no `/api/*` route, no
new Storage surface. RLS + execute boundary: `permissions-matrix.md` PERM016/PERM017/PERM018.

## Endpoints by Domain

### Auth (Route Handler)

| Method | Path | Code | Handler | Description |
|--------|------|------|---------|--------------|
| GET | `/auth/callback` | ROUTE001 | `app/auth/callback/route.ts:74` (`GET`) | Google OAuth callback. Two branches: `code` present + `exchangeCodeForSession` succeeds → redirect to same-origin `next` (default `/todo`); `error` present, exchange fails, or transport throw → fixed `/login?error=oauth_failed`. Origin for every redirect comes from `NEXT_PUBLIC_SITE_URL` only, never the request (`:31-43`, CWE-644 defence). |

### Auth (Server Actions — not HTTP-routable, but the app's only other server-callable surface)

| Action | File:line | Description |
|--------|-----------|--------------|
| `signInWithGoogle()` | `app/login/actions.ts:16` | Builds `redirectTo = ${NEXT_PUBLIC_SITE_URL}/auth/callback`, calls `supabase.auth.signInWithOAuth({ provider: "google", redirectTo })`, redirects to the returned Google consent URL. Fails fast if `NEXT_PUBLIC_SITE_URL` is missing rather than composing a broken `undefined/auth/callback` (`:17-22`). |
| `setLocale(locale)` | `app/_actions/locale.ts:13` | Resolves the candidate locale (BL001), writes the `NEXT_LOCALE` cookie, then `revalidatePath("/", "layout")` (`:26`) so the whole layout subtree re-renders in the new locale. |
| `signOut()` | `app/_actions/auth.ts:17` | `supabase.auth.signOut()` then `redirect("/login")`. The `signOut()` error is deliberately discarded (`:17-21`) so an already-invalid session still lands on `/login`. |

### Kudos (Server Actions — F004/F005, the app's write paths into Postgres + Storage)

| Action | File:line | Description |
|--------|-----------|--------------|
| `toggleKudosLike(kudosId)` | `app/kudos/_actions/toggle-kudos-like.ts:59` | The only writer on `/kudos` (F004). Resolves the acting user from the session (never from an argument), returns the unchanged `{liked, hearts}` read for an anonymous caller or a self-like attempt (BR-003, re-enforced by RLS `with check`), else inserts/deletes the one `kudos_likes` row matching `(kudos_id, user_id)` (toggle), swallows a `23505` unique-violation race, and always returns the database's real post-write `{liked, hearts}` — `hearts = kudos.heart_baseline + count(kudos_likes)` (BR-001). Calls `refresh()` (`next/cache`) rather than `revalidatePath`. |
| `createKudos(prevState, payload)` | `app/kudos/new/_actions/create-kudos.ts:73` | The only writer on `/kudos/new` (F005). Resolves the acting user from the session; `ComposePayload` carries no sender field at all, so a forged sender is unrepresentable, not merely rejected. Re-validates every rule server-side (`validateCompose`), re-checks each image URL resolves to this project's own `kudos-attachments` Storage path (`isOwnStorageUrl`), then calls the `create_kudos` Postgres RPC. Maps the RPC's SQLSTATE back to a field error (`28000` → no session, `23514` on a hashtag-count violation → too-many/required) and logs anything else without reflecting the raw DB message to the client. On success, `redirect("/kudos")` — no `refresh()`, since the destination route is already dynamic. |
| `uploadKudosImage(file)` | `app/kudos/new/_actions/upload-kudos-image.ts:47` | Writes to Supabase **Storage**, not Postgres — one call per selected file from `/kudos/new`'s image picker (F005). Re-checks the MIME type server-side, then sniffs the file's actual leading bytes against a magic-number allow-list (`matchesImageSignature`) before ever writing to the public `kudos-attachments` bucket — `file.type` alone is caller-declared and not trusted. Object path is `${user.id}/${timestamp}-${uuid}.${ext}`, matching the bucket's owner-scoped `storage.objects` INSERT policy. Signals failure by **rejecting** with a typed `UploadKudosImageError` (not a returned `{error}` field), because the frozen `UploadKudosImage` contract type has no error slot. |
| `openSecretBox()` | `app/kudos/secret-box/_actions/open-secret-box.ts:37` | The only writer on `/kudos/secret-box` (F009). Takes **no argument**, not even an id — calls the `open_secret_box` Postgres RPC and maps its `error.code` to a closed `OpenSecretBoxResult` union (`28000` → `unauthenticated`, `P0002` → `no-boxes`, anything else → `failed`, logged by code only, never by message text). On success, `revalidatePath`s `/kudos/secret-box`, `/kudos` and `/profile` so all three box counters agree. |

### Kudos (Postgres RPC — F005/F009, the app's stored-procedure calls)

| Function | Called via | Description |
|----------|------------|--------------|
| `create_kudos(p_receiver_id, p_campaign, p_message, p_message_format, p_is_anonymous, p_anonymous_name, p_hashtag_ids, p_image_urls)` | `supabase.rpc("create_kudos", {...})` from `createKudos` | `supabase/migrations/20260907025909_viet_kudo_write_path.sql`. `security invoker` (**not** `security definer`, confirmed live: `pg_proc.prosecdef = f`) — runs as the calling role, so every RLS policy on `kudos`/`kudos_hashtags`/`kudos_attachments`/`sunners` still applies; it exists only to make the three-table insert transactional, not to bypass RLS. Takes **no `sender_id` parameter** — resolves the actor from `auth.uid()` internally and auto-provisions a `sunners` row on first write (upsert on the unique `auth_user_id`, so a double-submit cannot create two rows). Raises `28000` when unauthenticated, `23514` on any business-rule violation (blank campaign/message, hashtag count outside 1–5, more than 5 images), `23503` when the receiver doesn't exist. |
| `open_secret_box()` | `supabase.rpc("open_secret_box")` from `openSecretBox` | `supabase/migrations/20260910170000_secret_box_open_path.sql`. **`security definer`** (confirmed live: `pg_proc.prosecdef = t`) — the app's first, and deliberately so: it must `UPDATE public.sunners.secret_box_unopened_count`, and that table intentionally carries no `UPDATE` policy at all, so RLS cannot be the containment here. Takes **zero parameters** — the actor comes only from `auth.uid()`. In one transaction: resolves/provisions the caller's `sunners` row (same idiom as `create_kudos`), guards the decrement with `secret_box_unopened_count > 0` inside the `UPDATE` itself (closes a two-tab race), draws one badge from `secret_box_badge_odds` join `rule_items` by relative weight, inserts one `secret_box_openings` row, returns the badge + both new counters. Raises `28000` when unauthenticated, `P0002` when no unopened boxes remain. |

## Background Jobs

None. There is no cron, no queue worker, no scheduled task anywhere in the repo — confirmed by
absence of any `scheduled-job`/`queue-worker` pattern in `app/` or `lib/` (scout-report.md §5, §9).

## Webhooks / External Calls

| Direction | Target / Source | Event / Endpoint | Description |
|-----------|------------------|-------------------|--------------|
| outgoing | Supabase Auth (GoTrue) | `signInWithOAuth`, `exchangeCodeForSession`, `getUser`, `signOut` | Every Supabase call outside `lib/kudos/` is `auth.*`. |
| outgoing | Supabase Postgres (PostgREST, F004) | `.from(table).select/insert/delete` on 10 `public.*` tables via `supabase-js` | Added by the Kudos Live Board — `lib/kudos/queries.ts` (reads), `toggle-kudos-like.ts` (the one write). Bound by RLS, never `service_role`; see `permissions-matrix.md` PERM006/PERM007. |
| outgoing | Supabase Postgres RPC (F005) | `supabase.rpc("create_kudos", {...})` | `createKudos`'s multi-table write — see the Postgres RPC table above. Bound by RLS same as any other role-scoped call (`security invoker`); see `permissions-matrix.md` PERM009. |
| outgoing | Supabase Postgres RPC (F009, `security definer`) | `supabase.rpc("open_secret_box")` | `openSecretBox`'s single-writer call — see the Postgres RPC table above. **Not** bound by RLS (runs as the function owner); containment is the pinned `search_path`, zero parameters, and `EXECUTE` revoked from `anon`/`public`. See `permissions-matrix.md` PERM018. |
| outgoing | Supabase Storage (F005, first object-storage integration) | `.storage.from("kudos-attachments").upload(...)` / `.getPublicUrl(...)` | `uploadKudosImage` writes objects under `{user.id}/...`; the bucket is public-read so board cards can render permanent image URLs. `next.config.ts`'s `images.remotePatterns` was extended to allow `next/image` to serve from this host. See `permissions-matrix.md` PERM010. |
| outgoing (transitive) | Google OAuth | consent screen + token exchange | Reached **only through** Supabase — no Google SDK, no direct Google API call anywhere in the codebase (`config.toml:336-338`). |
| incoming | none | — | No incoming webhook exists — `/auth/callback` is a browser redirect target (302 round-trip via the user's browser), not a server-to-server webhook receiver. |

## Summary

| Category | Count |
|----------|-------|
| Route handlers (app's own API surface) | 1 |
| Server actions | 7 |
| Postgres RPCs | 2 (`create_kudos`, `open_secret_box`) |
| Background jobs | 0 |
| Outgoing integrations | 5 (Supabase Auth direct, Supabase Postgres/PostgREST direct, Supabase Postgres RPC, Supabase Storage direct, Google OAuth transitive) |
| Incoming webhooks | 0 |
