# Phase 09 — Integration: page wiring, board `?id=` links, the F004 amendment — implementer report

## Files touched

| File | Change | Lines |
|---|---|---|
| `app/profile/page.tsx` | **rewrite** — `ComingSoon` gone; guard layer two, `?id=` resolution, data → components | 143 (was 15) |
| `app/kudos/_components/sunner-chip.tsx` | edit — `href` now `/profile?id={id}` with an `id > 0` guard, comment reversed on the record | 103 (was 94) |
| `app/kudos/_components/gift-leaderboard.tsx` | edit — `href={`/profile?id=${gift.sunnerId}`}` | 78 (was 73) |
| `app/kudos/_components/kudos-board.tsx` | edit — `hashtagFilterId` initialised from `?hashtag=` (FR-405) | 189 (was 175) |
| `lib/kudos/queries.ts` | edit (inherited) — `KUDOS_FEED_SELECT` hoisted + exported; `gift_awards.sunner_id` added to `fetchGifts` and `GiftFeedRow` | 199 (was 199) |
| `lib/kudos/view-model.ts` | edit (inherited) — `GiftRowView.sunnerId: number`, additively | 137 (was 131) |
| `lib/kudos/board-data.ts` | edit (inherited) — maps `sunnerId` | 158 (was 157) |
| `lib/profile/profile-queries.ts` | edit — imports the hoisted select, drops its duplicate copy (obligation F) | 184 (was 199) |
| `e2e/kudos-live-board.spec.ts` | edit — K-9's two href assertions narrowed to `/^\/profile\?id=\d+$/`, each with a recorded reason | 617 (was 606) |

`lib/kudos/map-kudos-card.ts` and `app/kudos/_actions/toggle-kudos-like.ts` were inherited but
needed no change and are byte-identical to what phase 04 left. **Every file is under 200 lines.**

Nothing outside the ownership list was touched: no `app/profile/_components/**`,
no `lib/profile/{profile-view-model,profile-data,resolve-profile-id}.ts`, no
`app/profile/_actions/**`, no `supabase/**`, no `lib/supabase/database.types.ts`, no
`app/_components/account-menu.tsx`, no `kudos-card.tsx`, no `anonymous-sender-chip.tsx`, no
`app/kudos/page.tsx`, and **none of `e2e/profile.spec.ts`, `e2e/profile-anon.spec.ts`,
`e2e/profile-auth.setup.ts`, `e2e/fixtures/profile-constants.ts` or `playwright.config.ts`**.

`lib/profile/profile-queries.ts` is the one file edited that the prompt's freeze list also names.
It is edited **only** as obligation F instructs, and the diff is exactly two hunks: the import line,
and the deletion of the duplicated `KUDOS_FEED_SELECT` constant. Called out here rather than
folded in silently, because the two instructions collide on that path.

Evidence written this phase:

- `evidence/phase-09-measurements.log` — the two REDs, the GREENs, the anonymity payload, the live
  grant re-read, every suite summary with its exit code, the database state
- `evidence/phase-09-probe-source.log` (222 lines) — the throwaway probe in full, so the numbers
  are reproducible rather than merely reported

## Obligation G first: the database

Read back **before** any measurement as `kudos=58 anon=1 auth_users=0 linked=0` — exactly what
phase 05 handed over, so no reset was needed to start. `npx supabase db reset` was then run three
times (exit 0 each): before the F004 regression runs, before the second profile-suite run, and at
the end. **Phase 10 inherits `kudos=58 anon=1 auth_users=0 linked=0`.**

## RED first, twice — and neither RED was inherited

This repo has no unit runner, so both REDs are real browser runs.

**RED 1 — the board links.** The F004 amendment was made *before* `sunner-chip.tsx` changed, which
is the only ordering under which it is a test rather than a rubber stamp:

```
$ npx playwright test e2e/kudos-live-board.spec.ts --project=anon -g "K-9"
  Error: expect(locator).toHaveAttribute(expected) failed
  Expected pattern: /^\/profile\?id=\d+$/
  Received string:  "/profile"
  1 failed, 1 passed (1.5m)     EXIT=1
```

**RED 2 — the `?hashtag=` deep link.** Key Insight 1's trap is that a URL-only assertion passes on
a half-truth, so the probe asserts the board's *filter state* and its *card contents*, and it was
run against the unchanged board first:

```
  baseline: 10 cards on page 1, first tag = Toàn diện
  ?hashtag=Toàn diện: 10 cards            <- the board ignored the param entirely
  Error: expect(received).toContain(expected)
    Expected value: "Toàn diện"
    Received array: ["Giỏi chuyên môn", "Hiệu suất cao", "Truyền cảm hứng"]
  1 failed, 1 passed            EXIT=1
```

Both went green on the change (§ Checks). The probe lived in a throwaway `.probe-tmp/` with its own
Playwright config, was run with `--config`, and was **deleted**; `git status` shows no trace, and
`e2e/**` was never used as a scratchpad. Its source is in `evidence/phase-09-probe-source.log`.

## What was done

### 1. `app/profile/page.tsx` — composition only

The call order is forced by a dependency, exactly as phase 05 specified:

```ts
const supabase = await createClient();
const [{ locale, dictionary, isAuthenticated, isAdmin }, viewer, searchParams] =
  await Promise.all([getPageContext(), resolveViewer(supabase), props.searchParams]);
if (!viewer.isAuthenticated) redirect("/login");            // guard layer two
const resolution = resolveProfileId(searchParams?.id, viewer.sunnerId);
if (resolution.kind === "not-found") notFound();
const targetId = resolution.kind === "self" ? viewer.sunnerId : resolution.id;
const result = await getProfileData(supabase, targetId, viewer);
if (result.kind === "not-found") notFound();
```

`resolveProfileId` needs the viewer's own id to canonicalise `?id={me}`, and `getProfileData` needs
the resolved target — so only the three independent request reads share the `Promise.all`. Both
`notFound()` verdicts return before a single component renders. The page signature is
`PageProps<"/profile">`, this repo's shipped convention (`app/login/page.tsx:30`) and the typed form
Next 16 documents for the async `searchParams` promise
(`next/dist/docs/01-app/03-api-reference/03-file-conventions/page.md:125`).

Layout is three lines of the page's own: the `#00101A` root, `<main>`, and one
`px-6 pt-16 sm:px-12 lg:px-36` gutter around the B slot. The C section carries its own `py-16`, so
both region gaps come out at 64px. Everything measured lives in phases 07/08.

The B slot is the frozen contract's single branch and nothing re-derives it:

```tsx
{vm.stats !== null ? <ProfileStatsCard … /> : vm.writeKudoTargetId !== null ? <WriteKudoBar … /> : null}
```

The trailing `null` is unreachable under the contract (`stats` non-null iff `isSelf`,
`writeKudoTargetId` iff not) and is written out rather than forced with a `!` — a `!` would be this
file asserting something about data it did not produce.

`KudosDirectionSection` is mounted against phase 08 § 1's prop contract verbatim, including
`copy: { eyebrow: kudos.eyebrow, direction: profile.direction, feed: profile.feed, card: kudos.card, toast: kudos.toast }`.
Fact E was honoured: **no** `onCopyLink`/`onHashtagClick` prop is passed, and nothing the section
already owns (the four SM-001 states, the FR-403 switch, the request-id race guard, the hashtag push,
the Copy-Link toast) is re-implemented at page level. `fetchProfileKudosPage` and `toggleKudosLike`
travel straight through as props, unwrapped, and `revealOwnAnonymous` is passed from nowhere.

### 2. The two board links

`sunner-chip.tsx` now emits `/profile?id={sunner.id}` with an `id > 0` fallback to the bare
`/profile`. The guard is unreachable today — `map-kudos-card.ts` redacts a masked sender to the
`id: 0` stub and `kudos-card.tsx:125` routes those rows to `AnonymousSenderChip`, which has no link
at all (measured: the masked card's only link is the receiver's, § 4 below) — and exists so a future
caller cannot leak `?id=0`. The comment that claimed the href "is the fixed literal, never built
from a field" is replaced by one that records the reversal and cites where it was ratified, since a
reader finding the old comment beside the new code would rightly distrust both.

`gift-leaderboard.tsx` emits `/profile?id={gift.sunnerId}`, unblocked by adding the plain
`gift_awards.sunner_id` column to `fetchGifts`'s select and `GiftFeedRow`, then `sunnerId: number`
to `GiftRowView` and one line in `board-data.ts`'s map. No new embed, and because the column is
NOT NULL on the base table there is no nullability to handle — hence no guard here, unlike the chip.

`account-menu.tsx:93` was not touched.

### 3. `kudos-board.tsx` reads `?hashtag=`

```ts
const initialHashtagName = useSearchParams().get("hashtag");
const [hashtagFilterId, setHashtagFilterId] = useState<number | null>(
  () => board.hashtagOptions.find((option) => option.name === initialHashtagName)?.id ?? null,
);
```

Matched by **name**, because the id is a database key and must not appear in a link. Absent, empty
or unrecognised resolves to `null`, which is byte-identical to the state this board shipped with —
that is what keeps F004's board assertions true, and it is asserted directly (`/kudos`,
`/kudos?hashtag=`, `/kudos?hashtag=#not-a-real-tag` all leave zero options `aria-selected`).

**One correction to the phase file's step 6.** The hashtag *name* carries no `#`:
`hashtags.name` is `Toàn diện` and `kudos-hashtag-row.tsx:39` renders the `#` itself. The first
probe read the rendered text and looked for `#Toàn diện`, which matched nothing — the probe was
wrong, not the board. `KudosDirectionSection`'s `router.push` already sends the bare name, so the
two halves agree; recorded because a reader assuming `?hashtag=#tag` would "fix" a working link.

Read as the **initial** value only. Once mounted the filter menu owns the state, so re-picking is
not fighting the URL; `useSearchParams` costs nothing at build time here because every route in this
app is `ƒ (Dynamic)` (build output), so the prerender/`Suspense` caveat in
`next/dist/docs/01-app/03-api-reference/04-functions/use-search-params.md` does not apply.

### 4. Obligation F — the hoist was clean, so it was done

`KUDOS_FEED_SELECT` is now exported from `lib/kudos/queries.ts` and imported by
`lib/profile/profile-queries.ts`; `fetchKudos` reads the same constant. The column list exists once
again, which matters because `.returns<KudosFeedRow[]>()` is an assertion — a column dropped from
one of two copies would have surfaced as unexpected nulls in the mapper, not as a type error
(phase 05's unresolved question 2, closed).

`queries.ts` came out at 208 lines after the hoist plus `sunner_id`. Rather than leave it over the
cap, four single-argument signatures were folded onto one line each (the shape
`profile-queries.ts` already uses) and two comment paragraphs tightened — 199 lines, no information
dropped. `profile-queries.ts` fell from 199 to 184.

### 5. What was deliberately *not* done

- `canLike` was left as phase 04's single `viewerIsSender` predicate. The plan's literal form was
  not restored (fact D).
- The keyvisual origin was not "fixed" (fact H). Phase 10's visual diff owns that call.
- No test was added to `e2e/kudos-live-board.spec.ts`; the phase file permits lines 354/356 only.
  The hashtag and `?id=` proofs are therefore probe transcripts, named as such below.

## Checks

| Check | Result |
|---|---|
| `npm run typecheck` | **exit 0** |
| `npm run lint` | **exit 0** — 30 warnings, all pre-existing in `e2e/*.spec.ts`; **zero** in a file this phase touched |
| `npm run build` | **exit 0** — 13 routes, every one `ƒ (Dynamic)` |
| Line counts | 143 / 103 / 78 / 189 / 199 / 137 / 158 / 184 — every file **under 200** |
| `TODO` / `FIXME` / `: any` / `as any` in the touched files | **none** |
| `grep -rn '\.from("kudos")' lib app` | **nothing** |
| `select` grant on `public.kudos`, read live | `postgres`, `service_role` — **anon/authenticated still have none** |
| `npx supabase db reset` | **exit 0** ×3; final state `kudos=58 anon=1 auth_users=0 linked=0` |

### Suite runs — real commands, real summary lines

| Command | Result |
|---|---|
| `npx playwright test e2e/kudos-live-board.spec.ts --project=anon -g "K-9"` (RED, pre-change) | `1 failed, 1 passed (1.5m)` **EXIT=1** |
| `npx playwright test --project=anon` | `81 passed (2.1m)` **EXIT=0** |
| `npx playwright test --project=kudos-authed` | `62 passed (1.5m)` **EXIT=0** |
| `npx playwright test --project=profile-authed` | `22 passed, 5 failed (2.0m)` **EXIT=1** |
| `npx playwright test --project=profile-authed` (re-run after `db reset`) | `22 passed, 5 failed (2.0m)` **EXIT=1** — the identical five |

**No F004 regression.** `81` and `62` are the same totals phases 04 and 05 measured, and the `81`
now includes the *narrowed* K-9 rather than the literal one. `callback-security.spec.ts:91` did not
flake on this run.

### `/profile` renders — the point of the phase

22 of the 27 profile cases pass, and what they cover is the page working end to end: `?id={other}`
renders that Sunner (FUN_001), a non-existent id and all four malformed ids return **404** with no
hero (FUN_003/FUN_004), `?id=` empty renders the self view and `?id=1&id=2` 404s (FUN_005), the hero
and its six locked badge slots render (GUI_002), the first-person/neutral badge heading switches
(GUI_003), the sparse profile renders unbroken (GUI_009), the five statistics rows and the disabled
Secret Box button render (GUI_004/GUI_005), another's profile shows the write bar and **no** stats
while the viewer's own shows stats and no bar (FUN_006/FUN_007/FUN_008), the dropdown offers both
directions on self and **Received only** on another's profile (FUN_009/SEC_001), re-picking the
active direction is a no-op (FUN_011), infinite scroll pages to the end-of-feed message (FUN_013),
cards match the board's format including masking (GUI_006), no Spam chip (GUI_007), the heart
round-trips to the server and back (FUN_014), and the page contains no email and no auth uuid
(SEC_004).

**The five failures are all test-side, and none is an absent element.** Details in the handover.

### The two new links, proven end to end

```
landed on /kudos?hashtag=Qu%E1%BA%A3n%20l%C3%BD%20xu%E1%BA%A5t%20s%E1%BA%AFc for tag Quản lý xuất sắc
board filtered to 8 cards, every one carries Quản lý xuất sắc
  ✓ profile hashtag click reaches /kudos?hashtag= AND the board filters on it
gift row 1: Huỳnh Dương Xuân -> /profile?id=2
clicked through to /profile?id=2, hero names Huỳnh Dương Xuân
  ✓ gift-leaderboard emits a working ?id=
Huỳnh Dương Xuân /profile?id=2 -> hero renders Huỳnh Dương Xuân
  ✓ sunner-chip ?id= resolves to that Sunner's profile
```

The hashtag proof clicks a real `kudos-hashtag` button on a real profile card, follows the push, and
then asserts the **filter menu shows exactly that tag `aria-selected`** and that every card left on
the board carries it — the URL is checked as well, but the URL alone was never the claim. The two
`?id=` proofs click the link and assert the destination hero names that person, so the id is right
and not merely well-shaped.

### Anonymity through the wired page, per row, at payload level

The seeded anonymous row (`kudos 58`, real sender sunner 2) sits on **page 3** of receiver 1's feed,
so the probe scrolls the keyset feed through the real A2 action until all 26 cards are loaded, then
reads the action's own response body:

```
feed loaded 26 cards; 2 action payloads captured
masked card links: ["/profile?id=1"]        <- the receiver only; the masked sender is not a link
sender object: "sender":{"id":0,"fullName":"Ẩn danh","department":"","avatarUrl":"…","badge":"New Hero","badgeTooltip":null},
  - contains none of: "id":2 / CEVC10 / Legend Hero / Huỳnh
masked row redacted; the same sender's open sends still named
```

**The first version of this check was wrong, and the way it was wrong is worth recording.** It
scanned the whole payload for `"sender":{"id":2` and failed — because sunner 2 legitimately appears
as the named sender of four *non-anonymous* Kudos on that very page. That is phase 05's K3d finding
arriving from the other direction: the guarantee is per **row**, not per person, and a check
demanding per-person invisibility asserts something false. The shipped check therefore isolates
kudos 58's own `sender` object and verifies it field by field, and separately asserts that
`"sender":{"id":2` **is** present elsewhere — so a regression that over-masked would fail too.

## Acceptance criteria (phase file Todo List)

- [x] `page.tsx` composed, `ComingSoon` removed, < 200 lines — 143; `grep ComingSoon app/profile` is empty
- [x] Page re-resolves the session (layer two of the guard) — `resolveViewer` → `redirect("/login")`
- [x] `notFound()` on a bad id **and** on a missing `sunners` row; no partial profile ever renders — FUN_003/FUN_004 assert HTTP 404 **and** `heroElement().toHaveCount(0)`, both green
- [x] `?id=` matching the viewer renders the self face with **no redirect** — the resolver canonicalises to `self`; FUN_002 confirms the URL is preserved (its stats-card assertion fails for an unrelated fixture reason, below)
- [x] `GiftRowView.sunnerId` added via the plain `gift_awards.sunner_id` column — `/profile?id=2` clicked through
- [x] `sunner-chip` emits `?id=`, with an `id > 0` guard, comment updated — K-9 green under the narrowed pattern
- [x] `kudos-board.tsx` reads `?hashtag=`, defaulting to `null` — filter state asserted, and absent/empty/unknown all leave the shipped default
- [x] `kudos-live-board.spec.ts:354,356` narrowed, each with a recorded reason — and RED-verified before the code changed
- [x] `account-menu.tsx` untouched
- [x] typecheck + lint + build exit 0

Success criteria: `/profile?id=2` renders that Sunner with a write bar and no stat row (FUN_006 —
green); `?id=banana|42.5|99999999|1&id=2` all render the 404 page (FUN_003/FUN_004/FUN_005 — green);
`/profile?id=` renders the self face (FUN_005 — green); every board `kudos-sender`/`kudos-receiver`
href matches `/^\/profile\?id=\d+$/` and the anonymous card's sender stays a non-link (K-9 + the
masked-card link list); the hashtag click lands on a board whose **filter menu shows that tag
active**; `npm run build` exits 0.

`/profile?q=anything` is served by the resolver's absent-`id` branch (phase 06, unchanged here) —
the shipped Sunner-search box still works and does not 404.

## Deviations from the phase file

1. **`lib/profile/profile-queries.ts` was edited** — two hunks, the DRY hoist obligation F asked
   for. The phase file does not list that path, and the prompt's freeze list names it; recorded
   above rather than buried.
2. **`?hashtag=` carries the bare tag name, no `#`.** Step 6 is silent on this and the probe got it
   wrong first. § 3.
3. **`getProfileData` is called with the client as its first argument**, per phase 05's deviation 1,
   not the `(targetId, viewer)` shape the architecture block sketches.
4. **The page creates a Supabase client that `getPageContext()` does not share.** Two clients per
   request, which is exactly what the shipped `/kudos` page does (`getPageContext()` +
   `getKudosBoard()`); `getPageContext` does not expose its own. The NFR's "one client per request"
   is honoured to the same degree as the screen it was written from.
5. **The `?id=` proofs and the hashtag proof are probe transcripts, not durable tests.** The phase
   file permits only two lines of change in the one e2e file this phase owns, so a durable test for
   either link cannot live here. Named as a gap, not papered over — see handover 3.
6. **`npm run build` was run, and so were the suites.** Step 9 says not to run the full Playwright
   suite in this phase; the prompt's verification section overrides that and requires the F004
   regression plus a real profile-suite run. The prompt won.

## What phase 10 inherits

1. **Five profile-suite failures, all test-side. None is an absent element.**

   - **`FUN_010` (:405), `FUN_012` (:446), `SEC_002` (:595)** — `getByText("Đã gửi")` is a
     strict-mode violation on the self view: it matches the dropdown option *and* the statistics
     card's label `Số Kudos bạn đã gửi:`.
     ```
     strict mode violation: getByText('Đã gửi') resolved to 2 elements:
       1) <span …>Số Kudos bạn đã gửi:</span>
       2) <button role="option" data-testid="profile-direction-option">Đã gửi (0)</button>
     ```
     This is the **same defect class** `reports/tester-profile-testcase-repair.md` repaired in
     `FUN_009`/`FUN_011`, and that report states these three were "verified unaffected" — the
     verification ran against a `setContent` harness containing only the dropdown, so it could not
     see the stats card. On the real page they are affected. The fix is the same one that report
     already applied twice (`getByTestId("profile-direction-option").filter({ hasText: … })`), it is
     *stronger* than what is there, and neither copy string can move: the stats labels are reused
     verbatim from the board sidebar (AMEND-3) and the direction labels are bound by SCR006 § 3.
   - **`FUN_002` (:136) and `GUI_001` (:197)** — both assume the `profile-authed` session **is**
     seeded sunner 1. It is not: `profile-auth.setup.ts` signs up a brand-new user every run, which
     has no `sunners` row at all, and clarifications A4 makes that the *normal* authenticated case.
     So `?id=1` correctly resolves to **another** Sunner (write bar, no stats card) and bare
     `/profile` correctly renders the sparse self view whose name is the email local-part
     (`e2e-1788849859215-…`), not `Huỳnh Dương Xuân Nhật`. Measured proof the branch itself works:
     `FUN_005`'s "empty `?id=` renders the self view" asserts the same `profile-stats-card` and
     **passes**. Two ways out, both outside this phase's ownership: link the setup's auth user to
     `sunners.id = 1`, or stop the fixture assuming the viewer is the frame viewer. No
     implementation answer exists — provisioning a `sunners` row on a GET is forbidden by BR-001,
     and phase 05 measured that the read path provisions nothing.

2. **`TC_WEB_PROFILE_FUN_015` currently passes vacuously.** It looks for the hashtag as
   `card.locator("a").filter({ hasText: /#\w+/ })`, but `kudos-hashtag-row.tsx:32` renders a
   `<button>`, so the locator resolves to nothing, `isVisible()` is false, and the entire body —
   including both URL assertions — is skipped. It would keep passing if the link were deleted
   outright. The real behaviour is proven in this phase's probe; the durable test needs
   `getByTestId("kudos-hashtag")` and, per clarifications, an assertion on the board's **filter
   state** rather than the URL.

3. **Neither new link has a durable test for its *destination*.** K-9 pins the href shape on the
   board, which is real coverage; nothing durable asserts that following it renders the right
   person, or that `?hashtag=` filters. Both are proven here by probe
   (`evidence/phase-09-probe-source.log`) and both belong in `e2e/**`, which is phase 10's.

4. **`SEC_002`'s durable coverage is still the gap phase 05 named.** It now fails earlier, on the
   ambiguous locator, so it has not yet exercised its own subject. When the locator is fixed, note
   that its only assertion after switching to the Sent list is `expect(feedArea).toBeVisible()` —
   it will pass whether or not the author's own anonymous card is there. Phase 05's M3b–M3g are the
   behaviour it should be asserting.

5. **The keyvisual origin question is open and untouched** (fact H / phase 07's unresolved question
   2). If the visual diff calls it out, the fix belongs in `app/profile/page.tsx`, and the page is
   now a 143-line composition with room for a page-level layer.

6. **The database is at `kudos=58 anon=1 auth_users=0 linked=0`** after a final `db reset`.

## Unresolved questions

1. **`FUN_002`/`GUI_001` need a decision, not a repair.** Making the e2e session own `sunners.id = 1`
   changes what *every* profile-authed case exercises — the sparse self view (A4, the case
   `GUI_009` covers and the one real signups actually hit) would stop being the default. Changing
   the two fixtures instead keeps that coverage but drops the only assertions that the seeded frame
   viewer's own profile renders. Whichever way it goes, it is a test-design call above this phase.
2. **The `?hashtag=` read is initial-state-only, and a client-side navigation to a *different* tag
   while already on `/kudos` would not re-filter.** No surface does that today — the board's own
   hashtag click sets state directly, and the profile's push is a cross-route navigation that
   remounts the board (measured working). Making it reactive would mean either syncing state to the
   URL on every filter click (a shipped-behaviour change to F004, and 27 assertions) or a
   `useEffect` that fights the user's own selection. YAGNI, and named so nobody reads the current
   shape as an oversight.
3. **ADV-4 stands unchanged** (phase 05): the profile does one extra `fetchReceivedCounts` read per
   page and `fetchReceivedAggregate` reads every received row to sum hearts, which truncates at
   `max_rows = 1000`. Nothing here made it better or worse.
4. **Carried from phases 03/04/05:** `anon`/`authenticated` still hold blanket
   `INSERT`/`UPDATE`/`DELETE` grants on `public.kudos` and `public.kudos_readable` (inert under
   RLS). The `SELECT` revoke — the one this feature exists to deliver — was re-read live this phase
   and is intact.
