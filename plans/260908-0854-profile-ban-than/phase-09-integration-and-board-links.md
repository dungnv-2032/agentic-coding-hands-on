# Phase 09 — Integration: page wiring, board `?id=` links, the F004 test amendment

**Track:** Integration · **Owner:** `implementer` · **Effort:** 2h
**File ownership:** `app/profile/page.tsx`, `app/kudos/_components/sunner-chip.tsx`,
`app/kudos/_components/gift-leaderboard.tsx`, `app/kudos/_components/kudos-board.tsx`,
`e2e/kudos-live-board.spec.ts`, **plus inherited from phase 04 on its completion:**
`lib/kudos/queries.ts`, `lib/kudos/board-data.ts`, `lib/kudos/view-model.ts`

## Context Links

- Phases 01, 05, 06, 07, 08 must all be complete.
- `clarifications.md` § premise 3 ("Both" — the route *and* the board emit `?id=`), § "Route and
  access", § "Card interactions"
- `spec/F006_ProfileBanThan/functional-spec.md` FR-003, FR-102, FR-402, FR-405
- Code: `app/kudos/_components/sunner-chip.tsx:69`, `gift-leaderboard.tsx:57`,
  `e2e/kudos-live-board.spec.ts:354,356`, `app/kudos/_components/kudos-board.tsx:61,91-116`

## Overview

- **Priority:** P1 — this is where RED turns GREEN.
- **Status:** pending
- Wire the page (guard re-check, `?id=` resolution, data → components), make the board emit
  `?id=`, honour the hashtag deep link, and narrow F004's two ratified href assertions on purpose.

## Key Insights

1. **`/kudos` reads no query string at all.** `kudos-board.tsx` keeps `hashtagFilterId` in
   `useState` (line 61) and maps tag *name* → option id (line 91). So FR-405's "hashtag click
   navigates to the board filtered by that tag" is **not** satisfied by a bare
   `Link href="/kudos?hashtag=X"` — the board would render unfiltered and the test would pass on a
   half-truth. This contradicts nothing in `clarifications.md`; it is a mechanism the clarifications
   assumed existed. It must be added deliberately: initialise `hashtagFilterId` from
   `useSearchParams().get("hashtag")`, matched by name against `board.hashtagOptions`, defaulting to
   `null` when absent or unrecognised — so all 27 shipped board assertions stay true.
2. **`GiftRowView` has no sunner id.** `fetchGifts` selects `sunner:sunners(full_name)` only, so
   `gift-leaderboard.tsx` cannot build `?id=`. Fix it the cheap way: add `sunner_id` — a **plain,
   non-null column on `gift_awards`** — to the select list, and `sunnerId: number` to `GiftRowView`.
   No new embed, no nullability to handle.
3. **`SunnerChip`'s `href` is deliberately a fixed literal** ("never built from a field", per its own
   comment, ratified as K-9). Changing it to `?id={sunner.id}` is a knowing reversal of that
   property, so it is recorded here rather than done quietly. It is safe for anonymous rows:
   `kudos-card.tsx:125` routes them to `AnonymousSenderChip`, which has no link at all — so the
   redacted `id: 0` stub can never reach this component. Add a guard anyway (`id > 0` falls back to
   the bare `/profile`) so a future caller cannot leak an `?id=0`.
4. **`account-menu.tsx:93` stays a bare `/profile`.** It is the viewer's own menu; there is no id to
   carry, and `/profile` with no query string already means "me". Do not touch that file.
5. **The F004 amendment is deliberate narrowing, never a silent edit.**
   `e2e/kudos-live-board.spec.ts:354` and `:356` assert
   `toHaveAttribute("href", "/profile")`; both become a pattern match on `/^\/profile\?id=\d+$/`.
   This is *stricter* than before (it now pins a shape rather than a literal), and it is the only
   change permitted in that file.
6. **The page is the second half of the two-layer guard.** It re-resolves the session itself and
   redirects on absence, so the guard survives a future edit to `proxy.ts`'s route list (FR-102).

## Requirements

Functional: FR-003, FR-102, FR-401, FR-402, FR-405 (hashtag destination), plus the composition of
every 2xx/3xx/4xx requirement into one rendered page. Non-functional: `page.tsx` < 200 lines;
`getPageContext()` and `getProfileData()` run under one `Promise.all` (the shape
`app/kudos/page.tsx:48` already uses); the Supabase `user` object never enters a Client Component.

## Architecture

```
GET /profile[?id=N]
  proxy.ts (phase 06)  → unauthenticated? 307 /login
  app/profile/page.tsx
    ├ Promise.all([ getPageContext(), createClient()→resolveViewer() ])
    ├ resolveProfileId(searchParams.id, viewer.sunnerId)      ← phase 06
    │    not-found → notFound()
    │    self      → targetId = viewer.sunnerId (may be null → sparse)
    │    other     → targetId = N
    ├ getProfileData(targetId, viewer)   → ProfileViewModel   ← phase 05
    │    sunner missing → notFound()
    └ render: HomeHeader · ProfileKeyvisual · ProfileHero(+ProfileBadgeRow)
              · stats ? ProfileStatsCard : WriteKudoBar
              · KudosDirectionSection(fetchPage=fetch-profile-kudos-page,
                                      toggleLike=toggleKudosLike)  ← existing action, untouched
              · SiteFooter
```

`onHashtagClick` in the profile pushes `/kudos?hashtag=<tag>`; `kudos-board.tsx` reads that param on
mount. Copy Link reuses the board's toast component.

**Data flow:** one server render produces hero + branch + page 1; only subsequent pages cross the
wire, via the phase-05 action. The heart still round-trips to the database for its count.

## Related Code Files

Modify: `app/profile/page.tsx` (replace the `ComingSoon` placeholder — the route already exists),
`sunner-chip.tsx` (href), `gift-leaderboard.tsx` (href), `kudos-board.tsx` (read `?hashtag=`),
`lib/kudos/queries.ts` + `view-model.ts` + `board-data.ts` (`sunnerId` on `GiftRowView`),
`e2e/kudos-live-board.spec.ts` (lines 354, 356 only).
Delete: nothing. **Do not touch** `app/_components/account-menu.tsx`, `kudos-card.tsx`,
`anonymous-sender-chip.tsx`, `toggle-kudos-like.ts`, `viewer.ts`, `derive.ts`.

## Implementation Steps

1. Replace `app/profile/page.tsx`'s body: metadata kept, `ComingSoon` import dropped. Compose per
   the diagram; call `notFound()` for both `not-found` verdicts (bad id, missing sunner).
2. Re-resolve the session in the page and redirect to `/login` when absent — the defence-in-depth
   half of PERM011.
3. `queries.ts`: add `sunner_id` to `fetchGifts`'s select and to `GiftFeedRow`.
   `view-model.ts`: add `sunnerId: number` to `GiftRowView`. `board-data.ts`: map it.
4. `gift-leaderboard.tsx`: `href={`/profile?id=${gift.sunnerId}`}`.
5. `sunner-chip.tsx`: `href={sunner.id > 0 ? `/profile?id=${sunner.id}` : "/profile"}`; update the
   comment that currently says the href is a fixed literal, citing FR-003 and this phase.
6. `kudos-board.tsx`: initialise `hashtagFilterId` from `useSearchParams().get("hashtag")` resolved
   against `board.hashtagOptions` by name; unknown or absent → `null`. Add a one-line comment
   naming FR-405 as the reason.
7. `e2e/kudos-live-board.spec.ts:354,356`: swap the literal for `/^\/profile\?id=\d+$/`, and add a
   comment above each recording that this is F006's deliberate narrowing of a ratified assertion.
8. `npm run typecheck`, `npm run lint`, `npm run build`.
9. Hand off to phase 10. Do **not** run the full Playwright suite here.

## Todo List

- [ ] `page.tsx` composed, `ComingSoon` removed, < 200 lines
- [ ] Page re-resolves the session (layer two of the guard)
- [ ] `notFound()` on a bad id **and** on a missing `sunners` row; no partial profile ever renders
- [ ] `?id=` matching the viewer renders the self face with **no redirect**
- [ ] `GiftRowView.sunnerId` added via the plain `gift_awards.sunner_id` column
- [ ] `sunner-chip` emits `?id=`, with an `id > 0` guard, comment updated
- [ ] `kudos-board.tsx` reads `?hashtag=`, defaulting to `null`
- [ ] `kudos-live-board.spec.ts:354,356` narrowed, each with a recorded reason
- [ ] `account-menu.tsx` untouched
- [ ] typecheck + lint + build exit 0

## Success Criteria

- `/profile` authenticated renders the self face; `/profile?id=2` renders that Sunner's face with a
  write bar and **no** stat row; `/profile?id=banana|42.5|99999999|1&id=2` all render the 404 page.
- `/profile?id={own id}` shows no redirect in the address bar and is identical to `/profile`.
- `/profile?q=anything` renders the self face — the shipped Sunner-search box still works.
- On `/kudos`, every `kudos-sender`/`kudos-receiver` href matches `/^\/profile\?id=\d+$/`, and the
  anonymous card's sender remains a non-link.
- Clicking a hashtag on a profile card lands on `/kudos?hashtag=<tag>` **with the board filtered** —
  the filter menu shows that tag active, not just the URL carrying it.
- `npm run build` exits 0.

## Risk Assessment

| Risk | L×I | Countermeasure |
|---|---|---|
| `?hashtag=` added to the URL but the board ignores it, and a URL-only assertion passes | **H** × M | Key Insight 1; the success criterion asserts the board's *filter state*, not the URL |
| Reading `?hashtag=` changes F004's default board state | M × H | Absent/unknown → `null`, i.e. today's exact initial state; `--project=anon` must stay green |
| `?id=0` leaks from a redacted anonymous stub | L × M | `id > 0` guard, plus `kudos-card.tsx:125` already routes anonymous rows elsewhere |
| The F004 amendment is committed as a bare regex swap and later read as a relaxation | M × M | Comment at both lines + the record in `clarifications.md` premise 3 + this phase's step 7 |
| `page.tsx` grows past 200 lines by inlining layout | M × M | Layout lives in phases 07/08's components; the page only composes |
| Two `notFound()` paths conflated, letting a half-rendered profile through | L × H | Both verdicts return before any component renders; asserted in phase 02 |

**Rollback.** Revert `page.tsx` to the `ComingSoon` placeholder and revert the four board files plus
the two test lines — one commit. The proxy guard (phase 06) may stay; a guarded `ComingSoon` is
harmless. Reverting the board links **must** revert the test amendment in the same commit, or
F004's suite goes red.

## Security Considerations

- FR-102/PERM011: the page's own session check is what makes the guard survive a proxy edit.
- FR-603: only `isAuthenticated`/`isAdmin` and the `ProfileViewModel` cross into Client Components —
  never the Supabase `user`, never `viewer.userId`.
- SEC_001: on another Sunner's profile the sent count is **absent from the props**, so no client
  serialisation can carry it. Verify by searching the rendered HTML for the string.
- `toggleKudosLike` is passed as a prop (F004's "Server Action as a prop" idiom); no Track A file
  imports it directly.

## Next Steps

- Blocks phase 10 (GREEN + visual evidence).
- Depends on 01, 05, 06, 07, 08.

---

## Inherited from phase 08 (added 2026-09-08) — read before wiring the page

- **The direction trigger lives in `profile-direction-menu.tsx`, not in the section.** Phase 08 moved
  it because `kudos-direction-section.tsx` measured 287 lines with it inline; the alternatives were a
  fourth file (outside that phase's ownership) or deleting the design-provenance comments.
- **`onCopyLink` / `onHashtagClick` are resolved *inside* `kudos-direction-section.tsx`, not accepted
  as props.** This phase renders the section from a Server Component, and this Next version throws on
  a plain function prop crossing that boundary. The exact prop contract to code against is in
  `reports/momorph-ui-implementer-phase-08.md` § 1 — read it rather than inferring the shape.
- `kudos-direction-section.tsx` is the section's single `"use client"` boundary and already owns
  SM-001's four states, the FR-403 switch, a monotonic request-id race guard, the hashtag push and the
  Copy-Link toast. Do not re-implement any of them at the page level.

## Inherited from phase 04 (added 2026-09-08)

- `lib/kudos/map-kudos-card.ts` is now the ONE shared row→card mapper; `board-data.ts` delegates to
  it and holds no mapping code. `view-model.ts` gained `sentAnonymously` additively.
- `canLike` is no longer the literal `ctx.viewerSunnerId !== row.sender_id` the plan transcribed —
  that breaks the common e2e case (authenticated viewer with no `sunners` row reading a masked row:
  `null !== null` wrongly disables the heart). It is one `viewerIsSender` predicate guarding both
  nulls. Do not "restore" the literal form.
- **`fetchGifts` still lacks `gift_awards.sunner_id`** — phase 04 left it alone because it is in that
  phase's file but not its scope. **Adding it is this phase's job**, and it is what unblocks
  `gift-leaderboard` emitting `?id=`.
- The sidebar's `kudosSent` carries a null guard now: an anonymous visitor can no longer count the
  frame viewer's anonymous sends, which is the correct answer under SEC_002.
- **The local database is not in seed state.** F005's compose e2e linked `sunners.id = 10` to a real
  auth user and `resolveSidebarSunnerId`'s fallback quietly depends on it. Run `npx supabase db reset`
  before measuring anything, or the numbers are not reproducible.
