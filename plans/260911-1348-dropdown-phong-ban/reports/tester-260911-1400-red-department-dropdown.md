# RED E2E — Department Dropdown (K-26..K-30)

Phase 01 execution. Five Playwright assertions written and run via `npm run test:e2e`.

## Test Command

```bash
npm run test:e2e -- e2e/kudos-live-board.spec.ts --project=anon -g "K-26|K-27|K-28|K-29|K-30"
```

## Exit Code

**1** — valid non-zero exit; two assertions failed (K-26, K-27).

## Test Files

- `e2e/kudos-live-board.spec.ts` — five new tests (K-26 through K-30), plus two helper locators (`departmentOption`, `receiverDepartment`).
- `e2e/fixtures/kudos-constants.ts` — added `TEST_DEPARTMENT = "STVC - R&D"` constant.

## Per-Test Results

| Test | Status | Assertion | Failure Text |
|------|--------|-----------|--------------|
| K-26 | FAILED | computed `text-align` and `cursor` on department option | Expected text-align "center", got "left". Expected cursor "pointer", got "default". |
| K-27 | FAILED | `boundingBox().height` and computed `max-height` must be exactly 348px | Expected boundingBox.height 348, got 320. Expected computed max-height "348px", got "320px". |
| K-28 | PASSED | select "STVC - R&D" → menu closes → all visible cards have receiver department "STVC - R&D" (with count guard) | — (regression guard: filter logic already in `kudos-board.tsx`; just untested) |
| K-29 | PASSED | reopen menu → selected option has `aria-selected="true"` | — (regression guard: state already persists; just untested) |
| K-30 | PASSED | baseline hrefs → select → narrow → reopen → click same option → restored hrefs match baseline (with count guard) | — (regression guard: toggle-to-clear logic already works; just untested) |

## Why K-26 and K-27 Failed (Expected)

Phase file insight 2: "FR-208/209/213 WILL fail today: `text-left` (not centered), no `cursor-pointer` class, `max-h-80` (320px, not 348px) — confirmed by reading `kudos-filter-menu.tsx`."

- **K-26:** Asserts computed style directly on the rendered button element. Current code applies `text-left` class (line 48 of `kudos-filter-menu.tsx`); spec requires `text-align: center` and `cursor: pointer`.
- **K-27:** Asserts exact equality `boundingBox().height === 348` and `maxHeight === "348px"`. Current code uses `max-h-80` (Tailwind's 80 = 320px). Changed from `<=` to `===` per coordinator feedback to ensure test fails at 320px and will lock in the exact height once phase 02 applies the correct class.

## Why K-28..K-30 Passed as Regression Guards

Phase file insight 1: "FR-210/211/212 assertions will fail today for want of test scaffolding, not want of behavior — the filter logic is already correct in `kudos-board.tsx`. A valid RED for those three comes from asserting something that has never been asserted, e.g. no prior test reads the receiver-department text or `aria-selected` persistence. Do not weaken these into no-ops to force a 'real' failure — write the correct assertion; if it happens to pass immediately, record it explicitly as a **regression guard**."

- K-28: Filter logic already implemented in `kudos-board.tsx::matchesFilters()` and wired in the component state. Assertion just proves it works end-to-end. Count guard `expect(count).toBeGreaterThan(0)` added before loops to prevent vacuous pass if filter yields zero results.
- K-29: `aria-selected` already set on the button via `aria-selected={selected}`. Assertion proves state persists across reopen.
- K-30: Toggle-to-clear logic already wired in `kudos-board.tsx`. Assertion proves full round-trip works. Count guard `expect(count).toBeGreaterThan(0)` added before loop to prevent vacuous pass.

## Typecheck

```
npm run typecheck
```

Passed clean. No TS errors.

## Handoff to Phase 02

| Field | Value |
|-------|-------|
| `redTestFiles` | `e2e/kudos-live-board.spec.ts` |
| `redCommand` | `npm run test:e2e -- e2e/kudos-live-board.spec.ts --project=anon -g "K-26\|K-27\|K-28\|K-29\|K-30"` |
| `redExitCode` | 1 |
| `redFailure` — K-26 | Expected text-align "center", got "left". Expected cursor "pointer", got "default". |
| `redFailure` — K-27 | Expected boundingBox.height 348, got 320. Expected computed max-height "348px", got "320px". |
| `redFailure` — K-28 | N/A — regression guard (count guard added) |
| `redFailure` — K-29 | N/A — regression guard |
| `redFailure` — K-30 | N/A — regression guard (count guard added) |

After phase 02 (UI changes), rerun the same command GREEN with this exact exit code expected: **0**.

---

**Status:** DONE
**Summary:** Five E2E tests written, defects fixed per coordinator feedback. K-26 and K-27 now fail on expected frame-fidelity assertions (text-align/cursor and max-height). K-28 and K-30 have count guards to prevent vacuous pass. K-29 passed as regression guard. Exact equality assertions lock in required values for phase 02 GREEN.
