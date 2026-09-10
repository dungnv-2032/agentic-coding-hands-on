# Playwright E2E harness — reference for a new screen-level spec

## 1. Run command

Whole file, its own project (mirrors CI, forces the right auth setup as a dependency):
```
npx playwright test e2e/<file>.spec.ts --project=<project-name>
```
Or the npm script for the whole suite: `npm run test:e2e` (= `playwright test`).

Confirmed live: `npx playwright test e2e/profile-anon.spec.ts --project=anon` → real dev server boot, real Supabase signUp, GREEN in ~2 min (see §5 for exact output shape).

Config: `playwright.config.ts`, `testDir: "e2e"`, `reporter: "list"`, `fullyParallel: false`.

**Projects and dependency chains** (name → testMatch → dependencies → storageState):
| Project | testMatch (regex) | depends on | storageState |
|---|---|---|---|
| `setup` | generic `*auth.setup.ts`, excludes homepage/kudos/profile-prefixed | — | writes `e2e/.auth/user.json` |
| `homepage-auth-setup` | `homepage-auth.setup.ts` | — | writes `e2e/.auth/homepage-user.json` |
| `kudos-auth-setup` | `kudos-auth.setup.ts` | — | writes `e2e/.auth/kudos-user.json` |
| `profile-auth-setup` | `profile-auth.setup.ts` | — | writes `e2e/.auth/profile-user.json` |
| `anon` | smoke\|login-screen\|route-guard\|callback-security\|homepage\|award-system\|profile-anon\|kudos-live-board(not -authed) | `setup` | none (no session) |
| `authed` | `authenticated.spec.ts` | `setup` | `e2e/.auth/user.json` |
| `kudos-authed` | `kudos-live-board-authed\|viet-kudo` | `kudos-auth-setup` | `e2e/.auth/kudos-user.json`; `expect.timeout` raised to 15s (server-authoritative heart toggle) |
| `homepage-authed` | `homepage-authed.spec.ts` | `homepage-auth-setup` | `e2e/.auth/homepage-user.json` |
| `profile-authed` | `profile.spec.ts` | `profile-auth-setup` | `e2e/.auth/profile-user.json`; `expect.timeout` 15s |
| `visual-capture` | `capture-homepage-visual.spec.ts` | `homepage-auth-setup` | on-demand only, not in default suite |

Pattern for a new screen: pick `anon` if public/unauthenticated is enough (add the new spec's basename to the `anon` testMatch regex); otherwise add a dedicated `<name>-auth.setup.ts` + `<name>-auth-setup` project + `<name>-authed` project, each with its OWN session file — never reuse `e2e/.auth/user.json` from `setup`/`authed`, because `authenticated.spec.ts`'s C9 test does a global `signOut()` that revokes that shared session non-deterministically for concurrent workers. This isolation pattern is documented at `e2e/profile-auth.setup.ts:9-24`.

## 2. webServer / baseURL / preconditions

- `webServer.command`: `npm run dev -- --hostname 127.0.0.1 --port 3000` — **auto-started by config**, `reuseExistingServer: false` (always fresh, so `NEXT_PUBLIC_EVENT_START_AT` env is re-read every run), `timeout: 120_000`.
- `baseURL: "http://127.0.0.1:3000"` — must stay `127.0.0.1` everywhere (cookie domain pinning comment at top of config), not `localhost`.
- `webServer.env`: injects `NEXT_PUBLIC_EVENT_START_AT` pinned to now+45 days (deterministic countdown state).
- Preconditions for any run:
  - **Supabase local must already be running** (confirmed live: `docker ps` shows `supabase_db_my-app`, `supabase_auth_my-app`, etc. — the config does not start Supabase itself).
  - `.env.local` must exist at repo root with `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_SITE_URL` — read directly by `e2e/fixtures/supabase-session.ts` (Node doesn't auto-load Next's env) AND by the Next dev server itself.
  - WSL2-only: `.playwright-libs/` vendored shared-lib workaround (gitignored), no-op if system libs present.

## 3. Selector conventions

- **data-testid is the primary, near-exclusive selector**: `page.getByTestId("profile-hero")`, `card.getByTestId("kudos-sender")`, etc. Naming style: kebab-case, `<screen>-<element>` (`profile-badge-slot`, `profile-direction-option`, `kudos-heart-count`) or bare component name reused across screens (`kudos-card`, `kudos-sender`) when the same card renders on multiple screens.
- **Role queries** used sparingly for semantic elements: `page.getByRole("heading", { level: 1 })`, `bar.getByRole("link")`, `menu.getByRole("option", { selected: true })`.
- **Vietnamese copy** asserted as exact exported string constants from `e2e/fixtures/*-constants.ts` (never inline literals), transcribed verbatim from a `clarifications.md` doc cited in each constants file's header — e.g. `EMPTY_STATES.received = "Hiện tại chưa có Kudos nào."`. Assertions use `toContainText`/`toHaveText` against these constants, or `.filter({ hasText: LABEL })` scoped to a specific testid when a bare `getByText` would be a strict-mode violation (documented case: `DIRECTION_LABELS` collide between trigger, option, and stats-card text — see `profile-constants.ts:64-80`).
- Never assert on untranslated hardcoded Vietnamese strings inline; always route through a fixtures constants file so a copy change is a one-line fix.

## 4. Auth vs anonymous

- Anonymous/public screens run in the `anon` project — **no setup project needed** if the screen requires zero session (e.g. `kudos-live-board.spec.ts` un-authed cases run here). `anon` still depends on `setup` in the config, but a spec matched only under `anon`'s testMatch never touches storageState.
- Access-control-only specs (redirect-to-login assertions for an otherwise-authed screen) are split into a separate `*-anon.spec.ts` file registered under `anon`, sibling to the authed file (pattern: `profile.spec.ts` vs `profile-anon.spec.ts`).
- Authenticated screens: a dedicated `<screen>-auth.setup.ts` creates a session via `createTestSession()` (`e2e/fixtures/supabase-session.ts` — real Supabase `signUp` against local GoTrue, captures cookies through an in-memory jar, converts to Playwright storageState JSON, domain forced to `127.0.0.1`). Each setup writes its own `e2e/.auth/<screen>-user.json` (gitignored) plus, for profile, a sidecar meta file (`profile-user-meta.json`) recording the signed-up email/local-part for assertions that need the actual generated identity (JWT fallback name).
- **A new anonymous public screen spec needs NO setup project** — add its file to the `anon` testMatch regex directly.

## 5. What a valid RED looks like

Reporter is `list`. Confirmed live GREEN shape:
```
Running N tests using 1 worker
✓ Test session created and saved to e2e/.auth/user.json   <- setup project console.log, only if setup runs
  ✓  1 [setup] › e2e/auth.setup.ts:60:6 › authenticate and save state (6.6s)
  ✓  2 [anon] › e2e/profile-anon.spec.ts:16:7 › ... ACC_001 ... (570ms)
  3 passed (2.0m)
```
A **valid assertion RED** replaces `✓` with `✘`/`1)` per failing test, followed by Playwright's own diff block (`Error: expect(locator).toBeVisible()` etc. with `Expected/Received` or `Locator:`/`Timeout` detail), and ends with `N failed` — the process exits non-zero from a genuine `expect()` mismatch against the real running app.

**Distinguish from non-assertion failures** (these are NOT a valid RED and must not be reported as one):
- `Error: browserType.launch: ... error while loading shared libraries` → browser/lib install failure (WSL2 missing libs — see `.playwright-libs/` workaround in config header).
- `Process from config.webServer was not able to start. Exit code: ...` or `Timed out waiting 120000ms from config.webServer` → dev-server/config failure, not the app under test.
- `.env.local not found...` or `Missing NEXT_PUBLIC_SUPABASE_URL...` thrown from `supabase-session.ts` → env/config failure, surfaces inside a `setup` project test as its own thrown Error, not an `expect()` diff.
- `ECONNREFUSED 127.0.0.1:xxxx` / GoTrue `signUp failed` → Supabase local not running — precondition failure, not an assertion RED.
- A real RED must show the failing test's title with `1)` and a `page.getByTestId(...)`/`expect(...)` line pointing at app behavior, sourced from the spec file itself.

## 6. Test-data / seed dependency

Specs are tightly coupled to `supabase/seed.sql` rows, referenced by name/id through constants files (never hardcoded inline in spec bodies):
- `sunners` id 1 = **"Huỳnh Dương Xuân Nhật"**, dept `CEVC10`, `kudos_received_baseline=0`, 25 received/25 sent seeded rows (`FRAME_VIEWER_*`).
- `sunners` id 2 = **"Huỳnh Dương Xuân"**, dept `CEVC10`, `kudos_received_baseline=50` → tier "Legend"/"Super Hero" depending on suite math (`FRAME_RECEIVER_*`); has 25 seeded received Kudos used for feed-paging test.
- `sunners` "Nguyễn Hoàng Linh" (dept `CEVC2 - CySS`, baseline 45) used as `COMPOSE_TARGET_NAME` in profile's SEC_002 — deliberately NOT id 1/2 so the compose side-effect (recipient's received count) doesn't corrupt other tests' assumptions, and its name is unambiguous in the recipient-picker substring search.
- 13 seeded hashtags (`HASHTAG_OPTIONS`), department list, and a leaderboard/gift dataset back the kudos-live-board suite.
- Tests that **write** data (profile SEC_002 compose, heart-toggle likes) always clean up via direct `psql`/`docker exec supabase_db_my-app psql` `DELETE` scoped by a run-unique token (`campaign`) or resolved-at-runtime id — never a hardcoded/snapshotted uuid, since auth ids differ every run. A new spec that mutates data must follow this same cleanup-in-`finally`/`afterEach` pattern to stay idempotent across repeated RED/GREEN cycles.
- `createTestSession()` always signs up a **brand-new** Supabase Auth user per run (`e2e-<ts>-<pid>-<rand>@example.com`) — a new authed spec gets a fresh session with **no** `sunners` row by default (BR-001: GET never provisions one), so "self" views are the sparse/JWT-fallback state unless the spec explicitly links the session to a seeded roster row.

## Unresolved / to verify before writing the new spec
- Whether the new "the-le-rules-panel" screen is public (→ `anon`, no setup) or requires auth — not determinable from this harness alone; needs the screen's own spec/clarifications.
- Exact seed rows (if any) the new screen needs were not investigated — this report only covers rows already consumed by profile/kudos suites.
