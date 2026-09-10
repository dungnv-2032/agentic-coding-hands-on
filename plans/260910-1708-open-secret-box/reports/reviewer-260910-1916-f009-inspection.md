# Reviewer Report — F009 Open Secret Box

**Branch:** `feat/open-secret-box` · **Base:** `main` (`ab80d35`) · **Migration commit:** `abd0d1a`
**Scope:** full feature — migration, seed, `lib/secret-box/*`, page + 3 components, server action, profile
unlock, i18n, e2e (`secret-box.spec.ts`, `secret-box-anon.spec.ts`, capture specs, fixtures, `playwright.config.ts`)
**Depth:** full read + live verification against the running Supabase DB, plus a live re-run of both gate suites.

## Assessment

Clean. This is the second Postgres/RLS feature in the repo (after F004) and the first to use
`security definer`; it holds the bar F004 set and gets the privileged-function boundary right in every
place I could find to push on it. I re-derived the three claimed mitigations against the live DB rather
than trusting the migration's comments or `permissions.md`, and all three held. I also ran the actual
concurrency race (10 parallel calls against a 5-box account) rather than trusting the `> 0` guard from
reading the SQL, and it produced exactly 5 successes / 5 `no-boxes`, counter landed on exactly 0, 5
`secret_box_openings` rows — no double-spend, no negative count, no orphaned row. Both gate suites
(`secret-box.spec.ts` 10/10, `secret-box-anon.spec.ts` 5/5) pass live, `npm run typecheck` is clean,
`npm run lint` is 0 errors / 30 warnings (29 pre-existing + 1 new, see Low). No critical or high findings.

## Critical

None.

## High

None.

## Medium

**M1 — SB-04 doesn't perform a second click; it only reads state after the first.**
`e2e/secret-box.spec.ts:146-177` ("double-click race is rejected, exactly one decrement") calls
`opener.click()` once, waits 100ms, and asserts the button is `disabled`/`aria-busy` at that moment. It
never issues a second click. Playwright's own actionability check already refuses to click a
`disabled` button, so this test cannot distinguish "the native `disabled` attribute is set" (true from
CSS/React state alone) from "a genuine second click attempt was rejected." The explicit JS-level guard
in `secret-box-opener.tsx:44` (`if (disabled) return;` — described in that file's own docblock as "the
second, explicit layer the plan's Risk Assessment calls for") is exercised by nothing here: delete that
line and this test still passes, because no second click is ever attempted.
**Fix:** force a real second click while pending, e.g. `await Promise.all([opener.click(), opener.click({ force: true })])`
or dispatch a raw `click` event past the `disabled` attribute, then assert the counter only moved once.
This is a test-integrity gap of the exact class the task asked me to hunt for (SB-07/SB-08/SB-A2 already
caught and fixed this session) — it isn't vacuous (it does prove the pending-state UI renders correctly)
but it doesn't prove what its own name and comment claim.

## Low

**L1 — New lint warning introduced by this branch.** `e2e/secret-box-anon.spec.ts:57` — SB-A3's
callback destructures `{ page }` but never uses it (the test drives `fetch()` directly). Not one of the
30 pre-existing warnings the task described as already-known; this one is new. Trivial fix: drop the
unused destructure or prefix `_page`.

**L2 — `fetchUnopenedCount` (`lib/secret-box/queries.ts:36`) throws `error.message` uncaught, same as
`resolveViewer()`, `fetchRuleSections`/`fetchRuleItems`, and every `profile-queries.ts` read.** No
`app/kudos/error.tsx` exists, so a Supabase read failure here surfaces through Next's generic
production error boundary rather than anything this feature adds — I checked this isn't a new leak path,
it's the codebase's existing (undocumented) convention for Server Component reads. Flagging only because
the task asked me to look hard at data leakage; I found nothing F009-specific to fix, just noting the
inherited pattern in case a future pass wants a shared `try/catch` at the page boundary across all of
these call sites at once, not just this one.

## Security — the three `security definer` mitigations (verified live, not from the comments)

Ran directly against the local Supabase Postgres, not just read the SQL:

1. **`search_path` pinned.** `pg_proc.proconfig = {search_path=public}` for `open_secret_box` — confirmed
   via `pg_proc`/`pg_roles` query.
2. **EXECUTE revoked from `anon`/`public`.** `information_schema.routine_privileges` shows only
   `postgres`, `authenticated`, `service_role` hold `EXECUTE`. Live negative test: `set local role anon;
   select public.open_secret_box();` → `ERROR: permission denied for function open_secret_box` — refused
   before the function body runs at all, not by an internal check.
3. **No identity parameter.** Confirmed via `pg_get_function_identity_arguments` → empty. There is no
   `p_sunner_id`/`p_badge_id` to forge; SB-08 additionally proves a raw RPC call with an unexpected JSON
   argument is refused by PostgREST (`403`), and a direct `PATCH` on `sunners.secret_box_unopened_count`
   is refused (no UPDATE policy exists — confirmed via `\d+ public.sunners`, only `sunners_select_all`
   and `sunners_insert_own` policies exist).

**Unauthenticated caller refused correctly.** `v_uid is null` raises `28000`, mapped by the Server Action
to `reason: 'unauthenticated'` by errcode, never by message text (`open-secret-box.ts:43`).

**Cannot act for another Sunner.** The function derives `v_sunner_id` solely from
`auth.uid()` against `sunners.auth_user_id`; there is no path — RPC argument, header, or otherwise — for
a caller to name a different sunner. `resolveViewer()` (not `resolveSidebarSunnerId()`, the seeded
display fallback) is what `page.tsx:62` and `queries.ts` actually use — confirmed by reading both call
sites and `lib/kudos/viewer.ts`'s own docblock distinguishing the two.

## Concurrency — verified with a real race, not just the `> 0` placement

The `> 0` guard sits inside the `UPDATE ... WHERE id = v_sunner_id AND secret_box_unopened_count > 0`
(`20260910170000_secret_box_open_path.sql:158-163`), not a preceding `SELECT`, so Postgres's own row
lock closes the window. I fired 10 truly concurrent `open_secret_box()` calls (10 parallel `psql`
processes, same simulated `auth.uid()`) against an account seeded with exactly 5 boxes:

- 5 calls returned a row (success), 5 raised `no unopened secret boxes remain` (`P0002`)
- Final `secret_box_unopened_count = 0`, `secret_box_opened_count = 5` — never negative, never over-spent
- `secret_box_openings` holds exactly 5 rows for that sunner — one per real success, no duplicates

`e2e/secret-box.spec.ts` SB-07 additionally proves this over real HTTP (two simultaneous `fetch()` calls
to the RPC endpoint with a bearer token) — I re-ran it live, passes.

## RLS on the two new tables — matches the F004 precedent

`secret_box_badge_odds`: `select` open to `anon, authenticated` (`using (true)`) — intentional, odds are
printed in the design. No insert/update/delete policy.
`secret_box_openings`: `select` restricted to own rows via
`exists (select 1 from sunners s where s.id = sunner_id and s.auth_user_id = (select auth.uid()))` — the
same bridge-through-`sunners` idiom as `kudos_likes_delete_own`. No insert/update/delete policy anywhere
— confirmed via `pg_policies`, exactly 2 policies total across both tables, both `SELECT`. The broad
`GRANT ALL`-shaped rows in `information_schema.role_table_grants` are Supabase's own platform-level
default ACL (same finding as F004, see memory) — RLS is the effective gate, and every insert into either
table only ever happens inside the `security definer` function.

## The public route (`/kudos/secret-box`)

`proxy.ts` untouched, confirmed by `git diff main --stat` showing no route/middleware file in the diff.
The screen resolves `200` for every visitor (verified live via SB-A1); entitlement is enforced entirely
by (a) the inert face — no sign-in link when authenticated-but-no-`sunners`-row, count `00`, opener
`disabled` — and (b) the EXECUTE grant, which is the only place that actually matters since a client
could bypass the UI and hit the RPC directly (SB-A3 does exactly that, gets refused). Nothing in
`page.tsx` or `queries.ts` reaches for `resolveSidebarSunnerId()`.

## The Server Action (`open-secret-box.ts`)

- No arguments — confirmed, matches the SQL function's own zero-argument signature.
- Error mapping is by `error.code` (`28000`, `P0002`) only; the `default` branch logs `error.code` alone
  via `console.error`, never `error.message`, and the raw Postgres error never enters the returned
  `OpenSecretBoxResult` — confirmed by reading the full function body, there is no other path back to
  the client.
- Empty-array result (`data?.[0]` undefined) is treated as `reason: 'failed'`, not assumed non-empty.
- `revalidatePath` covers `/kudos/secret-box`, `/kudos`, `/profile` — matches technical-spec § 3.2 — and
  only runs after a confirmed success, so a rejected call doesn't invalidate three route caches for
  nothing.

## The profile unlock

`profile-stats-card.tsx`'s new `<Link href="/kudos/secret-box">` only ever renders on the viewer's own
profile. I didn't just accept the component's docblock claim ("`ProfileStatsCard` itself is only
mounted when `stats !== null`, which is true iff `isSelf`") — I traced it: `lib/profile/profile-data.ts`'s
own docblock states this is a pre-existing invariant from F006 (not introduced by this diff), and
`app/profile/page.tsx:122-128` shows the single `vm.stats !== null ? <ProfileStatsCard/> : vm.writeKudoTargetId !== null ? <WriteKudoBar/> : null` branch — there is no code path where `ProfileStatsCard`
(and therefore this button) renders for anyone but the viewer's own profile. Even if it somehow did, the
button only navigates to `/kudos/secret-box`; opening a box still only ever acts on the *caller's own*
session via `auth.uid()`, so there's no cross-account write surface here even hypothetically. The
`e2e/profile.spec.ts` `GUI_005` rewrite independently confirms both faces (own profile: enabled link with
correct `href`; another's profile: stats card and button both absent) — re-ran it live as part of the
authed suite context; passes.

## Test integrity — audited adversarially per the task's ask

Two classes the task named as already caught this session (SB-07/SB-08 authenticating as `anon`, SB-A2
passing against the old placeholder) are fixed in the current files — I read the current
`getAuthenticatedToken()` path in `secret-box.spec.ts` and confirmed it signs in with real credentials via
`signInWithPassword`, not the anon key, before hitting the RPC. `SB-A2` now asserts on
`data-testid="secret-box-panel"` / `secret-box-opener` / `secret-box-signin`, none of which exist on the
old `ComingSoon` placeholder, so it cannot pass against the pre-F009 code — confirmed by checking those
`data-testid`s only exist in the new components.

One more of that class found: **M1 above (SB-04)**. I did not find others — SB-01/02/03/05/06/09 and
SB-A1/A3/A4 each assert on a concrete, feature-specific DOM state or HTTP status that the old placeholder
or a broken implementation could not produce by accident (e.g. SB-03's badge `alt` must be one of the six
real `rule_items.label` values; SB-A3 asserts a `4xx` status specifically from the RPC endpoint, not just
"some non-200"; SB-05 reads the actual DB row via the service-role fixture rather than trusting the UI
alone).

## Done Well

- The weighted draw (`order by random() ^ (1.0/weight) desc limit 1`, Efraimidis-Spirakis) is correct
  for single-item weighted sampling and the seeded weights (30/25/20/10/10/5) match BR-003 exactly —
  verified by querying the live table, not just reading the `insert`.
- DEC-03 (odds rows in `seed.sql`, not the migration) is the right call and the migration's own comment
  explains why — verified this actually matters: `rule_items` content itself lives in `seed.sql`, so a
  migration-time label join would silently match zero rows on `db reset`.
- The provisioning block's `Unassigned` department dependency isn't a landmine — I checked it's
  guaranteed by the earlier `20260907025909_viet_kudo_write_path.sql` migration, not assumed.
- Test fixtures (`secret-box-grant.ts`) read the service-role key at runtime from `npx supabase status
  -o json` and write nothing to disk but email/userId — no committed secret, no product-code test branch.
- `formatBoxCount` living in the shared `contract.ts` (not duplicated between the render and the e2e
  assertions) closes off a whole class of "test padding rule drifted from render padding rule" bug before
  it could happen.

## Edge Cases Turned Up

- Zero-box account calling the RPC: refused server-side (`P0002`), not just UI-disabled — confirmed live
  with a real zero-box row.
- Fresh account with no `sunners` row at all: provisioning path runs, lands at `unopened_count = 0`
  (grants nothing), then the same `> 0` guard still refuses the open in the same call — read through the
  function body, this can't leave a half-provisioned state since it's all one transaction.
- Odds table empty (hypothetical/future misconfiguration): function raises `P0001` rather than decrementing
  a box for nothing and returning no badge — read and confirmed in the SQL, not exercised live (would
  require deleting seed data).

## Actions In Order

1. Strengthen SB-04 to issue a genuine second click and assert only one decrement resulted from it (M1).
2. Drop the unused `page` param in SB-A3, or prefix it `_page` (L1).
3. Optional, not blocking: consider a shared error boundary for the `lib/*/queries.ts` throw-on-error
   convention repo-wide (L2) — out of scope for this feature, pattern predates it.

## Numbers

- Files reviewed: 24 (migration, seed diff, 2 lib modules, page + 3 components, 1 action, 1 modified
  component, 5 i18n files, 6 e2e/fixture files, `playwright.config.ts`)
- `npm run typecheck`: 0 errors
- `npm run lint`: 0 errors, 30 warnings (29 pre-existing, 1 new — L1)
- Live test run: `secret-box.spec.ts` 10/10, `secret-box-anon.spec.ts` 5/5, both exit 0 (re-run by me,
  not just taken on the tester report's word)
- Live concurrency probe: 10 parallel calls / 5 boxes → 5 success, 5 `P0002`, final count exactly 0

## Still Unresolved

None blocking. M1 and L1 are the only actionable items; neither is a security or correctness defect in
the shipped behavior, both are test-file quality improvements.

**Status:** DONE
**Summary:** F009's security-definer boundary, concurrency guard, and RLS shape all held under live
verification (not just static reading) — no critical or high findings. One medium test-integrity gap
(SB-04 never actually double-clicks) and one new lint warning are the only actionable items.
**Concerns/Blockers:** None.
