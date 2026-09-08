---
status: draft
authored_by: takumi
created: 2026-09-08
lang: vi
---

# Permissions — forward-draft delta (F006_ProfileBanThan)

**Phạm vi file này:** CHỈ phần `docs/system/permissions.md` mà F006 đổi. Đọc file hiện tại (đã
`implemented`, mô tả tới F005) để lấy phần còn lại — bốn điểm dưới đây THAY THẾ đúng phần tương
ứng khi Core pass reconcile.

## Thay thế § "Reconciliation Note" — điểm mới của vòng này

**Vòng này (Profile bản thân) đổi bản chất một ranh giới đã có, không chỉ thêm route mới:**
1. **`/profile` gia nhập danh sách route guarded** — route thứ ba sau `/todo`, `/kudos/new`, cùng
   một điều kiện `isGuarded` trong `proxy.ts`, cộng page tự re-check session lần nữa (defense in
   depth — mã mới `PERM011`, dự kiến).
2. **Lần đầu tiên một bảng bị REVOKE quyền `select` trực tiếp đã từng mở công khai.** `PERM006`
   (đọc công khai `kudos`) không còn đúng nguyên văn: `public.kudos` tự nó không còn `select`-able
   từ `anon`/`authenticated` nữa — quyền đọc chuyển sang một view mới, `public.kudos_readable`
   (mã mới `PERM012`, dự kiến). Đây là lần đầu "đọc công khai" cần một tầng trung gian thay vì một
   policy `using (true)` thẳng trên bảng.
3. **Ẩn danh chuyển từ quy ước tầng hiển thị sang bảo đảm tầng dữ liệu.** Trước F006, `permissions.md`
   ghi thẳng: "Ẩn danh che người gửi ở tầng hiển thị, không xoá người gửi ở tầng dữ liệu... Bất kỳ ai
   đọc được database vẫn biết ai gửi." Câu đó không còn đúng sau F006 — `kudos_readable` null hoá
   `sender_id` thật ở tầng đọc cho bất kỳ ai không phải chính người gửi. Xem thay thế đầy đủ ở mục
   dưới.

## Thay thế § "Access Boundaries" → "Ranh giới ở tầng database (RLS — mới)"

Bổ sung ngay sau dòng `PERM006` hiện có:

- **`select` trên `public.kudos` bị REVOKE khỏi `anon` VÀ `authenticated` (PERM012 một nửa).**
  Đọc trực tiếp bảng gốc giờ chỉ chủ sở hữu (vai trò migration) mới làm được.
- **`select` trên `public.kudos_readable` (view) mở cho `anon`+`authenticated` (PERM012 nửa còn
  lại)** — thay thế đúng vị trí `PERM006` cho MỌI điểm đọc Kudos của ứng dụng kể từ nay. View
  chạy dưới quyền chủ sở hữu (không set `security_invoker`), nên vẫn đọc được bảng gốc đã bị revoke
  — cơ chế tương đương `security definer` ở cấp function, áp cho view. Cột duy nhất bị biến đổi là
  `sender_id`: null khi `is_anonymous = true` và caller không phải người gửi đó, giữ nguyên trong
  mọi trường hợp khác. Chi tiết predicate: `docs/features/F006_ProfileBanThan/technical-spec.md § 4.2`.
- **Danh sách "Đã gửi" trên `/profile` chỉ tự-scoped theo session gọi (`PERM013`, dự kiến).** Không
  có tham số nào trong request cho phép một session xin danh sách Đã gửi của người khác — biên nằm
  ở mệnh đề `WHERE sender_id = (session hiện tại)`, không phải ở việc route/UI có hiện tuỳ chọn
  "Đã gửi" hay không (hồ sơ người khác không hiện tuỳ chọn đó — lớp thứ hai, không phải biên thật).

## Thay thế § "Special Conditions" — dòng "Ẩn danh che người gửi..."

**Câu cũ (không còn đúng sau F006):** "Ẩn danh che người gửi ở tầng hiển thị, không xoá người gửi
ở tầng dữ liệu... Bất kỳ ai đọc được database vẫn biết ai gửi."

**Câu thay thế:** Ẩn danh giờ là một bảo đảm ở TẦNG ĐỌC, không chỉ một quy ước hiển thị.
`sender_id` thật của một Kudos ẩn danh (1) vẫn được LƯU nguyên trong `public.kudos` (không xoá dữ
liệu — vẫn truy được khi cần, ví dụ kiểm duyệt sau này), nhưng (2) không đọc được qua bất kỳ
đường nào ứng dụng dùng, vì đường đọc duy nhất (`kudos_readable`) đã null hoá nó cho bất kỳ ai
không phải chính người gửi, và đường đọc trực tiếp bảng gốc đã bị revoke khỏi cả hai role ứng dụng
dùng. Người có quyền chủ sở hữu database (migration/admin CLI) vẫn đọc được `sender_id` thật —
ẩn danh KHÔNG che khỏi tầng đó, chỉ che khỏi mọi role mà ứng dụng chạy dưới.

## Thêm mới — mã `PERM###` dự kiến của vòng này

| Mã (dự kiến) | Mô tả | Thay thế/bổ sung |
|---|---|---|
| `PERM011` | Route guard `/profile` (path + subpath), cùng điều kiện `isGuarded` | Bổ sung — không thay `PERM001`/`PERM008` |
| `PERM012` | Revoke `select` trên `kudos` khỏi `anon`/`authenticated` + grant `select` trên `kudos_readable` | **Thay thế `PERM006`** làm nguồn quyền đọc Kudos thật |
| `PERM013` | Danh sách "Đã gửi" tự-scoped theo session, không nhận id mục tiêu từ client | Bổ sung — không có trong bất kỳ mã nào trước đó |

Mã thật (`PERM0NN`) được cấp ở bước promote, không phải ở bản vẽ này — bảng trên chỉ ghi nhận ý
định, đúng quy tắc forward-draft (không tự đặt mã thật).
