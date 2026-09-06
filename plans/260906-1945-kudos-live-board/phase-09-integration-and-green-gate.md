# Phase 09 — Integration & the GREEN gate

**Track:** Shared (the two tracks meet) · **Owner:** `implementer` · **Depends:** 04, 07, 08 ·
**Effort:** 1.5h · **test_policy:** `e2e-red-first`

## MoMorph refs:
- Sun* Kudos - Live board: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/MaZUn5xHXZ
- Clarifications: plans/260906-1945-kudos-live-board/clarifications.md
- testPolicy: e2e-red-first

## Context Links

- [plan.md](plan.md) — every phase · [phase-04](phase-04-typed-data-layer-and-like-action.md) (`getKudosBoard`, `toggleKudosLike`) · [phase-05](phase-05-ui-foundation-i18n-icons-hero-sidebar.md) · [phase-07](phase-07-ui-board-filters-carousel-feed.md) · [phase-08](phase-08-ui-spotlight-board.md)
- [test-contract.md](test-contract.md) — the whole file, including § "Supabase amendment"
- [RED gate](../reports/tester-260906-1958-kudos-red-gate.md) — the exact command and the 26 assertions
- Evidence to match against: [evidence/kudos-red-run.log](evidence/kudos-red-run.log)
- Shell to copy: `app/awards-information/page.tsx:55-126` · `app/_components/coming-soon.tsx` (the
  `signOutAction` prop pattern at line 29)

## Overview

**Priority:** P1 · **Status:** delivered.

One file of real work — `app/kudos/page.tsx` — plus the run that takes the suite from 26 failed to
26 passed. This is the only phase that changes what a user sees, and the only one whose rollback is
a single-file revert.

## Key Insights

1. **This phase owns `app/kudos/page.tsx` alone.** Track A never imports Track B and Track B never
   imports Track A; the page is the seam, so exactly one phase writes it. Until now it has rendered
   `ComingSoon`, which is why every earlier phase left the app working.
2. **The Server Action travels as a prop.** `page.tsx` imports `toggleKudosLike` and passes it into
   `kudos-board.tsx` as `toggleLike` — the pattern already shipped at
   `app/_components/coming-soon.tsx:29` for `signOutAction`. Track A's components stay free of any
   Track B import.
3. **The metadata title is not up for redesign.** `app/kudos/page.tsx:5` already reads
   `"Sun* Kudos — Sun* Annual Awards 2025"`; keep it byte-identical.
4. **The chrome is composed, not rebuilt** — `HomeHeader`, `SiteFooter`, `getPageContext()`, the
   `bg-[#00101A]` wrapper and both font variables, exactly as `app/awards-information/page.tsx:66-68`
   does it. No `FloatingWidget`, no `KudosPromo`: this screen *is* Kudos.
5. **`db reset` runs before the suite, never during it.** The seed must be applied and
   `auth.users` truncated *before* Playwright's `setup` project signs up its fresh user. Running it
   mid-run pulls the session out from under the authed project and `proxy.ts:41-46` bounces the
   browser. Nothing in `package.json` or `playwright.config.ts` may call it.
6. **A vacuous pass is a failure.** K-25 returns early if the first card's heart is disabled, and
   K-10 skips its assertions the same way. Both must be confirmed to have *executed* their
   assertions, not merely reported green — the heart on the top card must be enabled for the authed
   viewer (phase 01 § Key Insight 2, phase 03 § Key Insight 9).
7. **The draft ERD needs reconciling.** `technical-spec.md § 4.2` types ids as `uuid`; the shipped
   schema uses `bigint generated always as identity`, adds `sunners.kudos_received_baseline` and
   `departments.filter_position`, and points `kudos_likes.user_id` at `auth.users`. This phase
   updates the draft so promote does not carry a contradiction forward.

## Requirements

**Functional:** every FR the plan touches becomes observable here — FR-101, FR-201…FR-207,
FR-401…FR-403, FR-601, FR-602 — plus BR-001…BR-004, DEC-001…DEC-003, SM-001, ALG-001, ALG-002.

**Non-functional:** `app/kudos/page.tsx` ≤200 lines (the shell is thin by design); one
`getPageContext()` call and one `getKudosBoard()` call per request; the Supabase `user` object never
crosses into a Client Component; the 26 assertions pass with no assertion, locator, or timeout
weakened and no test skipped.

## Architecture

```
GET /kudos
  └─ app/kudos/page.tsx  (async server component, ≤200 lines)
       ├─ getPageContext()            → locale, dictionary, isAuthenticated, isAdmin
       ├─ getKudosBoard()             → KudosBoardViewModel                (phase 04)
       ├─ <HomeHeader …/>                                                  (unchanged)
       ├─ <main>
       │    ├─ <KudosHero copy/>                                           (phase 05, server)
       │    ├─ <KudosBoard board copy toggleLike={toggleKudosLike}/>        (phase 07, client)
       │    ├─ <SpotlightBoard nodes ticker copy/>                          (phase 08, client)
       │    └─ <KudosSidebar copy counts gifts/>                            (phase 05, server)
       └─ <SiteFooter dictionary/>
```

Page order is fixed by clarifications § "Resolved from source data": header → hero → HIGHLIGHT
KUDOS → SPOTLIGHT BOARD → ALL KUDOS + sidebar → footer. The sidebar sits beside the ALL KUDOS
section, and both live inside `<main>`.

## Related Code Files

**Modify:** `app/kudos/page.tsx` (replace the `ComingSoon` body; keep the `metadata` export) ·
`spec/kudos-live-board/technical-spec.md` (§ 4.2 ERD id types + the two added columns)
**Read only:** every phase 04–08 artifact, `app/awards-information/page.tsx`,
`app/_page-context.ts`, `app/_fonts.ts`
**Create:** none · **Delete:** none

## Implementation Steps

1. Rewrite `app/kudos/page.tsx` per § Architecture. Keep the `Metadata` export exactly as it is;
   replace only the component body.
2. `npm run typecheck && npm run lint`.
3. `npm run build` — the first check that the whole graph resolves, including the committed
   generated types, with no live database needed at build time.
4. Apply the data: `npx supabase db reset`. Confirm it exits 0 and that phase 03's count query
   still returns `50, 13, 50, 0, 1000, 7` (likes back at 0 — a previous test run may have added
   rows, and the reset is what clears them).
5. Run the gate, the exact RED command, unchanged:
   ```
   npx playwright test e2e/kudos-live-board.spec.ts e2e/kudos-live-board-authed.spec.ts --reporter=list
   ```
6. Confirm the two authed tests did not take their early-return branch: in the run, the top card's
   heart must be enabled. If K-10/K-25 pass without asserting, treat the phase as **incomplete** —
   the cause is a viewer-identity regression (phase 01 § Key Insight 2), not a test to relax.
7. For any remaining failure, fix the owning phase's files — never the spec, the fixtures, or the
   assertions. Contract-level surprises go back to the orchestrator.
8. Save the green log beside the red one: `evidence/kudos-green-run.log`.
9. Update `technical-spec.md § 4.2` per Key Insight 7: ids to `bigint identity`,
   `kudos_likes.user_id` → `auth.users`, and the two added columns with their one-line reasons.
10. Hand off to `tester` for the visual pass (Playwright MCP capture against the frame). Known and
    accepted visual differences from the frame, so the tester does not report them as defects:
    the edit pen is absent for anon and for the fresh authed user (correct per FR-204, since
    neither is the sender), and every avatar/attachment is the single committed sample (A3).

## Todo List

- [ ] `app/kudos/page.tsx` rewritten; `metadata` untouched; ≤200 lines
- [ ] Chrome composed, not rebuilt; no `FloatingWidget`, no `KudosPromo`
- [ ] `toggleKudosLike` passed as the `toggleLike` prop, not imported by any Track A file
- [ ] `npm run typecheck && npm run lint && npm run build` all exit 0
- [ ] `npx supabase db reset` before the suite; nothing calls it during
- [ ] The exact RED command exits 0 — 26 passed
- [ ] K-10 and K-25 verified to have executed their assertions, not returned early
- [ ] `evidence/kudos-green-run.log` saved
- [ ] `technical-spec.md § 4.2` reconciled with the shipped schema
- [ ] Handed to `tester` for visual validation, with the two accepted differences stated

## Success Criteria

- `npx playwright test e2e/kudos-live-board.spec.ts e2e/kudos-live-board-authed.spec.ts --reporter=list`
  exits **0**: 26 passed, 0 failed, 0 skipped.
- `git diff` touches no file under `e2e/` — not a spec, not a fixture, not the config.
- K-25 demonstrably wrote a real row: after the run,
  `docker exec supabase_db_my-app psql -U postgres -d postgres -c "select count(*) from kudos_likes;"`
  returns 0 (the test toggles back), while a manual click followed by the same query returns 1.
- The rest of the suite is unharmed: `npx playwright test --reporter=list` shows no new failure in
  `homepage`, `award-system`, `login-screen`, `route-guard`, `callback-security`, or
  `authenticated`.
- `/kudos/new`, `/kudos/secret-box`, `/kudos/123`, and `/profile` all still render `ComingSoon`.

## Risk Assessment

| Risk | L×I | Countermeasure |
|---|---|---|
| K-10/K-25 pass vacuously via their early-return branch | **High** × **High** | Step 6 is a gate, not a note: the phase is incomplete until both are seen to assert. The seed guarantees an enabled top card; the fix is always in the implementation |
| `db reset` run mid-suite, signing the browser out | Med × High | Pre-suite only, stated in three places; `test:e2e` and the Playwright config stay untouched |
| A leftover `kudos_likes` row from an earlier run shifts the top card's count and breaks K-25's before/after comparison | Med × Med | Step 4's reset clears them, and step 4 re-checks the count query before the suite runs |
| The full suite regresses somewhere else (shared `setup` project, new dev-server env) | Med × High | Success criterion 4 runs the whole suite, not just the kudos specs |
| A failure is "fixed" by editing an assertion | Low × **High** | Step 7 forbids it and criterion 2 checks `git diff` over `e2e/` |
| PostgREST serves a stale schema and the page 500s at render | Low × Med | phase 02 § Risk holds the reload procedure; a 500 here is a data-layer symptom, not a UI one |
| Track A and Track B disagree about a contract field discovered only now | Low × High | The contract was frozen in phase 01 and both tracks compiled against it; any gap is an orchestrator amendment, applied once in phase 01's file |

**Rollback:** `git checkout -- app/kudos/page.tsx`. `/kudos` returns to `ComingSoon`, every other
phase's code stays on disk and inert, and no user-visible surface is left half-built. The schema
and seed can stay (nothing reads them) or come out with `npx supabase db reset` after removing the
migration.

## Security Considerations

- `getPageContext()` stays the single session read, and only `isAuthenticated`/`isAdmin` reach
  `HomeHeader` — the Supabase `user` object must not appear anywhere in `page.tsx`'s JSX
  (`app/_page-context.ts:22-25`).
- `getKudosBoard()`'s payload is the contract and nothing more: no `auth_user_id`, no email, no
  other viewer's user id.
- The route stays public and unguarded, matching the settled decision; `proxy.ts` is not touched,
  so `/todo` and `/login` keep their guards and nothing else gains one.
- The like path's real defence is RLS (phase 02), proven independently of the UI; this phase must
  not add a client-side check that could be mistaken for the boundary.
- No new environment variable, no new external host, no secret in the diff. `.env.example` is not
  part of this phase.

## Next Steps

- `tester` — GREEN rerun of the exact command plus the visual pass against the frame.
- `reviewer` — full-diff review once the tester is satisfied.
- `delivery-tracker` / `doc-writer` — promote the spec drafts (`work_type: feature`,
  `spec_draft`, `system_doc_drafts` in `plan.md`'s frontmatter), where the `F###` code is allocated;
  it is deliberately absent from this plan.
- Carried forward, unbuilt by design: the four placeholder destinations, the special-day ×2 credit,
  account-balance accrual, the rank-up leaderboard, and the auth-guard question — all recorded in
  `clarifications.md` § Unresolved questions.
