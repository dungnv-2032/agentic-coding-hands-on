---
feature: F002
owner: tester
depends_on: [phase-07]
status: completed
effort: 2h
completed: 2026-09-05
---

# Phase 08 — Tester: event-time pin, GREEN rerun, visual validation

## Context Links

- Plan + frozen contract: [plan.md](./plan.md) · Decisions: [clarifications.md](./clarifications.md) — ORCH-01, ORCH-02, ORCH-03
- RED baseline: [red-evidence.json](./evidence/red-evidence.json) · [test-contract.md](./evidence/test-contract.md)
- Suites: `e2e/homepage.spec.ts` (anon, 16), `e2e/homepage-authed.spec.ts` (authed, 4), plus the 25 tests already green

## Overview

- **Priority:** P1 · **Owner agent:** `tester` · **Status:** pending · **Effort:** 2h
- **Depends on:** 07 (and through it 01-06). **Blocks:** nothing — this is the gate.
- Pins the deterministic event time (ORCH-01), reruns `redCommand` to GREEN, triages the harness
  defects listed below, and owns every piece of browser evidence for the screen.

## Key Insights

- `NEXT_PUBLIC_*` is inlined when the dev server starts, so `webServer.env` in `playwright.config.ts`
  is the only lever a test can pull; `page.addInitScript` or a per-test override cannot reach it (ORCH-01).
- **`reuseExistingServer: !process.env.CI` silently defeats that pin.** If a `npm run dev` is already
  listening on 127.0.0.1:3000, Playwright reuses it and `webServer.env` never applies. Kill any running
  dev server before the GREEN run, or the countdown tests pass or fail for the wrong reason.
- Two invariants bind the pinned value: `0 < target − now < 100 days`, because ID-12/39/40 assert
  `/^\d{2}$/` and a three-digit day count fails; and the ID-41/42/43 fake clock must be set **after**
  `target`, because that test currently pins `2026-01-01`, which is now in the past — with any future
  `target` it would assert the expired state while the counter is still live.
- ORCH-02 already authorises tightening ID-41/42/43: assert the live state first (counter non-zero,
  "Coming soon" visible), then move the clock past `target` and assert the expired state.
- **Several assertions in the RED suite cannot be satisfied by any implementation.** They are
  mechanism defects, not behaviour requirements, and they are this phase's to repair — under the rule
  in "Triage" below. This is the single largest risk in the plan (R1).

## Requirements

- ORCH-01 — `playwright.config.ts` pins a future `NEXT_PUBLIC_EVENT_START_AT` via `webServer.env`;
  `.env.example` keeps the real (past) event date, which phase 02 already documented.
- The exact `redCommand` reruns GREEN: `npm run test:e2e -- --project=anon --project=authed`, exit 0.
- The 25 tests green at RED time stay green (login, route guard, callback security, authenticated).
- ORCH-03 — the admin case (ID-5/37) stays skipped, never faked with an invented session.
- Visual validation of `/` against the MoMorph frame at 1280×800, 800×600 and 375×667.

## Architecture

```
playwright.config.ts ─ webServer.env.NEXT_PUBLIC_EVENT_START_AT = <now + ~30d, ISO-8601>
        │
        ├─► anon project   ── homepage.spec.ts ──► live countdown state
        │                                     └──► page.clock fixed at target + 1d ──► expired state
        └─► authed project ── homepage-authed.spec.ts (storageState from auth.setup.ts)
```

## Related Code Files

**Modify:** `playwright.config.ts` (`webServer.env`), `e2e/homepage.spec.ts` and
`e2e/homepage-authed.spec.ts` — **defect repair only**, per the triage rule
**Create:** `plans/260905-1153-homepage-saa/evidence/green-evidence.json`
**Not owned:** everything under `app/`, `lib/`, `public/` — a failing test is fixed in the
implementation by its owning phase, never by editing the assertion.

## Triage rule for a failing test (non-negotiable)

1. **Behaviour missing or wrong** → return a bounded fix to the owning phase's agent
   (`momorph-ui-implementer` for Track A, `implementer` for Track B). Never touch the test.
2. **Mechanism defect** — the assertion cannot express its own intent (a locator that resolves to
   several elements under strict mode, a CSS property read that never returns the authored value, a
   hard-coded date that has since passed) → repair the *mechanism*, preserve the intent verbatim,
   and record the before/after in `green-evidence.json`.
3. **Anything that would loosen what the test proves** → stop and escalate to the orchestrator.
   Deleting a case, widening a regex to match less, or replacing an assertion with a `.count()` check
   is never in scope for this phase.

Known mechanism defects, all confirmed against the frame and the specs before implementation started:

| Test | Defect | Intent-preserving repair |
|---|---|---|
| ID-7 | `getByText(/root.*further/i)`, `/days\|hours\|minutes/i`, `/kudos/i` each match several elements (the prose repeats "Root Further"; three countdown labels; nav + CTA + section + footer all say Kudos) → strict-mode violation | `.first()` on those three locators; the region assertions they stand for are unchanged |
| ID-15 | `getByText(/top project/i)` matches both `Top Project` and `Top Project Leader` | `.first()`, or scope to `[data-testid='award-card-<slug>']`, which the contract guarantees |
| ID-16 | `getComputedStyle(el).gridTemplateColumns` on a rendered grid resolves to used pixel values, so `toContain("repeat(3")` can never be true | count the tracks in the resolved value (3 at ≥1024px, 2 below) — same assertion, working mechanism |
| ID-25/26 | `getByText(/about saa 2025\|awards grid/i)` matches the header **and** the footer link | `.first()` |
| ID-41/42/43 | fake clock pinned to `2026-01-01`, now in the past | set the clock after the pinned `target`; assert the live state before it (ORCH-02) |
| ID-24/30-35, ID-53 | `:has-text(/regex/)` inside a CSS string — verify it parses; if Playwright rejects it, it is a syntax defect | `:text-matches("…", "i")`, same intent |

## Implementation Steps

1. Confirm no dev server is running on 127.0.0.1:3000; then add `env: { NEXT_PUBLIC_EVENT_START_AT: … }`
   to `webServer` in `playwright.config.ts`, honouring both invariants above, with a comment naming
   ORCH-01 and the `reuseExistingServer` trap.
2. Run `npm run test:e2e -- --project=anon --project=authed`; capture the real exit code.
3. Sort each failure through the triage rule. Send behaviour failures back to the owning agent with
   the file, the assertion and the expected DOM; repair only mechanism defects here.
4. Tighten ID-41/42/43 per ORCH-02 — live state asserted before the clock moves.
5. Rerun until exit code 0 with 20 homepage tests accounted for (19 passing, ID-5/37 skipped) and the
   25 pre-existing tests still passing.
6. Visual validation via Playwright MCP against `design/homepage-saa.png` at 1280×800, 800×600 and
   375×667: region order, awards grid column count, sticky header, floating widget overlay, footer.
   Material mismatches go back to `momorph-ui-implementer` as a bounded fix.
7. Write `evidence/green-evidence.json`: command, exit code, pass/fail/skip counts, the pinned event
   value, every mechanism repair with its before/after, and the screenshot paths.

## Todo List

- [x] `webServer.env` pins a future event time honouring both invariants
- [x] `redCommand` rerun, real exit code recorded (not summarised)
- [x] Every failure triaged; no assertion weakened; escalations raised where required
- [x] ID-41/42/43 asserts the live state before the expired state (ORCH-02)
- [x] ID-5/37 still skipped, no invented admin session (ORCH-03)
- [x] Visual validation at three viewports; mismatches returned as bounded fixes
- [x] `green-evidence.json` written

## Success Criteria

- `npm run test:e2e -- --project=anon --project=authed` exits `0`.
- 44 passing / 1 skipped against the RED baseline of 25 passing / 19 failing / 1 skipped.
- Every mechanism repair is listed in `green-evidence.json` with its justification; the count of
  assertions is not lower than at RED.

## Risk Assessment

| ID | Risk | Likelihood | Impact | Countermeasure |
|----|------|-----------|--------|----------------|
| R8-1 | A stale dev server swallows `webServer.env`, and the countdown tests report a false result | High | High | Step 1 precondition; assert the live countdown as the first check of the run |
| R8-2 | Mechanism repair slides into assertion weakening | Medium | High | The triage rule; every repair recorded with before/after and reviewable |
| R8-3 | Pinned target more than 100 days out → three-digit days fail ID-12/39/40 | Medium | Medium | Invariant stated in step 1 and in plan.md R4 |
| R8-4 | Visual mismatch treated as acceptable because tests are green | Medium | Medium | `visual-contract` obligations survive under `e2e-red-first`; step 6 is not optional |
| R8-5 | A behaviour failure is "fixed" by editing the test to match the code | Low | High | Triage rule 1; the owning phase fixes it, this phase never does |

## Security Considerations

- ORCH-03 stands: no `service_role` key enters this repo, and no admin session is forged to turn a
  skipped test green. The role gate stays code-observable and E2E-deferred.
- `e2e/.auth/user.json` holds a real session and must remain gitignored; never paste its contents into
  evidence files or reports.
- The pinned event time is a public value; nothing secret may be added to `webServer.env`.

## Rollback

`git checkout -- playwright.config.ts e2e/` returns the suite to its RED-evidence state. The
implementation is unaffected — only the gate reverts.

## Next Steps

On GREEN: hand to `reviewer`, then the docs pass (`doc-writer`) and promote, where `SCR-homepage` and
the `TBD (draft)` codes in the spec get their real allocations.
