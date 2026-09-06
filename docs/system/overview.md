**Project**: my-app (SAA 2025)
**Generated**: 2026-09-05 (Core pass draft)
**Architecture Type**: Monolithic Next.js App Router (Server Components + Server Actions), không
tách backend riêng — xem [architecture.md](architecture.md).

## Executive Summary

Đây là website công khai cho Sun* Annual Awards 2025 (SAA 2025) — một sự kiện thường niên nội
bộ của Sun*, dùng để truyền thông chủ đề mùa giải "Root Further", giới thiệu 6 hạng mục giải
thưởng, quảng bá Sun* Kudos, và cho phép Sunner đăng nhập bằng tài khoản Google để vào khu vực
đã xác thực. Repo ship **ba** tính năng end-to-end (số liệu file/dòng bên dưới là ảnh chụp của Core pass
2026-09-05: 61 file TS/TSX, ~4.347 dòng — chưa tính màn hình F003 thêm vào ngày 2026-09-06):

- **F001_Login** — đăng nhập Google qua Supabase Auth (GoTrue), gác cổng `/todo`/`/login`,
  chọn ngôn ngữ VN/EN, đăng xuất. Xem `docs/features/F001_Login/functional-spec.md`.
- **F002_HomepageSaa** — trang chủ công khai `/`: header, hero + đếm ngược sự kiện, khối chủ đề
  "Root Further", lưới 6 thẻ giải thưởng, quảng bá Sun* Kudos, widget nổi, footer; cộng chuông
  thông báo (rỗng) + menu tài khoản khi đã đăng nhập. Xem
  `docs/features/F002_HomepageSaa/functional-spec.md`.
- **F003_AwardSystem** — màn hình công khai "Hệ thống giải" tại `/awards-information`: hero tiêu
  đề mùa giải, menu danh mục sáu mục dính bên trái có scroll-spy, sáu thẻ chi tiết giải thưởng,
  khối Sun* Kudos và footer dùng lại của trang chủ. Không có API, không có bảng dữ liệu. Xem
  `docs/features/F003_AwardSystem/functional-spec.md`.

Bốn route còn lại (`/kudos`, `/standards`, `/profile`, `/admin`) là **placeholder công khai** —
mỗi route chỉ render `<ComingSoon />` (header/footer thật + thông báo "sắp ra mắt"), chưa có nội
dung nghiệp vụ thật. Chúng tồn tại để mọi liên kết trên trang chủ có đích hợp lệ, không phải vì
đã có tính năng đứng sau. `/awards-information` từng nằm trong nhóm này và đã rời khỏi nó ngày
2026-09-06 khi F003 ship.

For architecture diagrams and tech stack details, see [architecture.md](architecture.md).

## Key Design Decisions

### Decision 1: Không tự dựng data layer — mọi state nghiệp vụ nằm ở Supabase GoTrue hoặc trong code

**Context**: Ứng dụng cần biết ai đã đăng nhập và (một trường hợp) vai trò admin, nhưng không
có nhu cầu lưu trữ dữ liệu nghiệp vụ nào khác ở giai đoạn này (danh sách giải thưởng, nội dung
i18n đều tĩnh).

**Decision**: Không có bảng, migration, hay SQL nào của riêng app. Toàn bộ schema là
`auth.users` do GoTrue quản lý; app chỉ đọc `user` (null/non-null), `user.app_metadata.role`,
`user.email` (`scout-report.md § 4`). Danh mục 6 giải thưởng và hai bộ dictionary vi/en là các
mảng TypeScript đóng băng trong code, không phải bảng dữ liệu.

**Rationale**: YAGNI — dựng schema riêng cho một cờ vai trò hay một danh sách 6 phần tử cố
định là thừa. `app_metadata.role` được cấp phát ngoài băng (out-of-band) trong Supabase, code
không ghi giá trị này ở đâu cả — câu hỏi "admin được provision thế nào" chưa trả lời được từ
code (`scout-report.md § Unresolved questions`).

### Decision 2: i18n tự viết bằng cookie + dictionary tĩnh, không dùng thư viện i18n

**Context**: Cần hai ngôn ngữ (vi mặc định, en) hiển thị nhất quán server/client mà không dùng
URL segment (`/vi/...`, `/en/...`).

**Decision**: Một cookie `NEXT_LOCALE` (`lib/i18n/locales.ts:14`), một interface `Dictionary`
dùng chung cho `vi.ts`/`en.ts` (kiểm tra ở compile-time qua `tsc --noEmit`), đọc trực tiếp
trong Server Component qua `_page-context.ts` — không middleware negotiation, không
`Accept-Language` sniffing.

**Rationale**: KISS — hai locale cố định không cần một thư viện i18n đầy đủ tính năng
(pluralization, ICU message format...) mà dự án không dùng tới. Đánh đổi: `app/layout.tsx:15`
đang hardcode `lang="en"` dù mặc định là `vi` — một khiếm khuyết i18n thật, chưa được sửa
(`scout-report.md § 7`).

## Security Overview

- **Authentication**: Google OAuth duy nhất, qua Supabase GoTrue (`supabase.auth.signInWithOAuth`)
  — không có đăng nhập email/mật khẩu trong UI, không giới hạn domain Google
  (`app/login/actions.ts:8-9`).
- **Authorization**: Rất mỏng — chỉ một route guard hai luật (`/todo` cần session, `/login`
  bounce khi đã có session — `proxy.ts:41-46`) và một điều kiện hiển thị menu
  (`app_metadata.role === "admin"` — `app/_page-context.ts:40`). Xem
  [permissions.md](permissions.md) để biết ranh giới thật của mô hình này.
- **Data Encryption**: Không có xử lý mã hoá riêng của app; giao vận qua HTTPS/cookie do
  Next.js + Supabase quản lý. Không service-role key nào được giữ trong repo
  (`.env.example`, `scout-report.md § 6`).
- **API Security**: Route handler duy nhất (`/auth/callback`) tự phòng thủ open-redirect và
  origin-spoofing — origin lấy từ `NEXT_PUBLIC_SITE_URL`, không lấy từ `Host` header của
  request (`app/auth/callback/route.ts:31-64`, BL-07). Không có API surface nào khác của app để
  đánh giá.

## Scalability

- **Current Capacity**: Không có số liệu tải/production nào trong repo để trích dẫn — không
  benchmark, không APM, không cấu hình autoscale.
- **Scaling Strategy**: Không xác định được từ code — không có Deployment View
  (xem [architecture.md § Deployment View](architecture.md)), nên không có cơ sở để mô tả chiến
  lược scale.
- **Performance Targets**: Không có SLA/ngân sách hiệu năng nào ghi trong repo. Ràng buộc hiệu
  năng duy nhất quan sát được là ở test: `playwright.config.ts` pin giá trị đếm ngược 45 ngày để
  tránh lỗi hiển thị 3 ký tự khi >99 ngày (`scout-report.md § BL-03`) — một giới hạn thiết kế
  của component, không phải một mục tiêu hiệu năng hệ thống.

## Boundaries

- Ứng dụng **không có** backend/API riêng ngoài một route handler OAuth callback; mọi tương tác
  dữ liệu khác là qua Supabase Auth SDK trực tiếp từ Server Component/Server Action.
- Ứng dụng **không có** database, migration, hay ORM của riêng nó — ranh giới dữ liệu dừng ở
  `auth.users` do GoTrue sở hữu.
- Ứng dụng **không có** hệ thống thông báo thật — chuông thông báo trên header chỉ mở một panel
  rỗng ("Không có thông báo mới"), không có nguồn dữ liệu backend (`scout-report.md § 1`,
  `notification-bell.tsx:38-42`).
- `/admin` **không** phải một ranh giới phân quyền — xem giới hạn nêu rõ ở
  [permissions.md](permissions.md).
- Không có CI/CD, IaC, hay cấu hình triển khai nào trong repo ở thời điểm Core pass này.
