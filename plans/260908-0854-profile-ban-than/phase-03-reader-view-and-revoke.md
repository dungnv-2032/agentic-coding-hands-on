# Phase 03 — Reader view, revoke, policy repair, seed

**Track:** B (schema/security — must land **before** the data layer) · **Owner:** `implementer` · **Effort:** 2.5h
**File ownership:** `supabase/migrations/20260908100000_profile_reader_view.sql` (new),
`supabase/seed.sql`, `lib/supabase/database.types.ts` (regenerated, never hand-edited)

## Context Links

- `clarifications.md` § "Security — the finding that changes the design", § "Resolved by probe: the
  reader view exposes flat sender columns", § "Resolved against the live database"
- `reports/orchestrator-postgrest-masked-view-probe.md` — **the constraint on this phase**
- `spec/F006_ProfileBanThan/technical-spec.md` § 4.2 (`Security — view đọc an toàn`)
- `spec/system/permissions.md` (PERM012/PERM013 forward draft), `spec/system/architecture.md`
- Existing SQL: `supabase/migrations/20260906140914_kudos_live_board.sql:161-195`,
  `supabase/migrations/20260907025909_viet_kudo_write_path.sql:36-70, 118-235`

## Overview

- **Priority:** P1 — FR-001. SEC_001 and SEC_002 are false statements about the system until this lands.
- **Status:** pending
- Turn Kudos anonymity from a rendering convention into a read-layer guarantee: a masked reader
  view, direct `select` on `public.kudos` revoked, and the two shipped write paths kept working.

## Key Insights

### 1. The revoke as written in the spec breaks the heart toggle and `create_kudos()`. Measured.

`clarifications.md` states "three call sites is the whole blast radius — measured, not estimated."
That measurement was taken at the **application** layer (`.from("kudos")`). At the **SQL** layer
there are four more dependants on `select` privilege on `public.kudos`, and the revoke takes them
all down. Probed against the running local stack, `revoke select on public.kudos from authenticated`
alone, inside a rolled-back transaction, as role `authenticated` with a real JWT claim:

```
--- P1: kudos_likes insert (policy references public.kudos) ---
ERROR:  permission denied for table kudos
HINT:  Grant the required privileges to the current role with: GRANT SELECT ON public.kudos TO authenticated;

--- P2: create_kudos() (security invoker, INSERT ... RETURNING) ---
ERROR:  permission denied for table kudos
CONTEXT: SQL statement "insert into public.kudos (...) returning id"
         PL/pgSQL function create_kudos(...) line 76 at SQL statement
```

Two independent mechanisms:

- **RLS policy expressions are evaluated with the caller's privileges.** Three policies join
  `public.kudos` inside their `WITH CHECK`: `kudos_likes_insert_own`
  (`20260906140914:174-179`), `kudos_hashtags_insert_own` and `kudos_attachments_insert_own`
  (`20260907025909:47-70`). Revoke the privilege and the heart toggle — the very action FR-405
  reuses "untouched" — dies for every user.
- **`INSERT ... RETURNING id` requires `select` on the returned column,** and `create_kudos()` is
  deliberately `security invoker` so RLS still applies to it. F005's entire write path dies.

**This contradicts `clarifications.md`'s stated blast radius and it is not a judgement call — it is a
measured `permission denied`.** Recorded here rather than resolved quietly, per the standing rule.

### 2. The fix set, also measured working

Same transaction shape, all five probes:

```
P1 kudos_likes insert  → INSERT 0 1                          (definer helper in the policy)
P2 create_kudos        → new_id 69                            (grant select (id))
P3 select sender_id    → ERROR permission denied for table kudos   (the hole is closed)
P4 select count(id)    → 63                                   (granted column only; harmless)
P5 view read           → id 1 | sender_id 1 | Huỳnh Dương Xuân Nhật   (owner-privileged view still reads)
```

- `create function public.is_kudos_sender(bigint) ... language sql security definer stable` and
  rewrite the three policies to call it. The predicate keeps its exact meaning; only *whose*
  privileges evaluate it changes.
- `grant select (id) on public.kudos to authenticated` — a **column** grant, the minimum
  `INSERT ... RETURNING id` needs. It exposes nothing: row ids are already public via the view, and
  a `where sender_id = …` filter on the base table is still denied (a WHERE clause needs `select` on
  that column — probed: denied for both `anon` and `authenticated`). This avoids editing F005's
  `create_kudos()` at all, and avoids the far worse alternative of making it `security definer`,
  which would bypass every INSERT policy the migration comment says it deliberately honours.

### 3. The view exposes flat pre-masked sender columns — never an embeddable FK

From the probe report: a `CASE`-masked column is not traceable, so the FK-hinted embed fails with
`PGRST200`; and **dropping the hint returns the wrong human with a 200** (the receiver in the sender
slot). So the view does the sender join itself. Re-verified over HTTP with the browser anon key
against a temporary `probe_kudos_readable` (created, measured, dropped — `pg_views` in `public` back
to **0**): all four of `fetchKudos`'s embeds still resolve through the view —
`receiver:sunners!kudos_receiver_id_fkey(... department:departments(name))`,
`hashtags:kudos_hashtags(...)`, `attachments:kudos_attachments(...)`, `likes:kudos_likes(count)` —
because `id` and `receiver_id` stay plain, traceable columns.

### 4. The mask is what preserves F004's self-like refusal

Because the `CASE` reveals `sender_id` **to the sender**, `toggle-kudos-like.ts:73`'s
"cannot like your own kudos" check still fires for the author of an anonymous Kudo, and
`board-data.ts`'s `canLike`/`isOwnedByViewer` keep their meanings. The caller predicate must
therefore live **inside** the view, evaluated per row by the database — not in application code.

### 5. `spotlight_ticker_events` needs no change, and the invariant must be written down

Measured: 7/7 rows have `sunner_id` = the Kudos' **receiver**, 0/7 the sender. A receiver is public
even on an anonymous Kudos, so the pairing cannot leak a sender. The migration carries a comment
recording the invariant so a later writer does not put a sender there and re-open what this closes.

### 6. The seed has zero anonymous Kudos (measured), so the mask is untestable today

`select count(*) filter (where is_anonymous) from public.kudos` → **0**. One seeded anonymous row is
the minimum that makes GUI_006's masking and SEC_001's premise observable.

## Requirements

Functional: FR-001. Non-functional: additive and re-runnable under `supabase db reset`; the F004
board and F005 compose path stay green; PostgREST must see the new view without a container restart.

## Architecture

```
        anon / authenticated                       migration owner (postgres)
                 │                                            │
   select ✗  public.kudos  (revoked; select(id) to authenticated only)
                 │                                            │
                 └──► public.kudos_readable  ──────────────────┘
                        owner-privileged view (no security_invoker)
                        · id, receiver_id, campaign, message, sent_at,
                          heart_baseline, message_format, is_anonymous, anonymous_name  → plain
                        · sender_id, sender_full_name, sender_avatar_url,
                          sender_kudos_received_baseline, sender_department_name
                          → CASE-masked together, per row, on caller identity
   insert   public.kudos_likes / kudos_hashtags / kudos_attachments
                        policies now call public.is_kudos_sender(bigint)  [security definer]
```

**Data flow:** app → PostgREST → `kudos_readable` (mask applied in SQL, per row) → rows in which an
anonymous sender is already absent. Nothing downstream can un-mask, because nothing downstream has
the privilege.

## Related Code Files

Create: `supabase/migrations/20260908100000_profile_reader_view.sql` — sorts after
`20260907025909_viet_kudo_write_path.sql`.
Modify: `supabase/seed.sql` (one new group, Group D). Regenerate: `lib/supabase/database.types.ts`
via `npm run db:types` — **never** hand-edit.
Delete: none. Do not alter `create_kudos()`, and do not alter any existing migration file.

## Implementation Steps

1. Create the migration with a header comment stating the measured problem (the anon key reading
   `sender_id` off an anonymous row), the two mechanisms that make the naive revoke fail, and the
   `spotlight_ticker_events` invariant.
2. `create function public.is_kudos_sender(p_kudos_id bigint) returns boolean language sql
   security definer stable set search_path = public` returning the `exists(...)` predicate copied
   from `kudos_likes_insert_own`. `grant execute ... to authenticated`.
3. `drop policy` + `create policy` for the three insert policies, substituting
   `public.is_kudos_sender(kudos_id)` for the inline join. `kudos_likes_insert_own` keeps its
   `(select auth.uid()) = user_id` conjunct and negates the helper.
4. `create view public.kudos_readable` — all nine unmasked `kudos` columns plus the five masked
   sender columns, joining `sunners` then `departments` for the sender. **Do not** set
   `security_invoker`; the owner-privileged default *is* the mechanism. One shared `CASE` predicate:
   `k.is_anonymous and k.sender_id is distinct from (select s.id from public.sunners s where s.auth_user_id = (select auth.uid()))`.
5. `revoke select on public.kudos from anon, authenticated;` then
   `grant select (id) on public.kudos to authenticated;` (that order — the table revoke would
   otherwise drop the column grant). `grant select on public.kudos_readable to anon, authenticated;`
6. `notify pgrst, 'reload schema';` as the last statement. PostgREST caches the schema; without this
   the view is invisible until a restart (the probe needed the reload).
7. Add Group D to `supabase/seed.sql`, after Group C, with a comment block in F004's style
   justifying every composed value:
   - **one** row: sender `Huỳnh Dương Xuân` (an existing corpus person), receiver
     `Huỳnh Dương Xuân Nhật` (the frame viewer, so the row is reachable at `/profile?id=1`),
     `is_anonymous = true`, `anonymous_name = null`.
   - Justify: `anonymous_name` stays NULL **on purpose** so the shipped fallback
     `ANONYMOUS_FALLBACK_LABEL = "Ẩn danh"` (`lib/kudos/board-data.ts:28`) is exercised — the design
     CSV publishes no anonymous display name, and inventing one would be inventing design data.
   - `heart_baseline` = 1, matching Group B, which keeps the row far below Group A's floor of 52 so
     it can never enter the top-5 highlight carousel and cannot move F004's `.first()`-based K-9.
   - `sent_at` continues Group C's `- (n) * interval '6 hours'` walk so ordering stays deterministic.
   - Verified safe against F004's suite: no e2e assertion fixes an absolute `kudos-card` count, and
     `SIDEBAR_STATS` asserts **labels only**, not the verbatim `25`s.
8. `supabase db reset` (or `supabase migration up`), then `npm run db:types`, then `npm run typecheck`.
9. Run the acceptance probes in § Success Criteria and paste their output into
   `evidence/phase-03-security-probes.log`.

## Todo List

- [ ] Migration filename sorts after `20260907025909_viet_kudo_write_path.sql`
- [ ] `is_kudos_sender()` created `security definer stable`, execute granted
- [ ] Three insert policies rewritten to call it; predicate semantics unchanged
- [ ] `kudos_readable` created with flat masked sender columns; `receiver_id` left plain
- [ ] Caller predicate lives **inside** the view's `CASE`
- [ ] `security_invoker` deliberately **not** set, with a comment saying why
- [ ] `revoke` then `grant select (id)` in that order; view granted to both roles
- [ ] `notify pgrst, 'reload schema'` present
- [ ] `spotlight_ticker_events` invariant recorded as a comment
- [ ] Seed Group D added, each value justified inline
- [ ] `npm run db:types` regenerated; `kudos_readable` appears under `Views`
- [ ] All eight acceptance probes pass; output captured to `evidence/`

## Success Criteria

Observable, each a command:

1. `docker exec supabase_db_my-app psql -U postgres -d postgres -c "select count(*) from pg_views where schemaname='public' and viewname='kudos_readable';"` → 1.
2. As `anon` over HTTP: `GET /rest/v1/kudos?select=id,sender_id&limit=1` → **error**, not 200.
3. As `anon` over HTTP on the seeded anonymous row: `sender_id`, `sender_full_name`,
   `sender_avatar_url`, `sender_department_name`, `sender_kudos_received_baseline` are all `null`;
   `is_anonymous` is `true`; `receiver_id` is present.
4. On a non-anonymous row, as `anon`: `sender_full_name` equals the **expected named person**, and
   is **different** from the receiver's name — the assertion that case C of the probe report would fail.
5. As the sender's own session (`set local request.jwt.claims` with that `auth_user_id`), the same
   anonymous row returns the real `sender_id` and name.
6. `select id from public.kudos where sender_id = 1` as `anon` → permission denied (no filter oracle).
7. `insert into public.kudos_likes …` as `authenticated` → succeeds (heart toggle alive).
8. `select public.create_kudos(…)` as `authenticated` → returns an id (F005 write path alive).
9. `grep -c "is_anonymous" supabase/seed.sql` ≥ 1 and
   `select count(*) filter (where is_anonymous) from public.kudos` ≥ 1 after reset.

## Risk Assessment

| Risk | L×I | Countermeasure |
|---|---|---|
| Revoke silently kills the heart toggle and compose | **measured certain** without the fix | The definer helper + column grant are steps 2/3/5, and probes 7 and 8 are release-blocking |
| Implementer "fixes" a `PGRST200` by dropping the FK hint | M × **H** | Flat sender columns mean there is no sender hint to drop; success criterion 4 asserts the *right person*, which case C fails |
| Forgetting `notify pgrst` → PostgREST 404s the view, looks like a code bug | M × M | Step 6 + probe 2/3 exercise the HTTP path, not just psql |
| Column grant misread as re-opening the hole | M × L | Probe 6 shows a filter on `sender_id` is still denied; only `id` is readable |
| Seed row shifts a ratified F004 assertion | L × M | `heart_baseline = 1` keeps it out of the top-5; no count assertions exist (verified by grep of `kudos-live-board.spec.ts`) |
| `db:types` hand-edited | L × M | `npm run db:types` is the only permitted path; diff must show generated formatting |
| Local DB carries 6 stray e2e `kudos` rows and 6 stray `sunners` (measured) | M × L | Run `supabase db reset` before validating, so probe numbers are reproducible |

**Rollback.** Supabase migrations are forward-only; locally `supabase db reset` reverts everything.
For a deployed environment, the down path is a new migration containing exactly:

```sql
grant select on public.kudos to anon, authenticated;   -- restores kudos_select_all's reach
revoke select (id) on public.kudos from authenticated; -- table grant now covers it
drop view public.kudos_readable;
-- restore the three policies to their inline-join form (verbatim from
-- 20260906140914:174-179 and 20260907025909:47-70), then:
drop function public.is_kudos_sender(bigint);
notify pgrst, 'reload schema';
```

Order matters: restore the table grant **before** dropping the view, or the board is dark between
the two statements. Phase 04's call sites must be reverted in the same deploy — a reverted view with
a repointed `queries.ts` is a broken board.

## Security Considerations

- The view is the *only* narrowing; it runs owner-privileged, so its `CASE` is the entire boundary.
  No application code may re-implement or bypass it (`architecture.md` delta records this).
- Anonymity is a **read**-layer guarantee, not deletion: `public.kudos.sender_id` still holds the
  truth for a future moderation feature, reachable only by the migration/admin role.
- `is_kudos_sender()` is `security definer` and takes a bigint id only — it returns a boolean, never
  a sender id, so it cannot be used as an oracle. It is `stable` and `set search_path = public`.
- `revoke ... from anon` matters most: the anon key ships to every browser by design.

## Next Steps

- Blocks phase 04 (the three call sites cannot be repointed at a view that does not exist).
- Hand the regenerated `database.types.ts` shape to phase 04 — `kudos_readable` lands under
  `Database["public"]["Views"]`, not `["Tables"]`, so `queries.ts`'s `Row<>` helper does not cover it.
- Advisory (out of scope): no composite `(receiver_id, sent_at desc, id desc)` index is added.
  At 57 seeded rows the existing single-column indexes are adequate; revisit with ADV-1.
