"use client";

import { useRouter } from "next/navigation";
import { useCallback, useRef, useState } from "react";

import { KudosToast } from "@/app/kudos/_components/kudos-toast";
import type { Dictionary } from "@/lib/i18n/dictionaries";
import type { KudosCardView, ToggleKudosLike } from "@/lib/kudos/view-model";
import type { FeedCursor, FeedDirection, FetchProfileKudosPage, ProfileFeedPage } from "@/lib/profile/profile-view-model";

import { ProfileDirectionMenu } from "./profile-direction-menu";
import { ProfileKudosFeed } from "./profile-kudos-feed";

/** SM-001's four load states, named as the functional spec names them. */
type FeedStatus = "idle" | "switching" | "loading-more" | "settled";

export interface KudosDirectionCopy {
  /** SCR006 C.1 reuses the board's `kudos.eyebrow` — no new key. */
  eyebrow: string;
  direction: Dictionary["profile"]["direction"];
  feed: Dictionary["profile"]["feed"];
  card: Dictionary["kudos"]["card"];
  toast: Dictionary["kudos"]["toast"];
}

// mm:362:5088 — 57px/64px/700, tracking -0.25px, #FFEA9E; the board's exact
// section-heading treatment, mobile step-down included.
const HEADING_CLASS =
  "text-[32px] leading-[40px] font-bold tracking-[-0.25px] text-[#FFEA9E] sm:text-[57px] sm:leading-[64px]";
// mm:362:5084 / mm:362:5090 declare `padding: 0 144px`; the content inside
// measures 680px centred on the 1440 canvas (startX 380 → endX 1060). Padding
// on the OUTER box, cap on an INNER box — never both on one element
// (code-rules.md's container rule, misapplied once in `all-kudos-section.tsx`).
const GUTTER_CLASS = "w-full px-6 sm:px-12 lg:px-36";
const CAP_CLASS = "mx-auto flex w-full max-w-[680px] flex-col";

/**
 * mm:362:5083 ("Frame 530", `flex-column gap:40px`) — regions C and D of
 * SCR006: the KUDOS header (`mm:362:5084`) with its direction dropdown, and
 * the paged card feed (`mm:362:5091`). This is the section's **single client
 * boundary**: direction, accumulated pages and the Copy-Link toast live here,
 * so the trigger label and the feed can never disagree about which list is on
 * screen. `page.tsx` (phase 09) stays a Server Component and passes the two
 * Server Functions through as props — F004's "Server Action as a prop" idiom
 * (`kudos-board.tsx`), which is why nothing here imports `lib/profile/*` or
 * Supabase. `onHashtagClick`/`onCopyLink` are resolved here, not taken as
 * props: a Server Component cannot pass an event handler across the boundary
 * at all. DEC-001 — **`Đã nhận` is active on first render** and `initialPage`
 * is page 1 of it; the frame's `Đã gửi (5)` is the mock's moment, and
 * TC_WEB_PROFILE_FUN_009 governs the default.
 */
export function KudosDirectionSection({
  targetSunnerId,
  isSelf,
  counts,
  initialPage,
  copy,
  fetchPage,
  toggleLike,
}: {
  targetSunnerId: number | null;
  isSelf: boolean;
  /** `sent` is null on another Sunner's profile — SEC_001, absent not hidden. */
  counts: { received: number; sent: number | null };
  initialPage: ProfileFeedPage;
  copy: KudosDirectionCopy;
  fetchPage: FetchProfileKudosPage;
  toggleLike: ToggleKudosLike;
}) {
  const router = useRouter();
  const [direction, setDirection] = useState<FeedDirection>("received");
  const [cards, setCards] = useState<KudosCardView[]>(initialPage.cards);
  const [cursor, setCursor] = useState<FeedCursor | null>(initialPage.nextCursor);
  const [hasMore, setHasMore] = useState(initialPage.hasMore);
  const [status, setStatus] = useState<FeedStatus>(initialPage.hasMore ? "idle" : "settled");
  const [toast, setToast] = useState<{ message: string; key: number } | null>(null);

  // Monotonic request id — only the newest request may commit, so a double
  // click (or a switch landing on an in-flight load-more) discards the stale
  // response instead of letting it overwrite.
  const requestIdRef = useRef(0);
  const inFlightRef = useRef(false);
  const toastKeyRef = useRef(0);

  const loadPage = useCallback(
    async (next: FeedDirection, nextCursor: FeedCursor | null) => {
      const switching = nextCursor === null;
      const requestId = (requestIdRef.current += 1);
      inFlightRef.current = true;
      setStatus(switching ? "switching" : "loading-more");
      if (switching) {
        // FR-403 — the old direction's pages go immediately, while `direction`
        // (hence the trigger label) does not move until the new page lands.
        // Dropping cursor/hasMore also unmounts the sentinel, so no load-more
        // races the switch.
        setCards([]);
        setCursor(null);
        setHasMore(false);
      }
      try {
        const page = await fetchPage({ targetSunnerId, direction: next, cursor: nextCursor });
        if (requestId !== requestIdRef.current) return;
        setDirection(next);
        setCards((current) => (switching ? page.cards : [...current, ...page.cards]));
        setCursor(page.nextCursor);
        setHasMore(page.hasMore);
        setStatus(page.hasMore ? "idle" : "settled");
      } catch {
        // No feed error state exists in the spec or the test cases, so none is
        // invented: the feed stops. `hasMore` is forced false on purpose —
        // true would keep the sentinel mounted and re-fire the failure.
        if (requestId !== requestIdRef.current) return;
        setHasMore(false);
        setStatus("settled");
      } finally {
        if (requestId === requestIdRef.current) inFlightRef.current = false;
      }
    },
    [fetchPage, targetSunnerId],
  );

  const handleSelect = useCallback(
    // DEC-002 — the menu closed itself already; re-picking the active option
    // changes nothing else. No request, no blank list, and unlike the board's
    // filters there is no "unfiltered" state to fall back to.
    (next: FeedDirection) => {
      if (next !== direction) void loadPage(next, null);
    },
    [direction, loadPage],
  );

  const handleLoadMore = useCallback(() => {
    // A ref, not state, so a second sentinel intersection in the same tick is
    // rejected synchronously instead of racing a re-render.
    if (inFlightRef.current || !hasMore || cursor === null) return;
    void loadPage(direction, cursor);
  }, [cursor, direction, hasMore, loadPage]);

  const handleHashtagClick = useCallback(
    // FR-405 — the profile owns no hashtag filter; it hands the tag to the
    // board, which reads `?hashtag=` on mount (phase 09).
    (tag: string) => router.push(`/kudos?hashtag=${encodeURIComponent(tag)}`),
    [router],
  );

  const handleCopyLink = useCallback(
    (success: boolean) => {
      const message = success ? copy.toast.copySuccess : copy.toast.copyFailure;
      setToast({ message, key: (toastKeyRef.current += 1) });
    },
    [copy.toast.copyFailure, copy.toast.copySuccess],
  );

  return (
    <section data-testid="profile-kudos-section" className={`flex flex-col py-16 ${GUTTER_CLASS}`}>
      {/* mm:362:5083 — 40px between the header block and the feed. */}
      <div className={`${CAP_CLASS} gap-10`}>
        {/* mm:362:5084 (mms_C_Header Giải thưởng) — 16px column gap. */}
        <div className="flex w-full flex-col gap-4">
          {/* mm:362:5085 (mms_C.1_title) — 24px/32px/700, white. */}
          <p className="text-2xl leading-8 font-bold text-white">{copy.eyebrow}</p>
          {/* mm:362:5086 (Rectangle 26) — 1px #2E3940. */}
          <div aria-hidden className="h-px w-full bg-[#2E3940]" />
          {/* mm:362:5087 (Frame 488) — row, 32px gap, space-between, 64px tall.
              `flex-wrap` is the only addition: the frame exists at 1440 only,
              where heading + trigger cannot share a phone line. */}
          <div className="flex flex-wrap items-center justify-between gap-8">
            {/* mm:362:5088 — a literal per SCR006 § 3 ("Tĩnh, không cần key
                riêng"): the word is identical in vi and en. */}
            <h2 className={HEADING_CLASS}>KUDOS</h2>
            <ProfileDirectionMenu
              counts={counts}
              isSelf={isSelf}
              copy={copy.direction}
              activeDirection={direction}
              onSelect={handleSelect}
            />
          </div>
        </div>
        {/* mm:362:5090 → mm:362:5091 (mms_D_Post all) */}
        <ProfileKudosFeed
          cards={cards}
          direction={direction}
          hasMore={hasMore}
          isBusy={status === "switching" || status === "loading-more"}
          onLoadMore={handleLoadMore}
          copy={copy.feed}
          cardCopy={copy.card}
          onHashtagClick={handleHashtagClick}
          onCopyLink={handleCopyLink}
          toggleLike={toggleLike}
        />
      </div>

      {/* Copy Link reuses the board's toast verbatim (FR-405). */}
      <KudosToast toast={toast} onDismiss={() => setToast(null)} />
    </section>
  );
}
