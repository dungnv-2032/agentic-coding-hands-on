# Review — `/login` Feature (Google OAuth on Supabase, Next 16)

## Review Summary

### Scope
- Files reviewed: `app/login/page.tsx`, `app/login/actions.ts`, `app/login/_components/*.tsx`, `app/auth/callback/route.ts`, `app/todo/{page,actions}.tsx`, `proxy.ts`, `lib/supabase/{server,client,update-session}.ts`, `lib/i18n/{locales,dictionaries,messages/vi,messages/en}.ts`, `e2e/**`, `playwright.config.ts`, `supabase/config.toml`, `.env.example`, `eslint.config.mjs`, `app/globals.css`
- Lines: ~950 across the above (excluding generated/e2e boilerplate)
- Depth: full (against `functional-spec.md`, `technical-spec.md`, `clarifications.md`, `plan.md`)

### Assessment
Solid, disciplined work. The team correctly identified and fixed the one WCAG issue, wrote a genuinely-exercised E2E for the hardest risk (cookie rotation on redirect), and left an honest trail of open questions (`clarifications.md` W1/W2) instead of burying them. `tsc`/`lint` reconfirmed clean during this review. One real security gap remains: the `Host`-header-derived origin in `app/auth/callback/route.ts` is not validated against an allow-list, and the reasoning recorded in `clarifications.md` to justify it does not hold once traced through the code. Everything else — open-redirect handling, cookie preservation, Server Action safety, Next 16 API usage, spec fidelity, accessibility — is in good shape with only minor findings.

### Critical
None.

### High

**H1 — `Host`-header-derived origin is untrusted and unvalidated; the stated mitigation doesn't cover the easiest-to-hit path.**
`app/auth/callback/route.ts:41-42`:
```ts
const host = request.headers.get("host");
const origin = host ? `${request.nextUrl.protocol}//${host}` : request.nextUrl.origin;
```
The engineering reason for avoiding `request.nextUrl.origin` (Next 16 rewrites `127.0.0.1`→`localhost`, breaking the pinned-cookie dev setup) is correct and independently verifiable at `node_modules/next/dist/server/web/next-url.js`. But the mitigation recorded in `clarifications.md` W1 ("Supabase independently validates `redirect_to`... the value is only used to build a same-origin callback URL") does not hold as written:
- Supabase's `additional_redirect_urls` allow-list validates the `redirectTo` passed to `signInWithOAuth` in `app/login/actions.ts:30` — a completely different value, built from `NEXT_PUBLIC_SITE_URL`, not from the `Host` header. It has no bearing on what this route does with an incoming request.
- "Only used to build a same-origin callback URL" is circular: `origin` *is* the attacker-controlled value; saying the redirect stays same-origin relative to itself doesn't neutralize a Host-header injection.
- The failure paths — `route.ts:50` (`error` present) and `route.ts:71` (no code/failed exchange) — use the raw `Host`-derived `origin` in **every environment**, including production, with **zero** allow-list check. These paths require no authentication, no valid `code`, and no session: `GET /auth/callback` (or `GET /auth/callback?error=x`) with a forged `Host` header is enough to get a 302 to an attacker-chosen domain (`${origin}/login?error=oauth_failed`). This is a textbook CWE-644 open redirect, reachable by anyone who can get a request to the origin with an arbitrary `Host` header (direct-IP access, a misconfigured reverse proxy/nginx `default_server`, or any edge that doesn't enforce a domain allow-list before forwarding).
- The production-aware branch that *does* exist (`route.ts:61-66`, only reached on the success path) swaps trust from `Host` to `x-forwarded-host` — which is equally attacker-controllable unless the specific hosting platform is guaranteed to overwrite it on every hop. That's an assumption the code doesn't state or enforce, and it still doesn't apply to the two failure-path redirects.

**Fix:** validate the incoming host against an explicit allow-list before using it to build any redirect — e.g. derive the allowed host from `new URL(process.env.NEXT_PUBLIC_SITE_URL).host` (already used in `actions.ts:30`) plus `127.0.0.1:3000`/`localhost:3000` for dev, and fall back to that trusted value whenever the incoming `Host` doesn't match:
```ts
const ALLOWED_HOSTS = new Set([
  new URL(process.env.NEXT_PUBLIC_SITE_URL!).host,
  "127.0.0.1:3000",
  "localhost:3000",
]);
const rawHost = request.headers.get("host");
const host = rawHost && ALLOWED_HOSTS.has(rawHost) ? rawHost : new URL(process.env.NEXT_PUBLIC_SITE_URL!).host;
const origin = `${request.nextUrl.protocol}//${host}`;
```
Apply the same trusted value to *every* redirect in the file, not just the success path. This keeps the 127.0.0.1-vs-localhost fix (it still avoids `nextUrl.origin`) while closing the injection. Not graded Critical only because exploitation additionally requires an infra-level Host-forwarding weakness that well-managed platforms (Vercel, properly configured `nginx` with `server_name`) rule out — but this app documents no such assumption, so it should be fixed before any non-managed production deployment.

### Warnings

**W1 — Language-selector focus is lost on selection.**
`app/login/_components/language-selector.tsx:53-56`: `handleSelect` calls `setOpen(false)` after `onClick`, which unmounts the clicked `<button role="option">`. Since focus was on that element, the browser drops focus to `<body>` with nothing to restore it — a keyboard user who just navigated Tab→Enter loses their place and must re-Tab from the top of the page. Return focus to the trigger button explicitly:
```ts
const triggerRef = useRef<HTMLButtonElement>(null);
function handleSelect(value: Locale) {
  setOpen(false);
  triggerRef.current?.focus();
  ...
}
```
Also note the `role="listbox"`/`role="option"` pairing implies WAI-ARIA APG listbox keyboard semantics (arrow-key navigation, roving tabindex) that aren't implemented — it works today only because every option is independently Tab-reachable, which happens to satisfy the spec's "keyboard-operable" bar (US003) but will surprise a screen-reader user expecting arrow keys. Low-cost fix: either drop `role="listbox"`/`role="option"` for a plain `role="menu"`/`role="menuitem"` (no arrow-key expectation) or add arrow-key handling. Not blocking, but worth doing before this pattern is copied elsewhere.

**W2 — `x-forwarded-host` trust in the success branch is undocumented and effectively equivalent to the Host-header risk in H1.**
`app/auth/callback/route.ts:61-66`. Same root cause as H1; folding this into the H1 fix (single trusted-host source, applied uniformly) resolves both.

### Medium

**M1 — Self-referential CSS custom property, works today only by cascade accident.**
`app/globals.css` (new lines):
```css
--font-montserrat: var(--font-montserrat);
--font-montserrat-alternates: var(--font-montserrat-alternates);
```
Unlike the existing convention two lines above it (`--font-sans: var(--font-geist-sans)` — aliasing a *different*-named variable), these two alias a variable to itself. At `:root`, this is a genuine CSS custom-property cycle, and per spec `--font-montserrat` computes to its guaranteed-invalid value there. It currently works only because `app/login/page.tsx:47-48` applies `montserrat.variable`/`montserratAlternates.variable` (which set concrete, non-cyclic values for the same custom-property names) directly on the wrapping `<div>`, and every consumer of the `font-montserrat`/`font-montserrat-alternates` Tailwind utilities in this feature (`login-content.tsx`, `login-footer.tsx`) is a descendant of that div, so the element-local declaration shadows the broken `:root` one before inheritance ever needs to fall back to it. The moment either utility class is used somewhere that is *not* a descendant of that specific div (a different page, a portal, a modal rendered via `createPortal`), it will silently render with no font applied and no error. Recommend either applying the two `variable` classes at the root layout (`app/layout.tsx`) instead of page-locally, or renaming the theme tokens to avoid the literal self-reference so a future reader doesn't copy the pattern into a context where it breaks.

**M2 — Route-guard prefix matching is broader than the two routes it's meant to protect.**
`proxy.ts:41,44`: `pathname.startsWith("/todo")` / `startsWith("/login")` would also match a hypothetical future `/todo-export` or `/login-help` route and silently guard/redirect it. No exploit today (no such routes exist), but it's an easy trap for the next person adding a route. Prefer `pathname === "/todo" || pathname.startsWith("/todo/")` (same for `/login`).

**M3 — `resolveNextPath` is sound, but the design that makes it sound (always concatenating a literal, trusted origin in front of `next`) is not obvious from the function itself, and isn't tested beyond the plain absolute-URL case.**
`app/auth/callback/route.ts:14-19`. I traced protocol-relative (`//evil.com`, caught explicitly), backslash variants (`/\evil.com`, `/\\/evil.com` — harmless here specifically *because* `origin` is prepended as a literal string before any URL parsing occurs, so the authority component is already fixed by the time a browser or `new URL()` would parse backslashes-as-slashes), and percent-encoded double slashes (decoded by `URLSearchParams.get()` before the check runs, so still caught). All hold up — but only test `C10` exists (`e2e/login-screen.spec.ts:147`), covering only the absolute-URL case the prompt already called out as covered. Add cases for `//evil.com` and one backslash variant so the safety property is pinned by a test, not only by this review's trace-through. Also worth a defensive note: if `next` ever contains a raw CR/LF (unlikely via `URLSearchParams`, which already decodes `%0D%0A` into literal characters), `NextResponse.redirect()` will throw when building the `Location` header (Node's `Headers` rejects control characters) rather than produce a malformed response — that's a 500, not an open redirect, but confirm it's caught by whatever top-level error boundary exists so it doesn't leak a stack trace (see Data Leakage note below).

**M4 — No error boundary around the route handler; an unexpected `exchangeCodeForSession` throw (vs. its normal `{error}` return) would surface a raw Next.js error page.**
`app/auth/callback/route.ts:53-67`. The code correctly handles the *documented* failure mode (`exchangeError` truthy), but `supabase.auth.exchangeCodeForSession` and `createClient()` are not wrapped — a network blip to the local GoTrue instance, or a malformed `code` that the client-side parser itself throws on, would propagate as an unhandled exception in a Route Handler, which Next renders as a generic 500 (not necessarily a leaked stack trace in production mode, but worth being deliberate about rather than relying on Next's default). Wrap the `code` branch in try/catch and fall through to the same `OAUTH_FAILED_REDIRECT`, consistent with how `signOut()` already treats `supabase.auth.signOut()`'s error as non-fatal.

### Low

**L1 — `todo/page.tsx` and `login/actions.ts` both call `createClient()` and `cookies()` independently rather than sharing a request-scoped instance; harmless (each is correctly re-created per request per the doc comment in `lib/supabase/server.ts:1-9`) but is a small duplicated pattern across 4 files. Not worth a shared helper at this size (YAGNI holds).

**L2 — `IconGoogle`/`IconFlagVn`/`IconChevronDown` (`icons.tsx`) have no `aria-hidden` on the `<svg>` root itself; correctness is preserved because every call site wraps them in a text-labeled button or marks the wrapper `aria-hidden`, but adding `aria-hidden="true"` (or `focusable="false"`) directly on the icon components would make them safe by default for any future call site that forgets the wrapper.

**L3 — `setLocale`/`signInWithGoogle`/`signOut` all correctly call `redirect()`/mutate cookies outside any try/catch (confirmed by reading all three), so `NEXT_REDIRECT` is never swallowed. Calling this out as a strength, not a defect — flagged here only because the prompt asked me to specifically verify it.

### Edge Cases Turned Up (scouting pass, beyond the diff)

1. **Prefetch race on `/auth/callback`.** A link-prefetching browser feature or a security scanner following the Google-redirect URL early could consume the one-time `code` before the real navigation lands, causing the genuine user's browser to hit `exchangeCodeForSession` with an already-used code → falls to `OAUTH_FAILED_REDIRECT`. Nothing in the code causes this, and nothing can fully prevent it (inherent to the authorization-code grant over a followable GET link) — noted for awareness, not a defect.
2. **`isLocalEnv` check uses `NODE_ENV === "development"`, not a hosting-environment check.** `route.ts:62`. Running the app with `NODE_ENV=production` locally (e.g., `next build && next start` during a pre-deploy smoke test) would silently take the `x-forwarded-host` branch instead of the localhost-safe one. Low risk (dev workflow uses `next dev`), but worth a comment noting the coupling.
3. **Double-submit on `signInWithGoogle`.** The button disables via `useFormStatus().pending` (`google-sign-in-button.tsx:15`), which only reflects the *client's* view of one in-flight submission; two rapid form submissions before React re-renders the disabled state (a slow input event queue under load) could in principle fire two Server Action invocations. Not exploitable for anything beyond two `signInWithOAuth` calls (idempotent, both redirect to Google) — cosmetic at worst.
4. **Locale-switch race.** `language-selector.tsx:50-52` fires `setLocale` inside `startTransition` without awaiting; two fast, different selections could resolve out of order server-side, leaving the cookie on the *first*-completing rather than *last*-clicked locale. Cosmetic (a UI preference, not security-sensitive) — noted per the concurrency check, not blocking.

### Done Well
- **Cookie-preservation fix (`proxy.ts:30-39`) is correctly universal and correctly bypassed where it must be.** Every guarded redirect (`/todo`→`/login`, `/login`→`/todo`) goes through `redirectWithSessionCookies`; `/auth/callback` and `/` fall through untouched, exactly as required for the OAuth round-trip to complete. `e2e/authenticated.spec.ts` C8, backed by `e2e/fixtures/supabase-session.ts:89-98` genuinely forcing an expired `access_token` with a live `refresh_token` before the guarded redirect, is a real, non-cosmetic regression test for the plan's #1 risk — not just an assertion that happens to pass.
- **Server Actions correctly keep `redirect()` outside try/catch** in all three call sites, and `signOut()` deliberately swallows the Supabase-side error while still redirecting, matching the spec's "expired session sign-out must not error" requirement (US004 edge case).
- **`resolveLocale`/`setLocale` validate untrusted input against a closed set** (`LOCALES.includes`) rather than writing raw cookie/action input — correct even though `setLocale` is directly POST-able.
- **`next/image` uses `preload`, not the Next-16-deprecated `priority`**, in both `login-header.tsx` and `login-content.tsx`.
- **No reflected XSS surface**: the `?error` query param only toggles a boolean (`hasError`) in `page.tsx:41-43`; the actual message text always comes from the static dictionary, never from user input.
- **Accessibility**: the one prior WCAG 2.5.3 violation (English `aria-label` over Vietnamese visible text) is genuinely fixed on `/todo` (`app/todo/page.tsx:32-38`, verified no `aria-label` override present, comment explains why), and I found no recurrence anywhere else in the reviewed files — `login-header.tsx`'s `aria-label={"${labels.language}: ${currentLabel}"}` correctly contains the visible text as a substring.
- **Honesty in the paper trail**: `clarifications.md` W1/W2 documenting a self-identified risk instead of hiding it is exactly the right instinct — the H1 finding above is the reviewer's job of finishing that trail, not a gotcha.

### Actions In Order
1. Fix H1/W2 — add a `Host`-allowlist check in `app/auth/callback/route.ts`, applied uniformly to every redirect in the file (error, no-code, and success paths).
2. Fix W1 — restore focus to the language-selector trigger after `handleSelect`.
3. Fix M4 — wrap the `exchangeCodeForSession` branch in try/catch, falling through to `OAUTH_FAILED_REDIRECT`.
4. Fix M2 — tighten the proxy's path matching to exact-or-subpath.
5. Fix M1 — move the two font `variable` classes to the root layout, or rename the theme tokens to break the literal self-reference.
6. Add the two missing `resolveNextPath` test cases (M3) for durability, not because a gap was found.

### Numbers
- Type coverage: `npx tsc --noEmit` — clean, 0 errors (re-verified during this review).
- Lint: `npm run lint` — clean, 0 findings (re-verified during this review).
- Test coverage: 12/12 E2E per the stated baseline (not re-run in this review — read-only scope); test-to-requirement mapping (C1–C10 login/callback, C6–C9 route guard/auth) traced against `functional-spec.md` FR/US IDs and found complete for everything E2E-observable under Assumption A1.

### Still Unresolved
- **A1 (real Google round-trip)** remains the largest untested surface, as flagged going in. Beyond what's already logged in `clarifications.md` (A1, A3): the concrete things that *cannot* be exercised without real Google credentials and that I cannot further de-risk by reading code are (a) whether `skip_nonce_check = true` is actually required for this Supabase CLI version against a real Google id_token, and (b) whether the registered Google Cloud redirect URI will exactly match `NEXT_PUBLIC_SITE_URL/auth/callback` in whatever real domain this ships to — both are pure configuration risks, not code defects, and both are already called out as open assumptions. No new blocking risk found beyond what's on record.
- H1 is the one item I'd treat as production-blocking; everything else in Warnings/Medium/Low is safe to ship and fix opportunistically.

**Status:** DONE_WITH_CONCERNS
**Summary:** The feature is well-built and spec-faithful with clean types/lint and a genuinely-exercised regression test for the hardest risk (cookie rotation on redirect), but `app/auth/callback/route.ts` derives its redirect origin from the raw, unvalidated `Host`/`x-forwarded-host` headers on every path including the unauthenticated error/no-code fallback — the mitigation recorded in `clarifications.md` doesn't hold once traced through the code, and this should get a host allow-list before any production deployment outside a strictly domain-bound platform.
**Concerns/Blockers:** H1 (Host-header open redirect, all environments, unauthenticated) — recommend fixing before this ships to a real deployment target; nothing else in this review blocks merging to continue local/dev work.
