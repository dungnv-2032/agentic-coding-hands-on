---
status: implemented
authored_by: takumi
created: 2026-09-08
---

# SCR-ProfileBanThan — Screen Spec

**Screen**: SCR-ProfileBanThan: Profile bản thân
**Feature**: F006_ProfileBanThan
**Type**: composite
**Route**: `/profile` (và `/profile?id={sunnerId}`)
**Generated**: 2026-09-08

## 1. Overview

**Purpose:** Sunner đã đăng nhập xem hồ sơ nhận diện (avatar, tên, phòng ban, huy hiệu Hero) của chính mình hoặc của một đồng nghiệp, xem thống kê cá nhân hoặc bấm thẳng vào một lời cảm ơn dành cho người đang xem, và duyệt Kudos đã nhận/đã gửi.
**Actors:** Sunner (đã đăng nhập)
**Entry Conditions:** Phiên đăng nhập hợp lệ. Chưa đăng nhập → chuyển hướng `/login` trước khi màn hình này render (route guard, không phải trạng thái của chính màn hình). `?id=` hợp lệ nhưng không khớp ai, sai định dạng, hoặc lặp lại → trang 404 (không phải trạng thái của màn hình này).
**Exit Conditions:** Bấm hashtag rời sang `/kudos` đã lọc; bấm thanh viết Kudo rời sang `/kudos/new?receiverId=`; mọi điều hướng khác (menu, header) là điều hướng chung, không riêng màn hình.

## 2. Screen Layout

### Layout Sketch

Trang một cột, căn giữa 680px (`mm:362:5073`/`362:5091`), nền `#00101A` toàn trang. Từ trên xuống: banner keyvisual phủ 512px đầu trang (`mm:I1210:12622;2167:5140`), khối hero căn giữa full-width (`mm:362:5052`) chứa avatar/tên/huy hiệu/6 ô icon, rồi một trong hai khối B (thống kê HOẶC thanh viết Kudo), rồi header mục KUDOS (`mm:362:5084`) và feed thẻ Kudos một cột.

```
┌───────────────────────────────────────────┐
│  Keyvisual banner (static, phủ 512px đầu)  │
├───────────────────────────────────────────┤
│  A: Avatar + Tên + Phòng ban + Huy hiệu    │
│     A.3: 6 ô icon huy hiệu (con của A)     │
├───────────────────────────────────────────┤
│  B: Card thống kê (self)                   │
│     — HOẶC —                               │
│  B: Thanh viết Kudo (other)                │
├───────────────────────────────────────────┤
│  C: Header "KUDOS" + dropdown chiều        │
├───────────────────────────────────────────┤
│  D: Feed thẻ Kudos (cuộn vô hạn)           │
└───────────────────────────────────────────┘
```

### Layout Regions

| Region ID | Name | mm id | Position | Scrollable | States |
|-----------|------|-------|----------|------------|--------|
| Keyvisual | Banner nền hero | `I1210:12622;2167:5140` | static, phủ 512px đầu trang | no | self, other (giống nhau) |
| A | Khối hero — nhận diện | `362:5052` | static | no | self, other, sparse |
| A.3 | Hàng 6 ô icon huy hiệu (con của A) | `362:5064` | static | no | locked (luôn luôn, mọi mặt) |
| B | Card thống kê / Thanh viết Kudo | `362:5073` (vị trí dùng chung cho cả hai) | static | no | self (card) / other (thanh viết Kudo) |
| C | Header mục KUDOS | `362:5084` | static | no | self (2 chiều), other (1 chiều) |
| D | Feed thẻ Kudos | `362:5091` | dọc, cuộn vô hạn | yes | empty (received), empty (sent), loading, end-of-feed |

## 3. UI Elements

| ID | Region | mm id | Element | Required | Default | States | Action | Copy key |
|----|--------|-------|---------|----------|---------|--------|--------|----------|
| A.1 | A | `362:5053` | Avatar tròn 200×200, viền trắng 4px | — | placeholder tròn nếu `avatarUrl` rỗng | self, other, sparse (placeholder) | — | — |
| A.2.name | A.2 | `362:5055` | Tên, vàng `#FFEA9E`, 36px/700 | — | — | self, other, sparse | — | — (data: `hero.fullName`) |
| A.2.dept | A.2 | `362:5057` | Phòng ban, trắng, 22px/700 | — | Ẩn hoàn toàn nếu `department` null | self, other, sparse (ẩn dòng) | — | — (data: `hero.department`) |
| A.2.dot | A.2 | `362:5060` | Dấu chấm phân cách 4×4, `#999` 40% opacity | — | Ẩn cùng lúc với A.2.dept khi không có phòng ban | self, other | — | — |
| A.2.badge | A.2 | `3053:6061` | Pill huy hiệu Hero, viền `#FFEA9E`, text 12.8px/700 | — | **Ẩn hoàn toàn** khi 0 Kudos đã nhận (khác ngưỡng "New Hero" thấp nhất — 0 Kudos không có huy hiệu nào, GUI_009) | self, other, sparse (ẩn) | — | — (data: `badgeTierFor()` label) |
| A.3 | A.3 | `362:5064` | Hàng 6 ô icon huy hiệu | — | 6 ô, tất cả xám `#323231`, không ô nào ẩn/mở khoá | self, other, sparse — **giống hệt nhau ở mọi mặt** (AMEND-2: không artwork, không state khác) | — | `badges.headingSelf` / `badges.headingOther` (tiêu đề phía trên hàng, key riêng theo mặt — không phải một node mm) |
| B2–B7 | A.3 (con) | `362:5066`–`362:5071` | 6 ô vòng tròn 64×64, viền trắng 2px, nền `#323231` phẳng | — | Luôn xám, luôn khoá | locked (mọi mặt) | — | — |
| B.self | B | `362:5074` | Card thống kê (chỉ mặt self) | — | Ẩn hoàn toàn trên mặt other | self / **ẩn trên other** | — | `stats.kudosReceived`, `stats.kudosSent`, `stats.heartsReceived`, `stats.secretBoxOpened`, `stats.secretBoxUnopened` |
| B.1 | B | `362:5076` | Hàng "Số Kudos bạn nhận được" | — | — | self | — | `stats.kudosReceived` |
| B.2 | B | `362:5077` | Hàng "Số Kudos bạn đã gửi" | — | — | self | — | `stats.kudosSent` |
| B.3 | B | `362:5078` | Hàng "Số tim bạn nhận được" | — | — | self | — | `stats.heartsReceived` |
| B.4 | B | `362:5080` | Hàng "Số Secret Box bạn đã mở" | — | Đọc cột thật, `0` cho hồ sơ rỗng | self, sparse (0) | — | `stats.secretBoxOpened` |
| B.5 | B | `362:5081` | Hàng "Số Secret Box chưa mở" | — | Đọc cột thật, `0` cho hồ sơ rỗng | self, sparse (0) | — | `stats.secretBoxUnopened` |
| B.6 | B | `362:5082` | Nút "Mở Secret Box" | — | **Luôn `disabled`** | self | Bấm không làm gì (không dialog, không điều hướng) | `stats.secretBoxButton` |
| B.other | B (cùng vị trí) | *(không có node riêng — dùng slot `362:5073`, mô hình theo thanh viết Kudo của bảng tin)* | Thanh viết Kudo, nêu tên người đang xem | — | Ẩn hoàn toàn trên mặt self | other / **ẩn trên self** | Bấm → `/kudos/new?receiverId={id}` | `writeBar.label` (interpolate tên) |
| C.1 | C | `362:5085` | Tiêu đề "Sun* Annual Awards 2025" | — | — | self, other (giống nhau) | — | Tái dùng key `kudos.eyebrow` đã có — không phải copy mới của màn này |
| C.2 | C | `362:5088` | Tiêu đề "KUDOS", vàng, 57px/700 | — | — | self, other | — | Tĩnh, không cần key riêng (đúng chữ "KUDOS") |
| C.3 | C | `362:5089` | Trigger dropdown chiều | — | **"Đã nhận (N)" active** (DEC-001 — KHÔNG phải "Đã gửi (5)" của frame) | self (2 option), other (1 option, không "Đã gửi") | Bấm mở/đóng danh sách 1–2 option | `direction.receivedLabel`, `direction.sentLabel` (interpolate N/M) |
| C.3.1 | C (con, không mm riêng) | — | Danh sách option dropdown | — | Ẩn | self (2 dòng), other (1 dòng) | Chọn 1 option — tái dùng panel style của `kudos-filter-menu.tsx` | như trên |
| D | D | `362:5091` | Cột feed thẻ Kudos | — | — | empty, loading, end-of-feed | Cuộn để tải thêm | — |
| D.card | D (con, lặp) | *(tái dùng nguyên `KudosCard`, không phải node riêng của màn này)* | Thẻ Kudos — sender/receiver, thời gian, danh hiệu, nội dung, hashtag, tim, Copy Link | — | — | mọi mặt — y hệt bảng tin | Thả tim, bấm hashtag, Copy Link | Tái dùng `kudos.card.*` |
| D.3.1 | D.card (con) | `I3127:24169;3127:24095`, `I3127:24455;3127:24095` | Chip "Spam" | — | **KHÔNG BAO GIỜ render** (GUI_007 — không có mô hình kiểm duyệt) | — (đo được nhưng không dùng) | — | — |
| D.empty.received | D | — | Copy rỗng chiều "Đã nhận" | — | Hiện khi feed rỗng, chiều = received | empty | — | `feed.emptyReceived` — nguyên văn bảng tin |
| D.empty.sent | D | — | Copy rỗng chiều "Đã gửi" | — | Hiện khi feed rỗng, chiều = sent | empty | — | `feed.emptySent` — copy riêng, khác received |
| D.end | D | — | Thông báo hết feed | — | Hiện khi `hasMore === false` | end-of-feed | — | `feed.endOfFeed` |

**Ngoài phạm vi inventory này** (thuộc header/footer dùng chung toàn site, không phải nội dung riêng của màn hình): `mms_1_Button` (`I362:5041;186:1597`, icon header), `mms_7.4_Button-IC` (`I435:3154;1161:9487`, link footer) — cả hai đã có component dùng chung, màn này không sửa.

## 4. User Actions

> **Scope:** tương tác trong-màn-hình. Điều hướng rời màn hình xem `## 8. Navigation`.

### Available Actions

| Action | Element | Trigger | Condition | Result on this screen | Source |
|--------|---------|---------|-----------|------------------------|--------|
| Mở dropdown chiều | C.3 | click | — | C.3.1 hiện danh sách option | TBD (draft) |
| Chọn chiều khác đang active | C.3, C.3.1 | click option chưa active | self only (other chỉ có 1 option) | Xoá feed hiện tại ngay, C.3.1 đóng, D vào state `loading`, nạp trang 1 chiều mới, nhãn C.3 đổi SAU khi trang mới về | TBD (draft) |
| Chọn lại chiều đang active | C.3, C.3.1 | click option đang active | — | C.3.1 đóng, không gì khác đổi — không request | TBD (draft) |
| Cuộn tới cuối feed | D | scroll tới sentinel | `hasMore === true` | Nạp thêm 10 thẻ, nối vào cuối D | TBD (draft) |
| Cuộn tới cuối feed, hết dữ liệu | D | scroll tới sentinel | `hasMore === false` | D.end hiện, sentinel unmount | TBD (draft) |
| Thả tim một thẻ | D.card | click icon tim | không phải Kudo do chính viewer gửi | Số tim đổi theo giá trị server trả về | TBD (draft) |
| Tự thả tim Kudo của mình | D.card | click icon tim trên thẻ mình gửi (thấy ở chiều "Đã gửi") | — | Bị từ chối, số tim không đổi, thông báo y hệt bảng tin | TBD (draft) |
| Bấm hashtag | D.card | click | — | Điều hướng `/kudos?hashtag={tag}` (xem `## 8. Navigation`) | TBD (draft) |
| Copy Link | D.card | click | — | Copy link, hiện toast (y hệt bảng tin) | TBD (draft) |
| Bấm thanh viết Kudo | B.other | click | chỉ hiện khi mặt other | Điều hướng `/kudos/new?receiverId={id}` (xem `## 8. Navigation`) | TBD (draft) |
| Bấm nút "Mở Secret Box" | B.6 | click | chỉ hiện khi mặt self | Không làm gì — nút `disabled` | TBD (draft) |

### Happy Path

**Mặt self:** 1. Sunner mở `/profile` → 2. Hero + 6 ô huy hiệu render → 3. Card thống kê (B) render 5 chỉ số thật + nút Secret Box disabled → 4. Header KUDOS (C) render, dropdown "Đã nhận" active → 5. Feed (D) render trang 1 Đã nhận → 6. Sunner có thể đổi dropdown sang "Đã gửi", cuộn thêm, thả tim, bấm hashtag/Copy Link.

**Mặt other:** 1. Sunner mở `/profile?id={other}` → 2. Hero + 6 ô huy hiệu của người đó render → 3. Thanh viết Kudo (B.other) thay card thống kê → 4. Header KUDOS render, dropdown chỉ có "Đã nhận" → 5. Feed render Kudos người đó đã nhận → 6. Sunner bấm thanh viết Kudo để mở `/kudos/new?receiverId={id}` đã điền sẵn.

### Branches

| Decision point | Condition | Outcome on this screen | Source |
|----------------|-----------|------------------------|--------|
| Bước 1 (mọi mặt) | `?id=` sai định dạng/không tồn tại/lặp lại | Trang 404 — không render bất kỳ region nào ở trên | TBD (draft) |
| Bước 1 (self) | Session chưa có dòng `sunners` | Region A render với tên/avatar từ JWT, không huy hiệu Hero (A.2.badge ẩn), B render 5 hàng đều `0`, D rỗng | TBD (draft) |
| Bước 6 | Đổi dropdown giữa lúc đang cuộn | D bỏ toàn bộ trang đã tích luỹ của chiều cũ, về trạng thái `loading` rồi `idle` với trang 1 chiều mới | TBD (draft) |

## 5. UI States

| State | Trigger | Visual Behavior | User Action Available | Source |
|-------|---------|----------------|-----------------------|--------|
| self | `?id=` rỗng/vắng/khớp viewer | B là card thống kê; C có 2 option | Mọi action ở trên | TBD (draft) |
| other | `?id=` hợp lệ, khác viewer | B là thanh viết Kudo; C chỉ có "Đã nhận" | Không có "Chọn chiều Đã gửi"; không có "Bấm nút Secret Box" | TBD (draft) |
| sparse | self, session chưa có dòng `sunners` | A không huy hiệu Hero; B toàn `0`; D rỗng | Giống self, chỉ khác dữ liệu | TBD (draft) |
| locked | A.3/B2–B7, mọi mặt | 6 ô xám cố định | Không action nào — chỉ hiển thị | TBD (draft) |
| empty (received) | D rỗng, chiều = received | D.empty.received hiện | Đổi chiều, hoặc chờ Kudos mới | TBD (draft) |
| empty (sent) | D rỗng, chiều = sent | D.empty.sent hiện | Đổi chiều | TBD (draft) |
| loading | Vừa đổi chiều hoặc vừa cuộn, chờ A2 | D giữ nội dung cũ (đổi chiều: đã xoá); sentinel/skeleton — TBD (draft) chưa quyết định chi tiết hiển thị chờ | Chờ | TBD (draft) |
| end-of-feed | `hasMore === false` sau một lần tải | D.end hiện thay cho sentinel | Không còn action cuộn | TBD (draft) |

## 6. Validation & Feedback

Không có trường nhập liệu nào trên màn hình này — toàn bộ tương tác là điều hướng/đọc, trừ thả tim (đã có validation ở tầng server action `toggleKudosLike`, không lặp lại ở đây). N/A cho phần còn lại của mục này.

## 7. Conditional UI

| Condition | Type | Element(s) | Visible when | Hidden when | Notes |
|-----------|------|------------|--------------|-------------|-------|
| Card thống kê vs thanh viết Kudo | configuration | B.self, B.other | B.self: `targetId === viewer.sunnerId`. B.other: ngược lại | Đúng một trong hai luôn hiện, không bao giờ cả hai hoặc không cái nào | Một nhánh dữ liệu duy nhất quyết định (`technical-spec.md § 1`) |
| Option "Đã gửi" trong dropdown chiều | configuration | C.3.1 (dòng "Đã gửi") | `targetId === viewer.sunnerId` | mặt other | Không chỉ ẩn — hoàn toàn không có trong response server trả về, không phải CSS ẩn (chi tiết bảo mật: `technical-spec.md § 3.3`) |
| Huy hiệu Hero (A.2.badge) | configuration | A.2.badge | Kudos đã nhận `> 0` | 0 Kudos đã nhận (`badgeTierFor` không có ngưỡng cho 0) | GUI_009 |
| Dòng phòng ban (A.2.dept, A.2.dot) | configuration | A.2.dept, A.2.dot | `department !== null` | `department === null` (hồ sơ sparse) | GUI_009 |
| Chip "Spam" (D.3.1) | configuration | D.3.1 | **không bao giờ** | luôn luôn | GUI_007 — field tồn tại ở tầng dữ liệu, không có điều kiện nào bật nó ở màn này |

## 8. Navigation

### Entry Points

| From | Trigger there | Condition | Source |
|------|----------------|-----------|--------|
| Bảng tin Kudos (`/kudos`) | Bấm tên Sunner trên `SunnerChip` (thẻ Kudos) | đã đăng nhập | TBD (draft) |
| Sidebar quà tặng (`/kudos`) | Bấm tên Sunner trên `GiftLeaderboard` | đã đăng nhập | TBD (draft) |
| Menu tài khoản (mọi trang) | Bấm "Profile" | đã đăng nhập | TBD (draft) |

### Exits

| Action | Element | Condition | Destination | Result | Source |
|--------|---------|-----------|-------------|--------|--------|
| Bấm hashtag trên một thẻ | D.card | — | `/kudos?hashtag={tag}` | điều hướng thẳng, bảng tin đã lọc theo tag đó | TBD (draft) |
| Bấm thanh viết Kudo | B.other | chỉ mặt other | `/kudos/new?receiverId={id}` | điều hướng thẳng, người nhận đã điền sẵn, vẫn sửa được | TBD (draft) |
| `?id=` không hợp lệ | — | sai định dạng/không tồn tại/lặp lại | trang 404 | không render bất kỳ region nào của màn hình này | TBD (draft) |

## 9. Accessibility

| Aspect | Status | Notes |
|--------|--------|-------|
| ARIA roles/labels | [EXPECTED] | C.3.1 dùng `role="listbox"`/`role="option"` (cùng khuôn `kudos-filter-menu.tsx`); D.card tái dùng nguyên aria của `KudosCard` |
| Keyboard navigation | [EXPECTED] | Dropdown C.3/C.3.1 mở/đóng/chọn được bằng bàn phím; D.card giữ nguyên hành vi bàn phím đã có |
| Focus management | [EXPECTED] | Đổi chiều dropdown không đánh mất focus khỏi trigger C.3 |
| Screen reader compatibility | [EXPECTED] | 6 ô A.3/B2–B7 không mang tên riêng (không có gì để công bố ngoài "đã khoá" chung); D.empty.*/D.end dùng `aria-live` khi thay nội dung feed |
| Error announcement | N/A — no error states on this screen (read-only apart from the existing heart action) | — |

## 10. Responsive Behavior

N/A — no responsive behavior found in source (frame đo được ở 1440px duy nhất, giống mọi màn Kudos khác đã ship).
