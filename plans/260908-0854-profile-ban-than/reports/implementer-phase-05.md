# Phase 05 — Profile data layer + keyset server action — implementer report

## Files touched

| File | Change | Lines |
|---|---|---|
| `lib/profile/profile-queries.ts` | **create** — typed reads against `sunners` and `kudos_readable`, raw row shapes only | 199 |
| `lib/profile/profile-data.ts` | **create** — `getProfileData()`, `buildFeedPage()`, the JWT fallback reader, count derivation | 199 |
| `app/profile/_actions/fetch-profile-kudos-page.ts` | **create** — `"use server"`, the A2 keyset action | 84 |

All three are net-new. `git status --porcelain lib/profile app/profile/_actions` shows exactly
`?? app/profile/_actions/`, `?? lib/profile/profile-data.ts`, `?? lib/profile/profile-queries.ts`
— plus `?? lib/profile/profile-view-model.ts`, which is **phase 01's** still-uncommitted file and
was not touched (byte-identical to what phase 01 left).

Nothing outside the ownership list was touched: no `lib/kudos/**`, no `app/kudos/**`, no
`supabase/**`, no `lib/supabase/database.types.ts`, no `app/profile/_components/**`, no
`app/profile/page.tsx`, no `lib/profile/{profile-view-model,resolve-profile-id}.ts`, no `e2e/**`,
no plan or spec file. `fetchGifts` was left alone (obligation C).

Evidence written this phase:

- `evidence/phase-05-measurements.log` (222 lines) — RED, the 69 checks with real output, the
  no-duplicate-`sent_at` finding, the static criteria, the suite runs, the final database state
- `evidence/phase-05-harness-source.log` (498 lines) — the harness in full, so the numbers are
  reproducible rather than merely reported

## Obligation D first: the database was NOT in seed state, and now is

`npx supabase db reset` was run **before** any measurement — exit 0, all three migrations applied
in order, seed loaded — and the state read back as `kudos=58 anon=1 auth_users=0 linked=0`. Phase
04 was right: F005's compose e2e had left `sunners.id = 10` linked to a real `auth.users` row, so
nothing measured against that database would have been reproducible. Reset again after the
mutating measurements, and a third time after `--project=kudos-authed` (which writes), so phase 09
inherits `kudos=58 anon=1 auth_users=0 linked=0`. Every number in this report comes from a reset
database.

## RED first

The repo has no unit-test runner and adding one is a `package.json` change outside this phase's
ownership. So the RED is the 69 checks written before the three modules existed — 48 seed-state
and 21 mutating — every one of them unrunnable:

```
error TS6053: File 'app/profile/_actions/fetch-profile-kudos-page.ts' not found.
error TS6053: File 'lib/profile/profile-data.ts' not found.
error TS6053: File 'lib/profile/profile-queries.ts' not found.
--- node check-read.js ---
Error: Cannot find module '.../out/lib/profile/profile-queries'
```

Unlike phase 04's pure-function transcript, these checks run the **real compiled modules against
the real local Supabase over HTTP**. Exactly one substitution exists: `@/lib/supabase/server`'s
client factory, whose `cookies()` needs a Next request scope. The action module itself is the real
compiled file, so its validation branches, its `resolveViewer()` call and its server-side column
choice are all genuinely exercised. Sessions are real signups; the SEC_002 author composes through
F005's real `create_kudos()` RPC.

## The three decisions phase 04 handed over

### A. `receivedCountBySunnerId` — queried for the page's Sunners, not built from the page

Phase 04 named the trap: the board tallies received counts over a full-table read, so a map built
from a keyset page understates every badge tier. Both fallbacks it offered are wrong in a way that
ships green — an empty map silently keys every tier off `kudos_received_baseline` alone, which for
sunner 1 (baseline 0, 26 received) renders **New Hero** where the board renders **Super Hero**.

So the route taken is the third one: `fetchReceivedCounts(supabase, sunnerIds)` reads the real
counts for exactly the Sunners appearing on the page — receivers plus non-null senders, so ≤ 21
ids for a ten-card page. What makes it correct is that it is the **same tally over the same source**
as `board-data.ts`: both count rows in `kudos_readable` grouped by `receiver_id`, so for any id in
the set the two numbers are equal by construction, not by coincidence. Measured:
`fetchReceivedCounts([1,2,3])` → `{1: 26, 2: 25, 3: 1}`, matching SQL, and the first card's
receiver badge comes back `Super Hero` (K4e, K5).

One extra read per page, bounded by the page size. Not free, and recorded as ADV-4 below rather
than hidden: it is the same read *profile* F004 already has (ADV-1), and the alternative was wrong
numbers.

### B. `revealOwnAnonymous` now has a measured, end-to-end proof

Phase 04's checks E and F were the one thing in that phase whose regression would be silent. They
are now proven through a real write and a real read, not a fabricated row (M3a–M3g):

A fresh signed-up user composes an anonymous Kudo through `create_kudos()` (which provisions them
as sunner 10), then their own Sent list is read through the **real server action**:

```
own Sent list: 1 card — {"id":71,"sender":{"id":10,"fullName":"phase05-sec002-…",
  "department":"Unassigned","avatarUrl":"/images/kudos/sample-avatar.png","badge":"New Hero",
  "badgeTooltip":null},"anonymousSenderLabel":null,"sentAnonymously":true,
  "canLike":false,"isOwnedByViewer":true}
```

The same row, same code, in receiver 1's Received feed as an anonymous visitor:

```
{"id":71,"sender":{"id":0,"fullName":"Ẩn danh","department":"","avatarUrl":"…","badge":"New Hero",
  "badgeTooltip":null},"anonymousSenderLabel":"Ẩn danh"}
```

- **M3b/M3c** — SEC_002 holds: the author's own anonymous Kudo **is** in their Sent list, named as
  theirs, `anonymousSenderLabel: null`. The measured filter is the bare `sender_id=eq.{me}` phase
  04 specified; there is no `NOT is_anonymous` filter and must not be.
- **M3d** — `sentAnonymously` stays `true` (FR-602, rendered by nothing — AMEND-3).
- **M3e** — `canLike: false`, `isOwnedByViewer: true`: BR-003 survives the reveal.
- **M3f** — the same row is masked for everybody else, and the author's local-part appears nowhere
  in the masked card.
- **M3g** — `revealOwnAnonymous` **off** (the Received face) keeps the mask even for the author, so
  the board's shipped behaviour is untouched.
- **M4** — the caller's own sent **count** includes the anonymous send, so the counter and the list
  agree. This is the under-reporting trap clarifications § "My own Sent list" warns about, closed.

**These are still not a durable test**, and cannot be from this phase: `e2e/**` belongs to phases
02/10. Carried forward as inheritance below — phase 10's `TC_WEB_PROFILE_SEC_002` is the one that
must own it, and as written today it asserts only `expect(feedArea).toBeVisible()`, which passes
whether or not the anonymous card is there.

### C. `fetchGifts` untouched

Left exactly as phase 04 left it. Phase 09's job.

## What was done

### 1. `profile-queries.ts` — five reads, one cursor validator

`fetchProfileSunner` selects exactly the seven columns FR-603 allows and returns `null` rather than
throwing, because `notFound()` is the page's decision. `fetchReceivedAggregate` returns
`{count, hearts}` in one read using the board's exact `heart_baseline + likes` formula.
`fetchSentCount` is head-only. `fetchReceivedCounts` is decision A. `fetchKudosPage` is ALG-002.

### 2. The keyset predicate, and a correction to the phase file's premise

The measured working form is the one the phase file gives:

```ts
.or(`sent_at.lt.${sentAt},and(sent_at.eq.${sentAt},id.lt.${id})`)
```

with `.order("sent_at", {ascending:false}).order("id", {ascending:false}).limit(FEED_PAGE_SIZE + 1)`.

**But Key Insight 1's justification for it is factually wrong, and that matters.** It says the form
is needed because "the seed generates many" duplicate `sent_at` values. Measured on the reset
database:

```
select sent_at, count(*) from public.kudos group by 1 having count(*) > 1;
 sent_at | count
---------+-------
(0 rows)
```

There are **no** duplicate `sent_at` values in the seed at all. The seed walks back in 6-hour
steps, one row per timestamp. So the phase file's own no-duplicate/no-skip success criterion —
"assert the union of three pages has 25 distinct ids" — **passes identically for the degraded
`sent_at.lt`-only form**, and the countermeasure the risk table relies on does not work.

So the tie was constructed deliberately: 12 rows sharing one `sent_at` for receiver 3, straddling
the page-1 boundary, and the degraded predicate run against the same data (M1a–M1e):

```
  inserted 12 rows at a single sent_at for receiver 3; receiver 3 now has 13 rows
  ties: 12 rows share 2025-11-01 12:00:00+00
  page 1: 70,69,68,67,66,65,64,63,62,61  hasMore=true nextCursor={"sentAt":"2025-11-01T12:00:00+00:00","id":61}
  page 2: 60,59,51                        hasMore=false nextCursor=null
PASS  M1a all 13 rows come back across the pages — 13 vs 13
PASS  M1b no duplicate across the tie boundary
PASS  M1c order identical to the SQL row-comparison ground truth — 70,…,61,60,59,51
PASS  M1d page 1's last row and page 2's first row SHARE a sent_at — 61 | 60
PASS  M1e the degraded `sent_at.lt`-only predicate DOES drop the tied rows
      — sent_at.lt alone returns 1 rows where the correct predicate returns 3: ids 51
```

M1e is the proof that the shipped predicate is load-bearing: `sent_at.lt` alone silently loses
rows 60 and 59. The tie rows were deleted in-run and the database reset afterwards.

### 3. Paging over real seed data (K1a–K1f, K2)

```
ground truth: receiver 1 has 26 rows, hearts 26
ground truth id order: 26,27,…,50,58
  page 1: 10 cards, hasMore=true, nextCursor={"sentAt":"2025-10-21T09:00:00+00:00","id":35}
  page 2: 10 cards, hasMore=true, nextCursor={"sentAt":"2025-10-18T21:00:00+00:00","id":45}
  page 3:  6 cards, hasMore=false, nextCursor=null
  page ids: 26…35  ||  36…45  ||  46,47,48,49,50,58
```

26 rows, 26 distinct ids, order byte-identical to the SQL `order by sent_at desc, id desc` ground
truth, boundary `35 → 36` with no repeat, last page `hasMore: false` and `nextCursor: null`. The
`FEED_PAGE_SIZE + 1` read returns 11 raw rows and 10 cards, so the extra row never reaches the
client.

The phase file's success criterion says "25 rows"; it is **26** — phase 03's Group D added the
anonymous row to receiver 1. Same for `counts.received`: 26, not 25.

### 4. The anonymity guarantee through *this* read path (K3a–K3f)

The seeded anonymous row (`kudos 58`, real sender sunner 2 = `Huỳnh Dương Xuân`, baseline 50 →
`Legend Hero`, dept `CEVC10`) read as an anonymous visitor through `fetchKudosPage` +
`buildFeedPage`:

```
sender: {"id":0,"fullName":"Ẩn danh","department":"","avatarUrl":"/images/kudos/sample-avatar.png",
         "badge":"New Hero","badgeTooltip":null}   anonymousSenderLabel: "Ẩn danh"
```

The redacted stub: not the sender's id, not their department, not their `Legend Hero` tier, no
tooltip. Exactly one masked card and exactly one `sentAnonymously: true` across all three pages.

**One check had to be rewritten, and the reason is worth recording.** The first version scanned the
whole payload for the string `Huỳnh Dương Xuân` and failed — because that is a strict *prefix* of
the receiver's own name, `Huỳnh Dương Xuân Nhật`, which is on all 26 cards. A substring scan cannot
decide this question. The check now verifies the sender's distinctive facts field by field, and
separately that **no anonymous card names them while their four open sends still do** (K3d) — the
guarantee is per-row, not per-person, and a check that demanded per-person invisibility would have
been asserting something false.

### 5. `fetchSentCount` read as the wrong caller exposed the mask working

A check that called `fetchSentCount(anon, 2)` came back `11` against a SQL truth of `12`. Not a
bug: `kudos_readable` masks sunner 2's own anonymous send from an anonymous caller, so it does not
match `sender_id=eq.2`. That is SEC_001/SEC_002 at the database layer — somebody else's anonymous
sends cannot even be **counted** through the view. `getProfileData` only ever calls it with
`viewer.sunnerId`, where the view reveals the caller's own rows; M4 measures that complete case.
Kept as K4d with that framing rather than deleted, because it is the sharpest available proof that
the count cannot be reconstructed.

### 6. `profile-data.ts` — one branch, taken once

`isSelf = targetId === viewer.sunnerId`, and everything self/other follows from it: `stats`
non-null iff `isSelf`, `writeKudoTargetId` non-null iff not, `counts.sent` null iff not.
Measured both faces:

```
other:  isSelf=false stats=null counts={"received":26,"sent":null} writeKudoTargetId=1
        hero badge "Super Hero" + the real tooltip, department "CEVC10"
self:   isSelf=true  stats={"kudosReceived":26,"kudosSent":25,"heartsReceived":26,
                            "secretBoxOpened":25,"secretBoxUnopened":25}
        counts={"received":26,"sent":25} writeKudoTargetId=null      (SQL truth 26/25/26/25/25)
```

Secret Box reads the real columns — `25`/`25` for the frame viewer, `0`/`0` for the sparse view,
no hardcoded number anywhere (M2d).

### 7. The sparse self view, and the one thing the seed cannot exercise

A real fresh signup with no `sunners` row (K7a–K7h):

```
{"isSelf":true,"hero":{"sunnerId":null,"fullName":"phase05-1788…","department":null,
 "avatarUrl":"/images/kudos/sample-avatar.png","badge":null,"badgeTooltip":null},
 "stats":{"kudosReceived":0,"kudosSent":0,"heartsReceived":0,"secretBoxOpened":0,
 "secretBoxUnopened":0},"writeKudoTargetId":null,"counts":{"received":0,"sent":0},
 "initialPage":{"cards":[],"nextCursor":null,"hasMore":false},"unlockedBadgeSlots":[]}
```

The name is the email **local-part**; the model contains no `@` at all and no auth uuid. And
`select count(*) from sunners where auth_user_id = '<uid>'` → `0` **after** the read: BR-001 holds,
the GET provisioned nothing.

`hero.badge === null` at zero received could not be exercised on seed data — **every one of the
nine seeded sunners has at least one received Kudo** (measured; the lowest is sunner 3 at 1, which
correctly renders `New Hero`, K6h). So it is measured on the auto-provisioned sunner instead
(M5): `counts.received: 0`, `badge: null`, `badgeTooltip: null`, and `department: "Unassigned"`
carried through rather than nulled.

### 8. `fetch-profile-kudos-page.ts` — the security boundary, and SC-003

`direction` is narrowed against the two literals, `targetSunnerId` must be a positive integer or
`null`, and the cursor goes through `isValidFeedCursor` before any query. Malformed input returns
an empty page. Then `column` is chosen **here**, server-side, and for `sent` it is paired with
`viewer.sunnerId` — `targetSunnerId` is not read in that branch at all.

SC-003 measured twice, once with an empty Sent list and once with a real one (K8c, M6):

```
K8c  two different targetSunnerId, identical 'sent' payload — {"cards":[],"nextCursor":null,"hasMore":false}
M6   targetSunnerId 1 / 2 / 999999 all return the caller's own 1 card: id 71
```

All six malformed inputs return an empty page (K8e), including the filter-injection attempt
`sentAt: "2025-10-23T15:00:00+00:00,id.gt.0)"` — which is why `TIMESTAMP_PATTERN` excludes `,`,
`(`, `)` and `"` rather than settling for `Date.parse`. The cursor's `sentAt` is passed through
**verbatim**, never round-tripped through `new Date().toISOString()`: Postgres stores
microseconds and `toISOString()` truncates to milliseconds, which would shift the boundary and
skip or duplicate rows.

The action also refuses an unauthenticated caller (gate A0). It reads Next 16's
`node_modules/next/dist/docs/01-app/03-api-reference/01-directives/use-server.md`: read-only, so
no `refresh()`/`revalidatePath()` — those exist to re-render after a mutation, and this action has
none. `cacheComponents` is not enabled in `next.config.ts`, so no `"use cache"` semantics apply.

## Checks

| Check | Result |
|---|---|
| `npm run typecheck` | **exit 0** |
| `npm run lint` | **exit 0** — 30 warnings, all pre-existing in `e2e/*.spec.ts`; none in a phase-05 file |
| Line counts | 199 / 199 / 84 — every file **under 200** |
| `grep -rn '\.from("kudos")' lib/profile app/profile` | **nothing** |
| `grep -rn '\.from("kudos_readable")' lib/profile` | 4 — `profile-queries.ts:82,97,121,184` |
| `grep -rnE 'auth_user_id\|\.email\b'` | the email in **exactly one** place (`profile-data.ts:103`, `split("@")[0]`); `auth_user_id` only inside a comment |
| `any` / `as any` / `!` assertions | **none** (the one cast is `as Record<string, unknown>`, which exists precisely to stop Supabase's `UserMetadata` `any` leaking, with a comment saying so) |
| `TODO` / `FIXME` | **none** |
| Measurement harness | **69 passed, 0 failed** (48 seed-state + 21 mutating) |
| `npx supabase db reset` | **exit 0** ×4; final state `kudos=58 anon=1 auth_users=0 linked=0` |

### F004 regression — real commands, real summary lines

| Command | Result |
|---|---|
| `npx playwright test --project=anon` | `81 passed (2.3m)` **EXIT=0** |
| `npx playwright test --project=kudos-authed` | `62 passed (1.8m)` **EXIT=0** |

Identical totals to phase 04's (81 / 62), so nothing regressed — as expected, since none of the
three files is imported by anything yet.

**One flake, recorded rather than dropped:** on the *first* full `--project=anon` run,
`e2e/callback-security.spec.ts:91` ("next as protocol-relative //evil.com is rejected") failed once
— `80 passed, 1 failed`, `expect(response.status()).toBe(307)`. Re-running that spec alone gave
`8 passed`, and both subsequent full runs gave `81 passed`. It is in a spec this phase does not
touch, exercising a route no phase-05 code is reachable from.

## Acceptance criteria (phase file Todo List)

- [x] `profile-queries.ts` selects only the allowed `sunners` columns — K4a asserts the returned key set exactly
- [x] Keyset uses the measured `.or(sent_at.lt…,and(sent_at.eq…,id.lt…))` form — and M1e proves the degraded form drops rows, on data built for the purpose because the seed has no ties
- [x] `FEED_PAGE_SIZE + 1` read; extra row dropped — K2: raw 11 → 10 cards
- [x] `direction: "sent"` ignores `targetSunnerId` and reads the session — K8c and M6, twice
- [x] `callerSunnerId === null` + `sent` → empty page, no error — K8d
- [x] JWT fallback chain matches `create_kudos()` verbatim, incl. email local-part — K7b, and the `nullif(…, '')` blank-skip reproduced
- [x] `hero.badge === null` when received == 0 — M5 (no seeded sunner has 0 received; measured)
- [x] `badgeTierFor` / `badgeTooltipFor` / `FEED_PAGE_SIZE` reused, not reimplemented — imported from `derive.ts`; the row→card mapping is `map-kudos-card.ts`, not forked
- [x] `stats !== null` iff `isSelf`; `counts.sent === null` iff not `isSelf` — K6b (other) and M2b/M2c (self)
- [x] No write on any read path — K7g re-reads `sunners` after the sparse render: still 0 rows
- [x] SC-003 verified by hand and recorded in `evidence/` — K8c + M6
- [x] All three files < 200 lines; typecheck + lint exit 0 — 199 / 199 / 84
- [x] Success criterion: `grep "auth_user_id\|\.email\b"` — one email touch, no auth uuid
- [x] Success criterion: `grep 'from("kudos")' lib/profile` → nothing

## Deviations from the phase file

1. **`getProfileData` takes the Supabase client as its first argument.** The architecture block
   writes `getProfileData(targetId | null, viewer)`. It cannot create its own client without
   creating a *second* one per request: the page must resolve the viewer **before** it can resolve
   `?id=` (phase 06's `resolveProfileId` needs `viewerSunnerId`), which it must do before calling
   this. Taking the client honours the NFR "one Supabase client per request" literally, and is
   `lib/kudos/queries.ts`'s existing signature convention. Phase 09 calls:
   `createClient()` → `resolveViewer()` → `resolveProfileId()` → `getProfileData(supabase, …)`.
2. **`buildFeedPage` and `emptyFeedPage` are exported from `profile-data.ts`** and imported by the
   action, so page 1 and every page after it are built by one function (DRY). The phase file
   describes the two call sites separately but does not say how they share; a fourth file would
   have been outside this phase's ownership.
3. **The cursor validator lives in `profile-queries.ts`, not the action.** A `"use server"` file
   may only export async functions, so a sync type guard cannot live there. It sits next to the
   `.or()` string it protects — validation at the point of use — and the action calls it before any
   query, which is what step 7 asks for. `fetchKudosPage` re-checks and throws, unreachable from a
   client: two layers, one validator.
4. **The action returns an empty page for an unauthenticated caller.** Not in the phase file;
   implied by gate A0 (`§ 3.3 Who · Sunner đã đăng nhập`). It discloses nothing new either way —
   the Received feed is already public on `/kudos` — so this is defence in depth, not a fix.
5. **A no-session sparse view returns the `not-found` sentinel.** The phase file does not say what
   happens when `readJwtIdentityFallback` finds no user. Unreachable through the doubly-guarded
   page; answered this way rather than by rendering a blank name.
6. **Comment volume was trimmed twice to fit under 200 lines.** No information dropped; the file
   headers point at the migration and `map-kudos-card.ts` instead of restating them.
7. **Two of the phase file's measured numbers are stale, and one of its premises is wrong.**
   `counts.received` for sunner 1 is **26**, not `25 + baseline` (phase 03's Group D). And Key
   Insight 1's "the seed generates many" duplicate `sent_at` values is false — there are none,
   which is why the no-duplicate/no-skip criterion alone could not have caught the degraded
   predicate. Both corrected by measurement, not by argument.

## What phase 09 inherits

- **The call sequence is fixed by a dependency, not a preference:**
  ```ts
  const supabase = await createClient();
  const viewer = await resolveViewer(supabase);            // lib/kudos/viewer.ts, untouched
  const resolution = resolveProfileId(searchParams.id, viewer.sunnerId);   // phase 06
  if (resolution.kind === "not-found") notFound();
  const targetId = resolution.kind === "self" ? viewer.sunnerId : resolution.id;
  const result = await getProfileData(supabase, targetId, viewer);
  if (result.kind === "not-found") notFound();             // FR-402
  ```
  `resolution.kind === "self"` maps to `viewer.sunnerId`, which is `null` exactly in the sparse
  case — do **not** pass `null` for every self view, or a real Sunner loses their own stats.
- **`getProfileData` returns a sentinel, not a thrown 404.** `{ kind: "not-found" }` covers both a
  well-formed id with no `sunners` row and (unreachably) a missing session. `notFound()` is the
  page's call.
- **Pass the action straight through as a prop.** `fetchProfileKudosPage` already satisfies the
  frozen `FetchProfileKudosPage` type, and `KudosDirectionSection` (phase 08) takes it as
  `fetchPage`. Do not wrap it, and do not pass `revealOwnAnonymous` from anywhere — the action
  derives it from the resolved direction, which is the whole point.
- **`counts.sent === null` already means "no `Đã gửi` option".** The component does not need to
  re-test `isSelf`; that is SC-002 and it is decided once, here.
- **`unlockedBadgeSlots` is always `[]`** and that is data, not a stub (AMEND-2).
- **`fetchGifts` still needs `gift_awards.sunner_id`** for the gift-leaderboard `?id=` link — one
  line in the select and one field on `GiftRowView`. Untouched here, as instructed.

## Unresolved questions

1. **The `revealOwnAnonymous` coverage is still a transcript, not a test — and phase 10's
   SEC_002 case as currently written would not catch a regression.** M3b–M3g prove the behaviour
   end-to-end through a real compose and the real action, which is much stronger than phase 04's
   transcript, but it lives in a scratchpad harness. `e2e/profile.spec.ts:568`
   (`TC_WEB_PROFILE_SEC_002`) is the durable owner, and today its only assertion after switching
   to the Sent list is `await expect(feedArea).toBeVisible()` — it passes whether or not the
   author's own anonymous card is in the list, and whether or not it is masked. It needs to assert
   the composed card is present **and** shows the author's own name. `e2e/**` is phase 02/10's
   ownership, so this is a handover, not an omission.
2. **`KUDOS_FEED_SELECT` is duplicated from `lib/kudos/queries.ts`'s `fetchKudos`.** The card
   *shape* is single-sourced (both use `KudosFeedRow`), but the column *list* now exists twice, and
   `.returns<T[]>()` is an assertion — a column dropped from one copy would not fail typecheck, it
   would surface as unexpected nulls in the mapper. `lib/kudos/**` was frozen for this phase, so
   the constant could not be hoisted. Whoever next opens `queries.ts` should export it from there
   and have both callers read it.
3. **ADV-4 (new): the profile does one extra read per page for badge tiers, and two unbounded reads
   per profile.** `fetchReceivedCounts` costs one query per page (decision A), and
   `fetchReceivedAggregate` reads *every* row a Sunner has received to sum hearts. At 26 rows and
   `max_rows = 1000` in `supabase/config.toml` that is fine; past 1000 received Kudos the heart sum
   would silently truncate to the first 1000 rows. Same class as ADV-1/ADV-3, and the honest fix is
   a stored counter or an RPC aggregate — not this phase's call.
4. **`e2e/profile.spec.ts` and `--project=profile-authed` were not run**, because
   `app/profile/page.tsx` is still `ComingSoon` — phase 09's file. The three modules this phase
   produced are currently imported by nothing; that is also why the F004 totals could not have
   moved. The first genuine end-to-end signal for this layer arrives with phase 09.
5. **Carried unchanged from phase 03/04:** `anon`/`authenticated` still hold blanket
   `INSERT`/`UPDATE`/`DELETE` grants on `public.kudos` and `public.kudos_readable` (inert under
   RLS). Nothing here narrows or widens it.
