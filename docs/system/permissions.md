---
status: implemented
authored_by: takumi
created: 2026-09-06
lang: vi
---

# Permissions

**Project**: my-app (SAA 2025)
**Analysis Scope**: Toàn bộ route + Server Action trong `app/`, `proxy.ts`, và — mới — RLS policy
trong `supabase/migrations/`.

> **Curated, plain-language view.** Mã `PERM###` chính thức nằm ở
> [`docs/generated/permissions-matrix.md`](../generated/permissions-matrix.md); trang này dùng lại
> mã đã có. Hai policy RLS của Kudos Live Board đã được gán mã thật: `PERM006` (đọc công khai) và
> `PERM007` (ghi like, có chủ sở hữu).

## Reconciliation Note

Thay đổi đáng kể nhất của vòng này: **hệ thống có ranh giới phân quyền ở tầng database lần đầu
tiên.** Trước Kudos Live Board, toàn bộ access control của dự án là một câu hỏi duy nhất — "có
session hay không" — do `proxy.ts` thực thi trên đúng hai route. Mọi thứ khác là hiển thị UI.

Kudos Live Board thêm một tầng thật: RLS trên `public.*`. Từ nay có những row mà người xem ẩn
danh đọc được nhưng không ghi được, và việc chặn đó **không** phụ thuộc vào UI — Postgres từ chối
ở tầng dưới. Đây là tiền lệ mọi bảng sau sẽ đi theo.

## Authorization System Type

**System Type**: `hybrid` — role-based rất mỏng ở tầng app (một vai trò, kiểm ở đúng một nơi),
cộng ownership thật ở tầng database (RLS khớp `auth.uid()`).

| System Type | Description |
|-------------|-------------|
| `rbac` | Role-Based Access Control — roles (admin, user, manager) drive access |
| `abac` | Attribute-Based Access Control — policies on attributes (department, owner, status) |
| `acl` | Access Control List — explicit per-user permissions |
| `ownership` | Resource Ownership — owner_id / created_by / can_edit rules |
| `hybrid` | Mixed — roles combined with ownership checks |
| `other` | Custom permission logic |

Trước đây trang này ghi `role-based`. Đổi sang `hybrid` vì `kudos_likes` là ownership thật:
policy so `(select auth.uid())` với `user_id` của row, không so vai trò.

**Identified Roles**:
- Khách vãng lai (anonymous) — không có session Supabase. Ở tầng DB là Postgres role `anon`.
- Người dùng đã đăng nhập (authenticated) — session Supabase hợp lệ qua Google OAuth. Ở tầng DB
  là role `authenticated`, JWT mang `sub` = `auth.uid()`.
- Quản trị viên (admin) — `user.app_metadata.role === "admin"` (`app/_page-context.ts:40`); giá
  trị này **không được ghi bởi bất kỳ code nào trong repo**. Vai trò này **không** xuất hiện
  trong RLS policy nào của Kudos — nó vẫn thuần là điều kiện hiển thị.

## Curated View

- **Khách vãng lai** xem được toàn bộ trang chủ (`/`), màn hình hệ thống giải
  (`/awards-information`), **màn hình Kudos Live Board (`/kudos`) đầy đủ** — highlight, feed,
  spotlight, sidebar, số tim — và mọi route placeholder còn lại (`/kudos/new`,
  `/kudos/secret-box`, `/kudos/[id]`, `/standards`, `/profile`, `/admin`); đăng nhập được qua
  `/login`; **không** xem được `/todo`.
  Trên `/kudos`, khách vãng lai **không thả tim được**: nút heart render ở trạng thái `disabled`.
- **Người dùng đã đăng nhập** xem được mọi thứ khách vãng lai xem được, cộng `/todo`, và **thả
  tim được** — like được lưu thành row, tồn tại qua reload. Không thả tim được trên kudos do
  chính mình gửi (nút `disabled`).
- **Quản trị viên** thấy thêm đúng một mục "Admin Dashboard" trong menu tài khoản. Trên `/kudos`
  vai trò admin **không mở khoá gì cả** — không moderation, không xoá, không cấu hình ngày đặc
  biệt. Những thứ đó thuộc commission khác (`Admin - Review content`, `Admin - Setting`).

## Access Boundaries

Giờ có hai loại ranh giới, và cần phân biệt rõ:

**Ranh giới ở tầng route (`proxy.ts`)** — không đổi. Chỉ xét có session hay không, trên đúng hai
route: `/todo` cần session (`PERM001`), `/login` bounce khi đã có session (`PERM002`),
`/auth/callback` loại trừ có chủ đích (`PERM003`). `/kudos` và mọi route Kudos con **không** được
thêm guard — công khai có chủ đích, vì lối vào duy nhất tới nó (nav trang chủ, CTA `KudosPromo`)
đều công khai; gác một đích đến mà cửa vào để mở là vô nghĩa.

**Ranh giới ở tầng database (RLS — mới)**:
- `select` trên toàn bộ bảng Kudos mở cho `anon` và `authenticated` (`PERM006`). Dữ liệu trên màn
  hình này là lời cảm ơn công khai trong nội bộ Sun*; không có row nào riêng tư theo người xem.
- `insert` / `delete` trên `kudos_likes` chỉ mở cho `authenticated`, và `with check` /
  `using` bắt buộc `(select auth.uid()) = user_id`; `insert` còn chặn thêm trường hợp người xem
  chính là người gửi kudos đó (`PERM007`, BR-003). Người dùng không tạo hay xoá được like của
  người khác — Postgres từ chối, không phải UI từ chối.
- **Không có** policy `update` nào trên `kudos_likes`: bỏ tim là `delete`, không phải cập nhật cờ.
- Mọi bảng bật RLS. Một bảng `public` không bật RLS sẽ đọc được không giới hạn qua PostgREST —
  đó là lỗi cấu hình, không phải mặc định chấp nhận được.

**Điểm cần nói thẳng:** nút heart `disabled` ở UI **không** phải ranh giới bảo vệ. Nó là chỉ dẫn
cho người dùng. Ranh giới thật là policy RLS. Hai lớp này phải cùng đúng, và nếu chỉ một lớp
đúng thì lớp phải đúng là RLS.

## Special Conditions

- **`/admin` vẫn không có authorization boundary — chỉ có menu-link gating.** Không đổi, và Kudos
  không sửa. Nếu một tính năng admin thật được xây ở `/admin`, nó **phải tự kiểm tra vai trò phía
  server**; ẩn liên kết trong menu không bảo vệ gì cả.
- **Cộng tim vào tài khoản người gửi (+1, hoặc +2 ngày đặc biệt) chưa được xây.** Spec `C.4.1` mô
  tả nó, nhưng nó cần persistence cho số dư cộng bề mặt cấu hình `Admin - Setting` — cả hai đều
  chưa có. Biểu tượng `x2` trên sidebar là **hiển thị theo frame, không phải mô phỏng logic**.
  Đây là khoảng trống đã ghi nhận, không phải lỗ hổng bị bỏ sót.
- **Test case `71b3ef43` yêu cầu người chưa đăng nhập bị đẩy về `/login`** — trái với thiết kế
  route công khai ở trên. Ghi nhận, không cài đặt; cần một quyết định sản phẩm về việc toàn bộ bề
  mặt Kudos có phải members-only hay không.
- Không có domain allow-list cho đăng nhập Google — mọi tài khoản Google hợp lệ đều được phép.
- Không có time-based, IP-based, hay feature-flag nào chi phối quyền truy cập.
- `app_metadata.role` không có quy trình provisioning nào trong code — câu hỏi "admin được cấp
  bằng cách nào" vẫn không trả lời được từ repo.
