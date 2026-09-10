---
phase: 06
title: "Integration — /kudos/secret-box page.tsx"
status: complete
owner: implementer
track: integration
test_policy: e2e-red-first
effort: 0.5h
depends_on: [04, 05]
---

# Phase 06 — Integration: `app/kudos/secret-box/page.tsx`

## Context Links

- [technical-spec](spec/open-secret-box/technical-spec.md) § 3.1 — the four resolution steps
- [functional-spec](spec/open-secret-box/functional-spec.md) FR-001, FR-105, FR-202, BR-006
- [plan.md](plan.md) DEC-02 — no header/footer, `<h1>` inside `<main>`
- [phase-04](phase-04-presentational-components.md) (component props) ·
  [phase-05](phase-05-server-action-and-queries.md) (action + query)
- Composition precedent: `app/profile/page.tsx` (Server Action passed as a prop), `app/standards/page.tsx`

## Overview

- **Priority:** P1 — the seam where both tracks meet.
- **Status:** pending
- Replace the `ComingSoon` placeholder with the real Server Component: resolve the viewer, read the
  count, decide `canOpen` / `showSignIn`, and compose phase 04's components with phase 05's action.
  One file, half an hour, no new logic invented here.

## Key Insights

- **The route stays public and must keep returning `200`** (FR-001, BR-006, K-21). No `redirect()`,
  no `notFound()`, no proxy change — entitlement is decided inside the screen.
- Three inputs, three outputs: `resolveViewer()` → `sunnerId === null` gives
  `unopenedCount = 0, canOpen = false, showSignIn = !isAuthenticated`; otherwise
  `fetchUnopenedCount()` and `canOpen = unopenedCount > 0`. A signed-in session with no roster row
  therefore looks inert **without** a sign-in link, exactly as clarifications resolved.
- `getPageContext()` supplies locale + dictionary the way every shipped screen does; only
  `dictionary.secretBox` is passed down.
- The Server Action travels **as a prop** (F004's idiom): no Track A file imports it directly, so
  the component tree stays testable and the boundary stays one-way.
- `metadata.title` stays a real title; the existing placeholder metadata line is kept and its
  wording checked against the screen (K-21's *title* text is phase 07's edit, not this file's).

## Requirements

Functional:
- `GET /kudos/secret-box` → `200` for everyone, `<main>` present, the panel's `<h1>` inside it.
- Anonymous: counter `00`, no instruction line, opener inert, sign-in link visible.
- Signed in without a `sunners` row: same, minus the sign-in link.
- Signed in with `n > 0`: counter `formatBoxCount(n)`, instruction visible, opener operable.
- The close control and the box control are rendered into the panel's slots.

Non-functional: Server Component (no `"use client"`), under 200 lines (it will be ~60), no Supabase
row and no `User` object crossing into a component, `npm run typecheck` and `npm run lint` exit 0.

## Architecture

```
SecretBoxPage (async Server Component)
├─ createClient()  →  resolveViewer(supabase)          [auth-only identity]
├─ getPageContext()                                    [locale + dictionary]
├─ sunnerId === null ? 0 : await fetchUnopenedCount(supabase, sunnerId)
├─ canOpen    = unopenedCount > 0 && sunnerId !== null
├─ showSignIn = !viewer.isAuthenticated
└─ <main>
     <SecretBoxPanel copy unopenedCount canOpen showSignIn
        closeSlot={<SecretBoxDismiss copy/>}
        boxSlot={<SecretBoxOpener canOpen copy openAction={openSecretBox}/>} />
   </main>
```

## Related Code Files

Modify: `app/kudos/secret-box/page.tsx` (sole owned file — the whole body is replaced).

Read for context: `app/profile/page.tsx`, `app/_page-context.ts`, `lib/kudos/viewer.ts`,
`lib/secret-box/queries.ts`, `app/kudos/secret-box/_components/*`.

Create / Delete: none. Not modified: `proxy.ts`, `app/_components/coming-soon.tsx` (still used by
`/kudos/[id]`), anything under `_components/` or `_actions/`.

## Implementation Steps

1. Replace the body: imports, `getPageContext()` + `createClient()`/`resolveViewer()` in a
   `Promise.all`, then the count read (it depends on `sunnerId`, so it cannot join that `Promise.all`).
2. Compute `canOpen` and `showSignIn` once, here. No component re-derives them.
3. Render `<main>` wrapping the panel, centering the card on the full-height `#00101A` page (DEC-02).
4. Pass `openSecretBox` as a prop.
5. Rewrite the docblock: the current one calls the route a declared placeholder. State the frame,
   the public-route contract and where entitlement is enforced.
6. `npm run typecheck && npm run lint`, then run both fixed commands locally for signal.

## Todo List

- [x] `ComingSoon` import removed; page is an async Server Component
- [x] Viewer resolved with `resolveViewer()`; no `resolveSidebarSunnerId()`
- [x] `canOpen` / `showSignIn` computed once, in this file
- [x] Action passed as a prop, not imported by any component
- [x] `<main>` wraps the panel and contains the `<h1>`
- [x] Placeholder docblock replaced
- [x] typecheck + lint exit 0

## Success Criteria

- `curl -o /dev/null -w "%{http_code}" http://127.0.0.1:3000/kudos/secret-box` → `200` signed out.
- Both suites from phase 01 pass locally (official verdict is phase 07).
- `grep -n "ComingSoon" app/kudos/secret-box/page.tsx` → no match, while `/kudos/[id]` still uses it.
- `git diff --name-only` lists exactly one file.

## Risk Assessment

| Risk | L×I | Countermeasure |
|------|-----|----------------|
| A guard (`redirect`/`notFound`) added for anonymous visitors → K-21 and FR-001 break | M×**H** | BR-006 restated in Requirements; SB-A1 asserts the anonymous `200` |
| `<h1>` left outside `<main>` while copying the `/standards` shape | M×**H** | DEC-02; SB-A1 asserts `main h1` |
| The count read joined into `Promise.all` with `resolveViewer()` → reads `undefined` sunnerId | M×M | Step 1 states the dependency explicitly, as `app/profile/page.tsx` documents for itself |
| Signed-in-without-roster-row treated as anonymous → a pointless sign-in link | M×L | Two separate booleans; SB and the clarifications distinguish the cases |
| Track A/B seam mismatch (prop names drift) surfaces only here | M×M | Phase 02 froze the shared types; prop names are listed in phase 04's Architecture block |
| Page grows the composition of a header/footer "for consistency" | L×M | DEC-02 — the frame draws neither |

## Security Considerations

- `resolveViewer()`'s `userId` never leaves this file, and no Supabase `User` object crosses into a
  component — `app/_page-context.ts`'s boundary held.
- The public route now renders per-session data. Only the viewer's **own** count is read, keyed by
  `resolveViewer()`'s `sunnerId`; there is no `?id=` and nothing user-supplied enters the query.
- Anonymous rendering must not leak a seeded Sunner's counters — the `sunnerId === null` branch
  returns a literal `0` and reads nothing.

## Next Steps

- Unblocks phase 07 (GREEN + visual + adapted assertions).
- Rollback: restoring the `ComingSoon` body reverts the whole feature's user-visible surface in one
  file, which is the cheapest kill switch if the screen must be pulled after release. Phases 04/05
  then become dead code to remove in a follow-up, and phase 07's two adapted assertions must be
  reverted with it.
