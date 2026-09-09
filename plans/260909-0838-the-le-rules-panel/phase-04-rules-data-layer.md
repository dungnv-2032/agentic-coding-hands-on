# Phase 04 — Tầng dữ liệu `lib/rules/`

## Context Links

- `research/researcher-01-supabase-and-i18n-conventions.md § 3` — khuôn `queries.ts` / `<feature>-data.ts`
- `spec/the-le/technical-spec.md § 3.1` (khối **BE**) và `§ 5.4 Data Flow`
- `phase-01-contract-and-i18n.md § Architecture` — `RulesViewModel` đóng băng
- `phase-03-migration-seed-types.md § Architecture` — tên bảng, cột, `kind`
- House style: `lib/kudos/queries.ts`, `lib/kudos/board-data.ts`, `lib/supabase/server.ts`

## Overview

- **Priority**: P1
- **Status**: **completed** — phase duy nhất ship đúng nguyên si kế hoạch, không sai lệch nào.
- **Description**: Hai file: `queries.ts` (chỉ đọc typed, client là tham số) và `rules-data.ts`
  (orchestrator: một client mỗi request, `Promise.all` hai read độc lập, map row → `RulesViewModel`).
  Row database không bao giờ chạm tới component.

## Key Insights

1. **Client là tham số, không tạo trong `queries.ts`.** Đúng chữ ký repo:
   `async function fetchX(supabase: SupabaseClient<Database>): Promise<XRow[]>`. `rules-data.ts` tạo
   một client mỗi request qua `createClient()` của `lib/supabase/server.ts` rồi luồn xuống.
2. **Không try/catch.** Idiom repo: kiểm `{ data, error }`, `if (error) throw new Error(\`fetchX
   failed: ${error.message}\`)`, return `data`. Không class error riêng.
3. **Hai bảng phẳng, không embed** — nên dùng thẳng `Row<"rule_sections">` / `Row<"rule_items">` từ
   `database.types.ts`, KHÔNG khai interface thủ công. Interface thủ công + `.returns<T[]>()` chỉ
   dành cho embed FK-hinted và view (`kudos_readable`), không phải cho hai bảng này.
4. **Bảng rỗng không phải lỗi** (functional-spec § 9). Hai query trả `[]`, view-model có ba mảng rỗng,
   panel render chrome + hai nút. Không throw, không màn trắng. `data ?? []` là chỗ xử lý.
5. **Phân loại `kind` xảy ra đúng một lần**, ở `rules-data.ts`. Component không bao giờ lọc.
6. **Không caching layer.** Repo không dùng `unstable_cache`/`revalidate` ở đâu; `cookies()` trong
   `getPageContext()` đã ép dynamic rendering rồi.

## Requirements

- **FR-205** — `image_path` từ row đi thẳng vào view-model, không biến đổi
- **BR-001** — `.order("position", { ascending: true })` ở CẢ HAI query, mọi lúc
- **BR-002** — tầng này chỉ chạm dữ liệu; không import gì từ `lib/i18n/`
- Edge case (functional-spec § 9) — bảng rỗng → mảng rỗng; lỗi query → `throw new Error("fetchX failed: …")`

## Architecture

```
getRulesContent()                       lib/rules/rules-data.ts
  ├─ await createClient()               (một client mỗi request)
  ├─ Promise.all([
  │    fetchRuleSections(supabase),     select * order by position
  │    fetchRuleItems(supabase),        select * order by position
  │  ])
  ├─ sections  = rows.map(toSectionView)
  ├─ heroTiers = items.filter(kind==='hero_tier').map(toHeroTierView)
  ├─ icons     = items.filter(kind==='collectible_icon').map(toIconView)
  └─ return { sections, heroTiers, collectibleIcons }   : RulesViewModel
```

`queries.ts` (~40 dòng):

```ts
type Row<T extends keyof Database["public"]["Tables"]> = Database["public"]["Tables"][T]["Row"];
export type RuleSectionRow = Row<"rule_sections">;
export type RuleItemRow = Row<"rule_items">;

export async function fetchRuleSections(supabase: SupabaseClient<Database>): Promise<RuleSectionRow[]>
export async function fetchRuleItems(supabase: SupabaseClient<Database>): Promise<RuleItemRow[]>
```

Cả hai: `.from("rule_sections").select("*").order("position", { ascending: true })`.

**Xử lý `description` nullable.** `rule_items.description` là `text` nullable ở tầng row, nhưng
`RulesHeroTierView.description` là `string`. Chỗ nối: `toHeroTierView` dùng `row.description ?? ""`.
Không throw — một hero tier thiếu mô tả vẫn render được nhãn và ảnh; ném lỗi ở đây sẽ biến một ô
thiếu chữ thành một màn hình trắng, đúng thứ § 9 nói là không nên.

**`kind` là `string` sau khi generate types** (cột `text` + `check`, không phải enum Postgres), nên
so sánh bằng chuỗi literal. Khai hai hằng số ở `queries.ts` để không rải magic string:
`export const RULE_ITEM_KIND = { heroTier: "hero_tier", collectibleIcon: "collectible_icon" } as const;`

## Related Code Files

**Create**
- `lib/rules/queries.ts`
- `lib/rules/rules-data.ts`

**Modify** — không có (`lib/rules/view-model.ts` thuộc phase 01, chỉ đọc ở đây).

**Delete** — không có.

## Implementation Steps

1. Tạo `lib/rules/queries.ts` với doc-comment đầu file theo kiểu `lib/kudos/queries.ts`: nói rõ
   client là tham số, chỉ row thô, `rules-data.ts` sở hữu view-model, và hai bảng phẳng nên dùng
   `Row<T>` chứ không khai interface thủ công.
2. Khai `Row<T>` alias, export `RuleSectionRow`, `RuleItemRow`, `RULE_ITEM_KIND`.
3. Viết `fetchRuleSections`: `.from("rule_sections").select("*").order("position", { ascending: true })`,
   kiểm `error` → `throw new Error(\`fetchRuleSections failed: ${error.message}\`)`, return `data ?? []`.
4. Viết `fetchRuleItems` cùng khuôn, `.from("rule_items")`.
5. Tạo `lib/rules/rules-data.ts` export `getRulesContent(): Promise<RulesViewModel>`, theo § Architecture.
   Ba hàm map là hàm thuần, module-level, không export (chỉ `getRulesContent` là public).
6. Xác nhận `rules-data.ts` KHÔNG import gì từ `lib/i18n/` và `queries.ts` KHÔNG import
   `lib/supabase/server.ts` (chỉ import type `SupabaseClient`).
7. `npm run typecheck` rồi `npm run lint`.
8. Kiểm chứng chạy thật, không chỉ compile — dựng một probe tạm rồi xoá:
   ```
   npx tsx -e "import('./lib/rules/rules-data.ts')" 2>/dev/null || true
   ```
   Nếu repo không có `tsx`, bỏ qua bước này; phase 07 sẽ là lần chạy thật đầu tiên và phase 08 là
   nơi chứng minh. Đừng cài dependency mới chỉ để probe.

## Todo List

- [x] `lib/rules/queries.ts` — `Row<T>` alias, hai `fetchX`, `RULE_ITEM_KIND`
- [x] `.order("position", { ascending: true })` ở CẢ HAI query (`queries.ts:45`, `queries.ts:65`)
- [x] `data ?? []` — bảng rỗng trả mảng rỗng, không throw
- [x] `lib/rules/rules-data.ts` — `getRulesContent()` với `Promise.all`
- [x] Phân loại `kind` một lần, ba mảng ra view-model
- [x] `description ?? ""` cho hero tier
- [x] Không import `lib/i18n/` trong tầng này
- [x] `npm run typecheck` + `npm run lint` sạch

## Sai lệch so với kế hoạch

Không có. `getRulesContent` là export duy nhất của `rules-data.ts`, ba mapper giữ private, cả hai file
dưới ngưỡng 200 dòng.

Một chỗ **không** kiểm được và cố ý để lại: nhánh **bảng rỗng** và nhánh **lỗi query** (§ Requirements,
functional-spec § 9) chưa có test tự động nào chạm tới — repo không có unit-test runner, và dựng một
cái là ngoài scope của commission này. Hai nhánh đó đã được đọc bằng mắt, không được chứng minh bằng
lần chạy nào. Ghi ở đây làm nợ, không làm lời khẳng định (`plan.md § "Đã biết và chấp nhận"`).

## Success Criteria

- `npm run typecheck` exit 0 — chứng minh `Row<"rule_sections">` resolve được, tức phase 03 đã sinh
  types đúng.
- `npm run lint` exit 0.
- `grep -c "order(" lib/rules/queries.ts` = 2 — BR-001 có mặt ở cả hai query.
- `grep "lib/i18n" lib/rules/` trả rỗng — biên BR-002 không bị lấn.
- Cả hai file dưới 200 dòng (`wc -l lib/rules/*.ts`).
- `getRulesContent` là export duy nhất của `rules-data.ts` (ba mapper giữ private).

## Risk Assessment

| Risk | Likelihood | Impact | Countermove |
|---|---|---|---|
| Quên `.order()` ở một query → thứ tự về theo `id` | Trung bình | Cao — `GUI_002/005/006` của phase 02 sẽ đỏ ở phase 08 | `grep -c "order("` = 2 ở Success Criteria |
| Tạo client BÊN TRONG `queries.ts` | Trung bình | Trung bình — nhiều client mỗi request | Bước 6 kiểm import tường minh |
| Khai interface row thủ công thay vì `Row<T>` | Trung bình | Thấp — drift với schema | Key Insight 3 nêu rõ khi nào mới cần interface thủ công |
| Ném lỗi khi `description` null | Thấp | Trung bình — màn trắng vì một ô thiếu chữ | `?? ""` ở § Architecture |
| Phase 03 chưa chạy → `Row<"rule_sections">` không tồn tại | Trung bình | Cao — typecheck đỏ, trông như lỗi code | Dependency đã ghi: 03 → 04 strict. Nếu gặp, chạy `npm run db:types` trước |

**Rollback**: `rm -rf lib/rules/queries.ts lib/rules/rules-data.ts`. Không phase nào khác import chúng
cho tới phase 07, nên gỡ ra không cascade.

## Security Considerations

- Tầng này **chỉ đọc**: không `insert`, không `update`, không `rpc`. Không Server Action nào ở đây.
- Client dùng là `createClient()` của `lib/supabase/server.ts` — anon key + session cookie, đi qua RLS.
  **Không** service-role key ở bất kỳ đâu trong feature này.
- Không tham số nào từ người dùng đi vào query (không `searchParams`, không dynamic segment), nên
  không có bề mặt injection. Nếu về sau ai thêm filter theo input, phải dùng `.eq()` có tham số của
  postgrest-js, không nối chuỗi.
- Row trả về không chứa dữ liệu cá nhân nào — nội dung thể lệ là copy công khai.

## Next Steps

- **Chặn**: phase 07 (page gọi `getRulesContent()`).
- **Không chặn**: phase 05, 06 — chúng nhận `RulesViewModel` làm props, không gọi tầng này.
- Bàn giao sang phase 07: chữ ký `getRulesContent(): Promise<RulesViewModel>` và sự thật rằng nó tự
  tạo client, nên page KHÔNG cần truyền client vào.
