# Phase 06 — UI: the kudos card family

**Track:** A (presentational UI) · **Owner:** `momorph-ui-implementer` (activates
`momorph-implement-design`) · **Depends:** 05 · **Effort:** 2.5h · **test_policy:** `e2e-red-first`

## MoMorph refs:
- Sun* Kudos - Live board: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/MaZUn5xHXZ
- Clarifications: plans/260906-1945-kudos-live-board/clarifications.md
- testPolicy: e2e-red-first

**Goal** One card component that renders both variants the frame defines — the highlight slide and
the feed row — from a single `KudosCardView`.

## Context Links

- [plan.md](plan.md) · [phase-01](phase-01-foundation-and-integration-contract.md) (contract) · [phase-05](phase-05-ui-foundation-i18n-icons-hero-sidebar.md) (dictionary + icons)
- [test-contract.md](test-contract.md) § "Kudos card", § "Copy link", § "Supabase amendment"
- [clarifications.md](clarifications.md) § "Card fields (B.3 / C.3)", the campaign/pen decision, the heart-rules decision
- `e2e/kudos-live-board.spec.ts:351-434` (K-9, K-24, K-11) · `e2e/kudos-live-board-authed.spec.ts` (K-10, K-25)
- [UI study](../reports/researcher-260906-1958-repo-ui-conventions.md) § 6 (data-testid rules, `aria-*` present-or-absent)

## Overview

**Priority:** P1 · **Status:** delivered. The card carries 14 of the contract's hooks and is where
strict-mode locator collisions bite hardest — five of the six traps below live in this phase.

## Key Insights

1. **Only one element per card may carry `data-testid="sunner-badge"`.** K-9 does
   `card.getByTestId("sunner-badge")` then `toBeVisible()` — strict mode, so two matches throw.
   The frame shows a badge on both the sender and receiver chip. Resolution: the **sender's** badge
   carries `sunner-badge`; the receiver's carries `sunner-badge-receiver`. `getByTestId` matches
   exactly, so the contract's hook stays unique and unchanged — this is an additive suffix in the
   repo's own `<component>-<slug>` convention, not a contract change.
2. **`kudos-detail-link` must exist at most once inside the carousel.** K-12 asserts
   `toBeVisible()` on a carousel-scoped locator; five slides each rendering a detail link would be
   a strict-mode violation. Only the **active** slide renders it — which is also what the frame
   shows, since the flanks are faded and non-interactive. Phase 07 owns the active-slide decision;
   this phase takes `variant` and `isActive` as props and renders accordingly.
3. **`href` must be `/kudos/<digits>`.** K-12's regex is `/\/kudos\/\d+/`. `KudosCardView.id` is a
   number by contract (phase 01 § Key Insight 1); build the href as `` `/kudos/${id}` `` and never
   from any other field.
4. **Sender and receiver links both point at `/profile`** — exactly that, no query, no id (K-9
   asserts `toHaveAttribute("href", "/profile")`).
5. **The heart's disabled rule is `!canLike`**, which the view model has already resolved to
   "no session **or** the viewer is the sender". The card must not recompute it; recomputing is how
   K-24 or K-25 quietly breaks. `aria-pressed` reflects `likedByViewer` on first render.
6. **Line clamp differs by variant** — 3 lines in the highlight slide, 5 in the feed — and
   attachments render in the feed only, at most 5.
7. **Timestamps and heart counts arrive pre-formatted.** `sentAtLabel` is already
   `HH:mm - MM/DD/YYYY` and heart counts go through the frozen `formatHeartCount`. The card must
   not call `Intl` or `toLocaleString` — ICU differences between the server and browser runtimes
   would hydration-mismatch `1.000`.
8. **Hashtags are `<button>`s, not links** (they set the filter, per FR-403), at most 5 on one line
   then `…`. The click handler is a prop supplied by phase 07.
9. **`kudos-edit` renders only when `isOwnedByViewer`.** With a real viewer identity that is false
   for anon and for the fresh e2e user, so the pen will not appear in either test run. That is
   correct behavior, not a regression — the frame's state assumed the viewer was the sender.
   Recorded as a known visual difference for the tester's visual pass.
10. **No heading element inside a card** — `h1` belongs to the hero (K-0) and `h2` to the three
    sections (K-2/K-13/K-17). A card heading would break both strict locators.

## Requirements

**Functional:** FR-204 (all card fields, both variants), FR-402 (Copy Link + toast trigger),
FR-403 (hashtag chip sets the filter), FR-602/BR-003 surface (heart disabled state), BR-001 display
(`hearts` already includes the baseline).

**Non-functional:** every file ≤200 lines; one testid per element; `aria-pressed` is always present
on the heart (K-9 asserts the attribute exists, so it is `"true"`/`"false"`, not present-or-absent);
`aria-current`/`aria-hidden` on slides are present-or-absent, matching
`award-category-nav.tsx:31-34`; every arbitrary value carries `mm:{nodeId}`.

## Architecture

**Integration contract consumed** (frozen): `KudosCardView`, `SunnerView`, `KudosAttachmentView`,
`BadgeTier`, `ToggleKudosLike`, plus `formatHeartCount` from `lib/kudos/derive.ts`. Nothing added.

```
kudos-card.tsx          props { card, variant: "highlight"|"feed", isActive, copy,
                                 onHashtagClick, onCopyLink, toggleLike }
  ├─ sunner-chip.tsx    props { sunner, role: "sender"|"receiver", copy }   ← owns both badge testids
  ├─ kudos-hashtag-row  props { hashtags, onHashtagClick }
  ├─ kudos-attachments  props { attachments }                               feed variant only
  └─ kudos-card-actions props { card, copy, onCopyLink, toggleLike }        the only client concern
```

`kudos-card-actions.tsx` holds the heart button, the count, Copy Link, and the detail link. It
renders inside phase 07's client boundary, so it needs no `"use client"` of its own — but it must
never be imported by a server component (the sidebar does not render cards, so nothing does).

**Hooks emitted:** `kudos-card`, `kudos-sender`, `kudos-receiver`, `sunner-badge`,
`sunner-badge-receiver`, `kudos-time`, `kudos-campaign`, `kudos-body`, `kudos-image`,
`kudos-hashtag`, `kudos-heart`, `kudos-heart-count`, `kudos-copy-link`, `kudos-detail-link`,
`kudos-edit`.

**Out of scope:** the toast element itself and the clipboard call (07), filter state (07), the
carousel (07), spotlight (08), any data read (04/09), `kudos-empty` (07 owns both empty states).

## Related Code Files

**Create:** `app/kudos/_components/kudos-card.tsx` · `sunner-chip.tsx` ·
`kudos-card-actions.tsx` · `kudos-attachments.tsx` · `kudos-hashtag-row.tsx`
**Modify:** none
**Read only:** `lib/kudos/view-model.ts`, `lib/kudos/derive.ts` (both frozen),
`app/kudos/_components/kudos-icons.tsx` and the `kudos` dictionary namespace (phase 05),
`app/awards-information/_components/award-detail-card.tsx` (card layout precedent)
**Delete:** none

## Implementation Steps

1. Read the card's nodes live from the frame (`get_frame` on `MaZUn5xHXZ`): 64px avatars, 32px send
   glyph, 88px attachment thumbs, `#FFF8E1` card, `#FFF2C6` message box, `#D4271D` heart/hashtag.
2. `sunner-chip.tsx` — avatar (`next/image`), name link to `/profile`, department, badge with
   `title={badgeTooltip}`. `role="sender"` emits `kudos-sender` + `sunner-badge`;
   `role="receiver"` emits `kudos-receiver` + `sunner-badge-receiver`. Omit `title` when
   `badgeTooltip` is null (New Hero has no published copy).
3. `kudos-hashtag-row.tsx` — up to 5 `<button data-testid="kudos-hashtag">#{tag}</button>` then a
   literal `…` when there are more.
4. `kudos-attachments.tsx` — up to 5 `kudos-image` thumbs, feed variant only.
5. `kudos-card-actions.tsx` — `kudos-heart` (`aria-pressed`, `disabled={!card.canLike}`),
   `kudos-heart-count` via `formatHeartCount`, `kudos-copy-link` labelled `Copy Link`, and
   `kudos-detail-link` labelled `Xem chi tiết` rendered only when `variant === "highlight" && isActive`.
6. `kudos-card.tsx` — compose them in frame order: sender chip → send glyph → receiver chip →
   timestamp → campaign → message (clamped by variant) → attachments (feed) → hashtags → actions.
   Add `kudos-edit` when `card.isOwnedByViewer`.
7. `npm run typecheck && npm run lint`.

## Todo List

- [ ] `sunner-badge` on the sender only; `sunner-badge-receiver` on the receiver
- [ ] Both person links `href="/profile"` exactly
- [ ] `kudos-detail-link` only when highlight **and** active; href `` `/kudos/${id}` ``
- [ ] Heart: `aria-pressed` always present, `disabled={!card.canLike}`, no recomputed rule
- [ ] Count formatted by the frozen `formatHeartCount`; no `Intl` anywhere
- [ ] Clamp 3 (highlight) / 5 (feed); attachments feed-only, max 5
- [ ] Hashtags are buttons, max 5 then `…`
- [ ] `kudos-edit` gated on `isOwnedByViewer`
- [ ] No heading element inside the card
- [ ] Every file ≤200 lines; `mm:{nodeId}` on every arbitrary value
- [ ] `npm run typecheck && npm run lint` clean

## Success Criteria

- Typecheck and lint exit 0.
- Rendering one `KudosCardView` yields exactly one match for each of the 14 card hooks and exactly
  one `sunner-badge` — the strict-mode traps in Key Insights 1 and 2 are structurally impossible.
- No import from `lib/kudos/queries.ts`, `board-data.ts`, `app/kudos/_actions/**`, or
  `@/lib/supabase/*`.
- Every visual value traces to an `mm:{nodeId}` comment.
- Card assertions (K-9, K-11, K-12) stay red only because nothing mounts the card yet.

## Risk Assessment

| Risk | L×I | Countermeasure |
|---|---|---|
| Two `sunner-badge` matches per card → K-9 strict-mode failure | **High** × High | The suffix split in Key Insight 1, enforced by `sunner-chip.tsx` deriving the testid from its `role` prop — one code path, not two hand-written ones |
| Five `kudos-detail-link` matches → K-12 strict-mode failure | **High** × High | Rendered only when highlight **and** active; the condition lives in one place (step 5) |
| The card recomputes `canLike` and diverges from the server's rule | Med × **High** | `canLike` is consumed as-is; the card has no access to viewer identity to recompute it with |
| `toLocaleString("vi-VN")` used for the count and hydration-mismatching | Med × High | The frozen `formatHeartCount` is the only permitted formatter; ICU is never called |
| A `title` on New Hero invents copy that does not exist | Low × Med | `badgeTooltip` is nullable by contract and `title` is omitted when null |
| Card grows past 200 lines | Med × Low | Pre-split into five files before writing, per § Architecture |

**Rollback:** delete the five files. Nothing mounts them until phase 07 composes them and 09 wires
the page, so removal is clean at any point.

## Security Considerations

- No data access and no session read; the card renders the props it is handed.
- `message`, `campaign`, and hashtag text render as text nodes — never through
  `dangerouslySetInnerHTML`, even though the content is seeded and trusted today.
- `href` values are built from a numeric id and the fixed `/profile` literal, so no
  database string reaches a URL position.
- `toggleLike` is received as a prop and invoked with `card.id` only; the card never constructs a
  user identifier.
- Attachment and avatar `src` values are local `public/` paths from the seed; if a remote URL ever
  appears there, `next/image` will reject it rather than silently proxying it.

## Next Steps

Unblocks phase 07 (the board composes these cards). Phase 08 runs concurrently and does not depend
on this phase.
