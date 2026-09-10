-- Thể lệ rules panel (F007) — schema + RLS for the panel's editorial content.
-- See plans/260909-0838-the-le-rules-panel/phase-03-migration-seed-types.md
-- for the full rationale.
--
-- This is the first screen in the repository whose EDITORIAL COPY lives in the
-- database. `/awards-information` hardcodes its copy in `lib/`; the F007
-- commission explicitly asks for the Supabase local project instead
-- (clarifications.md § "Content source — the Supabase requirement"), so the
-- three prose sections, the four Hero tiers and the six collectible icons are
-- rows, read per request through `lib/rules/`.
--
-- Two tables, not three. `rule_items.kind` is a discriminator: the Hero tiers
-- and the collectible icons differ only in WHICH COLUMNS they populate, not in
-- shape (technical-spec § 4.2 "Polymorphic Behavior"). A table per Figma
-- heading would be layout leaking into the schema.
--
-- Images stay on disk under `public/images/rules/` (FR-205); a row holds only
-- the public path. No binary in the database, no Storage bucket, and this
-- migration opens no upload surface.

-- ---------------------------------------------------------------------------
-- rule_sections — the three ordered prose sections.
-- ---------------------------------------------------------------------------
-- `closing_body` is a column, not a fourth section: the line "Những Sunner thu
-- thập trọn bộ 6 icon…" renders AFTER section 2's icon grid, so it belongs to
-- section 2. Nullable because only section 2 has one.
create table public.rule_sections (
  id bigint generated always as identity primary key,
  -- Explicit render order (BR-001). Never id, never insertion order.
  position smallint not null unique,
  heading text not null,
  body text not null,
  closing_body text
);

-- ---------------------------------------------------------------------------
-- rule_items — the four Hero tiers and the six collectible icons.
-- ---------------------------------------------------------------------------
-- `description` is nullable at the row level because collectible icons carry
-- no description in the frame; a `hero_tier` row always fills it, and the
-- view-model resolves that branch once in `lib/rules/rules-data.ts`.
create table public.rule_items (
  id bigint generated always as identity primary key,
  kind text not null check (kind in ('hero_tier', 'collectible_icon')),
  position smallint not null,
  label text not null,
  description text,
  image_path text not null,
  -- (kind, position), not position alone: the two kinds run two independent
  -- sequences (hero tiers 1..4, collectible icons 1..6).
  unique (kind, position)
);

-- ---------------------------------------------------------------------------
-- Row Level Security — enabled on both tables. A public table without RLS is
-- readable and writable without limit through the anon key; that is a
-- misconfiguration, not an acceptable default.
-- ---------------------------------------------------------------------------
alter table public.rule_sections enable row level security;
alter table public.rule_items enable row level security;

-- Read: the rules copy is public content, same shape as kudos_select_all.
create policy "rule_sections_select_all" on public.rule_sections for select to anon, authenticated using (true);
create policy "rule_items_select_all" on public.rule_items for select to anon, authenticated using (true);

-- No insert/update/delete policy on either table: RLS denies by default, so
-- silence is the deny. Writing an explicit deny policy would be noise, not
-- extra safety. These two tables are read-only to every client role; content
-- changes travel through a migration or a seed, never through the API.

-- ---------------------------------------------------------------------------
-- Grants — explicit. The F004 migration's `grant select on all tables in
-- schema public` applied to the tables that existed THEN; it does not reach
-- forward to these two. auto_expose_new_tables is unset in config.toml and
-- defaults to true, but a default is not a contract.
-- ---------------------------------------------------------------------------
grant select on public.rule_sections to anon, authenticated;
grant select on public.rule_items to anon, authenticated;

-- Without this, PostgREST serves a stale schema cache and every request to the
-- new tables returns 404 — a failure that looks exactly like a code bug.
notify pgrst, 'reload schema';
