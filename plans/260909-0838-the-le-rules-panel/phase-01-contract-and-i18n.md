# Phase 01 — Contract đóng băng + khối `rules` i18n

## Context Links

- `clarifications.md § "Test contract"` — bảng `data-testid`, ràng buộc cả spec RED lẫn UI
- `clarifications.md § "Resolved from source data"` — nguồn duy nhất của mọi chuỗi
- `spec/the-le/technical-spec.md § 4.1, § 4.2` — danh sách component + shape hai bảng
- `spec/the-le/functional-spec.md` — FR-003, BR-002, BR-003
- `research/researcher-01-supabase-and-i18n-conventions.md § 4` — 5 bước thêm namespace i18n
- House style: `lib/i18n/messages/{dictionary.ts,vi.ts,en.ts,vi-profile.ts}`, `lib/kudos/view-model.ts`

## Overview

- **Priority**: P1 — chặn mọi phase khác
- **Status**: **completed** — với một sai lệch: khối `Dictionary["rules"]` chốt ở đây có 6 key, bản
  ship còn **3** (`panelTitle`, `closeButton`, `writeKudosButton`). Xem § "Sai lệch so với kế hoạch".
- **Description**: Đóng băng hai biên mà Track A và Track B đều dựng lên trên: kiểu view-model
  `RulesViewModel` và khối copy `Dictionary["rules"]`. Sau phase này, không phase nào được sửa hai
  biên đó; ai cần đổi phải quay lại đây.

## Key Insights

1. **`vi` là source shape của `Dictionary`** (nói thẳng trong `vi.ts`). Viết `vi-rules.ts` trước,
   `en-rules.ts` sau, khớp key-for-key — drift là compile error, không có fallback runtime.
2. **Khối `rules` CHỈ chứa chrome** (BR-002): tiêu đề panel, hai nhãn nút, nhãn aria, alt ảnh. Nội
   dung thể lệ nằm trong database, không nằm ở đây. Ranh giới này là lý do tồn tại của cả feature.
3. **View-model phải đóng băng và page-shaped**, không phải row thô — khuôn `board-data.ts` /
   `profile-data.ts`: `queries.ts` trả row, `rules-data.ts` map sang view-model, component chỉ thấy
   view-model.
4. `dictionary.ts` hiện dài ~292 dòng. Thêm khối `rules` (~12 dòng interface) vẫn dưới ngưỡng 200 dòng?
   **Không** — file này đã vượt từ trước và là interface thuần, không phải file logic; giữ nguyên
   cách repo đang làm, không tách `dictionary.ts` trong phase này (ngoài scope, sẽ churn 6 file khác).

## Requirements

- **FR-003** — khối `rules` vào interface `Dictionary`, cùng `vi-rules.ts` + `en-rules.ts`, nối vào
  `vi.ts` / `en.ts`.
- **BR-002** — chrome là i18n copy; nội dung thể lệ là dữ liệu. Không bên nào lấn sang bên kia.
- **BR-003** — không có cột/khoá `locale` cho nội dung. Hệ quả (`NEXT_LOCALE=en` → chrome EN + thân VI)
  được ghi thẳng vào doc-comment của `vi-rules.ts`, không giấu.

## Architecture

`RulesViewModel` là một object đóng băng, page-shaped, đúng ba trường:

```ts
export interface RulesSectionView {
  position: number;
  heading: string;
  body: string;
  /** Dòng kết render SAU danh sách của mục — chỉ mục 2 có. */
  closingBody: string | null;
}

export interface RulesHeroTierView {
  position: number;
  label: string;
  description: string;
  imagePath: string;
}

export interface RulesCollectibleIconView {
  position: number;
  caption: string;
  imagePath: string;
}

export interface RulesViewModel {
  sections: readonly RulesSectionView[];
  heroTiers: readonly RulesHeroTierView[];
  collectibleIcons: readonly RulesCollectibleIconView[];
}
```

Lý do `heroTiers` và `collectibleIcons` là hai mảng riêng dù cùng bảng `rule_items`: `kind` là
chuyện của schema, không phải chuyện của component. `rules-data.ts` phân loại một lần; component
không bao giờ phải lọc.

`description` của hero tier là `string` (không nullable) và `caption` của icon là `string` — phân
biệt nullable ở tầng row (`rule_items.description text`), không ở tầng view-model, vì view-model
biết `kind` nào điền cột nào (technical-spec § 4.2 "Polymorphic Behavior").

Khối `Dictionary["rules"]`:

```ts
rules: {
  /** Tiêu đề panel — render là `<h1>` của trang (FR-201). */
  panelTitle: string;
  /** Nhãn aria của container `role="dialog"`. */
  panelAriaLabel: string;
  closeButton: string;
  writeKudosButton: string;
  /** Alt cho ảnh pill huy hiệu, mang "{tier}". */
  heroTierImageAlt: string;
  /** Alt cho artwork icon sưu tập, mang "{name}". */
  collectibleIconImageAlt: string;
};
```

## Related Code Files

**Create**
- `lib/rules/view-model.ts`
- `lib/i18n/messages/vi-rules.ts`
- `lib/i18n/messages/en-rules.ts`

**Modify**
- `lib/i18n/messages/dictionary.ts` — thêm khối `rules` kèm doc-comment kiểu khối `kudos`/`profile`
- `lib/i18n/messages/vi.ts` — `import { viRules }` + `rules: viRules,`
- `lib/i18n/messages/en.ts` — `import { enRules }` + `rules: enRules,`

**Delete** — không có.

## Implementation Steps

1. Tạo `lib/rules/view-model.ts` với đúng bốn interface ở § Architecture. Doc-comment đầu file trỏ
   về `plans/260909-0838-the-le-rules-panel/phase-01-contract-and-i18n.md` và nói rõ đây là biên
   đóng băng cho cả hai track.
2. Thêm khối `rules` vào interface `Dictionary` (`lib/i18n/messages/dictionary.ts`), đặt sau khối
   `kudosCompose`, kèm doc-comment nêu: feature F007, screen `b1Filzi9i6`, frame `3204:6051`, và
   BR-002 ("chrome ở đây, nội dung thể lệ ở database").
3. Tạo `lib/i18n/messages/vi-rules.ts`:
   ```ts
   export const viRules: Dictionary["rules"] = {
     panelTitle: "Thể lệ",
     panelAriaLabel: "Thể lệ",
     closeButton: "Đóng",
     writeKudosButton: "Viết KUDOS",
     heroTierImageAlt: "Huy hiệu {tier}",
     collectibleIconImageAlt: "Icon {name}",
   };
   ```
   Ba chuỗi đầu phiên âm nguyên văn từ `clarifications.md` (`3204:6055`, `3204:6093`, `3204:6094`).
   Doc-comment ghi BR-003 và hệ quả song ngữ.
4. Tạo `lib/i18n/messages/en-rules.ts` khớp key-for-key: `panelTitle: "Rules"`,
   `panelAriaLabel: "Rules"`, `closeButton: "Close"`, `writeKudosButton: "Viết KUDOS"`,
   `heroTierImageAlt: "{tier} badge"`, `collectibleIconImageAlt: "{name} icon"`.
   **`writeKudosButton` giữ nguyên tiếng Việt ở cả hai locale** — cùng lý do `login.signInButton`
   giữ "LOGIN With Google" trong `en.ts`: đây là copy thiết kế / tên sản phẩm, không phải văn xuôi
   để dịch. Ghi lý do đó vào doc-comment.
5. Nối vào `vi.ts` và `en.ts` theo đúng 5 bước của researcher-01 § 4 — import module, thêm
   `rules: viRules,` / `rules: enRules,`; KHÔNG inline namespace vào `vi.ts`.
6. Chạy `npm run typecheck` rồi `npm run lint`.

## Todo List

- [x] `lib/rules/view-model.ts` với bốn interface đóng băng
- [x] Khối `rules` trong interface `Dictionary` + doc-comment — **3 key, không phải 6** (xem dưới)
- [x] `lib/i18n/messages/vi-rules.ts` (copy phiên âm nguyên văn)
- [x] `lib/i18n/messages/en-rules.ts` khớp key-for-key
- [x] Nối `rules` vào `vi.ts` và `en.ts`
- [x] `npm run typecheck` sạch
- [x] `npm run lint` sạch

## Sai lệch so với kế hoạch (post-phase, `plan.md § PP-5`)

Ba key alt/aria mà § Architecture chốt ở đây đã bị **xoá** sau khi phase 06/07 quyết định cách khác:

| Key đã xoá | Vì sao nó thành code chết |
|---|---|
| `heroTierImageAlt` (`"Huy hiệu {tier}"`) | Component không giữ tên bậc — chỉ có `label` là câu ngưỡng, nên template sinh ra `Huy hiệu Có 1-4 người gửi Kudos cho bạn`, tệ hơn im lặng. Pill lấy `alt=""` (trang trí theo WCAG 1.1.1), nhãn text ngay cạnh đã mang trọn nghĩa. |
| `collectibleIconImageAlt` (`"Icon {name}"`) | Cùng lý do: caption là text node ngay dưới artwork, alt lặp lại bắt screen reader đọc hai lần. |
| `panelAriaLabel` | Panel lấy tên khả truy cập từ `aria-labelledby` trỏ `<h1>` — một nhãn, không phải hai nguồn. |

Phase 06 § Architecture đã dự liệu đúng lối ra này ("nếu không dùng, **bỏ prop đó đi** thay vì để tham
số chết"); hệ quả là prop `imageAltTemplate` của cả hai component cũng không tồn tại trong bản ship.
Khối `rules` cuối cùng: `panelTitle`, `closeButton`, `writeKudosButton`. Lý do được ghi lại nguyên văn
trong doc-comment của `rules-hero-tier-list.tsx` và `rules-collectible-grid.tsx`, không chỉ ở đây.

`RulesViewModel` với bốn interface thì **không đổi một dòng nào** từ lúc đóng băng — cả hai track dựng
trọn vẹn trên nó, đúng như phase này đặt ra.

## Success Criteria

- `npm run typecheck` exit 0 — chứng minh `vi` và `en` khớp shape, không key nào thiếu.
- `npm run lint` exit 0.
- `RulesViewModel` export được từ `lib/rules/view-model.ts` và không import gì từ `@supabase/*`
  (biên view-model không được rò kiểu database vào component).
- Không chuỗi tiếng Việt nào của NỘI DUNG thể lệ (heading mục, mô tả bậc, caption icon) xuất hiện
  trong bất kỳ file i18n nào — grep `"NGƯỜI NHẬN KUDOS"` trong `lib/i18n/` trả về rỗng.

## Risk Assessment

| Risk | Likelihood | Impact | Countermove |
|---|---|---|---|
| Copy chrome bị "cải thiện" thay vì phiên âm | Trung bình | Cao — vi phạm luật MoMorph | Doc-comment mỗi file nói thẳng "Do not paraphrase"; phase 08 so lại với frame |
| `en-rules.ts` dịch luôn `Viết KUDOS` | Trung bình | Thấp | Bước 4 nêu rõ + lý do; `en.ts` đã có tiền lệ `signInButton` |
| View-model bị thêm trường "cho chắc" | Thấp | Trung bình — YAGNI | Bốn interface ở § Architecture là đủ và đóng; thêm trường phải quay lại phase này |

**Rollback**: `git checkout -- lib/i18n/messages/ && rm -rf lib/rules/`. Không có state ngoài file,
không migration, không dữ liệu — hoàn tác sạch.

## Security Considerations

Không. Phase này không chạm database, không chạm session, không chạm route. Khối i18n là hằng số
tĩnh compile vào bundle; không có input người dùng nào đi qua đây.

## Next Steps

- **Chặn**: phase 02 (spec RED import hằng số copy độc lập, nhưng cần biết `panelTitle` cuối cùng),
  và qua đó chặn 03–07.
- **Bàn giao**: đường dẫn `lib/rules/view-model.ts` + shape `Dictionary["rules"]` là input bắt buộc
  của phase 04 (map sang view-model) và phase 05/06/07 (đọc chrome).
