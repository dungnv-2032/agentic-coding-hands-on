import type { Metadata } from "next";
import { cookies } from "next/headers";
import "./globals.css";

import { LOCALE_COOKIE, resolveLocale } from "@/lib/i18n/locales";

import { montserrat, montserratAlternates } from "./_fonts";

export const metadata: Metadata = {
  title: "Sun* Annual Awards 2025",
  description:
    "Sun* Annual Awards 2025 — Root Further: hệ thống giải thưởng, Sun* Kudos và toàn bộ thông tin sự kiện SAA 2025.",
};

/**
 * `lang` tracks the locale the page is actually rendered in. It was hardcoded
 * to "en" while the app's default locale is "vi" and the header lets the user
 * switch — so screen readers picked the wrong pronunciation and search engines
 * were told the wrong language for every page.
 */
export default async function RootLayout({ children }: LayoutProps<"/">) {
  const cookieStore = await cookies();
  const locale = resolveLocale(cookieStore.get(LOCALE_COOKIE)?.value);

  return (
    <html
      lang={locale}
      className={`${montserrat.variable} ${montserratAlternates.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
