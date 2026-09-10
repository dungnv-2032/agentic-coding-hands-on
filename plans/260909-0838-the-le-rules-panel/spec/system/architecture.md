---
status: draft
authored_by: takumi
created: 2026-09-09
lang: vi
target: docs/system/architecture.md
mode: forward-draft (append/amend — not a replacement)
---

# Forward-draft — architecture, vòng F007 (Thể lệ)

Bản này là phần F007 cần được HỢP vào `docs/system/architecture.md` khi promote. Nó **bổ sung**,
không thay thế phần F001–F006 đã có ở đó.

## Amend — dòng mô tả phạm vi ở đầu file

`**Project**: my-app (SAA 2025) — mô tả tới F006 (Profile bản thân).`
→ `**Project**: my-app (SAA 2025) — mô tả tới F007 (Thể lệ).`

## Append — vào § System Architecture, sau đoạn "Thay đổi của vòng F005"

**Thay đổi của vòng F007 (Thể lệ):** cho tới F006, mọi thứ nằm trong Postgres đều là **dữ liệu giao
dịch** — người, Kudos, tim, hashtag, sự kiện ticker. Nội dung biên tập thì hardcode trong `lib/`:
`/awards-information` đọc `lib/awards.ts` và `lib/award-system.ts`, hai file TypeScript. F007 là lần
đầu **nội dung biên tập được đưa vào database**: `public.rule_sections` (ba mục văn xuôi có thứ tự) và
`public.rule_items` (bốn bậc huy hiệu Hero + sáu icon sưu tập, phân biệt bằng cột `kind`).

Hệ quả kiến trúc, nói thẳng vì nó tạo tiền lệ: repo giờ có **hai** chỗ hợp lệ để nội dung màn hình
sống — `lib/*.ts` (F003) và bảng Postgres (F007) — và không có luật nào trong repo phân xử chỗ nào
đúng cho màn tiếp theo. F007 chọn database vì commission yêu cầu tường minh ("use Supabase local
project"), không vì một nguyên tắc đã được thống nhất. Ai đóng khoảng trống này nên đóng bằng một
quyết định được ghi lại, không bằng cách bắt chước màn gần nhất.

Điều F007 **không** mang vào, ghi lại để không phải tìm: không Server Action, không thao tác ghi,
không Storage bucket. Ảnh huy hiệu và icon nằm trên đĩa dưới `public/images/rules/`, dòng database chỉ
giữ đường dẫn (`image_path`) — cùng cách mọi màn khác đối xử với asset Figma của nó.

## Append — vào § Data Layer / Read path (chỗ mô tả `lib/kudos`, `lib/profile`)

`lib/rules/` theo đúng khuôn đã có: `queries.ts` chỉ chứa read có kiểu (client luôn là tham số, không
bao giờ tạo bên trong), `rules-data.ts` là orchestrator tạo một client mỗi request rồi bắn hai read độc
lập qua một `Promise.all`, `view-model.ts` giữ shape đóng băng mà component tiêu thụ. Dòng database
không chạm tới component — cùng ranh giới `board-data.ts` và `profile-data.ts` đã dựng.

Mọi query của feature này mang `order by position` tường minh. Đây là idiom sẵn có (`hashtags.position`,
`departments.filter_position`, `kudos_hashtags.position`), không phải quy ước mới.

## Append — vào § Deployment View, sau đoạn về bước schema

Bước schema của F007 mang thêm một ràng buộc mà F004–F006 không có: `supabase/seed.sql` từ nay chứa
**nội dung sản phẩm** (chữ thể lệ hiển thị cho người dùng), không chỉ dữ liệu dev/test. Câu "seed là dữ
liệu dev/test, không phải dữ liệu production" ở trên vì thế **không còn đúng trọn vẹn**: các dòng
`rule_sections`/`rule_items` cần có mặt ở mọi môi trường thì màn `/standards` mới có gì để hiển thị.
Repo vẫn chưa có nơi nào mô tả cách nội dung đó tới được môi trường thật — khoảng trống đã ghi nhận, và
F007 làm nó rộng thêm chứ không thu hẹp.
