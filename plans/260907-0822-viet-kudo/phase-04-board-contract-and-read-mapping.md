# Phase 04 — Board contract & read mapping

**Track:** B · **Owner:** `implementer` · **Depends:** 01, 03 ·
**Effort:** 2h · **test_policy:** `e2e-red-first`

## Context Links

- [plan.md](plan.md) · [phase-01](phase-01-foundation-and-integration-contract.md) (the doc types) · [phase-03](phase-03-schema-rls-storage-and-image-host.md) (the columns)
- [clarifications.md](clarifications.md) § Rich text (the `'plain'` discriminator is what keeps F004 intact), assumption **A3** (anonymity hides the sender, never the receiver)
- [technical-spec.md](spec/viet-kudo/technical-spec.md) § 4.2 DISC-001
- Files to extend, never rewrite: `lib/kudos/queries.ts:45-64` (the select string + `KudosFeedRow`), `lib/kudos/board-data.ts:87-105` (the card mapping), `lib/kudos/view-model.ts:31-46` (`KudosCardView`)
- F004 precedent: [phase-04](../260906-1945-kudos-live-board/phase-04-typed-data-layer-and-like-action.md)

## Overview

**Priority:** P1 · **Status:** completed.

Teach the shipped read path about three new columns and hand the board two new fields. Producer-only:
this phase populates the contract, and the card keeps ignoring the new fields until phase 05. That is
what keeps the tree compiling at every point.

## Key Insights

1. **The contract additions must be producer-safe.** Adding a *required* field to `KudosCardView`
   breaks compilation only for the producer (`board-data.ts`), which this phase also owns; consumers
   that ignore the field still compile. That ordering — producer and contract in one phase, consumer
   in the next — is the whole reason 04 and 05 are separate.
2. **`sender` must be redacted, not merely hidden.** For `is_anonymous = true` rows the real
   sender's name, department, avatar and badge must never enter the client payload — hiding them in
   the component would still ship them in the RSC flight data. So `board-data.ts` substitutes a
   redacted `SunnerView` (`id: 0`, the anonymous label as `fullName`, empty department, the committed
   sample avatar, `New Hero`, `badgeTooltip: null`) and sets the new `anonymousSenderLabel`. The real
   `row.sender.id` is still used server-side for `canLike`/`isOwnedByViewer` before it is dropped.
3. **`canLike`/`isOwnedByViewer` keep using the real sender id.** An anonymous kudos is still owned by
   its author, and the author still cannot like it (`kudos_likes_insert_own` already forbids that at
   the database). Computing these from the redacted stub would silently invert both.
4. **The label falls back to a neutral string, and that string is data, not copy.** When
   `anonymous_name` is null the label is `"Ẩn danh"`. It is set here rather than in the dictionary
   because it substitutes for a person's *name* — a data value, exactly like `sunners.full_name` —
   and because the card renders it through the same slot. Recorded as an unresolved design question
   (clarifications § Unresolved question 4 covers the field; its neutral fallback is unauthored).
5. **The 57 seeded rows carry `message_format = 'plain'` by column default**, so
   `kudos-body` renders byte-identically and no F004 assertion moves. Verified at phase 03 step 6.
6. **The select string and `KudosFeedRow` must change together.** `queries.ts` pins the embed shape
   with `.returns<KudosFeedRow[]>()`; adding a column to one and not the other type-checks but
   returns `undefined` at runtime.
7. **Regenerate, never hand-edit, `database.types.ts`.** `npm run db:types` is the only path
   (`package.json`), and phase 03's migration must be applied first or the new columns are absent
   from the output.

## Requirements

**Functional:** DISC-001 (the `message_format` discriminator reaches the view model), A3 (anonymity
data reaches the card), FR-207/BR-004 unchanged, every F004 behavior preserved bit for bit for
`'plain'`, non-anonymous rows.

**Non-functional:** each file ≤200 lines (`board-data.ts` is at 180 — if the redaction pushes it
over, extract `toAnonymousSenderView` into the same file's top section rather than splitting the
module); still **one** board read per request, no new query; `bigint` ids coerced with `Number()` at
the mapping boundary only; no `any`; the generated type file is committed.

## Architecture

```
lib/kudos/view-model.ts        (additive only)
  KudosCardView
    + messageFormat: MessageFormat            // "plain" | "doc", from compose-contract.ts
    + anonymousSenderLabel: string | null     // non-null ⇒ card renders the anonymous chip

lib/kudos/queries.ts
  fetchKudos select  … id, campaign, message, sent_at, heart_baseline,
                        message_format, is_anonymous, anonymous_name, …
  interface KudosFeedRow  + message_format: string
                          + is_anonymous: boolean
                          + anonymous_name: string | null

lib/kudos/board-data.ts
  const ANONYMOUS_FALLBACK_LABEL = "Ẩn danh";
  toAnonymousSenderView(label)  → SunnerView { id: 0, fullName: label, department: "",
                                   avatarUrl: "/images/kudos/sample-avatar.png",
                                   badge: "New Hero", badgeTooltip: null }

  rows.map(row => {
    const label = row.is_anonymous ? (row.anonymous_name?.trim() || ANONYMOUS_FALLBACK_LABEL) : null;
    return {
      …unchanged fields,
      messageFormat: row.message_format === "doc" ? "doc" : "plain",   // narrow, never cast
      anonymousSenderLabel: label,
      sender: label === null
        ? toSunnerView(row.sender, receivedCountBySunnerId.get(row.sender.id) ?? 0)
        : toAnonymousSenderView(label),
      canLike:        viewer.isAuthenticated && viewer.sunnerId !== row.sender.id,   // real id
      isOwnedByViewer: viewer.sunnerId !== null && viewer.sunnerId === row.sender.id, // real id
    };
  })
```

**Received counts:** an anonymous kudos still increments its **receiver's** received count (A3 —
anonymity protects the giver). The existing `receivedCountBySunnerId` loop keys on `row.receiver.id`
and needs no change. The redacted sender's `id: 0` never enters that map.

## Related Code Files

**Modify:** `lib/kudos/view-model.ts` · `lib/kudos/queries.ts` · `lib/kudos/board-data.ts`
**Generate + commit:** `lib/supabase/database.types.ts`
**Create:** none · **Delete:** none
**Read only:** `lib/kudos/compose-contract.ts` (frozen), `lib/kudos/derive.ts` (frozen),
`app/kudos/_components/kudos-card.tsx` (phase 05 owns it)

## Implementation Steps

1. Confirm phase 03's migration is applied (`docker exec supabase_db_my-app psql -U postgres -d
   postgres -c "\\d public.kudos"` shows the three columns), then `npm run db:types` and commit the
   result. If the columns are missing, stop — the migration is not applied and everything after this
   step would be built on a stale type file.
2. `view-model.ts` — add the two fields to `KudosCardView`, importing `MessageFormat` as a type from
   `compose-contract.ts`. Extend the file's frozen-contract header with one sentence naming this
   phase and why the fields are additive.
3. `queries.ts` — add the three columns to the `fetchKudos` select string **and** the matching three
   fields to `KudosFeedRow`. Change nothing else about the query: same `.order("sent_at", {
   ascending: false })`, same FK hints, same `likes:kudos_likes(count)`.
4. `board-data.ts` — add `ANONYMOUS_FALLBACK_LABEL` and `toAnonymousSenderView`, then extend the
   `rows.map` exactly as § Architecture shows. Narrow `message_format` with a comparison, never a
   cast: an unexpected value degrades to `'plain'`, which renders the raw string as text — safe by
   construction.
5. `npm run typecheck && npm run lint`.
6. Prove the read path against real data without any UI. Insert one `'doc'` anonymous row directly,
   then read it back through PostgREST:
   ```
   docker exec supabase_db_my-app psql -U postgres -d postgres -c \
     "insert into kudos (sender_id, receiver_id, campaign, message, message_format, is_anonymous, anonymous_name, sent_at)
      select s.id, r.id, 'PHASE04 PROBE',
             '{\"blocks\":[{\"type\":\"paragraph\",\"runs\":[{\"type\":\"text\",\"text\":\"probe\",\"bold\":true}]}]}',
             'doc', true, 'Người bí ẩn', now()
      from sunners s, sunners r where s.id <> r.id limit 1;"
   curl -s "http://127.0.0.1:54321/rest/v1/kudos?select=id,message_format,is_anonymous,anonymous_name&campaign=eq.PHASE04%20PROBE" \
     -H "apikey: $NEXT_PUBLIC_SUPABASE_ANON_KEY"
   ```
   Then load `/kudos` in the browser and confirm the probe card shows `Người bí ẩn` where the sender
   chip's name goes, the receiver's real name unchanged, and the body still readable (it renders as
   raw JSON at this phase — phase 05 is what makes it pretty; that is expected here and must be
   stated in the handoff, not "fixed" by casting).
7. Delete the probe row (`delete from kudos where campaign = 'PHASE04 PROBE';` via `psql`, which is
   superuser and unaffected by the missing DELETE policy) and re-run
   `npx playwright test e2e/kudos-live-board.spec.ts --reporter=list` — must be green.

## Todo List

- [x] Migration confirmed applied, `npm run db:types` regenerated and committed with the 3 columns
- [x] `KudosCardView` gains `messageFormat` + `anonymousSenderLabel`, header updated
- [x] `queries.ts` select string and `KudosFeedRow` both extended; nothing else in the query changed
- [x] `board-data.ts` redacts the sender for anonymous rows and keeps the real id for `canLike`/`isOwnedByViewer`
- [x] `message_format` narrowed by comparison, never cast
- [x] `board-data.ts` still ≤200 lines
- [x] `npm run typecheck && npm run lint` clean
- [x] Step 6 probe: anonymous label renders, receiver unaffected
- [x] Probe deleted; `kudos-live-board.spec.ts` green

## Success Criteria

- `getKudosBoard()` satisfies the extended `KudosBoardViewModel` with no cast and no `any`.
- For every seeded row: `messageFormat === "plain"`, `anonymousSenderLabel === null`, and the mapped
  `sender` is identical to what shipped before this phase.
- For the step-6 probe: `anonymousSenderLabel === "Người bí ẩn"`, the mapped `sender.fullName` is that
  label, `sender.id === 0`, and the response payload contains **no trace** of the real sender's name.
- `canLike` for the probe is still computed from the real sender, so the author cannot like it.
- `e2e/kudos-live-board.spec.ts` green before and after.

## Risk Assessment

| Risk | L×I | Countermeasure |
|---|---|---|
| The real sender's identity leaks into the client payload for an anonymous kudos | Med × **High** | Redaction happens in the mapping, server-side, before the view model exists; success criteria inspects the payload for the real name |
| `canLike`/`isOwnedByViewer` accidentally computed from the redacted `id: 0`, letting an author like their own anonymous kudos | Med × High | Both lines read `row.sender.id` explicitly and are called out in § Architecture; RLS refuses it anyway as the second layer |
| Select string extended but `KudosFeedRow` not, so fields silently arrive `undefined` | Med × High | Step 3 changes both in one edit; step 6 reads the probe values back through the real query |
| `db:types` run before the migration is applied, so the new columns are missing and later phases build on a stale file | Med × High | Step 1 refuses to proceed until `\d public.kudos` shows them |
| `board-data.ts` crosses 200 lines | Med × Low | The helper stays in-file at the top; if it still overflows, `toAnonymousSenderView` moves to `derive.ts`-style pure code — but only with the orchestrator's sign-off, since `derive.ts` is frozen |
| A future migration adds a third `message_format` value and the narrowing silently degrades it to `'plain'` | Low × Low | The `check` constraint in phase 03 makes a third value impossible without a migration that would also touch this mapping |

**Rollback:** revert the three source files and regenerate the type file from the pre-phase-03
schema. Nothing consumes the new fields yet, so the board returns to its shipped behavior exactly.

## Security Considerations

- Anonymity is enforced at the **mapping** boundary, which is the last point where the real identity
  legitimately exists. Anything downstream is a client payload and must not carry it.
- `sunners.auth_user_id` remains unmapped — `SunnerView` has no field for it and none is added.
- Only the anon key is used, via `lib/supabase/server.ts`; no `service_role` anywhere.
- The redacted avatar is the committed placeholder already shipped for F004, not a remote URL, so
  anonymity cannot leak through an avatar path.
- `message_format` is narrowed rather than cast, so a hostile column value cannot route content into
  the doc renderer.

## Next Steps

05 consumes `messageFormat` and `anonymousSenderLabel`; 07 writes rows that exercise both. Hand 05 a
one-line note that a `'doc'` row currently renders as raw JSON on the board — that is this phase's
intended, temporary state and 05's first job.
