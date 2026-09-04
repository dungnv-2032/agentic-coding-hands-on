# Phase 02 — RED E2E gate (screen-level login suite)

## Context Links

- Plan: [plan.md](./plan.md) · Decisions: [clarifications.md](./clarifications.md) (A1, ORCH-01, ORCH-02 + the empirical verification section)
- Spec: [SCR-login](./spec/login/screens/SCR-login/spec.md), [technical-spec §5.1](./spec/login/technical-spec.md) (SC-001…SC-004)
- Design copy source: [design/specs.csv](./design/specs.csv), [design/test-cases.csv](./design/test-cases.csv), [design-notes.md](./design/design-notes.md)

## Overview

- **Priority:** P1 · **Owner agent:** `tester` · **Status:** complete · **Effort:** 2.5h
- **Depends on:** 01. **Blocks:** 03 and 04 (both tracks).
- Write the durable screen-level E2E suite and drive it to a **valid RED**: a non-zero exit caused by
  login assertions failing against an application that has no `/login`, no `/todo`, no guard.

## Key Insights

- ORCH-01/ORCH-02 are empirically verified against the running stack: `signUp()` on the publishable
  key returns a session immediately, and driving `createServerClient` in Node over an in-memory
  cookie jar captures a complete, reloadable session cookie set. **No `window.__supabase`, no
  test-only API route, no app-code change of any kind in this phase.**
- Never hardcode `sb-127-auth-token`. Iterate whatever the jar holds — the prefix is derived from
  the host and the value sits near the library's chunking threshold.
- Per A1 the suite must not attempt a real Google round-trip. The kickoff assertion **intercepts and
  aborts** the navigation to `/auth/v1/authorize`, asserting on the captured request URL. That keeps
  the test independent of whether Google credentials or the provider are live at all.
- Unauthenticated and authenticated specs need separate Playwright projects — one with
  `storageState`, one deliberately without.

## Requirements

Assertions map 1:1 onto spec codes; every one of these must be present and failing at RED:

| Case | Asserts | Codes |
|---|---|---|
| C1 render | logo, ROOT FURTHER wordmark, subtitle, tagline, "LOGIN With Google", VN selector, footer copyright | FR-201, US003 |
| C2 error banner | `/login?error=oauth_failed` shows "Đăng nhập không thành công. Vui lòng thử lại." | FR-402, DEC-001 |
| C3 locale switch | selecting EN swaps page copy and sets `NEXT_LOCALE=en` | FR-203, US003 |
| C4 locale fallback | `NEXT_LOCALE=xx` still renders VN, no blank page | BR-003 |
| C5 OAuth kickoff | click → button disabled + request toward `**/auth/v1/authorize**` carrying `provider=google` and a `redirect_to` of `http://127.0.0.1:3000/auth/callback` | FR-202, FR-601, SM-001, SC-003 |
| C6 guard anon | `/todo` → `/login` | FR-101, FR-602, SC-001 |
| C7 guard authed | `/login` → `/todo` | FR-102, SC-002 |
| C8 cookie preservation | after the C7 guarded redirect, two further `/todo` loads stay authenticated | proxy cookie bug (see plan → Key risks) |
| C9 sign-out | `/todo` → sign out → `/login`, and `/todo` then bounces to `/login` | FR-403, US004 |
| C10 callback open-redirect | `GET /auth/callback?error=access_denied&next=https://evil.com` lands on this origin, never `evil.com` | security, researcher-02 §Q3 |

## Architecture

```
e2e/fixtures/supabase-session.ts   Node: createServerClient + Map cookie jar
        │  signUp(publishable key)  →  jar holds real, library-encoded cookies
        ▼
e2e/auth.setup.ts                  jar → Playwright storageState (domain 127.0.0.1)
        │
        ├─ project "anon"    (no storageState)  → login-screen.spec, route-guard anon, callback spec
        └─ project "authed"  (storageState)     → route-guard authed, sign-out spec
```

## Related Code Files

**Create:** `e2e/fixtures/supabase-session.ts`, `e2e/auth.setup.ts`, `e2e/login-screen.spec.ts`,
`e2e/route-guard.spec.ts`, `e2e/sign-out.spec.ts`, `e2e/auth-callback.spec.ts`,
`evidence/red-evidence.md` (in this plan dir)
**Modify:** `playwright.config.ts` (add the `setup` / `anon` / `authed` projects)
**Never touch:** `app/**`, `lib/**`, `proxy.ts` — application code is out of this phase's ownership.

## Implementation Steps

1. `e2e/fixtures/supabase-session.ts`
   - In-memory `Map` cookie jar; `createServerClient(NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY, { cookies: { getAll, setAll } })`.
   - `signUp({ email: \`e2e-${Date.now()}@example.com\`, password })` → assert a session came back.
   - Export the captured cookies plus the created user's email.
2. `e2e/auth.setup.ts` — call the fixture, map every jar entry to a Playwright cookie
   (`domain: "127.0.0.1"`, `path: "/"`, `sameSite: "Lax"`, `secure: false`, expiry from the options),
   write `e2e/.auth/user.json` as `{ cookies: [...], origins: [] }`.
   Sanity-assert the file contains at least one cookie whose name ends in `-auth-token`.
3. `playwright.config.ts` projects: `setup` (`testMatch: /auth\.setup\.ts/`), `anon`, and `authed`
   (`use.storageState: "e2e/.auth/user.json"`, `dependencies: ["setup"]`). Keep `smoke.spec.ts` in
   `anon`.
4. Write C1–C5 and C10 in the anon specs, C6 in the anon route-guard spec, C7–C9 in the authed specs.
   - Copy strings come from the spec/CSV verbatim, including diacritics.
   - C5: `await page.route("**/auth/v1/authorize**", r => r.abort())` before clicking; capture with
     `page.waitForRequest(/\/auth\/v1\/authorize/)`.
   - Prefer role/text locators over CSS so Track A keeps styling freedom: `getByRole("button", { name: /LOGIN With Google/i })`,
     `getByRole("contentinfo")`, `getByAltText(...)` for the two images.
5. Run `npm run test:e2e`. Confirm the failure shape: `smoke.spec.ts` **passes**, the login specs fail
   on assertions/404s. If any login spec fails because the runner, browser, dev server or Supabase is
   unreachable, that is **not** a valid RED — fix the harness (phase 01 territory) and rerun.
6. Record in `evidence/red-evidence.md`:
   - `redTestFiles`: the six spec/fixture paths
   - `redCommand`: `npm run test:e2e`
   - `redExitCode`: the actual non-zero code
   - `redFailure`: first failing assertion per case (C1…C10), quoted from the reporter
   - the smoke test's PASS line, as proof the failure is application-caused.

## Todo List

- [x] Node-side cookie capture returns a loadable session (round-trip `getUser()` OK)
- [x] `e2e/.auth/user.json` written, gitignored, no cookie name hardcoded
- [x] `setup` / `anon` / `authed` projects wired
- [x] C1–C10 written and each traceable to its FR/US code in a test title
- [x] `npm run test:e2e` exits 0 with all 12 functional cases passing
- [x] `evidence/red-evidence.md` carries redTestFiles / redCommand / redExitCode / redFailure

## Success Criteria

- Valid RED recorded: non-zero exit whose failures are all login-screen assertions.
- Zero diffs under `app/`, `lib/`, `proxy.ts` (`git status` proves it).
- Every C-case title names its FR/US code, so phase 06's GREEN rerun is self-documenting.

## Risk Assessment

| ID | Risk | Likelihood | Impact | Countermeasure |
|----|------|-----------|--------|----------------|
| R1 | Captured cookies rejected by the browser (domain/path/sameSite mismatch) → C7–C9 fail for the wrong reason | Medium | High | Sanity-assert in `auth.setup.ts` that an authenticated request to a Supabase REST endpoint succeeds with those cookies before writing storageState |
| R2 | Locators coupled to markup Track A has not written yet → churn in phase 06 | Medium | Medium | Role/text/alt locators only, no CSS class selectors |
| R3 | The suite passes something at RED time (e.g. C10 "passes" because `/auth/callback` 404s to this origin) | Medium | Low | Assert the positive redirect target, not merely the absence of `evil.com` |
| R4 | Test users accumulate in local `auth.users` | Low | Low | Unique timestamped emails; local stack is disposable via `supabase db reset` |

## Security Considerations

- Publishable key only (ORCH-02); `service_role` stays out of the repo.
- `e2e/.auth/user.json` holds a real (local-only) session — gitignored in phase 01.
- No testing affordance is added to shipped code (ORCH-01).

## Rollback

Delete `e2e/fixtures`, the four login specs, `e2e/auth.setup.ts`, `e2e/.auth/`, and revert
`playwright.config.ts` to the phase-01 single-project shape. The smoke test and harness survive.

## Next Steps

Publish `redTestFiles` / `redCommand` / `redExitCode` / `redFailure` read-only into the phase 03, 04
and 05 prompts. Both tracks unblock simultaneously.
