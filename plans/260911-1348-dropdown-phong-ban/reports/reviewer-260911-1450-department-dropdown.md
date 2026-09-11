# Review — Dropdown Phòng ban (`WXK5AYB_rG`), `feat/dropdown-phong-ban`

## Scope
- Files reviewed: `app/kudos/_components/kudos-filter-menu.tsx`, `e2e/kudos-live-board.spec.ts`, `e2e/fixtures/kudos-constants.ts`, `e2e/capture-department-dropdown-visual.spec.ts`, `playwright.config.ts`
- Commits: `c174d6f` (feat), `b7f6f03` (test), `92a7b84` (test)
- Lines: 301 insertions / 4 deletions across 5 files
- Depth: full diff read + surrounding call sites (`kudos-filter-bar.tsx`, `kudos-card.tsx`, `sunner-chip.tsx`)
- Requirement source: spec-delta FR-208..FR-213, clarifications.md — read in full and checked against code, not just cited

## Assessment
Small, well-scoped change. The three frame-fidelity fixes are correct and the geometry claim is provably right, not asserted on faith. The shared-component risk (hashtag listbox) was reasoned through in clarifications and verified in code — the `scrollable` gate is intact. Test suite is adversarially sound on the points I probed hardest (department-name prefix collision, restoration proof, per-card scoping). One real gap: the new on-demand Playwright project runs by default under `npm run test:e2e` (no `--project` filter), same as its four siblings — pre-existing pattern, not introduced here, but flagging since it was in scope to check.

## Critical
None.

## High
None.

## Medium
1. **`department-dropdown-visual-capture` project has no `testIgnore` and will run inside a plain `playwright test` invocation.** `playwright.config.ts:188-192` adds it without exclusion; `package.json:11` (`test:e2e": "playwright test"`) has no `--project` filter, so a bare `npm run test:e2e` executes this capture spec too, overwriting evidence PNGs on every full run. This is not new — `visual-capture`, `fab-visual-capture`, `hashtag-dropdown-visual-capture`, `addlink-box-visual-capture`, `secret-box-visual-capture` (playwright.config.ts:163-213) all share the same shape — but it's now five instances of a convention that should really use `testIgnore` on the "anon"/default run path or be invoked only via explicit `--project=`. Out of scope to fix in this branch (matches existing repo convention exactly), flagging as a standing item.
   - Fix: add `testIgnore: /capture-.*-visual\.spec\.ts/` (or similar) to whichever project(s) run by default, once — covers all five, not just this one.

## Low
1. `kudos-live-board.spec.ts` is now 814 lines, well past the repo's 200-line file-size guidance (`development-rules.md`). Pre-existing (was already ~625 lines before this branch), and splitting a screen's canonical e2e spec has real cost (test-contract traceability), so not blocking — but the file is the single largest artifact in this diff's blast radius and keeps growing every feature. Worth a follow-up to split by concern (e.g., filters vs. cards vs. carousel) rather than deferring indefinitely.
2. `capture-department-dropdown-visual.spec.ts:20` types the `page` parameter inline as `import("@playwright/test").Page` instead of importing `Page` at the top — works, compiles clean, just inconsistent with the named import already used two lines above (`import { expect, test } from "@playwright/test"`).

## Edge Cases Turned Up
- **Hashtag listbox regression from the shared-component fix**: verified `kudos-filter-bar.tsx:70-78` never passes `scrollable` for the hashtag menu, so `max-h-[348px] overflow-y-auto` (gated by `scrollable ? ... : ""`, `kudos-filter-menu.tsx:35`) never applies to the 13-option hashtag list — it stays auto-height as before. K-3's `toHaveText(HASHTAG_OPTIONS)` (exact per-option text, unaffected by `text-left`→`text-center` or the removed `gap-1`) still passes per the reported 30/30. No regression found.
- **348px math, independently re-derived**: Tailwind `p-4` = 16px all sides, `text-base` = 16px font, `leading-6` = 24px line-height → row content box = 24 + 16×2 = 56px. 6 rows × 56 = 336px, container `p-[6px]` top+bottom = 12px → 336+12 = **348px exactly**, provided there is zero inter-row gap. Removing `gap-1` (was 4px×5 gaps = 20px, which would have made the old total 356/368px depending on row count) is load-bearing, not cosmetic — without it the 348px claim is false. Confirmed correct.
- **Department-name prefix collision, the adversarial case named in the brief**: `DEPARTMENT_OPTIONS` (`kudos-constants.ts`) contains `STVC - R&D`, `STVC - R&D - DTR`, `STVC - R&D - DPS`, `STVC - R&D - AIR`, `STVC - R&D - SDX` — four names for which `TEST_DEPARTMENT` is a strict prefix. Every locator that resolves `TEST_DEPARTMENT` (`departmentOption`, `receiverDepartment`, the K-26 hashtag/department style check via `getByRole`, the K-30/visual-capture selectors) passes `exact: true`. Without it, `getByRole("option", { name: "STVC - R&D" })` or `getByText("STVC - R&D")` would be a Playwright strict-mode violation (5 accessible-name matches) or a substring match landing on the wrong department card — either would fail loud, not silently pass wrong. Verified every call site; no missed `exact: true`.
- **`receiverDepartment()`'s sender/receiver scoping**: walked the DOM — `kudos-card.tsx:124-136` renders sender chip and receiver chip as two independent `SunnerChip` instances, siblings only at the `Info user` row level, not at the "Frame 477" level. `sunner-chip.tsx:64` — the `kudos-receiver` `<Link>` and its department `<span>` (`sunner-chip.tsx:86-88`) share the SAME immediate parent (`Frame 477` div). So `card.getByTestId("kudos-receiver").locator("..")` resolves to that specific div, and `.getByText(name, {exact:true})` searches only its descendants — the sender's department span, several DOM levels away in a disjoint subtree, is unreachable from this locator chain. The comment's claim ("a bare page-level text match would also hit the SENDER's department on the same card") is accurate and the fix (`.locator("..")`) is the right one, not overkill.
- **K-30's restoration proof**: baseline is captured via `page.evaluate` querying `[data-testid="kudos-receiver"]` hrefs, sorted, BEFORE any filter is applied, then re-captured and compared after select→toggle-off. This is a real round-trip check (order-independent via `.sort()`, catches both "wrong set" and "wrong count"), not a vacuous count comparison. Correctly avoids depending on the first feed page's department mix, as the code comment states.
- **`toBeGreaterThan(0)` guards** in K-28/K-30: count is asserted `> 0` *before* the per-card loop runs, so a 0-count board would fail the assertion rather than have the loop silently execute zero times and let the test pass vacuously. Not vacuous.
- Checked `AnonymousSenderChip` (F005) does not touch the receiver slot — `kudos-card.tsx:125-129` gates only the sender; the receiver always renders `SunnerChip role="receiver"`, so `receiverDepartment()` is unaffected by anonymous-sender kudos, including in the seed data used for K-28/K-30.
- Verified typecheck (`tsc --noEmit`, exit 0) and lint (`eslint` on the 5 touched files: 18 pre-existing `no-unused-vars` warnings on locator helpers `kudosSender`/`kudosReceiver`/etc. defined ahead of use elsewhere in the file — none from this diff's own additions) independently; matches the reported "lint exit 0, typecheck exit 0, no new warnings" claim.

## Done Well
- The code comment on `kudos-filter-menu.tsx:11-14` states the exact 348px arithmetic inline — a reviewer (or the next editor) can verify the geometry claim without archaeology. Good practice, keep doing it.
- Clarifications.md correctly identified that changing text-align/cursor for BOTH listboxes is the *correct* behavior (same Figma component instance), not a scope leak, and the diff matches that call exactly — no bespoke `testId`-based branching was invented to "protect" the hashtag listbox from a change it's supposed to get.
- Test comments explain *why* a given assertion shape was chosen over a simpler one (e.g., why K-30 uses href round-trip instead of a count, why `receiverDepartment` needs `.locator("..")`, why `TEST_DEPARTMENT` needs `exact: true`) — this is exactly the kind of test-quality documentation that lets a reviewer verify intent instead of guessing it.
- `scrollable` prop reused rather than adding a new one-off flag for the height fix — no unnecessary API surface added (YAGNI held).

## Actions In Order
1. (Standing, not blocking) Add `testIgnore` to prevent the five on-demand visual-capture projects, including this one, from executing under a bare `npm run test:e2e`.
2. (Optional, low) Split `kudos-live-board.spec.ts` by concern in a future pass; not this branch's job.
3. (Nit, optional) Hoist the inline `import("@playwright/test").Page` type in `capture-department-dropdown-visual.spec.ts:20` to the existing named import.

## Numbers
- Type coverage: `tsc --noEmit` exit 0 on the 5 touched files (repo-wide check, no new errors)
- Test coverage: 5 new e2e tests (K-26..K-30) covering FR-208..FR-213; reported RED→GREEN evidence (6/6) and full-file 30/30 confirmed consistent with the code as read
- Lint findings: 18 warnings in `kudos-live-board.spec.ts`, all pre-existing unused locator helpers, 0 from this diff's additions; 0 errors

## Still Unresolved
- The visual-capture project default-run scoping (Medium #1) is a five-instance standing pattern in this repo, not something to fix inside this branch — flagging for the maintainer to batch-fix across all five rather than patching just this one.

**Status:** DONE
**Summary:** Three frame-fidelity fixes are correct and the 348px claim is independently verified true; the shared-listbox risk to the hashtag menu was checked in code and does not regress. Five new e2e tests are adversarially sound on prefix-collision, scoping, and vacuous-loop risks. No critical or high findings; one pre-existing, five-instance-wide medium (visual-capture project not excluded from default runs) and two low nits.
**Concerns/Blockers:** None blocking. See Medium #1 for a standing (not new) test-infra item worth a follow-up ticket.

## Overall Score: 9/10
