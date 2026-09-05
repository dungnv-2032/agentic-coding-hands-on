---
title: "Homepage SAA 2025 — public landing screen at /"
description: "Phased blueprint for the SAA 2025 homepage: shared header promotion, i18n copy, hero countdown, awards grid, placeholder routes and the e2e-red-first GREEN gate."
status: completed
priority: P1
effort: 12h
branch: feat/language-dropdown-open-state
tags: [homepage, saa2025, nextjs16, i18n, countdown, e2e, momorph]
created: 2026-09-05
completed: 2026-09-05
work_type: feature
spec: docs/features/F002_HomepageSaa/
test_policy: e2e-red-first
momorph:
  fileKey: 9ypp4enmFmdK3YAFJLIu6C
  screenId: i87tDx10uM
---

# Homepage SAA 2025 — Implementation Plan

Decisions: [clarifications.md](./clarifications.md) — authoritative, not re-openable (13 Q/A + ORCH-01..03). Spec draft: [functional](./spec/homepage-saa/functional-spec.md) · [technical](./spec/homepage-saa/technical-spec.md) · [SCR-homepage](./spec/homepage-saa/screens/SCR-homepage/spec.md) · [permissions](./spec/system/permissions.md)
RED gate (valid, exit 1 — not to be re-established): [red-evidence.json](./evidence/red-evidence.json) · [test-contract.md](./evidence/test-contract.md) · Research: [Next.js 16](./reports/researcher-260905-1153-nextjs16-conventions.md) · Design: [homepage-saa.png](./design/homepage-saa.png)

## Phases

| # | Phase | Owner agent | Depends on | Status | Effort |
|---|-------|-------------|------------|--------|--------|
| 01 | [Shared promotion: LanguageSelector, icons, setLocale, signOut](./phase-01-shared-component-and-action-promotion.md) | implementer | — | ✓ completed | 1h |
| 02 | [Track B — i18n copy, awards data, env docs](./phase-02-track-b-i18n-awards-data-and-env.md) | implementer | — | ✓ completed | 1h |
| 03 | [Track A — MoMorph asset export](./phase-03-track-a-momorph-asset-export.md) | momorph-ui-implementer | — | ✓ completed | 1h |
| 04 | [Track A — header shell (nav, bell, account, language)](./phase-04-track-a-header-shell.md) | momorph-ui-implementer | 01, 02, 03 | ✓ completed | 2h |
| 05 | [Track A — hero and countdown](./phase-05-track-a-hero-and-countdown.md) | momorph-ui-implementer | 02, 03 | ✓ completed | 1.5h |
| 06 | [Track A — body sections, footer, page assembly](./phase-06-track-a-body-footer-and-page-assembly.md) | momorph-ui-implementer | 04, 05 | ✓ completed | 3h |
| 07 | [Track B — ComingSoon and 5 placeholder routes](./phase-07-track-b-coming-soon-placeholder-routes.md) | implementer | 06 | ✓ completed | 0.5h |
| 08 | [Tester — event-time pin, GREEN rerun, visual validation](./phase-08-tester-green-rerun-and-visual-validation.md) | tester | 07 | ✓ completed | 2h |

```
01 ─┐
02 ─┼─► 04 ─┐
03 ─┘   05 ─┴─► 06 ──► 07 ──► 08
```

01, 02, 03 have no predecessors and run **concurrently**. 04 and 05 start against the frozen contract below without waiting — transient type errors until 01/02 land are expected and resolve at 06. Track A and Track B share no file; there is no merge barrier after the already-passed RED gate.

## Integration contract (frozen — both tracks code against this)

| Symbol | File (owner) | Signature |
|---|---|---|
| `LanguageSelector` | `app/_components/language-selector.tsx` (01) | `{ locale, labels }` — unchanged behaviour, new path |
| `setLocale` | `app/_actions/locale.ts` (01) | `(locale: string) => Promise<void>`, `revalidatePath("/", "layout")` |
| `signOut` | `app/_actions/auth.ts` (01) | `() => Promise<void>`, redirects `/login` |
| `Dictionary`, `getDictionary` | `lib/i18n/messages/dictionary.ts`, `lib/i18n/dictionaries.ts` (02) | sync, server-read |
| `AWARDS` | `lib/awards.ts` (02) | `readonly { slug, key, image }[]`, design order |
| `HomeHeader` | `app/_components/home-header.tsx` (04) | `{ locale, dictionary, isAuthenticated, isAdmin, signOutAction }` |
| `CountdownTimer` | `app/_components/countdown-timer.tsx` (05) | `{ eventStartAt?: string, labels }` |
| `getPageContext` | `app/_page-context.ts` (06) | `() => Promise<{ locale, dictionary, isAuthenticated, isAdmin }>` |
| `SiteFooter` | `app/_components/site-footer.tsx` (06) | `{ dictionary }` |

Award slugs, frozen: `top-talent`, `top-project`, `top-project-leader`, `best-manager`, `signature-2025-creator`, `mvp`. Dictionary namespaces Track A may use: `header.*`, `home.*`, `comingSoon.*`, `footer.*` (key list in [phase 02](./phase-02-track-b-i18n-awards-data-and-env.md)).
**Never pass the Supabase user object into a Client Component — only `isAuthenticated`/`isAdmin` booleans.**

## File ownership (per file, never by glob under `app/_components/`)

- **01** `app/_components/{language-selector,icons}.tsx`, `app/_actions/{locale,auth}.ts`, `app/login/actions.ts`, `app/login/_components/{login-header,google-sign-in-button}.tsx`, `app/todo/{actions.ts,page.tsx}`
- **02** `lib/i18n/**`, `lib/awards.ts`, `.env.example`
- **03** `public/images/home/**`, `plans/260905-1153-homepage-saa/design/asset-manifest.md`
- **04** `app/_components/{home-header,home-nav,notification-bell,account-menu,use-dismiss-on-outside}.tsx`
- **05** `app/_components/{home-hero,countdown-timer}.tsx`
- **06** `app/page.tsx`, `app/layout.tsx`, `app/_fonts.ts`, `app/_page-context.ts`, `app/globals.css`, `app/_components/{root-further-block,awards-grid,award-card,kudos-promo,floating-widget,site-footer}.tsx`
- **07** `app/_components/coming-soon.tsx`, `app/{awards-information,kudos,standards,profile}/page.tsx`
- **08** `playwright.config.ts`, `e2e/**` (defect repair only), `evidence/green-evidence.json`. Nobody edits `proxy.ts` or `lib/supabase/**` — `/` already falls through (FR-001/BR-001).

## Key risks

- **R1 — the RED suite carries defects no implementation can satisfy** (strict-mode multi-match in ID-7 / ID-15 / ID-25-26; ID-16 reads `repeat(3` out of a *computed* `grid-template-columns`, which resolves to px; ID-41's fake clock `2026-01-01` is now in the past). GREEN is unreachable without tester-owned **mechanism** repair — phase 08 owns the triage rules, weakening any intent is forbidden and escalates. Highest-impact open item.
- **R2 — the shared promotion is the widest blast radius**: `/login` is live and its E2E suite is the only guard. Phase 01 is a pure move plus import rewrite — no behaviour edits, no dropdown retrofit.
- **R3 — locale switch must re-render `/`**: `revalidatePath("/login")` is too narrow; widening to `("/", "layout")` is what makes ID-25/26 possible and is verified there.
- **R4 — event-time pin invariants** (ORCH-01): `0 < target − now < 100 days` (days stay 2 digits) **and** the ID-41 fake clock must sit after `target`; `reuseExistingServer` silently ignores `webServer.env` when a dev server is already up.
- **R5 — RISK-02, 35 `MM_MEDIA_*` nodes unverified for export**: phase 03 isolates it; a missing asset falls back to recorded geometry over a flat design colour, so dropping the file in later costs zero code edits.
- **R6 — the frame reads "Comming soon"** (design typo). FR-202 and tests ID-13/41 say `Coming soon`; ship the corrected spelling.
