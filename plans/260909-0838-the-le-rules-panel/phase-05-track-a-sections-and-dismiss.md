# Phase 05 — Track A: mục văn xuôi + cụm đóng panel

## MoMorph refs

- Thể lệ UPDATE: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/b1Filzi9i6
- Clarifications: `plans/260909-0838-the-le-rules-panel/clarifications.md`
- testPolicy: `e2e-red-first`

## Context Links

- `clarifications.md § "Resolved from source data"` — kích thước chữ, màu, node id từng khối
- `clarifications.md § "Layout and behaviour"`, `§ "Test contract"`
- `design/the-le.png` — frame render 1×
- `spec/the-le/technical-spec.md § 3.2, § 4.1, § 4.3`
- `phase-01-contract-and-i18n.md` — `RulesSectionView`, `Dictionary["rules"]`
- `phase-02-e2e-red-gate.md § Success Criteria` — RED evidence (read-only input)
- House style: `app/awards-information/_components/`, `app/_components/floating-widget.tsx`

## Overview

- **Priority**: P1
- **Status**: **completed** — `rules-section.tsx` đúng như kế hoạch. `rules-panel-dismiss.tsx` thì
  **không**: Key Insight 2 (`window.history.length > 1`) đã bị đo và bác bỏ, và file phải thêm một
  chốt chống va Escape không ai lường trước. Xem § "Sai lệch so với kế hoạch".
- **Description**: Hai mảnh của Track A chạy song song với Track B: component render một mục văn xuôi
  (`rules-section.tsx`, server) và cụm đóng panel (`rules-panel-dismiss.tsx`, client — nút `Đóng`,
  phím `Escape`, click backdrop). Không phase nào khác chạm hai file này.

## Key Insights

1. **Cụm đóng panel là một file, hai export.** Backdrop (`fixed inset-0`) và nút `Đóng` (trong chân
   drawer) nằm ở hai chỗ khác nhau của cây DOM, nên không thể là một component. Nhưng chúng dùng
   CHUNG một hàm `dismiss()` — nên chúng ở chung một file với một hook `useRulesDismiss()` private.
   Đó là DRY đúng chỗ: một định nghĩa "đóng nghĩa là gì", hai điểm gắn.
2. **`window.history.length > 1`, đọc TẠI THỜI ĐIỂM BẤM.** `document.referrer` không dùng được —
   điều hướng client-side của Next không cập nhật nó (technical-spec § 3.2). Giả định A1 chấp nhận
   over-report; hệ quả xấu nhất là quay về trang trước thay vì `/`, vẫn không phải ngõ cụt.
3. **`Đóng` là `<button>` thật, không `<Link>`** (FR-401) — đích của nó là "nơi bạn vừa đến", không
   phải một URL cố định.
4. **Mục 2 có `closingBody` render SAU lưới icon**, nên `rules-section.tsx` KHÔNG tự render
   `closingBody`. Nó nhận `children` và đặt phần con SAU `body`, rồi `closingBody` sau `children`.
   Phase 07 truyền lưới icon vào làm `children` của mục 2.
5. **Chỉ ba thứ hydrate trên màn này**: nút `Đóng`, listener `Escape`, click backdrop. Mọi thứ khác
   là HTML tĩnh. Đừng biến `rules-section` thành Client Component.

## Requirements

- **FR-202** — mục văn xuôi: heading `#FFEA9E` in hoa + body trắng canh đều (`text-justify`).
  Mục 1 và 2 heading 22/28 bold; mục 3 heading 24/32 bold. Body 16/24 bold.
- **FR-401 / BR-004** — `Đóng` → `router.back()` khi có lịch sử, ngược lại `router.push("/")`
- **FR-404** — `Escape` và click backdrop làm đúng việc `Đóng` làm
- **Test contract** — `data-testid="rules-section"` (×3), `data-testid="rules-close-button"` (×1)
- **DEC-002** — KHÔNG dựng prop `disabled` cho nút. Không gì set được nó; đó là code chết.

## Architecture

### `rules-section.tsx` (server, ~45 dòng)

```tsx
interface RulesSectionProps {
  section: RulesSectionView;
  /** 24/32 cho mục "KUDOS QUỐC DÂN" (mm:3204:6090), 22/28 cho hai mục còn lại. */
  headingSize?: "lg" | "md";
  /** Lưới/danh sách chèn giữa body và closingBody — mục 1 nhận bậc Hero, mục 2 nhận lưới icon. */
  children?: React.ReactNode;
}
```

Render:
```
<section data-testid="rules-section">
  <h2 class="text-[#FFEA9E] font-bold ...">{section.heading}</h2>
  <p  class="text-white text-justify text-base/6 font-bold">{section.body}</p>
  {children}
  {section.closingBody && <p class="text-white text-justify ...">{section.closingBody}</p>}
</section>
```

`headingSize`: `"md"` → `text-[22px]/[28px]`, `"lg"` → `text-2xl/8` (24/32). Hai giá trị, không phải
một prop `className` tự do — đóng biến thể lại theo đúng hai thứ frame có.

**`<section>` chứ không `<div>`**, và heading là `<h2>` — `<h1>` là của tiêu đề panel (FR-201), thuộc
phase 07. Đừng dùng `<h1>` ở đây; hai `<h1>` sẽ phá assertion `getByRole("heading", { level: 1 })`.

### `rules-panel-dismiss.tsx` (client, ~60 dòng)

```tsx
"use client";

function useRulesDismiss() {
  const router = useRouter();
  return useCallback(() => {
    if (window.history.length > 1) router.back();
    else router.push("/");
  }, [router]);
}

/** Nền tối phía sau drawer. Click để đóng; cũng là chỗ gắn listener Escape. */
export function RulesBackdrop({ ariaHidden }: ...) { ... }

/** Nút `Đóng` trong chân drawer. */
export function RulesCloseButton({ label }: { label: string }) { ... }
```

`RulesBackdrop`:
- `<div className="fixed inset-0 z-40 bg-black/50" aria-hidden onClick={dismiss} />`
- `useEffect` gắn `keydown` trên `document`, `if (e.key === "Escape") dismiss()`, cleanup ở return.
  Gắn ở `document` (không ở `window`) để khớp cách listener toàn cục thường viết trong repo.

`RulesCloseButton`:
```tsx
<button
  type="button"
  data-testid="rules-close-button"
  onClick={dismiss}
  className="flex h-14 items-center gap-2 rounded border border-[#998C5F] bg-[#FFEA9E]/10 px-4 text-white transition-colors hover:bg-white/10"
>
  <Image src="/images/rules/close-icon.svg" alt="" aria-hidden width={24} height={24} />
  {label}
</button>
```

- `border-[#998C5F]`, `bg-[#FFEA9E]/10` = `rgba(255,234,158,0.10)`, `rounded` = 4px, padding 16px,
  gap 8px, icon 24×24 — đo được từ `3204:6093`.
- `hover:bg-white/10` là token đã được duyệt cho nút dùng chung này ở `language-selector.tsx` /
  `home-nav.tsx` — tái dùng, không bịa giá trị mới (`clarifications.md § GUI_004`).
- Bề rộng 94px trên frame đến từ nội dung (`icon + gap + "Đóng" + padding`), KHÔNG hardcode `w-[94px]`.
  Chân drawer để `Viết KUDOS` `flex-1` nuốt phần còn lại, nên `Đóng` tự nhiên co về đúng bề rộng đó.
- `close-icon.svg` là `fill="white"` — đúng cho nút nền tối này. (Nút vàng thì KHÔNG, xem phase 06.)
- `label` đến từ `dictionary.rules.closeButton`, không hardcode `"Đóng"`.

## Related Code Files

**Create**
- `app/standards/_components/rules-section.tsx`
- `app/standards/_components/rules-panel-dismiss.tsx`

**Modify** — không có.

**Delete** — không có.

## Implementation Steps

1. Đọc `design/the-le.png` và `clarifications.md § "Resolved from source data"` trước khi viết dòng
   nào. Không đoán giá trị thị giác — dữ liệu MoMorph là thẩm quyền.
2. Tạo `app/standards/_components/rules-section.tsx` theo § Architecture. Doc-comment đầu file ghi
   node id `3204:6132/6133` (mục 1), `3204:6077/6078/6089` (mục 2), `3204:6090/6091` (mục 3), và nói
   rõ vì sao `closingBody` render sau `children`.
3. Đánh dấu `data-testid="rules-section"` trên `<section>` gốc — đúng một cái mỗi mục.
4. Tạo `app/standards/_components/rules-panel-dismiss.tsx` với `"use client"` ở dòng đầu, hook
   private `useRulesDismiss()`, và hai export `RulesBackdrop` / `RulesCloseButton`.
5. Trong `RulesBackdrop`, `useEffect` cleanup listener ở return — rò listener giữa các lần điều hướng
   client-side là lỗi thật, không phải chuyện lý thuyết.
6. Doc-comment của `useRulesDismiss` ghi giả định A1 nguyên văn: `window.history.length > 1` over-report
   trong tab đã duyệt nhiều trang, hệ quả xấu nhất là quay về trang trước thay vì `/` — vẫn không ngõ cụt.
7. Chạy `npm run typecheck`, rồi `npm run lint`.
8. **Không** chạy `npx playwright test` ở phase này — panel chưa được ráp (phase 07), nên spec vẫn RED
   một cách đúng đắn. Chạy nó ở đây chỉ tạo nhiễu.

## Todo List

- [x] Đọc frame render + clarifications trước khi code
- [x] `rules-section.tsx` — `<section data-testid="rules-section">`, `<h2>`, body `text-justify`
- [x] `headingSize` hai biến thể `"md"` (22/28) / `"lg"` (24/32)
- [x] `children` chèn giữa `body` và `closingBody`
- [x] `rules-panel-dismiss.tsx` với `"use client"` + hook `useRulesDismiss` private
- [x] `RulesBackdrop` — click + `Escape` (có cleanup) — **cộng thêm chốt `defaultPrevented`, xem dưới**
- [x] `RulesCloseButton` — `data-testid="rules-close-button"`, icon 24×24, `hover:bg-white/10`
- [x] Không prop `disabled` ở đâu (DEC-002)
- [x] `npm run typecheck` + `npm run lint` sạch
- [x] ~~`window.history.length > 1` đọc tại thời điểm bấm~~ → **thay bằng `navigation.canGoBack`**,
      `history.length` còn lại làm fallback (xem dưới)

## Sai lệch so với kế hoạch (post-phase)

**1. Key Insight 2 sai — đã đo, không phải suy đoán** (`plan.md § PP-1`).
Kế hoạch chốt `window.history.length > 1` và chấp nhận nó over-report, lý lẽ là "hệ quả xấu nhất vẫn
không phải ngõ cụt". Sai. Đo trên Chromium bị lái ở phase 07:

```
newPage() mới           -> url about:blank, history.length = 1
sau goto("/standards")  -> url /standards,  history.length = 2
```

Tab giữ nguyên `about:blank` ban đầu trong session history, nên **deep link báo length 2** và đi nhánh
`router.back()` — đưa người dùng về `about:blank`, đúng cái ngõ cụt BR-004 sinh ra để cấm. `FUN_003b`
bắt được.

Bản ship feature-detect Navigation API: `navigation.canGoBack` là `false` trên tab mới và `true` sau
một soft navigation từ `/`, tức là nó phân biệt được đúng hai trường hợp `history.length` không phân
biệt nổi. `history.length` giữ lại làm fallback cho engine chưa có Navigation API (Safari/Firefox tại
thời điểm viết), nơi hành vi over-report cũ vẫn áp dụng — nhưng không thành ngõ cụt, vì các engine đó
không tự sinh entry `about:blank` như một Chromium bị lái.
Xem `rules-panel-dismiss.tsx:18-51`; A1 trong `docs/features/F007_TheLe/technical-spec.md § 5.2` đã
viết lại thành **BÁC BỎ**.

**2. `Escape` va nhau giữa hai listener cấp `document`** (`plan.md § PP-6`).
Không phase nào lường trước: `language-selector.tsx` cũng gắn `keydown` bubble-phase trên `document`.
Đóng dropdown ngôn ngữ bằng `Escape` **cũng đóng luôn panel** và đá người dùng khỏi trang.
`stopPropagation()` không cứu được — hai listener nằm trên cùng một node, chỉ `event.defaultPrevented`
phân biệt được. Chốt nằm ở `rules-panel-dismiss.tsx:97-114`.

Đây là chi phí có thật của "gắn listener toàn cục riêng thay vì mượn `use-dismiss-on-outside.ts`"
(quyết định đã ghi trong doc-comment): mỗi listener toàn cục mới là một va chạm tiềm tàng với các
listener toàn cục đã có.

## Success Criteria

- `npm run typecheck` exit 0, `npm run lint` exit 0.
- Cả hai file dưới 200 dòng.
- `grep -c "use client" app/standards/_components/rules-section.tsx` = 0 — mục văn xuôi là server.
- `grep "disabled" app/standards/_components/` trả rỗng (DEC-002).
- `grep '"Đóng"' app/standards/_components/` trả rỗng — nhãn đi qua `dictionary`, không hardcode.
- `rules-section.tsx` không chứa `<h1>`.
- Listener `Escape` có cleanup: `removeEventListener` xuất hiện trong `rules-panel-dismiss.tsx`.

## Risk Assessment

| Risk | Likelihood | Impact | Countermove |
|---|---|---|---|
| Gộp backdrop và nút `Đóng` thành một component | Trung bình | Trung bình — không đặt được vào hai chỗ trong cây | § Architecture chốt hai export, một hook |
| Dùng `<h1>` cho heading mục | Trung bình | Cao — phá `getByRole("heading", { level: 1 })` của `GUI_001` | Bước 2 + Success Criteria grep `<h1>` |
| Rò listener `keydown` giữa các lần điều hướng | Trung bình | Trung bình — `Escape` đóng nhiều lần | Bước 5 bắt buộc cleanup |
| Hardcode `w-[94px]` cho `Đóng` | Trung bình | Thấp — vỡ ở locale EN ("Close" ngắn hơn) | § Architecture nói rõ bề rộng đến từ nội dung |
| Dựng `disabled` để `GUI_003`/`FUN_005` xanh | Thấp | **Cao** — vi phạm "no fake" của `primary-workflow.md` | DEC-002 + grep ở Success Criteria; hai test đó là `test.skip` có chủ đích |
| `rules-section` bị biến thành Client Component "cho tiện" | Thấp | Trung bình — mất SSR của toàn bộ nội dung | Key Insight 5 + grep `use client` |

**Rollback**: `rm app/standards/_components/rules-section.tsx app/standards/_components/rules-panel-dismiss.tsx`.
Chưa file nào import chúng cho tới phase 07 — gỡ ra không cascade, `/standards` vẫn là `ComingSoon`.

## Security Considerations

- `RulesCloseButton` và `RulesBackdrop` là Client Component nhưng **không nhận props nhạy cảm** — chỉ
  một `label: string` từ dictionary. Không object user Supabase nào vượt biên server/client ở đây
  (luật đã có từ F001: chỉ boolean được qua).
- `dismiss()` chỉ gọi `router.back()` / `router.push("/")` — đích cố định, không đọc từ URL, nên
  **không có bề mặt open-redirect**. Đây là điểm khác biệt có chủ ý với `/auth/callback`, nơi
  `callback-security.spec.ts` phải canh open-redirect.
- Không `dangerouslySetInnerHTML` ở đâu. `section.body` là text từ database, render như text node —
  React escape sẵn.

## Next Steps

- **Chặn**: phase 07 (ráp vào `rules-panel.tsx`).
- **Chạy song song với**: phase 03, 04 (Track B) và phase 06 (Track A) — ownership rời nhau hoàn toàn.
- Bàn giao sang phase 07: chữ ký `RulesSectionProps`, và hai export `RulesBackdrop` / `RulesCloseButton`
  cùng chỗ chúng phải được đặt (`RulesBackdrop` là anh em của drawer, dưới z-index; `RulesCloseButton`
  nằm trong chân drawer).
