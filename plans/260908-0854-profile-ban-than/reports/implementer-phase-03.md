# Phase 03 — Reader view, revoke, policy repair, seed — implementer report

## Files touched

| File | Change | Lines |
|---|---|---|
| `supabase/migrations/20260908100000_profile_reader_view.sql` | create | 200 |
| `supabase/seed.sql` | edit — Group D added after Group C | +45 (289 → 334) |
| `lib/supabase/database.types.ts` | regenerated via `npm run db:types` | +56 / −1 |

`git status --porcelain` shows exactly these three paths from this phase. Nothing outside the
ownership list was touched — no `create_kudos()` edit, no existing migration edited, no app code,
no test file, no plan/spec file. (`app/profile/_components/`, `e2e/profile*`, `lib/i18n/*` and the
`docs/*` churn in the same working tree belong to phases 01/02/07/08 running concurrently.)

Evidence log: `plans/260908-0854-profile-ban-than/evidence/phase-03-security-probes.log` (272 lines,
every command and its raw output).

## What was done

### 1. `is_kudos_sender(bigint)` — the load-bearing half of the fix

`security definer stable set search_path = public`, `execute` granted to `authenticated`. The
`exists(...)` body is copied verbatim from `kudos_likes_insert_own`, so the predicate keeps its exact
meaning; only *whose* privileges evaluate it changes. It takes a bigint and returns a boolean —
never a sender id — so it cannot serve as a de-anonymization oracle.

### 2. The three INSERT policies rewritten to call it

`kudos_likes_insert_own`, `kudos_hashtags_insert_own`, `kudos_attachments_insert_own` dropped and
recreated. `kudos_likes_insert_own` keeps its `(select auth.uid()) = user_id` conjunct and negates
the helper. Read back from `pg_policy` after reset:

```
 kudos_attachments_insert_own | is_kudos_sender(kudos_id)
 kudos_hashtags_insert_own    | is_kudos_sender(kudos_id)
 kudos_likes_insert_own       | ((( SELECT auth.uid() AS uid) = user_id) AND (NOT is_kudos_sender(kudos_id)))
```

### 3. `public.kudos_readable`

Nine plain columns (`id`, `receiver_id`, `campaign`, `message`, `sent_at`, `heart_baseline`,
`message_format`, `is_anonymous`, `anonymous_name`) + five flat, pre-masked sender columns
(`sender_id`, `sender_full_name`, `sender_avatar_url`, `sender_kudos_received_baseline`,
`sender_department_name`). The view does the `sunners` → `departments` join itself; there is no
embeddable sender FK and therefore no hint an implementer can "fix" a `PGRST200` by dropping.

`security_invoker` is deliberately **not** set, with a comment in the migration saying why: the
owner-privileged default *is* the mechanism, and the view's own `CASE` is the entire boundary.

The shared predicate is computed **once per row** in a `cross join lateral`
(`hide_sender`) rather than pasted five times — DRY, and probed not to disturb PostgREST's column
traceability (P4/P4b below).

### 4. Grants, in the required order

```sql
revoke select on public.kudos from anon, authenticated;
grant select (id) on public.kudos to authenticated;
grant select on public.kudos_readable to anon, authenticated;
```

Verified from `information_schema` after reset: on `public.kudos` the **only** `SELECT` left is
`authenticated` on column `id`; `anon` has no `SELECT` at all. Both roles have `SELECT` on the view.

### 5. `notify pgrst, 'reload schema'` and the invariant comment

Last executable statement. The `spotlight_ticker_events.sunner_id` invariant ("always the RECEIVER,
never a sender — measured 7/7") is recorded as a header comment, with the reason a future writer
must not break it.

### 6. Seed Group D — one anonymous row

Sender `Huỳnh Dương Xuân` (sunner 2, an existing corpus person), receiver `Huỳnh Dương Xuân Nhật`
(sunner 1, the frame viewer, so the row is reachable at `/profile?id=1`), `is_anonymous = true`,
`anonymous_name = null`, `heart_baseline = 1`, `sent_at` continuing Group C's `6 hours` walk at
`n = 67`. Lands as `kudos.id = 58`. Every value justified inline in F004's comment style, including
why `anonymous_name` stays NULL (exercises the shipped `ANONYMOUS_FALLBACK_LABEL = "Ẩn danh"`; the
design CSV publishes no anonymous display name and inventing one would be inventing design data).

### 7. Rollback note

Written into the migration file itself, after the `notify`, so the down path lives next to the up
path: the four statements, the policy-restoration pointer, the ordering constraint (restore the
table grant **before** dropping the view, or the board is dark between the two statements) and the
warning that phase 04's call sites must revert in the same deploy.

## Checks

| Check | Result |
|---|---|
| `npx supabase db reset` | **exit 0** — `Applying migration 20260908100000_profile_reader_view.sql` → `Finished`. Run 3× (initial, post-probe restore, post-comment-trim); clean every time. |
| `npm run db:types` | **exit 0** — generated, not hand-edited; diff is generator formatting only |
| `npm run typecheck` | **exit 0** |
| `npm run lint` | **exit 0** — 30 warnings, all in `e2e/*.spec.ts` (`homepage`, `homepage-authed`, `kudos-live-board`, `profile`, `viet-kudo`); none in a file this phase touched |
| Migration file size | 200 lines (at the cap, not over) |
| `database.types.ts` shape | `kudos_readable` lands under `Database["public"]["Views"]`, with its **only** `Relationships` entry `kudos_receiver_id_fkey → sunners`. No sender relationship exists to mis-hint. `is_kudos_sender` appears under `Functions`. |

### Acceptance probes — all nine, plus three extra

Full transcript in `evidence/phase-03-security-probes.log`. Probes were run as a **real signed-up
user** (`POST /auth/v1/signup` → `8b2563a9-907e-46fc-ad97-b1e9a4ba26ea`), not a fabricated uuid,
exactly as `clarifications.md` § CORRECTION requires.

| # | Probe | Result |
|---|---|---|
| 1 | `pg_views` count for `kudos_readable` | **1** |
| 2 | anon, HTTP `GET /rest/v1/kudos?select=id,sender_id&limit=1` | **HTTP 401** `42501 permission denied for table kudos` |
| 3 | anon, HTTP, seeded anonymous row `id=58` through the view | `sender_id`, `sender_full_name`, `sender_avatar_url`, `sender_department_name`, `sender_kudos_received_baseline` **all null**; `is_anonymous: true`; `receiver_id: 1` present |
| 4 | anon, HTTP, non-anonymous `id=1` | `sender_id: 1`, `sender_full_name: "Huỳnh Dương Xuân Nhật"` — the **right** person, and different from `receiver: {id: 2, "Huỳnh Dương Xuân"}`. Case C of the probe report would have returned the receiver here. |
| 5 | the sender's own session on `id=58` (psql, real auth user linked to sunner 2 inside a rolled-back txn) | `sender_id: 2`, `sender_full_name: "Huỳnh Dương Xuân"` — unmasked, so F004's self-like refusal keeps its meaning |
| 6 | `select id from public.kudos where sender_id = 1` as `anon` | **permission denied**. Also denied: bare `select id from kudos limit 1` as `anon`, and the same filter as `authenticated`. `select count(id)` as `authenticated` → 58 (granted column only, harmless). **No filter oracle.** |
| 7 | HTTP `POST /rest/v1/kudos_likes` with the real user's JWT | **HTTP 201** + `DELETE` → **204**. Heart toggle alive, both halves. |
| 8 | HTTP `POST /rest/v1/rpc/create_kudos` with the real user's JWT | **HTTP 200 → `59`**. Called with 2 hashtags and 1 image and `is_anonymous: true`, so `kudos_hashtags_insert_own` and `kudos_attachments_insert_own` — the other two rewritten policies — were exercised too. F005 write path alive. |
| 9 | `grep -c is_anonymous supabase/seed.sql` → **2**; `count(*) filter (where is_anonymous)` after reset → **1** | pass |
| 4b | *extra:* `fetchKudos`'s full select through the view (sender embed swapped for the five flat columns) | **HTTP 200** — all four remaining embeds resolve: `receiver:sunners!kudos_receiver_id_fkey(... department:departments(name))`, `hashtags:kudos_hashtags(position, hashtag:hashtags(name))`, `attachments:kudos_attachments(...)`, `likes:kudos_likes(count)`. De-risks phase 04. |
| 7b | *extra:* the probe user, now sender of `kudos.id=59`, tries to like it | **HTTP 403** `new row violates row-level security policy for table "kudos_likes"`. The definer helper **preserved** the self-like refusal — it did not merely stop erroring. |
| 8b | *extra:* the mask end-to-end on a **real** anonymous Kudos written by a **real** session (`id=59`) | as anon → `sender_id: null`, `sender_full_name: null`; as the sender → `sender_id: 10`, own name. And `?sender_id=eq.10&is_anonymous=is.true` as anon → `[]`, so SEC_002's count cannot be reconstructed through the view either. |

Probes 7/8/7b/8b mutate the database on purpose; a final `npx supabase db reset` restored the seed
exactly (`58` kudos rows, `1` anonymous, `0` `auth.users`) and the log records that.

## Acceptance criteria (phase file Todo List)

- [x] Migration filename sorts after `20260907025909_viet_kudo_write_path.sql` — `20260908100000_…`, and `db reset` applied them in that order
- [x] `is_kudos_sender()` created `security definer stable`, execute granted — `pg_proc`: `prosecdef=t`, `provolatile=s`, `proconfig={search_path=public}`
- [x] Three insert policies rewritten to call it; predicate semantics unchanged — proven live by probe 7b (self-like still refused), not just by reading the SQL
- [x] `kudos_readable` created with flat masked sender columns; `receiver_id` left plain — probe 4/4b
- [x] Caller predicate lives **inside** the view's `CASE` — via the `mask.hide_sender` lateral, one evaluation per row; probe 5 exercises the caller branch
- [x] `security_invoker` deliberately **not** set, with a comment saying why — migration § 3
- [x] `revoke` then `grant select (id)` in that order; view granted to both roles — `information_schema` read back after reset
- [x] `notify pgrst, 'reload schema'` present — last executable statement; probes 2/3/4 hit the HTTP path with no container restart
- [x] `spotlight_ticker_events` invariant recorded as a comment — migration header
- [x] Seed Group D added, each value justified inline
- [x] `npm run db:types` regenerated; `kudos_readable` appears under `Views`
- [x] All eight (nine) acceptance probes pass; output captured to `evidence/phase-03-security-probes.log`

## Deviations from the phase file

1. **The shared `CASE` predicate is computed in a `cross join lateral`**, not written out five
   times. The phase file said "one shared `CASE` predicate" with the expression given; this is that
   expression, evaluated once per row instead of five. It was the riskier of the two spellings for
   PostgREST column traceability, so it was probed rather than assumed — P4 and P4b confirm every
   embed still resolves and `database.types.ts` still derives `kudos_receiver_id_fkey`. If a later
   phase ever needs the inlined form, it is a mechanical substitution.
2. **The rollback SQL lives inside the migration file** rather than only in the phase document, so
   the down path travels with the up path. This is what pushed the file to exactly 200 lines; four
   comment paragraphs were tightened (no information dropped) to stay inside the cap.
3. **`sender_id` is the masked column's name**, per the phase file's architecture block and success
   criterion 3 — *not* `sender_id_visible`, which is the name the earlier probe report used for its
   throwaway view. Flagged because the two documents disagree and phase 04 must use `sender_id`.

## Unresolved questions

1. **F004's board is dark between this phase and phase 04 — measured, and by design.** All three
   `.from("kudos")` call sites (`lib/kudos/queries.ts:53`,
   `app/kudos/_actions/toggle-kudos-like.ts:26,73`) still read the base table, which probe 2 shows
   is now `permission denied`. So `/kudos` and the heart toggle are **broken right now**, and
   F004's e2e suite will fail until phase 04 repoints them. The plan's dependency graph
   (`03 → 04 → 05`, strictly sequential) already says this; recorded here so nobody reads a red
   F004 run as a defect in this phase. **Phase 04 must land before any suite is judged.**
2. **Pre-existing, out of scope, worth someone's attention:** `anon` and `authenticated` also hold
   `INSERT`/`UPDATE`/`DELETE`/`TRUNCATE`/`TRIGGER`/`REFERENCES` grants on `public.kudos` (and on
   every other table in `public`, and now on the new view) from Supabase's default blanket grant.
   They are inert — RLS denies by default and neither migration writes an UPDATE or DELETE policy —
   and revoking them is a change to F004/F005's schema surface, not this phase's. Not a hole; a
   wider blast radius than necessary. Suggest an advisory alongside ADV-1/ADV-2/ADV-3.
3. **`anonymous_name` is NULL on the only seeded anonymous row**, on purpose (no design source).
   Whichever phase renders the card must therefore hit the `ANONYMOUS_FALLBACK_LABEL` branch, not
   the `anonymous_name` branch. If a test wants to assert a *published* anonymous alias, a copy
   decision is needed first — the same class of gap as phase 01's `feed.endOfFeed`.
