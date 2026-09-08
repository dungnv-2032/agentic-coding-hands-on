import Image from "next/image";
import Link from "next/link";

import type { SunnerView } from "@/lib/kudos/view-model";

type ChipRole = "sender" | "receiver";

const NAME_TESTID: Record<ChipRole, string> = {
  sender: "kudos-sender",
  receiver: "kudos-receiver",
};

const BADGE_TESTID: Record<ChipRole, string> = {
  sender: "sunner-badge",
  receiver: "sunner-badge-receiver",
};

/**
 * mm:256:4830 (Infor — `C.3.1_Thông tin người gửi` / `C.3.3_Thông tin
 * người nhận`, both instance the same component). 64px avatar, name link,
 * department, and tier badge.
 *
 * test-contract.md ratification #2: the receiver's badge carries
 * `sunner-badge-receiver`, not `sunner-badge` — two elements sharing one
 * testid on the same card makes `card.getByTestId("sunner-badge")`
 * strict-mode ambiguous (K-9). The suffix is derived from `role` so there
 * is exactly one code path, never two hand-written badge blocks.
 *
 * `title` is present only when `badgeTooltip` is non-null — `New Hero` has
 * no published hoa-thị copy below the 10-Kudos threshold (derive.ts).
 *
 * Card-fix (2026-09-06): the frame only defines this chip at 235px fixed
 * (mm:I3127:21871;256:4858), and the sender→glyph→receiver row (parent,
 * mm:I3127:21871;256:4857) needs 235+235+32(glyph)+2×24(gap-6) = 550px
 * minimum content to hold both chips without overlap — below that, the
 * receiver chip clips past the card edge. This chip switches from
 * full-width/stacked to the fixed 235px row layout at the same
 * `min-[1360px]` viewport breakpoint as the row in kudos-card.tsx — see
 * that file's header comment for why a plain viewport breakpoint was
 * chosen (a `@container` attempt didn't reliably activate in testing) and
 * why 1360px specifically (empirically measured card-width crossover).
 */
export function SunnerChip({ sunner, role }: { sunner: SunnerView; role: ChipRole }) {
  return (
    // mm:256:4858 (C.3.1/C.3.3 instance) — 235px is the frame's FEED chip
    // width (row mm:256:4857, 600px inside the 680px card). The HIGHLIGHT
    // card is only 528px wide (row mm:I2940:13464;335:9442, 480px) and the
    // frame still draws both chips side by side there, so the chip must be
    // elastic and merely *capped* at 235px rather than fixed to it: a hard
    // 235px overflows the highlight card (2x235 + the 32px send glyph = 550
    // > 528) and clipped the receiver. `min-w-0` lets the flex child shrink
    // below its content width so long names ellipsize instead of pushing
    // the row wider than the card.
    <div className="flex w-full min-w-0 max-w-xs flex-1 flex-col items-center justify-center gap-[13px] min-[1360px]:max-w-[235px]">
      {/* mm:256:4734 (MM_MEDIA_Avatar) */}
      <Image
        src={sunner.avatarUrl}
        alt=""
        width={64}
        height={64}
        className="h-16 w-16 shrink-0 rounded-full border-[1.869px] border-white object-cover"
      />
      {/* mm:256:4737 (Frame 477) */}
      <div className="flex w-full min-w-0 flex-col items-start gap-0.5">
        {/* mm:256:4735 — accessible name = the person's name (K-9). The href
            WAS the fixed literal "/profile"; F006 (FR-003, phase 09) makes it
            carry the viewed Sunner's id, because a profile route nothing links
            to is dead surface. That reversal is recorded in
            `plans/260908-0854-profile-ban-than/clarifications.md` premise 3
            and narrows K-9's ratified assertion to `/profile?id=\d+$`.
            The `id > 0` guard is the anonymity backstop: `map-kudos-card.ts`
            redacts a masked sender to the `id: 0` stub, and `kudos-card.tsx`
            already routes those rows to `AnonymousSenderChip` (no link at
            all) — so the guard is unreachable today and exists so a future
            caller cannot leak `?id=0` into a URL. */}
        <Link
          data-testid={NAME_TESTID[role]}
          href={sunner.id > 0 ? `/profile?id=${sunner.id}` : "/profile"}
          className="w-full truncate text-center text-base leading-6 font-bold tracking-[0.15px] text-[#00101A] hover:underline"
        >
          {sunner.fullName}
        </Link>
        {/* mm:256:4741 (Huy hiệu + Sao) */}
        <div className="flex w-full min-w-0 items-center justify-center gap-2.5">
          {/* mm:256:4751 */}
          <span className="min-w-0 truncate text-sm leading-5 font-bold tracking-[0.1px] text-[#999]">
            {sunner.department}
          </span>
          {/* mm:256:4754 (Ellipse 70) */}
          <span aria-hidden className="h-1 w-1 shrink-0 rounded-full bg-[#999] opacity-40" />
          {/* mm:3106:17694 (MM_MEDIA_<tier> Hero) */}
          <span
            data-testid={BADGE_TESTID[role]}
            title={sunner.badgeTooltip ?? undefined}
            className="inline-flex shrink-0 items-center justify-center rounded-full border border-[#FFEA9E]/70 bg-black/30 px-2 py-0.5 text-[11px] leading-4 font-bold tracking-[0.08px] whitespace-nowrap text-white"
          >
            {sunner.badge}
          </span>
        </div>
      </div>
    </div>
  );
}
