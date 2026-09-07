# Write-path conventions for "Viết Kudo" (`/kudos/new`)

Researched 2026-09-07. Report only, no code written.

## 1. Form submission — current API, confirmed from local docs

Read `node_modules/next/dist/docs/01-app/02-guides/forms.md` and
`.../01-getting-started/07-mutating-data.md` (Next 16.3.4 ships these as the
live docs for this exact version — not web/memory).

- `useActionState` (from `react`, not `next`) is the **current, non-deprecated**
  way to wire a form to a Server Action and get per-field errors + pending
  state back: `const [state, formAction, pending] = useActionState(action, initialState)`,
  `<form action={formAction}>`. `forms.md:190-274`.
- `<form action={serverFn}>` alone (no hook) still works and is progressively
  enhanced — Server Components support it "even if JavaScript hasn't loaded"
  (`mutating-data.md:132`). Client Components queue the submission until
  hydration (`mutating-data.md:170`). For this modal (interactive rich-text,
  live counters) a Client Component + `useActionState` is required regardless.
- `useFormStatus` (react-dom) is the alternate pending-state source, only
  useful when the submit button is a separate component nested in the form.
- **Refresh vs revalidate, both real APIs in this version**: `next/cache`
  exports `revalidatePath`, `revalidateTag`, `updateTag`, and `refresh`
  (confirmed via `node_modules/next/cache.d.ts`). `mutating-data.md:381-421`:
  `refresh()` "refreshes the client router" but "does not revalidate tagged
  data" — it's the lighter call. The repo's only precedent,
  `app/kudos/_actions/toggle-kudos-like.ts:115`, already uses `refresh()`
  after a write. Follow that precedent for the new action too — it's this
  repo's established idiom, and there's no `"use cache"`/tag involved in the
  kudos reads today (`lib/kudos/board-data.ts`/`queries.ts` are plain awaits,
  not cached fetches), so `refresh()` is sufficient and consistent. `revalidatePath`
  is used exactly once in the repo, in `app/_actions/locale.ts:24`, for a
  cross-cutting layout change — not the pattern for a single-screen write.
- `next.config.ts` is bare (`{ /* config options here */ }`) — **`cacheComponents`
  is NOT enabled**. Confirmed by reading the file directly; this rules out
  `"use cache"`/`cacheLife`/`cacheTag` concerns and the whole
  `authentication-with-cache-components.md` migration path for this work.

**Recommendation:** Client Component wrapping the dialog body, `useActionState`
bound to a new `app/kudos/_actions/create-kudos.ts` Server Action, return
`{ errors: Record<field, string> }`-shaped state on validation failure (mirrors
the doc's `createUser` example, `forms.md:147-161`), `refresh()` on success
(matches `toggleKudosLike`). Cost: one new client boundary; no new dependency.

## 2. Validation — no library, confirmed

`package.json` dependencies/devDependencies: only `@supabase/ssr`,
`@supabase/supabase-js`, `next`, `react`, `react-dom` (deps) and
`@playwright/test`, `tailwindcss`, `eslint`, `supabase` CLI, `typescript`
(devDeps). `zod`/`zod-validation-error` appear ONLY in `package-lock.json` as
a **transitive** dependency of something else (not imported anywhere in
`app/`/`lib/` — grepped, zero hits outside the lockfile). No `yup`/`valibot`.

Existing style: `lib/award-system.ts` (`AWARD_UNITS: Record<AwardKey, ...>`,
exhaustive by TS) and `lib/kudos/derive.ts` (pure zero-dependency predicates,
explicit doc-comment banning any runtime import because the module is
client-bundle-reachable). Both hand-rolled, no library, by house style.

**Recommendation, ranked:**
1. **Hand-written predicates in a new `lib/kudos/validate.ts`** (e.g.
   `validateRecipient`, `validateTitle`, `validateHashtags` capped at 5,
   `validateAttachments` capped at 5, `validateMessage` length) mirroring
   `derive.ts`'s zero-dependency, pure-function shape. Cost: ~40-80 lines,
   zero new dependency, matches two existing precedents exactly (YAGNI/DRY —
   the rule set here is 5 flat checks, not a nested schema). This is the
   only option consistent with the codebase's demonstrated preference.
2. Adding Zod: rejected. The repo has explicitly not adopted it despite it
   sitting one `npm install` away and being the doc's own recommended
   example (`forms.md:134`) — introducing it for one screen breaks the
   established "no validation lib" convention project-wide and is disproportionate
   to 5 flat rules.
- **Enforcement**: validate inside the Server Action itself, before any
  Supabase call — HTML `required`/`maxlength` are UX only. `forms.md:9-10` and
  `mutating-data.md:31-32` both warn Server Functions are POST-reachable
  directly, bypassing the UI.

## 3. RLS for INSERT into `kudos` — verified live against the running DB

Live query (`docker exec supabase_db_my-app psql ... pg_policies`) confirms
`supabase/migrations/20260906140914_kudos_live_board.sql` is exactly what's
deployed: **12 policies total, all SELECT except `kudos_likes_insert_own` and
`kudos_likes_delete_own`.** `kudos`, `kudos_hashtags`, `kudos_attachments` have
SELECT-only policies — RLS default-denies INSERT on all three today (migration
comment says as much: "No insert/delete on the other nine tables: RLS denies
by default, so silence is the deny").

Also missing: **grants**. The migration's grant block is `grant select on all
tables ... ; grant insert, delete on public.kudos_likes to authenticated;` —
`kudos`/`kudos_hashtags`/`kudos_attachments` have no INSERT grant either. RLS
policy alone is not enough; Postgres checks table-level GRANT first, then RLS.
Both need a new migration.

**Bridging `sender_id` (→ `sunners.id`) to `auth.uid()`**: `kudos.sender_id`
is not a `uuid`/`auth.users` FK — it's `bigint references sunners(id)`. The
`with check` must join through `sunners`, same idiom already shipped in
`kudos_likes_insert_own` (`...where s.auth_user_id = (select auth.uid())`):

```
with check (
  exists (
    select 1 from public.sunners s
    where s.id = sender_id and s.auth_user_id = (select auth.uid())
  )
)
```

This is what "stops someone forging a kudos as another sender" — the check
makes `sender_id` provably resolve to the caller's own linked `sunners` row;
a client-supplied `sender_id` for anyone else fails the `with check` and the
INSERT is rejected at the DB, not just hidden in the UI (same defense-in-depth
posture `docs/system/permissions.md` documents for `kudos_likes`: "Hai lớp
này phải cùng đúng, và nếu chỉ một lớp đúng thì lớp phải đúng là RLS").

**`kudos_hashtags` / `kudos_attachments` need their own INSERT policies too** —
RLS is per-table, not inherited through FK. Idiom: insert is allowed only when
the referenced `kudos_id` was just created by the caller, i.e. its `sender_id`
resolves to `auth.uid()` via the same sunners join:

```
with check (
  exists (
    select 1 from public.kudos k
    join public.sunners s on s.id = k.sender_id
    where k.id = kudos_id and s.auth_user_id = (select auth.uid())
  )
)
```

Same shape for both tables. No update/delete policies needed (Hủy just
discards client state; nothing partially written needs correcting — but see
open question on partial-insert failure below).

## 4. Sender identity — the consequential one

Verified live: `select count(*), count(auth_user_id) from sunners` → **9
rows, 0 linked.** `lib/kudos/viewer.ts:65-71` documents why: no mechanism
links a freshly-signed-up e2e/OAuth user to a seeded `sunners` row, and the
"first row wins" fallback (`resolveSidebarSunnerId`) is explicitly
DISPLAY-ONLY, "must never feed `canLike`" — i.e. it's already established
codebase policy that a session with no linked sunner is **not** a real
identity for a write.

**Options, ranked:**

1. **Auto-provision a `sunners` row on first authenticated write (recommended).**
   In the create-kudos action: if `resolveViewer()` returns `sunnerId: null`
   but `isAuthenticated: true`, insert a new `sunners` row keyed to
   `auth_user_id = user.id` (full_name/avatar from `user.user_metadata` or a
   placeholder, `department_id` — needs a default; `kudos_received_baseline`
   etc. default to 0) before inserting the kudos. Cost: one extra INSERT +
   its own RLS policy (`sunners` currently has SELECT-only too — a 4th policy
   needed, `with check (auth.uid() = auth_user_id)`); this is the ONLY option
   that makes the write self-sufficient for every future authenticated user,
   including the real Google OAuth population this app is actually built
   for, not just the e2e fixture. It also means "sender" for the compose
   screen is always the logged-in Sunner, never a picker — consistent with
   every other actor-derivation in the repo (`toggleKudosLike` never accepts
   an actor argument).
2. **Link e2e fixture user to one seeded sunner (`UPDATE sunners SET
   auth_user_id = ...`).** Cheap for tests, but doesn't solve production: real
   users signing in via Google OAuth still hit `sunnerId: null` on first visit
   and the compose screen breaks for everyone except the one seeded/patched
   row. This treats the symptom in test fixtures only — rejected as
   insufficient for a user-facing feature, though it may still be needed
   *in addition* to (1) if e2e wants a stable, pre-existing sender identity
   for assertions rather than exercising the provisioning path every run.
3. **Require picking "yourself" from the recipient-style search as the
   sender** (i.e. compose screen asks the user to self-identify). Rejected —
   defeats the RLS ownership check in §3 entirely (`sender_id` would be
   client-supplied and unverifiable), and contradicts BR-003/DEC-003's
   existing pattern of deriving identity from session only.

**Recommendation: (1), optionally combined with (2) for e2e determinism.**
Cost of (1): a new `sunners` INSERT policy, a "first write auto-provisions"
code path with its own edge cases (concurrent double-submit racing the
provision — needs `on conflict (auth_user_id) do nothing` + re-select, since
`auth_user_id` is already `unique`), and a product decision on default
`department_id`/`avatar_url` for a freshly provisioned Sunner (no design
input exists for this — flag as open question below).

## 5. Image upload

`supabase/config.toml:114-120`: `[storage] enabled = true`, but the bucket
block is commented out (`# [storage.buckets.images]` and everything under it).
**No bucket is declared.** Storage is running but unconfigured.

Real upload path (if pursued): declare a bucket in `config.toml`, add bucket
RLS (`storage.objects` policies scoped `bucket_id = 'kudos-attachments'` and
an owner-matching `with check`), upload from a Client Component via
`@supabase/ssr` browser client (`createClient` in `lib/supabase/client.ts`)
or inside the Server Action via `formData.get(file)` + `supabase.storage.from(...).upload(...)`,
then store the returned public/signed URL in `kudos_attachments.image_url`.
Cost: new migration, new bucket, new RLS surface, MIME/size validation,
client-side upload UI (progress, retry) — a meaningfully larger scope than
everything else in this commission combined.

**Cheaper alternative, and what F004 already does**: `kudos_attachments`
today stores URLs pointing at committed sample assets — clarifications.md A3:
"Attachment and avatar artwork is sample placeholder art in the design itself
(`MM_MEDIA_Sample Image`)... reuse a single committed sample per role rather
than exporting eight near-identical crops." A compose flow that lets the user
"attach" by picking from a small fixed set of committed sample images (or a
placeholder-only single default) keeps `kudos_attachments.image_url` a plain
string, needs zero storage/RLS work, and is *honest* about the design's own
placeholder status rather than pretending real upload when the design assets
themselves are stand-ins.

**Recommendation:** reuse sample assets (mirrors A3), not real upload — real
Storage upload is a disproportionate scope increase for a form whose own
source design ships placeholder imagery. This is the one place YAGNI cuts
hardest: building bucket RLS + client upload UI for a "first write form"
commission when the shipped board already treats these images as sample data
is speculative scope, not required scope. If the product genuinely wants real
upload later, it's an additive migration, not a rework.

## 6. Rich text

`kudos.message` is `text not null`, rendered server-side, line-clamped
(clarifications.md line 45: "message body (clamp 3 lines in HIGHLIGHT, 5 in
ALL KUDOS, then `...`)"). No sanitizer dependency exists — grepped
`dompurify`/`sanitize-html`/`marked`/`remark` in `package.json` and
`package-lock.json`: zero hits anywhere (not even transitive).

**Options, ranked by cost/risk:**

| Option | Storage | XSS exposure | Cost |
|---|---|---|---|
| Plain text, drop formatting | `text` (unchanged) | None — no markup rendered, ever | Lowest. Toolbar becomes decorative-only or is dropped; contradicts the commission's explicit toolbar requirement. |
| Markdown source, render via a markdown lib | `text` (markdown string) | Depends entirely on the renderer: an unsanitized HTML-emitting markdown renderer (most of them, incl. raw HTML passthrough) is exactly as exposed as raw HTML unless paired with a sanitizer | Needs a new dependency (`marked`/`remark`) — none present — plus a sanitizer for safety, since markdown renderers routinely allow raw HTML through by default. |
| Sanitized HTML | `text`/new column, sanitized at write OR read time | Real risk if sanitized only client-side (attacker skips the client and POSTs directly — `forms.md`'s own warning: Server Functions are POST-reachable directly) or only at write time with no re-sanitization at render. Must sanitize server-side, ideally at BOTH write and render (defense in depth) | Needs `dompurify`/`sanitize-html`, neither present; heaviest dependency + attack-surface option. |
| JSON document model (e.g. simple `{type, marks, children}` tree from the toolbar) | new `jsonb` column | Lowest real XSS exposure — rendering walks a typed tree and only ever emits known-safe elements (`<strong>`, `<em>`, `<a href>` with an allow-listed scheme, etc.); nothing is ever `dangerouslySetInnerHTML` | No dependency needed if hand-rolled to the toolbar's exact 6 operations (bold/italic/strike/list/link/quote) — but it's real design+implementation work: a serialization format, a renderer, and a client editor that produces it. |

**Recommendation:** hand-written JSON document model, minimal — the toolbar's
6 operations map to a closed set of node types, and a hand-rolled renderer
that never touches `dangerouslySetInnerHTML` has zero XSS surface by
construction, matching the repo's "no dependency unless truly needed" bar
(§2). This costs more implementation effort than plain text but is the only
option that satisfies the commission's toolbar requirement without adding a
markdown/sanitizer dependency AND without XSS risk. If effort must be cut,
fall back to **plain text, drop formatting** (cost: broken spec compliance,
zero risk) before ever reaching for unsanitized/sanitized HTML — HTML in
either form is the wrong tradeoff here given zero existing sanitizer
infrastructure and a public board that renders this to every visitor,
authenticated or not (`kudos_select_all` grants `anon` SELECT).

## 7. @mentions

Schema support: **none.** No junction table for kudos↔mentioned-sunner exists
in the migration. `sunners.full_name` is free text, not unique-indexed for
lookup-by-name (no index on `full_name`). Minimal honest scope: client-side
`@`-trigger opens a search-as-you-type over `sunners` (same data source and
UX pattern as the required recipient searchable select — likely the same
component, reused), and on submit the resolved mention becomes a literal
`@Full Name` token inside the message body (or a node in the JSON doc model
from §6) — no new table, no notification, no separate mention record. A
"real" mention system (clickable profile link, notification, a
`kudos_mentions` join table) is out of scope: nothing in the schema, spec, or
clarifications.md anticipates it, and inventing one is exactly the kind of
scope creep YAGNI exists to catch.

## 8. Route vs modal

`node_modules/next/dist/docs/01-app/03-api-reference/03-file-conventions/intercepting-routes.md`
describes `(.)`/`(..)`/`(...)` conventions paired with parallel routes
(`@modal` slot) specifically for modal-over-page-preserving-URL patterns.

But this repo's own shipped test contract already settles it: `e2e/kudos-live-board.spec.ts`
K-22 (`kudos-live-board.spec.ts:601-606`) asserts the compose control is a
plain `<a>` with `href="/kudos/new"` — a **hard navigation**, not a
client-side-intercepted soft nav. K-21 (`:574-598`) already asserts `/kudos/new`
is a real, directly-navigable route rendering `ComingSoon` today. Both tests
are pre-existing, ratified, frame-verbatim test contract — building an
intercepting route now would either contradict K-22 (if the link stays a
plain `<a>`, no interception fires anyway on same-origin plain navigation
without a `Link` + parallel-route wiring) or require rewriting an already-passing
test.

**Recommendation: render `/kudos/new` as a normal page**, with the dialog
chrome (backdrop, centered card) as page-level CSS/markup, `Hủy` navigating
back (`router.back()` or an `<a href="/kudos">`). This is simpler (no
`@modal` slot, no `default.js`, no dual render path for hard vs soft nav) and
is what the existing test contract already locks in. Intercepting routes are
NOT "genuinely low-cost here" — they're actively working against a shipped,
ratified assertion (K-22) that this is a plain link.

## 9. Testing a form

`playwright.config.ts` projects: `kudos-authed` runs only
`kudos-live-board-authed.spec.ts` with `storageState: e2e/.auth/user.json`
(from `e2e/auth.setup.ts`, which calls `createTestSession()` in
`e2e/fixtures/supabase-session.ts` — signs up a unique `e2e-<ts>-<pid>-<rand>@example.com`
user via `supabase.auth.signUp`, captures cookies, writes Playwright
storageState). `anon` project explicitly excludes `kudos-live-board-authed`
via negative lookahead in its `testMatch` regex.

A screen-level RED-first test for `/kudos/new` (per `e2e-red-first` policy —
this form has real state transitions: validation, submit, navigate away) is
authenticated, behavioral, and writes data — the closest existing shape is
`kudos-live-board-authed.spec.ts`, not the `anon` board tests. **Recommendation:
add a new spec file matched into the existing `kudos-authed` project**
(`testMatch: /kudos-live-board-authed\.spec\.ts/` would need widening to also
match a new `kudos-compose*.spec.ts`, or the new file is named to match the
existing pattern) rather than standing up a new Playwright project — one auth
setup, one storageState, reused. Given §4's provisioning requirement, the RED
test's fixture user will hit the "no linked sunners row" path on first visit,
which is exactly the path the provisioning code in §4 needs to prove works —
useful coincidence, not something to route around.

**Hard constraint, repeated from the task brief and worth restating**:
`npx supabase db reset` truncates `auth.users` and must never run mid-suite —
the e2e fixture creates a fresh signUp user per run for exactly this reason
(collision-proofing comment at `supabase-session.ts:70-77`); a compose-form
test that inserts real `kudos`/`sunners` rows needs to either accept
accumulating test data across runs or explicitly clean up its own inserted
rows in an `afterEach`/teardown — resetting the whole DB is not an option
mid-suite.

---

## Ranked overall recommendation

1. Page (not intercepting route) at `/kudos/new`, Client Component +
   `useActionState`, new Server Action `create-kudos.ts` following
   `toggleKudosLike`'s shape (session-derived identity, `refresh()` on
   success, errors-as-return-value not throw).
2. Hand-written predicates in `lib/kudos/validate.ts`, no new dependency.
3. New migration: INSERT policy + grant for `kudos`, `kudos_hashtags`,
   `kudos_attachments`, `sunners` (all bridging through the
   `sunners.auth_user_id = auth.uid()` join, same idiom as `kudos_likes`).
4. Auto-provision `sunners` on first authenticated write (§4 option 1) — the
   single highest-risk, highest-effort item; needs a product answer on
   default `department_id`/`avatar_url` before it can be built (see below).
5. Reuse sample-asset images for attachments, skip real Storage upload.
6. Hand-rolled JSON document model for rich text, zero sanitizer dependency,
   zero `dangerouslySetInnerHTML`.
7. `@mention` as client-side search-and-insert over `sunners`, no new schema.
8. New e2e spec added to the `kudos-authed` Playwright project.

## Unresolved questions

- **§4**: what `department_id`/`avatar_url`/`full_name` does a freshly
  auto-provisioned `sunners` row get for a real Google OAuth user? Schema
  requires `department_id not null` and `avatar_url not null` — Google
  profile has name/picture but no Sun* department. No design or clarification
  answers this; needs a product decision (a default "Unassigned" department
  row? block compose until a profile-completion step exists?) before
  implementation.
- **§3/§4**: concurrent double-submit racing the sunners auto-provision —
  needs `on conflict (auth_user_id) do nothing` handling, not covered by any
  existing migration precedent.
- **§6**: no MoMorph field inventory was pulled in this pass (report-only,
  no MCP calls made) — the exact toolbar node types (does "quote" nest lists?
  can links wrap bold text?) need a look at the actual screen spec
  (`ihQ26W78P2`) before the JSON model's shape is finalized.
- **§9**: whether the RED-first test tears down its own inserted `kudos` row,
  or the board's growing row count is accepted as acceptable e2e noise, is a
  call for whoever writes the phase plan — not resolved here.
- **§5**: if the product later wants real upload, no research was done here
  on Supabase Storage bucket RLS specifics (owner-scoped policies, signed URL
  TTLs) — deferred as out of scope given the recommendation to skip it.

**Status:** DONE
**Summary:** All 9 questions answered with file:line/live-DB citations; Next 16.3.4 form APIs confirmed from local docs (`useActionState`, `refresh()` from `next/cache`, no `cacheComponents`); RLS gap for `kudos`/`kudos_hashtags`/`kudos_attachments`/`sunners` INSERT confirmed live via psql; sender-identity provisioning flagged as the highest-risk open item.
**Concerns/Blockers:** §4 (sunners auto-provisioning defaults) is a real product gap, not just a research gap — implementation should not proceed on that path without a decision on default department/avatar for a freshly provisioned Sunner.
