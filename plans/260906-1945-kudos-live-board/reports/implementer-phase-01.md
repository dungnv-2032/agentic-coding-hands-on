# Implementer report — phase 01: Foundation & integration contract

**Status:** completed

## Files touched (all newly created, none pre-existing)
- `lib/kudos/view-model.ts` (+108 lines) — frozen contract types only, no runtime export
- `lib/kudos/derive.ts` (+107 lines) — 7 pure helpers (`badgeTierFor`, `badgeTooltipFor`,
  `formatHeartCount`, `formatSentAt`, `pickHighlight`, `matchesFilters`, `FEED_PAGE_SIZE`)
- `app/kudos/new/page.tsx` (+15 lines) — placeholder, renders `ComingSoon`
- `app/kudos/secret-box/page.tsx` (+15 lines) — placeholder, renders `ComingSoon`
- `app/kudos/[id]/page.tsx` (+17 lines) — placeholder, renders `ComingSoon`, no `params` prop declared/read
- `package.json` (+1 line) — added `db:types` script only, nothing else changed

`app/kudos/page.tsx` was NOT touched — confirmed via `git diff --stat` (empty), still renders
`ComingSoon` per phase 09 ownership.

## Checks
- Typecheck (`npm run typecheck`): **fails, exit 1** — but the 8 errors are all in
  `e2e/kudos-live-board-authed.spec.ts` (Locator vs Page type mismatch at 4 call sites), a
  pre-existing tester-owned file outside my scope, timestamped before this task started. Verified
  by `git stash -u` (removes all my files + all untracked files) and re-running typecheck: clean,
  0 errors — meaning the baseline before any kudos work is clean, and after stash-pop the same 8
  errors reappear, none of them in `lib/kudos/*` or `app/kudos/*`. Not fixed — out of scope
  (e2e/ is tester-owned) and not introduced by this phase.
- Lint (`npm run lint`): clean, exit 0, 27 pre-existing warnings (all in `e2e/*.spec.ts`,
  unused-var style, none in my files).
- K-21 in isolation (`npx playwright test e2e/kudos-live-board.spec.ts --grep "K-21"`): **PASS**
  (2 passed: setup + K-21). All three placeholder routes return HTTP 200 with a visible `main` and
  `main h1`.
- Full `kudos-live-board.spec.ts` run (`--reporter=list`, `anon` project): **2 passed, 23 failed** —
  the 2 passes are `[setup]` and K-21; all 23 remaining assertions (K-0 through K-23, minus K-21)
  fail on missing screen hooks (`sunner-search`, `highlight-section`, etc. don't exist on `/kudos`
  yet — `app/kudos/page.tsx` still renders `ComingSoon`), exactly as expected. Nothing weakened,
  nothing accidentally green.

## Acceptance Criteria
- [x] `lib/kudos/view-model.ts` — full contract surface (`BadgeTier`, `SunnerView`,
  `KudosAttachmentView`, `KudosCardView`, `FilterOptionView`, `SidebarCountsView`, `GiftRowView`,
  `SpotlightNodeView`, `SpotlightTickerRowView`, `KudosBoardViewModel`, `KudosLikeResult`,
  `ToggleKudosLike`), no `any`, no runtime export, no imports from `@/lib/supabase/*`
- [x] `lib/kudos/derive.ts` — 7 helpers, pure (no I/O/React/Intl), badge tooltip copy
  copy-pasted verbatim from `clarifications.md` (not retyped)
- [x] `app/kudos/new/page.tsx`, `app/kudos/secret-box/page.tsx`, `app/kudos/[id]/page.tsx` all
  render `ComingSoon`, `[id]` ignores `params` entirely (no prop declared, nothing echoed to DOM)
- [x] `package.json` — `db:types` script added, script not run (no schema exists yet)
- [x] `npm run typecheck && npm run lint` — lint clean; typecheck fails only on pre-existing
  out-of-scope file (see above), zero errors in owned files
- [x] K-21 green in isolation

## Notes / design decisions
- `formatSentAt` uses a fixed UTC+7 offset computed by hand (no `Intl`, no timezone DB) per Key
  Insight #4 — matches the e2e regex `^\d{2}:\d{2} - \d{2}\/\d{2}\/\d{4}$` (no offset assertion in
  the spec beyond the format).
- `formatHeartCount` groups digits manually (no `toLocaleString`), matching `vi-VN` grouping for
  the dot separator.
- Confirmed `app/_components/coming-soon.tsx` already renders `<main>`+`<h1>` — no gap, no edit
  needed there (it's out of scope regardless).
- Read `node_modules/next/dist/docs/01-app/03-api-reference/03-file-conventions/{page,dynamic-routes}.md`
  before writing `app/kudos/[id]/page.tsx`: in this Next version `params` is a `Promise`. Since the
  plan requires the page to ignore params entirely, I simply never declare the prop — no version-
  sensitive API used, nothing to await.

## Unresolved questions
1. The typecheck failure in `e2e/kudos-live-board-authed.spec.ts` (Locator/Page mismatch, 4 call
   sites) blocks a fully clean `npm run typecheck` at the repo level. It's tester-owned and
   pre-existing (timestamped before this task), so I left it — flagging for whoever owns that file
   next (phase 09 or the tester) since "compiles under `tsc --noEmit`" is a stated non-functional
   requirement for the contract, which it does; the repo-wide command's exit code is degraded by a
   file outside this phase's scope.
