# Phase 06 — Integration, GREEN rerun, visual validation

## Context Links

- Plan: [plan.md](./plan.md) · RED evidence: `evidence/red-evidence.md` (written in phase 02)
- Decisions: [clarifications.md](./clarifications.md) (A1 scope of the E2E, A2 Playwright MCP flakiness, ORCH-05 hero)
- Design reference image: `design/login-screen.png`

## Overview

- **Priority:** P1 · **Owner agent:** `tester` · **Status:** complete · **Effort:** 1.5h
- **Depends on:** 04 (Track A) and 05 (Track B). **Blocks:** nothing.
- Rerun the exact command recorded at RED and prove it GREEN, then own the visual evidence and the
  static gates. This is the only phase where the two tracks are judged together.

## Key Insights

- GREEN must come from the **same** `redCommand` on the **same** spec files. A test that was edited
  to fit the implementation is not evidence — harness defects may be fixed, assertions may not be
  weakened, and any assertion change must be recorded with its reason.
- A2 says Playwright MCP failed to connect in the study session. Visual validation must not hinge on
  it: fall back to `@playwright/test` full-page screenshots into `evidence/`, compared by eye against
  `design/login-screen.png`.
- RISK-01 stays open by design. The check here is not "the hero matches the design" but "the hero
  layer carries the recorded geometry over the fallback and references
  `/images/login/hero.png`, so dropping the asset in is a zero-code change".

## Requirements

- Every phase-02 case C1–C10 passes, each traceable to its FR/US code.
- `npm run lint`, `npx tsc --noEmit`, `npm run build` all clean.
- Visual evidence captured for SCR-login in both `idle` and `error` states, plus the EN locale.

## Architecture

```
redCommand (unchanged) ─► anon project  : smoke, C1–C5, C6, C10
                        └ authed project: C7, C8, C9
        │
        ├─► evidence/green-evidence.md   (exit 0, per-case PASS lines)
        └─► evidence/screenshots/*.png   (idle · error · EN · /todo)
static gates ─► lint · tsc --noEmit · next build
```

## Related Code Files

**Create:** `evidence/green-evidence.md`, `evidence/screenshots/**` (in this plan dir)
**May modify:** `e2e/**` — harness defects only (timeouts, waits, locator typos)
**Read-only:** all of `app/`, `lib/`, `proxy.ts`. A failure here goes back to the owning phase's agent
as a bounded fix; this phase never patches application code.

## Implementation Steps

1. Run the recorded `redCommand` (`npm run test:e2e`) unchanged. Capture the full reporter output.
2. Any red case → classify it: harness defect (fix here), Track A defect (bounded fix back to
   `momorph-ui-implementer`, phase 04 scope), or Track B defect (back to `implementer`, phase 03/05
   scope). Never relax an assertion to reach green.
3. Re-run until exit code 0 with all of C1–C10 plus the smoke test passing.
4. Static gates: `npm run lint`, `npx tsc --noEmit`, `npm run build`. All must be clean; a build
   failure blocks sign-off even with green tests.
5. Visual validation of SCR-login. Try Playwright MCP first; on `CONNECT_TIMEOUT` (A2) fall back to
   `page.screenshot({ fullPage: true })` inside a throwaway capture spec. Capture: `/login` idle,
   `/login?error=oauth_failed`, `/login` with `NEXT_LOCALE=en`, and `/todo`. Compare each against
   `design/login-screen.png` and record any material mismatch as a bounded Track A fix.
6. Hero check (ORCH-05): confirm the rendered element references `/images/login/hero.png`, that the
   dark-navy fallback shows in its absence, and that the recorded geometry values are present in the
   markup/CSS. Record RISK-01 as still open.
7. Write `evidence/green-evidence.md`: command, exit code 0, per-case PASS lines keyed to FR/US
   codes, the static-gate outputs, screenshot paths, and any assertion that was changed with why.
8. Flip every phase row in `plan.md` to `completed` and set the plan `status: completed`.

## Todo List

- [x] `npm run test:e2e` exits 0 with 19 tests passing (12 functional + 7 CWE-644 regression)
- [x] No assertion weakened; corrections made to C3/C5 with documented reasons
- [x] lint, `tsc --noEmit`, `next build` clean
- [x] Screenshots captured for idle / error / EN / `/todo`
- [x] Hero fallback + geometry + `/images/login/hero.png` reference verified; RISK-01 noted open
- [x] CWE-644 high-severity open redirect fixed and covered by 7-test regression suite

## Success Criteria

| Observable | Code |
|---|---|
| `/login` renders header, hero, wordmark, button, footer | FR-201 |
| Click → button disabled + authorize request with `provider=google` | FR-202, FR-601, SM-001 |
| VN default, EN switch persists in `NEXT_LOCALE`, invalid value falls back to VN | FR-203, BR-003 |
| `/login?error=oauth_failed` shows the exact error copy | FR-402, DEC-001 |
| Anon `/todo` → `/login`; authed `/login` → `/todo`; repeated authed loads stay authenticated | FR-101, FR-102, FR-602 |
| Sign-out lands on `/login` and `/todo` then bounces | FR-403, US004 |
| `[auth.external.google]` present with env-substituted credentials | FR-001 |
| `/auth/callback` allow-listed and reachable unguarded | FR-002 |

## Risk Assessment

| ID | Risk | Likelihood | Impact | Countermeasure |
|----|------|-----------|--------|----------------|
| R1 | Pressure to edit assertions to reach GREEN | Medium | Critical | Step 2 classification rule; every assertion change recorded with its reason in the evidence file |
| R2 | Playwright MCP unavailable again (A2) | High | Low | Screenshot fallback is the primary path, MCP the bonus |
| R3 | Flaky C8 (cookie preservation depends on a rotation actually occurring) | Medium | Medium | Assert the invariant — repeated authed loads never bounce — rather than the presence of a `Set-Cookie` on one specific response |
| R4 | Visual mismatch attributable only to the missing hero asset | High | Low | RISK-01 is explicitly excluded from the visual verdict; judge layout, type and spacing only |

## Security Considerations

- Confirm `git status` shows no `.env`, `.env.local` or `e2e/.auth/user.json` staged.
- Confirm no `service_role` key and no `window.__supabase`-style hook entered app code (ORCH-01/02).
- Confirm the screenshots and evidence carry no real credentials — fixture users are throwaway local
  accounts.

## Rollback

Nothing shipped here beyond evidence files; delete `evidence/green-evidence.md` and
`evidence/screenshots/` to revert. Application rollback is per owning phase.

## Next Steps

- Manual smoke test of the real Google round-trip once Google Cloud credentials exist — the one
  claim `skip_nonce_check = true` still rests on (A3).
- Retry the MoMorph render endpoint for `662:14389`; drop the file at `public/images/login/hero.png`
  and close RISK-01 without a code change.
- No `docs/` directory exists in this repo, so no roadmap/changelog sync applies yet; creating it is
  a separate decision, not this plan's work.
