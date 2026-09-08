import { IconGift } from "@/app/kudos/_components/kudos-icons";
import type { Dictionary } from "@/lib/i18n/dictionaries";
import { formatHeartCount } from "@/lib/kudos/derive";
import type { ProfileStatsView } from "@/lib/profile/profile-view-model";

/**
 * mm:362:5073 (`mms_B_Thống kê`) — the statistics card, the SELF face of the
 * B slot. `app/profile/page.tsx` renders this when `stats !== null` and
 * `WriteKudoBar` when it is null; that single data-level branch is the whole
 * self/other decision (SC-002) and is never re-derived here.
 *
 * Every token is `kudos-sidebar.tsx`'s, verbatim: `border-[#998C5F]`,
 * `bg-[#00070C]`, `rounded-[17px]`, the `#2E3940` divider, 22px white labels
 * against 32px `#FFEA9E` values, and the gold button. Only the geometry
 * differs — 680px wide at `p-10` (40px) instead of the board sidebar's 422px
 * at `p-6` — so this card is a re-lay of shipped parts, not new work.
 *
 * Counts render through `formatHeartCount`, never `toLocaleString`: ICU
 * version drift between the server and the browser hydration-mismatches a
 * formatted number (see `lib/kudos/derive.ts`).
 */

/** mm:362:5076–mm:362:5078, mm:362:5080–mm:362:5081 — 600×40, row, 8px gap. */
function StatRow({ label, value }: { label: string; value: number }) {
  return (
    <div data-testid="profile-stat" className="flex w-full items-center justify-between gap-2">
      <span className="text-[22px] leading-7 font-bold text-white">{label}</span>
      <span className="text-[32px] leading-10 font-bold text-[#FFEA9E]">
        {formatHeartCount(value)}
      </span>
    </div>
  );
}

export function ProfileStatsCard({
  copy,
  stats,
}: {
  copy: Dictionary["profile"]["stats"];
  stats: ProfileStatsView;
}) {
  return (
    // mm:362:5073 — 680px, centred in the 1440 artboard, column, 24px gap.
    <section className="mx-auto flex w-full max-w-[680px] flex-col gap-6">
      {/* mm:362:5074 (`Thống kê`) — 40px padding, 17px radius, 10px gap. */}
      <div
        data-testid="profile-stats-card"
        className="flex w-full flex-col gap-2.5 rounded-[17px] border border-[#998C5F] bg-[#00070C] p-10"
      >
        {/* mm:362:5075 (`Nội dung`) — 600×357, column, 16px gap. */}
        <div className="flex w-full flex-col gap-4">
          {/* mm:362:5076 */}
          <StatRow label={copy.kudosReceived} value={stats.kudosReceived} />
          {/* mm:362:5077 */}
          <StatRow label={copy.kudosSent} value={stats.kudosSent} />
          {/* mm:362:5078 — no flame "x2" badge here: that belongs to the
              board sidebar's row (mm:3241:14931), and this frame draws the
              hearts row plain. */}
          <StatRow label={copy.heartsReceived} value={stats.heartsReceived} />

          {/* mm:362:5079 (Rectangle 14) — 600×1, `#2E3940`. */}
          <div aria-hidden className="h-px w-full bg-[#2E3940]" />

          {/* mm:362:5080 */}
          <StatRow label={copy.secretBoxOpened} value={stats.secretBoxOpened} />
          {/* mm:362:5081 */}
          <StatRow label={copy.secretBoxUnopened} value={stats.secretBoxUnopened} />

          {/* mm:362:5082 — 600×60, 8px radius, `#FFEA9E` on `#00101A` text,
              8px gap. A `<button disabled>`, deliberately NOT the sidebar's
              `<a href="/kudos/secret-box">`: the Secret Box is a deferred
              commission, so the control is rendered and inert (no dialog, no
              navigation, no error) rather than linking somewhere unbuilt. */}
          <button
            type="button"
            disabled
            data-testid="profile-secret-box-button"
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-[#FFEA9E] px-4 py-4 text-[#00101A] disabled:cursor-not-allowed"
          >
            <span className="text-[22px] leading-7 font-bold">{copy.secretBoxButton}</span>
            {/* mm:I362:5082;186:1766 (24×24 gift glyph, `aria-hidden` so the
                accessible name stays exactly "Mở Secret Box"). */}
            <IconGift aria-hidden className="h-6 w-6 shrink-0" />
          </button>
        </div>
      </div>
    </section>
  );
}
