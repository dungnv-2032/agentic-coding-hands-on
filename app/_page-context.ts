import { cookies } from "next/headers";

import { getDictionary } from "@/lib/i18n/dictionaries";
import type { Dictionary } from "@/lib/i18n/dictionaries";
import { LOCALE_COOKIE, resolveLocale } from "@/lib/i18n/locales";
import type { Locale } from "@/lib/i18n/locales";
import { createClient } from "@/lib/supabase/server";

export interface PageContext {
  locale: Locale;
  dictionary: Dictionary;
  isAuthenticated: boolean;
  isAdmin: boolean;
}

/**
 * One shared read for every screen that needs locale + session state — `/`
 * here, and phase 07's placeholder routes (plan.md integration contract).
 * Mirrors `/todo`'s `Promise.all([createClient(), cookies()])` pattern
 * (F001_Login) so the two reads run concurrently rather than serially.
 *
 * Only `isAuthenticated`/`isAdmin` — plain booleans — are safe to forward
 * into a Client Component (`HomeHeader`); the Supabase `user` object never
 * crosses that boundary (A2 assumption, plan.md "Never pass the Supabase
 * user object into a Client Component").
 */
export async function getPageContext(): Promise<PageContext> {
  const [supabase, cookieStore] = await Promise.all([createClient(), cookies()]);
  const {
    data: { user },
  } = await supabase.auth.getUser();

  const locale = resolveLocale(cookieStore.get(LOCALE_COOKIE)?.value);
  const dictionary = getDictionary(locale);

  return {
    locale,
    dictionary,
    isAuthenticated: user !== null,
    isAdmin: user?.app_metadata?.role === "admin",
  };
}
