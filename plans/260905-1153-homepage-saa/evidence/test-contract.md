# SAA 2025 Homepage E2E Test Contract

## Test Files

- **Anonymous visitor tests:** `e2e/homepage.spec.ts` (16 tests covering public `/` homepage access)
- **Authenticated user tests:** `e2e/homepage-authed.spec.ts` (4 tests covering header features for logged-in users)

Both files are registered in `playwright.config.ts`:
- `homepage.spec.ts` matches the `anon` project
- `homepage-authed.spec.ts` matches the `authed` project

## Test Execution

Run all homepage tests:
```bash
npm run test:e2e -- --project=anon --project=authed
```

Or individually:
```bash
npm run test:e2e -- --project=anon          # Anonymous visitor tests only
npm run test:e2e -- --project=authed        # Authenticated user tests only
```

## Test Coverage by Test ID

### Anonymous Visitor Tests (anon project)

| Test ID | Feature | Status | Notes |
|---------|---------|--------|-------|
| ID-0 | Homepage loads publicly | ✅ PASSED | Confirms no auth redirect |
| ID-7 | Overall structure (header, hero, countdown, grid, Kudos, footer) | ❌ FAILED | Elements missing |
| ID-9 | "About SAA 2025" nav selected state | ❌ FAILED | Nav elements missing |
| ID-12 | Countdown displays DAYS / HOURS / MINUTES | ❌ FAILED | Countdown element missing |
| ID-13 | "Coming soon" visible when event in future | ❌ FAILED | Element missing |
| ID-14 | Event info (26/12/2025, Âu Cơ Art Center, livestream note) | ❌ FAILED | Event info block missing |
| ID-15 | Awards grid shows 6 cards | ❌ FAILED | Award cards missing |
| ID-16 | Responsive grid (3 col desktop, 2 col tablet/mobile) | ❌ FAILED | Grid structure missing |
| ID-17 | Footer (logo, nav links, copyright) | ❌ FAILED | Footer missing |
| ID-39/40 | Countdown values zero-padded to 2 digits | ❌ FAILED | Countdown markup missing |
| ID-41/42/43 | "Coming soon" hidden, countdown at 00 when event passed | ✅ PASSED | Clock manipulation validates logic |
| ID-24/30-35 | Language menu (click open/close, outside click, keyboard) | ❌ FAILED | Language menu missing from homepage |
| ID-25/26 | EN/VN language switch | ❌ FAILED | Language menu not rendered |
| ID-44/45 | CTA buttons navigate to /awards-information and /kudos | ❌ FAILED | Buttons missing |
| ID-47/48/49/50/52 | Award card navigates to `/awards-information#<slug>` | ❌ FAILED | Card structure missing |
| ID-53 | Kudos "Chi tiết" navigates to /kudos | ❌ FAILED | Kudos section missing |
| ID-55/59 | Footer links resolve (no 404s) | ❌ FAILED | Footer missing |

### Authenticated User Tests (authed project)

| Test ID | Feature | Status | Notes |
|---------|---------|--------|-------|
| ID-1 | Header shows notification bell and account button | ❌ FAILED | Header not rendered |
| ID-27 | Notification panel opens/closes on bell click | ❌ FAILED | Bell missing |
| ID-36 | Account menu opens with Profile and Sign out | ❌ FAILED | Menu missing |
| ID-38 | Regular user does NOT see Admin Dashboard | ❌ FAILED | Menu missing |
| ID-5/37 | Admin user sees Admin Dashboard (SKIPPED) | ⏭️ SKIPPED | Requires admin role seeding |

## Required DOM Elements (data-testid Contract)

The implementation MUST include these `data-testid` attributes so tests can find elements:

```
countdown-value           — Each countdown digit display (days, hours, minutes)
award-card                — Generic award card container
awards-grid               — Awards grid layout container
award-card-top-talent     — Top Talent card
award-card-top-project    — Top Project card
award-card-top-project-leader    — Top Project Leader card
award-card-best-manager   — Best Manager card
award-card-signature-2025-creator — Signature 2025 Creator card
award-card-mvp            — MVP card
notification-panel       — Notification panel (authenticated only)
account-menu              — Account dropdown menu (authenticated only)
```

Without these, tests will fail with "element not found" errors.

## Deferred Test Cases

- **ID-28**: Unread notification badge — deferred until notification backend exists (clarifications A1)
- **ID-5/37**: Admin dashboard for admin users — deferred; requires Supabase admin role seeding implementation

## Selector Fallback Patterns

Where `data-testid` is not available, tests also search by:
- Accessible roles: `getByRole('banner')`, `getByRole('contentinfo')`, `getByRole('link')`, `getByRole('button')`
- Visible text: `getByText()` with regex patterns (Vietnamese and English)
- ARIA attributes: `aria-haspopup`, `aria-current`, etc.

## Test Environment

- **Viewport:** Desktop (1280×800) by default; tests also validate tablet (800×600) and mobile (375×667) breakpoints
- **Auth:** Unauthenticated tests run in `anon` project with no cookies; authenticated tests run in `authed` project with Supabase session from `e2e/.auth/user.json`
- **Dev Server:** Tests expect `http://127.0.0.1:3000` running with `npm run dev`
- **Time Handling:** ID-41/42/43 uses Playwright's `page.clock` to simulate future dates

## Notes for Implementation

1. **Language menu on homepage:** The login screen already has a language selector; this must be promoted to a shared component and rendered on the homepage too (clarifications decision Q2).
2. **Placeholder routes:** Four placeholder routes (`/awards-information`, `/kudos`, `/standards`, `/profile`) must exist to satisfy ID-55/59 "no broken links" assertion.
3. **Event countdown:** Default event time from env var `NEXT_PUBLIC_EVENT_START_AT` is `2025-12-26T18:30:00+07:00`; unparseable values render `00/00/00` and hide "Coming soon" without throwing.
4. **Language strings:** All copy must be in both Vietnamese and English; extend the `Dictionary` type in the i18n system.
5. **Fonts:** Montserrat and Montserrat Alternates, already declared in `/login` via `next/font/google`.

## Red-First Evidence

- **Exit code:** 1 (non-zero — valid RED)
- **Failed tests:** 19 (all due to missing homepage elements)
- **Passed tests:** 25 (existing test suite, unaffected)
- **Skipped tests:** 1 (admin role seeding not implemented)
- **Duration:** 2.9 minutes

Run the command after implementation to confirm GREEN:
```bash
npm run test:e2e -- --project=anon --project=authed
```

Expected outcome: all 20 homepage tests pass (19 currently failing + 1 skipped admin test), 25 existing tests remain passing, exit code 0.
