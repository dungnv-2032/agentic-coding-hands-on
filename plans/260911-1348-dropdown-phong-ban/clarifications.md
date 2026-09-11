# Clarifications — Dropdown Phòng ban (MoMorph `WXK5AYB_rG`)

**MoMorph refs**
- Dropdown Phòng ban: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/WXK5AYB_rG
- Parent screen: SCR004 Kudos Live Board (`/kudos`), feature F004
- specs: 4 design items (A, A.1, A.2, A.3) — `spec_status: done`
- test cases: none published for this frame (0 rows)
- testPolicy: `e2e-red-first`

**Standing authority.** User granted auto-resolution: "nếu có vấn đề gì cần confirm với tôi,
tự động triển khai theo hướng câu trả lời đầu tiên, Yes hoặc câu trả lời Recommend mà ko cần
confirm tôi." Every decision below is taken on the Recommended option without a blocking
question.

## Session 2026-09-11

- Q: Frame này là dropdown rời, không phải một route. Nó thuộc màn hình nào? → A: **Là trạng
  thái mở của nút lọc `Phòng ban` đã có trên `/kudos` (F004/SCR004), dựng bởi
  `app/kudos/_components/kudos-filter-menu.tsx`.** Rationale: file đó đã ghi
  `mm:563:8026 (mms_A_Dropdown-List, JWpsISMAaM/WXK5AYB_rG)` trong header — frame này chính
  là component nó đang render. Không route mới, không `F###` mới; đây là delta của F004,
  giữ dãy feature-code liền mạch.

- Q: Phần lớn hành vi trong spec (click → chọn + đóng + lọc toàn trang, click lại → bỏ lọc)
  đã chạy trong code nhưng **chưa có test nào chứng minh**. Vậy công việc thật là gì? → A:
  **Khoá hành vi đã có bằng e2e trước (RED thật trên các khẳng định chưa tồn tại), rồi sửa ba
  điểm lệch frame còn lại: text căn giữa, `cursor: pointer`, chiều cao hộp 348px.**
  Rationale: `momorph-development.md` bắt `e2e-red-first` khi spec chứa chuyển trạng thái;
  RED hợp lệ ở đây đến từ FR-208/209/213 (chưa dựng) cộng FR-210/211/212 (chưa có testid để
  khẳng định), không phải từ lỗi cấu hình.

- Q: `kudos-filter-menu.tsx` dùng chung cho listbox Hashtag và listbox Phòng ban. Đổi căn giữa
  + pointer có làm hỏng listbox Hashtag không? → A: **Đổi chung, coi là đúng thiết kế.**
  Rationale: header của file đã dẫn cả `JWpsISMAaM` (hashtag) lẫn `WXK5AYB_rG` (phòng ban) về
  **cùng một** instance Figma `mms_A_Dropdown-List` — cùng component thì cùng hình thức. Tách
  đôi style theo `testId` sẽ là bịa ra khác biệt mà thiết kế không có.

- Q: "Mục đã chọn trong ô nổi, nền sáng" — có đổi token màu của trạng thái selected không? → A:
  **Không. Giữ `bg-[rgba(255,234,158,0.10)]` + `[text-shadow:0_0_6px_#FAE287]` đang có.**
  Rationale: ảnh frame cho thấy đúng hiệu ứng ô sáng + chữ phát sáng vàng mà cặp token này
  đang tạo ra; đổi sang giá trị khác là đoán, vi phạm rule 1 (không đoán giá trị hình ảnh).

- Q: "Hover hiển thị hiệu ứng nổi nhẹ" nên dựng bằng gì? → A: **Giữ nền hover
  `rgba(255,234,158,0.05)` đang có và thêm `transition-colors` cho nó chuyển mượt.**
  Rationale: KISS — spec nói "nhẹ"; thêm `translate`/`shadow` là dựng thêm chuyển động mà
  frame tĩnh không đo được.

- Q: Hộp 101x348px của frame ánh xạ thế nào sang listbox rộng 256px trên web? → A: **Chỉ lấy
  chiều cao: `max-h-[348px]`, hàng cao 56px, bỏ `gap-1`, giữ `p-[6px]` → đúng 6 hàng hiện ra
  như frame, phần dư cuộn trong hộp.** Rationale: 6×56 + 6×2 = 348 khớp tuyệt đối, nên
  348px là con số đo được chứ không phải làm tròn; chiều rộng 101px là bề rộng artboard của
  frame rời, không phải bề rộng trong ngữ cảnh trang.

- Q: Dữ liệu phòng ban lấy từ đâu? → A: **Supabase local đang chạy — `public.departments`
  (52 dòng, 50 dòng có `filter_position`), đọc qua `fetchFilterOptions()` như hiện tại.**
  Rationale: user chỉ định "use Supabase local project"; đường đọc đã có sẵn và đã được K-3
  khẳng định đúng 50 option. Không hardcode, không migration mới.

- Q: Phòng ban nào dùng làm dữ liệu khẳng định trong e2e? → A: **`STVC - R&D`** — seed local
  có 12 kudos nhận bởi Sunner thuộc phòng ban này trên tổng 69, nên lọc xong board hẹp lại
  rõ ràng mà vẫn còn card để kiểm tra (khác với các phòng ban chỉ có 1 kudos).
