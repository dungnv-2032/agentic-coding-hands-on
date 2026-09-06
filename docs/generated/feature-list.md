# Feature List

## Feature Hierarchy

| # | Feature | Priority | Type | Status |
|---|---------|----------|------|--------|
| 1 | F001 — Login | P1 | ui | implemented |
| 2 | F002 — Homepage SAA | P1 | ui | implemented |
| 3 | F003 — Award System | P1 | ui | implemented |

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
