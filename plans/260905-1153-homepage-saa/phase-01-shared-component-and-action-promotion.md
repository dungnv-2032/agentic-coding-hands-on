---
feature: F002
owner: implementer
depends_on: []
status: completed
effort: 1h
completed: 2026-09-05
---

# Phase 01 — Shared promotion: LanguageSelector, icons, setLocale, signOut

## Context Links

- Plan + frozen contract: [plan.md](./plan.md) · Decisions: [clarifications.md](./clarifications.md) ("Promote to shared", "Account menu")
- Spec: § 4.1 Components in [technical-spec.md](./spec/homepage-saa/technical-spec.md); FR-201, FR-404
- Regression guard: `e2e/login-screen.spec.ts`, `e2e/authenticated.spec.ts`, `e2e/route-guard.spec.ts` (currently green — 25 passing tests in [red-evidence.json](./evidence/red-evidence.json))

## Overview

- **Priority:** P1 · **Owner agent:** `implementer` · **Status:** pending · **Effort:** 1h
- **Depends on:** nothing. **Runs concurrently with:** 02, 03. **Blocks:** nothing hard — 04 codes against the frozen import paths.
- Highest-risk step in the plan and therefore first: `/login` is live code, and this phase moves three
  of its parts out from under it so `/` can reuse them (DRY, clarifications "Promote to shared").

## Key Insights

- **Pure move.** Not one line of behaviour changes. The only edits are the import paths and the one
  `revalidatePath` argument named below. Anything else is scope creep with a live screen on the line.
- `setLocale`'s `revalidatePath("/login")` is why the homepage would keep serving pre-switch copy after
  a language change. Widening to `revalidatePath("/", "layout")` invalidates the whole layout subtree,
  which is what E2E ID-25/26 asserts on `/`.
- `signOut` currently lives in `app/todo/actions.ts` and is imported by `app/todo/page.tsx`; the
  homepage account menu (FR-404) needs the same action, so it moves to `app/_actions/auth.ts`.
- `app/_components/` and `app/_actions/` are underscore-prefixed private folders — App Router does not
  route them. No new URL appears from this move.
- `icons.tsx` carries `IconGoogle`, used only by `google-sign-in-button.tsx`. It moves with the file
  because the flag/chevron icons in the same module are what the shared selector needs; splitting the
  module would be a second refactor for no gain (YAGNI).

## Requirements

- FR-201 — the homepage header reuses the `/login` language selector rather than duplicating it.
- FR-404 — the account menu's Sign out reuses the existing sign-out action.
- Non-functional: `/login` and `/todo` behave exactly as before; every file stays under 200 lines;
  kebab-case names preserved.

## Architecture

```
before                                   after
app/login/_components/language-selector  app/_components/language-selector.tsx
app/login/_components/icons.tsx          app/_components/icons.tsx
app/login/actions.ts :: setLocale        app/_actions/locale.ts :: setLocale   (revalidatePath "/" layout)
app/todo/actions.ts  :: signOut          app/_actions/auth.ts   :: signOut
app/login/actions.ts :: signInWithGoogle  (stays — /login-only, not shared)
```

## Related Code Files

**Create:** `app/_components/language-selector.tsx`, `app/_components/icons.tsx`,
`app/_actions/locale.ts`, `app/_actions/auth.ts`
**Modify:** `app/login/actions.ts` (drop `setLocale` + its now-unused imports),
`app/login/_components/login-header.tsx` (import path), `app/login/_components/google-sign-in-button.tsx`
(import path), `app/todo/actions.ts` (re-export removed — see step 5), `app/todo/page.tsx` (import path)
**Delete:** `app/login/_components/language-selector.tsx`, `app/login/_components/icons.tsx`,
`app/todo/actions.ts` (once empty)
**Not owned:** `lib/i18n/**` (02), every `app/_components/*` file the plan assigns to 04/05/06, `e2e/**` (08).

## Implementation Steps

1. `git mv app/login/_components/icons.tsx app/_components/icons.tsx` — content untouched.
2. `git mv app/login/_components/language-selector.tsx app/_components/language-selector.tsx`; fix its
   two imports: `./icons` stays relative (same folder now), `../actions` becomes `@/app/_actions/locale`.
3. Create `app/_actions/locale.ts` (`"use server"`) holding `setLocale` verbatim from
   `app/login/actions.ts`, with the single change `revalidatePath("/login")` → `revalidatePath("/", "layout")`
   and a comment saying why (both `/` and `/login` render locale-dependent copy).
4. Delete `setLocale` from `app/login/actions.ts`; drop `cookies`, `revalidatePath`, `LOCALE_COOKIE`,
   `resolveLocale` imports if nothing else uses them. `signInWithGoogle` stays put.
5. Create `app/_actions/auth.ts` (`"use server"`) holding `signOut` verbatim; delete
   `app/todo/actions.ts`; point `app/todo/page.tsx` at `@/app/_actions/auth`.
6. Update `app/login/_components/login-header.tsx` → `@/app/_components/language-selector`, and
   `google-sign-in-button.tsx` → `@/app/_components/icons`.
7. `npm run lint && npm run typecheck` clean, then `npm run test:e2e -- --project=anon --project=authed`
   and confirm the 25 previously-passing tests are still passing (homepage failures stay failing —
   that is phase 04-07 work, not a regression).

## Todo List

- [x] `icons.tsx` and `language-selector.tsx` moved with `git mv`, content unchanged
- [x] `setLocale` in `app/_actions/locale.ts`, `revalidatePath("/", "layout")`
- [x] `signOut` in `app/_actions/auth.ts`; `app/todo/actions.ts` removed
- [x] Four importers updated; no import of `app/login/_components/{icons,language-selector}` remains
- [x] lint + typecheck clean; login/todo/route-guard/callback-security E2E still green

## Success Criteria

- `grep -rn "login/_components/\(icons\|language-selector\)" app` returns nothing.
- The 25 tests green before this phase are green after it; the homepage tests are unchanged in count.
- Manual: `/login` language switch still flips copy and writes `NEXT_LOCALE`; `/todo` sign-out still
  lands on `/login`.

## Risk Assessment

| ID | Risk | Likelihood | Impact | Countermeasure |
|----|------|-----------|--------|----------------|
| R1-1 | A missed importer leaves `/login` failing to compile | Medium | High | Step 7 grep + typecheck; the login E2E suite is the gate |
| R1-2 | `revalidatePath("/", "layout")` over-invalidates and masks a caching bug elsewhere | Low | Low | Scope is two static pages; accepted deliberately over a second narrow call (DRY) |
| R1-3 | Temptation to "improve" the dropdown while moving it (shared dismiss hook, a11y tweaks) | Medium | High | Explicitly out of scope: 04 writes its own `use-dismiss-on-outside.ts` and does not touch this file |
| R1-4 | `signOut` removal breaks `/todo` while `/` does not exist yet | Low | Medium | Same-phase import update + `authenticated.spec.ts` sign-out case |

## Security Considerations

- Both moved actions keep `"use server"` at the top of their new files — losing that directive would
  turn them into client-bundled functions.
- `setLocale` keeps validating through `resolveLocale` before writing the cookie; raw input never
  reaches `cookies().set`.
- `signOut` keeps its no-try/catch shape: `redirect()` throws `NEXT_REDIRECT` internally and must not
  be swallowed, and an already-expired session must still land on `/login`.

## Rollback

`git revert` the phase commit. Nothing else in the tree references the new paths until 04 lands, so the
revert is self-contained.

## Next Steps

Phase 04 imports `@/app/_components/language-selector`; phase 04's account menu imports
`@/app/_actions/auth`. Both paths are frozen in [plan.md](./plan.md).
