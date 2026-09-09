# Phase 07 — Tích hợp: vỏ drawer + `app/standards/page.tsx`

## Context Links

- `spec/the-le/technical-spec.md § 3.1` (khối **FE**), `§ 4.1`, `§ 5.4 Data Flow`
- `clarifications.md § "Route and surfacing"`, `§ "Layout and behaviour"`, `§ "Test contract"`
- `design/the-le.png` — frame render 1×
- Phase 04 (`getRulesContent`), phase 05 (`RulesSection`, `RulesBackdrop`, `RulesCloseButton`),
  phase 06 (`RulesHeroTierList`, `RulesCollectibleGrid`, `pen-icon.svg`)
- House style: `app/awards-information/page.tsx` (shell chuẩn), `app/_page-context.ts`, `app/_fonts.ts`

## Overview

- **Priority**: P1
- **Status**: **completed** — `/standards` render nội dung thật, `ComingSoon` chỉ bị thay ở route này.
  Một thuộc tính ở § Architecture đã bị gỡ sau review (`aria-modal`), và chính phase này là nơi đo ra
  lỗi dismiss của phase 05. Xem § "Sai lệch so với kế hoạch".
- **Description**: Phase DUY NHẤT ráp mọi mảnh: vỏ drawer `rules-panel.tsx` và trang thật
  `app/standards/page.tsx` thay `ComingSoon`. Đây là lần đầu tiên `/standards` render nội dung thật.

## Key Insights

1. **`ComingSoon` bị thay, không bị xoá.** Component vẫn phục vụ `/admin` (và bất kỳ route đặt chỗ nào
   còn lại). Chỉ `app/standards/page.tsx` đổi.
2. **Mục 1 và mục 2 nhận `children`.** Bậc Hero là `children` của mục 1; lưới icon là `children` của
   mục 2 (và `closingBody` của mục 2 render sau lưới — đúng như `rules-section.tsx` đã dựng ở phase 05).
   Mục 3 không có `children`.
3. **`sections[i]` truy cập theo chỉ số là mong manh nếu bảng rỗng.** Bảng rỗng phải render chrome +
   hai nút, không nổ (functional-spec § 9). Nên `rules-panel.tsx` map qua mảng và quyết định `children`
   theo `position`, không viết `sections[0]` / `sections[1]` cứng.
4. **Chân drawer ghim, cột nội dung cuộn.** `h-svh` + `flex flex-col` + cột nội dung `flex-1
   overflow-y-auto` + chân drawer `shrink-0`. Đây là chỗ FR-403 sống hoặc chết — `FUN_001/002` đo đúng
   `scrollHeight`/`clientHeight` của `rules-panel-content`.
5. **`Viết KUDOS` dùng `pen-icon.svg` MỚI của phase 06** (`/images/rules/pen-icon.svg`, `fill="#00070C"`),
   KHÔNG phải `/images/home/widget-pen-icon.svg`. Dùng nhầm = bút vô hình trên nền vàng.
6. **`<a href="/kudos/new">` thật, không `router.push`, không kiểm quyền client** (BR-005). Dùng
   `<Link>` của Next là được — nó render ra `<a href>`, nên assertion `getAttribute("href")` của
   `FUN_004` vẫn khớp.

## Requirements

- **FR-201** — `<h1>` = `dictionary.rules.panelTitle`; `rules-panel` mang `role="dialog"` và
  `aria-labelledby` trỏ id của `<h1>`. (~~`aria-modal="true"`~~ — gỡ sau review, xem § "Sai lệch so
  với kế hoạch"; FR-201 ở functional-spec đã sửa theo.)
- **FR-202/203/204** — ba mục theo `position`, bậc Hero trong mục 1, lưới icon trong mục 2
- **FR-402 / BR-005** — `<a href="/kudos/new">` với `data-testid="rules-write-kudos-link"`, `flex-1`
- **FR-403** — `rules-panel-content` cuộn độc lập, chân drawer ghim
- **FR-404** — `RulesBackdrop` là anh em của drawer, dưới z-index
- **FR-405** — drawer `w-full max-w-[553px]`
- **Test contract** — `rules-panel`, `rules-panel-content`, `rules-write-kudos-link`

## Architecture

### `app/standards/page.tsx` (~50 dòng)

```tsx
export const metadata: Metadata = { title: "Thể lệ — Sun* Annual Awards 2025" };

export default async function StandardsPage() {
  const [{ locale, dictionary, isAuthenticated, isAdmin }, rules] = await Promise.all([
    getPageContext(),
    getRulesContent(),
  ]);
  ...
}
```

Hai read độc lập → `Promise.all`, đúng khuôn `board-data.ts` / `_page-context.ts`. `getRulesContent()`
tự tạo client của nó (phase 04); page không truyền client vào.

Composition, sao chép khuôn `app/awards-information/page.tsx`:

```
<div className={`${montserrat.variable} ${montserratAlternates.variable} flex min-h-svh w-full flex-col bg-[#00070C] font-montserrat`}>
  <HomeHeader locale dictionary isAuthenticated isAdmin signOutAction={signOut} />
  <main className="flex flex-1 flex-col" />        {/* nền phẳng — frame không có nội dung bên trái */}
  <SiteFooter dictionary={dictionary} />
  <RulesBackdrop />                                 {/* fixed inset-0 z-40 */}
  <RulesPanel rules={rules} copy={dictionary.rules} />  {/* fixed inset-y-0 right-0 z-50 */}
</div>
```

`<main>` rỗng là có chủ ý và phải được comment: frame's vùng trái là nền tối phẳng, không có nội dung.
Không bịa nội dung vào đó. Nó vẫn tồn tại để shell giữ đúng cấu trúc `header / main / footer` mà bốn
màn đã ship đang dùng.

**KHÔNG render `FloatingWidget`** — cùng lý do `/awards-information` không render: frame không có.
(Và widget trỏ về chính `/standards`, nên có nó ở đây là một vòng lặp vô nghĩa.)

### `app/standards/_components/rules-panel.tsx` (server, ~80 dòng)

```tsx
interface RulesPanelProps { rules: RulesViewModel; copy: Dictionary["rules"]; }
```

```
<aside data-testid="rules-panel"
       role="dialog" aria-modal="true" aria-labelledby="rules-panel-title"
       class="fixed inset-y-0 right-0 z-50 flex h-svh w-full max-w-[553px] flex-col justify-between bg-[#00070C] px-10 pb-10 pt-6">

  <div data-testid="rules-panel-content" class="flex flex-1 flex-col gap-6 overflow-y-auto">
    <h1 id="rules-panel-title" class="text-[45px]/[52px] font-bold text-[#FFEA9E]">{copy.panelTitle}</h1>
    {rules.sections.map(section => (
      <RulesSection key={section.position} section={section}
                    headingSize={section.position === 3 ? "lg" : "md"}>
        {section.position === 1 && <RulesHeroTierList tiers={rules.heroTiers} ... />}
        {section.position === 2 && <RulesCollectibleGrid icons={rules.collectibleIcons} ... />}
      </RulesSection>
    ))}
  </div>

  <div class="flex shrink-0 gap-4 pt-6">
    <RulesCloseButton label={copy.closeButton} />
    <Link href="/kudos/new" data-testid="rules-write-kudos-link"
          class="flex h-14 flex-1 items-center justify-center gap-2 rounded bg-[#FFEA9E] px-4 font-bold text-[#00070C] transition-colors hover:bg-[#F0D98A]">
      <Image src="/images/rules/pen-icon.svg" alt="" aria-hidden width={24} height={24} />
      {copy.writeKudosButton}
    </Link>
  </div>
</aside>
```

- `padding 24 40 40 40` (frame) → `px-10 pb-10 pt-6`.
- `justify-between` trên panel + `flex-1 overflow-y-auto` trên cột nội dung + `shrink-0` trên chân
  drawer = chân ghim, nội dung cuộn. **Đúng ba class này là FR-403.**
- `headingSize` quyết định theo `position === 3`, không theo chỉ số mảng — bảng rỗng hay thiếu mục
  cũng không nổ (Key Insight 3).
- `hover:bg-[#F0D98A]` — "hover darkens it slightly" (`clarifications.md § GUI_004`). Đây là giá trị
  MỚI, không có token sẵn cho nút vàng đặc; ghi lý do vào doc-comment.
- `<aside>` chứ không `<div>`: drawer là nội dung bổ trợ nằm ngoài luồng chính. `role="dialog"` được
  đặt tường minh nên vai trò ngữ nghĩa không mơ hồ.
- **Không focus trap, không `inert` trên nền.** Đây là một route, không phải modal thật — người dùng
  tab ra header/footer là hành vi đúng của một trang. `aria-modal="true"` được đòi bởi test contract
  nên vẫn đặt; ghi mâu thuẫn nhỏ này vào doc-comment thay vì dựng focus trap không ai yêu cầu (YAGNI).

## Related Code Files

**Create**
- `app/standards/_components/rules-panel.tsx`

**Modify**
- `app/standards/page.tsx` — thay toàn bộ nội dung `ComingSoon` bằng trang thật

**Delete** — không có. `app/_components/coming-soon.tsx` **giữ nguyên** (còn route khác dùng).

## Implementation Steps

1. Xác nhận bốn phụ thuộc đã sẵn sàng: `lib/rules/rules-data.ts` (phase 04), hai component phase 05,
   hai component + `pen-icon.svg` phase 06. Thiếu bất kỳ cái nào → **BLOCKED**, không stub thay thế.
2. `ComingSoon` **không** trở thành dead code — đã đo: `app/admin/page.tsx`,
   `app/kudos/secret-box/page.tsx` và `app/kudos/[id]/page.tsx` vẫn render nó (các file
   `awards-information` / `kudos` / `kudos/new` / `profile` chỉ còn nhắc tên trong comment lịch sử).
   Nên chỉ thay ở `app/standards/page.tsx` và **giữ nguyên** `app/_components/coming-soon.tsx`.
   Nếu muốn xác nhận lại: `grep -rln "ComingSoon" app/`.
3. Tạo `app/standards/_components/rules-panel.tsx` theo § Architecture. Doc-comment ghi node
   `3204:6051` (frame), `3204:6052` (drawer), `3204:6053` (cột nội dung), `3204:6092` (chân drawer),
   và ghi rõ ba quyết định: dùng `pen-icon.svg` mới của `rules/` chứ không của `home/`; `hover:bg-[#F0D98A]`
   là giá trị mới cho nút vàng đặc; không focus trap vì đây là route.
4. Viết lại `app/standards/page.tsx` theo § Architecture. Giữ `export const metadata` nhưng đổi title
   sang `"Thể lệ — Sun* Annual Awards 2025"`. Xoá comment "Declared placeholder (phase 07…)" cũ — nó
   đã hết đúng.
5. Comment `<main>` rỗng nêu rõ lý do (frame's vùng trái là nền phẳng), để lần đọc sau không ai tưởng
   là thiếu sót.
6. `npm run typecheck`, `npm run lint`, rồi `npm run build` — build là chỗ lỗi Server/Client boundary
   lộ ra mà typecheck bỏ qua.
7. Chạy thử bằng mắt một lần trước khi bàn giao: `npm run dev`, mở `http://127.0.0.1:3000/standards`,
   xác nhận panel hiện, cuộn được, hai nút thấy được (đặc biệt: **bút có nhìn thấy trên nền vàng không**).
8. **Không** tự chạy `npx playwright test` để tuyên bố GREEN — đó là việc của `tester` ở phase 08.
   Nhưng nếu muốn tự kiểm nhanh thì được, miễn kết quả không thay thế phase 08.

## Todo List

- [x] Xác nhận 4 phụ thuộc phase 04/05/06 đã có
- [x] `grep -rn "ComingSoon" app/` — biết ai còn dùng trước khi thay
- [x] `rules-panel.tsx` — `<aside data-testid="rules-panel">` + `role="dialog"` + `aria-labelledby`
      — ~~`aria-modal`~~ **đã gỡ sau review H1** (xem dưới)
- [x] `<h1 id="rules-panel-title">` = `copy.panelTitle`
- [x] `rules-panel-content`: `flex-1 overflow-y-auto`; chân drawer `shrink-0`
- [x] `children` gán theo `section.position`, không theo chỉ số mảng
- [x] `<Link href="/kudos/new" data-testid="rules-write-kudos-link">` + `flex-1` + `pen-icon.svg` của `rules/`
- [x] `app/standards/page.tsx` — `Promise.all([getPageContext(), getRulesContent()])`, shell chuẩn
- [x] `<main>` rỗng có comment giải thích
- [x] Không render `FloatingWidget`
- [x] `npm run typecheck` + `npm run lint` + `npm run build` sạch — `/standards` là route động
- [x] Xem bằng mắt ở `npm run dev` — bút TỐI, hiện rõ trên nền `#FFEA9E`

## Sai lệch so với kế hoạch (post-phase)

**1. `aria-modal="true"` đã bị gỡ** (`plan.md § PP-2`).
§ Architecture đặt nó vào rồi tự ghi mâu thuẫn ngay bên dưới: "Không focus trap, không `inert` trên
nền… `aria-modal="true"` được đòi bởi test contract nên vẫn đặt". Review H1 ở phase 08 không chấp nhận
lối thoả hiệp đó: khai modality trong khi header/footer vẫn nằm trong tab order là **hứa với screen
reader một thứ UI không giữ**. Hai lối ra khả dĩ — dựng focus trap (không ai yêu cầu, YAGNI) hoặc bỏ
lời hứa. Chọn bỏ lời hứa: `role="dialog"` + `aria-labelledby` ở lại, `aria-modal` biến mất, và E2E
`GUI_001` nay assert nó **VẮNG MẶT** (`e2e/the-le.spec.ts:66-72`). Sửa lan sang `clarifications.md`
và FR-201 của cả hai functional-spec.

Đáng ghi lại: contract đóng băng ở phase 02 **có thể** sửa — nhưng chỉ theo hướng làm assertion mạnh
lên, và phải sửa đồng bộ mọi bản sao của nó. Đó là điều đã làm ở đây.

**2. Phase này là nơi lỗi dismiss của phase 05 bị đo ra** (`plan.md § PP-1`). Bước 7 "xem bằng mắt"
và lượt tự kiểm ở bước 8 phát hiện `FUN_003b` đỏ vì `history.length` báo 2 trên deep link — trả về
phase 05 sửa bằng `navigation.canGoBack`, không nới test.

**3. Chân drawer dùng `mt-6` chứ không `pt-6`** — cùng khoảng cách 24px, khác chỗ đặt; `gap-4` và
`shrink-0` giữ nguyên như § Architecture. Vụn, ghi cho khớp bản đọc sau.

## Success Criteria

- `npm run typecheck`, `npm run lint`, `npm run build` đều exit 0.
- `/standards` render `<h1>Thể lệ</h1>`, 3 `rules-section`, 4 `rules-hero-tier`, 6 `rules-collectible-icon`.
- `grep "ComingSoon" app/standards/page.tsx` trả rỗng.
- `grep "images/home/widget-pen-icon" app/standards/` trả rỗng — dùng đúng asset mới.
- `grep -c "h1" app/standards/_components/rules-panel.tsx` — đúng một `<h1>` trên toàn trang
  (`HomeHeader`/`SiteFooter` không có `<h1>`; xác nhận bằng `getByRole("heading",{level:1})` ở phase 08).
- Cả hai file dưới 200 dòng.
- Xem bằng mắt: bút TỐI, thấy rõ trên nền `#FFEA9E`.

## Risk Assessment

| Risk | Likelihood | Impact | Countermove |
|---|---|---|---|
| Dùng `/images/home/widget-pen-icon.svg` theo thói quen | **Cao** | Cao — bút vô hình, phase 08 bắt được nhưng tốn một vòng | Key Insight 5 + grep ở Success Criteria + kiểm mắt ở bước 7 |
| `sections[0]`/`sections[1]` cứng → nổ khi bảng rỗng | Trung bình | Cao — vi phạm § 9, màn trắng | Key Insight 3, gán `children` theo `position` |
| Thiếu `shrink-0` ở chân drawer → chân bị nén, `FUN_001` sai | Trung bình | Cao | Ba class của FR-403 nêu tường minh ở § Architecture |
| `HomeHeader` hoặc `SiteFooter` có sẵn một `<h1>` → `GUI_001` mơ hồ | Thấp | Cao — strict-mode violation | Success Criteria đòi xác nhận; nếu có, đổi `<h1>` của panel thành `<h2>` sẽ SAI (FR-201) — phải sửa chỗ kia hoặc báo lên |
| `<Link>` không render `href` như mong đợi | Thấp | Cao — `FUN_004` đỏ | `<Link>` của Next luôn render `<a href>`; nếu không, thay bằng `<a>` thuần |
| Panel `z-50` bị header che | Trung bình | Trung bình | Panel `fixed z-50`, backdrop `z-40`; kiểm mắt ở bước 7 |
| Xoá `ComingSoon` "cho gọn" | Thấp | Trung bình — hỏng route khác | Bước 2 + § Related Code Files nói rõ giữ nguyên |

**Rollback**: `git checkout -- app/standards/page.tsx && rm app/standards/_components/rules-panel.tsx`.
`/standards` quay lại `ComingSoon` — route vẫn resolve, footer và widget vẫn không 404. Hai bảng
Supabase ở lại (vô hại, không ai đọc). Rollback không cascade sang phase nào.

## Security Considerations

- **Chỉ hai boolean qua biên server/client.** `getPageContext()` trả cả object, nhưng chỉ
  `isAuthenticated`/`isAdmin` vào `HomeHeader`. Object user Supabase KHÔNG BAO GIỜ vượt biên — luật
  đã có từ F001, và phase này không được là chỗ đầu tiên phá nó.
- **Không Server Action nào trên trang này** ngoài `signOut` đã có sẵn của `HomeHeader`. Trang không
  ghi gì.
- **`Viết KUDOS` không tự phán quyền** (BR-005). `proxy.ts` canh `/kudos/new`; nhân bản luật ở đây
  tạo hai nguồn sự thật. Không thêm `if (!isAuthenticated)` quanh nút.
- **Không open-redirect**: `<Link href>` là hằng số `/kudos/new`, không đọc từ `searchParams`.
- Nội dung render từ database là text node (React escape), không `dangerouslySetInnerHTML`.

## Next Steps

- **Chặn**: phase 08 (GREEN + visual).
- Bàn giao sang phase 08: `/standards` đã render thật; `redCommand` không đổi
  (`npx playwright test e2e/the-le.spec.ts --project=anon`), giờ phải xanh.
- Sau delivery (ngoài scope các phase): `doc-writer` cấp `PERM###` cho hai bảng, dựng
  `docs/features/F007_TheLe/`, và cập nhật `docs/generated/{route-list,screen-list,feature-list}.md`.
