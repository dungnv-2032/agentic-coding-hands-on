# Phase 04 — Repoint the three call sites, extract the shared card mapper — implementer report

## Files touched

| File | Change | Lines |
|---|---|---|
| `lib/kudos/queries.ts` | edit — `.from("kudos")` → `.from("kudos_readable")`, `KudosFeedRow`'s sender half → five flat nullable columns | 199 (was 185) |
| `lib/kudos/board-data.ts` | edit — delegates to the mapper; the inlined row→card body, `toSunnerView`, `toAnonymousSenderView`, `heartsOf` and `ANONYMOUS_FALLBACK_LABEL` removed | 157 (was 188) |
| `lib/kudos/map-kudos-card.ts` | **create** — the one shared mapper | 166 |
| `lib/kudos/view-model.ts` | edit — `sentAnonymously: boolean` added additively to `KudosCardView` | 131 (was 122) |
| `app/kudos/_actions/toggle-kudos-like.ts` | edit — **two lines**, both table names | 117 (unchanged) |

`git diff --stat` on the owned paths: `58 insertions, 66 deletions` across four tracked files, plus
the new file. Nothing outside the ownership list was touched — no `supabase/**`, no
`lib/supabase/database.types.ts`, no `app/profile/**`, no `app/kudos/_components/**`, no
`app/kudos/page.tsx`, no `lib/profile/**`, no test file, no plan/spec file. The other dirty paths in
the working tree (`lib/i18n/*`, `playwright.config.ts`, `docs/*`, `supabase/*`, `e2e/profile*`,
`app/profile/_components/`, `lib/profile/`) belong to phases 01/02/03/07/08.

Evidence written this phase:

- `evidence/phase-04-red-board.log` (1161 lines) — the pre-fix RED run, in full
- `evidence/phase-04-suite-runs.log` — RED and all three GREEN summary lines side by side
- `evidence/phase-04-anonymity.log` — the HTTP/psql probe transcript (P1–P6b)
- `evidence/phase-04-mapper-checks.log` — the mapper behavioural checks, source + output

## What was done

### 1. RED first, and it was already there

Phase 03 handed over a deliberately broken board, so the failing test existed before any edit and was
captured before touching a line:

```
npx playwright test e2e/kudos-live-board.spec.ts --project=anon
  23 failed
  2 passed (5.4m)                                                     EXIT=1
cause: Error: fetchKudos failed: permission denied for table kudos
       at fetchKudos (lib/kudos/queries.ts:65:20)
       at async getKudosBoard (lib/kudos/board-data.ts:64:70)
       at async KudosPage (app/kudos/page.tsx:50:5)
```

That is the exact failure phase 03 predicted (its unresolved question 1), from the exact line, so the
suite was measuring the revoke and not something else. The same command after the repoint is the
GREEN below. **The grant on `public.kudos` was not restored** — `revoke select` is still the only
state the migration leaves, verified live as probe P1.

### 2. `queries.ts` — the sender stops being an embed

`KudosFeedRow.sender: SunnerEmbed` became `sender_id`, `sender_full_name`, `sender_avatar_url`,
`sender_kudos_received_baseline`, `sender_department_name`, all `number | string | null`. The select
string lists those five and keeps the other four embeds **verbatim**, `kudos_receiver_id_fkey` hint
included. `.returns<KudosFeedRow[]>()` stays.

Only the five `sender_*` columns are typed nullable. The generator marks *every* view column nullable
because a view carries no NOT NULL metadata, but the other nine are NOT NULL on the base table and
`kudos_readable` neither filters nor masks them, so the row type says what actually arrives rather
than what the generator can prove. The five that the database genuinely nulls are the five that are
nullable here — the type carries the security property instead of hiding it behind a cast.

No `!`, no `as`, no `any` anywhere in the phase's diff (grepped).

### 3. `map-kudos-card.ts` — moved, then extended, in that order

`toSunnerView`, `toAnonymousSenderView`, `heartsOf`, `ANONYMOUS_FALLBACK_LABEL` and the row→card body
moved out of `board-data.ts` behaviour-first; the `revealOwnAnonymous` option and `sentAnonymously`
were added only after the board's suite came back green on the moved code.

One deliberate re-shape: `toSunnerView` used to take a `SunnerEmbed`. The sender no longer is one, so
it now takes a small `SunnerFacts` record and two thin adapters feed it — `toReceiverView` (from the
embed) and `toSenderView` (from the flat columns). The badge/tooltip/department arithmetic exists
once, as before.

`toSenderView` returns `SunnerView | null`: it checks the four load-bearing sender columns
individually and returns `null` if any is missing. That is the boundary check, and it is also the
narrowing — `showsRealSender` is `senderView !== null && (anonymousLabel === null || revealOwn)`, a
condition TypeScript narrows on its own. A null sender has exactly one correct answer, the anonymous
view; there is no second lookup to recover a name, and the mask is nowhere re-implemented in
TypeScript.

### 4. The one translation that needed care: `canLike` / `isOwnedByViewer`

The phase file said these keep their meanings for free. They do — but **not** via the obvious
transcription. `viewer.sunnerId !== row.sender.id` naively becomes
`ctx.viewerSunnerId !== row.sender_id`, and that is wrong in a case the e2e suite hits constantly: an
authenticated viewer with no `sunners` row (`viewerSunnerId === null`) looking at a masked anonymous
row (`sender_id === null`) would compare `null !== null` → `false` → **heart disabled**, where F004
ships it enabled (clarifications A4 makes the no-`sunners`-row session the common authenticated case,
and phase 03 just seeded the first anonymous row, so the two nulls now meet on a real page).

The faithful form is one predicate:

```ts
const viewerIsSender =
  row.sender_id !== null && ctx.viewerSunnerId !== null && ctx.viewerSunnerId === row.sender_id;
canLike: ctx.viewerIsAuthenticated && !viewerIsSender,
isOwnedByViewer: viewerIsSender,
```

`sender_id === null` means the database refused to disclose the sender, which by construction means
the caller is not that sender — so a masked row is never "owned" and never blocks the heart, and the
author of an anonymous Kudo still cannot like it, because the view reveals `sender_id` to them (P6).
Equivalent to the old expression in every reachable case; check B in the mapper log is the one that
would have caught the naive version.

### 5. `board-data.ts` — delegation, and one honest count change

The received-count map, sidebar counts, gift/spotlight mapping and the returned `KudosBoardViewModel`
are untouched. Two things changed beyond the delegation:

- `revealOwnAnonymous` is **not** passed, so the board keeps showing an author their own anonymous
  Kudo as a masked chip — F004's shipped behaviour.
- the sidebar's `kudosSent` loop reads `row.sender_id !== null && row.sender_id === sidebarSunnerId`
  instead of `row.sender.id === sidebarSunnerId`. For a signed-in viewer nothing changes: the view
  reveals their own sends, anonymous ones included (P6b: 12 sent, 1 of them anonymous). For the
  anonymous-visitor display fallback the seeded frame viewer's anonymous sends can no longer be
  counted — and must not be, because that number is precisely what SEC_002 forbids publishing about
  someone else. The board's shipped figures are unchanged in fact as well as in principle: the only
  anonymous row's sender is sunner 2 while the display fallback is sunner 1.

### 6. `toggle-kudos-like.ts` — two lines, nothing else

`git diff` is exactly two changed lines, both `.from("kudos")` → `.from("kudos_readable")`. The
BR-003 check, `readHeartState`, `refresh()`, the `23505` handling and the error paths are byte
identical. The BR-003 comparison survives untouched because a masked `sender_id` is `null`, which
cannot equal a real `viewer.sunnerId`, and the caller who *is* the sender gets the real id (P6) —
with `kudos_likes_insert_own` re-checking it under RLS regardless.

## Checks

| Check | Result |
|---|---|
| `npm run typecheck` | **exit 0** |
| `npm run lint` | **exit 0** — 30 warnings, all pre-existing in `e2e/*.spec.ts`; none in a file this phase touched |
| `grep -rn '\.from("kudos")' lib app` | **nothing** |
| `grep -rn '\.from("kudos_readable")' lib app` | exactly **3**: `lib/kudos/queries.ts:78`, `app/kudos/_actions/toggle-kudos-like.ts:26,73` |
| Line counts | 199 / 157 / 166 / 131 / 117 — every file **under 200** |
| `!` / `as` / `any` in the diff | none |

### Suite runs — real commands, real summary lines

| Command | Before this phase | After |
|---|---|---|
| `npx playwright test e2e/kudos-live-board.spec.ts --project=anon` | `23 failed, 2 passed (5.4m)` **EXIT=1** | `25 passed (1.8m)` **EXIT=0** |
| `npx playwright test --project=kudos-authed` | not run (board dark) | `62 passed (1.5m)` **EXIT=0** |
| `npx playwright test --project=anon` (full project, phase step 8) | not run | `81 passed (1.6m)` **EXIT=0** |

The full `anon` project covers `kudos-live-board` (24), `homepage` (21), `award-system` (13),
`login-screen` (10), `callback-security` (7), `route-guard` (2), `profile-anon` (2), `smoke` (1).
`kudos-authed` covers F004's authenticated board and F005's whole compose suite; the two that matter
most here:

```
✓ K-10 — heart toggle flips aria-pressed and updates count by 1 (4.1s)
✓ K-25 — heart persists across page reload (5.8s)
```

K-25 is the end-to-end proof for the heart: it writes, re-reads `{liked, hearts}` from the database
through `kudos_readable` **twice** (`readHeartState` plus the BR-003 read), reloads the page and the
count is still right. K-24 (every heart disabled for anon) and K-9 (sender/receiver/badge on the
first card) are inside the 25 above.

### The anonymity guarantee, measured through the new read path

Full transcript in `evidence/phase-04-anonymity.log`. Ground truth first, from the base table as
superuser: `kudos 1: sender=1 (Huỳnh Dương Xuân Nhật) receiver=2 (Huỳnh Dương Xuân)`,
`kudos 58: sender=2 (Huỳnh Dương Xuân) is_anonymous=true`.

| # | Probe | Result |
|---|---|---|
| P1 | anon, HTTP `GET /rest/v1/kudos?select=id,sender_id` | **HTTP 401** `42501 permission denied for table kudos` — the revoke is intact; nothing was "fixed" by restoring the grant |
| P2 | anon, HTTP, **the exact shipped `fetchKudos` select string**, `id=eq.58` | **HTTP 200**; all five `sender_*` **null**; `is_anonymous: true`; `receiver: 1`; and all four embeds resolved (`receiver`, `hashtags`, `attachments`, `likes`) |
| P3 | same select, anon, non-anonymous `id=eq.1` | `sender_id 1 | Huỳnh Dương Xuân Nhật | dept CEVC10` vs `receiver 2 | Huỳnh Dương Xuân` — the **right** person, and demonstrably not the receiver, which is the failure mode the probe report warned ships green |
| P4 | anon, filter oracles on the view: `sender_id=eq.2&is_anonymous=is.true`, `sender_id=not.is.null&is_anonymous=is.true`, `sender_full_name=ilike.*Xuân*&is_anonymous=is.true` | `[]`, `[]`, `[]` — SEC_002's count cannot be reconstructed through the view |
| P5 | `toggle-kudos-like.ts`'s two reads replayed verbatim as anon on `id=58` | `[{"heart_baseline":1,"likes":[{"count":0}]}]` and `[{"sender_id":null}]` — the write path's reads work, and the BR-003 read discloses nothing |
| P6 | the **author** of `kudos 58` (real `auth.users` row linked to sunner 2 inside a rolled-back txn, `role authenticated` + `request.jwt.claims`) | `58 | 2 | Huỳnh Dương Xuân | t` — revealed, so `canLike`/`isOwnedByViewer`/`revealOwnAnonymous` have real material |
| P6b | the same caller, `where sender_id = 2` | `my_sent_total 12, my_anonymous_sent 1` — for phase 05 |
| Page | `curl /kudos` as an anonymous visitor, then read the card object out of the SSR payload | see below |

The rendered page, not an assertion about it — the anonymous card as it reaches the browser:

```json
{"id":58,"sender":{"id":0,"fullName":"Ẩn danh","department":"","avatarUrl":"/images/kudos/sample-avatar.png",
 "badge":"New Hero","badgeTooltip":null},"receiver":{"id":1,"fullName":"Huỳnh Dương Xuân Nhật",...},
 ...,"canLike":false,"isOwnedByViewer":false,"messageFormat":"plain",
 "anonymousSenderLabel":"Ẩn danh","sentAnonymously":true}
```

`sender` is the redacted stub. `Huỳnh Dương Xuân` — the real sender, sunner 2 — appears nowhere in
that card object: no name, no department, no avatar, no id, no badge tooltip. Across the whole
payload: 58 cards, `anonymousSenderLabel:"Ẩn danh"` exactly **1**, `sentAnonymously:true` exactly
**1** — the seeded row, and only it.

### Mapper behavioural checks

The repo has no unit-test runner (`package.json` scripts are `dev/build/start/lint/typecheck/test:e2e/db:types`),
and adding one is a `package.json` change outside this phase's ownership. So the mapper — which is
pure: no client, no session read, no `next/*` import — was compiled to CJS and exercised directly.
Source and output are in `evidence/phase-04-mapper-checks.log`; all eight pass:

```
PASS  A non-anonymous row, other viewer: real sender, no chip, badge from baseline+received
PASS  B masked row, authed viewer with NO sunners row: chip, heart still ENABLED (F004 parity)
PASS  C masked row, anonymous visitor: chip, heart disabled
PASS  D revealed row on the BOARD (revealOwnAnonymous off): author still sees the chip, cannot heart it
PASS  E revealed row on the profile SENT list (revealOwnAnonymous on): author shown, still marked anonymous
PASS  F revealOwnAnonymous cannot unmask SOMEONE ELSE's anonymous Kudo
PASS  G a published anonymous_name is used; whitespace-only falls back
PASS  H a non-anonymous row whose sender columns arrive null degrades to the chip, never to a fake identity
```

Check A failed on its first run — and the code was right, my expected badge was wrong (baseline 7 +
3 received = 10 → `Rising Hero`, not `New Hero`). Recorded because it is also the proof that the
sender's badge tier is keyed off `sender_id` in the received-count map, not off the receiver's.
Check F is the security-relevant one: `revealOwnAnonymous: true` cannot unmask anybody else, because
the database has already decided whether `sender_id` is visible at all — the option can only decline
to re-mask what the caller was already shown.

## Acceptance criteria (phase file Todo List)

- [x] `sentAnonymously` added additively to `KudosCardView` — every existing field keeps its meaning; it renders nothing, and the comment in the contract says so
- [x] `KudosFeedRow` sender half is five flat nullable columns
- [x] `queries.ts` reads `kudos_readable`; receiver embed hint untouched — P2 proves all four embeds still resolve through the shipped select
- [x] `map-kudos-card.ts` created; behaviour moved, not rewritten — moved and proven green before the option was added
- [x] `revealOwnAnonymous` option present and defaulted `false` — checks D (off) / E (on) / F (cannot cross to another author)
- [x] `board-data.ts` delegates; view model output equivalent for the board — 25/25 anon board assertions, 62/62 kudos-authed, `board-data.ts` contains no row→card mapping code
- [x] `toggle-kudos-like.ts:26` and `:73` read `kudos_readable`; nothing else changed — diff is exactly two lines
- [x] All touched files < 200 lines — 199 / 157 / 166 / 131 / 117
- [x] `npm run typecheck` / `npm run lint` exit 0
- [x] F004's board + kudos-authed projects pass — `81 passed` / `62 passed`, both EXIT=0
- [x] Success criterion: `grep '\.from("kudos")'` returns nothing; `kudos_readable` appears at exactly three call sites
- [x] Success criterion: the seeded anonymous row renders `Ẩn danh` with no department, no tier badge (`badgeTooltip: null`) and no `/profile` link — the redacted stub carries `id: 0`, which is what routes the card to `AnonymousSenderChip`

## Deviations from the phase file

1. **`toSunnerView` was re-shaped, not moved verbatim.** It took a `SunnerEmbed`; the sender is no
   longer one. It now takes a `SunnerFacts` record with two thin adapters (`toReceiverView`,
   `toSenderView`). Behaviour identical — same badge arithmetic, same `department ?? ""`, same
   tooltip — but the signature had to change or the flat columns would have needed a fabricated
   embed object to pass through it.
2. **`canLike` / `isOwnedByViewer` are computed from one `viewerIsSender` predicate**, not from the
   two inline comparisons. The phase file said not to "fix" them, and this does not: it is the only
   spelling that keeps their old meaning once `sender_id` is nullable (§4 above, and check B).
3. **The sidebar's `kudosSent` loop needed a null guard** (§5). The phase file listed the sidebar
   counts as "exactly as they are"; the count is unchanged for every viewer the board actually has,
   but the expression could not stay literally the same because `row.sender` no longer exists.
4. **The mapper's checks are a transcript, not a durable test file.** No unit runner exists and
   adding one is out of this phase's ownership. The first attempt to keep the script as
   `evidence/phase-04-mapper-checks.js` turned `npm run lint` **red** (eslint
   `no-require-imports` reaches into `plans/`), so it is stored as a log with its source inline.
   Named as a gap, not papered over: these eight cases deserve to be a real test file the day this
   repo gets a unit runner.
5. **Two extra comment paragraphs were tightened in `queries.ts`** to bring it from 210 back to 199
   lines after the new documentation was added. No information dropped; the PGRST200/wrong-human
   reasoning now points at the migration § 3 and `map-kudos-card.ts` instead of repeating them a
   third time (DRY).

## What phases 05 and 09 inherit

**Phase 05** (`lib/profile/**`, `app/profile/_actions/**`):

- `import { toKudosCardView, heartsOf, toReceiverView, ANONYMOUS_FALLBACK_LABEL } from "@/lib/kudos/map-kudos-card"`.
  `toKudosCardView(row, ctx, opts)` with `ctx: { viewerSunnerId, viewerIsAuthenticated, likedKudosIds: Set<number>, receivedCountBySunnerId: Map<number, number> }`.
- `opts.revealOwnAnonymous` is server-only by contract. Resolve `callerSunnerId` from the session
  inside the action and set it from that; never accept it as an argument. It cannot leak anything on
  its own (check F), but that is a property of the database's mask, not a licence to pass it through
  from a client.
- **The Sent list needs no `NOT is_anonymous` filter and must not have one.**
  `kudos_readable?sender_id=eq.{me}` already returns the caller's own anonymous rows, because the
  view reveals `sender_id` to its author — measured: 12 sent, 1 anonymous (P6b). That is exactly the
  under-reporting trap clarifications § "My own Sent list" warns about, and the view closes it.
- **`receivedCountBySunnerId` is a decision phase 05 has to make deliberately.** The board derives it
  from a full-table read; a keyset-paged profile feed sees one page, so a map built from a page gives
  wrong badge tiers (too low). Pass an empty map to fall back to `kudos_received_baseline` alone, or
  query the counts — but do not build it from the page and assume it is complete.
- A row whose sender columns arrive `null` is final. Never re-query to recover the name.

**Phase 09** (`lib/kudos/{queries,board-data,view-model}.ts` + `map-kudos-card.ts`, and
`app/kudos/_components/**`): all four files are handed over typecheck-clean, lint-clean and green on
`--project=anon` + `--project=kudos-authed`. `KudosCardView.sentAnonymously` exists and is
deliberately unrendered — wiring a chip to it would invent design data (AMEND-3, and the auto-resolved
FR-602 answer in clarifications).

## Unresolved questions

1. **`GiftRowView` still carries no sunner id.** Clarifications § "Two blueprint findings" says the
   fix is adding the plain `gift_awards.sunner_id` to `fetchGifts`'s select so
   `gift-leaderboard.tsx` can emit `?id=`. `fetchGifts` lives in `queries.ts`, which this phase owns,
   but the change is not in this phase's file plan, has no consumer yet, and would widen a frozen
   contract (`GiftRowView`) that phase 09 is about to wire — so it was left alone (YAGNI). Whoever
   ships the gift-leaderboard link needs one line in `fetchGifts` and one field on `GiftRowView`.
2. **The eight mapper checks are not durable.** See deviation 4. The board's e2e suite covers cases
   A–D and G indirectly; **E and F — the `revealOwnAnonymous` option — have no durable test until
   phase 05 writes one.** That is the one thing in this phase whose regression would be silent, and
   it is the phase-05 e2e case (SEC_002's Sent-list parity) that should own it.
3. **`anon`/`authenticated` still hold blanket `INSERT`/`UPDATE`/`DELETE` grants on
   `public.kudos_readable`** as well as the base table — Supabase's default grant, inert under RLS,
   and already carried by phase 03's unresolved question 2. Nothing this phase did narrows or widens
   it. Still worth an advisory.
4. **`sunners.id = 10` is linked to a real `auth.users` row in the local database**, left behind by
   F005's compose e2e test (`e2e-1788844582682-110317-nx2g3a`). Pre-existing, not created here; my
   own author-side probe ran inside a rolled-back transaction and the link count was verified
   unchanged afterwards. Flagged because `resolveSidebarSunnerId`'s "first row with
   `auth_user_id IS NULL`" fallback silently depends on which rows are linked, and a local database
   that has run the compose suite is no longer in seed state. `npx supabase db reset` restores it.
