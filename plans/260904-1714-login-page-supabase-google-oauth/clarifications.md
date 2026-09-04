# Clarifications — Login Screen (SAA 2025)

- **Screen:** Login — https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/GzbNeVGJHz
- **fileKey:** `9ypp4enmFmdK3YAFJLIu6C` · **screenId:** `GzbNeVGJHz` · **figma node:** `662:14387`
- **Design revision:** `9b6a80531ed3a0744c2a0c2ed06a55af`
- **Source data:** 8 spec items, 17 test cases (downloaded to `design/`)
- **testPolicy:** `e2e-red-first`

## Session 2026-09-04

- Q: SDD mode for this project? → A: **On** — spec-first, persisted to `.claude/.tkm.json`.
- Q: Spec/doc prose language? → A: **Tiếng Việt** (`spec_lang: vi`, bootstraps `primary_lang`).
- Q: Test policy — behavioral test cases auto-select `e2e-red-first`, but no E2E runner exists. → A: **Add `@playwright/test`, run `e2e-red-first`.** Tester owns a screen-level E2E that must fail RED on the login assertions before any UI/backend code, then rerun GREEN. Constrains: implementation cannot start until valid RED evidence exists.
- Q: Local Supabase has no `[auth.external.google]`; Google OAuth needs a Google Cloud client ID + secret. → A: **Wire config + env placeholders.** Add `[auth.external.google]` to `supabase/config.toml` reading `SUPABASE_AUTH_EXTERNAL_GOOGLE_CLIENT_ID` / `_SECRET`, set `skip_nonce_check = true` (required for local Google sign-in), document in `.env.example`. Constrains: the real Google round-trip is not automatable in E2E — see Assumption A1.
- Q: i18n scope for the VN/EN language selector. → A: **Lightweight cookie + typed dictionary**, no library. `NEXT_LOCALE` cookie read server-side; `vi`/`en` message module. Constrains: no locale routing segments, no `next-intl`.
- Q: How far to take routing, given `/todo` does not exist? → A: **Stub `/todo` + guard in `proxy.ts`.** Authenticated on `/login` → `/todo`; unauthenticated on `/todo` → `/login`. Constrains: `proxy.ts` gains route protection, which it currently disclaims.

## Resolved from source data (no user input needed)

- Error copy on failed/cancelled Google auth: `"Đăng nhập không thành công. Vui lòng thử lại."` (spec item 2.2.1, `validationNote`).
- OAuth callback route: `/auth/callback` — already present in `additional_redirect_urls` in `supabase/config.toml`.
- Logo is **non-interactive** (test case `b9805e65`), despite spec item 1.1 marking click behavior "chưa rõ".
- Footer is fixed at the bottom and non-interactive (test case `33a1dacf`).
- Default language is `VN` with flag left + chevron right (test cases `5f1cbabd`, `98e20775`).
- Login button: disabled + loading indicator while authenticating (`37eae882`); shadow/elevation on hover (`c18649fa`).
- All Google accounts are permitted — no domain allow-list (spec item 2.2.1, `transitionNote`).
- Assets available from MoMorph: `MM_MEDIA_Logo`, `MM_MEDIA_VN`, `MM_MEDIA_Down`, `MM_MEDIA_Root Further Logo`, `MM_MEDIA_Google`. "ROOT FURTHER" is an image, not text.

## Assumptions

- **A1 — E2E cannot complete a real Google round-trip.** Google's consent screen is not automatable and local Supabase has no mock provider. The RED/GREEN E2E therefore asserts what *is* observable: the screen renders per spec, an unauthenticated visitor sees `/login`, clicking the button initiates a redirect toward the Supabase authorize endpoint with `provider=google`, an authenticated session on `/login` is bounced to `/todo`, and an unauthenticated hit on `/todo` is bounced to `/login`. Authenticated-state tests seed the session directly against local Supabase rather than through Google.
- **A2 — Playwright MCP failed to connect this session** (`CONNECT_TIMEOUT`). `@playwright/test` is independent of it, so `e2e-red-first` is unaffected; only the tester's MCP-driven visual validation may need a retry.

## Unresolved questions

- None blocking. Logo click-through remains "unclear" in the spec but the test case settles it as non-interactive.

## Orchestrator decisions on research findings (2026-09-04)

> Numbered `ORCH-xx` on purpose. `DEC-###` is a reserved canonical code token that the feature spec
> uses for branch decision points (`DEC-001`, `DEC-002` in `functional-spec.md` / `technical-spec.md`),
> so these orchestrator-level decisions must not reuse it.

Two items were flagged by the Supabase research as needing a call before implementation. Both are
internal test-infrastructure choices with no effect on shipped behavior, so they are settled here
rather than escalated.

- **ORCH-01 — No test hook in application code.** The research recommended exposing
  `window.__supabase` (non-prod only) so Playwright could call `setSession()` inside a live page,
  with a dev-only `/api/test/session` route as the alternative. **Both are rejected**: each leaks a
  testing affordance into shipped application code, and a route that mints sessions is an auth
  surface we would then have to defend. Instead the E2E global setup instantiates
  `createServerClient` from `@supabase/ssr` **in Node**, backed by an in-memory cookie jar, calls
  `setSession()` on it, and captures exactly the cookies the library itself writes — then feeds
  them into Playwright `storageState`. This reuses `@supabase/ssr`'s own encoding (chunking,
  base64url) without hand-rolling it and without touching `app/`. If it proves unworkable, fall
  back to the dev-only route — never to the `window` hook.
- **ORCH-02 — E2E users are created with the anon key, not `service_role`.** The research assumed
  `auth.admin.createUser`, which needs the `service_role` key. That is unnecessary here: this
  stack has `enable_signup = true` and `[auth.email] enable_confirmations = false`, so a plain
  `signUp()` on the publishable key returns a usable session immediately. This also respects the
  deliberate decision recorded in `.env.example` that the `service_role` key is "NOT listed here on
  purpose" — the E2E suite introduces no reason to walk that back.
- **ORCH-03 — Add `NEXT_PUBLIC_SITE_URL`.** Needed for the OAuth `redirectTo` origin. Set to
  `http://127.0.0.1:3000` locally, matching `site_url` and the entries already in
  `additional_redirect_urls`. Chosen over deriving the origin from request headers because the
  value must match Supabase's redirect allow-list exactly, and an explicit env var makes that
  correspondence visible.
- **ORCH-04 — Keep `getUser()` in `update-session.ts`.** The current official Supabase example has
  moved to `getClaims()`, which validates the JWT locally and skips the network round-trip. That is
  a latency optimization that trades away real-time revocation detection, and nobody asked for it.
  Out of scope.

## Assumptions (added)

- **A3 — `skip_nonce_check = true` is doc-sourced, not verified.** It comes from the Supabase CLI's
  own generated annotation ("Required for local sign in with Google auth") and the upstream CLI
  template, cross-checked; but no live Google round-trip has exercised it, because no Google Cloud
  credentials exist yet. Worth a manual smoke test the first time real credentials are pasted in.
  Note the official generic docs example shows `false` — a documented upstream inconsistency, not
  an error on our side.

## Empirical verification of ORCH-01 / ORCH-02 (2026-09-04, against the running local stack)

Both decisions were probed against the live local Supabase stack before being handed to the planner,
so the E2E design does not rest on assumption.

**ORCH-02 — `signUp()` on the publishable key returns a session immediately.** Confirmed:
`POST /auth/v1/signup` returned `access_token`, `token_type: bearer`, `expires_in: 3600` and a user
id on the first call. No `service_role` key was involved. The E2E suite can therefore mint its own
fixture users with the key already in `.env.local`.

**ORCH-01 — the Node-side cookie capture works.** A throwaway probe instantiated
`createServerClient` from `@supabase/ssr` in plain Node against an in-memory `Map` cookie jar,
called `signUp()`, and captured everything the library wrote:

```
sb-127-auth-token-flow-<hash>-code-verifier    159 bytes
sb-127-auth-token-flows-code-verifier           55 bytes
sb-127-auth-token-code-verifier                159 bytes
sb-127-auth-token                             2886 bytes   ← the session cookie
round-trip getUser(): OK (same user id)
```

Feeding those cookies into a second, fresh client and calling `getUser()` returned the same user —
so the captured set is a complete, loadable session. Two things this settles:

1. The cookie-name prefix on this stack really is **`sb-127-auth-token`** (derived from the
   `127.0.0.1` host), not `sb-<project-ref>-auth-token`. Nothing should hardcode it — the capture
   approach reads whatever the library chooses.
2. At 2886 bytes the session cookie sits just under `@supabase/ssr`'s ~3180-byte chunking
   threshold. Hand-crafting this value would have been one claim or one longer email address away
   from silently crossing into multi-chunk encoding and breaking. Delegating the encoding to the
   library is what makes the fixture durable.

## Session 2026-09-04 (rest point)

- Q: Study + Spec rest point — proceed to Blueprint? → A: **Approved.**
- Q: How to handle the un-exportable hero artwork (RISK-01)? → A: **ORCH-05 — build around it, retry
  later.** Implement the hero as a full-bleed layer carrying the geometry recorded from node
  `662:14389` (1441×1022 at top 2px/left 0; `background-position: -440px -217.975px`;
  `background-size: 159.763% 133.371%`; `no-repeat`) over a solid dark-navy fallback matching the
  design's base tone. Constrains: the image must be referenced as `public/images/login/hero.png` and
  wired so that dropping the file in later is a **one-file change requiring no code edit** — do not
  inline a gradient "lookalike" of the artwork, which would have to be unpicked later. RISK-01 stays
  open until the real asset lands.

## Watch items raised during the forge (for the Inspect stage)

- **W1 — `nextUrl.origin` rewrites loopback hosts, and the fix has a trade-off.** Phase 03 found that
  Next 16 rewrites any loopback hostname to the literal `localhost`
  (`node_modules/next/dist/server/web/next-url.js:15,19` — the regex matches `127.x.x.x`, `[::1]` and
  `localhost`, then assigns `parsed.hostname = 'localhost'`). Because this project pins cookies and
  `site_url` to `127.0.0.1`, using `request.nextUrl.origin` would have produced a mismatched origin and
  broken the session. Verified independently — a real and well-found bug. The fix derives the origin
  from the raw `Host` header instead. **The reviewer must check this:** a `Host` header is
  client-controllable, so deriving a redirect origin from it is the classic Host-header-injection
  shape. It is acceptable here because Supabase independently validates `redirect_to` against
  `additional_redirect_urls`, and because the value is only used to build a same-origin callback URL —
  but confirm that reasoning holds in the code as written, and that nothing else trusts that origin.
- **W2 — `.env.local` was edited by phase 03** to add `NEXT_PUBLIC_SITE_URL`, which sits outside that
  phase's declared file ownership. Gitignored local config, needed for `signInWithGoogle` to work at
  all, and disclosed rather than hidden. Accepted; noted so the ownership deviation is on the record.
