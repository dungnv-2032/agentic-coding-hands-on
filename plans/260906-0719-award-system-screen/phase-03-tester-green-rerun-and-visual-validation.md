---
feature: F003 · test_policy: e2e-red-first · owner: tester
fileKey: 9ypp4enmFmdK3YAFJLIu6C · screenId: zFYDgyj_pD · depends_on: [02] · status: complete · effort: 1.5h
---

> **Delivered 2026-09-06 across four rounds** (first GREEN → final verdict → delivery verification → seal).
> Final: award-system **14/14**, homepage **22/22**, full anon project **54/54**, all exit 0. Visual PASS —
> no material mismatch left. Two departures from this phase's written scope, both recorded rather than
> smoothed over:
> 1. **`e2e/award-system.spec.ts` was edited**, which "Never touch: `e2e/**`" forbade. Two assertions were
>    *added* on orchestrator instruction — ID-7's exact 336×336 badge geometry, and a W-3 heading/landmark
>    structure test. Both strengthen the contract; nothing was skipped, relaxed or retried into a pass. The
>    W-3 lock's own first run went red on a wrong assertion by the tester, which was corrected and the red
>    run kept in evidence (`seal-award-system-run-failed-assertion.log`).
> 2. **Playwright MCP was unavailable the whole time** (`chrome` channel absent at
>    `/opt/google/chrome/chrome`). Every capture ran through the project's own Chromium instead. Step 5's
>    "Playwright MCP visual capture" was met in substance, not by the named tool.
>
> Reports: [final verdict](./reports/tester-260906-0851-award-system-final-verdict.md) ·
> [delivery verification + seal](./reports/tester-260906-0935-award-system-delivery-verification.md).

# Phase 03 — Tester: GREEN rerun + visual validation

## MoMorph refs:
- Hệ thống giải: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/zFYDgyj_pD
- Clarifications: plans/260906-0719-award-system-screen/clarifications.md
- testPolicy: e2e-red-first

## Context Links

- [plan.md](./plan.md) — RED evidence block (the command below must be byte-identical to `redCommand`)
- [evidence/award-system-red-run.log](./evidence/award-system-red-run.log) — the established RED, exit 1
- [phase-02](./phase-02-track-a-award-system-ui.md) — the implementation under test
- [design/award-system.png](./design/award-system.png) — the visual reference (1440×6410)
- `playwright.config.ts` — `anon` project, `baseURL http://127.0.0.1:3000`, `reuseExistingServer: false`

## Overview

**Priority:** P1 · **Status:** complete · **Owner:** `tester` · **Depends on:** 02 · **Effort:** 1.5h

Close the `e2e-red-first` loop: rerun the exact command that produced the RED and require exit 0, then own
the browser/visual evidence for the screen. This phase is the only owner of the GREEN verdict and of every
screenshot; the UI agent does not grade its own work.

## Key Insights

1. **Same command, or it proves nothing.** `npx playwright test e2e/award-system.spec.ts --project=anon`.
   A different file, project, grep filter or config makes the GREEN incomparable to the recorded RED.
2. **The pass count is the honest gate, not the exit code alone.** RED was 11 failed / 2 passed. GREEN is
   **13 passed, 0 failed**. ID-0/2 was already green before implementation — judging by "did anything turn
   green" would let a half-built screen through.
3. **A dependency/config failure is not a red test.** The same rule that qualified the RED applies in
   reverse: a browser-install, dev-server or WSL shared-library failure is an environment defect to fix, not
   a verdict. `playwright.config.ts` already vendors the missing WSL libs under `.playwright-libs/`.
4. **The whole suite matters, not just this file.** Six shipped homepage tests navigate into
   `/awards-information` and assert the URL holds. A regression there is this feature's regression.
5. **`playwright.config.ts` is not editable here.** ORCH-03 and phase ownership both lock it. The award-system
   spec is already matched by the `anon` project's `testMatch`.

## Requirements

**Functional**
- Rerun `redCommand` verbatim; require exit 0 and 13/13 passed.
- Run the full suite (`npm run test:e2e`) once to prove no cross-suite regression.
- Capture visual evidence at the design's own reference width and compare against
  `design/award-system.png`, region by region.
- Record the GREEN evidence next to the RED log so the pair is auditable.

**Non-functional**
- No test is skipped, `.only`-ed, retried into a pass, or weakened. No assertion is edited.
- Evidence files are written under this plan folder only.

## Architecture

```
phase 02 code ──► npx playwright test e2e/award-system.spec.ts --project=anon
                       │  exit 0, 13 passed  ──► evidence/award-system-green-run.log
                       │  exit ≠ 0           ──► triage (below) ──► bounded fix back to phase 02
                       ▼
                  npm run test:e2e            (full suite — regression gate)
                       ▼
                  Playwright MCP capture @1440 wide, full page
                       │  visuals/award-system-{hero,nav,cards,kudos,footer}.png
                       ▼
                  region-by-region diff vs design/award-system.png ──► visuals/visual-report.md
```

**Triage rules when the rerun is not GREEN** — in this order, and never past step 3:
1. Environment (browser deps, dev server, port) → fix the environment, rerun.
2. Implementation defect → hand a **bounded** fix back to `momorph-ui-implementer` naming the failing test
   ID, the locator and the assertion. Do not fix UI code here.
3. A genuine defect in the spec's *mechanism* (not its intent) → **escalate to the orchestrator**. Editing
   `e2e/award-system.spec.ts` is outside this phase's ownership; weakening intent is forbidden outright.

## Related Code Files

**Create**
- `plans/260906-0719-award-system-screen/evidence/award-system-green-run.log`
- `plans/260906-0719-award-system-screen/evidence/green-evidence.json` — `{ command, exitCode, passed,
  failed, timestamp, suiteRun }`
- `plans/260906-0719-award-system-screen/visuals/*.png` + `visuals/visual-report.md`

**Modify** — none.
**Delete** — none.
**Never touch:** `e2e/**`, `playwright.config.ts`, `app/**`, `lib/**`, `docs/**`.

## Implementation Steps

1. Confirm the working tree carries phase 02's files and that `npm run typecheck` and `npm run build` are
   clean. A build failure is a phase 02 defect, not a test result.
2. Run `npx playwright test e2e/award-system.spec.ts --project=anon`. Capture stdout verbatim to
   `evidence/award-system-green-run.log`, including the real exit code.
3. Confirm **13 passed, 0 failed** and that all 11 previously-RED tests are named in the pass set:
   ID-3, ID-4, ID-5, ID-6, ID-7, ID-8, ID-9/11, ID-10, ID-12, ID-13, deep-link.
4. Run `npm run test:e2e` (full suite). `e2e/homepage.spec.ts` must stay green — especially the six tests
   that navigate into `/awards-information`.
5. Playwright MCP visual capture at 1440px width, full page, default locale (`vi`, no locale cookie),
   unauthenticated. Save the full-page shot plus per-region crops.
6. Compare against `design/award-system.png` region by region and record each verdict in
   `visuals/visual-report.md`:
   - hero: keyvisual bleed, ROOT FURTHER wordmark placement, centered eyebrow / hairline / gold title
   - left menu: six items, 24×24 icons, gold active text + underline, sticky behavior while scrolling
   - each of the six cards: image side alternation (Top Talent left → MVP right), 336×336 gold-bordered
     image, icon-prefixed title, paragraph(s), quantity line, prize row(s)
   - Signature card specifically: two prize blocks with `Hoặc` between them
   - Kudos block and footer: byte-for-byte the same rendering as the homepage
   - the three hand-authored icons, if phase 02 reported any — judge these explicitly
7. Interaction evidence (not covered by a screenshot): click a mid-list menu item and capture the resulting
   active state; load `/awards-information#mvp` and capture the landing position.
8. Write `evidence/green-evidence.json`. Report `DONE` only when the rerun is exit 0 **and** the full suite
   is green. A material visual mismatch is `DONE_WITH_CONCERNS` with a bounded fix listed, never a silent pass.

## Todo List

- [x] Build clean before testing — `npm run build` exit 0
- [x] `npx playwright test e2e/award-system.spec.ts --project=anon` → exit 0, byte-identical to `redCommand`
- [x] ~~13~~ **14 passed / 0 failed**; all 11 previously-RED tests named in the pass set
- [x] Full suite green; homepage suite unaffected — anon project **54/54**, homepage **22/22**
- [x] `evidence/award-system-green-run.log` written with verbatim output + exit code (plus the final, delivery and seal round logs)
- [~] **`evidence/green-evidence.json` never written.** Its content shipped instead as `temper-results.json`, `raw-temper-runs-award-system-{green,final,delivery,seal}.json` and `delivery-verification-award-system.json` — same fields, different filenames. Named artifact absent; the data is not.
- [x] Visual capture at 1440 wide, `vi` locale, unauthenticated — via project Chromium, not MCP (see header)
- [~] **`visuals/visual-report.md` never written.** The region-by-region verdicts live in the two tester reports and in `visual-measurements-award-system{,-final}.json`. Anyone looking for the planned filename will not find it.
- [x] Card alternation and the Signature two-prize block explicitly checked
- [x] Hand-authored icons judged explicitly — all four card icons measured `rgb(255,255,255)` against the frame's sampled `#FFFFFF`
- [x] Menu-click and `#mvp` deep-link interaction evidence captured (incl. 375px deep-link + tap captures)
- [~] No test skipped, `.only`-ed, or weakened — **held**. `playwright.config.ts` untouched since RED — **held**. `e2e/**` untouched — **not held**: two assertions added on instruction (see header).

## Success Criteria

- Recorded RED (exit 1, 11 failed) and recorded GREEN (exit 0, ~~13~~ **14 passed**) for the **same
  command**, both on disk under `evidence/`. **Met.**
- Full suite green — no regression in the shipped homepage or login suites. **Met** (54/54).
- ~~`visuals/visual-report.md`~~ per-region verdict against `design/award-system.png` — **met in substance,
  wrong home**: the verdicts and every measurement are in the two tester reports and
  `visual-measurements-award-system{,-final}.json`; the named file was never created.
- Zero console errors and zero page errors observed on load (ID-13 already asserts this; the visual pass
  confirms it holds outside the test harness too).

## Risk Assessment

| Risk | L×I | Countermeasure |
|---|---|---|
| WSL browser dependencies missing → the run fails for environment reasons | M×M | `playwright.config.ts` already vendors the libs under `.playwright-libs/`; treat any such failure as environment, fix, rerun — never record it as a verdict. |
| A pass is claimed on exit code alone while ID-0/2 was always green | M×H | The gate is the pass **count** and the named test list, not the exit code alone. |
| Smooth-scroll timing makes ID-9/11 or the deep-link test flaky | M×M | Playwright assertions poll; if a flake appears, rerun to establish whether it is intermittent and report the rate — do **not** add a retry or a `waitForTimeout` to the spec. |
| Visual diff blocked by the 32px background-width delta on the Kudos block | L×L | Recorded as an accepted assumption (clarifications A3) — not a mismatch. |
| Award images look wrong at 336×336 in context | L×M | clarifications A1 says re-export is a bounded follow-up, not a blocker. Record it and move on. |
| Temptation to "fix" a failing assertion in the spec | L×H | Ownership forbids editing `e2e/**`. Mechanism defects escalate; intent is never weakened. |
| Dev server port 3000 already in use → `reuseExistingServer: false` conflict | L×M | Stop any stray dev server before the run; the config deliberately refuses to reuse one. |

**Rollback:** this phase writes only evidence files — deleting them reverts it completely. If GREEN cannot
be reached, the rollback is phase 02's (revert the route to `ComingSoon`), not this phase's.

## Security Considerations

- Tests run unauthenticated in the `anon` project — the screen is public by design, so no credential is
  needed and none is introduced.
- Evidence files must not contain tokens, cookies, `.env` values, or Supabase keys. Screenshots are taken
  logged out, so no session artifact can leak into `visuals/`.
- No `storageState` from the authenticated projects is loaded or copied into this phase's evidence.
- `.playwright-libs/` stays gitignored and machine-local.

## Next Steps

- **Unblocks:** phase 04 (docs) — it may only run once GREEN is recorded.
- **On failure:** bounded fix back to `momorph-ui-implementer` (named test ID + locator + assertion), or
  escalate a mechanism defect to the orchestrator. Never a third blind retry.
- **Not this phase:** editing application code, editing the spec, `docs/**`.
