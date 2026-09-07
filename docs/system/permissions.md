---
status: implemented
authored_by: takumi
created: 2026-09-07
lang: vi
---

# Permissions

**Project**: my-app (SAA 2025)
**Analysis Scope**: Toàn bộ route + Server Action trong `app/`, `proxy.ts`, và — mới — RLS policy
trong `supabase/migrations/`.

> **Curated, plain-language view.** Mã `PERM###` chính thức nằm ở
> [`docs/generated/permissions-matrix.md`](../generated/permissions-matrix.md); trang này dùng lại
> mã đã có. Hai policy RLS của Kudos Live Board đã được gán mã thật: `PERM006` (đọc công khai) và
> `PERM007` (ghi like, có chủ sở hữu). Viết Kudo (F005) thêm ba mã: `PERM008` (route guard
> `/kudos/new`), `PERM009` (insert `kudos`/`kudos_hashtags`/`kudos_attachments`/`sunners`, không có
> update/delete), `PERM010` (bucket Storage `kudos-attachments`).

## Reconciliation Note

Thay đổi đáng kể nhất của vòng này: **hệ thống có ranh giới phân quyền ở tầng database lần đầu
tiên.** Trước Kudos Live Board, toàn bộ access control của dự án là một câu hỏi duy nhất — "có
session hay không" — do `proxy.ts` thực thi trên đúng hai route. Mọi thứ khác là hiển thị UI.

Kudos Live Board thêm một tầng thật: RLS trên `public.*`. Từ nay có những row mà người xem ẩn
danh đọc được nhưng không ghi được, và việc chặn đó **không** phụ thuộc vào UI — Postgres từ chối
ở tầng dưới. Đây là tiền lệ mọi bảng sau sẽ đi theo.

**Vòng này (Viết Kudo) đổi hai thứ nữa:**
1. **Danh sách route được guard không còn là hai.** `/kudos/new` được thêm vào cùng `/todo` — guard
   đầu tiên kể từ F001. Viết một lời cảm ơn cần danh tính, nên ở đây có thứ thật cần bảo vệ.
2. **Có policy `insert` đầu tiên cho dữ liệu nội dung**, không chỉ cho lượt tim. Người dùng đã đăng
   nhập tự tạo được `kudos` (kèm hashtag và ảnh), và RLS chốt rằng họ chỉ tạo được **với tư cách
   chính mình**. Vẫn **không** có `update`/`delete` — sửa và xoá bài là commission khác.

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

**Ranh giới ở tầng route (`proxy.ts`)** — **đổi ở vòng này**. Vẫn chỉ xét có session hay không,
nhưng trên ba route: `/todo` cần session (`PERM001`), `/login` bounce khi đã có session
(`PERM002`), `/auth/callback` loại trừ có chủ đích (`PERM003`), và **`/kudos/new` cần session**
(`PERM001`/`PERM008` — cùng một điều kiện `isGuarded` trong `proxy.ts`, xét hai route) — khách
vãng lai bị đẩy về `/login`.

Phân biệt cho rõ, vì hai vế nghe giống nhau mà khác hẳn: **bề mặt đọc** của Kudos (`/kudos`,
`/kudos/[id]`, `/kudos/secret-box`) vẫn công khai có chủ đích — lối vào tới nó (nav trang chủ, CTA
`KudosPromo`) đều công khai, gác một đích đến mà cửa vào để mở là vô nghĩa. **Bề mặt ghi**
(`/kudos/new`) thì không: nó cần biết ai đang gửi, nên nó được gác.

**Ranh giới ở tầng database (RLS — mới)**:
- `select` trên toàn bộ bảng Kudos mở cho `anon` và `authenticated` (`PERM006`). Dữ liệu trên màn
  hình này là lời cảm ơn công khai trong nội bộ Sun*; không có row nào riêng tư theo người xem.
- `insert` / `delete` trên `kudos_likes` chỉ mở cho `authenticated`, và `with check` /
  `using` bắt buộc `(select auth.uid()) = user_id`; `insert` còn chặn thêm trường hợp người xem
  chính là người gửi kudos đó (`PERM007`, BR-003). Người dùng không tạo hay xoá được like của
  người khác — Postgres từ chối, không phải UI từ chối.
- **Không có** policy `update` nào trên `kudos_likes`: bỏ tim là `delete`, không phải cập nhật cờ.
- **`insert` trên `kudos`, `kudos_hashtags`, `kudos_attachments`, `sunners` — mới, `PERM009`.**
  Chỉ mở cho `authenticated`. Điểm cốt lõi: `kudos.sender_id` trỏ tới `sunners`, **không** trỏ tới
  `auth.users`, nên predicate phải bắc cầu qua bảng `sunners`:
  `sender_id in (select id from sunners where auth_user_id = (select auth.uid()))`.
  `kudos_hashtags` / `kudos_attachments` kiểm quyền sở hữu dòng `kudos` cha. `sunners` mở `insert`
  để một người vừa đăng nhập tự tạo được danh tính của chính mình (`with check` khớp `auth_user_id`
  = `auth.uid()`), không tạo hộ ai khác.
  **Đường ghi thật đi qua một hàm, không gọi thẳng bốn policy trên.** `createKudos` gọi
  `supabase.rpc("create_kudos", ...)` — hàm này xác nhận là `security invoker` (**không phải**
  `security definer`, kiểm tra trực tiếp trên DB: `pg_proc.prosecdef = f`), nên chạy dưới quyền
  người gọi và mọi policy trên vẫn áp dụng đầy đủ; hàm tồn tại để gộp ba bảng ghi vào một
  transaction, không phải để né RLS. Quan trọng hơn: **hàm không nhận tham số `sender_id` nào cả**
  — người gửi luôn suy từ `auth.uid()` bên trong hàm. Vì vậy mạo danh người gửi không phải là điều
  *bị từ chối*, mà là điều **không thể biểu diễn được** — client không có chỗ nào để nhét
  `sender_id` của người khác vào request.
- **Không có policy `update` và `delete` nào cho `kudos`.** Đã gửi là không sửa, không xoá — ở
  phạm vi commission này. Không mở sẵn quyền mà chưa màn nào dùng.
- **Bucket Storage cho ảnh đính kèm (`kudos-attachments`, `PERM010`)** có policy riêng:
  `authenticated` ghi được — và chỉ ghi được vào thư mục của chính mình (path bắt đầu bằng
  `auth.uid()` của người gọi) — đọc công khai (ảnh hiện trên bảng công khai). Kiểu file được kiểm
  **cả ở server**, vì client không phải biên: kiểm MIME khai báo trước, rồi soi tiếp byte đầu file
  so với chữ ký nhị phân thật của định dạng đó trước khi ghi.
- Mọi bảng bật RLS. Một bảng `public` không bật RLS sẽ đọc được không giới hạn qua PostgREST —
  đó là lỗi cấu hình, không phải mặc định chấp nhận được.

**Điểm cần nói thẳng:** nút heart `disabled` ở UI **không** phải ranh giới bảo vệ. Nó là chỉ dẫn
cho người dùng. Ranh giới thật là policy RLS. Hai lớp này phải cùng đúng, và nếu chỉ một lớp
đúng thì lớp phải đúng là RLS.

## Special Conditions

- **Ẩn danh che người gửi ở tầng hiển thị, không xoá người gửi ở tầng dữ liệu.** `is_anonymous`
  đổi cách thẻ Kudos render phía người gửi; `sender_id` vẫn lưu thật. Nói thẳng vì đây là điều dễ
  bị hiểu sai: đó **không** phải ẩn danh trước hệ thống, chỉ là ẩn danh trước người đọc. Bất kỳ ai
  đọc được database vẫn biết ai gửi. Nếu sau này cần ẩn danh thật (không truy được), đó là thiết kế
  khác và phải nói rõ với người dùng.

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
