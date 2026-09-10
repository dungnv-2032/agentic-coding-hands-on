import Link from "next/link";

import type { Dictionary } from "@/lib/i18n/dictionaries";
import { formatBoxCount } from "@/lib/secret-box/contract";

/**
 * mm:1466:7676 — the Open Secret Box card (F009, screen `J3-4YFIpMM`, frame
 * `1466:7676`, `/kudos/secret-box`). A Server Component: it renders the
 * page's only `<h1>` (FR-101 — DEC-02, phase-06 wraps this panel in
 * `<main>`) and takes the close/box controls as injected slots so it never
 * imports either Client Component itself (`closeSlot`/`boxSlot`, the
 * architecture in `phase-04-presentational-components.md`).
 *
 * `canOpen`/`showSignIn` are received as-is, never re-derived: whether a
 * viewer can open a box (no session / no `sunners` row / zero boxes) is a
 * judgement made once upstream (phase 05/06) and handed down as two
 * booleans, per the plan's Key Insights.
 *
 * The anonymous sign-in row shares the instruction line's slot rather than
 * adding a second measured row: the frame draws no separate node for it
 * (unauthored, clarifications.md — the inert state differs from the
 * entitled-zero-boxes state only by this link), and the two are mutually
 * exclusive, so one conditional slot is the minimum that satisfies FR-102
 * and FR-105 without inventing new geometry.
 */
interface SecretBoxPanelProps {
  copy: Dictionary["secretBox"];
  canOpen: boolean;
  showSignIn: boolean;
  unopenedCount: number;
  closeSlot: React.ReactNode;
  boxSlot: React.ReactNode;
}

export function SecretBoxPanel({
  copy,
  canOpen,
  showSignIn,
  unopenedCount,
  closeSlot,
  boxSlot,
}: SecretBoxPanelProps) {
  return (
    // mm:1466:7676 — 651.5×822.6, `#00101A`, 12.73 radius, padding
    // 23.87 vertical / 12.73 horizontal, column, 22.28 gap. `mx-auto` +
    // `max-w` self-centers regardless of the parent's own layout mode
    // (`profile-stats-card.tsx`'s idiom). `relative` so the close glyph
    // (mm:1466:7679) can sit out of the flex flow, exactly where the frame
    // draws it — overlapping the title's row, not stacked below it.
    //
    // `min-h-[822.59px]` + `justify-center` is measured, not padding added
    // by eye. The frame's six children sum to 645px, its five gaps to
    // 111.38 and its padding to 47.73 — 804.11 in total, 18.48px SHORT of
    // the 822.587 the frame itself declares. That slack is real: the node
    // carries a fixed height with `justify-content: center`, so the card is
    // a fixed-size modal whose content floats in the middle, not a box that
    // shrink-wraps its rows. A purely content-driven card renders 804 and
    // misses the design by that 18.48 (e2e SB-A4). `min-h` rather than `h`
    // so the card can still grow instead of clipping when the viewport is
    // too narrow to hold the 557px box slot at full size.
    <div
      data-testid="secret-box-panel"
      className="relative mx-auto flex w-full max-w-[651.5px] min-h-[822.59px] flex-col justify-center gap-[22.28px] rounded-[12.73px] bg-[#00101A] px-[12.73px] py-[23.87px]"
    >
      {/* mm:1466:7678 — the page's only <h1> (FR-101); phase 06 wraps this
          panel in <main>, satisfying the e2e `main h1` contract. */}
      <h1 className="w-full text-center text-[25.46px] leading-[31.82px] font-bold text-[#FFEA9E]">
        {copy.title}
      </h1>

      {/* mm:1466:7679 — 19×19, frame-absolute x 606–625 / y 39–58, i.e.
          top: 39px, right: 651.5 − 625 = 26.5px from this panel's own
          top-left (the `relative` ancestor above). */}
      <div className="absolute top-[39px] right-[26.5px] h-[19px] w-[19px]">{closeSlot}</div>

      {/* mm:1466:7680 — upper hairline, 626×1, `#2E3940`. */}
      <div aria-hidden className="h-px w-full bg-[#2E3940]" />

      {/* mm:1466:7683 — FR-102: rendered only when the viewer can open.
          FR-105: the anonymous face renders a sign-in prompt in this same
          row instead (see the docblock above). Neither re-derives identity;
          both booleans arrive as props. */}
      {canOpen ? (
        <p
          data-testid="secret-box-instruction"
          className="text-[12.73px] leading-[19.09px] font-bold tracking-[0.398px] text-white"
        >
          {copy.instruction}
        </p>
      ) : showSignIn ? (
        <p className="text-center text-[12.73px] leading-[19.09px] font-bold tracking-[0.398px] text-white">
          {copy.signInPrompt}{" "}
          <Link href="/login" data-testid="secret-box-signin" className="underline">
            {copy.signInCta}
          </Link>
        </p>
      ) : null}

      {/* mm:1466:7684 — 557×557 box slot; the interactive control itself is
          injected (`SecretBoxOpener` owns its own client-only state).

          `aspect-square` + `max-w` rather than a hard `h-[557px] w-[557px]`:
          the frame is drawn at 1440 and 557px of fixed width would push a
          horizontal scrollbar onto any phone (the panel's own padding leaves
          barely 375px there). Squaring by aspect ratio keeps the box
          centered and undistorted at every width — which is what test case
          `dd842531` actually asks for — while still measuring exactly 557 at
          the design viewport, where SB-A4 checks it. */}
      <div className="mx-auto aspect-square w-full max-w-[557px]">{boxSlot}</div>

      {/* mm:1466:7688 — lower hairline, matches mm:1466:7680. */}
      <div aria-hidden className="h-px w-full bg-[#2E3940]" />

      {/* mm:1466:7689 — footer row, 35 tall, 6.36 gap, centered.

          The node declares `width: 174px`, but its two children are
          absolutely positioned and together span 238→418 = 180: the label
          (mm:1466:7692) measures 136 wide, the number (mm:1466:7693) 37,
          plus the 6.36 gap. Figma lets them overflow their own frame; CSS
          flex does not, and a literal `w-[174px]` wrapped the label onto two
          lines ("Secretbox chưa / mở"), which the frame plainly draws as one.
          So the row sizes to its content and `whitespace-nowrap` keeps the
          label intact — `mx-auto` still centers it under the box, which is
          what the 174 was expressing. */}
      <div className="mx-auto flex h-[35px] items-center justify-center gap-[6.36px]">
        {/* mm:1466:7692 */}
        <span className="whitespace-nowrap text-[12.73px] leading-[19.09px] font-bold tracking-[0.398px] text-white">
          {copy.countLabel}
        </span>
        {/* mm:1466:7693 — `formatBoxCount` (phase 02) owns the "05"/"00"
            padding rule; never re-implemented here. */}
        <span
          data-testid="secret-box-count"
          className="text-[28.64px] leading-[35px] font-bold text-[#FFEA9E]"
        >
          {formatBoxCount(unopenedCount)}
        </span>
      </div>
    </div>
  );
}
