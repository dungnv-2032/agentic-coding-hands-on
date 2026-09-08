import Image from "next/image";

import type { ProfileHeroView } from "@/lib/profile/profile-view-model";

import { ProfileBadgeRow } from "./profile-badge-row";
import { ProfileKeyvisual } from "./profile-keyvisual";

/**
 * mm:362:5052 (`mms_A_Info`) — the hero identity block: keyvisual, avatar,
 * name, department + tier badge, then the six badge slots.
 *
 * Frame: 1440×468, column, `align-items: center`, `justify-content: center`,
 * 32px gap between all four children (avatar y184–384, name y416–496, badge
 * row y528–592, caption y624–652 — every step exactly 32px).
 *
 * Carries the page's ONLY `<h1>` (the Sunner's name), the same division of
 * labour `kudos-hero.tsx` documents: `app/profile/page.tsx` and the KUDOS
 * section must use `<h2>` and below.
 *
 * `ProfileKeyvisual` is rendered here, not by the page, because its layers
 * need this section's `relative isolate` to sit at `-z-10` without falling
 * behind the page background. The page must not render it a second time.
 *
 * AMEND-1: there are no hoa-thị stars on this row. `mms_A.2_Name` contains
 * exactly the name, the department, a 4×4 dot and one tier-badge pill — no
 * star node exists anywhere in the frame, so none is invented.
 */
export function ProfileHero({
  hero,
  badgeHeading,
  unlockedBadgeSlots,
}: {
  hero: ProfileHeroView;
  /** `badges.headingSelf` / `badges.headingOther`, resolved by the page. */
  badgeHeading: string;
  unlockedBadgeSlots?: readonly number[];
}) {
  return (
    // mm:362:5052 — `pt-[184px]` is the frame's distance from the BANNER's top
    // (y0) to the hero content (avatar y184). This section's padding-box top
    // edge is the banner's datum, because `ProfileKeyvisual` anchors to it, so
    // 184px is the only value measured from the right origin.
    //
    // It was `pt-[104px]` — the frame's header-band-to-hero gap (band ends
    // y80), the right number from the wrong datum. Those 80px dropped the six
    // `#323231` badge circles onto the bright keyvisual ribbons: they landed
    // 63px ABOVE the banner's bottom edge where the frame puts them 17px
    // below it, on flat `#00101A`. See reports/implementer-visual-fix.md for
    // the pixel measurements.
    <section
      data-testid="profile-hero"
      className="relative isolate flex w-full flex-col items-center justify-center gap-8 pt-[184px]"
    >
      <ProfileKeyvisual />

      {/* mm:362:5053 (`mms_A.1_Avatar`) — 200×200, 4px white ring. Also an
          inline Figma image fill with no `MM_MEDIA_*` node, so the artwork
          comes from the view model, never from the frame. */}
      {hero.avatarUrl ? (
        <Image
          src={hero.avatarUrl}
          alt=""
          width={200}
          height={200}
          className="h-[200px] w-[200px] shrink-0 rounded-full border-4 border-white object-cover"
        />
      ) : (
        // Sparse profile (A4: signed in, no `sunners` row). The frame defines
        // no empty-avatar artwork; the flat `#323231` it uses for a locked
        // badge slot is the one placeholder grey this screen actually has.
        <div
          aria-hidden
          className="h-[200px] w-[200px] shrink-0 rounded-full border-4 border-white bg-[#323231]"
        />
      )}

      {/* mm:362:5054 (`mms_A.2_Name`) — column, 8px gap. */}
      <div className="flex flex-col items-center gap-2">
        {/* mm:362:5055 — 36px/44px bold, `#FFEA9E`. */}
        <h1 className="text-center text-[36px] leading-[44px] font-bold text-[#FFEA9E]">
          {hero.fullName}
        </h1>

        {/* mm:362:5056 (`A.2.2. Thông tin chi tiết`) — row, 10px gap, centred. */}
        <div className="flex items-center justify-center gap-2.5">
          {/* mm:362:5057 + mm:362:5060 — a null department hides the text AND
              the separator dot together, never one without the other. */}
          {hero.department !== null && (
            <>
              <span className="text-[22px] leading-7 font-bold text-white">{hero.department}</span>
              {/* mm:362:5060 (Ellipse 70) — 4×4, `#999` at 40%. */}
              <span aria-hidden className="h-1 w-1 shrink-0 rounded-full bg-[#999] opacity-40" />
            </>
          )}

          {/* mm:3053:6061 (`danh hiệu`) — 109×19 pill, 0.5px `#FFEA9E` border,
              48px radius, 12.821px/17px bold white text with a 1.3px white
              glow. Hidden outright at 0 received Kudos (GUI_009) — that is
              `badge === null`, NOT a "New Hero" pill.
              The instance also layers `image 26`/`image 27` glow rectangles
              behind the text; neither resolves through `get_media_files`, so
              the pill renders transparent rather than with invented artwork —
              the same rule that retired the stars and the badge images. */}
          {hero.badge !== null && (
            <span
              data-testid="profile-tier-badge"
              title={hero.badgeTooltip ?? undefined}
              className="inline-flex h-[19px] shrink-0 items-center justify-center rounded-[48px] border-[0.5px] border-[#FFEA9E] px-2.5 text-[12.821px] leading-[17px] font-bold tracking-[0.092px] whitespace-nowrap text-white"
              style={{ textShadow: "0 0 1.3px #FFF" }}
            >
              {hero.badge}
            </span>
          )}
        </div>
      </div>

      {/* mm:362:5064 + mm:3053:10052 */}
      <ProfileBadgeRow heading={badgeHeading} unlockedSlots={unlockedBadgeSlots} />
    </section>
  );
}
