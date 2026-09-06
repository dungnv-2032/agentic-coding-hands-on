# Phase 02 — Kudos schema & RLS — implementer report

**Status:** completed

## File

`supabase/migrations/20260906140914_kudos_live_board.sql` (created via `npx supabase migration
new kudos_live_board`, never hand-named).

## Tables (10, not 9)

Nine per plan (`departments`, `hashtags`, `sunners`, `kudos`, `kudos_hashtags`,
`kudos_attachments`, `kudos_likes`, `gift_awards`, `spotlight_ticker_events`), plus a 10th,
**`board_stats`**: single row (`id smallint pk default 1 check (id=1)`,
`spotlight_kudos_total integer not null default 0`). This was mandated by the task instructions
(test-contract.md "Blueprint ratification" > "Overridden" — the frame's `388 KUDOS` is a seeded DB
value read by the query layer, not i18n copy). It is *additive* to phase-02.md's table list, same
idiom already established for `kudos.heart_baseline` / `sunners.kudos_received_baseline`. No row
inserted here — seeding is phase 03's job; this migration only provides the column. Flagged as a
deviation below.

Both `kudos → sunners` FKs named explicitly (`kudos_sender_id_fkey`, `kudos_receiver_id_fkey`) via
inline `constraint` clauses in `create table` (simpler than the plan's implied
create-then-alter). `departments.filter_position` and `hashtags.position`/`kudos_hashtags.position`
present. `kudos_likes.user_id → auth.users(id)`, `unique(kudos_id, user_id)`. Seven indexes as
specified.

## Verification (real DB, not assumed)

`npx supabase db reset` → exit 0. `WARN: no files matched pattern: supabase/seed.sql` is the
expected no-op (phase 03 not yet landed).

**Tables:** `\dt public.*` → 10 rows (all expected names present).

**RLS enabled, all 10:**
```
relname                 | relrowsecurity
board_stats              | t
departments              | t
gift_awards               | t
hashtags                 | t
kudos                    | t
kudos_attachments         | t
kudos_hashtags            | t
kudos_likes               | t
spotlight_ticker_events   | t
sunners                   | t
```

**Policies (`pg_policies`):** 12 rows — one `select` per table (`to {anon,authenticated}`,
`qual=true`), plus on `kudos_likes`: `kudos_likes_insert_own` (`INSERT`, `to authenticated`,
`with_check = ((select auth.uid()) = user_id) AND NOT EXISTS(... s.auth_user_id = (select
auth.uid()))`) and `kudos_likes_delete_own` (`DELETE`, `to authenticated`, `using = (select
auth.uid()) = user_id`). No `update` policy anywhere. Confirmed via
`select tablename, policyname, roles, cmd, qual, with_check from pg_policies where
schemaname='public'`.

**Anon boundary — REST API, anon key, `http://127.0.0.1:54321/rest/v1/`:**
- `GET /kudos_likes?select=*` → **HTTP 200**, `[]`
- `POST /kudos_likes` `{"kudos_id":1,"user_id":"00000000-...-000000000000"}` → **HTTP 401**,
  `{"code":"42501", "message":"new row violates row-level security policy for table
  \"kudos_likes\""}`

**psql, `set role`:**
- `set role anon; insert into kudos_likes ...` → `ERROR: new row violates row-level security
  policy for table "kudos_likes"` (not an FK error — RLS is the first gate hit).
- `set role authenticated; insert into kudos_likes ...` (no JWT, `auth.uid()` null) → same RLS
  error.

## Checks

- `npx supabase db reset`: exit 0.
- `npm run lint`: 0 errors, 27 pre-existing warnings in `e2e/*.spec.ts` (unused fixtures from
  phases not yet wired) — none introduced by this change, no SQL files touched by lint.
- `npm run typecheck` intentionally **not** run per task instruction (8 known pre-existing errors
  in `e2e/kudos-live-board-authed.spec.ts` owned by tester, unrelated to this phase; no TS files
  were touched here).

## Acceptance criteria (phase-02.md § Success Criteria)

- [x] `db reset` exits 0, nine (+1) tables exist.
- [x] `relrowsecurity` true for all tables.
- [x] Anon insert into `kudos_likes` fails RLS (proved via both REST 401 and psql `set role anon`).
- [x] Authenticated role with no JWT: same insert fails (`auth.uid()` null).
- [x] No browser/e2e state touched — only `supabase/migrations/**` created.

## Deviation from plan.md literal table count

Plan's own table lists ("nine tables", "Todo List", "Success Criteria") predate the later
test-contract.md ratification that requires the spotlight `388` total to be a seeded DB value. The
task's delegation message explicitly named this as binding ("Provide for it in the schema... a
single-row board-stats value or an equivalent seeded column"), so `board_stats` was added as the
minimal-diff way to satisfy it without touching an existing table's shape. Flagging for
orchestrator awareness — not silently reconciled.

## Unresolved questions

1. `board_stats.spotlight_kudos_total` seeding is out of this phase's scope (phase 03 owns
   `seed.sql`) — confirm phase 03's implementer knows to populate the single row with `388`.
2. `sunners.department_id` was made `not null` (plan didn't state nullability explicitly); every
   frame sunner has a department, so this reads as the correct tightening, not a gap.
