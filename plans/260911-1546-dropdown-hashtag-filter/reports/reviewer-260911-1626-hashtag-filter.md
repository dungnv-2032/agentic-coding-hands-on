# Review — Dropdown Hashtag filter (feat/dropdown-hashtag-filter)

**reviewer · 260911-1626** · Status: **DONE**

## Scope

- Files reviewed:
  - `app/kudos/_components/kudos-filter-menu.tsx`, `app/kudos/_components/kudos-filter-bar.tsx` (uncommitted)
  - `e2e/kudos-live-board.spec.ts`, `e2e/fixtures/kudos-constants.ts` (committed `25d8f7f`)
  - `e2e/capture-hashtag-filter-visual.spec.ts` (untracked), `playwright.config.ts` (uncommitted)
  - `docs/features/F004_KudosLiveBoard/functional-spec.md`, `technical-spec.md` (uncommitted)
- Lines: ~210 (e2e additions) + ~30 net (UI diff) + ~20 (docs) + 7 (playwright.config) + 91 (new capture spec)
- Depth: full — `git diff main...HEAD` plus working-tree diff, read against plan.md, both phase files, spec-delta.md, clarifications.md, study-context.json, and both tester reports.

## Assessment

Small, disciplined change that does exactly what its plan says and nothing more. The `scrollable` prop removal is a clean gate deletion — the department branch's class set is verified byte-identical (confirmed by reading the diff hunk directly: the two classes move out of a ternary into the base string, nothing else changes), and K-27 stayed green in the reported full-file run. The focus glow reuses the frozen `#FAE287` token exactly as clarified, placed on the shared base className so it applies uniformly. `fetchFilterOptions()`/`matchesFilters()` and everything outside the five declared touchpoints are untouched (verified via `git diff` against `lib/` and `kudos-board.tsx` — empty). Both touched components stay well under the 200-line rule (59 / 112 lines). Typecheck is clean as of this review. e2e-red-first was honored honestly: the RED report shows two real failures (742px vs 348px, `text-shadow: none`) and three tests that already passed as regression guards, matching the plan's own prediction — this is not a manufactured RED.

Two things did not fully land: one assertion in the new K-32 test is unintentionally tautological, and the docs promote only reached half of what phase 03 asked for. Neither is a functional defect in the shipped UI — the feature itself is correct and evidenced.

## Critical

None.

## Warning

1. **`e2e/kudos-live-board.spec.ts:911`** — K-32's hover-state half is dead weight.
   ```
   expect(bgStyle).not.toBe("rgb(255, 234, 158, 0.1)"); // not selected dark
   ```
   `getComputedStyle` never serializes an alpha<1 color as `rgb(r, g, b, a)` — a color with alpha gets `rgba(...)`. The literal string on the right is not a value any browser can produce, so this assertion is unconditionally true regardless of what `backgroundColor` actually is. It provides zero protection for the claim in the comment above it ("Confirm hover state is unchanged"). Worth noting too: even with the typo fixed, the check is close to structurally guaranteed already — `firstOption` is never the selected option in this test, so the ternary in `kudos-filter-menu.tsx` can't produce the selected background here regardless of what phase 02 did to the focus branch.
   **Fix:** either assert the real computed value for the unfocused/default branch (`rgba(0, 0, 0, 0)` for the no-hover-no-select state, matching what the base button actually renders), or drop this half of K-32 — it doesn't currently verify anything the diff could break.

2. **`docs/screens/SCR004_KudosLiveBoard/spec.md:74`** — docs promote is half-done.
   Phase 03's own "Next steps" (`plans/260911-1546-dropdown-hashtag-filter/phase-03-green-and-visual-evidence.md:122`) says to promote FR-214..FR-219 into **both** `docs/features/F004_KudosLiveBoard/` and `docs/screens/SCR004_KudosLiveBoard/`. Only the features docs (`functional-spec.md`, `technical-spec.md`) were updated — faithfully, nothing renumbered or removed, FR-214..219/BR-214..216 land in the right tables. The screen spec's UI-states row at line 74 still reads:
   > "khối Phòng ban cuộn trong hộp cao tối đa 348px (6 dòng), không đẩy layout trang"

   That's now stale: the 348px scroll box is the shared default for **both** listboxes post-diff (FR-214), and this row says nothing about the hashtag side or the new `focus-visible` glow (FR-215) at all.
   **Fix:** update that row to describe both `filter-menu-hashtag` and `filter-menu-department` under the shared 348px/6-row behavior, and add a mention of the keyboard-focus glow.

## Suggestion

1. **`app/kudos/_components/kudos-filter-menu.tsx:47`** — the glow is additive to the browser's native `:focus-visible` outline, not a replacement for it. I checked: no `outline-none` appears anywhere in this component, `kudos-filter-bar.tsx`, or `app/globals.css`, and Tailwind's preflight import doesn't touch focus outlines. So today's WCAG 2.1 AA story (2.4.7 Focus Visible, 1.4.11 Non-text Contrast) is actually satisfied by the *native* outline, with the text-shadow as the on-brand enhancement the frame asked for — a `text-shadow` alone would not reliably clear the 3:1 non-text-contrast bar by itself, especially against the varying backgrounds behind an absolutely-positioned dropdown. Nothing in the suite pins this combination down, so a later pass that adds `focus-visible:outline-none` (a common instinct when someone notices the "double ring") would quietly break keyboard accessibility with no red test. Given the project's standing rule against inventing new visual tokens, I'm not suggesting a new focus treatment — just recommend a test or a code comment asserting the native outline must stay.

2. **`plans/260911-1546-dropdown-hashtag-filter/plan.md:28-32,75-79`** — phase status and the "Done when" checklist are still `pending`/unchecked even though valid RED, GREEN, and visual evidence already exist on disk. Tracking hygiene only.

## Interrogated Questions (from the brief)

1. **Old conditional vs. new default — any gap tests wouldn't catch?** No. Only two call sites ever existed (department always passed `scrollable`, hashtag never did); the diff makes both paths converge, and both are covered — K-27 pins department (unchanged), K-31 pins hashtag (newly bounded). `max-h` is confirmed visually inert for lists shorter than 6 rows (phase-02 insight, architecturally sound, not currently exercised since both real lists are ≥6 rows).

2. **Flex-shrink compressing the 56px rows inside the bounded box?** No compression risk found. CSS's "automatic minimum size" (`min-height: auto`) keeps content-sized flex items at their natural height inside a scrolling flex container — that's exactly why this pattern scrolls instead of squeezing. This isn't just theory here: the new capture spec (`e2e/capture-hashtag-filter-visual.spec.ts:69-72`) asserts `rowBox.height === 56` as an **exact** value at runtime, not a screenshot-only claim, and the tester report confirms it passed. The one real edge case — root font-size/text-zoom changing `rem`-based row height while `348px` stays a fixed px value — degrades gracefully (fewer full rows visible before scrolling), not into compression, and doesn't violate WCAG 1.4.4 since content stays reachable via scroll rather than being cut off.

3. **Is `text-shadow` alone sufficient for WCAG 2.1 AA focus visibility?** Not alone — but it isn't alone in this codebase. The native `:focus-visible` outline is never suppressed anywhere the glow applies, so AA is met by the outline with the glow as the frame-mandated visual accent on top. Flagged as a suggestion (not a warning) precisely because nothing currently breaks it, but nothing guards it either — see Suggestion 1.

4. **Brittle/tautological e2e assertions?** One found and reported as Warning 1 above (K-32's hover-background check). K-31, K-33, K-34, K-35 all assert against real, specific, runtime-computed values (exact pixel heights, `scrollHeight > clientHeight`, per-card hashtag-chip membership across both sections, href-set round-trips) — none of those are tautological.

5. **Docs promote fidelity?** Faithful where it landed (functional-spec.md, technical-spec.md: FR-214..219/BR-214..216 added in sequence, nothing renumbered or removed), but incomplete against the phase's own instruction — see Warning 2.

## Done Well

- The `e2e-red-first` discipline was followed for real: the RED report shows genuine failures on computed styles (`742` vs `348`, `text-shadow: none`), not a weakened or staged red.
- The `scrollable` prop removal is a textbook gate deletion — verified byte-identical class output for the unaffected caller, with the regression tripwire (K-27) actually run and passing, not just asserted in prose.
- Geometry claims (`348px`, `56px`) are proven with exact-value runtime assertions in both the behavioral suite and the visual-capture spec, not left to a screenshot's eyeball comparison.
- Scope discipline held: no drive-by touches to `kudos-board.tsx`, `lib/kudos/derive.ts`, or the selection/toggle logic; the diff is confined to presentation plus the one prop removal, exactly as phase 02 specified.

## Actions In Order

1. Fix or remove the tautological background assertion in `e2e/kudos-live-board.spec.ts:911` (Warning 1).
2. Update `docs/screens/SCR004_KudosLiveBoard/spec.md:74` to describe the shared 348px box for both listboxes and mention the focus glow (Warning 2).
3. Optionally, add a regression guard for the native focus outline before this pattern gets "polished" later (Suggestion 1).
4. Reconcile `plan.md`'s phase table and Done-when checklist with the evidence already on disk (Suggestion 2).

## Numbers

- Type coverage: typecheck exit 0 (verified independently via `npx tsc --noEmit`)
- Test coverage: 35/35 `kudos-live-board.spec.ts` (`anon`) per tester GREEN report; not independently re-run in this review, but cross-checked against `evidence/temper-results.json` and both tester reports for consistency
- Lint findings: 0 errors, 31 pre-existing warnings (per tester GREEN report; not independently re-run)

## Still Unresolved

None blocking. See Actions In Order for the two Warning-level cleanups worth doing before merge.

---

**Status:** DONE
**Summary:** No critical or breaking issues. Two Warning-level findings (a tautological e2e assertion, an incomplete docs promote) and two Suggestion-level notes (focus-outline regression guard, plan tracking hygiene). Score 8/10, `criticalCount: 0`, verdict `SEALED`.
**Concerns/Blockers:** None.
