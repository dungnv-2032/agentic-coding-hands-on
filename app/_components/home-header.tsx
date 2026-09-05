"use client";

import Image from "next/image";
import Link from "next/link";

import type { Dictionary } from "@/lib/i18n/dictionaries";
import type { Locale } from "@/lib/i18n/locales";

import { LanguageSelector } from "@/app/_components/language-selector";
import { HomeNav } from "@/app/_components/home-nav";
import { NotificationBell } from "@/app/_components/notification-bell";
import { AccountMenu } from "@/app/_components/account-menu";
import { useScrollToTopIfCurrent } from "@/app/_components/use-scroll-to-top-if-current";

interface HomeHeaderProps {
  locale: Locale;
  dictionary: Dictionary;
  isAuthenticated: boolean;
  isAdmin: boolean;
  signOutAction: () => Promise<void>;
}

/**
 * R1 header shell (`mms_A1_Header`, node `2167:9091`) — sticky at the top
 * of the 4480px-tall homepage; `banner` landmark since it renders at the
 * page root. Left cluster: logo + nav (`I2167:9091;186:2166`, gap 64px).
 * Right cluster: bell / language / account (`I2167:9091;186:1601`, gap
 * 16px), in the design's own left-to-right order (bell startX 1148 <
 * language 1204 < account 1328). Bell and account are absent from the DOM
 * (not just hidden) when `isAuthenticated` is false — BR-002.
 */
export function HomeHeader({
  locale,
  dictionary,
  isAuthenticated,
  isAdmin,
  signOutAction,
}: HomeHeaderProps) {
  const scrollToTopIfHome = useScrollToTopIfCurrent("/");
  return (
    // mm:2167:9091 — bg rgba(16,20,23,.8), padding 12px 144px, gap 238px (space-between)
    // (desktop values only — 144px padding with a non-wrapping row is the
    // one Figma frame's captured desktop width; below `lg` the row wraps
    // onto its own line and padding shrinks like every other section's
    // `px-6 sm:px-12 lg:px-36` scale, so the cluster never pushes past the
    // viewport (was: fixed px-36 overflowing to scrollWidth 653 at 375px)).
    <header className="sticky top-0 z-20 flex w-full flex-wrap items-center justify-between gap-x-4 gap-y-2 bg-[rgba(16,20,23,0.8)] px-6 py-3 sm:px-12 lg:px-36">
      <div className="flex flex-wrap items-center gap-4 sm:gap-16">
        {/* mm:I2167:9091;178:1033;178:1030 — byte-identical to /login (asset-manifest.md) */}
        <Link
          href="/"
          aria-label={dictionary.header.logoAlt}
          onClick={scrollToTopIfHome}
        >
          <Image
            src="/images/login/saa-logo.png"
            alt={dictionary.header.logoAlt}
            width={52}
            height={48}
            preload
          />
        </Link>
        <HomeNav dictionary={dictionary} />
      </div>
      <div className="ml-auto flex flex-wrap items-center gap-4">
        {isAuthenticated && <NotificationBell dictionary={dictionary} />}
        <LanguageSelector
          locale={locale}
          labels={{
            language: dictionary.login.languageLabel,
            vi: dictionary.login.languageVi,
            en: dictionary.login.languageEn,
          }}
        />
        {isAuthenticated && (
          <AccountMenu
            dictionary={dictionary}
            isAdmin={isAdmin}
            signOutAction={signOutAction}
          />
        )}
      </div>
    </header>
  );
}
