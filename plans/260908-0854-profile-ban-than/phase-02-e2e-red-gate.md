# Phase 02 — E2E RED gate: its own session, its own Playwright project

**Track:** Test (the `e2e-red-first` gate) · **Owner:** `tester` · **Effort:** 2h
**File ownership:** `e2e/profile.spec.ts`, `e2e/profile-auth.setup.ts`,
`e2e/fixtures/profile-constants.ts`, `playwright.config.ts`

## Context Links

- **`plans/260907-0822-viet-kudo/reports/orchestrator-k25-root-cause.md` — read it before writing a line.**
- Pattern to copy: `e2e/kudos-auth.setup.ts`, `e2e/homepage-auth.setup.ts` (its header comment states the rule)
- `clarifications.md` § "Route and access", § "Viewer identity", § "Security"
- `spec/F006_ProfileBanThan/functional-spec.md` § 10 "Edge Behaviours to Verify", § Traceability
- `design/test-cases.csv` (30 cases)

## Overview

- **Priority:** P1 — the `e2e-red-first` policy makes a valid RED the release gate for phases 03–08.
- **Status:** complete
- Produce one durable screen-level E2E suite for `/profile`, wired to its **own** session file and
  its **own** Playwright project, and record a real non-zero exit caused by the profile assertions.

## Key Insights

1. **The session hazard is the whole reason this phase exists first.**
   `e2e/authenticated.spec.ts`'s C9 signs out with Supabase's default `scope: 'global'`, which
   **revokes** the session rather than clearing a cookie. Any authed project sharing
   `e2e/.auth/user.json` fails nondeterministically depending on whether its page load lands before
   or after C9. This cost F004 three wrong diagnoses (timeout → dev-server crash → "too many
   concurrent tests"), each of which made the suite slower instead of correct. `/profile` is
   auth-gated, so it **must** get `e2e/profile-auth.setup.ts` + `e2e/.auth/profile-user.json`.
2. **The `setup` project's `testMatch` regex will swallow the new setup file.** It is currently
   `/^((?!homepage)(?!kudos).)*auth\.setup\.ts$/`. `profile-auth.setup.ts` matches it, so the setup
   would run in **two** projects. Narrow it to
   `/^((?!homepage)(?!kudos)(?!profile).)*auth\.setup\.ts$/`. This exact widening/narrowing step was
   the fix in the K-25 report; missing it is a silent duplicate-session bug.
3. **The e2e user has no `sunners` row** (`create_kudos()` provisions on first write only), so the
   *default* observable state at `/profile` is the sparse self view: zero counters, `0`/`0` Secret
   Box, empty feed, no tier pill, six grey circles. Every assertion about a populated profile must
   target `?id=1` (the seeded frame viewer, 25 received / 25 sent / 25-25 Secret Box — measured).
4. **A "sender name rendered" assertion passes the broken case.** The PostgREST probe showed an
   un-hinted embed returning the **receiver** in the sender slot with a 200. Assertions must name
   the *expected person*, never merely assert a non-empty name.
5. **SEC_002 (my own anonymous Kudo in my own Sent list) cannot be observed by a fresh e2e user
   with no sent Kudos.** The only honest path is: compose one anonymous Kudo through `/kudos/new`
   (which provisions the `sunners` row as a side effect), then read `/profile` → `Đã gửi`. Written
   as exactly one test, with cleanup, and its coupling to the compose flow documented in-file.

## Requirements

Functional coverage (mapped to the design's 30 test cases):

| Group | Cases | Where asserted |
|---|---|---|
| Access | ACC_001, ACC_002 | anon project: `/profile` and `/profile?id=1` redirect to `/login`; authed: render |
| `?id=` resolution | FUN_001–005 | `?id=banana`, `?id=42.5`, `?id=' or 1=1`, `?id=99999999`, `?id=1&id=2` → 404; `?id=` empty, `?q=x`, `?id={self}` → self view, **no redirect in the address bar** |
| Hero + badges | GUI_001, GUI_002, GUI_009 | six `profile-badge-slot` elements always; tier pill present at `?id=1`, **absent** on the sparse self view; no star element anywhere (AMEND-1) |
| Stats / write bar | GUI_004, GUI_005, FUN_006–008 | self: five `profile-stat` rows + `profile-secret-box-button` `disabled`; `?id=2`: **zero** stat rows, write bar naming that Sunner, href `/kudos/new?receiverId=2` |
| Direction dropdown | FUN_009–012, SEC_001, SEC_003 | self: two options, `Đã nhận` active first; `?id=2`: one option and **`Đã gửi` absent from the whole page body** (`expect(body).not.toContainText("Đã gửi")`) |
| Feed + paging | FUN_013, GUI_006, GUI_007 | at `?id=1`: ≥10 cards, scroll adds a page, no duplicate `kudos-card` ids across pages, end-of-feed message on the last page, **no** Spam chip |
| Card interactions | FUN_014, FUN_015 | heart count changes to the **server's** value and survives reload; hashtag click lands on `/kudos?hashtag=…` with the board filtered; Copy Link toast |
| Security | SEC_002, SEC_004 | own anonymous Kudo in own Sent list shows own name; page HTML contains no `@` email string and no auth uuid |

Non-functional: the suite must be idempotent across runs (F004's `kudos_likes` residue lesson —
delete by `kudos_id`, never by a hardcoded auth uuid).

## Architecture

```
playwright.config.ts
├── setup                  testMatch narrowed: (?!homepage)(?!kudos)(?!profile)
├── profile-auth-setup     testMatch /profile-auth\.setup\.ts$/
├── profile-authed         testMatch /profile\.spec\.ts/  (excludes -auth.setup)
│                          storageState: e2e/.auth/profile-user.json
│                          dependencies: ["profile-auth-setup"]
│                          expect: { timeout: 15_000 }   ← heart is server-authoritative
└── anon                   testMatch extended with |profile-anon  (route-guard cases)
```

`profile.spec.ts` must not match `profile-auth.setup.ts`; use `/^profile\.spec\.ts$/`-style anchoring
or a distinct name. Anonymous route-guard cases go in `e2e/profile-anon.spec.ts` under the existing
`anon` project (no session, so no hazard).

**Data flow:** `profile-auth.setup.ts` → `createTestSession()` (existing fixture) → cookies pinned to
`127.0.0.1` → `e2e/.auth/profile-user.json` → `profile-authed` project loads it.

## Related Code Files

Create: `e2e/profile-auth.setup.ts` (adapted from `kudos-auth.setup.ts`, header comment naming the
C9 hazard), `e2e/profile.spec.ts`, `e2e/profile-anon.spec.ts`, `e2e/fixtures/profile-constants.ts`.
Modify: `playwright.config.ts` (narrow `setup`, add two projects, extend `anon`'s `testMatch`).
Delete: none. **Do not touch** `e2e/authenticated.spec.ts`, `e2e/.auth/user.json`,
`e2e/kudos-auth.setup.ts` or `e2e/kudos-live-board.spec.ts` (the last is phase 09's).

## Implementation Steps

1. Read the K-25 root-cause report and `homepage-auth.setup.ts`'s header comment.
2. Write `e2e/profile-auth.setup.ts` from `kudos-auth.setup.ts`, changing only `authFile` to
   `e2e/.auth/profile-user.json` and the log lines. Keep the explanatory header.
3. Edit `playwright.config.ts`: narrow the `setup` `testMatch` with `(?!profile)`; add
   `profile-auth-setup` and `profile-authed`; add `profile-anon` to the `anon` project's pattern.
4. Write `e2e/fixtures/profile-constants.ts`: the seeded frame viewer's name/id, the five stat
   labels, the two direction labels, the two empty strings, the badge-slot count (6).
5. Write `e2e/profile-anon.spec.ts` — ACC_001/ACC_002 redirects.
6. Write `e2e/profile.spec.ts` — the authed matrix above, with `data-testid` hooks agreed here and
   consumed by phases 07/08: `profile-hero`, `profile-badge-row`, `profile-badge-slot`,
   `profile-tier-badge`, `profile-stats-card`, `profile-stat`, `profile-secret-box-button`,
   `profile-write-bar`, `profile-direction-trigger`, `profile-direction-option`,
   `profile-feed`, `profile-feed-empty`, `profile-feed-end`, `profile-feed-sentinel`.
   Reuse F004's `kudos-card`, `kudos-sender`, `kudos-heart` inside the feed — do not re-testid them.
7. Add the sender-identity assertion explicitly: at `?id=1`, the first Received card's
   `kudos-sender` text must equal a **named** seeded person, and `kudos-receiver` must equal the
   frame viewer. Assert the two are different strings.
8. Add `afterEach`/`afterAll` cleanup: delete `kudos_likes` by `kudos_id` (seed creates zero rows,
   so any row is test residue), and delete the composed anonymous Kudo by its sender's
   `auth_user_id`, resolved at runtime — never a snapshotted uuid.
9. Run **only** the two new projects, and record the real exit code, the failing assertion, and the
   command:
   `npx playwright test --project=profile-auth-setup --project=profile-authed --project=anon`
   (do not run the full suite in this phase).
10. Confirm the RED is caused by the profile assertions — the setup project must be **green** and
    the browser must launch. A dependency, config, browser-install or dev-server failure is **not**
    a valid RED; fix it and re-run before declaring the gate open.

## Todo List

- [ ] K-25 report and `homepage-auth.setup.ts` read
- [ ] `profile-auth.setup.ts` writes `e2e/.auth/profile-user.json` (its own file, not shared)
- [ ] `setup` project `testMatch` narrowed with `(?!profile)`
- [ ] `profile-auth-setup` + `profile-authed` projects added, `profile-anon` folded into `anon`
- [ ] `profile-authed` carries the 15s `expect` timeout, scoped to that project only
- [ ] Anon redirect cases written
- [ ] Authed matrix written, all 30 design test cases mapped or explicitly marked not-honoured
- [ ] Sender-identity assertion names the expected person
- [ ] Idempotent cleanup, no hardcoded auth uuid
- [ ] Valid RED recorded: `redTestFiles`, `redCommand`, `redExitCode`, `redFailure`

## Success Criteria

- `profile-auth-setup` passes (1 test) and writes `e2e/.auth/profile-user.json`.
- The suite exits **non-zero**, and every failure names a profile assertion (missing testid, wrong
  status, wrong copy) — not a launch, install or config error.
- `git diff playwright.config.ts` shows exactly: one narrowed regex, two added projects, one
  extended `anon` pattern. No change to the `authed` or `kudos-authed` projects.
- A single-project rerun of `--project=authed` still passes, proving C9's session was not disturbed.

## Risk Assessment

| Risk | L×I | Countermeasure |
|---|---|---|
| New project reuses `user.json` or `kudos-user.json` | M × **H** | Own setup + own storageState is a checklist item and a review gate; the K-25 report is cited in the file header |
| `setup` project runs `profile-auth.setup.ts` twice | **H** × M | Explicit `(?!profile)` step; verify with `npx playwright test --list` that the file appears in exactly one project |
| RED is invalid (config/browser failure) | M × H | Step 10 requires the setup project green and the browser launched before the gate is declared |
| Suite becomes flaky through shared DB state | M × M | Cleanup by `kudos_id`; the seed creates zero `kudos_likes` (measured: 0 rows today) |
| SEC_002 test couples this suite to F005's compose flow | M × M | One isolated test, documented in-file, and its failure diagnosed against `viet-kudo.spec.ts` before the profile is blamed |
| The live DB carries e2e residue (measured: 6 stray `kudos`, 6 stray `sunners`) | M × L | Assert relative changes and named people, never absolute table totals; recommend `supabase db reset` before the GREEN run |

## Security Considerations

- SEC_004: assert the rendered HTML contains no `@`-bearing email and no uuid-shaped string.
- SEC_003: attempt `/profile?id={other}` and assert no `Đã gửi` surface exists; the server-side
  self-scoping proof lives in phase 05's criteria, not here (the UI is only the second layer).
- The setup file must never log the session token — only the email and the cookie **name**, matching
  `kudos-auth.setup.ts`.

## Next Steps

- Opens the gate for phases 03–08. Pass `redTestFiles` / `redCommand` / `redExitCode` /
  `redFailure` read-only into both Track A phase prompts.
- Phase 10 reruns the identical command for GREEN.
