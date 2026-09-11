---
status: draft
authored_by: takumi
created: 2026-09-11
lang: vi
feature: F004_KudosLiveBoard
screen: SCR004_KudosLiveBoard
momorph: JWpsISMAaM
---

# Spec delta — Dropdown Hashtag filter (MoMorph `JWpsISMAaM`)

Delta trên F004 (Kudos Live Board). Không tạo F-code mới: dropdown Hashtag là một phần của bộ
lọc đã có trong FR-203; frame này nói rõ hành vi và hình thức của **listbox hashtag** khi mở.
Nó là frame anh em của `WXK5AYB_rG` (Phòng ban) — cùng một instance Figma
`mms_A_Dropdown-List`, nên mọi yêu cầu ở đây áp cho component dùng chung.

## 1. Nguồn yêu cầu

- MoMorph specs `JWpsISMAaM` (4 item, tải 2026-09-11):
  - **A** `mms_A_Dropdown-List` — "Danh sách dropdown để lọc hashtag. Hiển thị: mục được chọn
    (ô nổi, nền tối, viền/hiệu ứng sáng); các mục khác là dòng text. Chức năng: **click mục →
    chọn giá trị, đóng dropdown và áp dụng filter với toàn bộ trang**; **scroll: danh sách cuộn
    khi vượt quá chiều cao**. State selected: nền nổi + chữ sáng." Kèm danh sách **13 hashtag**:
    Toàn diện, Giỏi chuyên môn, Hiệu suất cao, Truyền cảm hứng, Cống hiến, Aim High, Be Agile,
    Wasshoi, Hướng mục tiêu, Hướng khách hàng, Chuẩn quy trình, Giải pháp sáng tạo,
    Quản lý xuất sắc.
  - **A.1** `mms_A.1_Tag1` — "Mục 131x56px. Selected: nền tối + glow. **Click: toggle
    chọn/bỏ chọn** và áp bộ lọc. **Hover/focus: hiển thị glow**."
  - **A.2** `mms_A.2_Tag2` — "Click: chọn làm bộ lọc, hiển thị trạng thái selected.
    Hover: nền sáng nhẹ. State: Default và Selected."
  - **A.3** `mms_A.3_Tag3` — "Click: chọn mục và **đóng dropdown** (áp bộ lọc).
    State: Selected."
- MoMorph test cases `JWpsISMAaM`: **rỗng** (0 dòng). Test contract nằm ở phase 01.

## 2. Hiện trạng (đọc từ code, 2026-09-11)

`kudos-filter-menu.tsx` đã dựng listbox dùng chung; `kudos-filter-bar.tsx` mở/đóng nó;
`kudos-board.tsx` nối `hashtagFilterId` vào `matchesFilters()`. Nên **click → lọc toàn trang →
đóng dropdown** và **click lại → bỏ lọc** đã chạy cho hashtag. Text căn giữa và `cursor: pointer`
đã có (FR-208/209, phiên trước, dùng chung).

Hai khoảng trống thật:

1. **Chưa có hộp cuộn cho listbox hashtag.** `max-h-[348px] overflow-y-auto` hiện gắn sau cờ
   `scrollable`, và `kudos-filter-bar.tsx` chỉ truyền cờ đó cho Phòng ban. 13 hàng × 56px +
   12px padding = **740px**, đổ dài quá khung nhìn — trái đúng câu "scroll khi vượt quá chiều
   cao" của spec A.
2. **Chưa có test nào khẳng định phía hashtag.** `kudos-live-board.spec.ts` mới có K-3 (đếm 13
   option) và K-8 (reset carousel); K-26..K-30 của phiên trước đều khẳng định trên listbox
   Phòng ban. Không có test nào chứng minh click hashtag đóng menu, lọc cả hai section, giữ
   highlight khi mở lại, hay click lại thì bỏ lọc.

Ngoài ra `focus-visible` của option hiện chỉ có outline mặc định trình duyệt — spec A.1 nói
"hover/**focus**: glow", nên phần focus là chưa dựng.

## 3. Yêu cầu chức năng (delta)

- **FR-214** Listbox hashtag cao tối đa **348px** (6 hàng 56px + 6px padding trên/dưới), phần
  còn lại **cuộn trong hộp** — không đẩy layout trang, không cắt mất option nào (đủ 13).
  Hộp cuộn là mặc định của `KudosFilterMenu`; cờ `scrollable` bị bỏ vì cả hai listbox đều cần.
- **FR-215** Khi option nhận focus bàn phím, nó hiển thị **glow** cùng token `#FAE287` của
  trạng thái selected (không đổi hover: nền `rgba(255,234,158,0.05)` giữ nguyên).
- **FR-216** Click một option hashtag **đóng dropdown ngay** và áp filter lên **cả HIGHLIGHT
  KUDOS lẫn ALL KUDOS**: chỉ còn kudos mang hashtag đó.
- **FR-217** Option hashtag đang chọn mang highlight bền: mở lại dropdown vẫn thấy
  `aria-selected="true"` cùng nền sáng + glow.
- **FR-218** Click lại chính option hashtag đang chọn sẽ **bỏ lọc**, board trở về đầy đủ.
- **FR-219** Danh sách hashtag đúng **13 mục theo `position`** của `public.hashtags`, khớp thứ
  tự frame — giữ nguyên, không hoist mục đã chọn lên đầu.

## 4. Quy tắc nghiệp vụ

- **BR-214** Nhãn option là tên hashtag trong DB (`Cống hiến`, `Wasshoi`, …). Chuỗi
  `#Dedicated`/`#Inspring` trong ảnh frame là placeholder tiếng Anh của bản dựng Figma;
  chính spec A liệt kê 13 tên tiếng Việt là dữ liệu thật.
- **BR-215** Bộ lọc hashtag và bộ lọc Phòng ban **AND** với nhau (`matchesFilters()` giữ nguyên).
- **BR-216** Không route mới, không bảng mới, không migration, không Server Action.
  `fetchFilterOptions()` và `matchesFilters()` không đổi một dòng.

## 5. Máy trạng thái

`hashtagFilterId: number | null` trong `kudos-board.tsx` (giữ nguyên):

```
null --click option X--> X --click option X--> null
                          |
                          +--click option Y--> Y
```
Mọi chuyển trạng thái đều đóng menu và `resetPaging()`.

## 6. Ngoài phạm vi

- Đa chọn hashtag (frame chỉ mô tả một mục selected).
- Đưa hashtag đang lọc vào URL (`?hashtag=` hiện chỉ đọc lúc mount — FR-405 của F006, không đổi).
- Đổi token màu selected/hover.
- Bất kỳ thay đổi nào ở listbox Phòng ban ngoài việc bỏ cờ `scrollable` (hành vi y hệt).

## 7. Câu hỏi còn treo

Không còn. Toàn bộ quyết định đã chốt trong `clarifications.md`.
