import Image from "next/image";
import Link from "next/link";

import type { Dictionary } from "@/lib/i18n/dictionaries";

import { IconChevronDown } from "./icons";
import { CountdownTimer } from "./countdown-timer";

/**
 * mm:2167:9027 (mms_3.5_Keyvisual) + mm:2167:9029 (Cover overlay) +
 * mm:2167:9031 (Frame 487 — wordmark, countdown/event info, CTAs).
 *
 * `eventStartAt` is read from `process.env.NEXT_PUBLIC_EVENT_START_AT` by
 * the page (06) and passed down as a literal — never read here, so server
 * and client agree on the same value (plan.md integration contract).
 */

interface HomeHeroProps {
  dictionary: Dictionary;
  eventStartAt?: string;
}

export function HomeHero({ dictionary, eventStartAt }: HomeHeroProps) {
  const { home } = dictionary;

  return (
    // mm:2167:9026 (Homepage SAA frame background) + mm:2167:9030 (Bìa)
    // No `overflow-hidden` here: the keyvisual (mm:2167:9027) is 1512x1392 —
    // taller than this section's own content box — and the design has it
    // bleed past the hero into the top of the Root Further block
    // (mm:3204:10152 starts at y=899, the image ends at y=1392). Clipping
    // would recreate the hard-cut defect this fixes.
    <section className="relative isolate bg-[#00101A] px-6 pt-24 pb-24 sm:px-12 lg:px-36">
      {/* mm:2167:9027 (mms_3.5_Keyvisual) — intrinsic 1512x1392 aspect-ratio
          box anchored to the top so the artwork keeps its full width/height
          proportions at any viewport width instead of being object-cover
          cropped into a shorter container. */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 -z-10 aspect-[1512/1392] w-full"
      >
        {/* mm:2167:9028 (MM_MEDIA_Keyvisual BG) */}
        {/* Full-bleed and first-viewport, so THIS is the LCP element — not
            the wordmark below it. `preload` (Next 16's replacement for the
            deprecated `priority`) keeps it out of the lazy-load default;
            `sizes` stops the optimizer assuming a narrower candidate. */}
        <Image
          src="/images/home/keyvisual-hero-bg.png"
          alt=""
          fill
          sizes="100vw"
          preload
          className="object-cover"
        />
        {/* mm:2167:9029 (Cover) — dark readability overlay */}
        <div
          className="absolute inset-0"
          style={{
            background:
              "linear-gradient(12deg, #00101A 23.7%, rgba(0, 18, 29, 0.46) 38.34%, rgba(0, 19, 32, 0) 48.92%)",
          }}
        />
      </div>

      <div className="mx-auto flex max-w-[1224px] flex-col items-start gap-10">
        {/* mm:2788:12911 (MM_MEDIA_Root Further Logo) — above the fold and
            only ~13KB, so it is preloaded too; the keyvisual above is the
            actual LCP candidate by area. */}
        <Image
          src="/images/home/root-further-hero-wordmark.png"
          alt={home.wordmarkAlt}
          width={451}
          height={200}
          preload
          className="h-auto w-[280px] max-w-full sm:w-[360px] lg:w-[451px]"
        />

        {/* mm:2167:9034 (Frame 523 — countdown + event info) */}
        <div className="flex flex-col items-start gap-4">
          <CountdownTimer
            eventStartAt={eventStartAt}
            labels={{
              comingSoon: home.comingSoon,
              days: home.days,
              hours: home.hours,
              minutes: home.minutes,
            }}
          />
          <EventInfo home={home} />
        </div>

        {/* mm:2167:9062 (mms_B3_Call-To-Action) */}
        <div className="flex flex-wrap items-start gap-10">
          <Link
            href="/awards-information"
            role="button"
            className="flex items-center gap-1 rounded-lg bg-[#FFEA9E] px-6 py-4 text-[22px] leading-7 font-bold text-[#00101A] transition-colors hover:bg-[#FFF8E1]"
          >
            {home.ctaAwards}
            <IconChevronDown aria-hidden className="h-6 w-6 -rotate-90" />
          </Link>
          <Link
            href="/kudos"
            role="button"
            className="flex items-center gap-1 rounded-lg border border-[#998C5F] bg-[rgba(255,234,158,0.10)] px-6 py-4 text-[22px] leading-7 font-bold text-white transition-colors hover:bg-[rgba(255,234,158,0.40)]"
          >
            {home.ctaKudos}
            <IconChevronDown aria-hidden className="h-6 w-6 -rotate-90" />
          </Link>
        </div>
      </div>
    </section>
  );
}

/** mm:2167:9053 (mms_B2_Thông tin sự kiện) — copy is dictionary-sourced. */
function EventInfo({ home }: { home: Dictionary["home"] }) {
  return (
    <div className="flex flex-col items-start gap-2">
      {/* mm:2167:9054 (Frame 522) */}
      <div className="flex flex-wrap items-center gap-[60px]">
        {/* mm:2167:9055 (Group 417) */}
        <p className="flex items-baseline gap-2 text-base leading-6 font-bold tracking-[0.15px] text-white">
          {home.eventTimeLabel}
          <span className="text-2xl leading-8 text-[#FFEA9E]">{home.eventTimeValue}</span>
        </p>
        {/* mm:2167:9058 (Group 418) */}
        <p className="flex items-baseline gap-2 text-base leading-6 font-bold tracking-[0.15px] text-white">
          {home.eventVenueLabel}
          <span className="text-2xl leading-8 text-[#FFEA9E]">{home.eventVenueValue}</span>
        </p>
      </div>
      {/* mm:2167:9061 */}
      <p className="text-base leading-6 font-bold tracking-[0.5px] text-white">
        {home.eventLivestream}
      </p>
    </div>
  );
}
