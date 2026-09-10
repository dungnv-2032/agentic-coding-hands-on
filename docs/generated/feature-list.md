# Feature List

## Feature Hierarchy

| # | Feature | Priority | Type | Status |
|---|---------|----------|------|--------|
| 1 | F001 — Login | P1 | ui | implemented |
| 2 | F002 — Homepage SAA | P1 | ui | implemented |
| 3 | F003 — Award System | P1 | ui | implemented |
| 4 | F004 — Kudos Live Board | P1 | mixed | implemented |
| 5 | F005 — Viet Kudo | P1 | mixed | implemented |
| 6 | F006 — Profile ban than | P1 | mixed | implemented |
| 7 | F007 — The Le | P1 | mixed | implemented |
| 8 | F008 — Floating Action Button | P2 | ui | implemented |

## Feature Details

### F001 — Login

**Priority:** P1 | **Type:** ui | **Status:** implemented | **Slug:** F001_Login

Đăng nhập SAA 2025 bằng Google OAuth qua Supabase Auth, kèm gác cổng route, chọn ngôn ngữ VN/EN và đăng xuất.

**Related:** screens: SCR001 | routes: /login, /auth/callback, /todo | models: —

### F002 — Homepage SAA

**Priority:** P1 | **Type:** ui | **Status:** implemented | **Slug:** F002_HomepageSaa

Trang chủ công khai SAA 2025 tại `/`: keyvisual ROOT FURTHER, đồng hồ đếm ngược tới giờ sự kiện, khối nội dung Root Further, lưới 6 hạng mục giải thưởng, khối Sun* Kudos, nút widget nổi và footer. Header dùng chung với /login (chọn ngôn ngữ VN/EN) và bổ sung chuông thông báo cùng menu tài khoản cho người đã đăng nhập.

**Related:** screens: SCR002 | routes: / | models: —

### F003 — Award System

**Priority:** P1 | **Type:** ui | **Status:** implemented | **Slug:** F003_AwardSystem

Màn hình công khai "Hệ thống giải" tại `/awards-information`, thay hẳn shell `ComingSoon` từng chiếm route đó: hero tiêu đề mùa giải, menu danh mục sáu mục dính bên trái có scroll-spy, sáu thẻ chi tiết giải thưởng xen kẽ trái/phải (mô tả, số lượng, giá trị giải), khối Sun* Kudos và footer dùng lại của trang chủ. Nhận deep link `#<slug>` từ sáu thẻ giải thưởng trên trang chủ. Đủ hai ngôn ngữ VN/EN, không có API và không có bảng dữ liệu.

**Related:** screens: SCR003 | routes: /awards-information | models: —

### F004 — Kudos Live Board

**Priority:** P1 | **Type:** mixed | **Status:** implemented | **Slug:** F004_KudosLiveBoard

Màn hình công khai Sun* Kudos - Live board tại `/kudos`: highlight carousel top-5 theo số tim, bộ lọc Hashtag + Phòng ban AND-combine trên cả hai mục, Spotlight word-cloud kèm ticker, feed ALL KUDOS infinite scroll, sidebar thống kê cá nhân và bảng 10 Sunner nhận quà. Lớp Postgres đầu tiên của repo: migration, RLS, seed lấy nguyên từ frame Figma.

**Related:** screens: SCR004 | routes: /kudos | models: kudos, kudos_likes, sunners, hashtags, departments, gift_awards, spotlight_events

### F005 — Viet Kudo

**Priority:** P1 | **Type:** mixed | **Status:** implemented | **Slug:** F005_VietKudo

Màn soạn Kudo tại `/kudos/new`, thay shell `ComingSoon`: chọn người nhận bằng autocomplete, đặt danh hiệu, viết nội dung trong editor rich-text (đậm/nghiêng/gạch/danh sách/liên kết/trích dẫn và @mention), gắn 1-5 hashtag, đính kèm tối đa 5 ảnh upload thật lên Supabase Storage, và tuỳ chọn gửi ẩn danh. Route được gác đăng nhập đầu tiên kể từ F001, và là đường ghi nhiều bảng đầu tiên của repo.

**Related:** screens: SCR005 | routes: /kudos/new | models: kudos, kudos_hashtags, kudos_attachments, sunners, departments

### F006 — Profile ban than

**Priority:** P1 | **Type:** mixed | **Status:** implemented | **Slug:** F006_ProfileBanThan

Màn Profile tại `/profile`, thay shell `ComingSoon`: hero keyvisual với avatar, tên, phòng ban và huy hiệu danh hiệu; hàng 6 ô icon (đều khoá); và mục KUDOS phân trang bằng keyset cursor. `?id=` mở profile người khác — khi đó card thống kê được thay hoàn toàn bằng thanh viết Kudo, và số Kudos đã gửi bị ẩn vì nó đếm cả Kudos gửi ẩn danh. Route được gác đăng nhập; migration kèm theo biến tính ẩn danh của Kudos từ quy ước tầng render thành bảo đảm tầng dữ liệu.

**Related:** screens: SCR006 | routes: /profile | models: kudos, kudos_likes, sunners, hashtags, departments, gift_awards, kudos_readable

### F007 — The Le

**Priority:** P1 | **Type:** mixed | **Status:** implemented | **Slug:** F007_TheLe

Màn Thể lệ tại `/standards`, thay shell `ComingSoon` cuối cùng do F002 để lại trên các lối tắt trang chủ: drawer 553px bám mép phải trên shell chuẩn, ba mục văn xuôi có thứ tự, 4 bậc huy hiệu Hero kèm ảnh pill, lưới 6 icon sưu tập, chân drawer hai nút `Đóng` / `Viết KUDOS`. Route công khai, không Server Action, không thao tác ghi. Đây là lần đầu **nội dung biên tập** của một màn hình sống trong Postgres thay vì hardcode trong `lib/` (F003 làm cách còn lại) — hai bảng chỉ đọc, RLS public-read, ảnh nằm trên đĩa và dòng dữ liệu chỉ giữ đường dẫn.

**Related:** screens: SCR007 | routes: /standards | models: rule_sections, rule_items | perms: PERM014, PERM015

### F008 — Floating Action Button

**Priority:** P2 | **Type:** ui | **Status:** implemented | **Slug:** F008_FloatingActionButton

Nút nổi góc dưới-phải trang chủ chuyển từ hai `<Link>` thẳng thành một disclosure trigger thật: bấm pill mở nhóm ba nút `Thể lệ` → `/standards`, `Viết KUDOS` → `/kudos/new`, và nút tròn đỏ `Hủy`. Đóng bằng `Hủy`, `Escape` hoặc bấm ra ngoài, dùng lại nguyên `use-dismiss-on-outside.ts`. Thuần client state — không bảng mới, không migration, không Server Action, không endpoint; hai đích đến đều đã ship (F007, F005) và không bị sửa. Frame thứ hai của thiết kế (`Sv7DFwBw1h`) lật lại kết luận "no quick-action menu" mà F002 rút ra khi chỉ nhìn thấy frame collapsed.

**Related:** screens: SCR002 | routes: /, /standards, /kudos/new | models: — | perms: —
