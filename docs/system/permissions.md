# Permissions

**Project**: my-app (SAA 2025)
**Generated**: 2026-09-05 (Core pass draft — reconciled against as-built code)
**Analysis Scope**: Toàn bộ route + Server Action trong `app/`, cộng `proxy.ts`.

> **Curated, plain-language view.** Tài liệu này đối chiếu bản forward-draft
> `docs/system/permissions.md` (viết trước khi code, SDD) với code thật sau khi build xong
> F001_Login và F002_HomepageSaa. Mã `PERM###` chính thức nay đã có ở
> [`docs/generated/permissions-matrix.md`](../generated/permissions-matrix.md) (PERM001-PERM005,
> Core pass 2026-09-05) — trang này dùng lại đúng 5 mã đó, không tự cấp phát mã riêng.

## Reconciliation Note

Bản draft `docs/system/permissions.md` (2026-09-05) mô tả đúng với as-built ở **hầu hết mọi
điểm** — không phát hiện sai lệch giữa dự định và code. Điểm cần nói rõ thêm so với bản draft:
draft đã ghi đúng rằng `/admin` "chưa tồn tại trong phạm vi" tại thời điểm viết trước, nhưng
**route `/admin` hiện đã tồn tại** trong code (`app/admin/page.tsx`) — dưới dạng placeholder
`ComingSoon`, **không có kiểm tra vai trò phía server nào được thêm vào nó**
(`app/admin/page.tsx:8-12`). Bản curated dưới đây phản ánh trạng thái as-built này.

## Authorization System Type

**System Type**: `role-based` (nhưng rất mỏng — chỉ một vai trò được kiểm tra, ở đúng một nơi)

| System Type | Description |
|-------------|-------------|
| `rbac` | Role-Based Access Control — roles (admin, user, manager) drive access |
| `abac` | Attribute-Based Access Control — policies on attributes (department, owner, status) |
| `acl` | Access Control List — explicit per-user permissions |
| `ownership` | Resource Ownership — owner_id / created_by / can_edit rules |
| `hybrid` | Mixed — roles combined with ownership checks |
| `other` | Custom permission logic |

**Identified Roles**:
- Khách vãng lai (anonymous) — không có session Supabase.
- Người dùng đã đăng nhập (authenticated) — session Supabase hợp lệ qua Google OAuth.
- Quản trị viên (admin) — `user.app_metadata.role === "admin"` (`app/_page-context.ts:40`); giá
  trị này **không được ghi bởi bất kỳ code nào trong repo** — được cho là cấp phát ngoài băng
  trong Supabase (`scout-report.md § 4`).

## Curated View

- **Khách vãng lai** xem được toàn bộ trang chủ (`/`) và mọi route placeholder
  (`/awards-information`, `/kudos`, `/standards`, `/profile`, `/admin`); đăng nhập được qua
  `/login`; **không** xem được `/todo` — bị điều hướng về `/login`.
- **Người dùng đã đăng nhập** xem được mọi thứ khách vãng lai xem được, cộng `/todo`; nếu vào
  lại `/login` sẽ bị điều hướng ngay về `/todo`. Trên trang chủ, người dùng này còn thấy thêm
  chuông thông báo (panel rỗng) và menu tài khoản (Profile, Sign out).
- **Quản trị viên** thấy mọi thứ người dùng đã đăng nhập thấy được, cộng một mục "Admin
  Dashboard" xuất hiện thêm trong menu tài khoản — **nhưng bấm vào đó chỉ dẫn tới `/admin`, vốn
  vẫn là route công khai không có kiểm tra vai trò**. Vai trò admin ở đây không mở khoá thêm
  bất kỳ dữ liệu hay hành động nào ngoài một liên kết hiển thị.

## Access Boundaries

Ranh giới truy cập thật sự trong hệ thống này rất hẹp:

- Ranh giới duy nhất được `proxy.ts` thực thi (route-guard, chạy trên mọi request trừ asset
  tĩnh) là **có session hay không** — chia đúng hai route: `/todo` (cần session, `PERM001`) và
  `/login` (bounce khi đã có session, `PERM002`). Đây là ranh giới thật, có kiểm tra ở
  edge/server (`proxy.ts:41-46`); `/auth/callback` được loại trừ có chủ đích khỏi cả hai
  (`PERM003`, `proxy.ts:11-13`).
- Mọi route khác — `/`, cả 5 placeholder, và `/auth/callback` — **công khai như nhau**, không
  phân biệt vai trò. `/profile` và `/admin` công khai là chủ ý (chưa có nội dung cần bảo vệ),
  không phải lỗ hổng bị bỏ sót.
- Ranh giới "admin" **không phải** một ranh giới truy cập theo nghĩa hệ thống access-control —
  nó là một điều kiện hiển thị UI (`PERM004`: `app_metadata.role === "admin"` quyết định một
  `<Link>` có render hay không trong `account-menu.tsx:99-107`). Không có route, Server Action,
  hay lần đọc dữ liệu nào kiểm tra lại điều kiện này. Bất kỳ ai gõ thẳng URL `/admin` đều vào
  được, có session hay không, có role admin hay không.
- Ẩn/hiện chuông thông báo và biểu tượng tài khoản theo trạng thái đăng nhập (`PERM005`,
  `home-header.tsx:66,75`) cũng là hiển thị, không phải bảo vệ dữ liệu — panel thông báo hiện
  tại rỗng do chưa có nguồn dữ liệu thông báo nào.

## Special Conditions

- **`/admin` không có authorization boundary — chỉ có menu-link gating.** Đây là giới hạn quan
  trọng nhất cần nói thẳng: nếu một tính năng admin thật được xây ở `/admin` trong tương lai, nó
  **phải tự kiểm tra vai trò phía server**; việc ẩn liên kết trong menu hiện tại không bảo vệ gì
  cả và không được mô tả (ở bất kỳ tài liệu nào khác) như một ranh giới phân quyền đã có sẵn.
- Không có domain allow-list cho đăng nhập Google — mọi tài khoản Google hợp lệ đều được phép
  (`app/login/actions.ts:8-9`).
- Không có time-based, IP-based, hay feature-flag nào chi phối quyền truy cập trong repo hiện
  tại.
- `app_metadata.role` không có quy trình provisioning nào trong code — câu hỏi "admin được cấp
  bằng cách nào" không trả lời được từ repo (giữ nguyên trong
  `scout-report.md § Unresolved questions`, không được suy diễn thêm ở đây).
