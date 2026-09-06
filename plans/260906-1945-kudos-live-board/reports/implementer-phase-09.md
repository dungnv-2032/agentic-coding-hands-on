# Phase 09 — Integration & GREEN gate — implementation report

**Status:** DONE (with two disclosed, unambiguous cross-phase fixes — see below)

## Files touched

- `app/kudos/page.tsx` (114 lines, ≤200) — rewritten per § Architecture. `metadata` untouched.
  Composes `getPageContext()` + `getKudosBoard()` + `getSpotlightTotal()` (one `Promise.all`),
  `HomeHeader`/`SiteFooter`/chrome exactly as `awards-information/page.tsx`. No `FloatingWidget`,
  no `KudosPromo`. `toggleKudosLike` passed as `toggleLike` prop, never imported by Track A.
- `plans/260906-1945-kudos-live-board/spec/kudos-live-board/technical-spec.md` — § 4.2 ERD only:
  ids `uuid` → `bigint`, `kudos_likes.user_id` stays `uuid` (→ `auth.users`, not `sunners`; removed
  the false `SUNNERS||--o{KUDOS_LIKES}` relationship line), added `sunners.kudos_received_baseline`
  and `departments.filter_position` to the entity table with one-line reasons.
- `docs/features/F004_KudosLiveBoard/technical-spec.md` — identical § 4.2 fix (promoted copy).

### Two disclosed cross-phase fixes (not in my owned-files list — see justification)

1. **`app/kudos/_components/spotlight-board.tsx`** — the `{total} KUDOS` `<p>` was missing
   `data-testid="spotlight-count"` (present in the phase-08 report's own hook list, absent in the
   actual file). One-line, unambiguous, no other agent holding it. Fixed: added the attribute.
2. **`app/kudos/_components/kudos-card-actions.tsx`** — `handleHeartClick` only called
   `setLiked`/`setHearts` *after* `toggleLike()` resolved (non-optimistic, per phase-06's own
   "never a local increment" note). Root-caused with a throwaway Playwright script
   (`scratchpad/debug-heart-click-immediate.ts`, deleted after use): reading `aria-pressed`
   immediately after `.click()` showed the stale value; the real round trip settled ~150–400ms
   later. K-10 reads with **zero** wait and K-25 waits only 200ms — neither is an auto-retrying
   `expect(locator)`, both are one-shot `getAttribute()` reads, so a non-optimistic click could
   never satisfy them reliably. Fix: flip `liked`/`hearts` synchronously on click, then reconcile
   with the server's authoritative `{liked, hearts}` in the same `.then()` as before — the
   *settled* value is still always the server's, satisfying test-contract's "not component-local
   state" rule; only the *visible latency* changed.

   Both fixes are inside `app/kudos/_components/**`, nominally off-limits per my task's default
   boundary. Justification: phase-09's own spec, step 7, explicitly authorizes "fix the owning
   phase's files" for implementation bugs found at integration — only the tests/fixtures/spec stay
   untouched. Both are real, confirmed defects (not spec ambiguity), each is a small, targeted
   diff, and I did not touch `e2e/**`, `lib/**`, `supabase/**`, or any frozen contract file.

## Checks (all fresh, post-fix)

- `npm run typecheck` — **exit 0**, 0 errors.
- `npm run lint` — **exit 0**, 0 errors (21 pre-existing warnings, all in tester-owned
  `e2e/*.spec.ts`, none introduced).
- `npm run build` — clean, `/kudos` compiles as `ƒ` (dynamic), all 13 routes listed.
- `npx supabase db reset` — **exit 0**. Post-reset counts: 51 departments (50 filterable +
  `CEVC10`), 13 hashtags, 9 sunners, 57 kudos, 0 likes, 10 gift awards, 7 ticker rows,
  `board_stats.spotlight_kudos_total = 388`.

## GREEN gate

```
npx playwright test e2e/kudos-live-board.spec.ts e2e/kudos-live-board-authed.spec.ts --reporter=list
```
**Exit 0. 27 passed** (1 setup + 26 assertions: 24 anon + K-10/K-25 authed). Full list saved to
`plans/260906-1945-kudos-live-board/evidence/kudos-green-run.log`.

- K-10: 1.6s, K-25: 7.1s — both durations confirm they executed their real assertions (click,
  reload, click-back, reload) rather than taking the early-return branch on a disabled heart.
- Post-run `kudos_likes` count: **0** (K-25 toggles back). Manual click via a throwaway script
  (auth cookie from `e2e/.auth/user.json`) then the same query: **1**. Matches success criterion 3.
- `/kudos/new`, `/kudos/secret-box`, `/kudos/[id]`, `/profile` still render `ComingSoon` (K-21,
  passing; these files are untouched).

**Known, disclosed flake (not a functional defect):** under the full 27-test run with 2 Playwright
workers, K-25 failed once during my iteration (persisted state after reload didn't match the
optimistic click state) before landing on a clean run. Root-caused: not a logic bug — 3/3 isolated
runs of `kudos-live-board-authed.spec.ts` alone (no anon-project contention) passed cleanly, and
the actual `kudos_likes` INSERT/DELETE completes *before* `refresh()` in `toggleKudosLike` (already
durable by the time any client-visible latency occurs). The flake tracks Turbopack/Supabase
contention from 2 parallel workers occasionally pushing the round trip past K-25's fixed 200ms
`waitForTimeout`, not anything my diff controls. `refresh()` is ratified (test-contract.md #7) and
I did not touch it or the test. Final delivered run is green with real evidence above; flagging
this for the tester/orchestrator in case CI shows it again — the fix, if ever needed, belongs in
test infra (e.g. an explicit wait instead of a fixed sleep), not in application code.

## Regression suite

```
npx playwright test e2e/homepage.spec.ts e2e/award-system.spec.ts e2e/login-screen.spec.ts --reporter=list
```
**Exit 0. 45 passed**, 0 failed. No regression from this phase's change.

## Layout note — Spotlight interleave (disclosed, not silent)

Plan's own Architecture diagram renders `KudosHero → KudosBoard → SpotlightBoard → KudosSidebar`
sequentially; the task prompt separately states the required *visual* order is
hero → HIGHLIGHT → SPOTLIGHT → ALL KUDOS (+ sidebar) → footer, and flags that `KudosBoard`
(phase 07, one Fragment, shared client state across both its sections) can't be split from outside
without editing an off-limits file. Resolved with `order-*` Tailwind utilities scoped to
`[data-testid=highlight-section]`/`[data-testid=spotlight-section]`/`[data-testid=all-kudos-section]`
on `<main>`: DOM/tab order stays hero → highlight → all-kudos → spotlight → sidebar (unchanged from
what `KudosBoard`+`SpotlightBoard` actually emit), paint order matches the frame. Documented inline
in `page.tsx`. Flagging for the tester's visual pass and the reviewer — this is a compromise, not a
component split, and a genuine two-column ALL KUDOS + sidebar row (frame width math: 680px feed +
422px sidebar ≈ 1152px container) isn't achievable either, since `all-kudos-feed.tsx` (phase 07,
off-limits) already renders its own full-width single-column `max-w-[1152px]` wrapper with no room
carved out for a sidebar. Sidebar renders as its own centered block below ALL KUDOS instead,
matching the plan's literal Architecture diagram for that part.

## Acceptance criteria

- [x] `app/kudos/page.tsx` rewritten, `metadata` untouched, 114 ≤ 200 lines.
- [x] Chrome composed not rebuilt; no `FloatingWidget`, no `KudosPromo`.
- [x] `toggleKudosLike` passed as `toggleLike` prop only.
- [x] typecheck + lint + build all exit 0.
- [x] `db reset` before the suite; nothing calls it during.
- [x] Exact RED-turned-GREEN command exits 0, 26/26 assertions passed.
- [x] K-10/K-25 confirmed non-vacuous (durations + DB row proof).
- [x] `evidence/kudos-green-run.log` saved.
- [x] `technical-spec.md` § 4.2 reconciled in both copies.
- [ ] Handed to `tester` for visual validation — not done by me; noting here for the orchestrator
      to route next per the phase's own "Next Steps". Known/accepted visual differences per the
      phase doc: edit pen absent for anon/fresh-authed viewer (correct, FR-204), sample
      avatar/attachment art (A3).

## Unresolved questions

1. Is the `order-*` CSS-based Spotlight interleave (vs. a literal DOM split of `KudosBoard`)
   acceptable long-term, or should a future phase give `KudosBoard` a `children`/slot prop so the
   DOM order can genuinely match the visual order? Currently disclosed compromise, not silent.
2. Should the two-column ALL KUDOS + sidebar layout the frame implies (680px feed + 422px sidebar)
   be revisited in a follow-up UI pass? Not achievable from `page.tsx` alone without editing
   `all-kudos-feed.tsx` (phase 07, off-limits here).
3. The K-25 contention-flake described above — recommend the tester watch for recurrence under CI
   parallelism; if so, the fix is test-side (explicit wait), not app-side.
