# Reviewer inspection — Sun* Kudos Live Board (F004)

**Decision: SEALED.** 0 critical, 0 high, 2 low, 1 deferred. Verdict written to
`plans/260906-1945-kudos-live-board/evidence/inspection-verdict.json` and validated clean against
`.claude/hooks/lib/evidence-validator.cjs` (hard stage).

## Scope

- `supabase/migrations/20260906140914_kudos_live_board.sql`, `supabase/seed.sql`
- `lib/kudos/{view-model,derive,queries,board-data,viewer}.ts`, `lib/supabase/database.types.ts`
- `app/kudos/page.tsx`, `app/kudos/_actions/toggle-kudos-like.ts`, `app/kudos/{new,secret-box,[id]}`
- `app/kudos/_components/*` (~20 files)
- `lib/i18n/messages/{dictionary,vi,en,vi-kudos,en-kudos}.ts`
- `e2e/kudos-live-board*.spec.ts`, `e2e/fixtures/kudos-constants.ts`, `playwright.config.ts`
- `docs/system/architecture.md`, `docs/system/permissions.md`

Depth: full read of every changed source file, plus live queries against the running local
Supabase database (not just migration text) for the security claims.

## Assessment

This is the strongest-evidenced delivery I've seen in this repo: every architectural claim in the
reports is independently checkable, and every one I checked held. RLS is correct and I verified it
live, not from the SQL alone — anon insert genuinely rejected, duplicate like genuinely rejected by
the unique constraint, no UPDATE path exists anywhere. The heart write path's history (optimistic →
proven broken by K-25 → reverted to server-authoritative) is disclosed in the code's own comment,
not just a report, and the current implementation matches what's claimed. `canLike` is provably
auth-only (`viewer.ts`), never the sidebar's seeded-viewer fallback. Test integrity checks out: K-10
clicks back and asserts the round trip, K-25 uses `expect(heart).toBeEnabled()` instead of a silent
skip, no `.skip`/`.fixme`/`.only` anywhere. The seed is composition of real frame data, not
invention, and says so inline everywhere it stretches (A5 department assignment, hashtag
recombination, gift-line reuse).

## Critical

None.

## High

None.

## Medium

None.

## Low

1. **`e2e/kudos-live-board.spec.ts` is 616 lines**, over the repo's 200-line file cap.
   Fix: split by section (hero/filters/carousel, card, spotlight, sidebar/misc) into 3-4 files
   sharing the locator helpers via a fixture module. Not blocking: `homepage.spec.ts` (604),
   `award-system.spec.ts` (466) and `login-screen.spec.ts` (310) already violate the same cap and
   shipped before this feature — this is an established (if undocumented) convention for E2E specs
   in this repo, not a new regression.
2. **Stale `48` in `e2e/fixtures/kudos-constants.ts`** — the `DEPARTMENT_OPTIONS` doc comment says
   "48 entries" and K-3's test title says "department has 48", but the array itself holds the
   correct 50 (verified against the live DB) and the assertion uses `.length` dynamically, so
   nothing breaks. Fix: update the comment and test title to 50 for anyone grepping later.

## Suggestion

1. **`resolveViewer()`/`resolveSidebarSunnerId()` throw on any read failure** (`lib/kudos/viewer.ts`)
   rather than degrading — a transient Supabase hiccup on this one query 500s the whole `/kudos`
   page for every viewer, not just the affected session. Low likelihood (RLS grants `anon` select on
   `sunners`) and no acceptance criterion exercises it, but worth a graceful-degradation pass
   (render with `viewer: { isAuthenticated: false, sunnerId: null }` and log, rather than throw) in
   a follow-up.
2. `fetchKudos()` reads the entire `kudos` table server-side every request (57 rows today) and pages
   client-side. Fine at this scale; if the table grows past a few hundred rows this should become a
   real `range()`/keyset-paginated query instead.

## Edge Cases Turned Up

- **Self-like is double-defended**: blocked in the app (compares `viewer.sunnerId` to
  `kudosRow.sender_id`) *and* independently in RLS (`kudos_likes_insert_own`'s `NOT EXISTS` join to
  `sunners.auth_user_id`). RLS alone would still hold if the app check were ever removed.
- **Double-click race**: the `pending` guard in `kudos-card-actions.tsx` plus the
  `(kudos_id, user_id)` unique constraint are two independent layers — a live duplicate insert
  against the constraint genuinely rejects with `23505`, which the action code explicitly tolerates.
- **`388 KUDOS` and the department-count correction** both trace to an authoritative ratification
  (test-contract.md, 2026-09-06c) that fixed a number the original brief got wrong. The built system
  matches the *corrected* number in both cases, verified live — the study-context.json brief simply
  wasn't regenerated after the ratification.
- **React key warning** (debugger report, 2026-09-06 23:32) on `KudosBoard`'s top-level Fragment was
  real and is fixed — all four children now carry literal keys.

## Done Well

- RLS posture is least-privilege: select-all is fine (public thank-you data by design), write is
  scoped to one table and one predicate, no update path exists anywhere, and the broad `GRANT ALL`
  visible in `information_schema` is Supabase's own platform default (owned by `supabase_admin`,
  predates this migration) — RLS is the real and effective gate, not the grants.
- The write path's own code comment documents *why* it isn't optimistic anymore, including the
  specific test failure that proved the optimistic version wrong (K-25 reload racing an in-flight
  insert) — the reasoning lives where the next person will actually find it.
- `docs/system/architecture.md` and `docs/system/permissions.md` were rewritten for the new DB/RLS
  layer, and both match what's actually running — checked live policies against the prose.
- Seed data is honestly composed: every stretch (recombining names/departments across more rows
  than the frame shows) is commented in `seed.sql` with its MoMorph-rule justification, and
  `clarifications.md` assumption A5 records the one place a value was assigned, not transcribed.

## Actions In Order

1. Split `e2e/kudos-live-board.spec.ts` into smaller files (Low, cosmetic, not blocking).
2. Fix the stale "48" comment/test-title in `e2e/fixtures/kudos-constants.ts` (Low, cosmetic).
3. Consider graceful degradation instead of throw in `viewer.ts` (Suggestion, deferred).

## Numbers

- Type coverage: `npm run typecheck` exit 0 (temper-results.json, corroborated — no `any` found in
  reviewed files).
- Test coverage: 26 e2e assertions (24 anon + K-10/K-25 authed) + 1 setup = 27 passed, run 4×
  including once with no reset between runs; 57 passed across the full regression suite. No unit
  test runner in this repo (Playwright E2E is the only harness, per architecture.md).
- Lint findings: 0 errors; 21 pre-existing warnings outside this feature, unchanged.

## Still Unresolved

- None blocking. The two Low findings above are cosmetic and don't affect security, correctness, or
  the acceptance criteria; the one Suggestion is a hardening item for a future pass, not this one.
