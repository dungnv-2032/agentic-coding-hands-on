# RED Evidence — Phase 02 (e2e-red-first)

**Date:** 2026-09-04 (updated with corrected C3/C5 assertions)
**Command:** `npm run test:e2e`
**Exit code:** `1` (non-zero — valid RED, 4 failures)
**Test count:** 12 total tests
**Passed:** 8 (setup, smoke, C1, C2, C3, C4, C5, C10)
**Failed:** 4 (C6, C7, C8, C9)

---

## Valid RED Confirmation

This is a **valid RED** because:
1. ✓ Real non-zero exit code `1` caused by application-level assertion failures
2. ✓ Infrastructure is healthy: `smoke.spec.ts` passes in both `anon` and `authed` projects, proving the harness, browser, dev server, and Supabase are operational
3. ✓ The auth setup works: `auth.setup.ts` successfully creates a test user, captures cookies (`sb-127-auth-token`), and writes storageState for authenticated tests
4. ✓ C8 now properly exercises the risky code path: it traverses the guarded redirect from `/login` to `/todo` with an expired access token that forces cookie refresh, then verifies subsequent requests work with the refreshed cookies
5. ✓ C10 properly asserts open-redirect protection by checking the page origin, not substring matching
6. ✓ All failures are application-caused, not configuration/dependency/infrastructure failures

---

## Test Files

```
e2e/fixtures/supabase-session.ts    — Node fixture: creates users via signUp() on publishable key, captures cookies
e2e/auth.setup.ts                   — Playwright setup project: runs once, produces storageState at e2e/.auth/user.json
e2e/login-screen.spec.ts            — anon project: C1, C2, C3, C4, C5, C10
e2e/route-guard.spec.ts             — anon project: C6
e2e/authenticated.spec.ts           — authed project: C7, C8, C9
```

---

## RED Failures (by case)

### Harness Health & Passing Tests (8 PASSED)

| Test | Project | Result | Evidence |
|------|---------|--------|----------|
| Setup: authenticate and save state | setup | ✓ PASS | Test user `e2e-1788524180607@example.com` created; auth token cookie `sb-127-auth-token` captured with expired access token (forces refresh); storageState written |
| Smoke: dev server responds | anon | ✓ PASS | `GET /` → 200, body non-empty |
| **C1:** Renders login screen | anon | ✓ PASS | Logo, wordmark, subtitle, tagline, button, language selector, and footer all visible |
| **C2:** Error banner | anon | ✓ PASS | `?error=oauth_failed` displays Vietnamese error message: `"Đăng nhập không thành công. Vui lòng thử lại."` |
| **C3:** Locale switch | anon | ✓ PASS | Clicking EN renders English content (`"Start your journey with SAA 2025."`) and sets `NEXT_LOCALE=en` cookie |
| **C4:** Locale fallback | anon | ✓ PASS | Invalid `NEXT_LOCALE=xx` falls back to Vietnamese without blank page |
| **C5:** OAuth kickoff | anon | ✓ PASS | Login button initiates OAuth; request to `/auth/v1/authorize` carries `provider=google` and correct `redirect_to` (parsed URL, not substring) |
| **C10:** Callback open-redirect | anon | ✓ PASS | Origin check correctly validates page stayed on `http://127.0.0.1:3000` (not redirected to `evil.com`) |

### Application-Level Failures (4 cases — RED remains valid)

| Case | Project | Test | Failure | Root Cause |
|------|---------|------|---------|------------|
| **C6** | anon | unauthenticated `/todo` access redirects to `/login` | Expected URL to contain `/login`, but received `http://127.0.0.1:3000/todo` | Unauthenticated guard not implemented; `/todo` does not redirect to `/login` |
| **C7** | authed | authenticated `/login` access redirects to `/todo` | Expected URL to contain `/todo`, but received `http://127.0.0.1:3000/login` | Authenticated guard not implemented; `/login` does not redirect to `/todo` |
| **C8** | authed | guarded redirect from `/login` to `/todo` with token refresh, then subsequent `/todo` loads stay authenticated | Expected URL to contain `/todo` after redirect, but received `http://127.0.0.1:3000/login` | Guard not implemented. **Fixture sets expired access token, forcing proxy to refresh cookies during redirect; C8 exercises the critical cookie rotation path (risk R1)** |
| **C9** | authed | signing out redirects to `/login` and `/todo` thereafter bounces to `/login` | `Test timeout of 30000ms` waiting for sign-out button | `/todo` page and sign-out functionality not yet implemented |

---

## Test Assertion Corrections (Phase 02 refinement)

Two assertions were corrected after initial creation to eliminate false failures:

### C5 — URL Parameter Parsing
- **Defect:** Used substring matching on `redirect_to`, which fails because `@supabase/auth-js` percent-encodes the parameter (`http%3A%2F%2F...`)
- **Fix:** Parse the OAuth request URL with `new URL()` and use `searchParams.get()` to check decoded values
- **Result:** ✓ PASS (correctly asserts `provider=google` and exact callback URL)

### C3 — Content Change + Async Cookie
- **Defect:** Clicked EN locale change but never verified the page content actually switched to English; race condition on cookie read
- **Fix:** Wait for English subtitle text to appear (`"Start your journey with SAA 2025."`), then use `expect.poll()` for cookie assertion
- **Result:** ✓ PASS (both content change and cookie setting verified with proper async handling)

## Progress Summary

**Track B (phase 03) — Implementation Complete:** `/login` screen now renders with all elements, error banner works, locale switching works, OAuth redirect initiates correctly.

**Remaining Work (phases 04 & 05):** Route guards (C6, C7, C8) and sign-out (C9).

---

## Summary

- **redTestFiles:** `e2e/fixtures/supabase-session.ts`, `e2e/auth.setup.ts`, `e2e/login-screen.spec.ts`, `e2e/route-guard.spec.ts`, `e2e/authenticated.spec.ts`
- **redCommand:** `npm run test:e2e`
- **redExitCode:** `1` (4 failures remain for guards and sign-out)
- **redPass:** Cases C1–C5, C10 (8 tests) — Login screen rendering, error handling, locale switching, OAuth kickoff, and open-redirect protection all working. Track B implementation verified.
- **redFailure:** Cases C6, C7, C8, C9 (4 tests) — All route-guard and sign-out functionality. **C8 exercises cookie rotation risk:** fixture sets expired access token, forcing proxy to refresh during guarded redirect; test catches if rotated cookies are dropped.
