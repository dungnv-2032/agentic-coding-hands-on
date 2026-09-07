# Phase 07 — Write path: reads, validation, and the two Server Actions

**Track:** B (behavior/backend) · **Owner:** `implementer` · **Depends:** 01, 03, 04 ·
**Effort:** 3.5h · **test_policy:** `e2e-red-first`

## Context Links

- [plan.md](plan.md) · [phase-01](phase-01-foundation-and-integration-contract.md) (payload + error codes) · [phase-03](phase-03-schema-rls-storage-and-image-host.md) (`create_kudos`, the bucket, the policies) · [phase-04](phase-04-board-contract-and-read-mapping.md) (regenerated types)
- [clarifications.md](clarifications.md) § Sender identity, § Images, § Validation
- [technical-spec.md](spec/viet-kudo/technical-spec.md) § 3.2 A2, § 3.3 A3, § 4.4 (BR-002, BR-004, and the Bin-3 "no write accepts an actor id from the client" rule), § 4.5 ALG-001/INT-001, § 5.1 SC-003/SC-004
- [write-path study](reports/write-path-conventions.md) § 1 (`useActionState`, `refresh()` vs `revalidatePath`, no `cacheComponents`), § 2 (hand-rolled predicates, validate inside the action), § 4 (provisioning, ranked)
- The one existing write to copy: `app/kudos/_actions/toggle-kudos-like.ts:1-117` — actor from session, errors as return value, never a throw at the client
- Next 16.3.4 docs read for this phase: `01-app/02-guides/forms.md:9-10,134,147-161,190-274` · `01-app/01-getting-started/07-mutating-data.md:31-32,132,170,381-421,462-504` (`redirect` semantics and the "any code after it won't execute" note)

## Overview

**Priority:** P1 · **Status:** completed.

The whole server half of the screen: the one read that feeds the pickers, the pure validation
predicates, and two Server Actions. After this phase the write path is complete and provable by
`curl`/`psql` alone — the form does not exist yet.

## Key Insights

1. **Both actions are Server Actions, including the upload.** The upload must be, not merely may be:
   a plain client function cannot cross the RSC boundary as a prop, and phase 12's rule is that no
   Track A file imports a Track B module. Making the upload a Server Action keeps that rule intact
   **and** puts MIME validation on the server where it cannot be skipped. This diverges from
   `technical-spec.md § 3.2`/INT-001, which drew a browser-side Storage call; clarifications only
   fixed *real upload to Storage*, not the transport. Recorded divergence, reason stated.
2. **`create-kudos` is a thin shell over `create_kudos`.** Validate in TypeScript (so the client gets
   per-field codes), then one `supabase.rpc("create_kudos", …)`. The atomicity, the provisioning and
   the sender derivation all live in the function (phase 03) because PostgREST cannot transact across
   three tables and there is deliberately no DELETE policy to compensate with.
3. **`redirect("/kudos")` must sit outside every `try`.** It throws a framework control-flow
   exception; a `catch` would swallow it and the user would sit on a form that already wrote a row.
   The action's shape is: validate → rpc → *if error, return codes* → `redirect()` as the last
   statement at the top level (`mutating-data.md:504`).
4. **No `revalidatePath`, no `refresh()`.** `/kudos` reads `cookies()` and is therefore dynamic, and
   `next.config.ts` sets no `cacheComponents`, so there is no cache entry to invalidate — the
   redirect's own render is already fresh. `toggleKudosLike` uses `refresh()` because it *stays* on
   the page; this action leaves it. Different situation, different call.
5. **`ComposePayload` is untrusted.** It arrives from a client component, and `forms.md:9-10` warns
   Server Functions are POST-reachable directly. Every field is re-checked here: `receiverId` is a
   positive integer that exists in `sunners`, `title`/`plainText` are non-blank after trim,
   `hashtagIds` is 1–5 positive integers, `imageUrls` is ≤5 strings that each start with this
   project's own Storage public prefix, `anonymousName` is trimmed and length-capped.
6. **Image URLs are re-validated by origin, not by extension.** A client could pass any string. The
   check is: the URL parses, its origin equals `NEXT_PUBLIC_SUPABASE_URL`'s origin, and its path
   begins `/storage/v1/object/public/kudos-attachments/`. An attacker-supplied `evil.com/x.png`
   fails; a renamed `.pdf` cannot reach `kudos_attachments` because it never got a Storage URL from
   step 1 in the first place (the upload action validates the MIME before writing the object).
7. **`ALG-001` filtering stays client-side.** `getComposeOptions()` reads all sunners and all
   hashtags **once**, at page render. No server round-trip per keystroke — the same
   fetch-once-filter-in-the-client shape F004 uses for its filters.
8. **Storage paths must be unique per upload, and must not dedupe.** ID-18/19 set the *identical*
   fixture five times and expect five thumbnails. The path is
   `{auth.uid()}/{Date.now()}-{crypto.randomUUID()}.{ext}` — the uid prefix is what the storage
   policy checks, the rest is what makes five copies five objects.
9. **The upload action returns a URL or a code, never a throw.** Same discipline as
   `toggleKudosLike`: a thrown Server Action error surfaces as an opaque client error and the picker
   could not show `Định dạng file không được hỗ trợ`.
10. **Orphaned objects are accepted.** Removing a thumbnail drops it from client state only; the
    Storage object stays. It is unreferenced, unlisted and harmless — a cleanup job is a separate
    commission, and inventing a delete path would mean a DELETE policy this commission deliberately
    withholds.

## Requirements

**Functional:** FR-001, FR-002, FR-003, FR-206, FR-402, FR-403's submit half, BR-001 (provision, via
the function), BR-002 both halves, BR-004 server half, BR-005 (columns written), the Bin-3
no-client-actor rule, ALG-001's data source, SC-003, SC-004.

**Non-functional:** each file ≤200 lines; `validate-compose.ts` is pure and zero-dependency
(client-bundle-reachable, same rule as `derive.ts`); one read per page render for the options; no
`any`; the Supabase `user` object never leaves the server; only the anon key, through
`lib/supabase/server.ts`.

## Architecture

```
lib/kudos/compose-options.ts            "server-only" read
  getComposeOptions(): Promise<ComposeOptionsView>
    ├─ sunners:  id, full_name, avatar_url, department:departments(name)   order by full_name
    └─ hashtags: id, name                                                  order by position
       (one client, Promise.all — the app/_page-context.ts:28 pattern)

lib/kudos/validate-compose.ts           pure predicates, no imports but types
  validateCompose(payload): ComposeFieldErrors        ← recipient/title/body/hashtag, ALL at once (ID-56)
  isAcceptedImageType(mimeOrName): boolean            ← ACCEPTED_IMAGE_MIME, used by BOTH sides
  isOwnStorageUrl(url, supabaseOrigin): boolean       ← origin + path prefix check

app/kudos/new/_actions/upload-kudos-image.ts   "use server"
  uploadKudosImage(formData): Promise<UploadResult>
    ├─ getUser(); no session → { error: "unknown" }
    ├─ file = formData.get("file"); not a File → { error: "invalidType" }
    ├─ !isAcceptedImageType(file.type) → { error: "invalidType" }        ← server half of BR-004
    ├─ path = `${user.id}/${Date.now()}-${crypto.randomUUID()}.${ext}`
    ├─ storage.from("kudos-attachments").upload(path, file, { contentType: file.type })
    └─ { url: getPublicUrl(path).data.publicUrl }

app/kudos/new/_actions/create-kudos.ts         "use server"
  createKudos(prev: CreateKudosState, payload: ComposePayload): Promise<CreateKudosState>
    ├─ getUser(); no session → { errors: { form: "unknown" } }
    ├─ errors = validateCompose(payload); non-empty → { errors }          ← ID-56, all at once
    ├─ imageUrls.every(isOwnStorageUrl) else → { errors: { form: "unknown" } }
    ├─ rpc("create_kudos", { p_receiver_id, p_campaign: title,
    │      p_message: JSON.stringify(payload.doc), p_message_format: "doc",
    │      p_is_anonymous, p_anonymous_name, p_hashtag_ids, p_image_urls })
    ├─ error → map pg errcode → { errors: … }; nothing was written (function transaction rolled back)
    └─ redirect("/kudos")            ← top level, outside any try
```

**Data flow (submit):** client payload → `createKudos` → `validateCompose` → `rpc` → *inside one
transaction* provision sunner → insert `kudos` → insert `kudos_hashtags` → insert
`kudos_attachments` → returns id → `redirect("/kudos")` → `/kudos` re-renders dynamically → phase 04's
mapping → phase 05's renderer → the new card, newest-first, on page one of the feed.

## Related Code Files

**Create:** `lib/kudos/compose-options.ts` · `lib/kudos/validate-compose.ts` ·
`app/kudos/new/_actions/create-kudos.ts` · `app/kudos/new/_actions/upload-kudos-image.ts`
**Modify:** none · **Delete:** none
**Read only:** `lib/kudos/compose-contract.ts` (frozen), `lib/supabase/server.ts`,
`app/kudos/_actions/toggle-kudos-like.ts` (the idiom), `lib/kudos/viewer.ts`

## Implementation Steps

1. `lib/kudos/validate-compose.ts` first — it is pure, and both actions plus phase 10 depend on it.
   `validateCompose` collects **every** failing field into one object; it must not early-return.
2. `lib/kudos/compose-options.ts` — one Supabase server client, `Promise.all` of the two reads, map
   to `ComposeOptionsView`, coerce ids with `Number()` once at the boundary.
3. `upload-kudos-image.ts` — `"use server"` on line 1. Validate the session, then the file, then
   upload. Derive `ext` from the MIME (never from the filename, which is attacker-controlled), and
   fall back to `bin` if the MIME is unmapped — though an unmapped MIME cannot reach that far,
   because it failed `isAcceptedImageType`.
4. `create-kudos.ts` — `"use server"` on line 1. Follow § Architecture in that exact order. Map the
   function's raised errcodes: the "no session" raise → `{ form: "unknown" }`, the hashtag-count
   raise → `{ hashtag: "required" }` or `"tooMany"`, anything else → `{ form: "unknown" }` with the
   real message logged server-side and **not** returned to the client.
5. `npm run typecheck && npm run lint`.
6. Prove the happy path with no UI. Get a real authed token the same way the suite does, then call
   the RPC directly:
   ```
   TOKEN=$(curl -s -X POST "http://127.0.0.1:54321/auth/v1/signup" \
     -H "apikey: $NEXT_PUBLIC_SUPABASE_ANON_KEY" -H "Content-Type: application/json" \
     -d '{"email":"phase07-'$RANDOM'@example.com","password":"phase07pass"}' | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
   curl -s -X POST "http://127.0.0.1:54321/rest/v1/rpc/create_kudos" \
     -H "apikey: $NEXT_PUBLIC_SUPABASE_ANON_KEY" -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"p_receiver_id":3,"p_campaign":"PHASE07 PROBE","p_message":"{\"blocks\":[]}","p_message_format":"doc","p_is_anonymous":false,"p_anonymous_name":null,"p_hashtag_ids":[1],"p_image_urls":[]}'
   ```
   Expect a numeric kudos id. Then confirm with `psql` that **exactly one** new `sunners` row exists
   for that `auth_user_id`, that its `department_id` is `Unassigned`, and that the `kudos` row carries
   `message_format='doc'`.
7. Prove the double-submit guard: run the same RPC twice with the same token and confirm
   `select count(*) from sunners where auth_user_id = …` is still 1.
8. Prove the forgery refusal: call the RPC with a token, then attempt a **direct**
   `POST /rest/v1/kudos` with `sender_id` set to somebody else's sunner id and that same token —
   must be 401/403 from RLS, never 201.
9. Prove the upload policy: with the same token, `POST` an object to
   `/storage/v1/object/kudos-attachments/{other-uid}/x.png` and confirm refusal; then to
   `/storage/v1/object/kudos-attachments/{own-uid}/x.png` and confirm success and public
   readability.
10. Delete the probe rows and objects with `psql`/`docker exec`. `npx playwright test
    e2e/kudos-live-board.spec.ts --reporter=list` must stay green.

## Todo List

- [x] `validate-compose.ts` pure, zero-dependency, collects all field errors at once (never early-returns)
- [x] `isAcceptedImageType` is the single definition, shared by the action and phase 10
- [x] `compose-options.ts` — one client, `Promise.all`, ids coerced once
- [x] `upload-kudos-image.ts` — `"use server"`, session → MIME → uid-prefixed unique path → public URL
- [x] Extension derived from MIME, never from the uploaded filename
- [x] `create-kudos.ts` — `"use server"`, validate → origin-check URLs → rpc → `redirect` outside every try
- [x] No `revalidatePath`/`refresh()` in this action, with the reason in a comment
- [x] Errors returned as codes; raw database messages logged server-side only
- [x] Steps 6–9 all behave as stated; probes cleaned up
- [x] `npm run typecheck && npm run lint` clean; board suite still green

## Success Criteria

- Step 6 returns a kudos id and provisions exactly one `sunners` row with the `Unassigned` department.
- Step 7 proves the double-submit guard: still one `sunners` row.
- Step 8 proves forgery is refused at the database, not just in the UI.
- Step 9 proves a user cannot write into another user's Storage folder, and that a legitimate object
  is publicly readable.
- `validateCompose({})` returns all four field codes in one object, not the first one.
- `grep -n "service_role" lib/ app/` returns nothing.
- No file exceeds 200 lines; `create-kudos.ts` contains exactly one `redirect` and it is the last
  top-level statement.

## Risk Assessment

| Risk | L×I | Countermeasure |
|---|---|---|
| `redirect()` called inside a `try`, swallowed, and the user sees a "failed" form after a successful write | **High** × High | Structured as validate/rpc/return-or-redirect with the redirect at top level; a code comment cites `mutating-data.md:504`; step 6 exercises the success path |
| The transport divergence from `technical-spec.md § 3.2` (Server Action vs browser client) confuses a reviewer | Med × Med | Stated in § Key Insights 1 with its two reasons; the spec draft is reconciled at promote |
| A client forges an `imageUrls` entry pointing at an attacker host | Med × High | `isOwnStorageUrl` checks origin **and** path prefix; the object could not exist otherwise |
| A renamed `.pdf` reaches `kudos_attachments` | Med × High | The upload action validates MIME before the object exists, so no Storage URL is ever issued for it; the create action then only accepts our own Storage URLs |
| A raised database error leaks internals to the client | Med × Med | Only codes are returned; the message is logged server-side |
| Provisioning races on a genuine double-submit and creates two identities | Med × High | `on conflict (auth_user_id) do nothing` + re-select inside the function's transaction; step 7 tests it |
| `getComposeOptions` grows into a per-keystroke query | Low × Med | Called once from `page.tsx` (phase 12); ALG-001 filters client-side, stated in the file header |
| Orphaned Storage objects accumulate | **High** × Low | Accepted and documented; unreferenced objects are inert. A cleanup job is a separate commission |
| The nine seeded sunners have `auth_user_id NULL`, so the e2e user is always provisioned fresh — a slower first submit | Med × Low | One extra INSERT inside the same transaction; ID-46/47 allows 10s for the navigation |

**Rollback:** delete the four files. Nothing imports them until phase 12, so the app is unaffected;
the migration from phase 03 stays and remains harmless on its own.

## Security Considerations

- **The actor is never a parameter.** `createKudos` takes only the payload, and `ComposePayload` has
  no sender field; the function resolves the sender from `auth.uid()`. Forging a sender is
  unrepresentable in the API and refused by RLS besides (step 8).
- Every rule is enforced twice: TypeScript predicates for the user-facing codes, and the database
  (policies + the function's raises) as the authority. If only one can be right it is the database
  (`docs/system/permissions.md:91`).
- The Supabase `user` object stays inside the actions; only URLs and error codes cross back.
- Storage writes are confined to `{auth.uid()}/…` by policy; the path is built from the session's
  uid, not from anything the client sent.
- File extension comes from the validated MIME, so a filename like `x.png.html` cannot influence the
  stored object's name.
- Only the anon key is used. `.env.example` still carries no `service_role` key and this phase does
  not add one.
- `anonymous_name` is trimmed and length-capped before storage; it is rendered as text by phase 05,
  never as markup.

## Next Steps

Phase 12 imports both actions in `page.tsx` and passes them down as props. Phase 10 imports
`isAcceptedImageType` from `validate-compose.ts` for the client-side half of BR-004 — tell it the
exported name so it does not write a second copy.
