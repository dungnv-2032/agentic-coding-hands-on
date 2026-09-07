# Dropdown ngôn ngữ: hợp đồng thị giác từ MoMorph + điều hướng bàn phím đầy đủ

**Date**: 2026-09-05 (session 10:10–11:37 +07)  
**Severity**: medium  
**Component**: login page language selector (E02)  
**Status**: resolved  

## What Happened

Login page đã có dropdown ngôn ngữ hoạt động (mở/đóng), nhưng panel khi mở được trang điểm bằng giá trị tự chế (`bg-[#0B0F12]`, không viền, không phân biệt hàng được chọn) vì lúc viết F001_Login, design chưa vẽ trạng thái mở. MoMorph screen `hUyaaugye2` giờ cung cấp hợp đồng thực.

Ba giai đoạn: (1) RED e2e cho hợp đồng open-state + keyboard nav, (2) triển khai visual contract + listbox keyboard nav, (3) GREEN, xác thực thị giác, kiểm tra regression, cập nhật docs. Chạy dưới `e2e-red-first`: RED trước (C3c/C3d/C3e), rồi triển khai, rồi GREEN.

Tất cả cổng kiểm tra vượt qua: typecheck 0, lint 0, build 0, e2e 23/23 (11 spec này + 12 spec authentication + setup), reviewer 8/10 không critical, evidence gate SEALED.

## The Brutal Truth

Sự thật tàn nhẫn: bốn điều không vừa vặn như họ lẽ ra phải vừa, mỗi cái dạy được cái gì.

**1. Design ngụ ý overlay, người dùng chọn drop-below — nhưng ai đọc Figma sẽ nghĩ code sai.**

Trong design node tree (figma `721:4942`), hàng VN dùng chung `componentId 186:1692` với nút trigger đóng trên F001_Login — cả hai `108×56`, cùng một component. Strong signal là panel được vẽ chồng lên trigger. Nhưng clarifications.md ghi: người dùng chọn thả xuống dưới (`absolute top-full`) chứ không đè lên. Quyết định lợp suốt, không mở để tái thảo luận.

Bài học: hàng năm tới, ai đó sẽ mở Figma, thấy componentId dùng chung, và nói "code được restyle để overlay, đó là cách design muốn" — và sửa lại. Cái phải ghi là: *design gợi ý overlay, nhưng lựa chọn drop-below được ghi quyết định trong clarifications.md tại lúc này*.

**2. Subagent báo cáo xác thực thị giác nhưng không có ảnh.**

Tester agent viết: "visual validation" ✓, nhưng evidence folder trống không ảnh. Nguyên nhân: script `capture-dropdown.mjs` nó để lại tại repo root gọi `browser.createContext()` — đó không phải Playwright API. Cái đúng là `newContext`. Script lặng lẽ thất bại, chỉ CSS assertion chạy.

Kết quả: báo cáo nói "visual PASS" với bằng chứng chỉ là computed-style check. Hình ảnh được tái chụp sau đó bằng chromium bundled của project qua temp Playwright config, vì Playwright MCP server muốn kênh Chrome tại `/opt/google/chrome/chrome` — không có.

Bài học khó chịu: khi một agent báo cáo validation thị giác, phải kiểm tra xem nó thực sự có ảnh hay chỉ mô phỏng. "Reported" không phải "done" khi không có artifact.

**3. Spec có lỗi mà chỉ đọc source mới bắt được.**

Spec-delta.md đầu tiên gộp hai quyết định thành một hàng: "Escape / click ngoài → trả focus về trigger". Nhưng code ý định là: Escape trả focus, click ngoài **không** giật focus (user đang nhắm chỗ khác). Doc-writer đọc source (`language-selector.tsx:58` no focus return on outside-click), nhận ra lỗi, chia thành hai hàng (§7 row 2 và row 3, §9 khác nhau). Spec sau đó được sửa.

Bài học: agent thứ hai đọc code thắng agent thứ nhất đọc giấy. Spec tự chế luôn có khoảng cách với hành vi thực; cần downstream agent có quyền kiểm tra.

**4. Schema evidence-gate chặt chẽ và không ghi chép tại điểm sử dụng.**

`study-context.json` và `inspection-verdict.json` bị reject nếu có extra key, bắt buộc mỗi `acceptanceCovered` phải lặp lại chính xác text của criterion, hạn chế `disposition` chỉ Accept/Reject/Defer, yêu cầu `path:NNN` line number trên bất kỳ Accept finding. Ba lần lặp lại mới pass.

Bài học: schema này cần một README hoặc inline comment. Hoặc xuất nó từ template thay vì viết tay. Hiện tại, trial-and-error là cách học nó.

## Technical Details

### RED baseline
```json
{
  "C3c": "Expected: \"rgb(0, 7, 12)\" Received: \"rgb(11, 15, 18)\" (panel bg)",
  "C3d": "Expected: \"rgba(255, 234, 158, 0.2)\" Received: \"rgba(0, 0, 0, 0)\" (selected option)",
  "C3e": "Expected: focused Received: inactive (VN option not focused on open)"
}
```

Đúng. Hai cái pertinent: panel nền còn giá trị cũ `#0B0F12` (rgb 11,15,18), option được chọn không có nền phân biệt. Cái thứ ba: focus landing — tester ghi trong C3e: khi panel mở, focus phải nhảy vào option đang chọn. Code cũ không làm.

### GREEN rerun

```
npx playwright test e2e/login-screen.spec.ts --project=anon → exit 0, 11/11 pass
npm run test:e2e → exit 0, 23/23 pass (full suite, setup + anon + authed)
```

Không regression trên C1, C3, C3b (case bị ảnh hưởng nhất bởi ul/li → div[role=listbox] migration), C4, C5, C10.

### Visual contract — verbatim từ spec-delta §3

Panel: `bg-[#00070C]`, `border border-[#998C5F]`, `rounded-lg` (8px), `p-1.5` (6px).  
Option row: `w-[108px] h-14`, `rounded-[2px]`.  
Selected: `bg-[rgba(255,234,158,0.2)]`.  
Unselected hover: `hover:bg-[rgba(255,234,158,0.08)]`.  
Label: Montserrat 700, 16px/24px, letter-spacing 0.15px.

Không suy đoán, không làm tròn. Đúng từng token.

### Keyboard navigation — FR-203.c

- ArrowDown/ArrowUp: di chuyển activeIndex vòng quanh danh sách (modulo 2).
- Home/End: nhảy đầu/cuối.
- Enter/Space: chọn locale (nút native button đã handle; không preventDefault Space ở handler để tránh double-fire).
- Escape: closePanel + restoreFocusToTrigger (document-level listener).
- Focus landing: khi open=true, useEffect focus optionRefs[activeIndex]; khi activeIndex thay đổi giữa open panel, effect fires again.

Roving tabindex: `tabIndex={index === activeIndex ? 0 : -1}` — chỉ một option có tabIndex 0, rest là -1. Screen reader thấy được option roles.

### React purity smell — reviewer flag

Reviewer tìm: `setOpen` trong handler dùng functional updater, nhưng bên trong nó gọi `setActiveIndex(OPTIONS.findIndex(...))` — side effect trong pure function.

```tsx
// BEFORE (smelly)
onClick={() => {
  setOpen((prev) => {
    const next = !prev;
    if (next) setActiveIndex(OPTIONS.findIndex((o) => o.value === locale));
    return next;
  });
}}
```

Lý thuyết: React có thể gọi updater nhiều lần (StrictMode double-invoke dev, hoặc rebase render). Thực tế: `OPTIONS.findIndex()` idempotent, `setActiveIndex` bails out via `Object.is` — harmless hôm nay. Nhưng nó fragile: nếu ai đó làm computation phụ thuộc vào `prev`, hoặc app sau này thêm `<StrictMode>` xung quanh tree, nó im lặng break.

**Fix áp dụng:** orchestrator sửa lại — đọc `open` trực tiếp, gọi hai setter riêng biệt. React 18 auto-batch trong event handler nên cùng render. Typecheck, lint, e2e 23/23 xanh sau fix.

### IconFlagEn — hand-drawn, không MoMorph source

FR-203.a: "mỗi option có cờ của riêng nó". Design hàng VN có cờ VN (node `...;186:1709`), hàng EN có cờ GB-NIR (Union Jack). Nhưng `icons.tsx` không có `IconFlagEn` — chỉ `IconFlagVn`.

Để thỏa C3b (two distinct SVGs), phải draw `IconFlagEn` bằng tay — geometry match `IconFlagVn` (cùng 24×24 canvas). JSDoc ghi honestly: "No MoMorph counterpart. Hand-drawn to match IconFlagVn geometry."

Reviewer low-severity flag: asset source không từ design. Nhưng justified — cần để satisfy FR-203.a. Worth một note trong clarifications.md cho traceability, không cần rework.

## What We Tried

### Phase 01 — RED (tester, 45m)

Viết test assertions cho C3c/C3d/C3e:
- C3c: kiểm tra panel background computed style === "rgb(0, 7, 12)" (đo từ `#00070C`), option background === "rgb(255, 255, 255)" (transparent, fallback white value), border 1px, radius.
- C3d: option được chọn === "rgba(255, 234, 158, 0.2)".
- C3e: khi mở panel, focus phải active trên option có `aria-selected=true`.

Tester thêm vào `e2e/login-screen.spec.ts` trong test C3 suite. Chạy: exit 1, ba failures chính xác như expected.

### Phase 02 — Implement (momorph-ui-implementer, 1h30)

Bắt đầu từ RED evidence + spec-delta §3 (read-only).

1. **Container migration:** thay `ul[role=list]` → `div[role=listbox]`, `li[role=listitem]` → `button[role=option]`.
2. **Panel styling:** áp dụng tokens verbatim: bg-[#00070C], border border-[#998C5F], rounded-lg, p-1.5. Xóa giá trị cũ: bg-[#0B0F12], hover:bg-white/10, shadow-lg, overflow-hidden, min-w-[108px], py-1, px-4 py-2 on option.
3. **Option styling:** w-[108px] h-14, rounded-[2px], flex justify-center. Selected: bg-[rgba(255,234,158,0.2)]. Hover: hover:bg-[rgba(255,234,158,0.08)] (mutually exclusive via ternary, không CSS cascade conflict).
4. **Keyboard handler:** `handleListKeyDown` cho ArrowDown/ArrowUp/Home/End. Focus management: useEffect([open, activeIndex]) để focus optionRefs[activeIndex]. Document listener cho Escape (từ cái hiện tại, reuse).
5. **roving tabindex:** `tabIndex={index === activeIndex ? 0 : -1}`.
6. **Focus restoration:** click option gọi `handleSelect` → setOpen(false) → triggerRef.focus(). Click ngoài (document listener) setOpen(false) **no focus return**. Escape: setOpen(false) + triggerRef.focus().

Reviewer then caught setActiveIndex-in-updater smell; orchestrator fixed. File 186 line, under 200-line limit, no split.

### Phase 03 — GREEN + visual validation + docs sync

Rerun: e2e exit 0, 23/23 pass, C3c/C3d/C3e green.

Visual validation: tester report không có ảnh. Orchestrator re-captured bằng temp Playwright config + project bundled chromium:
- `panel-open.png`: panel mở, default locale VN. Selected row (VN) có nền vàng nhạt, EN transparent.
- `panel-hover-en.png`: hover EN (unselected). Hover background barely visible (rgba(255,234,158,0.08) on #00070C black).
- `panel-focus-en.png`: keyboard focus ring trên EN. Ring màu #998C5F (reuse panel border).
- `header-in-context.png`: panel trong context header. Trigger ở trên, chevron xoay 180°, panel thả xuống dưới (không đè overlay).

Visual overall PASS.

Docs sync: doc-writer updated:
- `docs/features/F001_Login/functional-spec.md`: FR-203.a/b/c bổ sung (thay "TBD").
- `docs/screens/SCR001_Login/spec.md` §7: mỗi interaction row thay thế "TBD (draft)" (row mở/đóng, chọn, di chuyển, Escape, click ngoài).
- `docs/screens/SCR001_Login/spec.md` §9: ARIA, keyboard, focus semantics ghi rõ.
- `spec/language-dropdown/spec-delta.md`: flip status → "applied".

## Root Cause Analysis

Không có root cause để phân tích — đây là mặc định feature mà đã được thiết kế + xây dựng đúng.

Nhưng ba điểm "bệnh nhân" đã xác định ở The Brutal Truth là dấu hiệu hệ thống:

1. **Thiếu traceability giữa design intent và code decision.** Design node tree gợi ý overlay; clarifications.md ghi drop-below. Người tương lai đọc Figma sẽ không thấy clarifications.md. Cơ chế là: ghi link từ design → clarifications.md trong code JSDoc (đã làm), nhưng không là rule bắt buộc.

2. **Agent completion report không phải là acceptance — cần xác thực artifact.**  "visual validation completed ✓" mà không có screenshot là chỉ báo cáo trạng thái, không bằng chứng. Phải check.

3. **Spec tự chế và code thực hiện sẽ lệch nếu không có downstream reader.**  Spec đầu tiên gộp "Escape + click outside" thành một hành vi. Code tách biệt. Doc-writer đọc code, bắt được. Nếu chỉ có spec + acceptance test (mà acceptance test không cover click-outside focus), sẽ trôi.

## Lessons Learned

1. **Lưu decision rationale ở vị trí nó sẽ được tìm thấy.** Design node gợi ý overlay; nó sẽ lại gợi ý lần tới. Ghi vào `clarifications.md` và **link từ code** (JSDoc hoặc comment), không chỉ trong plan doc. Người tương lai tìm thấy code trước design.

2. **"Visual validation" cần artifact.** Nếu agent báo cáo validation thị giác, cần ít nhất một ảnh. Công thức: report("visual-pass") → screenshot. Không screenshot → re-capture trước accept.

3. **Downstream reader là lớp an toàn cho spec.** Không tin spec tự chế. Mỗi khi có downstream agent (doc-writer, reviewer) đọc source, họ sẽ bắt sai lệch. Khuyến khích nó.

4. **Schema phức tạp cần comment.** `study-context.json` schema strict nhưng undocumented tại điểm dùng. Template hoặc README giúp. Nếu schema từ tool, tool nên output violation rõ ràng (đừng silent reject).

5. **React side effect trong updater là code smell.** Nó làm việc hôm nay vì data idempotent. Nhưng nó nguy hiểm hàng năm tới. `setOpen(value); setActiveIndex(computed)` ở handler level, không bên trong updater. Clarity trên safety.

## Next Steps

| Task | Owner | By | Note |
|---|---|---|---|
| Tab-to-close panel (deferred per user decision) | backlog | — | Medium severity. Panel stays open nếu user Tab ra khỏi nó. FR-203.c không cover; C3e không assert. Known limitation, ghi ở plan.md §74 + spec.md §9. Reopen as task nếu product muốn. |
| `aria-controls` dangling ID pre-existing | backlog | — | Trigger có `aria-controls` → listbox ID, nhưng panel conditionally rendered nên ID không tồn tại khi đóng. Pre-existing. Fix: always-mount panel (display:none) hoặc drop `aria-controls` khi !open. Low priority. |
| `IconFlagEn` provenance note | done | — | Thêm vào `docs/screens/SCR001_Login/spec.md` §3 traceability comment (đã làm bởi doc-writer). |
| Cập nhật evidence-gate schema docs | pending | — | Schema `study-context.json`/`inspection-verdict.json` cần README hoặc inline comment ở template. Backlog: `plans/260905-1010-.../evidence/schema-documentation.md`. |

---

**Cổng kiểm tra cuối:**
- typecheck: 0 errors
- lint: 0 errors (post-review fix: fixed `'page: any'` type)
- build: 0 errors
- e2e: 23/23 pass
- reviewer: 8/10 (0 critical)
- evidence gate: SEALED ✓
