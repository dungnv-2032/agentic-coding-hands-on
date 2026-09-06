---
status: promoted
authored_by: takumi
fcode: F003
created: 2026-09-06
lang: vi
---

> **PROMOTED 2026-09-06** → `docs/features/F003_AwardSystem/technical-spec.md`. Bản này là bản nháp lịch sử của phase 01; bản trong `docs/` là bản có hiệu lực và đã điền `**Source:**` thật. Đừng sửa file này.

# F003_AwardSystem — Technical Spec

**Priority**: P1
**Type**: ui
**Generated**: 2026-09-06

**See also:** [`functional-spec.md`](./functional-spec.md) — mô tả bằng ngôn ngữ đời thường, quyết định
còn mở, requirement/business rule dạng một dòng, màn hình, user story, kịch bản, edge case và cấu hình
cho người đọc BA/QA.

**How to read this file:** § 2 là mục lục — chọn action cần quan tâm rồi đọc thẳng khối tương ứng ở § 3.
§ 4 là phụ lục dùng chung — chỉ nhảy vào khi một khối § 3 trỏ tới.

## 1. Technical Overview

Màn hình công khai tại `/awards-information`, thay chỗ shell `ComingSoon` đang chiếm route đó. Một Server
Component đọc locale + phiên đăng nhập qua `getPageContext()` (dùng chung với trang chủ, không thêm điểm
đọc thứ hai) rồi render toàn bộ nội dung tĩnh: hero, sáu thẻ giải thưởng, và các thành phần chrome tái
dùng nguyên trạng của F002 (`HomeHeader`, `KudosPromo`, `SiteFooter`). Chỉ menu danh mục bên trái là Client
Component — nó theo dõi vị trí cuộn để đổi mục đang sáng và xử lý cú bấm. Không có endpoint mới, không có
bảng dữ liệu, không có thao tác ghi; `proxy.ts` không bị đụng tới (clarifications.md ORCH-03 + quyết định
auth). Dữ liệu giải thưởng tách hai lớp theo đúng mẫu F002 đã dựng: *identity* (slug, khoá từ điển, ảnh,
đơn vị) trong một module dữ liệu, *copy* (tiêu đề, mô tả, số lượng, mức giải) trong từ điển i18n dưới một
namespace mới, khớp nhau bằng cùng một `AwardKey`.

## 2. Action Index

| # | Action (handler) | Method · Path | Codes | Writes | Detail |
|---|---|---|---|---|---|
| **A0** | *cross-cutting — belongs to no single action* | — | FR-001, FR-601, BR-001 | — | § 4.4 |
| **A1** | `` `AwardSystemPage#render` `` *(planned)* | `GET` `/awards-information` | FR-002, FR-101, FR-201, FR-202, FR-204, FR-205, FR-206, FR-207, FR-208, BR-004, US007 | — *(read-only)* | § 3.1 |
| **A2** | `` `AwardCategoryNav#interact` `` *(planned, client-only)* | *(client state — no HTTP)* | FR-102, FR-203, FR-401, FR-402, FR-403, BR-002, BR-003, DEC-002, US008 | — *(client state only)* | § 3.1 |

## 3. Actions

### 3.1 CAP-01 — Đọc hệ thống giải thưởng SAA 2025

#### A1 · Render màn hình hệ thống giải
`GET` `/awards-information` → `` `AwardSystemPage#render` `` *(planned)*
`FR-002` `FR-101` `FR-201` `FR-202` `FR-204` `FR-205` `FR-206` `FR-207` `FR-208` `BR-004` `US007` · `SCR003_AwardSystem`

**Who** · Khách truy cập (đã đăng nhập hay chưa đều xem được — FR-001, § 4.4)
**FE** · Server Component render năm khối theo thứ tự thiết kế (FR-201): `HomeHeader` tái dùng nguyên trạng
— mục "Award Information" tự sáng vì nav đã suy trạng thái chọn từ đường dẫn hiện tại, nên không sửa gì ở
đó (FR-101, ORCH-03); hero gồm ảnh keyvisual + chữ hình ROOT FURTHER + cụm eyebrow/đường kẻ/tiêu đề vàng
canh giữa (FR-202); phần hệ thống giải gồm `AwardCategoryNav` (A2) dính bên trái và sáu `AwardDetailCard`
xen kẽ ảnh trái/ảnh phải theo chỉ số lẻ/chẵn, dưới `lg` gộp về một cột với ảnh lên trước (FR-204, FR-205);
`KudosPromo` tái dùng nguyên trạng (FR-207); `SiteFooter` tái dùng nguyên trạng. `FloatingWidget` **không**
render ở màn hình này (FR-208). Mọi chuỗi hiển thị lấy từ từ điển đã phân giải theo locale (FR-002) — không
có chuỗi cứng trong component.
**Request** · không có tham số — trang tĩnh, không dùng `searchParams`; `#<slug>` là fragment nên không tới
server.
**BE** · không có — thuần render phía server. Nội dung sáu giải là dữ liệu tĩnh biên soạn từ thiết kế
(clarifications.md — "Use Figma design content as mock data source"), không phải bảng dữ liệu (§ 4.2).
**Rule** ·

**BR-004 — Giá trị giải là một danh sách, không phải hai trường phẳng.** Mỗi giải mang một danh sách mức
giải, mỗi mức gồm số tiền và một ghi chú tuỳ chọn: bốn giải có đúng một mức kèm ghi chú, Signature có hai
mức nối nhau bằng dòng `Hoặc`, Best Manager và MVP có một mức không ghi chú. Nhờ vậy component render đúng
một dạng dữ liệu cho cả sáu thẻ và không rẽ nhánh theo tên giải; ghi chú trống thì không sinh dòng rỗng.
Đây là quy tắc về hình dạng dữ liệu, không phải một nhánh quyết định — không cấp mã `DEC-###`. *(FR-206)*
**Result** · Chỉ render — không ghi dữ liệu. Bấm `Chi tiết` ở khối Kudos điều hướng `/kudos` (FR-207); các
lối ra khác thuộc header/footer tái dùng, không phải hành vi mới của action này.
**Source:** `TBD (draft)`

<!-- Không cần sequence diagram: read-only, không ghi bảng nào, không phải background/async action. -->

---

#### A2 · Menu danh mục — scroll-spy, bấm nhảy, và deep link *(client-only)*
*(client state — no HTTP)* → `` `AwardCategoryNav#interact` `` *(planned)*
`FR-102` `FR-203` `FR-401` `FR-402` `FR-403` `BR-002` `BR-003` `DEC-002` `US008` · `SCR003_AwardSystem`

**Who** · Khách truy cập đang đọc màn hình hệ thống giải
**FE** · `AwardCategoryNav` là Client Component duy nhất của tính năng này. Nó render sáu mục theo đúng thứ
tự thiết kế, mỗi mục có biểu tượng 24×24 phía trước; mục đang sáng đổi sang chữ vàng + gạch chân vàng
(FR-203). Trạng thái sáng giữ trong một biến `activeSlug` cục bộ (§ 4.3). Ba nguồn ghi vào biến đó: cú bấm
của người dùng (FR-401), hash đọc lúc mount (FR-102, DEC-002), và `ALG-001` chạy theo vị trí cuộn (FR-402,
§ 4.5).
**Request** · không có — mọi tương tác ở đây là trạng thái phía client, không phát sinh HTTP request nào.
**BE** · không có.
**Rule** ·

**BR-002 — Menu luôn có đúng một mục đang sáng.** `activeSlug` là một giá trị đơn, không phải tập hợp, nên
việc "chỉ một mục sáng" là bất biến của kiểu dữ liệu chứ không phải một bước dọn dẹp phải nhớ chạy. Thứ tự
ưu tiên khi nhiều nguồn cùng muốn ghi: cú bấm gần nhất khoá `ALG-001` trong khoảng thời gian cuộn mượt (nếu
không thì observer sẽ bắn liên tục dọc đường cuộn và làm mục sáng nhấp nháy), sau đó tới hash lúc mount,
sau cùng là vị trí cuộn. *(FR-402)*

**BR-003 — Người dùng bật giảm chuyển động thì nhảy tức thì.** Đọc `prefers-reduced-motion` và chọn kiểu
cuộn tương ứng — `smooth` khi không bật, nhảy thẳng khi có bật; khoá chống nhấp nháy của BR-002 khi đó rút
về 0 vì không còn quãng cuộn nào để bảo vệ. *(FR-403)*

Quyết định nguồn seed mục sáng lúc mở trang:

| DEC | subtype | Condition | What the user sees | Source |
|---|---|---|---|---|
| **DEC-002** | interaction, flow | `location.hash` khớp một slug trong danh sách sáu giải | Mục menu tương ứng sáng ngay khi trang mở, thay vì kẹt ở mục đầu | `TBD (draft)` |
| **DEC-002** | interaction, flow | không có hash, hoặc hash không khớp slug nào | Mục đầu tiên (Top Talent) sáng, trang mở từ đầu, không có cú nhảy nào | `TBD (draft)` |

**Result** · Chỉ đổi trạng thái cục bộ và vị trí cuộn — không ghi dữ liệu, không gọi API. Cú bấm cập nhật
địa chỉ trang thành `#<slug>` bằng cách thay thế mục lịch sử hiện tại chứ không thêm mục mới, để nút Back
vẫn quay về trang chủ chứ không phải lùi qua từng hạng mục vừa xem (FR-401).
**Source:** `TBD (draft)`

<!-- Không cần sequence diagram: không ghi bảng nào, không phải background action; toàn bộ nội dung là
     một biến trạng thái với ba nguồn ghi, đã nêu đủ ở rung Rule + ALG-001. -->

### 3.2 Edge cases

| Action | Scenario | Behavior |
|---|---|---|
| A1 | Khách chưa đăng nhập mở trang | Trang render đầy đủ, không redirect — route công khai theo BR-001 (§ 4.4) |
| A1 | Một giải chỉ có một mức và không có ghi chú | Chỉ render số tiền, không sinh dòng ghi chú rỗng (BR-004) |
| A2 | Hash không khớp slug nào | Bỏ qua hash, mục đầu tiên sáng, không có cú nhảy (DEC-002) |
| A2 | Người dùng bật giảm chuyển động | Nhảy tức thì thay vì cuộn mượt; mục sáng vẫn đúng (BR-003) |
| A2 | Thẻ cuối trang không cao bằng một màn hình | `ALG-001` chọn hạng mục gần đỉnh vùng nhìn nhất nên mục cuối vẫn sáng được (§ 4.5) |
| A2 | Client Component chưa sẵn sàng | Sáu thẻ và menu vẫn đọc được vì nội dung là tĩnh do server render; chỉ mục sáng chưa tự chạy theo cuộn |

## 4. Shared Foundation

### 4.1 Components

| Component | Responsibility | Used in | File |
|---|---|---|---|
| `HomeHeader` *(tái dùng F002, không sửa)* | Logo, nav 3 mục (mục "Award Information" tự sáng trên route này), bộ chọn ngôn ngữ, chuông + tài khoản khi đã đăng nhập | A1 | `app/_components/home-header.tsx` |
| `SiteFooter` *(tái dùng F002, không sửa)* | Footer 4 liên kết + bản quyền | A1 | `app/_components/site-footer.tsx` |
| `KudosPromo` *(tái dùng F002, không sửa)* | Khối quảng bá Sun* Kudos + CTA `Chi tiết` | A1 | `app/_components/kudos-promo.tsx` |
| `getPageContext` *(tái dùng F002, không sửa)* | Điểm đọc locale + phiên đăng nhập dùng chung | A1 | `app/_page-context.ts` |
| `AwardSystemHero` *(planned)* | Keyvisual, chữ hình ROOT FURTHER, cụm eyebrow/đường kẻ/tiêu đề vàng | A1 | `TBD (draft)` — dự kiến `app/_components/award-system-hero.tsx` |
| `AwardSystemSection` *(planned)* | Bố cục hai cột: menu dính bên trái + cột sáu thẻ bên phải; dưới `lg` gộp một cột | A1 | `TBD (draft)` — dự kiến `app/_components/award-system-section.tsx` |
| `AwardCategoryNav` *(planned, Client Component)* | Sáu mục danh mục, trạng thái sáng, bấm nhảy, đọc hash lúc mount | A2 | `TBD (draft)` — dự kiến `app/_components/award-category-nav.tsx` |
| `AwardDetailCard` *(planned)* | Một thẻ chi tiết: ảnh 336×336, tiêu đề có biểu tượng, mô tả, số lượng, danh sách mức giải; đảo trái/phải theo chỉ số | A1 | `TBD (draft)` — dự kiến `app/_components/award-detail-card.tsx` |
| `AwardPrizeList` *(planned)* | Render danh sách mức giải theo BR-004 — nối `Hoặc` khi có nhiều mức, bỏ dòng ghi chú khi `note` trống | A1 | `TBD (draft)` — dự kiến `app/_components/award-prize-list.tsx` |
| `AwardQuantityLine` *(planned)* | Dòng `Số lượng giải thưởng:` kèm biểu tượng và giá trị | A1 | `TBD (draft)` — dự kiến `app/_components/award-quantity-line.tsx` |

*Sáu component `planned` ở trên là toàn bộ bề mặt UI mới. Bốn component tái dùng được nêu để nói rõ chúng
**không** được sao chép lại — DRY, và ORCH-03 khoá `home-nav.tsx`/`site-footer.tsx` ở chế độ chỉ đọc.*

### 4.2 Data Model

#### Key Entities

N/A — tính năng này không đọc hay ghi bảng dữ liệu nào (functional-spec.md § 1 Non-Scope; clarifications.md
assumption A2). Nội dung sáu giải là hằng số biên soạn từ thiết kế, tách hai lớp theo đúng mẫu F002:

| Nguồn | Nội dung | File |
|---|---|---|
| Module dữ liệu *(planned)* | *Identity* mỗi giải: `slug`, `key` (`AwardKey`), `image`, và thứ tự thiết kế | `TBD (draft)` — dự kiến `lib/award-system.ts` |
| Từ điển i18n *(planned)* | *Copy* mỗi giải dưới namespace mới `awardSystem`: tiêu đề, các đoạn mô tả, số lượng + đơn vị, danh sách mức giải; khoá bằng cùng `AwardKey`. Mở rộng `Dictionary` để một khoá thiếu ở EN là lỗi biên dịch (FR-002) | `TBD (draft)` — dự kiến `lib/i18n/messages/{vi,en}-award-system.ts` + `lib/i18n/messages/dictionary.ts` |

`AwardKey` và sáu tệp ảnh `award-*.png` dùng lại nguyên trạng từ F002 — không định nghĩa union thứ hai,
không xuất ảnh mới (clarifications.md — "Award images", "Where does the award detail copy live").

#### Polymorphic Behavior

N/A — no discriminator fields in Key Entities.

### 4.3 State Management

Một biến trạng thái cục bộ duy nhất trong `AwardCategoryNav` (A2): `activeSlug`, giá trị là một trong sáu
slug. **Không** mô hình hoá thành `SM-###`: sáu giá trị đó không phải sáu trạng thái có luật chuyển — mọi
thay đổi đều là phép gán trực tiếp từ một trong ba nguồn ghi ở A2, chuyển từ bất kỳ giá trị nào sang bất kỳ
giá trị nào, không có guard và không có transition bị cấm. Một `stateDiagram-v2` sáu đỉnh nối đầy đủ sẽ
không nói thêm điều gì mà rung `**Rule**` của A2 chưa nói. Thứ tự ưu tiên giữa ba nguồn ghi là BR-002, đã
nêu tại chỗ ở § 3.

### 4.4 Shared Rules

#### Bin 3 — cross-cutting, belongs to no single action

**A0 · FR-001 / FR-601 / BR-001 — `/awards-information` là route công khai, không thêm guard.** Đây là quy
tắc *cross-cutting*: nó áp cho toàn bộ route, không thuộc riêng A1 hay A2. Route guard hiện có của
F001_Login chỉ chặn `/todo` và `/login`, và tính năng này **không** sửa nó (clarifications.md ORCH-03 +
quyết định auth). Màn hình chỉ chứa nội dung công khai của mùa giải — không có dữ liệu người dùng, không có
thao tác ghi — nên không có gì cần chặn. Yêu cầu ngược lại của test ID-1 được ghi làm quyết định còn mở
(functional-spec.md § 3 D001, § 11 RISK-01), không phải yêu cầu triển khai.
**Source:** `TBD (draft)`

### 4.5 Algorithms & Integrations

### Chọn mục danh mục đang sáng theo vị trí cuộn (ALG-001)
**Linked FR:** FR-402
**Used in:** A2
**Source:** `TBD (draft)`
**Input:** vị trí sáu thẻ giải thưởng trong vùng nhìn · cờ khoá do cú bấm gần nhất đặt (BR-002) ·
**Output:** slug của hạng mục đang sáng · **Complexity:** O(1) mỗi lần vùng nhìn đổi (observer trả về đúng
các mục vừa cắt ngưỡng, không quét lại cả sáu thẻ mỗi khung hình)
**Description:** Theo dõi sáu thẻ bằng một observer với vùng quan sát thu hẹp về phía đỉnh khung nhìn. Trong
số các thẻ đang cắt vùng đó, chọn thẻ có cạnh trên gần đỉnh nhất — nhờ vậy thẻ cuối trang, dù không cao
bằng một màn hình, vẫn sáng được khi cuộn tới đáy. Khi cờ khoá của BR-002 đang bật (đang chạy cuộn mượt sau
một cú bấm), bỏ qua mọi cập nhật để mục sáng không nhấp nháy dọc đường cuộn.

**Pseudocode:**
```text
observe(sixCardElements, rootMargin: thu hẹp về đỉnh khung nhìn)

on intersectionChange(entries):
  if clickLockActive: return              # BR-002 — cú bấm thắng scroll-spy
  visible = entries.filter(isIntersecting)
  if visible.isEmpty: return              # giữ nguyên mục đang sáng
  activeSlug = visible.minBy(distanceFromViewportTop).slug

on click(item):
  clickLockActive = true
  activeSlug = item.slug
  scrollTo(item.card, behavior: prefersReducedMotion ? "instant" : "smooth")   # BR-003
  replaceHistoryEntry("#" + item.slug)    # FR-401 — thay thế, không thêm mục lịch sử
  clickLockActive = false  (sau khi cuộn dừng; ngay lập tức khi instant)

on mount:
  activeSlug = slugFromHash(location.hash) ?? firstSlug     # DEC-002
```

Không có `INT-###` — tính năng này không gọi dịch vụ ngoài nào.

### 4.6 Configuration

N/A — không có biến cấu hình nào cho tính năng này.

**Client behavior:** see `behavior-logic.md`, `permissions.md`, `architecture.md` — cả ba đều không đổi vì
tính năng này. Không có debounce/optimistic UI/polling/upload/realtime; bề mặt client duy nhất là một
observer theo vị trí cuộn (`ALG-001`, A2), không phải polling API (`behavior-logic.md` — không có logic nền
mới). Không có cổng chạy thời gian chạy nào mới (`permissions.md`). Không có service/layer/tích hợp/kho dữ
liệu mới (`architecture.md`).

## 5. Verification & Technical Notes

### 5.1 Technical Verification

- **SC-001** *(A1)* Mở `/awards-information` ở trạng thái chưa đăng nhập → ra nội dung thật (không phải shell
  "Coming soon"), không redirect (covers FR-001, FR-601, FR-201)
- **SC-002** *(A1)* Sáu thẻ hiện đúng thứ tự thiết kế, mỗi thẻ đủ ảnh/tiêu đề/mô tả/số lượng/giá trị giải,
  Top Talent hiện `10 Cá nhân` (covers FR-204, FR-205)
- **SC-003** *(A1)* Thẻ Signature hiện hai mức giải nối bằng `Hoặc`; Best Manager và MVP không có dòng ghi
  chú (covers FR-206)
- **SC-004** *(A2)* Bấm mục menu thứ n → trang cuộn tới thẻ thứ n, địa chỉ đổi thành `#<slug>`, đúng một mục
  sáng (covers FR-401, FR-402)
- **SC-005** *(A2)* Mở thẳng `/awards-information#mvp` → mục MVP sáng ngay khi trang mở (covers FR-102)
- **SC-006** *(A1)* Đổi ngôn ngữ sang EN → toàn bộ nội dung màn hình đổi theo, không còn chuỗi tiếng Việt
  (covers FR-002)
- **SC-007** *(A1)* Bấm `Chi tiết` ở khối Sun* Kudos → điều hướng `/kudos`, không 404 (covers FR-207)
- **SC-008** *(A1)* Không có nút widget nổi nào trong DOM của màn hình này (covers FR-208)

#### US007_BrowseAwardSystem *(A1)*

**Independent Test:** Mở `/awards-information` không cần đăng nhập, đối chiếu sáu thẻ với bảng nội dung đã
chốt trong `clarifications.md`, rồi đổi ngôn ngữ sang EN và đối chiếu lại.

**Acceptance Scenarios:**

1. **Given** khách chưa đăng nhập mở `/awards-information`, **When** trang tải xong, **Then** đủ năm khối
   hiện đúng thứ tự và sáu thẻ giải thưởng đủ nội dung.
2. **Given** khách đang xem trang ở tiếng Việt, **When** đổi sang EN, **Then** mọi chuỗi hiển thị đổi theo,
   không có ô trống và không còn chuỗi tiếng Việt.

#### US008_JumpToAwardCategory *(A2)*

**Independent Test:** Chạy trên trình duyệt thật để có vị trí cuộn thật; kiểm cả ba nguồn ghi mục sáng (bấm,
hash lúc mount, cuộn tay) và cả nhánh giảm chuyển động.

**Acceptance Scenarios:**

1. **Given** khách đang ở đầu trang, **When** bấm mục "MVP", **Then** trang cuộn tới thẻ MVP, địa chỉ đổi
   thành `#mvp`, và chỉ mục "MVP" sáng.
2. **Given** khách mở `/awards-information#khong-ton-tai`, **When** trang tải xong, **Then** mục đầu tiên
   sáng, trang mở từ đầu, không có cú nhảy và không có lỗi.

### 5.2 Assumptions

- *(A1)* Sáu ảnh giải thưởng, keyvisual, chữ hình ROOT FURTHER và nền khối Kudos dùng lại nguyên các tệp đã
  có từ F002 — đúng kích thước 336×336 mà thiết kế yêu cầu, không xuất mới (clarifications.md A1, A3).
- *(A1)* Nội dung sáu giải là hằng số biên soạn từ thiết kế, không có nguồn dữ liệu động phía sau; nếu sau
  này cần quản trị nội dung giải thưởng thì đó là một tính năng khác (clarifications.md A2).
- *(A1)* `HomeHeader`/`SiteFooter`/`KudosPromo` được compose nguyên trạng; trạng thái "Award Information"
  đang chọn đã tự đúng nhờ cách nav suy từ đường dẫn, nên không cần sửa gì ở đó (ORCH-03).
- *(A2)* Deep link từ trang chủ dùng đúng bộ slug mà F002 đã cố định — module dữ liệu mới phải tái dùng
  chính bộ slug đó, không định nghĩa lại, nếu không mọi liên kết `#<slug>` đang xanh sẽ trượt.

### 5.3 Unresolved Questions

- Tên tệp/component ở § 4.1 và § 4.2 là dự kiến (`TBD (draft)`) — chốt lúc triển khai; bản nháp này cố ý
  không đặt trước đường dẫn cho code chưa tồn tại.
- Câu hỏi thật sự còn mở là quyết định sản phẩm về test ID-1 (chặn hay không chặn khách chưa đăng nhập) —
  ghi ở `functional-spec.md` § 3 D001 và § 11 RISK-01, không phải câu hỏi kỹ thuật.

### 5.4 Source References

Chưa có mã nguồn — màn hình này chưa được viết. Hành vi dự kiến xem `functional-spec.md` § 7 User Stories và
§ 3 của file này. Các trích dẫn `**Source:**` thật được điền lúc promote, sau khi code tồn tại.

#### Data Flow

N/A — không có luồng dữ liệu ghi. A1 chỉ render, A2 chỉ đổi trạng thái cục bộ và vị trí cuộn (§ 4.2, § 4.3).

### 5.5 Artifact References

| Artifact | File | Codes Used | Reviewed |
|----------|------|------------|----------|
| Feature List | [feature-list.md](../../../../docs/generated/feature-list.md) | F003 | [ ] |
| Architecture | [architecture.md](../../../../docs/system/architecture.md) | `TBD (draft)` — không có trigger kiến trúc, xem § 4.6 | [ ] |
| Permissions | [permissions.md](../../../../docs/system/permissions.md) | `TBD (draft)` — không có trigger auth, xem § 4.4 | [ ] |
| Screens | [functional-spec.md § 6](./functional-spec.md#6-screens) | `TBD (draft)` — `SCR003_AwardSystem` dự kiến, cấp chính thức lúc promote | [ ] |
