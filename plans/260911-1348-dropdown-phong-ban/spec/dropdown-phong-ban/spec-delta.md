---
status: draft
authored_by: takumi
created: 2026-09-11
lang: vi
feature: F004_KudosLiveBoard
screen: SCR004_KudosLiveBoard
momorph: WXK5AYB_rG
---

# Spec delta — Dropdown Phòng ban (MoMorph `WXK5AYB_rG`)

Delta trên F004 (Kudos Live Board). Không tạo F-code mới: dropdown Phòng ban là một phần
của bộ lọc đã có trong FR-203, frame này chỉ nói rõ hành vi và hình thức của **listbox**
khi nó mở.

## 1. Nguồn yêu cầu

- MoMorph specs `WXK5AYB_rG` (4 item, tải 2026-09-11):
  - **A** `mms_A_Dropdown-List` — "Dropdown chọn phòng ban; 'CEVC2' đang được chọn.
    Display: khung dọc bo góc, nền tối (101x348px); mục đã chọn trong ô nổi, nền sáng.
    Function: click chọn mục và đổi highlight; hover hiển thị hiệu ứng nổi nhẹ."
    Kèm danh sách 50 phòng ban lọc được.
  - **A.1 / A.2 / A.3** `mms_A.{1,2,3}_Phòng ban {1,2,3}` — "Display: Text căn giữa.
    Function: Click → chọn và **đóng dropdown**, áp dụng filter cho **toàn trang**
    (lọc ra các lời cảm ơn đến người thuộc phòng ban này). Hover → **con trỏ pointer**,
    giữ hiệu ứng highlight. State → active/selected hiển thị highlight."
- MoMorph test cases `WXK5AYB_rG`: **rỗng** (0 dòng). Test contract nằm ở phase 01.

## 2. Hiện trạng (đọc từ code, 2026-09-11)

`app/kudos/_components/kudos-filter-menu.tsx` đã dựng listbox và
`kudos-board.tsx` đã nối `departmentFilterId` vào `matchesFilters()`, nên
**click → lọc toàn trang** và **click lại → bỏ lọc** đã chạy. Chưa có test nào chứng
minh điều đó: `kudos-live-board.spec.ts` chỉ có K-3 (đếm 50 option) và K-8 (reset
carousel). Về hình thức, listbox đang lệch frame ở ba điểm: text căn trái, không có
`cursor: pointer` (mặc định của `<button>` là `default`), và hộp cuộn cao 320px thay vì
348px (6 dòng đúng bằng frame).

## 3. Yêu cầu chức năng (delta)

- **FR-208** Mỗi option trong dropdown Phòng ban hiển thị tên phòng ban **căn giữa**.
- **FR-209** Khi hover, option đổi con trỏ thành **pointer** và giữ hiệu ứng highlight nền.
- **FR-210** Click một option **đóng dropdown ngay** và áp filter lên **cả HIGHLIGHT KUDOS
  lẫn ALL KUDOS**: chỉ còn kudos gửi đến Sunner thuộc phòng ban đó.
- **FR-211** Option đang chọn mang highlight bền: mở lại dropdown vẫn thấy nó
  `aria-selected="true"` và có nền sáng + glow.
- **FR-212** Click lại chính option đang chọn sẽ **bỏ lọc**, board trở về đầy đủ.
- **FR-213** Hộp dropdown Phòng ban cao tối đa **348px** (đúng 6 dòng 56px + 6px padding
  trên/dưới của frame), phần còn lại cuộn trong hộp — không đẩy layout trang.

## 4. Ngoài phạm vi

Không đổi schema, migration, RLS, Server Action hay route. `getKudosBoard()`,
`fetchFilterOptions()`, `matchesFilters()` giữ nguyên. Không thêm filter vào URL.
Không đổi trigger button (`filter-department`), chỉ đổi listbox.

## 5. Ràng buộc

- `kudos-filter-menu.tsx` dùng chung cho cả hashtag lẫn phòng ban, và cả hai frame trỏ về
  cùng một component Figma `mms_A_Dropdown-List` — nên FR-208/FR-209 áp cho cả hai
  listbox, đúng thiết kế, không phải tác dụng phụ.
- Danh sách 50 phòng ban lấy từ `public.departments` (Supabase local, `filter_position`
  NOT NULL), không hardcode.
- File chạm vào phải dưới 200 dòng.
