import { useMemo } from "react";

import type { Dictionary } from "@/lib/i18n/dictionaries";
import { pickHighlight } from "@/lib/kudos/derive";
import type { KudosCardView, ToggleKudosLike } from "@/lib/kudos/view-model";

import { KudosCard } from "./kudos-card";
import { IconArrowLeft, IconArrowRight } from "./kudos-icons";

// mm:335:9620 (KUDO - Highlight instance width) / mm:2940:13463 (B.2.3
// itemSpacing) — measured pixel constants driving the centre-mode transform.
const SLIDE_WIDTH = 528;
const SLIDE_GAP = 24;

/**
 * mm:2940:13461 (B.2_HIGHLIGHT KUDOS) — top-5-by-hearts carousel, recomputed
 * after filtering (plan.md § Key Insight 2/3). DOM order equals
 * `pickHighlight` order; centring is a track transform, never a DOM
 * reorder, so K-4's `slides.nth(0)`/`nth(count-1)` hold. `carousel-pagination`
 * renders unconditionally, even at 0 slides (`1/0`), and `kudos-empty`
 * fills the empty state without hiding the pager (Key Insight 3/4 + Todo).
 * Carries no `"use client"` of its own — reached only inside
 * `kudos-board.tsx`'s client boundary.
 */
export function HighlightCarousel({
  cards,
  activeIndex,
  onIndexChange,
  copy,
  onHashtagClick,
  onCopyLink,
  toggleLike,
}: {
  cards: KudosCardView[];
  activeIndex: number;
  onIndexChange: (index: number) => void;
  copy: Dictionary["kudos"]["card"];
  onHashtagClick: (hashtag: string) => void;
  onCopyLink: (success: boolean) => void;
  toggleLike: ToggleKudosLike;
}) {
  const slides = useMemo(() => pickHighlight(cards), [cards]);
  const total = slides.length;
  const clampedIndex = total === 0 ? 0 : Math.min(activeIndex, total - 1);
  const current = total === 0 ? 1 : clampedIndex + 1;

  const prevDisabled = total === 0 || clampedIndex <= 0;
  const nextDisabled = total === 0 || clampedIndex >= total - 1;
  const trackOffset = clampedIndex * (SLIDE_WIDTH + SLIDE_GAP) + SLIDE_WIDTH / 2;

  return (
    // mm:2940:13461 (B.2_HIGHLIGHT KUDOS)
    <div data-testid="highlight-carousel" className="relative flex w-full items-center gap-2 py-6 pb-16">
      {/* mm:2940:13470 (B.2.1_Button lùi) — 60px round prev arrow */}
      <button
        type="button"
        data-testid="carousel-prev"
        aria-label="Previous"
        disabled={prevDisabled}
        onClick={() => onIndexChange(clampedIndex - 1)}
        className="z-10 flex h-[60px] w-[60px] shrink-0 items-center justify-center rounded-full text-white disabled:opacity-30"
      >
        {/* mm:I2940:13470;186:1420 (MM_MEDIA_Left) */}
        <IconArrowLeft aria-hidden className="h-10 w-10" />
      </button>

      <div className="relative w-full overflow-hidden">
        {total === 0 ? (
          // mm: no dedicated node — empty highlight state, spec-verbatim copy.
          <p data-testid="kudos-empty" className="w-full py-16 text-center text-base font-bold text-white/70">
            {copy.empty}
          </p>
        ) : (
          <div
            className="flex items-stretch transition-transform duration-300"
            style={{ transform: `translateX(calc(50% - ${trackOffset}px))`, gap: `${SLIDE_GAP}px` }}
          >
            {slides.map((card, index) => {
              const isActive = index === clampedIndex;
              return (
                // mm:335:9620 (KUDO - Highlight) — per-slide wrapper carrying
                // the carousel's a11y state; the flanks are faded + inert.
                <div
                  key={card.id}
                  data-testid="highlight-slide"
                  aria-current={isActive ? "true" : undefined}
                  aria-hidden={isActive ? undefined : "true"}
                  className={`shrink-0 transition-opacity duration-300 ${
                    isActive ? "opacity-100" : "pointer-events-none opacity-40"
                  }`}
                  style={{ width: `${SLIDE_WIDTH}px` }}
                >
                  <KudosCard
                    card={card}
                    variant="highlight"
                    isActive={isActive}
                    copy={copy}
                    onHashtagClick={onHashtagClick}
                    onCopyLink={onCopyLink}
                    toggleLike={toggleLike}
                  />
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* mm:2940:13468 (B.2.2_Button tiến) — 60px round next arrow */}
      <button
        type="button"
        data-testid="carousel-next"
        aria-label="Next"
        disabled={nextDisabled}
        onClick={() => onIndexChange(clampedIndex + 1)}
        className="z-10 flex h-[60px] w-[60px] shrink-0 items-center justify-center rounded-full text-white disabled:opacity-30"
      >
        {/* mm:I2940:13468;186:1420 (MM_MEDIA_Right) */}
        <IconArrowRight aria-hidden className="h-10 w-10" />
      </button>

      {/* mm: pager — no dedicated node in the frame; "2/5 with its own 28px
          arrows" per clarifications § HIGHLIGHT KUDOS. Reuses the same
          IconArrowLeft/Right pair the 60px arrows use (186:1420 instances
          both sizes in the frame). */}
      <div className="absolute bottom-0 left-1/2 flex -translate-x-1/2 items-center gap-3 text-white">
        <button
          type="button"
          data-testid="pager-prev"
          aria-label="Previous page"
          disabled={prevDisabled}
          onClick={() => onIndexChange(clampedIndex - 1)}
          className="flex h-[28px] w-[28px] items-center justify-center rounded-full border border-[#998C5F] disabled:opacity-30"
        >
          <IconArrowLeft aria-hidden className="h-4 w-4" />
        </button>
        <span data-testid="carousel-pagination" className="text-sm font-bold tracking-[0.5px]">
          {`${current}/${total}`}
        </span>
        <button
          type="button"
          data-testid="pager-next"
          aria-label="Next page"
          disabled={nextDisabled}
          onClick={() => onIndexChange(clampedIndex + 1)}
          className="flex h-[28px] w-[28px] items-center justify-center rounded-full border border-[#998C5F] disabled:opacity-30"
        >
          <IconArrowRight aria-hidden className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
