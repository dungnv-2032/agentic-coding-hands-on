import type { ReactNode } from "react";

import type { Dictionary } from "@/lib/i18n/dictionaries";
import type { KudosCardView, ToggleKudosLike } from "@/lib/kudos/view-model";

import { AllKudosFeed } from "./all-kudos-feed";

const SECTION_HEADING_CLASS =
  "text-[32px] leading-[40px] font-bold tracking-[-0.25px] text-[#FFEA9E] sm:text-[57px] sm:leading-[64px]";

// mm:2940:13475 (C_All kudos) / mm:2940:13481 ("Frame 502") — padding lives
// on the OUTER box, the 1152px cap on an INNER box, never combined on the
// same element. This is the pattern `kudos-hero.tsx` already documents
// ("the section carries the lg:px-36 gutters OUTSIDE this cap, same
// container pattern as award-system-hero.tsx"); the header this component
// replaced had drifted from it by stacking both on one div, which — once a
// hard two-column row sits under it — leaves only ~864px of real content
// width at `lg` instead of 1152px (144px/side padding on top of an
// already-1152-capped box, not instead of it). At exactly the frame's own
// 1440px canvas this fix restores the literal 680+50(gap)+422=1152 fit with
// zero shrink; `sunner-chip.tsx` (off-limits) hard-codes two 235px
// `shrink-0` chips per card, so anything narrower than ~630px genuinely
// overflows the card — confirmed with a throwaway screenshot before this
// fix (see the phase report) and not a case `basis`/`shrink` alone could
// paper over.
const GUTTER_CLASS = "w-full px-6 sm:px-12 lg:px-36";
const CAP_CLASS = "mx-auto flex w-full max-w-[1152px]";

/**
 * mm:2940:13475 (C_All kudos) — the section header plus the two-column row
 * (mm:2940:13481, "Frame 502": feed column measures 680px, sidebar 422px,
 * ~50px real gap from position math — 874 - 824; the node's declared
 * `gap:80px` is larger than the actual measured spacing and is not used).
 * Split out of `kudos-board.tsx` to stay under the 200-line file cap
 * (layout-fix task, 2026-09-06).
 *
 * Mobile-first: stacks (feed, then sidebar) below `lg`; becomes the frame's
 * row at `lg` and up. `basis-*` + default `shrink` (rather than a hard
 * `max-w`/fixed width) let both columns keep the frame's ~680:422 ratio at
 * viewports between `lg` and 1440 too, where the gutters alone don't yet
 * leave the full 1152px.
 */
export function AllKudosSection({
  eyebrow,
  heading,
  cards,
  pages,
  onLoadMore,
  copy,
  onHashtagClick,
  onCopyLink,
  toggleLike,
  sidebarSlot,
}: {
  eyebrow: string;
  heading: string;
  cards: KudosCardView[];
  pages: number;
  onLoadMore: () => void;
  copy: Dictionary["kudos"]["card"];
  onHashtagClick: (hashtag: string) => void;
  onCopyLink: (success: boolean) => void;
  toggleLike: ToggleKudosLike;
  sidebarSlot: ReactNode;
}) {
  return (
    <section data-testid="all-kudos-section" className="flex w-full flex-col gap-10 py-16">
      <div className={GUTTER_CLASS}>
        <div className={`${CAP_CLASS} flex-col gap-4`}>
          {/* mm:2940:14222 (Sun* Annual Awards 2025) */}
          <p className="text-2xl leading-8 font-bold text-white">{eyebrow}</p>
          {/* mm:2940:14223 (Rectangle 26) */}
          <div aria-hidden className="h-px w-full bg-[#2E3940]" />
          {/* mm:2940:14225 (ALL KUDOS) */}
          <h2 className={SECTION_HEADING_CLASS}>{heading}</h2>
        </div>
      </div>

      <div className={GUTTER_CLASS}>
        <div className={`${CAP_CLASS} flex-col gap-10 lg:flex-row lg:items-start lg:gap-[50px]`}>
          <div className="min-w-0 w-full lg:basis-[680px] lg:shrink lg:grow-0">
            <AllKudosFeed
              cards={cards}
              pages={pages}
              onLoadMore={onLoadMore}
              copy={copy}
              onHashtagClick={onHashtagClick}
              onCopyLink={onCopyLink}
              toggleLike={toggleLike}
            />
          </div>

          {/* mm:2940:13488 (D_Thống menu phải) — 422px measured width;
              shrinks proportionally with the feed column above rather than
              holding a rigid width. Independently scrollable gift list
              stays inside KudosSidebar (unchanged, off-limits file). */}
          <div className="min-w-0 w-full lg:basis-[422px] lg:shrink lg:grow-0">{sidebarSlot}</div>
        </div>
      </div>
    </section>
  );
}
