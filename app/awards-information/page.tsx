import type { Metadata } from "next";

import { signOut } from "@/app/_actions/auth";
import { getPageContext } from "@/app/_page-context";
import { montserrat, montserratAlternates } from "@/app/_fonts";
import { HomeHeader } from "@/app/_components/home-header";
import { KudosPromo } from "@/app/_components/kudos-promo";
import { SiteFooter } from "@/app/_components/site-footer";
import { AWARD_UNITS } from "@/lib/award-system";
import { AWARDS } from "@/lib/awards";

import { AwardCategoryNav } from "./_components/award-category-nav";
import { AwardDetailCard } from "./_components/award-detail-card";
import { AwardSystemHero } from "./_components/award-system-hero";

export const metadata: Metadata = { title: "Award Information — Sun* Annual Awards 2025" };

/**
 * R2/W-1 — one offset, three consumers: the sticky menu's `top`, each card's
 * `scroll-margin-top`, and the scroll-spy's band. They all read
 * `--award-header-offset`.
 *
 * At `lg` the wrapper below pins it to 112px, the value the desktop geometry
 * was measured against — a class in the cascade, so nothing that happens at
 * runtime can move it. Below `lg` the header wraps to several rows
 * (`home-header.tsx` and `home-nav.tsx` are both `flex-wrap`), so no single
 * literal is right; `useAwardScrollSpy` measures the header and publishes its
 * real height on `<html>`, which this subtree inherits. The `112px` fallback
 * baked into every consumer keeps the pre-JS and measurement-failed paths
 * identical to today's behaviour.
 */
const HEADER_OFFSET_LG = "lg:[--award-header-offset:112px]";

/**
 * SCR_award-system — `/awards-information`, the public "Hệ thống giải" screen
 * (MoMorph `zFYDgyj_pD`, frame `313:8436`). Replaces the `ComingSoon`
 * placeholder this route shipped with; `/kudos`, `/standards`, `/profile` and
 * `/admin` still render it.
 *
 * Composition mirrors `app/page.tsx`: `getPageContext()` is the single read of
 * locale + session, and only its two booleans cross into `HomeHeader`, a
 * Client Component — the Supabase user object never does. `HomeHeader`,
 * `KudosPromo` and `SiteFooter` are composed unchanged (the frame's Kudos
 * block is byte-identical to the homepage's), and this screen deliberately
 * renders NO `FloatingWidget`: the frame shows none.
 *
 * The two-column body is a plain `<div>`, never a `<section>`. The E2E suite
 * resolves the Kudos block as "the `<section>` containing 'Sun* Kudos'", so a
 * `<section>` wrapper up here would make that locator ambiguous.
 *
 * `AWARDS` drives both the menu and the cards, so the two lists cannot drift
 * out of order; copy is zipped in from `awardSystem.cards[key]` and the unit
 * text from `awardSystem.units[AWARD_UNITS[key]]`.
 */
export default async function AwardsInformationPage() {
  const { locale, dictionary, isAuthenticated, isAdmin } = await getPageContext();
  const { awardSystem } = dictionary;
  const labels = {
    quantity: awardSystem.quantityLabel,
    prize: awardSystem.prizeLabel,
    prizeOr: awardSystem.prizeOr,
  };

  return (
    // mm:313:8436 (Hệ thống giải frame)
    <div
      className={`${montserrat.variable} ${montserratAlternates.variable} ${HEADER_OFFSET_LG} flex min-h-svh w-full flex-col bg-[#00101A] font-montserrat`}
    >
      <HomeHeader
        locale={locale}
        dictionary={dictionary}
        isAuthenticated={isAuthenticated}
        isAdmin={isAdmin}
        signOutAction={signOut}
      />
      <main className="flex flex-1 flex-col">
        <AwardSystemHero hero={awardSystem.hero} />

        {/* mm:313:8458 (mms_B_Hệ thống giải thưởng) — the frame lays this row
            out `space-between` with an 80px minimum gap: menu 178px, cards
            853px, 1152px of room. The 121px that actually separates them is
            leftover space, not a declared gap, so `justify-between` + a 853px
            basis reproduces both edges exactly at the artboard width while
            still letting the cards shrink on narrower screens. Declaring only
            the 80px gap left the card column 42px left of the frame. */}
        <div className="mx-auto flex w-full max-w-[1440px] flex-col gap-10 px-6 pt-16 pb-16 sm:px-12 lg:flex-row lg:items-start lg:justify-between lg:gap-20 lg:px-36 lg:pt-30 lg:pb-24">
          <AwardCategoryNav
            items={AWARDS.map((award) => ({
              slug: award.slug,
              label: awardSystem.cards[award.key].navLabel,
            }))}
            ariaLabel={awardSystem.navAriaLabel}
          />

          {/* mm:313:8466 (D.Danh sách giải thưởng) — 853px at the artboard,
              free to shrink below it (`grow-0` keeps it off the leftover
              space so `justify-between` can place it against the right edge). */}
          <div className="flex min-w-0 flex-1 flex-col gap-20 lg:grow-0 lg:basis-[853px]">
            {AWARDS.map((award, index) => (
              <AwardDetailCard
                key={award.slug}
                award={award}
                card={awardSystem.cards[award.key]}
                unit={awardSystem.units[AWARD_UNITS[award.key]]}
                labels={labels}
                imageFirst={index % 2 === 0}
                isLast={index === AWARDS.length - 1}
              />
            ))}
          </div>
        </div>

        {/* mm:335:12023 (mms_D1_Sunkudos) — the shipped component, widened to
            this frame's container. The homepage frame is a 1512 artboard
            (1512 − 288 gutters = 1224); this one is 1440 (→ 1152), and the
            block is 1152 wide here. At the homepage's 1224 cap the text column
            narrows by 216px and the body copy runs under the KUDOS logo, which
            the frame keeps clear. The prop keeps one component for both
            screens — the homepage passes nothing and is unchanged. */}
        <KudosPromo home={dictionary.home} maxWidthClass="max-w-[1440px]" />
      </main>
      {/* mm:354:4323 (Footer) */}
      <SiteFooter dictionary={dictionary} />
    </div>
  );
}
