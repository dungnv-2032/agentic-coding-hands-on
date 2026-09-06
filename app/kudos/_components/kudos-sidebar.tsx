import Link from "next/link";

import type { Dictionary } from "@/lib/i18n/dictionaries";
import { formatHeartCount } from "@/lib/kudos/derive";
import type { GiftRowView, SidebarCountsView } from "@/lib/kudos/view-model";

import { GiftLeaderboard } from "./gift-leaderboard";
import { IconFlame, IconGift } from "./kudos-icons";

/**
 * mm:2940:13488 (D_Thống menu phải). Test-contract.md § Sidebar: five
 * `sidebar-stat` rows in exact order, then `secret-box-button`, then the
 * gift leaderboard. Numbers come from the (frozen) view model — labels come
 * from the dictionary (plan.md Key Insight 6).
 */
export function KudosSidebar({
  copy,
  counts,
  gifts,
}: {
  copy: Dictionary["kudos"]["sidebar"];
  counts: SidebarCountsView;
  gifts: GiftRowView[];
}) {
  return (
    // mm:2940:13488
    <aside data-testid="kudos-sidebar" className="flex w-full max-w-[422px] flex-col gap-6">
      {/* mm:2940:13489 (D.1_Thống kê tổng quat) */}
      <div className="flex w-full flex-col gap-2.5 rounded-[17px] border border-[#998C5F] bg-[#00070C] p-6">
        {/* mm:2940:13490 (Nội dung) */}
        <div className="flex w-full flex-col gap-4">
          {/* mm:2940:13491 (D.1.2_Số kudos nhận được) */}
          <div data-testid="sidebar-stat" className="flex w-full items-center justify-between gap-2">
            <span className="text-[22px] leading-7 font-bold text-white">{copy.stats.kudosReceived}</span>
            <span className="text-[32px] leading-10 font-bold text-[#FFEA9E]">
              {formatHeartCount(counts.kudosReceived)}
            </span>
          </div>

          {/* mm:2940:13492 (D.1.3_Số kudos đã gửi) */}
          <div data-testid="sidebar-stat" className="flex w-full items-center justify-between gap-2">
            <span className="text-[22px] leading-7 font-bold text-white">{copy.stats.kudosSent}</span>
            <span className="text-[32px] leading-10 font-bold text-[#FFEA9E]">
              {formatHeartCount(counts.kudosSent)}
            </span>
          </div>

          {/* mm:3241:14882 (D.1.4_Số tim) — flame + "x2" is displayed, never
              simulated (clarifications: special-day ×2 stays out of scope). */}
          <div data-testid="sidebar-stat" className="flex w-full items-center justify-between gap-2">
            <span className="text-[22px] leading-7 font-bold text-white">{copy.stats.heartsReceived}</span>
            <span className="flex items-center">
              {/* mm:3241:14931 (Group 435) */}
              <span className="relative inline-flex h-10 w-[34px] items-center justify-center text-[#FFEA9E]">
                <IconFlame aria-hidden className="absolute inset-0 h-full w-full" />
                <span className="relative text-[17px] font-bold text-white" style={{ WebkitTextStroke: "1px #000" }}>
                  x2
                </span>
              </span>
              <span className="text-[32px] leading-10 font-bold text-[#FFEA9E]">
                {formatHeartCount(counts.heartsReceived)}
              </span>
            </span>
          </div>

          {/* mm:2940:13494 (D.1.5_phân cách nội dung) */}
          <div aria-hidden className="h-px w-full bg-[#2E3940]" />

          {/* mm:2940:13495 (D.1.6_Số secret box đã mở) */}
          <div data-testid="sidebar-stat" className="flex w-full items-center justify-between gap-2">
            <span className="text-[22px] leading-7 font-bold text-white">{copy.stats.secretBoxOpened}</span>
            <span className="text-[32px] leading-10 font-bold text-[#FFEA9E]">
              {formatHeartCount(counts.secretBoxOpened)}
            </span>
          </div>

          {/* mm:2940:13496 (D.1.7_Số secret box chưa mở) */}
          <div data-testid="sidebar-stat" className="flex w-full items-center justify-between gap-2">
            <span className="text-[22px] leading-7 font-bold text-white">{copy.stats.secretBoxUnopened}</span>
            <span className="text-[32px] leading-10 font-bold text-[#FFEA9E]">
              {formatHeartCount(counts.secretBoxUnopened)}
            </span>
          </div>

          {/* mm:2940:13497 (D.1.8_Button mở quà) — accessible name is exactly
              "Mở Secret Box"; the gift glyph is aria-hidden (Key Insight 5). */}
          <Link
            data-testid="secret-box-button"
            href="/kudos/secret-box"
            className="flex w-full items-center justify-center gap-1 rounded-lg bg-[#FFEA9E] px-4 py-4 text-[#00101A] transition-opacity hover:opacity-90"
          >
            <span className="text-[22px] leading-7 font-bold">{copy.secretBoxButton}</span>
            {/* mm:I2940:13497;186:1766 (MM_MEDIA_Open Gift) */}
            <IconGift aria-hidden className="h-6 w-6 shrink-0" />
          </Link>
        </div>
      </div>

      {/* mm:2940:13510 */}
      <GiftLeaderboard copy={copy} gifts={gifts} />
    </aside>
  );
}
