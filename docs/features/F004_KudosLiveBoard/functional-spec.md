---
status: draft
authored_by: takumi
created: 2026-09-06
lang: vi
---

**Priority**: P1
**Type**: mixed

## 1. Overview

**Problem:** Sun* chưa có nơi công khai cho thấy các lời cảm ơn (Kudos) đang diễn ra trong công ty — không ai nhìn được ai đang được ghi nhận, không lọc được theo hashtag hay phòng ban, và không có chỗ nào cho một Sunner thấy vị trí đóng góp của chính mình.
**Solution:** Màn hình công khai `/kudos` hiển thị carousel HIGHLIGHT gồm 5 kudos được tim nhiều nhất, bộ lọc Hashtag/Phòng ban áp đồng thời lên cả carousel lẫn feed đầy đủ, bảng SPOTLIGHT dạng word-cloud kèm ticker hoạt động trực tiếp, feed ALL KUDOS cuộn vô hạn, và một sidebar cá nhân hiển thị số liệu ghi nhận + bảng xếp hạng quà tặng. Người xem đã đăng nhập thả tim được và lượt thích được lưu lại; khách ẩn danh xem được toàn bộ nội dung nhưng nút tim bị khoá.
**Scope:** Thay thế trang `ComingSoon` hiện có tại `/kudos` bằng màn hình thật; xem/lọc/tương tác với Kudos; đây là schema Postgres đầu tiên repo này sở hữu (migration + RLS + seed).
**Non-Scope:** Viết Kudos mới, mở Secret Box, xem chi tiết một Kudos, trang hồ sơ Sunner, cộng dồn số tim vào tài khoản người gửi, cấu hình ngày đặc biệt nhân đôi tim, bảng xếp hạng thăng hạng — mỗi mục là một CTA thật dẫn tới route `ComingSoon` riêng, không xây ở bản vẽ này (clarifications.md, quyết định #5 và #6).

**Actors**

| Actor | Description | Primary goal |
|-------|--------------|---------------|
| Sunner (đã đăng nhập) | Nhân viên Sun* đã đăng nhập | Xem, lọc, thả tim và chia sẻ Kudos; xem số liệu ghi nhận của chính mình |
| Khách ẩn danh | Người truy cập `/kudos` chưa đăng nhập | Xem toàn bộ nội dung công khai của màn hình (không thả tim được) |

## 2. Functional Capabilities

| ID | Capability | What the user can do | User Stories | Requirements | Business Rules | Screens |
|----|------------|------------------------|-----------------|---------------|-------------------|---------|
| CAP-01 | Xem & lọc kudos | Xem carousel Highlight và feed All Kudos đầy đủ, lọc theo Hashtag/Phòng ban | US001, US002, US003 | FR-001, FR-002, FR-201, FR-202, FR-203, FR-204, FR-206, FR-601 | DEC-001, DEC-002 | TBD (draft) |
| CAP-02 | Tương tác với một kudos | Thả/gỡ tim, copy link chia sẻ, bấm hashtag trên card để lọc | US004, US005 | FR-401, FR-402, FR-403, FR-602 | BR-001, BR-002, BR-003, DEC-003, SM-001 | TBD (draft) |
| CAP-03 | Khám phá Spotlight board | Xem word-cloud + ticker hoạt động trực tiếp, tìm tên trong board | US006 | FR-205 | — | TBD (draft) |
| CAP-04 | Xem vị trí ghi nhận cá nhân | Xem 5 số liệu của bản thân và bảng xếp hạng quà tặng | US007 | FR-207 | BR-004 | TBD (draft) |
| CAP-05 | Tiếp cận các bề mặt Kudos liên quan | Vào các CTA dẫn tới soạn Kudos, Secret Box, chi tiết Kudos, hồ sơ Sunner (đều là `ComingSoon`) | US008 | FR-101 | — | TBD (draft) |

## 3. Open Decisions

None — no unresolved domain confirmations. Bốn câu hỏi còn để ngỏ của phiên nghiên cứu (auth guard toàn màn hình, cộng dồn tim đặc biệt, phân biệt lượt tim đặc biệt ở backend, đích tìm kiếm Sunner) đã được orchestrator quyết định phương án mặc định trong `clarifications.md` § Unresolved questions và không chặn việc triển khai — xem `technical-spec.md § 5.3 Unresolved Questions` để không lặp lại ở đây.

## 4. Requirements

### Foundation (0xx)

- **FR-001** Supabase local project được seed bằng dữ liệu phòng ban, hashtag, Sunner, kudos, liên kết kudos-hashtag, ảnh đính kèm, lượt thích, quà tặng và sự kiện ticker — chép nguyên văn từ frame Figma.
- **FR-002** Kiểu dữ liệu Supabase được sinh tự động và commit tại `lib/supabase/database.types.ts`.

### Navigation (1xx)

- **FR-101** `/kudos` truy cập được công khai từ nav trang chủ và CTA của khối `KudosPromo`, không yêu cầu đăng nhập.

### Kudos Live Board (2xx)

- **FR-201** Hero hiển thị tiêu đề "Hệ thống ghi nhận và cảm ơn", wordmark KUDOS, thanh soạn Kudos (dẫn tới `/kudos/new`) và ô tìm Sunner (tối đa 100 ký tự, submit tới `/profile`).
- **FR-202** HIGHLIGHT KUDOS hiển thị carousel gồm 5 kudos nhiều tim nhất, tính lại sau mỗi lần lọc; mũi tên trước/sau 60px disable ở hai đầu; có phân trang dạng `hiện tại/tổng`.
- **FR-203** Bộ lọc Hashtag và Phòng ban AND-combine trên cả hai khu vực Highlight và All Kudos, và reset carousel về slide 1; chọn lại option đang chọn sẽ bỏ lọc.
- **FR-204** Card kudos hiển thị chip người gửi/nhận, badge kèm tooltip hoa-thị, mốc thời gian, nhãn campaign, nội dung message bị clamp dòng, dãy hashtag (tối đa 5), nút tim + số đếm, Copy Link; card Highlight có thêm "Xem chi tiết"; card feed có thêm gallery đính kèm (tối đa 5) và bút sửa cho kudos của chính người xem.
- **FR-205** SPOTLIGHT BOARD hiển thị word-cloud tên người nhận theo bố cục xác định trước (không random giữa server và client), điều khiển Pan/Zoom và expand toàn màn hình, ticker hoạt động trực tiếp, và ô tìm kiếm (tối đa 100 ký tự) thu hẹp các node hiển thị.
- **FR-206** ALL KUDOS hiển thị feed đầy đủ với cuộn vô hạn và trạng thái rỗng "Hiện tại chưa có Kudos nào."
- **FR-207** Sidebar hiển thị 5 số liệu ghi nhận của Sunner đang đăng nhập, link "Mở Secret Box", và bảng xếp hạng "10 SUNNER NHẬN QUÀ MỚI NHẤT"; khách ẩn danh thấy sidebar của Sunner mẫu đã seed.

### Interaction (4xx)

- **FR-401** Bấm nút tim một kudos toggle một lượt thích được lưu lại cho người xem đã đăng nhập; số đếm và trạng thái pressed giữ nguyên sau khi tải lại trang.
- **FR-402** Bấm Copy Link ghi URL của kudos vào clipboard và hiện toast "Link copied — ready to share!".
- **FR-403** Bấm một hashtag chip trên card đặt hashtag đó làm bộ lọc Hashtag đang hoạt động.

### Security (6xx)

- **FR-601** Khách ẩn danh có toàn quyền đọc mọi khu vực của màn hình — không có nội dung nào bị ẩn.
- **FR-602** Nút tim bị khoá khi không có phiên đăng nhập hoặc khi người xem chính là người gửi kudos đó.

## 5. Business Rules

- Số tim hiển thị bằng mốc đã seed cộng số lượt thích thật, để dữ liệu mẫu từ frame ("1.000") hiển thị đúng cho tới khi có lượt tim thật đầu tiên. (BR-001)
- Mỗi người xem chỉ thả được một tim cho một kudos, ép bằng ràng buộc duy nhất trong database. (BR-002)
- Người gửi không thể tự thả tim cho kudos của chính mình. (BR-003)
- Khách ẩn danh xem sidebar của một Sunner mẫu đã seed sẵn (không gắn với tài khoản thật), để khối này luôn có đúng một trạng thái hiển thị. (BR-004)
- Carousel Highlight luôn là 5 kudos nhiều tim nhất, tính lại mỗi khi bộ lọc đổi và quay về slide 1. (DEC-001)
- Chọn hashtag hoặc phòng ban lọc đồng thời cả Highlight và All Kudos; chọn lại option đang chọn để bỏ lọc. (DEC-002)
- Nút tim bị khoá khi chưa đăng nhập hoặc khi đang xem đúng kudos mình gửi; các trường hợp còn lại nút tim hoạt động và lưu lại lượt thích. (DEC-003)
- Một lượt thích của một người xem trên một kudos chỉ có hai trạng thái — chưa thích / đã thích — và chuyển đổi qua đúng một hành động thả tim. (SM-001)

## 6. Screens

| Screen Name | SCR### | What User Sees | What User Can Do |
|-------------|--------|-----------------|-------------------|
| {Kudos Live Board} | {SCR###_NameSlug — allocated at promote} | Hero + carousel Highlight + bộ lọc + Spotlight board + feed All Kudos + sidebar cá nhân, trên nền `/kudos` công khai | Lọc, cuộn, thả tim, copy link, tìm kiếm trong Spotlight, mở các CTA dẫn tới soạn Kudos/Secret Box/chi tiết/hồ sơ |

### User Journey

1. Người dùng (đăng nhập hoặc ẩn danh) vào `/kudos` và thấy hero, carousel Highlight 5 kudos nhiều tim nhất, và bộ lọc Hashtag/Phòng ban.
2. Người dùng chọn một hashtag hoặc phòng ban — cả carousel Highlight và feed All Kudos lọc lại theo cùng bộ lọc, carousel quay về slide 1.
3. Người dùng cuộn xuống Spotlight board, gõ tên vào ô tìm kiếm — word-cloud thu hẹp còn các node khớp tên.
4. Người dùng cuộn tới ALL KUDOS, feed tải thêm card khi chạm tới cuối danh sách hiện có.
5. Người dùng (đã đăng nhập) bấm tim trên một card — số đếm tăng 1 và nút chuyển trạng thái pressed, lưu lại kể cả sau khi tải lại trang.
6. Người dùng bấm Copy Link trên một card — URL được chép vào clipboard, toast xác nhận hiện ra.
7. Người dùng nhìn sang sidebar bên phải, thấy 5 số liệu ghi nhận của bản thân (hoặc của Sunner mẫu nếu đang ẩn danh) và bảng xếp hạng quà tặng.
8. Người dùng bấm vào thanh soạn Kudos, "Mở Secret Box", "Xem chi tiết", tên/avatar một Sunner, hoặc ô tìm Sunner ở hero — mỗi nơi dẫn tới một route thật hiển thị `ComingSoon` vì bề mặt đó thuộc một commission khác.

## 7. User Stories

### US001_ViewHighlightKudos — Xem carousel Highlight Kudos

**Actor:** Khách ẩn danh
**Goal:** Xem nhanh 5 kudos đang được cộng đồng ghi nhận nhiều nhất mà không cần đăng nhập.
**Business value:** Cho thấy hoạt động ghi nhận sôi động của Sun* ngay từ lần ghé thăm đầu tiên, không có rào cản đăng nhập.

**Acceptance Criteria:**
- [ ] Carousel hiển thị tối đa 5 slide, slide giữa nổi bật, hai bên mờ và không tương tác được.
- [ ] Mũi tên trước/sau bị disable đúng ở slide đầu/cuối; phân trang hiện đúng dạng `hiện tại/tổng`.

### US002_FilterKudosByHashtagAndDepartment — Lọc kudos theo Hashtag/Phòng ban

**Actor:** Khách ẩn danh
**Goal:** Thu hẹp cả carousel Highlight và feed All Kudos về đúng chủ đề hoặc phòng ban đang quan tâm.
**Business value:** Giúp người xem tìm nhanh những lời cảm ơn liên quan tới mình hoặc đội nhóm mình, thay vì lướt toàn bộ feed.

**Acceptance Criteria:**
- [ ] Chọn một hashtag hoặc phòng ban lọc lại cả hai khu vực cùng lúc và đưa carousel về slide 1.
- [ ] Chọn lại chính option đang chọn sẽ bỏ lọc, trả cả hai khu vực về trạng thái đầy đủ.

### US003_BrowseAllKudosFeed — Cuộn xem toàn bộ Kudos

**Actor:** Khách ẩn danh
**Goal:** Xem hết các kudos đang có, tải thêm khi cuộn tới cuối danh sách hiện tại.
**Business value:** Cho phép khám phá sâu hơn 5 kudos nổi bật ở carousel, không giới hạn số lượng xem được.

**Acceptance Criteria:**
- [ ] Feed tải thêm card khi phần tử sentinel cuối feed lọt vào khung nhìn, tới khi hết dữ liệu.
- [ ] Khi không có kudos nào khớp bộ lọc, feed hiện đúng "Hiện tại chưa có Kudos nào."

### US004_HeartKudos — Thả tim cho một kudos

**Actor:** Sunner (đã đăng nhập)
**Goal:** Bày tỏ sự ủng hộ với một lời cảm ơn bằng cách thả tim, và biết lượt thích của mình được lưu lại thật sự.
**Business value:** Tạo tương tác thật (không phải state ảo phía client) làm dữ liệu ghi nhận đáng tin cậy hơn.

**Acceptance Criteria:**
- [ ] Bấm tim đổi trạng thái pressed và tăng/giảm số đếm đúng 1 đơn vị theo chiều bấm.
- [ ] Tải lại trang sau khi bấm tim vẫn giữ đúng trạng thái pressed và số đếm mới.
- [ ] Nút tim bị khoá trên kudos do chính Sunner này gửi.

### US005_CopyKudosLink — Chia sẻ link một kudos

**Actor:** Khách ẩn danh
**Goal:** Lấy nhanh đường link tới một kudos cụ thể để chia sẻ cho người khác.
**Business value:** Giúp lan toả một lời cảm ơn ra ngoài phạm vi màn hình, không cần đăng nhập.

**Acceptance Criteria:**
- [ ] Bấm Copy Link ghi đúng URL của kudos đó vào clipboard.
- [ ] Toast "Link copied — ready to share!" hiện ra ngay sau khi copy.

### US006_SearchSpotlightBoard — Tìm tên trong Spotlight board

**Actor:** Khách ẩn danh
**Goal:** Tìm nhanh một Sunner cụ thể giữa word-cloud đông người trên Spotlight board.
**Business value:** Word-cloud đẹp nhưng khó dò bằng mắt khi có nhiều tên; ô tìm kiếm giúp xác nhận một cái tên có đang được nhắc tới không.

**Acceptance Criteria:**
- [ ] Gõ vào ô tìm kiếm (tối đa 100 ký tự) chỉ giữ lại các node tên khớp.
- [ ] Không có tên nào khớp thì hiện trạng thái rỗng của Spotlight board.

### US007_ViewPersonalSidebar — Xem vị trí ghi nhận cá nhân

**Actor:** Sunner (đã đăng nhập)
**Goal:** Biết mình đã nhận/gửi bao nhiêu Kudos, nhận bao nhiêu tim, và mình có đang nằm trong bảng xếp hạng quà tặng không.
**Business value:** Biến việc ghi nhận thành một chỉ số cá nhân người dùng quay lại xem, không chỉ là feed công khai.

**Acceptance Criteria:**
- [ ] Sidebar hiện đúng 5 dòng số liệu theo thứ tự cố định của Sunner đang đăng nhập.
- [ ] Khách ẩn danh vẫn thấy đúng một trạng thái sidebar (rơi về Sunner mẫu đã seed), không có trạng thái thứ hai nào khác.

### US008_NavigateToRelatedSurfaces — Tiếp cận các bề mặt Kudos khác

**Actor:** Khách ẩn danh
**Goal:** Bấm vào soạn Kudos, Secret Box, chi tiết một kudos, hồ sơ Sunner, hoặc tìm hồ sơ Sunner, và biết rõ những bề mặt đó chưa sẵn sàng thay vì gặp lỗi 404.
**Business value:** Giữ mọi CTA trên màn hình đều điều hướng được thật, trung thực về phạm vi đã xây ở bản vẽ này.

**Acceptance Criteria:**
- [ ] Mỗi CTA (soạn Kudos, Mở Secret Box, Xem chi tiết, avatar/tên, ô tìm Sunner) dẫn tới một route thật.
- [ ] Route đích hiển thị `ComingSoon`, không phải trang lỗi.

## 8. Scenarios

### US001_ViewHighlightKudos — Happy Path

**Given** người dùng chưa đăng nhập, **When** họ mở `/kudos`, **Then** carousel Highlight hiện tối đa 5 kudos, sắp theo số tim giảm dần, slide giữa nổi bật.

### US001_ViewHighlightKudos — Error: không có kudos nào khớp bộ lọc hiện tại

**Given** một bộ lọc đang lọc ra 0 kudos, **When** carousel Highlight tính lại top-5, **Then** carousel hiện trạng thái rỗng thay vì slide trống.

### US002_FilterKudosByHashtagAndDepartment — Happy Path

**Given** người dùng đang ở `/kudos`, **When** họ chọn một hashtag, **Then** cả Highlight và All Kudos chỉ còn kudos mang hashtag đó, và carousel quay về slide 1.

### US002_FilterKudosByHashtagAndDepartment — Error: chọn lại option đang lọc

**Given** một hashtag đang được chọn, **When** người dùng bấm lại đúng option đó, **Then** bộ lọc bị bỏ, cả hai khu vực trả về trạng thái đầy đủ.

### US003_BrowseAllKudosFeed — Happy Path

**Given** người dùng đã cuộn hết các card đang tải, **When** sentinel cuối feed lọt vào khung nhìn, **Then** trang tiếp theo của feed được tải thêm vào cuối danh sách.

### US003_BrowseAllKudosFeed — Error: hết dữ liệu để tải thêm

**Given** feed đã hiển thị toàn bộ kudos khớp bộ lọc, **When** sentinel lọt vào khung nhìn lần nữa, **Then** không có trang mới nào được tải, feed dừng lặng lẽ ở trạng thái hiện tại.

### US004_HeartKudos — Happy Path

**Given** Sunner đã đăng nhập xem một kudos không phải do mình gửi, **When** họ bấm nút tim, **Then** số đếm tăng 1, nút chuyển trạng thái pressed, và giá trị này còn nguyên sau khi tải lại trang.

### US004_HeartKudos — Error: cố thả tim trên kudos của chính mình

**Given** Sunner đang xem kudos do chính mình gửi, **When** họ nhìn vào nút tim, **Then** nút hiện ở trạng thái khoá (disabled), không nhận click.

### US005_CopyKudosLink — Happy Path

**Given** người dùng đang xem một card kudos, **When** họ bấm Copy Link, **Then** URL của kudos được chép vào clipboard và toast "Link copied — ready to share!" hiện ra.

### US005_CopyKudosLink — Error: trình duyệt từ chối quyền clipboard

**Given** trình duyệt chặn quyền ghi clipboard, **When** người dùng bấm Copy Link, **Then** hành động thất bại một cách rõ ràng thay vì hiện toast thành công giả — cách xử lý cụ thể chưa được `clarifications.md` mô tả, ghi nhận là chi tiết kỹ thuật cần đọc thêm code ở `technical-spec.md § 5.3`.

### US006_SearchSpotlightBoard — Happy Path

**Given** Spotlight board đang hiện đủ các node tên, **When** người dùng gõ một tên vào ô tìm kiếm, **Then** chỉ các node tên khớp còn hiển thị.

### US006_SearchSpotlightBoard — Error: không có tên nào khớp

**Given** người dùng gõ một chuỗi không khớp tên nào, **When** kết quả tìm kiếm rỗng, **Then** Spotlight board hiện trạng thái rỗng của board.

### US007_ViewPersonalSidebar — Happy Path

**Given** một Sunner đã đăng nhập mở `/kudos`, **When** trang tải xong, **Then** sidebar hiện đúng 5 số liệu và bảng xếp hạng quà tặng của chính Sunner đó.

### US007_ViewPersonalSidebar — Error: khách ẩn danh không có dữ liệu cá nhân thật

**Given** người xem chưa đăng nhập, **When** trang tải xong, **Then** sidebar vẫn hiện đúng một trạng thái — số liệu của Sunner mẫu đã seed — chứ không để trống hay báo lỗi.

### US008_NavigateToRelatedSurfaces — Happy Path

**Given** người dùng đang ở `/kudos`, **When** họ bấm vào thanh soạn Kudos, **Then** trình duyệt điều hướng tới `/kudos/new`, nơi hiển thị `ComingSoon`.

### US008_NavigateToRelatedSurfaces — Error: gõ vào ô tìm Sunner ở hero rồi submit

**Given** người dùng gõ tên một Sunner vào ô tìm ở hero, **When** họ submit, **Then** trình duyệt điều hướng tới `/profile` kèm từ khoá tìm kiếm, nơi hiển thị `ComingSoon` vì màn hình kết quả tìm Sunner thật chưa tồn tại ở web.

## 9. Edge Cases

| Scenario | What Happens | User-Facing Message |
|----------|--------------|----------------------|
| Bộ lọc Hashtag + Phòng ban không khớp kudos nào | Cả Highlight và All Kudos đều rỗng | "Hiện tại chưa có Kudos nào." |
| Nội dung message dài hơn giới hạn dòng clamp (3 dòng Highlight / 5 dòng feed) | Nội dung bị cắt và thêm dấu ba chấm | "None — cắt lặng lẽ, không có thông báo" |
| Khách ẩn danh cố thả tim | Nút tim đã ở trạng thái disabled nên không nhận click; nếu request vẫn tới server thì bị RLS từ chối | "None — chặn ở giao diện trước khi có request nào" |
| Ô tìm Spotlight board không khớp tên nào | Ẩn hết node, hiện trạng thái rỗng riêng của board | "TBD (draft) — chưa có copy xác nhận từ frame; test-contract chỉ yêu cầu phần tử `spotlight-empty` xuất hiện, chưa cho nội dung chữ." |
| Cuộn tới hết dữ liệu đã seed của All Kudos | Sentinel không còn tải thêm trang nào | "None — dừng lặng lẽ, không có thông báo hết dữ liệu" |
| Bấm tim lần hai trên một kudos đã thích | Lượt thích bị gỡ, số đếm giảm đúng 1, trạng thái pressed quay lại ban đầu | "None — không có toast, chỉ đổi trạng thái nút và số đếm" |

## 10. Edge Behaviours to Verify

- **FR-202** → Carousel luôn hiện đúng 5 kudos nhiều tim nhất hiện có, tính lại ngay sau khi bộ lọc đổi.
- **FR-203** → Chọn/bỏ chọn một filter option lọc đồng thời cả hai khu vực và luôn đưa carousel về slide 1.
- **FR-204** → Card Highlight và card feed clamp nội dung đúng số dòng khác nhau (3 và 5).
- **FR-205** → Bố cục word-cloud giống hệt nhau giữa lần render đầu tiên trên server và trên trình duyệt (không lệch do random).
- **FR-206** → Feed chỉ tải thêm khi sentinel lọt vào khung nhìn, không tải trước khi cần.
- **FR-207** → Sidebar luôn hiện đúng một trạng thái duy nhất, kể cả khi chưa đăng nhập.
- **FR-401** → Số đếm tim và trạng thái pressed giữ nguyên sau khi tải lại trang.
- **FR-402** → Toast copy-link luôn xuất hiện ngay sau một cú bấm Copy Link thành công.
- **FR-601** → Mọi khu vực của màn hình hiển thị đầy đủ cho khách ẩn danh, không thiếu nội dung nào.
- **FR-602** → Nút tim bị khoá đúng hai trường hợp: chưa đăng nhập, hoặc đang xem kudos của chính mình.

## 11. Risks & Known Issues

N/A — none found. Đây là bản vẽ greenfield, chưa có code để quan sát hành vi bất thường; các giới hạn phạm vi đã biết (cộng dồn tim đặc biệt, bảng xếp hạng thăng hạng, auth guard toàn màn hình) được ghi ở `technical-spec.md § 5.3 Unresolved Questions`, không phải defect.

## 12. Dependencies

| Dependency | Type | Why this feature needs it | Evidence |
|------------|------|-----------------------------|----------|
| Supabase local project | infrastructure | Là nơi lưu schema, RLS và seed mới của tính năng này — schema SQL đầu tiên repo sở hữu | `supabase/config.toml`, `plans/260906-1945-kudos-live-board/clarifications.md` § Session 2026-09-06 (b) |
| `getPageContext()` (chrome dùng chung) | feature | Cung cấp `locale`, `dictionary`, `isAuthenticated` để dựng header/footer và xác định trạng thái đăng nhập của viewer | `app/_page-context.ts` |
| `e2e/auth.setup.ts` (hạ tầng test có sẵn) | infrastructure | Bộ test `kudos-authed` tái sử dụng storage state đã có sẵn (`e2e/.auth/user.json`) thay vì tạo setup mới | `plans/260906-1945-kudos-live-board/test-contract.md` § Supabase amendment |

## 13. Configuration

```text
SUNNER_SEARCH_MAX_LEN = 100     # số ký tự tối đa cho ô tìm Sunner ở hero và ô tìm Spotlight board
HIGHLIGHT_CAROUSEL_SIZE = 5     # số kudos hiển thị trong carousel Highlight
CARD_HASHTAG_MAX = 5            # số hashtag hiển thị tối đa trên một card trước khi rút gọn
CARD_ATTACHMENT_MAX = 5         # số ảnh đính kèm tối đa trên một card feed
GIFT_LEADERBOARD_SIZE = 10      # số dòng trong bảng "10 SUNNER NHẬN QUÀ MỚI NHẤT"
```
