# Feature List

## Feature Hierarchy

| # | Feature | Priority | Type | Status |
|---|---------|----------|------|--------|
| 1 | F001 — Login | P1 | ui | implemented |
| 2 | F002 — Homepage SAA | P1 | ui | implemented |
| 3 | F003 — Award System | P1 | ui | implemented |
| 4 | F004 — Kudos Live Board | P1 | mixed | implemented |

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
