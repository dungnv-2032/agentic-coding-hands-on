# Phase 04 — Typed data layer & like action

**Track:** B (behavior/backend) · **Owner:** `implementer` · **Depends:** 03 ·
**Effort:** 2h · **test_policy:** `e2e-red-first`

## Context Links

- [plan.md](plan.md) · [phase-01](phase-01-foundation-and-integration-contract.md) (the contract this phase must satisfy) · [phase-02](phase-02-kudos-schema-and-rls.md) · [phase-03](phase-03-seed-from-frame-corpus.md)
- [technical-spec.md § 3.2 A2](spec/kudos-live-board/technical-spec.md) (the action), § 4.4 BR-001/BR-003, § 5.1 SC-003/SC-004
- [test-contract.md](test-contract.md) § "Supabase amendment" — K-24, K-25
- [Supabase study](../reports/researcher-260906-1958-supabase-data-layer.md) § 4 (generated types), § 5 (server reads, `cookies()` already async), § 6 (anon vs authed)
- Patterns to copy: `lib/supabase/server.ts:10-34`, `app/_page-context.ts:27-42`, `app/_actions/auth.ts:1-21`
- Next 16.3.4 docs read for this phase: `node_modules/next/dist/docs/01-app/03-api-reference/04-functions/refresh.md`, `.../revalidatePath.md`, `.../cookies.md`

## Overview

**Priority:** P1 · **Status:** delivered.

Turns the seeded tables into the frozen view model, and adds the one write path on the screen.
Four small modules plus the generated type file. This is the phase that makes `KudosBoardViewModel`
real; phase 09 only wires it into a page.

## Key Insights

1. **`refresh()`, not `revalidatePath()`.** `/kudos` reads `cookies()` (via `getPageContext()` and
   the Supabase server client), which opts the route into dynamic rendering — there is no cache
   entry to invalidate (`cookies.md:69`, study § 5, and `next.config.ts` does not set
   `cacheComponents`). `refresh()` from `next/cache` is the Next 16 API for refreshing the client
   router from inside a Server Action, and it is exported by this exact build (verified against
   `node_modules/next/cache.d.ts`). Calling it inside the action means the action's response
   carries the re-rendered tree, so the client transition ends on fresh server data instead of
   flashing back through a reverted optimistic value.
2. **Identity is auth-only; the sidebar's fallback is display-only.** `viewer.sunnerId` resolves
   solely through `sunners.auth_user_id = user.id` and stays `null` when there is no such row.
   The sidebar separately resolves *which* sunner's counters to show, falling back to the seeded
   frame viewer (`auth_user_id is null`). Two functions, two names, never merged — merging them
   would disable the top card's heart for the e2e user and hollow out K-25 (see phase 01 § Key
   Insight 2).
3. **PostgREST needs FK hints for the two `sunners` joins**, which is why phase 02 named the
   constraints: `sender:sunners!kudos_sender_id_fkey(...)`, `receiver:sunners!kudos_receiver_id_fkey(...)`.
   Without the hint the embed is ambiguous and the request errors.
4. **Heart counts come back as an aggregate, not a row list.** `likes:kudos_likes(count)` gives the
   count per kudos in the same round trip; the viewer's own likes are one extra query
   (`from("kudos_likes").select("kudos_id").eq("user_id", uid)`), so the response never carries
   other people's user ids into the payload.
5. **Badge tier and displayed hearts are derived, never stored.** `badgeTierFor(kudos_received_baseline + receivedCount)`
   and `heart_baseline + likeCount` (BR-001). Both helpers already exist frozen in
   `lib/kudos/derive.ts`; this phase calls them and must not reimplement either.
6. **The action derives `user_id` from the session, never from an argument.** Its only parameter is
   `kudosId`. A client-supplied user id would be trivially forgeable, and RLS would reject it
   anyway — but the action must not offer the shape at all.
7. **A double click races the unique constraint.** Catch Postgres `23505` on insert and treat it as
   already-liked rather than surfacing an error; then read the count back so the returned value is
   the database's, not an assumption (`technical-spec.md § 3.6`).

## Requirements

**Functional:** FR-002, FR-207 + BR-004 (sidebar counts, anon fallback), FR-401 (a like persists),
FR-601 (anon reads everything), FR-602 + BR-003 (`canLike` false with no session or when the viewer
is the sender), BR-001, BR-002, SM-001, DEC-003, ALG-001 (via `pickHighlight`).

**Non-functional:** each file ≤200 lines; one board read per request (no N+1 — one kudos query with
embeds, one viewer-likes query, one sidebar query, one gifts query, one ticker query); the
generated type file is committed so `npm run build` never needs a live database; no `any`; the
Supabase `user` object never leaves the server (`app/_page-context.ts:22-25`).

## Architecture

```
GET /kudos ─▶ board-data.getKudosBoard()
                ├─ viewer.resolveViewer()      → { isAuthenticated, sunnerId }      (auth only)
                ├─ queries.fetchKudos()        → kudos + sender/receiver + hashtags
                │                                 + attachments + likes(count)
                ├─ queries.fetchViewerLikes()  → Set<kudosId>                       (authed only)
                ├─ queries.fetchFilterOptions()→ 13 hashtags, 50 departments (ordered)
                ├─ queries.fetchSidebar()      → counts (identity sunner ?? seeded viewer) + gifts
                └─ queries.fetchSpotlight()    → 7 nodes + 6 ticker rows
                        ▼
                KudosBoardViewModel  ──▶ (phase 09) app/kudos/page.tsx ──▶ Track A components

click heart ─▶ toggleKudosLike(kudosId)  "use server"
                ├─ resolveViewer(); no session → throw (RLS would refuse anyway)
                ├─ select existing like → delete it, or insert one (23505 ⇒ already liked)
                ├─ re-read heart_baseline + count → KudosLikeResult
                └─ refresh()
```

**Module split (200-line cap, one job each):**

| File | Job |
|---|---|
| `lib/supabase/database.types.ts` | generated, committed, never hand-edited |
| `lib/kudos/viewer.ts` | `resolveViewer()` (identity) and `resolveSidebarSunnerId()` (display fallback) — the two notions, kept apart by file |
| `lib/kudos/queries.ts` | the five typed reads; returns row shapes, no view-model assembly |
| `lib/kudos/board-data.ts` | `getKudosBoard(): Promise<KudosBoardViewModel>` — assembles rows into the contract using `derive.ts` |
| `app/kudos/_actions/toggle-kudos-like.ts` | `"use server"`, satisfies `ToggleKudosLike` |

**Ordering:** each row maps to `KudosCardView` with `hashtags` sorted by `kudos_hashtags.position`,
`attachments` by `position`, the feed by `sent_at desc`, filter options by `position` /
`filter_position` (K-3 compares text in order), and gifts by `awarded_at desc limit 10`.

## Related Code Files

**Create:** `lib/kudos/viewer.ts` · `lib/kudos/queries.ts` · `lib/kudos/board-data.ts` ·
`app/kudos/_actions/toggle-kudos-like.ts`
**Generate + commit:** `lib/supabase/database.types.ts`
**Modify:** none
**Read only:** `lib/kudos/view-model.ts`, `lib/kudos/derive.ts` (frozen), `lib/supabase/server.ts`,
`app/_page-context.ts`
**Delete:** none

## Implementation Steps

1. `npm run db:types` → `lib/supabase/database.types.ts`. Commit it. If it comes back empty or
   without the nine tables, the migration is not applied: re-run `npx supabase db reset` (phase 02
   § Risk covers the PostgREST cache case).
2. `lib/kudos/viewer.ts`:
   - `resolveViewer()` — one `supabase.auth.getUser()`; on a user, look up
     `sunners.id where auth_user_id = user.id` (`maybeSingle()`); return
     `{ isAuthenticated, sunnerId }`. Return only those two fields; the `user` object stays here.
   - `resolveSidebarSunnerId(identitySunnerId)` — the identity id when present, else the seeded
     viewer's id (`auth_user_id is null`).
3. `lib/kudos/queries.ts` — the five reads from § Architecture, each a named exported function
   taking the client as an argument so `board-data.ts` creates it once per request.
4. `lib/kudos/board-data.ts` — `getKudosBoard()`: create the client once, run the independent
   reads with `Promise.all` (the pattern at `app/_page-context.ts:28`), then map into the contract:
   - `hearts = heart_baseline + likeCount` (BR-001)
   - `likedByViewer = viewerLikes.has(id)`
   - `canLike = isAuthenticated && sunnerId !== sender.id`
   - `isOwnedByViewer = sunnerId !== null && sunnerId === sender.id`
   - `badge = badgeTierFor(kudos_received_baseline + receivedCount)`, `badgeTooltip = badgeTooltipFor(badge)`
   - `sentAtLabel = formatSentAt(sent_at)`
   Coerce every id with `Number()` at this boundary.
5. `app/kudos/_actions/toggle-kudos-like.ts` — `"use server"` first line; signature
   `toggleKudosLike(kudosId: number): Promise<KudosLikeResult>`; validate `Number.isInteger(kudosId) && kudosId > 0`;
   resolve the session; select the existing like; delete or insert; catch `23505` as already-liked;
   re-read the count; `refresh()`; return `{ liked, hearts }`.
6. `npm run typecheck && npm run lint`.
7. Prove the read path without any UI — a throwaway `node`/`tsx` call is not available here, so
   verify at the database level instead: run the same select through PostgREST and confirm the
   embeds resolve:
   ```
   curl -s "http://127.0.0.1:54321/rest/v1/kudos?select=id,heart_baseline,sender:sunners!kudos_sender_id_fkey(full_name),receiver:sunners!kudos_receiver_id_fkey(full_name),likes:kudos_likes(count)&limit=1" \
     -H "apikey: $NEXT_PUBLIC_SUPABASE_ANON_KEY"
   ```
   A 200 with nested `sender`/`receiver`/`likes` proves the FK hints and the anon read policy. A
   `300`/`PGRST201` means the FK hint is wrong.
8. Confirm the anon write refusal through the API as well: a `POST /rest/v1/kudos_likes` with the
   anon key must return 401/403, never 201 (SC-004's DB-layer half).

## Todo List

- [ ] `npm run db:types` run and `lib/supabase/database.types.ts` committed with nine tables
- [ ] `viewer.ts` — identity and sidebar fallback as two separate functions
- [ ] `queries.ts` — five reads, FK hints on both `sunners` embeds, `likes:kudos_likes(count)`
- [ ] `board-data.ts` — assembles `KudosBoardViewModel`, calls `derive.ts` (does not reimplement it)
- [ ] `toggle-kudos-like.ts` — `"use server"`, `kudosId` only, `23505` handled, `refresh()` called
- [ ] `npm run typecheck && npm run lint` clean
- [ ] Step 7 curl returns 200 with nested embeds
- [ ] Step 8 anon insert returns 401/403

## Success Criteria

- `lib/supabase/database.types.ts` is committed and contains all nine tables.
- `getKudosBoard()` returns a value that satisfies `KudosBoardViewModel` with no cast and no `any`.
- 50 cards, 13 hashtag options, 50 department options, 7 spotlight nodes, 6 ticker rows, 10 gift
  rows, and sidebar counts of 25/25/25/25/25 for an anon caller.
- The top card reports `hearts === 1000`, `likedByViewer === false`, and `canLike === false` for
  anon.
- Step 7 and step 8 both behave as stated — reads open, writes refused.
- No kudos e2e assertion changes state yet: nothing renders this data until phase 09.

## Risk Assessment

| Risk | L×I | Countermeasure |
|---|---|---|
| Ambiguous embed (`PGRST201`) on the two `sunners` FKs | **High** × High | Explicit `!constraint` hints, named in phase 02; step 7 fails loudly if wrong |
| `refresh()` absent or renamed in this Next build | Low × High | Verified present in `node_modules/next/cache.d.ts` for 16.3.4 before planning; if it ever disappears, fall back to `revalidatePath("/kudos")` and accept the wider invalidation the doc warns about |
| Optimistic value flashes back before the refreshed tree arrives, making K-10 read a stale attribute | Med × High | `refresh()` is called **inside** the action so the transition resolves with the new tree; phase 07 pairs it with `useOptimistic` inside `startTransition` |
| Sidebar fallback leaks into identity, hollowing out K-25 | Med × **High** | Enforced structurally: two named functions, and `canLike` is computed only from `resolveViewer()`'s `sunnerId` |
| Generated types drift after a later migration | Low × Med | `npm run db:types` is the single regeneration path and the file is never hand-edited |
| Five queries per render become a latency problem | Low × Low | `Promise.all` on the independent reads; the route is dynamic and per-request by design (study § 5) |
| `bigint` ids arriving as strings and breaking `===` comparisons | Med × Med | `Number()` coercion at the mapping boundary in step 4, once, not scattered |

**Rollback:** delete the four created modules and the generated type file. Nothing imports them
until phase 09, so the app is unaffected.

## Security Considerations

- The Supabase `user` object never leaves `viewer.ts`; only `{ isAuthenticated, sunnerId }` travels
  onward, matching the rule at `app/_page-context.ts:22-25` and `architecture.md:107`.
- `toggleKudosLike` takes **no** user identifier. The uid comes from the session; RLS re-checks it
  and also re-checks BR-003, so the UI's disabled state is never the only defence.
- `sunners.auth_user_id` is readable by policy but must not be mapped into `SunnerView` — the
  contract has no field for it, and adding one would put an auth uuid into the client payload.
- Only the anon key is used, through `lib/supabase/server.ts`; no `service_role` key is read,
  stored, or referenced.
- `kudosId` is validated as a positive integer before it reaches a query, so a malformed value
  fails in the action rather than becoming a database round trip.
- The action returns only `{ liked, hearts }` — no row, no user id, no error internals.

## Next Steps

Track B is complete. Phase 09 consumes `getKudosBoard()` and `toggleKudosLike`. If Track A is still
running, nothing here waits on it.
