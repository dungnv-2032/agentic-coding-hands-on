import Image from "next/image";
import Link from "next/link";

import type { Dictionary } from "@/lib/i18n/dictionaries";

import { IconChevronDown } from "./icons";

/**
 * R4/D1-D2 — Sun* Kudos promo (`mms_D1_Sunkudos`, node `3390:10349`). Its
 * own `<section>` (never the awards section) so ID-53's
 * `section:has-text(/kudos/i)` scope resolves to exactly this block, and
 * the awards section's negative "no Kudos text" scope stays honest.
 */
export function KudosPromo({ home }: { home: Dictionary["home"] }) {
  const { kudos } = home;

  return (
    // mm:3390:10349
    <section className="mx-auto w-full max-w-[1224px] px-6 py-8 sm:px-12 lg:px-36">
      <div className="relative isolate flex w-full flex-col items-start justify-center overflow-hidden rounded-2xl bg-[#0F0F0F] p-10 sm:p-16">
        {/* mm:I3390:10349;313:8416 (MM_MEDIA_Kudos Background) */}
        <Image
          src="/images/home/kudos-section-bg.png"
          alt=""
          aria-hidden
          fill
          sizes="(min-width: 1024px) 1224px, 100vw"
          className="pointer-events-none -z-10 object-cover"
        />
        {/* mm:I3390:10349;313:8419 (mms_D2_Content) */}
        <div className="flex max-w-[457px] flex-col items-start gap-8 text-white">
          <div className="flex flex-col gap-4">
            {/* mm:I3390:10349;313:8421 */}
            <p className="text-2xl leading-8 font-bold">{kudos.eyebrow}</p>
            {/* mm:I3390:10349;313:8422 */}
            <h2 className="text-[57px] leading-[64px] font-bold tracking-[-0.25px] text-[#FFEA9E]">
              {kudos.title}
            </h2>
            {/* mm:I3390:10349;313:8423 */}
            <p className="text-justify text-base leading-6 font-bold tracking-[0.5px]">
              <span className="block">{kudos.subtitle}</span>
              {kudos.body}
            </p>
          </div>
          {/* mm:I3390:10349;313:8426 (mms_D2.1_Button-IC) */}
          <Link
            href="/kudos"
            className="flex items-center gap-1 rounded bg-[#FFEA9E] px-4 py-4 text-base leading-6 font-bold tracking-[0.15px] text-[#00101A] transition-colors hover:bg-[#FFF8E1]"
          >
            {kudos.cta}
            <IconChevronDown aria-hidden className="h-4 w-4 -rotate-45" />
          </Link>
        </div>
        {/* mm:I3390:10349;329:2948 (MM_MEDIA_Logo/Kudos) */}
        <Image
          src="/images/home/kudos-logo.svg"
          alt={kudos.title}
          width={364}
          height={74}
          className="absolute top-1/2 right-16 hidden -translate-y-1/2 sm:block"
        />
      </div>
    </section>
  );
}
