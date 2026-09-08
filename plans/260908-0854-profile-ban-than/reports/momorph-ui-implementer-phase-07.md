# Phase 07 — Track A: keyvisual, hero, badge row, stats card, write-Kudo bar

`mode: screen` · `testPolicy: e2e-red-first` · MoMorph `9ypp4enmFmdK3YAFJLIu6C` / `3FoIx6ALVb`

RED gate honoured read-only: phase 02's `redExitCode: 1` / 24 failures on
`expect(getByTestId('profile-hero')).toBeVisible()` (`evidence/red-run.log`,
`reports/tester-phase-02-red.md`). No test file was created, edited, or run here.

## Files touched

| File | Lines | What it renders |
|---|---|---|
| `app/profile/_components/profile-keyvisual.tsx` | 53 | `mm:I1210:12622;2167:5140` — 512px banner + gradient wash |
| `app/profile/_components/profile-hero.tsx` | 114 | `mm:362:5052` — avatar, name (`<h1>`), department + dot + tier pill |
| `app/profile/_components/profile-badge-row.tsx` | 84 | `mm:362:5064` six slots + `mm:3053:10052` caption |
| `app/profile/_components/profile-stats-card.tsx` | 89 | `mm:362:5073`/`5074`/`5075` — 5 rows, divider, disabled Secret Box button |
| `app/profile/_components/write-kudo-bar.tsx` | 57 | B slot, other face — one link to `/kudos/new?receiverId={id}` |

Nothing outside `ownedFiles` was opened for writing. `app/profile/page.tsx` (09),
`kudos-direction-section.tsx` / `profile-direction-menu.tsx` /
`profile-kudos-feed.tsx` (08 — already present on disk when this phase ran),
`supabase/`, `lib/**` and every `e2e/**` file are untouched.

## Design values used, and where each came from

| Value | Source |
|---|---|
| Banner `h-[512px] object-cover` + wash `linear-gradient(8deg, #00101A 8.6%, rgba(0,19,32,0) 37.25%)` | `momorph-visual-study.md` § Keyvisual; phase file's reuse clause |
| Banner artwork `/images/kudos/kv-background.png` | Same Figma component `2167:5141` that `kudos-hero.tsx` renders as `I2940:13432;2167:5141`; `get_media_files` returns **no** URL for `I1210:12622;2167:5141` (inline fill) |
| Hero column, `gap-8`, `items-center justify-center` | `get_frame_node_tree`/`query_section(362:5052)`: `gap:32px`, both axes centre, 1440×468 |
| `pt-[104px]` | Frame arithmetic: hero top y184 − header band bottom y80 |
| Avatar 200×200, `border-4 border-white`, `rounded-full` | `mm:362:5053` |
| Name 36px/44px bold `#FFEA9E` | `mm:362:5055` |
| Detail row `gap-2.5`, centred | `mm:362:5056` (`gap:10px`, `justify-content:center`) |
| Department 22px/28px bold white | `mm:362:5057` |
| Dot `h-1 w-1 bg-[#999] opacity-40` | `mm:362:5060` (4×4, `rgba(153,153,153,1)`, opacity 0.4) |
| Tier pill `h-[19px] rounded-[48px] border-[0.5px] border-[#FFEA9E]`, text 12.821px/17px, `tracking-[0.092px]`, `textShadow 0 0 1.3px #FFF`, `px-2.5` | `mm:3053:6061` + `mm:I3053:6061;3007:17519`; horizontal padding from the measured 715→726 / 814→824 insets |
| Slot 80×64, circle 64×64 `border-2 border-white bg-[#323231]`, `gap-4`, 1px black hairline | `mm:362:5065`, `mm:362:5066`–`5071`, `mm:I362:5066;3053:10046` (AMEND-2) |
| Caption 22px/28px bold white, centred, below the row | `mm:3053:10052` (y624–652) |
| Card `p-10 rounded-[17px] border-[#998C5F] bg-[#00070C] gap-2.5`, rows wrapper `gap-4` | `mm:362:5074`/`362:5075`; tokens verbatim from `kudos-sidebar.tsx` |
| Rows: label 22px/28px white, value 32px/40px `#FFEA9E`, `justify-between` | `mm:362:5076`–`5078`, `5080`–`5081` |
| Divider `h-px bg-[#2E3940]` | `mm:362:5079` |
| Button `py-4 rounded-lg bg-[#FFEA9E] text-[#00101A] gap-2` | `mm:362:5082` (600×60, padding 16, radius 8, gap 8) |
| Write-bar shell `rounded-[68px] border-[#998C5F] bg-[rgba(255,234,158,0.1)] px-4 py-6`, pen glyph, 16px bold | `mm:2940:13449` via `kudos-hero.tsx`; `spec.md` row `B.other` resolves this region as "mô hình theo thanh viết Kudo của bảng tin" |
| All counts | `formatHeartCount` (`lib/kudos/derive.ts`) — never `toLocaleString` |

Copy is 100% dictionary-sourced (`Dictionary["profile"]["stats"|"writeBar"]`,
badge heading resolved by the page). No count, name, or label is hardcoded.

## MoMorph calls

`get_media_files` ×1 · `query_section` ×2 (`362:5052`, `362:5056`).
Prompt-supplied design evidence reused instead of re-measuring:
`reports/momorph-visual-study.md`, `design/specs.csv`, `design/profile.png`
(read at two crops: page top y0–420, hero+stats y380–1200).

## Checks

| Check | Command | Exit |
|---|---|---|
| Typecheck | `npm run typecheck` | **0** |
| Lint | `npm run lint` | **0** — 30 warnings, all in `e2e/*.spec.ts`, **0** in `app/profile/_components/` |
| File size | `wc -l` | 53 / 114 / 84 / 89 / 57 — all < 200 |
| Asset coverage | n/a | No `MM_MEDIA_*` node maps into these regions: `get_media_files` returns no URL for the keyvisual, the avatar, any of the six badge slots, or the tier pill's `image 26`/`image 27` glow rects. The one asset referenced (`/images/kudos/kv-background.png`) is shipped and present. |

E2E was **not** run — the page is not wired until phase 09, and GREEN plus
visual validation belong to phase 10.

## Acceptance checklist

- [x] Every phase-file testid present: `profile-hero`, `profile-tier-badge`, `profile-badge-row`, `profile-badge-slot` (×6, one per `SLOT_NODE_IDS` entry), `profile-stats-card`, `profile-stat` (×5 `StatRow` usages), `profile-secret-box-button`, `profile-write-bar`
- [x] AMEND-1 honoured — no star node, no `starCountFor`, nothing invented on the name row
- [x] AMEND-2 honoured — six identical flat `#323231` circles, 64×64, `border-2 border-white`, `rounded-full`, 16px gap, fixed B2→B7 order, rendered **inside** the hero directly under the name
- [x] `hero.badge === null` hides the pill; `department === null` hides the text **and** the dot together
- [x] Self/other decided once at data level — no component re-derives "is this me"; the page picks `ProfileStatsCard` vs `WriteKudoBar` off `stats === null`
- [x] Secret Box control is `<button type="button" disabled>`, not the sidebar's `<a href="/kudos/secret-box">`
- [x] Write bar contains exactly one link, `href="/kudos/new?receiverId={id}"`, label interpolating the target's name
- [x] Reuse, not re-derivation: `kudos-hero.tsx` banner/wash + compose shell, `kudos-sidebar.tsx` stats tokens and gold button, `kudos-icons.tsx` `IconGift`/`IconPen`, `formatHeartCount`
- [x] `mm:{nodeId}` marker on every mapped node; no `data-mm-id` leaking into HTML
- [x] Next.js 16: `preload` used instead of the deprecated `priority`
- [x] Out-of-scope respected — no Spam chip, no data fetch, no Supabase import, no responsive breakpoints, no name/avatar/department editing

## Corrections to the prompt's authority documents

1. **The badge caption is a real frame node, and it sits BELOW the circles.**
   `momorph-visual-study.md` lists `mms_A.3` as the 6 slots only, and
   `docs/screens/SCR006_ProfileBanThan/spec.md` records the heading as
   "(không phải một node mm)" placed "phía trên hàng". Both are wrong:
   `query_section(362:5052)` returns a fourth hero child,
   **`mm:3053:10052`** — TEXT `"Bộ sưu tập icon của tôi"`, 264×28, 22px/28px
   weight 700 white, **y624–652**, i.e. 32px *under* the row (y528–592).
   `design/profile.png` confirms it. Implemented below the row, per the frame.

2. **Two hero image layers are unsourceable, so neither is invented.** The
   tier pill's `image 26` / `image 27` glow rectangles
   (`I3053:6061;3053:7682`, `I3053:6061;3053:7672`) have no `get_media_files`
   URL, exactly like the badge artwork AMEND-2 retired. The pill therefore
   renders transparent behind its measured gold hairline and glowing white
   text, rather than with a guessed backdrop.

## Unresolved questions

1. **`TC_WEB_PROFILE_GUI_005` cannot pass as written — and no implementation
   can fix it.** Line 292 asserts `await expect(button).toBeDisabled()`; line
   296 then calls `await button.click()`. Playwright resolves *both* through
   one predicate — `elementState` → `getAriaDisabled` =
   `isNativelyDisabled(element) || hasExplicitAriaDisabled(element)`
   (`node_modules/playwright-core/lib/coreBundle.js`) — so anything that
   satisfies `toBeDisabled()` also fails click's enabled-actionability check
   and times out. `aria-disabled` instead of the native attribute does not
   escape it. The spec is unambiguous that the button is `disabled`
   (clarifications § Statistics card; `spec.md` row `B.6` "Luôn `disabled`"),
   so the design was implemented and the test line is the defect. For the
   orchestrator/tester to resolve — `click({ force: true })`, or asserting
   no-navigation without a click. **I did not weaken the test.**

2. **Keyvisual vertical origin.** The frame draws the banner from y0 with the
   header painted over it; `HomeHeader` is `sticky` and *in flow*, so the
   banner starts ~64px lower and the strip behind the header shows page
   background rather than artwork. This is the same compromise the shipped
   `/kudos` screen makes, and the phase file directed reuse of that pattern.
   If phase 10's visual diff calls it out, the fix is a page-level layer in
   `page.tsx` (phase 09's file), not these five.

3. **`unlockedBadgeSlots` has no renderable unlocked state.** The prop is
   accepted and wired, but with zero badge artwork in the frame the only
   non-invented effect is dropping the locked `#323231` fill — an empty ring.
   The list is always empty today, so no test observes it. Real badge imagery
   remains a separate commission; flagged so nobody reads the wiring as a
   finished unlocked state.

4. **Avatar placeholder colour.** A sparse profile (`avatarUrl === ""`) renders
   a flat `#323231` circle inside the measured 4px white ring. `spec.md` row
   `A.1` asks for "placeholder tròn" without a colour, and `#323231` is the
   only placeholder grey this frame defines. Substitute if a real
   empty-avatar asset exists elsewhere.
