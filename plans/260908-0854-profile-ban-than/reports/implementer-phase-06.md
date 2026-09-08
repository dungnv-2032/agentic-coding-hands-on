# Implementer report — Phase 06: route guard + `?id=` resolver

## Files touched

| File | Change | Lines |
|---|---|---|
| `proxy.ts` | modified — one clause added to `isGuarded` + doc comment | 73 total (+8/-1) |
| `lib/profile/resolve-profile-id.ts` | created | 81 |

## Checks

| Check | Result |
|---|---|
| Typecheck (`npm run typecheck`) | exit `0` — clean |
| Lint (`npm run lint`) | exit `0` — 0 errors, 30 pre-existing warnings in `e2e/*.spec.ts` (unused vars, other agents' in-progress files); nothing in either owned file |

## Acceptance criteria (phase file's Todo List)

| Criterion | Status |
|---|---|
| `/profile` added to `isGuarded` as exact-path-or-subpath | done — `pathname === "/profile" \|\| pathname.startsWith("/profile/")` |
| Allowlist not inverted; `/kudos`, `/kudos/[id]`, `/kudos/secret-box` untouched | done — only one clause added, nothing removed |
| `resolveProfileId` pure and exhaustive over the seven input classes | done — no imports beyond the type export itself; no `next/*`, no Supabase, no `async` |
| Repeated-differing → `not-found`; repeated-identical → accepted | done — `Set` dedup on the array branch |
| Unknown params ignored, never 404 | done — resolver only ever receives `searchParams.id`; any other param never reaches it |
| Shape check precedes every use of the value | done — regex test runs before `Number()`, before the self-id comparison |
| typecheck + lint exit 0 | done |

## Success criteria verification

- `git diff proxy.ts`: exactly one changed condition (5-line `isGuarded` clause) plus the doc-comment addition — confirmed via `git diff`, no touch to `redirectWithSessionCookies`, the `/login` redirect, or `config.matcher`.
- `grep -n 'action="/profile"' app/kudos/_components/kudos-hero.tsx` → still matches at line 77; the shipped search form target is untouched.
- Manual trace of `resolveProfileId` against the phase's decision table (all inputs listed in "Success Criteria"): `banana`, `42.5`, `' or 1=1'`, `1e3`, `-1` all fail `/^\d{1,18}$/` → `not-found`; `["1","2"]` → `not-found` (distinct-value array); a 19-digit string fails the regex → `not-found`; `undefined`, `""`, `["1","1"]` with viewer `1` → `self`; any call where the caller passes `undefined` for `id` (i.e. only `?q=` was present) → `self`. All match the table.
- Live server assertions (307 redirects, anon `/kudos*` still rendering) were **not** run — dev server / Playwright are out of scope per the task's explicit constraints ("Do NOT start a dev server", "Do NOT run the Playwright suite"). Phase 02's tester owns that evidence.

## Design notes

- `resolveProfileId`'s `not-found` branch covers only malformed shape and repeated-differing values, per the phase's architecture section and technical-spec.md § A1: "well-formed id matching no `sunners` row" is a database question, resolved by `getProfileData` in the data layer (phase 05/09), not here. The module stays pure with zero I/O as required.
- The "unknown param ignored" behaviour needed no special-case code: the resolver's contract is over `raw: string | string[] | undefined` — the caller (the page, phase 09) is what reads `searchParams.id` specifically, so a request carrying only `?q=` simply never produces a value for `raw` in the first place. Documented in the module comment so a future reader doesn't go looking for a `q` filter that doesn't exist here.

## Unresolved questions

None.

**Status:** DONE
