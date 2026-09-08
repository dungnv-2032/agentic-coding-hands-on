# Phase 01 — Contract + i18n — implementer report

## Files touched

| File | Change | Lines |
|---|---|---|
| `lib/profile/profile-view-model.ts` | create | 72 |
| `lib/i18n/messages/vi-profile.ts` | create | 48 |
| `lib/i18n/messages/en-profile.ts` | create | 36 |
| `lib/i18n/messages/dictionary.ts` | edit — added `profile` block after `kudos` | +27 |
| `lib/i18n/messages/vi.ts` | edit — import + wire `viProfile` | +2 |
| `lib/i18n/messages/en.ts` | edit — import + wire `enProfile` | +2 |

`git diff --stat` / `git status` confirm only these six files changed. No component, query, migration or test file touched.

## Contract (`lib/profile/profile-view-model.ts`)

Written exactly to the phase file's architecture section: `FeedDirection`, `FeedCursor`,
`ProfileHeroView` (nullable `sunnerId`/`department`/`badge`), `ProfileStatsView`, `ProfileFeedPage`,
`ProfileViewModel` (`stats`/`writeKudoTargetId` mutually exclusive on `isSelf`, `counts.sent`
nullable), `FetchProfileKudosPage`. Type-only import of `BadgeTier`/`KudosCardView` from
`@/lib/kudos/view-model`. No `starCountFor`, no star field (AMEND-1 honored). No I/O, no React, no
`Intl`.

## Dictionary / copy

- `Dictionary.profile` added between `kudos` and `kudosCompose`, mirroring the `kudos` nesting.
- `vi-profile.ts`: the five `stats.*` labels and `secretBoxButton` are copy-pasted verbatim from the
  shipped `vi-kudos.ts` (`sidebar.stats` / `secretBoxButton`), not retyped. `badges.*`,
  `writeBar.label`, `direction.*`, `feed.emptyReceived`/`emptySent` transcribed from
  `clarifications.md` as instructed.
- `en-profile.ts`: faithful translation, same key set.

### Unsourced key — flagged, not invented

`feed.endOfFeed` has **no source string** anywhere: `docs/screens/SCR006_ProfileBanThan/spec.md`
marks it `TBD (draft)` in all three referencing rows, and the MoMorph frame never captured a scrolled
`hasMore === false` state. F004's board (the only precedent) shows **no** end-of-feed message by
design ("dừng lặng lẽ ở trạng thái hiện tại" — functional-spec). Per instruction not to invent copy,
I left both `vi-profile.ts` and `en-profile.ts`'s `endOfFeed` as `""` with an inline comment
explaining why, rather than writing a Vietnamese/English sentence with no design authority. **A copy
source is needed before whichever later phase renders `feed.D.end`.**

## Checks

- Typecheck: **clean, exit 0**
- Parity gate verified live: removed `secretBoxButton` from `en-profile.ts` → `tsc --noEmit` failed
  with `TS2741: Property 'secretBoxButton' is missing…` (exit 2) → file restored → exit 0 again.
- Lint: **exit 0** (28 pre-existing warnings in unrelated `e2e/*.spec.ts` files — untouched by this
  phase, not introduced by it).
- Key-set parity: `grep`-derived key lists for `vi-profile.ts` / `en-profile.ts` — **19 / 19, identical set**.
- File sizes: 72 / 48 / 36 lines — all well under the 200-line cap.

## Acceptance criteria (phase file Todo List)

- [x] `lib/profile/profile-view-model.ts` created, types only, no runtime import
- [x] `Dictionary.profile` added
- [x] `vi-profile.ts` written, five stat labels copied from `vi-kudos.ts` not retyped
- [x] `en-profile.ts` written with an identical key set
- [x] `vi.ts` / `en.ts` wired
- [x] `npm run typecheck` exit 0
- [x] `npm run lint` exit 0

## Unresolved questions

1. **`profile.feed.endOfFeed` copy** — no design or spec source exists (spec.md: `TBD (draft)` ×3).
   Shipped as `""` with a documenting comment in both locale files. Needs a copy decision (new
   clarification, or explicit "F004-style silent stop, drop the element") before the phase that
   renders the feed's end sentinel.

**Status:** DONE_WITH_CONCERNS
**Summary:** Contract + `profile` Dictionary block + both locale files created and wired exactly to
spec; typecheck/lint clean, parity gate proven live. One concern: `feed.endOfFeed` has no sourced
copy anywhere in the design/spec chain, shipped empty rather than invented — flagged above for the
UI-rendering phase to resolve.
**Concerns/Blockers:** `feed.endOfFeed` unsourced (see above) — not a blocker for this phase (types +
i18n only), but blocks whichever phase renders it until resolved.
