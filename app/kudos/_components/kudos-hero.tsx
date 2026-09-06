import Image from "next/image";
import Link from "next/link";

import type { Dictionary } from "@/lib/i18n/dictionaries";

import { IconPen, IconSearch } from "./kudos-icons";

/**
 * mm:2940:13436 (Frame 487) + mm:2940:13437 (A_KV Kudos) + mm:2940:13448
 * (Button chuc nang). Carries the page's ONLY `<h1>` — test-contract.md
 * asserts `getByRole("heading", { level: 1 })` under strict mode, so every
 * downstream section (06/07/08) must use `<h2>`.
 *
 * The compose bar is an `<a>`, not an `<input>` (K-1/K-22: its accessible
 * name equals the placeholder sentence and it links to `/kudos/new`). The
 * Sunner search is a plain GET form to `/profile` (clarifications: the real
 * search-results screen is unbuilt) — no client JavaScript needed.
 */
export function KudosHero({ copy }: { copy: Dictionary["kudos"]["hero"] }) {
  return (
    // mm:2940:13436 (Frame 487) — 144px gutters at the 1440 artboard.
    <section className="relative isolate flex flex-col gap-10 px-6 pt-24 sm:px-12 lg:px-36">
      {/* mm:I2940:13432;2167:5141 (MM_MEDIA_KV Background) */}
      <Image
        src="/images/kudos/kv-background.png"
        alt="Sun* Kudos keyvisual background"
        width={1440}
        height={512}
        priority
        className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[512px] w-full object-cover"
      />
      {/* mm:I2940:13432;1210:12612 (Cover) — readability wash into #00101A. */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[512px] w-full"
        style={{
          background: "linear-gradient(25deg, #00101A 14.74%, rgba(0, 19, 32, 0.00) 47.8%)",
        }}
      />

      {/* 1152px, not 1440 — the section carries the lg:px-36 gutters
          OUTSIDE this cap, same container pattern as award-system-hero.tsx. */}
      <div className="mx-auto flex w-full max-w-[1152px] flex-col gap-10">
        {/* mm:2940:13437 (A_KV Kudos) */}
        <div className="flex flex-col gap-[10px]">
          {/* mm:2940:13439 */}
          <h1 className="text-[28px] leading-[36px] font-bold text-[#FFEA9E] sm:text-[36px] sm:leading-[44px]">
            {copy.title}
          </h1>

          {/* mm:2940:13440 (MM_MEDIA_Kudos logo) — reuses the shipped
              wordmark artwork verbatim (clarifications § New image assets). */}
          <Image
            src="/images/home/kudos-logo.svg"
            alt="KUDOS"
            width={593}
            height={104}
            className="h-auto w-[240px] sm:w-[380px] lg:w-[593px]"
          />
        </div>

        {/* mm:2940:13448 (Button chuc nang) */}
        <div className="flex w-full flex-col gap-8 sm:flex-row sm:items-center">
          {/* mm:2940:13449 (A.1_Button ghi nhận) */}
          <Link
            data-testid="kudos-compose"
            href="/kudos/new"
            className="flex flex-[2] items-center gap-4 rounded-[68px] border border-[#998C5F] bg-[rgba(255,234,158,0.1)] px-4 py-6 text-white transition-colors hover:bg-[rgba(255,234,158,0.18)]"
          >
            {/* mm:I2940:13449;186:2759 (MM_MEDIA_Pen) */}
            <IconPen aria-hidden className="h-6 w-6 shrink-0" />
            <span className="text-base font-bold tracking-[0.15px]">{copy.composePlaceholder}</span>
          </Link>

          {/* mm:2940:13450 (Tìm kiếm sunner) */}
          <form
            action="/profile"
            method="get"
            className="flex flex-1 items-center gap-4 rounded-[68px] border border-[#998C5F] bg-[rgba(255,234,158,0.1)] px-4 py-6"
          >
            {/* mm:I2940:13450;186:2759 (MM_MEDIA_Search) */}
            <IconSearch aria-hidden className="h-6 w-6 shrink-0 text-white" />
            <input
              data-testid="sunner-search"
              type="text"
              name="q"
              maxLength={100}
              placeholder={copy.searchPlaceholder}
              className="w-full bg-transparent text-base font-bold tracking-[0.15px] text-white placeholder:text-white focus:outline-none"
            />
          </form>
        </div>
      </div>
    </section>
  );
}
