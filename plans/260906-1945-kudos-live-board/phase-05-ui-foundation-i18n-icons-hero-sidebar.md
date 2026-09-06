# Phase 05 — UI foundation: i18n, icons, assets, hero, sidebar

**Track:** A (presentational UI) · **Owner:** `momorph-ui-implementer` (activates
`momorph-implement-design`) · **Depends:** 01 · **Effort:** 2.5h · **test_policy:** `e2e-red-first`

## MoMorph refs:
- Sun* Kudos - Live board: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/MaZUn5xHXZ
- Clarifications: plans/260906-1945-kudos-live-board/clarifications.md
- testPolicy: e2e-red-first

**Goal** The screen's shared vocabulary — every string in both locales, every icon, the two image
exports — plus the two sections that need no client state: the hero and the sidebar.

## Context Links

- [plan.md](plan.md) · [phase-01](phase-01-foundation-and-integration-contract.md) (frozen contract) · [test-contract.md](test-contract.md) § Landmarks, § Sidebar
- [clarifications.md](clarifications.md) § "Resolved from source data" (hero, sidebar, palette), decision on assets
- [UI study](../reports/researcher-260906-1958-repo-ui-conventions.md) § 2 (Tailwind v4 + `mm:` comments), § 3 (dictionary), § 4 (icons/assets)
- Frame image: [design/kudos-live-board.png](design/kudos-live-board.png) · figma node `2940:13431`
- Patterns to copy: `lib/i18n/messages/vi-award-system.ts`, `lib/i18n/messages/dictionary.ts:26-152`,
  `app/awards-information/_components/award-system-icons.tsx`, `app/_components/icons.tsx`

## Overview

**Priority:** P1 · **Status:** delivered. Everything downstream in Track A imports this phase's
dictionary namespace and icon set, so it goes first and its API is then stable.

## Key Insights

1. **`388 KUDOS` ships as dictionary copy, not data.** K-13 asserts the literal string; the seed
   holds 50 kudos, so a real `count(*)` renders the wrong text. It is the frame's TEXT node with no
   queryable source, and inventing a settings table for it would be a fake data source (phase 03
   § Key Insight 7). Both locales carry `388 KUDOS` — a number is locale-independent.
2. **`h1` must be unique page-wide.** K-0 does `getByRole("heading", { level: 1 })` under strict
   mode. `HomeHeader` and `SiteFooter` contain no `h1` (verified), so the hero owns the only one:
   `Hệ thống ghi nhận và cảm ơn`.
3. **The compose bar is an `<a>`, not an input.** K-1 asserts its *accessible name* equals the
   placeholder sentence and K-22 asserts `href="/kudos/new"`. So it is a link styled as an input
   whose visible text is that sentence — never a real `<input placeholder>`.
4. **The Sunner search needs no client JavaScript.** `<form action="/profile" method="get">` with
   `<input name="q" maxlength="100">` submits the query to the placeholder route, as the settled
   decision requires. A server component with a plain GET form is the whole feature.
5. **`Mở Secret Box`'s accessible name must be exactly that**, so the gift glyph carries
   `aria-hidden="true"` and no `<title>`. The same applies to every decorative icon on the screen.
6. **Sidebar labels come from the dictionary; sidebar numbers come from the view model.**
   `SidebarCountsView` carries integers only. K-18 asserts the five labels in order with
   `toContainText`, so the vi copy must be verbatim, including the trailing colon.
7. **`Số tim bạn nhận được:` renders the `x2` flame glyph** — displayed, never simulated. The
   special-day ×2 rule stays out of scope (clarifications § Unresolved questions 2).

## Requirements

**Functional:** FR-201 (hero: title, wordmark, compose bar, search), FR-207 + BR-004 (five sidebar
rows, Secret Box link, gift leaderboard, `Chưa có dữ liệu` empty state).

**Non-functional:** dual-locale, compile-enforced by extending `Dictionary`; every file ≤200 lines;
every arbitrary Tailwind value carries an `mm:{nodeId}` comment; icons are inline SVG with
`fill="currentColor"`, never `<img>`; no `"use client"` in this phase — all four components are
server components.

## Architecture

**Integration contract consumed** (frozen, phase 01): `SidebarCountsView`, `GiftRowView`, and the
`kudos` slice of `Dictionary`. This phase adds no field to the contract.

```
kudos-hero.tsx      ← props: { copy }                       server
kudos-sidebar.tsx   ← props: { copy, counts, gifts }        server
gift-leaderboard.tsx← props: { copy, gifts }                server
kudos-icons.tsx     ← inline SVG set, no props but className shared by every Track A phase
```

**Icon set** (one file, all inline, `currentColor`): pen, search, send, heart, link, chevron-down,
gift, flame, expand, pan/zoom, carousel-arrow, pager-arrow.

**Assets** (`public/images/kudos/`): `kv-background.png` (`MM_MEDIA_KV Background`, 1440×512),
`spotlight-canvas.png`, `sample-avatar.png`, `sample-attachment.png`. The last two are the single
committed sample per role (assumption A3) and phase 03's seed already stores exactly these two
paths — do not rename them. The `KUDOS` wordmark reuses the shipped
`public/images/home/kudos-logo.svg`; export nothing for it.

**Hooks emitted:** `kudos-compose`, `sunner-search`, `kudos-sidebar`, `sidebar-stat` (×5, in
order), `secret-box-button`, `gift-leaderboard`, `gift-row`, `gift-empty`.

**Out of scope for this phase:** kudos cards (06), filters/carousel/feed (07), spotlight (08),
`app/kudos/page.tsx` and any Supabase read (09), the `HomeHeader`/`SiteFooter` chrome (composed
unchanged in 09), `FloatingWidget` and `KudosPromo` (this screen renders neither).

## Related Code Files

**Create:** `lib/i18n/messages/vi-kudos.ts` · `lib/i18n/messages/en-kudos.ts` ·
`app/kudos/_components/kudos-icons.tsx` · `kudos-hero.tsx` · `kudos-sidebar.tsx` ·
`gift-leaderboard.tsx` · the four files under `public/images/kudos/`
**Modify:** `lib/i18n/messages/dictionary.ts` (add the `kudos` namespace) · `vi.ts` · `en.ts`
(wire it in)
**Read only:** `lib/kudos/view-model.ts`, `design/kudos-live-board.png`, the MoMorph frame
**Delete:** none

## Implementation Steps

1. Pull the frame's live values through MoMorph MCP (`get_frame` on `MaZUn5xHXZ`) — every hex,
   size, radius and spacing comes from there, none is guessed.
2. Add the `kudos` namespace to `Dictionary`: hero (title, composePlaceholder, searchPlaceholder),
   section eyebrow + the three section titles, filter labels, card labels (`Copy Link`,
   `Xem chi tiết`, empty state), the four badge tier names, the three hoa-thị sentences, spotlight
   (count literal, search placeholder, `Pan/Zoom`, ticker sentence template, empty state), sidebar
   (five labels, `Mở Secret Box`, gift heading, `Chưa có dữ liệu`), and both toast strings
   (`Link copied — ready to share!` and a copy-failure message — see phase 07 § Key Insight 5).
3. Create `vi-kudos.ts` with copy transcribed verbatim from clarifications, and `en-kudos.ts` with
   a faithful translation. Wire both into `vi.ts` / `en.ts` as `kudos: viKudos` / `kudos: enKudos`.
4. Build `kudos-icons.tsx` with the twelve glyphs, each with `aria-hidden="true"` and sized by the
   caller's className. Split into a second file only if it approaches 200 lines.
5. Export the four images at the frame's dimensions into `public/images/kudos/`.
6. Build `kudos-hero.tsx`: KV background via `next/image` with explicit width/height and a real
   `alt`; the `h1`; the wordmark; the compose `<a>` (Key Insight 3); the GET form (Key Insight 4).
7. Build `kudos-sidebar.tsx` and `gift-leaderboard.tsx` per § Architecture. The gift list scrolls
   independently; the five stat rows render in the contract's exact order.
8. `npm run typecheck && npm run lint`. A key present in `vi-kudos.ts` but missing from
   `en-kudos.ts` fails typecheck — that is the intended gate, not a nuisance.

## Todo List

- [ ] `Dictionary` extended; `vi-kudos.ts` + `en-kudos.ts` complete and wired into `vi.ts`/`en.ts`
- [ ] vi copy verbatim, including trailing colons on the five sidebar labels
- [ ] `spotlight.count` = `388 KUDOS` in both locales
- [ ] Twelve inline `currentColor` glyphs, all `aria-hidden`
- [ ] Four images exported at frame dimensions; sample paths match phase 03's seed exactly
- [ ] Hero: single `h1`, compose `<a href="/kudos/new">` with the sentence as its accessible name, GET form to `/profile` with `maxlength="100"`
- [ ] Sidebar: five `sidebar-stat` rows in order, flame glyph on the hearts row, `secret-box-button` accessible name exactly `Mở Secret Box`
- [ ] `gift-leaderboard` with heading, `gift-row`s, `gift-empty`
- [ ] Every arbitrary Tailwind value carries `mm:{nodeId}`; every file ≤200 lines
- [ ] `npm run typecheck && npm run lint` clean

## Success Criteria

- `npm run typecheck` and `npm run lint` exit 0; removing one `en-kudos.ts` key makes typecheck
  fail (the dual-locale gate is real, not decorative).
- Every component renders from props alone — no import from `lib/kudos/queries.ts`,
  `board-data.ts`, or `@/lib/supabase/*`. Track A must not reach into Track B.
- Every visual value traces to a frame node named in an `mm:` comment; a reviewer can check any
  one of them against MoMorph.
- No file exceeds 200 lines; no `"use client"` was added.
- The kudos e2e assertions are unchanged — nothing is mounted until phase 09.

## Risk Assessment

| Risk | L×I | Countermeasure |
|---|---|---|
| A guessed hex or spacing value | Med × High | Values are read live from the frame in step 1; the `mm:{nodeId}` comment makes any guess visible in review |
| `kudos-icons.tsx` grows past 200 lines with twelve glyphs | Med × Low | Split into `kudos-icons.tsx` + `kudos-glyphs.tsx` at the 200-line line; both stay this phase's files |
| The gift glyph adds text to `secret-box-button`'s accessible name and K-19 fails | Med × Med | Every glyph carries `aria-hidden="true"` and no `<title>`, enforced in step 4 |
| A second `h1` appears later in Track A and breaks K-0's strict locator | Med × High | Stated here and repeated in 06/07/08: sections use `h2`, cards use no heading element |
| Sample image paths renamed, orphaning phase 03's seed strings | Low × Med | The four filenames are frozen in both phase files; a rename is an orchestrator decision |
| EN translation drifts from the design intent | Low × Low | vi is authoritative and verbatim; en is a faithful translation, and no test asserts EN copy |

**Rollback:** delete the created files and revert the three dictionary edits. Nothing renders this
phase's output until 09, so the app is unaffected at every point.

## Security Considerations

- No data access, no session read, no Server Action in this phase — props only.
- The GET form submits to `/profile`, a first-party placeholder route; no external target and no
  user content is echoed back into the DOM by this phase.
- `next/image` sources are local `public/` paths only — no remote loader, so no new host is
  admitted to the image pipeline.
- No copy string interpolates anything from the database, so no untrusted value reaches the
  dictionary layer.

## Next Steps

Unblocks phase 06 (cards) and phase 08 (spotlight), which may run concurrently. Track B is running
in parallel and is not waiting on this phase.
