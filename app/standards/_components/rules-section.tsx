import type { ReactNode } from "react";

import type { RulesSectionView } from "@/lib/rules/view-model";

/**
 * Heading treatment, the only two the frame publishes (FR-202):
 *
 * - `md` — 22/28, `letter-spacing: 0` (`mm:3204:6132`, `mm:3204:6077`)
 * - `lg` — 24/32, `letter-spacing: 0` (`mm:3204:6090`, "KUDOS QUỐC DÂN")
 *
 * Two named variants rather than a free `className` prop: the frame has
 * exactly these two sizes, so closing the set here is what stops a fourth
 * size arriving from taste instead of from the design.
 */
const HEADING_CLASS = {
  md: "text-[22px] leading-7",
  lg: "text-2xl leading-8",
} as const;

/**
 * Body treatment — 16/24/700, `letter-spacing: 0.5px`, justified, white
 * (`mm:3204:6133`, `mm:3204:6078`, `mm:3204:6089`, `mm:3204:6091`). Identical
 * to the paragraph class already used in `award-detail-card.tsx`; the two
 * frames really do share this text style, so the string is repeated rather
 * than a shared export invented across screen boundaries.
 */
const BODY_CLASS = "text-justify text-base leading-6 font-bold tracking-[0.5px] text-white";

interface RulesSectionProps {
  section: RulesSectionView;
  /** `lg` = 24/32 for "KUDOS QUỐC DÂN" (`mm:3204:6090`); `md` = 22/28 for the other two. */
  headingSize?: "md" | "lg";
  /**
   * The list wedged between `body` and `closingBody` — section 1 receives the
   * Hero tier list, section 2 the collectible-icon grid (both phase 06).
   * Sections without a list pass nothing.
   */
  children?: ReactNode;
}

/**
 * One prose section of the Thể lệ panel (SCR007, screen `b1Filzi9i6`).
 *
 * Source nodes, one per rendered instance:
 *
 * | # | container | heading | body | closing |
 * |---|-----------|---------|------|---------|
 * | 1 | `3204:6131` | `3204:6132` | `3204:6133` | — |
 * | 2 | flat in `3204:6076` | `3204:6077` | `3204:6078` | `3204:6089` |
 * | 3 | flat in `3204:6076` | `3204:6090` | `3204:6091` | — |
 *
 * Sections 2 and 3 are not wrapped in their own Figma frames — their text
 * nodes sit as direct children of `3204:6076` beside section 1's frame. That
 * is a layering accident, not a structural difference: every gap in that
 * column measures 16px, section 1's inner gaps included, so rendering all
 * three as `<section class="gap-4">` inside a `gap-4` column reproduces the
 * frame exactly while giving the suite the three `rules-section` elements the
 * test contract fixes.
 *
 * `closingBody` renders AFTER `children`, not after `body`: on section 2 the
 * line "Những Sunner thu thập trọn bộ 6 icon…" (`3204:6089`) sits below the
 * icon grid (`3204:6079`), so a component that emitted body → closing → grid
 * would put it in the wrong place. It is `null` on the other two sections and
 * then emits no element at all, rather than an empty paragraph.
 *
 * A Server Component, deliberately — nothing here reacts to anything. The
 * screen's only client boundary is `rules-panel-dismiss.tsx`.
 *
 * The heading is an `<h2>`. `<h1>` belongs to the panel title (FR-201,
 * phase 07); a second `<h1>` on the page would break the suite's
 * `getByRole("heading", { level: 1 })`.
 *
 * Every string comes from `RulesSectionView`, i.e. from `rule_sections`
 * (BR-002). No rules copy is written into this file.
 */
export function RulesSection({ section, headingSize = "md", children }: RulesSectionProps) {
  return (
    // mm:3204:6131 — flex column, gap 16px, 473px wide inside the drawer's
    // 40px gutters. `w-full` rather than `w-[473px]`: below the 553px frame
    // the drawer goes full-bleed (clarifications § Layout), and a fixed width
    // would overflow the viewport there.
    <section data-testid="rules-section" className="flex w-full flex-col items-start gap-4">
      {/* mm:3204:6132 */}
      <h2 className={`${HEADING_CLASS[headingSize]} font-bold text-[#FFEA9E]`}>
        {section.heading}
      </h2>
      {/* mm:3204:6133 */}
      <p className={BODY_CLASS}>{section.body}</p>
      {children}
      {/* mm:3204:6089 — section 2 only; below the grid, never above it. */}
      {section.closingBody ? <p className={BODY_CLASS}>{section.closingBody}</p> : null}
    </section>
  );
}
