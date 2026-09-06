import Image from "next/image";

import type { Dictionary } from "@/lib/i18n/dictionaries";

/**
 * mm:313:8437 (mms_3_Keyvisual) + mm:313:8439 (Cover) + mm:313:8450 (KV
 * wordmark) + mm:313:8453 (mms_A_Title hệ thống giải thưởng).
 *
 * Carries the page's ONLY `<h1>`. `e2e/award-system.spec.ts` ID-4 asserts
 * `toHaveText` on `getByRole("heading", { level: 1 })`, so the heading holds
 * that one string and nothing else — no nested span, no icon, no sr-only
 * text. The eyebrow is likewise the sole *visible* copy of "Sun* Annual
 * Awards 2025" on the screen: the header/footer logos carry it only as
 * `alt`/`aria-label`, which `getByText` ignores.
 */
export function AwardSystemHero({ hero }: { hero: Dictionary["awardSystem"]["hero"] }) {
  return (
    // mm:313:8449 (Bìa) — 96px top padding, 144px gutters at the 1440 artboard.
    <section className="relative isolate flex flex-col gap-16 px-6 pt-24 sm:px-12 lg:gap-30 lg:px-36">
      {/* mm:313:8437 (mms_3_Keyvisual) — the frame reuses the homepage
          keyvisual artwork under a different Figma crop: a 1440x547 box whose
          image fill is drawn at `101.245% x 367.889%` offset
          `-0.163px / -858.967px`. Those offsets are re-expressed as
          percentages of the overflow (0.163/18 and 858.967/1465.4) so the same
          band of the artwork stays framed at every viewport width. A CSS
          background — not `next/image` — because that non-uniform crop is not
          expressible through `object-fit` (clarifications: reuse the shipped
          asset, export nothing new). */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 -z-10 aspect-[1440/547] w-full"
        style={{
          backgroundImage: "url(/images/home/keyvisual-hero-bg.png)",
          backgroundSize: "101.245% 367.889%",
          backgroundPosition: "0.906% 58.62%",
          backgroundRepeat: "no-repeat",
        }}
      >
        {/* mm:313:8439 (Cover) — readability wash, gold artwork into #00101A. */}
        <div
          className="absolute inset-0"
          style={{
            background: "linear-gradient(0deg, #00101A -4.23%, rgba(0, 19, 32, 0.00) 52.79%)",
          }}
        />
      </div>

      {/* 1152px, not 1440: the section carries the `lg:px-36` gutters OUTSIDE
          this cap, whereas the body row and the Kudos block cap the padding
          box. All three agree at the 1440 artboard, but above ~1728px a 1440
          cap here would run the hairline 144px past the card column's rules on
          either side. The keyvisual above stays on the `<section>` so it can
          still bleed full width. */}
      <div className="mx-auto flex w-full max-w-[1152px] flex-col gap-16 lg:gap-30">
        {/* mm:313:8450 (KV) */}
        {/* mm:2789:12915 (MM_MEDIA_Root Further Logo) — 338x150 at the
            artboard, same 169/75 aspect as the shipped 451x200 export. */}
        <Image
          src="/images/home/root-further-hero-wordmark.png"
          alt={hero.wordmarkAlt}
          width={451}
          height={200}
          preload
          className="h-auto w-[200px] max-w-full sm:w-[280px] lg:w-[338px]"
        />

        {/* mm:313:8453 (mms_A_Title hệ thống giải thưởng) — gap 16px. */}
        <div className="flex w-full flex-col gap-4">
          {/* mm:313:8454 */}
          <p className="w-full text-center text-2xl leading-8 font-bold text-white">
            {hero.eyebrow}
          </p>
          {/* mm:313:8455 (Rectangle 26) */}
          <div aria-hidden className="h-px w-full bg-[#2E3940]" />
          {/* mm:313:8456 (Frame 488) — centres the heading in the 1152 column. */}
          <div className="flex w-full items-center justify-center">
            {/* mm:313:8457 */}
            <h1 className="text-center text-[32px] leading-10 font-bold tracking-[-0.25px] text-[#FFEA9E] sm:text-[44px] sm:leading-13 lg:text-[57px] lg:leading-16">
              {hero.title}
            </h1>
          </div>
        </div>
      </div>
    </section>
  );
}
