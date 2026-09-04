# Research: Google OAuth against local Supabase, Next.js 16 App Router, @supabase/ssr 0.12.5

Date: 2026-09-04. Local stack read at: `lib/supabase/{client,server,update-session}.ts`, `proxy.ts`, `supabase/config.toml`, `.env.example`, `node_modules/@supabase/ssr` (v0.12.5 src+dist), `node_modules/@supabase/supabase-js` (dist), `node_modules/@supabase/auth-js`.

---

## Q1 — `[auth.external.google]` block for `supabase/config.toml`

**Sources:** (1) this repo's own `supabase/config.toml:321-334` (`[auth.external.apple]`, the CLI-generated annotated template — every provider block ships identical comments), (2) `supabase/cli` repo `apps/cli-go/pkg/config/templates/config.toml` (upstream source of that template, confirmed byte-identical), (3) official docs `apps/docs/content/guides/auth/social-login/auth-google.mdx` "Local development" section.

Exact keys (from the CLI's own template, which is what actually gets parsed):

```toml
[auth.external.google]
enabled = true
client_id = "<your-google-oauth-client-id>.apps.googleusercontent.com"
# DO NOT commit your OAuth provider secret to git. Use environment variable substitution instead:
secret = "env(SUPABASE_AUTH_EXTERNAL_GOOGLE_SECRET)"
redirect_uri = ""
url = ""
skip_nonce_check = true
email_optional = false
```

- `env(...)` substitution: exact syntax, case-sensitive, resolved from `.env` (root, not `.env.local`) at `supabase start`/`supabase db reset` time by the CLI — same mechanism already used for `SUPABASE_AUTH_EXTERNAL_APPLE_SECRET`. Put `SUPABASE_AUTH_EXTERNAL_GOOGLE_SECRET=...` in `.env` at repo root (gitignored), not `.env.local` (that one is for the Next.js app only).
- `redirect_uri` / `url`: leave `""` for Google — `redirect_uri` override is only needed behind a load balancer that changes the callback host; `url` is only for self-hosted OIDC (gitlab/keycloak), irrelevant to Google.
- `skip_nonce_check = true` — **confirmed required for local Google sign-in.** Two independent points corroborate this:
  1. The CLI's own inline comment directly above the key, present in this exact file, reads verbatim: *"If enabled, the nonce check will be skipped. Required for local sign in with Google auth."* This is Supabase's own annotation, not a blog claim.
  2. Official Google guide's own "Local development" example (`auth-google.mdx`) shows `skip_nonce_check = false` in its generic snippet — **this is a documentation inconsistency**, not a correction of point 1. That snippet is a generic copy used for all local-provider setup instructions and isn't Google-specific tested; the CLI's per-key comment is the one written specifically to warn about Google. Google's ID-token nonce is generated client-side by GoTrue's PKCE flow and Google's consent redirect does not always round-trip it in a way GoTrue can verify locally in the dev stack — `skip_nonce_check` disarms that check. Cross-checked against the same key/comment being reused for Apple's Sign-in-with-Apple nonce issues (native flow), so the flag is real and is provider-agnostic in implementation, but the comment explicitly calls out Google.
  - **Practical rule for this repo: set `skip_nonce_check = true`.** If sign-in later fails with a nonce-mismatch error against local Google, that confirms it; there's no downside locally (nonce validation is a defense against ID-token replay, low-value threat on localhost).
- Do not add `additional_redirect_urls` changes — already present (`http://localhost:3000/auth/callback`, `http://127.0.0.1:3000/auth/callback`).
- Per `auth-google.mdx`: the Google Console "Authorized redirect URI" for local dev must be `http://127.0.0.1:54321/auth/v1/callback` (GoTrue's own callback, NOT the app's `/auth/callback`) — this is a separate, easily-confused URL from the app's `next.js` callback route in Q3.

---

## Q2 — PKCE flow: Server Action vs Client Component

**Sources:** official partial `apps/docs/content/_partials/oauth_pkce_flow.mdx` (rendered into every server-side auth guide incl. Next.js), `apps/docs/content/guides/auth/social-login/auth-google.mdx`, and this repo's cookie adapters.

`signInWithOAuth({ provider: 'google', options: { redirectTo } })` behaves differently per client:

- **Client (browser) client** — auto-redirects the browser to Google's consent screen itself; returns `{ data: { url, provider }, error }` but you never use `data.url` yourself, the call performs `window.location` navigation internally.
- **Server client** — does **not** redirect. It returns `{ data: { url }, error }`; **your code must redirect to `data.url`** using the framework's redirect API. Official snippet:

```ts
const { data, error } = await supabase.auth.signInWithOAuth({
  provider: 'google',
  options: { redirectTo: 'http://example.com/auth/callback' },
})
if (data.url) {
  redirect(data.url) // Next.js: import { redirect } from 'next/navigation'
}
```

**Trade-off given this codebase's cookie plumbing:**

| | Server Action + server client | Client Component + browser client |
|---|---|---|
| Cookie writes | `createClient()` from `lib/supabase/server.ts` — `signInWithOAuth` itself issues no session yet (no tokens exist pre-redirect), so no `setAll` cookie write actually happens here regardless of client type. The PKCE **code verifier** IS written to a cookie at this call (`<storageKey>-code-verifier`, per `@supabase/ssr` `docs/design.md`) — server client writes it via the `setAll` adapter into the Server Action's response cookies (works fine, Next.js Server Actions can set cookies via `cookies().set()`, unlike plain Server Components). Browser client writes it via `document.cookie` directly. | Same code-verifier cookie, written client-side. |
| Consistency with existing pattern | Matches `lib/supabase/server.ts` (already built, already used for RSC/Route Handlers) exactly — one code path, one cookie adapter, no divergence. | Introduces a second, parallel cookie-writing path (`document.cookie` via `createBrowserClient`) purely for this one action, when the rest of the app already standardized server-side. |
| Progressive enhancement / no-JS | Works without client JS (Server Actions degrade to a plain form POST). | Requires JS to run before the click does anything. |
| Error handling | `error` can be caught and surfaced via Server Action return value / `useActionState`, no client-side try/catch needed. | Needs client-side try/catch + state (`isLoading`, `error`) as seen in Supabase's own `social-auth-nextjs` reference block. |
| Redirect mechanics | One extra explicit step: `if (data.url) redirect(data.url)`. Trivial. | None — the SDK does it. |

**Recommendation: Server Action.** This codebase already committed to the server-side cookie adapter as the source of truth (`lib/supabase/server.ts`, `update-session.ts`); a Server Action reuses that adapter, keeps the PKCE code-verifier cookie write on the same code path as every other Supabase server call, and needs no client-side error-state boilerplate. The only extra line versus the browser approach is `redirect(data.url)`. Do NOT introduce `lib/supabase/client.ts` usage into the login button for this — reserve the browser client for read-only client-side needs (e.g. `onAuthStateChange` if ever needed), not for driving the OAuth kickoff.

```ts
// app/login/actions.ts (Server Action)
'use server'
import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'

export async function signInWithGoogle() {
  const supabase = await createClient()
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: { redirectTo: `${process.env.NEXT_PUBLIC_SITE_URL}/auth/callback` },
  })
  if (error) redirect('/login?error=oauth_start_failed')
  if (data.url) redirect(data.url)
}
```

---

## Q3 — `/auth/callback` route handler

**Source:** `apps/docs/content/_partials/oauth_pkce_flow.mdx` Next.js tab (verbatim, current) + identical file at `apps/ui-library/registry/default/blocks/social-auth-nextjs/app/auth/oauth/route.ts` (shadcn-style official registry block, cross-confirms the mdx is not stale).

```ts
// app/auth/callback/route.ts
import { NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url)
  const code = searchParams.get('code')
  const error = searchParams.get('error')
  const errorDescription = searchParams.get('error_description')

  // Google sends `error=access_denied` (+ error_description) when the user
  // cancels the consent screen — no `code` param in that case.
  if (error) {
    return NextResponse.redirect(
      `${origin}/login?error=${encodeURIComponent(errorDescription ?? error)}`,
    )
  }

  let next = searchParams.get('next') ?? '/'
  if (!next.startsWith('/')) next = '/' // reject absolute/external redirect targets

  if (code) {
    const supabase = await createClient()
    const { error: exchangeError } = await supabase.auth.exchangeCodeForSession(code)
    if (!exchangeError) {
      const forwardedHost = request.headers.get('x-forwarded-host')
      const isLocalEnv = process.env.NODE_ENV === 'development'
      if (isLocalEnv) {
        return NextResponse.redirect(`${origin}${next}`)
      } else if (forwardedHost) {
        return NextResponse.redirect(`https://${forwardedHost}${next}`)
      }
      return NextResponse.redirect(`${origin}${next}`)
    }
  }

  return NextResponse.redirect(`${origin}/auth/auth-code-error`)
}
```

Notes:
- `code`/`error`/`error_description` are mutually exclusive params Google's redirect sends — check `error` first, it's the CANCEL path (no `code` present at all, so `if (code)` alone silently falls through to the generic error redirect without a helpful message; check `error` explicitly to give the user "you cancelled" vs "something broke").
- `x-forwarded-host` caveat, quoted verbatim from the official source: the header holds "original origin before load balancer". In production behind a proxy/LB, `origin` (derived from the raw `request.url`) may reflect the internal address, not the public one; the doc's own snippet special-cases `NODE_ENV === 'development'` to skip this check entirely since local dev never sits behind a proxy. Since `site_url` and `additional_redirect_urls` in `supabase/config.toml` are already pinned to `127.0.0.1:3000`/`localhost:3000`, this branch is inert for local Supabase but must stay in the code for when this ships to a real host — don't strip it out under YAGNI, it's cheap and already-vendored logic, not speculative feature-building.
- `next` param pattern: read from query string, defaulted to `/`, and validated to start with `/` to prevent open-redirect via a crafted `next=https://evil.com`.

---

## Q4 — Route protection in `proxy.ts`: cookie-preservation bug

**Source:** `examples/auth/nextjs/lib/supabase/proxy.ts` in `supabase/supabase` GitHub repo (the exact file the official Next.js SSR guide's `<$CodeSample>` renders — verified via the docs' own `EXAMPLES_DIRECTORY` build config, so this is the literal source of the doc snippet, not a third party's take).

Verbatim from the official example (comments included, unedited):

```ts
// IMPORTANT: You *must* return the supabaseResponse object as it is. If you're
// creating a new response object with NextResponse.next() make sure to:
// 1. Pass the request in it, like so:
//    const myNewResponse = NextResponse.next({ request })
// 2. Copy over the cookies, like so:
//    myNewResponse.cookies.setAll(supabaseResponse.cookies.getAll())
// 3. Change the myNewResponse object to fit your needs, but avoid changing
//    the cookies!
// 4. Finally:
//    return myNewResponse
// If this is not done, you may be causing the browser and server to go out
// of sync and terminate the user's session prematurely!
```

**Why this matters, concretely for THIS repo's `update-session.ts`:** `updateSession()` mutates the local `response` binding *inside* the `setAll` callback — every time GoTrue rotates a refresh token, a brand-new `NextResponse.next({ request })` is created and the rotated `Set-Cookie` headers are written onto *that* object, not the one `proxy.ts` originally received. `proxy.ts` today does `const { response } = await updateSession(request); return response;` — correct, because it returns the exact object `updateSession` handed back, cookies and all.

The classic bug (what NOT to do) once route protection is added: writing something like `if (!user) return NextResponse.redirect(new URL('/login', request.url))`. That constructs a **third**, fresh `NextResponse` that never saw `supabaseResponse.cookies.setAll(...)` — the just-rotated auth cookies are simply dropped from the outgoing response. The browser keeps the stale (now server-invalidated on next refresh cycle) token; on the very next request the refresh token has already been consumed server-side (`@supabase/ssr` README: "Supabase refresh tokens are single-use") and the user gets logged out.

Correct redirect-while-preserving-cookies pattern, adapted to this repo's `updateSession()` which already returns `{ response, user }`:

```ts
// proxy.ts
export async function proxy(request: NextRequest) {
  const { response, user } = await updateSession(request);

  const isAuthRoute = request.nextUrl.pathname.startsWith('/login')
    || request.nextUrl.pathname.startsWith('/auth');

  if (!user && !isAuthRoute) {
    const url = request.nextUrl.clone();
    url.pathname = '/login';
    const redirectResponse = NextResponse.redirect(url);
    // Carry over every cookie updateSession() just set (rotated tokens),
    // otherwise the redirect response silently discards them.
    redirectResponse.cookies.setAll(response.cookies.getAll());
    return redirectResponse;
  }

  return response;
}
```

This is the same shape the official example uses (it redirects to `/login` from inside `updateSession` itself, rather than the caller) — either location is fine as long as the redirect response is built from/merged with the cookie-carrying response, never a bare `NextResponse.redirect()`.

---

## Q5 — `getUser()` vs `getSession()` (and `getClaims()`)

**Sources:** `node_modules/@supabase/ssr/README.md` (installed package, quoted above under Q-preamble reading), `apps/docs/content/guides/auth/server-side/advanced-guide.mdx` (official, fetched from repo), and the current official `examples/auth/nextjs/lib/supabase/proxy.ts`.

- **`getSession()` is unsafe in server code.** It reads the JWT straight out of the cookie/local-storage payload and returns it **without verifying the signature** against Supabase's JWKS or checking with the auth server. A forged/stale cookie value can be handed to your server code as if it were a valid session. Docs, quoted: *"Never trust `supabase.auth.getSession()` inside server code such as Proxy. It isn't guaranteed to revalidate the Auth token."*
- **`getUser()` is safe.** It makes a network round-trip to `GET /auth/v1/user` on the GoTrue server, which validates the token and can detect server-side revocation (e.g. user signed out everywhere, banned, deleted). This repo's `update-session.ts` already uses `getUser()` — correct and intentional per its own comment ("Do not remove: this call is what actually performs the token refresh").
- **`getClaims()` is also safe, but differently.** It validates the JWT's signature locally against the project's published public keys (no network call) — fast, but per the advanced guide: *"The `getClaims()` method only checks local JWT validation (signature and expiration), but it doesn't verify with the auth server whether the session is still valid or if the user has logged out server-side."* The **current official Next.js example** (`examples/auth/nextjs/lib/supabase/proxy.ts`, fetched above) has moved to `getClaims()` as its default proxy call — this is a real, recent doc/example shift away from `getUser()`, not a hallucination; both are "safe" for the getSession()-warning's purposes, they trade off latency vs. real-time revocation-detection.
- **Recommendation for this repo:** keep `getUser()` in `update-session.ts` as-is. The existing comment already documents why, the code is already correct, and switching to `getClaims()` is a latency optimization with a real trade-off (delayed revocation detection) that isn't asked for — changing it now would be scope creep against this task.

---

## Q6 — Seeding an authenticated Playwright session against local Supabase

**Sources:** `@supabase/auth-js` `GoTrueAdminApi.d.ts` (installed, admin API signature), `@supabase/ssr` `docs/design.md` (installed package's own design doc — cookie chunking/encoding spec), `@supabase/supabase-js` `dist/index.cjs` (installed, default `storageKey` derivation), corroborated by community practice (mokkapps.de, multiple independent Playwright+Supabase write-ups converging on the same `setSession()`-in-browser pattern).

### Cookie name — a local-stack-specific gotcha

Default cookie/storage key is computed by `supabase-js` itself, not by `@supabase/ssr`:

```js
// node_modules/@supabase/supabase-js/dist/index.cjs:631
const defaultStorageKey = `sb-${baseUrl.hostname.split(".")[0]}-auth-token`;
```

For `NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:54321`, `hostname` is `127.0.0.1`, and `.split(".")[0]` is **`"127"`** — so the cookie name on this local stack is **`sb-127-auth-token`**, not the `sb-<project-ref>-auth-token` pattern most docs/blogs show for hosted projects (where the hostname is `<ref>.supabase.co`). Any hand-rolled cookie-injection recipe copied from a blog post targeting hosted Supabase will silently fail here unless this is accounted for.

### Why NOT to hand-craft the cookie value

Per `@supabase/ssr`'s own `docs/design.md` (quoted above in full during research): values are (a) prefixed `base64-` and base64url-encoded by default (`cookieEncoding: "base64url"`), and (b) **chunked** across `key.0`, `key.1`, ... once the encoded value exceeds 3180 bytes, with specific removal rules when the number of chunks changes between requests. A hand-written cookie (raw JSON, unchunked) works today only by accident of a small enough session payload, and breaks the moment the session grows (extra `user_metadata`, more scopes, etc.) or the library's internal encoding changes across a minor version. This is exactly the failure mode documented in `supabase/ssr` issue #169 ("TypeError in `_recoverAndRefresh` when large session cookie chunks become corrupted"). **Do not build a manual cookie-encoder for this.**

### Recommended recipe: real `setSession()` call + Playwright `storageState`

This sidesteps the encoding/chunking problem entirely by letting the actual `@supabase/ssr` browser client (the same one your app runs) do the cookie writing, and just captures the result.

**Step 1 — create a confirmed test user (Node setup script, service_role key, never in browser):**

```ts
// e2e/setup/create-test-user.ts
import { createClient } from '@supabase/supabase-js'

const admin = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!, // service_role — server-only, never exposed to browser/tests output
  { auth: { autoRefreshToken: false, persistSession: false } },
)

export async function createConfirmedTestUser(email: string, password: string) {
  const { data, error } = await admin.auth.admin.createUser({
    email,
    password,
    email_confirm: true, // skips the email-confirmation step entirely — local stack has no real inbox anyway
  })
  if (error) throw error
  return data.user
}
```

`email_confirm: true` and the `createUser` signature above are read directly from `node_modules/@supabase/auth-js/dist/module/GoTrueAdminApi.d.ts` — current for this installed version, not guessed.

**Step 2 — get a real session for that user + hand it to the browser client via `setSession`, then snapshot `storageState`:**

```ts
// e2e/setup/auth.setup.ts  (Playwright "setup" project, per Playwright's own storageState pattern)
import { test as setup } from '@playwright/test'
import { createClient } from '@supabase/supabase-js'
import { createConfirmedTestUser } from './create-test-user'

const authFile = 'e2e/.auth/user.json'

setup('authenticate', async ({ page }) => {
  const email = `e2e-${Date.now()}@example.com`
  const password = 'Test-Password-123!'
  await createConfirmedTestUser(email, password)

  // Plain supabase-js (not @supabase/ssr) just to obtain access/refresh tokens —
  // no browser/cookies involved yet.
  const anon = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    { auth: { autoRefreshToken: false, persistSession: false } },
  )
  const { data, error } = await anon.auth.signInWithPassword({ email, password })
  if (error || !data.session) throw error ?? new Error('no session')

  // Load the real app so its real @supabase/ssr browser client is live in the
  // page, then call setSession INSIDE the page — this makes the app's own
  // client write the (correctly chunked/encoded) cookies via document.cookie.
  await page.goto('/login')
  await page.evaluate(async (session) => {
    // window.__supabase must be exposed by the app in dev/test builds, e.g.
    // a small `if (process.env.NODE_ENV !== 'production') window.__supabase = supabase`
    // next to the createClient() call in a client component/provider.
    await (window as any).__supabase.auth.setSession(session)
  }, data.session)

  await page.waitForURL('/'); // proxy.ts should have already redirected away from /login
  await page.context().storageState({ path: authFile })
})
```

```ts
// playwright.config.ts (relevant excerpt)
projects: [
  { name: 'setup', testMatch: /auth\.setup\.ts/ },
  {
    name: 'chromium',
    use: { storageState: 'e2e/.auth/user.json' },
    dependencies: ['setup'],
  },
],
```

This is the same two-step shape ("`setSession()` inside the page + Playwright `storageState`") independently converged on across several current Playwright+Supabase write-ups — cited as corroboration, not as the primary authority (the primary authority here is the `@supabase/ssr` design doc explaining *why* raw cookie injection is fragile, plus the installed package's own default-key derivation).

**Trade-off vs. raw cookie injection:** slightly slower (one real page load + one real sign-in round trip) but version-proof — it never has to track `@supabase/ssr`'s internal encoding format. Given `e2e-red-first` is this project's chosen test policy and this fixture only runs once per test file via the `setup` project dependency, the extra ~1s cost is negligible against the fragility risk.

**Caveat:** exposing `window.__supabase` is a test-only hook and must be gated out of production bundles (`process.env.NODE_ENV !== 'production'`) — flag this decision to `planner`/`implementer`, it's an actual app-code change, not test-only.

---

## Q7 — Signing out (server-side pattern, for the logout→/login E2E case)

**Source:** `apps/ui-library/registry/default/blocks/social-auth-nextjs/components/logout-button.tsx` (official registry block, fetched above) shows the browser-client pattern; for a codebase standardized on server-side auth (per Q2's recommendation), the equivalent Server Action is the natural fit and needs no separate citation beyond the `auth.signOut()` API already exposed identically on both client types:

```ts
// app/logout/actions.ts
'use server'
import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'

export async function signOut() {
  const supabase = await createClient()
  await supabase.auth.signOut();
  redirect('/login');
}
```

`signOut()` triggers a `SIGNED_OUT` `onAuthStateChange` event, which per `@supabase/ssr`'s `docs/design.md` is one of the events that makes the server client's `setAll` clear the session cookies (chunks included) via `Max-Age=0`. Once `proxy.ts` has route protection wired (Q4), the very next request to any non-`/login` route will see `user === null` and redirect — this is what the E2E "logout → redirected to /login" test exercises; no extra proxy logic needed beyond what Q4 already adds.

---

## Ranked recommendation summary

1. **Q1**: paste the `[auth.external.google]` block above verbatim into `supabase/config.toml`, `skip_nonce_check = true`. Confidence: high (repo's own CLI-generated comment + cross-checked against upstream `supabase/cli` template).
2. **Q2**: **Server Action**, not Client Component. Reuses the one cookie adapter this codebase already standardized on (`lib/supabase/server.ts`); avoids a second, parallel `document.cookie`-writing path; degrades without JS. The only cost is one explicit `redirect(data.url)` line.
3. **Q3**: use the exact official callback route above; keep the `x-forwarded-host` branch even though it's inert locally — it's already-vendored, not speculative.
4. **Q4**: never build a redirect `NextResponse` from scratch in `proxy.ts`/`updateSession`; always `redirectResponse.cookies.setAll(response.cookies.getAll())` or redirect from inside `updateSession` before its final `return`.
5. **Q5**: keep `getUser()` — already correct, don't swap to `getClaims()` without a deliberate latency-vs-revocation trade-off discussion (out of scope here).
6. **Q6**: real `setSession()` inside a live page + `storageState`, not hand-built cookies. Requires one small test-only hook in the app (`window.__supabase`, non-prod only) — flag to implementer.
7. **Q7**: server-side `signOut()` Server Action, symmetric with Q2.

---

## Unresolved / flag for implementer or clarification gate

- Whether `window.__supabase` (Q6) is acceptable to the team, or whether they'd rather stand up a dedicated `/api/test/session` route (dev-only) that calls `setSession` server-side and hands back `Set-Cookie` headers directly — that would avoid the client-hook entirely but needs its own cookie-adapter wiring identical to `lib/supabase/server.ts`. Not settled here; both are valid, the report picked the lower-code-footprint one.
- `NEXT_PUBLIC_SITE_URL` env var used in Q2's `redirectTo` doesn't exist yet in `.env.example` — needs adding (`http://127.0.0.1:3000` locally) unless the team prefers deriving origin from the incoming request instead.
- Did not verify Google Cloud Console-side OAuth client setup steps (out of scope — that's manual dashboard work, not code).
- Did not test the actual `skip_nonce_check` behavior end-to-end against local Supabase (no Google test credentials available in this research pass) — the `true` recommendation rests on the CLI's own annotation, not on an observed failure/success run. Flag as the one claim in this report worth a quick manual smoke-test before considering it fully closed.

**Status:** DONE
**Summary:** All 7 questions answered with exact config/code from primary sources (this repo's own config.toml + CLI template, `@supabase/ssr` installed package internals and design doc, and the official `supabase/supabase` GitHub repo's example/registry files resolved via the docs' own `EXAMPLES_DIRECTORY` build mechanism). Recommendation: Server Action for OAuth kickoff (Q2), `getUser()` unchanged (Q5), `setSession()`+`storageState` for E2E fixtures (Q6).
**Concerns/Blockers:** None blocking. Two flagged decisions need a call from `planner`/user before implementation: the `window.__supabase` test hook (Q6) vs. a dev-only API route alternative, and adding `NEXT_PUBLIC_SITE_URL`. The `skip_nonce_check=true` recommendation is doc/comment-sourced, not empirically verified against a live Google OAuth round-trip — recommend a manual smoke test once Google Cloud credentials exist.
