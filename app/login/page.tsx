import { cookies } from "next/headers";
import { Montserrat, Montserrat_Alternates } from "next/font/google";

import { getDictionary } from "@/lib/i18n/dictionaries";
import { LOCALE_COOKIE, resolveLocale } from "@/lib/i18n/locales";

import { signInWithGoogle } from "./actions";
import { HeroBackground } from "./_components/hero-background";
import { LoginContent } from "./_components/login-content";
import { LoginFooter } from "./_components/login-footer";
import { LoginHeader } from "./_components/login-header";

const montserrat = Montserrat({
  variable: "--font-montserrat",
  subsets: ["latin", "vietnamese"],
  weight: ["400", "700"],
});

const montserratAlternates = Montserrat_Alternates({
  variable: "--font-montserrat-alternates",
  subsets: ["latin"],
  weight: ["700"],
});

/**
 * SCR-login — the single entry screen for SAA 2025 (spec.md §1). Reads the
 * locale cookie and `?error` query directly (BR-003 fallback lives in
 * `resolveLocale`; DEC-001's error banner is driven by query presence, not
 * value) and composes the four regions from design-notes.md's node tree.
 */
export default async function LoginPage(props: PageProps<"/login">) {
  const [cookieStore, searchParams] = await Promise.all([
    cookies(),
    props.searchParams,
  ]);

  const locale = resolveLocale(cookieStore.get(LOCALE_COOKIE)?.value);
  const dictionary = getDictionary(locale);

  const errorParam = searchParams?.error;
  const hasError =
    (typeof errorParam === "string" && errorParam.length > 0) ||
    (Array.isArray(errorParam) && errorParam.length > 0);

  return (
    // mm:662:14387
    <div
      className={`${montserrat.variable} ${montserratAlternates.variable} relative flex min-h-svh w-full flex-col overflow-hidden bg-[#00101A] font-montserrat`}
    >
      <HeroBackground />
      <LoginHeader locale={locale} dictionary={dictionary} />
      <LoginContent
        dictionary={dictionary}
        hasError={hasError}
        signInAction={signInWithGoogle}
      />
      <LoginFooter copyright={dictionary.footer.copyright} />
    </div>
  );
}
