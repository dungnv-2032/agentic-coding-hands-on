# Reviewer Inspection — Viết Kudo compose screen (F005)

**Scope:** RLS/write path, XSS renderer, route guard, sender provisioning, server validation,
F004 regression, test integrity, repo conventions. Depth: full read + live adversarial DB testing
(not just reading the migration text).

## Assessment

Solid. This is the repo's first user-facing write and its first auth-guarded route since F001, and
it holds up under live adversarial testing, not just code inspection. `criticalCount: 0`. Three Low
findings, none blocking.

## Critical

None.

## High

None.

## Medium

None.

## Low

1. **File-size boundary.** `compose-form.tsx` and `board-data.ts` land at exactly 200 lines, not
   strictly *under* the repo's 200-line cap. Not a lint/build failure. Fix: trim a few lines if this
   is ever touched again, not worth a standalone pass now.
2. **Image count cap enforced one layer further out than hashtags.** `validateCompose()`
   (`lib/kudos/validate-compose.ts:32`) checks `hashtagIds.length > MAX_HASHTAGS` but has no matching
   check for `imageUrls.length > MAX_IMAGES`. The `create_kudos` SQL function does reject >5 images
   (`array_length(p_image_urls,1) > 5`), so a client bypassing the picker still gets rejected — but
   it surfaces as a generic `{form:"unknown"}` instead of a field-specific error, and it's the only
   place the "re-check every rule in the action" framing isn't literally true (it's re-checked in the
   RPC, not the action). Fix: add the same length check to `validateCompose()` for symmetry.
3. **MIME check trusts the client-declared type.** `upload-kudos-image.ts:61` calls
   `isAcceptedImageType(file.type)`, which reads the browser/attacker-declared `File.type`, not file
   content. An attacker can label arbitrary bytes `image/jpeg` and have them stored+served publicly
   from `kudos-attachments`. Low risk today — the object is served with that declared content-type,
   never executed as HTML/JS, and `next/image` only ever consumes it as an `<img>` source — but worth
   a magic-byte sniff if the bucket's threat model grows (e.g. if it's ever linked to for download).

## Security of the write path — verified live, not from migration text

Ran adversarial SQL directly against the Supabase container (`docker exec supabase_db_my-app psql`),
not just read the migration:

- `set local role anon; insert into kudos (...)` → `ERROR: new row violates row-level security
  policy for table "kudos"`. Anon cannot write, full stop.
- `set local role authenticated` with a JWT for an unrelated uid, `sender_id=1` (someone else's row)
  → same RLS violation. Forging a sender by direct table insert is impossible.
- `anon` calling the `create_kudos` RPC → `ERROR: create_kudos requires an authenticated session`
  (checked inside the function via `auth.uid() is null`, and `anon` has no `EXECUTE` grant on the
  function at all — belt and suspenders).
- `create_kudos` takes **no `sender_id` parameter** — the actor is resolved from `auth.uid()` inside
  the function body. A forged sender isn't merely rejected, it's unrepresentable in the RPC's own
  signature. This is a stronger property than most write paths get.
- `prosecdef = f` confirmed live: `create_kudos` is genuinely `security invoker`, so every RLS policy
  above still applies inside the function — it does not bypass RLS, it just gives the multi-table
  write (`kudos` + `kudos_hashtags` + `kudos_attachments`) one transaction to run in. `security
  definer` here would have been a real privilege-escalation hole (the function could then write as
  the function owner regardless of caller identity) — the choice is correct.
- Live `pg_policies` confirms exactly 4 INSERT policies and 4 SELECT policies on the four tables, and
  **no UPDATE/DELETE policy anywhere** — silence is deny, matching the stated intent (editing/deleting
  a Kudos is a separate, unbuilt commission).
- Sender auto-provisioning: created a throwaway `auth.users` row, called `create_kudos` twice under
  that identity in one session — exactly one `sunners` row resulted (`on conflict (auth_user_id) do
  nothing`), with `full_name`/`avatar_url`/`department_id` resolving to the documented fallbacks
  (`Unassigned` department, `sample-avatar.png`). Idempotent under double-submit, as claimed.
- Storage bucket policies: insert requires `(storage.foldername(name))[1] = auth.uid()::text` (one
  user cannot write into another's folder), read is public (matches the public board's needs), no
  update/delete policy on `storage.objects` either.
- **The broad `anon`/`authenticated` table GRANTs** (INSERT/UPDATE/DELETE/TRUNCATE all present in
  `information_schema.role_table_grants`) look alarming in isolation but are the standard Supabase-CLI
  scaffold default privileges applied schema-wide, not something this migration introduced — RLS is
  the actual gate, and it holds as shown above.

## XSS in the rich-text renderer — verified

`kudos-message-body.tsx` never touches `dangerouslySetInnerHTML`; it walks `parseKudosDoc`'s output
into `<span>`/`<strong>`/`<em>`/`<s>`/`<a>` React elements. `parseKudosDoc` (`lib/kudos/rich-text.ts`)
rejects malformed JSON, unknown block/run `type` values, and non-allow-listed link schemes by
returning `null` — confirmed by reading the parser, not the report's prose. A `null` parse degrades to
the plain-text render. The link scheme allow-list (`http:`/`https:`/`mailto:`) is checked **twice**
independently — once in the parser, once again at render time in `kudos-message-body.tsx`'s
`isAllowedLinkHref` — so even a hand-built object that skipped the parser still cannot emit an unsafe
`href`. `javascript:`/`data:`/`vbscript:` cannot survive either check (`new URL(href).protocol`
rejects them against the allow-list).

## Route guard blast radius — verified

`proxy.ts`'s `isGuarded` is `pathname === "/kudos/new" || pathname.startsWith("/kudos/new/")` — an
exact match plus subpath, never a bare `startsWith("/kudos")`. This cannot catch `/kudos`,
`/kudos/[id]`, or `/kudos/secret-box`.

## F004 regression — verified

Live-queried the 57 seeded rows: `message_format='plain'` and `is_anonymous=false` for all 57.
`kudos-card.tsx`'s uncommitted diff is purely additive — a conditional `AnonymousSenderChip` swap-in
and `KudosMessageBody` wrapping the exact same `<p data-testid="kudos-body">` markup with the same
className, so the plain/non-anonymous render path is genuinely unchanged.

## Test integrity — spot-checked

No `.skip`/`.fixme`/`xit`/`xdescribe` in `viet-kudo.spec.ts` or `route-guard.spec.ts`. Every
`toHaveCount` call uses a number, not the broken `async fn` form the ratification describes repairing.
`playwright.config.ts` project `testMatch` patterns for `kudos-authed` and `anon` are mutually
exclusive by construction (negative lookahead on `-authed`) — no file matches two projects.

## Done Well

- Live adversarial verification over trusting the migration's comments (forged sender_id, anon
  writes, anon RPC calls all independently reproduced as rejected).
- `security invoker` + no-`sender_id`-parameter design makes forgery unrepresentable, not merely
  checked.
- Zero-`dangerouslySetInnerHTML` renderer with a double-checked link-scheme allow-list.
- Honest, dated orchestrator rulings in `test-contract.md` for every real ambiguity (submit-disabled
  contradiction, broken `toHaveCount` assertions, K-21 scoping) rather than silent guessing.

## Actions In Order

1. (Optional, low) Add an `imageUrls.length > MAX_IMAGES` check to `validateCompose()` for symmetry
   with the hashtag path and a field-specific error instead of the generic DB fallback.
2. (Optional, low) Trim `compose-form.tsx`/`board-data.ts` a few lines below 200 next time either is
   touched.
3. (Optional, low) Consider content-sniffing image uploads if the Storage bucket's exposure grows.

## Numbers

- Typecheck: 0 errors (repo-wide)
- Lint: 0 errors, 28 pre-existing unrelated warnings
- Full suite: 144 passed / 144, twice consecutively
- RLS: proven live via adversarial `psql`, not read off the migration

## Still Unresolved

None blocking. Worth a human's eyes regardless of this verdict: this migration's INSERT-policy shape
is now the precedent every later write table will copy (per the plan's own blast-radius note) — the
pattern is sound, but it's the kind of precedent worth a second pair of eyes before it propagates.
