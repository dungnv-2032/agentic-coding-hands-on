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

## SCR005_VietKudo

**Feature:** F005 — Viet Kudo
**Route:** /kudos/new
**Description:** Trang soạn Kudos, chỉ vào được khi đã đăng nhập — chọn người nhận qua autocomplete, đặt danh hiệu, viết nội dung rich-text (đậm/nghiêng/gạch/danh sách/liên kết/trích dẫn, @mention), gắn 1-5 hashtag, đính kèm tối đa 5 ảnh, tuỳ chọn gửi ẩn danh.
**States:** loading, empty, error, saving, success

## SCR006_ProfileBanThan

**Feature:** F006 — Profile ban than
**Route:** /profile (và /profile?id={sunnerId})
**Description:** Hồ sơ Sunner — hero nhận diện (avatar, tên, phòng ban, huy hiệu Hero), hàng 6 ô icon khoá, card thống kê cá nhân hoặc thanh viết Kudo, và feed Kudos đã nhận/đã gửi phân trang keyset.
**States:** loading, empty, error, self, other, sparse

## SCR007_TheLe

**Feature:** F007 — The Le
**Route:** /standards
**Description:** Drawer Thể lệ 553px bám mép phải trên shell chuẩn — ba mục văn xuôi, 4 bậc huy hiệu Hero, lưới 6 icon sưu tập, chân drawer hai nút Đóng / Viết KUDOS. Nội dung đọc từ `rule_sections`/`rule_items` mỗi request.
**States:** default, empty, scrolling, no-scroll

## SCR009_OpenSecretBox

**Feature:** F009 — Open Secret Box
**Route:** /kudos/secret-box
**Description:** Thẻ đơn không shell — tiêu đề, dòng hướng dẫn, khung hộp quà bấm được, đếm số hộp chưa mở. Bấm hộp gọi `open_secret_box()` (Postgres, `security definer`), rút một huy hiệu ngẫu nhiên theo tỷ lệ trọng số, trừ một hộp chưa mở. Trước F009 route này là `ComingSoon`.
**States:** entitled, sparse, anon, opened, pending, error
