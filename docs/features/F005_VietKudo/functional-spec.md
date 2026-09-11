---
status: draft
authored_by: takumi
created: 2026-09-07
lang: vi
---

**Priority**: P1
**Type**: mixed

## 1. Overview

**Problem:** Bảng tin Kudos (`/kudos`, F004) đã công khai, nhưng chưa ai gửi được Kudos thật — CTA "Viết Kudo" trên bảng tin dẫn tới một trang `ComingSoon`. Đây cũng là màn hình đầu tiên trong repo bắt buộc đăng nhập để dùng và là form ghi dữ liệu đầu tiên (mọi ghi trước đó chỉ là thả tim).
**Solution:** Trang `/kudos/new` — chỉ Sunner đã đăng nhập vào được — cho phép chọn người nhận qua autocomplete, đặt một Danh hiệu (tiêu đề Kudos hiển thị trên bảng tin), viết nội dung trong ô soạn có định dạng (đậm/nghiêng/gạch ngang/danh sách đánh số/liên kết/trích dẫn) kèm mention `@ + tên` đồng nghiệp, gắn 1–5 hashtag, đính kèm tối đa 5 ảnh thật tải lên Supabase Storage, và tuỳ chọn gửi ẩn danh kèm tên hiển thị. Gửi thành công đưa người dùng về `/kudos`, Kudos mới hiện ngay trên bảng tin.
**Scope:** Form soạn Kudos đầy đủ tại `/kudos/new`; validate cả client lẫn server; tự động cấp một dòng `sunners` cho Sunner đăng nhập lần đầu chưa từng viết Kudos; migration mở quyền INSERT cho `kudos`, `kudos_hashtags`, `kudos_attachments`, `sunners`.
**Non-Scope:** Sửa hoặc xoá một Kudos đã gửi (`Màn Sửa bài viết` và `Admin - Review content` là commission khác); giới hạn độ dài nội dung hay bộ đếm ký tự (không có trong thiết kế); màn hình duyệt/kiểm duyệt nội dung.

**Actors**

| Actor | Description | Primary goal |
|-------|--------------|---------------|
| Sunner (đã đăng nhập) | Nhân viên Sun* đã đăng nhập, actor duy nhất của màn hình này | Soạn và gửi một Kudos cho đồng nghiệp, có thể ẩn danh |

## 2. Functional Capabilities

| ID | Capability | What the user can do | User Stories | Requirements | Business Rules | Screens |
|----|------------|------------------------|-----------------|---------------|-------------------|---------|
| CAP-01 | Soạn nội dung Kudos | Chọn người nhận, đặt Danh hiệu, viết nội dung có định dạng và mention đồng nghiệp | US001 | FR-102, FR-201, FR-202, FR-203, FR-204, FR-213, FR-214, FR-215, FR-216, FR-217, FR-218, FR-219 | BR-006 | TBD (draft) |
| CAP-02 | Đính kèm hashtag và ảnh | Gắn 1–5 hashtag từ danh sách có sẵn, đính kèm tối đa 5 ảnh thật | US002 | FR-001, FR-205, FR-206 | BR-002, BR-003, BR-004 | TBD (draft) |
| CAP-03 | Gửi hoặc hủy Kudos | Bật ẩn danh kèm tên hiển thị tuỳ chọn, gửi (validate đầy đủ) hoặc hủy bỏ | US003 | FR-002, FR-003, FR-101, FR-207, FR-401, FR-402, FR-403, FR-601, FR-602 | BR-001, BR-005, DEC-001, DEC-002 | TBD (draft) |

## 3. Open Decisions

None — no unresolved domain confirmations. `/tkm:takumi --auto` đã quyết định phương án mặc định/khuyến nghị cho mọi câu hỏi mở trong `clarifications.md`, không chặn triển khai — xem `technical-spec.md § 5.3 Unresolved Questions` để không lặp lại ở đây.

## 4. Requirements

### Foundation (0xx)

- **FR-001** Supabase local có một bucket Storage riêng cho ảnh đính kèm Kudos, giới hạn ghi cho đúng chủ sở hữu ảnh.
- **FR-002** Migration bổ sung ba cột mới trên `kudos` (`is_anonymous`, `anonymous_name`, `message_format`) cùng policy INSERT cho `kudos`, `kudos_hashtags`, `kudos_attachments`, `sunners`.
- **FR-003** Một phòng ban `Unassigned` được seed sẵn (không nằm trong danh sách lọc Phòng ban) để làm phòng ban mặc định cho Sunner mới được tự động cấp.

### Navigation (1xx)

- **FR-101** `/kudos/new` chỉ vào được khi đã đăng nhập; chưa đăng nhập bị chuyển hướng sang `/login`.
- **FR-102** Thanh soạn Kudos trên bảng tin `/kudos` dẫn thẳng tới `/kudos/new` bằng điều hướng trang thật, không phải modal chồng trang.

### Viết Kudo (2xx)

- **FR-201** Các trường hiển thị đúng thứ tự: Người nhận, Danh hiệu, nội dung, Hashtag, Image, checkbox gửi ẩn danh, rồi hai nút Hủy/Gửi ở cuối.
- **FR-202** Trường Người nhận là ô tìm kiếm bắt buộc, chỉ chọn được từ danh sách Sunner có sẵn qua autocomplete; khoảng trắng đầu/cuối chuỗi tìm được bỏ qua.
- **FR-203** Trường Danh hiệu là input văn bản bắt buộc; nội dung nhập sẽ hiển thị làm tiêu đề Kudos trên bảng tin.
- **FR-204** Ô soạn nội dung bắt buộc có toolbar 6 định dạng (đậm, nghiêng, gạch ngang, danh sách đánh số, chèn liên kết qua hộp thoại `Thêm đường dẫn` hai trường — FR-213..FR-219, trích dẫn) và hỗ trợ gõ `@ + tên` để mở danh sách gợi ý và mention một đồng nghiệp.
- **FR-205** Trường Hashtag bắt buộc tối thiểu 1, tối đa 5; chọn qua dropdown đa chọn có trạng thái (FR-208..FR-212) lấy dữ liệu hashtag có sẵn, hiển thị dạng chip có nút xoá riêng từng chip.
- **FR-206** Trường Image không bắt buộc, tối đa 5 ảnh thật được tải lên Storage; nút thêm ảnh ẩn hoàn toàn khi đủ 5 và hiện lại ngay khi một ảnh bị xoá; chỉ nhận file ảnh, các định dạng khác bị từ chối.
- **FR-207** Checkbox "Gửi lời cám ơn và ghi nhận ẩn danh" tắt theo mặc định; bật lên hiện thêm một ô nhập tên hiển thị ẩn danh (tuỳ chọn, không bắt buộc).
- **FR-208** Mỗi dòng trong dropdown Hashtag hiển thị trạng thái đã chọn của chính nó: nền nổi `rgba(255,234,158,0.2)` kèm icon check tròn 24×24 bên phải. Dòng chưa chọn giữ đúng một khoảng trống 24×24 ở chỗ icon để danh sách không xô lệch khi trạng thái đổi.
- **FR-209** Bấm một dòng **đã chọn** trong dropdown gỡ hashtag đó ra: icon check biến mất, nền trở lại bình thường, chip tương ứng biến mất. Bấm một dòng **chưa chọn** thêm hashtag đó như cũ.
- **FR-210** Khi đã chọn đủ 5 hashtag, mọi dòng **chưa chọn** bị vô hiệu hoá — mờ đi, `disabled`, không phản hồi click. Các dòng **đã chọn** vẫn bấm được: đó là lối thoát duy nhất khỏi trạng thái đầy.
- **FR-211** Khi đã chọn đủ 5 hashtag, thông báo "Tối đa 5 hashtag" hiển thị thường trực như lý do của trạng thái vô hiệu hoá ở FR-210, và biến mất ngay khi số hashtag tụt xuống dưới 5.
- **FR-212** Dropdown giữ nguyên thứ tự `public.hashtags.position` lấy từ Supabase; chọn hay bỏ chọn không sắp xếp lại dòng nào.
- **FR-213** Hộp thoại chèn liên kết hiển thị tiêu đề `Thêm đường dẫn` và hai ô nhập xếp dọc, mỗi ô có nhãn nằm **bên trái**: `Nội dung` rồi `URL`. Bấm nhãn `Nội dung` chuyển focus sang ô nhập của nó; nhãn `URL` chỉ để thông tin. Ô đang được focus hiện viền nổi.
- **FR-214** Ô `Nội dung` là văn bản hiển thị của liên kết: bắt buộc, 1–100 ký tự, không được chỉ gồm khoảng trắng. Khi mở hộp thoại, nếu trong ô soạn đang bôi đen một đoạn khác rỗng thì ô này điền sẵn đoạn đó; nếu không thì để trống.
- **FR-215** Ô `URL` bắt buộc, 5–2048 ký tự, và phải là URL hợp lệ theo danh sách scheme đã chốt (`http:`, `https:`, `mailto:`). Định dạng được kiểm khi rời ô (blur) và khi bấm `Lưu`. Khi mở hộp thoại ô luôn trống.
- **FR-216** Nút `Lưu` luôn bấm được. Bấm `Lưu` kiểm cả hai ô: mỗi ô sai hiện thông báo lỗi của riêng nó, hộp thoại không đóng và không liên kết nào được chèn. Cả hai hợp lệ thì liên kết được chèn và hộp thoại đóng.
- **FR-217** Chèn thành công thay đoạn văn bản đang bôi đen bằng giá trị ô `Nội dung` (chèn tại con trỏ nếu không bôi đen gì), rồi đánh dấu liên kết mang `href` là giá trị ô `URL` lên đúng đoạn vừa chèn. Định dạng nào đang chồng lên vùng bị thay sẽ bị bỏ, không neo lại bằng phỏng đoán.
- **FR-218** Nút `Hủy`, phím `Escape` và bấm ra ngoài đều đóng hộp thoại và hủy mọi thay đổi: không chèn gì, và giá trị hai ô không được giữ lại cho lần mở sau.
- **FR-219** Nhóm nút nằm cố định ở đáy hộp thoại và ở lại đó khi nội dung cuộn. `Hủy` là nút nhỏ có viền kèm icon `X`; `Lưu` là nút lớn nền vàng `#FFEA9E` chiếm phần chiều ngang còn lại, kèm icon liên kết.

### Interaction (4xx)

- **FR-401** Nút Gửi bị khoá khi Người nhận, Danh hiệu, nội dung hoặc Hashtag còn thiếu; mở khoá ngay khi đủ cả bốn.
- **FR-402** Bấm Gửi khi còn thiếu trường bắt buộc hiển thị đồng thời lỗi "Không được để trống" cho mọi trường còn thiếu, không dừng ở lỗi đầu tiên; mỗi rule vẫn được kiểm tra lại phía server, không chỉ dựa vào trạng thái nút.
- **FR-403** Gửi thành công đưa trình duyệt về `/kudos` và Kudos mới xuất hiện ngay trên bảng tin; bấm Hủy đóng form ngay lập tức, không lưu gì, cũng đưa về `/kudos`.

### Security (6xx)

- **FR-601** `/kudos/new` yêu cầu một phiên đăng nhập hợp lệ; người gửi luôn được suy ra từ phiên đăng nhập, không bao giờ nhận trực tiếp từ dữ liệu client gửi lên.
- **FR-602** Chỉ chủ sở hữu (qua liên kết `sunners.auth_user_id` với phiên đăng nhập) mới ghi được vào `kudos`, `kudos_hashtags`, `kudos_attachments`, `sunners` của chính họ — ràng buộc ở tầng database, không chỉ ở giao diện.

## 5. Business Rules

- Sunner viết Kudos lần đầu được tự động cấp một dòng `sunners` gắn với tài khoản đăng nhập, dùng tên/ảnh từ hồ sơ Google và phòng ban `Unassigned` khi chưa có phòng ban thật; gửi trùng lúc không tạo ra hai dòng trùng nhau. (BR-001)
- Một Kudos phải có tối thiểu 1 và tối đa 5 hashtag; khi đã đủ 5, mọi dòng hashtag chưa chọn trong dropdown bị vô hiệu hoá và "Tối đa 5 hashtag" hiển thị thường trực làm lý do — không hashtag thứ 6 nào được thêm. (BR-002)
- Một Kudos đính kèm tối đa 5 ảnh; nút thêm ảnh ẩn hoàn toàn khi đủ 5 và hiện lại ngay khi một ảnh bị xoá bớt. (BR-003)
- Chỉ file đúng định dạng ảnh mới được đính kèm; file sai định dạng (ví dụ pdf, mp4, txt) bị từ chối ngay khi chọn và không được tải lên. (BR-004)
- Khi gửi ẩn danh, bảng tin công khai hiển thị tên hiển thị ẩn danh (hoặc một nhãn trung lập nếu bỏ trống) thay cho người gửi thật; người nhận luôn hiển thị đúng như đã chọn. (BR-005)
- Một liên kết chỉ vào được nội dung Kudo khi **cả** văn bản hiển thị **và** URL đều hợp lệ; URL phải nằm trong danh sách scheme đã chốt. Đây là chốt chặn thứ nhất trong ba: trình đọc kiểm lại khi phân tích nội dung, trình vẽ kiểm lần nữa khi hiển thị. (BR-006)
- Bật checkbox ẩn danh hiện ngay ô nhập tên hiển thị; tắt lại ẩn ô đó đi. (DEC-001)
- Nút Gửi chuyển từ khoá sang mở ngay khi đủ bốn trường bắt buộc (Người nhận, Danh hiệu, nội dung, Hashtag); thiếu bất kỳ trường nào trong bốn trường đó nút vẫn khoá. (DEC-002)

## 6. Screens

| Screen Name | SCR### | What User Sees | What User Can Do |
|-------------|--------|-----------------|-------------------|
| {Viết Kudo} | {SCR###_NameSlug — allocated at promote} | Trang soạn Kudos: Người nhận, Danh hiệu, ô soạn nội dung có toolbar, Hashtag, Image, checkbox ẩn danh, hai nút Hủy/Gửi | Chọn người nhận, đặt Danh hiệu, viết nội dung có định dạng/mention, gắn hashtag, đính kèm ảnh, bật ẩn danh, gửi hoặc hủy |

### User Journey

1. Sunner đã đăng nhập bấm thanh soạn Kudos trên `/kudos` và được đưa tới `/kudos/new`.
2. Sunner tìm và chọn Người nhận từ danh sách gợi ý, gõ Danh hiệu, rồi viết lời cảm ơn trong ô soạn — có thể bôi đậm/nghiêng/gạch ngang, chèn danh sách đánh số hoặc liên kết, trích dẫn, và gõ `@ + tên` để mention một đồng nghiệp.
3. Sunner bấm "+ Hashtag" chọn 1–5 hashtag; mỗi hashtag hiện thành một chip có thể xoá riêng.
4. Sunner (tuỳ chọn) bấm "+ Image" chọn tối đa 5 ảnh thật; mỗi ảnh hiện thumbnail đúng ảnh đã chọn kèm nút xoá; nút thêm ảnh tự ẩn khi đủ 5.
5. Sunner (tuỳ chọn) bật checkbox gửi ẩn danh — một ô nhập tên hiển thị hiện ra, có thể bỏ trống.
6. Sunner bấm Gửi. Nếu còn thiếu trường bắt buộc, mọi lỗi "Không được để trống" hiện cùng lúc và form không gửi. Nếu đủ, nút chuyển trạng thái đang xử lý rồi trình duyệt quay về `/kudos`, nơi Kudos mới đã hiển thị trên bảng tin.
7. Nếu Sunner bấm Hủy ở bất kỳ lúc nào, form đóng ngay, không lưu gì, và trình duyệt cũng quay về `/kudos`.

## 7. User Stories

### US001_ComposeKudosMessage — Soạn nội dung Kudos

**Actor:** Sunner (đã đăng nhập)
**Goal:** Chọn đúng người nhận, đặt một Danh hiệu, và viết lời cảm ơn có định dạng, có thể mention đồng nghiệp khác trong nội dung.
**Business value:** Lời cảm ơn được trình bày rõ ràng, có thể nhấn mạnh ý chính và nhắc tới người khác — khiến Kudos đọc tự nhiên và cá nhân hơn một dòng văn bản thuần.

**Acceptance Criteria:**
- [ ] Gõ vào ô tìm Người nhận hiện danh sách gợi ý lọc theo tên đã gõ (khoảng trắng thừa được bỏ qua); chọn một tên điền vào trường và đóng danh sách.
- [ ] Bôi đen văn bản trong ô soạn rồi bấm một nút định dạng (đậm/nghiêng/gạch ngang/danh sách đánh số/trích dẫn) áp đúng định dạng đó; bấm nút liên kết mở hộp thoại `Thêm đường dẫn` (điền sẵn đoạn đang bôi đen vào ô `Nội dung`), nhập `Nội dung` và `URL` hợp lệ rồi bấm `Lưu` chèn liên kết vào đúng vị trí đó; bỏ trống hoặc nhập sai thì mỗi ô sai hiện lỗi và hộp thoại không đóng.
- [ ] Gõ `@` rồi tiếp tục gõ tên mở danh sách gợi ý đồng nghiệp; chọn một người chèn đúng tên đó vào nội dung.

### US002_AttachHashtagsAndImages — Đính kèm hashtag và ảnh

**Actor:** Sunner (đã đăng nhập)
**Goal:** Gắn các hashtag phù hợp và đính kèm ảnh minh hoạ thật cho Kudos đang soạn.
**Business value:** Hashtag giúp Kudos được lọc/tìm thấy trên bảng tin; ảnh thật (không phải ảnh mẫu) làm lời cảm ơn đáng tin và sinh động hơn.

**Acceptance Criteria:**
- [ ] Bấm "+ Hashtag" mở danh sách chọn; chọn tối đa 5 hashtag, mỗi hashtag hiện thành một chip; bấm nút xoá trên một chip chỉ xoá đúng chip đó, các chip còn lại giữ nguyên.
- [ ] Cố chọn hashtag thứ 6 bị từ chối: các dòng chưa chọn trong dropdown đã `disabled`, thông báo "Tối đa 5 hashtag" đang hiện, 5 hashtag đã chọn không đổi.
- [ ] Dòng đã chọn hiện icon check và nền nổi; dòng chưa chọn không có icon nhưng vẫn giữ khoảng trống 24×24 nên danh sách không xô lệch.
- [ ] Bấm lại một dòng đã chọn sẽ gỡ đúng hashtag đó — chip tương ứng biến mất, các chip khác nguyên vẹn; ở trạng thái đủ 5, thao tác này mở khoá lại các dòng chưa chọn và ẩn thông báo.
- [ ] Thứ tự dòng trong dropdown khớp `public.hashtags.position` và không đổi qua các lần chọn/bỏ chọn.
- [ ] Bấm "+ Image" chọn một file `.jpg`/`.png` tải lên thành công và hiện đúng ảnh vừa chọn dưới dạng thumbnail có nút xoá; chọn file `.pdf`/`.mp4`/`.txt` bị từ chối với thông báo lỗi định dạng, không có ảnh nào được thêm.
- [ ] Đủ 5 ảnh thì nút "+ Image" biến mất; xoá bớt một ảnh thì nút hiện lại ngay.

### US003_SendOrCancelKudos — Gửi hoặc hủy Kudos, có thể ẩn danh

**Actor:** Sunner (đã đăng nhập)
**Goal:** Gửi Kudos đã soạn (công khai hoặc ẩn danh kèm tên hiển thị tuỳ chọn), hoặc hủy bỏ nếu đổi ý — biết chắc lỗi gì cần sửa nếu form chưa đủ điều kiện gửi.
**Business value:** Người gửi kiểm soát được việc lộ danh tính, và luôn biết chính xác cần sửa gì trước khi Kudos thật sự được ghi nhận.

**Acceptance Criteria:**
- [ ] Nút Gửi khoá khi Người nhận/Danh hiệu/nội dung/Hashtag còn thiếu; mở khoá ngay khi đủ cả bốn.
- [ ] Bấm Gửi khi form còn trống hoàn toàn hiện đồng thời lỗi "Không được để trống" cho Người nhận, Danh hiệu, nội dung và Hashtag; form không được gửi đi.
- [ ] Bật checkbox ẩn danh hiện ngay ô nhập tên hiển thị (tuỳ chọn); tắt lại ẩn ô đó đi; gửi Kudos ẩn danh xong, bảng tin `/kudos` hiển thị tên ẩn danh (hoặc nhãn trung lập nếu bỏ trống) thay cho người gửi thật, người nhận vẫn hiển thị đúng.
- [ ] Gửi thành công đưa trình duyệt về `/kudos` với Kudos mới đã có mặt trên bảng tin; bấm Hủy đóng form ngay, không lưu gì, cũng đưa về `/kudos`.

## 8. Scenarios

**US001_ComposeKudosMessage**
- **Given** Sunner đã đăng nhập đang ở `/kudos/new`, **When** gõ "Nguyễn" vào ô Người nhận, **Then** danh sách gợi ý chỉ hiện các tên chứa "Nguyễn" và chọn một tên điền đúng vào trường.
- **Given** ô soạn nội dung đang trống, **When** gõ "Cảm ơn @" rồi tiếp tục gõ tên, **Then** danh sách gợi ý đồng nghiệp hiện ra và chọn một người chèn đúng tên đó vào nội dung.

**US002_AttachHashtagsAndImages**
- **Given** Kudos đang soạn chưa có hashtag nào, **When** thêm lần lượt 5 hashtag hợp lệ, **Then** cả 5 hiện thành chip riêng và có thể tiếp tục thao tác bình thường.
- **Given** đã có đủ 5 hashtag, **When** cố thêm hashtag thứ 6, **Then** thông báo "Tối đa 5 hashtag" hiện ra và hashtag thứ 6 không được thêm.

**US003_SendOrCancelKudos**
- **Given** Người nhận, Danh hiệu, nội dung và ít nhất 1 hashtag đã điền đủ, **When** bấm Gửi, **Then** form hiện trạng thái đang xử lý rồi trình duyệt về `/kudos`, và Kudos mới hiển thị trên bảng tin.
- **Given** mọi trường bắt buộc đang trống, **When** bấm Gửi, **Then** lỗi "Không được để trống" hiện đồng thời tại Người nhận, Danh hiệu, nội dung và Hashtag, form không được gửi.

## 9. Edge Cases

| Scenario | What Happens | User-Facing Message |
|----------|--------------|----------------------|
| Cố thêm hashtag thứ 6 khi đã có 5 | Hashtag thứ 6 không được thêm, 5 hashtag cũ giữ nguyên | "Tối đa 5 hashtag" |
| Chọn file sai định dạng (.pdf/.mp4/.txt) cho phần đính kèm ảnh | File bị từ chối, không có ảnh nào được thêm | Thông báo lỗi định dạng file không hợp lệ |
| Bấm Gửi khi tất cả trường bắt buộc còn trống | Không có gì được gửi lên server; mọi lỗi hiện cùng lúc | "Không được để trống" tại từng trường thiếu |
| Bật checkbox ẩn danh nhưng để trống ô tên hiển thị | Kudos vẫn gửi được bình thường (trường tuỳ chọn) | Bảng tin hiện một nhãn trung lập thay cho tên người gửi |
| Sunner đã đăng nhập nhưng chưa từng viết Kudos (chưa có dòng `sunners`) bấm Gửi hai lần liên tiếp thật nhanh | Hệ thống chỉ tạo đúng một dòng `sunners` cho tài khoản đó, không tạo trùng | Không có thông báo đặc biệt — Kudos vẫn gửi thành công |
| Kudos cũ đã seed từ trước (F004) hiển thị lại trên bảng tin | Vẫn hiển thị y hệt như trước — chỉ Kudos soạn từ form này mới dùng định dạng nội dung mới | Không đổi |

## 10. Edge Behaviours to Verify

- **FR-202** Gõ khoảng trắng đầu/cuối vào ô tìm Người nhận vẫn lọc đúng danh sách (khoảng trắng bị bỏ qua trước khi so khớp).
- **FR-214 / FR-217** Mở hộp thoại khi đang bôi đen một đoạn điền sẵn đúng đoạn đó vào ô `Nội dung`; sửa lại giá trị rồi `Lưu` thay đoạn cũ bằng giá trị mới chứ không chèn thêm.
- **FR-216** Bấm `Lưu` với cả hai ô trống hiện đồng thời lỗi ở cả hai ô, không phải lần lượt từng ô sau mỗi lần bấm.
- **FR-218** Đóng hộp thoại bằng `Hủy`, `Escape` hoặc bấm ra ngoài rồi mở lại: hai ô trống, không giữ giá trị nhập dở của lần trước.
- **FR-205** Xoá một hashtag chip không ảnh hưởng tới các chip còn lại.
- **FR-206** Xoá một ảnh khi đang đủ 5 làm nút "+ Image" hiện lại ngay, không cần tải lại trang.
- **FR-401 / DEC-002** Điền đủ 4 trường bắt buộc rồi xoá lại một trường làm nút Gửi khoá lại ngay, không cần bấm Gửi để kiểm tra.
- **FR-402** Lỗi "Không được để trống" hiện đồng thời cho mọi trường thiếu, không phải lần lượt từng trường sau mỗi lần bấm Gửi.
- **FR-403** Bấm Hủy sau khi đã nhập một số dữ liệu không để lại Kudos nào trên bảng tin khi quay lại `/kudos`.
- **FR-601 / FR-602** Gọi thẳng hành động gửi Kudos mà bỏ qua giao diện (không qua session hợp lệ) bị database từ chối, không phụ thuộc vào việc ẩn nút trên UI.

## 11. Risks & Known Issues

N/A — none found.

## 12. Dependencies

| Dependency | Type | Why this feature needs it | Evidence |
|------------|------|-----------------------------|----------|
| F004_KudosLiveBoard | feature | Kudos mới gửi phải xuất hiện thật trên bảng tin `/kudos` để chứng minh việc ghi đã thành công; card Kudos ẩn danh cần bảng tin đổi cách hiển thị người gửi | `clarifications.md` § "Successful `Gửi`", § "Anonymous" |
| Supabase Storage (bucket ảnh đính kèm) | infrastructure | Ảnh đính kèm là file thật của người dùng, không phải ảnh mẫu — cần một bucket Storage thật đang bật | `supabase/config.toml` (`[storage] enabled = true`, bucket hiện đang bị comment) |
| Phiên đăng nhập Google OAuth (đã có, F001) | external-service | Nguồn thông tin (tên, ảnh) để tự động cấp một dòng `sunners` cho Sunner viết Kudos lần đầu | `clarifications.md` § "Sender identity" |

## 13. Configuration

N/A — no user-facing configuration constants for this feature.
