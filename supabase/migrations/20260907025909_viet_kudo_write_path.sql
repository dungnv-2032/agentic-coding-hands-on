-- Viết Kudo (`/kudos/new`) — write path: columns, INSERT policies + grants,
-- the transactional create_kudos() function, the attachments bucket, and the
-- seeded Unassigned department. See
-- plans/260907-0822-viet-kudo/phase-03-schema-rls-storage-and-image-host.md
-- and clarifications.md § "What the schema cannot hold yet" / § "Sender
-- identity" / assumption A1.
--
-- Additive only: no existing column is altered, nothing is dropped or
-- renamed. Deliberately no UPDATE and no DELETE policy anywhere in this
-- migration — editing a Kudos ("Màn Sửa bài viết") and moderating/deleting
-- one ("Admin - Review content") are separate, not-yet-built commissions.
-- Silence stays the deny for both verbs on every table this migration
-- touches, exactly as `20260906140914_kudos_live_board.sql` already relies
-- on for nine of its ten tables.

-- ---------------------------------------------------------------------------
-- 1. New kudos columns
-- ---------------------------------------------------------------------------
alter table public.kudos
  add column is_anonymous boolean not null default false,
  add column anonymous_name text,
  add column message_format text not null default 'plain'
    check (message_format in ('plain', 'doc'));

-- ---------------------------------------------------------------------------
-- 2. Seeded `Unassigned` department — backs auto-provisioned sunners
--    (clarifications.md assumption A1). filter_position stays NULL so it can
--    never enter the Phòng ban dropdown; F004's K-3 asserts exactly 50
--    filterable options.
-- ---------------------------------------------------------------------------
insert into public.departments (name, filter_position)
values ('Unassigned', null)
on conflict (name) do nothing;

-- ---------------------------------------------------------------------------
-- 3. INSERT policies — all `to authenticated`, all bridging through
--    sunners.auth_user_id = (select auth.uid()), the idiom already shipped
--    for kudos_likes_insert_own. `(select auth.uid())` is wrapped so
--    Postgres evaluates it once as an InitPlan.
-- ---------------------------------------------------------------------------
create policy "kudos_insert_own" on public.kudos for insert to authenticated
with check (
  exists (
    select 1 from public.sunners s
    where s.id = sender_id and s.auth_user_id = (select auth.uid())
  )
);

create policy "kudos_hashtags_insert_own" on public.kudos_hashtags for insert to authenticated
with check (
  exists (
    select 1 from public.kudos k
    join public.sunners s on s.id = k.sender_id
    where k.id = kudos_id and s.auth_user_id = (select auth.uid())
  )
);

create policy "kudos_attachments_insert_own" on public.kudos_attachments for insert to authenticated
with check (
  exists (
    select 1 from public.kudos k
    join public.sunners s on s.id = k.sender_id
    where k.id = kudos_id and s.auth_user_id = (select auth.uid())
  )
);

create policy "sunners_insert_own" on public.sunners for insert to authenticated
with check ((select auth.uid()) = auth_user_id);

-- ---------------------------------------------------------------------------
-- 4. Grants — a policy without a matching grant is still a deny; Postgres
--    checks the table GRANT first, then RLS.
-- ---------------------------------------------------------------------------
grant insert on public.kudos, public.kudos_hashtags, public.kudos_attachments, public.sunners
  to authenticated;

-- ---------------------------------------------------------------------------
-- 5. Storage bucket + policies. Created in SQL, not supabase/config.toml —
--    the toml bucket block requires a container restart to take effect,
--    easy to forget; a SQL insert is recreated automatically by
--    `supabase db reset`.
--
--    Public read: the Kudos board is public and attachments render into
--    permanent URLs server-side, so a signed URL would expire mid-render.
--    Narrow write: authenticated only, and only under a first path segment
--    equal to the caller's own uid — one user cannot write into another's
--    folder, and no policy permits update/delete of an existing object.
-- ---------------------------------------------------------------------------
insert into storage.buckets (id, name, public)
values ('kudos-attachments', 'kudos-attachments', true)
on conflict (id) do nothing;

create policy "kudos_attachments_object_insert" on storage.objects for insert to authenticated
with check (
  bucket_id = 'kudos-attachments'
  and (storage.foldername(name))[1] = (select auth.uid())::text
);

create policy "kudos_attachments_object_read" on storage.objects for select to anon, authenticated
using (bucket_id = 'kudos-attachments');

-- ---------------------------------------------------------------------------
-- 6. create_kudos() — the multi-table write, in one transaction.
--
--    PostgREST cannot transact across kudos / kudos_hashtags /
--    kudos_attachments, and there is deliberately no DELETE policy to
--    compensate a partial failure with. `security invoker` (not definer) is
--    deliberate: the function runs as the caller, so every policy above
--    still applies — RLS is not bypassed, merely given a single-transaction
--    place to run. The actor is resolved from auth.uid() inside the
--    function; the client has no argument in which to put a sender_id at
--    all, so forging one is unrepresentable rather than merely rejected.
--
--    Order matters: resolve/provision the sender FIRST, so the kudos
--    `with check` (which joins through sunners) can see the row, then
--    validate input, then insert. The sunners provision upserts on the
--    already-unique auth_user_id and re-selects, so a double-submit cannot
--    create two rows.
-- ---------------------------------------------------------------------------
create function public.create_kudos(
  p_receiver_id bigint,
  p_campaign text,
  p_message text,
  p_message_format text,
  p_is_anonymous boolean,
  p_anonymous_name text,
  p_hashtag_ids bigint[],
  p_image_urls text[]
)
returns bigint
language plpgsql
security invoker
set search_path = public
as $$
declare
  v_uid uuid := auth.uid();
  v_sender_id bigint;
  v_full_name text;
  v_avatar_url text;
  v_unassigned_department_id bigint;
  v_kudos_id bigint;
begin
  if v_uid is null then
    raise exception 'create_kudos requires an authenticated session'
      using errcode = '28000'; -- invalid_authorization_specification
  end if;

  -- Resolve the caller's sunners row, provisioning it on first write.
  select id into v_sender_id from public.sunners where auth_user_id = v_uid;

  if v_sender_id is null then
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

    select id into v_sender_id from public.sunners where auth_user_id = v_uid;
  end if;

  if v_sender_id is null then
    raise exception 'failed to resolve or provision sender'
      using errcode = 'P0001'; -- raise_exception (generic backstop, unreachable in practice)
  end if;

  if p_receiver_id is null or not exists (select 1 from public.sunners where id = p_receiver_id) then
    raise exception 'receiver is required and must exist'
      using errcode = '23503'; -- foreign_key_violation
  end if;

  if p_campaign is null or btrim(p_campaign) = '' then
    raise exception 'campaign (Danh hiệu) must not be blank'
      using errcode = '23514'; -- check_violation
  end if;

  if p_message is null or btrim(p_message) = '' then
    raise exception 'message must not be blank'
      using errcode = '23514'; -- check_violation
  end if;

  if p_message_format is null or p_message_format not in ('plain', 'doc') then
    raise exception 'message_format must be plain or doc'
      using errcode = '23514'; -- check_violation
  end if;

  if p_hashtag_ids is null or array_length(p_hashtag_ids, 1) is null
     or array_length(p_hashtag_ids, 1) < 1 or array_length(p_hashtag_ids, 1) > 5 then
    raise exception 'a kudos must carry between 1 and 5 hashtags'
      using errcode = '23514'; -- check_violation
  end if;

  if p_image_urls is not null and array_length(p_image_urls, 1) > 5 then
    raise exception 'a kudos may carry at most 5 images'
      using errcode = '23514'; -- check_violation
  end if;

  insert into public.kudos (
    sender_id, receiver_id, campaign, message, sent_at,
    is_anonymous, anonymous_name, message_format
  )
  values (
    v_sender_id, p_receiver_id, p_campaign, p_message, now(),
    coalesce(p_is_anonymous, false), p_anonymous_name, p_message_format
  )
  returning id into v_kudos_id;

  insert into public.kudos_hashtags (kudos_id, hashtag_id, position)
  select v_kudos_id, hashtag_id, (ordinality - 1)::smallint
  from unnest(p_hashtag_ids) with ordinality as t(hashtag_id, ordinality);

  if p_image_urls is not null and array_length(p_image_urls, 1) > 0 then
    insert into public.kudos_attachments (kudos_id, image_url, position)
    select v_kudos_id, image_url, (ordinality - 1)::smallint
    from unnest(p_image_urls) with ordinality as t(image_url, ordinality);
  end if;

  return v_kudos_id;
end;
$$;

grant execute on function public.create_kudos(
  bigint, text, text, text, boolean, text, bigint[], text[]
) to authenticated;
