---
status: draft
authored_by: takumi
created: 2026-09-10
lang: vi
promote_target: docs/system/permissions.md
promote_mode: append-section
---

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

| Mã (dự kiến) | Mô tả | Thay thế/bổ sung |
|---|---|---|
| `PERM016` | `secret_box_badge_odds_select_all` — đọc công khai tỷ lệ rút huy hiệu (`anon` + `authenticated`), không policy ghi | Bổ sung |
| `PERM017` | `secret_box_openings_select_own` — mỗi người chỉ đọc lịch sử mở hộp của chính mình, bắc qua `sunners.auth_user_id = auth.uid()` | Bổ sung |
| `PERM018` | `execute` trên `open_secret_box()` chỉ cấp cho `authenticated`; hàm là **người ghi duy nhất** của `sunners.secret_box_*` và `secret_box_openings` | Bổ sung — không thay mã nào |

F009 **không** thêm route guard nào: `/kudos/secret-box` giữ nguyên là route công khai theo hợp
đồng đã ratify của F004, và việc chặn "chưa đăng nhập thì không mở được" nằm ở tầng màn cộng với
`PERM018`, không nằm ở `proxy.ts`. Đây là lần đầu một ranh giới của dự án được thực thi **chỉ**
bằng grant trên hàm chứ không bằng redirect — đáng ghi lại, vì nó có nghĩa là kiểm thử phải bắn
thẳng vào RPC chứ không chỉ bấm nút.
