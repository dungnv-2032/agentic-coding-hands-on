"use server";

import { revalidatePath } from "next/cache";
import { cookies } from "next/headers";

import { LOCALE_COOKIE, resolveLocale } from "@/lib/i18n/locales";

/**
 * Persists the selected UI locale (FR-203 / BR-003). Invalid input falls
 * back to the default locale via `resolveLocale` rather than writing raw
 * user input into the cookie.
 */
export async function setLocale(locale: string): Promise<void> {
  const next = resolveLocale(locale);
  const cookieStore = await cookies();
  cookieStore.set(LOCALE_COOKIE, next, {
    path: "/",
    maxAge: 60 * 60 * 24 * 365,
    sameSite: "lax",
  });
  // Server Components read the locale on render. This action is now shared
  // between `/login` and `/` (both render locale-dependent copy), so the
  // revalidation widens from the old `/login`-only path to the whole layout
  // subtree — otherwise the homepage would keep serving pre-switch copy
  // after a language change (plan risk R3/R4).
  revalidatePath("/", "layout");
}
