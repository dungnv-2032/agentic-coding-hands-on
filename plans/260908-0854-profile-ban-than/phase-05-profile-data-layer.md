# Phase 05 — Profile data layer + keyset server action

**Track:** B · **Owner:** `implementer` · **Effort:** 2.5h
**File ownership:** `lib/profile/profile-queries.ts`, `lib/profile/profile-data.ts`,
`app/profile/_actions/fetch-profile-kudos-page.ts`

## Context Links

- Phase 01 (`ProfileViewModel`), phase 03 (`kudos_readable`), phase 04 (`toKudosCardView`)
- `clarifications.md` § "Statistics card (mms_B)", § "Viewer identity", § "Badge collection and hero
  tier", § "Paging", § "Security — the finding that changes the design"
- `spec/F006_ProfileBanThan/technical-spec.md` § 3.1 (A1 BE), § 3.3 (A2), § 4.5 ALG-002, § 4.4
- Prior art: `lib/kudos/board-data.ts` (`Promise.all` shape), `lib/kudos/viewer.ts:resolveViewer`,
  `supabase/migrations/20260907025909_viet_kudo_write_path.sql` (`create_kudos()`'s JWT fallback chain)

## Overview

- **Priority:** P1 — every FR in the 2xx/3xx/4xx/6xx bands reads its data from here.
- **Status:** pending
- Produce `ProfileViewModel` for either face of the route, and serve subsequent KUDOS pages by a real
  keyset cursor with the Sent direction hard-scoped to the calling session.

## Key Insights

1. **PostgREST cannot express SQL row comparison.** The technical spec writes
   `(sent_at, id) < (:cursor.sentAt, :cursor.id)`, which postgrest-js has no syntax for. Measured
   working over HTTP against the view instead:
   `or=(sent_at.lt.<ts>,and(sent_at.eq.<ts>,id.lt.<id>))` with `order=sent_at.desc,id.desc`.
   In postgrest-js: `.or(\`sent_at.lt.${sentAt},and(sent_at.eq.${sentAt},id.lt.${id})\`)`. Same
   semantics, stable across duplicate `sent_at` values (the seed generates many).
2. **Fetch `FEED_PAGE_SIZE + 1` and discard the extra** to derive `hasMore` without a second
   `count(*)`. The extra row never reaches the client.
3. **The Sent direction never accepts a target id.** `callerSunnerId` is resolved from
   `resolveViewer(supabase)` *inside* the action; `targetSunnerId` is ignored entirely when
   `direction === "sent"`. This is the security boundary (FR-601/PERM013) — hiding the dropdown
   option on another Sunner's profile is only the second layer.
4. **`sunnerId: null` is the normal case, not an edge one.** The e2e user signs up fresh every run
   and has no `sunners` row until their first write. So: `direction: "sent"` with
   `callerSunnerId === null` returns an **empty page, not an error**; and the self view renders from
   the JWT (A4/BR-001).
5. **The JWT fallback chain must be copied from `create_kudos()`, not reinvented:**
   `user_metadata.full_name` → `user_metadata.name` → the email **local-part**; and
   `user_metadata.avatar_url` → `picture` → `/images/kudos/sample-avatar.png`. The local-part is
   deliberate: it is the same value a write would have stored, and it is not an address, so SEC_004
   ("no email address in the payload") still holds. `resolveViewer()` deliberately keeps the Supabase
   `User` object inside `viewer.ts`, so this phase adds its own narrow reader in `lib/profile/` and
   **does not modify `viewer.ts`**.
6. **The hero pill is hidden at 0 received, not rendered as "New Hero".** `badgeTierFor(0)` returns
   `"New Hero"`, so `hero.badge` must be set to `null` by *this* layer when received == 0
   (SCR006 § 7, GUI_009). `badgeTierFor` itself is reused untouched — one function, one rule (BR-002).
7. **There are no hoa-thị stars.** AMEND-1 retired them and assumption A2 with them; no
   `starCountFor`, no star field on the contract.
8. **Counters follow F004's shipped idiom exactly** so the board and the profile can never disagree:
   received = `sunners.kudos_received_baseline + count(received rows)`; sent = `count(sent rows)`
   (there is no sent baseline column); hearts received = `sum(heart_baseline + like count)` over the
   received rows. Secret Box reads the two real columns — measured `0/0` for 14 sunners and `25/25`
   for the frame viewer, so the e2e viewer shows a genuine `0`/`0` with no hardcoded number.

## Requirements

Functional: FR-203, FR-204, FR-206 (the two counts), FR-401/FR-402 support (the `notFound()`
decision is taken in phase 09 using phase 06's resolver; this layer signals "no such sunner"),
FR-403, FR-404, FR-601, FR-602, FR-603, BR-001, BR-002, BR-003, BR-004, SM-001's server half.

Non-functional: independent reads run under one `Promise.all`, one Supabase client per request
(`board-data.ts`'s shape); each file < 200 lines; no client-reachable server import.

## Architecture

```
app/profile/page.tsx (phase 09)
  └─ getProfileData(targetId | null, viewer) ──► ProfileViewModel
       Promise.all
         ├─ fetchProfileSunner(targetId)            sunners: id, full_name, avatar_url,
         │                                          department:departments(name),
         │                                          kudos_received_baseline,
         │                                          secret_box_opened_count, secret_box_unopened_count
         ├─ fetchReceivedAggregate(targetId)        kudos_readable: heart_baseline, likes(count)
         │                                          where receiver_id = target      → received, hearts
         ├─ fetchSentCount(callerSunnerId)          kudos_readable head+count where sender_id = caller
         │                                          (self face only; else null)
         └─ fetchProfileKudosPage(target,"received",null)   page 1, keyset

KudosDirectionSection (client, phase 08)
  └─ fetchProfileKudosPage(...)  "use server"  ──► ProfileFeedPage
       direction=received → where receiver_id = targetSunnerId
       direction=sent     → where sender_id  = resolveViewer().sunnerId   (target id IGNORED)
       both               → order sent_at.desc,id.desc · limit 11 · or(...) keyset
       rows → toKudosCardView(..., { revealOwnAnonymous: direction === "sent" })
```

**Data flow:** every Kudos read goes through `kudos_readable`; every `sunners` read selects only the
allowed profile columns. `stats` is computed **once**, here, and is `null` for anyone but the caller
— no component re-tests "is this my profile" (SC-002).

## Related Code Files

Create:
- `lib/profile/profile-queries.ts` — typed reads against `sunners` and `kudos_readable`, returning
  raw row shapes only (mirrors `lib/kudos/queries.ts`'s role).
- `lib/profile/profile-data.ts` — `getProfileData()`, the JWT fallback reader, count derivation,
  assembly of the frozen `ProfileViewModel`.
- `app/profile/_actions/fetch-profile-kudos-page.ts` — `"use server"`, the A2 action.

Modify: none. **Do not touch** `lib/kudos/viewer.ts`, `lib/kudos/derive.ts`,
`app/kudos/_actions/toggle-kudos-like.ts`.

## Implementation Steps

1. `profile-queries.ts`: `fetchProfileSunner(supabase, id)` selecting **only**
   `id, full_name, avatar_url, kudos_received_baseline, secret_box_opened_count,
   secret_box_unopened_count, department:departments(name)`. Return `null` (not throw) when no row
   matches — `notFound()` is the caller's decision.
2. `profile-queries.ts`: `fetchReceivedAggregate(supabase, sunnerId)` → `{ count, hearts }` from
   `kudos_readable` filtered on `receiver_id`, selecting `heart_baseline, likes:kudos_likes(count)`.
3. `profile-queries.ts`: `fetchSentCount(supabase, sunnerId)` → `{ count: 'exact', head: true }`
   on `kudos_readable` filtered on `sender_id`.
4. `profile-queries.ts`: `fetchKudosPage(supabase, { column, sunnerId, cursor })` — the shared
   keyset read. `column` is `"receiver_id" | "sender_id"`, chosen by the caller, never by a client
   string. `limit(FEED_PAGE_SIZE + 1)`, `.order("sent_at",{ascending:false}).order("id",{ascending:false})`,
   and the `.or(...)` cursor predicate from Key Insight 1. Reuse `FEED_PAGE_SIZE` from
   `lib/kudos/derive.ts` — do not redeclare 10.
5. `profile-data.ts`: `readJwtIdentityFallback(supabase)` → `{ fullName, avatarUrl }` only. It calls
   `supabase.auth.getUser()` and lets **nothing else** out of the function.
6. `profile-data.ts`: `getProfileData(targetId, viewer)`:
   - `targetId === null` (sparse self) → hero from the JWT fallback, `department: null`,
     `badge: null`, `stats` all zeros, `counts: { received: 0, sent: 0 }`, empty `initialPage`.
     **No write of any kind** — a GET must not provision a `sunners` row.
   - otherwise read; `null` row → return a sentinel the page turns into `notFound()`.
   - `isSelf = targetId === viewer.sunnerId`; `stats` non-null iff `isSelf`;
     `writeKudoTargetId` non-null iff not `isSelf`; `counts.sent` null iff not `isSelf`.
   - `hero.badge = received > 0 ? badgeTierFor(received) : null`, `badgeTooltip` from
     `badgeTooltipFor` when badge is non-null.
7. `fetch-profile-kudos-page.ts`: validate `direction` against the two literals and `cursor`'s two
   fields (`Number.isInteger(id)`, ISO-parsable `sentAt`) before any query; malformed input returns
   an empty page rather than throwing. Resolve `callerSunnerId` from the session. Map rows with
   `revealOwnAnonymous: direction === "sent"`.
8. `npm run typecheck`, `npm run lint`, `wc -l` all three files (< 200 each).
9. Prove SC-003 by hand: call the action twice in one session with two different `targetSunnerId`
   values and `direction: "sent"`, and diff the two responses — they must be identical.

## Todo List

- [ ] `profile-queries.ts` selects only the allowed `sunners` columns
- [ ] Keyset uses the measured `.or(sent_at.lt…,and(sent_at.eq…,id.lt…))` form, not row comparison
- [ ] `FEED_PAGE_SIZE + 1` read; extra row dropped before returning
- [ ] `direction: "sent"` ignores `targetSunnerId` and reads the session
- [ ] `callerSunnerId === null` + `sent` → empty page, no error
- [ ] JWT fallback chain matches `create_kudos()` verbatim, incl. email local-part
- [ ] `hero.badge === null` when received == 0
- [ ] `badgeTierFor` / `badgeTooltipFor` / `FEED_PAGE_SIZE` reused, not reimplemented
- [ ] `stats !== null` iff `isSelf`; `counts.sent === null` iff not `isSelf`
- [ ] No write on any read path
- [ ] SC-003 verified by hand and recorded in `evidence/`
- [ ] All three files < 200 lines; typecheck + lint exit 0

## Success Criteria

- `getProfileData(null, {sunnerId: null, isAuthenticated: true})` returns a complete model: name and
  avatar present, `department: null`, `badge: null`, all five stats `0`, `initialPage.cards` empty.
- `getProfileData(1, …)` returns `counts.received === 25 + baseline` and Secret Box `25/25`
  (measured seed values), and `stats === null` when the viewer is not sunner 1.
- Two calls with `direction: "sent"` and different `targetSunnerId` return identical payloads.
- Paging across a 25-row feed yields no duplicate and no skipped `id` (assert the union of three
  pages has 25 distinct ids), and the last page reports `hasMore === false`.
- `grep -rn "auth_user_id\|\.email\b" lib/profile app/profile/_actions` shows the email touched in
  exactly one place — the local-part fallback — and `auth_user_id` nowhere.
- `grep -rn "from(\"kudos\")" lib/profile` → nothing.

## Risk Assessment

| Risk | L×I | Countermeasure |
|---|---|---|
| Implementer translates the spec's row comparison literally, gets a postgrest syntax error, then "simplifies" to `sent_at.lt` alone and silently drops rows sharing a timestamp | M × **H** | Key Insight 1 gives the exact measured predicate; the no-duplicate/no-skip criterion catches the degraded form (the seed has many equal `sent_at` values) |
| `direction: "sent"` scoped by `targetSunnerId` → cross-user disclosure | L × **H** | The `column` argument is chosen server-side; SC-003 is a release-blocking manual proof; phase 02's SEC_003 test also probes it |
| A GET provisions a `sunners` row to "fix" the sparse view | L × H | BR-001 states it explicitly; success criterion asserts the sparse model without a row |
| Hero shows "New Hero" on a 0-Kudos profile | M × M | `badge: null` rule is a checklist item and a phase-02 assertion |
| Heart aggregation drifts from the board's number | M × M | Same formula, same helper, same `heart_baseline + likes` expression as `map-kudos-card.ts` |
| Reading all received rows to sum hearts scales badly | M × L | Same read profile F004 already has (ADV-1); 25 rows today. Recorded, not fixed here |

**Rollback.** These three files are net-new and referenced only by phase 09; deleting them plus
phase 09's page reverts the feature with the security migration intact.

## Security Considerations

- FR-603: no `auth_user_id`, no email address, no `userId` in any returned shape. The only email
  touch is `split("@")[0]`.
- FR-601/PERM013: the Sent boundary is a server-side `WHERE`, from the session. A hand-rolled request
  cannot widen it.
- The masked view is trusted, not re-implemented: a `null` `sender_full_name` means anonymous, and
  the layer must not attempt any second lookup to recover it.
- `fetch-profile-kudos-page.ts` is a server action, i.e. a public POST endpoint. Every field of its
  input is validated before use, and no field of it selects a table or a column name.

## Next Steps

- Blocks phase 09.
- Depends on 01, 03, 04.
