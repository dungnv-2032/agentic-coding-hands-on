# Phase 06 — Route guard + `?id=` resolver

**Track:** B (runs concurrently with 03–05 and with Track A) · **Owner:** `implementer` · **Effort:** 0.5h
**File ownership:** `proxy.ts`, `lib/profile/resolve-profile-id.ts` (new)

## Context Links

- `clarifications.md` § "The three authored premises that do not hold in this repository" (premise 1
  and premise 2), § "Route and access"
- `spec/F006_ProfileBanThan/functional-spec.md` FR-101, FR-102, FR-401, FR-402
- Code: `proxy.ts:47-51` (`isGuarded`), `app/kudos/_components/kudos-hero.tsx:76-89` (the shipped
  Sunner-search form whose target is `/profile`)

## Overview

- **Priority:** P1 — TC_ACC_001/002 and TC_FUN_001–005 all land here.
- **Status:** complete
- Add `/profile` to the proxy's guarded allowlist, and put `?id=` resolution in one pure, testable
  function with no I/O.

## Key Insights

- **There is no `PUBLIC_ROUTES` in this repo.** TC_ACC_001 assumes an inverse list; `proxy.ts` holds
  an explicit allowlist of *guarded* prefixes and everything else falls through public. Add
  `/profile` to that allowlist in the exact shape `/kudos/new` already uses — `pathname === "/profile"
  || pathname.startsWith("/profile/")` — and **do not invert the list**. Inverting would move every
  existing route's access decision inside a commission about one screen, and F004's public read path
  (`/kudos`, `/kudos/[id]`, `/kudos/secret-box`) is ratified public: an inversion puts all of it one
  editing mistake away from being guarded.
- **The id is a `bigint`, not a uuid.** There is no uuid-keyed `profiles` table; the person entity is
  `public.sunners` with `id bigint generated always as identity`. TC_FUN_003/004's *defence* is kept
  exactly — a malformed id never reaches Postgres, so no `22P02`-class error can surface as a 500 —
  only the type changes. Shape-check `/^\d{1,18}$/` **before** any query.
- **`?q=` must not 404.** `kudos-hero.tsx:77` ships a live `GET` form with `action="/profile"` and
  `name="q"`, so `/profile?q=anything` is reachable today. Unknown params are ignored and the self
  view renders (A5). Returning 404 for an unrecognised param would turn the shipped Sunner-search
  box into a 404 generator. Building the search *result* is a separate commission.
- **The proxy's redirect helper wipes the query string** (`url.search = ""` in
  `redirectWithSessionCookies`). That is existing, correct behaviour for `/login` — do not change it,
  and do not add a `next=` parameter; that is not in scope and touches the ratified OAuth round trip.
- Two layers, deliberately: the proxy is the gate, and the page re-resolves the session itself, so
  the guard holds even if the proxy's route list is later edited (TC_ACC_001's own note asks for
  exactly this). The page half is phase 09's step.

## Requirements

Functional: FR-101 (proxy guard, exact path + subpath), FR-401 (shape check before any query),
FR-402 (the five resolution outcomes). Non-functional: `resolve-profile-id.ts` must be pure — no
`next/*`, no Supabase, no `async` — so it is trivially exercised and reusable.

## Architecture

```ts
// lib/profile/resolve-profile-id.ts
export type ProfileIdResolution =
  | { kind: "self" }               // absent, empty, or equal to the viewer's own id
  | { kind: "other"; id: number }  // well-formed, different from the viewer
  | { kind: "not-found" };         // malformed, or repeated with differing values

export function resolveProfileId(
  raw: string | string[] | undefined,
  viewerSunnerId: number | null,
): ProfileIdResolution;
```

Decision table, exhaustive:

| Input | Result |
|---|---|
| absent, or `""` | `self` — a cleared query string is not an error |
| `["1","1"]` (repeated, identical) | treat as `"1"` |
| `["1","2"]` (repeated, differing) | `not-found` — choosing one would hide the caller's mistake |
| fails `/^\d{1,18}$/` (`banana`, `42.5`, `' or 1=1`, a truncated uuid) | `not-found`, before any query |
| passes, `=== viewerSunnerId` | `self` — canonicalised, **no redirect** |
| passes, `!== viewerSunnerId` | `other` |
| any other param (`?q=`, `?foo=`) | ignored entirely; never enters the decision |

**Data flow:** `searchParams.id` (Next 16 async `searchParams`) → `resolveProfileId` → one of three
verdicts. `not-found` → `notFound()`. `self` with `viewerSunnerId === null` → the sparse view.

## Related Code Files

Create: `lib/profile/resolve-profile-id.ts`.
Modify: `proxy.ts` — one clause added to `isGuarded`, plus a sentence in the module doc comment.
Delete: none.

## Implementation Steps

1. `proxy.ts`: extend `isGuarded` with `|| pathname === "/profile" || pathname.startsWith("/profile/")`.
2. Update the `proxy.ts` doc comment: `/profile` is guarded because the screen is a signed-in
   identity surface; the match is exact-path-or-subpath, never `startsWith("/profile")` alone — same
   reasoning already written there for `/kudos/new`.
3. Write `resolve-profile-id.ts` implementing the table above, with the regex as a module constant
   and a comment naming the reason for `{1,18}` (a bigint's decimal width, so no value can overflow
   on parse).
4. `npm run typecheck`, `npm run lint`.
5. Verify the shipped search box: `grep -n 'action="/profile"' app/kudos/_components/kudos-hero.tsx`
   still matches, and `?q=` maps to `self` in the table.

## Todo List

- [ ] `/profile` added to `isGuarded` as exact-path-or-subpath
- [ ] The guarded allowlist was **not** inverted; `/kudos`, `/kudos/[id]`, `/kudos/secret-box` untouched
- [ ] `resolveProfileId` is pure and exhaustive over the seven input classes
- [ ] Repeated-with-differing-values → `not-found`; repeated-identical → accepted
- [ ] Unknown params ignored, never a 404
- [ ] Shape check precedes every use of the value
- [ ] typecheck + lint exit 0

## Success Criteria

- `git diff proxy.ts` shows exactly one changed condition plus comment text — no change to the
  `/login` redirect, the cookie-copy helper, or the `matcher`.
- Anonymous `GET /profile` and `GET /profile?id=1` both 307 to `/login` (phase 02's anon suite).
- `GET /kudos`, `/kudos/1`, `/kudos/secret-box` still render anonymously — F004's public read path
  is unmoved (`--project=anon` green).
- `resolveProfileId` returns `not-found` for `banana`, `42.5`, `' or 1=1`, `1e3`, `-1`,
  `["1","2"]`, and a 19-digit string; and `self` for `undefined`, `""`, `["1","1"]` when the viewer
  is 1, and any input when only `?q=` is present.

## Risk Assessment

| Risk | L×I | Countermeasure |
|---|---|---|
| `startsWith("/profile")` used, catching a future `/profiles` route | L × M | Exact-path-or-subpath is spelled out in the step and in the comment, mirroring `/kudos/new` |
| Allowlist inverted "while we're in here" | L × **H** | Explicit prohibition + a success criterion that anonymous `/kudos` still renders |
| `?q=` returns 404 and breaks the shipped search box | M × M | Decision table row + step 5's grep; A5 recorded |
| A malformed id reaches Postgres and surfaces as a 500 | L × M | The regex gate is upstream of every query, and the resolver has no I/O to reach a database with |
| The proxy redirect losing the query string is mistaken for a bug and "fixed" | L × M | Key Insight records that it is intentional and out of scope |

**Rollback.** Two files, both trivially revertible; reverting `proxy.ts` alone makes `/profile`
public again without breaking any other route.

## Security Considerations

- Two-layer guard (PERM011): the proxy plus the page's own session re-resolution in phase 09.
  Neither is sufficient alone by design.
- The shape check is the injection boundary: no `?id=` value is interpolated into a query until it
  has passed `/^\d{1,18}$/` and `Number()`.
- Returning `not-found` rather than an error message for a non-existent id avoids an enumeration
  oracle distinguishing "no such Sunner" from "malformed".

## Next Steps

- Consumed by phase 09 (`app/profile/page.tsx` calls `resolveProfileId` then `notFound()`).
- Depends on phase 02's gate only; independent of 03–05, so it may run alongside them.
