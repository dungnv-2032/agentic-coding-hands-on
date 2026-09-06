"use client";

import { useEffect, useRef } from "react";

/**
 * IntersectionObserver over the ALL KUDOS `feed-sentinel` (plan.md § Key
 * Insight 10 / Implementation Step 5). Client-side paging over data already
 * fetched (assumption A4): the caller unmounts the sentinel once
 * `hasMore` is false, which both stops the effect from re-observing and
 * guards against firing past the end of the list. `"use client"` on this
 * file follows `use-award-scroll-spy.ts`'s convention even though it is
 * only ever reached inside `kudos-board.tsx`'s existing client boundary.
 */
export function useInfiniteFeed({
  hasMore,
  onIntersect,
}: {
  hasMore: boolean;
  onIntersect: () => void;
}) {
  const sentinelRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!hasMore) return;
    const node = sentinelRef.current;
    if (!node) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          onIntersect();
        }
      },
      { rootMargin: "200px" },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, [hasMore, onIntersect]);

  return sentinelRef;
}
