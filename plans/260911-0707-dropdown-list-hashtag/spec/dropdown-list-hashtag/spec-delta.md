---
status: draft
authored_by: takumi
created: 2026-09-11
lang: vi
promotes_to:
  - docs/features/F005_VietKudo/functional-spec.md
  - docs/features/F005_VietKudo/technical-spec.md
  - docs/screens/SCR005_VietKudo/spec.md
momorph_screen: p9zO-c4a4x
---

# Spec delta — Dropdown list hashtag (E13)

Amendment to F005 / SCR005. Không phải feature mới: frame `p9zO-c4a4x` là **trạng thái mở của
E13** (`data-testid="hashtag-menu"`) đã khai báo sẵn trong SCR005 § 4, dòng E13 ghi rõ "nguồn dữ
liệu companion frame `p9zO-c4a4x`". Delta này chỉ định nghĩa hành vi bên trong danh sách đó.

## Điều gì đổi

E13 hiện tại là danh sách **chỉ-thêm**: bấm một dòng thì thêm hashtag, bấm lại không gỡ, dòng nào
cũng bấm được kể cả khi đã đủ 5. Frame `p9zO-c4a4x` mô tả một danh sách **đa chọn có trạng thái**:
mỗi dòng mang trạng thái selected/unselected nhìn thấy được, bấm để bật/tắt, và khi đủ 5 thì các
dòng chưa chọn ngừng phản hồi.

## Yêu cầu chức năng bổ sung

- **FR-207** Mỗi dòng trong E13 hiển thị trạng thái đã chọn của chính nó: nền nổi
  `rgba(255,234,158,0.2)` + icon check tròn 24×24 bên phải (`mm:1002:13185`, `mm:1002:13204`).
  Dòng chưa chọn không có nền nổi và giữ một khoảng trống 24×24 đúng chỗ icon, để danh sách không
  xô lệch khi trạng thái đổi (`mm:1002:13104`, item A.2 verbatim).
- **FR-208** Bấm một dòng **đã chọn** sẽ gỡ hashtag đó khỏi danh sách đã chọn — icon check biến
  mất, nền trở lại bình thường, và chip tương ứng ở E14 biến mất. Bấm một dòng **chưa chọn** thêm
  hashtag đó như cũ (items A/B/C/D `userAction`).
- **FR-209** Khi đã chọn đủ 5 hashtag, mọi dòng **chưa chọn** bị vô hiệu hoá: mờ đi, `disabled`,
  không phản hồi click (item D `validationNote`). Các dòng **đã chọn** vẫn bấm được — đó là lối
  thoát duy nhất khỏi trạng thái đầy.
- **FR-210** Khi đã chọn đủ 5 hashtag, E15 (`hashtag-error`) hiển thị "Tối đa 5 hashtag" như lý do
  thường trực của trạng thái vô hiệu hoá ở FR-209, và ẩn đi ngay khi số hashtag tụt xuống dưới 5.
- **FR-211** Danh sách giữ nguyên thứ tự `public.hashtags.position` từ Supabase; chọn hay bỏ chọn
  không sắp xếp lại dòng nào.

## Business rule chịu ảnh hưởng

- **BR-002** (tối đa 5) không đổi về nội dung, đổi về cách ép: trước đây chặn tại cú click thứ 6
  rồi báo lỗi; từ nay chặn bằng cách vô hiệu hoá dòng chưa chọn, và "Tối đa 5 hashtag" là lời giải
  thích thường trực thay vì phản ứng tức thời. Reducer `compose-state.ts` vẫn giữ nguyên guard
  `MAX_HASHTAGS` làm lớp phòng thủ thứ hai — không dòng code nào tin vào riêng giao diện.

## Acceptance criteria

- [ ] Mở E13 khi chưa chọn gì: mọi dòng ở trạng thái unselected, không dòng nào có icon check.
- [ ] Bấm một dòng chưa chọn: dòng đó chuyển sang selected (nền nổi + icon check), một chip mới
      xuất hiện ở E14.
- [ ] Bấm lại đúng dòng đó: dòng trở về unselected, chip tương ứng biến mất, các chip khác nguyên vẹn.
- [ ] Chọn đủ 5: mọi dòng chưa chọn `disabled`, E15 hiện "Tối đa 5 hashtag", số chip vẫn là 5 sau
      khi cố bấm một dòng chưa chọn.
- [ ] Ở trạng thái đủ 5, bấm một dòng **đã chọn** vẫn gỡ được — số chip còn 4, các dòng chưa chọn
      bấm lại được, E15 biến mất.
- [ ] Thứ tự dòng khớp `public.hashtags.position` của Supabase local và không đổi qua các lần toggle.

## Ngoài phạm vi

- Không thêm route, bảng, migration hay Server Action nào. Đường đọc `getComposeOptions()` giữ nguyên.
- Không đổi hành vi đóng/mở menu (vẫn đóng sau mỗi lần toggle) — frame không nói gì về điểm này.
- Không hoisting dòng đã chọn lên đầu danh sách.

## Promote mapping (applied 2026-09-11)

`FR-207` was already taken in `docs/features/F005_VietKudo/functional-spec.md` (checkbox ẩn danh),
so the delta's draft-local IDs were shifted by one when promoted. Draft → promoted:

| Draft (this file) | Promoted into docs |
|---|---|
| FR-207 (trạng thái selected của dòng) | **FR-208** |
| FR-208 (toggle bật/tắt) | **FR-209** |
| FR-209 (disable dòng chưa chọn khi đủ 5) | **FR-210** |
| FR-210 (lỗi thường trực "Tối đa 5 hashtag") | **FR-211** |
| FR-211 (giữ thứ tự `position`) | **FR-212** |

Promoted into: `docs/features/F005_VietKudo/functional-spec.md` (FR-208..FR-212, BR-002 reworded,
US002 acceptance criteria), `docs/features/F005_VietKudo/technical-spec.md` (§ 3.2, A1 row, BR-002),
`docs/screens/SCR005_VietKudo/spec.md` (E13 + new E13.1/E13.2, interaction + validation rows).
