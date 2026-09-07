# Phase 03 — Schema, RLS, Storage bucket, image host

**Track:** B · **Owner:** `implementer` · **Depends:** — ·
**Effort:** 2h · **test_policy:** `e2e-red-first`

## Context Links

- [plan.md](plan.md) · [clarifications.md](clarifications.md) § What the schema cannot hold yet, § Sender identity, § Images
- [technical-spec.md](spec/viet-kudo/technical-spec.md) § 4.2 (columns, the four INSERT policies verbatim), § 5.1 SC-004
- [permissions.md draft](spec/system/permissions.md) · [architecture.md draft](spec/system/architecture.md)
- [write-path study](reports/write-path-conventions.md) § 3 (RLS **and** grants both missing — verified live), § 5 (bucket block commented out)
- Existing schema to extend, never rewrite: `supabase/migrations/20260906140914_kudos_live_board.sql`
  — table DDL `:14-120`, policies `:150-192`, grants `:194-195`, and the `kudos_likes_insert_own`
  bridge idiom `:172-179`
- Next 16.3.4 docs read for this phase: `node_modules/next/dist/docs/01-app/03-api-reference/02-components/image.md:533-556` (`remotePatterns`, incl. the `new URL()` shorthand)

## Overview

**Priority:** P1 · **Status:** completed.

One additive migration and one line of Next config. After this phase the database can accept a
Kudos, the bucket exists, and the board can render a remote image URL — but nothing writes yet, and
every existing read behaves identically.

## Key Insights

1. **A policy without a grant is still a deny.** The study verified live that
   `kudos`/`kudos_hashtags`/`kudos_attachments`/`sunners` have neither an INSERT policy nor an INSERT
   grant; Postgres checks the table GRANT first, then RLS. Both halves ship here, or the write fails
   with a permission error that looks like an RLS bug and is not.
2. **`kudos.sender_id` is a `bigint` into `sunners`, not an `auth.users` uuid.** The `with check`
   must therefore bridge — `exists (select 1 from public.sunners s where s.id = sender_id and
   s.auth_user_id = (select auth.uid()))`. That predicate is the only thing stopping a client forging
   a Kudos as somebody else. `(select auth.uid())` is wrapped so Postgres evaluates it once as an
   InitPlan, matching `kudos_likes_insert_own`.
3. **Three tables cannot be written atomically through PostgREST, and there is deliberately no
   DELETE policy to compensate with.** A partial failure would leave a Kudos with no hashtags, which
   violates BR-002 at rest and cannot be cleaned up. So this migration also ships
   `public.create_kudos(...)`, a **`security invoker`** function: one implicit transaction, RLS still
   evaluated as the caller (so every policy above is still the authority), the actor resolved from
   `auth.uid()` inside the function so the client has no place to put a `sender_id` at all, and the
   first-write `sunners` provision performed in the same transaction. This diverges from
   `technical-spec.md § 3.3`, which drew the inserts inside the Server Action — recorded as a
   deliberate divergence in § Risk, and the reason is atomicity, not preference.
4. **The provision reads the JWT, not a client argument.** Inside the function,
   `auth.jwt() -> 'user_metadata' ->> 'full_name'` (falling back to `name`, then the local part of
   `email`) and `... ->> 'avatar_url'` (falling back to `picture`, then
   `/images/kudos/sample-avatar.png`, the design's own committed placeholder). `on conflict
   (auth_user_id) do nothing` + re-select, because `auth_user_id` is already `unique` and a
   double-submit must not create two rows.
5. **`Unassigned` goes in the migration, not `seed.sql`.** `seed.sql` is F004's file and is not
   re-run by every environment the same way; the department is a structural precondition of the
   provision path, so it ships as an idempotent `insert … on conflict (name) do nothing` here.
   `filter_position` stays `NULL`, which keeps it out of the Phòng ban dropdown and K-3's 50 options
   intact.
6. **The bucket is created in SQL, not in `config.toml`.** `supabase/config.toml:114-120` has the
   bucket block commented out, and editing it requires `supabase stop && supabase start` — a
   container restart in every environment, easy to forget and invisible when forgotten. An
   `insert into storage.buckets … on conflict do nothing` inside the migration is recreated by
   `supabase db reset` automatically. One mechanism, not two.
7. **The bucket is public-read on purpose.** The Kudos board is public (`kudos_select_all` grants
   `anon`), attachments render server-side into permanent URLs, and signed URLs would expire inside a
   rendered page. Read is open; **write** is narrow: authenticated only, and only under a first path
   segment equal to the caller's own uid.
8. **`next/image` will throw on the first attachment without `remotePatterns`.**
   `kudos-attachments.tsx` renders every `image_url` through `next/image`; an unconfigured host is a
   render-time error, which takes down the whole `/kudos` page and with it every F004 assertion. The
   pattern is derived from `NEXT_PUBLIC_SUPABASE_URL` at config-eval time so local, CI and any future
   hosted project all work from one source of truth.

## Requirements

**Functional:** FR-001 (bucket), FR-002 (columns + policies + grants), FR-003 (`Unassigned`), BR-001
(provision), BR-002/BR-003 enforced as a backstop inside `create_kudos`, BR-004 server half,
SC-004's database layer.

**Non-functional:** the migration is additive and idempotent — it adds columns with defaults, adds
policies, adds grants, and inserts two rows conditionally. It alters no existing column, drops
nothing, and renames nothing. `npx supabase db reset` must succeed and leave every F004 seed count
unchanged. **No UPDATE and no DELETE policy is created anywhere.**

## Architecture

```
supabase/migrations/20260907HHMMSS_viet_kudo_write_path.sql
 1. alter table public.kudos
      add column is_anonymous   boolean not null default false,
      add column anonymous_name text,
      add column message_format text not null default 'plain'
        check (message_format in ('plain','doc'));
 2. insert into public.departments (name, filter_position) values ('Unassigned', null)
      on conflict (name) do nothing;
 3. policies (insert only, authenticated only)
      kudos_insert_own              with check (exists (select 1 from sunners s
                                       where s.id = sender_id and s.auth_user_id = (select auth.uid())))
      kudos_hashtags_insert_own     with check (exists (select 1 from kudos k join sunners s
                                       on s.id = k.sender_id
                                       where k.id = kudos_id and s.auth_user_id = (select auth.uid())))
      kudos_attachments_insert_own  same shape, kudos_attachments
      sunners_insert_own            with check ((select auth.uid()) = auth_user_id)
 4. grant insert on public.kudos, public.kudos_hashtags,
                     public.kudos_attachments, public.sunners to authenticated;
 5. insert into storage.buckets (id, name, public) values
      ('kudos-attachments','kudos-attachments', true) on conflict (id) do nothing;
    policy kudos_attachments_object_insert on storage.objects for insert to authenticated
      with check (bucket_id = 'kudos-attachments'
                  and (storage.foldername(name))[1] = (select auth.uid())::text);
    policy kudos_attachments_object_read on storage.objects for select to anon, authenticated
      using (bucket_id = 'kudos-attachments');
 6. create function public.create_kudos(
      p_receiver_id bigint, p_campaign text, p_message text, p_message_format text,
      p_is_anonymous boolean, p_anonymous_name text,
      p_hashtag_ids bigint[], p_image_urls text[]) returns bigint
    language plpgsql security invoker set search_path = public as $$ … $$;
      ├─ resolve v_sender from sunners where auth_user_id = auth.uid()
      ├─ if null: insert (auth_user_id, full_name, department_id=Unassigned, avatar_url)
      │           on conflict (auth_user_id) do nothing;  re-select
      ├─ raise on: no session · receiver missing · campaign/message blank
      │            · array_length(p_hashtag_ids) not between 1 and 5 · image urls > 5
      ├─ insert kudos (sender_id = v_sender, sent_at = now(), …) returning id
      ├─ insert kudos_hashtags  (position = ordinality)
      └─ insert kudos_attachments (position = ordinality); return the id
    grant execute on function public.create_kudos(...) to authenticated;
```

```ts
// next.config.ts — the only product-code change in this phase
const supabaseUrl = new URL(process.env.NEXT_PUBLIC_SUPABASE_URL ?? "http://127.0.0.1:54321");
images: { remotePatterns: [new URL(`${supabaseUrl.origin}/storage/v1/object/public/**`)] }
```

## Related Code Files

**Create:** `supabase/migrations/20260907HHMMSS_viet_kudo_write_path.sql`
**Modify:** `next.config.ts`
**Delete:** none
**Read only:** `supabase/migrations/20260906140914_kudos_live_board.sql`, `supabase/seed.sql`,
`supabase/config.toml`, `lib/kudos/viewer.ts`

## Implementation Steps

1. Create the migration with a real UTC timestamp prefix (`date -u +%Y%m%d%H%M%S`). Head it with a
   comment naming clarifications § "What the schema cannot hold yet" and stating plainly that no
   UPDATE/DELETE policy is created and why.
2. Write steps 1–5 from § Architecture in that order. Every `insert` carries `on conflict … do
   nothing`; every `create policy` uses the exact predicate text above.
3. Write `create_kudos`. Order matters: resolve/provision the sender **first** (so the `kudos`
   `with check` can see the row), then validate, then insert. Use
   `unnest(p_hashtag_ids) with ordinality` for `position`. Raise with `errcode` values distinct
   enough for the action to tell "no session" from "bad input".
4. `npx supabase db reset`. It must complete cleanly, apply both migrations and the F004 seed.
5. Verify the shape live:
   ```
   docker exec supabase_db_my-app psql -U postgres -d postgres -c \
     "select tablename, policyname, cmd from pg_policies where schemaname in ('public','storage') order by 1,3,2;"
   ```
   Expect the 12 F004 policies untouched, plus exactly four new `public` INSERT policies and two
   `storage.objects` policies. **Zero** rows with `cmd` in (`UPDATE`, `DELETE`) beyond F004's
   `kudos_likes_delete_own`.
6. Verify the counts F004 depends on:
   ```
   docker exec supabase_db_my-app psql -U postgres -d postgres -c \
     "select (select count(*) from kudos) k, (select count(*) from hashtags) h,
             (select count(*) from departments where filter_position is not null) d,
             (select count(*) from departments) dall;"
   ```
   Expect `57 | 13 | 50 | 51` — the 51st department is `Unassigned`, and it must not be counted in
   the filterable 50.
7. Verify the anon write refusal at the API layer (SC-004's database half):
   ```
   curl -s -o /dev/null -w '%{http_code}\n' -X POST "http://127.0.0.1:54321/rest/v1/kudos" \
     -H "apikey: $NEXT_PUBLIC_SUPABASE_ANON_KEY" -H "Content-Type: application/json" \
     -d '{"sender_id":1,"receiver_id":2,"message":"x","sent_at":"2026-09-07T00:00:00Z"}'
   ```
   Must be 401/403, never 201. Repeat against `/rest/v1/rpc/create_kudos` — anon must be refused
   there too.
8. Edit `next.config.ts` per § Architecture. Keep the existing `NextConfig` typing.
9. `npm run typecheck && npm run lint`, then `npm run build` — the config is only exercised at
   build/dev start, so a malformed `remotePatterns` surfaces there and nowhere else.

## Todo List

- [x] Migration created with a real UTC timestamp; header states the no-UPDATE/no-DELETE decision
- [x] Three columns added with defaults + the `message_format` check constraint
- [x] `Unassigned` inserted with `filter_position NULL`, idempotently
- [x] Four INSERT policies, predicates exactly as § Architecture
- [x] INSERT grants for all four tables to `authenticated`
- [x] Bucket row + two `storage.objects` policies (narrow insert, open read)
- [x] `create_kudos` written: provision → validate → insert ×3 → return id; execute granted
- [x] `npx supabase db reset` clean
- [x] Step 5 policy inventory as expected, no new UPDATE/DELETE
- [x] Step 6 counts `57 | 13 | 50 | 51`
- [x] Step 7 anon POST and anon RPC both refused
- [x] `next.config.ts` remotePatterns derived from `NEXT_PUBLIC_SUPABASE_URL`
- [x] `npm run typecheck && npm run lint && npm run build` clean

## Success Criteria

- `db reset` applies cleanly and F004's board suite still passes unchanged
  (`npx playwright test e2e/kudos-live-board.spec.ts`).
- The policy inventory shows 4 new public INSERT policies + 2 storage policies and no new
  UPDATE/DELETE anywhere.
- Filterable departments stay at exactly 50; `hashtags` stays at 13; `kudos` stays at 57.
- Anon cannot insert a `kudos` row nor execute `create_kudos`.
- `npm run build` succeeds with the new `images.remotePatterns`.
- Every pre-existing row reads `message_format = 'plain'`, `is_anonymous = false`,
  `anonymous_name = null`.

## Risk Assessment

| Risk | L×I | Countermeasure |
|---|---|---|
| Policy ships without the matching grant, so the first write fails with a confusing permission error | **High** × High | Both in one migration, in adjacent blocks; step 7 exercises the refusal path and phase 07 exercises the allow path |
| `create_kudos` diverges from the spec draft's "inserts in the action" design and confuses a reviewer | Med × Med | Divergence stated in § Key Insights 3 with its reason (atomicity across 3 tables, no DELETE policy to compensate); `technical-spec.md § 3.3` is a draft and is reconciled at promote |
| `security definer` used by mistake, silently bypassing RLS | Low × **High** | `security invoker` is written explicitly plus `set search_path = public`; step 7's anon RPC refusal fails loudly if it were definer |
| `Unassigned` leaks into the Phòng ban dropdown and breaks K-3's 50 | Med × High | `filter_position NULL`; step 6 asserts the 50/51 split directly |
| Concurrent first writes race the provision and create two `sunners` rows | Med × Med | `on conflict (auth_user_id) do nothing` + re-select, inside the function's transaction; `auth_user_id` is already `unique` |
| Public bucket exposes more than intended | Med × Med | Read is scoped to `bucket_id = 'kudos-attachments'` only; insert is scoped to the caller's own uid folder; no other bucket exists |
| Missing `remotePatterns` takes down all of `/kudos`, not just the new screen | Med × **High** | Shipped in this same phase, before any row can hold a remote URL; `npm run build` in step 9 is the gate |
| `storage.foldername` unavailable or renamed in this Supabase version | Low × Med | Verified at step 5 by creating the policy — a bad function name fails the migration immediately, not at runtime |

**Rollback:** the migration is additive, so rollback is a new migration dropping the four policies,
the two storage policies, the function, the three columns and the two seeded rows — not an edit to
this file once applied. Before it is applied anywhere, deleting the file and reverting
`next.config.ts` is enough.

## Security Considerations

- The four `with check` predicates are the real boundary. The UI's disabled states and the action's
  TypeScript validation are conveniences; if only one layer can be right, it is RLS
  (`docs/system/permissions.md:91`).
- `create_kudos` never accepts a sender id. Identity comes from `auth.uid()` inside the function, so
  forging a sender is not merely rejected — it is unrepresentable.
- No `service_role` key is read, stored or referenced. `.env.example` deliberately omits it and this
  phase does not change that.
- Storage insert is confined to `{auth.uid()}/…`; one user cannot write into another's folder, and
  no policy permits overwriting or deleting an existing object.
- `message_format` carries a `check` constraint so a stray value can never reach the renderer's
  discriminator.
- Anonymity is a data flag only. It hides the sender on the board (phase 04/05); it does **not** hide
  `sender_id` in the row, which is deliberate — moderation still needs to know who wrote it, and the
  column is never mapped into a client payload for an anonymous kudos (phase 04 § Security).

## Next Steps

04 regenerates the types over these columns and maps them; 07 calls `create_kudos` and the upload
policy. Tell 04 the exact migration filename so its header can cite it.
