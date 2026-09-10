# Phase 08 — GREEN + visual validation

## Context Links

- `phase-02-e2e-red-gate.md` — `redCommand`, `redExitCode`, `evidence/red-run.txt`
- `research/researcher-02-playwright-harness.md § 5` — hình dạng GREEN, và cái gì KHÔNG phải kết quả hợp lệ
- `clarifications.md § "Layout and behaviour"`, `§ GUI_004` (hover), `§ "Test contract"`
- `design/the-le.png` — frame render 1×, chuẩn để so
- `spec/the-le/technical-spec.md § 5.1`
- `.claude/rules/momorph/momorph-development.md § "Tester Hand-off and Integration"`

## Overview

- **Priority**: P1 — phase cuối, quyết định feature xong hay chưa
- **Status**: **completed** — GREEN đạt (10 passed / 2 skipped, exit 0) và lượt visual đã chạy, tìm ra
  ba lệch V-1/V-2/V-3 rồi trả việc đúng luật. Hai điều **không** như kế hoạch: lượt GREEN phải thêm
  `--timeout=180000` ở CLI, và bước "không hồi quy" cho kết quả **BẤT PHÂN**, không phải xanh. Xem
  § "Sai lệch so với kế hoạch".
- **Description**: Chạy lại **đúng** `redCommand` để đòi GREEN, rồi làm lượt visual validation bằng
  Playwright MCP: so panel đang chạy với `design/the-le.png`, kiểm hover hai nút. `tester` sở hữu
  phase này; không sửa file nguồn nào.

## Key Insights

1. **Command không được đổi.** `npx playwright test e2e/the-le.spec.ts --project=anon` — cùng file,
   cùng project, cùng assertion. Đổi command hay nới assertion để lấy GREEN là làm giả bằng chứng.
2. **Hover là mối lo visual-contract**, không assert trong strict E2E (technical-spec § 5.1). Nó được
   xác nhận ở lượt visual của phase này, bằng ảnh chụp trạng thái hover.
3. **Hai `test.skip` phải vẫn hiện** trong output GREEN với lý do DEC-002. Nếu chúng biến mất, ai đó
   đã xoá test — đó là regression của tính minh bạch, không phải dọn dẹp.
4. **`tester` không sửa code UI.** Lỗi GREEN hoặc lệch thị giác đáng kể → trả bản sửa có giới hạn về
   `momorph-ui-implementer` (Track A) hoặc `implementer` (Track B), KHÔNG làm yếu test.
5. **Seed phải đang ở trong database.** Nếu ai đó chạy `supabase db reset` sau phase 03 mà không seed,
   panel rỗng và GREEN sẽ đỏ vì lý do sai. Kiểm trước khi chạy.

## Requirements

- Toàn bộ FR/BR của feature, gián tiếp qua 9 test của phase 02
- **GUI_004** (hover hai nút) — xác nhận bằng visual, không bằng assertion
- **DEC-002** — hai `test.skip` hiện trong output kèm lý do

## Architecture

Ba lượt, theo thứ tự:

```
1. Tiền đề   → Supabase chạy? seed có trong DB? .env.local có?
2. GREEN     → npx playwright test e2e/the-le.spec.ts --project=anon   (đòi exit 0)
3. Visual    → Playwright MCP: chụp panel, so với design/the-le.png, chụp hover hai nút
```

Bằng chứng đổ vào `evidence/`:

| File | Nội dung |
|---|---|
| `evidence/green-run.txt` | command, exit code, output đầy đủ của lượt GREEN |
| `evidence/visual-panel.png` | panel ở 1440×1796, so trực tiếp với frame |
| `evidence/visual-hover-close.png` | `Đóng` ở trạng thái hover |
| `evidence/visual-hover-write-kudos.png` | `Viết KUDOS` ở trạng thái hover |
| `reports/tester-260909-the-le.md` | verdict + mọi lệch tìm được |

## Related Code Files

**Create**
- `evidence/green-run.txt`, `evidence/visual-*.png`
- `reports/tester-260909-the-le.md`

**Modify** — không file nguồn nào. Nếu phase này thấy cần sửa nguồn, nó **trả việc**, không tự sửa.

**Delete** — không có.

## Implementation Steps

1. **Tiền đề.** `docker ps | grep supabase_db_my-app` phải có. Rồi kiểm seed thật sự nằm trong DB.
   **`psql` KHÔNG có trên PATH của máy này** (đã đo) — chạy trong container, đúng idiom repo:
   ```
   docker exec -i supabase_db_my-app psql -U postgres -d postgres \
     -c "select count(*) from public.rule_sections;" \
     -c "select kind, count(*) from public.rule_items group by kind;"
   ```
   Kỳ vọng 3 / (`hero_tier` 4, `collectible_icon` 6). Sai số → chạy `npx supabase db reset` rồi kiểm
   lại. Vẫn sai → **BLOCKED** về phase 03.
2. **GREEN.** Chạy nguyên văn:
   ```
   npx playwright test e2e/the-le.spec.ts --project=anon
   ```
   Ghi toàn bộ output vào `evidence/green-run.txt` kèm exit code.
3. **Phân loại nếu đỏ.** Đỏ vì assertion → đọc diff, quy về Track A hay Track B, trả việc có giới hạn
   kèm dòng lỗi cụ thể. Đỏ vì browser/webServer/env → sửa hạ tầng rồi chạy lại; đó không phải kết quả
   của app.
4. **Kiểm hai `test.skip` còn nguyên** trong output.
5. **Visual, bằng Playwright MCP.** Mở `http://127.0.0.1:3000/standards` ở 1440×1796 (kích thước
   artboard), chụp panel. So từng mục với `design/the-le.png`:
   - tiêu đề `Thể lệ` 45/52, `#FFEA9E`
   - ba heading mục: hai cái 22/28, `KUDOS QUỐC DÂN` 24/32
   - bốn bậc Hero: ảnh pill + nhãn CÙNG hàng, mô tả dòng dưới
   - lưới icon 3 cột, hai hàng ba, ô 80px, gap 16/24, caption in hoa canh giữa
   - chân drawer: `Đóng` ~94px, `Viết KUDOS` chiếm phần còn lại
   - **bút trên nút vàng có NHÌN THẤY không** (rủi ro số một của feature này)
6. **Hover.** Hover `Đóng` → nền sáng lên (`hover:bg-white/10`). Hover `Viết KUDOS` → vàng tối đi.
   Chụp cả hai.
7. **Responsive.** Thu viewport về 390px, xác nhận drawer tràn hết bề ngang và KHÔNG có thanh cuộn
   ngang (FR-405). Lưới icon 3×80 + 2×16 = 272px vẫn vừa.
8. **Không hồi quy.** Chạy `npx playwright test --project=anon` (cả project) để chắc việc sửa
   `playwright.config.ts` ở phase 02 không làm đỏ suite nào khác.
9. Viết `reports/tester-260909-the-le.md`: verdict, output GREEN, mọi lệch thị giác kèm mức độ, và
   danh sách những gì KHÔNG kiểm được.

## Todo List

- [x] Supabase chạy + seed có trong DB (3 / 4 / 6)
- [x] `npx playwright test e2e/the-le.spec.ts --project=anon` → exit 0, **10 passed / 2 skipped**
      (cộng `--timeout=180000`, xem dưới)
- [x] `evidence/green-run.txt` với command + exit code + output; `evidence/green-run-post-polish.txt`
      cho lượt chạy lại sau khi sửa V-1/V-2
- [x] Hai `test.skip` vẫn hiện kèm lý do DEC-002
- [x] Visual: chụp panel 1440×1796, so từng mục với frame (`evidence/visual-*.png`,
      `evidence/visual-measurements.json`, `evidence/visual-polish-*`)
- [x] **Kiểm bút có thấy được trên nền `#FFEA9E`** — thấy rõ
- [x] Hover `Đóng` và `Viết KUDOS`, chụp cả hai
- [x] Responsive 390px: không cuộn ngang (`evidence/visual-panel-390.png`)
- [ ] ~~`npx playwright test --project=anon` — không suite nào đỏ thêm~~ → **BẤT PHÂN**, không đạt
      được kết luận này. Xem § "Sai lệch so với kế hoạch". Đây là ô duy nhất không tick được.
- [x] Report — ship dưới tên `reports/tester-260909-1100-green-and-visual-validation.md`
      (kế hoạch ghi `tester-260909-the-le.md`; đổi theo quy ước đặt tên `{type}-{date}-{slug}.md`)

## Sai lệch so với kế hoạch (post-phase)

**1. Lượt GREEN phải thêm `--timeout=180000` ở CLI.**
Command cố định chạy **tám lần** đều exit 1 mà **không chạy nổi một test màn nào**: `auth.setup.ts` của
project `[setup]` hết ngân sách 30s/test trong khi `next dev` nguội còn đang compile, và "11 did not
run". Chứng minh đó là ngân sách chứ không phải app: `npx playwright test --project=setup
--timeout=180000` → exit 0, chính test setup đó pass trong 4.2s giữa một lượt 1.6m gần như toàn bộ là
boot `next dev`. `--timeout` là override CLI: **không file nào bị sửa, không assertion nào bị nới**,
`expect()` giữ nguyên mặc định 5s và cả mười assertion màn hình đều pass. Ghi lại vì § Key Insight 1
của phase này đòi command byte-for-byte — điều kiện đó đã bị phá, một cách công khai, và đây là chỗ nó
được ghi (`evidence/green-run-post-polish.txt:6-24`).

**2. Bước 8 "không hồi quy" cho kết quả BẤT PHÂN** (`plan.md § "Đã biết và chấp nhận"`).
`npm run test:e2e` → **70 passed / 26 failed / 94 không chạy**. Mọi failure là timeout 30s của
`auth.setup.ts` trên `next dev` nguội, không diff assertion nào. Đã chứng minh **không** phải hồi quy
của F007: chạy riêng từng spec vẫn đỏ y hệt, kể cả `smoke.spec.ts` vốn có trước feature này
(`evidence/regression-anon-per-spec.txt`). Nhưng "không phải lỗi của chúng ta" **không** đồng nghĩa
"đã kiểm và tốt" — **94 test là CHƯA ĐƯỢC KIỂM**. Timeout của harness xứng đáng một commission riêng.

Hai chữ ký khác, đã ghi nhận nhưng chưa chẩn đoán: `kudos-live-board-authed` K-10/K-25 đỏ ở
20.6s/24.5s — **dưới** trần 30s, nên không phải cùng nguyên nhân.

**3. Lượt visual tìm ra ba lệch, cả ba đã sửa và chạy lại GREEN** — đúng vòng "trả việc, không tự sửa"
mà Key Insight 4 đặt ra:

| Lệch | Nội dung | Trả về |
|---|---|---|
| **V-1** | Caption icon không xuống dòng: track grid resolve về max-content nên ô 147px / pitch 163px thay vì 80px / 148.5px; gap dọc 24px thay vì 16px | phase 06 (`plan.md § PP-4`) |
| **V-2** | Mất 20px thụt trái của hàng bậc Hero | phase 06 (`plan.md § PP-4`) |
| **V-3** | Caption icon 6 sai chữ: `ROOT FUTHER` — đọc `itemName` thay vì `character` của node | phase 03 + fixture phase 02 (`plan.md § PP-3`) |

Hai lệch cố ý **không** sửa, đã cân nhắc: pitch hàng bậc Hero 84 vs 88px (chênh 4px là line box mô tả
40 vs 44, không phải khoảng cách hardcode) và font caption 12px vs 11px frame khai (12px tái hiện đúng
số dòng và chiều cao instance; 11px làm lệch cả hai).

**4. Review H1 (`aria-modal`) đến từ lượt này** — xem `plan.md § PP-2` và phase 07 § "Sai lệch". Nó
sửa contract đã đóng băng, theo hướng **mạnh lên** (assert vắng mặt), không phải nới ra.

## Success Criteria

- `npx playwright test e2e/the-le.spec.ts --project=anon` **exit 0** — đạt: 10 passed (9 test màn +
  `[setup]`) / 2 skipped.
- Output GREEN đến từ **cùng command** phase 02 đã dùng cho RED — **đạt một phần**: cùng file, cùng
  project, cùng assertion, nhưng có thêm `--timeout=180000` ở CLI (§ "Sai lệch so với kế hoạch" § 1).
- ~~`npx playwright test --project=anon` không đỏ thêm suite nào so với trước feature~~ → **BẤT PHÂN**
  (§ "Sai lệch so với kế hoạch" § 2). Đã loại trừ F007 là nguyên nhân; chưa chứng minh được toàn suite xanh.
- Ảnh chụp panel khớp `design/the-le.png` ở: thứ tự mục, đếm 4 bậc + 6 icon, bố cục lưới 3 cột, chân
  drawer hai nút. Lệch nhỏ về khoảng cách được ghi lại, không tự sửa.
- Bút trên nút `Viết KUDOS` **nhìn thấy được** — tương phản rõ với nền vàng.
- Hai ảnh hover cho thấy đổi trạng thái thật.
- 390px: không thanh cuộn ngang.

## Risk Assessment

| Risk | Likelihood | Impact | Countermove |
|---|---|---|---|
| Seed không có trong DB → GREEN đỏ vì lý do sai | **Cao** — `db reset` hay bị chạy giữa chừng | Cao — chẩn đoán sai, trả việc nhầm chỗ | Bước 1 là gate bắt buộc trước khi chạy test |
| Nới assertion / đổi command để lấy GREEN | Trung bình | **Rất cao** — bằng chứng giả | Key Insight 1 + so byte dòng command ở Success Criteria |
| Xoá hai `test.skip` cho "sạch" output | Trung bình | Cao — mất minh bạch DEC-002 | Bước 4 + Success Criteria đòi 2 skipped |
| `tester` tự sửa UI cho xanh | Trung bình | Cao — phá ownership, mất dấu vết | Key Insight 4; § Related Code Files: không file nguồn nào |
| `FUN_002` không đạt vì nội dung luôn dài hơn viewport | Trung bình | Trung bình | Phase 02 đã dựng bậc viewport; nếu vẫn không đạt, báo DONE_WITH_CONCERNS kèm số đo thật |
| Lệch thị giác nhỏ bị thổi thành blocker | Trung bình | Thấp — vòng lặp thừa | Ghi mức độ cho từng lệch; chỉ lệch ĐÁNG KỂ mới trả việc |
| Sửa `playwright.config.ts` ở phase 02 làm đỏ suite khác | Thấp | Cao | Bước 8 chạy cả project `anon` |

**Rollback**: phase này không đổi file nguồn nào, nên không có gì để hoàn tác. Nếu GREEN không đạt
được sau hai vòng trả việc, escalate lên người dùng thay vì vòng thứ ba mù.

## Security Considerations

- Lượt chạy dùng project `anon`, không session, không tạo user Supabase Auth — không rác identity.
- Spec không ghi dữ liệu, nên không cần cleanup và không làm lệch giả định của `profile.spec.ts` /
  `kudos-*.spec.ts` về số Kudos của sunner id 1/2.
- **Ảnh chụp không được chứa dữ liệu cá nhân thật.** `/standards` chỉ render nội dung thể lệ công khai;
  nhưng `HomeHeader` ở trạng thái đã đăng nhập có thể hiện tên/email. Chụp ở trạng thái **anon** để
  `evidence/*.png` commit được an toàn. Repo là private, nhưng đó không phải lý do để cẩu thả.
- Xác nhận lại một lần bằng đo, không bằng niềm tin, rằng `anon` vẫn không ghi được vào hai bảng:
  ```
  docker exec -i supabase_db_my-app psql -U postgres -d postgres \
    -c "set role anon; insert into public.rule_items (kind,position,label,image_path) values ('hero_tier',9,'x','/y');"
  ```
  Kỳ vọng: lỗi. Thành công = FR-601 hỏng, và đó là blocker bất kể E2E xanh thế nào.

## Next Steps

- GREEN + visual đạt → feature xong về mặt code. Bàn giao còn lại (ngoài scope các phase):
  - `reviewer` đọc toàn bộ diff trước khi mở PR
  - `doc-writer` cấp `PERM###` cho `rule_sections`/`rule_items` trong
    `docs/generated/permissions-matrix.md`, dựng `docs/features/F007_TheLe/`, cập nhật
    `docs/generated/{route-list,screen-list,feature-list}.md` và `docs/_canonical-fcodes.json`
  - `delivery-tracker` chuyển `plan.md` sang `status: completed`
- Việc còn treo, cố ý ngoài scope: nối 6 artwork icon vào `app/profile/_components/profile-badge-row.tsx`
  (RISK-01) — commission riêng, vì nó sửa một màn đã ship mà frame này không nói gì về nó.
