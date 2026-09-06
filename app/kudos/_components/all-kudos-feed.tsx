import type { Dictionary } from "@/lib/i18n/dictionaries";
import { FEED_PAGE_SIZE } from "@/lib/kudos/derive";
import type { KudosCardView, ToggleKudosLike } from "@/lib/kudos/view-model";

import { KudosCard } from "./kudos-card";
import { useInfiniteFeed } from "./use-infinite-feed";

/**
 * mm:2940:13482 (C.2_Danh sách lời cảm ơn) feed column. Client-side paging
 * over data already fetched (assumption A4): reveals `FEED_PAGE_SIZE` more
 * rows as `feed-sentinel` enters view, then unmounts the sentinel — which
 * both stops the observer and satisfies "stops silently at the end"
 * (plan.md § Key Insight 10). `kudos-empty` renders when the *filtered* set
 * is empty. Carries no `"use client"` of its own — reached only inside
 * `kudos-board.tsx`'s client boundary; `use-infinite-feed.ts` owns the one
 * DOM-effect API this file needs.
 *
 * Layout-fix task (2026-09-06): this component no longer owns the outer
 * `mx-auto max-w-[1152px] px-*` container — `kudos-board.tsx` now wraps this
 * feed column and `KudosSidebar` together in one row (mm:2940:13481) so the
 * two sit side by side, matching the frame. This file only lays out its own
 * column's contents.
 */
export function AllKudosFeed({
  cards,
  pages,
  onLoadMore,
  copy,
  onHashtagClick,
  onCopyLink,
  toggleLike,
}: {
  cards: KudosCardView[];
  pages: number;
  onLoadMore: () => void;
  copy: Dictionary["kudos"]["card"];
  onHashtagClick: (hashtag: string) => void;
  onCopyLink: (success: boolean) => void;
  toggleLike: ToggleKudosLike;
}) {
  const visible = cards.slice(0, pages * FEED_PAGE_SIZE);
  const hasMore = visible.length < cards.length;
  const sentinelRef = useInfiniteFeed({ hasMore, onIntersect: onLoadMore });

  if (cards.length === 0) {
    return (
      // mm: no dedicated empty-state node in the frame; text is
      // spec-verbatim (clarifications § "ALL KUDOS").
      <p data-testid="kudos-empty" className="w-full py-12 text-center text-base font-bold text-white/70">
        {copy.empty}
      </p>
    );
  }

  return (
    // mm:2940:13482 (C.2 feed column) — vertical card list; width and page
    // gutters now come from the row wrapper in kudos-board.tsx.
    <div className="flex w-full flex-col gap-10">
      {visible.map((card) => (
        <KudosCard
          key={card.id}
          card={card}
          variant="feed"
          copy={copy}
          onHashtagClick={onHashtagClick}
          onCopyLink={onCopyLink}
          toggleLike={toggleLike}
        />
      ))}
      {hasMore && <div ref={sentinelRef} data-testid="feed-sentinel" aria-hidden className="h-px w-full" />}
    </div>
  );
}
