# Existing conventions for a Supabase-backed read-only content screen

Sources read: migrations `20260906140914_kudos_live_board.sql`, `20260908100000_profile_reader_view.sql`,
`supabase/config.toml`, `supabase/seed.sql` (skim), `lib/supabase/{server,client}.ts`,
`lib/kudos/{board-data,queries}.ts`, `lib/profile/{profile-data,profile-queries}.ts`,
`app/_page-context.ts`, `lib/i18n/*`, `package.json`, `next.config.ts`,
`docs/system/{architecture,permissions}.md`.

## 1. Migration conventions

- **Filename**: `<YYYYMMDDHHMMSS>_<snake_case_slug>.sql`. Three files exist so far, all timestamp-first (matches Supabase CLI default). Slug names the feature (`kudos_live_board`, `viet_kudo_write_path`, `profile_reader_view`), not the table.
- **Header comment block**: every migration opens with a comment stating (a) the feature code (F004/F006) it belongs to, (b) a pointer to the plan phase file that has the rationale, (c) for non-trivial ones, the MEASURED problem/evidence (e.g. curl output, error text) that justified the design — not just an assertion.
- **Section dividers**: `-- ---...---` (79 dashes) + `-- tablename` header before each `create table`, and again before Indexes / RLS / Grants blocks.
- **Table/column naming**: snake_case plural table names (`departments`, `hashtags`, `sunners`, `kudos_likes`), singular FK columns (`department_id`, `sender_id`). `bigint generated always as identity primary key` is the PK idiom everywhere (no `uuid`, no `serial`). Baseline/seed-offset columns follow `<metric>_baseline` naming (`kudos_received_baseline`, `heart_baseline`) — a seeded starting number the query layer adds live counts to, never a live `count(*)` alone.
- **RLS shape for PUBLIC READ tables** (the pattern to copy for Thể lệ):
  ```sql
  alter table public.<table> enable row level security;
  create policy "<table>_select_all" on public.<table> for select to anon, authenticated using (true);
  ```
  Policy name convention: `<table>_select_all`. No `update`/`delete` policy anywhere for content tables — RLS denies by default, and the migration comments this explicitly ("silence is the deny") rather than writing a redundant deny policy.
- **`anon` is granted** — yes, explicitly, both in the policy `to anon, authenticated` and in the grant:
  ```sql
  grant select on all tables in schema public to anon, authenticated;
  ```
  Grants are explicit and never left to `auto_expose_new_tables` (commented out / unset in `config.toml:auto_expose_new_tables`, defaults true — "a default is not a contract").
- **If content must ever be masked per-caller**, the repo's precedent (`20260908100000`) is: revoke table `select`, expose a `security definer`-free **view** (`kudos_readable`) with `for select to anon, authenticated`, and `notify pgrst, 'reload schema';` after any grant/view change so PostgREST's schema cache picks it up immediately (otherwise a 404 that looks like a code bug). A pure read-only "Thể lệ" screen almost certainly does NOT need this — plain table + `_select_all` policy is the right-sized pattern (YAGNI: don't build a masked view for content with no per-user variance).
- **Enum-like values**: no native Postgres `enum` type used; `text` columns constrained inline where needed (e.g. would be `check (...)` — see `board_stats.id smallint primary key default 1 check (id = 1)` for a singleton-row pattern, directly reusable if Thể lệ is a single static content blob rather than a list).

## 2. Seed conventions

- `supabase/seed.sql` is one flat file (333 lines), path fixed in `config.toml` (`[db.seed] sql_paths = ["./seed.sql"]`), run automatically after migrations on `supabase db reset` (`[db.seed] enabled = true`).
- **Organized by table**, one `insert into public.<table> (...)` values-block per section, same `-- ---` divider + header comment style as migrations. Order follows FK dependency order (departments → hashtags → sunners → kudos → join tables → gift_awards → spotlight_ticker_events → board_stats).
- **Idempotency**: NOT idempotent via `ON CONFLICT` — relies on `supabase db reset` truncating everything first ("plain inserts are re-runnable — no ON CONFLICT needed", stated verbatim in the file header). Do not add `ON CONFLICT` machinery; follow the existing "reset truncates, plain insert" idiom.
- **Design-sourced content rows**: every string literal is transcribed **verbatim** from the plan's `clarifications.md` ("Resolved from source data" section) or from an e2e fixtures file, never invented — explicit MoMorph rule cited in-file: "Use Figma design content as mock data source. Do NOT invent data." Thể lệ copy must be sourced the same way (from the design/clarifications, byte-for-byte).
- **Ordering columns**: explicit `smallint` `position` (or `filter_position`) columns drive display order — never rely on insertion order or `id`. `hashtags.position`, `departments.filter_position` (nullable — null means "not in the filter menu"), `kudos_hashtags.position`, `kudos_attachments.position`. If Thể lệ has an ordered list of rule sections, add a `position smallint not null unique` column.

## 3. Data-layer conventions

- **File split**: `lib/<feature>/queries.ts` (or `<feature>-queries.ts` for profile) holds ONLY typed Supabase reads — no view-model shaping. `lib/<feature>/board-data.ts` / `profile-data.ts` is the orchestrator that calls the queries, runs independent reads via `Promise.all`, and maps rows → frozen view-model types (`view-model.ts` / `profile-view-model.ts`, not shown but referenced). Keep this split for Thể lệ: `lib/rules/queries.ts` + `lib/rules/rules-data.ts` (or similar) rather than one file.
- **Query function signature**: `async function fetchX(supabase: SupabaseClient<Database>, ...args): Promise<XRow[]|XRow>` — client is always a parameter, never created inside the query file (`board-data.ts`/`profile-data.ts` create the one-per-request client via `createClient()` from `lib/supabase/server.ts` and thread it through).
- **Error handling**: uniform pattern, no try/catch — check `{ data, error }` and `if (error) throw new Error(`fetchX failed: ${error.message}`);` then return `data`. No custom error classes.
- **Row typing**: reuse generated `Database["public"]["Tables"][T]["Row"]` via a local `Row<T>` alias for plain tables; for embedded/nested selects (`.select("a:b(...)")`) declare an explicit interface and pin with `.returns<T[]>()` because postgrest-js's select-string type inference isn't exhaustive for FK-hinted embeds. Views (outside `Row<T>`'s reach) are typed the same explicit-interface way.
- **Server component fetch shape**: page/orchestrator creates ONE Supabase client per request (`await createClient()`), resolves viewer identity, then fires all independent reads through a single `Promise.all([...])` (see `board-data.ts:47`, `app/_page-context.ts:28`, `profile-data.ts:157`). Sequential awaits are used only when a later read genuinely depends on an earlier result (e.g. `sidebarSunnerId` needed before `fetchSidebarBoxCounts`).
- **View-model / mapping split**: raw DB rows never reach a component. `queries.ts` returns typed rows → `<feature>-data.ts` maps rows into a **frozen, page-shaped view-model interface** (`KudosBoardViewModel`, `ProfileViewModel`) that the page/component consumes directly. Shared mapping logic (e.g. `toKudosCardView`) lives in its own module and is reused across features rather than duplicated (`map-kudos-card.ts` reused by both kudos board and profile feed) — DRY precedent to follow if Thể lệ content maps into a shape shared elsewhere (unlikely, but don't duplicate a mapper if one already fits).
- No caching layer (`unstable_cache`/`revalidate`) used anywhere in these files — reads are plain per-request Supabase calls; Next.js dynamic rendering is already forced by `cookies()` usage.

## 4. i18n conventions

- `Dictionary` (in `lib/i18n/messages/dictionary.ts`) is one big interface, one top-level key per screen/feature (`login`, `header`, `home`, `awardSystem`, `kudos`, `profile`, `kudosCompose`, `comingSoon`...). Fields are plain `string` (not `as const` literals) so `en.ts` can hold different copy while a missing key still fails `tsc`.
- **Adding a new screen namespace** (e.g. `rules` for Thể lệ):
  1. Add a new top-level key + nested shape to the `Dictionary` interface in `dictionary.ts`, with a doc-comment block citing the feature code / screen id, same style as `kudos`/`profile` blocks.
  2. Create `lib/i18n/messages/vi-<feature>.ts` exporting `export const vi<Feature>: Dictionary["<feature>"] = {...}` — copy transcribed verbatim from clarifications/design (comment says so explicitly, e.g. viKudos file header).
  3. Create `lib/i18n/messages/en-<feature>.ts` mirroring the same shape (not read in this task but structurally implied — `vi.ts` imports `viHome`, `viAwardSystem`, `viKudos`, `viKudosCompose`, `viProfile`; `en.ts` presumably mirrors with `enX`).
  4. Wire the new module into `lib/i18n/messages/vi.ts` (and `en.ts`) as `<feature>: vi<Feature>,` inside the `vi`/`en` const — do NOT inline large namespaces directly in `vi.ts`, which stays thin and only composes.
  5. `vi` is called out as "the authoritative source shape for the Dictionary type" — write vi first, en second, matching key-for-key (compile error on drift is the safety net, no runtime fallback).
- **How a page reads it**: `getPageContext()` in `app/_page-context.ts` is the single shared read for locale+session — resolves `Locale` from the `NEXT_LOCALE` cookie via `resolveLocale()`, then `getDictionary(locale)`, returned inside a `PageContext` object (`{ locale, dictionary, isAuthenticated, isAdmin }`). A page calls `await getPageContext()` once and threads `dictionary.rules` (etc.) down to components — never imports `vi`/`en` directly in a page.

## 5. `database.types.ts` regeneration

- Regenerated via `npm run db:types` → `supabase gen types typescript --local --schema public > lib/supabase/database.types.ts` (package.json). Requires local Supabase stack running (`--local` flag reads the local Postgres schema).
- **It IS committed**: `git ls-files lib/supabase/database.types.ts` returns the file — not gitignored. Any new table/view (e.g. a `rules` table) requires running `npm run db:types` after the migration and committing the regenerated file; do not hand-edit it.

## 6. Repo-specific rules in docs/

- **No `docs/code-standards.md` exists in this repo** (checked — absent from `docs/`; only referenced as an aspirational path in `.claude/rules/documentation-management.md`, never created). Nothing to quote from it.
- `docs/system/permissions.md` (status: implemented, lang: vi) is the load-bearing doc for this work:
  - States plainly (verbatim, translated): "Kudos Live Board thêm một tầng thật: RLS trên `public.*`... đây là tiền lệ mọi bảng sau sẽ đi theo" (RLS-on-every-table is binding precedent for any new table).
  - Tracks a `PERM###` code registry (`docs/generated/permissions-matrix.md`) — a new public-read table/policy for Thể lệ would need a new `PERM0##` entry, following the existing pattern of "planned" codes noted as "(dự kiến)" until assigned.
  - Confirms current system type is `hybrid` (thin app-level role check + real DB-level RLS ownership) — a read-only Thể lệ table adds no new ownership logic, stays firmly on the "public read, anon+authenticated" side already established by `kudos_select_all` et al.
- `docs/system/architecture.md` (status: implemented, lang: vi) narrates the same RLS/Storage/write-path history — no additional binding rule beyond what's captured above; useful only as context, nothing new to enforce.
- `docs/features/` holds one folder per feature code (`F001_Login` … `F006_ProfileBanThan`) — a new Thể lệ feature will presumably need its own `F0##_TheLe` folder for consistency with `docs/_canonical-fcodes.json` / `docs/_source-to-fcode.json`, but assigning the fcode is outside this research's scope.

## Unresolved / left uncovered

- Did not read `en.ts` / `en-*.ts` message files (not in the requested file list) — the i18n mirroring convention above (step 3) is inferred from `vi.ts`'s import structure and the `Dictionary` type's dual-locale contract stated in `dictionary.ts`'s own comment, not directly confirmed. Verify shape before writing `en-rules.ts`.
- Did not read `lib/kudos/view-model.ts`, `lib/profile/profile-view-model.ts`, or `map-kudos-card.ts` (out of scope per task) — cited only from comments in files that reference them.
- `docs/generated/permissions-matrix.md` (the PERM### source of truth) was not opened — only referenced from `permissions.md`. Whoever assigns a PERM code for the new table should read it directly.
- No prior "static content" (non-transactional, no likes/hearts/counts) table exists yet in this repo — `board_stats` (singleton, `id smallint check (id=1)`) is the closest precedent for a single-row content blob; if Thể lệ is instead a list of rule sections, the closer precedent is `hashtags`/`departments` (id + name + ordering column). Which shape fits depends on the actual Thể lệ content structure, not determined by this research.
