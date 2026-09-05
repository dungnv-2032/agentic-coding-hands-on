---
feature: F002 · test_policy: e2e-red-first · owner: momorph-ui-implementer
fileKey: 9ypp4enmFmdK3YAFJLIu6C · screenId: i87tDx10uM · depends_on: [01, 02, 03] · status: completed · effort: 2h
completed: 2026-09-05
---
# Phase 04 — Track A: header shell (nav, notification bell, account menu, language)
## MoMorph refs:
- Homepage SAA: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/i87tDx10uM
- Clarifications: plans/260905-1153-homepage-saa/clarifications.md
- testPolicy: e2e-red-first

**Goal:** render R1 of [SCR-homepage](./spec/homepage-saa/screens/SCR-homepage/spec.md) — sticky header with logo, three nav items, notification bell + empty panel and account menu (authenticated only), promoted language selector. Delivers FR-201, FR-102/DEC-001, FR-403, FR-404, FR-601/DEC-002, BR-002.

**Owns (only):** `app/_components/{home-header,home-nav,notification-bell,account-menu}.tsx`, `app/_components/use-dismiss-on-outside.ts`.
**Out of scope:** `app/_components/{language-selector,icons}.tsx` (01 — import, never edit), `app/page.tsx` (06), `lib/i18n/**` (02), `public/images/home/**` (03), `e2e/**` (08).
**Contract:** `HomeHeader({ locale, dictionary, isAuthenticated, isAdmin, signOutAction })`; import `LanguageSelector` from `@/app/_components/language-selector`, `signOut` from `@/app/_actions/auth`.

**Must hold (the RED suite locates by these):**
- Header is the `banner` landmark. Bell and account button are **absent from the DOM** when `isAuthenticated` is false (BR-002), not hidden by CSS.
- One match each on accessible name: bell `/notification|bell|thông báo/i`, account trigger `/account|profile|tài khoản|hồ sơ/i` — and neither may match the other's regex.
- `aria-haspopup="listbox"` stays unique to the language selector (bell/account use `menu`), or ID-24/30-35 grabs the wrong trigger.
- `data-testid="notification-panel"` and `data-testid="account-menu"`, both conditionally rendered; panel copy is `dictionary.header.notificationsEmpty`, no badge (ID-28 deferred).
- Account menu holds Profile as a **link** to `/profile`, Sign out as a **button** inside `<form action={signOutAction}>`, Admin Dashboard link only when `isAdmin`. The Profile label must carry no admin/dashboard wording — ID-38 asserts its absence.
- Nav: `About SAA 2025` carries `aria-current="page"` and on click prevents default + smooth-scrolls to top (DEC-001); `Award Information` → `/awards-information`; `Sun* Kudos` → `/kudos`.
- Bell and account share `use-dismiss-on-outside.ts` (outside click + Escape). Do **not** retrofit `language-selector.tsx` onto it — that file is frozen this phase.
- Every visual value (heights, spacing, colours, icon sizes, sticky offset) from MoMorph; `next/image` with `preload`, never the deprecated `priority`.

**Done:** typecheck + lint clean, each file under 200 lines, ID-1/27/36/38 pass at phase 08.
**Rollback:** delete the five files; nothing imports them until 06.
