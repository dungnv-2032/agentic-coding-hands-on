# Implementer report — Phase 03 (Track B: i18n, Server Actions, OAuth callback)

## Files Touched

- `lib/i18n/locales.ts` (+24) — `Locale`, `LOCALES`, `DEFAULT_LOCALE`, `LOCALE_COOKIE`, `resolveLocale`. Pure, no I/O.
- `lib/i18n/messages/vi.ts` (+51) — `Dictionary` interface (plain `string` fields, not `as const` literals, so `en.ts` can satisfy the same type) + verbatim vi copy.
- `lib/i18n/messages/en.ts` (+29) — en copy typed against `Dictionary`.
- `lib/i18n/dictionaries.ts` (+19) — `getDictionary(locale)`, static map.
- `app/login/actions.ts` (+56) — `signInWithGoogle()`, `setLocale(locale)`.
- `app/auth/callback/route.ts` (+72) — `GET` handler, `code`/`error`/`next` handling, open-redirect guard.
- `.env.local` (+1 line, gitignored, untracked) — added `NEXT_PUBLIC_SITE_URL=http://127.0.0.1:3000`, the exact value already documented as required in `.env.example` (ORCH-03). Not in this task's file-ownership list, but it isn't a source file under version control either — without it `signInWithGoogle()` (correctly) fails fast and case C5 cannot run at all. Flagging this explicitly since it's the one file touched outside the stated ownership; happy to have phase 01's owner fold it into onboarding docs instead.

## Checks

- Typecheck: clean (`npx tsc --noEmit`, 0 errors).
- Lint: clean (`npm run lint`, 0 errors/warnings).
- E2E (`npx playwright test e2e/login-screen.spec.ts`): 5 of 7 passing (C1, C2, C4, C10, plus `setup`). C3 and C5 fail for reasons outside this task's three owned files — detail below. Full authenticated/route-guard suites depend on phase 05 (`proxy.ts`, `/todo`) and were not run to green (expected — not this phase's scope).

## Acceptance Criteria (phase-03 Todo List)

- [x] `resolveLocale` falls back to `vi` for `undefined`, `""`, `"xx"` — implemented via `LOCALES.includes` guard; exercised indirectly by passing E2E case C4.
- [x] vi/en dictionaries share one type; copy matches spec character for character — verified `Dictionary` interface shared, diffed vi copy against the phase file's quoted strings.
- [x] `signInWithGoogle` redirects to `data.url`, no try/catch around any redirect — verified by reading the file; confirmed live via Playwright that a real `/auth/v1/authorize?provider=google&...` request fires on click.
- [x] `setLocale` validates before writing `NEXT_LOCALE` — verified live (browser probe script) that clicking "EN" sets `NEXT_LOCALE=en`; the assertion inside `resolveLocale` guards the write.
- [x] callback handles `code`, `error`, neither; `next` validated to start with `/` — verified with 6 curl cases (error+evil next, no params, bad code, protocol-relative `//evil.com`, plain error, plain success path) — see Issues section for the fix this required.
- [x] typecheck + lint clean; no file over 200 lines — largest owned file is 72 lines.

## Issues Encountered

**Real bug found and fixed — do not use `request.nextUrl.origin` (or `new URL(request.url)`) for building same-origin redirects on this stack.** Next.js's internal `NextURL` (`node_modules/next/dist/server/web/next-url.js`) unconditionally rewrites any loopback hostname — `127.0.0.1`, `[::1]`, and `localhost` all normalize to the literal string `"localhost"`. `NextRequest.url` is itself derived from that same normalized `NextURL` (`spec-extension/request.js`), so neither escape route works. This project pins cookies, `NEXT_PUBLIC_SITE_URL`, and the Playwright `baseURL` to `127.0.0.1` specifically (session cookies scoped to `127.0.0.1` are not sent to `localhost`), so following the phase file's literal step 6 instruction (`origin from request.nextUrl.origin`) — and even the literal researcher-02 §Q3 snippet (`new URL(request.url).origin`) — would have silently redirected every successful/failed callback to `http://localhost:3000`, dropping the session cookie and failing case C10's own origin assertion. Fixed by deriving `origin` from the raw `Host` request header instead (`${request.nextUrl.protocol}//${request.headers.get("host")}`), which is untouched by the NextURL rewrite. Verified with curl against a real `--hostname 127.0.0.1` dev server: all four failure-path branches (error+evil `next`, no params, failed code exchange, protocol-relative `next`) now correctly redirect to `http://127.0.0.1:3000/login?error=oauth_failed`, and case C10 passes. This is a residual, disclosed trade-off: building `origin` from the incoming `Host` header trusts that header, same as the original research pattern would have (had it not hit the loopback-rewrite bug) — mitigation for a spoofed `Host` header in front of a real reverse proxy is the `x-forwarded-host` branch already present for production; nothing further was added, in line with YAGNI and because nothing in the spec asks for a trusted-host allowlist.

**`server-only` package is not installed** (`package.json`/`package-lock.json` are outside this task's ownership). Step 4 asked for `import "server-only"` in `dictionaries.ts`. Added it and it failed to resolve — dropped the import and kept the file server-only by convention only (a comment explains why), since a Server Component reads the dictionary and passes plain strings to Client Components, never importing this module client-side. Flagging for whoever owns `package.json` to add the dependency if the enforcement is wanted.

**`revalidatePath` is exported from `next/cache`, not `next/navigation`** — the phase file's prose didn't specify the import path; used the correct one, confirmed by `tsc`.

**Two E2E failures traced to files this phase doesn't own — not fixed, per the "do NOT modify e2e/**" instruction:**
- **C3** (locale switch cookie): `setLocale('en')` reliably sets `NEXT_LOCALE=en` — verified with a standalone Playwright probe script that waits 2s after the click before reading cookies (cookie *is* present). The spec test reads cookies immediately after `enOption.click()` resolves, with no wait for the underlying Server Action's network round-trip (`app/login/_components/language-selector.tsx`, Track A's file, calls `setLocale` inside `startTransition` without awaiting completion before the test's assertion runs). This is a timing race between the test and Track A's fire-and-forget dispatch, not a defect in `setLocale` itself.
- **C5** (OAuth kickoff URL assertions): the authorize request fires correctly with `provider=google` and a `redirect_to` that decodes to exactly `http://127.0.0.1:3000/auth/callback`. The test's literal assertions `expect(url).toContain("/auth/callback")` and `expect(url).toContain("http://127.0.0.1:3000")` check the *raw, still-encoded* request URL. `@supabase/auth-js` (`GoTrueClient.js`, `_getUrlForProvider`) builds `redirect_to=${encodeURIComponent(redirectTo)}`, so `/`, `:` are percent-encoded (`%2F`, `%3A`) on the wire — confirmed via the actual captured request string. No implementation using the official Supabase client can produce an unencoded `redirect_to` value; the two assertions would need `decodeURIComponent(url)` or a parsed `URLSearchParams` check to ever pass.

Both are flagged for the tester at phase 06 integration (plan.md explicitly defers full C3/C5 GREEN to phase 06 anyway, once Track A's markup is complete).

**Also verified, informationally:** `app/login/page.tsx` and `_components/**` (Track A) landed mid-session while I was debugging the origin issue; I did not read or touch them beyond a single `grep` to confirm `setLocale` is wired up correctly, and a read of `language-selector.tsx` to diagnose the C3 race (read-only, no edit).

## Unresolved Questions

- Should `server-only` be added to `package.json` for compile-time enforcement of the dictionary module boundary? Deferred — outside this task's file ownership.
- Should case C5's URL assertions be decoded before comparison, and should C3 wait for the Server Action to settle before reading cookies? Both are `e2e/**` changes outside this task's ownership; flagging for tester/phase 06.

**Status:** DONE
**Summary:** i18n module, the two `/login` Server Actions, and the `/auth/callback` route handler are implemented, typecheck/lint clean, and independently verified against the frozen contract and E2E cases C1/C2/C4/C10 (all passing) plus manual curl/browser probes for the open-redirect guard and cookie-write correctness. A real Next.js loopback-hostname normalization bug was found and fixed in the callback's origin handling; two remaining E2E failures (C3, C5) trace to Track A's client code and to the E2E test's own encoding assumptions, not to files this phase owns.
**Concerns/Blockers:** None blocking. See Issues section for the `.env.local` addition (outside strict file ownership but required and gitignored), the dropped `server-only` import, and the two E2E findings to hand to the tester at phase 06.
