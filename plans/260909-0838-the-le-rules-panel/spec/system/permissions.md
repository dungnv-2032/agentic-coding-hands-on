---
status: draft
authored_by: takumi
created: 2026-09-09
lang: vi
target: docs/system/permissions.md
mode: forward-draft (append/amend — not a replacement)
---

# Forward-draft — permissions, vòng F007 (Thể lệ)

Bản này là phần F007 cần được HỢP vào `docs/system/permissions.md` khi promote. Nó **bổ sung**,
không thay thế phần F001–F006 đã có ở đó.

## Append — vào § Access Boundaries

**`/standards` là route công khai, và đó là quyết định có chủ đích.** `proxy.ts` canh `/todo`,
`/kudos/new` (khớp chính xác) và `/profile`; `/standards` không nằm trong danh sách và không được thêm
vào. Thể lệ chương trình là thứ người chưa đăng nhập cần đọc *trước* khi quyết định tham gia — đặt nó
sau tường đăng nhập sẽ đảo ngược thứ tự đó.

**Hai bảng mới chỉ đọc được, cho cả `anon` lẫn `authenticated`.** `public.rule_sections` và
`public.rule_items` theo đúng khuôn `kudos_select_all` mà F004 đặt ra và `docs/system/permissions.md`
đã ghi là tiền lệ ràng buộc:

```sql
alter table public.rule_sections enable row level security;
create policy "rule_sections_select_all" on public.rule_sections
  for select to anon, authenticated using (true);
grant select on public.rule_sections to anon, authenticated;
```

— và y hệt cho `rule_items`. **Không có policy `insert`/`update`/`delete` nào**, nên RLS từ chối mặc
định: im lặng chính là từ chối, không cần viết policy deny thừa. Không có Server Action nào trên màn
này, nên cũng không tồn tại con đường ghi nào từ phía ứng dụng.

Điều này an toàn được vì nội dung thể lệ **không có biến thiên theo người xem**: mọi người đọc đúng
cùng một chữ. Không cần masked view kiểu `kudos_readable` (F006) — đó là cơ chế cho dữ liệu mà *ai đang
hỏi* làm đổi *câu trả lời*, và không có gì như thế ở đây. Dựng một view che cho nội dung tĩnh là chi
phí không mua được gì.

**Sửa nội dung thể lệ hiện chỉ làm được qua migration/seed.** Không có bề mặt quản trị, và `/admin`
vẫn không có authorization boundary thật (không đổi ở vòng này). Nếu sau này có màn admin sửa thể lệ,
nó phải mang theo policy ghi **và** một kiểm tra vai trò phía server — cả hai đều chưa tồn tại, và
không được mở sẵn quyền cho một màn chưa có.

## Append — § Mã `PERM###` dự kiến của vòng F007

| Mã (dự kiến) | Mô tả | Thay thế/bổ sung |
|---|---|---|
| `PERM014` | `rule_sections_select_all` — đọc công khai nội dung thể lệ (`anon` + `authenticated`) | Bổ sung |
| `PERM015` | `rule_items_select_all` — đọc công khai danh sách huy hiệu/icon (`anon` + `authenticated`) | Bổ sung |

Mã thật được cấp ở bước promote/rebuild-spec, không phải ở trang này. Các **grant** mà hai mã này mô
tả thì đi cùng migration của F007 và đo được ngay sau `supabase db reset`.
