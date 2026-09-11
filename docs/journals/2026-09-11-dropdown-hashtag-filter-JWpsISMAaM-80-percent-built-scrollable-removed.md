# JWpsISMAaM Dropdown Hashtag Filter — 80% already built, `scrollable` prop removed, focus glow added

**Date**: 2026-09-11 (session 2026-09-11 15:46 → 2026-09-11 16:55 +07)
**Severity**: medium
**Component**: `app/kudos/`, `e2e/kudos-live-board.spec.ts` (tests K-31 through K-35), `kudos-filter-menu.tsx`, `kudos-filter-bar.tsx`
**Status**: resolved

## What Happened

Delivered JWpsISMAaM Dropdown Hashtag Filter — MoMorph frame opens a 348px listbox of hashtags on `/kudos`, clicking an option filters the board to that hashtag, clicking the same option again clears the filter. Test policy `e2e-red-first`, work plan under `plans/260911-1546-dropdown-hashtag-filter/`. Final gates: RED to GREEN on the byte-identical command (exit 1 → exit 0, 5 tests + setup = 6/6), full suite 35/35 (including K-27 department regression guard), typecheck clean, lint 0 errors (clean), reviewer score 8/10 with zero critical findings. The headline discovery: **the frame looked unbuilt, but the code was already 80% there.** The same click-select-close-reclick-clear pattern that powered the department filter was already working for hashtags in `kudos-board.tsx`. The real deliverable was not a component — it was tests (five new ones, K-31 through K-35) plus two CSS class changes: removing a dead `scrollable` prop that made the listbox render 742px instead of 348px, and adding focus-state glow that was present on hover but missing on keyboard navigation.

## The Brutal Truth

This is genuinely maddening to log, because I almost wasted an hour building a dropdown from scratch when the dropdown was already there. The frame says "Dropdown Hashtag Filter" — all caps, looks like a whole component. I opened the code, ready to build. Then I read `kudos-board.tsx` and realized the state management, the filter application, the clear-on-reclick logic — all of it was live and untested, exactly like the department filter from earlier that day. The test suite K-31 through K-35 are the first proof that this code path actually works for hashtags, not just departments. We shipped a feature, took it for granted, and moved on. The real work was not building it; it was admitting we had never tested it.

The sting is that two agents lost time chasing ghosts in the evidence gate during delivery. The schema is strict (extra keys rejected, `temper-results.json` must be an object `{"commands":[...]}` whose every entry carries its own `status` field, not a bare array, `acceptanceCovered` entries must echo the acceptance criteria verbatim, `disposition` is a three-value enum not free text), and guessing the shape cost both of them. One of them eventually copied the structure from the phòng-ban evidence that had already passed the gate and the seal went through. The gate is doing its job — it is strict and it is strict for good reason — but the lesson is worth writing down: the first time through, copy the shape from an already-sealed sibling plan. Do not invent.

And the orphaned dev server was a knife twist. Typecheck kept failing with phantom errors in `.next/dev/types` (generated file, impossible to edit by hand). I killed a 5.6-hour-old `next dev` process that was pinned on v16.2.11 (project is on 16.3.4), removed `.next/dev/types`, and typecheck went green immediately. Two agents had eaten that error. A stale dev server rewrites the generated type files with broken syntax, and because they are generated, the linter will not touch them. The next person to see a phantom typecheck error should check `npm ls next` and `ps aux | grep "next dev"` before chasing the code.

## Technical Details

### 1. The hashtag filter was already shipping, untested

**The page:** `/kudos` has a "Hashtag" filter button in the toolbar (distinct from the department button added earlier).

**What was already live in `kudos-board.tsx`:**
```tsx
const [selectedHashtag, setSelectedHashtag] = useState<string | null>(null);

const handleHashtagSelect = (hashtag: string) => {
  if (selectedHashtag === hashtag) {
    setSelectedHashtag(null); // Click again to clear
  } else {
    setSelectedHashtag(hashtag);
  }
};

// Filter is applied when fetching kudos
const filteredKudos = kudos.filter(k => 
  !selectedHashtag || k.hashtags.includes(selectedHashtag)
);
```

**What was missing:** Not a single test. No assertion that clicking a hashtag filters the board, no proof that clicking again clears it. K-31 through K-35 exist to fix this. (K-27 for departments had already established that per-card assertions are the only reliable proof.)

### 2. Two CSS gaps (the actual implementation work)

**Gap 1: Listbox rendered 742px instead of 348px**
- Frame spec: 348px max-height scrollable container
- Shipped code: `kudos-filter-bar.tsx` passed `scrollable={true}` only to the department branch
- Result: Hashtag listbox rendered without the `scrollable` prop, so the 13 hashtags (each 56px) stacked without constraint: 13 × 56px + padding = 742px tall, spilling past the viewport
- Fix: Removed the dead `scrollable` prop entirely. Both branches need it; a conditional was always going to rot. Changed the component to always pass the box height, removed the prop gate.
- Test K-33 asserts exact height: `expect(height).toBe(348)`

**Code before:**
```tsx
{/* kudos-filter-bar.tsx */}
{filterType === 'department' && (
  <KudosFilterMenu
    items={departments}
    scrollable={true}  {/* dead condition — hashtag branch never got this */}
    onSelect={handleDepartmentSelect}
  />
)}
{filterType === 'hashtag' && (
  <KudosFilterMenu
    items={hashtags}
    {/* scrollable never passed — 13 rows × 56px = 742px */}
    onSelect={handleHashtagSelect}
  />
)}
```

Code after:
```tsx
{/* Both branches now */}
<KudosFilterMenu
  items={filterType === 'department' ? departments : hashtags}
  onSelect={filterType === 'department' ? handleDepartmentSelect : handleHashtagSelect}
/>
```

And `kudos-filter-menu.tsx`:
```tsx
// Always apply max-height; removed the scrollable prop gate
const container = `
  flex flex-col max-h-[348px] overflow-y-auto
  ...
`;
```

**Gap 2: No glow on focus (keyboard navigation)**
- Frame spec: Item A.1 calls for a glow on hover **and** on focus
- Shipped code: `focus-visible:text-shadow` was missing; only hover had the glow
- Problem: Keyboard users (Tab into the listbox, arrow keys to navigate) never got visual feedback on focus — the glow only appeared on mouse hover
- Fix: Added `focus-visible:[text-shadow:0_0_6px_#FAE287]` reusing the token from the selected state
- Test K-34 verifies the glow by tabbing into the menu, pressing Down to reach an item, and capturing `getComputedStyle().textShadow`

Code:
```tsx
{/* kudos-filter-menu.tsx */}
<li
  role="option"
  className={`
    p-4 cursor-pointer transition-colors
    hover:[text-shadow:0_0_6px_#FAE287]
    focus-visible:[text-shadow:0_0_6px_#FAE287]  {/* added */}
    ${selected ? 'bg-[#FFEA9E] font-semibold' : ''}
  `}
  onKeyDown={handleKeyNavigation}
>
  {item.label}
</li>
```

### 3. Five tests (K-31 through K-35)

**K-32 — "Hashtag option renders with pointer cursor"**
- Locates one hashtag row in the open listbox
- Asserts `cursor: pointer` on the rendered option
- Passes 6/6 scoped (5 tests + setup), 35/35 full-suite

**K-33 — "Listbox max-height is exactly 348px"**
- Opens listbox, measures the scroll container bounding box
- Asserts `height === 348` (exact, not `<=`, not `>= 340`)
- Same math as K-27: six rows of 56px each (p-4 + text-base + leading-6, no gap between rows), container adds 6px padding
- Fails immediately if width changes without intent

**K-34 — "Focus glow appears on keyboard navigation"**
- Tabs into the listbox, presses Down arrow to navigate to the third item
- Captures computed `text-shadow` via `getComputedStyle()`
- Asserts the glow token is present: `0 0 6px rgb(250, 226, 135)`
- Uses `toHaveCSS()` to retry through any transition delay (learned from the phòng-ban session)

**K-35 — "Clicking a hashtag filters the board"**
- Opens listbox, selects the `#Wasshoi` hashtag (position 8, requires scrolling the box)
- Asserts `every visible card.hashtags includes 'Wasshoi'`
- Confirms at least one card present (filter is actually running)
- Exact same pattern as K-28 (department filter), transferred directly

### 4. Failed attempt: tautological assertion trap

The first draft of K-34 looked like this:
```typescript
// WRONG — would never fail:
const bgStyle = getComputedStyle(focusedItem).textShadow;
expect(bgStyle).not.toBe("rgb(255, 234, 158, 0.1)");
```

Reason: `getComputedStyle().textShadow` serializes to a string like `"0px 0px 6px rgb(250, 226, 135)"` or `"none"`, never `"rgb(..., 0.1)"` with an alpha channel in the 4-value form. The assertion was mathematically impossible to fail — no value of `text-shadow` would ever produce that string. Caught in reviewer pre-commit.

Fixed to a positive assertion:
```typescript
// RIGHT
const bgStyle = getComputedStyle(focusedItem).textShadow;
expect(bgStyle).toContain("rgb(250, 226, 135)");
```

Lesson: **A negative assertion against an impossible value is not a test.** Prefer asserting the value you expect. If you find yourself writing `expect(...).not.toBe(badValue)`, stop and ask: "Is there any circumstance under which badValue would actually occur?" If the answer is no, the test is broken.

### 5. Failed attempt: one-shot style read caught transition mid-fire

The first RED run used:
```typescript
// WRONG — caught mid-transition
page.locator('[role=option]').nth(2).focus();
const bgStyle = getComputedStyle(page.locator('[role=option]').nth(2)).textShadow;
expect(bgStyle).toContain("rgb(250, 226, 135)");
```

The component has `transition-colors duration-200`, so the glow does not appear instantly. The `.focus()` call changes focus, the next line reads the computed style, and it catches the `text-shadow` mid-transition (or hasn't started yet). The value is `"none"` or partially-computed.

Fixed by switching to `toHaveCSS()` which retries:
```typescript
// RIGHT — toHaveCSS() retries through the transition
await expect(page.locator('[role=option]').nth(2)).toHaveCSS(
  'text-shadow',
  /rgb\(250, 226, 135\)/
);
```

Lesson: **`transition-colors` breaks one-shot style reads.** If the component has a transition on any CSS property being tested, use `toHaveCSS()` or a similar retry matcher. It will poll the property until it stabilizes or timeout, so transitioned values are captured correctly.

### 6. Focus-visible does not match Playwright `locator.focus()`

Blueprint surfaced this early: In Chromium, `locator.focus()` programmatically focuses an element, but `:focus-visible` (CSS pseudo-class for "keyboard-navigated focus") does not match because the focus arrived by script, not keyboard. Learned from prior sessions but worth repeating: to test `focus-visible`, focus must arrive by keyboard. The test uses `page.keyboard.press('Tab')` to navigate into the listbox, then `press('ArrowDown')` to reach an item, so `:focus-visible` applies.

### 7. Text-shadow is not a sufficient focus indicator alone

The glow passes WCAG 2.1 AA (contrast and size) only because the native outline was never suppressed. If a future change adds `focus-visible:outline-none`, the glow alone becomes too subtle. A comment now pins this in `kudos-filter-menu.tsx`:

```tsx
{/* WCAG note: text-shadow glow is sufficient focus indicator ONLY because
    the native outline remains visible. Never add outline-none to :focus-visible
    without adding a second strong indicator (outline, border, or background shift).
    See WCAG 2.1 Success Criterion 2.4.7. */}
```

No test would catch an outline-suppression regression, so this is a code comment, not a test assertion.

### 8. Orphaned dev server rewrites generated types with broken syntax

During the evidence gate seal, `npm run typecheck` kept reporting errors in `.next/dev/types/` (auto-generated file, owned by Next.js). The errors were phantom — the source was clean. Root cause: a stale `next dev` process (5.6 hours old, pinned on v16.2.11 instead of the project's v16.3.4) was rewriting the generated type files with broken output. Killing the process and clearing `.next/` fixed it.

Command that solved it:
```bash
pkill -f "next dev"
rm -rf .next/
npm run typecheck  # now passes
```

Lesson: If `npm run typecheck` reports errors only in `.next/dev/` or `.next/types/` and the source is clean, check for a stale dev server. Run `npm ls next` to confirm versions, `ps aux | grep "next dev"` to list running processes, and kill the old one. Do not spend time chasing generated files.

### 9. Evidence gate schema is strict and worth knowing upfront

The seal step rejected the first attempt because:
- Extra keys in `study-context.json` (added debug fields that were not in the template)
- `temper-results.json` was a bare array `[{command: "...", exitCode: 0, ...}]` instead of `{"commands": [...], "status": [...]}`
- `acceptanceCovered` entries did not echo the acceptance-criterion text verbatim (paraphrased instead)
- `disposition` field was free text instead of the enum `Accept|Reject|Defer`

Solution: Copy the folder structure from the already-sealed phòng-ban evidence. The gate is a schema validator, not a human reader. The exact shape matters. Faster than re-reading the gate protocol for the tenth time.

## What We Tried

1. **Assumed the frame needed a full implementation.** Opened with "build a hashtag dropdown component," then read the code and found it was already there. Frame work became "add tests and fix two CSS gaps," not "write a new component."

2. **Wrote tests with negative assertions against impossible values (K-34 first draft).** The tautological `expect(...).not.toBe("rgb(255, 234, 158, 0.1)")` would never fail because `getComputedStyle().textShadow` never serializes to that format. Caught in reviewer pre-commit. Switched to positive assertion: `toContain("rgb(250, 226, 135)")`.

3. **Used one-shot `getComputedStyle()` after `.focus()` for a transitioned property (K-34 second draft).** The component has `transition-colors duration-200`, so the glow was mid-transition or not yet applied when the read happened. Flipped to `toHaveCSS()` which retries and waits for the transition to settle.

4. **Tried to test `:focus-visible` with `locator.focus()` (blueprint early catch).** Chromium does not match `:focus-visible` when focus arrives programmatically; only keyboard navigation triggers it. The test uses `page.keyboard.press('Tab')` and `press('ArrowDown')` instead. Note for the next person: if you see `:focus-visible` in the spec, focus must be keyboard-driven.

5. **Hit phantom typecheck errors in `.next/dev/types/`.** Spent an hour thinking the code was broken, then discovered a 5.6-hour-old `next dev` process running v16.2.11 was rewriting the generated files. Killed it, cleared `.next/`, and typecheck passed. Two agents chased this same ghost because the symptom pointed at the wrong place.

6. **Failed the evidence gate seal on the first try over schema violations.** Added extra debug keys to `study-context.json`, wrapped the array wrong in `temper-results.json`, paraphrased acceptance criteria instead of echoing them verbatim, and used free text for `disposition` instead of the enum. Copied the exact structure from the already-sealed phòng-ban evidence folder and the seal went through. The gate is strict; learn the schema from a passed sibling, not from re-reading the spec.

## Root Cause Analysis

1. **A frame marked "build this" does not mean "build from zero."** The hashtag filter was already live. The frame showed the UX, not the implementation status. The code review step (reading `kudos-board.tsx` for existing filter patterns) was what surfaced it. If the study phase had skipped code-reading and jumped to "start building," we would have spent two hours on a duplicate implementation. Lesson: search the codebase for existing patterns before designing the component from the frame.

2. **A conditional that exists only in one branch will rot.** The `scrollable={true}` prop was passed only to the department dropdown, so the hashtag branch never received it. Instead of a default (which would have been wrong — a prop with no universal default should not exist), the component should always apply the box height. A prop that is conditional on a sibling feature is a maintenance hazard. Lesson: if two branches need the same behavior, bake it into the component, not the caller.

3. **Negative assertions against impossible values are not tests.** A test that says `expect(val).not.toBe(impossible_value)` will always pass, so it is not testing anything. Prefer positive assertions on the value you expect. If the design allows a range (e.g., "at least 100px"), then `>= 100` makes sense. But "must have this glow" means assert the glow is present, not assert the glow is not absent.

4. **Transitioned properties must be read with retry matchers, not one-shot snapshots.** A `transition-colors duration-200` means the value changes gradually over 200ms. A single `getComputedStyle()` read will catch it mid-transition (or before it starts). Use `toHaveCSS()` or a similar retry mechanism to poll until the value stabilizes.

5. **`:focus-visible` does not match programmatic focus in Chromium.** The CSS pseudo-class only matches keyboard navigation. If the test uses `locator.focus()`, it will not trigger `:focus-visible`. Use keyboard events instead: `page.keyboard.press('Tab')` to navigate and `press('ArrowDown')` to move within the listbox.

6. **Generated files rewritten by stale dev servers are a phantom error source.** A `next dev` process pinned on an old version can rewrite `.next/dev/` with broken syntax. The typecheck error appears to be in the source, but it is actually in the auto-generated output. Kill stale processes and clear the build directory before chasing the code.

7. **The evidence gate schema is strict and is worth copying, not re-inventing.** The seal protocol enforces exact field names, specific data structures (arrays wrapped in objects, enums for disposition), and verbatim text matching for acceptance criteria. Learning the schema from an already-passed sibling is faster than reading the spec. The gate is a validator; copy the shape from what has already passed.

## Lessons Learned

1. **A frame that looks unbuilt can be 80% built already.** The hashtag dropdown was live in production, untested, and buried in the same state-management code as the department filter. The frame showed the UX and implied "build this," but the code was already there. Read the codebase before planning the implementation. If a feature has no tests, it is flying blind — that is the first place to look.

2. **A negative assertion against an impossible value is worse than no assertion.** It will always pass and gives false confidence. If you find yourself writing `expect(value).not.toBe(impossible)`, stop and ask: could this value ever occur? If not, assert the value you expect instead. Replace `expect(...).not.toBe(x)` with `expect(...).toBe(y)` where `y` is the correct value.

3. **Transitioned properties need retry matchers (`toHaveCSS`), not one-shot reads.** Any CSS property with `transition-*` applied will be mid-transition when a single `getComputedStyle()` reads it. Use `toHaveCSS()` or a polling assertion to capture the stable value. This is especially important for focus states, which are often transitioned.

4. **`:focus-visible` is keyboard-only in Chromium.** Programmatic `.focus()` does not trigger it. To test `:focus-visible`, navigate by keyboard. Use `page.keyboard.press('Tab')` to focus an element, then `press('ArrowDown')` to navigate within a list. The CSS pseudo-class will only match keyboard-driven focus.

5. **Text-shadow alone is not a sufficient focus indicator; keep the outline.** A glow passes WCAG only if the native outline is not suppressed. Document this with a code comment so a future change does not accidentally remove the outline and break accessibility.

6. **A stale dev server rewriting generated files is a silent corruption vector.** If `.next/dev/` errors appear in typecheck but source is clean, check for a running `next dev` process pinned on an old version. Kill it and clear `.next/` before chasing the code. The symptom is phantom errors in auto-generated files; the root cause is version mismatch.

7. **The evidence gate enforces a strict schema; copy it from a passed sibling, not from the spec.** The seal step validates exact field names, nested object structures, enum values for fields like `disposition`, and verbatim acceptance-criterion text. Learning this by trial-and-error costs time. Copy the `evidence/` folder structure from an already-sealed phase (e.g., phòng-ban) and adapt it. The gate is a validator, and the schema is precise.

8. **A prop that is conditional on a sibling feature will rot.** The `scrollable={true}` prop was supposed to be department-only, but when the hashtag branch arrived, no one passed it, and the box spilled to 742px. If two branches need the same behavior, do not gate it on a prop. Bake it into the component. Reserve props for genuinely divergent behavior.

## Next Steps

### Completed
- [x] Read `kudos-board.tsx` and confirm the hashtag filter was already shipping (click-select-clear-reclick logic identical to department filter).
- [x] Identify two gaps: 348px box never passed to hashtag branch (742px render), focus glow missing on keyboard navigation.
- [x] Write K-31 through K-35 tests per frame spec and prior department-filter tests.
- [x] Run RED exit 1 (K-33 and K-34 failed: 742px box, no text-shadow on focus).
- [x] Remove `scrollable` prop gate; apply max-h-[348px] unconditionally in `kudos-filter-menu.tsx`.
- [x] Add `focus-visible:[text-shadow:0_0_6px_#FAE287]` to option element.
- [x] Run GREEN exit 0, 6/6 scoped (5 tests + setup), byte-identical command.
- [x] Run full-file 35/35 (K-27 department regression guard confirmed passing, no new breakage).
- [x] Add code comment protecting the outline: "WCAG note: text-shadow glow is sufficient focus indicator ONLY because native outline remains visible."
- [x] Kill stale `next dev` process (v16.2.11), clear `.next/`, re-run typecheck (clean).
- [x] Lint: 0 errors. Exit 0.
- [x] Typecheck: clean. Exit 0.
- [x] Reviewer: 8/10, zero critical, zero high. Two minor (focus glow WCAG comment added, fixed in-session).
- [x] Evidence gate: seal attempt 1 failed (schema violations); copied structure from phòng-ban evidence folder; seal attempt 2 SEALED (hard).
- [x] Visual evidence: three captures (closed listbox, selected #Wasshoi row, glow on focus via keyboard Tab).
- [x] Commit K-31 through K-35 tests with feature changes (25d8f7f, c4bf487).

### Pending user decision
- [ ] Push to origin (awaiting user instruction).
- [ ] Open pull request against `main` (deferred until push is approved).

### Documentation
- [x] Log this entry (you are reading it).

---

**Status**: DONE
**Summary**: Delivered JWpsISMAaM Dropdown Hashtag Filter. Discovered the feature was already 80% built and shipping without tests. Wrote five tests — two genuine REDs plus three regression guards (K-31 through K-35) to lock down existing behavior. Fixed two CSS gaps: removed dead `scrollable` prop gate (which made hashtag box render 742px instead of 348px), added `focus-visible` glow that was missing on keyboard navigation. Caught two failed test approaches (tautological negative assertion, one-shot read of a transitioned property) and fixed both before commit. Killed a stale dev server that was corrupting generated types. Evidence gate seal required learning strict schema; copied structure from phòng-ban sibling. All gates passed: RED to GREEN, 35/35 full suite, lint 0, typecheck clean, reviewer 8/10. Two commits staged on feature branch.
**Concerns/Blockers**: None. Schema learning for evidence gate cost iteration; mitigated by copying from sealed sibling. Stale dev server cost two agents time; documented the diagnosis for next occurrence.
