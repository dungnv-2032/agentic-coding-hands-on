import Link from "next/link";
import { useState } from "react";

import type { Dictionary } from "@/lib/i18n/dictionaries";
import { formatHeartCount } from "@/lib/kudos/derive";
import type { KudosCardView, ToggleKudosLike } from "@/lib/kudos/view-model";

import { IconArrowRight, IconHeart, IconLink } from "./kudos-icons";

type CardActionsCopy = Pick<Dictionary["kudos"]["card"], "copyLink" | "viewDetail">;

/**
 * mm:256:5194 (C.4_Button) — the card family's only interactive leaf: the
 * heart toggle, the count, Copy Link, and the highlight-only "Xem chi tiết"
 * link. Carries no `"use client"` of its own (plan.md § Client/server
 * split): it renders only inside phase 07's client boundary via
 * `kudos-card.tsx`, which stays a server component. Never import this file
 * from a genuine server-rendered tree — `useState`/`onClick` below require
 * an ancestor `"use client"` boundary to actually run.
 *
 * `liked`/`hearts` seed from the view model and are only ever overwritten
 * by `toggleLike`'s own resolved result — never a naive local increment
 * (test-contract.md Supabase amendment: "not component-local state"). The
 * `disabled` expression is `!card.canLike`, verbatim, never recomputed
 * (plan.md § Key Insight 5) — anon-viewer and own-kudos both already
 * resolve to `false` upstream.
 */
export function KudosCardActions({
  card,
  copy,
  showDetailLink,
  onCopyLink,
  toggleLike,
}: {
  card: KudosCardView;
  copy: CardActionsCopy;
  showDetailLink: boolean;
  /** Reports clipboard success/failure so the caller can pick the matching toast copy. */
  onCopyLink: (success: boolean) => void;
  toggleLike: ToggleKudosLike;
}) {
  const [liked, setLiked] = useState(card.likedByViewer);
  const [hearts, setHearts] = useState(card.hearts);
  const [pending, setPending] = useState(false);

  function handleHeartClick() {
    // Server-authoritative, deliberately NOT optimistic. test-contract.md
    // requires `aria-pressed` to reflect the viewer's *persisted* like read
    // from `kudos_likes`, "not component-local state" — so the button only
    // ever shows a value the database has confirmed.
    //
    // Phase 09 briefly made this optimistic because K-10/K-25 then read
    // `aria-pressed` with a zero/fixed wait and could outrun the round trip.
    // The tester has since replaced those one-shot reads with auto-retrying
    // web-first assertions, so the optimistic flip is no longer needed — and
    // it was actively harmful: flipping before the insert committed let K-25
    // satisfy its post-click assertion and then reload *while the write was
    // still in flight*, so the reloaded page legitimately rendered
    // `aria-pressed="false"` and the persistence proof failed against a
    // perfectly working data layer. Waiting for the server's own result is
    // what makes "click, reload, still liked" a real proof.
    if (pending) return; // a second click racing the in-flight toggle
    setPending(true);
    void toggleLike(card.id)
      .then((result) => {
        setLiked(result.liked);
        setHearts(result.hearts);
      })
      .finally(() => setPending(false));
  }

  async function handleCopyClick() {
    // No defined behavior for a denied clipboard permission (clarifications
    // § "Copy link" — open question). Degrades to reporting failure rather
    // than throwing; the caller decides how to surface it (dictionary
    // already carries both `toast.copySuccess` and `toast.copyFailure`).
    try {
      const url = `${window.location.origin}/kudos/${card.id}`;
      await navigator.clipboard.writeText(url);
      onCopyLink(true);
    } catch {
      onCopyLink(false);
    }
  }

  return (
    // mm:256:5194 — hearts on the left, Copy Link/detail buttons on the right.
    <div className="flex w-full items-center justify-between gap-6">
      {/* mm:256:5175 (C.4.1_Hearts) */}
      <div className="flex items-center gap-1">
        {/* mm:256:5174 */}
        <span data-testid="kudos-heart-count" className="text-2xl leading-8 font-bold text-[#00101A]">
          {formatHeartCount(hearts)}
        </span>
        {/* mm:256:5171 (MM_MEDIA_Heart) */}
        <button
          type="button"
          data-testid="kudos-heart"
          aria-pressed={liked}
          disabled={!card.canLike}
          onClick={handleHeartClick}
          className="flex h-8 w-8 shrink-0 items-center justify-center disabled:cursor-not-allowed disabled:opacity-50"
        >
          <IconHeart
            aria-hidden
            className={`h-8 w-8 ${liked ? "text-[#D4271D]" : "text-[#998C5F]"}`}
          />
        </button>
      </div>

      <div className="flex items-center gap-2">
        {/* mm:256:5216 (C.4.2_Copy link button) */}
        <button
          type="button"
          data-testid="kudos-copy-link"
          onClick={handleCopyClick}
          className="flex items-center gap-1 rounded p-4 text-[#00101A] transition-opacity hover:opacity-80"
        >
          <span className="text-base leading-6 font-bold tracking-[0.15px]">{copy.copyLink}</span>
          {/* mm:256:5216;186:1441 (MM_MEDIA_Link) */}
          <IconLink aria-hidden className="h-6 w-6 shrink-0" />
        </button>

        {showDetailLink && (
          // mm:335:9663 ("Xem chi tiết") — highlight cards, active slide
          // only (ratification #3): five simultaneous links would be a
          // strict-mode violation on K-12.
          <Link
            data-testid="kudos-detail-link"
            href={`/kudos/${card.id}`}
            className="flex items-center gap-1 rounded p-4 text-[#00101A] transition-opacity hover:opacity-80"
          >
            <span className="text-base leading-6 font-bold tracking-[0.15px]">{copy.viewDetail}</span>
            {/* mm:335:9663;186:1441 — glyph has no MM_MEDIA_ tag in the
                frame (bare "IC" instance); reuses the shared arrow glyph
                already shipped for the carousel rather than hand-drawing a
                near-identical one-off (YAGNI). */}
            <IconArrowRight aria-hidden className="h-6 w-6 shrink-0" />
          </Link>
        )}
      </div>
    </div>
  );
}
