import { Fragment } from "react";

import type { Dictionary } from "@/lib/i18n/dictionaries";

import { IconLicense } from "./award-system-icons";

type Prizes = Dictionary["awardSystem"]["cards"][keyof Dictionary["awardSystem"]["cards"]]["prizes"];

interface AwardPrizeListProps {
  prizes: Prizes;
  /** "Giá trị giải thưởng:" — repeated per row, as the frame does. */
  prizeLabel: string;
  /** "Hoặc" — the separator between Signature's two rows. */
  prizeOr: string;
}

/**
 * mm:I313:8467;214:2540 (Frame 444, one row) and mm:313:8490 / mm:313:8498 /
 * mm:313:8501 (Signature: row, "Hoặc" separator, row) — the same 32px-gap
 * rhythm the content column uses.
 *
 * The `Giá trị giải thưởng:` label lives INSIDE the row, not above the list:
 * the frame repeats it for each of Signature's two prizes (mm:I313:8467;214:2544
 * and mm:313:8494), which is why the E2E suite reads that one label through
 * `.first()` while `Số lượng giải thưởng:` — rendered once per card — has no
 * such escape hatch.
 *
 * `note` is rendered only when the dictionary actually carries one. Best
 * Manager and MVP omit the key entirely, and the suite asserts a count of ZERO
 * occurrences of the per-award note inside those two sections — an empty
 * element would still be a match.
 */
export function AwardPrizeList({ prizes, prizeLabel, prizeOr }: AwardPrizeListProps) {
  return (
    <div className="flex w-full flex-col gap-8">
      {prizes.map((prize, index) => (
        <Fragment key={`${prize.amount}-${index}`}>
          {index > 0 && (
            // mm:313:8498 (Frame 524) — label then a hairline running to the edge.
            <div className="flex items-center gap-2">
              {/* mm:313:8499 */}
              <p className="text-sm leading-5 font-bold tracking-[0.1px] text-[#2E3940]">
                {prizeOr}
              </p>
              {/* mm:313:8500 (Rectangle 11) */}
              <div aria-hidden className="h-px flex-1 bg-[#2E3940]" />
            </div>
          )}
          {/* mm:I313:8467;214:2541 (Frame 443) */}
          <div className="flex flex-col gap-4">
            {/* mm:I313:8467;214:2542 (Frame 497) */}
            <div className="flex items-center gap-4">
              {/* White glyph, gold label — the frame's own sampling. */}
              <IconLicense aria-hidden className="h-6 w-6 shrink-0 text-white" />
              {/* mm:I313:8467;214:2544 */}
              <p className="text-2xl leading-8 font-bold text-[#FFEA9E]">{prizeLabel}</p>
            </div>
            {/* mm:I313:8467;214:2546 */}
            <p className="text-[36px] leading-11 font-bold text-white">{prize.amount}</p>
            {/* mm:I313:8467;214:2547 */}
            {prize.note && (
              <p className="text-sm leading-5 font-bold tracking-[0.1px] text-white">
                {prize.note}
              </p>
            )}
          </div>
        </Fragment>
      ))}
    </div>
  );
}
