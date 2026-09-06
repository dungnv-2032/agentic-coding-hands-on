---
authored_by: rebuild-spec (Core pass, generated layer)
---

# Behavior Logic

**Project**: my-app (SAA 2025)
**Generated**: 2026-09-05
**Analysis Scope**: `lib/i18n/`, `proxy.ts`, `lib/supabase/update-session.ts`, `app/auth/callback/route.ts`, `app/_components/`

**Note on the canonical 10 BL types**: this taxonomy (`custom-command`, `event-listener`,
`integration`, `mail`, `middleware`, `notification`, `observer`, `queue-worker`,
`scheduled-job`, `webhook`) targets backend job/event patterns. This app has no cron, no queue,
no email, no webhook receiver — its real decision logic is almost entirely request-scoped
(i18n resolution, session/cookie mechanics) or pure client-rendering rules. Five items below
fit the canonical types cleanly (`middleware`/`integration`); four do not fit any of the 10 and
are documented under **Client-Side Logic** instead of forced into a mismatched type — this is a
deliberate choice, not an omission (see Cardinality note below).

**Auth route guard is excluded from this file on purpose**: `proxy.ts:41-46`'s two redirect
rules are auth middleware and belong to `permissions-matrix.md` (PERM001/PERM002) per the
canonical rule "Auth/permission middleware → Permissions artifact only."

## Behavior Logic Index

### Type: middleware

| Code | Name | Trigger | Payload | File Schema |
|------|------|---------|---------|--------------|
| BL001 | Locale resolution + fallback | Every read of the `NEXT_LOCALE` cookie or a candidate locale string, at 4 call sites | N/A — synchronous return value, not async | N/A — not a file-exchange type |
| BL002 | Dictionary selection | Called immediately after BL001 resolves a locale, at render time | N/A | N/A |
| BL003 | Cookie-preserving redirect | Every guarded redirect (`proxy.ts:41-46`) whenever GoTrue rotates the refresh token | N/A | N/A |
| BL004 | Session refresh + cache-poisoning defence | Every non-asset request, via `proxy.ts`'s call into `updateSession()` | N/A | N/A |

### Type: integration

| Code | Name | Trigger | Payload | File Schema |
|------|------|---------|---------|--------------|
| BL005 | OAuth callback — origin pinning, open-redirect defence, error funnel | GET `/auth/callback`, on every Google OAuth round-trip | N/A — 302 redirect, not a message payload | N/A |

---

## Dev Appendix

### Cardinality Contract

Rule C1 (1 BL per inventory entry) applied: each BL below is one distinct decision point at one
file location, matching `scout-report.md` §5's numbering 1:1 (BL-01→BL001, BL-02→BL002,
BL-05→BL003, BL-06→BL004, BL-07→BL005). Scout's BL-04 (route guard) is excluded per the
Inclusion/Exclusion Matrix (auth middleware → Permissions). Scout's BL-03/08/09/10 (countdown,
role gating, scroll-vs-navigate, dismissal contract) are pure client-rendering decision logic
with no canonical-10 type match — documented under **Client-Side Logic** below rather than
force-typed.

---

## BL001: Locale resolution + fallback

**Type**: middleware
**Trigger**: Called at 4 sites whenever a locale value needs resolving from untrusted input (cookie or write-path candidate)
**Payload**: N/A
**File Schema**: N/A — not a file-exchange type
**Source File**: `lib/i18n/locales.ts`
**Source Symbol**: `resolveLocale`

### Description

Total function over untrusted input (`lib/i18n/locales.ts:22-24`):
```ts
return LOCALES.includes(value as Locale) ? (value as Locale) : DEFAULT_LOCALE;
```
`undefined`, `""`, `"fr"`, or any injected cookie value all collapse to `"vi"` (`DEFAULT_LOCALE`).
Called from `app/_page-context.ts:33`, `app/login/page.tsx:37`, `app/todo/page.tsx:24`, and
`app/_actions/locale.ts:14`. The write path (`locale.ts:14`) resolves *before* writing the
cookie, so a bad value can never enter `NEXT_LOCALE` from this app itself.

### Related Modules

- `app/_page-context.ts`
- `app/login/page.tsx`
- `app/todo/page.tsx`
- `app/_actions/locale.ts`

### Related Data Models

- MODEL004_Locale

---

## BL002: Dictionary selection

**Type**: middleware
**Trigger**: Called immediately after a `Locale` is resolved, at every server render that needs copy
**Payload**: N/A
**File Schema**: N/A — not a file-exchange type
**Source File**: `lib/i18n/dictionaries.ts`
**Source Symbol**: `getDictionary`

### Description

Static `Record<Locale, Dictionary>` lookup (`lib/i18n/dictionaries.ts:16-20`). Total by
construction — the key type is the 2-member `Locale` union, so no fallback branch is needed or
exists. Deliberately not lazy-imported (`:9-10`); deliberately not guarded by the `server-only`
package, even though a comment calls it "server-only by convention" — the full `Dictionary`
object does cross into client components (`HomeHeader`, `HomeNav`, `SiteFooter`,
`NotificationBell`, `AccountMenu`) via props, which is not a leak (public copy) but is a real
divergence from the stated convention.

### Related Modules

- `app/_page-context.ts`
- `app/_components/home-header.tsx`

### Related Data Models

- MODEL002_Dictionary
- MODEL004_Locale

---

## BL003: Cookie-preserving redirect

**Type**: middleware
**Trigger**: Every request matching one of the two guard rules in `proxy.ts:41-46`
**Payload**: N/A
**File Schema**: N/A
**Source File**: `proxy.ts`
**Source Symbol**: `proxy` (inline function `redirectWithSessionCookies`, `:30-39`)

### Description

The non-obvious half of the route guard. `updateSession()` builds a *new* `NextResponse` inside
its cookie callback whenever GoTrue rotates the refresh token; a bare `NextResponse.redirect()`
would be a third response that never saw those `Set-Cookie` headers. Because Supabase refresh
tokens are single-use, dropping them logs the user out on the very next request. So every guard
redirect copies `response.cookies.getAll()` onto the redirect (`proxy.ts:35-37`). Covered by E2E
case C8 (`e2e/authenticated.spec.ts`).

### Related Routes

- (any) `/todo`
- (any) `/login`

### Related Data Models

- MODEL001_AuthUser (session/refresh-token rows GoTrue manages)

---

## BL004: Session refresh + cache-poisoning defence

**Type**: middleware
**Trigger**: Every non-asset request (proxy matcher excludes `_next/static`, `_next/image`, `favicon.ico`, and 9 asset extensions)
**Payload**: N/A
**File Schema**: N/A
**Source File**: `lib/supabase/update-session.ts`
**Source Symbol**: `updateSession`

### Description

`supabase.auth.getUser()` (`update-session.ts:43`) is what actually performs the token refresh
(comment at `:40` confirms). On rotation, the `setAll` callback rebuilds the response and copies
the library's headers (`:32-34`) so CDNs/reverse proxies cannot cache a response carrying another
user's auth cookies. Refresh-token rotation is on with a 10s reuse interval
(`supabase/config.toml`: `enable_refresh_token_rotation = true`, `refresh_token_reuse_interval = 10`);
JWT expiry 3600s.

### Related Modules

- `proxy.ts`

### Related Data Models

- MODEL001_AuthUser

---

## BL005: OAuth callback — origin pinning, open-redirect defence, error funnel

**Type**: integration
**Trigger**: GET `/auth/callback`, every Google OAuth round-trip
**Payload**: N/A — this is a synchronous 302-redirect handler, not an async message; see `api-map.md` for the endpoint contract
**File Schema**: N/A
**Source File**: `app/auth/callback/route.ts`
**Source Symbol**: `GET` (helpers `resolveSiteOrigin`, `resolveNextPath`)

### Description

Three distinct decisions, all at `app/auth/callback/route.ts:31-107`:

1. **`resolveSiteOrigin()` (`:31-43`)** — the redirect origin comes from `NEXT_PUBLIC_SITE_URL`,
   never from the request. `request.nextUrl.origin` rewrites `127.0.0.1` → `localhost`
   (`:16-21`, and the session cookie is pinned to `127.0.0.1`); the raw `Host` header is
   client-controlled and this route is reachable unauthenticated, so building a redirect from it
   is CWE-644 (`:23-26`). A malformed env var falls to `FALLBACK_ORIGIN` rather than becoming a
   redirect target (`:38`).
2. **`resolveNextPath()` (`:54-64`)** — parses the candidate `next` param against our own origin
   and compares. Rejects absolute URLs, `//evil.com`, and `/\evil.com` (which WHATWG normalizes
   to `//evil.com`, so a naive `startsWith("//")` misses it — `:49-52`). Default `/todo`.
3. **Branch funnel (`:74-107`)** — `error` param present → skip the exchange entirely (user
   declined consent, `:81-85`). `code` present and exchange clean → redirect to `next`. Anything
   else (no params, exchange error, or thrown transport failure `:90-93`) → fixed
   `/login?error=oauth_failed`. **The provider's raw error text is never reflected** into the URL
   or the UI (`:68-70`).

### Related Routes

- (GET) `/auth/callback` — ROUTE001

### Related Data Models

- MODEL001_AuthUser

---

## Summary

- **Total Behavior Logic Items**: 5
- **By Type**: middleware: 4, integration: 1, custom-command: 0, event-listener: 0, mail: 0, notification: 0, observer: 0, queue-worker: 0, scheduled-job: 0, webhook: 0

---

## Cross-Reference Validation

- [x] All BL### codes are unique
- [x] All Source File paths match `scout-report.md` §5 inventory entries
- [x] All related route references are valid (ROUTE001 in `route-list.md`)
- [x] All related data model references are valid (MODEL001/002/004 in `entities.md`)
- [x] No orphaned behavior logic references

---

## Client-Side Logic

Five genuine decision-logic items exist that have no clean home in the canonical-10 BL taxonomy
(they are not background jobs, not middleware chains, not third-party integrations) and do not
match the template's five named client patterns (debounce, optimistic-UI, polling, upload
progress, realtime) either. Documented here in full rather than mistyped or dropped.

### Countdown computation

**Source**: `app/_components/countdown-timer.tsx:43-63`
**Trigger**: Component mount, then every `requestAnimationFrame`/interval tick

Three branches, all reachable:

| Branch | Condition | Output |
|--------|-----------|--------|
| Invalid/missing config | `parseEventDate` returns `null` (`!value` or `NaN` getTime, `:43-47`) | `00/00/00`, "Coming soon" hidden, exactly one `console.warn`, never throws (`:79-88`) |
| Expired | `diffMs <= 0` (`:51`) | `00/00/00`, "Coming soon" hidden (`showComingSoon: false`) |
| Live | `diffMs > 0` | floor-divide into days/hours/minutes, `padStart(2,"0")`, "Coming soon" shown (`:54-62`) |

Recomputes from `Date.now()` every tick rather than accumulating (`:50`) — self-corrects against
tab throttling. Initial render state touches no clock (`:72-75`) so server/client markup agree
without `suppressHydrationWarning`; live values arrive from `useEffect` after mount. Known
ceiling: `days` isn't clamped past 3 digits — `const [tens, units] = value` (`:119`) silently
drops a third digit past 99 days; `playwright.config.ts:29-31` pins the test fixture to 45 days
to stay under it.

### Admin role gating (computation side — see PERM004 for the enforcement side)

**Source**: `app/_page-context.ts:40` (`isAdmin = user?.app_metadata?.role === "admin"`)
**Trigger**: Every page render that calls `getPageContext()`

Strict literal comparison, optional-chained so an absent `app_metadata` yields `false` rather
than throwing. The computed boolean gates exactly one thing: the Admin Dashboard `<Link>` in
`account-menu.tsx:99-107`. See `permissions-matrix.md` PERM004 for why this is presentation
gating, not authorization.

### Scroll-vs-navigate rule

**Source**: `app/_components/use-scroll-to-top-if-current.ts:18-35`
**Trigger**: Click on a nav `<Link>` whose `href` matches the current route

`scrollToTopHandler` swallows the click and smooth-scrolls to top; the condition (`:11-16`) is
the entire point — attach it only when the link already points at the current route.
`useScrollToTopIfCurrent(href)` returns `undefined` off-route so the `<Link>` navigates normally.
Two consumers use the hook (`home-header.tsx:39`, `site-footer.tsx:25`); `HomeNav` composes the
bare handler with its own `selected` check instead, since calling a hook inside `.map()` would be
a hook-in-a-loop violation (`:27-30`). Fixes a regression: applying it unconditionally turned
"back to home" into a dead end on every route that reuses the header and footer — the four
remaining `ComingSoon` placeholders plus `/awards-information`. (The source comment at
`use-scroll-to-top-if-current.ts:14` still says "the five ComingSoon placeholders"; that count
predates F003 and is now four. Comment only — the behavior is route-agnostic and unaffected.)

### Outside/Escape dismissal contract

**Source**: `app/_components/use-dismiss-on-outside.ts:19-41`
**Trigger**: `pointerdown` outside the open popover, or `Escape` while it is open

Outside `pointerdown` closes **without** moving focus (`:24` — the user aimed elsewhere);
`Escape` closes **and** returns focus to the trigger (`:29-32`). Used by the notification bell
and account menu. `language-selector.tsx:53-75` holds a byte-equivalent inline copy deliberately
**not** retrofitted onto this shared hook (`use-dismiss-on-outside.ts:8-10`) — documented,
intentional duplication, not accidental drift.

### Award category scroll-spy + click lock (F003)

**Source**: `app/awards-information/_components/use-award-scroll-spy.ts:81-105` (resolve),
`:149-165` (observer), `:114-136` (lock release), `:176-193` (click)
**Trigger**: `IntersectionObserver` fires on any of the six award sections crossing the measurement
band; user click on a category menu item; `wheel`/`touchstart`/`keydown` during a click's settle
window

The observer is only a *trigger*, never the data source — its callback sees only the entries that
changed in that batch, which under a fast flick can rank a section that has already left the band.
Every fire re-measures all six sections live (`:85-90`) and picks the one whose top edge is closest
to the band top. Band runs from `--award-header-offset` down to 45% of viewport height, mirroring
the `rootMargin: -${offset}px 0px -55% 0px`.

| Branch | Condition | Output |
|--------|-----------|--------|
| Click lock held | `clickLock.current` true (`:158`) | Return without touching state — stops the menu flickering along a smooth scroll |
| A section in band | any rect straddles `[bandTop, bandBottom)` | `activeSlug` = nearest-to-band-top section (`:88-92`) |
| Above the first section | no section in band AND first section's top `>= bandBottom` (`:103-104`) | Falls back to the first slug — the frame lights Top Talent at the hero |
| Below the last section | no section in band, first section above the band | Keeps the current slug — never drops to zero active |

`activeSlug` is a single value, not a set, so "exactly one active" is an invariant of the state
shape rather than a cleanup step. A click sets the slug, locks, scrolls
(`behavior: "smooth"`, or `"auto"` under `prefers-reduced-motion`, `:180-184`), and
`history.replaceState`s the fragment — replace, never push, so Back leaves the page rather than
walking back through categories (`:186`). The lock expires after 700ms
(`SCROLL_SETTLE_MS`, `:25`) **or immediately** on a real user scroll input, and releasing always
re-runs the measurement (`:121`) — because `IntersectionObserver` only fires on *change*, a scroll
that ended inside the window would otherwise leave the menu stuck on the clicked item forever.

Hydration constraint: the first client render must byte-match the server's, and the suite asserts
zero console errors. A URL fragment never reaches the server, so the initial active item is always
`items[0]` (`:31`) and `location.hash`/`matchMedia`/`history` are touched only inside effects. The
deep-link effect (`:143-147`) therefore controls *position* only — it validates the fragment against
the frozen slug list before `getElementById`, then `scrollIntoView({ behavior: "auto" })`. The active
item catches up when the observer first delivers, a measured ~290ms after load. Accepted
deliberately — see `docs/features/F003_AwardSystem/functional-spec.md` § 11 RISK-04.

### Debounce / Throttle, Optimistic UI, Polling, Upload Progress, Realtime

N/A — no debounce/throttle, optimistic UI, polling, upload-progress, or realtime (WebSocket/SSE)
patterns detected anywhere in `app/` or `lib/`.
