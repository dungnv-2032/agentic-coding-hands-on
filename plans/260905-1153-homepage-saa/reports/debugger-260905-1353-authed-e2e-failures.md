# Debugger Report — `homepage-authed.spec.ts` failures (ID-27, ID-36, ID-38)

Date: 2026-09-05
Scope: `app/_components/account-menu.tsx` (fixed), `e2e/homepage-authed.spec.ts` (read-only, no test edit needed), everything else read-only.

## Verdict

**Two independent, proven root causes** — not one, and not "environmental."

1. **PROVEN + FIXED (in scope):** `app/_components/account-menu.tsx` set `role="menuitem"` on the Profile `<Link>` and the Sign-out `<button>`. An explicit ARIA `role` attribute overrides the element's native role, so both items stopped being an accessible `link` / `button` and became `menuitem` instead. `getByRole("link", …)` / `getByRole("button", …)` scoped to `[data-testid="account-menu"]` then find zero matches → "element(s) not found" on ID-36. Deterministic, 100% reproducible, fixed by removing the two `role="menuitem"` attributes.

2. **PROVEN, NOT FIXED (out of scope):** Every test in the `authed` Playwright project shares **one** Supabase session (`e2e/.auth/user.json`, created once by `e2e/auth.setup.ts` → `createTestSession()`). `e2e/authenticated.spec.ts`'s test **C9** calls the real `signOut` server action, which calls `supabase.auth.signOut()` with no `scope` argument — the SDK's default is `scope: 'global'`, which revokes that session everywhere. Whichever `homepage-authed.spec.ts` test's page-load lands *after* C9's revocation lands genuinely renders the **unauthenticated** header (bell/account button correctly absent from the DOM per this component's own documented contract, `home-header.tsx`: "absent from the DOM (not just hidden) when `isAuthenticated` is false — BR-002"). This is why the specific failing test(s) vary run-to-run, and why ID-1 is not a contradiction — it's a race, and this run ID-1 won it, ID-27/36/38 didn't. This is a test-fixture/session-isolation defect in files outside my edit scope (`e2e/auth.setup.ts`, `e2e/fixtures/supabase-session.ts`, `e2e/authenticated.spec.ts` — a different phase's files). Flagging for escalation, not fixing.

## Evidence chain

### Step 1 — reject "session-state pollution" as a vague label, get the real error text

Ran the file in isolation first (`npx playwright test e2e/homepage-authed.spec.ts --project=authed`, 1 worker, no `authenticated.spec.ts` in the run):

```
✓ ID-1   ✓ ID-27   ✘ ID-36   ✓ ID-38
```

Only ID-36 failed, with a **real accessible-tree snapshot** captured at failure (`test-results/.../error-context.md`):

```yaml
- button "Tài khoản" [expanded]
- menu "Tài khoản":
  - menuitem "Hồ sơ"       ← test looks for role "link"
  - menuitem "Đăng xuất"   ← test looks for role "button"
```

The account menu **did open** — session was fine, click worked, DOM was correct. The test's `getByRole("link", {name: /profile|hồ sơ/i})` failed because the item's accessible role is `menuitem`, not `link`. This eliminates "Playwright context reuse" and "hydration" for this failure outright: the button clicked, the menu opened, the content is correct, only the *role* mismatches the query. Read `account-menu.tsx:92-114` — both `<Link href="/profile" role="menuitem">` and `<button type="submit" role="menuitem">` carry an explicit override. Confirmed against `clarifications.md:19` — the design decision is "Profile / Sign out / Admin Dashboard, role-gated" (conditionally rendered by user role), **not** a mandate for the ARIA `menu`/`menuitem` widget pattern. `use-dismiss-on-outside.ts` and `language-selector.tsx` were read and ruled out — the dismiss-on-outside hook is copy-identical in intent to the already-green `language-selector.tsx`'s inline version and does not interfere with the click that *opens* the panel (it only listens after `open` is already true, confirmed by the effect's early `if (!open) return`).

### Step 2 — reproduce the full command exactly as reported

`npm run test:e2e -- --project=anon --project=authed --reporter=list` (6 workers, default):

Run A: 2 failed (ID-36, ID-38); ID-27 passed.
Run B (after the account-menu.tsx fix, re-run): **3 failed — ID-27, ID-36, ID-38, exactly the reported set** — and ID-1 passed. Different runs, different failing subsets, same test file, same code. This variability across identical commands is itself evidence against a deterministic UI bug and for a **race**.

### Step 3 — isolate the variable: workers

`npx playwright test --project=authed --workers=1` (forces `authenticated.spec.ts` to run to completion before `homepage-authed.spec.ts` starts, same shared `e2e/.auth/user.json`):

```
✓ C7  ✓ C8  ✓ C9  ✘ ID-1  ✘ ID-27  ✘ ID-36  ✘ ID-38
```

**All four `homepage-authed` tests fail, including ID-1**, once `authenticated.spec.ts`'s C9 (sign-out) has run first. This is the key experiment: it shows ID-1's pass/fail has nothing to do with the homepage code — it is purely a function of whether C9 has revoked the shared session yet by the time `homepage-authed.spec.ts` makes its request.

### Step 4 — find the mechanism

- `e2e/fixtures/supabase-session.ts`: `createTestSession()` creates **one** user/session for the *entire* `authed` project and deliberately sets `expires_at` to 60s in the past (comment: "Expire the access token so the proxy is forced to refresh it during the guarded redirect... for C8"). This session — access token pre-expired, one refresh token — is written once to `e2e/.auth/user.json` and loaded as `storageState` by **every** authed test file/context.
- `proxy.ts` (read-only, comment already documents the exact mechanism): "GoTrue rotates a refresh token... Supabase refresh tokens are single-use... the browser is left holding an already-consumed token and gets silently logged out on its very next request."
- `supabase/config.toml`: `enable_refresh_token_rotation = true`, `refresh_token_reuse_interval = 10` — only a 10s grace window for reuse.
- `app/_actions/auth.ts`: `signOut()` calls `supabase.auth.signOut()` with **no scope argument**. `node_modules/@supabase/auth-js/dist/main/GoTrueClient.js:3405`: `async signOut(options = { scope: 'global' })` — confirmed default is `'global'`, which the SDK's own docs describe as signing the user "out of all sessions."
- `app/_page-context.ts`: `getPageContext()` calls `supabase.auth.getUser()` (a real network validation, not a JWT-only check) and returns `isAuthenticated: user !== null`.
- `app/_components/home-header.tsx:24-28` (comment, verified against the accessibility snapshots): "Bell and account are absent from the DOM (not just hidden) when `isAuthenticated` is false."

Chain: one shared session (pre-expired access token) → every authed test's first request forces a GoTrue refresh → C9 additionally performs a real **global** sign-out, permanently killing that shared session → any homepage-authed test whose request lands after that (or loses the single-use-refresh-token race under the 6-worker schedule) gets `user: null` from `getUser()` → `HomePage` genuinely renders the anonymous header → bell/account are not in the DOM → Playwright reports "element(s) not found" / click timeout. **Confirmed directly**: the page snapshot captured at the moment of the ID-27 full-run failure shows the header rendering only the logo, nav, and language selector — no bell, no account button — i.e. the anonymous variant, not a slow-to-hydrate authenticated one.

## Hypotheses eliminated

| # | Hypothesis | Verdict | Evidence |
|---|---|---|---|
| 1 | Strict-mode violation misread as timeout | **Partially confirmed, but only explains ID-36 in isolation** | The isolated run's error was `toBeVisible() … element(s) not found`, not a strict-mode multi-match error — but it *is* a role mismatch (see root cause #1), not a raw "can't locate" failure. Fixed. |
| 2 | Session not actually authenticated (expired token in `user.json`) | **Confirmed, refined** | The token isn't merely stale — it's actively revoked mid-suite by C9's `signOut({scope:'global'})`, and separately race-prone via single-use refresh-token rotation. Not a static expiry problem; a live cross-test revocation. |
| 3 | Real UI defect: dismiss-on-outside swallows the opening click | **Eliminated** | `useDismissOnOutside`'s pointerdown listener is only registered `if (open)` — it cannot fire before the state that opens the panel exists. The isolated-run snapshot shows the menu **did** open (`[expanded]`, children present) when the session was valid; only the role query failed. |
| 4 | Hydration race (click lands before handler attaches) | **Eliminated as primary cause** | `auth.setup.ts` already performs a bundle-warmup step for `/login` and `/todo`; and the isolated single-worker run (no concurrency, no C9 interference) passed ID-1/27/38 with sub-second timings — a hydration race would not explain the specific, session-shaped failure signature (header falling back to the anonymous variant) seen in the full-run traces. |
| "Playwright session-state pollution / context reuse" (previous verdict) | **Refuted as stated, root cause named instead** | Playwright *does* give each test a fresh `BrowserContext` from the same `storageState` file — that part of the previous verdict is correct, but it stopped there. The pollution is not in Playwright's context handling; it is that **all those fresh contexts point at the same live Supabase session**, and one test (C9) legitimately destroys that shared session server-side. Named, not hand-waved. |

## Root cause statement

**#1 (fixed):** `app/_components/account-menu.tsx` explicitly set `role="menuitem"` on the Profile link and Sign-out button, overriding their implicit `link`/`button` roles and breaking every `getByRole("link"|"button", …)` query scoped to the menu — independent of session state, 100% reproducible in a clean, C9-free run.

**#2 (proven, escalated):** `e2e/authenticated.spec.ts`'s C9 test signs out the **one shared** Supabase session (`e2e/.auth/user.json`) with GoTrue's default `scope: 'global'`, which every test file in the `authed` project is using concurrently/sequentially. Once C9 runs (or a concurrent worker loses the single-use-refresh-token race, `refresh_token_reuse_interval = 10`s in `supabase/config.toml`), any other authed test that has not yet completed its page load is now genuinely unauthenticated, and the homepage correctly (by design, BR-002) renders without the bell/account button. This is a **test-fixture design defect** (one destructive, session-revoking test sharing state with independent scenario tests), not a UI bug, not a Playwright bug, and not vaguely "environmental."

## Fix applied (in scope)

`app/_components/account-menu.tsx`: removed the two `role="menuitem"` attributes from the Profile `<Link>` and the Sign-out `<button>`, restoring their native `link`/`button` accessible roles. No assertions were weakened, no `.first()` added, no test skipped — the test's locators were already correct against the documented contract (`clarifications.md:19`); the component was wrong.

Verified: `tsc --noEmit` clean (unrelated stale `.next/dev/types/validator.ts` errors cleared after deleting the generated file; not caused by this change), `npm run lint` clean (0 errors, pre-existing unused-var warnings only, all in test files untouched by this fix). Isolated re-run of `homepage-authed.spec.ts` alone: **5 passed, 1 skipped, exit 0** — ID-1/27/36/38 all green.

## Fix NOT applied (out of scope — escalating)

Root cause #2 lives in `e2e/auth.setup.ts`, `e2e/fixtures/supabase-session.ts`, and `e2e/authenticated.spec.ts` — none of which are `app/_components/**` or `e2e/homepage-authed.spec.ts`, and the brief explicitly restricts edits to those two locations plus says not to touch another phase's files without saying why. I'm saying why here instead of touching them. Recommended directions, ranked:

1. **Give `homepage-authed.spec.ts` its own session** — either its own `auth.setup.ts`-equivalent creating a second, independent test user, or a `test.beforeAll` in that file that calls `createTestSession()` again for its own isolated storageState, so C9's sign-out in a sibling file can never reach it.
2. **Scope C9's sign-out to `local`** — only if product behavior actually allows local-only sign-out semantics; likely wrong for a real security-sensitive "sign out" button, so treat this as the lower-priority option.
3. **Serialize `authenticated.spec.ts` after `homepage-authed.spec.ts`** in `playwright.config.ts` project ordering, or split them into separate Playwright projects each with their own `dependencies: ["setup"]` invocation (separate storageState files) — closes the immediate symptom but is fragile if a third destructive test is added later.

Option 1 is the correct fix: it addresses the actual invariant that broke (one Supabase session must not be shared between a test that legitimately destroys it and tests that assume it stays alive).

## Monitoring / test-architecture gap that let this through

- **No test isolation invariant for shared `storageState`.** Nothing flags "a destructive auth action (sign-out) shares a session file with N other test files." Add a lint/convention check or a comment contract in `playwright.config.ts` next to the `authed` project stating which files may safely assume a persistently-alive session versus which own a one-shot login.
- **`trace: "on-first-retry"` is dead configuration locally.** `playwright.config.ts` sets no `retries`, so retries default to `0` outside CI — meaning `on-first-retry` traces are **never captured** in local runs. Every diagnosis here had to rely on `error-context.md` accessibility snapshots instead of a real Playwright trace. Recommend `retries: process.env.CI ? 2 : 1` (or explicit `trace: "on"` for local ad-hoc debugging) so a trace actually exists next time.
- **No accessible-role review on ARIA-pattern components.** `role="menu"`/`role="menuitem"` was added without the matching keyboard-navigation behavior the ARIA APG requires for a real menu widget (no arrow-key roving focus, unlike `language-selector.tsx`'s fully-implemented `listbox`). A component-level a11y checklist (or an eslint-plugin-jsx-a11y rule flagging `role="menu"` without keydown handling) would have caught this before it reached tests.

## Re-run (real result, after the fix)

`npm run test:e2e -- --project=anon --project=authed --reporter=list`:

```
3 failed
  [authed] homepage-authed.spec.ts ID-27 [FR-201]
  [authed] homepage-authed.spec.ts ID-36 [FR-202]
  [authed] homepage-authed.spec.ts ID-38 [FR-203]
1 skipped
41 passed (2.4m)
```

Exit code: **1** (non-zero). This is the honest result — root cause #1 is fixed and verified in isolation (0 failures when `authenticated.spec.ts`'s C9 cannot race it), but root cause #2 is a real, still-open defect in files outside this task's edit scope, and it reproduces the exact ID-27/36/38 set the task described. I did not touch `e2e/auth.setup.ts`, `e2e/fixtures/supabase-session.ts`, `e2e/authenticated.spec.ts`, `proxy.ts`, or `lib/supabase/**` — confirmed via `git status --short`, only `app/_components/account-menu.tsx` shows as changed among the files this investigation touched.

**Status:** DONE_WITH_CONCERNS
**Summary:** Two distinct proven root causes, not "environmental": (1) `account-menu.tsx` overrode Profile/Sign-out's native `link`/`button` roles with `role="menuitem"`, breaking `getByRole` queries — fixed, verified GREEN in isolation. (2) `authenticated.spec.ts`'s C9 test performs a real, default-`scope:'global'` Supabase sign-out on the ONE session every `authed`-project test shares via `e2e/.auth/user.json`, so whichever homepage-authed test's request lands after that revocation (or loses the single-use-refresh-token race under 6 workers) is genuinely logged out and correctly renders the header without bell/account — this is why ID-1 sometimes passes and ID-27/36/38 don't, run to run. Root cause #2 is proven with reproducible evidence but lives outside my edit scope (test-fixture files in a different phase); re-run after fixing #1 alone still exits 1 with the exact reported 3-test failure set, confirming #2 is real and unresolved.
**Concerns/Blockers:** Root cause #2 needs a decision from whoever owns `e2e/auth.setup.ts` / `e2e/authenticated.spec.ts` (F001_Login phase) — recommend giving `homepage-authed.spec.ts` its own independent Supabase session (option 1 above) rather than sharing `e2e/.auth/user.json` with a file that contains a real global sign-out test. Until that lands, `--project=anon --project=authed` will keep failing nondeterministically (0-3 of ID-1/27/36/38, depending on worker scheduling).
