import { signOut } from "./_actions/auth";
import { getPageContext } from "./_page-context";
import { montserrat, montserratAlternates } from "./_fonts";
import { HomeHeader } from "./_components/home-header";
import { HomeHero } from "./_components/home-hero";
import { RootFurtherBlock } from "./_components/root-further-block";
import { AwardsGrid } from "./_components/awards-grid";
import { KudosPromo } from "./_components/kudos-promo";
import { FloatingWidget } from "./_components/floating-widget";
import { SiteFooter } from "./_components/site-footer";

/**
 * SCR002_Homepage — `/`, the public SAA 2025 landing screen (A1,
 * technical-spec.md), replacing the `create-next-app` boilerplate.
 * `getPageContext` is the one place session/locale state is read; only its
 * two booleans cross into `HomeHeader`, a Client Component — the Supabase
 * user object never does (plan.md integration contract).
 *
 * Header/hero (04/05) are composed, never edited, here. The four remaining
 * regions (06) render inside `<main>` in design order; header and footer
 * stay outside it as sibling landmarks (`banner` / `contentinfo`), and the
 * floating widget is `fixed`-positioned so its DOM position doesn't matter.
 */
export default async function HomePage() {
  const { locale, dictionary, isAuthenticated, isAdmin } = await getPageContext();

  return (
    // mm:2167:9026 (Homepage SAA frame)
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
        <HomeHero dictionary={dictionary} eventStartAt={process.env.NEXT_PUBLIC_EVENT_START_AT} />
        <RootFurtherBlock home={dictionary.home} />
        <AwardsGrid dictionary={dictionary} />
        <KudosPromo home={dictionary.home} />
      </main>
      <FloatingWidget widget={dictionary.home.widget} />
      <SiteFooter dictionary={dictionary} />
    </div>
  );
}
