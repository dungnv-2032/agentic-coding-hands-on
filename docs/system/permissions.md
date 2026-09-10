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
> `PERM004` (menu-link Admin Dashboard) và `PERM005` (header control chỉ cho người đã đăng nhập)
> không được kể ở trang này vì cả hai là `screen-permission` ở tầng hiển thị, không phải ranh giới
> route hay RLS — xem thẳng `permissions-matrix.md`.
> Ba ranh giới mới của F006 **chưa có mã thật**; xem § "Mã `PERM###` dự kiến của vòng F006".
> Thể lệ (F007) thêm hai mã **đã cấp thật**: `PERM014` (`rule_sections_select_all`) và `PERM015`
> (`rule_items_select_all`) — xem § "Ranh giới mới của vòng F007". Số hiệu bỏ trống `PERM011`–
> `PERM013` là có chủ đích: chúng vẫn dành cho F006, chưa ai viết entry cho chúng trong registry.
> Open Secret Box (F009) thêm ba mã **đã cấp thật**: `PERM016`, `PERM017`, `PERM018` — xem
> § "Ranh giới mới của vòng F009 (Open Secret Box)". Chúng lấy số tiếp theo sau `PERM015`, không
> đụng tới `PERM011`–`PERM013` vẫn đang dành cho F006.

## Reconciliation Note

Thay đổi đáng kể nhất của vòng F004: **hệ thống có ranh giới phân quyền ở tầng database lần đầu
tiên.** Trước Kudos Live Board, toàn bộ access control của dự án là một câu hỏi duy nhất — "có
session hay không" — do `proxy.ts` thực thi trên đúng hai route. Mọi thứ khác là hiển thị UI.

Kudos Live Board thêm một tầng thật: RLS trên `public.*`. Từ nay có những row mà người xem ẩn
danh đọc được nhưng không ghi được, và việc chặn đó **không** phụ thuộc vào UI — Postgres từ chối
ở tầng dưới. Đây là tiền lệ mọi bảng sau sẽ đi theo.

**Vòng F005 (Viết Kudo) đổi hai thứ nữa:**
1. **Danh sách route được guard không còn là hai.** `/kudos/new` được thêm vào cùng `/todo` — guard
   đầu tiên kể từ F001. Viết một lời cảm ơn cần danh tính, nên ở đây có thứ thật cần bảo vệ.
2. **Có policy `insert` đầu tiên cho dữ liệu nội dung**, không chỉ cho lượt tim. Người dùng đã đăng
   nhập tự tạo được `kudos` (kèm hashtag và ảnh), và RLS chốt rằng họ chỉ tạo được **với tư cách
   chính mình**. Vẫn **không** có `update`/`delete` — sửa và xoá bài là commission khác.

**Vòng này (F006 — Profile bản thân) đổi bản chất một ranh giới đã có, không chỉ thêm route mới:**
1. **`/profile` gia nhập danh sách route guarded** — route thứ ba sau `/todo`, `/kudos/new`, cùng
   một điều kiện `isGuarded` trong `proxy.ts`, cộng page tự re-check session lần nữa (defense in
   depth — mã mới `PERM011`, dự kiến).
2. **Lần đầu tiên một bảng bị REVOKE quyền `select` trực tiếp đã từng mở công khai.** `PERM006`
   (đọc công khai `kudos`) không còn đúng nguyên văn: `public.kudos` tự nó không còn `select`-able
   từ `anon`/`authenticated` nữa — quyền đọc chuyển sang một view mới, `public.kudos_readable`
   (mã mới `PERM012`, dự kiến). Đây là lần đầu "đọc công khai" cần một tầng trung gian thay vì một
   policy `using (true)` thẳng trên bảng.
3. **Ẩn danh chuyển từ quy ước tầng hiển thị sang bảo đảm tầng dữ liệu.** Trước F006, trang này
   ghi thẳng: "Ẩn danh che người gửi ở tầng hiển thị, không xoá người gửi ở tầng dữ liệu... Bất kỳ
   ai đọc được database vẫn biết ai gửi." Câu đó không còn đúng sau F006 — `kudos_readable` null
   hoá các cột `sender_*` thật ở tầng đọc cho bất kỳ ai không phải chính người gửi. Phát biểu thay
   thế nằm ở § Special Conditions.

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
  `/kudos/secret-box`, `/kudos/[id]`, `/standards`, `/admin`); đăng nhập được qua
  `/login`; **không** xem được `/todo`, và **từ F006 không xem được `/profile`** (route này đã
  được guard, khách vãng lai bị đẩy về `/login`).
  Trên `/kudos`, khách vãng lai **không thả tim được**: nút heart render ở trạng thái `disabled`.
- **Người dùng đã đăng nhập** xem được mọi thứ khách vãng lai xem được, cộng `/todo` và
  `/profile`, và **thả tim được** — like được lưu thành row, tồn tại qua reload. Không thả tim
  được trên kudos do chính mình gửi (nút `disabled`).
- **Quản trị viên** thấy thêm đúng một mục "Admin Dashboard" trong menu tài khoản. Trên `/kudos`
  vai trò admin **không mở khoá gì cả** — không moderation, không xoá, không cấu hình ngày đặc
  biệt. Những thứ đó thuộc commission khác (`Admin - Review content`, `Admin - Setting`).

## Access Boundaries

Giờ có hai loại ranh giới, và cần phân biệt rõ:

**Ranh giới ở tầng route (`proxy.ts`)** — **đổi ở vòng F005, rồi lại ở F006**. Vẫn chỉ xét có
session hay không, nhưng giờ trên bốn route: `/todo` cần session (`PERM001`), `/login` bounce khi
đã có session (`PERM002`), `/auth/callback` loại trừ có chủ đích (`PERM003`), **`/kudos/new` cần
session** (`PERM001`/`PERM008`), và **`/profile` cần session** (`PERM011`, dự kiến) — tất cả cùng
một điều kiện `isGuarded` trong `proxy.ts`; khách vãng lai bị đẩy về `/login`.

Phân biệt cho rõ, vì hai vế nghe giống nhau mà khác hẳn: **bề mặt đọc** của Kudos (`/kudos`,
`/kudos/[id]`, `/kudos/secret-box`) vẫn công khai có chủ đích — lối vào tới nó (nav trang chủ, CTA
`KudosPromo`) đều công khai, gác một đích đến mà cửa vào để mở là vô nghĩa. **Bề mặt ghi**
(`/kudos/new`) thì không: nó cần biết ai đang gửi, nên nó được gác. `/profile` cũng vậy — nó là
hồ sơ của một người cụ thể, nên nó cần biết người đó là ai.

**`/standards` là route công khai, và đó là quyết định có chủ đích (F007).** `proxy.ts` canh
`/todo`, `/kudos/new` (khớp chính xác) và `/profile`; `/standards` không nằm trong danh sách và
không được thêm vào. Thể lệ chương trình là thứ người chưa đăng nhập cần đọc *trước* khi quyết định
tham gia — đặt nó sau tường đăng nhập sẽ đảo ngược thứ tự đó. Nút `Viết KUDOS` trên màn này cũng
không tự phán quyền: nó luôn điều hướng, và `proxy.ts` chặn ở `/kudos/new` theo luật sẵn có. Nhân
bản luật đó ở màn Thể lệ sẽ tạo ra nguồn sự thật thứ hai cho cùng một quyết định.

**Ranh giới ở tầng database (RLS — mới)**:
- ~~`select` trên toàn bộ bảng Kudos mở cho `anon` và `authenticated` (`PERM006`)~~ — **câu này
  đã bị F006 thay thế; xem ba gạch đầu dòng ngay dưới.** Phần lý do vẫn đúng và vẫn giữ: dữ liệu
  trên màn hình này là lời cảm ơn công khai trong nội bộ Sun*; không có row nào riêng tư theo
  người xem. Cái đổi là *đường* đọc, không phải *ai* được đọc nội dung.
- **`select` trên `public.kudos` bị REVOKE khỏi `anon` VÀ `authenticated` (PERM012 một nửa).**
  Đọc trực tiếp bảng gốc giờ chỉ chủ sở hữu (vai trò migration) mới làm được. Trạng thái grant
  đo trên database đang chạy: `select` trên `public.kudos` chỉ còn `postgres` và `service_role`.
  Đo qua HTTP thật bằng anon key: `GET /rest/v1/kudos?select=id,sender_id` → **401**, body
  `{"code":"42501","message":"permission denied for table kudos"}`.
  Ngoại lệ duy nhất là một **column grant** hẹp: `grant select (id) on public.kudos to
  authenticated`. Nó cần cho `INSERT ... RETURNING id` trong `create_kudos()` (hàm này để
  `security invoker` có chủ đích, nên RLS vẫn áp) và không mở thêm gì — `where sender_id = ...`
  trên bảng gốc vẫn bị chặn, vì lọc theo một cột cũng đòi `select` trên đúng cột đó. Không có
  filter oracle.
- **`select` trên `public.kudos_readable` (view) mở cho `anon`+`authenticated` (PERM012 nửa còn
  lại)** — thay thế đúng vị trí `PERM006` cho MỌI điểm đọc Kudos của ứng dụng kể từ nay. View
  chạy dưới quyền chủ sở hữu (không set `security_invoker`), nên vẫn đọc được bảng gốc đã bị revoke
  — cơ chế tương đương `security definer` ở cấp function, áp cho view. Các cột bị biến đổi là
  **cả năm cột `sender_*`** — `sender_id`, `sender_full_name`, `sender_avatar_url`,
  `sender_kudos_received_baseline`, `sender_department_name`: cùng null khi `is_anonymous = true`
  và caller không phải người gửi đó, giữ nguyên trong mọi trường hợp khác. `receiver_id` không bị
  che (người nhận vẫn công khai). Chi tiết predicate:
  `docs/features/F006_ProfileBanThan/technical-spec.md § 4.2`.
- **Đường ghi được giữ nguyên qua đợt revoke này.** Ba policy `INSERT` (`kudos_likes_insert_own`,
  `kudos_hashtags_insert_own`, `kudos_attachments_insert_own`) từng join `public.kudos` ngay trong
  `with check` của chúng; policy được đánh giá bằng quyền của CALLER, nên revoke sẽ tự vô hiệu hoá
  chính chúng và giết thao tác thả tim của F004. Phần đọc đó đã được đưa vào trong một biên
  `security definer`: `public.is_kudos_sender(bigint)` — trả về `boolean`, không bao giờ trả id
  người gửi, nên không dùng được làm oracle de-anonymize. Đo sau khi ship: `POST /rest/v1/kudos_likes`
  → 201, `DELETE` → 204, `POST /rest/v1/rpc/create_kudos` → 200.
- **Danh sách "Đã gửi" trên `/profile` chỉ tự-scoped theo session gọi (`PERM013`, dự kiến).** Không
  có tham số nào trong request cho phép một session xin danh sách Đã gửi của người khác — biên nằm
  ở mệnh đề `WHERE sender_id = (session hiện tại)`, không phải ở việc route/UI có hiện tuỳ chọn
  "Đã gửi" hay không (hồ sơ người khác không hiện tuỳ chọn đó — lớp thứ hai, không phải biên thật).
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
- **Hai bảng nội dung thể lệ chỉ đọc được, cho cả `anon` lẫn `authenticated` (`PERM014`,
  `PERM015` — mới ở F007).** `public.rule_sections` và `public.rule_items` theo đúng khuôn
  `kudos_select_all` mà F004 đặt ra: `enable row level security`, đúng một policy
  `<table>_select_all` `for select to anon, authenticated using (true)`, `grant select` tường minh.
  **Không có policy `insert`/`update`/`delete` nào**, nên RLS từ chối mặc định — im lặng chính là
  từ chối, không cần viết policy deny thừa. Màn `/standards` cũng không có Server Action nào, nên
  không tồn tại con đường ghi nào từ phía ứng dụng. Đo trên database đang chạy: RLS bật trên cả hai
  bảng, đúng một policy `SELECT` mỗi bảng, `qual = true`, role `{anon,authenticated}`.

  Điều này an toàn được vì nội dung thể lệ **không có biến thiên theo người xem**: mọi người đọc
  đúng cùng một chữ. Không cần masked view kiểu `kudos_readable` (F006) — đó là cơ chế cho dữ liệu
  mà *ai đang hỏi* làm đổi *câu trả lời*, và không có gì như thế ở đây. Dựng một view che cho nội
  dung tĩnh là chi phí không mua được gì.

  **Sửa nội dung thể lệ hiện chỉ làm được qua migration/seed.** Không có bề mặt quản trị. Nếu sau
  này có màn admin sửa thể lệ, nó phải mang theo policy ghi **và** một kiểm tra vai trò phía server
  — cả hai đều chưa tồn tại, và không được mở sẵn quyền cho một màn chưa có.
- Mọi bảng bật RLS. Một bảng `public` không bật RLS sẽ đọc được không giới hạn qua PostgREST —
  đó là lỗi cấu hình, không phải mặc định chấp nhận được. **Đo được, cần nói thẳng:** `grant select`
  tường minh trong migration là thắt lưng cộng dây đeo quần, KHÔNG phải thứ chặn ghi. Trên stack
  Supabase local, `anon` và `authenticated` thực tế giữ `SELECT, INSERT, UPDATE, DELETE, TRUNCATE,
  REFERENCES, TRIGGER` trên mọi bảng `public` — kể cả các bảng cũ, do `alter default privileges`
  của chính Supabase (`pg_default_acl`: `anon=arwdDxtm`). **RLS mới là thứ từ chối ghi.** Đúng một
  quyền nằm ngoài lớp chặn đó — `TRUNCATE` không chịu sự chi phối của RLS — nhưng PostgREST không
  phơi ra đường nào tới nó, nên không có bề mặt nào client chạm được. Ghi lại vì nó đo được, không
  phải vì F007 tạo ra nó.

**Điểm cần nói thẳng:** nút heart `disabled` ở UI **không** phải ranh giới bảo vệ. Nó là chỉ dẫn
cho người dùng. Ranh giới thật là policy RLS. Hai lớp này phải cùng đúng, và nếu chỉ một lớp
đúng thì lớp phải đúng là RLS.

## Special Conditions

- **Ẩn danh là một bảo đảm ở TẦNG ĐỌC, không chỉ một quy ước hiển thị (đổi ở F006).**
  `sender_id` thật của một Kudos ẩn danh (1) vẫn được LƯU nguyên trong `public.kudos` (không xoá
  dữ liệu — vẫn truy được khi cần, ví dụ kiểm duyệt sau này), nhưng (2) không đọc được qua bất kỳ
  đường nào ứng dụng dùng, vì đường đọc duy nhất (`kudos_readable`) đã null hoá nó — cùng cả bốn
  cột `sender_*` còn lại — cho bất kỳ ai không phải chính người gửi, và đường đọc trực tiếp bảng
  gốc đã bị revoke khỏi cả hai role ứng dụng dùng. Người có quyền chủ sở hữu database
  (migration/admin CLI) vẫn đọc được `sender_id` thật — ẩn danh KHÔNG che khỏi tầng đó, chỉ che
  khỏi mọi role mà ứng dụng chạy dưới. Nếu sau này cần ẩn danh thật (không truy được cả bởi chủ
  sở hữu database), đó là thiết kế khác và phải nói rõ với người dùng.

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

## Mã `PERM###` dự kiến của vòng F006

| Mã (dự kiến) | Mô tả | Thay thế/bổ sung |
|---|---|---|
| `PERM011` | Route guard `/profile` (path + subpath), cùng điều kiện `isGuarded` | Bổ sung — không thay `PERM001`/`PERM008` |
| `PERM012` | Revoke `select` trên `kudos` khỏi `anon`/`authenticated` + grant `select` trên `kudos_readable` | **Thay thế `PERM006`** làm nguồn quyền đọc Kudos thật |
| `PERM013` | Danh sách "Đã gửi" tự-scoped theo session, không nhận id mục tiêu từ client | Bổ sung — không có trong bất kỳ mã nào trước đó |

Mã thật (`PERM0NN`) được cấp ở bước promote/rebuild-spec, không phải ở trang này — bảng trên chỉ
ghi nhận ý định. Các **grant** mà ba mã này mô tả thì đã ship và đã đo (xem § Access Boundaries);
chỉ số hiệu của mã là chưa cấp.

## Ranh giới mới của vòng F007 (Thể lệ)

| Mã | Mô tả | Thay thế/bổ sung |
|---|---|---|
| `PERM014` | `rule_sections_select_all` — đọc công khai nội dung thể lệ (`anon` + `authenticated`), không policy ghi | Bổ sung |
| `PERM015` | `rule_items_select_all` — đọc công khai danh sách huy hiệu/icon (`anon` + `authenticated`), không policy ghi | Bổ sung |

Khác với bảng F006 phía trên, **hai mã này đã được cấp thật** trong
[`docs/generated/permissions-matrix.md`](../generated/permissions-matrix.md) — có entry đầy đủ, có
Principal × Resource, có Related Modules. Chúng lấy `PERM014`/`PERM015` chứ không lấy
`PERM011`/`PERM012` vì ba số đó vẫn đang dành cho F006; lấy chồng lên sẽ làm hai trang tài liệu nói
hai chuyện khác nhau về cùng một mã.

F007 **không** thêm route guard nào, không thêm Server Action nào, không thêm bucket Storage nào, và
không đổi bất kỳ ranh giới nào đã có.

## Ranh giới mới của vòng F009 (Open Secret Box)

Vòng này thêm một **loại** ranh giới mà repo chưa từng có: một hàm Postgres `security definer`.
Mọi hàm trước đó (`create_kudos()`) chạy `security invoker`, tức RLS vẫn áp lên người gọi.
`open_secret_box()` thì không — nó chạy với quyền của chủ hàm, nên nó **bỏ qua** RLS theo đúng
thiết kế. Đó là một sự đánh đổi có chủ ý, không phải một chỗ lỏng tay:

Để trừ một hộp, ai đó phải `UPDATE public.sunners`. Bảng `sunners` cố tình không có policy
UPDATE nào, và cấp một policy như vậy sẽ mở cho mọi phiên đã đăng nhập quyền tự viết lại
`secret_box_unopened_count` của chính mình qua PostgREST — nghĩa là tự phát hộp cho mình. Chọn
`security definer` là chọn để **đúng một** đường ghi tồn tại, và đường đó tự suy ra chủ thể từ
`auth.uid()`, không nhận tham số danh tính nào để mà giả mạo.

Ba biện pháp giữ cho đặc quyền đó không rò ra ngoài phạm vi:

1. `set search_path = public` ghim cứng trong định nghĩa hàm — không thể bị chiếm quyền bằng một
   schema đặt trước trên đường tìm kiếm của người gọi.
2. `revoke execute on function public.open_secret_box() from anon, public` và chỉ
   `grant execute ... to authenticated` — khách vãng lai không gọi được, kể cả gọi thẳng qua RPC.
3. Hàm không nhận tham số nào. Không có `p_sunner_id`, không có `p_badge_id`: cả hai đều do
   database tự quyết, nên "mở hộp hộ người khác" và "chọn huy hiệu mình thích" là những câu
   PostgREST không diễn đạt nổi, chứ không phải những câu bị từ chối.

| Mã | Mô tả | Thay thế/bổ sung |
|---|---|---|
| `PERM016` | `secret_box_badge_odds_select_all` — đọc công khai tỷ lệ rút huy hiệu (`anon` + `authenticated`), không policy ghi | Bổ sung |
| `PERM017` | `secret_box_openings_select_own` — mỗi người chỉ đọc lịch sử mở hộp của chính mình, bắc qua `sunners.auth_user_id = auth.uid()` | Bổ sung |
| `PERM018` | `execute` trên `open_secret_box()` chỉ cấp cho `authenticated`; hàm là **người ghi duy nhất** của `sunners.secret_box_*` và `secret_box_openings` | Bổ sung — không thay mã nào |

Khác với bảng F006 phía trên, **ba mã này đã được cấp thật** trong
[`docs/generated/permissions-matrix.md`](../generated/permissions-matrix.md) — có entry đầy đủ,
đo trực tiếp trên database đang chạy.

F009 **không** thêm route guard nào: `/kudos/secret-box` giữ nguyên là route công khai theo hợp
đồng đã ratify của F004, và việc chặn "chưa đăng nhập thì không mở được" nằm ở tầng màn cộng với
`PERM018`, không nằm ở `proxy.ts`. Đây là lần đầu một ranh giới của dự án được thực thi **chỉ**
bằng grant trên hàm chứ không bằng redirect — đáng ghi lại, vì nó có nghĩa là kiểm thử phải bắn
thẳng vào RPC chứ không chỉ bấm nút.
