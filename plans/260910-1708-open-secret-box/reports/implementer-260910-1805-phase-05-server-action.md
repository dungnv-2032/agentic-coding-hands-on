# Implementer report — phase 05: server action, queries, profile unlock

**Phase:** 05 — Track B (server action, queries, profile button unlock)
**Scope:** `lib/secret-box/queries.ts` (new), `app/kudos/secret-box/_actions/open-secret-box.ts`
(new), `app/profile/_components/profile-stats-card.tsx` (modify)

## What shipped

### `lib/secret-box/queries.ts` (37 lines)
`fetchUnopenedCount(supabase, sunnerId): Promise<number>` — one `select
secret_box_unopened_count ... eq(id) ... maybeSingle()`. A missing row returns `0` instead of
throwing, matching § 3.1 step 2's "no session / no roster row" collapse into an inert zero-count
screen. Client is always an argument, never created inside — same discipline as
`lib/rules/queries.ts` / `lib/profile/profile-queries.ts`.

### `app/kudos/secret-box/_actions/open-secret-box.ts` (76 lines)
`"use server"`, `openSecretBox(): Promise<OpenSecretBoxResult>` — **no parameters**, mirroring the
SQL function. Calls `supabase.rpc("open_secret_box")`, maps `error.code`:
- `28000` → `{ ok: false, reason: "unauthenticated" }`
- `P0002` → `{ ok: false, reason: "no-boxes" }`
- anything else → `console.error(code)` (errcode only, never message text) then
  `{ ok: false, reason: "failed" }`

`data?.[0]` handles the array `returns table` hands back; an empty array on a nominal success is
also treated as `failed` rather than assumed non-empty. `revalidatePath` fires for
`/kudos/secret-box`, `/kudos`, `/profile` — success path only, inside the `if (error)` early
returns so a rejected call touches zero route caches.

### `app/profile/_components/profile-stats-card.tsx` (95 lines, +14/-10)
`<button type="button" disabled>` → `<Link href="/kudos/secret-box">`, copying
`kudos-sidebar.tsx`'s `secret-box-button` idiom (`transition-opacity hover:opacity-90`, same
token set otherwise). `data-testid="profile-secret-box-button"` preserved; accessible name stays
exactly `Mở Secret Box` (the `<span>` text is unchanged, `IconGift` stays `aria-hidden`). Docblock
above it now states the real rule instead of "deferred commission" (see next section for why no
`isSelf` prop was added).

## The "other profile" question — verified, not assumed

Read `lib/profile/profile-data.ts` and `app/profile/page.tsx` before deciding this. Confirmed:
`getProfileData()` sets `stats: isSelf ? {...} : null` — one branch, decided once
(`profile-data.ts:5-9`'s own comment: "The self/other branch is decided EXACTLY ONCE, here"). `
app/profile/page.tsx` never renders `ProfileStatsCard` when `stats` is `null` — it renders
`WriteKudoBar` instead (grep confirms `ProfileStatsCard` and `WriteKudoBar` are the only two
consumers of `vm.stats`/the two branches). So `ProfileStatsCard` is unreachable on another
Sunner's profile; it never receives a "disabled on someone else's page" case to handle, and adding
an `isSelf` prop to re-derive that would just duplicate a decision the data layer already made
(exactly the anti-pattern SC-002/plan.md § Key Insights calls out). No such prop was added.

## Live database verification

Used the existing e2e test user from `e2e/.auth/secret-box-credentials.json` (`sunnerId: 10`,
created by phase 01's setup) and called the RPC exactly as the action does — through
`POST /rest/v1/rpc/open_secret_box` with that user's real access token — rather than inventing a
new one. State restored to its pre-verification baseline (`unopened=5, opened=0`, 0 openings)
afterward so it doesn't interfere with the tester's later GREEN run.

```
$ docker exec supabase_db_my-app psql ... "update sunners set secret_box_unopened_count=2, secret_box_opened_count=0 where id=10"
UPDATE 1

$ curl -X POST http://127.0.0.1:54321/rest/v1/rpc/open_secret_box -H "Authorization: Bearer $TOKEN" -d "{}"
[{"rule_item_id":7,"label":"STAY GOLD","image_path":"/images/rules/icon-stay-gold.png","unopened_count":1,"opened_count":1}]
HTTP_STATUS:200

$ curl ... (second open)
[{"rule_item_id":9,"label":"BEYOND THE BOUNDARY","image_path":"/images/rules/icon-beyond-the-boundary.png","unopened_count":0,"opened_count":2}]
HTTP_STATUS:200

$ curl ... (third open, count already 0)
{"code":"P0002","details":null,"hint":null,"message":"no unopened secret boxes remain"}
HTTP_STATUS:500   # error.code === "P0002" is what the action reads — confirmed independent of HTTP status

$ docker exec supabase_db_my-app psql ... "select * from secret_box_openings where sunner_id=10"
 id | sunner_id | rule_item_id |           opened_at
----+-----------+--------------+-------------------------------
  1 |        10 |            7 | 2026-09-10 11:11:44.197773+00
  2 |        10 |            9 | 2026-09-10 11:11:51.566332+00
(2 rows)

$ docker exec supabase_db_my-app psql ... "select secret_box_unopened_count, secret_box_opened_count from sunners where id=10"
 secret_box_unopened_count | secret_box_opened_count
----------------------------+-------------------------
                          0 |                       2
```

Confirmed against the running database: the response shape exactly matches
`OpenSecretBoxResult`'s success mapping, exactly one `secret_box_openings` row per open, the
counter pair moves in lockstep (`unopened - 1`, `opened + 1`), and a refused open at 0 boxes
returns `code: "P0002"` which the action maps to `reason: "no-boxes"`. State was reset to
`unopened=5, opened=0, 0 openings` afterward.

One incidental finding, not a defect: calling the RPC with the anon key and **no** bearer token at
all returns `42501` (`permission denied for function`), not `28000` — the migration revokes
`EXECUTE` from `anon` entirely, so an unauthenticated PostgREST call never reaches the function
body's `auth.uid() is null` check. `28000` is reachable only from an `authenticated`-role JWT
whose `sub` somehow resolves to no user, which this app's session model does not produce. The
action's `failed` catch-all already covers `42501` correctly (verified: it logs the code and
returns `reason: "failed"`), so no change was needed — noted here so nobody mistakes the
`28000` branch for dead code.

## Verify commands

```
$ npm run typecheck    # exits 0
$ npm run lint          # 0 errors, 30 pre-existing warnings all in e2e/** (tester's scope, untouched)
$ npx eslint app/profile/_components/profile-stats-card.tsx app/kudos/secret-box/_actions/open-secret-box.ts lib/secret-box/queries.ts
                         # zero output — clean
$ grep -rn "resolveSidebarSunnerId" lib/secret-box app/kudos/secret-box   # no match (exit 1)
```

## Expected regression — do not revert

`TC_WEB_PROFILE_GUI_005` (`e2e/profile.spec.ts:415`) asserts
`await expect(button).toBeDisabled()` on `profile-secret-box-button`. That assertion is now false
by design: the button is a real `<Link>`. This is the exact, called-out consequence of plan.md's
dependency note ("05 knowingly reds `TC_WEB_PROFILE_GUI_005`; 07 re-aims it") and
phase-05's own Implementation Step 6. Left as-is; not reverted.

## File ownership check

`git status --porcelain` shows only `app/profile/_components/profile-stats-card.tsx` modified
among this phase's three owned files, plus the two new files (untracked, under their owned
directories: `app/kudos/secret-box/_actions/`, `lib/secret-box/`). Every other pending change in
the working tree (`e2e/**`, `lib/i18n/messages/**`, `playwright.config.ts`, phase 04's
`app/kudos/secret-box/_components/`) belongs to the concurrently-running phases 01/02/03/04 and
was not touched here. `lib/secret-box/contract.ts` (phase 02) was read, not modified.

## Todo list (phase-05-server-action-and-queries.md)

- [x] `fetchUnopenedCount` written, missing row → `0`
- [x] Action is parameterless and typed to `OpenSecretBoxResult`
- [x] Error mapping keyed on `code`, not message text
- [x] `data?.[0]` handled; empty array → `failed`
- [x] Three `revalidatePath` calls, success path only
- [x] Profile button is a `<Link>` with the testid, name and tokens intact; docblock refreshed
- [x] typecheck + lint exit 0

**Status:** DONE
**Summary:** `lib/secret-box/queries.ts` and the parameterless `openSecretBox` Server Action are
built and verified live against the running database (two successful opens with badge + counter
movement, one correctly-refused open at zero, exactly one `secret_box_openings` row per open); the
profile stats card's Secret Box button is now a real `<Link>` to `/kudos/secret-box`, reachable
only on the viewer's own profile because `ProfileStatsCard` itself never mounts on anyone else's.
**Concerns/Blockers:** None. One informational note recorded above: an unauthenticated call
without a bearer token surfaces Postgres `42501` (permission denied), not the `28000` this action
also maps — both are already handled correctly (`42501` falls through to `reason: "failed"`), this
is just documentation of an edge the migration's own `revoke execute` produces. As directed,
`TC_WEB_PROFILE_GUI_005` in `e2e/profile.spec.ts` now fails (button asserted disabled, now
enabled) — this is intentional and owned by phase 07, not reverted here.
