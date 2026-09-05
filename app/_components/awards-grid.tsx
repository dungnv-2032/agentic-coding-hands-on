import type { Dictionary } from "@/lib/i18n/dictionaries";
import { AWARDS } from "@/lib/awards";

import { AwardCard } from "./award-card";

/**
 * R3 — Awards section (`Hệ thống giải thưởng`, node `2167:9068`): C1 header
 * + C2 grid inside one `<section>`, so ID-7's `section:has-text` scoping
 * resolves to exactly one element (ORCH-05) and carries no "Kudos" text
 * (ID-53's negative scope on the Kudos section).
 */
export function AwardsGrid({ dictionary }: { dictionary: Dictionary }) {
  const { awards } = dictionary.home;

  return (
    // mm:2167:9068
    <section className="mx-auto flex w-full max-w-[1224px] flex-col items-start gap-20 px-6 py-16 sm:px-12 lg:px-36">
      {/* mm:2167:9069 (mms_C1_Header Giải thưởng) */}
      <div className="flex w-full flex-col items-start gap-4">
        {/* mm:2167:9070 */}
        <p className="text-2xl leading-8 font-bold text-white">{awards.eyebrow}</p>
        {/* mm:2167:9071 */}
        <div aria-hidden className="h-px w-full bg-[#2E3940]" />
        {/* mm:2167:9073 */}
        <h2 className="text-[57px] leading-[64px] font-bold tracking-[-0.25px] text-[#FFEA9E]">
          {awards.title}
        </h2>
      </div>

      {/* mm:5005:14974 (mms_C2_Award list) — 3 cols >=1024px, 2 below
          (clarifications overrides spec item C2's "1 column mobile" row;
          ORCH-04 repairs the RED suite's grid-column assertion) */}
      <div
        data-testid="awards-grid"
        className="grid w-full grid-cols-2 gap-x-20 gap-y-20 lg:grid-cols-3"
      >
        {AWARDS.map((award) => (
          <AwardCard
            key={award.slug}
            award={award}
            card={awards.cards[award.key]}
            detailLabel={awards.detailLabel}
          />
        ))}
      </div>
    </section>
  );
}
