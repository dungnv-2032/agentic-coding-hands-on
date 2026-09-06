# Research: first Postgres schema + typed data layer conventions

Trigger: kudos-live-board (`plans/260906-1945-kudos-live-board/clarifications.md`, session
2026-09-06 (b)) overrides the mock-data decision, needs a real `kudos_likes`-style table, RLS,
seed transcribed from the Figma frame, server reads via `lib/supabase/server.ts`. Confirmed
first SQL the repo owns (`docs/generated/entities.md`; `supabase/migrations/` absent; no `*.sql`
outside node_modules).

## 1. Migrations

- No `supabase/migrations/` dir. Create with `npx supabase migration new <name>` (verified
  locally, CLI v2.116.0) → writes `supabase/migrations/<timestamp>_<name>.sql`, timestamp
  auto-generated, never hand-typed.
- `supabase/config.toml:58-63` `[db.migrations] enabled = true`, `schema_paths = []` (empty →
  plain migration files, not declarative schema dirs).
- `supabase/config.toml:65-70` `[db.seed] enabled = true`, `sql_paths = ["./seed.sql"]`. File
  referenced but absent (confirmed by `docs/generated/entities.md`).
- Apply: `npx supabase db reset --local` — resets local DB to current migrations then runs seed
  (`--no-seed` skips). Right call here: local instance only, no prod/shared data at stake
  (`--linked` is the separate opt-in for remote). Wipes existing local `auth.users` too — fine,
  see §2. Do not hand-apply via `psql` — desyncs migration history from `db reset`/`db push`.

## 2. Seed

- `seed.sql` at `supabase/seed.sql` (relative to `supabase/`). Auto-runs on `db reset` and fresh
  `supabase start`.
- Risk with `e2e/auth.setup.ts`: low, ordering-dependent. `auth.setup.ts:60-134` →
  `createTestSession()` (`e2e/fixtures/supabase-session.ts:40+`) does a real `signUp` against
  local GoTrue per run, unique email each time. `db reset` truncates every schema incl. `auth`:
  - Safe: run `db reset` before `npm run test:e2e` (before Playwright's `setup` project).
  - Unsafe: run it mid-session — the live `auth.users` row vanishes, `getUser()` in
    `lib/supabase/server.ts` starts returning null, `proxy.ts:41-46` bounces an
    already-authenticated browser to `/login`. Not seed-specific, but seeding now gives a reason
    to reach for `db reset` mid-dev where it was previously a no-op.
  - New `seed.sql` must stay in `public.*` — never insert into `auth.users`/`auth.identities`
    directly (GoTrue-owned, unsupported path). Any "seeded viewer" fallback needs a real or
    nullable `user_id`, not a fabricated auth row.

## 3. RLS — exact idiom

Confirmed against Supabase's own troubleshooting doc (fetched verbatim) + 2 independent
secondary write-ups (leanware.co, makerkit.dev), all agreeing:

```sql
create policy "kudos_likes_select_all"
on public.kudos_likes for select
to anon, authenticated
using (true);

create policy "kudos_likes_insert_own"
on public.kudos_likes for insert
to authenticated
with check ((select auth.uid()) = user_id);

create policy "kudos_likes_delete_own"
on public.kudos_likes for delete
to authenticated
using ((select auth.uid()) = user_id);
```

Two rules from the official doc: (1) always name `to anon, authenticated` (or just
`authenticated` for writes) — an unscoped policy still runs its body against `anon`, wasting a
planner pass; (2) wrap `auth.uid()` as `(select auth.uid())` — forces an `InitPlan`, evaluated
once per query not once per row. `max_rows = 1000` (`config.toml:18`) caps PostgREST payloads —
relevant only if the feed ever queries directly via PostgREST instead of `server.ts`.

## 4. Typed queries

- No `supabase gen types` output anywhere; no `types/database.ts`. `docs/generated/entities.md`
  confirms zero ORM/query-builder usage — every existing call is `auth.*`.
- Command (verified locally): `npx supabase gen types typescript --local --schema public >
  types/database.ts`.
- **Recommendation: generate, don't hand-write.** Unlike `lib/award-system.ts`'s exhaustive
  `Record` over a closed 6-member compile-time enum, this is a live Postgres table — generated
  types track every future migration for free; hand-written ones drift silently. Fits DRY/YAGNI.
  Add a one-line `npm run db:types` script, commit the generated file (not gitignored, so build
  doesn't need a live DB). Keep hand-written domain types (`KudosLike`) in `lib/kudos/` as thin
  aliases over `Database["public"]["Tables"]["kudos_likes"]["Row"]` — mirrors the existing split
  (identity in `lib/awards.ts`, presentation layer in `lib/award-system.ts`).

## 5. Server reads (Next 16.3.4, read from node_modules)

- `next.config.ts` does not set `cacheComponents: true` → previous caching model applies
  (`node_modules/next/dist/docs/01-app/02-guides/caching-without-cache-components.md`), not the
  new Cache Components/`use cache` model.
- `cookies()` is already async in this repo — `lib/supabase/server.ts:11`, `app/_page-context.ts:28`
  — matching the official doc (`.../03-api-reference/04-functions/cookies.md:6-16,67-68`, async
  since v15.0.0-RC). No signature change needed.
- Same doc, line 69: using `cookies()` in a page/layout opts the route into dynamic rendering.
  `app/awards-information/page.tsx:56` → `getPageContext()` → `createClient()` → `cookies()`
  confirms `/awards-information` (and by the same pattern any new `/kudos` page) is dynamic,
  per-request, uncached — correct for per-viewer like state.
- Kudos likes read: reuse `lib/supabase/server.ts` verbatim inside the async Server Component,
  same shape as `getPageContext()` (`const supabase = await createClient(); const { data } =
  await supabase.from("kudos_likes")...`). Clarifications.md session (b) already specifies this.

## 6. Anon vs authed detection

- Single helper `getPageContext()` (`app/_page-context.ts:27-42`): one `supabase.auth.getUser()`
  call, derives `isAuthenticated`/`isAdmin` booleans only — raw `user` never crosses into Client
  Components (rule at `app/_page-context.ts:22-25`, echoed `docs/system/architecture.md:107`).
- Anon → `user: null` → `isAuthenticated: false`, anon-key client carries no JWT claim, so
  `to anon` RLS governs reads and `authenticated`-only policies reject writes at the DB layer —
  matches clarifications.md's stated design (line ~111-112).
- `proxy.ts:41-46` guards only `/todo`/`/login`; `/kudos` stays outside, per clarifications.md.

## Sources

- Official, read directly against this exact build: `node_modules/next/dist/docs/01-app/03-api-reference/04-functions/cookies.md`,
  `.../01-getting-started/08-caching.md`, `.../02-guides/caching-without-cache-components.md`.
- Official: supabase.com/docs/guides/troubleshooting/rls-performance-and-best-practices (fetched
  verbatim), supabase.com/docs/reference/cli/supabase-migration-new, `-db-reset`, `-gen-types`.
- Verified locally: `npx supabase migration new/db reset/gen types --help`, CLI v2.116.0 — no
  drift from docs.
- Secondary (RLS convention cross-check only): leanware.co/insights/supabase-best-practices,
  makerkit.dev/blog/tutorials/supabase-rls-best-practices.
- Repo ground truth: files named in the task, plus `docs/generated/entities.md` (rebuild-spec,
  authoritative "zero schema" baseline), `plans/260906-1945-kudos-live-board/clarifications.md`
  and `test-contract.md`, `playwright.config.ts`.

## Unresolved questions

- Exact table/column shape for `kudos_likes` (and any `kudos`/hashtag/department tables) — not
  specified anywhere read; derive from clarifications.md §"Frame dataset" + test-contract.md.
- Whether the seeded "mock viewer" sidebar fallback needs a nullable `user_id` on `kudos_likes`
  or a separate aggregate view — product/architecture call, not resolvable from what exists.
- No `types/database.ts` path convention exists yet — `types/` vs `lib/kudos/` vs
  `lib/supabase/` is an open naming choice for whoever implements.
