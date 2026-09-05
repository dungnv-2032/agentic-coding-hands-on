# Scout Report — my-app (SAA 2025)

Wave 0 artifact for the rebuild-spec Core pass. Every claim below was read out of the
source at the cited `file:line`. Where a thing does not exist, it says so.

- Project root: `/mnt/c/Users/nguyen.van.dungc/Desktop/project/my-app`
- Stack: Next.js 16.3.4 App Router · React 19.2.8 · TypeScript strict · Tailwind v4 · `@supabase/ssr` 0.12.5 · Playwright 1.62 (`package.json:14-29`)
- Scale: **61** `.ts`/`.tsx` files under `app/ lib/ e2e/ proxy.ts`, **4,347 LOC**
- Scripts: `dev`, `build`, `start`, `lint` (eslint), `typecheck` (`tsc --noEmit`), `test:e2e` (`package.json:5-12`). **No unit-test runner is configured** — Playwright E2E is the only test harness.
- `next.config.ts` is empty (`{}`) — no image domains, no rewrites, no experimental flags.
- Path alias `@/*` → repo root (`tsconfig.json:paths`).

---

## 1. File inventory

### Root config

| File | Purpose |
|---|---|
| `package.json` | Deps + 6 npm scripts. No test runner beyond Playwright. |
| `next.config.ts` | Empty config object. Nothing customised. |
| `tsconfig.json` | `strict: true`, `moduleResolution: bundler`, `@/*` alias, includes `.next/types`. |
| `eslint.config.mjs` | Flat config: `eslint-config-next` core-web-vitals + typescript; ignores `.claude/**`, `supabase/.temp/**` (heap exhaustion note at `eslint.config.mjs:15-17`). |
| `postcss.config.mjs` | Tailwind v4 via `@tailwindcss/postcss`. |
| `playwright.config.ts` | 6 projects, WSL2 vendored-lib shim (`:12-20`), pinned future `NEXT_PUBLIC_EVENT_START_AT` (`:33-35`), `baseURL http://127.0.0.1:3000`, `fullyParallel: false`. |
| `proxy.ts` | Next 16's renamed `middleware`. Session refresh + route guard. |
| `.env.example` | Documents the 4 public env vars + the 2 Supabase-CLI Google OAuth vars. |
| `supabase/config.toml` | Local Supabase stack config. Google provider enabled (`:336-338`). |
| `release-manifest.json`, `docs/.rebuild-state.json`, `docs/_canonical-fcodes.json`, `docs/_source-to-fcode.json` | Tooling state, not application code. |

### `app/` — routes and shared server helpers

| File | Purpose |
|---|---|
| `app/layout.tsx` | Root layout. `<html lang="en">` (hardcoded — **does not track the locale cookie**, `:15`), Montserrat font vars, SAA metadata. |
| `app/page.tsx` | `/` — SCR002 Homepage. Server Component; composes header/hero/root-further/awards/kudos/widget/footer. |
| `app/globals.css` | `@import "tailwindcss"` + `@theme inline` font tokens. Still carries `create-next-app` light/dark `--background`/`--foreground` and an `Arial` body font (`:24-28`) that every page overrides locally. |
| `app/_fonts.ts` | Shared `Montserrat` / `Montserrat_Alternates` instances. `/login` deliberately keeps its own duplicate (`:9-11`). |
| `app/_page-context.ts` | The single shared server read: locale + dictionary + `isAuthenticated` + `isAdmin`. |
| `app/_actions/auth.ts` | `"use server"` `signOut()` → `supabase.auth.signOut()` then `redirect("/login")`. |
| `app/_actions/locale.ts` | `"use server"` `setLocale()` → writes `NEXT_LOCALE`, `revalidatePath("/", "layout")`. |
| `app/todo/page.tsx` | `/todo` — deliberately unstyled authenticated landing that proves the guard + sign-out (`:15-17`). |
| `app/auth/callback/route.ts` | `/auth/callback` GET route handler — OAuth code exchange, origin pinning, open-redirect defence. |
| `app/awards-information/page.tsx`, `app/kudos/page.tsx`, `app/standards/page.tsx`, `app/profile/page.tsx`, `app/admin/page.tsx` | Five declared placeholders. Each is 14-16 lines: a `Metadata` title + `<ComingSoon />`. |
| `app/login/page.tsx` | `/login` — reads locale cookie + `?error`, composes the four login regions. |
| `app/login/actions.ts` | `"use server"` `signInWithGoogle()` — builds `redirectTo`, redirects to Google's consent URL. |

### `app/_components/` — shared/home components

| File | Purpose |
|---|---|
| `home-header.tsx` (client) | Sticky `banner`. Logo + `HomeNav` left; bell / language / account right. Bell + account are **absent from the DOM** when anonymous (`:66,:75`). |
| `home-nav.tsx` (client) | Three nav items; selected state derived from `usePathname()`, not hardcoded (`:50,:59`). |
| `home-hero.tsx` (server) | Keyvisual + wordmark + `CountdownTimer` + event info + two CTAs (`/awards-information`, `/kudos`). |
| `countdown-timer.tsx` (client) | ALG-001 countdown. See BL inventory. |
| `root-further-block.tsx` (server) | "Root Further" prose block; splits `paragraphs` at index 3 around the pull quote (`:20-21`). |
| `awards-grid.tsx` (server) | Section header + 6-card grid, `grid-cols-2 lg:grid-cols-3` (`:35`). |
| `award-card.tsx` (server) | One card = one `<Link href={/awards-information#<slug>}>` (`:34`). Two testids on two nested elements (`:31,:33`). |
| `kudos-promo.tsx` (server) | Kudos promo section, CTA → `/kudos`. |
| `floating-widget.tsx` (server) | `fixed` bottom-right pill: two links (`/kudos`, `/standards`) split by a "/" glyph. **Not a menu** (`:8-11`). |
| `site-footer.tsx` (client) | `contentinfo`. Logo + 4 nav links (`/`, `/awards-information`, `/kudos`, `/standards`) + copyright. Deliberately renders no current-page highlight (`:17-21`). |
| `language-selector.tsx` (client) | ARIA listbox locale switcher. Full keyboard model + outside/Escape dismissal inlined (frozen — **not** refactored onto the shared hook, `use-dismiss-on-outside.ts:8-10`). |
| `notification-bell.tsx` (client) | Toggles a presentational empty panel. **No notification backend exists** (`:38-42`) — no badge is rendered. |
| `account-menu.tsx` (client) | Profile link, conditional Admin Dashboard link, sign-out `<form action>`. |
| `coming-soon.tsx` (server) | Shared shell for all five placeholder routes — real header/footer + an honest "coming soon" body. |
| `icons.tsx` | 4 inline SVGs: `IconFlagVn`, `IconFlagEn`, `IconChevronDown`, `IconGoogle`. |
| `use-dismiss-on-outside.ts` (client) | Shared outside-pointerdown + Escape dismissal hook. |
| `use-scroll-to-top-if-current.ts` (client) | Scroll-vs-navigate rule. See BL inventory. |

### `app/login/_components/`

| File | Purpose |
|---|---|
| `login-header.tsx` (server) | Fixed-top header: non-interactive logo + `LanguageSelector`. |
| `login-content.tsx` (server) | Wordmark, copy, conditional `ErrorBanner`, `<form action={signInAction}>`. |
| `google-sign-in-button.tsx` (client) | `useFormStatus()` pending → disabled + loader (`:18`). |
| `error-banner.tsx` (server) | `role="alert" aria-live="assertive"` OAuth-failure banner. |
| `login-footer.tsx` (server) | `contentinfo` copyright bar. |
| `hero-background.tsx` (server) | Full-bleed artwork layer. **Points at `/images/login/hero.png`, which does not exist in `public/images/login/`** — a solid `#00101A` fallback shows through by design (`:4-9`). |

### `lib/`

| File | Purpose |
|---|---|
| `lib/i18n/locales.ts` | `Locale` type, `LOCALES`, `DEFAULT_LOCALE = "vi"`, `LOCALE_COOKIE = "NEXT_LOCALE"`, `resolveLocale()`. Pure — no I/O, no `next/headers`. |
| `lib/i18n/dictionaries.ts` | Static `Record<Locale, Dictionary>` map + `getDictionary()`. Deliberately not dynamic-import, deliberately **not** guarded by the `server-only` package (`:9-14`). |
| `lib/i18n/messages/dictionary.ts` | The `Dictionary` interface + `AwardKey` string-literal union. The compile-time i18n contract. |
| `lib/i18n/messages/vi.ts`, `vi-home.ts` | Vietnamese copy — the authoritative shape (`vi.ts:6-9`). |
| `lib/i18n/messages/en.ts`, `en-home.ts` | English copy, typed against the same interface. |
| `lib/awards.ts` | The 6 awards frozen in design order: `slug` + dictionary `key` + image path. Identity here, copy in the dictionary. |
| `lib/supabase/client.ts` | `createBrowserClient` factory. **Currently imported by nothing in `app/`** — no Client Component talks to Supabase directly. |
| `lib/supabase/server.ts` | Per-request `createServerClient`; swallows the Server-Component cookie-write throw (`:26-30`). |
| `lib/supabase/update-session.ts` | Token refresh + rotated-cookie write-back for `proxy.ts`; sets no-cache headers (`:30-34`). |

### `e2e/`

| File | Purpose |
|---|---|
| `e2e/fixtures/supabase-session.ts` | Mints a real GoTrue user via `signUp`, captures the library's own cookies through an in-memory jar, then deliberately back-dates `expires_at` so the proxy is forced to refresh (`:96-105`). |
| `e2e/auth.setup.ts` | Warms the `/login` client bundle to close a hydration race (`:9-22`), then writes `e2e/.auth/user.json`. |
| `e2e/homepage-auth.setup.ts` | Writes a **second, independent** session to `e2e/.auth/homepage-user.json`, isolated from C9's global sign-out (`:14-21`). |
| `e2e/smoke.spec.ts` | Harness canary — 1 test. |
| `e2e/route-guard.spec.ts` | C6 — anon `/todo` → `/login`. 1 test. |
| `e2e/authenticated.spec.ts` | C7 / C8 / C9 — authed `/login` → `/todo`, cookie rotation across the guarded redirect, sign-out. 3 tests. |
| `e2e/callback-security.spec.ts` | 7 tests: `Host`/`x-forwarded-host` spoofing, absolute / protocol-relative / backslash `next` values, one positive same-origin case. |
| `e2e/login-screen.spec.ts` | 10 tests C1–C5, C3b–C3e, C10 — login render, error banner, locale switch + cookie, dropdown visual contract, keyboard nav, bad-cookie fallback, OAuth kickoff. |
| `e2e/homepage.spec.ts` | 20 tests ID-0…ID-59 — anonymous homepage: structure, countdown (incl. expiry via clock override), responsive grid, language menu, all navigation targets. 533 lines, the largest file in the repo. |
| `e2e/homepage-authed.spec.ts` | 5 tests ID-1/27/36/38/5-37 — bell + account menu presence, panel open, menu contents, admin gating. |
| `e2e/capture-homepage-visual.spec.ts` | On-demand screenshot capture at 1512px and 375px into the plan's `evidence/`. Not part of the default run. |
| `e2e/.auth/user.json`, `e2e/.auth/homepage-user.json` | Generated storage states (artifacts, not source). |

---

## 2. Routes

Nine routes. Eight pages + one route handler. **No dynamic segments** — every route is a
literal path; there is no `[param]` directory anywhere.

| Route | Kind | Rendering | Guarded? | Evidence |
|---|---|---|---|---|
| `/` | Page (Server Component, async) | ƒ dynamic | Public | `app/page.tsx:24-25` → `getPageContext()` → `cookies()` at `app/_page-context.ts:28` |
| `/login` | Page (Server Component, async) | ƒ dynamic | Bounced when authed | `app/login/page.tsx:32` reads `cookies()` and `searchParams` |
| `/todo` | Page (Server Component, async) | ƒ dynamic | **Auth required** | `app/todo/page.tsx:19` `Promise.all([createClient(), cookies()])` |
| `/auth/callback` | Route Handler `GET` | ƒ dynamic (always) | Deliberately unguarded | `app/auth/callback/route.ts:74`; exemption reasoned at `proxy.ts:11-13` |
| `/awards-information` | Page → `<ComingSoon />` | ƒ dynamic | Public | `app/awards-information/page.tsx:12-14` |
| `/kudos` | Page → `<ComingSoon />` | ƒ dynamic | Public | `app/kudos/page.tsx:12-14` |
| `/standards` | Page → `<ComingSoon />` | ƒ dynamic | Public | `app/standards/page.tsx:12-14` |
| `/profile` | Page → `<ComingSoon />` | ƒ dynamic | **Public — explicitly not guarded** | `app/profile/page.tsx:9-11` |
| `/admin` | Page → `<ComingSoon />` | ƒ dynamic | **Public — no role check** | `app/admin/page.tsx:8-12` |

**Why everything is dynamic (ƒ):** the five placeholders render `ComingSoon`, which calls
`getPageContext()` (`app/_components/coming-soon.tsx:18`), which calls `cookies()`
(`app/_page-context.ts:28`). `cookies()` opts a route out of static generation. `/` reaches
the same call; `/login` and `/todo` call `cookies()` directly. So **no route in this app is
statically prerendered**. This is inferred from `cookies()` usage, not read off a build
manifest — I did not run `next build`, and no build output is committed.

**Server Actions** (not routes, but the third callable surface):
`signOut()` (`app/_actions/auth.ts:17`), `setLocale(locale)` (`app/_actions/locale.ts:13`),
`signInWithGoogle()` (`app/login/actions.ts:16`).

---

## 3. Server vs client boundary

**`"use client"` — 8 files** (grep over `app/ lib/`):
`app/_components/home-header.tsx`, `home-nav.tsx`, `countdown-timer.tsx`,
`notification-bell.tsx`, `account-menu.tsx`, `language-selector.tsx`,
`site-footer.tsx`, `use-dismiss-on-outside.ts`, `use-scroll-to-top-if-current.ts`,
plus `app/login/_components/google-sign-in-button.tsx`. (10 marker occurrences; the two
`.ts` files are hooks, not components.)

**`"use server"` — 3 files**: `app/_actions/auth.ts:1`, `app/_actions/locale.ts:1`,
`app/login/actions.ts:1`.

**Everything else is a Server Component**, including all 8 pages, `coming-soon.tsx`,
`home-hero.tsx`, `root-further-block.tsx`, `awards-grid.tsx`, `award-card.tsx`,
`kudos-promo.tsx`, `floating-widget.tsx`, `icons.tsx`, and 4 of the 5 login components.

**What crosses the boundary** — the rule is stated at `app/_page-context.ts:22-25` and held:

| Crossing | Payload | Note |
|---|---|---|
| `HomePage` → `HomeHeader` | `locale`, `dictionary`, `isAuthenticated: boolean`, `isAdmin: boolean`, `signOutAction` | The Supabase `user` object **never** crosses. Only the two derived booleans do (`app/page.tsx:32-38`). |
| `HomePage` → `HomeHero` | `dictionary`, `eventStartAt` read from `process.env.NEXT_PUBLIC_EVENT_START_AT` **by the page** | Passed as a literal so server and client agree; `home-hero.tsx:13-15`. `CountdownTimer` never reads `process.env` itself. |
| Server → `LanguageSelector` | `locale` + 3 label strings | The whole `Dictionary` is *not* passed here — only the 3 needed strings (`home-header.tsx:69-73`). |
| Client → Server | `signOutAction` invoked via `<form action>` (`account-menu.tsx:108`, `app/todo/page.tsx:31`); `setLocale` invoked inside `startTransition` (`language-selector.tsx:81-83`); `signInWithGoogle` via `<form action>` on `/login`. | |
| `proxy.ts` → runtime | Neither Server nor Client Component — Edge/Node proxy layer. | |

The full `Dictionary` object *is* serialized into the client bundle for `HomeHeader`,
`HomeNav`, `SiteFooter`, `NotificationBell` and `AccountMenu`. `lib/i18n/dictionaries.ts:9-14`
calls itself "server-only by convention" but that convention is broken here — the dictionary
object crosses to the client via props. Not a leak (it is public copy), but worth recording.

---

## 4. Data model / entities

**This application has no database schema of its own. None. Zero tables, zero migrations,
zero SQL.**

Confirmed:
- `supabase/migrations/` **does not exist** (`ls` → No such file or directory).
- `supabase/seed.sql` **does not exist**, despite `config.toml` declaring `[db.seed] sql_paths = ["./seed.sql"]`.
- `find . -name "*.sql"` outside `node_modules` returns **nothing**.
- No ORM, no query builder, no `from("...")` call anywhere — the only Supabase calls in the
  codebase are `auth.*` (`getUser`, `signOut`, `signInWithOAuth`, `exchangeCodeForSession`,
  `signUp`, `setSession`).

**The entire schema surface is Supabase's own managed `auth` schema** — `auth.users` and its
session/refresh-token rows, created and owned by GoTrue, not by this repo.

Fields this app actually reads off that surface:

| Read | Where | Use |
|---|---|---|
| `user` (null vs non-null) | `app/_page-context.ts:31,39` · `lib/supabase/update-session.ts:41-43` | `isAuthenticated`, route guard |
| `user.app_metadata.role` | `app/_page-context.ts:40` | `isAdmin` — compared against the literal `"admin"` |
| `user.email` | `app/todo/page.tsx:30` | Display only |

`app_metadata.role` is **never written by this codebase** — no code sets it. It is assumed to
be provisioned out-of-band in Supabase.

**Client-side persisted state**: exactly one cookie this app owns — `NEXT_LOCALE`
(`lib/i18n/locales.ts:14`), plus the `sb-*-auth-token` cookies GoTrue writes.

**In-repo data structures that stand in for tables**:
- `AWARDS` — 6 hardcoded records in `lib/awards.ts:27-42`. The award "catalog" is a frozen TS array, not data.
- `vi`/`en` dictionaries — static objects, not a translations table.

**Not present anywhere**: no API layer of the app's own (beyond the one OAuth callback), no
state-management library (no Redux/Zustand/Jotai/Context provider — state is `useState` in 5
client components), no data-fetching library (no SWR/TanStack Query), no form library, no
validation library (no Zod/Yup).

---

## 5. Business-logic inventory

Nine pieces of real decision logic. Everything else in the repo is presentation.

### BL-01 · Locale resolution + fallback — `lib/i18n/locales.ts:22-24`
```ts
return LOCALES.includes(value as Locale) ? (value as Locale) : DEFAULT_LOCALE;
```
Total function over untrusted input. `undefined`, `""`, `"fr"`, an injected cookie value —
all collapse to `"vi"`. Rule BR-003. Called from 4 sites: `_page-context.ts:33`,
`login/page.tsx:37`, `todo/page.tsx:24`, `_actions/locale.ts:14`. The write path
(`locale.ts:14`) resolves *before* writing, so a bad value can never enter the cookie from
this app.

### BL-02 · Dictionary selection — `lib/i18n/dictionaries.ts:16-20`
Static `Record<Locale, Dictionary>` lookup. Total by construction (the key type is the
2-member union). No fallback branch needed and none exists. Deliberately not lazy (`:9-10`).

### BL-03 · Countdown computation — `app/_components/countdown-timer.tsx:43-63`
Three branches, all reachable:

| Branch | Condition | Output |
|---|---|---|
| Invalid/missing config | `parseEventDate` returns `null` — `!value` or `Number.isNaN(date.getTime())` (`:43-47`) | `00/00/00`, "Coming soon" **hidden**, exactly one `console.warn`, never throws (`:79-88`) |
| Expired | `diffMs <= 0` (`:51`) | `00/00/00`, "Coming soon" **hidden** (`showComingSoon: false`) |
| Live | `diffMs > 0` | floor-divide into days/hours/minutes, each `padStart(2,"0")`, "Coming soon" **shown** (`:54-62`) |

Two further decisions worth recording:
- **Recompute, never accumulate** (`:50` re-reads `Date.now()` every tick) — self-corrects against browser tab throttling.
- **Hydration**: the initial state (`:72-75`) deliberately touches no clock — it derives `showComingSoon` purely from whether the prop string parses, so server and client markup agree and `suppressHydrationWarning` is never needed. The live values arrive from `useEffect` after mount (`:77-95`).
- `warnedRef` (`:70,:82`) absorbs React Strict Mode's dev-only double effect so the warning fires once, not twice.
- Note the three-digit ceiling: `days` is not clamped, so a target >99 days out renders a 3-char string and `const [tens, units] = value` (`:119`) silently drops the third digit. `playwright.config.ts:29-31` pins the test value to 45 days specifically to stay under this.

### BL-04 · Auth route guard — `proxy.ts:41-46`
Two rules, both prefix matches, nothing else guarded:
- `!user && pathname.startsWith("/todo")` → `/login`
- `user && pathname.startsWith("/login")` → `/todo`

Everything else falls through, `/auth/callback` in particular — guarding it would make the
OAuth round-trip structurally impossible (`:11-13`).

### BL-05 · Cookie-preserving redirect — `proxy.ts:30-39`
The non-obvious half of the guard. `updateSession()` builds a *new* `NextResponse` inside its
cookie callback whenever GoTrue rotates the refresh token; a bare `NextResponse.redirect()`
would be a third response that never saw those `Set-Cookie` headers. Because Supabase refresh
tokens are single-use, dropping them logs the user out on the very next request. So every
guard redirect copies `response.cookies.getAll()` onto the redirect (`:35-37`). Covered by E2E
case C8.

### BL-06 · Session refresh + cache poisoning defence — `lib/supabase/update-session.ts:22-35,41-43`
`supabase.auth.getUser()` at `:43` is what actually performs the refresh (`:40` says so).
On rotation, the `setAll` callback rebuilds the response and copies the library's headers
(`:32-34`) so CDNs/reverse proxies cannot cache a response carrying another user's auth cookies.

### BL-07 · OAuth callback — origin pinning, open-redirect defence, error funnel — `app/auth/callback/route.ts:31-107`
Three distinct decisions:
1. **`resolveSiteOrigin()` (`:31-43`)** — the redirect origin comes from `NEXT_PUBLIC_SITE_URL`, never from the request. Two documented traps: `request.nextUrl.origin` rewrites `127.0.0.1` → `localhost` (`:16-21`, and the session cookie is pinned to `127.0.0.1`); the raw `Host` header is client-controlled and this route is reachable unauthenticated, so building a redirect from it is CWE-644 (`:23-26`). A malformed env var falls to `FALLBACK_ORIGIN` rather than becoming a redirect target (`:38`).
2. **`resolveNextPath()` (`:54-64`)** — parses the candidate against our own origin and compares. Rejects absolute URLs, `//evil.com`, and `/\evil.com` (which WHATWG normalizes to `//evil.com`, so a naive `startsWith("//")` misses it — `:49-52`). Default `/todo`.
3. **Branch funnel (`:74-107`)** — `error` param present → skip the exchange entirely (the user-declined-consent path, `:81-85`). `code` present and exchange clean → `next`. Anything else — no params, exchange error, or a thrown transport failure (`:90-93`) — → one fixed `/login?error=oauth_failed`. **The provider's raw error text is never reflected** into the URL or the UI (`:68-70`).

### BL-08 · Role gating — `app/_page-context.ts:40` + `app/_components/account-menu.tsx:99-107`
`isAdmin = user?.app_metadata?.role === "admin"` — a strict literal comparison, optional-chained
so an absent `app_metadata` yields `false` rather than throwing. It gates **one thing only**:
whether the Admin Dashboard `<Link>` renders in the account menu. `/admin` itself performs no
check (`app/admin/page.tsx:8-12` says so outright: it is a placeholder that "doesn't pretend to
check the admin role"). **This is presentation gating, not authorization.**

### BL-09 · Scroll-vs-navigate rule — `app/_components/use-scroll-to-top-if-current.ts:18-35`
`scrollToTopHandler` swallows the click and smooth-scrolls to top. The whole point is the
**condition** (`:11-16`): attach it only when the link already points at the current route.
`useScrollToTopIfCurrent(href)` returns `undefined` off-route so the `<Link>` navigates
normally. Two consumers use the hook (`home-header.tsx:39`, `site-footer.tsx:25`); `HomeNav`
composes the bare handler with its own `selected` check instead, because calling a hook inside
`.map()` would be a hook in a loop (`:27-30`). The doc comment records the regression this
fixes: applying it unconditionally turned "back to home" into a dead end on all five
placeholder routes.

### BL-10 · Dismissal contract for popovers — `app/_components/use-dismiss-on-outside.ts:19-41`
Outside `pointerdown` closes **without** moving focus (the user aimed elsewhere, `:24`);
`Escape` closes **and returns focus to the trigger** (`:29-32`). Used by the bell and account
menu. `language-selector.tsx:53-75` holds a byte-equivalent inline copy that was deliberately
**not** retrofitted onto the hook (`use-dismiss-on-outside.ts:8-10`) — a known, documented
duplication.

### Also load-bearing, but thinner
- `app/login/page.tsx:41-43` — the error banner is driven by *presence* of `?error`, not its value; handles both `string` and `string[]` shapes of the param.
- `app/login/actions.ts:17-22` — fails fast on a missing `NEXT_PUBLIC_SITE_URL` rather than composing a broken `undefined/auth/callback`.
- `app/_actions/auth.ts:17-21` — `signOut()`'s error is deliberately discarded so an already-invalid session still lands on `/login`; `redirect()` sits outside any try/catch because it throws `NEXT_REDIRECT` internally (same reasoning at `login/actions.ts:11-14`).
- `app/_actions/locale.ts:26` — `revalidatePath("/", "layout")` widened from a `/login`-only revalidation once the homepage started rendering locale-dependent copy.
- `app/_components/root-further-block.tsx:20-21` — the pull quote is inserted after `paragraphs[2]`, a fixed index tied to the design, not to content.
- `app/_page-context.ts:28` — `Promise.all([createClient(), cookies()])` so the two reads run concurrently.

---

## 6. Auth / permissions surface

**Provider**: Google OAuth only, through Supabase GoTrue. `supabase/config.toml:336-338` —
`[auth.external.google] enabled = true`, credentials via `env(...)` substitution.
Apple and every other provider are `enabled = false`. Email signup is on
(`enable_signup = true`) but the app exposes **no** email/password UI — only the E2E fixture
uses `signUp` (`e2e/fixtures/supabase-session.ts:81`).

**No domain allow-list.** `app/login/actions.ts:8-9` states it explicitly: BR-001, every Google
account is permitted.

**Flow**: `/login` form → `signInWithGoogle()` server action → `supabase.auth.signInWithOAuth({ provider: "google", redirectTo: ${NEXT_PUBLIC_SITE_URL}/auth/callback })` → `redirect(data.url)` to Google → Google → `/auth/callback` → `exchangeCodeForSession(code)` → redirect to `next` (default `/todo`).

**Session maintenance**: `proxy.ts` runs on every non-asset request (matcher at `:51-56`
excludes `_next/static`, `_next/image`, `favicon.ico`, and 9 asset extensions) and calls
`updateSession()`, whose `getUser()` performs the actual token refresh. Refresh-token rotation
is on with a 10s reuse interval (`config.toml`: `enable_refresh_token_rotation = true`,
`refresh_token_reuse_interval = 10`), JWT expiry 3600s.

**Protected surface — exactly one route**: `/todo`. Plus `/login`'s inverse bounce.
Both at `proxy.ts:41-46`.

**Public surface**: `/`, `/awards-information`, `/kudos`, `/standards`, `/profile`, `/admin`,
`/auth/callback`. `/profile` and `/admin` being public is deliberate and documented
(`app/profile/page.tsx:9-11`, `app/admin/page.tsx:8-12`) — they hold no content yet.

**Authorization model**: there is effectively none. The single role signal,
`app_metadata.role === "admin"` (`app/_page-context.ts:40`), controls only whether a menu link
renders (`account-menu.tsx:99`). No route, no action, and no data read checks it. Anyone can
navigate to `/admin` directly.

**Anonymous vs authenticated UI difference** (`home-header.tsx:66,:75`): bell and account menu
are conditionally *rendered*, i.e. absent from the DOM, not hidden with CSS. Rule BR-002.

**Origin pinning**: `site_url = "http://127.0.0.1:3000"` with 4 entries in
`additional_redirect_urls`. `.env.example` warns that `NEXT_PUBLIC_SITE_URL` must match
exactly or Supabase rejects the redirect. `playwright.config.ts:22-24` repeats the
127.0.0.1-vs-localhost cookie-domain warning.

**Secrets**: no service-role key anywhere; `.env.example` explains its deliberate absence.
Both Google credentials use `env(...)` substitution in `config.toml` rather than literals.

---

## 7. i18n surface

**Scheme**: cookie-based, no URL segment, no `[locale]` route, no middleware negotiation, no
`Accept-Language` sniffing. Two locales.

| Element | Value | Location |
|---|---|---|
| Cookie name | `NEXT_LOCALE` | `lib/i18n/locales.ts:14` |
| Cookie attrs | `path: "/"`, `maxAge` 1 year, `sameSite: "lax"` | `app/_actions/locale.ts:16-20` |
| Locales | `["vi", "en"]` | `lib/i18n/locales.ts:10` |
| Default | `"vi"` — **vi is primary** | `lib/i18n/locales.ts:12` |
| Read sites | `_page-context.ts:33`, `login/page.tsx:37`, `todo/page.tsx:24` | |
| Write site | `setLocale()` server action, one caller (`language-selector.tsx:82`) | |
| Invalidation | `revalidatePath("/", "layout")` — whole layout subtree | `app/_actions/locale.ts:26` |

**vi is the authoritative shape** (`lib/i18n/messages/vi.ts:6-9`): `vi.ts`/`vi-home.ts` carry
copy transcribed verbatim from the design, and both files carry explicit "do not paraphrase"
instructions (`vi-home.ts:3-6`).

**The `Dictionary` compile-time contract** (`lib/i18n/messages/dictionary.ts`): a single
`interface` both locale objects are typed against, so a key present in `vi` but missing from
`en` fails `npm run typecheck` rather than degrading to a runtime blank (`:5-8`). Two design
notes on the type:
- Fields are plain `string`, not `as const` literals, so `en.ts` can hold different copy under the same type (`:2-4`).
- `AwardKey` is a **string-literal union** and `home.awards.cards` is `Record<AwardKey, ...>`, so a missing award card is a compile error, not a silent gap in the grid (`:11-22`).

**Deliberately untranslated strings** (`en.ts:7-11`): `login.signInButton`
("LOGIN With Google") and the three `header` nav labels stay English in both locales because
the design shows them that way. Not a bug.

**Known gaps** (read, not inferred):
- `app/layout.tsx:15` hardcodes `lang="en"` and never reads the locale cookie. On the `vi` default the document language attribute is wrong.
- `vi-home.ts:7-9` records one deliberate divergence from the design: "Coming soon" is spelled correctly here though the frame reads "Comming soon".
- `home.eventTimeValue` is a hardcoded copy string `"26/12/2025"` (`vi-home.ts`), independent of `NEXT_PUBLIC_EVENT_START_AT`. The two can drift.

---

## 8. Test surface

Playwright only. **No unit-test runner, no Vitest/Jest, no component tests, no `__tests__`
directory** — `package.json:11` has `test:e2e` and nothing else.

47 tests across 8 spec files + 2 setup files. `fullyParallel: false`
(`playwright.config.ts:40`). `reuseExistingServer: false` (`:99`) so the pinned countdown env
is re-read every run.

| Project | testMatch | Spec files it runs | Deps | storageState |
|---|---|---|---|---|
| `setup` | `/^((?!homepage).)*auth\.setup\.ts$/` (`:50`) | `e2e/auth.setup.ts` | — | writes `e2e/.auth/user.json` |
| `homepage-auth-setup` | `/homepage-auth\.setup\.ts$/` (`:56`) | `e2e/homepage-auth.setup.ts` | — | writes `e2e/.auth/homepage-user.json` |
| `anon` | `/(?:smoke\|login-screen\|route-guard\|callback-security\|homepage)\.spec\.ts/` (`:62`) | `smoke` (1), `login-screen` (10), `route-guard` (1), `callback-security` (7), `homepage` (20) = **39 tests** | `setup` | none (anonymous) |
| `authed` | `/authenticated\.spec\.ts/` (`:70`) | `authenticated.spec.ts` — C7/C8/C9 (**3 tests**) | `setup` | `e2e/.auth/user.json` |
| `homepage-authed` | `/homepage-authed\.spec\.ts/` (`:81`) | `homepage-authed.spec.ts` — ID-1/27/36/38/5-37 (**5 tests**) | `homepage-auth-setup` | `e2e/.auth/homepage-user.json` |
| `visual-capture` | `/capture-homepage-visual\.spec\.ts/` (`:91`) | `capture-homepage-visual.spec.ts` (**1 test**) — on-demand only | `homepage-auth-setup` | — |

Note the `anon` regex also matches `homepage-authed.spec.ts` on substring, but that file is
claimed by its own project; and `capture-homepage-visual.spec.ts` is excluded from `anon`
because the regex requires `.spec.ts` immediately after `homepage`.

**Why two independent sessions exist** — `homepage-auth.setup.ts:14-21`: `authenticated.spec.ts`'s
C9 calls `signOut()` at the default `scope: "global"`, revoking the one shared session for every
test in the `authed` project. Homepage-authed tests were failing nondeterministically depending on
whether their page load beat the revocation. Root cause is written up in
`plans/260905-1153-homepage-saa/reports/debugger-260905-1353-authed-e2e-failures.md`.

**Two documented environment hacks**, both real and both load-bearing:
- `playwright.config.ts:5-20` — vendored Chromium shared libs under `.playwright-libs/` for WSL2 machines where `playwright install --with-deps` needs interactive root. No-op when the directory is absent.
- `auth.setup.ts:9-22` — a client-bundle warmup that opens `/login` in a real browser and proves hydration (opens the listbox, `:40-41`) before any test runs. The comment records 46.8s-with-failures cold vs 11.6s-all-passing warm. `/todo` is deliberately *not* warmed (`:43-45`) — its sign-out is a plain form submit in a Server Component and needs no hydration.

**Session minting** (`e2e/fixtures/supabase-session.ts`): tests do not drive Google's consent
screen. They call `signUp` against local GoTrue with a `${Date.now()}-${pid}-${random}` email
(`:77` — the collision reasoning at `:70-76` is real: two setup projects can land in the same
millisecond), capture whatever cookies the library writes via an in-memory jar (`:52-68`, so
chunking and base64url encoding are never hand-rolled), then **back-date `expires_at` by 60s**
(`:100-103`) so the proxy is forced to refresh during the guarded redirect — that is what makes
C8 a real test of BL-05.

**Coverage shape**: security paths are the best-covered surface (7 callback-security tests +
C10). The countdown's expiry branch is exercised via a clock override in `homepage.spec.ts`
(ID-41/42/43). **`isAdmin`/ID-5/37 is present in `homepage-authed.spec.ts:104` but marked
skipped per ORCH-03** (`app/admin/page.tsx:10-11` references the skip). Nothing tests
`resolveLocale` or `computeCountdown` as pure functions — no unit layer exists to do it.

---

## 9. External integrations

**Supabase, and nothing else.** Runtime dependency list is 5 packages
(`package.json:14-20`): `@supabase/ssr`, `@supabase/supabase-js`, `next`, `react`, `react-dom`.

| Integration | Surface | Where |
|---|---|---|
| Supabase Auth (GoTrue) | `signInWithOAuth`, `exchangeCodeForSession`, `getUser`, `signOut` | `login/actions.ts:25`, `auth/callback/route.ts:96`, `_page-context.ts:31` + `update-session.ts:43` + `todo/page.tsx:22`, `_actions/auth.ts:19` |
| Google OAuth | Reached **only through** Supabase — no Google SDK, no direct Google API call | `config.toml:336-338` |
| Google Fonts | `next/font/google` (Montserrat, Montserrat Alternates) — self-hosted at build time by Next, not a runtime call | `app/_fonts.ts:1`, `app/login/page.tsx:2` |

**Supabase surfaces enabled in `config.toml` but unused by the app**: Storage
(`[storage] enabled = true`), Realtime (`enabled = true`), Studio, the vector store, the S3
protocol layer. These are local-stack defaults, not integrations — no code touches them.

**Explicitly absent**: no analytics, no error tracking (no Sentry), no email service, no
payment provider, no CMS, no feature-flag service, no logging service, no CDN configuration,
no CI workflow (`.github/` absent), no Dockerfile, no deployment config
(`vercel.json`/`netlify.toml` absent).

---

## Notable observations for downstream researchers

1. **Do not document a database.** There is no schema, no migration, no table, no query. Anything claiming otherwise is invented. The only persisted app-owned state is one cookie.
2. **Do not document an API layer.** One route handler exists and it is the OAuth callback. There are no REST/GraphQL endpoints of the app's own.
3. **`/admin` is not admin-protected.** The role check gates a menu link and nothing more. Describing it as an authorization boundary would be false.
4. **`hero-background.tsx` references `/images/login/hero.png`, which is not in `public/`.** The dark fallback is the shipped visual. Documented as intentional at `:4-9`.
5. **Two duplications are deliberate and documented**: `/login`'s own font instances (`_fonts.ts:9-11`) and the language selector's inline dismissal logic (`use-dismiss-on-outside.ts:8-10`). Both name the reason. Do not report them as accidental drift.
6. **`app/globals.css:3-28` still carries `create-next-app` boilerplate** (light/dark `--background`, Arial body font) that every page overrides with `bg-[#00101A]`. Dead but harmless.
7. **Every route is dynamic.** No page in this app can be statically prerendered as written, because `cookies()` is reached on all of them.
8. **`app/layout.tsx:15` hardcodes `lang="en"`** while the default locale is `vi` — a real, unclaimed i18n defect.
9. Every component file carries a `mm:<node-id>` comment tying it to a MoMorph/Figma node, plus prose recording *why* a value was chosen or a design detail was departed from. These comments are the richest requirements source in the repo and are worth reading over the design docs.
10. **File-size rule holds**: the largest source file is `e2e/homepage.spec.ts` at 533 lines (a test file); no component exceeds 188 lines.

## Unresolved questions

- `app_metadata.role` is read but never written anywhere in the repo. How is an admin provisioned? Not answerable from code.
- `home.eventTimeValue` (`"26/12/2025"`) and `NEXT_PUBLIC_EVENT_START_AT` are independent sources for the same fact. Is the duplication intentional, or expected to be derived?
- `lib/supabase/client.ts` has no importer in `app/`. Dead code, or reserved for a planned client-side feature?
- `docs/.rebuild-state.json`, `_canonical-fcodes.json`, `_source-to-fcode.json` and `release-manifest.json` were treated as tooling state and not analyzed. Flag if the Core pass needs them read.
