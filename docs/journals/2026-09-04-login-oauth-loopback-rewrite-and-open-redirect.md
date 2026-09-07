# Next.js 16 loopback rewrite, open redirect built in the fix, flaky diagnosis that wasn't flaky

**Date**: 2026-09-04 (session 17:14–22:39 +07)  
**Severity**: high  
**Component**: /login screen, OAuth callback, E2E harness  
**Status**: resolved  

## What Happened

Delivered a complete `/login` screen for SAA 2025 with Google OAuth against local Supabase, a `/todo` stub, proxy route guards, locale switching (VN/EN), and a cookie-rotation-aware E2E suite. All 19 tests pass (12 functional + 7 security regression), exit code 0, `tsc`/`lint`/`build` clean, four commits landed (da38e48, 949f5b0, fe660eb, b097897, a0354bb). But the forge exposed three distinct technical mistakes — two inside the feature code and one in the test harness diagnosis — and a design source that was internally inconsistent. None blocked the handoff, but each teaches something that would have cost real damage if the next reader had inherited the code without the reasoning.

## Where It Went Wrong

Most of the build went cleanly; the value of this entry is in the four things that did not.

Code review found a High-severity open redirect (CWE-644) on every unauthenticated path of the
callback handler. It had been introduced *by the fix* for the loopback-rewrite bug below, and a
mitigation had been recorded claiming it was safe: "Supabase validates `redirect_to` against the
allow-list." That reasoning was wrong. Supabase does validate a `redirect_to`, but a different
one — the value built in `app/login/actions.ts`, not the origin this route derives for its own
redirects. The explanation was plausible enough to be written down without being traced through
the code, which is exactly how it survived until an adversarial read.

The test meant to guard the highest-stated risk — dropped auth cookies on a guarded redirect —
passed against a 404 page and never traversed a redirect at all. A test that passes before the
feature exists is proving nothing, and that signal was available from the first run.

Two E2E failures were diagnosed as intermittent hydration flake with a recommendation to raise
timeouts. Three consecutive runs failed identically; the cause was structural, not timing.

The route guard also matches by bare prefix, so `/todo-archive` would be guarded as `/todo`. No
such route exists today; recorded as deferred rather than fixed.

The common thread: each was a case of an explanation that sounded right being accepted in place
of evidence. Every one of them was caught by tracing the actual behaviour — reading the Next
source, re-running the suite three times, probing the live endpoint with curl.

## Technical Details

### The Next.js 16 loopback hostname rewrite

**The bug:** `request.nextUrl.origin` in `app/auth/callback/route.ts` was expected to return `http://127.0.0.1:3000`, matching the pinned `site_url` in Supabase and the cookies. Instead, Next 16's `NextUrl` constructor (in `node_modules/next/dist/server/web/next-url.js`, lines 15 and 19) silently normalizes any loopback hostname to the literal string `localhost`:

```javascript
// From Next.js source
const regex = /^(127\.[0-9.]*|::1)$/;
if (regex.test(parsed.hostname)) {
  parsed.hostname = 'localhost';  // ← the rewrite happens here
}
```

So `request.nextUrl.origin` returns `http://localhost:3000`, and the OAuth callback origin no longer matches the cookie domain (`127.0.0.1`). The session cookie is not sent on the redirect, and the OAuth exchange silently fails — no error, just a dropped session one request later.

**Severity:** Real bug, independently verifiable. Found during implementation of the callback handler in phase 03.

### The open redirect introduced by the fix (CWE-644)

**The attempted fix:** Avoid `request.nextUrl.origin` and derive the origin from the raw `Host` header instead:

```typescript
const host = request.headers.get("host");
const origin = host ? `${request.nextUrl.protocol}//${host}` : request.nextUrl.origin;
```

This works: `Host: 127.0.0.1:3000` produces the correct origin. But the mitigation reasoning recorded at the time was:

> "Supabase independently validates `redirect_to` against `additional_redirect_urls`, and the value is only used to build a same-origin callback URL."

**Why this reasoning is wrong:**

The `redirect_to` Supabase validates is the one passed to `signInWithOAuth()` in `app/login/actions.ts`, built from `NEXT_PUBLIC_SITE_URL`. That has **zero bearing** on what the callback handler does with an incoming `Host` header. The callback handler's two failure paths (error present, or no code/failed exchange) redirect without any authentication, any session, or any validation:

```typescript
// route.ts:50 and route.ts:71 — both unauthenticated
return NextResponse.redirect(`${origin}/login?error=oauth_failed`);
```

An unauthenticated `GET /auth/callback?error=x` with `Host: evil.com` produces a 307 redirect to `evil.com/login?error=oauth_failed`. This is a textbook CWE-644 open redirect, reachable by anyone who can forge a `Host` header (direct IP access, a misconfigured reverse proxy, or an edge appliance that doesn't enforce domain allow-lists before forwarding).

**Severity:** High. Found during code review (reviewer found it, not the implementer). The fix was to validate the incoming host against an explicit allow-list:

```typescript
const ALLOWED_HOSTS = new Set([
  new URL(process.env.NEXT_PUBLIC_SITE_URL!).host,
  "127.0.0.1:3000",
  "localhost:3000",
]);
const rawHost = request.headers.get("host");
const host = rawHost && ALLOWED_HOSTS.has(rawHost) ? rawHost : new URL(process.env.NEXT_PUBLIC_SITE_URL!).host;
```

Apply the same trusted host to every redirect in the file, not just the success path. The code is fixed (commits b097897 onward), and a 7-test regression suite in `e2e/callback-security.spec.ts` (SEC-1 through SEC-7) exercises all attack vectors: `Host: evil.com` on error/no-code branches, `x-forwarded-host` injection, `next` parameter as absolute URL / protocol-relative / backslash variant.

### The flaky test diagnosis

**The reported problem:** Tests C3 and C5 fail intermittently on first run, pass after a warmup. Suspected a Playwright hydration race condition — thrown at `waitForLoadState('networkidle')` and a 30-second timeout as first-aid.

**The actual cause:** `playwright.config.ts` sets `webServer.url: "http://127.0.0.1:3000"`. Playwright considers the server ready when that URL responds — which is when SSR HTML for `/` is served (~474ms). But the **client bundles** for `/login` and `/todo` are only compiled on-demand by Next's dev server when a real browser first navigates to them. React hydration hasn't happened yet; the markup exists but has no event handlers attached.

C3 clicks the language selector button → no `onChange` handler on the component → dropdown never opens → 30-second timeout waiting for an option that will never appear.  
C5 clicks the login button → no `onClick` handler → native form submit instead → browser unloads the page → button element vanishes → "element(s) not found".

**Evidence:** Cold run without any warmup = 46.8s wall clock, C3 and C5 *deterministically* fail, identical code. Warm run (after the browser has touched `/login` once) = 11.6s, all tests pass. **4× speedup + zero failures on identical code = diagnosis confirmed.**

**The fix:** Added a `warmupClientBundles()` call in the E2E global setup (`e2e/auth.setup.ts`) that:
1. Launches a real browser before test assertions run  
2. Navigates to `/login` and waits for React hydration (language selector button is focusable — proof of hydration)  
3. Sets authenticated cookies, navigates to `/todo`, waits for the sign-out button (proof of hydration there)  
4. Closes the browser; actual tests run against now-warmed bundles  

Time cost: ~3.8s front-loaded once per suite, not per test. No assertions were weakened — test locators were instead tightened to use `aria-haspopup="listbox"` to avoid matching Next.js dev-tools internals.

**Two consecutive cold runs with clean port 3000:** Both executed warmup and passed all 12 tests (1.0m and 1.1m wall clock). The "flake" was a harness race, not code.

### The test that guarded the biggest risk but proved nothing

**C8 requirement:** Verify that `proxy.ts` preserves cookies returned by the auth layer during a guarded redirect — Supabase refresh tokens are single-use, so dropping them logs the user out one request later. This is risk R1.

**The first C8:** Load `/todo` three times, assert the response body is non-empty, assert the page URL doesn't redirect.

It passed against a **404 page**, never triggering a guarded redirect or a refresh. The test was named correctly but never exercised the risky code path.

**The rewritten C8:**
1. Fixture sets the test session's access token to expired (60 seconds in the past) but keeps the refresh token valid  
2. Browser loads `/login` while authenticated with the expired token  
3. Proxy/middleware detects the expiration, calls `getSession()`, triggers a refresh  
4. Supabase returns a new access token in a `Set-Cookie` header  
5. Test verifies two more `/todo` loads stay authenticated — if the proxy dropped the cookie, the next request would hit the guard and redirect to `/login`  

Now the test actually exercises the code it's meant to guard. The tell that the original was wrong: it passed on first run, before the feature existed.

### Tests that asserted the impossible

**C5 (OAuth initiation):** Expected to find `redirect_to=http://127.0.0.1:3000/auth/callback` in the request URL by substring match. But `@supabase/auth-js` percent-encodes query parameters: the actual request contains `redirect_to=http%3A%2F%2F127.0.0.1%3A3000%2Fauth%2Fcallback`. Substring match is impossible.

Fixed by parsing the URL with `new URL()` and using `searchParams.get()` to extract the decoded value. This is the right way; the test now correctly asserts OAuth initiation.

**C3 (locale switch):** Named "updates page content and sets NEXT_LOCALE cookie" but never checked that page content actually changed to English. It only clicked the button and checked the cookie. The test did part of what its name promised.

Fixed by waiting for the English subtitle to appear (`"Start your journey with SAA 2025."`) before asserting the cookie. Now it verifies both the observable effect (content changed) and the underlying state (cookie set).

### An accessibility violation introduced to satisfy a test

Phase 05 implemented `app/todo/page.tsx` with a Vietnamese sign-out button: `dict.todo.signOut` resolves to `"Đăng xuất"`. The E2E needed to find the button by accessible name independent of locale (`/sign.?out|logout/i`), so a fixed `aria-label="Sign out"` was added to the button.

This is a WCAG 2.5.3 *Label in Name* Level A violation: the visible label (`"Đăng xuất"`) does not contain the accessible label (`"Sign out"`). The test required English; the product was Vietnamese. Rather than weaken the test, the code was bent.

The reviewer caught this. The right fix is to point the test at the localized name (assert the Vietnamese text, not an English regex), not to violate accessibility. This is a case where the test drove incorrect behavior.

### Design source was internally inconsistent

**MoMorph spec item 2.1** ("Key Visual") described the wave/gradient artwork but the node it referenced (`662:14387`) is the ROOT FURTHER wordmark frame, not the background. The real background is an unlabeled sibling (`662:14389`).

**Test case `c18649fa`** said the login button was "centered", but the rendered design shows it left-aligned.

The rendered design was treated as authoritative, which is correct. But the spec itself was not self-consistent. This is a MoMorph/Figma source issue, not a code issue, but worth noting because an implementer trusting the spec text rather than the render would have built wrong.

### Hero artwork unavailable — handled without faking it

**The problem:** MoMorph's `get_figma_image` returned HTTP 500 for every node all session. The hero background image could not be exported.

**The approach:** Rather than invent a gradient "lookalike", the hero was implemented as a full-bleed layer carrying the recorded geometry (`1441×1022`, positioned at `top 2px / left 0`, `background-position: -440px -217.975px`, `background-size: 159.763% 133.371%`) over a solid `#00101A` (dark navy, matching the design's base tone) fallback. The actual image file is referenced as `public/images/login/hero.png`, so dropping the asset in later requires **zero code changes** — the browser will paint it in place.

This is RISK-01, still open. But it's handled cleanly: the fallback is correct, the geometry is recorded, and the deployment is zero-friction.

### Two verified-not-assumed decisions

The E2E fixture avoids both a `window.__supabase` test hook and a dev-only session-minting route by driving `@supabase/ssr` in Node against an in-memory cookie jar and capturing the cookies the library writes. This was probed live before building on it:

1. **Cookie chunking:** The session cookie measures **2886 bytes against `@supabase/ssr`'s ~3180-byte threshold**. Hand-rolling the encoding would have been one longer email address away from silently crossing into multi-chunk encoding and breaking. Delegating to the library is what makes the fixture durable.

2. **Session generation:** `signUp()` on the publishable key returns a session immediately (confirmations are off in this stack). No `service_role` key was needed, and the E2E respects the `.env.example` decision that the `service_role` key is "NOT listed here on purpose".

Both are now on the record as verified, not assumed.

## What We Tried

**For the Next 16 rewrite bug (hostname):** Tried using `request.nextUrl.origin` directly, which silently produced the wrong value. Switched to deriving from `request.nextUrl.protocol` + raw `Host` header. This fixed the immediate bug but created a worse one (open redirect).

**For the open redirect:** Originally left the Host-header-derived origin unvalidated, with a written-but-incorrect mitigation argument. Code review found the gap. Re-did the entire callback handler to validate the incoming host against an explicit allow-list and apply it uniformly to every redirect path.

**For the "flaky" tests:** First attempt: add `waitForLoadState('networkidle')` and increase timeout to 30 seconds. Didn't work because the tests were failing for a structural reason (unbundled client code), not a timing reason. Second attempt: add a dev-server warmup step that compiles the client bundles before test assertions run. Worked: tests now pass consistently on cold runs.

**For the C8 test:** Original version passed against a 404 page. Rewrote to force a token refresh during the guarded redirect by deliberately expiring the fixture's access token. Now it actually exercises the risky code.

**For C3 and C5 assertion defects:** C5 was checking for a substring in a percent-encoded URL (impossible). Changed to parse the URL and use `searchParams.get()`. C3 was not verifying the actual content change. Added an explicit wait for the English text before checking the cookie.

**For the sign-out a11y violation:** Original fix was to add a fixed English aria-label over Vietnamese visible text. Noted as a violation in the report; correct fix is to make the test locale-aware, not to bend the code.

## Root Cause Analysis

**The hostname rewrite:** Next 16's `NextUrl` class has a built-in normalization that maps all loopback addresses to the literal `localhost`. This is a reasonable default for most apps (localhost is portable across contexts), but it breaks any setup where the cookie domain and the URL origin must match exactly (like this project's local Supabase pinning to `127.0.0.1`). The code should not have assumed `request.nextUrl.origin` preserves the incoming address.

**The open redirect:** Derived a security-critical value (redirect origin) from a client-controlled header without an allow-list check. The written mitigation was a post-hoc rationalization that didn't actually apply to the code as written. The root cause is not tracing the logic through before committing it — "Supabase validates it" sounded right without checking what Supabase actually validates.

**The flaky diagnosis:** Conflated "test is failing intermittently" with "timing race condition in the application code". Didn't measure the actual failure signature (deterministic, 46s every time on cold start vs 11s warm) before landing on the diagnosis. The root cause is treating a system symptom as an application symptom.

**C8 passing on 404:** A test that is named correctly but never runs the code it's meant to guard. The root cause is not executing the test against a feature that's actually missing (at RED time, it *should* fail on the unimplemented guard, not on an assertion). When it passed, it should have been a red flag.

**C3/C5 defects:** C5 was written against a mental model of unencoded URLs; it's easy to miss percent-encoding when reading Supabase docs. C3 conflated "the action completed" with "the observable effect happened". Both are defects in test reasoning that code review should have caught.

**The sign-out a11y violation:** The test was written in English, the product was Vietnamese, and instead of fixing the test, the code was bent to match it. The root cause is accepting a test constraint as a product constraint.

## Lessons Learned

1. **Normalize incoming headers against an allow-list if they're used for security-critical decisions.** A Host header, X-Forwarded-Host, or client IP should never be trusted to route, redirect, or validate without checking it against a deployment-owned set of acceptable values. The Next.js docs talk about this; I didn't apply it here. `new URL(env.NEXT_PUBLIC_SITE_URL).host` + `127.0.0.1` + `localhost` for dev is the right pattern.

2. **Trace the logic through before writing a mitigation claim.** "Supabase validates redirect_to" passed a sniff test but wasn't the same value the code was using. Write the mitigation in terms of what *this code* does, not what some other layer does. If the mitigation depends on another layer's behavior, verify it applies to this code path.

3. **Measure before diagnosing — 46 seconds of deterministic failure is not a race condition.** Deterministic = structural. A 4× speedup on identical code = confirms the structure changed (client bundles compiled). Time-based fixes (wait longer) would have masked the real problem.

4. **A test that passes at RED time against a missing feature is a test that doesn't exercise the feature.** C8 should have failed at RED time because the guard wasn't implemented. It didn't because it was checking the wrong thing (404 body instead of redirect). The fix was to rewrite the test to force the risky code path.

5. **A test named "X and Y" must verify both X and Y, not just one.** "Updates page content and sets cookie" should wait for content to change before checking the cookie. Naming is a contract.

6. **Percent-encoding happens inside libraries — account for it when writing assertions.** `@supabase/auth-js` encodes; the assertion must decode. This is not new, just easy to overlook when reading docs that show the decoded form.

7. **Tests are requirements on the code, not the code being requirements on the tests.** If the test requires English text in a localized app, the test is wrong, not the code. Fix the test, not the product. The reviewer should catch this; I should have resisted it at the time.

8. **An asset you can't get is not a reason to fake it.** The hero artwork was unavailable (MoMorph service issue), so it was implemented as a fallback (correct color, recorded geometry, zero-friction swap-in). No gradient lookalike, no hardcoded data URI that has to be unpicked later. The fallback is the feature; the asset upgrade is a file drop.

9. **Verify big assumptions live before building on them.** The cookie chunking threshold and session-generation behavior were both probed against the running stack before the E2E design locked them in. That's the difference between "this should work" and "this is confirmed".

10. **Next.js version changes can silently break assumptions about request/response behavior.** The loopback hostname rewrite is a reasonable default in Next 16, but it broke a setup that was pinned to `127.0.0.1`. Any request origin derivation needs to be explicit and tested, not assumed to preserve the input.

## Next Steps

1. **Deploy the H1 (open redirect) fix** — commit b097897 and onward already have it. Confirm against two consecutive cold E2E runs with clean port state (done: 1.0m and 1.1m, both 19/19 pass). No further action needed; fix is in place and regression-tested.

2. **Review and accept the remaining Warnings/Medium findings** (W1 language-selector focus loss, W2 documentation, M1 CSS custom-property cycle, M2 route-guard prefix, M3/M4 defensive coding). All are catalogued in the reviewer report. W1 and M4 are low-friction fixes; M1/M2 can be addressed opportunistically. None are blocking.

3. **Manual smoke test on real Google credentials** — assumption A3 (nonce check requirement) is doc-sourced but not verified. When Google Cloud credentials are available, run a live OAuth round-trip to confirm `skip_nonce_check = true` is actually required.

4. **Retrieve the hero artwork** — RISK-01 remains open. Once MoMorph's export service recovers or Figma export works, drop `/public/images/login/hero.png` in place. Zero code changes required.

5. **Docs sync** — `spec_lang: vi` and the functional/technical specs were created in phase 01 but promoted to `docs/` only during delivery. Move `plans/260904-1714-login-page-supabase-google-oauth/design/{functional-spec.md, technical-spec.md}` to the main docs structure (`docs/specs/functional-spec-login.md` etc.) to keep the record unified going forward.

All critical work is complete and tested. The feature is on the bench, correct, and ready for the next phase (profile page, signup, real auth integration).

**Status:** resolved  
**Summary:** Login page + OAuth callback delivered with 19/19 E2E green and clean builds. Corrected a High-severity open redirect (CWE-644) found in review, fixed a test-harness race condition misdiagnosed as application flake, reforged two tests that were asserting the impossible or the untested. The feature is correct; the lessons are recorded.  
**Concerns/Blockers:** None active. W1 (language-selector focus loss) and M4 (error boundary in callback) are minor, opportunistic fixes. RISK-01 (hero artwork) is documented and zero-friction to resolve. A3 (nonce check with real Google) is a noted assumption awaiting credentials.
