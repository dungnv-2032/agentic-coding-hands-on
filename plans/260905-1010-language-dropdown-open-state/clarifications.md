# Clarifications — Dropdown ngôn ngữ (open state)

- **Screen:** Dropdown-ngôn ngữ — https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/hUyaaugye2
- **fileKey:** `9ypp4enmFmdK3YAFJLIu6C` · **screenId:** `hUyaaugye2` · **figma node:** `721:4942`
- **Parent feature:** F001_Login (docs/features/F001_Login) — extends the E02 language selector
- **testPolicy:** `e2e-red-first`

## Session 2026-09-05

- Q: Khi mở, panel dropdown đặt ở đâu so với trigger? → A: **Thả xuống dưới trigger** — trigger vẫn hiện với chevron xoay, panel rơi xuống dưới. Ràng buộc: giữ `absolute top-full` hiện tại; KHÔNG đè lên trigger dù design dùng chung componentId `186:1692` cho hàng VN và nút trigger.
- Q: Màu hover cho option chưa chọn (spec nói "hover đổi nền", design không cho token)? → A: **`rgba(255,234,158,0.08)`** — cùng hệ màu với nền selected `rgba(255,234,158,0.2)`. Ràng buộc: bỏ `hover:bg-white/10` trong danh sách option.
- Q: Thêm điều hướng bàn phím cho listbox? → A: **Có** — ArrowUp/ArrowDown/Home/End + Enter/Space, giữ Escape và click ngoài. Lý do: đã khai báo `role="listbox"` nên screen reader kỳ vọng mũi tên hoạt động; thiếu là lỗi a11y thật.

## Resolved from design data (không hỏi user — scout-first)

- Container panel: `background #00070C`, `border 1px solid #998C5F`, `border-radius 8px`, `padding 6px`, flex column.
- Option row: `108x56`, `border-radius 2px`, icon 24px + gap 4px + label, nội dung căn giữa (đo được padding trái 27px / phải 28px).
- Label: Montserrat 700, `16px/24px`, `letter-spacing 0.15px`, màu trắng.
- Selected row background: `rgba(255,234,158,0.2)`.
- Chevron KHÔNG xuất hiện trong hàng của panel (node tree hàng VN chỉ có IC + TEXT) — nhưng theo quyết định trên, trigger giữ chevron riêng.
