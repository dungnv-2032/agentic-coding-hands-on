# Phase 02 — RED-gate defect repair

**Track:** Test · **Owner:** `tester` · **Depends:** — ·
**Effort:** 1.5h · **test_policy:** `e2e-red-first`

> **Read this phase before any other.** It changes the definition of done. Three defects in the
> ratified suite make GREEN unreachable as written; two of them are contradictions inside the
> authored contract itself, not implementation bugs. Nothing here weakens an assertion — every
> change either repairs broken test code or resolves a contradiction in favour of the more
> load-bearing behavior, with the reason recorded.

## Context Links

- [plan.md](plan.md) · [test-contract.md](test-contract.md) § Submit state, § Landmarks · [clarifications.md](clarifications.md) § Validation
- [RED gate report](reports/tester-red-gate.md) · [RED log](evidence/viet-kudo-red-run.log)
- Files under repair: `e2e/viet-kudo.spec.ts` (1223 lines, 59 tests), `e2e/kudos-live-board.spec.ts` K-21, `e2e/fixtures/viet-kudo-constants.ts`
- Evidence read for the ruling: `node_modules/playwright-core/lib/coreBundle.js` (`getAriaDisabled`, `elementState`), `design/test-cases.csv` ID-48/ID-56, `design-source-analysis.md § 10` (frame `5c7PkAibyD`)

## Overview

**Priority:** P1 · **Status:** completed.

Repair the RED suite so that a correct implementation can reach exit 0, then re-run it and confirm
it is still RED for the right reason. This phase writes no product code and touches no file any
other phase owns.

## Key Insights

1. **CONFLICT 1 — ID-48 and ID-56 are mathematically irreconcilable.** ID-48 asserts
   `expect(composeSubmit).toBeDisabled()` on a pristine empty form. ID-56 clicks that same button on
   that same pristine empty form and expects all four required-field errors. Playwright resolves
   `toBeDisabled()` through `getAriaDisabled(element) = isNativelyDisabled(element) ||
   hasExplicitAriaDisabled(element)`, and `click()`'s actionability waits for the `enabled` state,
   which is the negation of the same predicate. **There is no markup that is simultaneously
   `toBeDisabled()`-true and clickable** — not `disabled`, not `aria-disabled="true"`. One of the two
   must change.
   **Ruling: ID-48 changes; ID-56 stands.** Three independent reasons. (a) The design ships a whole
   authored frame for this exact state — `5c7PkAibyD`, *"Viết KUDO - Lỗi chưa điền đủ thông tin đã
   ấn gửi"* ("error: pressed Gửi without filling enough information") — which can only exist if
   `Gửi` is pressable while incomplete. (b) Seven tests (ID-7, 11, 14, 50, 51, 52, 56) depend on
   clicking submit with a required field empty; honoring ID-48's reading would delete the entire
   submit-validation contract, which is the heart of the screen. (c) The frame beats stale prose —
   the same precedence rule F002, F003, F004 and this commission's own clarifications all applied.
   **Amendment:** `compose-submit` is never `disabled` and never `aria-disabled`. It carries
   `data-submit-ready="false" | "true"`, which reflects DEC-002 exactly, so the settled rule survives
   as an observable, asserted signal and as the button's inactive styling. ID-48 asserts
   `toHaveAttribute("data-submit-ready", "false")`; ID-49 keeps its `toBeEnabled()` and **gains**
   `toHaveAttribute("data-submit-ready", "true")`, so it stops being a vacuous assertion. This is a
   `test-contract.md` amendment and must be recorded there in the same commit.
2. **CONFLICT 2 — six assertions can never pass, whatever is built.**
   `await expect(options).toHaveCount(async (count) => count > 0)` at
   `e2e/viet-kudo.spec.ts:292, 325, 363, 622, 708` and `:973`. `toHaveCount` takes a **number** and
   compares by equality; a function argument never equals a count, so the assertion polls until it
   times out. Affected: ID-8, ID-10, ID-12, ID-25, ID-33 and the load-bearing ID-46/ID-47 board
   check. Repair each to the assertion its comment already says it means:
   `await expect(options.first()).toBeVisible()` for the "> 0" cases, and
   `await expect(titleCells.first()).toBeVisible()` for `:973`. Both are stronger than a bare count
   (they wait for a real rendered element), so nothing is weakened.
3. **CONFLICT 3 — F004's K-21 contradicts the new guard.** `e2e/kudos-live-board.spec.ts:573-597`
   (anon project) asserts `/kudos/new` returns 200, keeps the URL, and renders a `main h1`. ID-1
   (same project) asserts an anon visitor at `/kudos/new` is redirected to `/login`. Both cannot
   pass. Clarifications settled the guard explicitly ("`/kudos/new` is guarded, and this is the first
   guard added since F001"), and ID-1 is the newer, ratified case. **Amendment:** delete K-21's
   `/kudos/new` third and rename the test to
   `K-21 — placeholder routes /kudos/secret-box and /kudos/[id] render ComingSoon`. The other two
   thirds are untouched and still assert 200 + `main h1`. `/kudos/new`'s access behavior is now
   owned by ID-1 (anon) and ID-0 (authed) — coverage moves, it does not shrink.
4. **`TEST_SUNNER_1` / `TEST_SUNNER_2` are imported and never used**, and neither value exists in the
   seed: `Nguyễn Văn An` is not among the nine seeded sunners, and `Đỗ Hoàng Hiệp` differs in case
   from the seeded `Đỗ hoàng Hiệp`. Every test that needs a recipient types the substring `"Nguyễn"`
   (3 seeded matches) and clicks `.first()`, so no test depends on either constant. Remove the two
   unused imports from the spec; leave the constants in the fixture file but annotate them as
   unverified against the seed, so nobody builds an assertion on them later.
5. **ID-46/ID-47 has dead cleanup code** (an `if (supabaseUrl && supabaseKey)` block with only
   comments inside), so every full run leaves one extra `kudos` row plus its attachments behind. Real
   cleanup is **not** available: the migration deliberately creates no DELETE policy, so the anon key
   cannot delete the row, and reaching for `service_role` in an e2e test would put a
   security-bypassing key in the suite. **Ruling: accept the accumulation, delete the dead block, and
   state the invariant in a comment** — a pre-suite `npx supabase db reset` clears it, no assertion
   reads an exact card count (verified: `kudos-live-board.spec.ts` uses
   `expect(cardCount).toBeGreaterThan(0)`, never an equality), and the newest-first feed keeps the
   composed row on page one where ID-47 needs it.
6. **The RED must still be RED after the repair, and for the same reason.** Re-run and confirm the
   failures are absent-hook assertion failures, not config or dependency errors.

## Requirements

**Functional:** the repaired suite is reachable — for every assertion there exists an implementation
that satisfies it. ID-1 and ID-0 keep full custody of `/kudos/new` access. `test-contract.md` records
the `data-submit-ready` hook and the K-21 scope change.

**Non-functional:** no assertion is deleted, no `test.skip`, no `expect.soft`, no timeout raised, no
`force: true`. Only the six malformed assertions, ID-48/ID-49's submit-state assertions, K-21's scope,
two unused imports and one dead block change.

## Architecture

```
e2e/viet-kudo.spec.ts
  :292 :325 :363 :622 :708   toHaveCount(fn) ─▶ expect(...first()).toBeVisible()
  :973                       toHaveCount(fn) ─▶ expect(titleCells.first()).toBeVisible()
  ID-48                      toBeDisabled()  ─▶ toHaveAttribute("data-submit-ready","false")
  ID-49                      toBeEnabled()   ─▶ + toHaveAttribute("data-submit-ready","true")
  ID-46/47                   dead cleanup block ─▶ removed, invariant commented
  imports                    TEST_SUNNER_1/2 removed

e2e/kudos-live-board.spec.ts
  K-21                       /kudos/new third removed; title renamed; other two thirds untouched

test-contract.md
  § Submit state             data-submit-ready documented, with the ID-48/ID-56 ruling and its reason
  § Landmarks                compose-submit row updated: "never disabled; carries data-submit-ready"
```

## Related Code Files

**Modify:** `e2e/viet-kudo.spec.ts` · `e2e/kudos-live-board.spec.ts` · `e2e/fixtures/viet-kudo-constants.ts` · `test-contract.md`
**Create:** none · **Delete:** none
**Read only:** `design/test-cases.csv`, `clarifications.md`, `e2e/route-guard.spec.ts`, `supabase/seed.sql`

## Implementation Steps

1. Repair the six `toHaveCount(async …)` assertions. Keep each surrounding comment; the comment
   already describes the intended check.
2. ID-48: replace `toBeDisabled()` with `toHaveAttribute("data-submit-ready", "false")` and add a
   comment naming the ID-48-vs-ID-56 ruling and this phase as its source.
3. ID-49: keep `toBeEnabled()`, add `toHaveAttribute("data-submit-ready", "true")`.
4. K-21: delete the `/kudos/new` block, rename the test, and leave a comment pointing at ID-1 for the
   guard coverage.
5. Remove the `TEST_SUNNER_1`/`TEST_SUNNER_2` imports from `viet-kudo.spec.ts`; annotate both
   constants in `e2e/fixtures/viet-kudo-constants.ts` as not present in `supabase/seed.sql`.
6. ID-46/47: delete the dead `if (supabaseUrl && supabaseKey)` block; replace it with a comment
   stating that no DELETE policy exists by design, that a pre-suite `db reset` is the cleanup, and
   that no assertion depends on an exact card count.
7. Amend `test-contract.md` § Landmarks and § Submit state per § Architecture. Keep it factual and
   short; the reasoning lives in this phase file.
8. Re-run RED, narrow: `npx playwright test e2e/viet-kudo.spec.ts --reporter=list --workers=1
   --grep "ID-8|ID-10|ID-12|ID-25|ID-33|ID-46|ID-48|ID-49|ID-56"`. Expect non-zero, every failure a
   missing-hook assertion failure. Append the output to
   `evidence/viet-kudo-red-run-post-repair.log`.
9. Re-run the F004 anon board suite to prove K-21 is still meaningful and nothing else moved:
   `npx playwright test e2e/kudos-live-board.spec.ts --reporter=list`. This must be **green** —
   nothing in this phase touches the board's implementation.

## Todo List

- [x] Six `toHaveCount(async …)` assertions repaired to `.first()` visibility checks
- [x] ID-48 asserts `data-submit-ready="false"`, with the ruling cited in a comment
- [x] ID-49 asserts both `toBeEnabled()` and `data-submit-ready="true"`
- [x] K-21 scoped off `/kudos/new`, renamed, pointing at ID-1
- [x] `TEST_SUNNER_1/2` imports removed; constants annotated as unseeded
- [x] ID-46/47 dead cleanup block removed, accumulation invariant commented
- [x] `test-contract.md` amended (§ Landmarks, § Submit state)
- [x] Step 8 re-RED captured to `evidence/viet-kudo-red-run-post-repair.log`, assertion-caused
- [x] Step 9 `kudos-live-board.spec.ts` green
- [x] No skip, no soft assertion, no raised timeout, no `force: true` anywhere in the diff

## Success Criteria

- `grep -n "toHaveCount(async" e2e/` returns nothing.
- `grep -rn "test.skip\|expect.soft\|force: true" e2e/viet-kudo.spec.ts` returns nothing.
- Test count is unchanged: 59 in `viet-kudo.spec.ts`, and `route-guard.spec.ts` still holds ID-1.
- Step 8 exits non-zero with every failure traceable to an absent `data-testid`.
- Step 9 exits 0.
- `test-contract.md` documents `data-submit-ready` and no longer claims `compose-submit` carries
  `disabled`.

## Risk Assessment

| Risk | L×I | Countermeasure |
|---|---|---|
| The ID-48 ruling is read as "weakening a ratified test" | **High** × High | The reasoning is recorded three ways — here, in a code comment at the assertion, and in `test-contract.md`. `data-submit-ready` keeps DEC-002 asserted rather than dropping it, and ID-49 gets *stronger*. Escalate to the orchestrator for ratification before merging |
| K-21's edit is read as deleting F004 coverage | Med × High | Two of three thirds survive untouched; `/kudos/new` coverage moves to ID-1 (anon) + ID-0 (authed), which is strictly more than "renders some h1" |
| A repaired assertion is accidentally made weaker than intended | Med × High | `.first()` + `toBeVisible()` waits for a real element and auto-retries — strictly stronger than an equality on a count |
| Row accumulation eventually changes board rendering in a way a test does read | Low × Med | Verified today that no exact count is asserted; the invariant is written into the test as a comment so a future author sees the dependency |
| Re-RED accidentally passes because a hook already exists | Low × Med | Step 8 inspects the failure reason, not just the exit code |

**Rollback:** `git checkout` the four files. The suite returns to its current unreachable state; no
product code is involved.

## Security Considerations

- No `service_role` key enters the suite. Cleanup by privileged key was considered and rejected —
  a suite holding an RLS-bypassing credential is a worse outcome than a few accumulated rows.
- The K-21 amendment must not accidentally loosen the public surface: `/kudos`, `/kudos/[id]` and
  `/kudos/secret-box` keep their 200 assertions, so a future guard added to any of them fails loudly.
- ID-1 stays in the `anon` project. Do not move it into an authenticated project "to make it pass" —
  its whole value is running without a session.

## Next Steps

Phase 12 consumes the repaired suite as the GREEN gate. The `data-submit-ready` hook is an input to
phase 11 (`compose-actions.tsx` renders it) — tell the orchestrator the moment the amendment is
ratified so 11 builds against the final contract, not the old one.
