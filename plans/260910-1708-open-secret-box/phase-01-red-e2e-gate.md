---
phase: 01
title: "Strict RED e2e gate"
status: complete
owner: tester
track: gate
test_policy: e2e-red-first
effort: 2h
depends_on: []
---

# Phase 01 — Strict RED e2e gate

## Context Links

- [plan.md](plan.md) · [clarifications.md](clarifications.md) (14 resolved decisions, authoritative)
- [design/geometry.md](design/geometry.md) — every number the anon geometry test asserts
- [functional-spec](spec/open-secret-box/functional-spec.md) FR-001..FR-602 ·
  [technical-spec](spec/open-secret-box/technical-spec.md) § 6 · [permissions](spec/system/permissions.md)
- Precedent to imitate: `e2e/kudos-auth.setup.ts`, `e2e/fixtures/supabase-session.ts`,
  `e2e/profile-anon.spec.ts` / `e2e/profile.spec.ts` (the anon/authed file split)
- Runner config: `playwright.config.ts`

## Overview

- **Priority:** P1 — blocks every other phase.
- **Status:** pending
- Two durable screen-level specs (authed + anon), their own Playwright projects, their own auth
  setup, and a service-role grant fixture — driven to a valid assertion RED **before any product
  code exists**. This phase writes tests and config only: nothing under `app/`, `lib/`,
  `supabase/` or `public/` may change.

## Key Insights

- **The setup-project regex will double-run the new setup.** `playwright.config.ts`'s `setup`
  project matches `/^((?!homepage)(?!kudos)(?!profile).)*auth\.setup\.ts$/`. `secret-box-auth.setup.ts`
  contains none of those three substrings, so it matches — and would run in `setup` *and* in its own
  project, minting two users and grantings against the wrong one. Add `(?!secret-box)` to that
  alternation. This is part of THIS phase.
- **A missing testMatch entry exits 0.** The `anon` project's `testMatch` is an alternation; if
  `secret-box-anon` is absent the file is silently never collected and the run "passes". Prove
  collection with `--list` *before* claiming any RED.
- **The suite needs its own session** for the same reason kudos/profile/homepage do:
  `authenticated.spec.ts` C9 signs out globally and revokes any shared session.
- **A freshly signed-up user has no `sunners` row at all**, so "granting boxes" is an *insert* of a
  sunners row (service role, RLS bypassed) with `department = 'Unassigned'`, not an update of one.
- **The counter is mutable state shared by every test in the file** (`fullyParallel: false`, one
  worker per file). Each test therefore *sets* the count absolutely at its start through the grant
  fixture; no test may depend on the residue of the previous one, or a single retry cascades.
- **The forgery tests must speak PostgREST directly, not click.** `createTestSession()` uses the
  fixed password `Test123456!`, so the spec can sign the same user in from Node with the anon key
  and attempt (a) `PATCH /rest/v1/sunners` and (b) `rpc('open_secret_box', {p_sunner_id})`. That is
  the only way to prove test cases `5cc072ad` / `2e7bec78` — a UI click cannot.
- Anon runs in the existing `anon` project (no session, no grants), and owns the geometry
  assertions: they need no boxes.

## Requirements

Authed suite — `e2e/secret-box.spec.ts`, project `secret-box-authed`:

| ID | Test | Codes |
|----|------|-------|
| SB-01 | count=5 → `200`, `main h1` is the title, instruction line visible, counter reads `05` | FR-001, FR-101, FR-102, FR-104 |
| SB-02 | opener is an enabled control with a stable accessible name; box art present | FR-103, FR-202 |
| SB-03 | count=5 → click → a badge appears whose name is one of the six `rule_items` labels; counter reads `04` | FR-201, BR-002, BR-005 |
| SB-04 | opener rejects a second click while the first is in flight (disabled/`aria-busy`); after settle, exactly one decrement | FR-203, SM-001 |
| SB-05 | after an open, reload → counter still `04`; `/profile` stats read opened +1 / unopened −1 | BR-001, revalidate |
| SB-06 | count=1 → open → counter `00`, instruction line hidden, opener disabled | FR-102, FR-202 |
| SB-07 | count=1 → two **concurrent** `rpc('open_secret_box')` calls → exactly one succeeds, the other reports no-boxes; final count `0` | BR-004, FR-602, R1 |
| SB-08 | authenticated `PATCH /rest/v1/sunners?id=eq.{own}` with `secret_box_unopened_count` is rejected **and** the stored count is unchanged; `rpc` with a forged `p_sunner_id` argument errors | FR-601, `5cc072ad` |
| SB-09 | close glyph: arrived from `/kudos` → returns to `/kudos`; deep link → lands on `/kudos` | FR-301 |

Anon suite — `e2e/secret-box-anon.spec.ts`, project `anon`:

| ID | Test | Codes |
|----|------|-------|
| SB-A1 | `200`, `main` and `main h1` visible, title correct (this is K-21's contract, restated) | FR-001, FR-101 |
| SB-A2 | counter reads `00`, instruction line absent, opener not operable, sign-in link present | FR-105, FR-202 |
| SB-A3 | anon `rpc('open_secret_box')` with the anon key is refused (no `execute` grant) | PERM018 |
| SB-A4 | geometry at `1440 × 1024` against [design/geometry.md](design/geometry.md) | design |

Non-functional: every test sets its own precondition and is rerunnable; no credential or key is
committed; the service-role key is read at runtime from `npx supabase status -o json`.

## Architecture

```
secret-box-auth.setup.ts
  ├─ createTestSession()            → cookies + email + userId   (fixture, additive change)
  ├─ writes e2e/.auth/secret-box-user.json        (Playwright storageState — the config's path)
  └─ writes e2e/.auth/secret-box-credentials.json { email, password, userId, sunnerId }

fixtures/secret-box-grant.ts  (service role, key from `npx supabase status -o json`)
  ├─ ensureSunner(userId)      → inserts sunners row (dept 'Unassigned') if absent, returns sunnerId
  ├─ setUnopenedCount(userId, n)  → absolute set of secret_box_unopened_count (and opened=0)
  └─ readCounters(userId)      → { unopened, opened, openings }

secret-box.spec.ts  ── storageState ──> /kudos/secret-box  (DOM + navigation assertions)
                    └─ anon-key client signed in as the same user ──> PostgREST forgery probes
```

`playwright.config.ts` changes (three, all in this phase):

1. `setup` project testMatch → `/^((?!homepage)(?!kudos)(?!profile)(?!secret-box).)*auth\.setup\.ts$/`
2. new project `secret-box-auth-setup`, testMatch `/secret-box-auth\.setup\.ts$/`
3. new project `secret-box-authed`, testMatch `/secret-box\.spec\.ts$/`,
   `storageState: "e2e/.auth/secret-box-user.json"` (state only — the credentials live in the
   separate `secret-box-credentials.json`), `dependencies: ["secret-box-auth-setup"]`, `expect: { timeout: 15_000 }` (the
   opens are server-authoritative Postgres round trips, exactly the reason `kudos-authed` raised it)
4. `anon` testMatch alternation gains `secret-box-anon` (that literal — never bare `secret-box`,
   which would also collect the authed file)

## Related Code Files

Create: `e2e/secret-box.spec.ts`, `e2e/secret-box-anon.spec.ts`, `e2e/secret-box-auth.setup.ts`,
`e2e/fixtures/secret-box-constants.ts`, `e2e/fixtures/secret-box-grant.ts`.

Modify: `playwright.config.ts`; `e2e/fixtures/supabase-session.ts` — **additive only**: return
`userId: data.user.id` alongside `cookies` and `email`. Every existing caller destructures by name
and is unaffected; do not change the sign-up flow, the password, or the expired-token behaviour C8
depends on.

Read only: `design/geometry.md`, `clarifications.md`, `e2e/kudos-auth.setup.ts`,
`e2e/profile-anon.spec.ts`, `supabase/seed.sql` (the six labels), `app/kudos/secret-box/page.tsx`.

Delete: none.

## Implementation Steps

1. `e2e/fixtures/secret-box-constants.ts` — testids (`secret-box-panel`, `secret-box-opener`,
   `secret-box-badge`, `secret-box-count`, `secret-box-instruction`, `secret-box-close`,
   `secret-box-signin`), `ROUTE = "/kudos/secret-box"`, the drawn copy (title, instruction, count
   label) quoted from `design/geometry.md`, the six badge labels from `supabase/seed.sql`, and the
   geometry constants. Header docblock cites `design/geometry.md` as the source.
2. `e2e/fixtures/secret-box-grant.ts` — read the service-role key at runtime:
   `JSON.parse(execFileSync("npx", ["supabase", "status", "-o", "json"]))` → `SERVICE_ROLE_KEY`.
   Throw a *named* error if Supabase is not running; that is an infrastructure failure, never a RED.
3. `e2e/secret-box-auth.setup.ts` — session + credentials files, mirroring `kudos-auth.setup.ts`
   (cookie domain `127.0.0.1`, 3600s + buffer). Then `ensureSunner()` so every test starts from a
   real roster row.
4. Extend the `setup` exclusion with `(?!secret-box)`; add the two new projects and the `anon`
   alternation entry.
5. **Collection gate:** `npx playwright test e2e/secret-box.spec.ts --project=secret-box-authed --list`
   → must list 9. `npx playwright test e2e/secret-box-anon.spec.ts --project=anon --list` → 4.
   Zero collected means the regex is wrong; fix step 4 before continuing.
6. Write SB-01..SB-09 and SB-A1..SB-A4. Prefer `getByTestId`; `boundingBox()` +
   `getComputedStyle` for SB-A4 only.
7. Run the fixed command, then the companion:
   `npx playwright test e2e/secret-box.spec.ts --project=secret-box-authed`
   `npx playwright test e2e/secret-box-anon.spec.ts --project=anon`
8. Confirm the first failure names a screen assertion (a `secret-box-panel` / title locator timeout
   against the surviving `ComingSoon`), **not** a browser install, a missing dev server, a Supabase
   that is not running, or a setup-project error.
9. Record `evidence/red-evidence.md`: `redTestFiles`, `redCommand`, `redExitCode`, `redFailure`,
   both `--list` outputs, and the confirmation from step 8.

## Todo List

- [x] `secret-box-constants.ts` + `secret-box-grant.ts` created
- [x] `supabase-session.ts` returns `userId` (additive), all existing callers still typecheck
- [x] `secret-box-auth.setup.ts` creates session, credentials file and the `sunners` row
- [x] `setup` exclusion extended with `(?!secret-box)` — verified the setup runs exactly once
- [x] Two new projects registered; `anon` alternation gains `secret-box-anon`
- [x] `--list` shows 9 + 4 collected
- [x] SB-01..SB-09, SB-A1..SB-A4 written, each traceable to an FR/BR code
- [x] Fixed command run, exit code non-zero, failure confirmed to be a screen assertion
- [x] `evidence/red-evidence.md` written
- [x] **DEVIATION RECORDED:** SB-07 and SB-08 re-aimed post-capture to sign in via real credentials, not anon key; SB-08 forged RPC argument test unrepresentable (no parameters), re-aimed at PATCH + unexpected arg
- [x] **DEFECT FIXES RECORDED:** service-role client missing `Database` generic, `ensureSunner` typed `string` not `number`, `readCounters` filtered on non-existent `auth_user_id` column

## Success Criteria

- Both `--list` runs collect the stated counts → the config changes work.
- The fixed command exits **non-zero** and the first failure is a screen assertion.
- `git diff --name-only` lists only `e2e/**` and `playwright.config.ts`.
- Running the whole suite once (`npx playwright test`) shows `secret-box-auth.setup.ts` executing
  exactly once, and no pre-existing suite newly red.
- `evidence/red-evidence.md` carries verbatim commands, exit codes and failure excerpts.

## Risk Assessment

| Risk | L×I | Countermeasure |
|------|-----|----------------|
| `secret-box-auth.setup.ts` matched by the default `setup` project → two users, grants on the wrong one | **H×H** | The `(?!secret-box)` exclusion, plus the whole-suite run in Success Criteria that counts the setup executions |
| Missing `anon` alternation entry → "no tests found", exit 0 read as a pass | M×H | Step 5 `--list` gate is mandatory before any RED claim |
| Supabase not running → `supabase status` fails, read as a RED | M×H | Named infrastructure error in the grant fixture; step 8 classifies it explicitly as not-a-RED |
| Service-role key printed into logs, traces or evidence | L×H | Key is read into a local const and never logged; evidence quotes commands, never output containing keys |
| Counter residue between tests makes SB-03/SB-06 order-dependent and flaky | M×M | Every test calls `setUnopenedCount()` absolutely at its start |
| WSL2 Chromium libs missing | M×H | `.playwright-libs/` vendoring already in `playwright.config.ts`; an install failure is not a RED |
| Geometry asserted with absolute page offsets rather than card-relative sizes | M×M | SB-A4 asserts sizes and intra-card rhythm only; DEC-02/DEC-03 leave page placement unasserted |
| `supabase-session.ts` edit breaks the four suites that share it | L×H | Additive return field only; run `npx playwright test e2e/smoke.spec.ts --project=anon` and one authed suite before closing the phase |

## Security Considerations

- The service-role key is read at runtime and never written to a file, a fixture literal, or the
  evidence. `e2e/.auth/**` is already gitignored — confirm before the first run.
- SB-08 and SB-A3 are the security tests of this feature: they assert that the *only* way to move a
  counter is the definer function. They must fail RED for the right reason (no function yet) and
  must never be softened to "the UI hides the button".
- The grant fixture writes only to the test user's own row; it must never touch a seeded Sunner.
- Test users accumulate in the local `auth.users` table; that is already true of every suite and is
  out of scope here.

## Deviations from Plan (Recorded in Delivery)

### SB-07 and SB-08 Test Re-aims
The first pass shipped SB-07 and SB-08 signing in via the anon key. Phase 01 gate clarified: neither test could pass against `open_secret_box()` because the function is `security definer` with `REVOKE ... FROM anon` (PERM018). Both tests were rewritten to `signInWithPassword()` for real auth before the RPC. This is **stronger than planned** — the tests now prove the function is truly callable only as authenticated, not just UI-unreachable.

SB-08's second half asserted a "forged `p_sunner_id` argument"; the actual function takes **no parameters** at all. Re-aimed to test authenticated `PATCH /rest/v1/sunners?id=eq.{own}` rejection + unexpected RPC argument (`403`). This shape is more resistant to attack.

### Three Fixture Type/Runtime Defects Fixed by Orchestrator
- Service-role client in `secret-box-grant.ts` lacked its `Database` generic; typed `createClient<Database>()`.
- `ensureSunner` return type was `string` when `sunners.id` is `bigint`; corrected to `number`.
- `readCounters` fixture filtered `secret_box_openings` on non-existent `auth_user_id` column (a real runtime bug); removed.

## Next Steps

- Unblocks phases 02 and 03 (both may start immediately after the RED is recorded).
- Phase 07 reruns these two commands unchanged and requires exit 0.
- Rollback: reverting this phase alone leaves no orphan — the two projects and the specs are removed
  together, and `supabase-session.ts` returns one field fewer.
