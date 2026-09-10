import type { Metadata } from "next";

import { signOut } from "@/app/_actions/auth";
import { HomeHeader } from "@/app/_components/home-header";
import { SiteFooter } from "@/app/_components/site-footer";
import { montserrat, montserratAlternates } from "@/app/_fonts";
import { getPageContext } from "@/app/_page-context";
import { getRulesContent } from "@/lib/rules/rules-data";

import { RulesBackdrop } from "./_components/rules-panel-dismiss";
import { RulesPanel } from "./_components/rules-panel";

export const metadata: Metadata = { title: "Thể lệ — Sun* Annual Awards 2025" };

/**
 * SCR007 — `/standards`, the public "Thể lệ" screen (MoMorph screen
 * `b1Filzi9i6`, frame `3204:6051`). Replaces the shared placeholder
 * (`app/_components/coming-soon.tsx`) this route shipped with; `/admin`,
 * `/kudos/secret-box` and `/kudos/[id]` still render that component, so it
 * stays where it is.
 *
 * Two independent reads, so `Promise.all`: `getPageContext()` for locale +
 * session, `getRulesContent()` for the database-backed rules body (BR-002).
 * `getRulesContent()` creates its own Supabase client — nothing is threaded in
 * from here.
 *
 * Only the two booleans cross into `HomeHeader`, a Client Component. The
 * Supabase user object never does (the rule since F001, and this screen is not
 * where it gets broken).
 *
 * No `FloatingWidget`, for two reasons: the frame shows none, and the widget's
 * own "Thể lệ SAA" shortcut points at this very route.
 */
export default async function StandardsPage() {
  const [{ locale, dictionary, isAuthenticated, isAdmin }, rules] = await Promise.all([
    getPageContext(),
    getRulesContent(),
  ]);

  return (
    // mm:3204:6051 — `min-h-svh`, the shell every shipped screen uses, NOT
    // `h-svh overflow-hidden`. FR-403 wants the only scroll on
    // `rules-panel-content`, and this shell gives it that for free: header +
    // `flex-1` empty main + footer resolves to exactly one viewport, so the
    // page has nothing to scroll (measured, and `FUN_001` asserts it). Clipping
    // with `overflow-hidden` would buy the same guarantee at a real cost — on a
    // narrow viewport the header wraps and the footer stacks, and the clip
    // would cut the footer off with no way to reach it. A page that scrolls
    // there is correct behaviour.
    <div
      className={`${montserrat.variable} ${montserratAlternates.variable} flex min-h-svh w-full flex-col bg-[#00070C] font-montserrat`}
    >
      <HomeHeader
        locale={locale}
        dictionary={dictionary}
        isAuthenticated={isAuthenticated}
        isAdmin={isAdmin}
        signOutAction={signOut}
      />
      {/* Deliberately empty, and not an oversight: the frame's left region is
          flat dark with no content at all. The element stays so the shell keeps
          the header / main / footer structure the four shipped screens use, and
          so the drawer has a main region to be complementary to. */}
      <main className="flex flex-1 flex-col" />
      {/* mm:354:4323 (Footer) */}
      <SiteFooter dictionary={dictionary} />
      {/* Siblings, in z-order: scrim `z-40`, drawer `z-50` (FR-404/FR-405). */}
      <RulesBackdrop />
      <RulesPanel rules={rules} copy={dictionary.rules} />
    </div>
  );
}
