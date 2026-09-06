import type { Metadata } from "next";

import { signOut } from "@/app/_actions/auth";
import { getPageContext } from "@/app/_page-context";
import { montserrat, montserratAlternates } from "@/app/_fonts";
import { HomeHeader } from "@/app/_components/home-header";
import { SiteFooter } from "@/app/_components/site-footer";
import { getKudosBoard, getSpotlightTotal } from "@/lib/kudos/board-data";

import { toggleKudosLike } from "./_actions/toggle-kudos-like";
import { KudosBoard } from "./_components/kudos-board";
import { KudosHero } from "./_components/kudos-hero";
import { KudosSidebar } from "./_components/kudos-sidebar";
import { SpotlightBoard } from "./_components/spotlight-board";

export const metadata: Metadata = { title: "Sun* Kudos — Sun* Annual Awards 2025" };

/**
 * SCR_kudos-live-board — `/kudos`, the public "Sun* Kudos - Live board" screen
 * (MoMorph `MaZUn5xHXZ`, frame `2940:13431`). Replaces the `ComingSoon`
 * placeholder this route shipped with; `/kudos/new`, `/kudos/secret-box`,
 * `/kudos/[id]` and `/profile` still render it (phase 09's own scope stops
 * at this one file).
 *
 * Composition mirrors `app/awards-information/page.tsx`: `getPageContext()`
 * is the single read of locale + session, and only its two booleans cross
 * into `HomeHeader` — the Supabase `user` object never does. `getKudosBoard()`
 * is the single board read per request (phase 04). This screen renders NO
 * `FloatingWidget` and NO `KudosPromo` — the frame shows neither, and this
 * screen *is* Kudos (clarifications.md § "Shared chrome").
 *
 * Page order is fixed by clarifications § "Resolved from source data":
 * hero → HIGHLIGHT KUDOS → SPOTLIGHT BOARD → ALL KUDOS + sidebar → footer.
 *
 * `KudosBoard` owns the shared filter/carousel/paging state for BOTH the
 * HIGHLIGHT and ALL KUDOS sections in one Fragment, and now also owns
 * *placement* of `SpotlightBoard` and `KudosSidebar` via the `spotlightSlot`
 * and `sidebarSlot` props (layout-fix task, 2026-09-06): DOM/tab order is
 * hero → highlight → spotlight → all-kudos(+sidebar), identical to paint
 * order — no `order-*` CSS repaint. This replaces the earlier disclosed
 * compromise noted in the phase-09 report.
 *
 * `toggleKudosLike` (phase 04, Track B) travels into `KudosBoard` as the
 * `toggleLike` prop, the same "Server Action as a prop" pattern shipped at
 * `app/_components/coming-soon.tsx:29` for `signOutAction` — no Track A file
 * imports it directly.
 */
export default async function KudosPage() {
  const [{ locale, dictionary, isAuthenticated, isAdmin }, board, spotlightTotal] =
    await Promise.all([getPageContext(), getKudosBoard(), getSpotlightTotal()]);
  const { kudos } = dictionary;

  return (
    // mm:2940:13431 (Sun* Kudos - Live board frame)
    <div
      className={`${montserrat.variable} ${montserratAlternates.variable} flex min-h-svh w-full flex-col bg-[#00101A] font-montserrat`}
    >
      <HomeHeader
        locale={locale}
        dictionary={dictionary}
        isAuthenticated={isAuthenticated}
        isAdmin={isAdmin}
        signOutAction={signOut}
      />
      <main className="flex flex-1 flex-col">
        <KudosHero copy={kudos.hero} />

        <KudosBoard
          board={board}
          copy={{
            eyebrow: kudos.eyebrow,
            sections: kudos.sections,
            filters: kudos.filters,
            card: kudos.card,
            toast: kudos.toast,
          }}
          toggleLike={toggleKudosLike}
          spotlightSlot={
            <SpotlightBoard
              nodes={board.spotlight.nodes}
              ticker={board.spotlight.ticker}
              total={spotlightTotal}
              copy={{
                eyebrow: kudos.eyebrow,
                heading: kudos.sections.spotlight,
                board: kudos.spotlightBoard,
              }}
            />
          }
          sidebarSlot={
            <KudosSidebar copy={kudos.sidebar} counts={board.sidebar.counts} gifts={board.sidebar.gifts} />
          }
        />
      </main>
      <SiteFooter dictionary={dictionary} />
    </div>
  );
}
