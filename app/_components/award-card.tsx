import Image from "next/image";
import Link from "next/link";

import type { Award } from "@/lib/awards";

import { IconChevronDown } from "./icons";

interface AwardCardProps {
  award: Award;
  card: { title: string; description: string };
  detailLabel: string;
}

/**
 * mm:2167:9075 (mms_C2.1_Top Talent Award — same structure/component for
 * all six, `componentId: 214:1032`). The thumbnail is the pre-composed
 * `award-<slug>.png` (badge + category-name layer already alpha-composited,
 * asset-manifest.md) — no separate name overlay in code.
 *
 * The whole card is one link (FR-405, ID-47/48/49). test-contract.md: "one
 * element cannot hold two testids" — the generic `award-card` testid sits
 * on the outer wrapper, the slug-specific testid on the inner `<Link>` that
 * covers image + title + "Chi tiết" (ID-50/52). Hover lift + border glow
 * (spec item C2: "nâng nhẹ và viền/ánh sáng nổi bật") is hover-only — the
 * static frame's captured box-shadow is the highlighted state, not the rest
 * state.
 */
export function AwardCard({ award, card, detailLabel }: AwardCardProps) {
  return (
    // mm:2167:9075 (outer instance)
    <div data-testid="award-card" className="group flex w-full flex-col items-start gap-6">
      <Link
        data-testid={`award-card-${award.slug}`}
        href={`/awards-information#${award.slug}`}
        className="flex w-full flex-col items-start gap-6"
      >
        {/* mm:I2167:9075;214:1019 (mms_C2.1.1_Picture-Award) */}
        <Image
          src={award.image}
          alt={card.title}
          width={336}
          height={336}
          className="h-auto w-full rounded-3xl border border-[#FFEA9E] transition-transform duration-200 ease-out group-hover:-translate-y-1 group-hover:shadow-[0_4px_4px_rgba(0,0,0,0.25),0_0_6px_#FAE287]"
        />
        {/* mm:I2167:9075;214:1020 (Frame 490) */}
        <div className="flex flex-col items-start gap-1">
          {/* mm:I2167:9075;214:1021 (mms_C2.1.2) */}
          <p className="text-2xl leading-8 font-normal text-[#FFEA9E]">{card.title}</p>
          {/* mm:I2167:9075;214:1022 (mms_C2.1.3) — 2-line clamp with ellipsis */}
          <p className="line-clamp-2 text-base leading-6 tracking-[0.5px] text-white">
            {card.description}
          </p>
          {/* mm:I2167:9075;214:1023 (mms_C2.1.4_Button-IC) */}
          <span className="mt-2 flex items-center gap-1 py-4 text-base leading-6 font-bold tracking-[0.15px] text-white">
            {detailLabel}
            <IconChevronDown aria-hidden className="h-4 w-4 -rotate-45" />
          </span>
        </div>
      </Link>
    </div>
  );
}
