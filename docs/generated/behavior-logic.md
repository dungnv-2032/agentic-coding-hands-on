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

Nine genuine decision-logic items exist that have no clean home in the canonical-10 BL taxonomy
(they are not background jobs, not middleware chains, not third-party integrations) and do not
match the template's five named client patterns (debounce, optimistic-UI, polling, upload
progress, realtime) either. Documented here in full rather than mistyped or dropped. (Four more
F005 items that are request-scoped rather than purely client-side follow in their own section,
`## Request-Scoped Decision Logic — No Canonical-10 Match (F005)`, below.)

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

### Kudos filter + Highlight recompute (F004)

**Source**: `lib/kudos/derive.ts:96-104` (`matchesFilters`), `:84-88` (`pickHighlight`);
called from `app/kudos/_components/kudos-board.tsx:110-116` (`useMemo` on filter state) and
`highlight-carousel.tsx:42` (`useMemo` on the filtered array)
**Trigger**: Hashtag/Phòng ban selection in `KudosFilterBar`, or re-render after any filter change

Pure, no I/O — `KudosBoard` (`"use client"`, the screen's single client boundary) memoizes
`board.kudos.filter(card => matchesFilters(card, {hashtag, department}))` on every filter-id
change; `HighlightCarousel` re-derives its own `[...filtered].sort(hearts desc).slice(0,5)` from
that already-filtered array (`FR-202`, `FR-203`, `DEC-001`, `DEC-002`). AND-combined: a card must
match both the selected hashtag and the selected department when both are set. Re-selecting the
currently-active option toggles the corresponding id back to `null` (clear). Neither function
reaches the server — the full unfiltered dataset is fetched once per page load in
`KudosPage`/`getKudosBoard()`, and every filter interaction re-slices client state only. Selecting
any filter also resets carousel paging to slide 1 (`resetPaging()`, `kudos-board.tsx:68-71`).

### Kudos infinite-feed paging (F004)

**Source**: `app/kudos/_components/use-infinite-feed.ts:14-41`
**Trigger**: The `feed-sentinel` element entering the viewport (`IntersectionObserver`,
`rootMargin: "200px"`)

Client-side paging over data already fetched in one request (assumption A4,
`clarifications.md`) — there is no paginated re-fetch. `KudosBoard` tracks a `pages` counter
(`kudos-board.tsx:64`); `AllKudosSection` renders `cards.slice(0, pages * FEED_PAGE_SIZE)`
(`FEED_PAGE_SIZE = 10`, `lib/kudos/derive.ts:13`) and mounts the sentinel only while more rows
remain. The hook unmounts (and so stops observing) the sentinel once `hasMore` is false, which
both halts the effect and guards against firing past the end of the already-filtered list
(`FR-206`).

### Spotlight deterministic word-cloud layout (F004)

**Source**: `app/kudos/_components/spotlight-layout.ts:34-64` (`layoutSpotlightNodes`, ALG-002 in
`docs/features/F004_KudosLiveBoard/technical-spec.md` § 4.5), called from
`spotlight-board.tsx:50` inside `useMemo`
**Trigger**: Spotlight node id list changing (in practice: once per page load — the id list is
static per request)

A pure function of the sorted node-id array: a fixed-constant LCG (`SEED = 1988`, Numerical
Recipes multiplier, `spotlight-layout.ts:24-26`) seeded per-id — never `Math.random`, `Date.now`,
or `window` — places each name on a coarse grid sized to `sqrt(count * 1.6)` columns, then jitters
the cell and picks one of three size tiers (`lg`/`md`/`sm`) from further LCG draws. Same input,
byte-identical output on the server's first render and the browser's first client render, so
hydration never mismatches (`FR-205`). `SpotlightWordCloud` itself takes pre-computed positions as
a prop and holds no hooks of its own.

### Diacritic-insensitive recipient/mention matching (F005)

**Source**: `app/kudos/new/_components/use-body-editor-controller.ts:29-40` (`foldVietnameseText`),
reused by `app/kudos/new/_components/recipient-picker.tsx`
**Trigger**: Every keystroke in the recipient search input or after `@` in the body editor

`ALG-001` in `docs/features/F005_VietKudo/technical-spec.md § 4.5`. `value.normalize("NFD")`
decomposes most precomposed Vietnamese letters into base + combining mark, which a regex range
check (`U+0300`–`U+036F`) then strips — but `đ`/`Đ` is a distinct Vietnamese base letter, not a
base letter plus a combining mark, so NFD alone does not fold it; handled with an explicit
`replace(/đ/g, "d").replace(/Đ/g, "D")` before the final `toLowerCase()`. Both the recipient
autocomplete and the `@mention` menu filter an already-fetched `sunners` list client-side
(`ComposeOptionsView`, fetched once at page render — see `compose-options.ts`) with this same fold
applied to both the query and each candidate's `fullName`, never a per-keystroke server round trip.
One exported function, reused by both call sites rather than risking a second, divergent
implementation.

### Debounce / Throttle, Optimistic UI, Polling, Upload Progress, Realtime

N/A — no debounce/throttle, optimistic UI, polling, upload-progress, or realtime (WebSocket/SSE)
patterns detected anywhere in `app/` or `lib/`. (F004's heart toggle updates via a Server Action +
`refresh()`, not client-side optimistic state — see `api-map.md`'s `toggleKudosLike` entry.)

---

## Request-Scoped Decision Logic — No Canonical-10 Match (F005)

Four more genuine decision-logic items exist for Viết Kudo, and none of them is purely
client-side (they run server-side, inside a Server Action or a Postgres function), so they don't
belong under `## Client-Side Logic` above — but they also don't fit any of the canonical 10 BL
types (not middleware, not an outbound integration, not a background job). Documented in full
here rather than mistyped into a mismatched section.

### Rich-text document model and its safe renderer

**Source**: `lib/kudos/rich-text.ts` (`parseKudosDoc`, `serializeToDoc`), rendered by
`app/kudos/_components/kudos-message-body.tsx` (`renderBlocks`)
**Trigger**: Every board-card render where `kudos.message_format === "doc"` (server-rendered —
`kudos-card.tsx`/`kudos-message-body.tsx` carry no `"use client"` directive)

`kudos.message` holds either a plain string (`message_format = "plain"`, F004's 57 seeded rows and
every legacy row) or a minimal JSON document (`message_format = "doc"`, only rows written through
`/kudos/new`) — a list of blocks (`paragraph`/`ordered-list-item`/`quote`), each holding inline
runs with `bold`/`italic`/`strike`/`link href`/`mention sunnerId+label` flags, no deeper nesting.
`parseKudosDoc` is the untrusted-input boundary: `JSON.parse` failure, a non-object, a missing
`blocks` array, or any structurally-invalid block/run returns `null`, which `KudosMessageBody`
degrades to plain-text rendering rather than throwing. The renderer (`renderBlocks`/`renderRun`)
walks the parsed doc into React elements **only** — never `dangerouslySetInnerHTML`, never an HTML
string — because this content displays to every anonymous visitor on a public board and the repo
has no sanitizer dependency (no `dompurify`/`sanitize-html`/`marked`), so the XSS surface has to be
zero by construction. A `link` run's `href` is re-checked against `ACCEPTED_LINK_SCHEMES` at
**render** time too (`isAllowedLinkHref` in `kudos-message-body.tsx`) — a second, independent check
on top of `parseKudosDoc`'s own allow-list, so a hand-built doc object bypassing the parser still
cannot emit an unsafe `href`. A `mention` run prints its stored `label` verbatim — the sunner name
is never re-resolved at read time, so a later rename does not retroactively change past kudos.

### Server-side compose validation (defense-in-depth, all-errors-at-once)

**Source**: `lib/kudos/validate-compose.ts` (`validateCompose`), called from
`app/kudos/new/_actions/create-kudos.ts` before the `create_kudos` RPC
**Trigger**: Every `createKudos` invocation, regardless of what the client already checked

Never early-returns — collects every failing required field (recipient, title, body, hashtag
count) into one `ComposeFieldErrors` object so all required-field errors can render
simultaneously, matching the UI's "show every empty-field error at once" rule. Re-checked here
because Server Functions are POST-reachable directly, so the client's own validation (and its
never-actually-disabled `Gửi` button — see `docs/features/F005_VietKudo/technical-spec.md § 3.1`)
is a convenience, not the boundary. `create_kudos` itself re-validates the same rules a second time
inside its own transaction (blank campaign/message, hashtag count outside 1–5, more than 5 images)
— two independent layers, same discipline `permissions-matrix.md` PERM009 states for the RLS side.

### Sender auto-provisioning on first write

**Source**: `supabase/migrations/20260907025909_viet_kudo_write_path.sql:148-176` (inside
`create_kudos`)
**Trigger**: The first time an authenticated Sunner successfully calls `create_kudos` — `sunners`
is seeded with every `auth_user_id` NULL, so a freshly signed-in Google user has no sender identity
yet

Resolves `sunners.id` by `auth_user_id = auth.uid()`; when no row exists, provisions one before
proceeding: `full_name` from `user_metadata.full_name`/`name`, falling back to the email
local-part; `avatar_url` from `user_metadata.avatar_url`/`picture`, falling back to the committed
`/images/kudos/sample-avatar.png`; `department_id` always the seeded `Unassigned` department
(`filter_position NULL`, so it never enters F004's Phòng ban filter dropdown). The insert is an
`upsert` on the already-`unique` `auth_user_id` (`on conflict (auth_user_id) do nothing`), followed
by a re-select — so two concurrent first-time submits from the same Sunner cannot create two
`sunners` rows. This all runs inside `create_kudos`'s single transaction, before the `kudos` insert,
so the resolved `sender_id` is guaranteed to exist when the `kudos_insert_own` RLS policy checks it.

### Image magic-byte signature sniff

**Source**: `lib/kudos/validate-compose.ts` (`matchesImageSignature`, `IMAGE_SIGNATURES`), called
from `app/kudos/new/_actions/upload-kudos-image.ts` before the Storage `upload` call
**Trigger**: Every `uploadKudosImage` invocation, after the declared-MIME check passes

`file.type` is caller-declared and an attacker can label arbitrary bytes `image/jpeg`, so this is
a second, independent gate: the first `IMAGE_SIGNATURE_SNIFF_LENGTH` (12) bytes of the file are
read and compared against a magic-number allow-list — JPEG (`FF D8 FF`), PNG (8-byte PNG
signature), GIF (`GIF8`, covering both GIF87a/GIF89a), and WebP (`RIFF` at offset 0 **and**
`WEBP` at offset 8 — the only non-contiguous signature, because a 4-byte RIFF size field sits
between them that this check deliberately does not constrain). An unrecognized declared MIME
matches nothing — a whitelist, never a "no signature means trust it" fallback. Only after both the
declared-type check and this byte-sniff pass does the object get written to the public
`kudos-attachments` bucket.
