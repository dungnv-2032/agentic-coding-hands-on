---
title: "F007 Thể lệ (SCR007)"
description: "Thay ComingSoon ở /standards bằng drawer 553px đọc nội dung thể lệ từ hai bảng Supabase mới, dưới gate E2E RED-first."
status: completed
priority: P1
effort: 11h
branch: main
tags: [f007, the-le, standards, momorph, supabase, e2e-red-first]
created: 2026-09-09
completed: 2026-09-09
spec: plans/260909-0838-the-le-rules-panel/spec/the-le/
---

# F007 — Thể lệ

Spec input: `spec/the-le/{functional,technical}-spec.md` · hệ thống `spec/system/{architecture,permissions}.md`.
Authority: `clarifications.md` · frame `design/the-le.png` · MoMorph https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/b1Filzi9i6 (node `3204:6051`).
Nghiên cứu ràng buộc: `research/researcher-01-supabase-and-i18n-conventions.md`, `research/researcher-02-playwright-harness.md`.

**test_policy: `e2e-red-first`** (đã chốt, không mở lại) · `redCommand`: `npx playwright test e2e/the-le.spec.ts --project=anon`
(lượt GREEN cuối phải thêm `--timeout=180000` ở CLI vì `auth.setup.ts` hết ngân sách 30s trên `next dev`
nguội — không file nào sửa, không assertion nào nới; phase 08 § "Sai lệch so với kế hoạch")

## Ba sự thật đo được, đọc trước khi bắt đầu

1. **`public/images/rules/pen-icon.svg` KHÔNG có trên đĩa** — thư mục chỉ có 11/12 file. Và
   `public/images/home/widget-pen-icon.svg` (cùng node `186:1763`) là `fill="white"`, trong khi frame
   vẽ bút MÀU TỐI trên nền `#FFEA9E`. Tái dùng nguyên file có sẵn sẽ cho một cái bút trắng vô hình
   trên nền vàng. Giả định A2 của technical-spec KHÔNG đứng vững — xử lý ở phase 06.
2. **`/standards` hiện render `ComingSoon`** (`app/standards/page.tsx`), nên spec RED ở phase 02 fail
   bằng đúng một `expect(getByTestId("rules-panel")).toBeVisible()` timeout trên app đang chạy thật —
   một RED assertion hợp lệ, không phải lỗi config.
3. **F007 là fcode còn trống** (`docs/_canonical-fcodes.json` mới tới F006), và chưa có mã `PERM###`
   nào cấp cho hai bảng mới — `doc-writer` cấp lúc delivery, không phải việc của các phase dưới đây.

## Phases

| # | Phase | Track | Owner | Effort | Status |
|---|-------|-------|-------|--------|--------|
| 01 | [Contract đóng băng + khối `rules` i18n](phase-01-contract-and-i18n.md) | Foundation | implementer | 1h | completed — 3/6 key chrome, xem PP-5 |
| 02 | [E2E RED gate — `e2e/the-le.spec.ts` dưới project `anon`](phase-02-e2e-red-gate.md) | Test | tester | 1.5h | completed — contract sửa sau, xem PP-2/PP-3 |
| 03 | [Migration hai bảng + seed + `db:types`](phase-03-migration-seed-types.md) | B | implementer | 1.5h | completed — seed sửa lại, xem PP-3 |
| 04 | [Tầng dữ liệu `lib/rules/`](phase-04-rules-data-layer.md) | B | implementer | 1h | completed — đúng như kế hoạch |
| 05 | [Track A — mục văn xuôi + cụm đóng panel](phase-05-track-a-sections-and-dismiss.md) | A | momorph-ui-implementer | 2h | completed — dismiss viết lại, xem PP-1/PP-6 |
| 06 | [Track A — bậc Hero, lưới icon, asset bút](phase-06-track-a-tiers-and-icons.md) | A | momorph-ui-implementer | 1.5h | completed — bố cục sửa sau, xem PP-4/PP-5 |
| 07 | [Tích hợp — vỏ drawer + `app/standards/page.tsx`](phase-07-integration-panel-and-page.md) | Integration | implementer | 1.5h | completed — bỏ `aria-modal`, xem PP-2 |
| 08 | [GREEN + visual validation](phase-08-green-and-visual-validation.md) | Test | tester | 1h | completed — GREEN đạt, full-suite bất phân |

**Kết quả đo cuối cùng:** `npm run typecheck` exit 0 · `npm run lint` exit 0 (29 warning có từ trước,
toàn bộ nằm trong `e2e/*.spec.ts` cũ) · `npm run build` exit 0, `/standards` là route động ·
`npx playwright test e2e/the-le.spec.ts --project=anon` → **10 passed / 2 skipped, exit 0**
(`evidence/green-run.txt`, `evidence/green-run-post-polish.txt`).

## Dependency graph

```
01 ──> 02 ──┬─> 03 ──> 04 ──────┐
            ├─> 05 (Track A) ───┼─> 07 ──> 08
            └─> 06 (Track A) ───┘
```

- **01 chặn mọi thứ** — nó đóng băng `RulesViewModel` và `Dictionary["rules"]` để hai track dựng
  trên cùng một biên.
- **02 chặn 03–06** (`e2e-red-first`): một RED hợp lệ, gây ra bởi assertion của màn này chứ không phải
  bởi config / cài browser / dev server, LÀ cửa mở cho toàn bộ phần dựng.
- **03 → 04 sequential** (`database.types.ts` phải sinh xong trước khi `queries.ts` type được).
- **03, 04 chạy song song với 05, 06** — Track B và Track A không chạm file của nhau.
- **07 là phase DUY NHẤT** đụng `app/standards/page.tsx` và `rules-panel.tsx` (chỗ ráp mọi mảnh).

## File-ownership map (không hai phase song song nào chung đường dẫn)

| Phase | Owns |
|---|---|
| 01 | `lib/rules/view-model.ts`, `lib/i18n/messages/{dictionary,vi,en,vi-rules,en-rules}.ts` |
| 02 | `e2e/the-le.spec.ts`, `e2e/fixtures/the-le-constants.ts`, `playwright.config.ts` |
| 03 | `supabase/migrations/20260909093000_the_le_rules_content.sql`, `supabase/seed.sql`, `lib/supabase/database.types.ts` |
| 04 | `lib/rules/{queries,rules-data}.ts` |
| 05 | `app/standards/_components/{rules-section,rules-panel-dismiss}.tsx` |
| 06 | `app/standards/_components/{rules-hero-tier-list,rules-collectible-grid}.tsx`, `public/images/rules/pen-icon.svg` |
| 07 | `app/standards/_components/rules-panel.tsx`, `app/standards/page.tsx` |
| 08 | `evidence/`, `reports/` (không file nguồn nào) |

## Standing constraints

- **Mọi file code < 200 dòng** (`.claude/rules/development-rules.md`) — mọi lần chia đã đặt tên sẵn
  trong phase, không phát hiện dọc đường.
- **Không seed `ON CONFLICT`** — idiom của repo là "reset truncates, plain insert".
- **`order by position` là bắt buộc** ở cả hai query (BR-001).
- **Không bịa dữ liệu.** Mọi chuỗi tiếng Việt phiên âm nguyên văn từ
  `clarifications.md § "Resolved from source data"`, kể cả en-dash `10–20`. (`ROOT FUTHER` từng nằm
  trong danh sách này — sai, xem PP-3: đó là tên layer, không phải chữ được render.)
- **Không thêm dependency npm, không scaffold runner mới.** `@playwright/test ^1.62.1` đã có.
- **Không đụng `profile-badge-row.tsx`** (F006) — nối 6 artwork vào đó là commission khác (RISK-01).
- Rollback: phase 03 § Risk (migration + seed), phase 07 § Risk (thay `ComingSoon`).

## Sau khi các phase đóng

Sáu thay đổi xảy ra SAU khi các phase file đã viết xong. Không phase nào mô tả chúng, nên chúng nằm
ở đây; phase liên quan trỏ ngược về mục này.

| # | Việc | Phase bị đè lên | Đã đo ở đâu |
|---|------|-----------------|-------------|
| **PP-1** | `FUN_003b` đỏ thật: `window.history.length > 1` (giả định A1) sai — Chromium bị lái giữ `about:blank` ban đầu trong history, nên deep link đi nhánh `router.back()` và rơi vào `about:blank`, đúng ngõ cụt BR-004 cấm. Nay feature-detect `navigation.canGoBack`, `history.length` là fallback. A1 trong technical-spec viết lại từ "đứng vững" thành **BÁC BỎ**. | 05 | `rules-panel-dismiss.tsx:18-51`; `docs/features/F007_TheLe/technical-spec.md § 5.2` |
| **PP-2** | **Bỏ `aria-modal`** (review H1). Panel khai modality nhưng không dựng focus trap và vẫn để header/footer trong tab order — một lời hứa không giữ được. Giữ `role="dialog"` + `aria-labelledby`. E2E nay assert `aria-modal` **VẮNG MẶT**. Đây là lần sửa contract đã đóng băng trong `clarifications.md` và FR-201 ở cả hai functional-spec. | 02, 07 | `rules-panel.tsx:57-97`; `e2e/the-le.spec.ts:66-72` |
| **PP-3** | `ROOT FUTHER` → **`ROOT FURTHER`**. Bản chép đầu đọc `itemName` (tên layer) của node Figma thay vì `character` (chữ được render). Đọc lại qua MoMorph mới chốt được. Sửa ở seed, fixture E2E, `clarifications.md` và cả hai functional-spec; DB seed lại. | 02, 03 | `supabase/seed.sql:367-397`; `e2e/fixtures/the-le-constants.ts:17-78` |
| **PP-4** | Lệch thị giác V-1/V-2 sửa: hộp caption icon ép về đúng 80px của frame để caption xuống dòng như thiết kế (ô 147px → 80px, pitch 163 → 148.5px, số dòng khớp frame), và trả lại 20px thụt trái của hàng bậc Hero. Gap dọc lưới icon 24px → **16px** theo node `3204:6080`. | 06 | `rules-collectible-grid.tsx:22-32`; `rules-hero-tier-list.tsx:44-56` |
| **PP-5** | **Xoá key i18n chết** sau khi component chọn `alt=""` trang trí + `aria-labelledby`: `heroTierImageAlt`, `collectibleIconImageAlt`, `panelAriaLabel`. Khối `Dictionary["rules"]` còn đúng 3 key thay vì 6 như phase 01 dựng. Prop `imageAltTemplate` của hai component cũng biến mất theo. | 01, 06 | `lib/i18n/messages/dictionary.ts:302-307`, `vi-rules.ts` |
| **PP-6** | Thêm chốt chống va Escape (`event.defaultPrevented`) — handler Escape cấp `document` của language-selector cũng đang đóng luôn panel và đá người dùng khỏi trang. | 05 | `rules-panel-dismiss.tsx:97-114` |

## Đã biết và chấp nhận — ghi nhận trạng thái, không phải việc đang mở

- **Full-suite E2E BẤT PHÂN, không phải xanh.** `npm run test:e2e` → 70 passed / 26 failed / 94 không
  chạy; mọi failure là timeout 30s của `auth.setup.ts` trên `next dev` nguội, không diff assertion nào.
  Đã chứng minh **KHÔNG** phải hồi quy của F007: chạy riêng từng spec vẫn đỏ y hệt, kể cả
  `smoke.spec.ts` có trước feature này (`evidence/regression-anon-per-spec.txt`). Nhưng 94 test là
  **CHƯA ĐƯỢC KIỂM**, không phải đã kiểm và tốt. Timeout của harness xứng đáng một commission riêng.
- `kudos-live-board-authed` K-10/K-25 đỏ ở 20.6s/24.5s — dưới trần, chữ ký khác. Đã ghi nhận, chưa chẩn đoán.
- Không có unit test cho nhánh bảng rỗng / lỗi query — repo không có unit-test runner, dựng một cái là ngoài scope.
- `anon` có TRUNCATE trên mọi bảng public qua default privileges của Supabase — có từ trước, toàn repo
  (tái hiện được trên `board_stats` của F004), không với tới được qua PostgREST, cố ý không vá riêng một bảng.
- Pitch hàng bậc Hero 84px so với 88px của frame — 4px chênh là line box của mô tả (40 vs 44), không hardcode.
- Font caption 12px so với 11px frame khai — giữ, vì nó tái hiện đúng số dòng và chiều cao instance của frame.
- `PERM###` cho hai bảng mới **cố ý chưa cấp** — `doc-writer` cấp lúc delivery.
- **RISK-01 còn nguyên**: 6 artwork icon đã vào repo trong khi `profile-badge-row.tsx` (F006) vẫn vẽ
  vòng tròn phẳng `#323231`.
