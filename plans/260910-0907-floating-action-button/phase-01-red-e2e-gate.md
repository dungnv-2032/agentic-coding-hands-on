---
phase: 01
title: "Strict RED e2e gate"
status: complete
owner: tester
track: gate
test_policy: e2e-red-first
effort: 1h
depends_on: []
---

# Phase 01 — Strict RED e2e gate

## Context Links

- [plan.md](plan.md) · [clarifications.md](clarifications.md) § "Test contract" (testids are FIXED)
- [design/geometry.md](design/geometry.md) — every number asserted here comes from this file
- [evidence/study-context.json](evidence/study-context.json) — AC1..AC8
- Precedent spec to imitate in style: `e2e/the-le.spec.ts`
- Runner config: `playwright.config.ts` (`anon` project, line ~79-85)

## Overview

- **Priority:** P1 — blocks every other phase.
- **Status:** pending
- One durable screen-level E2E at `e2e/floating-action-button.spec.ts`, driven to a valid
  assertion RED **before any UI code exists**, plus the config change that makes the file run at
  all. This phase writes tests only; it must not touch `app/`, `lib/` or `public/`.

## Key Insights

- The `anon` project's `testMatch` is an alternation regex. Without `floating-action-button` in it,
  the file is silently never collected and the run exits **0 with "no tests found"** — which is a
  config failure masquerading as a pass, not a RED. Adding it is part of THIS phase.
- `anon` carries `dependencies: ["setup"]`. If `auth.setup.ts` fails, the run dies before the
  screen assertion — that is a dependency failure and is **not** a valid RED. The existing
  `the-le` suite already runs in `anon`, so setup is known-good; confirm it before claiming RED.
- Today `floating-widget.tsx` renders two `<Link>`s and no `data-testid`. So the first assertion
  (`getByTestId("fab-trigger")` visible) fails on a locator timeout — a genuine screen assertion.
- MoMorph downloaded **0 test cases** for both frames. The cases below are derived from the spec
  descriptions plus `clarifications.md`; they are the contract, not a suggestion.

## Requirements

Functional — one test per acceptance criterion:

| ID | Test | AC |
|----|------|----|
| FAB-01 | `/` renders `fab-trigger`, `aria-expanded="false"`, and no `fab-menu` | AC1 |
| FAB-02 | click trigger → `fab-menu` visible with `fab-standards`, `fab-write-kudos`, `fab-close`; trigger `aria-expanded="true"` and its `aria-controls` equals the menu's `id` | AC1, AC2 |
| FAB-03 | open → click `fab-standards` → URL `/standards`, `rules-panel-content` visible (DB-backed panel) | AC3 |
| FAB-04 | open → click `fab-write-kudos` (anonymous) → URL ends `/login`, not `/kudos/new` | AC4 |
| FAB-05 | open → click `fab-close` → `fab-menu` detached, `fab-trigger` visible, `aria-expanded="false"` | AC5 |
| FAB-06 | open → `Escape` → menu closed **and** `fab-trigger` is the focused element | AC5 |
| FAB-07 | open → pointerdown on page background → menu closed **and** `fab-trigger` is NOT focused | AC5 |
| FAB-08 | geometry at viewport 1440×1024 (see table below) | AC6 |

Non-functional:
- Writes no data → no cleanup block, safe to rerun (mirrors `the-le.spec.ts`).
- Runs unauthenticated in `anon`; the `/login` redirect is itself an assertion.
- Vietnamese copy is never inlined in the spec body — it lives in the constants file
  (repo convention, see `e2e/fixtures/the-le-constants.ts` header).

## Architecture

Data flow of the gate: `playwright.config.ts` testMatch → collects the spec → `anon` project
(no storageState) → dev server on `127.0.0.1:3000` → homepage `/` → DOM assertions on the five
fixed testids → navigation assertions against `/standards` and `/login`.

Geometry assertions (FAB-08), values transcribed from `design/geometry.md`:

| Target | Assertion |
|--------|-----------|
| `fab-menu` box | width `214`, height `224` |
| `fab-standards` box | `149 × 64` |
| `fab-write-kudos` box | `214 × 64` |
| `fab-close` box | `56 × 56` |
| vertical gaps | `standards.bottom + 20 === write-kudos.top`; `write-kudos.bottom + 20 === close.top` |
| right alignment | all three share the same `x + width` (flex-end column) |
| `fab-standards` / `fab-write-kudos` computed | `background-color: rgb(255, 234, 158)`, `border-radius: 4px` |
| `fab-close` computed | `background-color: rgb(212, 39, 29)`, border-radius ≥ 28px (full round) |
| label computed | `font-weight: 700`, `font-size: 24px`, `line-height: 32px`, `color: rgb(0, 16, 26)` |

Tolerance: ±1px on box metrics (sub-pixel layout), exact on colours. Assert **sizes and
relative rhythm only** — never viewport offsets: `clarifications.md` keeps the existing
`right-6 bottom-6` anchor, and the two MoMorph frames themselves disagree on the right margin
(collapsed endX 1297 vs expanded 1302), so an absolute-offset assertion would encode a
design-artifact wobble as a requirement.

## Related Code Files

Create:
- `e2e/floating-action-button.spec.ts`
- `e2e/fixtures/floating-action-button-constants.ts`

Modify:
- `playwright.config.ts` — one regex, `anon` project:
  `/(?:smoke|login-screen|route-guard|callback-security|homepage|award-system|profile-anon|the-le|floating-action-button|kudos-live-board(?!-authed))\.spec\.ts/`

Read only: `app/_components/floating-widget.tsx`, `design/geometry.md`, `clarifications.md`,
`e2e/the-le.spec.ts`, `e2e/fixtures/the-le-constants.ts`.

Delete: none.

## Implementation Steps

1. Write `e2e/fixtures/floating-action-button-constants.ts`: the five testids, `HOME_ROUTE = "/"`,
   `STANDARDS_ROUTE = "/standards"`, `COMPOSE_ROUTE = "/kudos/new"`, `LOGIN_ROUTE = "/login"`,
   the drawn labels (`MENU_STANDARDS_LABEL = "Thể lệ"`, `MENU_WRITE_KUDOS_LABEL = "Viết KUDOS"`,
   `CLOSE_LABEL = "Hủy"`, `TRIGGER_LABEL = "Hành động nhanh"`), and the geometry/colour constants
   from the table above. Header docblock cites `design/geometry.md` as the source.
2. Add `floating-action-button` to the `anon` `testMatch` alternation in `playwright.config.ts`.
3. Prove collection before proving failure:
   `npx playwright test e2e/floating-action-button.spec.ts --project=anon --list`
   → must list 8 tests. If it lists 0, the regex is wrong; fix step 2 before continuing.
4. Write the eight tests. Prefer `getByTestId`; use `boundingBox()` and
   `evaluate(el => getComputedStyle(el))` for FAB-08; `page.setViewportSize({width:1440,height:1024})`
   inside FAB-08 only.
5. Run the fixed command:
   `npx playwright test e2e/floating-action-button.spec.ts --project=anon`
6. Capture the exit code and the first failure text. Confirm the failure names the screen
   assertion (a `fab-trigger` locator timeout), not a browser install, missing dep, dev-server
   boot, or setup-project error.
7. Record the evidence in `plans/260910-0907-floating-action-button/evidence/red-evidence.md`:
   `redTestFiles`, `redCommand`, `redExitCode`, `redFailure`, plus the `--list` output.

## Todo List

- [ ] `e2e/fixtures/floating-action-button-constants.ts` created
- [ ] `playwright.config.ts` `anon` testMatch includes `floating-action-button`
- [ ] `--list` shows 8 collected tests
- [ ] FAB-01..FAB-08 written, each traceable to an AC
- [ ] Fixed command run; exit code non-zero
- [ ] Failure confirmed to be a screen assertion, not infrastructure
- [ ] `evidence/red-evidence.md` written

## Success Criteria

- `--list` collects exactly the 8 tests → the config change works.
- The fixed command exits **non-zero**, and the first failure is the `fab-trigger` assertion.
- No file under `app/`, `lib/` or `public/` was modified in this phase.
- `evidence/red-evidence.md` carries a verbatim command, exit code and failure excerpt.

## Risk Assessment

| Risk | L×I | Countermeasure |
|------|-----|----------------|
| testMatch regex typo → "no tests found" exit 0 read as a pass | M×H | Step 3 `--list` gate is mandatory before any RED claim |
| `auth.setup.ts` dependency fails → run dies before assertions | L×H | Confirm setup passed in the run output; `the-le` already proves it works in `anon` |
| WSL2 missing Chromium libs (`libnspr4` etc.) | M×H | `playwright.config.ts` already vendors them via `.playwright-libs/`; if absent, install and rerun — an install failure is NOT a RED |
| Geometry asserted with absolute viewport offsets → false failure after phase 03 | M×M | Sizes and relative rhythm only, per the Architecture note |
| Spec drifts from the fixed testids | L×H | testids come from the constants file, which quotes `clarifications.md` |

## Security Considerations

- Anonymous project by design; no credentials, no storageState, no secrets in the spec or fixtures.
- FAB-04 exercises the existing `proxy.ts` guard as a black box. `proxy.ts` is read-only here.
- The spec writes nothing to Supabase, so it needs no teardown and cannot leak fixture data.

## Next Steps

- Unblocks phase 02 (i18n + icon asset) and, through it, phase 03.
- Phase 05 reruns this identical command and requires exit 0.
