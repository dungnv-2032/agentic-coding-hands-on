---
feature: F002
owner: implementer
depends_on: [phase-06]
status: completed
effort: 0.5h
completed: 2026-09-05
---

# Phase 07 — Track B: ComingSoon shell and the five placeholder routes

## Context Links

- Plan + frozen contract: [plan.md](./plan.md) · Decisions: [clarifications.md](./clarifications.md) ("Screen scope", assumption A3)
- Spec: A3 in [technical-spec.md](./spec/homepage-saa/technical-spec.md); FR-002; [permissions.md § 2](./spec/system/permissions.md)
- Test contract: ID-55/59 ("no broken links"), ID-44/45, ID-53, ID-36 (Profile link target)

## Overview

- **Priority:** P2 · **Owner agent:** `implementer` · **Status:** pending · **Effort:** 0.5h
- **Depends on:** 06 (imports `getPageContext`, `HomeHeader`, `SiteFooter`). **Blocks:** 08.
- Five routes so that every link the homepage renders has a real destination (ORCH-11: `/admin` was added
  after the plan). They are declared placeholders, not stand-ins: no homepage assertion runs against them (assumption A3).

## Key Insights

- Reusing the real header and footer is the point — a bare static page would break the navigation
  experience and would not prove the header renders outside `/`.
- `/profile` is linked from the account menu and is therefore only reachable by an authenticated user
  today, but the route itself stays public: there is no protected content behind it yet, and
  `proxy.ts` guards exactly `/todo` and `/login` (BR-001). Adding a guard here is out of scope.
- Admin Dashboard points at `/admin` (SCR-homepage E10). A placeholder `/admin` route was added (ORCH-11)
  so no 404 occurs when an admin clicks it; a real implementation must check the role server-side (FR-601).
- One component, four one-line pages. Anything more is speculative (YAGNI).

## Requirements

- FR-002 — `/awards-information`, `/kudos`, `/standards`, `/profile`, `/admin` all render with the real header
  and footer and return a non-4xx status.
- Copy comes from `dictionary.comingSoon` (phase 02), in both locales.
- Non-functional: each file well under 200 lines; no route guard, no new dependency.

## Architecture

```
app/awards-information/page.tsx ─┐
app/kudos/page.tsx               │
app/standards/page.tsx           ├─► <ComingSoon />  ─► getPageContext() ─► <HomeHeader …/> <main>{copy}</main> <SiteFooter/>
app/profile/page.tsx             │
app/admin/page.tsx              ─┘
```

## Related Code Files

**Create:** `app/_components/coming-soon.tsx`, `app/awards-information/page.tsx`,
`app/kudos/page.tsx`, `app/standards/page.tsx`, `app/profile/page.tsx`, `app/admin/page.tsx`
**Modify:** none
**Not owned:** `app/page.tsx`, `app/_page-context.ts`, `app/_components/{home-header,site-footer}.tsx`
(06 — import only), `lib/i18n/**` (02), `e2e/**` (08).

## Implementation Steps

1. `app/_components/coming-soon.tsx` — async Server Component; call `getPageContext()`, render
   `HomeHeader` (passing `locale`, `dictionary`, `isAuthenticated`, `isAdmin`, `signOut`), a `<main>`
   with `dictionary.comingSoon.title` / `.body`, and `SiteFooter`. Apply the same font variable
   wrapper `app/page.tsx` uses so the placeholder is not rendered in the fallback system font.
2. Each of the five `page.tsx` files: `export default function Page() { return <ComingSoon />; }`
   plus a `metadata` export carrying the destination's name. No `searchParams`, no `params`.
3. Confirm the anchor case: `/awards-information#top-talent` must not 404 or scroll-error when the
   fragment has no matching element — a fragment with no target is a no-op in the browser, so nothing
   special is needed; do not invent anchor stubs.
4. `npm run lint && npm run typecheck` clean; `npm run build` succeeds with five new static routes.

## Todo List

- [x] `ComingSoon` renders the real header and footer, not a copy
- [x] Five routes created, each a one-liner delegating to `ComingSoon` (ORCH-11: /admin added)
- [x] Copy read from `dictionary.comingSoon`, both locales
- [x] No guard added, `proxy.ts` untouched
- [x] lint + typecheck + build clean

## Success Criteria

- `curl -o /dev/null -w "%{http_code}" http://127.0.0.1:3000/{awards-information,kudos,standards,profile,admin}`
  returns `200` for all five.
- ID-55/59 walks every footer link without a 4xx; ID-44/45 and ID-53 land on real pages.

## Risk Assessment

| ID | Risk | Likelihood | Impact | Countermeasure |
|----|------|-----------|--------|----------------|
| R7-1 | Placeholders drift into pretend implementations of the real screens | Low | Medium | Copy is a single "coming soon" message; no section of the target screen is mocked (A3) |
| R7-2 | A future guard on `/profile` is assumed to exist because the link is role-gated | Medium | Medium | Stated in this phase and in FR-601: hiding the link is not access control |
| R7-3 | Header/footer imports pull client-only code into four more routes, slowing them | Low | Low | Same components as `/`; the interactive parts are already leaf Client Components |

## Security Considerations

- These routes are public by design ([permissions.md § 2](./spec/system/permissions.md)) and hold no
  data. Nothing user-specific is rendered beyond the header's authenticated/admin booleans.
- No `searchParams` is read, so there is no reflected-input surface on any of the four.

## Rollback

Delete the six created files (coming-soon + five routes). The homepage still renders; only ID-55/59 regresses.

## Next Steps

Phase 08 runs the GREEN rerun across `/` and these five routes.
