# Implementer report — Phase 03: schema, RLS, storage, image host

**Status:** DONE

## Files touched
- `supabase/migrations/20260907025909_viet_kudo_write_path.sql` (new, ~230 lines) — via
  `npx supabase migration new viet_kudo_write_path` (real timestamp).
- `next.config.ts` (+13/-1) — `images.remotePatterns` derived from `NEXT_PUBLIC_SUPABASE_URL` via
  `new URL()` shorthand (`image.md:540`), falls back to `http://127.0.0.1:54321`.

No other file touched. `supabase/seed.sql`, `20260906140914_kudos_live_board.sql` read-only.

## What shipped
1. `kudos.is_anonymous boolean not null default false`, `anonymous_name text`,
   `message_format text not null default 'plain' check (in 'plain','doc')`.
2. `Unassigned` department, `filter_position = null`, idempotent insert.
3. Four INSERT policies (`kudos_insert_own`, `kudos_hashtags_insert_own`,
   `kudos_attachments_insert_own`, `sunners_insert_own`), predicates exactly as spec'd, all
   `to authenticated` + matching INSERT grants.
4. Bucket `kudos-attachments` (public read) + narrow-insert / open-read `storage.objects` policies.
5. `create_kudos(...)`, `security invoker`, `set search_path = public`: resolve/provision sender
   (upsert on `auth_user_id`, re-select) → validate (session, receiver, campaign/message non-blank,
   hashtags 1-5, images ≤5) → insert `kudos` → `kudos_hashtags` → `kudos_attachments` → return id.
   `execute` granted to `authenticated`.
6. Header states the no-UPDATE/no-DELETE decision.

## Verification (`npx supabase db reset`, exit 0, clean)

**Columns** (`\d kudos`): all three new columns present with correct defaults/check.

**Policy inventory** (`pg_policies`, public+storage) — 18 rows: F004's 12 untouched, plus exactly 4
new `public` INSERT policies and 2 new `storage.objects` policies. Zero new UPDATE/DELETE.
```
 kudos              | kudos_insert_own                | INSERT
 kudos_attachments   | kudos_attachments_insert_own     | INSERT
 kudos_hashtags      | kudos_hashtags_insert_own        | INSERT
 objects             | kudos_attachments_object_insert  | INSERT
 objects             | kudos_attachments_object_read    | SELECT
 sunners             | sunners_insert_own               | INSERT
```
`kudos_insert_own` with_check (verbatim): `EXISTS (SELECT 1 FROM sunners s WHERE s.id =
kudos.sender_id AND s.auth_user_id = (SELECT auth.uid()))`.

**Anon REST INSERT into `kudos`** (apikey only, exact spec curl): `HTTP 401`.
**Anon RPC `create_kudos`**: `HTTP 403`.
**Forged sender_id, real authed session** (fresh `/auth/v1/signup`, `sender_id:1` belonging to a
different sunner): `HTTP 403`, `{"code":"42501","message":"new row violates row-level security
policy for table \"kudos\""}`.
**Legit `create_kudos`, same session, no prior sunners row**: `HTTP 200`, id 60. Second call from
same session: `HTTP 200`, id 61; `select count(*) from sunners where auth_user_id=...` → **1** —
upsert + re-select stopped a double-submit from creating two rows; both kudos share `sender_id`.

**Seeded counts**: `select count(kudos), count(hashtags), count(departments where
filter_position is not null), count(departments)` → `k=57 | h=13 | d=50 | dall=52`. `k/h/d` match
spec exactly. `dall=52` not the phase doc's expected 51 — **discrepancy in the phase doc, not a
defect**: F004 already seeds a second non-filterable department (`CEVC10`), so pre-migration total
was already 51, not 50; this migration's `Unassigned` makes it 52. Filterable count (the load-
bearing assertion) is exactly 50.

**All 57 seeded rows**: `message_format='plain'`, `is_anonymous=false`, `anonymous_name=null` — 57/57/57.

**`storage.buckets`**: `kudos-attachments | kudos-attachments | public=true`.

Ran `db reset` once more after verification to discard my test writes and leave a clean state.

## Build/lint/typecheck
- `npm run typecheck`: clean, exit 0, repo-wide.
- `npm run lint`: 0 errors, 28 pre-existing warnings (unused vars in `e2e/*.spec.ts`, out of scope).
- `npm run build`: succeeded — all 14 routes incl. `/kudos/new` generated with the new
  `images.remotePatterns` in effect.

## F004 board suite
Could not run `npx playwright test e2e/kudos-live-board.spec.ts` directly — port 3000 was already
held by another `next dev` process (pid 1161790, started 10:03, likely a concurrent Track A/tester
agent on this plan), and `playwright.config.ts` sets `reuseExistingServer: false` by design.
Rather than kill a process I don't own, checked that same running server:
`curl http://127.0.0.1:3000/kudos` → `200`, page contains `data-testid="kudos-card"` and the
seeded campaign text `IDOL GIỚI TRẺ`. Combined with the DB-level counts above, confident the suite
passes but did not execute it myself. **Recommend re-running it once the port is free.**

## Unresolved
1. Phase doc's expected `57 | 13 | 50 | 51` is off by one department — pre-existing `CEVC10`
   already occupied a non-filterable slot before this migration; worth correcting in the doc.
2. Did not independently run `e2e/kudos-live-board.spec.ts` (port conflict, see above).
