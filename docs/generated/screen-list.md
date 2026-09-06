# Screen List

## SCR001_Login

**Feature:** F001 — Login
**Route:** /login
**Description:** Màn hình đăng nhập SAA 2025 — đăng nhập bằng Google, chọn ngôn ngữ VN/EN.
**States:** default, error, submitting

## SCR002_Homepage

**Feature:** F002 — Homepage SAA
**Route:** /
**Description:** Trang chủ công khai SAA 2025 — keyvisual ROOT FURTHER, đếm ngược sự kiện, hệ thống giải thưởng, khối Sun* Kudos.
**States:** anonymous, authenticated, admin, countdown-live, countdown-expired

## SCR003_AwardSystem

**Feature:** F003 — Award System
**Route:** /awards-information
**Description:** Màn hình công khai hệ thống giải thưởng SAA 2025 — hero tiêu đề mùa giải, menu danh mục sáu mục dính bên trái, sáu thẻ chi tiết giải thưởng, khối Sun* Kudos.
**States:** default, hash-seeded, hash-unmatched, reduced-motion, pre-hydration

## SCR004_KudosLiveBoard

**Feature:** F004 — Kudos Live Board
**Route:** /kudos
**Description:** Live board Sun* Kudos công khai: highlight, bộ lọc, spotlight, feed và sidebar.
**States:** loading, empty, error, success
