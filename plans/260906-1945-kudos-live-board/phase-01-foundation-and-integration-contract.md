# Phase 01 — Foundation & integration contract

**Track:** Shared prerequisite (blocks both tracks) · **Owner:** `implementer` ·
**Effort:** 1h · **test_policy:** `e2e-red-first`

## Context Links

- [plan.md](plan.md) · [clarifications.md](clarifications.md) · [test-contract.md](test-contract.md)
- [technical-spec.md § 4.2 Data Model](spec/kudos-live-board/technical-spec.md), [§ 4.5 ALG-001](spec/kudos-live-board/technical-spec.md)
- [Supabase study](../reports/researcher-260906-1958-supabase-data-layer.md) § 4 (typed queries, `db:types` script)
- [UI study](../reports/researcher-260906-1958-repo-ui-conventions.md) § 1 (screen anatomy), § 6 (data-testid)
- [RED gate](../reports/tester-260906-1958-kudos-red-gate.md) — K-21 currently fails on HTTP 404
- Existing pattern to copy: `app/_components/coming-soon.tsx` (whole file), `app/kudos/page.tsx:1-14`

## Overview

**Priority:** P1 — nothing else can start until the contract exists. **Status:** delivered.

Lands the three artifacts both tracks need before either can move: the frozen TypeScript
integration contract, the three placeholder routes (which turn K-21 green on their own), and the
`db:types` npm script. No Supabase read, no UI, no schema.

## Key Insights

1. **`kudos.id` must be numeric, not uuid.** `e2e/kudos-live-board.spec.ts:448` asserts
   `kudos-detail-link` href matches `/\/kudos\/\d+/`, and K-21 visits `/kudos/123`. The draft
   ERD in `technical-spec.md § 4.2` types `kudos.id` as `uuid`; a uuid href cannot satisfy that
   regex. Resolution: **`bigint generated always as identity`** for `kudos`, `sunners`,
   `departments`, `hashtags`, `kudos_attachments`, `kudos_likes`, `gift_awards`,
   `spotlight_ticker_events`. Only `kudos_likes.user_id` stays `uuid` (it is `auth.uid()`).
   Phase 09 reconciles the draft ERD.
2. **Two distinct notions of "viewer", and conflating them makes K-25 vacuous.**
   `viewer.sunnerId` is *identity* — resolved only from `sunners.auth_user_id = auth.uid()`, so it
   is `null` for an anon visitor **and** for the fresh e2e user who has no `sunners` row. The
   sidebar's *display* fallback to the seeded frame viewer is a separate resolution. If identity
   fell back to the seeded viewer, the top card (sent by that viewer) would render its heart
   `disabled`, `kudos-live-board-authed.spec.ts:76` would take its early-return branch, and K-25
   would pass while proving nothing. Identity is auth-only. Non-negotiable.
3. **Placeholder routes are independent of both tracks.** They touch no file either track owns,
   so landing them here makes K-21 the first assertion to go green and de-risks the route
   collision (`/kudos/new` static vs `/kudos/[id]` dynamic — Next resolves static first).
4. **`derive.ts` is imported by client components**, so it must stay pure: no `next/headers`, no
   Supabase, no `Intl` (ICU version drift between the server and browser runtimes would
   hydration-mismatch `1.000`). Heart grouping is explicit dot-insertion, not `toLocaleString`.

## Requirements

**Functional:** FR-002 (generated types committed, script wired), FR-101 partial (the four CTA
destinations resolve rather than 404 — `/profile` already ships), the ALG-001 top-5 rule and the
badge-threshold rule as pure functions.

**Non-functional:** every file ≤200 lines; `derive.ts` has zero runtime dependencies; the contract
compiles under `tsc --noEmit` with no `any`; the frozen files are not edited again by any later
phase without orchestrator approval.

## Architecture

```
lib/kudos/view-model.ts   types only, no runtime code      ← frozen
lib/kudos/derive.ts       pure fns over those types        ← frozen
        ▲                                    ▲
        │ produces                           │ consumes
   Track B (04)                          Track A (05-08)
        └──────────── wired by 09 (app/kudos/page.tsx) ────┘
```

**Data flow:** none yet — this phase declares the shape the data will travel in.

**Contract surface** (`lib/kudos/view-model.ts`):

```ts
export type BadgeTier = "New Hero" | "Rising Hero" | "Super Hero" | "Legend Hero";

export interface SunnerView {
  id: number; fullName: string; department: string; avatarUrl: string;
  badge: BadgeTier; badgeTooltip: string | null;   // null for New Hero — no published copy < 10
}
export interface KudosAttachmentView { id: number; imageUrl: string }
export interface KudosCardView {
  id: number; sender: SunnerView; receiver: SunnerView;
  campaign: string | null; message: string; sentAtLabel: string;   // "10:00 - 10/30/2025"
  hashtags: string[]; attachments: KudosAttachmentView[];
  hearts: number; likedByViewer: boolean; canLike: boolean; isOwnedByViewer: boolean;
}
export interface FilterOptionView { id: number; name: string }
export interface SidebarCountsView {
  kudosReceived: number; kudosSent: number; heartsReceived: number;
  secretBoxOpened: number; secretBoxUnopened: number;
}
export interface GiftRowView { id: number; sunnerName: string; giftLabel: string }
export interface SpotlightNodeView {
  id: number; name: string; kudosId: number; receivedAtLabel: string; isJustUpdated: boolean;
}
export interface SpotlightTickerRowView { id: number; timeLabel: string; name: string }
export interface KudosBoardViewModel {
  kudos: KudosCardView[];                       // full feed, newest first
  hashtagOptions: FilterOptionView[];           // 13, frame order
  departmentOptions: FilterOptionView[];        // 50, frame order
  spotlight: { nodes: SpotlightNodeView[]; ticker: SpotlightTickerRowView[] };
  sidebar: { counts: SidebarCountsView; gifts: GiftRowView[] };
  viewer: { isAuthenticated: boolean; sunnerId: number | null };
}
export interface KudosLikeResult { liked: boolean; hearts: number }
export type ToggleKudosLike = (kudosId: number) => Promise<KudosLikeResult>;
```

**Pure helpers** (`lib/kudos/derive.ts`):

| Function | Contract |
|---|---|
| `badgeTierFor(receivedCount)` | `< 10` New Hero · `>= 10` Rising · `>= 20` Super · `>= 50` Legend (clarifications badge decision) |
| `badgeTooltipFor(tier)` | Rising → the 10-Kudos sentence, Super → 20, Legend → 50, New Hero → `null`. Verbatim from clarifications § Badge tooltip copy |
| `formatHeartCount(n)` | dot-grouped, `1000` → `"1.000"`. Explicit grouping, never `Intl` |
| `formatSentAt(iso)` | `HH:mm - MM/DD/YYYY` in a fixed offset, matching `e2e/…spec.ts:376` |
| `pickHighlight(cards)` | ALG-001 — `[...cards].sort(hearts desc).slice(0, 5)`, stable tie-break on `id desc` |
| `matchesFilters(card, {hashtag, department})` | AND-combined; department matches **`receiver.department`** |
| `FEED_PAGE_SIZE` | `10` — 50 seeded rows page five times, satisfying assumption A4 |

`pickHighlight` must be a stable sort so SSR and the first client render agree.

## Related Code Files

**Create:** `lib/kudos/view-model.ts` · `lib/kudos/derive.ts` · `app/kudos/new/page.tsx` ·
`app/kudos/secret-box/page.tsx` · `app/kudos/[id]/page.tsx`
**Modify:** `package.json` (one script line)
**Read only:** `app/kudos/page.tsx`, `app/_components/coming-soon.tsx`, `app/awards-information/page.tsx`
**Delete:** none

## Implementation Steps

1. Write `lib/kudos/view-model.ts` exactly as § Architecture states. Types only — no runtime
   export, so nothing pulls a module into the client bundle.
2. Write `lib/kudos/derive.ts` with the seven helpers. Every literal sentence is copy-pasted from
   `clarifications.md` § "Badge tooltip copy" — do not retype Vietnamese by hand.
3. Create the three placeholder pages, each mirroring `app/kudos/page.tsx:1-14` verbatim in shape:
   a static `metadata` export with title `"<Screen> — Sun* Annual Awards 2025"` plus
   `return <ComingSoon />`. `app/kudos/[id]/page.tsx` ignores its `params` — it is a declared
   placeholder, not a detail screen.
4. Add `"db:types": "supabase gen types typescript --local --schema public > lib/supabase/database.types.ts"`
   to `package.json` scripts. Do not run it yet — no schema exists until phase 02.
5. Verify: `npm run typecheck && npm run lint`.
6. Verify K-21 alone goes green: `npx playwright test e2e/kudos-live-board.spec.ts -g "K-21" --reporter=list`.

## Todo List

- [ ] `lib/kudos/view-model.ts` — full contract surface, no `any`
- [ ] `lib/kudos/derive.ts` — 7 helpers, pure, tooltip copy pasted not retyped
- [ ] `app/kudos/new/page.tsx` renders `ComingSoon`
- [ ] `app/kudos/secret-box/page.tsx` renders `ComingSoon`
- [ ] `app/kudos/[id]/page.tsx` renders `ComingSoon`, ignores `params`
- [ ] `package.json` — `db:types` script
- [ ] `npm run typecheck && npm run lint` clean
- [ ] K-21 green in isolation

## Success Criteria

- `npm run typecheck` and `npm run lint` both exit 0.
- K-21 passes: `/kudos/new`, `/kudos/secret-box`, `/kudos/123` each return HTTP 200 with exactly
  one visible `main h1`.
- Every other kudos assertion still fails for the same reason as the RED run (missing screen
  hooks) — no assertion has been made to pass by weakening it.
- `lib/kudos/view-model.ts` and `derive.ts` are not referenced by `app/kudos/page.tsx` yet.

## Risk Assessment

| Risk | L×I | Countermeasure |
|---|---|---|
| Route collision: `/kudos/new` swallowed by `/kudos/[id]` | Low × High | Next resolves static segments before dynamic ones; K-21 asserts all three independently, so a collision fails loudly in step 6 |
| The contract turns out to be missing a field Track A or B needs | Med × High | A missing field is escalated to the orchestrator, which amends this phase's contract once and notifies both tracks — never patched unilaterally inside a track |
| `formatSentAt` drifts by timezone between the server render and the browser | Med × Med | Format server-side only, at a fixed offset, and ship the string in the view model (`sentAtLabel`); the client never re-derives it |
| `bigint` ids arriving as JS strings from PostgREST | Med × Med | Ids stay well inside `Number.MAX_SAFE_INTEGER`; phase 04 coerces with `Number()` at the query boundary and the contract types them as `number` |

**Rollback:** delete the five created files and revert the one `package.json` line. Nothing else
imports them yet, so the revert is total.

## Security Considerations

- No auth, no data access, no secrets in this phase.
- `derive.ts` must not import `next/headers`, `@/lib/supabase/*`, or anything server-only — it is
  reachable from the client bundle, and a server import there would leak into it.
- The placeholder pages inherit `ComingSoon`'s existing `getPageContext()` read; they must not add
  their own session handling or forward the Supabase `user` object anywhere.
- `/kudos/[id]` must not echo `params.id` into the DOM (no reflected-content surface on a route
  that renders for any arbitrary path).

## Next Steps

Unblocks phase 02 (Track B) and phase 05 (Track A), which then run concurrently. Both read this
contract; neither writes to it.
