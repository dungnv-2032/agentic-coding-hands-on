---
status: implemented
fcode: F003
authored_by: takumi
created: 2026-09-06
lang: vi
---

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

Màn hình công khai tại `/awards-information`, thay chỗ shell `ComingSoon` từng chiếm route đó. Một Server
Component đọc locale + phiên đăng nhập qua `getPageContext()` (dùng chung với trang chủ, không thêm điểm
đọc thứ hai) rồi render toàn bộ nội dung tĩnh: hero, sáu thẻ giải thưởng, và các thành phần chrome tái
dùng nguyên trạng của F002 (`HomeHeader`, `KudosPromo`, `SiteFooter`). Chỉ menu danh mục bên trái là Client
Component — nó theo dõi vị trí cuộn để đổi mục đang sáng và xử lý cú bấm. Không có endpoint mới, không có
bảng dữ liệu, không có thao tác ghi; `proxy.ts` không bị đụng tới (clarifications.md ORCH-03 + quyết định
auth). Dữ liệu giải thưởng tách hai lớp theo đúng mẫu F002 đã dựng: *identity* (slug, khoá từ điển, ảnh)
trong `lib/awards.ts` dùng chung với trang chủ, *đơn vị* trong `lib/award-system.ts`, và *copy* (tiêu đề,
mô tả, số lượng, mức giải) trong từ điển i18n dưới namespace `awardSystem`, khớp nhau bằng cùng một
`AwardKey`.

Một hằng số CSS duy nhất — `--award-header-offset` — được ba nơi cùng đọc: `top` của menu dính,
`scroll-margin-top` của mỗi thẻ, và dải đo của scroll-spy. Ở `lg` giá trị bị ghim cứng bằng class
`lg:[--award-header-offset:112px]` (`app/awards-information/page.tsx:32`); dưới `lg` header xuống nhiều
dòng nên chiều cao thật của nó được đo và công bố lên `<html>`.

## 2. Action Index

| # | Action (handler) | Method · Path | Codes | Writes | Detail |
|---|---|---|---|---|---|
| **A0** | *cross-cutting — belongs to no single action* | — | FR-001, FR-601, BR-001 | — | § 4.4 |
| **A1** | `` `AwardsInformationPage#render` `` | `GET` `/awards-information` | FR-002, FR-101, FR-201, FR-202, FR-204, FR-205, FR-206, FR-207, FR-208, BR-004, US007 | — *(read-only)* | § 3.1 |
| **A2** | `` `AwardCategoryNav#interact` `` *(client-only)* | *(client state — no HTTP)* | FR-102, FR-203, FR-401, FR-402, FR-403, BR-002, BR-003, BR-005, DEC-002, US008 | — *(client state only)* | § 3.1 |

## 3. Actions

### 3.1 CAP-01 — Đọc hệ thống giải thưởng SAA 2025

#### A1 · Render màn hình hệ thống giải
`GET` `/awards-information` → `` `AwardsInformationPage#render` ``
`FR-002` `FR-101` `FR-201` `FR-202` `FR-204` `FR-205` `FR-206` `FR-207` `FR-208` `BR-004` `US007` · `SCR003_AwardSystem`

**Who** · Khách truy cập (đã đăng nhập hay chưa đều xem được — FR-001, § 4.4)
**FE** · Server Component render năm khối theo thứ tự thiết kế (FR-201): `HomeHeader` tái dùng nguyên trạng
— mục "Award Information" tự sáng vì `home-nav.tsx:59` so `usePathname()` với `href` của từng mục, nên
không sửa gì ở đó (FR-101, ORCH-03); `AwardSystemHero` gồm ảnh keyvisual (CSS background, vì crop của
frame không diễn đạt được bằng `object-fit`) + chữ hình ROOT FURTHER + cụm eyebrow/đường kẻ/`<h1>` vàng
canh giữa (FR-202); phần hệ thống giải gồm `AwardCategoryNav` (A2) dính bên trái và sáu `AwardDetailCard`
xen kẽ ảnh trái/ảnh phải theo chỉ số chẵn/lẻ, dưới `lg` gộp về một cột với ảnh lên trước (FR-204, FR-205);
`KudosPromo` tái dùng, truyền `maxWidthClass="max-w-[1440px]"` cho artboard 1440 của màn hình này
(FR-207, ORCH-05); `SiteFooter` tái dùng nguyên trạng. `FloatingWidget` **không** render ở màn hình này
(FR-208). Mọi chuỗi hiển thị lấy từ từ điển đã phân giải theo locale (FR-002) — không có chuỗi cứng trong
component. `AWARDS` (`lib/awards.ts`) là nguồn duy nhất quyết định thứ tự và danh tính, dùng chung cho cả
menu lẫn danh sách thẻ, nên hai danh sách không thể lệch nhau.
**Request** · không có tham số — trang tĩnh, không dùng `searchParams`; `#<slug>` là fragment nên không tới
server.
**BE** · không có — thuần render phía server. Nội dung sáu giải là dữ liệu tĩnh biên soạn từ thiết kế
(clarifications.md — "Use Figma design content as mock data source"), không phải bảng dữ liệu (§ 4.2).
**Rule** ·

**BR-004 — Giá trị giải là một danh sách, không phải hai trường phẳng.** Mỗi giải mang một danh sách mức
giải, mỗi mức gồm số tiền và một ghi chú tuỳ chọn: bốn giải có đúng một mức kèm ghi chú, Signature có hai
mức nối nhau bằng dòng `Hoặc`, Best Manager và MVP có một mức không ghi chú. Nhờ vậy component render đúng
một dạng dữ liệu cho cả sáu thẻ và không rẽ nhánh theo tên giải; `note` là khoá tuỳ chọn (không phải chuỗi
rỗng) nên "không có ghi chú" là một sự thật ở mức kiểu, và không có phần tử rỗng nào được sinh ra
(`award-prize-list.tsx:61-65`). Đây là quy tắc về hình dạng dữ liệu, không phải một nhánh quyết định —
không cấp mã `DEC-###`. *(FR-206)*
**Result** · Chỉ render — không ghi dữ liệu. Bấm `Chi tiết` ở khối Kudos điều hướng `/kudos` (FR-207); các
lối ra khác thuộc header/footer tái dùng, không phải hành vi mới của action này.
**Source:** `app/awards-information/page.tsx:55-125` · `app/awards-information/_components/{award-system-hero,award-detail-card,award-prize-list,award-system-icons}.tsx` · `app/_page-context.ts:27-41`

<!-- Không cần sequence diagram: read-only, không ghi bảng nào, không phải background/async action. -->

---

#### A2 · Menu danh mục — scroll-spy, bấm nhảy, và deep link *(client-only)*
*(client state — no HTTP)* → `` `AwardCategoryNav#interact` ``
`FR-102` `FR-203` `FR-401` `FR-402` `FR-403` `BR-002` `BR-003` `BR-005` `DEC-002` `US008` · `SCR003_AwardSystem`

**Who** · Khách truy cập đang đọc màn hình hệ thống giải
**FE** · `AwardCategoryNav` là Client Component duy nhất của tính năng này. Nó render sáu mục theo đúng thứ
tự thiết kế, mỗi mục là một `<a href="#slug">` thật có biểu tượng 24×24 phía trước; mục đang sáng đổi sang
chữ vàng + gạch chân vàng và mang `aria-current="true"` (FR-203). Trạng thái sáng giữ trong `activeSlug`
(§ 4.3), do hook `useAwardScrollSpy` sở hữu — hook tách riêng khỏi component để cả hai file nằm dưới trần
200 dòng; component giữ phần hiển thị, hook giữ hình học và thời gian. Hai nguồn ghi vào `activeSlug`: cú
bấm của người dùng (FR-401) và `ALG-001` chạy theo vị trí cuộn (FR-402, § 4.5). **Hash không phải nguồn thứ
ba** — nó chỉ quyết định vị trí cuộn lúc mount, xem DEC-002.
**Request** · không có — mọi tương tác ở đây là trạng thái phía client, không phát sinh HTTP request nào.
**BE** · không có.
**Rule** ·

**BR-002 — Menu luôn có đúng một mục đang sáng.** `activeSlug` là một giá trị đơn, không phải tập hợp, nên
"chỉ một mục sáng" là bất biến của kiểu dữ liệu chứ không phải một bước dọn dẹp phải nhớ chạy. Cú bấm bật
một cờ khoá để `ALG-001` không làm mục sáng nhấp nháy dọc đường cuộn mượt; khoá đó hết hạn sau 700ms
(`SCROLL_SETTLE_MS`), hoặc **ngay lập tức** khi người dùng lăn chuột/chạm/bấm phím — vì lúc đó thao tác của
người dùng mới là đầu vào gần nhất. Nhả khoá luôn chạy lại phép đo vị trí, nên trạng thái không kẹt ở mục
đã bấm khi cú cuộn kết thúc mà không có sự kiện giao cắt nào mới. *(FR-402)*

**BR-003 — Người dùng bật giảm chuyển động thì nhảy tức thì.** Đọc `prefers-reduced-motion` tại đúng lúc
bấm và chọn kiểu cuộn tương ứng — `smooth` khi không bật, `auto` khi có bật; khoá chống nhấp nháy của
BR-002 khi đó hết hạn sau 0ms vì không còn quãng cuộn nào để bảo vệ. *(FR-403)*

**BR-005 — Không bao giờ rơi về không mục nào.** Khi không thẻ nào nằm trong dải đo: nếu thẻ đầu tiên đã
nằm dưới đáy dải (người dùng đang ở hero) thì mục đầu tiên sáng lại, đúng như thiết kế vẽ ở vị trí đó; nếu
không (người dùng đang ở vùng footer, dưới thẻ cuối) thì giữ nguyên mục hiện tại. Bất đối xứng có chủ đích:
xoá trắng sẽ phá bất biến "đúng một mục" mà test ID-9/11 khẳng định. *(FR-402)*

Quyết định vị trí và trạng thái lúc mở trang:

| DEC | subtype | Condition | What the user sees | Source |
|---|---|---|---|---|
| **DEC-002** | interaction, flow | `location.hash` khớp một slug trong danh sách sáu giải | Trang nhảy thẳng tới thẻ đó (`behavior: "auto"` — người dùng đang *tới nơi*, không có gì để diễn hoạt). Mục menu tương ứng sáng lên ngay sau khi hydrate, do phép đo vị trí — **không** do một `setState` từ hash | `use-award-scroll-spy.ts:143-147` |
| **DEC-002** | interaction, flow | không có hash, hoặc hash không khớp slug nào | Không cuộn, mục đầu tiên (Top Talent) sáng, không có lỗi console | `use-award-scroll-spy.ts:31,143-147` |

*Vì sao hash không ghi thẳng vào `activeSlug`: fragment không bao giờ được gửi lên server, nên HTML server
render bắt buộc sáng `AWARDS[0]`. Một `useState` khởi tạo từ `location.hash` sẽ render `top-talent` ở
server và `mvp` ở client — hydration mismatch, làm hỏng assertion "không lỗi console" của ID-13. Đánh đổi
được chấp nhận là một khoảng ~290ms sau khi tải, chỉ ở lối vào deep link (functional-spec.md § 11 RISK-04,
clarifications.md ORCH-04).*

**Result** · Chỉ đổi trạng thái cục bộ và vị trí cuộn — không ghi dữ liệu, không gọi API. Cú bấm cập nhật
địa chỉ trang thành `#<slug>` bằng `history.replaceState` chứ không thêm mục lịch sử mới, để nút Back vẫn
quay về trang trước chứ không lùi qua từng hạng mục vừa xem (FR-401). Cú bấm có phím bổ trợ (Ctrl/Cmd/
Shift/Alt) hoặc bằng nút chuột khác được trả lại cho trình duyệt xử lý như liên kết thường; `href` là thật,
không phải `href="#"` giả.
**Source:** `app/awards-information/_components/award-category-nav.tsx:36-88` · `app/awards-information/_components/use-award-scroll-spy.ts:30-195`

<!-- Không cần sequence diagram: không ghi bảng nào, không phải background action; toàn bộ nội dung là
     một biến trạng thái với hai nguồn ghi, đã nêu đủ ở rung Rule + ALG-001. -->

### 3.2 Edge cases

| Action | Scenario | Behavior |
|---|---|---|
| A1 | Khách chưa đăng nhập mở trang | Trang render đầy đủ, không redirect — route công khai theo BR-001 (§ 4.4) |
| A1 | Một giải chỉ có một mức và không có ghi chú | Chỉ render số tiền, không sinh phần tử ghi chú rỗng (BR-004) |
| A2 | Hash không khớp slug nào | Bỏ qua hash, mục đầu tiên sáng, không có cú nhảy, không có lỗi (DEC-002) |
| A2 | Người dùng bật giảm chuyển động | Nhảy tức thì thay vì cuộn mượt; mục sáng vẫn đúng (BR-003) |
| A2 | Cuộn ngược lên hero | Mục đầu tiên sáng lại (BR-005) |
| A2 | Cuộn tới đáy trang, dưới thẻ cuối | Giữ nguyên mục cuối đang sáng (BR-005) |
| A2 | Lăn chuột/chạm/bấm phím trong lúc cuộn mượt sau cú bấm | Khoá nhả ngay, mục sáng trả về hạng mục thật sự trên màn hình (BR-002) |
| A2 | Client Component chưa hydrate | Sáu thẻ và menu vẫn đọc được vì nội dung do server render; chỉ mục sáng chưa tự chạy theo cuộn |

## 4. Shared Foundation

### 4.1 Components

| Component | Responsibility | Used in | File |
|---|---|---|---|
| `HomeHeader` *(tái dùng F002, không sửa)* | Logo, nav 3 mục (mục "Award Information" tự sáng trên route này), bộ chọn ngôn ngữ, chuông + tài khoản khi đã đăng nhập | A1 | `app/_components/home-header.tsx` |
| `SiteFooter` *(tái dùng F002, không sửa)* | Footer 4 liên kết + bản quyền | A1 | `app/_components/site-footer.tsx` |
| `KudosPromo` *(tái dùng F002, thêm một prop tuỳ chọn)* | Khối quảng bá Sun* Kudos + CTA `Chi tiết`. Nhận `maxWidthClass?: "max-w-[1224px]" \| "max-w-[1440px]"`, mặc định là giá trị của trang chủ — trang chủ không truyền gì và render y như cũ (ORCH-05) | A1 | `app/_components/kudos-promo.tsx:21-38` |
| `getPageContext` *(tái dùng F002, không sửa)* | Điểm đọc locale + phiên đăng nhập dùng chung | A1 | `app/_page-context.ts` |
| `AwardsInformationPage` | Page Server Component: đọc context, ghim `--award-header-offset` ở `lg`, ghép năm khối, zip `AWARDS` với copy từ điển | A1 | `app/awards-information/page.tsx` |
| `AwardSystemHero` | Keyvisual (CSS background, crop riêng của frame), chữ hình ROOT FURTHER, cụm eyebrow/đường kẻ/`<h1>` vàng | A1 | `app/awards-information/_components/award-system-hero.tsx` |
| `AwardCategoryNav` *(Client Component)* | Sáu mục danh mục, trạng thái sáng, xử lý cú bấm, `aria-current` | A2 | `app/awards-information/_components/award-category-nav.tsx` |
| `useAwardScrollSpy` *(hook, client)* | Hình học và thời gian của A2: đo header, scroll-spy, khoá cú bấm, cuộn deep link | A2 | `app/awards-information/_components/use-award-scroll-spy.ts` |
| `AwardDetailCard` | Một thẻ chi tiết: `<section>` có `aria-labelledby`, ảnh 336×336, `<h2>` có biểu tượng, mô tả, số lượng, danh sách mức giải; đảo trái/phải theo chỉ số | A1 | `app/awards-information/_components/award-detail-card.tsx` |
| `AwardPrizeList` | Render danh sách mức giải theo BR-004 — chèn dòng `Hoặc` giữa các mức, bỏ ghi chú khi `note` vắng mặt | A1 | `app/awards-information/_components/award-prize-list.tsx` |
| `IconTarget` / `IconDiamond` / `IconLicense` | Ba biểu tượng SVG inline của màn hình (`MM_MEDIA_Target`, `Diamond`, `License`) | A1, A2 | `app/awards-information/_components/award-system-icons.tsx` |

*Bốn component ở đầu bảng là của F002 và được compose lại, **không** sao chép — DRY, và ORCH-03 khoá
`home-nav.tsx`/`site-footer.tsx` ở chế độ chỉ đọc. `kudos-promo.tsx` là file dùng chung duy nhất bị sửa,
và chỉ để nhận một prop có giá trị mặc định.*

*Ghi chú so với bản nháp: `AwardSystemSection` và `AwardQuantityLine` **không** được dựng thành component
riêng — bố cục hai cột nằm thẳng trong `page.tsx` và dòng số lượng nằm trong `AwardDetailCard`. Đổi lại,
bản nháp không dự đoán `useAwardScrollSpy` (tách ra ở trần 200 dòng) và `award-system-icons.tsx`.*

### 4.2 Data Model

#### Key Entities

N/A — tính năng này không đọc hay ghi bảng dữ liệu nào (functional-spec.md § 1 Non-Scope; clarifications.md
assumption A2). Nội dung sáu giải là hằng số biên soạn từ thiết kế, tách ba lớp:

| Nguồn | Nội dung | File |
|---|---|---|
| `lib/awards.ts` *(tái dùng F002, không sửa)* | *Identity* mỗi giải: `slug`, `key` (`AwardKey`), `image`, và thứ tự thiết kế | `lib/awards.ts:27-42` |
| `lib/award-system.ts` | *Đơn vị* mỗi giải: `AwardUnitKey` = `individual \| team \| individualOrTeam`, và `AWARD_UNITS: Record<AwardKey, AwardUnitKey>` — exhaustive, nên một giải thứ bảy thêm vào `AwardKey` không biên dịch được cho tới khi khai báo đơn vị | `lib/award-system.ts:18-32` |
| Từ điển i18n | *Copy* mỗi giải dưới namespace `awardSystem`: hero, nhãn, `units`, và `cards` (tiêu đề, nhãn menu, các đoạn mô tả, số lượng, danh sách mức giải); khoá bằng cùng `AwardKey`. `Dictionary` được mở rộng để một khoá thiếu ở EN là lỗi biên dịch (FR-002) | `lib/i18n/messages/dictionary.ts:112-146`, `lib/i18n/messages/{vi,en}-award-system.ts`, gắn vào `lib/i18n/messages/{vi,en}.ts` |

`AwardKey`, `AwardSlug` và sáu tệp ảnh `award-*.png` dùng lại nguyên trạng từ F002 — **không** định nghĩa
union thứ hai, vì trang chủ deep-link tới `/awards-information#<slug>` và hai danh sách slug lệch nhau sẽ
âm thầm làm hỏng mọi liên kết đó (`lib/award-system.ts:7-12`). Không xuất ảnh mới.

#### Polymorphic Behavior

N/A — no discriminator fields in Key Entities.

### 4.3 State Management

Một biến trạng thái cục bộ duy nhất, `activeSlug`, sở hữu bởi `useAwardScrollSpy`
(`use-award-scroll-spy.ts:31`), giá trị là một trong sáu slug và khởi tạo bằng slug đầu tiên. **Không** mô
hình hoá thành `SM-###`: sáu giá trị đó không phải sáu trạng thái có luật chuyển — mọi thay đổi đều là phép
gán trực tiếp từ một trong hai nguồn ghi ở A2, chuyển từ bất kỳ giá trị nào sang bất kỳ giá trị nào, không
có guard và không có transition bị cấm. Ngoài nó còn hai ref không phải state hiển thị: cờ khoá của cú bấm
và bộ đếm giờ nhả khoá (`:32-33`). Thứ tự ưu tiên giữa hai nguồn ghi là BR-002, đã nêu tại chỗ ở § 3.

### 4.4 Shared Rules

#### Bin 3 — cross-cutting, belongs to no single action

**A0 · FR-001 / FR-601 / BR-001 — `/awards-information` là route công khai, không có guard.** Đây là quy
tắc *cross-cutting*: nó áp cho toàn bộ route, không thuộc riêng A1 hay A2. Route guard hiện có của
F001_Login chỉ chặn `/todo` và `/login` (`proxy.ts:41-46`), và tính năng này **không** sửa nó
(clarifications.md ORCH-03 + quyết định auth). Màn hình chỉ chứa nội dung công khai của mùa giải — không có
dữ liệu người dùng, không có thao tác ghi — nên không có gì cần chặn. Yêu cầu ngược lại của test ID-1 được
ghi làm quyết định còn mở (functional-spec.md § 3 D001, § 11 RISK-01), không phải yêu cầu triển khai.

Đầu vào duy nhất chịu ảnh hưởng của bên ngoài trên màn hình này là `location.hash`; nó được đối chiếu với
danh sách slug cố định **trước khi** tới `getElementById` (`use-award-scroll-spy.ts:145`), nên một fragment
tuỳ ý không chọn được phần tử nào và im lặng không làm gì.
**Source:** `proxy.ts:41-46` · `app/awards-information/page.tsx:55-56` · `app/awards-information/_components/use-award-scroll-spy.ts:143-147`

### 4.5 Algorithms & Integrations

### Chọn mục danh mục đang sáng theo vị trí cuộn (ALG-001)
**Linked FR:** FR-402
**Used in:** A2
**Source:** `app/awards-information/_components/use-award-scroll-spy.ts:81-105` *(phép đo)*, `:149-165` *(observer)*, `:114-136` *(nhả khoá)*
**Input:** vị trí sáu thẻ giải thưởng so với dải đo · cờ khoá do cú bấm gần nhất đặt (BR-002) ·
**Output:** slug của hạng mục đang sáng · **Complexity:** O(6) mỗi lần vùng nhìn đổi — sáu phép
`getBoundingClientRect`, không quét lại mỗi khung hình
**Description:** `IntersectionObserver` chỉ dùng làm *cò kích hoạt*, không làm nguồn dữ liệu: callback của
nó chỉ thấy các mục vừa đổi trạng thái trong lô đó, nên dưới một cú vuốt nhanh nó có thể xếp hạng một thẻ
đã rời dải đo. Mỗi lần bị kích hoạt, `resolveActive()` đo lại **cả sáu** thẻ theo hình học sống: dải đo
chạy từ `--award-header-offset` (đỉnh, dưới header dính) tới 45% chiều cao khung nhìn (đáy, khớp với
`rootMargin: -55%`). Trong số các thẻ cắt dải, chọn thẻ có cạnh trên gần đỉnh dải nhất. Không thẻ nào cắt
dải thì áp BR-005. Khi cờ khoá của cú bấm đang bật, bỏ qua hoàn toàn.

**Pseudocode:**
```text
observe(sixCardElements, rootMargin: `-${headerOffset}px 0px -55% 0px`)

on intersectionChange():                  # cò kích hoạt, không đọc entries
  if clickLockActive: return              # BR-002 — cú bấm thắng scroll-spy
  resolveActive()

resolveActive():
  bandTop    = readOffset()               # --award-header-offset, đọc từ cascade
  bandBottom = viewportHeight * 0.45
  best = null
  for slug in slugs:
    rect = getBoundingClientRect(slug)
    if rect.bottom <= bandTop or rect.top >= bandBottom: continue
    if best is null or |rect.top - bandTop| < best.distance: best = slug
  if best: activeSlug = best; return
  # BR-005 — không thẻ nào trong dải
  if top(firstSlug) >= bandBottom: activeSlug = firstSlug    # đang ở hero
  # ngược lại (vùng footer): giữ nguyên mục hiện tại

on click(item):
  clickLockActive = true
  activeSlug = item.slug
  scrollTo(item.card, behavior: prefersReducedMotion ? "auto" : "smooth")   # BR-003
  replaceHistoryEntry("#" + item.slug)    # FR-401 — thay thế, không thêm mục lịch sử
  releaseLock after (prefersReducedMotion ? 0 : 700ms)

on wheel | touchstart | keydown:          # BR-002 — người dùng ghi đè cú bấm
  releaseLock()                           # nhả khoá rồi chạy lại resolveActive()

on mount:
  if hash matches a slug: scrollIntoView(hash, behavior: "auto")   # DEC-002 — chỉ vị trí
```

Không có `INT-###` — tính năng này không gọi dịch vụ ngoài nào.

### 4.6 Configuration

N/A — không có biến cấu hình nào cho tính năng này.

**Client behavior:** không có debounce/optimistic UI/polling/upload/realtime; bề mặt client duy nhất là
scroll-spy `ALG-001` (A2), đã được ghi vào `docs/generated/behavior-logic.md` § Client-Side Logic. Không có
cổng chạy thời gian chạy nào mới (`permissions.md`, `permissions-matrix.md` — hàng `/awards-information`
vốn đã là Allow/Allow/Allow, không đổi). Không có service/layer/tích hợp/kho dữ liệu mới
(`architecture.md`) — cả hai trigger kiến trúc và auth đều **không** kích hoạt cho màn hình này, đã đối
chiếu lại với code lúc promote: `proxy.ts` không có commit nào sau `949f5b0`, không có route handler mới,
không có bảng dữ liệu, không có phụ thuộc ngoài mới.

## 5. Verification & Technical Notes

### 5.1 Technical Verification

- **SC-001** *(A1)* Mở `/awards-information` ở trạng thái chưa đăng nhập → ra nội dung thật (không phải shell
  "Coming soon"), không redirect (covers FR-001, FR-601, FR-201) — `e2e/award-system.spec.ts` ID-0/2, ID-3
- **SC-002** *(A1)* Sáu thẻ hiện đúng thứ tự thiết kế, mỗi thẻ đủ ảnh/tiêu đề/mô tả/số lượng/giá trị giải,
  Top Talent hiện `10 Cá nhân` (covers FR-204, FR-205) — ID-6, ID-7
- **SC-003** *(A1)* Thẻ Signature hiện hai mức giải nối bằng `Hoặc`; Best Manager và MVP không có dòng ghi
  chú (covers FR-206) — ID-6
- **SC-004** *(A2)* Bấm mục menu thứ n → trang cuộn tới thẻ thứ n, địa chỉ đổi thành `#<slug>`, đúng một mục
  sáng (covers FR-401, FR-402) — ID-9/11
- **SC-005** *(A2)* Mở thẳng `/awards-information#mvp` → trang dừng ở thẻ MVP và mục MVP sáng (covers
  FR-102) — test "Deep link"
- **SC-006** *(A1)* Đổi ngôn ngữ sang EN → toàn bộ nội dung màn hình đổi theo, không còn chuỗi tiếng Việt
  (covers FR-002) — **chưa có test tự động**, xem functional-spec.md § 11 RISK-05
- **SC-007** *(A1)* Bấm `Chi tiết` ở khối Sun* Kudos → điều hướng `/kudos`, không 404 (covers FR-207) — ID-12
- **SC-008** *(A1)* Không có nút widget nổi nào trong DOM của màn hình này (covers FR-208) — ID-3 khẳng định
  thứ tự khối, không khẳng định trực tiếp sự vắng mặt của widget; đã đối chiếu bằng đọc code
  (`page.tsx:64-124` không import `FloatingWidget`)

**Kết quả đo thật (2026-09-06, seal round):** `npx playwright test e2e/award-system.spec.ts --project=anon`
exit **0** — 14 passed (13 test của màn hình + 1 setup project); `e2e/homepage.spec.ts --project=anon` exit
**0** — 22 passed; `npx playwright test --project=anon` exit **0** — 54 passed. `npx tsc --noEmit` exit
**0**. Bằng chứng: `plans/260906-0719-award-system-screen/reports/tester-260906-0935-award-system-delivery-verification.md`.

#### US007_BrowseAwardSystem *(A1)*

**Independent Test:** Mở `/awards-information` không cần đăng nhập, đối chiếu sáu thẻ với bảng nội dung đã
chốt trong `clarifications.md`, rồi đổi ngôn ngữ sang EN và đối chiếu lại.

**Acceptance Scenarios:**

1. **Given** khách chưa đăng nhập mở `/awards-information`, **When** trang tải xong, **Then** đủ năm khối
   hiện đúng thứ tự và sáu thẻ giải thưởng đủ nội dung.
2. **Given** khách đang xem trang ở tiếng Việt, **When** đổi sang EN, **Then** mọi chuỗi hiển thị đổi theo,
   không có ô trống và không còn chuỗi tiếng Việt.

#### US008_JumpToAwardCategory *(A2)*

**Independent Test:** Chạy trên trình duyệt thật để có vị trí cuộn thật; kiểm cả hai nguồn ghi mục sáng
(bấm, cuộn tay), nhánh deep link, và nhánh giảm chuyển động.

**Acceptance Scenarios:**

1. **Given** khách đang ở đầu trang, **When** bấm mục "MVP", **Then** trang cuộn tới thẻ MVP, địa chỉ đổi
   thành `#mvp`, và chỉ mục "MVP" sáng.
2. **Given** khách mở `/awards-information#khong-ton-tai`, **When** trang tải xong, **Then** mục đầu tiên
   sáng, trang mở từ đầu, không có cú nhảy và không có lỗi console.

### 5.2 Assumptions

- *(A1)* Sáu ảnh giải thưởng, keyvisual, chữ hình ROOT FURTHER và nền khối Kudos dùng lại nguyên các tệp đã
  có từ F002 — khâu kiểm thử đo được cả sáu ảnh đúng 336×336 (clarifications.md A1, A3).
- *(A1)* Nội dung sáu giải là hằng số biên soạn từ thiết kế, không có nguồn dữ liệu động phía sau; nếu sau
  này cần quản trị nội dung giải thưởng thì đó là một tính năng khác (clarifications.md A2).
- *(A1)* `HomeHeader`/`SiteFooter` được compose nguyên trạng; `KudosPromo` chỉ nhận thêm một prop có mặc
  định. Trạng thái "Award Information" đang chọn tự đúng nhờ `usePathname()` (ORCH-03).
- *(A2)* Deep link từ trang chủ dùng đúng bộ slug mà F002 đã cố định — `lib/award-system.ts` cố ý **không**
  định nghĩa lại bộ slug đó.
- *(A2)* Ở `lg`, `--award-header-offset` bị ghim bằng class `112px` nên hình học desktop mà khâu kiểm thử
  đã đo không thể bị thay đổi lúc chạy; dưới `lg`, giá trị là chiều cao header đo được + 40px.

### 5.3 Unresolved Questions

- Quyết định sản phẩm về test ID-1 (chặn hay không chặn khách chưa đăng nhập) — functional-spec.md § 3 D001
  và § 11 RISK-01. Không phải câu hỏi kỹ thuật.
- Test case ID-14 chưa chạy được chừng nào `/kudos` còn là shell `ComingSoon` (RISK-02).
- Hai follow-up ghi nhận ở functional-spec.md § 12: FUP-01 (header dính không có backdrop blur — khiếm
  khuyết có sẵn của `home-header.tsx`) và FUP-02 (cột `w-[60px]` chật với copy EN).
- Có nên nâng `timeout` mỗi test trong `playwright.config.ts` để CI có khoảng đệm trước lần biên dịch route
  nguội hay không — khuyến nghị của khâu kiểm thử, chưa áp dụng.

### 5.4 Source References

| Action | File | Lines |
|---|---|---|
| A1 | `app/awards-information/page.tsx` | 55-125 |
| A1 | `app/awards-information/_components/{award-system-hero,award-detail-card,award-prize-list,award-system-icons}.tsx` | toàn file |
| A1 | `app/_page-context.ts` | 27-41 |
| A1 | `app/_components/kudos-promo.tsx` | 21-38 (prop `maxWidthClass`) |
| A1 | `lib/award-system.ts` | 18-32 |
| A1 | `lib/i18n/messages/dictionary.ts` | 112-146 |
| A1 | `lib/i18n/messages/{vi,en}-award-system.ts` | toàn file |
| A2 | `app/awards-information/_components/award-category-nav.tsx` | 36-88 |
| A2 | `app/awards-information/_components/use-award-scroll-spy.ts` | 30-195 |
| A0 | `proxy.ts` | 41-46 (không sửa — chỉ trích dẫn) |

#### Data Flow

N/A — không có luồng dữ liệu ghi. A1 chỉ render, A2 chỉ đổi trạng thái cục bộ và vị trí cuộn (§ 4.2, § 4.3).

### 5.5 Artifact References

| Artifact | File | Codes Used | Reviewed |
|----------|------|------------|----------|
| Feature List | [feature-list.md](../../generated/feature-list.md) | F003 | [x] |
| Route List | [route-list.md](../../generated/route-list.md) | ROUTE005 | [x] |
| Architecture | [architecture.md](../../system/architecture.md) | — (narrative, no per-code cite; không có trigger kiến trúc — xem § 4.6) | [x] |
| Permissions | [permissions.md](../../system/permissions.md) | — (narrative, no per-code cite; không có trigger auth — xem § 4.4) | [x] |
| Screens | [functional-spec.md § 6](./functional-spec.md#6-screens) | SCR003_AwardSystem | [x] |
