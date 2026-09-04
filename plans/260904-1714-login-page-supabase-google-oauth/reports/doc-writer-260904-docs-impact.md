# Docs Impact — Login/Google OAuth feature (2026-09-04)

**Docs impact: minor** — the machine-registered spec layer (`docs/features/F001_Login/`,
`docs/screens/SCR001_Login/`) already fully covers feature behavior and was read but not touched (no
`docs/system`, `tkm:takumi` Step 6, or `rebuild-spec` Wave 9 invocation in this session — surgical-edit
permission for that layer wasn't granted here). What was genuinely missing was operational: nothing
told a newcomer how to make the feature *run* locally, and two implementation traps in `proxy.ts` /
`app/auth/callback/route.ts` exist only as inline code comments, not as documentation a reviewer would
find without opening those exact files.

## Files created

- `docs/setup/local-development.md` (115 lines, vi) — `npx supabase start`, `.env.local` vs repo-root
  `.env` (Google client id/secret via `env(...)` in `supabase/config.toml`), why
  `NEXT_PUBLIC_SITE_URL` must exactly match `site_url`/`additional_redirect_urls`, the 127.0.0.1-vs-
  localhost cookie trap, running `npm run test:e2e` (19 tests, 3 Playwright projects), and the WSL2
  vendored-Chromium-libs workaround (`.playwright-libs/`, `fs.existsSync` guard in
  `playwright.config.ts`).
- `docs/troubleshooting/login-oauth-gotchas.md` (86 lines, vi) — why `proxy.ts`'s
  `redirectWithSessionCookies` must copy `response.cookies.getAll()` (else single-use refresh tokens
  drop and users get silently logged out one request later — backed by `e2e/authenticated.spec.ts`
  case C8); why `app/auth/callback/route.ts` builds its redirect origin from `NEXT_PUBLIC_SITE_URL`
  and never from `request.nextUrl.origin` (Next 16 rewrites loopback hosts to `"localhost"`) or from
  `Host`/`x-forwarded-host` (open redirect, CWE-644 — backed by `e2e/callback-security.spec.ts`);
  RISK-01 (missing `hero.png`, `#00101A` fallback already wired, drops in with zero code change); A3
  (`skip_nonce_check = true` is Supabase-doc-sourced, never verified against a real Google round-trip).

## Files edited

- `README.md` — added a 7-line "Login (Google OAuth via local Supabase)" section pointing at the two
  new docs and at `docs/features/F001_Login/`. Rest of the boilerplate README left untouched.

## Verification performed

Read before writing, nothing assumed: `proxy.ts`, `app/auth/callback/route.ts`, `app/login/actions.ts`,
`app/login/page.tsx`, `app/todo/{page,actions}.tsx`, `lib/supabase/{server,client,update-session}.ts`,
`lib/i18n/{locales,dictionaries}.ts`, `supabase/config.toml` (auth + google sections), `.env.example`,
`playwright.config.ts`, `package.json` scripts, `.gitignore`, and ran
`npx playwright test --list` (confirmed 19 tests / 6 files / 3 projects as stated in the task). Cross-
checked against `docs/features/F001_Login/technical-spec.md` and `functional-spec.md` to avoid
duplicating what they already state — the new docs link out to them rather than repeat FR/BR content.

## Not touched (out of scope for this invocation)

- `docs/features/F001_Login/*`, `docs/screens/SCR001_Login/spec.md`, `docs/generated/*` — layered
  spec namespace; surgical edits there require `tkm:takumi` Step 6 or `tkm:manage-docs update`, neither
  of which invoked this session. Content was already accurate against source (spot-checked signatures,
  redirect paths, cookie name, FR/BR numbering — no drift found), so no advisory needed.
- `docs/system/*` (architecture.md, permissions.md, overview.md) — forward-authored/reconciled
  exclusively by `takumi`/`rebuild-spec`; not created here even though referenced as `TBD (draft)` in
  `technical-spec.md` § 5.5, since creating them is outside this agent's write authority for this
  invocation.

## Unresolved

- None blocking. If a future session runs a real Google OAuth round-trip and hits a nonce failure,
  `docs/troubleshooting/login-oauth-gotchas.md` § 4 points at the exact config line to revisit.

**Status:** DONE
**Summary:** Added a Vietnamese local-setup guide and an OAuth/proxy troubleshooting page under `docs/`, plus a short pointer section in `README.md`; left the machine-owned spec layer untouched since it was already accurate and this invocation doesn't hold surgical-edit rights there.
**Concerns/Blockers:** None.
