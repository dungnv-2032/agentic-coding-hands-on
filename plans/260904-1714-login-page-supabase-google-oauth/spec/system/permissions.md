---
status: draft
authored_by: takumi
created: 2026-09-04
lang: vi
---

# Permissions — Login (Supabase Google OAuth)

## Mô hình phân quyền

Tính năng này chỉ đưa vào MỘT lằn ranh phân quyền: **đã đăng nhập** hay **chưa đăng nhập**, xác định bằng phiên Supabase Auth (cookie session, refresh qua `proxy.ts`). Chưa có role/nhóm nào khác (admin, member, v.v.) — mọi tài khoản Google hợp lệ đều là cùng một loại người dùng, không có domain allow-list. Authorization System Type cho tính năng này: `other` — chỉ có kiểm tra "có phiên hay không", chưa phải RBAC/ABAC/ACL/ownership thật sự.

## Route guards

| Guard | Type | Route(s) | Condition | Consequence if bypassed |
|---|---|---|---|---|
| Chặn `/todo` khi chưa đăng nhập | route-guard | `/todo` | không có phiên Supabase hợp lệ | Điều hướng về `/login` — không có nội dung nào của `/todo` lộ ra trước khi điều hướng xảy ra (guard chạy trong `proxy.ts`, trước khi trang render) |
| Chặn `/login` khi đã đăng nhập | route-guard | `/login` | có phiên Supabase hợp lệ | Điều hướng về `/todo` — người dùng không thấy lại form đăng nhập |

Cả hai guard cùng nằm trong `proxy.ts` (mở rộng từ `updateSession` hiện có), không phải hai cơ chế tách biệt. `PERM###` cho từng guard: `TBD (draft)` — mã chính thức cấp khi promote.

## Client-side gates

| Gate | Type | Value(s) observed | Effect | Source |
|---|---|---|---|---|
| Ngôn ngữ hiển thị | locale-gate | cookie `NEXT_LOCALE` = `vi` \| `en`, mặc định `vi` khi thiếu | Chọn từ điển vi/en cho toàn bộ nội dung tĩnh của `/login` | `TBD (draft)` |

Không phát hiện (và không dự kiến thêm) `feature-flag`, `experiment`, hay `env-gate` nào cho tính năng này.

## Ngoài phạm vi

- Không có `screen-permission`/`action-permission`/`data-permission`/`field-permission` nào trong tính năng này — màn hình Login không có nội dung nào ẩn/hiện theo vai trò, và trang `/todo` chỉ là placeholder.
- Không có `api-scope` (OAuth scope) nào được yêu cầu ngoài phạm vi cơ bản mà Supabase Auth tự xin từ Google cho việc xác thực (không xin thêm scope truy cập dữ liệu Google của người dùng).
- Vai trò/nhóm người dùng (RBAC) chưa tồn tại trong hệ thống — sẽ chỉ xuất hiện khi tính năng to-do thật (ngoài phạm vi tài liệu này) định hình nhu cầu phân quyền theo dữ liệu.

## Chưa xác nhận

- `source:` (file:line) cho gate ngôn ngữ ở trên — chưa có code, sẽ điền khi promote/rebuild-spec chạy trên code thật.
