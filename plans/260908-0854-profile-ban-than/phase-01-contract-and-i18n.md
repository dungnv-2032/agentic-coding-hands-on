# Phase 01 — Integration contract + `profile` i18n block

**Track:** Foundation (blocks every other phase) · **Owner:** `implementer` · **Effort:** 1h
**File ownership:** `lib/profile/profile-view-model.ts`, `lib/i18n/messages/dictionary.ts`,
`lib/i18n/messages/vi.ts`, `lib/i18n/messages/en.ts`, `lib/i18n/messages/vi-profile.ts`,
`lib/i18n/messages/en-profile.ts`

## Context Links

- `clarifications.md` § "Localization", § "Statistics card", § "Badge collection and hero tier"
- `spec/F006_ProfileBanThan/technical-spec.md` § 4.1, § 4.2, § 4.3
- `spec/SCR006_ProfileBanThan/spec.md` § 3 (the `Copy key` column is the key list)
- Prior art: `lib/kudos/view-model.ts` (F004's frozen contract, same role), `lib/i18n/messages/vi-kudos.ts`

## Overview

- **Priority:** P1 — nothing else can start.
- **Status:** complete
- Freeze the TypeScript boundary both tracks build against, and land the copy keys Track A renders.
  Zero behaviour, zero UI, zero queries.

## Key Insights

- F004 solved this exact problem with `lib/kudos/view-model.ts`: a **types-only** module with no
  runtime import, so Track A and Track B never import each other. Repeat it, do not reinvent it.
- The self/other split is **one data-level branch**: `stats !== null` iff `isSelf`. Encode that in
  the contract so no component can re-decide it (technical-spec SC-002).
- The sparse self view (signed in, no `sunners` row — A4, the *normal* e2e case) must be
  representable: `hero.sunnerId` is nullable and `hero.badge` is nullable.
- `hero.badge` is `null` when received == 0. `badgeTierFor(0)` returns `"New Hero"`, so the null
  must come from the **data layer's** count check, not from `badgeTierFor` (SCR006 § 7, GUI_009).
- Parity is enforced at **compile time** — a key in `vi-profile.ts` missing from `en-profile.ts` is
  a `tsc --noEmit` failure. That is stronger than GUI_008's requested runtime parity test, and it
  is the mechanism this repo actually has (`locales/*.json` does not exist here).

## Requirements

Functional: FR-002 (the `profile` `Dictionary` block), FR-205 (two badge-heading keys), FR-208 (two
distinct empty-copy keys), FR-206 (direction labels with count interpolation), FR-203/FR-204 (stat
labels + write-bar label with name interpolation).

Non-functional: types only in `profile-view-model.ts` — no `next/*`, no `@/lib/supabase/*`, no React;
it must be importable from a Client Component. Each file under 200 lines.

## Architecture

`lib/profile/profile-view-model.ts` (types only):

```ts
import type { BadgeTier, KudosCardView } from "@/lib/kudos/view-model";

export type FeedDirection = "received" | "sent";
export interface FeedCursor { sentAt: string; id: number }

export interface ProfileHeroView {
  /** null on the sparse self view (signed in, no `sunners` row — A4). */
  sunnerId: number | null;
  fullName: string;
  /** null hides the department text AND the separator dot together. */
  department: string | null;
  avatarUrl: string;
  /** null when received == 0 — the pill is hidden, not rendered as "New Hero". */
  badge: BadgeTier | null;
  badgeTooltip: string | null;
}

export interface ProfileStatsView {
  kudosReceived: number; kudosSent: number; heartsReceived: number;
  secretBoxOpened: number; secretBoxUnopened: number;
}

export interface ProfileFeedPage {
  cards: KudosCardView[];
  nextCursor: FeedCursor | null;
  hasMore: boolean;
}

export interface ProfileViewModel {
  isSelf: boolean;
  hero: ProfileHeroView;
  /** Non-null IFF `isSelf` — the single self/other branch (SC-002). */
  stats: ProfileStatsView | null;
  /** Non-null IFF NOT `isSelf` — the write-bar's `/kudos/new?receiverId=` target. */
  writeKudoTargetId: number | null;
  /** `sent` is null on another Sunner's profile: the number never leaves the server (SEC_001). */
  counts: { received: number; sent: number | null };
  /** Page 1 of the RECEIVED direction, read server-side (DEC-001). */
  initialPage: ProfileFeedPage;
}

export type FetchProfileKudosPage = (input: {
  targetSunnerId: number | null;
  direction: FeedDirection;
  cursor: FeedCursor | null;
}) => Promise<ProfileFeedPage>;
```

Copy shape added to `Dictionary` (`profile:`), mirroring `kudos:`'s nesting:

```
profile: {
  badges: { headingSelf, headingOther }
  stats:  { kudosReceived, kudosSent, heartsReceived,
            secretBoxOpened, secretBoxUnopened, secretBoxButton }
  writeBar: { label }            // carries "{name}"
  direction: { receivedLabel, sentLabel }   // each carries "{count}"
  feed: { emptyReceived, emptySent, endOfFeed }
}
```

Interpolation uses the same `replace("{name}", …)` idiom the board already uses — no new helper.

**Data flow:** none. This phase produces types and string constants only.

## Related Code Files

Create: `lib/profile/profile-view-model.ts`, `lib/i18n/messages/vi-profile.ts`,
`lib/i18n/messages/en-profile.ts`.
Modify: `lib/i18n/messages/dictionary.ts` (add the `profile` block to the interface),
`lib/i18n/messages/vi.ts` and `en.ts` (import + wire the block).
Delete: none.

## Implementation Steps

1. Write `lib/profile/profile-view-model.ts` exactly as above. Type-only imports.
2. Add the `profile` block to the `Dictionary` interface in `dictionary.ts`, placed after `kudos`.
3. Write `vi-profile.ts`. Verbatim copy, no improvising:
   - `stats.*` labels — copy the five strings already in `vi-kudos.ts`'s `sidebar.stats` (the visual
     study measured them identical) plus `secretBoxButton: "Mở Secret Box"`.
   - `feed.emptyReceived: "Hiện tại chưa có Kudos nào."` — verbatim from the board (`vi-kudos.ts`).
   - `feed.emptySent: "Bạn chưa gửi Kudos nào."` — clarifications § "Paging".
   - `badges.headingSelf: "Bộ sưu tập icon của tôi"`, `headingOther: "Bộ sưu tập icon"`.
   - `writeBar.label: "Gửi lời cảm ơn và ghi nhận đến {name}"`.
   - `direction.receivedLabel: "Đã nhận ({count})"`, `sentLabel: "Đã gửi ({count})"`.
4. Write `en-profile.ts` with the same key set (`My icon collection` / `Icon collection`, etc.).
5. Wire both into `vi.ts` / `en.ts`.
6. `npm run typecheck` and `npm run lint`.

## Todo List

- [ ] `lib/profile/profile-view-model.ts` created, types only, no runtime import
- [ ] `Dictionary.profile` added
- [ ] `vi-profile.ts` written, five stat labels copied from `vi-kudos.ts` not retyped
- [ ] `en-profile.ts` written with an identical key set
- [ ] `vi.ts` / `en.ts` wired
- [ ] `npm run typecheck` exit 0
- [ ] `npm run lint` exit 0

## Success Criteria

- `npm run typecheck` exits 0. Deleting one key from `en-profile.ts` makes it exit non-zero
  (verify once, then restore) — that is the observable proof GUI_008's parity requirement holds.
- `grep -c` shows the same key count in `vi-profile.ts` and `en-profile.ts`.
- `git diff --stat` touches only the six files above. No component file changed.

## Risk Assessment

| Risk | L×I | Countermeasure |
|---|---|---|
| Contract missing a field a track needs later | M × H | The field is added **here** and both tracks are notified once — never patched inside a track (F004's `view-model.ts` header states this rule; keep it) |
| Copy invented rather than transcribed | M × M | Every string above is sourced to a file or a clarifications section; `secretBoxButton` and the five stat labels come from shipped `vi-kudos.ts` |
| `profile-view-model.ts` accidentally imports a server module, breaking the client bundle | L × M | Type-only imports; `npm run build` in phase 10 would fail loudly if violated |

## Security Considerations

- The contract deliberately has **no** `userId`, no email, and no `auth_user_id` field — FR-603 is
  enforced by the shape, not by discipline. `counts.sent` is nullable so the number is *absent*, not
  hidden, on another Sunner's profile (SEC_001).

## Next Steps

- Unblocks phase 02 (tests assert against these key names) and phases 03–08.
- Dependencies: none.
