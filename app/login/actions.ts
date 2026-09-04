"use server";

import { revalidatePath } from "next/cache";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { createClient } from "@/lib/supabase/server";
import { LOCALE_COOKIE, resolveLocale } from "@/lib/i18n/locales";

/**
 * Kicks off the Google OAuth flow (FR-202, FR-601, BR-001 — no domain
 * allow-list; every Google account is permitted).
 *
 * The server Supabase client does not navigate on its own: it returns the
 * Google consent URL and this action redirects to it. `redirect()` throws
 * `NEXT_REDIRECT` internally, so every call here sits outside any try/catch —
 * wrapping it would swallow the navigation and report a false error instead.
 */
export async function signInWithGoogle(): Promise<void> {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL;
  if (!siteUrl) {
    // Fail fast on a missing env var rather than composing a broken
    // `undefined/auth/callback` redirectTo that Supabase would silently reject.
    throw new Error("NEXT_PUBLIC_SITE_URL is not set");
  }

  const supabase = await createClient();
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: "google",
    options: { redirectTo: `${siteUrl}/auth/callback` },
  });

  if (error || !data.url) {
    redirect("/login?error=oauth_failed");
  }

  redirect(data.url);
}

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
  // Server Components read the locale on render; without this the /login
  // segment can keep serving the cached pre-switch copy (plan risk R4).
  revalidatePath("/login");
}
