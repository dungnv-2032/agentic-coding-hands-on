# Clarifications — Thể lệ (SCR007)

- MoMorph screen: `Thể lệ UPDATE` — https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/b1Filzi9i6
- figma node: `3204:6051` · 4 specs · 9 test cases · `design_status: done`, `spec_status: done`, `dev_status: none`
- Design artifacts: `design/specs.csv`, `design/test-cases.csv`, `design/the-le.png`
- testPolicy: **`e2e-red-first`** — the screen is a panel with real state transitions: open/close
  (`TC_THELE_FUN_003`), navigation out to the compose form (`TC_THELE_FUN_004`) and independent
  scroll (`TC_THELE_FUN_001/002`). That is behavioural, not a static mapping, so the auto-selection
  rule in `.claude/rules/momorph/momorph-development.md` picks strict E2E.
- Discipline: `--auto`. The commission says *"tự động triển khai theo hướng câu trả lời đâu tiên,
  Yes hoặc câu trả lời Recommend mà ko cần hỏi lại"* — every gate below is resolved by taking the
  first/Yes/Recommended option, without asking again.
- Supabase: **local project** (`supabase/migrations`, `supabase/seed.sql`), as instructed.

## Session 2026-09-09

### What the design is, and what the repository already has for it

The frame is a 553px right-hand drawer (`3204:6052`, `background #00070C`, padding `24 40 40 40`,
`justify-content: space-between`) sitting on a 1440×1796 dark canvas. It holds one scrollable
content column (`3204:6053`) and a two-button footer (`3204:6092`).

The repository already reserves a home for it. `app/standards/page.tsx` renders `ComingSoon`, and
its own comment names the reservation: *"the 'Tiêu chuẩn chung' screen isn't built yet, but the
footer link and the widget's standards shortcut must resolve rather than 404 (ID-55/59)."* The
floating widget links `/standards` under the label `standards: "Thể lệ SAA"`
(`lib/i18n/messages/vi-home.ts:79`), so the route was already the Thể lệ route in everything but
content.

### Route and surfacing

- Q: The design is a modal/drawer, but every screen shipped so far (SCR001–SCR006) is a route.
  Ship Thể lệ as a route, or as an in-page overlay opened from the floating widget?
  → A: **Route — the existing `/standards`.** Recommended: it is the target the floating widget and
  the footer already point at, the repo has a six-screen precedent of one MoMorph frame = one route,
  and a route is deep-linkable and directly testable under the `anon` Playwright project. An in-page
  overlay would require rewiring the widget on every page that renders it and would leave
  `/standards` dead. `ComingSoon` is replaced, exactly as `/awards-information`, `/kudos/new` and
  `/profile` each replaced it in turn.

- Q: The drawer is an overlay — what sits beneath it on the route?
  → A: **The standard shell**: `HomeHeader` + a dark `main` + `SiteFooter`, the same composition
  `app/kudos/page.tsx` and `app/awards-information/page.tsx` use, with the drawer rendered above it
  as `fixed inset-y-0 right-0` over a click-through-to-close backdrop. The frame's left region is
  flat dark with no content, so a scrim reproduces it faithfully without inventing a background.

- Q: `TC_THELE_FUN_003` — "Panel closes and the previous content is shown". Where does `Đóng` go?
  → A: **`router.back()` when this route has a history entry, otherwise `/`.** The button is a real
  `<button>`, not a `<Link>`, because its destination is "wherever you came from". Arriving by deep
  link is the fallback case and lands on the homepage — never a dead end. `Escape` and a backdrop
  click do the same thing (accessibility; not in the test cases, but standard for a dialog and free).

- Q: `TC_THELE_FUN_004` — "The Viết KUDOS input modal opens". This app has no compose modal.
  → A: **Navigate to `/kudos/new`.** That IS the compose surface in this repo (F005 Viet Kudo), and
  `proxy.ts` already guards it, so an anonymous click lands on `/login` by the existing rule. The
  *requirement* — "Viết KUDOS reaches the compose form" — is preserved; only the mechanism is
  translated to what exists here. Recorded as a deliberate translation, not a relaxation.

### Content source — the Supabase requirement

- Q: The commission says "use Supabase local project". The other content screens
  (`/awards-information`) hardcode their copy in `lib/`. Hardcode here too, or persist?
  → A: **Persist.** Two new tables in a new migration, read per request through
  `lib/rules/`. This is the explicit instruction and the whole point of the commission; a hardcoded
  panel would satisfy the pixels and ignore the ask.

- Q: What table shape? One table per content kind (sections / hero tiers / collectible icons), or
  one generic pair?
  → A: **Two tables — `public.rule_sections` + `public.rule_items`.** Recommended: the frame holds
  three ordered prose sections and two ordered *lists of things* (4 hero tiers, 6 collectible
  icons) that differ only in which fields they populate. A `kind` column (`hero_tier` |
  `collectible_icon`) on one `rule_items` table covers both without a third near-identical table
  (DRY), and `rule_sections` carries the ordered prose. Three tables would be one table per Figma
  heading, which is layout leaking into the schema.

  Shape follows the repo's own idioms verbatim (researcher-01):
  `bigint generated always as identity primary key`; ordering by an explicit
  `position smallint not null` (never insertion order or `id`); `<table>_select_all` RLS policy
  `for select to anon, authenticated using (true)`; explicit
  `grant select on ... to anon, authenticated`; no update/delete policy, because silence is the
  deny; `notify pgrst, 'reload schema';` after the grants.

- Q: Where do the badge and icon images live — in the database, or on disk?
  → A: **On disk under `public/images/rules/`, with the row storing the path.** Recommended: it is
  what every other screen does with its Figma assets, it keeps the migration small, and Next's
  `<Image>` wants a static path. All 12 assets were pulled from the frame during this gate; the two
  MoMorph returned no flat media for (`MM_MEDIA_New Hero` `3204:6163`, `MM_MEDIA_ Badge REVIVAL`
  `3204:6082`, both composed of vector rectangles plus text) were cropped from the 1×
  frame render at their measured frame coordinates rather than redrawn.

- Q: Does the content need a `locale` column so the panel can be English?
  → A: **No.** Recommended: the frame carries Vietnamese copy only, and the MoMorph rule is "use
  Figma design content as the mock data source, do NOT invent data" — an English column could only
  be filled by inventing translations. The *chrome* (panel title, the two button labels, aria
  labels) does go through the `Dictionary` with real vi + en strings, because those are short UI
  labels the repo already translates for every screen. Consequence, stated plainly rather than
  hidden: with `NEXT_LOCALE=en` the panel chrome is English and the rules body stays Vietnamese.
  A `locale` column is a one-migration change the day real English copy exists (YAGNI until then).

### Layout and behaviour

- Q: `TC_THELE_FUN_001/002` — scroll. What scrolls?
  → A: **The content column, not the page.** The drawer is `h-svh` with the footer pinned
  (`justify-content: space-between` in the frame, on a fixed-height panel) and the content column
  `overflow-y-auto`. `FUN_002`'s "content shorter than the panel, no scroll" is then automatic —
  `overflow-y-auto` produces no scrollbar and no scrollable distance when content fits, so both
  cases are one implementation, asserted as `scrollHeight > clientHeight` and its negation.

- Q: The frame is 553px wide. What happens below that?
  → A: **`w-full max-w-[553px]`** — full-bleed on a phone, 553px from there up. The design has no
  mobile frame; this is the minimal responsive rule that never overflows the viewport, and matches
  the wrap-rather-than-overflow fix already applied in `home-nav.tsx`.

- Q: `TC_THELE_GUI_003` and `TC_THELE_FUN_005` assert a **disabled** footer button — dimmed, and
  rejecting clicks. Nothing in this feature disables either button.
  → A: **Not applicable — recorded, not faked.** `Đóng` always closes and `Viết KUDOS` always
  navigates; there is no state, loading or otherwise, in which either is unavailable. Building a
  `disabled` prop that nothing can ever set would be dead code, and staging a fake disabled button
  purely to make a test case green is exactly the "no fake data, no stopgaps" line in
  `primary-workflow.md`. Both test cases are carried into `e2e/the-le.spec.ts` as `test.skip` with
  this reason inline, so the omission is visible in the suite output rather than silently dropped.
  The `spec_progress` on `B_Button` describing a disabled state stays true of the shared Figma
  *component*; it is not true of either instance on this screen.

- Q: `TC_THELE_GUI_004` — hover restyles both buttons.
  → A: **Yes, both.** `Đóng` is `border 1px #998C5F` over `rgba(255,234,158,0.10)`; hover lifts the
  fill toward the existing `hover:bg-white/10` token already approved for this shared button
  component in `language-selector.tsx` and `home-nav.tsx` (`code-rules` reuse, no new value
  invented). `Viết KUDOS` is solid `#FFEA9E`; hover darkens it slightly. Hover is a
  visual-contract concern and is validated by the visual pass, not asserted in the strict E2E.

### Test policy and its preflight

- Q: `visual-contract` or `e2e-red-first`?
  → A: **`e2e-red-first`.** Auto-selected by rule 3 of the resolution table (state transitions:
  panel open/close, navigation, scroll). Not forced by a flag; not overridable to
  `visual-contract` just because the screen is mostly text.
- Q: Does a real runner exist, so strict RED is legal here?
  → A: **Yes** — `@playwright/test ^1.62.1`, `npm run test:e2e`, `playwright.config.ts` with a
  webServer that boots `next dev` on `127.0.0.1:3000`. Web, not mobile. Nothing is installed or
  scaffolded for this run.
- Q: Which Playwright project?
  → A: **`anon`.** `/standards` is public — `proxy.ts` guards only `/todo`, exact `/kudos/new` and
  `/profile`. Per researcher-02, a public spec needs no setup project; its basename is added to the
  `anon` `testMatch` regex.
- Q: Does the spec need seeded rows?
  → A: **Yes — its own.** The panel renders nothing without `rule_sections`/`rule_items`, so the
  seed rows added by this feature ARE the fixture. The spec reads copy through exported constants in
  `e2e/fixtures/the-le-constants.ts`, transcribed from this file, per the repo convention. The spec
  writes no data, so it needs no cleanup block.

### Resolved from source data (copy is transcribed, never invented)

Panel title — `3204:6055`, 45/52 bold, `#FFEA9E`:

- `Thể lệ`

Section 1 heading — `3204:6132`, 22/28 bold, `#FFEA9E`:

- `NGƯỜI NHẬN KUDOS: HUY HIỆU HERO CHO NHỮNG ẢNH HƯỞNG TÍCH CỰC`

Section 1 body — `3204:6133`, 16/24 bold, white, justified:

- `Dựa trên số lượng đồng đội gửi trao Kudos, bạn sẽ sở hữu Huy hiệu Hero tương ứng, được hiển thị trực tiếp cạnh tên profile`

Hero tiers — `3204:6161`, `:6170`, `:6179`, `:6188`; label 16/24 bold white, description 14/20 bold white:

| pos | image (`3204:`) | label | description |
|-----|-----------------|-------|-------------|
| 1 | `6163` New Hero | `Có 1-4 người gửi Kudos cho bạn` | `Hành trình lan tỏa điều tốt đẹp bắt đầu – những lời cảm ơn và ghi nhận đầu tiên đã tìm đến bạn.` |
| 2 | `6172` Rising Hero | `Có 5-9 người gửi Kudos cho bạn` | `Hình ảnh bạn đang lớn dần trong trái tim đồng đội bằng sự tử tế và cống hiến của mình.` |
| 3 | `6181` Super Hero | `Có 10–20 người gửi Kudos cho bạn` | `Bạn đã trở thành biểu tượng được tin tưởng và yêu quý, người luôn sẵn sàng hỗ trợ và được nhiều đồng đội nhớ đến.` |
| 4 | `6190` Legend Hero | `Có hơn 20 người gửi Kudos cho bạn` | `Bạn đã trở thành huyền thoại – người để lại dấu ấn khó quên trong tập thể bằng trái tim và hành động của mình.` |

Note the en-dash in tier 3 (`10–20`) and the en-dashes inside descriptions 1 and 4 — they are in the
frame and are preserved byte-for-byte.

Section 2 heading — `3204:6077`, 22/28 bold, `#FFEA9E`:

- `NGƯỜI GỬI KUDOS: SƯU TẬP TRỌN BỘ 6 ICON, NHẬN NGAY PHẦN QUÀ BÍ ẨN`

Section 2 body — `3204:6078`, 16/24 bold, white, justified:

- `Mỗi lời Kudos bạn gửi sẽ được đăng tải trên hệ thống và nhận về những lượt ❤️ từ cộng đồng Sunner. Cứ mỗi 5 lượt ❤️, bạn sẽ được mở 1 Secret Box, với cơ hội nhận về một trong 6 icon độc quyền của SAA.`

Collectible icons — `3204:6079`, two rows of three, 80px wide slots, 16px gap, 24px row gap:

| pos | node (`3204:`) | caption |
|-----|----------------|---------|
| 1 | `6082` | `REVIVAL` |
| 2 | `6087` | `TOUCH OF LIGHT` |
| 3 | `6086` | `STAY GOLD` |
| 4 | `6083` | `FLOW TO HORIZON` |
| 5 | `6084` | `BEYOND THE BOUNDARY` |
| 6 | `6088` | `ROOT FURTHER` |

**AMENDED in phase 08 — this entry was wrong.** It originally read `ROOT FUTHER`, justified as
"the caption text node reads FUTHER". That justification read the wrong field of the node. A
MoMorph re-read of `I3204:6088;737:20392` returns:

- `itemName` (the Figma LAYER name) — `ROOT FUTHER`
- `character` (the rendered TEXT content) — `ROOT FURTHER`

The layer name was transcribed instead of the text content. The frame render agrees with
`character`, and so does the asset file name `icon-root-further.png`. The seed, the E2E fixture and
both specs now carry `ROOT FURTHER`. The rule itself is unchanged and still binding: transcribe the
source verbatim — this was a misread of which field IS the source, not a decision to "fix" a typo.

Section 2 closing line — `3204:6089`:

- `Những Sunner thu thập trọn bộ 6 icon sẽ nhận về một phần quà bí ẩn từ SAA 2025.`

Section 3 heading — `3204:6090`, 24/32 bold, `#FFEA9E`:

- `KUDOS QUỐC DÂN`

Section 3 body — `3204:6091`:

- `5 Kudos nhận về nhiều ❤️ nhất toàn Sun* sẽ chính thức trở thành Kudos Quốc Dân và được trao phần quà đặc biệt từ SAA 2025: Root Further.`

Footer — `3204:6092`, row, gap 16px, height 56px:

- `Đóng` — `3204:6093`, `border: 1px solid #998C5F`, `background rgba(255,234,158,0.10)`,
  `border-radius 4px`, padding 16px, gap 8px, icon `MM_MEDIA_Close` 24×24, measured 94px wide
- `Viết KUDOS` — `3204:6094`, `background #FFEA9E`, `border-radius 4px`, padding 16px, gap 8px,
  icon `MM_MEDIA_Pen` 24×24, 363px wide (i.e. it takes the remaining width — `flex-1`)

Text colour note: MoMorph reports a text node's fill under `backgroundColor`. `#FFEA9E` on the
headings and `#FFFFFF` on the bodies are text colours, matching how the existing screens in this
repo already read the same field.

### Assets pulled during this gate

`public/images/rules/` — `hero-badge-new-hero.png`, `hero-badge-rising-hero.png`,
`hero-badge-super-hero.png`, `hero-badge-legend-hero.png`, `icon-revival.png`,
`icon-touch-of-light.png`, `icon-stay-gold.png`, `icon-flow-to-horizon.png`,
`icon-beyond-the-boundary.png`, `icon-root-further.png`, `close-icon.svg`, `pen-icon.svg`.

`pen-icon.svg` duplicates `public/images/home/widget-pen-icon.svg` by node id
(`186:1763` is the same MoMorph component). Whoever implements the footer should diff the two and
reuse the existing file if they are identical, rather than shipping the copy.

### Unresolved

- The 6 collectible icons overlap conceptually with `app/profile/_components/profile-badge-row.tsx`,
  whose six slots render as flat `#323231` circles because F006's frame carried no badge artwork.
  This screen now brings that artwork into the repo. Wiring it into the profile badge row is a
  follow-up commission, deliberately out of scope here — it would change a shipped screen that this
  frame says nothing about.
- No `PERM###` code is assigned for the new tables. `docs/generated/permissions-matrix.md` is the
  registry; `doc-writer` allocates it at delivery.

## Test contract (shared — tester and UI implementer both bind to this)

`data-testid` values, fixed here so the RED spec and the UI agent cannot drift apart. Naming follows
the repo's `<screen>-<element>` kebab convention (researcher-02 §3).

| testid | element | count |
|--------|---------|-------|
| `rules-panel` | the drawer container | 1 |
| `rules-panel-content` | the scrollable content column | 1 |
| `rules-section` | one prose section (heading + body) | 3 |
| `rules-hero-tier` | one Hero tier row (pill image + label + description) | 4 |
| `rules-collectible-icon` | one collectible-icon slot (artwork + caption) | 6 |
| `rules-close-button` | the `Đóng` control — a real `<button>` | 1 |
| `rules-write-kudos-link` | the `Viết KUDOS` control — an `<a href="/kudos/new">` | 1 |

Additional bindings:

- the panel title renders as the page's `<h1>` and reads exactly `Thể lệ`
- `rules-panel` carries `role="dialog"`, labelled by the `<h1>`, and deliberately does **NOT** carry
  `aria-modal`. **AMENDED in phase 08 after review.** This line originally fixed `aria-modal="true"`.
  The panel builds no focus trap and makes nothing `inert` — a deliberate choice, because `/standards`
  is a route rather than an overlay on live content, so tabbing out to the header or footer is correct
  page behaviour. Declaring `aria-modal` on top of that told assistive tech "nothing outside this
  dialog exists" while the header and footer stayed in the tab order and stayed activatable, leaving
  three input modes disagreeing (the `z-40` scrim blocks the mouse over a `sticky z-20` header, the
  keyboard passes straight through, the screen reader is told the page is empty). The attribute was
  dropped rather than a trap built, and `e2e/the-le.spec.ts` now asserts its ABSENCE so it cannot
  creep back. A recorded contract change — not an assertion quietly loosened to make a build pass.
- Vietnamese copy is asserted from `e2e/fixtures/the-le-constants.ts`, never inline (researcher-02 §3)
- the spec file is `e2e/the-le.spec.ts`, registered under the `anon` project by adding `the-le`
  to that project's `testMatch` regex in `playwright.config.ts`
- `TC_THELE_GUI_003` and `TC_THELE_FUN_005` appear as `test.skip` carrying the not-applicable reason
