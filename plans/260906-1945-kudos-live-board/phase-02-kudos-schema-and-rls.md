# Phase 02 — Kudos schema & RLS

**Track:** B (behavior/backend) · **Owner:** `implementer` · **Depends:** 01 ·
**Effort:** 1.5h · **test_policy:** `e2e-red-first`

## Context Links

- [plan.md](plan.md) · [phase-01](phase-01-foundation-and-integration-contract.md) (contract, numeric ids)
- [clarifications.md](clarifications.md) § "Session 2026-09-06 (b)" + § "Schema decisions" — authoritative
- [technical-spec.md § 4.2 Data Model](spec/kudos-live-board/technical-spec.md), § 4.4 BR-001/BR-002/BR-003
- [permissions.md](spec/system/permissions.md) · [architecture.md](spec/system/architecture.md)
- [Supabase study](../reports/researcher-260906-1958-supabase-data-layer.md) § 1 (migrations), § 3 (**the exact RLS idiom**)
- `supabase/config.toml:58-63` (`[db.migrations]`), `:65-70` (`[db.seed]`), `:18` (`max_rows = 1000`)

## Overview

**Priority:** P1 · **Status:** delivered.

The first SQL this repository owns: nine tables, RLS on every one, read granted to `anon` and
`authenticated`, writes confined to `kudos_likes` for a signed-in viewer who is not the sender.
No seed rows here (phase 03), no TypeScript (phase 04).

## Key Insights

1. **Never hand-type the migration timestamp.** `npx supabase migration new kudos_live_board`
   creates `supabase/migrations/<timestamp>_kudos_live_board.sql`; write into that file. Applying
   DDL by `psql` directly desyncs migration history from `db reset` (study § 1).
2. **The RLS idiom is fixed, not a style choice.** Every policy names its roles
   (`to anon, authenticated`) and wraps the uid as `(select auth.uid())` so it evaluates once per
   query as an `InitPlan` rather than once per row (study § 3, verified against Supabase's own
   troubleshooting doc).
3. **`kudos_likes.user_id` references `auth.users(id)`, not `sunners(id)`.** The e2e authed user
   signs up fresh each run and has no `sunners` row; a FK to `sunners` would reject its insert and
   K-25 could never pass. It also has to be the raw `auth.uid()` for the RLS predicate to work.
4. **BR-003 is a policy predicate, not a CHECK constraint** — "sender cannot like own kudos" spans
   three tables, which `CHECK` cannot express. It goes in the `insert` policy's `with check`.
5. **Two seeded baselines carry the frame's numbers.** `kudos.heart_baseline` is already settled
   (clarifications § Schema decisions). Badge tier is *computed* from received count, but the
   frame shows `Huỳnh Dương Xuân` as `Legend Hero` (≥ 50 received) and a 50-row seed cannot give
   one sunner 50 real receipts — so `sunners.kudos_received_baseline` applies the identical
   approved idiom (seeded baseline + real rows) to the received count. This is additive to the
   draft ERD and is recorded here rather than invented in the seed.
6. **`departments` needs 51 rows but the filter menu needs exactly 50.** The frame's two named
   people sit in `CEVC10`, which is absent from the dropdown list; the list itself is 50 entries
   (the "(48 entries)" label in clarifications is a miscount of the same list — see phase 03
   § Key Insights). One nullable column serves both order and membership:
   `filter_position smallint unique`, `null` for `CEVC10`.
7. **Name both FKs to `sunners` explicitly.** PostgREST cannot disambiguate two foreign keys from
   `kudos` to the same table without a hint, so the constraints are named
   `kudos_sender_id_fkey` / `kudos_receiver_id_fkey` and phase 04 embeds against those names.
8. `auto_expose_new_tables` is unset in `config.toml`, so it defaults to `true` and new `public`
   tables are reachable by the Data API roles. Explicit `grant` statements are still written — a
   default is not a contract.

## Requirements

**Functional:** FR-001 (schema exists for all nine entities), FR-601 (anon reads everything),
FR-602 + BR-003 (writes refused at the DB layer when there is no session or the viewer is the
sender), BR-002 (`unique(kudos_id, user_id)`).

**Non-functional:** one migration file, idempotent within a `db reset`; no `public` function or
view; every table has RLS **enabled** (a table without RLS is readable *and writable* through the
anon key); no `service_role` dependency anywhere.

## Architecture

```
departments ──< sunners ──< kudos >── sunners            (sender_id, receiver_id)
                  │           ├──< kudos_hashtags >── hashtags
                  │           ├──< kudos_attachments
                  │           └──< kudos_likes >── auth.users
                  ├──< gift_awards
                  └──< spotlight_ticker_events >── kudos
```

**Tables and the columns the screen actually reads:**

| Table | Columns |
|---|---|
| `departments` | `id`, `name text not null unique`, `filter_position smallint unique` |
| `hashtags` | `id`, `name text not null unique`, `position smallint not null unique` |
| `sunners` | `id`, `auth_user_id uuid unique references auth.users(id) on delete set null`, `full_name text not null`, `department_id → departments`, `avatar_url text not null`, `kudos_received_baseline int not null default 0`, `secret_box_opened_count int not null default 0`, `secret_box_unopened_count int not null default 0` |
| `kudos` | `id`, `sender_id → sunners`, `receiver_id → sunners`, `campaign text`, `message text not null`, `sent_at timestamptz not null`, `heart_baseline int not null default 0 check (heart_baseline >= 0)` |
| `kudos_hashtags` | `kudos_id → kudos on delete cascade`, `hashtag_id → hashtags`, `position smallint not null`, `primary key (kudos_id, hashtag_id)` |
| `kudos_attachments` | `id`, `kudos_id → kudos on delete cascade`, `image_url text not null`, `position smallint not null` |
| `kudos_likes` | `id`, `kudos_id → kudos on delete cascade`, `user_id uuid not null references auth.users(id) on delete cascade`, `created_at timestamptz not null default now()`, `unique (kudos_id, user_id)` |
| `gift_awards` | `id`, `sunner_id → sunners`, `gift_label text not null`, `awarded_at timestamptz not null` |
| `spotlight_ticker_events` | `id`, `sunner_id → sunners`, `kudos_id → kudos on delete cascade`, `occurred_at timestamptz not null` |

`spotlight_ticker_events.kudos_id` exists because `test-contract.md` requires
`spotlight-node` to be `<a href="/kudos/<id>">` — a node with no kudos to point at cannot satisfy
the contract.

**Indexes:** `kudos(sent_at desc)`, `kudos(receiver_id)`, `kudos(sender_id)`,
`kudos_likes(kudos_id)`, `kudos_likes(user_id)`, `gift_awards(awarded_at desc)`,
`spotlight_ticker_events(occurred_at desc)`.

**Policies:**

```sql
-- read: all nine tables, identical shape
create policy "<t>_select_all" on public.<t> for select to anon, authenticated using (true);

-- write: kudos_likes only
create policy "kudos_likes_insert_own" on public.kudos_likes for insert to authenticated
with check (
  (select auth.uid()) = user_id
  and not exists (
    select 1 from public.kudos k
    join public.sunners s on s.id = k.sender_id
    where k.id = kudos_id and s.auth_user_id = (select auth.uid())
  )
);
create policy "kudos_likes_delete_own" on public.kudos_likes for delete to authenticated
using ((select auth.uid()) = user_id);
```

No `update` policy anywhere and no `insert`/`delete` on the other eight tables — RLS denies by
default, so silence is the deny.

## Related Code Files

**Create:** `supabase/migrations/<timestamp>_kudos_live_board.sql` (via the CLI — do not name it
by hand)
**Modify:** none
**Read only:** `supabase/config.toml`, `lib/kudos/view-model.ts` (field names must line up)
**Delete:** none

## Implementation Steps

1. `npx supabase migration new kudos_live_board`.
2. In the generated file, `create table` for the nine tables in FK order:
   `departments`, `hashtags`, `sunners`, `kudos`, `kudos_hashtags`, `kudos_attachments`,
   `kudos_likes`, `gift_awards`, `spotlight_ticker_events`. Name the two `kudos → sunners`
   constraints explicitly (Key Insight 7).
3. Add the seven indexes.
4. `alter table public.<t> enable row level security;` for all nine. Miss one and the anon key can
   write to it.
5. Write the nine `select` policies and the two `kudos_likes` write policies, exactly as § Architecture.
6. `grant select on all tables in schema public to anon, authenticated;` and
   `grant insert, delete on public.kudos_likes to authenticated;` — explicit, not inherited from
   `auto_expose_new_tables`.
7. Apply: `npx supabase db reset`. It runs migrations then `seed.sql` — which does not exist yet,
   so expect the seed step to be a no-op or a missing-file notice, not a failure of the DDL.
8. Prove the schema landed:
   `docker exec supabase_db_my-app psql -U postgres -d postgres -c "\dt public.*"` → nine tables.
9. Prove RLS is armed on every table:
   `docker exec supabase_db_my-app psql -U postgres -d postgres -c "select relname, relrowsecurity from pg_class where relnamespace = 'public'::regnamespace and relkind = 'r';"`
   → `relrowsecurity` true, nine times.
10. Prove anon cannot write:
    `docker exec supabase_db_my-app psql -U postgres -d postgres -c "set role anon; insert into public.kudos_likes (kudos_id, user_id) values (1, gen_random_uuid());"`
    → must fail with a row-level-security violation, not a FK error. If it fails on the FK first,
    re-run it after phase 03 seeds a real kudos row.
11. `npm run typecheck && npm run lint` (no TS changed, but the gate stays uniform).

## Todo List

- [ ] Migration file created by the CLI, never hand-named
- [ ] Nine tables, FK order, both `kudos → sunners` constraints explicitly named
- [ ] `filter_position` on `departments`, `position` on `hashtags` and `kudos_hashtags`
- [ ] `kudos.heart_baseline` and `sunners.kudos_received_baseline` present
- [ ] `kudos_likes.user_id` → `auth.users(id)`, `unique (kudos_id, user_id)`
- [ ] Seven indexes
- [ ] RLS enabled on all nine (verified in psql, not assumed)
- [ ] Nine select policies + two `kudos_likes` write policies, `to`-scoped, `(select auth.uid())`
- [ ] Explicit grants
- [ ] `npx supabase db reset` applies cleanly
- [ ] anon insert into `kudos_likes` refused by RLS

## Success Criteria

- `npx supabase db reset` exits 0 and nine tables exist in `public`.
- `relrowsecurity` is true for all nine tables.
- Under `set role anon`, `insert into public.kudos_likes` fails with an RLS violation.
- Under `set role authenticated` with no JWT, the same insert fails — `auth.uid()` is null, so
  `(select auth.uid()) = user_id` cannot hold.
- No kudos e2e assertion has changed state; this phase is invisible to the browser.

## Risk Assessment

| Risk | L×I | Countermeasure |
|---|---|---|
| One table left without RLS → the anon key can write it | Med × **High** | Step 9 queries `pg_class.relrowsecurity` for all nine and counts them; a missing row fails the phase |
| PostgREST serves a stale schema cache after the migration, so phase 04 gets 404s on `from("kudos")` | Med × Med | `db reset` notifies PostgREST to reload; if a 404 still appears, `docker exec supabase_db_my-app psql -U postgres -d postgres -c "notify pgrst, 'reload schema';"` and only then `npx supabase stop && npx supabase start` |
| `with check` subquery on `kudos`/`sunners` blocked by their own RLS | Low × High | Both carry `select` for `authenticated`, so the subquery reads them; step 10's authenticated variant proves it end to end |
| FK to `auth.users` breaks a future `db reset` ordering | Low × Med | `on delete cascade` for `kudos_likes`, `on delete set null` for `sunners.auth_user_id`; nothing seeded points at `auth.users` |
| Numeric ids overflow the JS number range | Low × Low | Identity sequences start at 1; the seed adds ~150 rows total |

**Rollback:** delete the migration file and run `npx supabase db reset`. The schema is local-only,
holds no production data, and nothing in `app/` imports it yet.

## Security Considerations

- RLS is the real boundary, not the UI. FR-602's disabled button is a courtesy; the `insert`
  policy is the enforcement, and step 10 proves it against a direct SQL call that bypasses the UI
  entirely (`technical-spec.md § 3.6`, the anon-bypass edge case).
- `to anon, authenticated` on reads is deliberate and matches the settled public-route decision;
  no table holds anything private — no emails, no auth data, no admin fields.
- No policy references `service_role`, and no code in this repo holds the service key.
- `sunners.auth_user_id` is the only link to `auth.*`; it is exposed to reads, so it must never be
  joined into a payload that reaches the client (phase 04 § Security).
- `max_rows = 1000` caps any PostgREST payload; the feed is 50 rows, far under it.

## Next Steps

Unblocks phase 03 (seed). Phase 04 needs both 02 and 03 applied before `npm run db:types` can
generate anything. Track A is unaffected and continues in parallel.
