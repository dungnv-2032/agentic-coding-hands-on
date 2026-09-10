---
phase: 03
title: "Data layer — tables, odds, open_secret_box(), db:types"
status: complete
owner: implementer
track: B
test_policy: e2e-red-first
effort: 1.5h
depends_on: [01]
---

# Phase 03 — Data layer (migration, odds seed, generated types)

## Context Links

- [technical-spec](spec/open-secret-box/technical-spec.md) § 3.2, § 4, § 5 — the function's step
  order and the two new tables
- [permissions](spec/system/permissions.md) — PERM016/017/018 and why `security definer` is the
  right trade here
- [clarifications.md](clarifications.md) — relative weights, server-side draw, provisioning
- [plan.md](plan.md) DEC-03 — odds rows go to `supabase/seed.sql`, not the migration
- Idiom to copy verbatim: `supabase/migrations/20260907025909_viet_kudo_write_path.sql:120-232`
  (`create_kudos()` — the JWT provisioning block)
- Seeded badges: `supabase/seed.sql:392-397` (`REVIVAL`, `TOUCH OF LIGHT`, `STAY GOLD`,
  `FLOW TO HORIZON`, `BEYOND THE BOUNDARY`, `ROOT FURTHER`)

## Overview

- **Priority:** P1 — every Track B line depends on the generated types.
- **Status:** pending
- One additive migration: two tables with RLS, the `open_secret_box()` function, its grants, and the
  odds rows appended to `seed.sql`. Ends with `npm run db:types`, without which the typed client
  cannot see the new tables at all.

## Key Insights

- **`security definer` is the whole point.** Decrementing a box means `UPDATE public.sunners`, and
  that table has no UPDATE policy by design (`20260906140914` grants select only,
  `20260907025909` adds insert only). Adding one would let any session rewrite its own box count
  through PostgREST — the exact attack SB-08 probes. The function becomes the single writer.
- **Postgres grants `EXECUTE` to `PUBLIC` by default on `create function`.** Without an explicit
  `revoke ... from public, anon`, an anonymous PostgREST call reaches the definer function. SB-A3
  exists to catch precisely that omission.
- **The `> 0` guard belongs inside the UPDATE**, never in a preceding SELECT. Two statements are a
  race window two tabs will walk through; SB-07 fires two concurrent RPCs to prove it is closed.
- **The odds cannot be seeded from the migration.** `rule_items` *content* lives in `seed.sql`, and
  `db reset` runs migrations before seeds, so a label-joined insert inside the migration matches
  zero rows on a fresh database and would ship a silently empty odds table (plan DEC-03). The rows
  go into `seed.sql` directly after the `rule_items` insert; the function raises when the table is
  empty so a missed seed fails loudly instead of decrementing a counter for nothing.
- **Weighted draw without a window function:** `order by random() ^ (1.0 / o.weight) desc limit 1`
  (Efraimidis–Spirakis). Correct for relative integer weights and — unlike `-ln(random())/weight` —
  safe when `random()` returns exactly `0`.
- `npm run db:types` overwrites `lib/supabase/database.types.ts` wholesale. Run it once, at the end,
  after the migration is applied; never hand-edit that file.

## Requirements

Functional:
- `secret_box_badge_odds (rule_item_id bigint pk → rule_items on delete cascade, weight smallint not null check (weight > 0))`.
- `secret_box_openings (id identity pk, sunner_id → sunners, rule_item_id → rule_items, opened_at timestamptz default now())`
  plus `secret_box_openings_sunner_id_idx`.
- RLS on both. `secret_box_badge_odds`: select to `anon, authenticated` (PERM016). `secret_box_openings`:
  select own rows only, via `sunners.auth_user_id = (select auth.uid())` (PERM017). **No** insert /
  update / delete policy anywhere (PERM018) — silence is denial, as `20260907025909` already relies on.
- `public.open_secret_box()` — no parameters, `language plpgsql`, `security definer`,
  `set search_path = public`, `returns table (rule_item_id bigint, label text, image_path text, unopened_count int, opened_count int)`.
  Step order fixed by the technical spec: resolve `auth.uid()` (null → `28000`) → resolve/provision
  the `sunners` row (JWT name/avatar, `Unassigned` department, `on conflict (auth_user_id) do nothing`,
  re-select) → guarded UPDATE (`not found` → `P0002`) → weighted draw (no row → `P0001`) → insert the
  opening → return one row.
- `revoke execute on function public.open_secret_box() from public, anon;`
  `grant execute on function public.open_secret_box() to authenticated;`
- `seed.sql`: six odds rows by label — STAY GOLD 30, FLOW TO HORIZON 25, TOUCH OF LIGHT 20,
  BEYOND THE BOUNDARY 10, REVIVAL 10, ROOT FURTHER 5 — `insert ... select` joined on
  `rule_items.label`, `on conflict do nothing`, so re-running is safe.
- `lib/supabase/database.types.ts` regenerated and containing both tables and the function.

Non-functional: the migration is additive only (no `drop`, no `alter` of an existing column); it is
re-runnable on a fresh database; all five function steps sit in one call, therefore one transaction
(FR-602).

## Architecture

```
click ─> Server Action (phase 05) ─> rpc('open_secret_box')  [authenticated role]
                                        │  SECURITY DEFINER, search_path=public
                                        ├─ 1. v_uid := auth.uid()            null -> 28000
                                        ├─ 2. resolve|provision sunners row  (create_kudos idiom)
                                        ├─ 3. UPDATE sunners
                                        │      SET unopened-1, opened+1
                                        │      WHERE id = v_sunner_id AND unopened > 0
                                        │      RETURNING counts             not found -> P0002
                                        ├─ 4. SELECT badge FROM secret_box_badge_odds o
                                        │      JOIN rule_items ri ON ri.id = o.rule_item_id
                                        │      ORDER BY random() ^ (1.0 / o.weight) DESC LIMIT 1
                                        │                                    no row -> P0001
                                        ├─ 5. INSERT secret_box_openings
                                        └─ 6. RETURN (badge + both counts)
```

Everything after step 1 rolls back together on any raise: no state where a box is spent without a
badge, or a badge exists without a spend.

## Related Code Files

Create: `supabase/migrations/20260910170000_secret_box_open_path.sql`.

Modify: `supabase/seed.sql` (six odds rows appended after the `rule_items` insert, with a comment
naming this migration); `lib/supabase/database.types.ts` (regenerated, never hand-edited).

Read for context: `supabase/migrations/20260907025909_viet_kudo_write_path.sql`,
`supabase/migrations/20260906140914_kudos_live_board.sql` (the `sunners` table and its policies),
`supabase/seed.sql:360-397`.

Delete: none. Not modified: `rule_items`, `sunners`, `gift_awards`, every existing policy.

## Implementation Steps

1. Write the migration: header comment (why definer, what the single write path is), the two tables,
   RLS enable, the two select policies, the grants (`select` on both tables to `anon, authenticated`),
   the function, then the revoke/grant pair.
2. Copy the provisioning block from `create_kudos()` verbatim; do not re-derive the JWT key
   precedence (`full_name` → `name` → email local part; `avatar_url` → `picture` → sample avatar).
3. Append the odds rows to `seed.sql` under a comment pointing back at this migration.
4. `npx supabase db reset` (applies migrations, then seed). Note in the phase report that this wipes
   local data; if the developer must keep it, `npx supabase migration up` plus running the odds
   insert by hand is the equivalent.
5. Verify by hand with `psql`:
   - `select count(*) from secret_box_badge_odds;` → `6`, `sum(weight)` → `100`.
   - anon role: `select set_role('anon'); select open_secret_box();` → permission denied.
   - authenticated user with 0 boxes → `P0002`.
   - 2000 draws in a loop → each of the six appears, and STAY GOLD leads ROOT FURTHER by roughly 6:1.
     A distribution check, not an exact assertion.
6. `npm run db:types`, then `npm run typecheck`.

## Todo List

- [x] Migration file created, additive only
- [x] Both tables + index + RLS + the two select policies
- [x] `open_secret_box()` with the six steps in the specified order and the three errcodes
- [x] `revoke execute ... from public, anon` present **before** the grant to `authenticated`
- [x] Odds rows appended to `seed.sql`, idempotent, joined by label
- [x] `npx supabase db reset` succeeds; the six odds rows exist afterwards
- [x] psql checks in step 5 all behave as stated
- [x] `npm run db:types` run; `database.types.ts` contains both tables and the function
- [x] `npm run typecheck` exits 0
- [x] **DEVIATION RECORDED:** DEC-03 already noted in plan.md — odds rows live in `seed.sql`, not migration, because `db reset` runs migrations before seed

## Success Criteria

- `grep -c "security definer" supabase/migrations/20260910170000_*.sql` → 1, and the same file
  contains `set search_path = public`.
- A direct anon RPC is refused; an authenticated RPC with 0 boxes raises `P0002` and leaves both
  counters unchanged (`select` before and after).
- After one successful call: `unopened` −1, `opened` +1, exactly one new `secret_box_openings` row.
- `secret_box_badge_odds` and `secret_box_openings` appear in `lib/supabase/database.types.ts`.
- No existing migration file is modified.

## Risk Assessment

| Risk | L×I | Countermeasure |
|------|-----|----------------|
| Default `EXECUTE to PUBLIC` left in place → anonymous callers reach a definer function | M×**H** | Explicit revoke in the migration; SB-A3 asserts it; step 5's `set role anon` check |
| `search_path` not pinned → schema-shadowing privilege escalation | L×**H** | `set search_path = public` in the function definition, checked by the grep in Success Criteria |
| Odds table empty on a fresh database (the DEC-03 trap) | **H**×M | Rows in `seed.sql` where the joined rows exist; the function raises `P0001` rather than silently spending a box |
| Guard split into SELECT-then-UPDATE → double spend under two tabs | M×**H** | `and secret_box_unopened_count > 0` inside the UPDATE; SB-07 fires concurrent RPCs |
| `db:types` forgotten → phase 05 writes against stale types and "fixes" it by casting | M×M | It is a todo item and a success criterion; phase 05 depends on this phase, not the reverse |
| `supabase db reset` wipes a developer's local data unexpectedly | M×M | Called out in step 4 with the non-destructive alternative |
| Weight semantics drift to percentages that must total 100 | L×M | Relative weights (clarifications); the check is `weight > 0`, never `sum = 100` |
| Function returns `setof` and phase 05 forgets `data[0]` | M×L | Return shape stated here and repeated in phase 05's contract |

## Security Considerations

- This is the first `security definer` surface in the repository. Its containment is exactly the
  three measures in [permissions](spec/system/permissions.md): pinned `search_path`, no identity
  parameter, execute granted only to `authenticated`.
- No parameter means "open someone else's box" and "pick my favourite badge" are not sentences
  PostgREST can form — unrepresentable, not merely rejected.
- `secret_box_openings` is readable only by its owner; the odds are deliberately public (they are
  printed in the design).
- No secret, key or connection string enters the migration or `seed.sql`.

## Next Steps

- Unblocks phase 05 (with phase 02).
- Promote PERM016/017/018 into `docs/system/permissions.md` after delivery (`doc-writer`), per the
  `promote_target` in the spec's frontmatter.
- Rollback: drop the two tables and the function in a new additive migration; nothing existing was
  altered, so no data is lost by reverting. Never edit this migration once it has been applied
  anywhere but a local database.
