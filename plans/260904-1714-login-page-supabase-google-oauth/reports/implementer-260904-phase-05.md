# Implementer report — Phase 05: proxy route guard, /todo, sign-out

## Files Touched

- `proxy.ts` (57 lines) — added `redirectWithSessionCookies()` helper and the two-prefix guard
  (`/todo` unauthenticated → `/login`; `/login` authenticated → `/todo`). Kept the existing
  `matcher` and `updateSession()` call untouched; now destructures `user` too.
- `app/todo/page.tsx` (created, 44 lines) — minimal authenticated Server Component: reads locale
  cookie, renders `dict.todo.title`, the signed-in email, and a `<form action={signOut}>` with a
  submit button.
- `app/todo/actions.ts` (created, 15 lines) — `signOut()` Server Action: `supabase.auth.signOut()`
  (its `{ error }` result deliberately ignored, not thrown, so an already-expired session still
  reaches `/login`) then `redirect("/login")` outside any try/catch.

No other files modified. `git status` confirms `lib/supabase/**`, `app/login/**`, `e2e/**` are
untouched by this session.

## Checks

- Typecheck: clean (`npx tsc --noEmit`, no errors)
- Lint: clean (`npm run lint`, no warnings/errors)
- E2E (`npm run test:e2e`, full suite): **12 passed, 0 failed**

### Per-case breakdown

| Case | Result |
|---|---|
| setup (auth.setup.ts) | pass |
| smoke.spec.ts | pass |
| C1 [FR-201, US003] | pass |
| C2 [FR-402, DEC-001] | pass |
| C3 [FR-203, US003] | pass |
| C4 [BR-003] | pass |
| C5 [FR-202, FR-601, SM-001, SC-003] | pass |
| **C6 [FR-101, FR-602, SC-001]** — unauth `/todo` → `/login` | **pass** |
| **C7 [FR-102, SC-002]** — auth `/login` → `/todo` | **pass** |
| **C8 [SC-001, proxy-cookie-rotation]** — cookie preservation across token refresh | **pass** |
| **C9 [FR-403, US004]** — sign-out then `/todo` bounces to `/login` | **pass** |
| C10 — callback open-redirect protection | pass |

## Acceptance Criteria

- [x] `proxy.ts` destructures `user` and keeps the existing `matcher` unchanged.
- [x] Every redirect built through `redirectWithSessionCookies` — zero bare `NextResponse.redirect`.
      Cookies are copied via `response.cookies.getAll()` iterated onto `redirectResponse.cookies.set(...)`
      (see deviation note below — `ResponseCookies` has no `.setAll`).
- [x] Guard limited to `/todo` and `/login`; `/auth/callback` provably unguarded — C10 and the OAuth
      redirect flow (C5) both pass, and the guard code only checks `startsWith("/todo")` /
      `startsWith("/login")`.
- [x] `/todo` renders title, email and a working sign-out form — C7, C8, C9 exercise this directly.
- [x] `signOut()` redirects outside try/catch and tolerates an expired session — no try/catch wraps
      `redirect()`; the `signOut()` call's error result is not thrown or inspected, so an
      already-invalid session still proceeds to `/login` (C9 passes with a fresh, non-expired
      session; the tolerance behavior itself follows directly from never throwing on that path).
- [x] `lib/supabase/**` untouched — confirmed via `git status`.
- [x] Typecheck + lint clean; all three files under 200 lines (57 / 44 / 15).

## Issues Encountered / Deviations

1. **Phase-file snippet used `redirectResponse.cookies.setAll(...)`, which does not exist on
   Next's `ResponseCookies` type** (`TS2551: Property 'setAll' does not exist on type
   'ResponseCookies'. Did you mean 'getAll'?`). Fixed by iterating `response.cookies.getAll()` and
   calling `redirectResponse.cookies.set(cookie)` per entry — same effect (every rotated cookie,
   name/value/options, copied onto the redirect response), just spelled with the API this Next
   version actually exposes. C8 (the test that specifically exercises this path with a
   deliberately expired access token) passes, confirming the copy is complete.
2. **Accessible-name conflict between the frozen i18n dictionary and the E2E's locale-independent
   probe.** `todo.signOut` resolves to `"Đăng xuất"` under the default `vi` locale (no locale
   cookie is set by `auth.setup.ts`), which does not match the required
   `/sign.?out|logout/i` accessible-name pattern. Resolved by keeping the dictionary-driven
   Vietnamese text as the visible label but adding a fixed `aria-label="Sign out"` on the button,
   with a comment explaining why — the accessible name needs to be discoverable independent of
   locale per this phase's explicit requirement, while the visible copy still honors
   `todo.signOut`. This is a deliberate, documented trade-off against strict "label matches
   accessible name" a11y practice, scoped to this placeholder page; flagging for reviewer/product
   awareness rather than silently picking a side.
3. `.env.local`, `lib/i18n/**`, `app/login/**` were read but not modified, consistent with file
   ownership.

**Status:** DONE
**Summary:** Route guard added to `proxy.ts` via a `redirectWithSessionCookies()` helper that
preserves rotated auth cookies on redirect; `/todo` page and `signOut()` Server Action implemented.
Typecheck, lint, and the full E2E suite (12/12, including C6–C9) all pass.
**Concerns/Blockers:** One documented trade-off — the sign-out button's `aria-label` is fixed to
English regardless of locale so the E2E can find it by role/name independent of the `vi` default,
while the visible label still uses the localized `todo.signOut` dictionary text. Flagging for
reviewer sign-off since it's a minor departure from strict accessible-name/visible-label parity.
