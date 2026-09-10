---
status: draft
fcode: F009
authored_by: takumi
created: 2026-09-10
lang: vi
---

# F009_OpenSecretBox

## 1. Technical Overview

`/kudos/secret-box` đổi từ `ComingSoon` sang một Server Component đọc danh tính người xem
(`resolveViewer()`, đã có) và số hộp chưa mở của chính họ, rồi truyền các giá trị **đã giải
quyết** (số nguyên, boolean, chuỗi copy) xuống một Client Component giữ trạng thái bấm. Không
đối tượng `User` nào của Supabase vượt qua ranh giới đó — đúng ràng buộc `app/_page-context.ts`
đang giữ.

Đường ghi là một hàm Postgres duy nhất, `public.open_secret_box()`, `security definer`,
`set search_path = public`. Đây là điểm khác biệt cố ý so với `create_kudos()` (`security
invoker`): lần mở hộp phải **UPDATE** `sunners`, mà bảng đó không có — và không nên có — policy
UPDATE nào; mở một policy như vậy đồng nghĩa với việc cho phép bất kỳ phiên nào tự viết lại số
hộp của mình qua PostgREST, tức là chính lỗ hổng mà test case `5cc072ad` đi tìm. Hàm là người
ghi duy nhất, tự suy ra chủ thể từ `auth.uid()`, và không nhận tham số danh tính nào.

## 2. Action Index

| # | Action (handler) | Method · Path | Codes | Writes | Detail |
|---|---|---|---|---|---|
| **A0** | *cross-cutting* | — | FR-001, FR-601, BR-006 | — | § 4 |
| **A1** | `SecretBoxPage` *(planned)* | `GET` `/kudos/secret-box` | FR-101..FR-105, BR-001, BR-005, US001 | — *(read-only)* | § 3.1 |
| **A2** | `openSecretBox` Server Action → `rpc('open_secret_box')` *(planned)* | `POST` *(action)* | FR-201..FR-203, FR-602, BR-002, BR-003, BR-004, SM-001, US002 | `sunners`, `secret_box_openings` | § 3.2 |
| **A3** | `SecretBoxCloseButton` *(planned)* | — *(history)* | FR-301 | — | § 3.3 |

## 3. Actions

### 3.1 A1 — Đọc trạng thái màn

`app/kudos/secret-box/page.tsx` (Server Component):

1. `createClient()` → `resolveViewer(supabase)`.
2. `sunnerId === null` → trạng thái khoá: `unopenedCount = 0`, `canOpen = false`, hiện liên kết
   đăng nhập (FR-105). Không `redirect()`, không `notFound()` — route phải giữ `200` (FR-001).
3. Ngược lại đọc `secret_box_unopened_count` của chính dòng đó
   (`lib/secret-box/queries.ts`, một `select` duy nhất, `maybeSingle`).
4. `canOpen = unopenedCount > 0`.

`resolveSidebarSunnerId()` **không** dùng ở đây: đó là fallback *hiển thị* của sidebar, trỏ về
Sunner mẫu trong seed. Mở hộp của người khác vì mình chưa có dòng nào là sai về bản chất.

### 3.2 A2 — Mở hộp

Server Action `app/kudos/secret-box/_actions/open-secret-box.ts`:

```
'use server'
openSecretBox(): Promise<OpenSecretBoxResult>
```

Không tham số — mọi thứ suy ra từ phiên. Gọi `supabase.rpc('open_secret_box')`, trả về một
`OpenSecretBoxResult` phân biệt (`{ ok: true, badge, unopenedCount, openedCount }` |
`{ ok: false, reason: 'unauthenticated' | 'no-boxes' | 'failed' }`), rồi `revalidatePath` cho
`/kudos/secret-box`, `/kudos` và `/profile` để ba bộ đếm không nói khác nhau.

Hàm SQL, theo thứ tự:

1. `v_uid := auth.uid()`; null → `raise ... errcode '28000'`.
2. Giải/ cấp dòng `sunners` cho `v_uid` — sao lại nguyên khối provisioning của `create_kudos()`
   (tên/avatar từ JWT, phòng ban `Unassigned`, `on conflict (auth_user_id) do nothing`).
3. `update public.sunners set secret_box_unopened_count = secret_box_unopened_count - 1,
   secret_box_opened_count = secret_box_opened_count + 1
   where id = v_sunner_id and secret_box_unopened_count > 0
   returning secret_box_unopened_count, secret_box_opened_count`.
   Điều kiện `> 0` nằm **trong** câu UPDATE, không phải một câu SELECT kiểm tra trước: hai câu
   tách rời là một cửa sổ chạy đua mà hai tab cùng bấm sẽ lọt qua. `not found` → `errcode
   'P0002'` (`no_data_found`), Server Action dịch thành `reason: 'no-boxes'` (BR-004).
4. Rút huy hiệu theo trọng số tích luỹ trên `secret_box_badge_odds` join `rule_items`
   (BR-003, BR-005).
5. `insert into public.secret_box_openings (sunner_id, rule_item_id) values (...)`.
6. Trả về một dòng: `rule_item_id`, `label`, `image_path`, hai bộ đếm mới.

Cả năm bước nằm trong một lời gọi hàm, tức một transaction (FR-602).

### 3.3 A3 — Đóng

Dùng lại đúng khuôn `rules-panel-dismiss.tsx`: `navigation.canGoBack` (fallback
`history.length > 1`) → `router.back()`, ngược lại `router.push('/kudos')`. Không mở rộng
`use-dismiss-on-outside.ts` — hook đó cần `open`/`triggerRef` mà màn này không có.

## 4. Data Model

Migration mới, **chỉ thêm**:

```sql
create table public.secret_box_badge_odds (
  rule_item_id bigint primary key references public.rule_items (id) on delete cascade,
  weight smallint not null check (weight > 0)
);

create table public.secret_box_openings (
  id bigint generated always as identity primary key,
  sunner_id bigint not null references public.sunners (id),
  rule_item_id bigint not null references public.rule_items (id),
  opened_at timestamptz not null default now()
);
create index secret_box_openings_sunner_id_idx on public.secret_box_openings (sunner_id);
```

RLS bật trên cả hai. `secret_box_badge_odds`: `select` cho `anon`/`authenticated` (tỷ lệ là
thông tin công khai, đã in trong spec thiết kế). `secret_box_openings`: `select` chỉ những dòng
của chính mình, bắc qua `sunners.auth_user_id = (select auth.uid())`. **Không** policy
`insert`/`update`/`delete` ở đâu cả — hàm `security definer` là người ghi duy nhất, và im lặng
vẫn là từ chối, đúng như `20260907025909` đã dựa vào.

Seed sáu trọng số bằng `insert ... select` join theo `rule_items.label`, `on conflict do
nothing`, để migration chạy lại được và không phụ thuộc vào id cụ thể.

## 5. Risks

- **R1 — Rút song song.** Hai tab cùng bấm. Chống bằng điều kiện `> 0` đặt ngay trong UPDATE
  (§ 3.2 bước 3); tab thua cuộc nhận `no-boxes`, không có hộp nào bị trừ hai lần.
- **R2 — `security definer` là bề mặt đặc quyền.** Giảm thiểu: `search_path` ghim cứng, không
  tham số danh tính, `revoke execute ... from anon`, chỉ `grant execute ... to authenticated`.
- **R3 — Test case ACCESSING xung đột với hợp đồng route công khai đã ratify.** Giải: chặn ở
  tầng màn, không ở tầng route (clarifications.md).
- **R4 — K-21 đang khẳng định `/kudos/secret-box` render `ComingSoon`.** Assertion thật của nó
  là `200` + `main` + `main h1`; màn mới vẫn thoả cả ba. Tiêu đề của test cần sửa lại cho đúng
  sự thật, nhưng assertion thì không nới lỏng.

## 6. Test Strategy

`e2e/secret-box.spec.ts` (RED trước khi code), project `secret-box-authed` riêng với setup
riêng — cùng lý do đã buộc kudos/profile/homepage phải có setup riêng: `authenticated.spec.ts`
C9 đăng xuất toàn cục. Setup vừa tạo phiên, vừa cấp hộp cho chính user đó bằng service-role key
đọc lúc chạy từ `npx supabase status -o json` (không key nào nằm trong repo).

Phần anon (`00`, hộp khoá, `200`) chạy trong project `anon` sẵn có.
