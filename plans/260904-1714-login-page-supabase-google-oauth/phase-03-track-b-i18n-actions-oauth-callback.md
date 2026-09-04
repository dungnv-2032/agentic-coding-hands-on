# Phase 03 — Track B: i18n module, Server Actions, OAuth callback

## Context Links

- Plan + frozen contract: [plan.md](./plan.md)
- Research: [researcher-02 §Q2/§Q3](./research/researcher-02-supabase-google-oauth.md), [researcher-01 §3/§5/§9](./research/researcher-01-nextjs16-conventions.md)
- Spec: A2, A3, A4 in [technical-spec.md](./spec/login/technical-spec.md); FR-202, FR-203, FR-401, FR-402, FR-601, BR-003, DEC-002

## Overview

- **Priority:** P1 · **Owner agent:** `implementer` (generic, normal RED-first contract) · **Status:** complete · **Effort:** 2h
- **Depends on:** 02 (valid RED evidence). **Runs concurrently with:** 04 (Track A). **Blocks:** 05.
- Behaviour and backend for the login flow: locale resolution, the two `/login` Server Actions, and
  the `/auth/callback` route handler.

## Key Insights

- `redirect()` throws `NEXT_REDIRECT` — it must sit **outside** any try/catch, or the redirect is
  swallowed and reported as an error.
- The server client (`lib/supabase/server.ts`) does **not** navigate: `signInWithOAuth` returns
  `data.url` and the action redirects to it. One cookie adapter, one code path (ORCH-recorded).
- Route handlers read query params from `request.nextUrl.searchParams`; there is no `searchParams`
  prop. `cookies()` is async and writable only here and in Server Actions.
- `redirectTo` must be `${NEXT_PUBLIC_SITE_URL}/auth/callback` — an exact match against Supabase's
  allow-list, which is why ORCH-03 made the origin an explicit env var.
- Track A is writing `app/login/page.tsx` at the same time and imports from these files. Land
  `lib/i18n/**` and `app/login/actions.ts` **first** inside this phase so the contract materialises
  early; transient type errors on the other track before that are expected and resolve at phase 06.

## Requirements

- FR-203 / BR-003 — `NEXT_LOCALE` cookie drives a typed vi/en dictionary; missing or invalid value
  falls back to `vi`. No i18n library, no locale path segment.
- FR-202 / FR-601 / BR-001 — the kickoff action starts Google OAuth with no domain allow-list check.
- FR-401 / FR-402 / DEC-002 — callback exchanges `code` → `/todo`; `error` or a failed exchange →
  `/login?error=oauth_failed`.
- Non-functional: every file under 200 lines, kebab-case, real implementations only.

## Architecture

```
cookie NEXT_LOCALE ─► resolveLocale() ─► getDictionary(locale) ─► (consumed by Track A page.tsx)

click ─► signInWithGoogle()  ─► supabase.auth.signInWithOAuth({provider:'google', redirectTo})
                              └─► redirect(data.url)  ──► Google ──► GET /auth/callback
                                                                        │ code  ─► exchangeCodeForSession ─► /todo
                                                                        │ error ─► /login?error=oauth_failed
select ─► setLocale('en'|'vi') ─► cookies().set('NEXT_LOCALE', …) ─► route re-renders
```

## Related Code Files

**Create:** `lib/i18n/locales.ts`, `lib/i18n/dictionaries.ts`, `lib/i18n/messages/vi.ts`,
`lib/i18n/messages/en.ts`, `app/login/actions.ts`, `app/auth/callback/route.ts`
**Modify:** none
**Explicitly NOT owned (Track A owns them):** `app/login/page.tsx`, `app/login/_components/**`,
`app/globals.css`, `public/images/login/**`. **Also not owned:** `proxy.ts`, `app/todo/**` (phase 05),
`e2e/**` (tester).

## Implementation Steps

1. `lib/i18n/locales.ts` — `export type Locale = "vi" | "en"`, `LOCALES`, `DEFAULT_LOCALE = "vi"`,
   `resolveLocale(value?: string): Locale` returning `DEFAULT_LOCALE` for anything not in `LOCALES`.
   Export `LOCALE_COOKIE = "NEXT_LOCALE"`. Pure — no `next/headers` import, so tests and both
   runtimes can use it.
2. `lib/i18n/messages/vi.ts` — the authoritative copy, verbatim from the spec:
   `login.subtitle` "Bắt đầu hành trình của bạn cùng SAA 2025.", `login.tagline` "Đăng nhập để khám phá!",
   `login.signInButton` "LOGIN With Google", `login.errorOauthFailed` "Đăng nhập không thành công. Vui lòng thử lại.",
   `footer.copyright` "Bản quyền thuộc về Sun* © 2025", plus `login.logoAlt`, `login.wordmarkAlt`,
   `login.languageLabel`, `login.languageVi` ("VN"), `login.languageEn` ("EN"), `todo.title`, `todo.signOut`.
3. `lib/i18n/messages/en.ts` — same shape, typed as the `vi` module's type so a missing key is a
   compile error. Keep `login.signInButton` as "LOGIN With Google" (it is design copy, not prose).
4. `lib/i18n/dictionaries.ts` — `import "server-only"`, static map `{ vi, en }`, `getDictionary(locale)`.
   Static import, not dynamic — two tiny modules, YAGNI on lazy loading.
5. `app/login/actions.ts` (`"use server"`):
   - `signInWithGoogle()` — `const supabase = await createClient()`; call `signInWithOAuth({ provider: "google", options: { redirectTo: \`${process.env.NEXT_PUBLIC_SITE_URL}/auth/callback\` } })`;
     `if (error || !data.url) redirect("/login?error=oauth_failed")`; then `redirect(data.url)`.
     **No try/catch anywhere around a redirect.** No domain filtering (BR-001/FR-601).
   - `setLocale(locale: string)` — `resolveLocale`, then `(await cookies()).set(LOCALE_COOKIE, next, { path: "/", maxAge: 60*60*24*365, sameSite: "lax" })`.
     Setting a cookie in a Server Action re-renders the route; if the selector does not refresh in
     practice, add `revalidatePath("/login")` — do not reach for a client-side router hack.
6. `app/auth/callback/route.ts` — `export async function GET(request: NextRequest)`:
   - read `code`, `error` from `request.nextUrl.searchParams`; `origin` from `request.nextUrl.origin`.
   - `next` param defaults to `/todo` and is rejected unless it starts with `/` (open-redirect guard,
     case C10).
   - `error` present → `NextResponse.redirect(\`${origin}/login?error=oauth_failed\`)` (fixed code per
     DEC-002; the user-facing string lives in the dictionary, not the URL).
   - `code` present → `exchangeCodeForSession(code)`; success → redirect to `next`, honouring the
     `x-forwarded-host` branch from researcher-02 §Q3 (inert locally, kept for a real host);
     failure → `/login?error=oauth_failed`.
   - no `code` and no `error` → `/login?error=oauth_failed`.
7. `npx tsc --noEmit` and `npm run lint` clean for the files this phase owns.

## Todo List

- [x] `resolveLocale` falls back to `vi` for `undefined`, `""`, `"xx"` (BR-003)
- [x] vi/en dictionaries share one type; copy matches the spec character for character
- [x] `signInWithGoogle` redirects to `data.url`, no try/catch around any redirect
- [x] `setLocale` validates before writing `NEXT_LOCALE`
- [x] callback handles `code`, `error`, neither; `next` validated to start with `/`
- [x] typecheck + lint clean; no file over 200 lines

## Success Criteria

- E2E cases C2, C3, C4, C5 and C10 from phase 02 turn GREEN once Track A's markup lands (C1/C3 need
  the page; C5 needs the button) — measured at phase 06, not asserted here.
- `curl -i "http://127.0.0.1:3000/auth/callback?error=access_denied"` → 307 to `/login?error=oauth_failed`.
- `curl -i "http://127.0.0.1:3000/auth/callback?error=access_denied&next=https://evil.com"` → target
  origin is this app, never `evil.com`.

## Risk Assessment

| ID | Risk | Likelihood | Impact | Countermeasure |
|----|------|-----------|--------|----------------|
| R1 | `redirect()` wrapped in try/catch → OAuth kickoff silently dies | Medium | High | Explicit step 5 rule; reviewer checks for `try` in `actions.ts` |
| R2 | `NEXT_PUBLIC_SITE_URL` unset at runtime → `redirectTo` becomes `undefined/auth/callback`, Supabase rejects it | Medium | High | Fail fast: throw a named error if the env var is missing, rather than composing a broken URL |
| R3 | Track A imports a dictionary key this phase did not ship | Medium | Medium | The key list is frozen in plan.md; both tracks read it from there |
| R4 | Setting a cookie in a Server Action does not visibly re-render for the selector | Low | Medium | Documented `revalidatePath("/login")` fallback in step 5 |

## Security Considerations

- Open-redirect guard on `next` (step 6) — the only user-controlled redirect target in the feature.
- No domain allow-list by design (FR-601/BR-001); do not add one.
- The error surface is a fixed code plus fixed copy — no provider error text is reflected to the user
  or into the URL.
- Cookie is written with `path=/` and `sameSite=lax`; it carries no user data beyond the locale.

## Rollback

Delete the six created files. `proxy.ts` is untouched, so the app returns to its pre-phase state and
only the RED suite regresses to its phase-02 baseline.

## Next Steps

Phase 05 consumes `lib/i18n` for the `/todo` placeholder and adds the route guard.
