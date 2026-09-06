import Image from "next/image";
import Link from "next/link";

import type { Dictionary } from "@/lib/i18n/dictionaries";
import type { GiftRowView } from "@/lib/kudos/view-model";

/**
 * mm:2940:13510 (D.3_10 SUNNER nhận quà). Test-contract.md § Sidebar:
 * `gift-leaderboard` container with a heading and `gift-row` rows (name
 * link + gift line), plus `gift-empty` when the list is empty. The list
 * scrolls independently of the page (`Frame 547`/`Frame 545` scrollbar).
 *
 * Avatars are the single committed `MM_MEDIA_Sample Image` placeholder per
 * assumption A3 — one file for every gift row rather than near-identical
 * per-row crops.
 */
export function GiftLeaderboard({
  copy,
  gifts,
}: {
  copy: Pick<Dictionary["kudos"]["sidebar"], "giftHeading" | "giftEmpty">;
  gifts: GiftRowView[];
}) {
  return (
    // mm:2940:13510
    <div
      data-testid="gift-leaderboard"
      className="flex w-full flex-col gap-4 rounded-[17px] border border-[#998C5F] bg-[#00070C] p-6 pr-4"
    >
      {/* mm:2940:13513 (D.3.1_title) */}
      <h3 className="text-center text-[22px] leading-7 font-bold text-[#FFEA9E]">
        {copy.giftHeading}
      </h3>

      {gifts.length === 0 ? (
        // mm:2940:13514 (Frame 547) — empty state
        <p data-testid="gift-empty" className="text-center text-base text-white">
          {copy.giftEmpty}
        </p>
      ) : (
        // mm:2940:13515 (Frame 548) + mm:2940:13521 (scrollbar visual)
        <ul className="flex max-h-[384px] w-full flex-col gap-4 overflow-y-auto pr-2 [scrollbar-color:#999_transparent] [scrollbar-width:thin]">
          {gifts.map((gift) => (
            // mm:2940:13516 (D.3.2_Thông tin Sunner nhận quà)
            <li key={gift.id} data-testid="gift-row" className="flex items-center gap-2">
              {/* mm:I2940:13516;256:7460 (MM_MEDIA_Avatar) */}
              <Image
                src="/images/kudos/sample-avatar.png"
                alt={gift.sunnerName}
                width={64}
                height={64}
                className="h-16 w-16 shrink-0 rounded-full border border-white object-cover"
              />
              <div className="flex flex-col gap-0.5">
                {/* mm:I2940:13516;256:7462 (Name) */}
                <Link
                  href="/profile"
                  className="text-[22px] leading-7 font-bold text-[#FFEA9E] hover:underline"
                >
                  {gift.sunnerName}
                </Link>
                {/* mm:I2940:13516;256:7472 (Thông báo content) */}
                <span className="text-base leading-6 font-bold tracking-[0.15px] text-white">
                  {gift.giftLabel}
                </span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
