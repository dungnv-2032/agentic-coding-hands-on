import Image from "next/image";
import Link from "next/link";

import type { Dictionary } from "@/lib/i18n/dictionaries";
import type { RulesViewModel } from "@/lib/rules/view-model";

import { RulesCloseButton } from "./rules-panel-dismiss";
import { RulesCollectibleGrid } from "./rules-collectible-grid";
import { RulesHeroTierList } from "./rules-hero-tier-list";
import { RulesSection } from "./rules-section";

/** `rule_sections.position` of the section that owns the Hero tier list (FR-203). */
const HERO_TIER_SECTION = 1;
/** `rule_sections.position` of the section that owns the collectible grid (FR-204). */
const COLLECTIBLE_SECTION = 2;
/** The only section the frame sets in 24/32 rather than 22/28 (`mm:3204:6090`). */
const LARGE_HEADING_SECTION = 3;

interface RulesPanelProps {
  rules: RulesViewModel;
  copy: Dictionary["rules"];
}

/**
 * mm:3204:6052 — the Thể lệ drawer (SCR007, `/standards`, screen `b1Filzi9i6`,
 * frame `3204:6051`). Assembles phases 05 and 06 into the shell the frame draws
 * against the right edge: `3204:6053` is the scrolling content column,
 * `3204:6092` the pinned footer row.
 *
 * ## FR-403 lives in exactly three classes
 *
 * `justify-between` here, `flex-1 overflow-y-auto` on `rules-panel-content`,
 * `shrink-0` on the footer row. That combination is what makes the CONTENT
 * COLUMN the page's only scrollable box — the page itself must not scroll
 * (`FUN_001` measures both). Change any one of the three and the requirement
 * goes with it.
 *
 * ## `children` is assigned by `position`, never by array index
 *
 * `sections[0]` / `sections[1]` would throw the moment `rule_sections` is
 * empty, and an unseeded table is not an error (functional-spec § 9) — the
 * chrome and both footer controls still have to render. Mapping the array and
 * branching on `section.position` degrades to "chrome only" instead of a blank
 * screen.
 *
 * ## Three decisions worth stating rather than rediscovering
 *
 * 1. **The pen is `/images/rules/pen-icon.svg`**, phase 06's asset, which ships
 *    `fill="#00070C"`. The older pen under `public/images/home/` is white and
 *    would be invisible on `#FFEA9E`; it still serves `floating-widget.tsx`,
 *    so it is left where it is rather than recoloured.
 * 2. **`hover:bg-[#F0D98A]`** — "hover darkens it slightly"
 *    (`clarifications.md § GUI_004`). A new literal, deliberately: the shared
 *    `hover:bg-white/10` token lifts a translucent fill and does nothing
 *    visible on a solid gold one, so this is the first solid-gold button in
 *    the app and the first time the value is needed.
 * 3. **No focus trap, no `inert` on the background, and NO `aria-modal`.**
 *    `/standards` is a route, not a modal over another screen; tabbing out to
 *    the header or the footer is correct page behaviour, and trapping focus
 *    would strand a keyboard user on a drawer they reached by URL.
 *
 *    `aria-modal="true"` WAS set here, because the test contract fixed it.
 *    Review found that it made the panel lie to assistive tech: it declares
 *    "nothing outside this dialog exists" while the header and footer stay in
 *    the tab order and stay activatable. Three input modes then disagreed —
 *    the scrim (`z-40`, over a `sticky z-20` header) blocks the mouse, the
 *    keyboard reaches straight through, and a screen reader is told the rest
 *    of the page is absent. A screen-reader user tabbing into content their
 *    own AT just denied existed is a real defect, not a stylistic one.
 *
 *    The attribute was dropped rather than a focus trap built: the no-trap
 *    decision above is deliberate and correct for a route, so the honest fix
 *    is to stop claiming modality this screen does not implement. `role`
 *    stays — the drawer IS a dialog, just not a modal one. The test contract
 *    in `clarifications.md` and FR-201 were amended to match; this is a
 *    recorded contract change, not a silently loosened assertion.
 *
 * `<aside>` rather than `<div>`: complementary content beside the (empty) main
 * region. `role="dialog"` is explicit, so the semantic role is never inferred.
 *
 * The accessible name comes from `aria-labelledby` pointing at the `<h1>`
 * (FR-201), which is the visible title. A `panelAriaLabel` dictionary key was
 * considered and deleted: duplicating the name as an `aria-label` would
 * override the visible one and hand screen readers a second source of truth.
 *
 * A Server Component. The only client boundary on this screen is
 * `rules-panel-dismiss.tsx`, which owns `Đóng`, the scrim and `Escape`.
 */
export function RulesPanel({ rules, copy }: RulesPanelProps) {
  return (
    // mm:3204:6052 — 553px drawer, `padding: 24px 40px 40px`.
    // `w-full max-w-[553px]` (FR-405): below 553px it goes full-bleed rather
    // than off-screen (clarifications § Layout).
    <aside
      data-testid="rules-panel"
      role="dialog"
      aria-labelledby="rules-panel-title"
      className="fixed inset-y-0 right-0 z-50 flex h-svh w-full max-w-[553px] flex-col justify-between bg-[#00070C] px-10 pb-10 pt-6"
    >
      {/* mm:3204:6053 — the one scrollable element on the page (FR-403). */}
      <div
        data-testid="rules-panel-content"
        className="flex flex-1 flex-col gap-6 overflow-y-auto"
      >
        {/* mm:3204:6055 — 45/52, the page's only <h1> (FR-201). */}
        <h1
          id="rules-panel-title"
          className="text-[45px] leading-[52px] font-bold text-[#FFEA9E]"
        >
          {copy.panelTitle}
        </h1>

        {/* mm:3204:6076 — sections 2 and 3 have no wrapper frame of their own;
            their text nodes sit flat beside section 1's frame and every gap in
            the column measures 16px. One `gap-4` column reproduces that. */}
        <div className="flex flex-col gap-4">
          {rules.sections.map((section) => (
            <RulesSection
              key={section.position}
              section={section}
              headingSize={section.position === LARGE_HEADING_SECTION ? "lg" : "md"}
            >
              {section.position === HERO_TIER_SECTION ? (
                <RulesHeroTierList tiers={rules.heroTiers} />
              ) : null}
              {section.position === COLLECTIBLE_SECTION ? (
                <RulesCollectibleGrid icons={rules.collectibleIcons} />
              ) : null}
            </RulesSection>
          ))}
        </div>
      </div>

      {/* mm:3204:6092 — footer row, 16px gap, 56px tall, pinned by `shrink-0`.
          The 24px separation is a MARGIN, not padding: both controls are `h-14`
          themselves, so padding inside a 56px row would squash them. */}
      <div className="mt-6 flex h-14 shrink-0 gap-4">
        {/* mm:3204:6093 */}
        <RulesCloseButton label={copy.closeButton} />
        {/* mm:3204:6094 — a real anchor, not `router.push`: FR-402/BR-005 says
            this screen does not judge auth. `proxy.ts` guards `/kudos/new`, and
            duplicating that rule here would create a second source of truth.
            `flex-1` takes the width `Đóng` leaves. */}
        <Link
          href="/kudos/new"
          data-testid="rules-write-kudos-link"
          className="flex h-14 flex-1 items-center justify-center gap-2 rounded bg-[#FFEA9E] px-4 text-base leading-6 font-bold tracking-[0.5px] text-[#00070C] transition-colors hover:bg-[#F0D98A]"
        >
          <Image src="/images/rules/pen-icon.svg" alt="" aria-hidden width={24} height={24} />
          {copy.writeKudosButton}
        </Link>
      </div>
    </aside>
  );
}
