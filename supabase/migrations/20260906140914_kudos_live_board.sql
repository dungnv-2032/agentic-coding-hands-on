-- Kudos Live Board (F004) — schema + RLS.
-- First SQL this repository owns. See plans/260906-1945-kudos-live-board/
-- phase-02-kudos-schema-and-rls.md for the full rationale.
--
-- Nine domain tables (FK order) plus `board_stats`, a single-row table that
-- carries the Spotlight board's seeded `388 KUDOS` total — a frame-verbatim
-- number, not a live count(*), per test-contract.md § "Blueprint ratification
-- (orchestrator, 2026-09-06c)" > "Overridden". Seeding happens in phase 03;
-- this migration only provides the column.

-- ---------------------------------------------------------------------------
-- departments
-- ---------------------------------------------------------------------------
create table public.departments (
  id bigint generated always as identity primary key,
  name text not null unique,
  -- Order + membership in the 50-entry filter dropdown. Null for departments
  -- (e.g. CEVC10) that exist on seeded people but are absent from the menu.
  filter_position smallint unique
);

-- ---------------------------------------------------------------------------
-- hashtags
-- ---------------------------------------------------------------------------
create table public.hashtags (
  id bigint generated always as identity primary key,
  name text not null unique,
  position smallint not null unique
);

-- ---------------------------------------------------------------------------
-- sunners
-- ---------------------------------------------------------------------------
create table public.sunners (
  id bigint generated always as identity primary key,
  auth_user_id uuid unique references auth.users (id) on delete set null,
  full_name text not null,
  department_id bigint not null references public.departments (id),
  avatar_url text not null,
  -- Additive to the draft ERD (Key Insight 5): the frame shows a Legend Hero
  -- (>= 50 received) that a 50-row seed cannot earn through real receipts
  -- alone. Displayed received count is baseline + count(real kudos rows).
  kudos_received_baseline int not null default 0,
  secret_box_opened_count int not null default 0,
  secret_box_unopened_count int not null default 0
);

-- ---------------------------------------------------------------------------
-- kudos
-- ---------------------------------------------------------------------------
-- PostgREST cannot disambiguate two FKs from kudos to sunners without a
-- named-constraint hint; both are named explicitly (Key Insight 7).
create table public.kudos (
  id bigint generated always as identity primary key,
  sender_id bigint not null constraint kudos_sender_id_fkey references public.sunners (id),
  receiver_id bigint not null constraint kudos_receiver_id_fkey references public.sunners (id),
  campaign text,
  message text not null,
  sent_at timestamptz not null,
  -- Same idiom as sunners.kudos_received_baseline: the frame's "1.000" hearts
  -- is a seeded baseline; displayed count is baseline + count(kudos_likes).
  heart_baseline int not null default 0 check (heart_baseline >= 0)
);

-- ---------------------------------------------------------------------------
-- kudos_hashtags
-- ---------------------------------------------------------------------------
create table public.kudos_hashtags (
  kudos_id bigint not null references public.kudos (id) on delete cascade,
  hashtag_id bigint not null references public.hashtags (id),
  position smallint not null,
  primary key (kudos_id, hashtag_id)
);

-- ---------------------------------------------------------------------------
-- kudos_attachments
-- ---------------------------------------------------------------------------
create table public.kudos_attachments (
  id bigint generated always as identity primary key,
  kudos_id bigint not null references public.kudos (id) on delete cascade,
  image_url text not null,
  position smallint not null
);

-- ---------------------------------------------------------------------------
-- kudos_likes
-- ---------------------------------------------------------------------------
-- user_id references auth.users(id), never sunners(id): the e2e authed user
-- signs up fresh each run and has no sunners row, and the RLS predicate needs
-- the raw auth.uid() (Key Insight 3 / test-contract.md ratification #4).
create table public.kudos_likes (
  id bigint generated always as identity primary key,
  kudos_id bigint not null references public.kudos (id) on delete cascade,
  user_id uuid not null references auth.users (id) on delete cascade,
  created_at timestamptz not null default now(),
  unique (kudos_id, user_id)
);

-- ---------------------------------------------------------------------------
-- gift_awards
-- ---------------------------------------------------------------------------
create table public.gift_awards (
  id bigint generated always as identity primary key,
  sunner_id bigint not null references public.sunners (id),
  gift_label text not null,
  awarded_at timestamptz not null
);

-- ---------------------------------------------------------------------------
-- spotlight_ticker_events
-- ---------------------------------------------------------------------------
-- kudos_id exists because test-contract.md requires spotlight-node to render
-- <a href="/kudos/<id>"> — a node with no kudos to point at cannot satisfy it.
create table public.spotlight_ticker_events (
  id bigint generated always as identity primary key,
  sunner_id bigint not null references public.sunners (id),
  kudos_id bigint not null references public.kudos (id) on delete cascade,
  occurred_at timestamptz not null
);

-- ---------------------------------------------------------------------------
-- board_stats — single-row seeded totals for the Spotlight board.
-- ---------------------------------------------------------------------------
-- The frame's "388 KUDOS" canvas heading is data transcribed from the design,
-- not i18n copy and not a live count(*) (count(*) from kudos is 50). It ships
-- as a seeded value in the database, read by the query layer — the same
-- idiom as kudos.heart_baseline / sunners.kudos_received_baseline.
create table public.board_stats (
  id smallint primary key default 1 check (id = 1),
  spotlight_kudos_total integer not null default 0
);

-- ---------------------------------------------------------------------------
-- Indexes
-- ---------------------------------------------------------------------------
create index kudos_sent_at_idx on public.kudos (sent_at desc);
create index kudos_receiver_id_idx on public.kudos (receiver_id);
create index kudos_sender_id_idx on public.kudos (sender_id);
create index kudos_likes_kudos_id_idx on public.kudos_likes (kudos_id);
create index kudos_likes_user_id_idx on public.kudos_likes (user_id);
create index gift_awards_awarded_at_idx on public.gift_awards (awarded_at desc);
create index spotlight_ticker_events_occurred_at_idx on public.spotlight_ticker_events (occurred_at desc);

-- ---------------------------------------------------------------------------
-- Row Level Security — enabled on every table in this migration. A public
-- table without RLS is readable (and writable) without limit through the
-- anon key; that is a misconfiguration, not an acceptable default.
-- ---------------------------------------------------------------------------
alter table public.departments enable row level security;
alter table public.hashtags enable row level security;
alter table public.sunners enable row level security;
alter table public.kudos enable row level security;
alter table public.kudos_hashtags enable row level security;
alter table public.kudos_attachments enable row level security;
alter table public.kudos_likes enable row level security;
alter table public.gift_awards enable row level security;
alter table public.spotlight_ticker_events enable row level security;
alter table public.board_stats enable row level security;

-- Read: every table, identical shape. This is public thank-you data.
create policy "departments_select_all" on public.departments for select to anon, authenticated using (true);
create policy "hashtags_select_all" on public.hashtags for select to anon, authenticated using (true);
create policy "sunners_select_all" on public.sunners for select to anon, authenticated using (true);
create policy "kudos_select_all" on public.kudos for select to anon, authenticated using (true);
create policy "kudos_hashtags_select_all" on public.kudos_hashtags for select to anon, authenticated using (true);
create policy "kudos_attachments_select_all" on public.kudos_attachments for select to anon, authenticated using (true);
create policy "kudos_likes_select_all" on public.kudos_likes for select to anon, authenticated using (true);
create policy "gift_awards_select_all" on public.gift_awards for select to anon, authenticated using (true);
create policy "spotlight_ticker_events_select_all" on public.spotlight_ticker_events for select to anon, authenticated using (true);
create policy "board_stats_select_all" on public.board_stats for select to anon, authenticated using (true);

-- Write: kudos_likes only. `(select auth.uid())` wraps the call as an
-- InitPlan evaluated once per query rather than once per row.
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

-- No update policy anywhere: unliking is a delete, not a flag flip. No
-- insert/delete on the other nine tables: RLS denies by default, so silence
-- is the deny.

-- ---------------------------------------------------------------------------
-- Grants — explicit, not inherited from auto_expose_new_tables (unset in
-- config.toml, defaulting to true; a default is not a contract).
-- ---------------------------------------------------------------------------
grant select on all tables in schema public to anon, authenticated;
grant insert, delete on public.kudos_likes to authenticated;
