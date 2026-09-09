---
status: implemented
fcode: F007
authored_by: takumi
created: 2026-09-09
lang: vi
---

# F007_TheLe

## 1. Technical Overview

`/standards` — route đã tồn tại nhưng đang render `ComingSoon` — được thay bằng một Server Component thật:
shell chuẩn (`HomeHeader` + `main` tối + `SiteFooter`) với một drawer 553px `fixed inset-y-0 right-0` chồng
lên trên qua một backdrop bấm-để-đóng. Đây là màn hình đầu tiên của repo có **nội dung biên tập nằm trong
database**: hai bảng mới `rule_sections` (văn xuôi có thứ tự) và `rule_items` (danh sách có thứ tự, phân
biệt bằng `kind`) thay cho lối hardcode trong `lib/` mà `/awards-information` đang dùng. Trang không có
Server Action nào và không ghi bảng nào — toàn bộ tương tác là điều hướng (`Viết KUDOS`) hoặc lịch sử
trình duyệt (`Đóng`), nên phần Client Component chỉ ôm đúng ba thứ: `router.back()`, phím `Escape`, và
click backdrop.

## 2. Action Index

| # | Action (handler) | Method · Path | Codes | Writes | Detail |
|---|---|---|---|---|---|
| **A0** | *cross-cutting — belongs to no single action* | — | FR-001, FR-004, FR-601, BR-001 | — | § 4.4 |
| **A1** | `StandardsPage` (`app/standards/page.tsx:34`) | `GET` `/standards` | FR-002, FR-003, FR-201, FR-202, FR-203, FR-204, FR-205, FR-403, FR-405, BR-002, BR-003, US001 | — *(read-only)* | § 3.1 |
| **A2** | `RulesCloseButton` + `RulesBackdrop` (`rules-panel-dismiss.tsx`, client) | *(no request — history/DOM only)* | FR-401, FR-404, BR-004, US002 | — | § 3.2 |
| **A3** | `Viết KUDOS` link (`<Link>` → static `<a>`) | `GET` `/kudos/new` *(navigation)* | FR-402, BR-005, US003 | — | § 3.3 |

## 3. Actions

### 3.1 CAP-01 — Đọc nội dung thể lệ

#### A1 · Dựng `/standards` và render toàn bộ drawer ở lần render đầu
`GET` `/standards` → `` `StandardsPage` `` (`app/standards/page.tsx:34`)
`FR-002` `FR-003` `FR-201` `FR-202` `FR-203` `FR-204` `FR-205` `FR-403` `FR-405` · `US001`

**Who** · Bất kỳ ai — route công khai, `proxy.ts` chỉ canh `/todo`, `/kudos/new` (exact) và `/profile`.
**FE** · Server Component. `await getPageContext()` một lần cho `locale` + `dictionary` + `isAuthenticated`
+ `isAdmin`; chỉ hai boolean đi vào `HomeHeader` (Client Component), object user của Supabase không bao giờ
đi qua. Chrome đọc từ `dictionary.rules` (`FR-003`); nội dung thể lệ KHÔNG đọc từ đó (`BR-002`). Drawer dựng
`fixed inset-y-0 right-0 w-full max-w-[553px] h-svh flex flex-col justify-between bg-[#00070C] px-10 pb-10 pt-6`
(`FR-405`), cột nội dung `flex-1 overflow-y-auto` (`FR-403`), chân drawer `flex gap-4 h-14` ghim dưới.
Backdrop là một anh em `fixed inset-0` nằm dưới drawer theo z-index.
**Request** · Không tham số. Không `searchParams`, không dynamic segment.
**BE** · `getRulesContent()` (`lib/rules/rules-data.ts`) tạo đúng một client mỗi request
(`await createClient()` từ `lib/supabase/server.ts`) rồi bắn hai read độc lập qua một `Promise.all`:
`fetchRuleSections(supabase)` và `fetchRuleItems(supabase)` (`lib/rules/queries.ts`). Cả hai đều
`order("position", { ascending: true })` (`BR-001`). Map dòng thô sang `RulesViewModel` đóng băng
(`lib/rules/view-model.ts`) — dòng database không bao giờ chạm tới component, đúng khuôn `board-data.ts` /
`profile-data.ts`.
**Rule**
- **BR-002 — Nội dung là dữ liệu, chrome là i18n.** `rule_sections`/`rule_items` giữ chữ thể lệ;
  `dictionary.rules` giữ tiêu đề panel, hai nhãn nút và nhãn aria. Không bên nào lấn sang bên kia. *(§ 4.4)*
- **BR-003 — Không có cột `locale`.** Frame chỉ có tiếng Việt; bịa bản dịch là vi phạm luật MoMorph. Hệ quả
  (`NEXT_LOCALE=en` → chrome EN + thân VI) được ghi nhận thẳng trong `functional-spec.md § 11 RISK-02`,
  không giấu. *(inline)*
- **Bảng rỗng không phải lỗi.** Hai query trả mảng rỗng → cột nội dung rỗng, chrome và hai nút vẫn đủ.
  Không throw, không màn trắng. *(inline)*

**Result** · Không ghi DB. Trả HTML đã render đầy đủ: `<h1>Thể lệ</h1>` (`FR-201`), ba `rules-section`
(`FR-202`), bốn `rules-hero-tier` (`FR-203`), sáu `rules-collectible-icon` trong lưới ba cột (`FR-204`),
ảnh phục vụ từ `public/images/rules/` qua `image_path` (`FR-205`). Chỉ chân drawer và backdrop hydrate
(§ 3.2); toàn bộ phần nội dung là HTML tĩnh.
**Source:** `app/standards/page.tsx:34-77`, `app/standards/_components/rules-panel.tsx`, `rules-section.tsx`, `rules-hero-tier-list.tsx`, `rules-collectible-grid.tsx`, `lib/rules/rules-data.ts`, `lib/rules/queries.ts`, `lib/rules/view-model.ts`

<!-- Không có diagram: hai read song song, không ghi bảng nào, không phải hành động nền. -->

---

### 3.2 CAP-02 — Đóng panel quay lại

#### A2 · Đóng drawer bằng nút, `Escape`, hoặc backdrop
*(không có request — chỉ lịch sử trình duyệt)* → `` `RulesCloseButton` `` + `` `RulesBackdrop` `` (`rules-panel-dismiss.tsx`, Client Component)
`FR-401` `FR-404` · `US002`

**Who** · Bất kỳ ai đang xem drawer.
**FE** · Client Component nhỏ nhất có thể, ôm đúng một callback `dismiss()` dùng chung cho ba lối vào:
`<button data-testid="rules-close-button">` (`FR-401`), `keydown` `Escape` gắn ở `document`, và `onClick`
của backdrop (`FR-404`). `dismiss()` gọi `router.back()` khi trang này có entry để quay về, ngược lại
`router.push("/")`. Phân biệt hai trường hợp bằng `navigation.canGoBack` (Navigation API) đọc tại thời
điểm bấm, có feature-detect `typeof === "boolean"`, và lùi về `window.history.length > 1` trên engine
chưa hỗ trợ. **Không dùng `history.length` một mình** — giả định đó đã bị đo và bác bỏ, xem § 5.2 A1.
`document.referrer` cũng không dùng được vì điều hướng client-side của Next không cập nhật nó.
**Rule**
- **BR-004 — `Đóng` nghĩa là "quay lại nơi bạn đến".** `/` chỉ là nhánh dự phòng cho deep link. Không bao
  giờ là ngõ cụt, và không bao giờ mặc định về trang chủ khi có lịch sử thật để quay lại. *(§ 4.4)*

**Result** · Không request, không ghi DB. Điều hướng trình duyệt.
**Source:** `app/standards/_components/rules-panel-dismiss.tsx:47-71` (`hasHistoryToReturnTo` + `useRulesDismiss`), `:94-116` (`RulesBackdrop` — `Escape` + nền ngoài), `:153-176` (`RulesCloseButton`)

---

### 3.3 CAP-03 — Đi thẳng sang viết Kudos

#### A3 · `Viết KUDOS` dẫn tới form soạn
`GET` `/kudos/new` *(navigation)* → `` `<Link href="/kudos/new">` `` (render ra `<a>`, static)
`FR-402` · `US003`

**Who** · Bất kỳ ai; `proxy.ts` quyết định ai đi tiếp được.
**FE** · Một `<a data-testid="rules-write-kudos-link" href="/kudos/new">` thật — không `onClick`, không
`router.push`, không kiểm quyền phía client. Nền `#FFEA9E`, `rounded`, `p-4`, `gap-2`, icon bút 24×24,
`flex-1` để chiếm nốt bề ngang còn lại cạnh `Đóng` (94px đo được trên frame).
**Rule**
- **BR-005 — Nút không tự phán quyền.** `/kudos/new` đã nằm trong danh sách guarded của `proxy.ts` từ F005;
  một người chưa đăng nhập bấm vào rơi về `/login` theo đúng luật sẵn có. Nhân bản luật đó ở đây tạo ra hai
  nguồn sự thật cho cùng một quyết định. *(§ 4.4)*
- **DEC-001 — dịch cơ chế, giữ yêu cầu.** `TC_THELE_FUN_004` nói "modal"; hệ thống này soạn Kudos bằng
  route. Ghi nhận là một bản dịch có chủ đích, không phải một nới lỏng. *(functional-spec.md § 3)*

**Result** · Điều hướng. Không ghi DB.
**Source:** `app/standards/_components/rules-panel.tsx` (`<Link href="/kudos/new" data-testid="rules-write-kudos-link">`), `proxy.ts:51-57`

## 4. Shared Foundation

### 4.1 Components

| Component | Kind | Purpose |
|-----------|------|---------|
| `app/standards/_components/rules-panel.tsx` | server | Vỏ drawer + bố cục cột nội dung / chân drawer |
| `app/standards/_components/rules-section.tsx` | server | Một mục văn xuôi (tiêu đề + thân) |
| `app/standards/_components/rules-hero-tier-list.tsx` | server | Bốn bậc Hero (ảnh pill + nhãn + mô tả) |
| `app/standards/_components/rules-collectible-grid.tsx` | server | Lưới ba cột sáu icon + caption |
| `app/standards/_components/rules-panel-dismiss.tsx` | client | `Đóng` + `Escape` + backdrop (§ 3.2) |
| `HomeHeader`, `SiteFooter` | server (existing) | Shell bên dưới drawer — dùng nguyên, không sửa |

Mỗi file giữ dưới 200 dòng theo `development-rules.md`; chia theo ranh giới nội dung của frame, không chia
tuỳ tiện.

### 4.2 Data Model

#### Key Entities

| Entity | Table | Key Columns | Purpose |
|--------|-------|-------------|---------|
| Mục thể lệ | `public.rule_sections` | `id bigint identity pk`, `position smallint not null unique`, `heading text not null`, `body text not null`, `closing_body text` | Ba mục văn xuôi có thứ tự; `closing_body` là dòng kết render SAU danh sách của mục đó (chỉ mục 2 dùng) |
| Mục danh sách | `public.rule_items` | `id bigint identity pk`, `kind text not null check (kind in ('hero_tier','collectible_icon'))`, `position smallint not null`, `label text not null`, `description text`, `image_path text not null` | Bốn bậc Hero và sáu icon sưu tập trong một bảng; `unique (kind, position)` |

#### Polymorphic Behavior

`rule_items.kind` là discriminator, hai giá trị:

| `kind` | Rows | `label` là | `description` | `image_path` là |
|--------|------|------------|---------------|-----------------|
| `hero_tier` | 4 | ngưỡng ("Có 1-4 người gửi Kudos cho bạn") | bắt buộc — đoạn mô tả bậc | ảnh pill huy hiệu |
| `collectible_icon` | 6 | caption in hoa ("REVIVAL") | `null` — frame không có mô tả cho icon | artwork tròn |

Một bảng thay vì hai vì hai danh sách khác nhau đúng ở chỗ *cột nào được điền*, không ở hình dạng
(DRY). Ba bảng sẽ là một bảng cho mỗi tiêu đề Figma — tức là bố cục rò rỉ vào schema.

### 4.3 State Management

Chỉ một mẩu state phía client: không có. `RulesPanelDismiss` không giữ state nào — nó chỉ gắn listener và
gọi router. Không context, không store, không `useState`.

### 4.4 Shared Rules

- **FR-001 / FR-601 — RLS public-read là tiền lệ ràng buộc.** `docs/system/permissions.md` ghi rõ mọi bảng
  sau F004 đều bật RLS. Hai bảng mới theo đúng khuôn `kudos_select_all`: `enable row level security`, đúng
  một policy `<table>_select_all` `for select to anon, authenticated using (true)`, `grant select` tường
  minh, không policy ghi (im lặng là từ chối). Hai mã đã được cấp trong
  `docs/generated/permissions-matrix.md`: **`PERM014`** (`rule_sections_select_all`) và **`PERM015`**
  (`rule_items_select_all`).
- **FR-004 — `database.types.ts` phải sinh lại.** `npm run db:types` sau khi migration chạy, commit kèm.
  File này được track, không gitignore, và không sửa tay.
- **BR-001 — `order by position` là bắt buộc.** Ở cả hai query, mọi lúc. Không dựa vào `id`, không dựa vào
  thứ tự insert.

### 4.5 Algorithms & Integrations

None — không thuật toán, không tích hợp ngoài. Hai `select` thẳng, một `Promise.all`.

### 4.6 Configuration

None.

**Client behavior:** see behavior-logic.md, permissions.md, architecture.md

## 5. Verification & Technical Notes

### 5.1 Technical Verification

- **testPolicy: `e2e-red-first`** — auto-chọn theo rule 3 của bảng resolution
  (`.claude/rules/momorph/momorph-development.md`): màn có chuyển trạng thái thật (đóng/mở panel, điều
  hướng ra form soạn, cuộn độc lập). Không bị ép bằng flag, và không được hạ xuống `visual-contract` chỉ vì
  màn phần lớn là chữ.
- **Runner có thật** — `@playwright/test ^1.62.1`, `npm run test:e2e`, `playwright.config.ts` với webServer
  boot `next dev` trên `127.0.0.1:3000`. Web, không phải mobile. Không cài, không scaffold gì cho lần chạy
  này.
- **Project: `anon`** — `/standards` công khai; thêm `the-le` vào regex `testMatch` của project `anon`.
  Spec công khai không cần setup project (researcher-02 § 4).
- **Fixture chính là seed của feature** — panel không render gì nếu `rule_sections`/`rule_items` rỗng, nên
  các dòng seed do FR-002 thêm LÀ fixture. Spec đọc chữ qua hằng số export từ
  `e2e/fixtures/the-le-constants.ts`, phiên âm từ `clarifications.md`, không bao giờ literal inline
  (researcher-02 § 3). Spec không ghi dữ liệu nên không cần block cleanup.
- **Test contract (`data-testid`)** — chốt trong `clarifications.md § "Test contract"`, ràng buộc cả spec
  RED lẫn agent dựng UI: `rules-panel`, `rules-panel-content`, `rules-section` (×3), `rules-hero-tier` (×4),
  `rules-collectible-icon` (×6), `rules-close-button`, `rules-write-kudos-link`.
- **`TC_THELE_GUI_003` / `TC_THELE_FUN_005`** vào suite dưới dạng `test.skip` kèm lý do inline (DEC-002) —
  hiện ra trong output, không biến mất.
- **Hover (`TC_THELE_GUI_004`)** là mối lo visual-contract, được xác nhận ở lượt visual của `tester`, không
  assert trong strict E2E.

### 5.2 Assumptions

- **A1 — BÁC BỎ (đo được, không phải suy đoán).** Giả định ban đầu: `window.history.length > 1` đủ để phân
  biệt "có chỗ quay lại" với "deep link", và trường hợp xấu nhất vẫn không phải ngõ cụt. Sai. Đo trên
  Chromium thật (phase 07):

  ```
  newPage() mới           -> url about:blank, history.length = 1
  sau goto("/standards")  -> url /standards,  history.length = 2
  ```

  Entry `about:blank` khởi tạo của tab nằm lại trong session history, nên một deep link báo length 2, đi
  nhánh `router.back()`, và ném người dùng ra `about:blank` — đúng cái ngõ cụt mà `BR-004` sinh ra để cấm
  (e2e `FUN_003b` bắt được).

  **Cách giải quyết đã ship:** feature-detect `navigation.canGoBack` (Navigation API) — trên tab mới nó là
  `false`, sau một soft navigation từ `/` nó là `true` — và giữ `window.history.length > 1` làm fallback cho
  engine chưa có API đó (Safari/Firefox tại thời điểm viết). Kiểm bằng `typeof === "boolean"` chứ không phải
  truthiness, để một engine trả về `false` thật vẫn được tôn trọng. Xem `rules-panel-dismiss.tsx`.

  Ghi chú đo thêm: Chrome chỉ phơi entry cùng origin cho Navigation API, nên khách tới từ Slack nhận
  `push("/")` thay vì bị ném ngược ra ngoài app — tốt hơn cả câu chữ của `BR-004`. Trên Firefox/Safari
  fallback đi nhánh `back()` và rời khỏi app. Cả hai đều không phải ngõ cụt.
- **A2 — BÁC BỎ.** Giả định: `pen-icon.svg` trùng node id `186:1763` với
  `public/images/home/widget-pen-icon.svg` nên tái dùng được file có sẵn. Hình học path đúng là giống nhau,
  nhưng file có sẵn là `fill="white"` còn nút `Viết KUDOS` nền `#FFEA9E` — tái dùng cho ra một cái bút
  trắng vô hình trên nền vàng. Phase 06 tạo `public/images/rules/pen-icon.svg` riêng với `fill="#00070C"`;
  file `home/` giữ nguyên vì vẫn phục vụ `floating-widget.tsx` trên nền tối.

### 5.3 Unresolved Questions

- ~~Chưa cấp mã `PERM###` cho hai bảng mới.~~ **Đã giải quyết ở bước delivery:** `PERM014` và
  `PERM015` trong `docs/generated/permissions-matrix.md`.
- Sáu artwork icon vào repo qua màn này trong khi `profile-badge-row.tsx` (F006) vẫn dựng vòng tròn phẳng
  `#323231`. Nối hai chỗ lại là một commission tiếp theo, cố ý ngoài scope (`functional-spec.md § 11 RISK-01`).

### 5.4 Source References

| Artifact | Path |
|----------|------|
| Clarification gate | `plans/260909-0838-the-le-rules-panel/clarifications.md` |
| Frame render | `plans/260909-0838-the-le-rules-panel/design/the-le.png` |
| Component specs (MoMorph) | `plans/260909-0838-the-le-rules-panel/design/specs.csv` |
| Test cases (MoMorph) | `plans/260909-0838-the-le-rules-panel/design/test-cases.csv` |
| Supabase/i18n conventions | `plans/260909-0838-the-le-rules-panel/research/researcher-01-supabase-and-i18n-conventions.md` |
| Playwright harness | `plans/260909-0838-the-le-rules-panel/research/researcher-02-playwright-harness.md` |

#### Data Flow

```text
GET /standards
  → getPageContext()            → locale + dictionary.rules + isAuthenticated/isAdmin
  → getRulesContent()
      → createClient()          (một client mỗi request)
      → Promise.all([
          fetchRuleSections()   select * from rule_sections order by position
          fetchRuleItems()      select * from rule_items    order by position
        ])
      → map rows → RulesViewModel (đóng băng)
  → render shell + drawer       (HTML tĩnh, trừ RulesPanelDismiss)
```

### 5.5 Artifact References

`plans/260909-0838-the-le-rules-panel/` — clarifications, design, research, evidence.
