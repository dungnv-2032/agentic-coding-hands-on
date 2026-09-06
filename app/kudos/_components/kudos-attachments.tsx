import Image from "next/image";

import type { KudosAttachmentView } from "@/lib/kudos/view-model";

/**
 * mm:256:5176 (C.3.6_Image đính kèm) — ALL KUDOS (feed) cards only, at most
 * 5 × 88px thumbs (test-contract.md § Kudos card). `.slice(0, 5)` is the
 * contract boundary itself, not a defensive guess: `kudos-image` must never
 * exceed 5 matches regardless of how many attachments the row carries.
 *
 * Card-fix (2026-09-06), V2 verification: 5×88px + 4×16px gap = 504px fits
 * inside the corrected 680px feed column's 600px content (desktop, one
 * row — unchanged from the frame). Below that — mobile card content can be
 * ~280px — 504px would overflow the card itself, so the row wraps
 * (`flex-wrap`) instead of clipping; thumbnails stay full 88px and
 * un-clipped, just spanning more rows.
 */
export function KudosAttachments({ attachments }: { attachments: KudosAttachmentView[] }) {
  if (attachments.length === 0) return null;

  return (
    // mm:256:5176
    <div className="flex w-full flex-wrap items-center gap-4">
      {attachments.slice(0, 5).map((attachment) => (
        // mm:513:8440 (Image) — outer wrapper radius; mm:513:8436
        // (MM_MEDIA_Sample Image) — inner asset keeps its own radius, per
        // code-rules.md rule 2b (wrapper shape follows the asset).
        <div
          key={attachment.id}
          className="flex h-[88px] w-[88px] shrink-0 items-center justify-center overflow-hidden rounded-[18px] border border-[#998C5F] bg-white"
        >
          <Image
            data-testid="kudos-image"
            src={attachment.imageUrl}
            alt=""
            width={88}
            height={88}
            className="h-full w-full rounded-[4px] border border-[#FFEA9E] object-cover"
          />
        </div>
      ))}
    </div>
  );
}
