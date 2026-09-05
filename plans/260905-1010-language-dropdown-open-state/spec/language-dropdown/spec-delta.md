---
status: applied
fcode: F001
extends: docs/features/F001_Login, docs/screens/SCR001_Login
authored_by: takumi
created: 2026-09-05
lang: vi
---

# Spec delta — Dropdown ngôn ngữ, trạng thái mở (E02)

**Nguồn design:** MoMorph `hUyaaugye2` — "Dropdown-ngôn ngữ" (figma `721:4942`).
**Vì sao có delta:** F001_Login được viết khi design CHƯA vẽ trạng thái mở. Code hiện tại
dựng panel bằng giá trị tự chế (`bg-[#0B0F12]`, không viền, không phân biệt mục đang chọn).
Design giờ đã có, nên phần "TBD (draft)" trong SCR001 §7 được thay bằng hợp đồng thật.

## 1. Delta vào functional-spec.md (F001_Login)

**FR-203** giữ nguyên, bổ sung tiêu chí:

- **FR-203.a** Panel mở hiển thị ĐẦY ĐỦ danh sách locale (VN, EN), mỗi mục có cờ + nhãn.
- **FR-203.b** Mục ứng với locale đang chọn có nền phân biệt rõ so với mục còn lại.
- **FR-203.c** Panel thao tác được bằng bàn phím: ArrowDown/ArrowUp di chuyển giữa các mục,
  Home/End nhảy đầu/cuối, Enter hoặc Space chọn, Escape đóng và trả focus về trigger.

**US003_LanguageSelection** — thêm acceptance:

- [ ] Panel mở phân biệt được mục đang chọn bằng nền, không chỉ bằng thuộc tính ẩn.
- [ ] Mở panel rồi bấm lại trigger thì panel đóng (toggle).
- [ ] Điều hướng được toàn bộ panel bằng bàn phím, không cần chuột.

## 2. Delta vào SCR001_Login/spec.md

### §7 — thay `TBD (draft)` cho hai hàng dropdown

| Hành động | Element | Trigger | Điều kiện | Kết quả | Source |
|---|---|---|---|---|---|
| Mở/đóng dropdown ngôn ngữ | E02 | click trigger | — | Toggle panel; chevron xoay 180° khi mở | design `721:4942` |
| Chọn ngôn ngữ | E02 | click / Enter / Space trên mục | panel đang mở | Đổi ngôn ngữ toàn màn hình, panel đóng, focus về trigger | design `721:4942` |
| Di chuyển trong panel | E02 | ArrowDown / ArrowUp / Home / End | panel đang mở | Focus chạy vòng trong danh sách mục | clarifications.md |
| Đóng bằng Escape | E02 | Escape | panel đang mở | Panel đóng, locale không đổi, focus **trả về trigger** | clarifications.md |
| Đóng bằng click ngoài | E02 | pointerdown ngoài panel | panel đang mở | Panel đóng, locale không đổi, **không** giật focus về trigger — người dùng đang nhắm chỗ khác | clarifications.md |

### §9 (accessibility) — thay `[EXPECTED]` bằng hợp đồng

- ARIA: trigger `aria-haspopup="listbox"` + `aria-expanded`; panel `role="listbox"`;
  mỗi mục `role="option"` + `aria-selected`.
- Keyboard: đầy đủ theo FR-203.c.
- Focus: mở panel thì focus vào mục đang chọn. Đóng bằng Escape hoặc bằng cách chọn một
  mục thì trả focus về trigger; đóng bằng click ngoài thì KHÔNG giật focus về.

## 3. Hợp đồng thị giác (visual contract)

Đo trực tiếp từ node design — không suy đoán.

| Thành phần | Thuộc tính | Giá trị | Node |
|---|---|---|---|
| Panel | background | `#00070C` | `525:11713` |
| Panel | border | `1px solid #998C5F` | `525:11713` |
| Panel | border-radius | `8px` | `525:11713` |
| Panel | padding | `6px` | `525:11713` |
| Panel | layout | flex column | `525:11713` |
| Mục | kích thước | `108 × 56` px | `I525:11713;362:6085` |
| Mục | border-radius | `2px` | `I525:11713;362:6085` |
| Mục | nội dung | cờ 24px + gap 4px + nhãn, căn giữa | `...;186:1937` |
| Mục (đang chọn) | background | `rgba(255,234,158,0.2)` | `I525:11713;362:6085` |
| Mục (không chọn) | background | trong suốt | `I525:11713;362:6128` |
| Mục (hover) | background | `rgba(255,234,158,0.08)` | clarifications.md (design không cho token) |
| Nhãn | font | Montserrat 700, 16px/24px, letter-spacing 0.15px, trắng | `...;186:1439` |

**Vị trí panel:** thả xuống dưới trigger (`absolute top-full`), KHÔNG đè lên trigger —
quyết định của user, xem clarifications.md. Design dùng chung componentId `186:1692`
cho hàng VN và nút trigger, nhưng đó không phải ràng buộc bắt buộc.

## 4. Ngoài phạm vi

- Không thêm locale mới ngoài VN/EN.
- Không đổi cơ chế lưu locale (cookie `NEXT_LOCALE` giữ nguyên).
- Không đụng tới trigger đóng ngoài việc xoay chevron (đã có).

## 5. Câu hỏi chưa giải quyết

- Không có. Ba điểm mơ hồ đã được user chốt trong clarifications.md.
