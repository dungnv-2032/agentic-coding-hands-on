-- Kudos anonymity as a read-layer guarantee (F006, FR-001).
-- See plans/260908-0854-profile-ban-than/phase-03-reader-view-and-revoke.md
-- and reports/orchestrator-postgrest-masked-view-probe.md.
--
-- THE MEASURED PROBLEM. `kudos_select_all` is `for select to anon,
-- authenticated using (true)`, and the anon key ships to every browser by
-- design. With one seeded row flipped to `is_anonymous`, that key read the
-- sender straight off the base table over HTTP:
--
--   GET /rest/v1/kudos?select=id,is_anonymous,sender_id&id=eq.1
--   [{"id":1,"is_anonymous":true,"sender_id":1}]
--
-- Masking lived only in `lib/kudos/view-model.ts`, i.e. at the render layer, so
-- SEC_001 and SEC_002 were false statements about the system. This migration
-- makes them true: a masked reader view becomes the only way `anon` /
-- `authenticated` can read kudos, and direct `select` is revoked.
--
-- WHY THE NAIVE REVOKE CANNOT SHIP ALONE — two mechanisms, both measured
-- against this stack inside a rolled-back transaction as role `authenticated`
-- with a real JWT claim. `revoke select on public.kudos from authenticated`
-- on its own produced:
--
--   -- kudos_likes insert (policy references public.kudos)
--   ERROR:  permission denied for table kudos
--   -- create_kudos() (security invoker, INSERT ... RETURNING id)
--   ERROR:  permission denied for table kudos
--   CONTEXT: SQL statement "insert into public.kudos (...) returning id"
--
--   1. RLS policy expressions are evaluated with the CALLER's privileges.
--      Three INSERT policies join `public.kudos` inside their own WITH CHECK
--      (`kudos_likes_insert_own` from 20260906140914, `kudos_hashtags_insert_own`
--      and `kudos_attachments_insert_own` from 20260907025909). Revoke the
--      caller's `select` and the policy that depends on it disarms itself —
--      F004's heart toggle dies for every user. Fixed by moving that read
--      inside a `security definer` boundary: `public.is_kudos_sender(bigint)`.
--      A column grant alone does NOT fix this, because the policy reads
--      `k.sender_id` as well as `k.id`.
--   2. `INSERT ... RETURNING id` needs `select` on the returned column, and
--      `create_kudos()` is deliberately `security invoker` so RLS still
--      applies to it (20260907025909 § 6). Fixed by `grant select (id)`, a
--      COLUMN grant — the minimum RETURNING needs. `create_kudos()` itself is
--      not touched; making it `security definer` would bypass every INSERT
--      policy it deliberately honours.
--
-- INVARIANT, RECORDED SO IT IS NOT RE-OPENED LATER.
-- `public.spotlight_ticker_events.sunner_id` is ALWAYS the Kudos' RECEIVER
-- (measured 7/7 seeded rows; 0 senders). It needs no masking because a
-- receiver stays public even on an anonymous Kudos. Never write a SENDER into
-- that column: under a `using (true)` select policy the (sunner_id, kudos_id)
-- pairing would re-derive by join exactly the sender this migration hides.

-- ---------------------------------------------------------------------------
-- 1. is_kudos_sender() — the policy predicate, moved inside a definer boundary
-- ---------------------------------------------------------------------------
-- The `exists(...)` body is copied verbatim from `kudos_likes_insert_own`: the
-- predicate keeps its exact meaning, only *whose* privileges evaluate it
-- changes. It takes a bigint and returns a boolean — never a sender id — so it
-- cannot serve as a de-anonymization oracle.
create function public.is_kudos_sender(p_kudos_id bigint)
returns boolean
language sql
security definer
stable
set search_path = public
as $$
  select exists (
    select 1 from public.kudos k
    join public.sunners s on s.id = k.sender_id
    where k.id = p_kudos_id and s.auth_user_id = (select auth.uid())
  );
$$;

comment on function public.is_kudos_sender(bigint) is
  'True when the current caller is the sender of the given kudos. security definer so RLS policies can use it after select on public.kudos is revoked (F006 phase 03).';

grant execute on function public.is_kudos_sender(bigint) to authenticated;

-- ---------------------------------------------------------------------------
-- 2. The three INSERT policies, rewritten to call the helper
-- ---------------------------------------------------------------------------
-- Semantics unchanged: each previously inlined the same join. Dropped and
-- recreated rather than edited, because Postgres has no `alter policy ... with
-- check` that can be re-run idempotently under `supabase db reset`.
drop policy "kudos_likes_insert_own" on public.kudos_likes;
create policy "kudos_likes_insert_own" on public.kudos_likes for insert to authenticated
with check (
  (select auth.uid()) = user_id
  and not public.is_kudos_sender(kudos_id)
);

drop policy "kudos_hashtags_insert_own" on public.kudos_hashtags;
create policy "kudos_hashtags_insert_own" on public.kudos_hashtags for insert to authenticated
with check (public.is_kudos_sender(kudos_id));

drop policy "kudos_attachments_insert_own" on public.kudos_attachments;
create policy "kudos_attachments_insert_own" on public.kudos_attachments for insert to authenticated
with check (public.is_kudos_sender(kudos_id));

-- ---------------------------------------------------------------------------
-- 3. kudos_readable — the only read path for anon/authenticated
-- ---------------------------------------------------------------------------
-- DELIBERATELY NOT `security_invoker = true`. The owner-privileged default IS
-- the mechanism: the view runs as its owner, so the base table's revoked grant
-- does not block it, and the view's own CASE becomes the entire anonymity
-- boundary. Setting security_invoker here would make the view unreadable and
-- tempt someone to "fix" it by restoring the table grant.
--
-- The sender is joined HERE and exposed as five FLAT pre-masked columns. It is
-- never offered as an embeddable FK, because a CASE-masked column is not
-- traceable to its base column: the FK-hinted embed fails with PGRST200, and
-- dropping the hint returns HTTP 200 with the wrong human — PostgREST falls
-- back to the only traceable FK left and puts the RECEIVER in the sender slot
-- (probe report, case C). Flat columns mean there is no sender hint to drop.
--
-- `id` and `receiver_id` stay plain, traceable columns, so all four of
-- fetchKudos's embeds still resolve through this view: receiver (via
-- kudos_receiver_id_fkey), kudos_hashtags, kudos_attachments, kudos_likes.
--
-- The CASE reveals the sender TO THE SENDER, which is what preserves F004's
-- self-like refusal (`toggle-kudos-like.ts` "cannot like your own kudos") and
-- board-data.ts's `canLike` / `isOwnedByViewer`. The caller predicate must
-- therefore be evaluated per row BY THE DATABASE — never re-implemented in
-- application code, which has no privilege to check it.
create view public.kudos_readable as
select
  -- plain: nothing here identifies an anonymous sender
  k.id,
  k.receiver_id,
  k.campaign,
  k.message,
  k.sent_at,
  k.heart_baseline,
  k.message_format,
  k.is_anonymous,
  k.anonymous_name,
  -- masked together, per row, on caller identity
  case when mask.hide_sender then null else k.sender_id end as sender_id,
  case when mask.hide_sender then null else sender.full_name end as sender_full_name,
  case when mask.hide_sender then null else sender.avatar_url end as sender_avatar_url,
  case when mask.hide_sender then null else sender.kudos_received_baseline end
    as sender_kudos_received_baseline,
  case when mask.hide_sender then null else sender_department.name end
    as sender_department_name
from public.kudos k
-- inner joins are safe: kudos.sender_id and sunners.department_id are both
-- `not null` with FK constraints, so no row can be dropped by them.
join public.sunners sender on sender.id = k.sender_id
join public.departments sender_department on sender_department.id = sender.department_id
-- one shared predicate, evaluated once per row rather than five times
cross join lateral (
  select k.is_anonymous
     and k.sender_id is distinct from (
           select s.id from public.sunners s
           where s.auth_user_id = (select auth.uid())
         ) as hide_sender
) as mask;

comment on view public.kudos_readable is
  'Masked reader view over public.kudos: the five sender_* columns are NULL on an anonymous Kudos unless the caller is its sender. Owner-privileged on purpose (no security_invoker) — this CASE is the whole anonymity boundary. F006 phase 03.';

-- ---------------------------------------------------------------------------
-- 4. Grants — order matters
-- ---------------------------------------------------------------------------
-- The table-level revoke must come FIRST: run the other way round it would
-- drop the column grant with it.
--
-- `grant select (id)` exposes nothing. Row ids are already public through the
-- view, and a `where sender_id = ...` filter on the base table is still denied
-- (a WHERE clause needs `select` on the column it filters — measured denied
-- for both anon and authenticated). So there is no filter oracle.
--
-- `kudos_select_all` is left in place: unreachable without a grant, and keeping
-- it makes the rollback a single `grant`.
revoke select on public.kudos from anon, authenticated;
grant select (id) on public.kudos to authenticated;
grant select on public.kudos_readable to anon, authenticated;

-- ---------------------------------------------------------------------------
-- 5. PostgREST schema cache — without this the view is invisible over HTTP
-- until the container restarts, which reads as a 404 and looks like a code bug.
-- ---------------------------------------------------------------------------
notify pgrst, 'reload schema';

-- ---------------------------------------------------------------------------
-- ROLLBACK (Supabase migrations are forward-only; locally `supabase db reset`
-- reverts everything). For a deployed environment the down path is a NEW
-- migration containing exactly this, and the ORDER matters: restore the table
-- grant BEFORE dropping the view, or the board is dark between the two
-- statements. F006 phase 04's call sites must be reverted in the same deploy —
-- a reverted view with a repointed queries.ts is a broken board.
--
--   grant select on public.kudos to anon, authenticated;   -- restores kudos_select_all's reach
--   revoke select (id) on public.kudos from authenticated; -- table grant now covers it
--   drop view public.kudos_readable;
--   -- restore the three policies to their inline-join form, verbatim from
--   -- 20260906140914_kudos_live_board.sql (kudos_likes_insert_own) and
--   -- 20260907025909_viet_kudo_write_path.sql (kudos_hashtags/attachments), then:
--   drop function public.is_kudos_sender(bigint);
--   notify pgrst, 'reload schema';
-- ---------------------------------------------------------------------------
