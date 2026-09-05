import Image from "next/image";

import type { Dictionary } from "@/lib/i18n/dictionaries";

/**
 * R2/B4 — "Root Further" content block (`mms_B4_content`, node
 * `5001:14827`) plus its decorative `ROOT`/`FURTHER` watermark (`Group 434`,
 * node `3204:10153`), inside the shared container `Frame 486` (node
 * `3204:10152`) — a 1152px content max-width centered in the 1512px cover
 * (code-rules.md §3, containered layout).
 *
 * Design order (read from the three MoMorph text nodes in `mms_B4_content`):
 * node `3204:10156` holds `paragraphs[0..2]` joined by newline, then the
 * quote node `3204:10161`, then node `3204:10162` holds `paragraphs[3..4]` —
 * the pull quote sits after the 3rd paragraph, matching the doc comment on
 * `Dictionary["home"]["rootFurther"]`.
 */
export function RootFurtherBlock({ home }: { home: Dictionary["home"] }) {
  const { rootFurther } = home;
  const beforeQuote = rootFurther.paragraphs.slice(0, 3);
  const afterQuote = rootFurther.paragraphs.slice(3);

  return (
    // mm:3204:10152 (Frame 486)
    <section className="mx-auto flex w-full max-w-[1152px] flex-col items-center gap-8 px-6 py-16 text-white sm:px-16 lg:px-[104px] lg:py-[120px]">
      {/* mm:3204:10153 (Group 434) — ROOT (top, offset right) / FURTHER (bottom, full width) */}
      <div
        role="img"
        aria-label={`${rootFurther.rootAlt} ${rootFurther.furtherAlt}`}
        className="relative h-[134px] w-[290px]"
      >
        {/* mm:3204:10155 */}
        <Image
          src="/images/home/root-watermark-text.png"
          alt=""
          aria-hidden
          width={189}
          height={67}
          className="absolute top-0 left-[51px]"
        />
        {/* mm:3204:10154 */}
        <Image
          src="/images/home/further-watermark-text.png"
          alt=""
          aria-hidden
          width={290}
          height={67}
          className="absolute top-[67px] left-0"
        />
      </div>

      {/* mm:5001:14827 (mms_B4_content) */}
      <div className="flex flex-col gap-8">
        {/* mm:3204:10156 */}
        <div className="flex flex-col gap-4 text-justify text-2xl leading-8 font-bold">
          {beforeQuote.map((paragraph, index) => (
            <p key={index}>{paragraph}</p>
          ))}
        </div>
        {/* mm:3204:10161 */}
        <p className="text-center text-xl leading-8 font-bold">
          {rootFurther.quote}
          <br />
          {rootFurther.quoteSource}
        </p>
        {/* mm:3204:10162 */}
        <div className="flex flex-col gap-4 text-justify text-2xl leading-8 font-bold">
          {afterQuote.map((paragraph, index) => (
            <p key={index}>{paragraph}</p>
          ))}
        </div>
      </div>
    </section>
  );
}
