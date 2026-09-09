# Phase 03 — Migration hai bảng + seed + `db:types`

## Context Links

- `research/researcher-01-supabase-and-i18n-conventions.md § 1, § 2, § 5` — khuôn migration, seed, regen types
- `clarifications.md § "Content source — the Supabase requirement"` — quyết định hai bảng + `kind`
- `clarifications.md § "Resolved from source data"` — **nguồn duy nhất** của mọi chuỗi seed
- `spec/the-le/technical-spec.md § 4.2` — cột, khoá, hành vi polymorphic
- `spec/system/permissions.md` — RLS là tiền lệ ràng buộc mọi bảng sau F004
- House style: `supabase/migrations/20260906140914_kudos_live_board.sql`, `supabase/seed.sql`

## Overview

- **Priority**: P1
- **Status**: **completed** — schema, RLS, grants và 13 dòng seed đúng như § Architecture. Một chuỗi
  seed đã phải sửa lại sau đó (`ROOT FUTHER` → `ROOT FURTHER`); xem § "Sai lệch so với kế hoạch".
- **Description**: Tạo `public.rule_sections` + `public.rule_items` với RLS public-read, seed toàn bộ
  nội dung thể lệ phiên âm nguyên văn từ frame, rồi sinh lại `lib/supabase/database.types.ts`. Đây là
  màn hình đầu tiên của repo có **nội dung biên tập nằm trong database**.

## Key Insights

1. **Hai bảng, không phải ba.** `rule_items.kind` là discriminator (`hero_tier` | `collectible_icon`);
   hai danh sách khác nhau đúng ở chỗ *cột nào được điền*, không ở hình dạng. Ba bảng sẽ là một bảng
   cho mỗi tiêu đề Figma — bố cục rò rỉ vào schema.
2. **`closing_body` là cột, không phải một `rule_sections` thứ tư.** Dòng `Những Sunner thu thập trọn
   bộ 6 icon…` render SAU lưới icon của mục 2, nên nó thuộc về mục 2, không phải một mục riêng.
   Nullable — chỉ mục 2 dùng.
3. **Không `ON CONFLICT`.** `supabase db reset` truncate sạch trước khi chạy seed; header của
   `seed.sql` nói thẳng "plain inserts are re-runnable". Thêm `ON CONFLICT` là đi ngược idiom.
4. **`notify pgrst, 'reload schema';` sau grants** — bỏ qua thì PostgREST trả 404 trông y hệt một bug
   code (researcher-01 § 1).
5. **`database.types.ts` được track, không gitignore, không sửa tay.** Sinh bằng `npm run db:types`
   và commit kèm.
6. **Ba chỗ "trông như lỗi" phải giữ nguyên**: en-dash trong `Có 10–20 người gửi Kudos cho bạn`,
   en-dash trong mô tả bậc 1 (`bắt đầu –`) và bậc 4 (`huyền thoại –`), và `ROOT FUTHER` (thiếu chữ R).
   Sửa "chính tả" ở đây là bịa dữ liệu.

## Requirements

- **FR-001** — hai bảng, RLS bật, đúng một policy `<table>_select_all` `for select to anon,
  authenticated using (true)`, `grant select` tường minh, KHÔNG policy ghi
- **FR-002** — seed toàn bộ nội dung, phiên âm nguyên văn, insert phẳng
- **FR-004** — `npm run db:types` sau migration, commit file sinh ra
- **FR-205** — ảnh trên đĩa, row chỉ giữ `image_path`; không nhị phân trong DB, không Storage bucket
- **FR-601** — hai bảng chỉ đọc được cho cả `anon` lẫn `authenticated`; không đường ghi nào
- **BR-001** — `position` là cột sắp xếp, `unique` để ngăn trùng thứ tự

## Architecture

```sql
create table public.rule_sections (
  id bigint generated always as identity primary key,
  position smallint not null unique,
  heading text not null,
  body text not null,
  closing_body text
);

create table public.rule_items (
  id bigint generated always as identity primary key,
  kind text not null check (kind in ('hero_tier', 'collectible_icon')),
  position smallint not null,
  label text not null,
  description text,
  image_path text not null,
  unique (kind, position)
);
```

`unique (kind, position)` chứ không `unique (position)`: hai `kind` có hai dãy thứ tự độc lập
(hero tier 1–4, icon 1–6).

**Bảng dữ liệu seed** — 3 + 4 + 6 = 13 dòng, mọi chuỗi từ `clarifications.md`:

`rule_sections`

| position | heading | body | closing_body |
|---|---|---|---|
| 1 | `NGƯỜI NHẬN KUDOS: HUY HIỆU HERO CHO NHỮNG ẢNH HƯỞNG TÍCH CỰC` | `Dựa trên số lượng đồng đội gửi trao Kudos, bạn sẽ sở hữu Huy hiệu Hero tương ứng, được hiển thị trực tiếp cạnh tên profile` | `null` |
| 2 | `NGƯỜI GỬI KUDOS: SƯU TẬP TRỌN BỘ 6 ICON, NHẬN NGAY PHẦN QUÀ BÍ ẨN` | `Mỗi lời Kudos bạn gửi sẽ được đăng tải trên hệ thống và nhận về những lượt ❤️ từ cộng đồng Sunner. Cứ mỗi 5 lượt ❤️, bạn sẽ được mở 1 Secret Box, với cơ hội nhận về một trong 6 icon độc quyền của SAA.` | `Những Sunner thu thập trọn bộ 6 icon sẽ nhận về một phần quà bí ẩn từ SAA 2025.` |
| 3 | `KUDOS QUỐC DÂN` | `5 Kudos nhận về nhiều ❤️ nhất toàn Sun* sẽ chính thức trở thành Kudos Quốc Dân và được trao phần quà đặc biệt từ SAA 2025: Root Further.` | `null` |

`rule_items` — `kind='hero_tier'`

| position | label | description | image_path |
|---|---|---|---|
| 1 | `Có 1-4 người gửi Kudos cho bạn` | `Hành trình lan tỏa điều tốt đẹp bắt đầu – những lời cảm ơn và ghi nhận đầu tiên đã tìm đến bạn.` | `/images/rules/hero-badge-new-hero.png` |
| 2 | `Có 5-9 người gửi Kudos cho bạn` | `Hình ảnh bạn đang lớn dần trong trái tim đồng đội bằng sự tử tế và cống hiến của mình.` | `/images/rules/hero-badge-rising-hero.png` |
| 3 | `Có 10–20 người gửi Kudos cho bạn` | `Bạn đã trở thành biểu tượng được tin tưởng và yêu quý, người luôn sẵn sàng hỗ trợ và được nhiều đồng đội nhớ đến.` | `/images/rules/hero-badge-super-hero.png` |
| 4 | `Có hơn 20 người gửi Kudos cho bạn` | `Bạn đã trở thành huyền thoại – người để lại dấu ấn khó quên trong tập thể bằng trái tim và hành động của mình.` | `/images/rules/hero-badge-legend-hero.png` |

`rule_items` — `kind='collectible_icon'` (`description` = `null` ở cả sáu)

| position | label | image_path |
|---|---|---|
| 1 | `REVIVAL` | `/images/rules/icon-revival.png` |
| 2 | `TOUCH OF LIGHT` | `/images/rules/icon-touch-of-light.png` |
| 3 | `STAY GOLD` | `/images/rules/icon-stay-gold.png` |
| 4 | `FLOW TO HORIZON` | `/images/rules/icon-flow-to-horizon.png` |
| 5 | `BEYOND THE BOUNDARY` | `/images/rules/icon-beyond-the-boundary.png` |
| 6 | `ROOT FUTHER` | `/images/rules/icon-root-further.png` |

Lưu ý: caption là `ROOT FUTHER` (nguyên văn node text) nhưng tên file là `icon-root-further.png`
(tên file do gate clarification đặt, đã có trên đĩa). Hai thứ khác nhau là **đúng** — đừng đổi bên nào.

`image_path` lưu đường dẫn public tuyệt đối bắt đầu bằng `/images/rules/`, khớp cách
`floating-widget.tsx` dùng `src="/images/home/..."` — component truyền thẳng vào `<Image src>`.

## Related Code Files

**Create**
- `supabase/migrations/20260909093000_the_le_rules_content.sql`

**Modify**
- `supabase/seed.sql` — thêm hai section mới ở CUỐI file (sau `board_stats`), theo đúng kiểu divider
  `-- ---` + comment header của file
- `lib/supabase/database.types.ts` — **sinh lại**, không sửa tay

**Delete** — không có.

## Implementation Steps

1. Tạo migration với header comment nêu: feature F007, trỏ về
   `plans/260909-0838-the-le-rules-panel/phase-03-migration-seed-types.md`, và nói rõ đây là bảng
   nội dung biên tập đầu tiên của repo (trước đây `/awards-information` hardcode trong `lib/`).
2. Trong migration, theo đúng thứ tự block của `20260906140914_kudos_live_board.sql`:
   divider + `-- rule_sections` + `create table`; divider + `-- rule_items` + `create table`;
   divider + `-- RLS`; divider + `-- Grants`.
3. Block RLS:
   ```sql
   alter table public.rule_sections enable row level security;
   alter table public.rule_items enable row level security;

   -- Đọc: nội dung thể lệ công khai, giống khuôn kudos_select_all.
   create policy "rule_sections_select_all" on public.rule_sections for select to anon, authenticated using (true);
   create policy "rule_items_select_all" on public.rule_items for select to anon, authenticated using (true);
   -- Không policy insert/update/delete: RLS mặc định từ chối. Im lặng chính là từ chối.
   ```
4. Block grants + reload:
   ```sql
   grant select on public.rule_sections to anon, authenticated;
   grant select on public.rule_items to anon, authenticated;
   notify pgrst, 'reload schema';
   ```
5. Thêm hai section vào cuối `supabase/seed.sql`, mỗi section có comment header trỏ về
   `clarifications.md § "Resolved from source data"` và nhắc luật MoMorph "Do NOT invent data".
   Insert phẳng `insert into public.rule_sections (position, heading, body, closing_body) values (...)`,
   `insert into public.rule_items (kind, position, label, description, image_path) values (...)`.
   **Không `ON CONFLICT`.**
6. Escape SQL: mọi dấu nháy đơn trong copy phải nhân đôi. Rà lại — trong 13 dòng trên **không có**
   dấu nháy đơn nào, nhưng có emoji `❤️` (UTF-8, an toàn trong `text`) và en-dash `–`.
7. Chạy `npx supabase db reset` — áp migration rồi chạy seed. Đọc output, xác nhận không lỗi.
8. Kiểm chứng bằng psql, không bằng niềm tin. **`psql` KHÔNG có trên PATH của máy này** (đã đo) —
   dùng đúng idiom repo đang dùng cho việc này (researcher-02 § 6), chạy psql bên trong container:
   ```
   docker exec -i supabase_db_my-app psql -U postgres -d postgres \
     -c "select position, left(heading,30) from public.rule_sections order by position;" \
     -c "select kind, count(*) from public.rule_items group by kind order by kind;"
   ```
   Kỳ vọng: 3 dòng sections, và `hero_tier` 4 / `collectible_icon` 6.
9. Kiểm chứng RLS thật sự chặn ghi — thử với vai `anon`:
   ```
   docker exec -i supabase_db_my-app psql -U postgres -d postgres \
     -c "set role anon; insert into public.rule_sections (position, heading, body) values (99,'x','y');"
   ```
   Kỳ vọng: lỗi (`permission denied` hoặc vi phạm RLS). Nếu insert THÀNH CÔNG → FR-601 hỏng, dừng lại.
   (Tên container lấy từ `docker ps`; researcher-02 đã đo là `supabase_db_my-app`.)
10. `npm run db:types`, rồi `git diff --stat lib/supabase/database.types.ts` để xác nhận file có đổi
    và chứa `rule_sections` / `rule_items`.
11. `npm run typecheck` — file types mới không được làm hỏng chỗ nào.

## Todo List

- [x] `supabase/migrations/20260909093000_the_le_rules_content.sql` với header + 4 block
- [x] Hai `create table` đúng cột/khoá ở § Architecture
- [x] RLS: bật + 2 policy `_select_all` + comment "im lặng là từ chối"
- [x] Grants tường minh + `notify pgrst, 'reload schema';`
- [x] 13 dòng seed vào cuối `supabase/seed.sql` (`seed.sql:347-397`), phiên âm nguyên văn — **trừ
      caption icon 6, đã sửa lại, xem dưới**
- [x] `npx supabase db reset` chạy sạch
- [x] psql xác nhận 3 + 10 dòng, đúng thứ tự `position`
- [x] psql xác nhận `anon` KHÔNG insert được
- [x] `npm run db:types` + commit `lib/supabase/database.types.ts` (chứa `rule_sections`, `rule_items`)
- [x] `npm run typecheck` sạch

## Sai lệch so với kế hoạch (post-phase, `plan.md § PP-3`)

Key Insight 6 liệt kê **ba** chỗ "trông như lỗi" phải giữ nguyên. Chỉ **hai** trong đó là thật:

| Chuỗi | Phán quyết cuối |
|---|---|
| en-dash `Có 10–20 người gửi Kudos cho bạn` | **Giữ.** Đúng nguyên văn frame. |
| en-dash trong mô tả bậc 1 (`bắt đầu –`) và bậc 4 (`huyền thoại –`) | **Giữ.** Đúng nguyên văn frame. |
| `ROOT FUTHER` | **Sai — đã sửa thành `ROOT FURTHER`.** |

Bản chép đầu đọc `itemName` của node Figma (tên layer, ai đó gõ thiếu chữ R) thay vì `character`
(chữ thực sự được render). Đọc lại qua MoMorph mới phân biệt được hai trường đó. Sửa lan sang seed,
fixture E2E, `clarifications.md` và cả hai functional-spec; DB đã seed lại
(`supabase/seed.sql:392-397`, lý do ghi thẳng trong comment header ở `seed.sql:367-371`).

Bài học đáng giữ: "phiên âm nguyên văn" chỉ có nghĩa khi biết đang phiên âm **trường nào**. Byte-check
ở § Success Criteria đã làm đúng việc của nó — nó bảo vệ chuỗi đang có, nó không kiểm được rằng chuỗi
đó lấy từ đúng nguồn.

## Success Criteria

- `npx supabase db reset` exit 0.
- `select count(*) from public.rule_sections` = 3; `select count(*) from public.rule_items` = 10,
  chia đúng 4 `hero_tier` / 6 `collectible_icon`.
- `set role anon; insert into public.rule_sections ...` **thất bại** — FR-601 chứng minh bằng đo, không
  bằng khẳng định.
- `set role anon; select * from public.rule_sections` **thành công** và trả 3 dòng.
- `lib/supabase/database.types.ts` chứa `rule_sections` và `rule_items`; `npm run typecheck` exit 0.
- `grep -c "ON CONFLICT" supabase/seed.sql` không tăng so với trước phase.
- Byte-check ba chỗ dễ bị "sửa": `grep "10–20" supabase/seed.sql` có kết quả; ~~`grep "ROOT FUTHER"
  supabase/seed.sql` có kết quả~~ → **tiêu chí này đã bị bác bỏ**, giá trị đúng là `ROOT FURTHER`
  (§ "Sai lệch so với kế hoạch").

## Risk Assessment

| Risk | Likelihood | Impact | Countermove |
|---|---|---|---|
| `db reset` xoá dữ liệu local của người khác đang dở việc | Trung bình | Trung bình | Đây là idiom sẵn có của repo (mọi seed đều đi qua reset); báo trước trong commit message; local-only, không production |
| Quên `notify pgrst` → PostgREST 404 trông như bug code | Trung bình | **Cao** — tốn hàng giờ debug sai hướng | Bước 4 bắt buộc; researcher-01 § 1 ghi rõ triệu chứng |
| Copy bị "sửa chính tả" (`ROOT FUTHER`, en-dash) | **Cao** — trông như lỗi thật | Cao — bịa dữ liệu, spec RED sẽ không khớp | Key Insight 6 + byte-check ở Success Criteria + comment inline trong seed |
| `unique (position)` thay vì `unique (kind, position)` | Trung bình | Cao — seed fail ở dòng thứ 5 | § Architecture nêu rõ lý do; lỗi lộ ngay ở bước 7 |
| Timestamp migration nhỏ hơn `20260908100000` | Thấp | Cao — thứ tự áp dụng sai | Tên file đã cố định `20260909093000` |
| `database.types.ts` bị sửa tay thay vì sinh lại | Thấp | Trung bình | Bước 10 dùng `git diff --stat` để xác nhận đúng file sinh ra |

**Rollback**: xoá file migration, `git checkout -- supabase/seed.sql lib/supabase/database.types.ts`,
rồi `npx supabase db reset` để quay về schema trước. Local-only nên không có dữ liệu người dùng thật
nào mất. Không có phase nào sau đã ghi vào hai bảng này (chúng read-only), nên rollback không cascade.

## Security Considerations

- **RLS bật trên cả hai bảng** — tiền lệ ràng buộc từ F004 (`spec/system/permissions.md`).
- **Đúng một policy mỗi bảng, chỉ `select`.** Không policy `insert`/`update`/`delete`: RLS mặc định
  từ chối, và viết một policy deny thừa là làm ồn chứ không làm an toàn hơn.
- **Grant tường minh**, không dựa vào `auto_expose_new_tables` — "một default không phải một hợp đồng"
  (researcher-01 § 1).
- **Không đụng schema `auth`.** Không dòng seed nào ghi vào `auth.users` — GoTrue sở hữu nó.
- **Không nhị phân trong DB** (FR-205): ảnh trên đĩa, row chỉ giữ đường dẫn. Không có bề mặt upload
  nào được mở ra bởi phase này.
- Cần một mã `PERM###` mới trong `docs/generated/permissions-matrix.md` cho hai bảng — **không phải
  việc của phase này**; `doc-writer` cấp lúc delivery.

## Next Steps

- **Chặn**: phase 04 (cần `database.types.ts` mới để type `Row<"rule_sections">`).
- **Không chặn**: phase 05, 06 (Track A dựng trên `RulesViewModel` của phase 01, không cần schema).
- Bàn giao sang phase 04: tên bảng, tên cột, và sự thật rằng `rule_items.description` nullable ở tầng
  row nhưng không nullable ở tầng view-model của `hero_tier`.
