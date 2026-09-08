import Link from "next/link";

import { IconPen } from "@/app/kudos/_components/kudos-icons";
import type { Dictionary } from "@/lib/i18n/dictionaries";

/**
 * The OTHER face of the B slot (`mm:362:5073`) — the write-Kudo bar shown on
 * another Sunner's profile in place of the statistics card.
 *
 * The frame captures only the self view, so this region has no node of its
 * own; `docs/screens/SCR006_ProfileBanThan/spec.md` (row `B.other`) resolves
 * it as "mô hình theo thanh viết Kudo của bảng tin" — modelled on the board's
 * compose bar. So the shell is `kudos-hero.tsx`'s shipped compose entry
 * verbatim (`mm:2940:13449`: 68px radius, `#998C5F` border,
 * `rgba(255,234,158,0.1)` fill, pen glyph, 16px bold label) re-laid at the B
 * slot's 680px. Nothing about it is invented.
 *
 * FUN_007 translated: F005 shipped Viết Kudo as a page, not a modal, so this
 * links to `/kudos/new?receiverId={id}`, which preselects the recipient and
 * leaves the field editable. Exactly one link lives inside the bar — the test
 * resolves it with `bar.getByRole("link")` under strict mode.
 *
 * No statistics row and no `Mở Secret Box` button appears anywhere on this
 * face; `app/profile/page.tsx` renders this component instead of
 * `ProfileStatsCard` when `stats === null`, and never both.
 */
export function WriteKudoBar({
  copy,
  targetName,
  targetSunnerId,
}: {
  copy: Dictionary["profile"]["writeBar"];
  /** `hero.fullName` of the Sunner being viewed — interpolated into the label. */
  targetName: string;
  /** `ProfileViewModel.writeKudoTargetId`; the page renders this only when non-null. */
  targetSunnerId: number;
}) {
  return (
    // mm:362:5073 (slot geometry: 680px, centred, 24px gap)
    <section
      data-testid="profile-write-bar"
      className="mx-auto flex w-full max-w-[680px] flex-col gap-6"
    >
      {/* Shell: mm:2940:13449 (`A.1_Button ghi nhận`) from the board hero. */}
      <Link
        href={`/kudos/new?receiverId=${targetSunnerId}`}
        className="flex w-full items-center gap-4 rounded-[68px] border border-[#998C5F] bg-[rgba(255,234,158,0.1)] px-4 py-6 text-white transition-colors hover:bg-[rgba(255,234,158,0.18)]"
      >
        {/* mm:I2940:13449;186:2759 (MM_MEDIA_Pen) */}
        <IconPen aria-hidden className="h-6 w-6 shrink-0" />
        <span className="text-base font-bold tracking-[0.15px]">
          {copy.label.replace("{name}", targetName)}
        </span>
      </Link>
    </section>
  );
}
