---
status: implemented
fcode: F003
authored_by: takumi
created: 2026-09-06
lang: vi
---

**Priority**: P1
**Type**: ui

## 1. Overview

**Problem:** Trang chủ SAA 2025 (F002_HomepageSaa) chỉ giới thiệu sáu hạng mục giải thưởng bằng một dòng mô tả cắt ngắn, rồi trỏ người đọc sang `/awards-information` — nơi trước đây chỉ có shell "Coming soon". Người đọc muốn biết mỗi hạng mục vinh danh ai, có bao nhiêu giải và giá trị bao nhiêu thì không có chỗ nào trả lời.
**Solution:** Màn hình công khai "Hệ thống giải" tại `/awards-information` — thay hẳn shell placeholder cũ — gồm hero tiêu đề mùa giải, một menu danh mục dính bên trái, sáu thẻ chi tiết giải thưởng xen kẽ trái/phải, rồi khối quảng bá Sun* Kudos và footer dùng lại nguyên trạng của trang chủ.
**Scope:** Trình bày đầy đủ nội dung sáu hạng mục (mô tả, số lượng, giá trị giải); menu danh mục tự sáng theo vị trí cuộn và bấm được để nhảy tới hạng mục tương ứng; nhận deep link `#<slug>` từ trang chủ; đủ hai ngôn ngữ VN/EN.
**Non-Scope:** Không có nội dung thật của Sun* Kudos — CTA "Chi tiết" vẫn tới shell placeholder `/kudos` (xem § 11 RISK-02). Không xuất ảnh mới: sáu ảnh giải thưởng và các ảnh nền đã có sẵn từ F002. Không sửa header/footer — trạng thái "Award Information" đang chọn tự đúng trên route này. Không có API, không có bảng dữ liệu, không có thao tác ghi. Không render nút widget nổi trên màn hình này.

**Actors**

| Actor | Description | Primary goal |
|-------|--------------|---------------|
| Khách truy cập | Người đọc `/awards-information`, đa số đi từ trang chủ hoặc từ một thẻ giải thưởng trên trang chủ | Hiểu rõ sáu hạng mục giải SAA 2025 — vinh danh ai, bao nhiêu giải, giá trị bao nhiêu |
| Người dùng đã đăng nhập | Người đã xác thực Google qua F001_Login | Đọc cùng nội dung đó; header vẫn có chuông thông báo + menu tài khoản như trên trang chủ (hành vi tái dùng, không re-specify ở đây) |

## 2. Functional Capabilities

<!-- Một outcome duy nhất theo .intent-enum.json: đọc hiểu hệ thống giải thưởng. Menu danh mục là
     affordance điều hướng trong chính trang đó, không phải outcome thứ hai. #CAP == 1, US count = 2
     (dưới ngưỡng warn 3-4 của type=ui) nên không cần dòng Single-capability rationale. -->

| ID | Capability | What the user can do | User Stories | Requirements | Business Rules | Screens |
|----|------------|------------------------|-----------------|---------------|-------------------|---------|
| CAP-01 | Đọc hệ thống giải thưởng SAA 2025 | Đọc chi tiết sáu hạng mục giải, dùng menu danh mục để nhảy nhanh tới hạng mục quan tâm, và đi tiếp sang Sun* Kudos | US007, US008 | FR-001, FR-002, FR-101, FR-102, FR-201, FR-202, FR-203, FR-204, FR-205, FR-206, FR-207, FR-208, FR-401, FR-402, FR-403, FR-601 | BR-001, BR-002, BR-003, BR-004, DEC-002 | SCR003_AwardSystem |

> **Cấp mã (traceability)**: hai user story soạn cục bộ cho tính năng này nhận mã global kế tiếp còn trống — `US007`, `US008`. Màn hình nhận `SCR003_AwardSystem`. Cả bốn mã đã được đăng ký chính thức lúc promote (2026-09-06) vào `docs/generated/user-stories.md`, `docs/generated/screen-list.md` và `docs/_canonical-fcodes.json`.

## 3. Open Decisions

| D### | Decision | Default proposal | Rationale | Blocks work |
|------|----------|-------------------|-----------|--------------|
| D001 | Test case ID-1 yêu cầu khách chưa đăng nhập vào màn hình này thì bị đẩy về trang đăng nhập. Hành vi đã ship thì ngược lại: route công khai. Chốt thế nào? | Giữ công khai — không thêm guard (FR-001, FR-601) | Lối vào duy nhất tới màn hình này là trang chủ công khai; chặn đích trong khi để ngỏ nguồn là vô nghĩa, và sẽ làm gãy sáu test trang chủ đang xanh vốn điều hướng tới đây ở trạng thái chưa đăng nhập. **ID-1 cố ý không triển khai** — ghi lại, không âm thầm bỏ *(clarifications.md — quyết định thứ hai; test ID-0, ID-1)* | no |

## 4. Requirements

### Foundation (0xx)

- **FR-001** `/awards-information` là route công khai — không có guard mới; shell "Coming soon" ở route này đã bị thay hẳn bằng màn hình thật. `proxy.ts` chỉ chặn `/todo` và `/login` (`proxy.ts:41-46`) và không bị đụng tới. *(clarifications.md — quyết định route và quyết định auth; test ID-0)*
- **FR-002** Toàn bộ nội dung màn hình có đủ hai ngôn ngữ VN và EN, và một khoá thiếu ở một ngôn ngữ là lỗi biên dịch chứ không phải khoảng trắng lúc chạy — cưỡng chế bằng `Dictionary["awardSystem"]` (`lib/i18n/messages/dictionary.ts:112-146`). VN chép nguyên văn từ thiết kế, EN là bản dịch sát nghĩa. *(clarifications.md — "i18n coverage")*

### Navigation (1xx)

- **FR-101** Mục "Award Information" trên header ở trạng thái đang chọn khi người dùng ở màn hình này — có sẵn nhờ `home-nav.tsx:59` so `usePathname()` với `href` của từng mục, nên header không phải sửa gì. *(clarifications.md — "Shared chrome" và ORCH-03)*
- **FR-102** Vào thẳng `/awards-information#<slug>` (đường dẫn mà mọi thẻ giải thưởng trên trang chủ đang trỏ tới) dừng ở đúng thẻ giải thưởng đó, và mục menu tương ứng sáng lên. **Vị trí là tức thì, trạng thái sáng thì đến sau khi trang hydrate** — xem BR-005 và § 11 RISK-04 cho khoảng chuyển tiếp được chấp nhận. *(clarifications.md — "Deep-link arrival", ORCH-04; test ID-11)*

### Award System Screen (2xx)

- **FR-201** Trang xếp đúng thứ tự thiết kế: header → hero → phần hệ thống giải (menu trái + sáu thẻ) → khối Sun* Kudos → footer. *(clarifications.md — "Page order")*
- **FR-202** Hero hiển thị ảnh keyvisual, chữ hình "ROOT FURTHER", và cụm tiêu đề canh giữa: dòng nhỏ `Sun* Annual Awards 2025` màu trắng, một đường kẻ mảnh, rồi tiêu đề vàng `Hệ thống giải thưởng SAA 2025`. Tiêu đề này là `<h1>` duy nhất của trang. *(spec item A)*
- **FR-203** Menu danh mục bên trái dính theo trang cuộn từ breakpoint `lg`, gồm đúng sáu mục theo thứ tự thiết kế — Top Talent, Top Project, Top Project Leader, Best Manager, Signature 2025 Creator, MVP — mỗi mục có một biểu tượng 24×24 phía trước; mục đang chọn hiện chữ vàng kèm gạch chân vàng. Dưới `lg` menu thành một hàng cuộn ngang. *(spec item C)*
- **FR-204** Mỗi thẻ giải thưởng gồm: ảnh vuông 336×336 bo góc viền vàng, tiêu đề giải có biểu tượng phía trước, đoạn mô tả, dòng `Số lượng giải thưởng:` kèm số lượng và đơn vị, dòng `Giá trị giải thưởng:` kèm một hoặc nhiều mức giải. *(spec item D.1–D.6, D.1.1)*
- **FR-205** Sáu thẻ hiển thị đúng nội dung đã chốt: Top Talent `10 Cá nhân` / `7.000.000 VNĐ`; Top Project `02 Tập thể` / `15.000.000 VNĐ`; Top Project Leader `03 Cá nhân` / `7.000.000 VNĐ`; Best Manager `01 Cá nhân` / `10.000.000 VNĐ`; Signature 2025 - Creator `01 Cá nhân hoặc tập thể` / `5.000.000 VNĐ` và `8.000.000 VNĐ`; MVP `01 Cá nhân` / `15.000.000 VNĐ`. *(clarifications.md — bảng "The six awards"; số lượng Top Talent lấy theo frame, không theo dòng CSV cũ)*
- **FR-206** Phần giá trị giải là một danh sách chứ không phải một dòng cố định: bốn giải có một mức kèm ghi chú `cho mỗi giải thưởng`; Signature có hai mức nối bằng `Hoặc` với ghi chú `cho giải cá nhân` / `cho giải tập thể`; Best Manager và MVP chỉ có số tiền, không có dòng ghi chú. *(clarifications.md — "Model prize as a list")*
- **FR-207** Khối Sun* Kudos ở cuối trang dùng lại y nguyên component đã có trên trang chủ — cùng dòng nhỏ, tiêu đề, phụ đề, đoạn mô tả và nút `Chi tiết` dẫn sang `/kudos`. Màn hình này truyền thêm bề rộng khung theo artboard 1440 của nó; trang chủ không truyền gì và render y như cũ. *(spec item D1/D2/D2.1; clarifications.md — "Shared chrome", ORCH-05)*
- **FR-208** Không render nút widget nổi trên màn hình này — thiết kế không có nó. *(clarifications.md — "floating widget")*

### Interaction (4xx)

- **FR-401** Bấm một mục menu thì trang cuộn mượt tới thẻ giải thưởng tương ứng và địa chỉ trên thanh URL đổi thành `#<slug>` của hạng mục đó, nhưng không tạo thêm một bước lùi trong lịch sử duyệt. *(clarifications.md — "left category menu"; test ID-9)*
- **FR-402** Khi người dùng cuộn tay, menu tự cập nhật theo hạng mục đang hiện trên màn hình, và tại mọi thời điểm chỉ có đúng một mục ở trạng thái đang chọn. *(clarifications.md — "left category menu"; test ID-11)*
- **FR-403** Người dùng bật chế độ giảm chuyển động của hệ điều hành thì thao tác bấm menu nhảy thẳng tới thẻ, không cuộn mượt. *(clarifications.md — "prefers-reduced-motion")*

### Security (6xx)

- **FR-601** Màn hình chỉ chứa nội dung công khai của mùa giải — không có dữ liệu người dùng, không có thao tác ghi — nên không cần và không có bất kỳ lớp chặn đăng nhập nào. Yêu cầu ngược lại ở test ID-1 được ghi làm quyết định còn mở (§ 3 D001), không phải làm yêu cầu triển khai. Fragment `#<slug>` do người dùng đưa vào được đối chiếu với danh sách slug cố định **trước khi** chạm DOM, nên một fragment bất kỳ không chọn được gì. *(clarifications.md — quyết định auth; test ID-1, ID-13)*

## 5. Business Rules

- Màn hình luôn công khai, không có guard mới ngoài route guard sẵn có của F001_Login — FR-001, FR-601 (BR-001)
- Menu danh mục luôn có đúng một mục đang sáng; cú bấm khoá quyền ghi trong tối đa 700ms, và bất kỳ thao tác cuộn thật nào của người dùng (lăn chuột, chạm, phím) trong khoảng đó trả quyền lại ngay cho vị trí cuộn — FR-401, FR-402 (BR-002)
- Hệ điều hành báo người dùng muốn giảm chuyển động thì mọi cú nhảy tới thẻ là tức thì, không cuộn mượt — FR-403 (BR-003)
- Giá trị giải là một danh sách mức giải, mỗi mức có số tiền và ghi chú tuỳ chọn; ghi chú trống thì không sinh dòng rỗng — FR-206 (BR-004)
- Lúc trang mở, mục đang sáng luôn là mục đầu tiên; hash chỉ quyết định *vị trí cuộn*, còn mục sáng do phép đo vị trí sửa lại sau khi trang hydrate. Hash lạ hoặc không có hash thì không cuộn và mục đầu tiên giữ nguyên — FR-102 (DEC-002)
- Khi không thẻ nào nằm trong vùng đo: ở phía trên thẻ đầu tiên thì mục đầu tiên sáng lại; ở phía dưới thẻ cuối (vùng footer) thì giữ nguyên mục hiện tại. Không bao giờ rơi về không mục nào — FR-402 (BR-005)

## 6. Screens

| Screen Name | SCR### | What User Sees | What User Can Do |
|-------------|--------|-----------------|-------------------|
| Hệ thống giải | SCR003_AwardSystem | Header (mục "Award Information" đang chọn), hero với keyvisual + chữ hình ROOT FURTHER + tiêu đề "Hệ thống giải thưởng SAA 2025", menu danh mục sáu mục dính bên trái, sáu thẻ chi tiết giải thưởng xen kẽ trái/phải, khối Sun* Kudos, footer | Cuộn đọc sáu hạng mục; bấm mục menu để nhảy tới hạng mục đó; bấm `Chi tiết` để sang Sun* Kudos; đổi ngôn ngữ; điều hướng tiếp qua header/footer |

### User Journey

1. Khách bấm một thẻ giải thưởng trên trang chủ (hoặc mục nav "Award Information") và tới `/awards-information`, có thể kèm `#<slug>` của hạng mục vừa bấm.
2. Trang mở ra ở đúng hạng mục đó; mục menu tương ứng sáng lên ngay sau khi trang hydrate (RISK-04). Vào thẳng không kèm hash thì trang mở từ hero và mục đầu tiên sáng.
3. Khách cuộn đọc lần lượt sáu thẻ — menu bên trái tự chạy theo, luôn chỉ một mục sáng.
4. Khách bấm thẳng một mục menu để nhảy tới hạng mục quan tâm; địa chỉ trang đổi theo để có thể chia sẻ lại đúng chỗ đó.
5. Cuối trang, khách bấm `Chi tiết` ở khối Sun* Kudos để sang trang Kudos, hoặc dùng footer/header đi tiếp.

## 7. User Stories

### US007_BrowseAwardSystem — Đọc hệ thống giải thưởng SAA 2025

**Actor:** Khách truy cập
**Goal:** Biết sáu hạng mục giải SAA 2025 vinh danh ai, mỗi hạng mục có bao nhiêu giải và giá trị bao nhiêu.
**Business value:** Trả lời trọn vẹn câu hỏi mà trang chủ mới chỉ gợi ra, và gỡ bỏ shell "Coming soon" mà mọi thẻ giải thưởng trên trang chủ từng dẫn tới.

**Acceptance Criteria:**
- [x] Trang hiển thị đủ năm khối theo đúng thứ tự thiết kế: header, hero, phần hệ thống giải, khối Sun* Kudos, footer.
- [x] Sáu thẻ giải thưởng hiện đúng thứ tự thiết kế, mỗi thẻ đủ ảnh, tiêu đề, mô tả, số lượng và giá trị giải.
- [x] Thẻ Signature hiện hai mức giải nối bằng `Hoặc`; Best Manager và MVP không có dòng ghi chú dưới số tiền.
- [ ] Đổi sang EN thì toàn bộ nội dung màn hình đổi theo, không còn chuỗi tiếng Việt sót lại. *(bản dịch EN đã có và được cưỡng chế ở compile-time; nhánh EN chưa có test tự động — xem § 11 RISK-05)*

### US008_JumpToAwardCategory — Nhảy tới một hạng mục qua menu danh mục

**Actor:** Khách truy cập
**Goal:** Đi thẳng tới hạng mục mình quan tâm mà không phải cuộn hết trang, và luôn biết mình đang đọc hạng mục nào.
**Business value:** Trang dài sáu khối nội dung; không có menu dính thì người đọc mất phương hướng và bỏ qua các hạng mục phía dưới.

**Acceptance Criteria:**
- [x] Bấm một mục menu cuộn tới đúng thẻ tương ứng và đổi địa chỉ trang thành `#<slug>` của hạng mục đó.
- [x] Trong lúc cuộn tay, mục menu sáng luôn khớp hạng mục đang hiện trên màn hình, và chỉ có đúng một mục sáng.
- [x] Vào thẳng `/awards-information#mvp` thì trang dừng ở thẻ MVP và mục MVP sáng sau khi hydrate (RISK-04).
- [ ] Người dùng bật chế độ giảm chuyển động thì cú nhảy là tức thì, không có hiệu ứng cuộn. *(đã code — `prefers-reduced-motion` đọc tại chỗ bấm; nhánh này chưa có test tự động, xem § 11 RISK-05)*

## 8. Scenarios

### US007_BrowseAwardSystem — Happy Path

**Given** khách chưa đăng nhập mở `/awards-information`, **When** trang tải xong, **Then** khách thấy đủ năm khối theo đúng thứ tự và sáu thẻ giải thưởng với đầy đủ số lượng, giá trị giải.

### US007_BrowseAwardSystem — Error: Khách chưa đăng nhập mở trang

**Given** khách hoàn toàn chưa có phiên đăng nhập, **When** mở `/awards-information`, **Then** trang hiện bình thường, không bị đẩy về trang đăng nhập, không có thông báo lỗi *(hành vi cố ý — § 3 D001)*.

### US008_JumpToAwardCategory — Happy Path

**Given** khách đang ở đầu trang, **When** bấm mục menu "MVP", **Then** trang cuộn tới thẻ MVP, địa chỉ đổi thành `/awards-information#mvp`, và chỉ mục "MVP" sáng.

### US008_JumpToAwardCategory — Error: Hash không khớp hạng mục nào

**Given** khách mở `/awards-information#khong-ton-tai`, **When** trang tải xong, **Then** trang mở từ đầu, mục đầu tiên sáng, không có lỗi hiển thị và không có cú nhảy nào.

## 9. Edge Cases

| Scenario | What Happens | User-Facing Message |
|----------|--------------|----------------------|
| Mở trang với hash không khớp hạng mục nào | Bỏ qua hash, mở từ đầu trang, mục menu đầu tiên sáng, không có lỗi console | "None — silent handling" |
| Người dùng bật chế độ giảm chuyển động của hệ điều hành | Bấm menu nhảy tức thì tới thẻ, không cuộn mượt; mục menu vẫn sáng đúng | "None — silent handling" |
| Cuộn tới cuối trang, thẻ cuối không cao bằng một màn hình | Mục menu cuối vẫn sáng — ở vùng footer, khi không thẻ nào trong vùng đo, mục hiện tại được giữ nguyên (BR-005) | "None — silent handling" |
| Cuộn ngược lên hero | Mục đầu tiên (Top Talent) sáng lại, đúng như thiết kế vẽ ở vị trí đó (BR-005) | "None — silent handling" |
| Trang đã hiện nhưng phần tương tác chưa sẵn sàng | Sáu thẻ và menu vẫn đọc được vì là nội dung server render; mục menu chưa tự sáng theo cuộn cho tới khi hydrate xong | "None — silent handling" |
| Bấm mục menu kèm Ctrl/Cmd/Shift/Alt, hoặc bằng nút chuột khác | Trình duyệt tự xử lý `href="#<slug>"` như một liên kết thường (mở tab mới) — không bị nuốt sự kiện | "None — silent handling" |
| Bấm mục menu rồi lăn chuột/chạm/bấm phím trong lúc đang cuộn | Khoá của cú bấm nhả ngay, mục sáng trả về hạng mục thật sự đang trên màn hình (BR-002) | "None — silent handling" |
| Khách chưa đăng nhập | Chuông thông báo và biểu tượng tài khoản không có trên header — giống hệt trang chủ, không phải hành vi riêng của màn hình này | "N/A — phần tử không tồn tại" |

## 10. Edge Behaviours to Verify

- **FR-001** → Mở `/awards-information` ở trạng thái chưa đăng nhập phải ra nội dung thật, không phải shell "Coming soon", cũng không bị đẩy về đăng nhập.
- **FR-002** → Đổi sang EN phải đổi toàn bộ nội dung màn hình; không được còn chuỗi tiếng Việt hay ô trống.
- **FR-102** → Vào thẳng bằng `#<slug>` của từng hạng mục phải dừng ở đúng thẻ đó và sáng đúng mục menu tương ứng sau khi hydrate.
- **FR-205** → Sáu thẻ phải đúng số lượng và giá trị giải như đã chốt — đặc biệt Top Talent là `10 Cá nhân`, không phải `10 Đơn vị`.
- **FR-206** → Thẻ Signature phải có hai mức giải nối bằng `Hoặc`; Best Manager và MVP không được sinh ra dòng ghi chú rỗng.
- **FR-402** → Trong suốt quá trình cuộn, số mục menu đang sáng phải luôn đúng bằng một.
- **FR-403** → Bật chế độ giảm chuyển động thì không được có hiệu ứng cuộn mượt.

## 11. Risks & Known Issues

| ID | Type | Description | Impact | Status |
|----|------|--------------|--------|--------|
| RISK-01 | risk | Test case ID-1 yêu cầu chặn khách chưa đăng nhập, trái với hành vi công khai đã ship. Màn hình cố ý **không** triển khai ID-1 và ghi lại thành quyết định còn mở (§ 3 D001) thay vì im lặng bỏ qua. | Nếu sau này chủ sản phẩm chốt phải chặn, sẽ phải chặn cả trang chủ và viết lại sáu test trang chủ đang xanh — phạm vi lớn hơn hẳn màn hình này. Quyết định đang chờ chủ sản phẩm. | [EXPECTED] |
| RISK-02 | risk | Nút `Chi tiết` của khối Sun* Kudos dẫn sang `/kudos`, vẫn là shell placeholder. Test case ID-14 ("Chi tiết" → 404 thân thiện) nhắm tới màn hình Kudos thật nên **không chạy được** ở giai đoạn này. | Liên kết không gãy và không 404, nhưng người đọc chưa tới được nội dung Kudos thật; đây là phạm vi của một tính năng khác. | [EXPECTED] |
| RISK-03 | risk | Sáu ảnh giải thưởng dùng lại nguyên các tệp đã có từ F002 thay vì xuất mới từ thiết kế (assumption A1). Khâu kiểm thử đo được cả sáu ảnh đúng 336×336. | Không phát sinh sai lệch ở vòng kiểm thử. Nếu một vòng so ảnh sau này phát hiện lệch, việc xuất lại ảnh là bó hẹp. | [RESOLVED] |
| RISK-04 | risk | **Deep link: mục menu sáng đúng chỉ sau khi trang hydrate (~290ms đo được).** URL fragment không bao giờ được gửi lên server, nên HTML server render bắt buộc sáng mục đầu tiên; phép đo vị trí sửa lại khi React hydrate xong. Đây là thời gian tới-tương-tác của route, không phải một hiệu ứng chuyển động. | Chỉ ảnh hưởng lối vào bằng deep link, dưới một giây, và kết thúc đúng trạng thái. Các phương án thay thế đều tệ hơn: đọc `location.hash` lúc render gây hydration mismatch (làm hỏng assertion "không lỗi console" của ID-13); không sáng mục nào ở server thì mọi lượt vào thường mất trạng thái sáng. **Chấp nhận có chủ đích — clarifications.md ORCH-04.** | [EXPECTED] |
| RISK-05 | risk | Hai nhánh chưa có test tự động: hiển thị ngôn ngữ EN và `prefers-reduced-motion`. Cả hai đã code và đã được đọc lại bằng tay, nhưng bộ E2E chỉ chạy Desktop Chrome ở locale mặc định. | Một hồi quy ở copy EN hoặc ở nhánh giảm chuyển động sẽ không bị bộ test bắt. Cột `w-[60px]` của đơn vị số lượng là chỗ dễ vỡ nhất ở EN — xem FUP-02 trong § 12. | [EXPECTED] |

## 12. Dependencies

| Dependency | Type | Why this feature needs it | Evidence |
|------------|------|-----------------------------|----------|
| F002_HomepageSaa | feature | Dùng lại nguyên trạng header, footer, khối Sun* Kudos, cơ chế đọc ngôn ngữ + phiên đăng nhập dùng chung, và sáu ảnh giải thưởng — màn hình này không tạo bản sao thứ hai của bất kỳ thứ nào | clarifications.md — "Shared chrome", "Award images" |
| F001_Login | feature | Bộ chọn ngôn ngữ VN/EN trên header đã promote thành dùng chung; không re-specify ở đây | clarifications.md — "Shared chrome" |
| `@playwright/test` | infrastructure | Cần cho `testPolicy: e2e-red-first` — màn hình có chuyển trạng thái thật (bấm menu → cuộn + đổi mục sáng, scroll-spy, deep link) | `e2e/award-system.spec.ts`, `playwright.config.ts` |
| Ảnh thiết kế đã xuất (`award-*.png`, keyvisual, chữ hình ROOT FURTHER, nền khối Kudos) | data | Toàn bộ ảnh của màn hình lấy từ bộ đã có, không xuất thêm | clarifications.md — "Award images"; assumption A1, A3 |

### Follow-ups ghi nhận, không xử lý ở tính năng này

- **FUP-01 — Header dính trong suốt 80% không có backdrop blur, nội dung trang lộ xuyên qua.** `home-header.tsx` dùng nền `rgba(16,20,23,0.8)` và không có `backdrop-filter`; ở bề rộng 375px, dòng tiền vàng `8.000.000 VNĐ` cuộn thấy rõ trên nhãn nav. Khâu kiểm thử đã đối chứng: nền header **giống hệt nhau** trên `/` và `/awards-information`, và tỉ lệ pixel không-phải-nền ở dải header tại 375px **cao hơn ở trang chủ (22%) so với màn hình này (10%)**. Đây là khiếm khuyết có sẵn của header dùng chung, màn hình này chỉ làm nó dễ thấy hơn. Thuộc về một ticket riêng trên `home-header.tsx` (ORCH-03 khoá read-only).
- **FUP-02 — Cột đơn vị số lượng cố định `w-[60px]`, hợp với copy VI nhưng chật với EN.** Đề xuất `max-w-[88px]` bị bỏ qua có chủ đích: `max-w` cho phép `Cá nhân` co về một dòng, tức là đổi cách render VI mà thiết kế đã quy định và khâu kiểm thử đã đo. Sửa locale phụ chưa có test bằng cách dịch chuyển locale mặc định đã có test là đánh đổi sai ở giai đoạn này. Xem lại khi EN có vòng kiểm thử hình ảnh riêng.

## 13. Configuration

N/A — no user-facing configuration constants for this feature.
