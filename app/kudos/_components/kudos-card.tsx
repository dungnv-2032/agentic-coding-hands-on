import type { Dictionary } from "@/lib/i18n/dictionaries";
import type { KudosCardView, ToggleKudosLike } from "@/lib/kudos/view-model";

import { KudosAttachments } from "./kudos-attachments";
import { KudosCardActions } from "./kudos-card-actions";
import { KudosHashtagRow } from "./kudos-hashtag-row";
import { IconPen, IconSend } from "./kudos-icons";
import { SunnerChip } from "./sunner-chip";

export type KudosCardVariant = "highlight" | "feed";

const VARIANT_SHELL: Record<KudosCardVariant, string> = {
  // mm:335:9620 (KUDO - Highlight) — 528px, 4px gold border, 16px radius.
  highlight: "w-full max-w-[528px] rounded-2xl border-4 border-[#FFEA9E] px-6 pt-6 pb-4",
  // mm:256:5231 (C.3_KUDO Post) — no border, 24px radius.
  feed: "w-full rounded-3xl px-6 pt-6 pb-4 sm:px-10 sm:pt-10",
};

const BODY_CLAMP: Record<KudosCardVariant, string> = {
  highlight: "line-clamp-3",
  feed: "line-clamp-5",
};

/**
 * mm:335:9620 / mm:256:5231 (`KUDO - Highlight` and `C.3_KUDO Post` — two
 * Figma component instances of the same field set). One component renders
 * both: `variant="feed"` clamps the body at 5 lines and shows attachments;
 * `variant="highlight"` clamps at 3, skips attachments (design carries none
 * on the highlight instance), and — only on the active slide — shows
 * `kudos-detail-link`.
 *
 * `kudos-edit` (the pen glyph) is feed-only: the highlight component's
 * campaign row is a bare `TEXT` node while the feed component's equivalent
 * row (`D.4_hashtag`) is a `FRAME` wrapping the campaign text *and*
 * `MM_MEDIA_Pen` — the design itself never draws the pen on a highlight
 * card, so gating stays faithful to the frame rather than inventing a
 * highlight-edit affordance the source never shows.
 *
 * Stays a server component: `kudos-card-actions.tsx` and
 * `kudos-hashtag-row.tsx` carry the only interactivity and need no
 * `"use client"` of their own — this file is only ever reached through
 * phase 07's client boundary (plan.md § Client/server split).
 *
 * Card-fix (2026-09-06), defect 1 — attempt 1 used a `@container` query on
 * the article so the Info-user row could key off the card's own rendered
 * width instead of the viewport. Reverted: empirically (Playwright against
 * the live page, `container-type: inline-size` confirmed via
 * `getComputedStyle`, article measured 680px, the `@container (min-width:
 * 630px)` rule present and its selector matching via `Element.matches`),
 * the container query never activated — even an injected `!important`
 * override under the same `@container` condition stayed inert. An
 * isolated repro with byte-identical CSS worked fine, so this looks like a
 * real-world quirk of this render pipeline for this element depth rather
 * than a CSS authoring mistake; not safe to ship unverified.
 *
 * Card-fix, attempt 2 (shipped): a plain viewport breakpoint,
 * `min-[1360px]:`, chosen empirically rather than assumed. The two-column
 * ALL KUDOS row (`all-kudos-section.tsx`, off-limits) applies `lg:shrink`
 * to the feed column, so card width is NOT monotonic in viewport width —
 * measured live (`scratchpad/measure-feed-width.mjs`): 423px at 1024px
 * viewport, dropping further before climbing back to 630.6px at 1360px and
 * 680px (frame-exact) at 1440px+. The chip row needs >=630px card width
 * (235+235+32+2×24 = 550px content + 80px measured `sm:px-10` padding,
 * mm:I3127:21871;256:4857/256:4858/256:5161). No single increasing
 * breakpoint can be exactly correct across that whole non-monotonic curve,
 * so `min-[1360px]:` is chosen to guarantee the two required states: the
 * frame's own 1440px renders as a horizontal row (matches exactly, 680px
 * card, 130px to spare), and every viewport below 1360px — including the
 * `lg`-to-1360px shrink dip — stays stacked, which never overflows. The
 * cost is that the ~726-1024px range, where the card is technically wide
 * enough for a row (single-column, pre-`lg`), stacks unnecessarily; the
 * frame defines no layout there, so this is a documented conservative
 * trade-off, not a defect.
 *
 * Defect 2 (message justification) was investigated and NOT changed: the
 * frame's own message-body node (`I3127:21871;256:5156`, verified via
 * `get_node`/`query_component`, both highlight and feed instances) carries
 * `textAlignHorizontal: JUSTIFIED`, not ragged-right. Per code-rules.md
 * rule 3 ("JUSTIFIED → text-align: justify... DO NOT default to left") the
 * existing `text-justify` below is pixel-correct to the frame — see the
 * report's Unresolved section.
 */
export function KudosCard({
  card,
  variant,
  isActive = false,
  copy,
  onHashtagClick,
  onCopyLink,
  toggleLike,
}: {
  card: KudosCardView;
  variant: KudosCardVariant;
  /** Highlight-carousel only — gates `kudos-detail-link` (ratification #3). */
  isActive?: boolean;
  copy: Dictionary["kudos"]["card"];
  onHashtagClick: (hashtag: string) => void;
  onCopyLink: (success: boolean) => void;
  toggleLike: ToggleKudosLike;
}) {
  const showEdit = variant === "feed" && card.isOwnedByViewer;

  return (
    // mm:335:9620 / mm:256:5231 — bg #FFF8E1 both variants; border/radius/
    // padding differ (VARIANT_SHELL). No heading element inside the card.
    <article
      data-testid="kudos-card"
      className={`flex flex-col gap-4 bg-[#FFF8E1] ${VARIANT_SHELL[variant]}`}
    >
      {/* mm:256:4857 (Info user) — the frame's sender -> glyph -> receiver
          row. Stacked below the `min-[1360px]` viewport breakpoint so the
          chips stay legible on a phone (the frame defines no mobile
          variant); the row above it, for BOTH variants, because the frame
          draws it as a row in the 680px feed card and in the 528px
          highlight card alike. The chips are elastic (see
          `sunner-chip.tsx`) so the narrower highlight card fits without
          clipping the receiver. */}
      <div className="flex w-full min-w-0 flex-col items-center gap-6 min-[1360px]:flex-row min-[1360px]:items-start min-[1360px]:justify-between">
        <SunnerChip sunner={card.sender} role="sender" />
        {/* mm:256:5161 (C.3.2_Icon sent) */}
        <div className="flex shrink-0 items-center justify-center py-2 min-[1360px]:py-[46px]">
          {/* mm:256:5147 (MM_MEDIA_Send) */}
          <IconSend aria-hidden className="h-8 w-8 text-[#00101A]" />
        </div>
        <SunnerChip sunner={card.receiver} role="receiver" />
      </div>

      {/* mm:256:5192 (Rectangle 14) */}
      <div aria-hidden className="h-px w-full bg-[#FFEA9E]" />

      {/* mm:256:5645 (Content) */}
      <div className="flex w-full flex-col gap-4">
        {/* mm:256:5229 (C.3.4_Time) */}
        <p data-testid="kudos-time" className="text-base leading-6 font-bold tracking-[0.5px] text-[#999]">
          {card.sentAtLabel}
        </p>

        {card.campaign !== null && (
          // mm:2234:33038 (D.4_hashtag) — campaign label, centered; pen
          // shown only on a feed card the viewer sent (edit-own-post).
          <div className="flex w-full items-center justify-center gap-2">
            <p data-testid="kudos-campaign" className="text-base leading-6 font-bold tracking-[0.5px] text-[#00101A]">
              {card.campaign}
            </p>
            {showEdit && (
              // mm:2234:33040 (MM_MEDIA_Pen)
              <a data-testid="kudos-edit" href={`/kudos/${card.id}`} aria-label="Edit kudos">
                <IconPen aria-hidden className="h-8 w-8 shrink-0 text-[#00101A]" />
              </a>
            )}
          </div>
        )}

        {/* mm:662:11382 (Frame 425 — message box); flattened
            rgba(255,234,158,0.4) over #FFF8E1 = #FFF2C6 (clarifications). */}
        <div className="w-full rounded-xl border border-[#FFEA9E] bg-[#FFF2C6] px-6 py-4">
          {/* mm:256:5156 */}
          <p
            data-testid="kudos-body"
            className={`text-justify text-xl leading-8 font-bold text-[#00101A] ${BODY_CLAMP[variant]}`}
          >
            {card.message}
          </p>
        </div>

        {variant === "feed" && <KudosAttachments attachments={card.attachments} />}

        <KudosHashtagRow hashtags={card.hashtags} onHashtagClick={onHashtagClick} />
      </div>

      {/* mm:256:7496 (Rectangle 15) */}
      <div aria-hidden className="h-px w-full bg-[#FFEA9E]" />

      <KudosCardActions
        card={card}
        copy={copy}
        showDetailLink={variant === "highlight" && isActive}
        onCopyLink={onCopyLink}
        toggleLike={toggleLike}
      />
    </article>
  );
}
