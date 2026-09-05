---
status: draft
authored_by: takumi
created: 2026-09-05
lang: vi
---

# Mô hình phân quyền

> Bản nháp forward-draft, viết trước khi code (SDD). Sẽ được promote vào `docs/system/permissions.md`
> tại thời điểm bắt đầu implement, rồi đối chiếu lại với as-built ở Core pass sau khi forge.
> Mọi mã `PERM###` / `ROUTE###` / `SCR###` để `TBD (draft)` — máy cấp phát khi reconcile, không đoán.

## 1. Các chủ thể (principals)

| Principal | Nguồn xác định | Ghi chú |
|---|---|---|
| Khách vãng lai (anonymous) | Không có session Supabase | Mặc định của mọi request |
| Người dùng đã đăng nhập (authenticated) | Session Supabase hợp lệ, làm tươi ở `proxy.ts` | Đăng nhập qua Google OAuth (F001_Login) |
| Quản trị viên (admin) | `user.app_metadata.role === "admin"` | Xem mục 4 |

`app_metadata` do server ghi, client không sửa được — đó là lý do vai trò đọc từ đây chứ không phải
`user_metadata`. Dự án hiện chưa có bảng vai trò riêng; tạo schema mới chỉ để chứa một cờ là thừa (YAGNI).

## 2. Phạm vi bảo vệ tài nguyên

| Tài nguyên | Anonymous | Authenticated | Admin | Mã |
|---|---|---|---|---|
| `/` (Homepage SAA) | Cho phép | Cho phép | Cho phép | `TBD (draft)` |
| `/login` | Cho phép | Chuyển hướng về `/todo` | Chuyển hướng về `/todo` | `TBD (draft)` |
| `/todo` | Chuyển hướng về `/login` | Cho phép | Cho phép | `TBD (draft)` |
| `/auth/callback` | Cho phép (bắt buộc) | Cho phép | Cho phép | `TBD (draft)` |
| Các route placeholder (`/awards-information`, `/kudos`, `/standards`, `/profile`) | Cho phép | Cho phép | Cho phép | `TBD (draft)` |

Homepage là trang công khai. `proxy.ts` chỉ chặn đúng hai tiền tố `/todo` và `/login`; mọi đường dẫn
khác đi thẳng — không thêm luật chặn nào cho `/` trong phạm vi này.

## 3. Hiển thị theo trạng thái đăng nhập (UI-level, không phải kiểm soát truy cập)

Trên header của Homepage:

- Chuông thông báo và nút tài khoản **chỉ render khi có session**. Khách vãng lai không thấy chúng.
- Đây là quyết định về hiển thị, không phải hàng rào bảo mật: chúng không bảo vệ dữ liệu nào cả,
  vì bản thân panel thông báo hiện là trạng thái rỗng và menu tài khoản chỉ chứa liên kết điều hướng.

## 4. Cổng vai trò admin

Mục "Admin Dashboard" trong menu tài khoản chỉ hiện khi **cả hai** điều kiện đúng: có session, và
`app_metadata.role === "admin"`.

Ranh giới cần nói rõ: đây mới chỉ là **ẩn/hiện một liên kết**. Trang `/admin` (chưa tồn tại trong
phạm vi này) khi được xây phải tự kiểm tra vai trò ở phía server — ẩn liên kết không phải là bảo vệ
route, và không được coi là đã bảo vệ.

## 5. Điểm chưa giải quyết

- Chưa có nguồn dữ liệu thông báo, nên chưa có luật phân quyền nào cho việc đọc/đánh dấu thông báo.
- Chưa có seed vai trò admin trong Supabase local (cần `service_role` key mà repo cố ý không giữ),
  nên nhánh admin chưa được phủ bởi E2E — xem `ORCH-03` trong `clarifications.md`.
