import Image from "next/image";

import type { RulesHeroTierView } from "@/lib/rules/view-model";

/**
 * mm:3204:6161 / :6170 / :6179 / :6188 — the four Hero tier rows under
 * section 1 of the Thể lệ drawer (screen `b1Filzi9i6`, frame `3204:6051`).
 *
 * Layout is read off `design/the-le.png`, not guessed: the badge pill and the
 * threshold label share ONE line, and the description wraps onto the line
 * below (FR-203). Not image-above-text.
 *
 * BR-001 — render order is the array order, which `lib/rules/rules-data.ts`
 * already produced with `order by position`. This component never sorts, and
 * never keys off `id`.
 *
 * ## Why the pills sit in a fixed 128px slot
 *
 * The four crops are tight and slightly inconsistent — 127×22, 110×20, 110×20
 * and 109×19 (measured, not assumed). In the frame the four labels all start
 * at the same x, so a fixed slot plus `object-contain` reproduces that
 * alignment while preserving each pill's aspect ratio. 128px is the width of
 * the widest crop, so nothing is ever scaled up by more than a hair.
 * `object-none` would be more literal but is unsafe here: `next/image` may
 * serve a resized srcset variant, and `object-none` would then draw at the
 * variant's intrinsic size rather than the design size.
 *
 * ## Why the pill takes `alt=""`
 *
 * The pill is decorative in the WCAG 1.1.1 sense — every bit of its meaning is
 * already carried by the `label` text immediately beside it — so it takes a
 * null alt.
 *
 * The alternative that was considered and rejected: a `"Huy hiệu {tier}"`
 * dictionary string. This component holds no tier name, only `label`, the
 * threshold sentence (`Có 1-4 người gửi Kudos cho bạn`), so the template would
 * have produced `Huy hiệu Có 1-4 người gửi Kudos cho bạn` — worse for a screen
 * reader than silence. The tier names (`New Hero` …) live only in the image
 * FILENAMES, and parsing `imagePath` back into user-visible prose would make a
 * storage detail load-bearing for accessibility, so a seed rename would quietly
 * change what a screen reader says. The `heroTierImageAlt` key has since been
 * deleted from `lib/i18n/messages/`; nothing here needs wiring.
 *
 * ## The 20px left indent is measured, not decoration
 *
 * The row frame (`3204:6161`) starts at the content column's own x=927, but
 * BOTH of its children — the pill (`3204:6163`) and the description
 * (`3204:6168`) — start at x=947. So the indent belongs inside the row, which
 * is why `pl-5` sits on the `<li>` and not on the `<ul>`: the row box stays
 * flush with the column the way the frame has it.
 */
export function RulesHeroTierList({ tiers }: { tiers: readonly RulesHeroTierView[] }) {
  return (
    // Row gap 16px: the frame's rows sit at y=260 and y=348, each 72px tall
    // (`3204:6161`, `3204:6170`), so 348 − 332 = 16.
    <ul className="flex flex-col gap-4">
      {tiers.map((tier) => (
        <li
          key={tier.position}
          data-testid="rules-hero-tier"
          className="flex flex-col gap-1 pl-5"
        >
          {/* Pill + threshold label on one line — measured gap is ~12px. */}
          <div className="flex items-center gap-3">
            <Image
              src={tier.imagePath}
              alt=""
              aria-hidden
              width={128}
              height={22}
              className="h-[22px] w-32 shrink-0 object-contain object-left"
            />
            <span className="text-base leading-6 font-bold text-white">{tier.label}</span>
          </div>
          <p className="text-sm leading-5 font-bold text-white">{tier.description}</p>
        </li>
      ))}
    </ul>
  );
}
