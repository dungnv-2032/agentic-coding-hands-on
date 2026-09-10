---
status: draft
authored_by: takumi
created: 2026-09-09
lang: vi
---

**Priority**: P1
**Type**: mixed

## 1. Overview

**Problem:** `/standards` từ F002 tới nay vẫn là một `ComingSoon` (`app/standards/page.tsx`) — chân trang (`footer.standards`) và lối tắt của floating widget (`vi-home.ts:79`, nhãn `Thể lệ SAA`) đều trỏ vào đó, nên route đã LÀ route Thể lệ ở mọi mặt trừ nội dung. Người dùng không có chỗ nào đọc được luật chơi: huy hiệu Hero mở khoá theo ngưỡng nào, 6 icon sưu tập là gì, Kudos Quốc Dân được trao ra sao. Toàn bộ những con số đó đang nằm rải rác trong code (`badgeTierFor`) và trong đầu ban tổ chức, không ở đâu người dùng đọc được.
**Solution:** Thay `ComingSoon` bằng một drawer 553px bám mép phải trên nền shell chuẩn (`HomeHeader` + `main` tối + `SiteFooter`), dựng đúng frame MoMorph `3204:6051`: tiêu đề `Thể lệ`, ba mục nội dung có thứ tự, 4 bậc huy hiệu Hero kèm ảnh pill, 6 icon sưu tập hai hàng ba, và chân drawer hai nút `Đóng` / `Viết KUDOS`. Nội dung KHÔNG hardcode: hai bảng mới `public.rule_sections` + `public.rule_items` giữ toàn bộ chữ, đọc mỗi request qua `lib/rules/`.
**Scope:** Migration hai bảng + RLS public-read + grants; seed toàn bộ nội dung phiên âm từ frame; `lib/rules/` (queries + data + view-model); `app/standards/page.tsx` thật + `_components/`; khối `rules` trong `Dictionary` (vi + en); 12 asset ảnh dưới `public/images/rules/`; spec E2E `e2e/the-le.spec.ts` đăng ký dưới project `anon`.
**Non-Scope:** Nối 6 artwork icon vào `profile-badge-row.tsx` của F006 (màn hình đã ship, frame này không nói gì về nó); cột `locale` cho nội dung thể lệ (frame chỉ có tiếng Việt — thêm cột chỉ để bịa bản dịch); màn hình quản trị sửa nội dung thể lệ; trạng thái `disabled` của hai nút chân drawer (§ 3, DEC-002).

**Actors**

| Actor | Description | Primary goal |
|-------|--------------|---------------|
| Khách vãng lai (chưa đăng nhập) | Bất kỳ ai mở `/standards` — route công khai, `proxy.ts` không chặn | Đọc thể lệ chương trình trước khi quyết định tham gia |
| Sunner (đã đăng nhập) | Nhân viên Sun* đã đăng nhập | Đọc thể lệ rồi đi thẳng sang form viết Kudos |

## 2. Functional Capabilities

| ID | Capability | What the user can do | User Stories | Requirements | Business Rules | Screens |
|----|------------|------------------------|-----------------|---------------|-------------------|---------|
| CAP-01 | Đọc nội dung thể lệ | Mở `/standards`, đọc ba mục thể lệ, 4 bậc huy hiệu Hero và 6 icon sưu tập, cuộn khi nội dung dài | US001 | FR-001, FR-002, FR-003, FR-004, FR-201, FR-202, FR-203, FR-204, FR-205, FR-403, FR-405 | BR-001, BR-002, BR-003 | SCR007_TheLe |
| CAP-02 | Đóng panel quay lại | Bấm `Đóng`, gõ `Escape`, hoặc bấm nền ngoài drawer để quay lại nội dung trước đó | US002 | FR-401, FR-404 | BR-004 | SCR007_TheLe |
| CAP-03 | Đi thẳng sang viết Kudos | Bấm `Viết KUDOS` để tới form soạn Kudos | US003 | FR-402 | BR-005 | SCR007_TheLe |

## 3. Open Decisions

None — no unresolved domain confirmations. Commission chạy `--auto` với chỉ thị *"tự động triển khai
theo hướng câu trả lời đầu tiên, Yes hoặc câu trả lời Recommend mà ko cần hỏi lại"*, nên mọi câu hỏi mở
trong `clarifications.md` đã được chốt bằng phương án Recommended. Hai điểm cần nói rõ vì chúng DỊCH
hoặc TỪ CHỐI một yêu cầu của test case gốc, chứ không im lặng bỏ qua:

- **DEC-001 — `TC_THELE_FUN_004` nói "The Viết KUDOS input modal opens"; repo này không có modal soạn Kudos.**
  Bề mặt soạn Kudos của hệ thống là route `/kudos/new` (F005). Nút điều hướng sang đó. *Yêu cầu* —
  "`Viết KUDOS` dẫn tới form soạn" — được giữ nguyên; chỉ cơ chế được dịch sang thứ tồn tại thật.
- **DEC-002 — `TC_THELE_GUI_003` và `TC_THELE_FUN_005` khẳng định một nút chân drawer ở trạng thái `disabled`.**
  Không áp dụng cho màn này: `Đóng` luôn đóng được và `Viết KUDOS` luôn điều hướng được — không có
  trạng thái nào (kể cả loading) khiến một trong hai không dùng được. Dựng một prop `disabled` mà không
  gì set được là code chết; dựng một nút mờ giả để test xanh là đúng thứ `primary-workflow.md` cấm.
  Hai test case được mang vào `e2e/the-le.spec.ts` dưới dạng `test.skip` kèm lý do inline, để chỗ thiếu
  hiện ra trong output của suite chứ không biến mất. `spec_progress` của `B_Button` mô tả trạng thái
  disabled vẫn đúng với *component* Figma dùng chung; nó không đúng với hai instance trên màn này.

## 4. Requirements

### Foundation (0xx)

- **FR-001** Migration mới tạo `public.rule_sections` (nội dung văn xuôi có thứ tự) và `public.rule_items`
  (danh sách có thứ tự, phân biệt bằng cột `kind`: `hero_tier` | `collectible_icon`), mỗi bảng bật RLS với
  đúng một policy `<table>_select_all` `for select to anon, authenticated using (true)`, cấp
  `grant select` tường minh cho `anon, authenticated`, và `notify pgrst, 'reload schema';` sau grants.
  Không policy `insert`/`update`/`delete` — im lặng chính là từ chối.
- **FR-002** `supabase/seed.sql` được bổ sung toàn bộ nội dung thể lệ, phiên âm nguyên văn từ
  `clarifications.md § "Resolved from source data"` — bao gồm gạch ngang en-dash trong `10–20`, trong hai
  mô tả bậc 1 và 4. (`ROOT FURTHER` viết bình thường: bản chép đầu tiên ra `ROOT FUTHER` vì đọc nhầm
  `itemName` — tên layer — thay vì `character` — chữ được render; đã sửa ở phase 08 sau khi đọc lại node.)
  Insert phẳng, không
  `ON CONFLICT` (khớp idiom "reset truncates" của file).
- **FR-003** Khối `rules` được thêm vào interface `Dictionary` (`lib/i18n/messages/dictionary.ts`) cùng
  `lib/i18n/messages/vi-rules.ts` và `en-rules.ts`, nối vào `vi.ts`/`en.ts`. Khối này chỉ chứa *chrome*
  (tiêu đề panel, hai nhãn nút, nhãn aria) — không chứa nội dung thể lệ, thứ đã nằm trong database.
- **FR-004** `lib/supabase/database.types.ts` được sinh lại bằng `npm run db:types` sau migration và commit
  cùng thay đổi; không sửa tay.

### Nội dung panel (2xx)

- **FR-201** Tiêu đề panel render là `<h1>` của trang và đọc đúng `Thể lệ`, 45/52 bold, `#FFEA9E`
  (`mm:3204:6055`). Container drawer mang `role="dialog"`, được `<h1>` này gán nhãn qua `aria-labelledby`,
  và **không** mang `aria-modal` (sửa ở phase 08): màn này cố ý không dựng focus trap và không `inert`
  phần nền — `/standards` là một route chứ không phải overlay đè lên nội dung đang sống, nên tab ra
  header/footer là hành vi đúng. Khai `aria-modal` trong khi vẫn để header/footer nằm trong tab order là
  nói dối assistive tech. `e2e/the-le.spec.ts` assert sự VẮNG MẶT của thuộc tính này.
- **FR-202** Ba mục văn xuôi (`rule_sections`) render theo `position` tăng dần, mỗi mục là một tiêu đề
  `#FFEA9E` in hoa + phần thân trắng canh đều: `NGƯỜI NHẬN KUDOS…` (22/28), `NGƯỜI GỬI KUDOS…` (22/28),
  `KUDOS QUỐC DÂN` (24/32). Mục 2 có thêm một dòng kết (`Những Sunner thu thập trọn bộ 6 icon…`) render
  SAU lưới icon.
- **FR-203** Bốn bậc huy hiệu Hero (`rule_items` `kind='hero_tier'`) render theo `position` ngay dưới thân
  mục 1: ảnh pill huy hiệu + nhãn ngưỡng 16/24 bold trắng trên một hàng, mô tả 14/20 bold trắng xuống dòng
  dưới.
- **FR-204** Sáu icon sưu tập (`rule_items` `kind='collectible_icon'`) render theo `position` thành lưới ba
  cột (hai hàng ba), ô rộng 80px, gap ngang 16px, gap dọc 24px, mỗi ô là artwork tròn + caption in hoa
  canh giữa.
- **FR-205** Ảnh huy hiệu và icon đọc từ `public/images/rules/` qua đường dẫn lưu trong cột
  `image_path` của dòng — không nhúng nhị phân vào database, không dùng Storage bucket.

### Điều hướng và tương tác (4xx)

- **FR-401** `Đóng` là một `<button>` thật (không phải `<Link>`): quay lại lịch sử trước đó khi route này
  có entry để quay về, ngược lại (mở bằng deep link) điều hướng về `/`. Không bao giờ là ngõ cụt.
- **FR-402** `Viết KUDOS` là một `<a href="/kudos/new">`. `/kudos/new` đã được `proxy.ts` canh, nên một
  người chưa đăng nhập bấm vào sẽ rơi về `/login` theo đúng luật sẵn có — màn này không thêm guard riêng.
- **FR-403** Cột nội dung cuộn độc lập, KHÔNG phải cả trang: drawer cao `h-svh` với chân drawer ghim
  (`justify-content: space-between` trên frame cao cố định), cột nội dung `overflow-y-auto`. Nội dung ngắn
  hơn panel thì không có thanh cuộn và không có khoảng cuộn nào — cùng một cách dựng phục vụ cả
  `TC_THELE_FUN_001` lẫn `FUN_002`.
- **FR-404** `Escape` và bấm vào nền ngoài drawer làm đúng việc `Đóng` làm.
- **FR-405** Drawer `w-full max-w-[553px]`: tràn hết bề ngang trên điện thoại, đúng 553px từ đó trở lên.
  Frame không có bản mobile; đây là luật responsive tối thiểu không bao giờ tràn viewport.

### Security (6xx)

- **FR-601** Hai bảng mới chỉ đọc được, cho cả `anon` lẫn `authenticated`. Không con đường nào từ giao diện
  hay từ anon key ghi được vào chúng — không policy ghi nào tồn tại, và trang không có Server Action nào.

## 5. Business Rules

- **BR-001 — Thứ tự hiển thị luôn đến từ `position`, không bao giờ từ `id` hay thứ tự insert.**
  `order by position` là mệnh đề bắt buộc ở mọi truy vấn của feature này. Đây là idiom đã có của repo
  (`hashtags.position`, `departments.filter_position`, `kudos_hashtags.position`).
- **BR-002 — Nội dung thể lệ là dữ liệu, không phải i18n copy.** Nó nằm trong `rule_sections`/`rule_items`,
  không nằm trong `Dictionary`. Ngược lại, chrome (tiêu đề panel, hai nhãn nút, nhãn aria) là i18n copy và
  KHÔNG nằm trong database. Ranh giới này giữ cho một lần đổi luật chơi là một lần sửa dữ liệu.
- **BR-003 — Nội dung chỉ có tiếng Việt, và điều đó được nói thẳng.** Frame chỉ mang copy tiếng Việt, và
  luật MoMorph là "dùng nội dung thiết kế làm nguồn, KHÔNG bịa dữ liệu" — một cột `locale` lúc này chỉ có
  thể được lấp bằng bản dịch tự nghĩ ra. Hệ quả nêu rõ chứ không giấu: với `NEXT_LOCALE=en`, chrome của
  panel là tiếng Anh còn phần thân thể lệ vẫn là tiếng Việt. Thêm cột `locale` là một migration duy nhất
  vào ngày có copy tiếng Anh thật (YAGNI cho tới lúc đó).
- **BR-004 — `Đóng` nghĩa là "quay lại nơi bạn đến", không phải "về trang chủ".** Về `/` chỉ là nhánh dự
  phòng khi không có lịch sử để quay lại.
- **BR-005 — `Viết KUDOS` không tự phán quyền.** Nó luôn điều hướng; việc chưa đăng nhập thì bị chặn là
  việc của `proxy.ts` trên `/kudos/new`, đã ship từ F005. Màn này không nhân bản luật đó.

## 6. Screens

| Screen | Route | Description |
|--------|-------|-------------|
| SCR007_TheLe | `/standards` | Drawer thể lệ 553px bám mép phải trên shell chuẩn; thay thế `ComingSoon` |

## 7. User Stories

- **US001** — Là một Sunner (hoặc khách), tôi muốn đọc thể lệ chương trình để biết huy hiệu Hero mở khoá ở
  ngưỡng nào, 6 icon sưu tập là gì và Kudos Quốc Dân được trao ra sao.
- **US002** — Là một người đang đọc thể lệ, tôi muốn đóng panel và quay lại đúng chỗ tôi đang dở.
- **US003** — Là một Sunner vừa đọc xong thể lệ, tôi muốn đi thẳng sang form viết Kudos mà không phải tự
  tìm đường.

## 8. Scenarios

**US001**
- Given nội dung thể lệ đã được seed, When tôi mở `/standards`, Then drawer hiện tiêu đề `Thể lệ`, ba mục
  nội dung đúng thứ tự, 4 bậc Hero kèm ảnh, và lưới 6 icon kèm caption.
- Given nội dung dài hơn chiều cao drawer, When tôi cuộn trong cột nội dung, Then cột nội dung cuộn tới
  hết nội dung trong khi chân drawer đứng yên.

**US002**
- Given tôi tới `/standards` từ trang chủ, When tôi bấm `Đóng`, Then tôi quay lại trang chủ.
- Given tôi mở `/standards` bằng deep link (không có lịch sử), When tôi bấm `Đóng`, Then tôi tới `/`.
- Given drawer đang mở, When tôi gõ `Escape` hoặc bấm vào nền ngoài drawer, Then hành vi giống hệt `Đóng`.

**US003**
- Given tôi đã đăng nhập, When tôi bấm `Viết KUDOS`, Then tôi tới `/kudos/new`.
- Given tôi chưa đăng nhập, When tôi bấm `Viết KUDOS`, Then `proxy.ts` chuyển tôi về `/login`.

## 9. Edge Cases

| Scenario | What Happens | User-Facing Message |
|----------|--------------|----------------------|
| Bảng `rule_sections`/`rule_items` rỗng (chưa seed) | Chrome vẫn render đầy đủ — tiêu đề `Thể lệ`, hai nút chân drawer đều hoạt động; vùng nội dung rỗng. Không throw, không màn trắng. | *(không có thông báo — panel đơn giản không có mục nào)* |
| Truy vấn Supabase lỗi | `fetchRuleSections`/`fetchRuleItems` throw `Error("fetchX failed: …")` theo đúng idiom của repo; Next dựng error boundary. | *(error boundary mặc định)* |
| `image_path` trỏ file không tồn tại | `<Image>` hỏng ảnh riêng ô đó; caption và nhãn vẫn đọc được. Không ảnh hưởng ô khác. | *(alt text của ảnh)* |
| Nội dung ngắn hơn chiều cao drawer | Không thanh cuộn, không khoảng cuộn (`scrollHeight === clientHeight`). | *(không có)* |
| Mở `/standards` khi chưa đăng nhập | Trang render đầy đủ — route công khai. | *(không có)* |

## 10. Edge Behaviours to Verify

- `scrollHeight > clientHeight` trên `rules-panel-content` với nội dung đã seed (FUN_001), và phủ định của
  nó khi nội dung vừa khít (FUN_002).
- `Đóng` sau một lần điều hướng nội bộ quay về đúng trang trước; `Đóng` trên deep link tới `/`.
- `Viết KUDOS` là `<a>` với `href="/kudos/new"` — kiểm bằng thuộc tính, không bằng kết quả điều hướng, để
  test dưới project `anon` không phụ thuộc vào redirect của guard.
- Thứ tự render khớp `position`, không khớp `id` — kiểm bằng cách so chuỗi caption theo đúng thứ tự thiết kế.

## 11. Risks & Known Issues

| ID | Type | Description | Impact | Status |
|----|------|--------------|--------|--------|
| RISK-01 | scope | 6 artwork icon lần đầu vào repo qua màn này, trong khi `profile-badge-row.tsx` (F006) vẫn render 6 vòng tròn `#323231` phẳng vì frame F006 không có artwork | Hai màn hình nói hai chuyện khác nhau về cùng 6 icon cho tới khi có commission nối chúng lại | Open — cố ý ngoài scope |
| RISK-02 | i18n | Chrome tiếng Anh + thân thể lệ tiếng Việt khi `NEXT_LOCALE=en` (BR-003) | Người đọc bản EN thấy nội dung song ngữ lệch | Accepted — ghi nhận, không giấu |

## 12. Dependencies

| Dependency | Type | Why this feature needs it | Evidence |
|------------|------|-----------------------------|----------|
| `HomeHeader`, `SiteFooter` | internal component | Shell chuẩn bên dưới drawer, dùng nguyên không sửa | `app/awards-information/page.tsx` |
| `getPageContext()` | internal | Một lần đọc locale + session cho cả trang | `app/_page-context.ts` |
| `/kudos/new` (F005) | internal route | Đích của `Viết KUDOS` (DEC-001) | `proxy.ts` |
| `proxy.ts` | internal | Canh `/kudos/new`, nên màn này không tự canh (BR-005) | `proxy.ts` |
| Supabase local | infra | Nguồn nội dung thể lệ; migration + seed chạy qua `supabase db reset` | `supabase/config.toml` |

## 13. Configuration

N/A — no user-facing configuration constants for this feature.
