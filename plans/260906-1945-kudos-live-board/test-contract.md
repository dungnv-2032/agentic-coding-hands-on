# Test contract — Sun* Kudos - Live board (`/kudos`)

Orchestrator-owned. The E2E spec and the implementation are both bound to this file:
`tester` writes assertions against it, `momorph-ui-implementer` and `implementer` emit exactly
these hooks. Neither side may change a hook unilaterally — a change comes back to the
orchestrator. Copy values come from `clarifications.md`, which is authoritative.

## Route

`/kudos` — public, no auth guard. Placeholder destinations (each renders `ComingSoon`):
`/kudos/new`, `/kudos/secret-box`, `/kudos/[id]`, `/profile` (already shipped).

## Landmarks and text

| Hook | Kind | Value |
|------|------|-------|
| page `<h1>` | text | `Hệ thống ghi nhận và cảm ơn` |
| `data-testid="kudos-compose"` | `<a href="/kudos/new">` | accessible name = `Hôm nay, bạn muốn gửi lời cảm ơn và ghi nhận đến ai?` |
| `data-testid="sunner-search"` | `<input maxlength="100">` | placeholder `Tìm kiếm profile Sunner` |
| `data-testid="highlight-section"` | `<section>` | contains `<h2>` `HIGHLIGHT KUDOS` |
| `data-testid="spotlight-section"` | `<section>` | contains `<h2>` `SPOTLIGHT BOARD` |
| `data-testid="all-kudos-section"` | `<section>` | contains `<h2>` `ALL KUDOS` |
| `data-testid="kudos-sidebar"` | `<aside>` | — |

Each section's eyebrow is `Sun* Annual Awards 2025`.

## Filters

| Hook | Kind | Contract |
|------|------|----------|
| `data-testid="filter-hashtag"` | `<button>` | label `Hashtag`; carries `aria-expanded` |
| `data-testid="filter-department"` | `<button>` | label `Phòng ban`; carries `aria-expanded` |
| `data-testid="filter-menu-hashtag"` | `role="listbox"` | 13 `role="option"` children (clarifications § hashtag list) |
| `data-testid="filter-menu-department"` | `role="listbox"` | 50 `role="option"` children (clarifications § department list) |
| option | `role="option"` | carries `aria-selected`; re-clicking the selected option clears the filter |

Selecting a filter re-filters **both** `highlight-section` and `all-kudos-section` and resets the
carousel to slide 1. Filters AND-combine. Department matches the **receiver's** department.

## Highlight carousel

| Hook | Kind | Contract |
|------|------|----------|
| `data-testid="highlight-carousel"` | container | — |
| `data-testid="highlight-slide"` | slide | at most 5; the centre slide carries `aria-current="true"`, flanks `aria-hidden="true"` |
| `data-testid="carousel-prev"` / `carousel-next"` | `<button>` | 60px arrows; `disabled` at slide 1 / slide N |
| `data-testid="pager-prev"` / `pager-next"` | `<button>` | 28px arrows; same disabled rule |
| `data-testid="carousel-pagination"` | text | exactly `<current>/<total>`, e.g. `2/5` |

Slides are the top-N by heart count, descending, recomputed after filtering.

## Kudos card (`data-testid="kudos-card"`)

| Hook | Kind | Contract |
|------|------|----------|
| `data-testid="kudos-sender"` / `kudos-receiver"` | link | accessible name = the person's name; `href="/profile"` |
| `data-testid="sunner-badge"` | element | text one of `New Hero` · `Rising Hero` · `Super Hero` · `Legend Hero`; `title` = the matching hoa-thị sentence |
| `data-testid="kudos-time"` | text | `HH:mm - MM/DD/YYYY` |
| `data-testid="kudos-campaign"` | text | e.g. `IDOL GIỚI TRẺ` |
| `data-testid="kudos-body"` | text | line-clamped: 3 lines in highlight, 5 in feed |
| `data-testid="kudos-image"` | `<img>` | feed cards only, at most 5 |
| `data-testid="kudos-hashtag"` | `<button>` | text `#<tag>`; click sets the hashtag filter to that tag |
| `data-testid="kudos-heart"` | `<button>` | carries `aria-pressed`; `disabled` when the viewer is the sender |
| `data-testid="kudos-heart-count"` | text | `vi-VN` grouping, e.g. `1.000` |
| `data-testid="kudos-copy-link"` | `<button>` | label `Copy Link` |
| `data-testid="kudos-detail-link"` | `<a href="/kudos/<id>">` | label `Xem chi tiết` — **highlight cards only** |
| `data-testid="kudos-edit"` | `<a href="/kudos/<id>">` | pen glyph; rendered only when the viewer is the sender |
| `data-testid="kudos-empty"` | text | `Hiện tại chưa có Kudos nào.` |
| `data-testid="feed-sentinel"` | element | infinite-scroll trigger in `all-kudos-section` |

Heart toggle: `aria-pressed` flips and `kudos-heart-count` moves by exactly 1 in the matching
direction. A second click returns both to the original values.

## Copy link

Clicking `kudos-copy-link` writes the kudos URL to the clipboard and shows
`data-testid="toast"` with the text `Link copied — ready to share!`.

## Spotlight board

| Hook | Kind | Contract |
|------|------|----------|
| `data-testid="spotlight-board"` | container | — |
| `data-testid="spotlight-count"` | text | `388 KUDOS` |
| `data-testid="spotlight-search"` | `<input maxlength="100">` | placeholder `Tìm kiếm` |
| `data-testid="spotlight-node"` | `<a href="/kudos/<id>">` | accessible name = the recipient's name; `title` = name + time received |
| `data-testid="spotlight-ticker"` | container | rows like `08:30PM Nguyễn Bá Chức đã nhận được một Kudos mới` |
| `data-testid="spotlight-panzoom"` | `<button>` | `aria-pressed`; `title` `Pan/Zoom` |
| `data-testid="spotlight-expand"` | `<button>` | `aria-pressed` |
| `data-testid="spotlight-empty"` | text | shown when no node matches the search |

Typing in `spotlight-search` narrows `spotlight-node` to matching names.

## Sidebar

| Hook | Kind | Contract |
|------|------|----------|
| `data-testid="sidebar-stat"` | row | 5 rows, in order: `Số Kudos bạn nhận được:` · `Số Kudos bạn đã gửi:` · `Số tim bạn nhận được:` · `Số Secret Box bạn đã mở:` · `Số Secret Box chưa mở:` |
| `data-testid="secret-box-button"` | `<a href="/kudos/secret-box">` | label `Mở Secret Box` |
| `data-testid="gift-leaderboard"` | container | heading `10 SUNNER NHẬN QUÀ MỚI NHẤT`; rows `data-testid="gift-row"` (name link + gift line) |
| `data-testid="gift-empty"` | text | `Chưa có dữ liệu` |

## Out of contract (deliberately not asserted)

Account-balance accrual on like, special-day ×2 crediting, an auth redirect on this route,
the rank-up leaderboard, and any dialog — all recorded in `clarifications.md`
§ Unresolved questions with the reason.

---

## Supabase amendment (orchestrator, 2026-09-06b)

The data source moved from a frozen TS module to the Supabase local project
(`clarifications.md` § "Session 2026-09-06 (b)"). Rows are now real, so three hooks above change
and two assertions are added. Everything not named here is unchanged.

### Overridden hooks

| Hook | Was | Now |
|------|-----|-----|
| `data-testid="kudos-heart"` | `disabled` when viewer is the sender | `disabled` when viewer is the sender **OR when there is no session**. `aria-pressed` reflects the viewer's *persisted* like, read from `kudos_likes` — not component-local state. |
| `data-testid="kudos-heart-count"` | client counter over mock data | derived from the persisted like count; still `vi-VN` grouped (`1.000`) |
| `data-testid="sidebar-stat"` | mock viewer's five rows | the **signed-in** Sunner's real counts; for an anon viewer it falls back to the seeded frame viewer so the block still renders exactly one state (supersedes assumption A2) |

### Added assertions

| ID | Project | Contract |
|----|---------|----------|
| K-24 | `anon` | Every `kudos-heart` is `disabled` for an anon viewer, and no heart click mutates `kudos-heart-count`. Read paths still render fully — the section headings, cards, spotlight and sidebar are all present without a session. |
| K-25 | `kudos-authed` | The heart **persists**: click it, reload the page, and `aria-pressed` plus `kudos-heart-count` hold their new values. Clicking again and reloading returns both to the original values. This is the one assertion that proves the data layer is real rather than client state. |

`K-10` (toggle flips `aria-pressed`, count moves by exactly 1) moves from the `anon` project to a
new `kudos-authed` project, because an anon viewer can no longer toggle. A new Playwright project
is required; it reuses the existing `e2e/auth.setup.ts` storage state
(`e2e/.auth/user.json`) rather than adding a second setup.

### Seed dependency

The suite asserts against **seeded** rows, so the seed is a test precondition, not decoration.
The seed's content is the frame corpus already fixed in `clarifications.md`
§ "Resolved from source data" — verbatim, nothing invented. A test that would only pass against
hand-tuned numbers invented for the test is out of contract.

---

## Blueprint ratification (orchestrator, 2026-09-06c)

The blueprint surfaced seven conflicts between the authoritative artifacts. Ruled on here — this
section is authoritative over anything above it that it names.

### Ratified as proposed

| # | Change | Ruling |
|---|--------|--------|
| 1 | `kudos.id` is `bigint generated always as identity`, not `uuid` | **Ratified.** The suite asserts `/\/kudos\/\d+/`; a uuid href fails it. `kudos-detail-link` and `kudos-edit` therefore resolve to `/kudos/<n>`. |
| 2 | Receiver chip carries `data-testid="sunner-badge-receiver"`; sender keeps `sunner-badge` | **Ratified — additive.** `card.getByTestId("sunner-badge")` is strict-mode ambiguous when both chips carry one hook. The contract hook stays unique and keeps its meaning (the sender's badge); the receiver's gets its own. Both carry the `title` rule below. |
| 3 | `kudos-detail-link` renders only on the **active** carousel slide | **Ratified.** Five simultaneous links are strict-mode ambiguous, and the frame draws `Xem chi tiết` only on the prominent centre card — the flanks are faded and explicitly non-interactive. |
| 4 | `kudos_likes.user_id` references `auth.users(id)`, never `sunners(id)`; viewer identity for `canLike` is auth-only | **Ratified, and load-bearing.** If the seeded-viewer fallback also fed `canLike`, the seeded card's heart would be `disabled`, K-25 would take an early-return branch and pass while proving nothing. The sidebar fallback stays presentation-only. |
| 5 | `sunners.kudos_received_baseline` seeds the frame's badge tiers | **Ratified.** Same idiom as `heart_baseline`: the frame shows `Legend Hero` (≥ 50 received) and seeding 50 real rows to earn it would be inventing data. |
| 6 | Department filter menu has **50** options, not 48; `CEVC10` is not among them | **Ratified and corrected at source.** The printed list in `clarifications.md` always held 50 — the `(48 entries)` label was miscounted and is now fixed. `CEVC10` (the frame people's department) is genuinely absent from the dropdown frame, so it seeds as a department row that is not a filter option. The row above now reads 50. |
| 7 | `refresh()` from `next/cache` rather than `revalidatePath` | **Ratified** on the blueprint's verification against this build's `node_modules/next/cache.d.ts`. The route is dynamic via `cookies()`, so there is no cache entry to invalidate. |

### Overridden

**`388 KUDOS` does NOT go in the i18n dictionary.** The blueprint proposed shipping it as dictionary
copy because `count(*)` over the seed is not 388. The conclusion is right that it must not be a live
`count(*)`; the placement is wrong. `388` is **data** — a number transcribed from the frame — and the
dictionary is **UI copy**, obliged in both vi and en. A number that reads identically in both
locales is not copy, and putting it there would oblige a translator to maintain a figure.

It ships the way the two ratified baselines above ship: **a seeded value in the database, read by the
query layer.** Add it to the seed as a single-row board-stats value (or an equivalent seeded column
the spotlight query already reads) and render `<seeded total> KUDOS`. This is the third instance of
one idiom, not a new mechanism: `heart_baseline`, `kudos_received_baseline`, and now the spotlight
total are all frame-verbatim numbers the seed carries because the real activity that would produce
them does not exist yet. K-13's literal assertion holds, and `lib/i18n` stays free of data.

### Corrected in place

**`e2e/fixtures/kudos-constants.ts` `BADGE_TIERS` was shifted by one tier** — it mapped New Hero to
the 10-Kudos sentence, Rising to 20, Super to 50, and Legend to a duplicate of 50. The blueprint
caught it. Corrected to the mapping `clarifications.md` § "Card badges" fixes: `New Hero` → **no
tooltip** (`null` — it is the pre-threshold tier and has no published copy), `Rising Hero` → the
10-Kudos sentence, `Super Hero` → 20, `Legend Hero` → 50. The type widened to
`Record<BadgeTier, string | null>`.

Consequently the `sunner-badge` row above is refined: `title` = the matching hoa-thị sentence **for
the three published tiers only**; a `New Hero` badge carries no `title` attribute. Asserting a
tooltip on `New Hero` would assert copy that does not exist in the design.
