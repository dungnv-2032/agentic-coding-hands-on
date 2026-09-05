"use client";

import Image from "next/image";
import Link from "next/link";

import type { Dictionary } from "@/lib/i18n/dictionaries";

import { useScrollToTopIfCurrent } from "@/app/_components/use-scroll-to-top-if-current";

/**
 * Item 7 — footer (`mms_7_Footer`, node `5001:14800`). A real `<footer>` so
 * `getByRole("contentinfo")` resolves (test-contract.md). Nav labels reuse
 * `dictionary.header.*` ("About SAA 2025" / "Award Information" / "Sun*
 * Kudos" — same copy, DRY) rather than duplicating strings under `footer.*`.
 *
 * The frame happens to capture "Award Information" in its component's
 * selected-state variant (clarifications.md, "Resolved from source data").
 * The footer carries no current-page indication here, and always showing
 * that highlight would misrepresent every other route that reuses this
 * footer (phase 07's placeholders) — so all four nav links share one plain
 * style instead of replicating that one frame's captured state verbatim.
 */
export function SiteFooter({ dictionary }: { dictionary: Dictionary }) {
  const { header, footer } = dictionary;
  const scrollToTopIfHome = useScrollToTopIfCurrent("/");

  const linkClassName =
    "rounded px-4 py-4 text-base leading-6 font-bold tracking-[0.15px] text-white transition-colors hover:bg-white/10";

  return (
    // mm:5001:14800
    <footer className="flex w-full flex-col items-center justify-between gap-6 border-t border-[#2E3940] px-6 py-10 sm:flex-row sm:px-12 lg:px-[90px]">
      {/* mm:I5001:14800;342:1407 (Frame 488) */}
      <div className="flex flex-wrap items-center justify-center gap-6 sm:gap-20">
        {/* mm:I5001:14800;342:1408 (mms_7.1_LOGO) — click logo scrolls to top (spec item 7) */}
        <Link
          href="/"
          aria-label={header.logoAlt}
          onClick={scrollToTopIfHome}
          className="flex h-16 items-start"
        >
          <Image src="/images/home/footer-saa-logo.png" alt={header.logoAlt} width={69} height={64} />
        </Link>
        {/* mm:I5001:14800;342:1409 (Frame 476) */}
        <nav className="flex flex-wrap items-center gap-2 sm:gap-6">
          <Link href="/" className={linkClassName}>
            {header.about}
          </Link>
          <Link href="/awards-information" className={linkClassName}>
            {header.awardInformation}
          </Link>
          <Link href="/kudos" className={linkClassName}>
            {header.kudos}
          </Link>
          <Link href="/standards" className={linkClassName}>
            {footer.standards}
          </Link>
        </nav>
      </div>
      {/* mm:I5001:14800;342:1413 */}
      <p className="text-sm leading-6 font-bold text-white">{footer.copyright}</p>
    </footer>
  );
}
