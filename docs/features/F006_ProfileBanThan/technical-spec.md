---
status: implemented
fcode: F006
authored_by: takumi
created: 2026-09-08
lang: vi
---

# F006_ProfileBanThan

## 1. Technical Overview

Route `/profile` (đã tồn tại, hiện là `ComingSoon`) được thay bằng một Server Component thật, thêm vào danh sách guarded của `proxy.ts` (cùng nhóm `/todo`/`/kudos/new`), và tự re-check session lần nữa (defense in depth). MỘT nhánh dữ liệu duy nhất — `stats` là `null` với bất kỳ ai không phải chính viewer — quyết định card thống kê hay thanh viết Kudo, quyết định một lần ở tầng dữ liệu, không lặp lại ở từng component. `?id=` được shape-check `/^\d{1,18}$/` trước khi chạm database (id là `sunners.id bigint`, không phải uuid). Mục KUDOS phân trang thật bằng keyset cursor — lần đầu tiên của repo, khác với cách F004 đọc hết bảng rồi cắt phía client. Migration đi kèm đóng một lỗ bảo mật đang mở trên dữ liệu đã ship: `sender_id` của một Kudos ẩn danh hiện đọc được thẳng qua anon key; một view kiểu "security definer" che nó lại.

## 2. Action Index

| # | Action (handler) | Method · Path | Codes | Writes | Detail |
|---|---|---|---|---|---|
| **A0** | *cross-cutting — belongs to no single action* | — | FR-001, FR-101, FR-102, FR-603 | — | § 4.4 |
| **A1** | `ProfilePage#Page` (planned) | `GET` `/profile` | FR-002, FR-201, FR-202, FR-203, FR-204, FR-205, FR-206, FR-207, FR-208, FR-401, FR-402, BR-001, BR-002, BR-003, BR-004, BR-005, DEC-001, US001, US002, US003 | — *(read-only)* | § 3.1 |
| **A2** | `fetchProfileKudosPage` (planned, Server Action) | `POST` (server action) `/profile` | FR-403, FR-404, FR-601, FR-602, DEC-002, SM-001, US003 | — *(read-only)* | § 3.3 |
| **A3** | `toggleKudosLike` (existing — F004/F005, reused untouched) | `POST` (server action) | FR-405 | `kudos_likes` | § 3.4 |

## 3. Actions

### 3.1 CAP-01 — Xem hero và huy hiệu

#### A1 · Dựng `/profile`, resolve `?id=`, và render toàn bộ trang ở lần render đầu
`GET` `/profile` → `` `ProfilePage#Page` `` (planned)
`FR-002` `FR-201` `FR-202` `FR-203` `FR-204` `FR-205` `FR-206` `FR-207` `FR-208` `FR-401` `FR-402` · `US001` `US002` `US003`

**Who** · Sunner đã đăng nhập *(gate A0 — § 4.4, FR-101/FR-102)*
**FE** · Server Component, copy đọc từ khối `profile` của `Dictionary` (`FR-002`, `lib/i18n/messages/vi-profile.ts`/`en-profile.ts`) qua `getPageContext()`. Đọc `searchParams.id` (Next 16 async `searchParams`); nếu xuất hiện nhiều hơn một giá trị (`?id=1&id=2`) coi như không hợp lệ. Shape-check `/^\d{1,18}$/`; sai → `notFound()` ngay. Hợp lệ và rỗng/vắng mặt → `targetId = viewer.sunnerId`. Hợp lệ và có giá trị → `targetId = parsed`; nếu `targetId === viewer.sunnerId` thì coi là mặt tự-xem (không redirect, chỉ đổi nhánh render). Mọi tham số khác (`?q=`) bị bỏ qua hoàn toàn — không đưa vào logic resolve.
**Request** · `searchParams.id?: string | string[]`.
**BE** · `getProfileData(targetId, viewerSunnerId)` (planned, `lib/profile/profile-data.ts`) chạy song song (`Promise.all`, khuôn `getKudosBoard()`): (1) hồ sơ mục tiêu từ `sunners` (id, full_name, avatar_url, department, kudos_received_baseline) — không có dòng nào khớp → `notFound()`; (2) tổng Kudos đã nhận của mục tiêu (đếm qua `kudos_readable`) để tính `badgeTierFor`; (3) nếu `targetId === viewerSunnerId`: 5 chỉ số thống kê (BR-003/BR-004) — nếu KHÔNG: `null`; (4) trang 1 của feed "Đã nhận" (10 dòng, keyset, § 4.5 ALG-002) qua `kudos_readable`.
**Rule**
- **BR-001 — Session đã đăng nhập nhưng chưa có dòng `sunners`.** Khi `viewerSunnerId === null` VÀ `targetId` cũng resolve về chính viewer (không có `?id=` thật để tra), render hero rỗng: tên/avatar suy từ `auth.jwt() -> 'user_metadata'` theo đúng chuỗi fallback `create_kudos()` đã dùng (`full_name`→`name`→email local-part; `avatar_url`→`picture`→ảnh mẫu `public/images/kudos/sample-avatar.png`), 0 mọi chỉ số, feed rỗng, 6 ô huy hiệu xám, không huy hiệu Hero (0 Kudos khác ngưỡng thấp nhất của `badgeTierFor`). Không ghi gì — GET không tạo dòng `sunners`. *(inline)*
- **BR-002 — Huy hiệu Hero dùng nguyên `badgeTierFor()` (`lib/kudos/derive.ts`, đã ship, không sửa).** Khoá theo tổng Kudos đã nhận, không phải số người gửi khác nhau. *(§ 4.4)*

| DEC | subtype | Condition | What the user sees | Source |
|---|---|---|---|---|
| **DEC-001** | render | `direction === "received"` (giá trị khởi tạo, luôn luôn — không đọc trạng thái mock của frame) | Dropdown trigger hiện "Đã nhận (N)" active khi trang vừa render, kể cả trên hồ sơ chính mình | `app/profile/page.tsx:1` (planned) |

**Result** · Không ghi DB. Trả về `ProfileViewModel` (§ 4.2) cho hai Client Component con: `KudosDirectionSection` (dropdown + feed, § 3.3) nhận trang 1 + cursor đã đọc sẵn (không fetch lại ngay khi mount); phần còn lại (hero, huy hiệu, card thống kê/thanh viết Kudo) render thẳng ở Server Component, không cần hydrate.
**Source:** TBD (draft)

<!-- Không có diagram: đọc dữ liệu (sunners + kudos_readable), không ghi bảng nào, không phải hành động nền — dưới ngưỡng cả hai tiêu chí. -->

---

### 3.2 CAP-02 — Xem thống kê cá nhân hoặc gửi Kudo

Nhánh thống kê/viết-Kudo (`stats` null hay không) được quyết định NGAY TRONG `A1` (§ 3.1, rung
**BE**/**Result**) — không có handler riêng, vì đây là đúng MỘT giá trị tính một lần ở server, không
phải một tương tác riêng. `FR-203`/`FR-204`/`BR-003`/`BR-004` đã được nêu đủ ở § 3.1; mục này chỉ
tồn tại để khớp một-bucket-một-CAP với `functional-spec.md § 2`.

---

### 3.3 CAP-03 — Đổi chiều và cuộn thêm mục KUDOS

Dropdown chiều và feed nằm trong một Client Component (`KudosDirectionSection`, con của A1) quản lý `direction`/`cursor`/`cards` cục bộ; chỉ việc LẤY TRANG TIẾP THEO (đổi chiều hoặc cuộn) cần một round-trip server vì mỗi trang mới là một truy vấn keyset thật, không phải một lát cắt của dữ liệu đã có sẵn trên client (khác hẳn `all-kudos-feed.tsx` của F004 — ADV-1, hai chiến lược cùng tồn tại có chủ đích).

#### A2 · Lấy trang KUDOS tiếp theo (đổi chiều hoặc cuộn)
`POST` (server action) `/profile` → `` `fetchProfileKudosPage` `` (planned)
`FR-403` `FR-404` `FR-601` `FR-602` · `US003`

**Who** · Sunner đã đăng nhập *(gate A0)*
**FE** · Đổi chiều dropdown: xoá `cards`/`cursor` cục bộ ngay (không hiện danh sách cũ), gọi A2 với `direction` mới và `cursor: null`; chỉ cập nhật nhãn trigger SAU khi trang mới đã về (FR-403). Cuộn tới `feed-sentinel`: tái dùng `useInfiniteFeed` (`app/kudos/_components/use-infinite-feed.ts`, hook có sẵn, không sửa) — `onIntersect` gọi A2 với `cursor` hiện tại, chiều không đổi. Chọn lại đúng chiều đang active: không gọi A2 (DEC-002, chặn tại client).
**Request** · `{ targetSunnerId: number; direction: "received" | "sent"; cursor: { sentAt: string; id: number } | null }`. `targetSunnerId` chỉ có ý nghĩa cho `direction: "received"`; bị BỎ QUA hoàn toàn khi `direction === "sent"` (BE luôn dùng session, không bao giờ tham số client — xem Rule).
**BE** · Với `direction === "received"`: `select ... from kudos_readable where receiver_id = :targetSunnerId and (sent_at, id) < (:cursor.sentAt, :cursor.id) order by sent_at desc, id desc limit FEED_PAGE_SIZE + 1` (đọc dư 1 dòng để biết `hasMore`, không trả dòng thừa cho client). Với `direction === "sent"`: đúng câu trên nhưng `where sender_id = :callerSunnerId` — `callerSunnerId` suy từ `resolveViewer(supabase).sunnerId` bên trong action, KHÔNG BAO GIỜ lấy từ `targetSunnerId` của request (FR-601). `direction === "sent"` mà `callerSunnerId === null` (chưa có dòng `sunners`) trả về trang rỗng, không lỗi.
**Rule**
- **BR — Chiều "Đã gửi" luôn tự-scoped, không bao giờ nhận id mục tiêu từ client.** `WHERE sender_id = callerSunnerId` (suy từ session) là biên bảo mật — không phải việc ẩn tuỳ chọn "Đã gửi" trên giao diện của hồ sơ người khác (đó chỉ là lớp thứ hai). Ngay cả khi một request thủ công gửi `direction: "sent"` kèm `targetSunnerId` của người khác, kết quả vẫn luôn là Kudos của CHÍNH người gọi. *(§ 4.4, cross-cutting — claimed by A0)*
- **BR-005 — Mỗi dòng trả về qua đúng mapper của bảng tin** (`toKudosCardView`-tương-đương, tái dùng logic `board-data.ts` mapping — không viết lại). Với `direction === "sent"` và dòng đó `is_anonymous = true` với `sender_id = callerSunnerId`: hiển thị chính caller là tác giả (không dùng `anonymousSenderLabel`), nhưng field `is_anonymous` gốc vẫn giữ `true` nội bộ — không tính lại thành "không ẩn danh". *(§ 4.4, SEC_002)*

**Result** · Không ghi DB. Trả `{ cards: KudosCardView[]; nextCursor: {sentAt, id} | null; hasMore: boolean }`. Client nối `cards` vào danh sách hiện có (chiều không đổi) hoặc thay hẳn danh sách (chiều vừa đổi).
**Source:** TBD (draft)

<!-- Không có diagram: đọc, không ghi bảng nào, không phải hành động nền. -->

---

### 3.4 CAP-03 — Thả tim, hashtag, Copy Link (tái dùng nguyên vẹn)

#### A3 · Thả/bỏ tim một Kudo trong feed hồ sơ
`POST` (server action, đã tồn tại) → `` `toggleKudosLike` `` (F004/F005, không sửa)
`FR-405`

**Who** · Sunner đã đăng nhập, không phải người gửi Kudo đó *(gate A0; BR-003 của F004 vẫn áp dụng)*
**FE** · Nút tim trên `KudosCard` (component tái dùng, § 4.1) gọi thẳng `toggleKudosLike(kudosId)` — không có wrapper riêng cho màn hồ sơ.
**Request** · `kudosId: number`.
**BE** · Y hệt hôm nay — xem `app/kudos/_actions/toggle-kudos-like.ts:59-117`. Không sửa file này.
**Result** · Số tim trả về từ server, không cộng dồn phía client (K-25, `plans/260906-1945-kudos-live-board/`).
**Source:** `app/kudos/_actions/toggle-kudos-like.ts:59-117` *(existing — action này đã tồn tại và không đổi; citation hợp lệ, không phải fabricated draft citation)*

Bấm hashtag: điều hướng tới `/kudos?hashtag=<tag>` qua `Link`, tái dùng nguyên `KudosHashtagRow` — không handler riêng, không route mới. Copy Link: tái dùng nguyên toast/hàm copy hiện có trong `KudosCardActions` — không sửa.

### 3.5 Edge cases

| Action | Scenario | Behavior |
|---|---|---|
| A0 | Khách chưa đăng nhập vào thẳng `/profile` | `proxy.ts` chuyển hướng `/login` trước khi A1 chạy |
| A1 | `?id=1&id=2` | Coi là không hợp lệ, `notFound()` — không chọn giá trị nào |
| A1 | `?id=` là chuỗi không khớp `/^\d{1,18}$/` | `notFound()` ngay, không có truy vấn database nào chạm `id` đó |
| A1 | `?id=` hợp lệ nhưng không khớp dòng `sunners` nào | `notFound()` |
| A1 | `?id=` khớp chính `viewer.sunnerId` | Canonical hoá về mặt tự-xem, không redirect |
| A1 | `?q=anything` (ô tìm kiếm Sunner) đi kèm | Bị bỏ qua, vẫn render mặt tự-xem |
| A2 | `direction: "sent"` kèm `targetSunnerId` của người khác (request thủ công, bỏ qua UI) | Server vẫn chỉ trả Kudos của chính người gọi — `targetSunnerId` bị bỏ qua cho chiều này |
| A2 | Đổi chiều khi trang trước còn đang fetch (double-click) | Trang cũ bị huỷ kết quả nếu về sau lần đổi chiều mới nhất (client giữ một request-id tăng dần, bỏ response cũ hơn request đang active) |

## 4. Shared Foundation

### 4.1 Components

| Component | Responsibility | Used in | File |
|---|---|---|---|
| `ProfilePage` (planned) | Server Component route — resolve `?id=`, gọi `getProfileData`, render hero/huy hiệu/nhánh thống kê-viết-Kudo, truyền trang 1 KUDOS xuống | A1 | `app/profile/page.tsx` (thay nội dung `ComingSoon` hiện có) |
| `ProfileHero` (planned) | Keyvisual + avatar + tên + phòng ban + huy hiệu Hero + tiêu đề huy hiệu | A1 | `app/profile/_components/profile-hero.tsx` |
| `ProfileBadgeRow` (planned) | 6 ô vòng tròn xám cố định `#323231`, con trực tiếp của `ProfileHero` (AMEND-2 — không phải section riêng) | A1 | `app/profile/_components/profile-badge-row.tsx` |
| `ProfileStatsCard` (planned) | 5 hàng chỉ số + nút "Mở Secret Box" `disabled` — chỉ render khi `stats !== null`. *Từ 2026-09-10 (F009), nút này là `<Link href="/kudos/secret-box">` thật, không còn `disabled`.* | A1 | `app/profile/_components/profile-stats-card.tsx` |
| `WriteKudoBar` (planned) | Thanh viết Kudo nêu tên, link `/kudos/new?receiverId=` — chỉ render khi `stats === null` | A1 | `app/profile/_components/write-kudo-bar.tsx` |
| `KudosDirectionSection` (planned, Client Component) | Dropdown chiều + feed + cuộn vô hạn, state cục bộ, gọi A2 | A1 (con), A2 | `app/profile/_components/kudos-direction-section.tsx` |
| `KudosCard` (existing, F004 — tái dùng nguyên vẹn) | Thẻ Kudos, che tên ẩn danh, tim/hashtag/Copy Link | A2, A3 | `app/kudos/_components/kudos-card.tsx` (KHÔNG sửa) |
| `fetchProfileKudosPage` (planned) | Server Action — trang KUDOS tiếp theo, keyset | A2 | `app/profile/_actions/fetch-profile-kudos-page.ts` |

### 4.2 Data Model

Không bảng mới. Một VIEW mới và hai thay đổi quyền trên bảng đã có — xem Security bên dưới. Không cột nào trên `sunners`/`kudos`/`spotlight_ticker_events` bị đổi.

#### Key Entities

| Entity | Table/View | Key Columns | Purpose |
|--------|-------|-------------|---------|
| Kudos đọc-an-toàn (mới) | `public.kudos_readable` (view) | Toàn bộ cột `kudos` (§ dưới), `sender_id` bị null hoá có điều kiện | Nguồn đọc DUY NHẤT cho mọi Kudos kể từ bản vẽ này — thay `public.kudos` tại ba call site (§ Security) |
| Sunner (không đổi) | `sunners` | *(không đổi)* | Đọc hồ sơ mục tiêu + đếm Kudos qua `kudos_readable` |
| Spotlight events (không đổi, chỉ ghi nhận invariant) | `spotlight_ticker_events` | `sunner_id` | **Invariant:** `sunner_id` LUÔN LÀ NGƯỜI NHẬN của `kudos_id` tương ứng — đo được trên dữ liệu thật (7/7 dòng khớp receiver, 0/7 khớp sender). Bảng này KHÔNG cần sửa vì không thể lộ người gửi ẩn danh qua cách nó được dùng hôm nay; ghi lại ở đây để một người viết sau không vô tình đổi `sunner_id` thành sender và mở lại lỗ vừa đóng. |

#### Security — view đọc an toàn cho Kudos ẩn danh

**Vấn đề đo được (không phải suy đoán):** `kudos_select_all` là `for select to anon, authenticated using (true)`, và `queries.ts:fetchKudos` (dòng 53) embed `sender:sunners!kudos_sender_id_fkey(...)` cho MỌI dòng, kể cả dòng ẩn danh. Bất kỳ ai cầm anon key (ship theo trình duyệt, có chủ đích) chạy được `select sender_id, is_anonymous from kudos` và de-anonymize toàn bộ Kudos ẩn danh trong bảng. Việc ẩn số "Đã gửi" của người khác (SEC_001) chỉ là màn kịch nếu truy vấn đó vẫn mở.

**Thiết kế** (không set `security_invoker` — mặc định `false`, PG15+ — nên view chạy dưới quyền chủ
sở hữu và vẫn đọc được `public.kudos` sau khi revoke bên dưới; cơ chế Postgres tương đương "security
definer" cho VIEW):

```sql
create view public.kudos_readable as
select
  k.id,
  case
    when k.is_anonymous
     and k.sender_id is distinct from (
       select s.id from public.sunners s where s.auth_user_id = (select auth.uid())
     )
    then null
    else k.sender_id
  end as sender_id,
  k.receiver_id, k.campaign, k.message, k.sent_at,
  k.heart_baseline, k.message_format, k.is_anonymous, k.anonymous_name
from public.kudos k;

revoke select on public.kudos from anon, authenticated;
grant select on public.kudos_readable to anon, authenticated;
```

**Cột:** đúng 10 cột của `kudos` hôm nay, không thêm không bớt — `sender_id` là cột duy nhất bị biến đổi. Predicate định danh caller: `k.sender_id is distinct from (select s.id from sunners where auth_user_id = (select auth.uid()))`, đúng idiom bắc cầu `sunners.auth_user_id = auth.uid()` mà `resolveViewer()`/policy INSERT của F005 đã dùng.

**Ba call site được trỏ lại view** (blast radius đo được, không ước lượng):
1. `lib/kudos/queries.ts:53` (`fetchKudos` — `.from("kudos")` → `.from("kudos_readable")`).
2. `app/kudos/_actions/toggle-kudos-like.ts:26` (`readHeartState` — đọc `heart_baseline` + `likes`).
3. `app/kudos/_actions/toggle-kudos-like.ts:73` (đọc `sender_id` để kiểm BR-003 "không tự thả tim").

`lib/supabase/database.types.ts` cần regenerate (`supabase gen types typescript --local`) sau migration để `kudos_readable` có type — không hand-edit file này.

#### Polymorphic Behavior

N/A — no discriminator fields in Key Entities. `kudos_readable.sender_id` là một cột bị NULL hoá có
điều kiện, không phải một discriminator kiểu `message_format` (`'plain' \| 'doc'`, F005) — nó không
đủ điều kiện DISC-###.

### 4.3 State Management

**SM-001 — `KudosDirectionSection` (kind: ui, ≥3 trạng thái).**

| State | Trigger | Note |
|---|---|---|
| `idle` | Trang 1 đã có sẵn từ A1 (SSR), chưa tương tác | Hiện `cards` ban đầu |
| `switching` | Vừa đổi chiều, đang chờ A2 trang 1 của chiều mới | `cards` cũ đã bị xoá khỏi state; trigger label CHƯA đổi (FR-403) |
| `loading-more` | Đang cuộn, đang chờ A2 trang tiếp theo cùng chiều | `cards` hiện tại vẫn hiển thị, sentinel chờ |
| `settled` | A2 trả về, `hasMore === false` | Hiện thông báo kết thúc feed, sentinel unmount (tái dùng cơ chế `useInfiniteFeed`) |

Không có state machine nào khác đạt ngưỡng phân loại — nhánh `stats`/`writeKudoBar` là một giá trị tính một lần ở server (§ 4.2), không phải state client.

### 4.4 Shared Rules

#### Bin 2

- **FR-603 — Không cột hồ sơ nào ngoài tập được phép từng được select.** `getProfileData` chỉ đọc `id, full_name, avatar_url, department, kudos_received_baseline` từ `sunners` — không `auth_user_id`, không email (không có cột email trên `sunners`; `resolveViewer().userId` không bao giờ rời server, đúng khuôn F004). **Used in:** A1, A2.
- **FR-601 — Chiều "Đã gửi" luôn tự-scoped.** `WHERE sender_id = callerSunnerId` suy từ session, không bao giờ từ `targetSunnerId` của request. **Used in:** A1 (trang 1, khi mặt tự-xem), A2 (mọi trang sau).

#### Bin 3

- **BR — Không request nào của màn hình này chấp nhận actor id từ client cho một thao tác ghi.** Duy nhất thao tác ghi trên trang này (thả tim, A3) đã là idiom có sẵn của F004/F005 — không đổi. **Claimed by:** A0.
- **BR — Auth guard hai lớp.** `proxy.ts` (route) + tự resolve lại session trong A1 (page) — cùng khuôn `/kudos/new` đã ship (xem § 2 Action Index, hàng A0). **Claimed by:** A0.

### 4.5 Algorithms & Integrations

### Keyset cursor cho phân trang KUDOS thật (ALG-002)
**Linked FR:** FR-404
**Used in:** A1 (trang 1), A2 (mọi trang sau)
**Source:** `TBD (draft)`

`order by sent_at desc, id desc`; cursor = `{sentAt, id}` của dòng cuối trang vừa trả; trang tiếp theo lọc `(sent_at, id) < (cursor.sentAt, cursor.id)` (row comparison, ổn định kể cả khi hai dòng trùng `sent_at`). Đọc dư 1 dòng mỗi lần để suy `hasMore` mà không cần `count(*)` riêng. Tái dùng `FEED_PAGE_SIZE` (`lib/kudos/derive.ts:13`, không sửa) — khác cách F004's `all-kudos-feed.tsx` cắt phía client trên dữ liệu đã fetch hết (ADV-1, hai chiến lược cố ý cùng tồn tại, xem § 5.3).

### 4.6 Configuration

None — `FEED_PAGE_SIZE` là hằng số tái dùng, không phải cấu hình mới của bản vẽ này.

**Client behavior:** see behavior-logic.md, permissions.md, architecture.md

## 5. Verification & Technical Notes

### 5.1 Technical Verification

- **SC-001** *(A1)* `?id=` sai định dạng, không tồn tại, hoặc lặp lại KHÔNG BAO GIỜ tạo ra một truy vấn Postgres mang giá trị thô của tham số đó — `notFound()` xảy ra trước bước đọc.
- **SC-002** *(A1)* `stats !== null` khi và chỉ khi `targetId === viewer.sunnerId` — một nhánh dữ liệu duy nhất, không có component nào tự kiểm tra lại "đây có phải hồ sơ của tôi không".
- **SC-003** *(A2)* Với `direction: "sent"`, đổi `targetSunnerId` trong request KHÔNG đổi kết quả trả về — chứng minh bằng cách gửi hai `targetSunnerId` khác nhau cùng một session và so hai response.
- **SC-004** *(A1, A2)* `kudos_readable` không bao giờ trả `sender_id` thật của một dòng `is_anonymous = true` cho một session không phải người gửi — kiểm bằng cách so kết quả `select` trực tiếp (nếu còn quyền, phải KHÔNG còn) và qua view.

### 5.2 Assumptions

- **A1 — `?id=` là `sunners.id` bigint** (kế thừa từ `clarifications.md` A1) — thiết kế không vẽ URL, tham số suy từ schema + ý định test case.
- **A2 — RETIRED.** Đã là "stars derived from tier" — bị AMEND-1 rút lại hoàn toàn: không có hoa-thị stars nào được implement, không `starCountFor`.
- **A3 — Thứ tự 6 ô huy hiệu lấy từ thứ tự node B2→B7 của frame** (kế thừa `clarifications.md` A3) — không artwork nào gán cho từng ô (AMEND-2).
- **A4 — Session đã đăng nhập không có dòng `sunners` render hồ sơ rỗng, không 404** (kế thừa `clarifications.md` A4).
- **A5 — `/profile?q=…` render mặt tự-xem** (kế thừa `clarifications.md` A5) — kết quả tìm kiếm là commission khác.
- **A6 — Dropdown mặc định "Đã nhận" active, không phải "Đã gửi (5)" của frame** (AMEND — frame chỉ chụp một khoảnh khắc mock).
- **A7 — Field CSV "typed status" (GUI_007 note) không tạo type mới ở bản vẽ này.** `KudosCardView` đã đủ để không render chip Spam (chỉ cần không render nó); một field `status` riêng cho card, nếu cần, là việc của người xây kiểm duyệt sau này — thêm nó bây giờ mà không dùng tới là suy đoán ngoài phạm vi (YAGNI).

### 5.3 Unresolved Questions

1. **PostgREST embedding qua view có cột `CASE`-biến-đổi (`kudos_readable.sender_id`) chưa được xác minh trên chính instance này.** Postgres theo dõi dependency của view lên `kudos.sender_id` dù nó nằm trong một `CASE` (nên PostgREST NHIỀU KHẢ NĂNG vẫn suy được quan hệ `sender_id -> sunners` để `sender:sunners!kudos_sender_id_fkey(...)` tiếp tục embed đúng), nhưng đây là suy luận từ cách PostgREST introspect, không phải một phép đo trên database đang chạy. Người triển khai PHẢI xác nhận bằng cách chạy đúng câu `select` của `fetchKudos` nhắm vào `kudos_readable` trước khi coi migration là xong; nếu embed không tự suy ra, phương án dự phòng là truyền embed hint tường minh hoặc tách các cột `sunners` liên quan thành cột phẳng ngay trong view thay vì dựa vào embedding quan hệ. Xem `## Spec-author concerns`.
2. **ADV-1** (advisory, out of scope): F004's `fetchKudos` đọc hết bảng rồi cắt phía client; feed hồ sơ dùng keyset cursor thật. Hai chiến lược cùng tồn tại — đáng hợp nhất khi bảng lớn hơn vài trăm dòng.
3. **ADV-2** (advisory, out of scope): không có ràng buộc `kudos_no_self`; việc từ chối tự-gửi Kudo chỉ nằm ở chỗ không có thanh viết Kudo nào mời gọi thao tác đó trên hồ sơ chính mình.

### 5.4 Source References

<!-- Các file dưới đây ĐÃ TỒN TẠI trong repo hôm nay — không phải Source rung của một action chưa viết code, mà là các file có sẵn bản vẽ này phụ thuộc vào / sẽ sửa. -->

| Action | Order | Symbol | Path | Purpose |
|---|---|---|---|---|
| — | 1 | `Page` placeholder hiện tại | `app/profile/page.tsx:1-15` | Nội dung sẽ bị thay thế; route đã tồn tại, hiện render `ComingSoon` |
| A0 | 2 | route guard | `proxy.ts:47-51` | `isGuarded` hiện chỉ xét `/todo` và `/kudos/new`; bản vẽ này thêm `/profile` |
| A0, A1 | 3 | `resolveViewer` | `lib/kudos/viewer.ts:37-59` | Identity `sunnerId`/`userId` — tái dùng nguyên vẹn, không sửa |
| A1 | 4 | `getPageContext` | `app/_page-context.ts:27-42` | Mẫu đọc `locale`/`dictionary`/`isAuthenticated` |
| A1, A2, A3 | 5 | `fetchKudos` | `lib/kudos/queries.ts:51-67` | Query cần trỏ lại `kudos_readable`; mapping logic (hashtags/attachments/likes) tái dùng nguyên |
| A1 | 6 | `badgeTierFor`, `FEED_PAGE_SIZE` | `lib/kudos/derive.ts:13-21` | Tái dùng nguyên, không sửa |
| A1 | 7 | `KudosCard` | `app/kudos/_components/kudos-card.tsx:89-191` | Component thẻ tái dùng nguyên vẹn cho feed hồ sơ |
| A2 | 8 | `toggleKudosLike` | `app/kudos/_actions/toggle-kudos-like.ts:59-117` | Action tim tái dùng nguyên, không sửa |
| A0 | 9 | INSERT/SELECT policy idiom | `supabase/migrations/20260906140914_kudos_live_board.sql:161-179` | `kudos_select_all`/`kudos_likes_insert_own` — migration mới REVOKE nửa đầu, thêm view mới |
| A0 | 10 | `create_kudos()` fallback chain | `supabase/migrations/20260907025909_viet_kudo_write_path.sql` (hàm `create_kudos`) | Chuỗi fallback tên/avatar từ JWT — BR-001 dùng lại nguyên logic (đọc, không gọi hàm) |
| FR-003 | 11 | link tên Sunner | `app/kudos/_components/sunner-chip.tsx:69`, `app/kudos/_components/gift-leaderboard.tsx:57`, `app/_components/account-menu.tsx:93` | Ba nơi phát `href="/profile"` — hai nơi đầu đổi sang `?id={sunnerId}`; `account-menu.tsx` giữ nguyên bare `/profile` (menu của chính mình, không có id nào để mang) |
| FR-003 | 12 | e2e assertion cần amend | `e2e/kudos-live-board.spec.ts:354,356` | So khớp `toHaveAttribute("href", "/profile")` — đổi sang mẫu `/profile\?id=\d+$` |
| — | 13 | search box đã ship | `app/kudos/_components/kudos-hero.tsx:76-89` | `<form action="/profile" method="get" name="q">` — A5, không được phá vỡ |
| A1, A2 | 14 | database types | `lib/supabase/database.types.ts` | Cần regenerate sau migration; không hand-edit |

#### Data Flow

```text
{Sunner bấm tên trên bảng tin/menu tài khoản} -> {GET /profile?id=... hoặc /profile} -> {proxy.ts guard (A0)} -> {A1 resolve id (shape-check -> notFound / self-canonical / other), đọc sunners + kudos_readable} -> {render hero+badges, nhánh stats/write-bar theo targetId===viewer, KudosDirectionSection với trang 1}
{Sunner đổi chiều hoặc cuộn} -> {A2 keyset query trên kudos_readable, sent luôn tự-scoped} -> {client nối/thay cards}
{Sunner thả tim} -> {A3 (existing, không đổi)}
```

### 5.5 Artifact References

| Artifact | File | Codes Used | Reviewed |
|----------|------|------------|----------|
| System Overview | [system-overview.md](../../../../docs/system/overview.md) | — | [ ] |
| Architecture (delta) | [architecture.md](../system/architecture.md) | — | [ ] |
| Permissions (delta) | [permissions.md](../system/permissions.md) | — | [ ] |
| Feature List | [feature-list.md](../../../../docs/generated/feature-list.md) | TBD (draft) | [ ] |
| Entities | [entities.md](../../../../docs/generated/entities.md) | TBD (draft) | [ ] |
| Screens | [functional-spec.md § 6](./functional-spec.md#6-screens) | TBD (draft) | [ ] |
| User Stories | [user-stories.md](../../../../docs/generated/user-stories.md) | TBD (draft) | [ ] |

## Spec-author concerns

- **PostgREST FK-embedding qua một view với cột `CASE`** (§ 4.2, § 5.3 mục 1) là điểm tôi tin tưởng nhất nhưng không thể đo được từ vị trí một spec-author (không viết code trong commission này). Thiết kế chính vẫn là view + `CASE`-mask vì nó đúng với "một view, một predicate" mà `clarifications.md` yêu cầu; nhưng nếu PostgREST không tự suy được quan hệ, người triển khai cần biết fallback ngay từ đầu thay vì phát hiện giữa chừng — đã ghi cả hai ở § 5.3.
- **Đánh số FR/BR/DEC/US.** Brief giao việc yêu cầu "tiếp nối từ F005, không restart ở 1". Tôi đã đo trực tiếp: cả 5 `functional-spec.md` đã ship (F001–F005) đều RESTART cục bộ theo từng feature (F002 có `FR-001` riêng, F003 có `FR-001` riêng, …), và `spec-authoring-contract.md` § "Per-section authoring rules" xác nhận "Author FR-### one-liners... banded... per template" không nói gì về nối tiếp toàn cục — chỉ `US###` có ghi chú "Allocate LOCALLY". Tôi theo đúng cái đã đo được trên 5 feature file thật thay vì literal của brief, vì một FR-001 mới trùng số với FR-001 của F001–F005 là bình thường trong repo này (mỗi feature một namespace cục bộ) — không phải một collision thật.
- **Huy hiệu Hero khoá theo tổng nhận, không phải số người gửi khác nhau** (BR-002) — CSV thiết kế có ghi chú ngược lại, nhưng `badgeTierFor()` đã ship và ratify cho F004 dùng đúng tổng nhận; giữ một hàm một luật quan trọng hơn theo đúng ghi chú của một CSV không phải nguồn hành vi (test case + code đã ship mới là).
