# Phase 04 — Repoint the three call sites, extract the shared card mapper

**Track:** B · **Owner:** `implementer` · **Effort:** 1.5h
**File ownership:** `lib/kudos/queries.ts`, `lib/kudos/board-data.ts`,
`lib/kudos/map-kudos-card.ts` (new), `lib/kudos/view-model.ts`,
`app/kudos/_actions/toggle-kudos-like.ts`

## Context Links

- Phase 03 (`kudos_readable` must exist and be typed before this starts)
- `clarifications.md` § "Security — the finding that changes the design" (the three call sites),
  § "Card shape in the feed", § "My own Sent list and my own anonymous Kudos"
- `spec/F006_ProfileBanThan/technical-spec.md` § 4.2 "Ba call site được trỏ lại view", § 3.3 BR-005
- Code: `lib/kudos/queries.ts:51-67`, `lib/kudos/board-data.ts:76-118`,
  `app/kudos/_actions/toggle-kudos-like.ts:26, 73`

## Overview

- **Priority:** P1 — FR-001's second half. The board must be byte-for-byte equivalent afterwards.
- **Status:** pending
- Point every Kudos read at `kudos_readable`, absorb the flat-sender shape change, and lift the
  row→card mapper out of `board-data.ts` so the profile feed reuses it instead of copying it.

## Key Insights

- **The sender stops being an embed and becomes five flat columns.** `KudosFeedRow.sender:
  SunnerEmbed` becomes `sender_id: number | null`, `sender_full_name: string | null`,
  `sender_avatar_url: string | null`, `sender_kudos_received_baseline: number | null`,
  `sender_department_name: string | null`. The **receiver embed is untouched** — `receiver_id` is
  still a plain column, so `receiver:sunners!kudos_receiver_id_fkey(...)` keeps resolving (probed).
- **Nullability is the mask.** For an anonymous row read by anyone but its author, all five are
  `null` — and `board-data.ts` already routes exactly those rows through
  `toAnonymousSenderView(...)`, so it never touches them. The narrowing is `anonymousSenderLabel ===
  null`, which the existing code already computes. No cast, no `!`.
- **`canLike` / `isOwnedByViewer` keep their meanings for free**, because the view reveals
  `sender_id` to the author. Do not "fix" them.
- **`board-data.ts` is 188 lines and the mapper must be shared.** Extracting the row→`KudosCardView`
  mapper into `lib/kudos/map-kudos-card.ts` is what keeps both files under the 200-line cap **and**
  is the only way the profile feed can be "the board's mapper, unchanged" rather than a copy (DRY).
- **The profile Sent list needs one behaviour the board must not have:** for my own anonymous Kudo,
  show *me* as author (clarifications § "My own Sent list"). That is a mapper **option**, defaulted
  off, not a branch inside the board.
- `kudos_readable` lands under `Database["public"]["Views"]`, so `queries.ts`'s
  `Row<T extends keyof …["Tables"]>` helper does not reach it. The file already declares explicit
  interfaces and pins them with `.returns<T[]>()` — keep doing that.

## Requirements

Functional: FR-001 (call sites), BR-005 (one mapper, two surfaces), FR-602 (reveal-own-anonymous as
an option). Non-functional: **no observable change to `/kudos`**; every file under 200 lines; no
new dependency; `toggleKudosLike`'s behaviour unchanged.

## Architecture

```
kudos_readable ──► queries.ts:fetchKudos            (flat sender cols + 4 embeds)
                        │
                        ▼
        map-kudos-card.ts:toKudosCardView(row, ctx, opts)   ◄── NEW, shared
                        │                                   opts.revealOwnAnonymous
        ┌───────────────┴───────────────┐
        ▼                               ▼
 board-data.ts (F004 board)      profile-queries.ts (phase 05)
```

`toKudosCardView(row, ctx, opts)`:
- `ctx`: `{ viewerSunnerId, viewerIsAuthenticated, likedKudosIds, receivedCountBySunnerId }`
- `opts.revealOwnAnonymous` (default `false`): when `true` **and** the row is anonymous **and**
  `row.sender_id === ctx.viewerSunnerId`, produce the real `SunnerView` and
  `anonymousSenderLabel: null`, while `sentAnonymously` stays `true`.

`KudosCardView` gains one additive field: `sentAnonymously: boolean` — the internal marker FR-602
asks for. **It renders nothing.** The design frame has no such element and AMEND-3 mandates full card
reuse, so inventing a visible chip would be inventing design data. Observability comes from Sent-list
count parity, not from a badge.

**Data flow (unchanged shape, new source):** PostgREST → masked rows → one mapper → `KudosCardView[]`
→ `KudosCard`. The heart write path still reads its authoritative `{liked, hearts}` from the database
after the write (K-25); nothing here makes it optimistic.

## Related Code Files

Create: `lib/kudos/map-kudos-card.ts`.
Modify: `lib/kudos/queries.ts` (`.from("kudos")` → `.from("kudos_readable")` at line 53, new
`KudosFeedRow` shape), `lib/kudos/board-data.ts` (delegate to the mapper, drop the inlined version),
`lib/kudos/view-model.ts` (add `sentAnonymously`),
`app/kudos/_actions/toggle-kudos-like.ts` (lines 26 and 73 → `kudos_readable`).
Delete: none.

## Implementation Steps

1. `view-model.ts`: add `sentAnonymously: boolean` to `KudosCardView` with a comment saying it is an
   internal marker with no visual surface in this commission.
2. `queries.ts`: rewrite `KudosFeedRow`'s sender half as the five flat nullable columns; change the
   select string to list them; change `.from("kudos")` to `.from("kudos_readable")`. Keep the four
   embeds verbatim, including the `kudos_receiver_id_fkey` hint. Keep `.returns<KudosFeedRow[]>()`.
3. Create `map-kudos-card.ts`: move `toSunnerView`, `toAnonymousSenderView`, `heartsOf`,
   `ANONYMOUS_FALLBACK_LABEL` and the row→card body out of `board-data.ts` **unchanged in
   behaviour**, then add the `revealOwnAnonymous` option and `sentAnonymously`.
4. `board-data.ts`: import and call the mapper; keep the received-count map, the sidebar counts, the
   gift/spotlight mapping and the returned `KudosBoardViewModel` exactly as they are.
5. `toggle-kudos-like.ts`: change both `.from("kudos")` to `.from("kudos_readable")`. Change nothing
   else — not the BR-003 check, not `refresh()`, not the error handling.
6. `npm run typecheck` and `npm run lint`.
7. Verify line counts: `wc -l lib/kudos/board-data.ts lib/kudos/map-kudos-card.ts lib/kudos/queries.ts`
   — each < 200.
8. Confirm F004 stayed green by running only its projects:
   `npx playwright test --project=anon --project=kudos-authed`.

## Todo List

- [ ] `sentAnonymously` added additively to `KudosCardView`
- [ ] `KudosFeedRow` sender half is five flat nullable columns
- [ ] `queries.ts:53` reads `kudos_readable`; receiver embed hint untouched
- [ ] `map-kudos-card.ts` created; behaviour moved, not rewritten
- [ ] `revealOwnAnonymous` option present and defaulted `false`
- [ ] `board-data.ts` delegates; view model output byte-identical for the board
- [ ] `toggle-kudos-like.ts:26` and `:73` read `kudos_readable`; nothing else changed
- [ ] All touched files < 200 lines
- [ ] `npm run typecheck` / `npm run lint` exit 0
- [ ] F004's board + kudos-authed projects pass

## Success Criteria

- `grep -rn '\.from("kudos")' lib app` returns **nothing**.
- `grep -rn '\.from("kudos_readable")' lib app` returns exactly three call sites.
- `npx playwright test --project=anon --project=kudos-authed` exits 0 — F004's 27 board assertions
  and F005's compose suite unchanged. In particular K-24 (every heart disabled for anon), K-9
  (sender/receiver/badge on the first card) and the heart-persists-across-reload case still pass.
- On `/kudos`, the seeded anonymous row (phase 03) renders the alias `Ẩn danh` with no department,
  no tier badge and no `/profile` link — `AnonymousSenderChip`, not `SunnerChip`.
- `board-data.ts` contains no row→card mapping code; the mapper is imported.

## Risk Assessment

| Risk | L×I | Countermeasure |
|---|---|---|
| Implementer restores the sender embed to make types easier, hits `PGRST200`, drops the hint, ships the **receiver** as the sender | M × **H** | Phase 03 § Key Insight 3 and the probe report are required reading; success criterion in phase 03 asserts the right person; there is no sender hint in the new select string to drop |
| Behaviour drifts during the mapper extraction | M × H | Move first and run F004's suite green **before** adding the `revealOwnAnonymous` option — two commits, not one |
| A `!` or `as` is used to silence the new nullability | M × M | The narrowing already exists (`anonymousSenderLabel === null`); lint/review rejects non-null assertions here |
| `toggle-kudos-like.ts` gets "improved" while open (optimistic flip) | L × **H** | K-25: the flip was proven broken and reverted. Only the two table names change; the diff must be two lines |
| `board-data.ts` grows past 200 lines instead of shrinking | L × M | Step 7 measures it |

**Rollback.** Revert these five files **together with** phase 03's migration; a repointed read path
against a dropped view is a dark board. Single revert commit, both phases.

## Security Considerations

- `resolveViewer().userId` still never leaves the server; the mapper receives `viewerSunnerId` only.
- `revealOwnAnonymous` must be settable **only** from server code that has already established the
  caller's identity from the session — never from a client argument. Phase 05 enforces this by
  resolving `callerSunnerId` inside the server action.
- The mask is not re-implemented in TypeScript. If `sender_full_name` arrives `null`, the correct
  response is the anonymous view — never a second lookup to recover the name.

## Next Steps

- Blocks phase 05 (needs the mapper and the flat row type).
- Hands `lib/kudos/{queries,board-data,view-model}.ts` ownership to phase 09 on completion.
