import { signOut } from "@/app/_actions/auth";
import { getPageContext } from "@/app/_page-context";
import { montserrat, montserratAlternates } from "@/app/_fonts";
import { HomeHeader } from "@/app/_components/home-header";
import { SiteFooter } from "@/app/_components/site-footer";

/**
 * Shared shell for every declared-placeholder route (phase 07,
 * clarifications.md "Screen scope", ORCH-11): `/awards-information`,
 * `/kudos`, `/standards`, `/profile`, `/admin`. None of these screens is
 * built yet — this renders the real header/footer so navigation and the
 * language selector keep working from every homepage link (ID-55/59,
 * "no broken links"), plus an honest "coming soon" body. It is a declared
 * placeholder, not a stand-in for the destination screen's real content
 * (assumption A3) — no section of the target screen is mocked here.
 */
export async function ComingSoon() {
  const { locale, dictionary, isAuthenticated, isAdmin } = await getPageContext();

  return (
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
      <main className="flex flex-1 flex-col items-center justify-center gap-4 px-6 py-24 text-center">
        <h1 className="text-2xl font-bold text-white">{dictionary.comingSoon.title}</h1>
        <p className="max-w-md text-base text-white/80">{dictionary.comingSoon.body}</p>
      </main>
      <SiteFooter dictionary={dictionary} />
    </div>
  );
}
