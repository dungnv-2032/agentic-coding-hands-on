---
status: draft
authored_by: takumi
created: 2026-09-08
lang: vi
---

**Priority**: P1
**Type**: mixed

## 1. Overview

**Problem:** `/profile` hiện là một `ComingSoon` công khai (`app/profile/page.tsx`) — mọi liên kết tên Sunner trên bảng tin (`sunner-chip.tsx`, `gift-leaderboard.tsx`) và menu tài khoản (`account-menu.tsx`) đều trỏ tới đây mà không có gì để xem. Đây cũng là màn hình đầu tiên phải tự phân biệt "hồ sơ của tôi" và "hồ sơ người khác" trên cùng một route, và là màn hình đầu tiên phát hiện một lỗ hổng bảo mật đang mở trên dữ liệu đã ship (F004): `sender_id` của một Kudos ẩn danh đọc được thẳng qua anon key.
**Solution:** Trang `/profile` (và `/profile?id={sunnerId}`) — công khai về mặt route nhưng đòi hỏi đăng nhập — dựng hero (keyvisual, avatar, tên, phòng ban, huy hiệu Hero, 6 ô icon khoá), rồi một trong hai mặt tuỳ theo `?id`: card thống kê cá nhân (5 chỉ số + Secret Box) trên hồ sơ của chính mình, hoặc thanh viết Kudo dẫn tới `/kudos/new?receiverId={id}` trên hồ sơ người khác. Bên dưới là mục KUDOS: dropdown chọn chiều (Đã nhận/Đã gửi), feed thẻ Kudos tái dùng nguyên component bảng tin, phân trang cuộn vô hạn bằng keyset cursor.
**Scope:** Route `/profile` + `?id=` resolution; hero + huy hiệu; card thống kê / thanh viết Kudo; mục KUDOS (dropdown, feed, tương tác thẻ); migration đóng lỗ lộ `sender_id` ẩn danh (view `security definer` + revoke); `sunner-chip`/`gift-leaderboard` đổi sang phát `?id=`; bổ sung `profile` block vào `Dictionary`.
**Non-Scope:** Kết quả tìm kiếm của ô `sunner-search` trên `kudos-hero.tsx` (`/profile?q=...` chỉ được đảm bảo không vỡ, không xây màn kết quả — A5); sửa/xoá Kudos; ràng buộc `kudos_no_self` (ADV-2); reconcile hai chiến lược phân trang (ADV-1); Secret Box thật (button vẫn `disabled`).

**Actors**

| Actor | Description | Primary goal |
|-------|--------------|---------------|
| Sunner (đã đăng nhập) | Nhân viên Sun* đã đăng nhập, actor duy nhất của màn hình này | Xem hồ sơ của mình hoặc của đồng nghiệp, duyệt Kudos đã nhận/đã gửi, gửi Kudo mới cho người đang xem |

## 2. Functional Capabilities

| ID | Capability | What the user can do | User Stories | Requirements | Business Rules | Screens |
|----|------------|------------------------|-----------------|---------------|-------------------|---------|
| CAP-01 | Xem hero và huy hiệu | Truy cập `/profile` (của mình) hoặc `/profile?id=` (của người khác), xem avatar/tên/phòng ban/huy hiệu Hero và 6 ô icon khoá | US001 | FR-002, FR-003, FR-101, FR-102, FR-201, FR-202, FR-205, FR-401, FR-402 | BR-001, BR-002 | TBD (draft) |
| CAP-02 | Xem thống kê cá nhân hoặc gửi Kudo | Trên hồ sơ của mình: xem 5 chỉ số + Secret Box. Trên hồ sơ người khác: bấm thanh viết Kudo đã điền sẵn người nhận | US002 | FR-203, FR-204 | BR-003, BR-004 | TBD (draft) |
| CAP-03 | Duyệt và tương tác mục KUDOS | Chọn chiều Đã nhận/Đã gửi, cuộn xem thêm, thả tim, bấm hashtag, copy link | US003 | FR-001, FR-206, FR-207, FR-208, FR-403, FR-404, FR-405, FR-601, FR-602, FR-603 | BR-005, DEC-001, DEC-002, SM-001 | TBD (draft) |

## 3. Open Decisions

None — no unresolved domain confirmations. `/tkm:takumi --auto` đã quyết định phương án mặc định/khuyến nghị cho mọi câu hỏi mở trong `clarifications.md`, không chặn triển khai. Hai điểm cần nói rõ vì chúng RÚT LẠI quyết định đã ghi trước đó trong `clarifications.md`, theo nghiên cứu hình ảnh đo đạc (`reports/momorph-visual-study.md`, § "Amendments from the measured visual study"): hoa-thị stars **không được implement** (không có node nào trong thiết kế — AMEND-1, retire assumption A2) và 6 ô huy hiệu **không có artwork thật** để làm xám (AMEND-2). Xem `technical-spec.md § 5.2/5.3` để không lặp lại ở đây.

## 4. Requirements

### Foundation (0xx)

- **FR-001** Migration thêm một view `security definer` đọc `kudos`, null hoá `sender_id`/thông tin người gửi cho một dòng ẩn danh trừ khi caller chính là người gửi đó; `revoke select on public.kudos from anon, authenticated`; ba call site hiện có (`lib/kudos/queries.ts:53`, `app/kudos/_actions/toggle-kudos-like.ts:26,73`) trỏ lại view này.
- **FR-002** Bổ sung khối `profile` vào interface `Dictionary` (`lib/i18n/messages/dictionary.ts`) cùng `lib/i18n/messages/vi-profile.ts`/`en-profile.ts`.
- **FR-003** `sunner-chip.tsx` và `gift-leaderboard.tsx` đổi liên kết tên Sunner từ `href="/profile"` sang `href="/profile?id={sunnerId}"`; `e2e/kudos-live-board.spec.ts:354,356` được sửa từ so khớp `"/profile"` sang mẫu `/profile\?id=\d+$` (một amendment có chủ đích lên một test đã ratify, ghi nhận tại đây, không phải nới lỏng âm thầm).

### Navigation (1xx)

- **FR-101** `/profile` (path chính xác và mọi subpath) được thêm vào danh sách guarded của `proxy.ts`, cùng nhóm với `/todo`/`/kudos/new`; chưa đăng nhập bị chuyển hướng `/login`.
- **FR-102** Trang tự resolve lại session của chính nó (defense in depth) — guard vẫn đúng dù danh sách route của `proxy.ts` bị sửa sau này.

### Hero và huy hiệu (2xx)

- **FR-201** Hero dựng theo đúng thứ tự: keyvisual banner (`mm:I1210:12622;2167:5140`) → avatar tròn 200×200 viền trắng (`mm:362:5053`) → tên màu vàng `#FFEA9E` (`mm:362:5055`) → dòng chi tiết gồm phòng ban, dấu chấm phân cách, huy hiệu Hero dạng pill (`mm:362:5056-5060, 3053:6061`). Huy hiệu Hero khoá theo tổng Kudos đã nhận (`badgeTierFor`, không phải số người gửi khác nhau — xem `technical-spec.md § "Spec-author concerns"`).
- **FR-202** Ngay dưới tên, 6 ô icon huy hiệu (`mm:362:5064` chứa `mm:362:5066`–`362:5071`) hiện dưới dạng vòng tròn xám phẳng `#323231`, 64×64, viền trắng 2px, khoảng cách 16px, đúng thứ tự trái→phải B2→B7 — không có artwork nào để làm xám (AMEND-2), không ô nào ẩn, không ô nào mở khoá.
- **FR-205** Tiêu đề dòng huy hiệu (nếu có, theo `technical-spec.md § 3` — key riêng, không phải một element mm) đọc ngôi thứ nhất trên hồ sơ của chính mình, trung tính trên hồ sơ người khác, qua hai key i18n riêng biệt.

### Thống kê / Viết Kudo (3xx)

- **FR-203** Trên hồ sơ của chính mình: card thống kê (`mm:362:5073`) hiện 5 hàng (Kudos nhận, Kudos gửi, tim nhận, Secret Box đã mở, Secret Box chưa mở) rồi nút "Mở Secret Box" (`mm:362:5082`) luôn `disabled`. *Từ 2026-09-10, F009_OpenSecretBox mở khoá nút này thành một liên kết thật sang `/kudos/secret-box` — vẫn chỉ trên hồ sơ của chính mình; xem `docs/features/F009_OpenSecretBox/functional-spec.md`.*
- **FR-204** Trên hồ sơ người khác: TOÀN BỘ card thống kê được thay bằng một thanh viết Kudo nêu tên người đang xem (`Gửi lời cảm ơn và ghi nhận đến {name}`), dẫn tới `/kudos/new?receiverId={id}` (đã điền sẵn người nhận, trường vẫn sửa được, không tự mở danh sách gợi ý). Không hàng chỉ số, không nút Secret Box nào xuất hiện trên mặt này.

### Mục KUDOS (4xx)

- **FR-206** Dropdown chiều (`mm:362:5089`): hồ sơ của chính mình hiện cả `Đã nhận (N)` và `Đã gửi (M)`, mặc định **Đã nhận** đang active (không phải `Đã gửi (5)` — đó là trạng thái mock của frame, xem `technical-spec.md § 5.2 A6`); hồ sơ người khác chỉ hiện `Đã nhận (N)`, không có tuỳ chọn/label/số đếm `Đã gửi` ở bất kỳ đâu trên trang.
- **FR-207** Mỗi thẻ trong feed tái dùng nguyên `KudosCard`/mapper của bảng tin (`app/kudos/_components/kudos-card.tsx`) — cùng cột dữ liệu, cùng cách che tên người gửi ẩn danh, cùng nút tim/Copy Link; chip "Spam" (`mm:I3127:24169/24455;3127:24095`) không bao giờ render (không có mô hình kiểm duyệt nào trong schema hay trong CSV thiết kế).
- **FR-208** Mỗi chiều có copy rỗng riêng: Đã nhận dùng nguyên văn của bảng tin ("Hiện tại chưa có Kudos nào."), Đã gửi dùng copy riêng ("Bạn chưa gửi Kudos nào.").

### Interaction (4xx)

- **FR-401** `?id=` được kiểm shape `/^\d{1,18}$/` trước khi chạm database; không khớp → `notFound()` ngay, không truy vấn.
- **FR-402** `?id=` rỗng hoặc vắng mặt → hồ sơ của chính mình. `?id=` khớp chính viewer → canonicalize về mặt tự-xem (không redirect, render y hệt `/profile`). `?id=` hợp lệ nhưng không khớp dòng `sunners` nào → `notFound()`. `?id=` lặp lại với hai giá trị khác nhau → `notFound()`. Tham số khác không nhận diện được (ví dụ `?q=`) → bị bỏ qua, vẫn render mặt tự-xem — không phá hỏng ô tìm kiếm Sunner đã ship (`kudos-hero.tsx:77`, `action="/profile" name="q"`).
- **FR-403** Đổi chiều dropdown nạp trang 1 của danh sách mới và bỏ toàn bộ trang đã tích luỹ của danh sách cũ; nhãn trigger chỉ đổi sau khi trang mới đã tải xong. Chọn lại đúng chiều đang active là no-op — không request, không xoá trắng danh sách.
- **FR-404** Feed cuộn vô hạn, 10 thẻ một lần (`FEED_PAGE_SIZE`, tái dùng từ `lib/kudos/derive.ts`), phân trang bằng keyset cursor để không thẻ nào trùng hoặc bị bỏ sót; hết trang cuối hiện thông báo kết thúc feed.
- **FR-405** Thả tim tái dùng nguyên `toggleKudosLike` — số tim hiển thị luôn là số server trả về, không cộng dồn phía client; tự thả tim Kudo của chính mình bị từ chối với đúng thông báo của bảng tin. Bấm hashtag điều hướng sang `/kudos` đã lọc theo tag đó. Copy Link tái dùng toast của bảng tin.

### Security (6xx)

- **FR-601** Danh sách Đã gửi chỉ đọc được Kudos mà `sender_id` khớp `sunners` của chính session đang gọi — biên bảo mật nằm ở mệnh đề `WHERE`/RLS của truy vấn, không phải ở việc ẩn nút trên giao diện; không có request nào trả về danh sách Đã gửi của người khác (kể cả khi biết `?id=` của họ).
- **FR-602** Danh sách Đã gửi của chính mình bao gồm cả Kudos đã gửi ẩn danh, hiển thị chính mình là tác giả (không dùng alias che tên như trên bảng tin công khai), vẫn giữ đánh dấu nội bộ là đã gửi ẩn danh.
- **FR-603** Không có affordance sửa trên tên/avatar/phòng ban ở bất kỳ mặt nào của route; payload trang không bao giờ chứa địa chỉ email hay auth uuid — chỉ các cột hồ sơ được phép mới được select.

## 5. Business Rules

- Một session đã đăng nhập nhưng chưa có dòng `sunners` (chưa từng viết Kudos) render hồ sơ tự-xem "rỗng": tên/avatar suy từ JWT theo đúng chuỗi fallback `create_kudos()` đã dùng (`full_name`→`name`→email local-part; `avatar_url`→`picture`→ảnh mẫu), 0 cho mọi chỉ số, feed rỗng, 6 ô huy hiệu xám, không huy hiệu Hero. Không 404, không tạo dòng `sunners` mới (`GET` không được phép ghi). (BR-001)
- Huy hiệu Hero dùng nguyên `badgeTierFor()` đã ship (`lib/kudos/derive.ts`), khoá theo TỔNG Kudos đã nhận ở ngưỡng 10/20/50 — không phải số người gửi khác nhau như một ghi chú trong CSV thiết kế đề xuất; một hàm, một luật, để bảng tin và hồ sơ không bao giờ hiện hai huy hiệu khác nhau cho cùng một người. (BR-002)
- Năm chỉ số suy ra bằng đúng idiom F004 đã ship: nhận = `sunners.kudos_received_baseline + count(kudos nhận được)`; gửi = `count(kudos đã gửi)` (không có cột baseline cho gửi); tim nhận = `sum(heart_baseline + count(kudos_likes))` trên các Kudos đã nhận. (BR-003)
- Hai hàng Secret Box đọc thẳng `secret_box_opened_count`/`secret_box_unopened_count` (không hardcode 0) — một session rỗng đọc đúng 0/0 mà không cần số hardcode nào; nút "Mở Secret Box" luôn `disabled`, bấm vào không làm gì (không dialog, không điều hướng, không lỗi). (BR-004) *Từ 2026-09-10 (F009), nút này là một liên kết thật trên hồ sơ của chính mình — hành vi `disabled` mô tả ở đây chỉ còn đúng cho phạm vi F006 tại thời điểm ship.*
- Thẻ Kudos trong feed hồ sơ hiển thị y hệt thẻ trên bảng tin — cùng che tên người gửi ẩn danh trên danh sách Đã nhận, cùng hành vi tim/hashtag/Copy Link — vì dùng chung một mapper. (BR-005)
- Dropdown chiều mặc định active **Đã nhận**, không phải trạng thái `Đã gửi (5)` mà frame chụp lại — frame chỉ ghi một khoảnh khắc, test case mới là nguồn hành vi mặc định. (DEC-001)
- Chọn lại đúng option đang active trong dropdown chiều đóng menu và giữ nguyên danh sách hiện tại — không có trạng thái "chưa lọc" nào để rơi về. (DEC-002)
- Mục KUDOS trên hồ sơ có bốn trạng thái tải — vừa render (`idle`), vừa đổi chiều (`switching`), đang tải thêm khi cuộn (`loading-more`), đã hết trang (`settled`) — chuyển tiếp qua đúng bốn hành động: render lần đầu, đổi chiều, cuộn, và trang cuối cùng trả về. (SM-001)

## 6. Screens

| Screen Name | SCR### | What User Sees | What User Can Do |
|-------------|--------|-----------------|-------------------|
| {Profile bản thân} | {SCR###_NameSlug — allocated at promote} | Hero (keyvisual, avatar, tên, phòng ban, huy hiệu, 6 ô icon khoá), card thống kê hoặc thanh viết Kudo, mục KUDOS (dropdown + feed) | Xem hồ sơ của mình/người khác qua `?id=`, đổi chiều Đã nhận/Đã gửi, cuộn xem thêm Kudos, thả tim, bấm hashtag, copy link, bấm thanh viết Kudo (nếu đang xem người khác) |

### User Journey

**Mặt tự-xem** (`/profile`, hoặc `?id=` rỗng/khớp chính mình):
1. Sunner đã đăng nhập bấm "Profile" ở menu tài khoản, hoặc gõ `/profile`.
2. Nếu chưa đăng nhập, `proxy.ts` chuyển hướng `/login` trước khi trang render.
3. Trang render hero của chính Sunner, card thống kê 5 chỉ số + Secret Box (disabled), và mục KUDOS với dropdown mặc định "Đã nhận" active.
4. Sunner có thể đổi sang "Đã gửi" để xem Kudos mình đã gửi, kể cả những cái đã gửi ẩn danh (hiển thị chính mình là tác giả).
5. Sunner cuộn xuống để tải thêm thẻ, thả tim, bấm hashtag hoặc Copy Link như trên bảng tin.

**Mặt xem người khác** (`/profile?id={sunnerId}` với `id` hợp lệ và khác viewer):
1. Sunner bấm tên một Sunner khác trên bảng tin (`sunner-chip`, `gift-leaderboard`) — liên kết giờ mang `?id={id}`.
2. Trang render hero của Sunner đó, thay card thống kê bằng một thanh viết Kudo nêu tên họ.
3. Mục KUDOS chỉ hiện "Đã nhận" — không có tuỳ chọn/label/số đếm "Đã gửi" ở bất kỳ đâu.
4. Bấm thanh viết Kudo đưa Sunner sang `/kudos/new?receiverId={id}` với người nhận đã điền sẵn, vẫn sửa được.
5. `?id=` không hợp lệ (sai định dạng, không tồn tại, hoặc lặp lại hai giá trị) trả về trang 404 ngay, không render một phần hồ sơ nào.

## 7. User Stories

### US001_ViewProfileHero — Xem hero và huy hiệu

**Actor:** Sunner (đã đăng nhập)
**Goal:** Xem thông tin nhận diện (avatar, tên, phòng ban, huy hiệu Hero) của chính mình hoặc của một đồng nghiệp qua `?id=`, biết chắc mình đang xem đúng ai.
**Business value:** Một điểm nhận diện chung cho mọi Sunner trên hệ thống — bảng tin, sidebar quà tặng và menu tài khoản đều dẫn về đúng một hồ sơ, không lạc sang trang trống.

**Acceptance Criteria:**
- [ ] Vào `/profile` khi đã đăng nhập hiện đúng hero của chính mình; chưa đăng nhập bị chuyển `/login`.
- [ ] Vào `/profile?id={other}` hợp lệ hiện đúng hero của Sunner đó; `?id=` khớp chính mình canonical hoá về mặt tự-xem.
- [ ] `?id=` sai định dạng, không tồn tại, hoặc lặp lại hai giá trị trả về 404, không render nội dung hồ sơ nào.
- [ ] Một session chưa có dòng `sunners` vẫn render hero rỗng hợp lệ (tên/avatar từ JWT), không 404.

### US002_ViewStatsOrSendKudos — Xem thống kê cá nhân hoặc gửi Kudo

**Actor:** Sunner (đã đăng nhập)
**Goal:** Trên hồ sơ của mình, biết chính xác 5 chỉ số Kudos/tim/Secret Box của mình; trên hồ sơ người khác, bấm thẳng vào một lời cảm ơn đã điền sẵn người nhận.
**Business value:** Một Sunner tự soi lại đóng góp của mình, và việc gửi lời cảm ơn cho một đồng nghiệp cụ thể chỉ mất một cú bấm thay vì tự gõ tên trong ô tìm kiếm.

**Acceptance Criteria:**
- [ ] Hồ sơ của mình hiện đúng 5 chỉ số thật (không hardcode) và nút "Mở Secret Box" luôn `disabled`, bấm vào không làm gì. *(Từ 2026-09-10, F009 mở khoá nút này — xem ghi chú tại FR-203.)*
- [ ] Hồ sơ người khác không hiện chỉ số hay nút Secret Box nào — thay bằng thanh viết Kudo nêu đúng tên họ.
- [ ] Bấm thanh viết Kudo đưa sang `/kudos/new?receiverId={id}` với người nhận đã điền sẵn và vẫn sửa được.

### US003_BrowseAndInteractKudosFeed — Duyệt và tương tác mục KUDOS

**Actor:** Sunner (đã đăng nhập)
**Goal:** Đổi qua lại giữa Kudos đã nhận và đã gửi (khi xem hồ sơ của mình), cuộn xem hết feed, và tương tác với từng thẻ y hệt trên bảng tin.
**Business value:** Không phải học lại một bộ tương tác mới — thẻ, tim, hashtag, Copy Link hoạt động giống bảng tin, và không ai xem được số Kudos đã gửi ẩn danh của người khác.

**Acceptance Criteria:**
- [ ] Hồ sơ của mình hiện dropdown 2 chiều, mặc định "Đã nhận" active; hồ sơ người khác chỉ hiện "Đã nhận", không có "Đã gửi" ở bất kỳ đâu trên trang.
- [ ] Đổi chiều nạp trang 1 của danh sách mới, bỏ các trang đã cuộn của danh sách cũ; chọn lại chiều đang active không làm gì.
- [ ] Cuộn xuống tải thêm 10 thẻ mỗi lần, không thẻ nào trùng/bị bỏ sót, hết feed hiện thông báo kết thúc.
- [ ] Danh sách Đã gửi của chính mình gồm cả Kudos gửi ẩn danh, hiển thị mình là tác giả; không có cách nào xem Đã gửi của người khác.
- [ ] Thả tim, bấm hashtag, Copy Link hoạt động y hệt bảng tin; tự thả tim Kudo của mình bị từ chối.

## 8. Scenarios

**US001_ViewProfileHero**
- **Given** Sunner A đã đăng nhập, **When** vào `/profile?id={Sunner B}`, **Then** hero hiện đúng avatar/tên/phòng ban/huy hiệu của Sunner B, không phải của Sunner A.
- **Given** Sunner A gõ `/profile?id=banana`, **When** trang render, **Then** trang 404 hiện ra, không có truy vấn database nào chạy với giá trị đó.

**US002_ViewStatsOrSendKudos**
- **Given** Sunner A đang ở `/profile` của chính mình, **When** trang render, **Then** card thống kê hiện 5 chỉ số thật của A, không có thanh viết Kudo nào.
- **Given** Sunner A đang ở `/profile?id={Sunner B}`, **When** bấm thanh viết Kudo, **Then** `/kudos/new?receiverId={B}` mở ra với B đã là người nhận.

**US003_BrowseAndInteractKudosFeed**
- **Given** Sunner A đang ở hồ sơ của chính mình với dropdown "Đã nhận" active, **When** đổi sang "Đã gửi", **Then** feed nạp lại trang 1 Kudos đã gửi của A, kể cả các Kudos gửi ẩn danh (hiện A là tác giả).
- **Given** Sunner A đang xem hồ sơ Sunner B, **When** tìm chữ "Đã gửi" trên toàn trang, **Then** không tìm thấy label, tuỳ chọn hay số đếm nào.

## 9. Edge Cases

| Scenario | What Happens | User-Facing Message |
|----------|--------------|----------------------|
| `?id=` lặp lại hai giá trị khác nhau (`?id=1&id=2`) | Không chọn giá trị nào, trả về 404 | Trang 404 |
| `?id=` chứa chuỗi không phải số (`banana`, `' or 1=1`, `42.5`) | Bị từ chối trước khi chạm database, trả về 404 | Trang 404 |
| Session đã đăng nhập nhưng chưa có dòng `sunners` | Hero rỗng render với tên/avatar từ JWT, 0 mọi chỉ số, feed rỗng, 6 ô huy hiệu xám | Không có thông báo lỗi — trang render bình thường |
| `?q=` (ô tìm kiếm Sunner trên bảng tin) gắn kèm | Bị bỏ qua như một tham số lạ, vẫn render mặt tự-xem | Không đổi |
| Đổi chiều dropdown khi đang cuộn giữa chừng một trang dài | Toàn bộ trang đã tải của chiều cũ bị bỏ, nạp lại trang 1 của chiều mới | Không có thông báo — feed thay thế ngay |
| Chọn lại đúng chiều đang active trong dropdown | Không có gì thay đổi, không có request nào được gửi | Không có thông báo |
| Bấm thả tim vào Kudo do chính mình gửi (thấy trong danh sách Đã gửi) | Bị từ chối, số tim không đổi | Đúng thông báo bảng tin đã dùng cho trường hợp này |
| Hai Sunner khác nhau cùng mở dropdown "Đã gửi" trên hồ sơ chính mình trong hai phiên riêng | Mỗi người chỉ thấy đúng Kudos đã gửi của chính mình | Không có thông báo — hai danh sách tách biệt |

## 10. Edge Behaviours to Verify

- **FR-401** Gõ `?id=` với một chuỗi bất kỳ không khớp `/^\d{1,18}$/` không bao giờ tạo ra một truy vấn database mang giá trị đó.
- **FR-402** Gõ `?id=` khớp chính id của viewer render y hệt `/profile` không query string — không có redirect nào trong thanh địa chỉ.
- **FR-403** Đổi chiều dropdown rồi đổi lại chiều cũ hai lần liên tiếp không để lại thẻ trùng nào trong feed.
- **FR-404** Cuộn hết một feed dài hơn 10 thẻ không bao giờ hiện lại một thẻ đã hiện ở trang trước.
- **FR-601** Không có URL hay tham số nào, kể cả khi biết `?id=` của người khác, trả về danh sách "Đã gửi" của họ.
- **FR-602** Danh sách "Đã gửi" của chính mình, đếm số thẻ, phải khớp đúng số `(N)` hiện trên trigger dropdown — kể cả khi trong đó có Kudos gửi ẩn danh.
- **FR-603** Kiểm payload/network response của trang không chứa chuỗi email hay auth uuid ở bất kỳ trường nào.

## 11. Risks & Known Issues

| Risk | Type | Note |
|------|------|------|
| Hai chiến lược phân trang cùng tồn tại (F004: đọc hết bảng rồi cắt phía client; F006: keyset cursor thật) | risk | Đáng cân nhắc hợp nhất khi bảng `kudos` vượt quá vài trăm dòng — ADV-1, không chặn commission này |
| Không có ràng buộc `kudos_no_self` ở tầng database | risk | Việc từ chối tự-gửi Kudo hiện chỉ nằm ở chỗ giao diện không mời gọi thao tác đó (không có thanh viết Kudo trên hồ sơ của chính mình) — ADV-2, thuộc phạm vi schema của F005, không phải của màn hình này |

## 12. Dependencies

| Dependency | Type | Why this feature needs it | Evidence |
|------------|------|-----------------------------|----------|
| F004_KudosLiveBoard | feature | Tái dùng nguyên `KudosCard`, `badgeTierFor`/`derive.ts`, `toggleKudosLike`, và bộ lọc hashtag của bảng tin — feed và tim trên hồ sơ phải không bao giờ khác bảng tin | `clarifications.md` § "Card shape trong feed", § "Card interactions" |
| F005_VietKudo | feature | Thanh viết Kudo dẫn tới `/kudos/new?receiverId=`, đã ship như một trang (không phải modal) | `clarifications.md` § "Write-Kudo bar" |
| Supabase local (RLS + view mới) | infrastructure | View `security definer` đóng lỗ lộ `sender_id` ẩn danh là điều kiện để SEC_001/SEC_002 là phát biểu đúng, không phải chỉ đúng trên giao diện | `clarifications.md` § "Security — the finding that changes the design" |

## 13. Configuration

N/A — no user-facing configuration constants for this feature.

## Traceability — MoMorph Test Cases

Tất cả 30 test case của `design/test-cases.csv`. "Not honoured" ghi rõ lý do; mọi dòng khác được thoả bởi FR/BR/DEC ghi kèm, kể cả khi cơ chế trong ghi chú CSV được dịch sang cơ chế thật của repo này (xem `clarifications.md` § "Ba tiền đề..." và § "Amendments").

| TC ID | FR/BR/DEC | Status | Note |
|-------|-----------|--------|------|
| TC_WEB_PROFILE_ACC_001 | FR-101, FR-102 | Honoured (mechanism translated) | `PUBLIC_ROUTES` không tồn tại — `/profile` được thêm vào allowlist guarded thay vì đảo danh sách |
| TC_WEB_PROFILE_ACC_002 | FR-101, FR-402 | Honoured | — |
| TC_WEB_PROFILE_FUN_001 | FR-003, FR-402 | Honoured (mechanism translated) | `use-board-interactions.ts -> openProfile` không tồn tại — `sunner-chip`/`gift-leaderboard` phát `?id=` trực tiếp |
| TC_WEB_PROFILE_FUN_002 | FR-402 | Honoured | — |
| TC_WEB_PROFILE_FUN_003 | FR-401, FR-402 | Honoured (mechanism translated) | id là `sunners.id bigint`, không phải uuid — shape-check thay Postgres `22P02` |
| TC_WEB_PROFILE_FUN_004 | FR-401 | Honoured (mechanism translated) | cùng lý do FUN_003 |
| TC_WEB_PROFILE_FUN_005 | FR-402 | Honoured | Bao gồm cả nhánh không nằm trong test case: `?q=` bị bỏ qua, không 404 |
| TC_WEB_PROFILE_GUI_001 | FR-201, BR-002 | **Not honoured (partial)** | Huy hiệu Hero honoured; hoa-thị stars **không implement** — không có node nào trong thiết kế (AMEND-1, retire A2/D11) |
| TC_WEB_PROFILE_GUI_002 | FR-202 | **Not honoured (partial)** | 6 ô/thứ tự cố định/khoá honoured; "real badge image desaturated" **không** — không có artwork nào trong thiết kế (AMEND-2) |
| TC_WEB_PROFILE_GUI_003 | FR-205, FR-002 | Honoured (mechanism translated) | `locales/{vi,en}/profile.json` không tồn tại — dùng `Dictionary` interface |
| TC_WEB_PROFILE_GUI_004 | FR-203, BR-003 | Honoured | — |
| TC_WEB_PROFILE_GUI_005 | FR-203, BR-004 | Honoured | — |
| TC_WEB_PROFILE_FUN_006 | FR-204 | Honoured | — |
| TC_WEB_PROFILE_FUN_007 | FR-204 | Honoured (mechanism translated) | "modal" → trang `/kudos/new?receiverId=` (F005 đã ship dạng trang) |
| TC_WEB_PROFILE_FUN_008 | FR-204 | Honoured (partial) | Yêu cầu (không thanh viết Kudo trên hồ sơ mình) honoured; ghi chú "database từ chối qua `kudos_no_self`" **không** — không có ràng buộc đó (ADV-2) |
| TC_WEB_PROFILE_FUN_009 | FR-206, DEC-001 | Honoured | — |
| TC_WEB_PROFILE_SEC_001 | FR-206, FR-601 | Honoured | Case quan trọng nhất màn hình — đóng bằng FR-001 (view + revoke), không chỉ ẩn UI |
| TC_WEB_PROFILE_SEC_002 | FR-602 | Honoured | — |
| TC_WEB_PROFILE_SEC_003 | FR-601 | Honoured | — |
| TC_WEB_PROFILE_GUI_006 | FR-207 | Honoured | Full reuse — không phải "giống", mà là cùng một component (AMEND-3) |
| TC_WEB_PROFILE_FUN_010 | FR-403 | Honoured | — |
| TC_WEB_PROFILE_FUN_011 | FR-403, DEC-002 | Honoured | — |
| TC_WEB_PROFILE_FUN_012 | FR-208 | Honoured | — |
| TC_WEB_PROFILE_FUN_013 | FR-404 | Honoured | — |
| TC_WEB_PROFILE_FUN_014 | FR-405 | Honoured | — |
| TC_WEB_PROFILE_FUN_015 | FR-405 | Honoured | — |
| TC_WEB_PROFILE_GUI_007 | FR-207 | Honoured | — |
| TC_WEB_PROFILE_GUI_008 | FR-002 | Honoured (mechanism translated) | Parity ép bằng compile-time (`npm run typecheck`), mạnh hơn parity test được yêu cầu |
| TC_WEB_PROFILE_GUI_009 | BR-001 | Honoured | — |
| TC_WEB_PROFILE_SEC_004 | FR-603 | Honoured | — |
