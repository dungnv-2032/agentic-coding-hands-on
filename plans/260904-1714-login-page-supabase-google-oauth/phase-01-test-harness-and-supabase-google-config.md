# Phase 01 — Test harness + Supabase Google / env foundation

## Context Links

- Plan: [plan.md](./plan.md) · Decisions: [clarifications.md](./clarifications.md) (ORCH-03, A2, A3)
- Research: [researcher-02 §Q1](./research/researcher-02-supabase-google-oauth.md) (exact `[auth.external.google]` block)
- Spec: FR-001, FR-002 in [functional-spec.md](./spec/login/functional-spec.md); §4.6 in [technical-spec.md](./spec/login/technical-spec.md)

## Overview

- **Priority:** P1 · **Owner agent:** `implementer` · **Status:** complete · **Effort:** 1.5h
- **Depends on:** nothing. **Blocks:** every other phase.
- Stand up the E2E runner and the environment/provider configuration, and **prove the harness is
  green before any feature code exists** — this is what makes phase 02's RED attributable to the
  application rather than to a missing browser binary or a dead dev server.

## Key Insights

- `e2e-red-first` only holds if a dependency/config/browser/dev-server failure cannot masquerade as
  RED. A trivial passing smoke test in this phase is the discriminator.
- Cookie domain must be pinned: `127.0.0.1:3000` everywhere (`site_url`, `NEXT_PUBLIC_SITE_URL`,
  Playwright `baseURL`, dev-server `--hostname`). A session cookie captured for `127.0.0.1` is not
  sent to `localhost` — mixing the two silently breaks the authenticated fixtures in phase 02.
- `env(...)` substitution in `supabase/config.toml` is resolved by the **CLI** from the repo-root
  `.env`, not from `.env.local` (which only the Next.js app reads).
- `additional_redirect_urls` already contains both `/auth/callback` entries — FR-002 needs no edit.

## Requirements

- FR-001 — Google provider configured in the local Supabase stack via env-substituted credentials.
- FR-002 — `/auth/callback` allow-listed (verify only; already true).
- Non-functional: no secret committed; `npm run test:e2e` runnable from a clean checkout.

## Architecture

```
package.json ──scripts──► playwright.config.ts ──webServer──► next dev @127.0.0.1:3000
                                   │
                                   └──testDir──► e2e/smoke.spec.ts  (must be GREEN here)

supabase/config.toml ──env()──► .env (repo root, gitignored) ──► GoTrue @54321
.env.example ──documents──► NEXT_PUBLIC_SITE_URL + the two Google vars
```

## Related Code Files

**Modify:** `package.json`, `package-lock.json`, `.gitignore`, `.env.example`, `supabase/config.toml`
**Create:** `playwright.config.ts`, `e2e/smoke.spec.ts`
**Create locally, never commit:** `.env` (repo root) with the two Google placeholders
**Do not touch:** anything under `app/`, `lib/`, `proxy.ts`

## Implementation Steps

1. `npm i -D @playwright/test`, then `npx playwright install chromium`. If the browser fails to
   launch on WSL2, run `npx playwright install-deps chromium` (or `install --with-deps chromium`).
2. Create `playwright.config.ts`:
   - `testDir: "e2e"`, `reporter: "list"`, `fullyParallel: false`, `forbidOnly: !!process.env.CI`
   - `use: { baseURL: "http://127.0.0.1:3000", trace: "on-first-retry" }`
   - `projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }]` — phase 02 adds the
     `setup` and authenticated projects.
   - `webServer: { command: "npm run dev -- --hostname 127.0.0.1 --port 3000", url: "http://127.0.0.1:3000", reuseExistingServer: !process.env.CI, timeout: 120_000 }`
3. `package.json` scripts: add `"test:e2e": "playwright test"` and `"typecheck": "tsc --noEmit"`.
4. `.gitignore`: add `/test-results/`, `/playwright-report/`, `/e2e/.auth/`.
5. `e2e/smoke.spec.ts` — one test: `await page.goto("/")` responds 200 and `document.body` is
   non-empty. Nothing about login. This file stays in the suite permanently as the infra canary.
6. `.env.example` — append (ORCH-03):
   - `NEXT_PUBLIC_SITE_URL=http://127.0.0.1:3000` with a comment that it must match `site_url` and
     the entries in `additional_redirect_urls`.
   - A commented note: `SUPABASE_AUTH_EXTERNAL_GOOGLE_CLIENT_ID` / `_SECRET` belong in the repo-root
     `.env` (read by the Supabase CLI), not in `.env.local`.
7. `supabase/config.toml` — insert after `[auth.external.apple]`, keys exactly as the CLI template
   (researcher-02 §Q1): `enabled = true`, `client_id = "env(SUPABASE_AUTH_EXTERNAL_GOOGLE_CLIENT_ID)"`,
   `secret = "env(SUPABASE_AUTH_EXTERNAL_GOOGLE_SECRET)"`, `redirect_uri = ""`, `url = ""`,
   **`skip_nonce_check = true`**, `email_optional = false`. Keep the CLI's own comment lines.
8. Create repo-root `.env` (gitignored) with placeholder values so the CLI's env substitution
   resolves: `SUPABASE_AUTH_EXTERNAL_GOOGLE_CLIENT_ID=local-placeholder.apps.googleusercontent.com`,
   `SUPABASE_AUTH_EXTERNAL_GOOGLE_SECRET=local-placeholder`.
9. `npx supabase stop && npx supabase start`, then `npx supabase status` — the stack must come back
   up. If the CLI rejects the block (credential validation), set `enabled = false`, leave the block
   and the comments in place, and record the fact in the phase report; nothing downstream depends on
   the provider actually being live (see Risk R2).
10. `npm run test:e2e` → exit code **0**. Record the command and exit code; phase 02 cites it as the
    proof that its RED is application-caused.

## Todo List

- [x] `@playwright/test` installed, chromium launches
- [x] `playwright.config.ts` with pinned `127.0.0.1:3000` baseURL + webServer
- [x] `test:e2e` and `typecheck` scripts added
- [x] `.gitignore` covers `test-results/`, `playwright-report/`, `e2e/.auth/`
- [x] `e2e/smoke.spec.ts` GREEN (exit 0)
- [x] `NEXT_PUBLIC_SITE_URL` documented in `.env.example`
- [x] `[auth.external.google]` block in `supabase/config.toml` with `skip_nonce_check = true`
- [x] Local stack restarts clean; `/auth/callback` confirmed already allow-listed (FR-002)
- [x] `git status` shows no `.env`, no key material staged

## Success Criteria

- `npm run test:e2e` exits 0 with only the smoke test present — harness validity established.
- `npx supabase status` healthy after the config change (FR-001 wired, credentials pending).
- `grep -r "sb_publishable\|service_role\|apps.googleusercontent" --include='*' -n .` finds nothing
  new outside `.env`/`.env.local`.

## Risk Assessment

| ID | Risk | Likelihood | Impact | Countermeasure |
|----|------|-----------|--------|----------------|
| R1 | Playwright browser deps missing on WSL2 → the runner cannot start | High | High (invalidates the whole test policy) | `playwright install-deps chromium`; this phase does not close until the smoke test exits 0 |
| R2 | `supabase start` rejects the Google block with placeholder credentials | Medium | High (kills the running local stack) | Verify by restarting inside this phase; fallback `enabled = false` with the block retained. Phase 02 intercepts the authorize navigation, so no test depends on a live provider |
| R3 | Dev server binds `localhost`/`::1` while tests use `127.0.0.1` → cookies never sent | Medium | High | `--hostname 127.0.0.1` in the webServer command; baseURL pinned to the same host |
| R4 | `skip_nonce_check = true` is doc-sourced, unverified (A3) | Low | Medium | Manual smoke test the first time real Google credentials land; recorded as a follow-up, not a blocker |

## Security Considerations

- Secrets stay in the gitignored repo-root `.env`; `config.toml` only ever carries `env(...)` refs.
- `service_role` key remains absent (ORCH-02) — the E2E suite gives no reason to introduce it.
- `.env.example` documents placeholders only.

## Rollback

`npm remove -D @playwright/test`; delete `playwright.config.ts` and `e2e/`;
`git checkout -- package.json package-lock.json .gitignore .env.example supabase/config.toml`;
`npx supabase stop && npx supabase start`. No application code was touched, so nothing else regresses.

## Next Steps

Hand the recorded `test:e2e` command and its exit-0 evidence to phase 02.
