import { KudosCard } from "@/app/kudos/_components/kudos-card";
import { useInfiniteFeed } from "@/app/kudos/_components/use-infinite-feed";
import type { Dictionary } from "@/lib/i18n/dictionaries";
import type { KudosCardView, ToggleKudosLike } from "@/lib/kudos/view-model";
import type { FeedDirection } from "@/lib/profile/profile-view-model";

/**
 * mm:362:5091 (`mms_D_Post all`) — the profile's Kudos column. Measured:
 * `flex-column, gap:24px, align-items:flex-start`, 680px, **single column**
 * (no grid, no second column — unlike the board's `mm:2940:13481` row). The
 * 24px gap is this frame's own value and deliberately differs from
 * `all-kudos-feed.tsx`'s `gap-10`; the outer 680px cap is applied by
 * `kudos-direction-section.tsx`, not here.
 *
 * `KudosCard` is reused **outright** with `variant="feed"` — FR-207/BR-005 and
 * TC_WEB_PROFILE_GUI_006 require the profile card to be the same component as
 * the board's, not a lookalike, so the two surfaces cannot drift. The measured
 * `#FFF8E1` fill and 24px radius already ship at `kudos-card.tsx:114` /
 * `VARIANT_SHELL.feed` (clarifications AMEND-3), so there is nothing to
 * re-token. The Spam chip (`mm:I3127:24169;3127:24095`) is never rendered:
 * `KudosCard` has no such element at all, which is what GUI_007 asks for.
 *
 * Paging is genuinely server-side here (keyset cursor, FR-404) — the board's
 * client-side `pages * FEED_PAGE_SIZE` slice does NOT apply. `use-infinite-feed.ts`
 * is reused unmodified: the sentinel unmounts once `hasMore` is false, which
 * both stops the observer and satisfies "stops at the end".
 *
 * Carries no `"use client"` of its own — reached only inside
 * `kudos-direction-section.tsx`'s client boundary (repo convention, see
 * `all-kudos-feed.tsx`).
 */
export function ProfileKudosFeed({
  cards,
  direction,
  hasMore,
  isBusy,
  onLoadMore,
  copy,
  cardCopy,
  onHashtagClick,
  onCopyLink,
  toggleLike,
}: {
  cards: KudosCardView[];
  /** The **committed** direction — drives which empty copy applies (FR-208). */
  direction: FeedDirection;
  hasMore: boolean;
  /** `switching` or `loading-more` — suppresses both status messages. */
  isBusy: boolean;
  onLoadMore: () => void;
  copy: Dictionary["profile"]["feed"];
  cardCopy: Dictionary["kudos"]["card"];
  onHashtagClick: (hashtag: string) => void;
  onCopyLink: (success: boolean) => void;
  toggleLike: ToggleKudosLike;
}) {
  const sentinelRef = useInfiniteFeed({ hasMore, onIntersect: onLoadMore });

  return (
    // mm:362:5091 — 24px gap, items-start, single column.
    <div data-testid="profile-feed" className="flex w-full flex-col items-start gap-6">
      {cards.map((card) => (
        <KudosCard
          key={card.id}
          card={card}
          variant="feed"
          copy={cardCopy}
          onHashtagClick={onHashtagClick}
          onCopyLink={onCopyLink}
          toggleLike={toggleLike}
        />
      ))}

      {hasMore && (
        <div ref={sentinelRef} data-testid="profile-feed-sentinel" aria-hidden className="h-px w-full" />
      )}

      {/* The feed's single status region. `aria-live` is required by phase 08
          for the end-of-feed message; the empty copy is announced through the
          same region rather than a second one, so a direction switch never
          fires two competing announcements. No node exists in the frame for
          either message (the screen spec lists D.empty.received, D.empty.sent
          and D.end with no mm id), so both are copy-only, unstyled beyond the
          board's own empty-state
          treatment in `all-kudos-feed.tsx`.

          While `isBusy` nothing is rendered here: SCR006 § UI States records the
          `loading` visual as "TBD (draft) chưa quyết định chi tiết hiển thị chờ",
          so a skeleton or spinner would be invented design. An empty region is
          the honest reading — and it keeps "you have seen everything" off the
          screen while page 1 of the new direction is still in flight. */}
      <div role="status" aria-live="polite" className="w-full">
        {!isBusy && cards.length === 0 && (
          <p
            data-testid="profile-feed-empty"
            className="w-full py-12 text-center text-base font-bold text-white/70"
          >
            {direction === "received" ? copy.emptyReceived : copy.emptySent}
          </p>
        )}
        {!isBusy && cards.length > 0 && !hasMore && (
          <p
            data-testid="profile-feed-end"
            className="w-full py-8 text-center text-base font-bold text-white/70"
          >
            {copy.endOfFeed}
          </p>
        )}
      </div>
    </div>
  );
}
