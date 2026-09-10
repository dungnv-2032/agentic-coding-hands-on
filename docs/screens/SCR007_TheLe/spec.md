---
status: implemented
authored_by: doc-writer
created: 2026-09-09
---

# SCR-TheLe — Screen Spec

**Screen**: SCR-TheLe: Thể lệ
**Feature**: F007_TheLe
**Type**: composite
**Route**: `/standards`
**Generated**: 2026-09-09

## 1. Overview

**Purpose:** Bất kỳ ai — đã đăng nhập hay chưa — đọc được luật chơi SAA 2025: huy hiệu Hero mở khoá ở ngưỡng nào, 6 icon sưu tập là gì, Kudos Quốc Dân được trao ra sao. Trước F007 route này chỉ là `ComingSoon`.
**Actors:** Khách vãng lai (chưa đăng nhập), Sunner (đã đăng nhập)
**Entry Conditions:** Không có. Route công khai — `proxy.ts` chỉ canh `/todo`, `/kudos/new` (khớp chính xác) và `/profile` (`proxy.ts:51-56`).
**Exit Conditions:** Bấm `Đóng` / gõ `Escape` / bấm nền ngoài drawer → quay lại trang trước (hoặc `/` nếu không có lịch sử); bấm `Viết KUDOS` → `/kudos/new`; hoặc rời qua header/footer dùng chung.

## 2. Screen Layout

### Layout Sketch

Shell chuẩn của mọi màn đã ship (`HomeHeader` + `main` tối + `SiteFooter`, `min-h-svh`, nền `#00070C`), với `main` **rỗng có chủ đích** — frame không vẽ gì ở vùng trái. Đè lên shell là hai anh em `fixed`: scrim `z-40` phủ toàn màn, và drawer `z-50` bám mép phải rộng tối đa 553px. Drawer chia hai: cột nội dung cuộn được và chân drawer ghim.

```
┌──────────────────────────────────────────────┬────────────────┐
│  R1: Header (HomeHeader, sticky z-20)         │                │
├──────────────────────────────────────────────┤  R4: Drawer     │
│                                               │   (z-50, 553px) │
│  R2: main — rỗng có chủ đích                  │  ┌────────────┐ │
│                                               │  │ R4.1 Nội   │ │
│  R3: Scrim (fixed inset-0, z-40, black/50)    │  │  dung (cuộn)│ │
│                                               │  ├────────────┤ │
├──────────────────────────────────────────────┤  │ R4.2 Chân  │ │
│  R5: Footer (SiteFooter)                      │  └────────────┘ │
└──────────────────────────────────────────────┴────────────────┘
```

### Layout Regions

| Region ID | Name | mm id | Position | Scrollable | States |
|-----------|------|-------|----------|------------|--------|
| R1 | Header dùng chung | — | sticky-top | no | anonymous, authenticated, admin |
| R2 | `main` rỗng | — | `flex-1`, static | no | — (không nội dung) |
| R3 | Scrim | *(vùng trái phẳng của `3204:6051`)* | `fixed inset-0`, `z-40` | no | — |
| R4 | Drawer Thể lệ | `3204:6052` | `fixed inset-y-0 right-0`, `z-50`, `h-svh` | no (bản thân drawer) | default |
| R4.1 | Cột nội dung | `3204:6053` | `flex-1` trong R4 | **yes — hộp cuộn duy nhất của trang** | default, empty (chưa seed) |
| R4.2 | Chân drawer | `3204:6092` | ghim dưới (`shrink-0`, `h-14`) | no | default |
| R5 | Footer dùng chung | `354:4323` | static | no | — |

## 3. UI Elements

| ID | Region | mm id | Element | testid | States | Action | Copy key |
|----|--------|-------|---------|--------|--------|--------|----------|
| E.1 | R4 | `3204:6052` | `<aside role="dialog" aria-labelledby="rules-panel-title">` — **không** `aria-modal` (xem § 9) | `rules-panel` | default | — | — |
| E.2 | R4.1 | `3204:6055` | `<h1>` tiêu đề `Thể lệ`, 45/52 bold `#FFEA9E` — `<h1>` duy nhất của trang | — | default | — | `rules.panelTitle` |
| E.3 | R4.1 | `3204:6131` | Mục thể lệ: `<h2>` `#FFEA9E` in hoa (22/28, riêng mục 3 là 24/32) + thân trắng `text-justify` | `rules-section` | default | — | — (data: `rule_sections.heading` / `.body`) |
| E.3.c | R4.1 | `3204:6089` | Dòng kết của mục 2, render **sau** lưới icon | — | chỉ mục 2 (`closing_body` không null) | — | — (data: `rule_sections.closing_body`) |
| E.4 | R4.1 | `3204:6161`, `3204:6170` | Bậc huy hiệu Hero: ảnh pill 128×22 + nhãn ngưỡng 16/24 bold trên một hàng, mô tả 14/20 bold xuống dòng | `rules-hero-tier` | default (×4) | — | — (data: `rule_items` `kind='hero_tier'`) |
| E.5 | R4.1 | `3204:6085` | Ô icon sưu tập: artwork 80×64 (`object-cover object-top`) + caption in hoa 12/16 canh giữa | `rules-collectible-icon` | default (×6) | — | — (data: `rule_items` `kind='collectible_icon'`) |
| E.6 | R4.2 | `3204:6093` | `<button>` `Đóng` — viền `#998C5F`, nền `#FFEA9E`/10, icon 24×24, `h-14` | `rules-close-button` | default (không có state `disabled` — DEC-002) | click → dismiss | `rules.closeButton` |
| E.7 | R4.2 | `3204:6094` | `<a href="/kudos/new">` `Viết KUDOS` — nền `#FFEA9E`, chữ `#00070C`, icon bút 24×24, `flex-1` | `rules-write-kudos-link` | default (không có state `disabled` — DEC-002) | click → điều hướng | `rules.writeKudosButton` |
| E.8 | R3 | — | Scrim `bg-black/50`, `aria-hidden`, không nằm trong tab order | — | default | click → dismiss; cũng là nơi gắn listener `Escape` | — |

**Ngoài phạm vi inventory này:** `HomeHeader` và `SiteFooter` — component dùng chung toàn site, màn này dùng nguyên, không sửa.

## 4. User Actions

> **Scope:** tương tác trong-màn-hình. Điều hướng rời màn hình xem `## 8. Navigation`.

### Available Actions

| Action | Element | Trigger | Condition | Result on this screen | Source |
|--------|---------|---------|-----------|------------------------|--------|
| Cuộn nội dung | R4.1 | scroll | nội dung cao hơn cột | Cột nội dung cuộn; chân drawer (R4.2) và trang đứng yên | `app/standards/_components/rules-panel.tsx` |
| Đóng bằng nút | E.6 | click | — | Rời màn hình (xem § 8) | `app/standards/_components/rules-panel-dismiss.tsx:153-176` |
| Đóng bằng bàn phím | document | `keydown` `Escape` | `event.defaultPrevented === false` | Y hệt E.6 | `rules-panel-dismiss.tsx:94-115` |
| Đóng bằng nền ngoài | E.8 | click | — | Y hệt E.6 | `rules-panel-dismiss.tsx:116` |
| Tab ra khỏi drawer | R4 | `Tab` | — | Focus đi tiếp sang header/footer — **có chủ đích**, không có focus trap | `rules-panel.tsx` (§ 9) |

### Happy Path

1. Người dùng mở `/standards` → 2. Shell + scrim + drawer render trong một lần render server → 3. Tiêu đề `Thể lệ`, ba mục nội dung theo `position`, 4 bậc Hero dưới mục 1, lưới 6 icon dưới mục 2, dòng kết của mục 2 dưới lưới → 4. Người dùng cuộn cột nội dung đọc hết → 5. Bấm `Viết KUDOS` sang `/kudos/new`, hoặc `Đóng` quay lại chỗ cũ.

### Branches

| Decision point | Condition | Outcome on this screen | Source |
|----------------|-----------|------------------------|--------|
| Bước 2 | `rule_sections`/`rule_items` rỗng (chưa seed) | Chrome vẫn đủ — tiêu đề, `Đóng`, `Viết KUDOS` đều render; R4.1 rỗng. Không throw, không màn trắng | `lib/rules/queries.ts` (`data ?? []`) |
| Bước 2 | Truy vấn Supabase lỗi | `fetchRuleSections`/`fetchRuleItems` throw `Error("fetchX failed: …")` → error boundary mặc định của Next | `lib/rules/queries.ts` |
| Bước 2 | `image_path` trỏ file không tồn tại | Riêng ô đó hỏng ảnh; caption và nhãn vẫn đọc được, các ô khác không ảnh hưởng | `functional-spec.md § 9` |
| Bước 5 | Không có lịch sử để quay lại (deep link, tab mới) | `Đóng` điều hướng `/` thay vì `back()` | `rules-panel-dismiss.tsx:47-51` (`hasHistoryToReturnTo`) |
| Bước 5 | Chưa đăng nhập, bấm `Viết KUDOS` | `proxy.ts` đẩy về `/login` — màn này không tự canh (BR-005) | `proxy.ts:51-57` |

## 5. UI States

| State | Trigger | Visual Behavior | User Action Available | Source |
|-------|---------|----------------|-----------------------|--------|
| default | Nội dung đã seed | Ba mục, 4 bậc Hero, 6 icon render đầy đủ | Mọi action ở § 4 | `supabase/seed.sql:347-397` |
| empty | Hai bảng rỗng | R4.1 rỗng; chrome và hai nút chân drawer nguyên vẹn | Đóng, Viết KUDOS | `lib/rules/queries.ts` |
| scrolling | Nội dung cao hơn R4.1 | `scrollHeight > clientHeight` trên `rules-panel-content`; R4.2 đứng yên | Cuộn | `e2e/the-le.spec.ts` FUN_001 |
| no-scroll | Nội dung thấp hơn R4.1 | Không thanh cuộn, không khoảng cuộn | — | `e2e/the-le.spec.ts` FUN_002 |

Không có state `loading`: trang là Server Component, HTML chỉ xuất hiện khi hai read đã xong. Không có state `disabled` cho E.6/E.7 — không điều kiện nào trên màn này khiến một trong hai không dùng được (DEC-002).

## 6. Validation & Feedback

Không có trường nhập liệu nào trên màn hình này — toàn bộ tương tác là đọc và điều hướng. N/A.

## 7. Conditional UI

| Condition | Type | Element(s) | Visible when | Hidden when | Notes |
|-----------|------|------------|--------------|-------------|-------|
| Dòng kết của mục | data | E.3.c | `closing_body !== null` (chỉ mục `position = 2`) | `closing_body === null` | Ẩn hẳn phần tử thay vì render `<p>` rỗng |
| Danh sách bậc Hero | data | E.4 | mục đang render có `position = 1` | mọi mục khác | Gán theo `position`, **không** theo chỉ số mảng — mảng rỗng vẫn phải render được chrome |
| Lưới icon sưu tập | data | E.5 | mục đang render có `position = 2` | mọi mục khác | như trên |
| Cỡ tiêu đề mục | configuration | E.3 | `position = 3` → 24/32; còn lại 22/28 | — | `LARGE_HEADING_SECTION` trong `rules-panel.tsx` |
| Thân thể lệ theo ngôn ngữ | — | E.3, E.4, E.5 | **luôn tiếng Việt**, kể cả `NEXT_LOCALE=en` | — | BR-003 — không có cột `locale`; chrome (E.2/E.6/E.7) thì đổi theo locale |

## 8. Navigation

### Entry Points

| From | Trigger there | Condition | Source |
|------|----------------|-----------|--------|
| Footer dùng chung (mọi trang) | Bấm liên kết `footer.standards` | — | `app/_components/site-footer.tsx` |
| Floating widget trang chủ | Bấm lối tắt `Thể lệ SAA` | — | `lib/i18n/messages/vi-home.ts` |
| URL trực tiếp / deep link | Mở `/standards` | — | route công khai |

### Exits

| Action | Element | Condition | Destination | Result | Source |
|--------|---------|-----------|-------------|--------|--------|
| `Đóng` / `Escape` / nền ngoài | E.6, E.8, document | có lịch sử để quay lại | trang trước đó | `router.back()` | `rules-panel-dismiss.tsx:65-67` |
| `Đóng` / `Escape` / nền ngoài | E.6, E.8, document | không có lịch sử (deep link, tab mới) | `/` | `router.push("/")` | `rules-panel-dismiss.tsx:69` |
| `Viết KUDOS` | E.7 | đã đăng nhập | `/kudos/new` | điều hướng thẳng | `rules-panel.tsx` |
| `Viết KUDOS` | E.7 | chưa đăng nhập | `/login` | `proxy.ts` chặn ở đích, không phải ở đây | `proxy.ts:51-57` |

## 9. Accessibility

| Aspect | Status | Notes |
|--------|--------|-------|
| ARIA roles/labels | [VERIFIED] | E.1 mang `role="dialog"` + `aria-labelledby="rules-panel-title"` trỏ vào `<h1>` hiển thị — tên khả truy cập là chính chữ người dùng nhìn thấy, không có `aria-label` thứ hai đè lên. **`aria-modal` cố tình KHÔNG được khai** (xem dưới). Ảnh huy hiệu và icon đều `alt="" aria-hidden` vì caption/nhãn đã là text thật ngay cạnh — khai alt sẽ khiến trình đọc màn hình đọc hai lần |
| Keyboard navigation | [VERIFIED] | `Escape` đóng panel, listener gắn ở `document` và **bỏ qua sự kiện đã `defaultPrevented`** — nếu không, đóng dropdown ngôn ngữ trên header bằng `Escape` sẽ đóng luôn panel và ném người dùng khỏi trang |
| Focus management | [VERIFIED] | **Không focus trap, không `inert` trên nền.** `/standards` là một route, không phải overlay đè lên nội dung đang sống — tab ra header/footer là hành vi đúng của trang, và bẫy focus sẽ nhốt người dùng bàn phím trên một drawer họ tới bằng URL. Vì không có focus trap, khai `aria-modal="true"` sẽ là nói dối trình đọc màn hình ("ngoài dialog này không còn gì") trong khi header/footer vẫn tab tới và bấm được. Thuộc tính đã bị **gỡ ở phase 08** sau review; `e2e/the-le.spec.ts:72` assert sự VẮNG MẶT của nó |
| Screen reader compatibility | [VERIFIED] | `<aside>` (complementary) chứ không phải `<div>`; scrim `aria-hidden` và không có affordance bàn phím riêng — tương đương bàn phím của nó là listener `Escape` |
| Error announcement | N/A — màn hình chỉ đọc, không có trạng thái lỗi trong-màn-hình | — |

## 10. Responsive Behavior

| Breakpoint | Behavior | Source |
|------------|----------|--------|
| < 553px | Drawer tràn hết bề ngang (`w-full`) thay vì tràn ra ngoài viewport | `rules-panel.tsx` (`w-full max-w-[553px]`) |
| ≥ 553px | Drawer đúng 553px, bám mép phải | như trên |

Frame chỉ đo được ở một bề ngang, không có bản mobile. `max-w` là luật responsive tối thiểu để drawer không bao giờ tràn viewport, không phải một bản thiết kế mobile được suy diễn.
