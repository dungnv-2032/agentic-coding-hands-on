import Image from "next/image";

import type { RulesCollectibleIconView } from "@/lib/rules/view-model";

/**
 * mm:3204:6079 — the six collectible icons under section 2 of the Thể lệ
 * drawer (screen `b1Filzi9i6`, frame `3204:6051`).
 *
 * Two rows of three (FR-204). `items-center` on each cell keeps the artwork
 * aligned when a caption wraps.
 *
 * ## The 80px cell is what makes the captions wrap
 *
 * Every badge instance in the frame (`3204:6083`, `3204:6084`, `3204:6088`) is
 * exactly `width: 80px`, `gap: 8px`, and its caption text node is 80px wide
 * too — so the caption WRAPS. Measured instance heights: 88px (one line),
 * 104px (`TOUCH OF LIGHT`, `FLOW TO HORIZON`, `ROOT FURTHER` — two lines) and
 * 120px (`BEYOND THE BOUNDARY` — three lines), i.e. 64 + 8 + 16·lines. Hence
 * `w-20` on the `<span>`, not only on the image: given the full column pitch,
 * all six captions run flat on one line and every row is 16px too short.
 *
 * ## Why the track list is literal 80px rather than `grid-cols-3`
 *
 * `RulesSection` is `flex … items-start`, so this `<ul>` is sized shrink-to-fit
 * and `repeat(3, minmax(0,1fr))` resolves each track to its max-content — which
 * is the caption's own width, so the pitch tracked whatever the longest caption
 * happened to measure (147px before `w-20`, 80px after). Fixed 80px tracks plus
 * `justify-between` inside the frame's own 377px row (`3204:6085`) reproduce
 * the measured child origins 975 / 1123 / 1272 exactly, and `mx-auto` supplies
 * the 48px the frame insets that row from the 473px content column. `w-full`
 * with `max-w` rather than a fixed `w-[377px]`: below the 553px frame the
 * drawer goes full-bleed, and a fixed width would overflow the viewport.
 *
 * BR-001 — render order is the array order, already sorted by `position` in
 * `lib/rules/rules-data.ts`. This component never re-sorts.
 *
 * ## The artwork is cropped to its top 64px, deliberately
 *
 * The PNGs are 80×88 or 80×104 and each one bakes its OWN caption into the
 * bitmap below the disc (measured: the disc occupies rows 0–63, rows 64–73 are
 * empty, the baked caption starts at row ~74). Rendering the full bitmap would
 * print every caption twice — once as pixels, once as the text node below,
 * which is the one the E2E spec asserts on and the one a screen reader can
 * read. So the image is drawn into a 80×64 box with `object-cover object-top`:
 * the cover scale factor is exactly 1 at that box, so nothing is resampled,
 * and the baked caption falls outside the box.
 *
 * No `rounded-full`: the box is 80×64, not square, and the disc's surround is
 * already opaque `#00070C` — the drawer's own background — so it is invisible
 * as shipped. Rounding the box would clip the disc into an ellipse.
 *
 * ## Why the artwork takes `alt=""`
 *
 * The caption sits directly beneath the artwork as real text, so any alt string
 * would make a screen reader announce each icon twice. The image is decorative
 * in the WCAG 1.1.1 sense and takes a null alt. That call is settled — the
 * dictionary key it replaced (`collectibleIconImageAlt`) has since been deleted
 * from `lib/i18n/messages/`, so there is nothing left to wire up here.
 * `rules-hero-tier-list.tsx` reached the same conclusion for the badge pills.
 *
 * ## `ROOT FURTHER` — and why this block used to say the opposite
 *
 * `caption` arrives as `ROOT FURTHER`, matching the asset name
 * `icon-root-further.png`. This comment previously insisted the caption was
 * `ROOT FUTHER` and must never be "corrected", on the grounds that it was
 * transcribed verbatim from the frame. The rule was right; the reading was
 * wrong. Node `I3204:6088;737:20392` carries BOTH:
 *
 *   itemName  = "ROOT FUTHER"    <- the Figma LAYER name
 *   character = "ROOT FURTHER"   <- the rendered TEXT
 *
 * The layer name had been transcribed instead of the text content. The frame
 * render agrees with `character`. Settled by a MoMorph re-read during phase 08
 * visual validation; seed, fixture and both specs carry the correction.
 *
 * The verbatim-transcription rule still stands and still binds — including the
 * genuine en dash in `Có 10–20 người gửi Kudos cho bạn`, which IS in the source
 * and must not be "fixed" to a hyphen.
 */
export function RulesCollectibleGrid({
  icons,
}: {
  icons: readonly RulesCollectibleIconView[];
}) {
  return (
    <ul className="mx-auto grid w-full max-w-[377px] grid-cols-[repeat(3,80px)] justify-between gap-y-4">
      {icons.map((icon) => (
        <li
          key={icon.position}
          data-testid="rules-collectible-icon"
          className="flex flex-col items-center gap-2"
        >
          <Image
            src={icon.imagePath}
            alt=""
            aria-hidden
            width={80}
            height={64}
            className="h-16 w-20 object-cover object-top"
          />
          {/* `uppercase` guards the styling if a seed row is ever entered in
              mixed case; the frame copy is already uppercase. */}
          <span className="w-20 text-center text-xs leading-4 font-bold tracking-[0.5px] text-white uppercase">
            {icon.caption}
          </span>
        </li>
      ))}
    </ul>
  );
}
