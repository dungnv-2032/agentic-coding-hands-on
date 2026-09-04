import Image from "next/image";

import type { Dictionary } from "@/lib/i18n/dictionaries";
import type { Locale } from "@/lib/i18n/locales";

import { LanguageSelector } from "./language-selector";

interface LoginHeaderProps {
  locale: Locale;
  dictionary: Dictionary;
}

/**
 * R1 — fixed-top header: non-interactive logo (E01) on the left, the
 * language selector (E02) on the right. `justify-between` keeps that split
 * true at every width, satisfying the "logo top-left / selector top-right
 * at every width" responsive requirement without a breakpoint table.
 */
export function LoginHeader({ locale, dictionary }: LoginHeaderProps) {
  return (
    // mm:662:14391
    <header className="relative z-20 flex w-full items-center justify-between bg-[rgba(11,15,18,0.8)] px-36 py-3">
      {/* mm:I662:14391;178:1033;178:1030 */}
      <Image
        src="/images/login/saa-logo.png"
        alt={dictionary.login.logoAlt}
        width={52}
        height={48}
        preload
      />
      <LanguageSelector
        locale={locale}
        labels={{
          language: dictionary.login.languageLabel,
          vi: dictionary.login.languageVi,
          en: dictionary.login.languageEn,
        }}
      />
    </header>
  );
}
