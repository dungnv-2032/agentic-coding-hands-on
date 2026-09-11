# Phase 03 — GREEN rerun + visual evidence

**tester · 260911-1610** · Status: **DONE**

## Summary

Closed the e2e-red-first loop: reran phase 01's targeted command GREEN with exact byte parity, verified full-file regression with K-27 tripwire passing, passed lint and typecheck, captured three visual states of the hashtag filter listbox, and confirmed fidelity against the MoMorph frame. All five hashtag filter tests (K-31..K-35) pass green, all 35 kudos-live-board tests pass green, and the visual evidence shows the 348px bounded scrollable box with focus/selected styling matching the spec.

## Test Results

### 1. Targeted GREEN — K-31..K-35

**Command:** `npm run test:e2e -- e2e/kudos-live-board.spec.ts --project=anon -g "K-31|K-32|K-33|K-34|K-35"`  
**Exit code:** 0  
**Result:** 6/6 passed (5 hashtag filter tests + setup)

- **K-31** — hashtag filter menu max-height is 348px and contains all 13 options ✓
- **K-32** — hashtag option shows focus glow with correct color on keyboard focus ✓
- **K-33** — clicking hashtag option closes menu and filters both sections ✓
- **K-34** — hashtag option retains aria-selected and styling after reopen ✓
- **K-35** — re-clicking hashtag option clears filter and restores full board ✓

### 2. Full Regression — K-0..K-35

**Command:** `npm run test:e2e -- e2e/kudos-live-board.spec.ts --project=anon`  
**Exit code:** 0  
**Result:** 35/35 passed

**Critical tripwires verified:**
- **K-3** — filter menus: hashtag has 13 options, department has 50 ✓
- **K-8** — filter selection resets carousel to slide 1 ✓
- **K-26..K-30** — department dropdown tests (all 5 passing, including K-27 which verifies department listbox remains 348px after prop removal) ✓

**Prop removal regression check (K-27):**  
Department listbox still bounded at `max-h-[348px]` and contains all 50 options after removing the `scrollable` prop from `kudos-filter-bar.tsx`. The shared `kudos-filter-menu.tsx` now has the scroll box as default, not conditional.

### 3. Code Quality

**Lint:** `npm run lint`  
**Exit code:** 0  
**Result:** 0 errors, 31 pre-existing warnings (no new errors introduced)

**Typecheck:** `npm run typecheck`  
**Exit code:** 0  
**Result:** Clean (no generated-file errors)

### 4. File Line Count

Both modified files respect the 200-line limit:
- `app/kudos/_components/kudos-filter-menu.tsx`: 59 lines
- `app/kudos/_components/kudos-filter-bar.tsx`: 112 lines

## Visual Evidence

### Captures Generated

Three screenshots captured at 1440px viewport, clipped to the listbox plus 80px margin:

1. **`hashtag-filter-closed.png`** (6.4 KB)  
   Both filter triggers (Hashtag and Phòng ban) closed, no menu visible.

2. **`hashtag-filter-open-unselected.png`** (34 KB)  
   Menu open, nothing selected. Shows 6 visible rows:
   - Toàn diện
   - Giỏi chuyên môn
   - Hiệu suất cao
   - Truyền cảm hứng
   - Công hiến
   - Aim High
   
   Geometry assertions passed:
   - Listbox bounding box height: **348px** (exact match to spec)
   - First row bounding box height: **56px** (exact match to spec)

3. **`hashtag-filter-open-selected-scrolled.png`** (34 KB)  
   Menu open with Wasshoi (position 8, below initial fold) selected and scrolled into view.
   Shows lower portion of list:
   - Công hiến (position 5)
   - Aim High (position 6)
   - Be Agile (position 7)
   - **Wasshoi (position 8) — selected with glow** ✓
   - Hương mục tiêu (position 9)
   - Hướng khách hàng (position 10)
   - Chuẩn quy trình (position 13, partial)

### Visual Comparison vs. MoMorph Frame (JWpsISMAaM)

**Closed state:**
- ✓ Both filter triggers present, styled with border, dark background
- ✓ Positioning matches frame

**Open unselected state:**
- ✓ Listbox bounded to 348px height (6 rows × 56px + padding)
- ✓ Dark background (#00070C) matches
- ✓ 1px border (#998C5F) matches
- ✓ 8px border radius matches
- ✓ Labels centered, bold, white text
- ✓ 6px container padding, 4px option padding
- ✓ Hover state: `rgba(255,234,158,0.05)` light background (not visible in unselected shot but confirmed by styling)

**Open selected state:**
- ✓ Selected row (Wasshoi) shows raised background `rgba(255,234,158,0.10)`
- ✓ Text-shadow glow matching spec: `rgb(250, 226, 135)` (= `#FAE287`)
- ✓ All 13 options remain mounted and accessible via scroll (position 8 is reachable)
- ✓ Scrolling works: menu scrolls down to show Wasshoi without cutting options
- ✓ Scroll position persists after selection + reopen + scroll to selected item

### No Material Mismatches

All visual elements match the frame specification:
- Dimensions correct (348px height, 56px rows, 6 visible per viewport)
- Colors and styling correct (borders, backgrounds, glows, hover/focus states)
- Typography correct (centered, bold, white, proper tracking)
- Spacing correct (padding, no gap between rows)
- Functionality proven (scrolling works, all 13 options mounted and accessible)

## Code Changes Verified

**Phase 02 changes confirmed:**
1. ✓ Removed `scrollable` prop from `KudosFilterMenu` signature and type definition
2. ✓ Moved `max-h-[348px] overflow-y-auto` from conditional (ternary) into base className
3. ✓ Added `focus-visible:[text-shadow:0_0_6px_#FAE287]` to base option className
4. ✓ Removed `scrollable` attribute from department menu call in `kudos-filter-bar.tsx`
5. ✓ Department menu still rendered byte-identical (same class set, just not conditional)

## Test Files Created/Modified

**New files:**
- `e2e/capture-hashtag-filter-visual.spec.ts` — captures three visual states
- `plans/260911-1546-dropdown-hashtag-filter/evidence/hashtag-filter-*.png` — three screenshots
- `plans/260911-1546-dropdown-hashtag-filter/evidence/temper-results.json` — command exit codes

**Modified files:**
- `playwright.config.ts` — added `hashtag-filter-visual-capture` project (no dependencies, public route, 1440px Desktop Chrome)

**Unchanged (off-limits):**
- `e2e/kudos-live-board.spec.ts` — read-only, RED assertions locked in from phase 01
- `e2e/fixtures/kudos-constants.ts` — read-only

## Acceptance Criteria Met

All FR-214..FR-219 acceptance criteria demonstrated:

| FR | Criteria | Evidence |
|----|----------|----------|
| FR-214 | Listbox bounded to max-height 348px with overflow-y-auto scrolling | K-31, screenshot geometry assertions |
| FR-215 | Keyboard-focused option shows glow with #FAE287 text-shadow | K-32, focus assertion on keyboard Tab |
| FR-216 | Clicking an option closes the menu and filters both board sections | K-33 |
| FR-217 | Selection persists on menu reopen (`aria-selected` + glow) | K-34 |
| FR-218 | Re-clicking the selected option clears the filter and restores the full board | K-35 |
| FR-219 | 13 options in `public.hashtags` position order, all mounted inside the bounded box | K-3 (names/order) + K-31 (all 13 mounted) |

## Summary Metrics

| Metric | Value |
|--------|-------|
| Tests run (targeted) | 6 |
| Tests passed (targeted) | 6 (100%) |
| Tests run (full file) | 35 |
| Tests passed (full file) | 35 (100%) |
| Regression tripwires | K-3, K-8, K-26..K-30 — all passed ✓ |
| Lint errors | 0 |
| Type errors | 0 |
| Visual captures | 3/3 ✓ |
| File line count compliance | 59 lines, 112 lines (both < 200) ✓ |
| Time to run full suite | ~1.6m |

## Status

**Status:** DONE

**Summary:** Phase 03 complete. Hashtag filter listbox passes all five RED→GREEN tests, full regression passes with department tripwire intact, code quality clean, visual evidence shows 348px scrollable box with correct styling and glow, and no material mismatches against frame spec.

**Concerns:** None. All assertions lock in place, no weakening required.

---

**Evidence artifacts:**
- Test exit codes: `evidence/temper-results.json`
- Visual evidence: `evidence/hashtag-filter-{closed,open-unselected,open-selected-scrolled}.png`
- Test file: `e2e/capture-hashtag-filter-visual.spec.ts`
- Playwright config: `playwright.config.ts` (hashtag-filter-visual-capture project)
