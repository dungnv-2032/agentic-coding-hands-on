# Clarifications — Sun* Kudos - Live board

- **Screen:** Sun* Kudos - Live board — https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/MaZUn5xHXZ
- **fileKey:** `9ypp4enmFmdK3YAFJLIu6C` · **screenId:** `MaZUn5xHXZ` · **figma node:** `2940:13431`
- **Design revision:** `904fca587cc5bbddf4075c207e680277` · design_status `done`, spec_status `done`
- **Companion frames (same commission, both `done`/`done`):** `JWpsISMAaM` Dropdown Hashtag filter (`721:5580`) · `WXK5AYB_rG` Dropdown Phòng ban (`721:5684`) — these ARE the menus items B.1.1/B.1.2 open, so they are in scope for this screen.
- **Source data:** 64 spec items, 41 test cases, 74 `MM_MEDIA_*` nodes + 4 + 4 dropdown spec items (fetched live via MoMorph MCP)
- **Frame image:** `design/kudos-live-board.png` (1440×5862)
- **testPolicy:** `e2e-red-first`
- **Mode:** `/tkm:takumi --auto` — user directed *"tự động triển khai theo hướng: câu hỏi đâu tiên, Yes hoặc câu trả lời Recommend mà ko cần hỏi lại"*.
  Every gap below is therefore resolved by the orchestrator on the recommended option and recorded here.
  **This file is authoritative and is not re-openable by sub-agents.**

## Session 2026-09-06

- Q: Which route does this screen live at? → A: **`/kudos`.** The frame's own header renders "Sun* Kudos" in the *selected* state, which identifies this route; `home-nav.tsx` derives selection from `usePathname()`, so it lights up with zero edits. `KudosPromo`'s CTA (`/kudos`) and the homepage nav already point there. The existing `ComingSoon` placeholder at `app/kudos/page.tsx` is **replaced** by the real screen — same move F003 made at `/awards-information`.
- Q: Where does the screen's data come from — Supabase tables, or static content? → A: **A frozen mock dataset derived verbatim from the Figma frame, under `lib/kudos/`.** `docs/generated/entities.md` records, by direct inspection, that this repo owns **zero tables, zero migrations, zero SQL** and every Supabase call is `auth.*`. Standing up a Kudos schema is a separate commission (it needs write paths, RLS, moderation — the `Admin - Review content` / `Viết Kudo` frames), and inventing one here would violate both YAGNI and the MoMorph rule *"Use Figma design content as mock data source. Do NOT invent data."* Every name, department, badge, timestamp, body, hashtag, count and gift line below is transcribed from the frame or the spec CSV — nothing is fabricated. **Track B therefore carries no backend work**; its surface is the data modules + i18n dictionary + pure filter/badge logic.
- Q: Is the screen behind an auth guard? Test case `71b3ef43` says an unauthenticated visitor clicking a profile/detail must be redirected to login. → A: **Route stays public — no guard added.** `proxy.ts` guards only `/todo` and `/login`; the only entry points to this screen are the public homepage nav and `KudosPromo`'s CTA, and F003 set the precedent that gating a destination whose entry point is public is incoherent. `71b3ef43` is **recorded as out of scope, not silently dropped** — see § Unresolved questions.
- Q: The sidebar is personal ("Số Kudos **bạn** nhận được"). What does an anonymous visitor see? → A: **The same block, rendered from the mock viewer.** The frame defines exactly one state for this sidebar and no anonymous variant; with no real per-user data source (decision 2), an auth-gated variant would be invented UI. Recorded as assumption **A2**.
- Q: Test policy. → A: **`e2e-red-first`.** The screen carries real state transitions — filter dropdowns that re-filter both sections and reset the carousel, carousel paging with end-disabled arrows, heart toggle with count mutation, clipboard + toast, search validation at 100 chars. Policy auto-selects strict per `.claude/rules/momorph/momorph-development.md` § 3. `@playwright/test` 1.62.1 with a working `playwright.config.ts` already exists (`anon` project), so the runner precondition is met; **nothing is installed or scaffolded**.
- Q: The screen has four affordances that open surfaces owned by *other* MoMorph frames — compose bar A.1 → `Viết Kudo` (`ihQ26W78P2`), "Mở Secret Box" D.1.8 → `Open secret box- chưa mở` (`J3-4YFIpMM`), "Xem chi tiết"/card body → `View Kudo` (`onDIohs2bS`), avatar/name → `Profile bản thân` (`3FoIx6ALVb`). Build them? → A: **No — each is its own commission. The triggers are real links to declared-placeholder routes that render `ComingSoon`.** This is the pattern the repo already runs (phase 07: "every nav/CTA link must resolve rather than 404"), and it is honest: the button exists, is reachable, navigates, and the destination says plainly it is not built. New placeholder routes: `/kudos/new`, `/kudos/secret-box`, `/kudos/[id]`. `/profile` already renders `ComingSoon`. **No dialog is faked on this screen.**
- Q: Spec CSV D.1.8 labels the sidebar button `Mở quà`; the frame renders **`Mở Secret Box`**. Which wins? → A: **Frame wins — `Mở Secret Box`.** Same precedence rule F002/F003 applied: the frame plus its live TEXT nodes are the later machine-readable artifact; the CSV prose row is stale.
- Q: Spec CSV item D describes **two** sidebar leaderboards ("10 SUNNER CÓ SỰ THĂNG HẠNG MỚI NHẤT" and "10 SUNNER NHẬN QUÀ MỚI NHẤT"), but only the gift list exists as a numbered item (D.3) and only it renders in the frame. → A: **One list — `10 SUNNER NHẬN QUÀ MỚI NHẤT`.** Frame wins; the rank-up list is not built.
- Q: Card badges. The frame shows four tiers (`New Hero`, `Rising Hero`, `Super Hero`, `Legend Hero`); the spec text (B.3.2/B.3.6) describes three "hoa thị" thresholds at 10 / 20 / 50 received Kudos. How do they map? → A: **Four tiers over the three published thresholds:** `New Hero` (< 10), `Rising Hero` (≥ 10), `Super Hero` (≥ 20), `Legend Hero` (≥ 50). The badge's hover tooltip carries the spec's hoa-thị copy **verbatim** (§ Resolved from source data). This is the only reading that consumes both artifacts without inventing a fourth threshold.
- Q: Item D.4 `Tag 'IDOL GIỚI TRẺ'` renders centered above the message with a pen icon at the right — is it a hashtag or something else? → A: **A campaign label, not a hashtag.** Hashtags render as a red `#…` row lower in the card (B.4.3/C.3.7); this one is centered, uppercase, has no `#`, and the file carries an `Action - Campaign` frame. Modelled as `campaign` on the kudos. The pen (`MM_MEDIA_Pen`, 32px) is **edit-own-post** — it renders only on kudos whose sender is the mock viewer (which, with the frame's dataset, is every ALL KUDOS card, matching the frame) and links to `/kudos/[id]` (`ComingSoon`). The `Màn Sửa bài viết- edit mode` frame is a separate commission.
- Q: Heart rules — the spec (C.4.1) is dense: one like per user per kudos, sender cannot like own kudos, +1 heart to the sender's account, +2 on an admin-configured special day, unlike revokes the same amount. How much is in scope? → A: **The two rules the frame can express are implemented; account-balance accrual is not.** In scope: toggle (gray ↔ red, count ±1) and *the sender's own kudos has the heart disabled*. Out of scope: crediting the sender's account +1/+2 and the special-day configuration — both need persistence and an admin surface (`Admin - Setting`), neither of which exists. The sidebar's "Số tim bạn nhận được" already renders the frame's `x2` flame glyph, so the special-day concept is **shown, not simulated**. Test cases `31936b72` (special day) and `63645b03`/`91e102ba` partially — see § Unresolved questions.
- Q: How is the Spotlight word cloud drawn — a library, or hand-rolled? → A: **Hand-rolled, deterministic layout, no new dependency.** A seeded PRNG places the frame's seven recipient names across the canvas at three size tiers, memoised so SSR and hydration agree byte-for-byte (a random layout would hydration-mismatch). Pan/zoom is a CSS `transform` on a wrapper — drag to pan, the `Pan/Zoom` control toggles the mode, and the expand glyph toggles a full-bleed view. Adding `d3-cloud` for seven names fails YAGNI and would be the project's first runtime chart dependency.
- Q: Filter semantics — Hashtag and Phòng ban together. → A: **AND-combined, and both sections react.** Selecting a hashtag filters ALL KUDOS *and* the HIGHLIGHT carousel (spec item B explicitly: "lọc danh sách (cả phần Highlight Kudos và All Kudos), cập nhật carousel và đặt pagination về 1"), and the carousel resets to slide 1. Phòng ban filters on the **receiver's** department (dropdown spec A.1: "lọc ra các lời cảm ơn đến người thuộc phòng ban này"). Re-clicking the selected option clears it (dropdown spec A.1: "toggle chọn/bỏ chọn").
- Q: Where does the highlight carousel's "top 5" come from? → A: **`[...kudos].sort(by hearts desc).slice(0, 5)`, recomputed after filtering.** Spec B.2: "5 card kudos có nhiều tim nhất". Not a separate hand-picked list.
- Q: The hero carries two inputs — a compose bar and a search. The spec CSV numbers only the compose bar (A.1) and the *Spotlight* search (B.7.3, placeholder `Tìm kiếm`, max 100). The hero's right-hand search (`2940:13450`) is unnumbered. → A: **Both searches ship, both capped at 100 chars.** Hero placeholder `Tìm kiếm profile Sunner` (verbatim from the frame), Spotlight placeholder `Tìm kiếm`. The hero search filters nothing on this screen — it targets Sunner *profiles*, whose screen is not built — so it submits to `/profile` (`ComingSoon`) with the query. The Spotlight search filters the word cloud in place.
- Q: i18n coverage. → A: **Full VN + EN**, enforced at compile time by extending the `Dictionary` interface with a `kudos` namespace. VN verbatim from the design; EN a faithful translation. **Mock *content*** (person names, message body, gift lines, ticker) is locale-independent and lives in `lib/kudos/`, not the dictionary — it is data, not UI copy.
- Q: Shared chrome — rebuild or compose? → A: **Compose unchanged:** `HomeHeader`, `SiteFooter`, `getPageContext`. This screen renders **no** `FloatingWidget` and **no** `KudosPromo` (the frame shows neither — it *is* the Kudos screen).
- Q: New image assets? → A: **Two exports needed** — the KV background (`MM_MEDIA_KV Background`, 1440×512) and the Spotlight canvas background. Avatars and the five attachment thumbnails are `MM_MEDIA_Sample Image` placeholders: reuse a single committed sample per role rather than exporting eight near-identical crops. The `KUDOS` wordmark reuses the shipped `public/images/home/kudos-logo.svg` (same artwork, `MM_MEDIA_Kudos logo` 593×104).

## Resolved from source data (no decision needed)

**Page order:** header → hero (KV background + `Hệ thống ghi nhận và cảm ơn` + KUDOS wordmark + compose bar + Sunner search) → HIGHLIGHT KUDOS (B) → SPOTLIGHT BOARD (B.6/B.7) → ALL KUDOS (C) + sidebar (D) → footer.

**Palette (sampled from the frame):** page `#00101A` · card `#FFF8E1` · message box `#FFF2C6` · sidebar card `#00070C` · gold `#FFEA9E` · filter button `#1A2527` · heart active `#D4271D` · hashtag red `#D4271D`.

**Hero (A):** title `Hệ thống ghi nhận và cảm ơn` (gold) · KUDOS wordmark · compose bar placeholder `Hôm nay, bạn muốn gửi lời cảm ơn và ghi nhận đến ai?` with 24px pen icon · search placeholder `Tìm kiếm profile Sunner` with 24px search icon.

**HIGHLIGHT KUDOS (B):** eyebrow `Sun* Annual Awards 2025` · hairline · title `HIGHLIGHT KUDOS` (gold) · filters `Hashtag` / `Phòng ban` (chevron-down, `#1A2527`) · 5-card carousel, centre card prominent and the flanks faded/non-interactive · 60px round prev/next arrows disabled at each end · pagination `2/5` with its own 28px arrows.

**Card fields (B.3 / C.3):** sender chip (64px avatar, name, department, badge) · 32px send glyph · receiver chip · timestamp `10:00 - 10/30/2025` (`HH:mm - MM/DD/YYYY`) · campaign label `IDOL GIỚI TRẺ` · message body (clamp **3** lines in HIGHLIGHT, **5** in ALL KUDOS, then `...`) · attachment gallery, max 5 × 88px (ALL KUDOS only) · hashtag row, max 5 on one line then `...` · action bar `1.000` + heart · `Copy Link` (24px link glyph) · `Xem chi tiết` (HIGHLIGHT only).

**Frame dataset (verbatim):**
- Sender `Huỳnh Dương Xuân Nhật` · `CEVC10` · badges seen: `New Hero`, `Rising Hero`, `Super Hero`
- Receiver `Huỳnh Dương Xuân` · `CEVC10` · badge `Legend Hero`
- Campaign `IDOL GIỚI TRẺ` · timestamp `10:00 - 10/30/2025` · hearts `1.000`
- Message: `Cảm ơn người em bình thường nhưng phi thường :D Cảm ơn sự chăm chỉ, cần mẫn của em đã tạo động lực rất nhiều cho team, để luôn nhắc mình luôn phải nỗ lực hơn nữa trong công việc. <3 và cuộc sống...`
- Hashtags: `#Dedicated #Inspring #Dedicated #Inspring #Dedicated #Inspring…`

**Hashtag filter list (13, from `JWpsISMAaM` item A, verbatim):** Toàn diện · Giỏi chuyên môn · Hiệu suất cao · Truyền cảm hứng · Cống hiến · Aim High · Be Agile · Wasshoi · Hướng mục tiêu · Hướng khách hàng · Chuẩn quy trình · Giải pháp sáng tạo · Quản lý xuất sắc.

**Department filter list (from `WXK5AYB_rG` item A, verbatim, 50 entries):** CTO · SPD · FCOV · CEVC1 · CEVC2 · STVC - R&D · CEVC2 - CySS · FCOV - LRM · CEVC2 - System · OPDC - HRF · CEVC1 - DSV - UI/UX 1 · CEVC1 - DSV · CEVEC · OPDC - HRD - C&C · STVC · FCOV - F&A · CEVC1 - DSV - UI/UX 2 · CEVC1 - AIE · OPDC - HRF - C&B · FCOV - GA · FCOV - ISO · STVC - EE · GEU - HUST · CEVEC - SAPD · OPDC - HRF - OD · CEVEC - GSD · GEU - TM · STVC - R&D - DTR · STVC - R&D - DPS · CEVC3 · STVC - R&D - AIR · CEVC4 · PAO · GEU · GEU - DUT · OPDC - HRD - L&D · OPDC - HRD - TI · OPDC - HRF - TA · GEU - UET · STVC - R&D - SDX · OPDC - HRD - HRBP · PAO - PEC · IAV · STVC - Infra · CPV - CGP · GEU - UIT · OPDC - HRD · BDV · CPV · PAO - PAO.

**SPOTLIGHT BOARD (B.6/B.7):** eyebrow `Sun* Annual Awards 2025` · title `SPOTLIGHT BOARD` (gold) · canvas heading `388 KUDOS` · search `Tìm kiếm` (16px icon) · word-cloud names, verbatim: `Đỗ hoàng Hiệp`, `Dương thúy An`, `Mai phương Thúy`, `Nguyễn Văn Quy`, `Lê Kiều Trang`, `Nguyễn Bá Chức`, `Nguyễn Hoàng Linh` (one node rendered in red as the just-updated node) · activity ticker line `08:30PM Nguyễn Bá Chức đã nhận được một Kudos mới` (6 rows, fading upward) · expand glyph bottom-right · `Pan/Zoom` control with tooltip `Pan/Zoom`.

**ALL KUDOS (C):** eyebrow `Sun* Annual Awards 2025` · title `ALL KUDOS` (gold) · vertical card feed with infinite scroll · empty state `Hiện tại chưa có Kudos nào.`

**Sidebar (D), verbatim rows:** `Số Kudos bạn nhận được: 25` · `Số Kudos bạn đã gửi: 25` · `Số tim bạn nhận được:` + `x2` flame glyph + `25` · divider · `Số Secret Box bạn đã mở: 25` · `Số Secret Box chưa mở: 25` · button `Mở Secret Box` (gift glyph, `#FFEA9E`) · card `10 SUNNER NHẬN QUÀ MỚI NHẤT` with rows `Huỳnh Dương Xuân` / `Nhận được 1 áo phông SAA`, independently scrollable · empty state `Chưa có dữ liệu`.

**Badge tooltip copy (B.3.2/B.3.6, verbatim):**
- 1 hoa thị: `Sunner đã nhận được 10 Kudos và bắt đầu lan tỏa năng lượng ấm áp đến mọi người xung quanh.`
- 2 hoa thị: `Sunner đã nhận được 20 Kudos và chứng minh sức ảnh hưởng của mình qua những hành động lan tỏa tích cực mỗi ngày.`
- 3 hoa thị: `Sunner đã nhận được 50 Kudos và trở thành hình mẫu của sự công nhận, sẻ chia và lan tỏa tinh thần Sun*.`

**Toast:** `Link copied — ready to share!`

## Assumptions

- **A1 — The mock dataset is the data layer.** `lib/kudos/` holds a frozen, Figma-derived dataset; likes/filters/carousel/search are client state over it and reset on reload. No persistence is claimed anywhere in the UI, the spec, or the tests.
- **A2 — The sidebar renders from the mock viewer regardless of session.** The frame defines no anonymous state and there is no per-user data source; gating it would be invented UI.
- **A3 — Attachment and avatar artwork is sample placeholder art in the design itself** (`MM_MEDIA_Sample Image`). One committed sample per role is byte-honest to the frame; it is not a claim about real people's photos.
- **A4 — Infinite scroll over a finite mock feed** means "reveal in pages of N as the sentinel enters view, then stop". The frame renders four cards; the dataset carries enough to page at least twice so the mechanism is observable.

## Unresolved questions

1. **Test case `71b3ef43` (unauthenticated → redirect to login)** is contradicted by the shipped public-route design (decision 3) and by six already-green anon tests that reach `/kudos` unauthenticated. Recorded, not implemented. Needs a product call on whether the whole Kudos surface is members-only.
2. **Test case `31936b72` (special-day like credits +2 hearts to the sender's account)** and the account-balance half of `63645b03`/`91e102ba` need persistence plus the `Admin - Setting` configuration surface. Out of scope here; the `x2` flame is displayed, not simulated.
3. **Spec CSV `qa` note on C.4.1** — "Cần phân biệt lượt thả tim bình thường và lượt thả tim đặc biệt … để thu hồi đúng số tim" — is a backend concern with no client-side expression. Carried forward to whichever commission builds the Kudos schema.
4. **Hero Sunner search has no destination screen.** It submits to `/profile` (`ComingSoon`) with the query; the real search-results screen (`[iOS] Sun*Kudos_Search Sunner` exists, web does not) is unbuilt.

## Session 2026-09-06 (b) — orchestrator override: data source

The user's re-invocation carries an explicit directive that outranks the auto-resolved
mock-data decision recorded above: *"Implement màn hình Sun* Kudos - Live board **use Supabase
local project**"*. A decision the orchestrator resolved on the user's behalf is superseded the
moment the user states their own; this section is authoritative over the § "Session 2026-09-06"
entry on data source only. Every other decision in this file stands unchanged.

- Q: Mock dataset under `lib/kudos/`, or the Supabase local project? → A: **Supabase local project.**
  Verified running: API `http://127.0.0.1:54321`, DB `postgresql://…@127.0.0.1:54322/postgres`,
  and `supabase/` carries **no `migrations/` directory** — the schema is net-new, not a
  modification. Track B therefore DOES carry backend work: migrations, RLS, a seed, and a typed
  query layer. This is the first SQL the repo owns.
- Q: What owns the row content, now that rows are real? → A: **The seed is transcribed verbatim
  from the Figma frame** — the same corpus § "Resolved from source data" already fixes (names,
  departments, badges, timestamp, body, hashtags, counts, gift lines, ticker, the 13 hashtags and
  48 departments). The MoMorph rule *"Use Figma design content as mock data source. Do NOT invent
  data"* is unchanged by moving that content from a TS module into `seed.sql`.
- Q: Reads on the server or the client? → A: **Server components read via `lib/supabase/server.ts`;
  interaction state (filters, carousel, hearts, searches) stays client-side.** This matches the
  shipped pattern in `app/awards-information/` and keeps the anon key bounded by RLS.
- Q: Does the heart toggle now persist? → A: **Yes — it writes.** With real tables a like is a row,
  so `kudos_likes` persists per-viewer and the count is derived. The two rules the frame expresses
  stay as recorded (toggle ±1; sender's own kudos disabled). Account-balance accrual and the
  special-day ×2 remain out of scope per § Unresolved questions — they need the admin surface.
- Q: Anonymous viewers, now that likes are rows? → A: **Read-only for anon; the heart requires a
  session.** RLS grants `select` to `anon` and restricts `insert`/`delete` on `kudos_likes` to
  `auth.uid()`. The route itself stays public (decision 3 above is untouched). Assumption **A2** is
  superseded: the sidebar now reads the signed-in Sunner's real counts, and falls back to the
  frame's seeded viewer for anon so the block still renders exactly one state.

### Schema decisions (orchestrator, resolving the study's open questions)

The Supabase study (`plans/reports/researcher-260906-1958-supabase-data-layer.md`) closed with
three questions it could not answer from what exists. Resolved here on the recommended option.

- Q: `seed.sql` may not insert into `auth.users` (GoTrue-owned), yet the frame shows a card with
  `1.000` hearts and a sidebar reading `25`. Where do seeded counts live if a like is a row owned
  by a real auth user? → A: **A seeded baseline column plus real like rows.** `kudos.heart_baseline`
  carries the frame's number (`1000`) and `kudos_likes` carries only genuine per-viewer likes; the
  displayed count is `heart_baseline + count(kudos_likes)`. Nothing fabricates an auth row, the
  frame's `1.000` renders exactly, and K-25 becomes observable: a signed-in viewer's like takes the
  card to `1.001` and a reload holds it there. The alternative — a nullable `user_id` on
  `kudos_likes` for seeded likes — would make the uniqueness constraint that enforces "one like per
  user per kudos" unenforceable, which is the one heart rule the frame does express.
- Q: What does the sidebar read for an anonymous viewer? → A: **A `sunners` row whose
  `auth_user_id` is NULL is the seeded frame viewer.** Its five counters carry the frame's verbatim
  `25`s. A signed-in viewer resolves to their own `sunners` row by `auth_user_id`; with no row (the
  e2e user signs up fresh each run) it falls back to the seeded viewer, so the block renders exactly
  one state in every case, as the frame defines. This is what supersedes assumption A2.
- Q: Where do generated DB types live — `types/`, `lib/kudos/`, or `lib/supabase/`? → A:
  **`lib/supabase/database.types.ts`**, generated by `npx supabase gen types typescript --local
  --schema public`, committed, with an `npm run db:types` script. It sits beside the client it types
  rather than opening a new top-level `types/` directory for one file, and committing it keeps
  `npm run build` working without a live database. `lib/kudos/` then holds thin domain aliases over
  those generated rows — the same identity/presentation split `lib/awards.ts` and
  `lib/award-system.ts` already run.
- Q: `npx supabase db reset` truncates `auth.users`, which would sign out a live session and break
  the authenticated e2e specs mid-run. → A: **Reset is a pre-suite step, never a mid-session one.**
  The seed is applied before Playwright's `setup` project runs, and `e2e/auth.setup.ts` then signs up
  its own fresh user against the reset stack. No test may call `db reset` while the suite is running.

- **A5 — The seven Spotlight people are assigned departments from the canonical 50.** The frame
  names them (`Đỗ hoàng Hiệp`, `Dương thúy An`, `Mai phương Thúy`, `Nguyễn Văn Quy`,
  `Lê Kiều Trang`, `Nguyễn Bá Chức`, `Nguyễn Hoàng Linh`) but never states their departments — only
  the sender/receiver pair is shown as `CEVC10`, and `CEVC10` is not one of the 50 options in the
  Phòng ban dropdown frame. Seeding every receiver as `CEVC10` therefore makes the department filter
  return zero rows for all 50 options, which contradicts the dropdown spec ("lọc ra các lời cảm ơn
  đến người thuộc phòng ban này") and leaves the feature unobservable. These seven are given
  departments drawn from the canonical 50 so that selecting a real option returns real rows. The
  frame's own card keeps its verbatim `CEVC10` pair untouched. This assigns a value the frame leaves
  blank rather than overriding one it states — the narrower of the two available choices, and it is
  recorded here rather than left implicit in the seed.

### Orchestrator corrections to my own visual findings (2026-09-06d)

Two of the findings I raised off the first screenshot were wrong, and the record should say so
rather than leave them standing as open defects.

- **V3 "the message body should be ragged-right" — WITHDRAWN.** The frame's own text nodes measure
  `textAlignHorizontal: JUSTIFIED` (`I3127:21871;256:5156` plus the highlight instances
  `I2940:1346{4,5,6};662:12223`). The design justifies the body deliberately. What I reacted to was
  not justification but justification inside a column that was still too narrow — the same
  680px-vs-392px bug behind V1 — and at the corrected 680px the spacing is even and reads well. The
  UI agent was right to refuse the change and escalate rather than quietly deviate from the design
  source; "never guess a visual value" cuts both ways, and it applies to the orchestrator too.
- **V5 "the frame card shows the wrong heart count" — NOT A DEFECT.** The feed is ordered newest
  first and `kudos` id=1 (the frame-verbatim card, `heart_baseline` 1000, `sent_at` 10:00 +07 on
  30/10/2025) leads it correctly. The `52` and `1.002` readings both came from screenshots scrolled
  to later cards, plus leftover `kudos_likes` rows before a reset. Verified against the database.

V1 (receiver chip clipped) and V2 (attachment gallery clipped) were real and are fixed. V4 (the
`1 Issue` overlay / React key warning) is still open and under diagnosis.
