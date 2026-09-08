# Phase 08 — Track A: KUDOS section (direction dropdown, feed, infinite scroll)

`mode: screen` · `testPolicy: e2e-red-first` · `momorph-ui-implementer`
Screen: `3FoIx6ALVb` (`fileKey 9ypp4enmFmdK3YAFJLIu6C`), frame node `362:5037`, regions C + D.

## 1. Files touched

| File | Lines | Role |
|---|---:|---|
| `app/profile/_components/kudos-direction-section.tsx` | 199 | Client boundary — state + wiring. Header (`mm:362:5084`), SM-001 state machine, request-id race guard, hashtag push, Copy-Link toast |
| `app/profile/_components/profile-direction-menu.tsx` | 149 | `mm:362:5089` trigger + its listbox; owns the option set (FR-206/SEC_001), labels, open/close, outside-dismiss |
| `app/profile/_components/profile-kudos-feed.tsx` | 112 | `mm:362:5091` single-column card feed; sentinel, empty copy, end-of-feed status region |

Nothing outside `ownedFiles` was created, edited or deleted. `app/profile/page.tsx` (09),
phase 07's five components, `lib/profile/*`, `app/profile/_actions/`, `app/kudos/_components/*`
and every `e2e/*` file are untouched. A throwaway Playwright probe was created under
`.probe-tmp/` and deleted in the same step (see § 6); `git status` shows no trace of it.

### Deviation from the phase file's stated split — recorded, not silent

Phase 08 describes `profile-direction-menu.tsx` as "(listbox)" and `kudos-direction-section.tsx`
as "(state + wiring)". The trigger button (`mm:362:5089`) and the option-list construction ended
up in the **menu** file instead of the section. Reason: with the trigger, `TRIGGER_CLASS`, the
option/label builder and the header JSX all in the section, that file measured **287 lines** —
past the phase's own hard `< 200` criterion — and the only alternatives were a fourth file
(outside `ownedFiles` ⇒ BLOCKED) or gutting the design-provenance comments the neighbouring
`app/kudos/_components/*` files all carry.

The three mandated paths are unchanged, all three are under 200 lines, and the resulting split is
the one F004 already uses: `kudos-filter-bar.tsx` owns trigger + open-state, `kudos-filter-menu.tsx`
owns the panel — here both halves of one dropdown sit in one file because the panel node
(SCR006 C.3.1) does not exist in the frame at all and has nothing of its own to own.

### Deviation from the stated prop list — `onCopyLink` / `onHashtagClick`

The phase's integration contract lists `onCopyLink` and `onHashtagClick` on the section's props.
They are **resolved inside the section** instead. Reason: phase 09 renders
`KudosDirectionSection` directly from `app/profile/page.tsx`, a Server Component, and this Next
version throws when a function prop that is not a Server Function crosses the boundary
(`node_modules/next/dist/docs/01-app/02-guides/server-and-client-boundary.md`: "Passing a
function as a prop from a Server Component to a Client Component throws. An event handler like
`onClick` cannot cross."). Accepting them as props would be a contract phase 09 could not honour.
They still exist as props one level down, on `ProfileKudosFeed`, exactly as
`all-kudos-feed.tsx` takes them from `kudos-board.tsx`.

**Phase 09 prop contract (what `page.tsx` must pass):**

```tsx
<KudosDirectionSection
  targetSunnerId={/* resolved target id, may be null on the sparse self view */}
  isSelf={vm.isSelf}
  counts={vm.counts}
  initialPage={vm.initialPage}
  copy={{ eyebrow: dict.kudos.eyebrow, direction: dict.profile.direction,
          feed: dict.profile.feed, card: dict.kudos.card, toast: dict.kudos.toast }}
  fetchPage={fetchProfileKudosPage}   // phase 05 Server Action
  toggleLike={toggleKudosLike}        // F004 action, untouched
/>
```

`KudosDirectionCopy` is exported from `kudos-direction-section.tsx` so phase 09 can type the
object rather than shape it by guesswork.

## 2. Design values used, with their source

Every value below came from a live MCP read this session, or from
`reports/momorph-visual-study.md` where the prompt said to reuse rather than re-measure. Nothing
is guessed.

| Element | Value | Source |
|---|---|---|
| Section wrapper `mm:362:5083` | `flex-column`, `gap:40px`, `align-items:center`, 1440 wide | `get_node(362:5083)` this session |
| Header `mm:362:5084` | `968×129`, `padding:0 144px`, `flex-column`, `gap:16px`, inner 680px | `query_section(362:5084)` this session |
| Eyebrow `mm:362:5085` | `24px/32px/700` Montserrat, white, `textAlign:left`, 680px, `"Sun* Annual Awards 2025"` | `query_section(362:5084)` |
| Divider `mm:362:5086` | `680×1`, `rgba(46,57,64,1)` = `#2E3940` | `query_section(362:5084)` |
| Header row `mm:362:5087` | `680×64`, `flex-row`, `gap:32px`, `space-between`, `items-center` | `query_section(362:5084)` |
| Heading `mm:362:5088` | `57px/64px/700`, `letter-spacing:-0.25px`, `#FFEA9E`, 218px, `"KUDOS"` | `query_section(362:5084)` |
| Trigger `mm:362:5089` | `1px solid #998C5F`, `bg rgba(255,234,158,0.10)`, `radius 4px`, `padding 16px 24px`, `gap 8px`, `align-self:stretch`, x 897→1060 | `get_node(362:5089)` this session |
| Trigger label frame `mm:I362:5089;186:2758` | `gap:4px`, `83×24` ⇒ 16px/24px/700, tracking `0.15px`, white | `get_node(I362:5089;186:2758)` this session |
| Trigger chevron `mm:I362:5089;186:2761` | `24×24` INSTANCE "Button down" | `get_node(362:5089)` childIds |
| Feed gutter `mm:362:5090` | 1440 wide, `padding:0 144px` | `get_node(362:5090)` this session |
| Feed `mm:362:5091` | `680px`, `flex-column`, `gap:24px`, `align-items:flex-start`, single column | `get_node(362:5091)` this session |
| Content centring | 680px centred on 1440 (startX 380 → endX 1060) | measured positions, both `5085` and `5091`; matches the visual study |
| Panel + option tokens | `bg #00070C`, `1px #998C5F`, `radius 8px`, `padding 6px`; option `p-4`, `radius 4px`, gold glow | reused verbatim from `kudos-filter-menu.tsx` (`mm:563:8026` / `mm:186:1496`) — C.3.1 has no node |
| Card fill / radius | `#FFF8E1`, `radius 24px` | already shipped at `kudos-card.tsx:114` + `VARIANT_SHELL.feed` (clarifications AMEND-3) — reused, not re-tokened |

**Copy sources** — `kudos.eyebrow` for C.1 and a bare `"KUDOS"` literal for C.2, both exactly as
`docs/screens/SCR006_ProfileBanThan/spec.md` § 3 dictates ("Tái dùng key `kudos.eyebrow`" /
"Tĩnh, không cần key riêng"). Direction labels and all three feed strings come through
`Dictionary["profile"]`; counts render via `formatHeartCount`, never `toLocaleString`.

**`feed.endOfFeed` is populated, not empty.** The task prompt warned it was deliberately `""`;
that is stale. `lib/i18n/messages/vi-profile.ts:58` now carries `"Bạn đã xem hết Kudos."` and
`en-profile.ts:34` `"You've seen all the Kudos."`, with a comment recording the orchestrator's
2026-09-08 decision, and `e2e/fixtures/profile-constants.ts:42` asserts the vi string. So
`profile-feed-end` renders visible text and nothing had to be invented here.

**Behaviour the frame does not capture — all honoured:**

- DEC-001 — `received` is the initial `direction`; the frame's `Đã gửi (5)` was ignored.
- SEC_001 — `counts.sent === null` ⇒ the `Đã gửi` label is never constructed, so the string is
  absent from the DOM rather than hidden by CSS. The option array is built inside
  `profile-direction-menu.tsx` from `counts` + `isSelf`.
- FR-403 — a switch clears cards, cursor and `hasMore` synchronously, requests `cursor: null`,
  and only assigns `direction` (hence the trigger label) after the page resolves.
- DEC-002 — re-picking the active option closes the menu and returns before any fetch.
- Double-click / overlapping switch — `requestIdRef` is bumped per request and any response whose
  id is not current is discarded; `inFlightRef` (a ref, so it is checked synchronously) rejects a
  duplicate sentinel intersection in the same tick.
- GUI_007 — no Spam chip: `KudosCard` has no such element, so there is nothing to suppress.
- K-25 — no optimistic heart. `toggleLike` is passed straight to `KudosCard` and the rendered
  count stays whatever `kudos-card-actions.tsx` gets back from the server.

**Two authored choices, flagged because the frame is silent on both:**

1. The dropdown panel is anchored `right-0` with `w-max min-w-full`, not the board's `left-0 w-64`
   — the trigger sits at the right edge of the 680px column, so a left-anchored 256px panel would
   hang past the content. C.3.1 has no node to contradict this.
2. While `switching`/`loading-more` the feed renders **no** placeholder. SCR006 § UI States records
   the `loading` visual as "TBD (draft) chưa quyết định chi tiết hiển thị chờ", so a skeleton or
   spinner would be invented design. This also keeps the end-of-feed message off screen while
   page 1 of the new direction is in flight.

A third, smaller one: on a `fetchPage` rejection the feed forces `hasMore = false` and settles.
No feed error state exists anywhere in the spec or the test cases, and leaving `hasMore` true
would keep the sentinel mounted and re-fire the failing request on every scroll.

## 3. Checks

| Check | Command | Exit |
|---|---|---|
| Typecheck | `npm run typecheck` (`tsc --noEmit`) | **0** |
| Lint | `npm run lint` (`eslint`) | **0** — 30 warnings, all in `e2e/*.spec.ts` (`homepage-authed`, `homepage`, `kudos-live-board`, `profile`, `viet-kudo`); **zero** in `app/profile/_components/*` |
| File size | `wc -l` | 199 / 149 / 112 — all `< 200` |
| Asset coverage | not applicable — see below | — |

**Asset coverage.** `list_media_nodes(3FoIx6ALVb)` returns 30 media nodes; **none** of them is in
region C, and every one inside region D (`MM_MEDIA_Avatar` 64×64, `MM_MEDIA_Sample Image` 88×88 on
the four card instances `3127:24169`, `3127:24455`, `1949:12834`, `3127:22945`) belongs to the
already-shipped `SunnerChip` / `KudosAttachments` subtree and is data-driven (real avatar and
attachment URLs), not a static asset. The one glyph in scope,
`mm:I362:5089;186:2761` "Button down", is an INSTANCE rather than an `MM_MEDIA_*` node and is
served by the existing inline `IconChevronDown` in `kudos-icons.tsx` — already `currentColor`, so
code-rules § 2a is satisfied by prior art. This plan has no `data/assets.md`, so
`validate_coverage.py` has nothing to validate. No asset was downloaded and none was needed.

**Lint note on `npm run lint`:** the pre-existing warning count is 30, not the 28 the task prompt
quoted. All 30 predate this phase (`e2e/*.spec.ts` only) and the delta is in files I do not own.

## 4. Acceptance checklist (phase 08 "Done when")

- [x] `npm run typecheck` exit 0
- [x] `npm run lint` exit 0
- [x] All three files `< 200` lines (199 / 149 / 112)
- [x] `profile-direction-trigger` present
- [x] `profile-direction-option` present
- [x] `profile-feed` present, and rendered **even when empty** so `FUN_012`'s
      `expect(feed).toContainText(...)` has a container to match inside
- [x] `profile-feed-empty`, `profile-feed-end`, `profile-feed-sentinel` present
- [x] On `isSelf === false` no `Đã gửi` string is constructed anywhere
- [x] Re-picking the active option fires zero requests
- [x] No duplicate `kudos-card` key after switching direction twice — a switch replaces `cards`
      wholesale and stale responses are discarded by request id
- [x] `KudosCard` reused outright with `variant="feed"`; `use-infinite-feed.ts` unmodified
- [x] No Supabase or `lib/profile/*` runtime import (types only, from the phase-01 contract)
- [x] No optimistic heart
- [ ] Browser evidence — phase 10 owns it (not attempted here, correctly)

## 5. RED / GREEN status

RED evidence was validated before any edit: `plans/260908-0854-profile-ban-than/evidence/red-run.log`
exists (60,723 bytes) and its tail lists `TC_WEB_PROFILE_FUN_009` through `FUN_013`, `SEC_001` and
`GUI_006` among the failures, with `84 passed` alongside — a genuine assertion failure caused by
the `ComingSoon` placeholder, not a dependency, config or server-start failure. Test files were
neither read for the purpose of shaping assertions nor modified.

GREEN is **not** claimed and could not be: `app/profile/page.tsx` still renders `ComingSoon`
(phase 09) and `fetchProfileKudosPage` does not exist yet (phase 05). The suite was deliberately
not run.

## 6. Unresolved questions

1. **`TC_WEB_PROFILE_FUN_009` and `FUN_011` look unpassable as written, for a reason no
   implementation can fix.** Both open the dropdown and then call
   `page.getByText("Đã nhận")` — `FUN_009` asserts `.toBeVisible()`, `FUN_011` calls `.click()`.
   With the menu open, the string `Đã nhận` is present in **two** places by design: the trigger
   (which `FUN_009` itself asserts on the line before, `expect(trigger).toContainText(received)`)
   and the received option. `getByText` defaults to `exact: false` — substring, case-insensitive
   (`node_modules/playwright-core/types/types.d.ts:3256`) — and a locator resolving to two
   elements is a strict-mode violation (same file, `:15968`).
   Making the two strings differ is not available: `docs/screens/SCR006_ProfileBanThan/spec.md`
   § 3 assigns the *same* `direction.receivedLabel` key to C.3 (trigger) and C.3.1 (option), and
   DEC-002 requires the active option to stay in the list.
   `FUN_010` and `FUN_012` are unaffected — they only ever `getByText("Đã gửi")` while the trigger
   reads `Đã nhận`, so those resolve to one element.
   **I could not execute this to confirm** — `browserType.launch` fails in this WSL2 sandbox
   ("Target page, context or browser has been closed"), and browser evidence is not mine to
   produce. Handing it to phase 10's tester: if it reproduces, the fix belongs in the test
   (`.getByTestId("profile-direction-option").filter({ hasText: ... })`, or
   `getByRole("option", { name: ... })`), and it is a test-precision fix, **not** a weakening —
   it asserts the option specifically instead of "some element on the page". It must not be
   resolved by changing the trigger or the option copy.
2. **`profile-feed-end` on a short first page.** SCR006 § UI States words the end-of-feed trigger
   as "`hasMore === false` sau một lần tải" (after one load). I render it whenever
   `!hasMore && cards.length > 0`, which includes an initial page that already fits — e.g. 3
   received Kudos shows "Bạn đã xem hết Kudos." without the user scrolling. That reads correctly
   to me and satisfies `FUN_013` (whose end-message assertion is conditional anyway), but if the
   intent was "only after a *subsequent* fetch", it is a one-line change in
   `profile-kudos-feed.tsx`. Not guessed silently.
3. **The 30 vs 28 pre-existing lint warnings** (§ 3). Worth a glance from whoever owns the e2e
   files, in case two warnings landed after the number in the task prompt was recorded.
