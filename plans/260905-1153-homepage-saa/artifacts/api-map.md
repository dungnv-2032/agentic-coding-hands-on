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

## Background Jobs

None. There is no cron, no queue worker, no scheduled task anywhere in the repo — confirmed by
absence of any `scheduled-job`/`queue-worker` pattern in `app/` or `lib/` (scout-report.md §5, §9).

## Webhooks / External Calls

| Direction | Target / Source | Event / Endpoint | Description |
|-----------|------------------|-------------------|--------------|
| outgoing | Supabase Auth (GoTrue) | `signInWithOAuth`, `exchangeCodeForSession`, `getUser`, `signOut` | Every Supabase call in the repo is `auth.*` — no Storage/Realtime/DB call, even though those surfaces are enabled in the local `config.toml` (unused). |
| outgoing (transitive) | Google OAuth | consent screen + token exchange | Reached **only through** Supabase — no Google SDK, no direct Google API call anywhere in the codebase (`config.toml:336-338`). |
| incoming | none | — | No incoming webhook exists — `/auth/callback` is a browser redirect target (302 round-trip via the user's browser), not a server-to-server webhook receiver. |

## Summary

| Category | Count |
|----------|-------|
| Route handlers (app's own API surface) | 1 |
| Server actions | 3 |
| Background jobs | 0 |
| Outgoing integrations | 2 (Supabase Auth direct, Google OAuth transitive) |
| Incoming webhooks | 0 |
