# Phase 05 — Track B: proxy route guard, /todo placeholder, sign-out

## Context Links

- Plan: [plan.md](./plan.md) · Research: [researcher-02 §Q4/§Q5/§Q7](./research/researcher-02-supabase-google-oauth.md)
- Spec: A0 (§4.4 Bin 3), A5, A6 in [technical-spec.md](./spec/login/technical-spec.md);
  [permissions.md](./spec/system/permissions.md); FR-101, FR-102, FR-403, FR-602, BR-002, US002, US004

## Overview

- **Priority:** P1 · **Owner agent:** `implementer` · **Status:** complete · **Effort:** 1.5h
- **Depends on:** 03 (needs `lib/i18n` for the placeholder copy). **Concurrent with:** 04.
  **Blocks:** 06.
- Add route protection to the existing `proxy.ts`, ship the minimal `/todo` landing page, and wire
  sign-out. This phase carries the single highest-risk change in the whole plan.

## Key Insights

- **The cookie-preservation bug is the plan's top risk.** `updateSession()` rebuilds its response
  object inside `setAll` every time GoTrue rotates a refresh token. A bare
  `NextResponse.redirect(...)` is a *third* response that never received those cookies — the rotated
  tokens are dropped, and because Supabase refresh tokens are single-use, the already-consumed token
  in the browser logs the user out on the very next request. The redirect response **must** inherit
  `response.cookies.getAll()`.
- Guard on explicit prefixes, not on "everything the matcher touches". The spec puts `/` and any
  other route out of scope; `/auth/callback` in particular must never be guarded or the OAuth
  round-trip cannot complete.
- `getUser()` stays in `update-session.ts` (ORCH-04). Do not switch to `getClaims()`, and do not
  modify `lib/supabase/**` at all — `updateSession` already returns the `user` this guard needs.
- `signOut()` clears the session cookies through the same adapter; the next guarded request then
  redirects on its own. No extra proxy logic is needed for US004.

## Requirements

- FR-101 / FR-602 — no session + `/todo` → `/login`.
- FR-102 — session + `/login` → `/todo`.
- FR-403 / US004 — sign-out ends the session and lands on `/login`; an already-expired session must
  still land on `/login` without surfacing an error.
- Non-functional: rotated auth cookies survive every guarded redirect.

## Architecture

```
request ─► proxy(request)
             │ const { response, user } = await updateSession(request)   // rotates tokens onto `response`
             ├ !user && /todo   ─► redirectWithCookies('/login')   ─┐
             ├  user && /login  ─► redirectWithCookies('/todo')    ─┤ both inherit response.cookies.getAll()
             └ otherwise        ─► response                        ─┘

/todo ─(form action)─► signOut() ─► supabase.auth.signOut() ─► redirect('/login')
```

## Related Code Files

**Modify:** `proxy.ts` (extend, do not replace; keep the existing `matcher`)
**Create:** `app/todo/page.tsx`, `app/todo/actions.ts`
**Explicitly NOT owned:** `lib/supabase/**` (contract frozen, ORCH-04), `app/login/**` (phases 03/04),
`e2e/**` (tester).

## Implementation Steps

1. In `proxy.ts`, destructure both values: `const { response, user } = await updateSession(request);`
   and replace the outdated "route protection is NOT wired up yet" comment with what the guard now does.
2. Add a local helper — the one step that defuses the top risk:
   ```ts
   const redirectWithSessionCookies = (pathname: string) => {
     const url = request.nextUrl.clone();
     url.pathname = pathname;
     url.search = "";
     const redirectResponse = NextResponse.redirect(url);
     // Carry over the tokens updateSession() just rotated. A bare NextResponse.redirect
     // drops them, and single-use refresh tokens then log the user out next request.
     redirectResponse.cookies.setAll(response.cookies.getAll());
     return redirectResponse;
   };
   ```
3. Guard on explicit prefixes only:
   `if (!user && pathname.startsWith("/todo")) return redirectWithSessionCookies("/login");`
   `if (user && pathname.startsWith("/login")) return redirectWithSessionCookies("/todo");`
   `return response;` — `/`, `/auth/**` and everything else fall through untouched.
4. `app/todo/page.tsx` — Server Component: `await createClient()`, `getUser()`, render
   `dict.todo.title`, the signed-in email, and a `<form action={signOut}>` submit button labelled
   `dict.todo.signOut`. Locale via `resolveLocale((await cookies()).get(LOCALE_COOKIE)?.value)`.
   Minimal markup, no styling ambition — it exists to prove FR-403 and the guard.
5. `app/todo/actions.ts` (`"use server"`) — `signOut()`: `await supabase.auth.signOut()` then
   `redirect("/login")`, the redirect **outside** any try/catch. Ignore a `signOut` error path
   deliberately: an expired session must still land on `/login` (US004 error scenario).
6. Verify manually before handing off: with the phase-02 storageState cookies, hit `/login` (expect
   `/todo`), reload `/todo` twice (expect still authenticated), then sign out (expect `/login`, and
   `/todo` then bounces).
7. `npx tsc --noEmit` and `npm run lint` clean.

## Todo List

- [x] `proxy.ts` destructures `user` and keeps the existing `matcher` unchanged
- [x] Every redirect built through `redirectWithSessionCookies` — zero bare `NextResponse.redirect`
- [x] Guard limited to `/todo` and `/login`; `/auth/callback` provably unguarded
- [x] `/todo` renders title, email and a working sign-out form
- [x] `signOut()` redirects outside try/catch and tolerates an expired session
- [x] `lib/supabase/**` untouched (`git status` proves it)
- [x] typecheck + lint clean; files under 200 lines

## Success Criteria

- E2E C6 (FR-101/FR-602), C7 (FR-102), C8 (cookie preservation) and C9 (FR-403) pass at phase 06.
- `curl -i -H "Cookie: <captured session>" http://127.0.0.1:3000/login` → 307 `/todo` **and** the
  response still carries the `sb-…-auth-token` `Set-Cookie` when a rotation occurred.
- Three consecutive authenticated `/todo` loads never bounce to `/login`.

## Risk Assessment

| ID | Risk | Likelihood | Impact | Countermeasure |
|----|------|-----------|--------|----------------|
| R1 | Bare `NextResponse.redirect` drops rotated cookies → intermittent logout, invisible in a single-request test | Medium | Critical | Dedicated helper (step 2) + dedicated E2E case C8 that loads a guarded page repeatedly, not once |
| R2 | Guard accidentally covers `/auth/callback` → OAuth can never complete | Low | Critical | Explicit prefix list, plus C10 exercising the callback unauthenticated |
| R3 | Redirect loop `/login` ⇄ `/todo` if the user check disagrees between guard and page | Low | High | One authority only: `updateSession()`'s `user`; pages never re-guard |
| R4 | Guard applied to `/` breaks the untouched default landing page | Low | Medium | Prefix guard, never a catch-all; smoke test on `/` stays green |
| R5 | `url.search` carried into the redirect leaks `?error=oauth_failed` onto `/todo` | Low | Low | `url.search = ""` in the helper |

## Security Considerations

- `/todo` is protected before render (permissions.md route-guard) — no content leaks pre-redirect.
- Session validity is decided by `getUser()`, which round-trips to GoTrue and therefore detects
  server-side revocation; `getSession()` must not appear anywhere in this phase.
- Sign-out clears cookies through the library's own adapter — no manual cookie deletion.

## Rollback

`git checkout -- proxy.ts` and delete `app/todo/`. The app reverts to session-refresh-only, `/login`
from phase 04 still renders, and only the guard/sign-out E2E cases regress to RED.

## Next Steps

Phase 06 reruns the exact `redCommand` for GREEN and performs visual validation.
