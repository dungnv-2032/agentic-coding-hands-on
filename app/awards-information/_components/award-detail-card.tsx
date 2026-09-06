import Image from "next/image";

import type { Award } from "@/lib/awards";
import type { Dictionary } from "@/lib/i18n/dictionaries";

import { AwardPrizeList } from "./award-prize-list";
import { IconDiamond, IconTarget } from "./award-system-icons";

type AwardCardCopy = Dictionary["awardSystem"]["cards"][keyof Dictionary["awardSystem"]["cards"]];

interface AwardDetailCardProps {
  award: Award;
  card: AwardCardCopy;
  /** Resolved from `AWARD_UNITS[key]` → `awardSystem.units[…]` by the page. */
  unit: string;
  labels: { quantity: string; prize: string; prizeOr: string };
  /** Even index → image left, odd → image right (frame D.1…D.6). */
  imageFirst: boolean;
  /** The frame draws no closing rule under D.6 (mm:313:8510). */
  isLast: boolean;
}

/**
 * mm:313:8467 (mms_D.1_Top talent) — one instance of `214:2554`/`214:2646`,
 * the component all six cards share. 336x336 award badge beside a content
 * column of title, description, quantity and prize, closed by an 853px rule.
 *
 * `scrollMarginTop` reads `--award-header-offset`, the one value the sticky
 * menu and the scroll-spy band also read, so the hash target and the header
 * cannot drift apart. It resolves to the pinned 112px at `lg` and to the
 * measured header height below it, where the header wraps to several rows —
 * a card parked behind it is unreachable content, not a cosmetic slip.
 *
 * The title is an `<h2>` naming its own `<section>` via `aria-labelledby`:
 * without it these six blocks contribute no headings and no landmarks, and a
 * screen-reader user arriving on a 6,410px page by deep link has no
 * structural way to reach or identify an award.
 *
 * Every asserted string sits in its own leaf element: the quantity number and
 * its unit are two sibling `<span>`s, never one node, because the suite reads
 * each of them with an exact-text match inside this section.
 */
export function AwardDetailCard({
  award,
  card,
  unit,
  labels,
  imageFirst,
  isLast,
}: AwardDetailCardProps) {
  const titleId = `${award.slug}-title`;

  return (
    <section
      id={award.slug}
      aria-labelledby={titleId}
      data-testid={`award-detail-${award.slug}`}
      style={{ scrollMarginTop: "var(--award-header-offset, 112px)" }}
      className={`flex w-full flex-col gap-20 ${isLast ? "" : "border-b border-[#2E3940] pb-20"}`}
    >
      {/* mm:I313:8467;214:2803 (Frame 506) — 40px gutter; the frame alternates
          the badge left/right per card and stacks image-first below `lg`. */}
      <div
        className={`flex flex-col gap-10 lg:gap-10 ${imageFirst ? "lg:flex-row" : "lg:flex-row-reverse"}`}
      >
        {/* mm:I313:8467;214:2525 (mms_D.1.1_Picture-Award) — the badge PNG is
            pre-composed (artwork + award name), so the wrapper radius lives on
            the image itself and the glow follows that same 24px shape.
            `self-start` + `aspect-square` are load-bearing, not decoration: as
            a flex child this `<img>` inherits `align-self: stretch`, which
            resolves its `height: auto` to the text column's height and renders
            the 336x336 source at up to 336x966 — a visible ellipse where the
            frame has a circle (spec D.1.1: 336x336). One
            shipped `award-<slug>.png` per card covers both media layers
            (`mm_media_Award-Thumb-Background` + `mm_media_Award-Name-*`): */}
        {/* mm:I313:8467;214:2525;81:2442 */}
        {/* mm:I313:8468;214:2617;81:2442 */}
        {/* mm:I313:8469;214:2525;81:2442 */}
        {/* mm:I313:8470;214:2617;81:2442 */}
        {/* mm:I313:8473;81:2442 */}
        {/* mm:I313:8510;214:2617;81:2442 */}
        <Image
          src={award.image}
          alt={card.title}
          width={336}
          height={336}
          className="aspect-square h-auto w-full max-w-[336px] shrink-0 self-start rounded-3xl border border-[#FFEA9E] shadow-[0_4px_4px_rgba(0,0,0,0.25),0_0_6px_#FAE287]"
        />

        {/* mm:I313:8467;214:2526 (mms_D.1.2_Content) — 32px column rhythm. */}
        <div className="flex min-w-0 flex-1 flex-col gap-8">
          {/* mm:I313:8467;214:2527 (content) */}
          <div className="flex flex-col gap-6">
            {/* mm:I313:8467;214:2528 (Frame 442) */}
            <div className="flex items-center gap-4">
              {/* White inside a card — the frame samples #FFFFFF on the glyph
                  next to a #FFEA9E label. Only the left menu makes the icon
                  follow the gold active state. */}
              <IconTarget aria-hidden className="h-6 w-6 shrink-0 text-white" />
              {/* mm:I313:8467;214:2530 — class list carried over from the `<p>`
                  this replaced, and Preflight already zeroes heading margins
                  and font-size, so promoting it changes nothing visually. */}
              <h2 id={titleId} className="text-2xl leading-8 font-bold text-[#FFEA9E]">
                {card.title}
              </h2>
            </div>
            {/* mm:I313:8467;214:2531 — index key: the list is static and never
                reordered, whereas keying on the paragraph itself would emit a
                duplicate-key console error the day two locales share a line —
                and the suite asserts zero console errors. */}
            {card.paragraphs.map((paragraph, index) => (
              <p
                key={index}
                className="text-justify text-base leading-6 font-bold tracking-[0.5px] text-white"
              >
                {paragraph}
              </p>
            ))}
          </div>

          {/* mm:I313:8467;214:2532 (Rectangle 8) */}
          <div aria-hidden className="h-px w-full bg-[#2E3940]" />

          {/* mm:I313:8467;214:2534 (Frame 443) — icon, gold label, then the
              count and its unit as two separate leaves. */}
          <div className="flex flex-wrap items-center gap-4">
            <IconDiamond aria-hidden className="h-6 w-6 shrink-0 text-white" />
            {/* mm:I313:8467;214:2536 */}
            <p className="text-2xl leading-8 font-bold text-[#FFEA9E]">{labels.quantity}</p>
            {/* mm:I313:8467;214:3552 (Số lượng) */}
            <span className="flex items-center gap-2">
              {/* mm:I313:8467;214:2538 */}
              <span className="text-[36px] leading-11 font-bold text-white">{card.quantity}</span>
              {/* mm:I313:8467;214:3532 — 60px wide in the frame, so a long unit
                  ("Cá nhân hoặc tập thể") wraps beside the number as designed. */}
              <span className="w-[60px] text-sm leading-5 font-bold tracking-[0.1px] text-white">
                {unit}
              </span>
            </span>
          </div>

          {/* mm:I313:8467;214:2539 (content rule) */}
          <div aria-hidden className="h-px w-full bg-[#2E3940]" />

          <AwardPrizeList
            prizes={card.prizes}
            prizeLabel={labels.prize}
            prizeOr={labels.prizeOr}
          />
        </div>
      </div>
    </section>
  );
}
