---
title: "Login screen (SAA 2025) — Google OAuth on local Supabase"
description: "Phased blueprint for /login with Google OAuth, route guard, cookie i18n and an e2e-red-first Playwright gate."
status: complete
priority: P1
effort: 11h
branch: main
tags: [auth, supabase, oauth, nextjs16, e2e, momorph]
created: 2026-09-04
completed: 2026-09-04
spec: docs/features/F001_Login/
test_policy: e2e-red-first
momorph:
  fileKey: 9ypp4enmFmdK3YAFJLIu6C
  screenId: GzbNeVGJHz
---

# Login (SAA 2025) — Implementation Plan

Decision record: [clarifications.md](./clarifications.md) — authoritative, not re-openable.
Spec: [functional](./spec/login/functional-spec.md) · [technical](./spec/login/technical-spec.md) · [SCR-login](./spec/login/screens/SCR-login/spec.md)
Research: [Next 16](./research/researcher-01-nextjs16-conventions.md) · [Supabase OAuth](./research/researcher-02-supabase-google-oauth.md) · [design notes](./design/design-notes.md)

## Phases

| # | Phase | Owner agent | Depends on | Status | Effort |
|---|-------|-------------|------------|--------|--------|
| 01 | [Test harness + Supabase/env foundation](./phase-01-test-harness-and-supabase-google-config.md) | implementer | — | complete | 1.5h |
| 02 | [RED E2E gate](./phase-02-red-e2e-login-suite.md) | tester | 01 | complete | 2.5h |
| 03 | [Track B — i18n, Server Actions, OAuth callback](./phase-03-track-b-i18n-actions-oauth-callback.md) | implementer | 02 | complete | 2h |
| 04 | [Track A — /login screen UI](./phase-04-track-a-login-screen-ui.md) | momorph-ui-implementer | 02 | complete | 3h |
| 05 | [Track B — proxy route guard, /todo, sign-out](./phase-05-track-b-proxy-guard-todo-signout.md) | implementer | 03 | complete | 1.5h |
| 06 | [Integration, GREEN rerun, visual validation](./phase-06-integration-green-and-visual-validation.md) | tester | 04, 05 | complete | 1.5h |

```
01 ──► 02 ──┬──► 04 (Track A) ──────────────┐
            └──► 03 ──► 05 (Track B) ───────┴──► 06
```

Phases 03/05 and phase 04 run **concurrently** after the shared gate (02). No merge barrier between the
tracks — file ownership is disjoint and the integration contract below is frozen up front.

## Integration contract (frozen — both tracks code against this)

| Symbol | File (owner) | Signature |
|---|---|---|
| `Locale`, `LOCALES`, `DEFAULT_LOCALE`, `resolveLocale(v?: string): Locale` | `lib/i18n/locales.ts` (03) | pure, no I/O |
| `getDictionary(locale: Locale): Dictionary` | `lib/i18n/dictionaries.ts` (03) | sync, `server-only` |
| `signInWithGoogle(): Promise<void>` | `app/login/actions.ts` (03) | Server Action, redirects |
| `setLocale(locale: string): Promise<void>` | `app/login/actions.ts` (03) | Server Action, writes `NEXT_LOCALE` |
| `signOut(): Promise<void>` | `app/todo/actions.ts` (05) | Server Action, redirects `/login` |

Dictionary keys Track A may use: `login.logoAlt`, `login.wordmarkAlt`, `login.subtitle`, `login.tagline`,
`login.signInButton`, `login.errorOauthFailed`, `login.languageLabel`, `login.languageVi`,
`login.languageEn`, `footer.copyright`, `todo.title`, `todo.signOut`.

## File ownership (no two parallel phases share a file)

- **01** `package.json`, `package-lock.json`, `playwright.config.ts`, `.gitignore`, `.env.example`, `supabase/config.toml`, `e2e/smoke.spec.ts`
- **02** `e2e/**` (takes over `playwright.config.ts` from 01), `evidence/red-evidence.md`
- **03** `lib/i18n/**`, `app/login/actions.ts`, `app/auth/callback/route.ts`
- **04** `app/login/page.tsx`, `app/login/_components/**`, `app/globals.css`, `public/images/login/**`
- **05** `proxy.ts`, `app/todo/page.tsx`, `app/todo/actions.ts`
- **06** read-only over app code; may edit `e2e/**` only to fix a harness defect, never to weaken an assertion

## Key dependencies & risks

- `@playwright/test` + a browser that actually launches on WSL2 — proven GREEN in 01 so any RED in 02 is the app's fault, never the harness (validity condition of `e2e-red-first`).
- Google Cloud credentials do not exist; per Assumption A1 the suite intercepts the authorize navigation instead of following it, so no phase depends on a real Google round-trip.
- **Highest risk:** dropping rotated auth cookies on the proxy redirect (phase 05, step 3) — single-use refresh tokens mean a silent logout one request later. Own step, own E2E case.
- **RISK-01 open:** `public/images/login/hero.png` is not exportable yet. Phase 04 ships the recorded geometry over a dark-navy fallback; dropping the file in later is a zero-code-change action.
