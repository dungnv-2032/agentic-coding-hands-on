-- Open Secret Box (F009) — write path: two tables, RLS, and the single
-- security-definer write path public.open_secret_box(). See
-- plans/260910-1708-open-secret-box/phase-03-data-layer-migration.md and
-- spec/open-secret-box/technical-spec.md § 3.2, § 4.
--
-- Additive only: no existing column is altered, nothing is dropped or
-- renamed.
--
-- Why this function runs as the definer (the first one in this repository): opening a box
-- must decrement public.sunners.secret_box_unopened_count, and that table
-- deliberately carries no UPDATE policy — granting one would let any
-- authenticated session rewrite its own box count directly through
-- PostgREST, which is exactly the attack test case 5cc072ad probes. The
-- function is the single writer instead, containing that privilege behind
-- three measures: (1) `set search_path = public` pinned so a caller cannot
-- shadow it with a schema earlier on their own search_path, (2) no
-- parameters at all — the actor comes only from auth.uid(), so "open
-- someone else's box" and "pick my own badge" are unrepresentable rather
-- than merely rejected, and (3) `execute` revoked from `public`/`anon` and
-- granted only to `authenticated` below. Postgres grants EXECUTE to PUBLIC
-- by default on `create function`; the revoke is not optional.
--
-- Deliberately no insert/update/delete policy anywhere in this migration —
-- silence stays the deny, exactly as `20260907025909_viet_kudo_write_path`
-- already relies on for nine of its tables.

-- ---------------------------------------------------------------------------
-- 1. secret_box_badge_odds — relative integer weights for the six
--    collectible_icon rule_items. Public read: the odds are printed in the
--    design, not a secret. Rows are seeded in supabase/seed.sql, not here —
--    see plan.md DEC-03: db reset runs migrations before seed, and
--    rule_items content itself lives in seed.sql, so a label-joined insert
--    here would match zero rows on a fresh database.
-- ---------------------------------------------------------------------------
create table public.secret_box_badge_odds (
  rule_item_id bigint primary key references public.rule_items (id) on delete cascade,
  weight smallint not null check (weight > 0)
);

-- ---------------------------------------------------------------------------
-- 2. secret_box_openings — one row per successful open, the audit trail
--    open_secret_box() writes to in the same transaction as the counter
--    decrement.
-- ---------------------------------------------------------------------------
create table public.secret_box_openings (
  id bigint generated always as identity primary key,
  sunner_id bigint not null references public.sunners (id),
  rule_item_id bigint not null references public.rule_items (id),
  opened_at timestamptz not null default now()
);
create index secret_box_openings_sunner_id_idx on public.secret_box_openings (sunner_id);

-- ---------------------------------------------------------------------------
-- Row Level Security — enabled on both tables. A public table without RLS
-- is readable (and writable) without limit through the anon key.
-- ---------------------------------------------------------------------------
alter table public.secret_box_badge_odds enable row level security;
alter table public.secret_box_openings enable row level security;

create policy "secret_box_badge_odds_select_all" on public.secret_box_badge_odds
  for select to anon, authenticated using (true);

-- Own rows only, bridging through sunners.auth_user_id — the same idiom as
-- kudos_likes_delete_own. `(select auth.uid())` wraps the call as an
-- InitPlan evaluated once per query rather than once per row.
create policy "secret_box_openings_select_own" on public.secret_box_openings
  for select to authenticated using (
    exists (
      select 1 from public.sunners s
      where s.id = sunner_id and s.auth_user_id = (select auth.uid())
    )
  );

-- No insert/update/delete policy on either table: open_secret_box() below
-- is the only writer.

grant select on public.secret_box_badge_odds, public.secret_box_openings
  to anon, authenticated;

-- ---------------------------------------------------------------------------
-- 3. open_secret_box() — the single write path. Steps fixed by
--    technical-spec § 3.2, all in one transaction (FR-602):
--      1. resolve auth.uid(), null -> 28000
--      2. resolve/provision the caller's sunners row (create_kudos() idiom,
--         copied verbatim: JWT name/avatar precedence, Unassigned dept)
--      3. guarded UPDATE — the `> 0` check lives INSIDE the UPDATE, not a
--         preceding SELECT, closing the two-tab race SB-07 probes; `not
--         found` -> P0002
--      4. weighted draw over secret_box_badge_odds join rule_items, no row
--         -> P0001 (an empty odds table would otherwise spend a box for
--         nothing — plan.md DEC-03)
--      5. insert the opening
--      6. return one row: badge + both new counters
-- ---------------------------------------------------------------------------
create function public.open_secret_box()
returns table (
  rule_item_id bigint,
  label text,
  image_path text,
  unopened_count int,
  opened_count int
)
language plpgsql
security definer
set search_path = public
as $$
declare
  v_uid uuid := auth.uid();
  v_sunner_id bigint;
  v_full_name text;
  v_avatar_url text;
  v_unassigned_department_id bigint;
  v_unopened int;
  v_opened int;
  v_rule_item_id bigint;
begin
  if v_uid is null then
    raise exception 'open_secret_box requires an authenticated session'
      using errcode = '28000'; -- invalid_authorization_specification
  end if;

  -- Resolve the caller's sunners row, provisioning it on first write. A
  -- freshly provisioned row starts at secret_box_unopened_count = 0, so
  -- provisioning grants nothing here — it only gives the counter something
  -- to be zero on.
  select id into v_sunner_id from public.sunners where auth_user_id = v_uid;

  if v_sunner_id is null then
    v_full_name := coalesce(
      nullif(auth.jwt() -> 'user_metadata' ->> 'full_name', ''),
      nullif(auth.jwt() -> 'user_metadata' ->> 'name', ''),
      split_part(auth.jwt() ->> 'email', '@', 1)
    );
    v_avatar_url := coalesce(
      nullif(auth.jwt() -> 'user_metadata' ->> 'avatar_url', ''),
      nullif(auth.jwt() -> 'user_metadata' ->> 'picture', ''),
      '/images/kudos/sample-avatar.png'
    );

    select id into v_unassigned_department_id
    from public.departments where name = 'Unassigned';

    insert into public.sunners (auth_user_id, full_name, department_id, avatar_url)
    values (v_uid, v_full_name, v_unassigned_department_id, v_avatar_url)
    on conflict (auth_user_id) do nothing;

    select id into v_sunner_id from public.sunners where auth_user_id = v_uid;
  end if;

  if v_sunner_id is null then
    raise exception 'failed to resolve or provision sunner'
      using errcode = 'P0001'; -- raise_exception (generic backstop, unreachable in practice)
  end if;

  -- The > 0 guard lives inside the UPDATE itself: a preceding SELECT check
  -- would leave a window two concurrent tabs could both walk through and
  -- double-spend the same box.
  update public.sunners
  set secret_box_unopened_count = secret_box_unopened_count - 1,
      secret_box_opened_count = secret_box_opened_count + 1
  where id = v_sunner_id and secret_box_unopened_count > 0
  returning secret_box_unopened_count, secret_box_opened_count
  into v_unopened, v_opened;

  if not found then
    raise exception 'no unopened secret boxes remain'
      using errcode = 'P0002'; -- no_data_found
  end if;

  -- Weighted draw (Efraimidis-Spirakis): order by random() ^ (1/weight)
  -- desc, take one. Correct for relative integer weights and, unlike
  -- -ln(random())/weight, safe when random() returns exactly 0.
  select o.rule_item_id
  into v_rule_item_id
  from public.secret_box_badge_odds o
  order by random() ^ (1.0 / o.weight) desc
  limit 1;

  if v_rule_item_id is null then
    raise exception 'secret_box_badge_odds is empty'
      using errcode = 'P0001'; -- raise_exception
  end if;

  insert into public.secret_box_openings (sunner_id, rule_item_id)
  values (v_sunner_id, v_rule_item_id);

  return query
    select ri.id, ri.label, ri.image_path, v_unopened, v_opened
    from public.rule_items ri
    where ri.id = v_rule_item_id;
end;
$$;

-- Postgres grants EXECUTE to PUBLIC by default on `create function`; revoke
-- it explicitly before granting to authenticated only, so an anonymous
-- PostgREST call cannot reach this security-definer function.
revoke execute on function public.open_secret_box() from public, anon;
grant execute on function public.open_secret_box() to authenticated;
