# Phase 02 — E2E RED gate (`e2e/the-le.spec.ts`, project `anon`)

## Context Links

- `research/researcher-02-playwright-harness.md` — projects, `testMatch`, RED hợp lệ là gì (§ 5), selector conventions (§ 3)
- `clarifications.md § "Test contract"` — bảng `data-testid`, ràng buộc cứng giữa spec và UI
- `clarifications.md § "Resolved from source data"` — nguồn phiên âm cho `the-le-constants.ts`
- `spec/the-le/functional-spec.md § 10` — "Edge Behaviours to Verify"
- `spec/the-le/technical-spec.md § 5.1` — testPolicy và preflight
- House style: `e2e/profile-anon.spec.ts`, `e2e/fixtures/profile-constants.ts`, `playwright.config.ts`

## Overview

- **Priority**: P1 — cửa gate của `e2e-red-first`; 03–06 không được bắt đầu trước khi phase này RED hợp lệ
- **Status**: **completed** — RED hợp lệ đạt được, gate mở đúng luật (`evidence/red-run.txt`,
  `evidence/red-run-full-output.txt`, `reports/tester-260909-1002-e2e-red-gate.md`). Nhưng contract
  đóng băng ở đây **đã bị sửa hai lần sau đó** — xem § "Sai lệch so với kế hoạch".
- **Description**: Viết một spec E2E cấp màn hình, đăng ký dưới project `anon`, và chạy nó tới một
  **RED assertion hợp lệ** — exit non-zero do `expect()` lệch với app đang chạy thật, không do
  config / cài browser / dev server. Bằng chứng RED được ghi lại và truyền read-only sang phase 05–07.

## Key Insights

1. **RED sẽ đến "miễn phí" và đúng cách.** `/standards` hiện render `ComingSoon` (`app/standards/page.tsx`),
   nên trang trả 200 và `getByTestId("rules-panel")` không tồn tại → `toBeVisible()` timeout. Đó là
   một `expect()` lệch với app thật, đúng định nghĩa RED hợp lệ ở researcher-02 § 5.
2. **Không cần setup project.** `/standards` công khai — `proxy.ts` chỉ canh `/todo`, `/kudos/new`
   (exact) và `/profile`. Chỉ cần thêm `the-le` vào regex `testMatch` của project `anon`
   (researcher-02 § 4).
3. **Seed CHÍNH LÀ fixture.** Panel không render mục nào nếu hai bảng rỗng. Spec không ghi dữ liệu
   nên KHÔNG cần block cleanup — khác với `profile.spec.ts` SEC_002.
4. **Chuỗi tiếng Việt không được inline.** Mọi copy đọc qua hằng số export từ
   `e2e/fixtures/the-le-constants.ts` (researcher-02 § 3), phiên âm từ `clarifications.md`.
5. **Đây là spec DUY NHẤT được sửa `playwright.config.ts`.** Không phase nào khác chạm file đó.

## Requirements

- **FR-201** — `<h1>` đọc đúng `Thể lệ`; `rules-panel` mang `role="dialog"` + `aria-modal="true"`
- **FR-202/203/204** — đếm và thứ tự: 3 `rules-section`, 4 `rules-hero-tier`, 6 `rules-collectible-icon`
- **FR-401 / BR-004** — `Đóng` quay lại trang trước; deep link thì về `/`
- **FR-402 / BR-005** — `Viết KUDOS` là `<a href="/kudos/new">`, kiểm bằng THUỘC TÍNH không bằng điều hướng
- **FR-403** — `rules-panel-content` cuộn độc lập: `scrollHeight > clientHeight`
- **BR-001** — thứ tự render khớp `position`, kiểm bằng so chuỗi caption theo đúng thứ tự thiết kế
- **DEC-002** — `TC_THELE_GUI_003` và `TC_THELE_FUN_005` vào suite dưới dạng `test.skip` kèm lý do inline

## Architecture

`e2e/fixtures/the-le-constants.ts` — hằng số phiên âm, không logic:

```ts
export const ROUTE = "/standards";
export const PANEL_TITLE = "Thể lệ";
export const SECTION_HEADINGS = [
  "NGƯỜI NHẬN KUDOS: HUY HIỆU HERO CHO NHỮNG ẢNH HƯỞNG TÍCH CỰC",
  "NGƯỜI GỬI KUDOS: SƯU TẬP TRỌN BỘ 6 ICON, NHẬN NGAY PHẦN QUÀ BÍ ẨN",
  "KUDOS QUỐC DÂN",
] as const;
export const HERO_TIER_LABELS = [
  "Có 1-4 người gửi Kudos cho bạn",
  "Có 5-9 người gửi Kudos cho bạn",
  "Có 10–20 người gửi Kudos cho bạn",   // en-dash, nguyên văn frame
  "Có hơn 20 người gửi Kudos cho bạn",
] as const;
export const COLLECTIBLE_CAPTIONS = [
  "REVIVAL", "TOUCH OF LIGHT", "STAY GOLD",
  "FLOW TO HORIZON", "BEYOND THE BOUNDARY", "ROOT FUTHER",  // sic — nguyên văn node text
] as const;
export const CLOSE_LABEL = "Đóng";
export const WRITE_KUDOS_LABEL = "Viết KUDOS";
export const COMPOSE_ROUTE = "/kudos/new";
```

Header file trỏ về `clarifications.md` là nguồn, và ghi rõ hai chỗ "trông như lỗi" (`10–20` en-dash,
`ROOT FUTHER`) là CỐ Ý, để không ai "sửa" chúng.

Bộ test trong `e2e/the-le.spec.ts`:

| Case | Maps to | Assertion |
|---|---|---|
| `GUI_001` | FR-201 | `<h1>` = `PANEL_TITLE`; `rules-panel` visible, `role="dialog"`, `aria-modal="true"` |
| `GUI_002` | FR-202 | 3 `rules-section`, heading thứ i chứa `SECTION_HEADINGS[i]` — chứng minh thứ tự `position` |
| `GUI_005` | FR-203 | 4 `rules-hero-tier`, label thứ i = `HERO_TIER_LABELS[i]`, mỗi ô có `<img>` |
| `GUI_006` | FR-204 | 6 `rules-collectible-icon`, caption thứ i = `COLLECTIBLE_CAPTIONS[i]`, mỗi ô có `<img>` |
| `FUN_001` | FR-403 | `rules-panel-content`: `scrollHeight > clientHeight` ở viewport mặc định |
| `FUN_002` | FR-403 | ở viewport cao (`setViewportSize` 1440×2400): `scrollHeight === clientHeight` |
| `FUN_003` | FR-401 | vào `/` → click link tới `/standards` → click `rules-close-button` → `page.url()` về `/` |
| `FUN_003b` | BR-004 | `goto("/standards")` trực tiếp (deep link) → `Đóng` → URL là `/` |
| `FUN_004` | FR-402 | `rules-write-kudos-link` có `getAttribute("href") === COMPOSE_ROUTE` |
| `GUI_003` | DEC-002 | `test.skip` — lý do inline |
| `FUN_005` | DEC-002 | `test.skip` — lý do inline |

**`FUN_002` — cách làm cho nó thật.** Nội dung đã seed dài hơn 553×~900, nên "nội dung vừa khít" phải
được tạo bằng cách nâng chiều cao viewport, không bằng cách xoá dữ liệu. `setViewportSize({ width: 1440,
height: 2400 })` trước `goto` cho panel `h-svh` cao 2400px — cao hơn nội dung → không có khoảng cuộn.
Nếu ở 2400px nội dung VẪN dài hơn, tăng lên 3200px; ghi con số thực đo được vào comment của test.

**`FUN_003` — lấy đâu ra một history entry.** Không dùng `page.goBack()` (đó là kiểm trình duyệt, không
kiểm nút). Điều hướng thật: `goto("/")`, rồi `page.goto("/standards")` KHÔNG tạo history client-side
đáng tin — thay vào đó click chính lối tắt `Thể lệ SAA` của floating widget trên trang chủ
(`vi-home.ts:79`, trỏ `/standards`). Nếu widget không hiện ở viewport mặc định, fallback: `goto("/")`
rồi `page.evaluate(() => history.pushState({}, "", "/standards"))` là KHÔNG chấp nhận được (giả lập).
Fallback đúng là click bất kỳ `<a href="/standards">` nào có thật trên `/` (chân trang
`footer.standards` luôn có). Ghi rõ selector đã dùng vào comment.

## Related Code Files

**Create**
- `e2e/fixtures/the-le-constants.ts`
- `e2e/the-le.spec.ts`

**Modify**
- `playwright.config.ts` — thêm `the-le` vào regex `testMatch` của project `anon`:
  `/(?:smoke|login-screen|route-guard|callback-security|homepage|award-system|profile-anon|the-le|kudos-live-board(?!-authed))\.spec\.ts/`

**Delete** — không có.

## Implementation Steps

1. Xác nhận tiền đề: Supabase local đang chạy (`docker ps` thấy `supabase_db_my-app`), `.env.local`
   tồn tại với `NEXT_PUBLIC_SUPABASE_URL` / `NEXT_PUBLIC_SUPABASE_ANON_KEY` / `NEXT_PUBLIC_SITE_URL`.
   Thiếu bất kỳ thứ nào → **BLOCKED**, không phải RED.
2. Viết `e2e/fixtures/the-le-constants.ts` theo § Architecture, phiên âm từ `clarifications.md`.
3. Viết `e2e/the-le.spec.ts` với 9 test chạy + 2 `test.skip`, dùng `getByTestId` theo bảng test
   contract, copy đọc từ hằng số.
4. Sửa regex `testMatch` của project `anon` trong `playwright.config.ts`.
5. Chạy:
   ```
   npx playwright test e2e/the-le.spec.ts --project=anon
   ```
6. **Phân loại kết quả trước khi gọi tên nó là RED.** Chỉ chấp nhận output có `1)` + tên test +
   dòng `expect(...)` / `page.getByTestId(...)` trỏ vào hành vi app, kết thúc bằng `N failed`.
   Từ chối và xử lý riêng: `browserType.launch: ... shared libraries` (cài browser),
   `Process from config.webServer was not able to start` (dev server),
   `Missing NEXT_PUBLIC_SUPABASE_URL` (env), `ECONNREFUSED` (Supabase chưa chạy).
7. Ghi bằng chứng vào `evidence/red-run.txt`: `redCommand`, `redExitCode`, và trích đoạn output có
   `1)` + dòng assertion. Ghi `redTestFiles: ["e2e/the-le.spec.ts"]`.
8. `npm run lint` để spec mới không làm hỏng gate lint.

## Todo List

- [x] Xác nhận Supabase local + `.env.local` (tiền đề, không phải RED)
- [x] `e2e/fixtures/the-le-constants.ts` phiên âm nguyên văn (`10–20` giữ nguyên; `ROOT FUTHER` **sau
      đó được sửa thành `ROOT FURTHER`** — xem dưới)
- [x] `e2e/the-le.spec.ts` — 9 test + 2 `test.skip` kèm lý do DEC-002
- [x] `the-le` vào regex `testMatch` project `anon` (`playwright.config.ts:82`)
- [x] Chạy `npx playwright test e2e/the-le.spec.ts --project=anon`
- [x] Phân loại failure: assertion RED hay lỗi hạ tầng
- [x] `evidence/red-run.txt` với command + exit code + trích đoạn
- [x] `npm run lint` sạch

## Sai lệch so với kế hoạch (post-phase)

**1. `GUI_001` bị đảo chiều — `aria-modal` giờ phải VẮNG MẶT** (`plan.md § PP-2`).
Bảng test ở § Architecture ghi `role="dialog"`, `aria-modal="true"`. Review H1 ở phase 08 bác bỏ:
panel không dựng focus trap và vẫn để header/footer trong tab order, nên `aria-modal="true"` là một
lời hứa với screen reader mà UI không giữ. Thuộc tính bị bỏ, và spec sửa thành
`await expect(panel).not.toHaveAttribute("aria-modal", /.*/)` (`e2e/the-le.spec.ts:66-72`) — assertion
mạnh lên chứ không bị nới. Đây là **lần sửa contract đã đóng băng**: `clarifications.md § "Test
contract"` và FR-201 ở cả hai functional-spec đều được sửa theo, không có chỗ nào còn nói `aria-modal`.

**2. `COLLECTIBLE_CAPTIONS[5]` sửa `ROOT FUTHER` → `ROOT FURTHER`** (`plan.md § PP-3`).
Header file phiên âm ban đầu bảo vệ `ROOT FUTHER` như "nguyên văn node text" — đọc nhầm `itemName`
(tên layer) thay vì `character` (chữ được render). Đọc lại qua MoMorph mới chốt được. Fixture nay ghi
`ROOT FURTHER` kèm lý do nguyên văn ở `the-le-constants.ts:17-20`. **`10–20` en-dash thì đúng và giữ
nguyên** — đừng lấy lần sửa này làm cớ "dọn" nốt chỗ kia.

**3. `FUN_003b` là test bắt được lỗi thật.** Nó đỏ ở phase 07 không phải vì UI chưa dựng mà vì logic
dismiss sai (`plan.md § PP-1`) — deep link rơi vào `about:blank`, đúng ngõ cụt BR-004 cấm. Một RED
gate làm được việc nó sinh ra để làm.

## Success Criteria

- `npx playwright test e2e/the-le.spec.ts --project=anon` exit **non-zero**.
- Output chứa ít nhất một `1) [anon] › e2e/the-le.spec.ts:...` kèm dòng `expect`/`getByTestId`
  trỏ vào `rules-panel` (hoặc testid khác của màn này) — **không** phải lỗi browser/webServer/env.
- Hai `test.skip` hiện trong output với lý do DEC-002, không biến mất im lặng.
- `evidence/red-run.txt` tồn tại và ghi đủ `redCommand` / `redExitCode` / trích đoạn.
- Các suite khác không đỏ thêm vì sửa `playwright.config.ts`: chạy kiểm chứng
  `npx playwright test --project=anon --list` và xác nhận số spec tăng đúng 1.

## Risk Assessment

| Risk | Likelihood | Impact | Countermove |
|---|---|---|---|
| Nhầm lỗi hạ tầng thành RED hợp lệ | **Cao** — WSL2 hay thiếu lib Chromium | **Cao** — mở gate sai, cả plan dựng trên nền giả | Bước 6 liệt kê 4 chữ ký loại trừ; `.playwright-libs/` là workaround đã có trong config |
| Regex `testMatch` bắt nhầm/sót | Trung bình | Trung bình — spec không chạy, "0 tests" trông như pass | `--list` ở Success Criteria bắt đúng lỗi này |
| `FUN_002` không bao giờ đạt `scrollHeight === clientHeight` | Trung bình | Thấp | Nâng viewport theo bậc (2400 → 3200), ghi số đo thật vào comment; nếu vẫn không đạt, báo DONE_WITH_CONCERNS chứ không xoá test |
| `FUN_003` không có history entry thật | Trung bình | Trung bình | Click `<a href="/standards">` có thật ở chân trang; cấm `history.pushState` giả lập |
| RED "quá tốt" — mọi test fail vì trang là `ComingSoon` | Chắc chắn | Không — đúng như thiết kế | Đây là RED mong đợi; phase 08 mới là nơi đòi GREEN |

**Rollback**: `git checkout -- playwright.config.ts && rm e2e/the-le.spec.ts e2e/fixtures/the-le-constants.ts`.
Không dữ liệu nào bị ghi, không migration nào chạy.

## Security Considerations

- Spec chạy dưới project `anon`, **không** storageState, **không** `createTestSession()` — không tạo
  user Supabase Auth nào, nên không rác identity tồn dư giữa các lần chạy.
- Spec **không ghi dữ liệu**: không `insert`, không `create_kudos()`, không heart toggle. Vì vậy
  không cần cleanup, và không có nguy cơ làm lệch giả định của `profile.spec.ts` / `kudos-*.spec.ts`
  về số Kudos của sunner id 1/2.
- `FUN_004` kiểm `href` chứ không điều hướng thật — cố ý: điều hướng thật dưới `anon` sẽ chạm
  redirect của `proxy.ts` sang `/login` và biến một test nội dung thành một test guard.

## Next Steps

- **Mở gate cho**: phase 03, 05, 06 (chạy được ngay, song song).
- **Bàn giao read-only** sang phase 05/06/07: `redCommand`, `redExitCode`, `redTestFiles`,
  `redFailure` (dòng assertion đầu tiên), `redEvidence` (`evidence/red-run.txt`).
- **Phase 08** chạy lại đúng `redCommand` này để đòi GREEN — không đổi command, không nới assertion.
