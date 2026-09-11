# Clarifications — Dropdown Hashtag filter (MoMorph `JWpsISMAaM`)

**MoMorph refs**
- Dropdown Hashtag filter: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/JWpsISMAaM
- Parent screen: SCR004 Kudos Live Board (`/kudos`), feature F004
- specs: 4 design items (A, A.1, A.2, A.3) — `spec_status: done`, `design_status: done`
- test cases: none published for this frame (0 rows)
- testPolicy: `e2e-red-first`

**Standing authority.** User granted auto-resolution: "nếu có vấn đề gì cần confirm với tôi,
tự động triển khai theo hướng câu trả lời đầu tiên, Yes hoặc câu trả lời Recommend mà ko cần
confirm tôi." Mọi quyết định dưới đây lấy phương án Recommended, không hỏi chặn.

## Session 2026-09-11

- Q: Frame này là dropdown rời, không phải route. Nó thuộc màn hình nào? → A: **Là trạng thái
  mở của nút lọc `Hashtag` đã có trên `/kudos` (F004/SCR004), dựng bởi
  `app/kudos/_components/kudos-filter-menu.tsx`.** Rationale: header file đó đã ghi
  `mm:563:8026 (mms_A_Dropdown-List, JWpsISMAaM/WXK5AYB_rG)` — `JWpsISMAaM` chính là frame
  này. Không route mới, không `F###` mới; đây là delta của F004, giữ dãy feature-code liền mạch.

- Q: Phần lớn hành vi (click → chọn + đóng + lọc toàn trang, click lại → bỏ chọn) đã chạy
  trong code. Vậy việc thật còn lại là gì? → A: **Một điểm lệch frame chưa dựng — listbox
  hashtag chưa có hộp cuộn — cộng với việc khoá hành vi đã có bằng e2e (chưa test nào
  khẳng định phía hashtag).** Rationale: spec A ghi rõ "Scroll: danh sách cuộn khi vượt quá
  chiều cao"; 13 hàng × 56px = 728px không có `max-h` nào chặn, listbox đổ dài quá khung nhìn.

- Q: Hộp cuộn của hashtag cao bao nhiêu? → A: **Đúng `max-h-[348px]` như listbox Phòng ban.**
  Rationale: cùng một instance Figma `mms_A_Dropdown-List`, cùng chiều cao artboard 348px;
  ảnh frame hashtag cũng hiện đúng 6 hàng. Con số 348 = 6×56 + 6×2 padding, đã đo và ratify
  ở plan `260911-1348-dropdown-phong-ban` (FR-213). Dùng lại, không đo lại, không bịa số khác.

- Q: `scrollable` đang là prop bật/tắt theo listbox. Có nên bật cho cả hai, hay bỏ prop? → A:
  **Bỏ prop `scrollable`, hộp cuộn thành mặc định của component.** Rationale: cả hai frame
  (`JWpsISMAaM`, `WXK5AYB_rG`) đều yêu cầu cuộn; giữ một cờ chỉ để bật cho cả hai chỗ gọi là
  điều kiện chết — KISS/DRY. `max-h` không cắt danh sách ngắn hơn 6 hàng nên không có rủi ro.

- Q: Spec A.1 ghi "Hover/focus: hiển thị glow" — có dựng thêm gì không? → A: **Giữ nguyên nền
  hover `rgba(255,234,158,0.05)` đang có và thêm glow khi focus bàn phím
  (`focus-visible`), dùng lại đúng token `#FAE287` của trạng thái selected.** Rationale: hover
  đã được ratify ở phiên trước (KISS, "nhẹ"); focus hiện chỉ có outline mặc định của trình
  duyệt, tức là frame nói "focus → glow" mà code chưa có. Token lấy từ chính component, không
  đoán màu mới.

- Q: "Mục đã chọn: ô nổi, nền tối, viền/hiệu ứng sáng" — có đổi token màu selected không? → A:
  **Không. Giữ `bg-[rgba(255,234,158,0.10)]` + `[text-shadow:0_0_6px_#FAE287]`.** Rationale:
  đã ratify ở phiên trước cho cùng component; đổi là đoán, vi phạm rule "không đoán giá trị
  hình ảnh".

- Q: Ảnh frame hiển thị nhãn dạng `#Dedicated` (có dấu `#`), code đang hiển thị tên thuần
  (`Cống hiến`). Có đổi nhãn không? → A: **Không.** Rationale: chính spec A liệt kê "Danh sách
  13 hashtag trong dropdown: Toàn diện / Giỏi chuyên môn / …" — đúng tên trong
  `public.hashtags`. `#Dedicated`, `#Inspring` là placeholder tiếng Anh của bản dựng Figma;
  danh sách 13 tên tiếng Việt mới là dữ liệu thật, và K-3 đã khẳng định đúng thứ tự đó.

- Q: Dữ liệu hashtag lấy từ đâu? → A: **Supabase local đang chạy — `public.hashtags`
  (13 dòng, `ORDER BY position`), đọc qua `fetchFilterOptions()` như hiện tại.** Rationale:
  user chỉ định "use Supabase local project"; đường đọc đã có và đã được K-3 khẳng định.
  Không hardcode, không migration mới.

- Q: Hashtag nào dùng làm dữ liệu khẳng định trong e2e? → A: **`Wasshoi`** — seed local có 8/69
  kudos mang tag này, nên board hẹp lại rõ ràng mà vẫn còn card để kiểm tra; và nó nằm ở
  position 8, tức **nằm ngoài 6 hàng đầu**, nên chọn được nó cũng là bằng chứng hộp cuộn hoạt
  động chứ không cắt mất option.
