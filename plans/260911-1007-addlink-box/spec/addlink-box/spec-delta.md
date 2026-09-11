---
status: draft
authored_by: takumi
created: 2026-09-11
lang: vi
fcode: F005
promotes_to:
  - docs/features/F005_VietKudo/functional-spec.md
  - docs/features/F005_VietKudo/technical-spec.md
  - docs/screens/SCR005_VietKudo/spec.md
momorph_screen: OyDLDuSGEa
---

# Spec delta — Addlink Box (hộp thoại `Thêm đường dẫn`)

Amendment to F005 / SCR005. Không phải feature mới: frame `OyDLDuSGEa` là **thiết kế chính thức
của hộp thoại chèn liên kết** mà `app/kudos/new/_components/link-dialog.tsx` đang dựng tạm. Chính
file đó ghi trong doc comment: *"No MoMorph node backs this dialog either (ratification item 6
lists it as unauthored)"*. Frame này lấp đúng chỗ trống ấy, nên delta chỉ nói phần thiết kế thật
khác phần dựng tạm.

## Điều gì đổi

Hộp thoại hiện tại có **một** ô nhập (`link-url-input`) và chặn lưu bằng cách **disable** nút xác
nhận. Frame mô tả một hộp thoại **hai ô nhập** — `Nội dung` (item B) và `URL` (item C) — với nút
`Lưu` luôn bấm được, validate khi bấm, và **hiện thông báo lỗi cho từng ô sai**. 25 test case của
frame gần như toàn bộ nói về lớp lỗi đó, thứ mà một nút disabled không bao giờ phát ra được.

Kèm theo là một thay đổi ngữ nghĩa thật: ô `Nội dung` là **văn bản hiển thị của liên kết**. Trước
đây dialog chỉ đánh dấu link lên vùng đang bôi đen; từ nay nó **thay vùng đang chọn bằng văn bản
vừa nhập** (hoặc chèn tại con trỏ nếu không bôi đen gì), rồi đánh dấu link lên đúng đoạn đó.

## Yêu cầu chức năng bổ sung

- **FR-213** Hộp thoại hiển thị tiêu đề `Thêm đường dẫn` (item A) và **hai** ô nhập xếp dọc, mỗi ô
  có nhãn nằm **bên trái**: `Nội dung` (item B.1 → B.2) và `URL` (item C.1 → C.2). Bấm vào nhãn
  `Nội dung` chuyển focus sang ô nhập tương ứng (item B.1 `userAction`); nhãn `URL` chỉ để thông
  tin (item C.1 "Không tương tác"). Ô nhập được focus hiện viền nổi (item B.2 "Focus: Hiện viền
  nổi").

- **FR-214** Ô `Nội dung` là văn bản hiển thị của liên kết: bắt buộc, độ dài 1–100 ký tự, không
  được chỉ gồm khoảng trắng (item B `validationNote` verbatim). Khi mở hộp thoại, nếu trong editor
  đang bôi đen một đoạn khác rỗng thì ô này **điền sẵn** đoạn đó; nếu không, ô để trống (item B.2
  `defaultValue` trống, TC `7d5ff602`).

- **FR-215** Ô `URL` bắt buộc, độ dài 5–2048 ký tự, phải là URL hợp lệ theo danh sách scheme đã
  chốt của `ACCEPTED_LINK_SCHEMES` (`http:`, `https:`, `mailto:`) — item C `validationNote`, mở
  rộng bằng hằng số bảo mật sẵn có thay vì một danh sách thứ hai. Ô này được kiểm tra định dạng
  **khi blur** và **khi bấm Lưu** (item C "Blur: Kiểm tra định dạng URL", TC `db2ca333`). Khi mở
  hộp thoại ô luôn trống (TC `57a9b74f`).

- **FR-216** Nút `Lưu` (item D.2) **luôn bấm được**. Bấm `Lưu` chạy validate cả hai ô: nếu có ô
  sai, mỗi ô sai hiện thông báo lỗi của riêng nó và hộp thoại **không đóng**, không có liên kết
  nào được chèn (TC `e5632ac7`). Nếu cả hai hợp lệ, liên kết được chèn và hộp thoại đóng
  (TC `ef4d0413`).

- **FR-217** Chèn thành công **thay** vùng văn bản đang chọn trong `body-editor` bằng giá trị ô
  `Nội dung`, rồi đánh dấu `link` mang `href` là giá trị ô `URL` lên đúng đoạn vừa chèn. Con trỏ
  rỗng (không bôi đen) thì chèn tại vị trí con trỏ. Mark nào đang nằm chồng lên vùng bị thay sẽ bị
  **bỏ**, không neo lại bằng phỏng đoán — đúng chính sách `remapMarks` đã công bố trong
  `rich-text.ts`.

- **FR-218** Nút `Hủy` (item D.1) đóng hộp thoại và **hủy mọi thay đổi**: không chèn gì, giá trị
  hai ô không được giữ lại cho lần mở sau. `Escape` và bấm ra ngoài hộp thoại có cùng hiệu lực
  (TC `48467d34`). Bấm `Hủy` hai lần liên tiếp không gây tác dụng phụ nào.

- **FR-219** Nhóm nút (item D) nằm cố định ở **đáy** hộp thoại và ở lại đó khi nội dung cuộn
  (TC `abddef4b`). `Hủy` là nút nhỏ, có viền, kèm icon `X`; `Lưu` là nút lớn nền vàng `#FFEA9E`,
  chiếm phần chiều ngang còn lại, kèm icon liên kết (TC `b13a3dcc`, `096b9346`).

## Business rule chịu ảnh hưởng

- **BR-006 (mới)** Một liên kết chỉ vào được nội dung Kudo khi **cả** văn bản hiển thị **và** URL
  đều hợp lệ. URL phải qua `ACCEPTED_LINK_SCHEMES`; đây là chốt chặn **thứ nhất** trong ba chốt mà
  `rich-text.ts` đã hứa — `parseKudosDoc` kiểm lại khi đọc, renderer kiểm lần nữa khi vẽ. Không
  chốt nào tin vào chốt trước.

## Acceptance criteria

- [ ] Mở hộp thoại từ nút `toolbar-link` khi không bôi đen gì: tiêu đề `Thêm đường dẫn`, hai ô
      `Nội dung` và `URL` đều trống, cả hai nhãn nằm bên trái ô của mình.
- [ ] Bôi đen một đoạn trong `body-editor` rồi mở hộp thoại: ô `Nội dung` điền sẵn đúng đoạn đó.
- [ ] Bấm nhãn `Nội dung`: con trỏ nhảy vào ô nhập `Nội dung`.
- [ ] Bấm `Lưu` khi cả hai ô trống: hai thông báo lỗi hiện ra, hộp thoại vẫn mở.
- [ ] Nhập `Nội dung` chỉ gồm khoảng trắng rồi `Lưu`: lỗi hiện ra, không lưu.
- [ ] Nhập `Nội dung` 101 ký tự rồi `Lưu`: lỗi độ dài hiện ra, không lưu. 1 ký tự thì được nhận.
- [ ] Nhập `URL` là `invalid-url` rồi blur: lỗi định dạng hiện ra ngay, chưa cần bấm `Lưu`.
- [ ] Nhập `URL` là `www` (4 ký tự) rồi `Lưu`: lỗi độ dài tối thiểu hiện ra, không lưu.
- [ ] Nhập `Nội dung` hợp lệ + `URL` `https://www.example.com` rồi `Lưu`: hộp thoại đóng, văn bản
      xuất hiện trong `body-editor`, và payload gửi đi chứa run `{ type: "link", text, href }`.
- [ ] Bấm `Hủy`, bấm ra ngoài, và bấm `Escape`: hộp thoại đóng, `body-editor` không đổi; mở lại
      thì hai ô trống (không giữ giá trị cũ).
- [ ] Nhóm nút ở đáy: `Hủy` có viền + icon `X` và hẹp hơn `Lưu`; `Lưu` nền vàng + icon liên kết.

## Ngoài phạm vi

- Không thêm route, bảng, migration hay Server Action nào. Đường ghi `createKudos` giữ nguyên.
- Không đổi `ACCEPTED_LINK_SCHEMES`, không đổi `KudosRun`/`KudosDoc` — run `link` đã có sẵn
  `text` + `href`, delta này chỉ cuối cùng cũng điền được cả hai.
- Không thêm WYSIWYG preview trong editor: `body-editor` vẫn là `<textarea>` controlled, mark vẫn
  nằm **trên** plain text (quyết định đã chốt ở phase 01 của F005, không mở lại ở đây).
- Không đụng tới sửa/gỡ một liên kết đã chèn — frame không nói gì về hai thao tác đó.

## Promote mapping (applied 2026-09-11)

No renumbering was needed: `FR-213`..`FR-219` and `BR-006` were all free in F005 at promote time
(the highest taken was `FR-212`, left by the hashtag-dropdown delta; the highest `BR` was `BR-005`).
Draft IDs promoted **unchanged**.

Promoted into:

| Target | What landed |
|---|---|
| `docs/features/F005_VietKudo/functional-spec.md` | FR-213..FR-219 in § 4 (2xx); BR-006 in § 5; CAP-01 row gains the new FRs + BR-006; FR-204 reworded to name the two-field dialog; US001 acceptance criterion rewritten; three new § 10 edge behaviours replacing the old single FR-204 line |
| `docs/features/F005_VietKudo/technical-spec.md` | A1 index row + § 3.1 linked-FR line extended; § 3.1 FE prose gains the capture-selection-at-open rule and the `insertLink` reason; BR-006 in § 3.1 Rule and § 4.4 Bin 2; § 4.1 gains `LinkDialog`, `validate-link.ts` and `insertLink`; SC-001 hook list gains the five new hooks |
| `docs/screens/SCR005_VietKudo/spec.md` | E09 rewritten + new E09.1..E09.5; two § 4 action rows; two § 6 validation rows; § 5 error state; § 9 focus-management row corrected to what is actually built |
