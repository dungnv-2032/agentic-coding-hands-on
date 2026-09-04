---
test_policy: e2e-red-first
owner: momorph-ui-implementer
fileKey: 9ypp4enmFmdK3YAFJLIu6C
screenId: GzbNeVGJHz
depends_on: [phase-02]
---
# Phase 04 — Track A: /login screen UI
## MoMorph refs:
- Login: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/GzbNeVGJHz
- Clarifications: plans/260904-1714-login-page-supabase-google-oauth/clarifications.md
- testPolicy: e2e-red-first

**Goal:** render SCR-login faithfully — header, hero, ROOT FURTHER block, Google button, footer — per [SCR-login spec](./spec/login/screens/SCR-login/spec.md), [design-notes.md](./design/design-notes.md), `design/specs.csv`, `design/test-cases.csv`.

**Owns (only):** `app/login/page.tsx`, `app/login/_components/**`, `app/globals.css`, `public/images/login/**`.
**Out of scope:** `app/login/actions.ts`, `lib/i18n/**`, `app/auth/callback/route.ts` (phase 03); `proxy.ts`, `app/todo/**` (phase 05); `e2e/**` (tester). Do not create, edit or stub them.
**Integration contract** (frozen in [plan.md](./plan.md)): import `signInWithGoogle`/`setLocale` from `app/login/actions.ts` and `getDictionary`/`resolveLocale` from `lib/i18n/*`; read `NEXT_LOCALE` via `await cookies()` and `error` via `PageProps<'/login'>`. Use only the dictionary keys plan.md lists.

**Must hold:**
- `next/image` `preload`, never the deprecated `priority`; string-path images need explicit size (logo 52×48, wordmark 451×200).
- Hero (RISK-01/ORCH-05): full-bleed layer referencing `/images/login/hero.png` with the recorded geometry — 1441×1022 at top 2px/left 0, `background-position:-440px -217.975px`, `background-size:159.763% 133.371%`, `no-repeat` — over a solid dark-navy fallback. No gradient imitation; dropping the real file in later must require zero code edits.
- Google icon sits RIGHT of the label; "ROOT FURTHER" is an image, not a webfont; logo and footer non-interactive; button left-aligned with the description column.
- Button disabled + loader on submit (SM-001) and shadow on hover; error banner with `aria-live` above the button when `?error` is present (DEC-001); selector defaults to VN (flag left, chevron right) and is keyboard-operable.
- Keep the accessible names the RED suite locates by: button "LOGIN With Google", image alts, `contentinfo` footer.

**Done:** phase 02 cases C1–C5 pass at phase 06 (FR-201, FR-202, FR-203, FR-402); `npm run lint` and `npx tsc --noEmit` clean; every file under 200 lines.
**Rollback:** delete `app/login/page.tsx` and `app/login/_components/`, `git checkout -- app/globals.css`.
