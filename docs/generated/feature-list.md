# Feature List

## Feature Hierarchy

| # | Feature | Priority | Type | Status |
|---|---------|----------|------|--------|
| 1 | F001 — Login | P1 | ui | implemented |
| 2 | F002 — Homepage SAA | P1 | ui | implemented |

## Feature Details

### F001 — Login

**Priority:** P1 | **Type:** ui | **Status:** implemented | **Slug:** F001_Login

Đăng nhập SAA 2025 bằng Google OAuth qua Supabase Auth, kèm gác cổng route, chọn ngôn ngữ VN/EN và đăng xuất.

**Related:** screens: SCR001 | routes: /login, /auth/callback, /todo | models: —

### F002 — Homepage SAA

**Priority:** P1 | **Type:** ui | **Status:** implemented | **Slug:** F002_HomepageSaa

Trang chủ công khai SAA 2025 tại `/`: keyvisual ROOT FURTHER, đồng hồ đếm ngược tới giờ sự kiện, khối nội dung Root Further, lưới 6 hạng mục giải thưởng, khối Sun* Kudos, nút widget nổi và footer. Header dùng chung với /login (chọn ngôn ngữ VN/EN) và bổ sung chuông thông báo cùng menu tài khoản cho người đã đăng nhập.

**Related:** screens: SCR002 | routes: / | models: —
