---
status: draft
authored_by: takumi
created: 2026-09-10
lang: vi
---

**Priority**: P2
**Type**: ui

## 1. Overview

**Problem:** Pill nổi góc dưới-phải trang chủ hiện là hai liên kết trực tiếp (`/kudos`, `/standards`) tách nhau bằng dấu `/` — không phản ánh đúng thiết kế thật: cạnh điều hướng đo được của MoMorph (`313:9138` → `313:9139`) cho thấy pill phải dẫn tới một trạng thái mở gồm ba lựa chọn (`Thể lệ`, `Viết KUDOS`, `Hủy`), không dẫn thẳng tới một đích.
**Solution:** Chuyển pill thành một cần mở/đóng thật (`aria-expanded`, `aria-controls`); bấm vào hiện nhóm ba nút đúng hình học đo được, đóng bằng `Hủy`, `Escape`, hoặc bấm ra ngoài; hai nút chính điều hướng sang `/standards` và `/kudos/new` — cả hai route đã ship.
**Scope:** Chuyển `app/_components/floating-widget.tsx` thành client component có state mở/đóng; mở rộng khối `home.widget` trong `Dictionary` (vi + en) với nhãn cho trigger, nhóm nút và nút đóng; một bộ spec E2E RED-first mới (`e2e/floating-action-button.spec.ts`); thích nghi test `FUN_003` đã ship của `e2e/the-le.spec.ts` theo đường bấm mới.
**Non-Scope:** Không route mới, không bảng hay migration Supabase mới; `/standards` và `/kudos/new` không bị sửa; FAB không mở rộng sang trang nào khác ngoài trang chủ `/`.

**Actors**

| Actor | Description | Primary goal |
|-------|--------------|---------------|
| Khách vãng lai (chưa đăng nhập) | Bất kỳ ai mở trang chủ `/` — route công khai | Mở nhanh Thể lệ, hoặc bị chuyển hướng đăng nhập nếu muốn viết Kudos |
| Sunner (đã đăng nhập) | Nhân viên Sun* đã đăng nhập | Mở nhanh Thể lệ hoặc đi thẳng sang viết Kudos ngay từ trang chủ |

## 2. Functional Capabilities

| ID | Capability | What the user can do | User Stories | Requirements | Business Rules | Screens |
|----|------------|------------------------|-----------------|---------------|-------------------|---------|
| CAP-01 | Mở menu nhanh | Bấm pill nổi để hiện nhóm ba nút hành động nhanh | US001 | FR-001, FR-101, FR-201, FR-202 | BR-001, BR-002, BR-005, BR-006, SM-001 | SCR002_Homepage |
| CAP-02 | Đóng menu quay về pill | Bấm `Hủy`, gõ `Escape`, hoặc bấm ra ngoài để đóng nhóm nút | US002 | FR-205, FR-401 | BR-004 | — |
| CAP-03 | Đi tới Thể lệ | Bấm `Thể lệ` để sang `/standards` | US003 | FR-203 | DEC-001 | — |
| CAP-04 | Đi tới Viết KUDOS | Bấm `Viết KUDOS` để sang `/kudos/new`, chuyển hướng `/login` nếu chưa đăng nhập | US004 | FR-204, FR-601 | BR-003, DEC-002 | — |

## 3. Open Decisions

None — no unresolved domain confirmations. Commission chạy `--auto` với chỉ thị *"nếu có vấn đề
gì cần confirm với tôi, tự động triển khai theo hướng câu trả lời đầu tiên, Yes hoặc câu trả lời
Recommend mà ko cần confirm tôi"*, nên mọi câu hỏi mở trong `clarifications.md` đã được chốt bằng
phương án Recommended. Hai điểm cần nói rõ vì chúng DỊCH một mô tả thiết kế sang cơ chế đã tồn tại
thật, chứ không im lặng bỏ qua:

- **DEC-001 — Mô tả thiết kế của `Thể lệ` nói "Mở modal/section"; repo này điều hướng bằng route.**
  Bề mặt Thể lệ của hệ thống là route `/standards` (F007, đã ship dạng drawer thật). Yêu cầu —
  "bấm Thể lệ thấy được nội dung thể lệ" — giữ nguyên; chỉ cơ chế được dịch sang thứ tồn tại thật.
- **DEC-002 — Cùng bản dịch cho `Viết KUDOS`.** Bề mặt soạn Kudos của hệ thống là route
  `/kudos/new` (F005, đã ship). Nút điều hướng sang đó; `proxy.ts` sẵn có quyết định ai đi tiếp được.

## 4. Requirements

### Foundation (0xx)

- **FR-001** Khối `home.widget` trong `Dictionary` (`lib/i18n/messages/dictionary.ts`,
  `vi-home.ts`, `en-home.ts`) được bổ sung nhãn cho pill trigger, nhóm nút mở, và nút đóng — cả
  `vi` lẫn `en`, giữ nguyên hai nhãn `writeKudos`/`standards` đã có.

### Navigation (1xx)

- **FR-101** Pill nổi chỉ render trên trang chủ `/`, đúng như hiện tại — không mở rộng bề mặt
  sang trang nào khác.

### Trang chủ — FAB nổi (2xx)

- **FR-201** Pill nổi là một cần mở/đóng thật: `aria-expanded` phản ánh trạng thái, `aria-controls`
  trỏ tới nhóm nút, hai icon và dấu `/` giữ nguyên làm nội dung của cần mở này (không còn hai
  liên kết trực tiếp).
- **FR-202** Bấm pill hiện nhóm ba nút (`Thể lệ`, `Viết KUDOS`, `Hủy`) đúng bố cục và kích thước đo
  được: cột dọc 214×224, khoảng cách 20px, hai nút chính 149×64/214×64 bo góc 4px nền `#FFEA9E`,
  nút đóng 56×56 bo tròn hết cỡ nền `#D4271D`.
- **FR-203** Nút `Thể lệ` điều hướng sang `/standards`.
- **FR-204** Nút `Viết KUDOS` điều hướng sang `/kudos/new`.
- **FR-205** Nút `Hủy` đóng nhóm nút, quay về pill.

### Interaction (4xx)

- **FR-401** Gõ `Escape` hoặc bấm ra ngoài vùng menu cũng đóng nhóm nút, giống hệt `Hủy` — tái
  dùng đúng hợp đồng dismiss đang phục vụ những popover khác trên trang.

### Security (6xx)

- **FR-601** Bấm `Viết KUDOS` khi chưa đăng nhập bị chuyển hướng sang `/login` bởi guard sẵn có —
  không có logic xác thực mới nào được thêm cho riêng nút này.

## 5. Business Rules

- Pill là một cần mở duy nhất, không phải hai liên kết trực tiếp; hai icon và dấu `/` trở thành
  nội dung của nút bấm đó (BR-001)
- FAB chỉ render trên trang chủ, không mở rộng sang trang khác (BR-002)
- Nút `Viết KUDOS` không tự phán quyền — việc chặn người chưa đăng nhập là việc của `proxy.ts`
  trên `/kudos/new`, không nhân bản logic đó ở đây (BR-003)
- `Escape` trả focus về pill; bấm ra ngoài thì không di chuyển focus (BR-004)
- Dưới 1024px các nút co theo nội dung thay vì giữ cứng 149/214px — bề rộng đo được là mức tối
  thiểu, không phải kích thước cứng (BR-005)
- Feature này không lưu và không đọc bất kỳ dữ liệu nào — trạng thái mở/đóng chỉ tồn tại phía
  client, không có bảng hay migration mới (BR-006)
- Bấm `Thể lệ` điều hướng sang `/standards` thay vì mở modal (DEC-001)
- Bấm `Viết KUDOS` điều hướng sang `/kudos/new` thay vì mở modal (DEC-002)
- Trạng thái mở/đóng của FAB là một máy trạng thái hai bước: `collapsed` ⇄ `expanded`, chuyển
  bằng bấm pill, `Hủy`, `Escape`, bấm ra ngoài, hoặc kết thúc khi điều hướng rời trang (SM-001)

## 6. Screens

| Screen Name | SCR### | What User Sees | What User Can Do |
|-------------|--------|-----------------|-------------------|
| Trang chủ (FAB nổi) | SCR002_Homepage | Pill nổi góc dưới-phải; khi bấm, thêm nhóm ba nút `Thể lệ`/`Viết KUDOS`/`Hủy` hiện tại chỗ | Mở/đóng nhóm nút nhanh; đi tới `/standards` hoặc `/kudos/new` |

### User Journey

1. Người dùng vào trang chủ, thấy pill nổi góc dưới-phải.
2. Bấm pill — nhóm ba nút hiện ra tại chỗ, pill biến mất.
3. Bấm `Thể lệ` hoặc `Viết KUDOS` để rời trang chủ sang route tương ứng; hoặc bấm `Hủy`, gõ
   `Escape`, hay bấm ra ngoài để đóng nhóm nút và quay về pill.

## 7. User Stories

### US001 — Mở menu nhanh từ pill nổi

**Actor:** Sunner (đã đăng nhập)
**Goal:** Bấm pill nổi để thấy ngay các hành động nhanh có sẵn từ trang chủ.
**Business value:** Rút ngắn đường tới Thể lệ và Viết Kudos xuống một điểm chạm duy nhất, thay vì
phải cuộn hoặc tìm liên kết trong footer.

**Acceptance Criteria:**
- [ ] Bấm pill hiện đủ ba nút `Thể lệ`, `Viết KUDOS`, `Hủy`.
- [ ] `aria-expanded` của pill chuyển từ `false` sang `true` khi menu mở.

### US002 — Đóng menu quay về pill

**Actor:** Sunner (đã đăng nhập)
**Goal:** Đóng nhóm nút vừa mở mà không cần rời trang.
**Business value:** Cho phép huỷ ý định giữa chừng mà không mất ngữ cảnh đang xem trên trang chủ.

**Acceptance Criteria:**
- [ ] Bấm `Hủy` đóng menu, pill hiện lại.
- [ ] Gõ `Escape` đóng menu và trả focus về pill.
- [ ] Bấm ra ngoài vùng menu đóng menu mà không di chuyển focus.

### US003 — Đi thẳng sang Thể lệ

**Actor:** Khách vãng lai (chưa đăng nhập)
**Goal:** Mở nhanh nội dung Thể lệ chương trình từ trang chủ.
**Business value:** Không phải rời trang chủ để tìm lối vào Thể lệ ở nơi khác (footer, menu).

**Acceptance Criteria:**
- [ ] Bấm `Thể lệ` đưa người dùng tới `/standards`.

### US004 — Đi thẳng sang Viết KUDOS

**Actor:** Sunner (đã đăng nhập)
**Goal:** Bắt đầu soạn một Kudos ngay từ trang chủ mà không cần tìm đường.
**Business value:** Giảm số bước từ "muốn ghi nhận đồng nghiệp" tới "đang soạn Kudos".

**Acceptance Criteria:**
- [ ] Đã đăng nhập, bấm `Viết KUDOS` đưa người dùng tới `/kudos/new`.
- [ ] Chưa đăng nhập, bấm `Viết KUDOS` chuyển hướng người dùng tới `/login`.

## 8. Scenarios

### US001 — Happy Path

**Given** đang ở trang chủ với pill đóng, **When** bấm pill, **Then** nhóm ba nút hiện ra và
`aria-expanded` chuyển thành `true`.

### US001 — Error: bấm nhiều lần liên tiếp

**Given** đang ở trang chủ với pill đóng, **When** bấm pill nhiều lần rất nhanh, **Then** menu chỉ
mở một lần, không có trạng thái nhấp nháy hay kẹt giữa hai state.

### US002 — Happy Path

**Given** menu đang mở, **When** bấm `Hủy`, **Then** menu đóng và pill hiện lại đúng vị trí cũ.

### US002 — Error: Escape khi menu đã đóng

**Given** pill đang đóng, **When** gõ `Escape`, **Then** không có gì thay đổi — không có handler
nào được gắn để lắng nghe khi menu đã đóng.

### US003 — Happy Path

**Given** menu đang mở, **When** bấm `Thể lệ`, **Then** trình duyệt điều hướng tới `/standards`.

### US004 — Happy Path

**Given** đã đăng nhập và menu đang mở, **When** bấm `Viết KUDOS`, **Then** trình duyệt điều hướng
tới `/kudos/new`.

### US004 — Error: chưa đăng nhập

**Given** chưa đăng nhập và menu đang mở, **When** bấm `Viết KUDOS`, **Then** hệ thống chuyển
hướng tới `/login` thay vì `/kudos/new`.

## 9. Edge Cases

| Scenario | What Happens | User-Facing Message |
|----------|--------------|----------------------|
| Bấm pill nhiều lần liên tiếp rất nhanh | Menu chỉ mở một lần, không nhấp nháy | *(không có thông báo)* |
| Tải lại trang (`F5`) trong khi menu đang mở | Menu về lại trạng thái đóng — trạng thái mở không được ghi nhớ qua lần tải lại | *(không có thông báo)* |
| Bấm `Thể lệ` hoặc `Viết KUDOS` rồi rời trang ngay | Điều hướng diễn ra bình thường, không có gì bị treo lại | *(không có thông báo)* |
| Chưa đăng nhập bấm `Viết KUDOS` | Chuyển hướng sang `/login`; nút không bị ẩn hay khoá trước đó | *(không có thông báo trên trang chủ — trang `/login` tự hiển thị)* |
| Gõ `Escape` khi menu đang đóng | Không có gì xảy ra | *(không có thông báo)* |

## 10. Edge Behaviours to Verify

- **FR-201** → Pill mang đúng `aria-expanded`/`aria-controls`, đổi giá trị khi menu mở/đóng.
- **FR-202** → Nhóm ba nút hiện đủ, đúng thứ tự và kích thước khi menu mở.
- **FR-203** → Bấm `Thể lệ` đưa người dùng đúng tới `/standards`.
- **FR-204** → Bấm `Viết KUDOS` đưa người dùng đúng tới `/kudos/new` (khi đã đăng nhập).
- **FR-205** → Bấm `Hủy` đóng menu, quay về pill.
- **FR-401** → `Escape` và bấm ra ngoài đều đóng menu; `Escape` trả focus về pill.
- **FR-601** → Chưa đăng nhập bấm `Viết KUDOS` kết thúc ở `/login`, không phải `/kudos/new`.

## 11. Risks & Known Issues

N/A — none found.

## 12. Dependencies

| Dependency | Type | Why this feature needs it | Evidence |
|------------|------|-----------------------------|----------|
| `/standards` (F007) | feature | Đích điều hướng của nút `Thể lệ` | `docs/features/F007_TheLe/` |
| `/kudos/new` (F005) | feature | Đích điều hướng của nút `Viết KUDOS`, đã được guard | `proxy.ts` |
| `app/_components/use-dismiss-on-outside.ts` | internal | `Escape` + bấm-ra-ngoài dùng lại nguyên, không viết lại | `app/_components/account-menu.tsx`, `language-selector.tsx` |
| Supabase local | infrastructure | Môi trường phát triển/kiểm thử E2E — FAB tự nó không đọc/ghi, nhưng đích `/standards` đọc dữ liệu thật khi test chạy | `clarifications.md § Local Supabase` |

## 13. Configuration

N/A — no user-facing configuration constants for this feature.
