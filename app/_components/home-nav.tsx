"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import type { Dictionary } from "@/lib/i18n/dictionaries";

import { scrollToTopHandler } from "@/app/_components/use-scroll-to-top-if-current";

/**
 * R1 nav (`mms_A1.2/.3/.5`, node `I2167:9091;178:653`, gap 24px).
 *
 * The three nav items are ONE component in Figma with three captured states —
 * selected (`186:1579`), hover (`186:1587`) and normal (`186:1593`). The frame
 * happens to snapshot "About SAA 2025" in the selected state because the frame
 * IS the homepage; that is a property of the route, not of the item. So the
 * selected state is derived from `usePathname()` rather than hardcoded: on
 * `/awards-information` the second item is the selected one, and on the
 * placeholder routes "About SAA 2025" is a normal link that actually navigates
 * home (ID-3, ID-20 — "from any page, click About SAA 2025" must reach `/`).
 *
 * Only the ALREADY-selected item swallows its click to scroll to top (spec
 * A1.2, DEC-001). Doing that unconditionally would have stranded every
 * placeholder route with a dead link home.
 *
 * Award Information / Sun* Kudos share Figma component `186:1433` with the
 * language selector's own trigger button (`I2167:9091;186:1696;186:1821`),
 * and the frame's static export carries no captured hover-fill on that
 * component. Reusing `hover:bg-white/10` — the token already approved for
 * that same shared component in `language-selector.tsx` — satisfies the
 * hover highlight (ID-23) without inventing a new value.
 */
const SELECTED_CLASS =
  "flex items-center gap-1 border-b border-[#FFEA9E] px-4 py-4 text-sm font-bold tracking-[0.1px] text-[#FFEA9E] [text-shadow:0_4px_4px_rgba(0,0,0,0.25),0_0_6px_#FAE287]";

const NORMAL_CLASS =
  "rounded px-4 py-4 text-sm font-bold tracking-[0.1px] text-white transition-colors hover:bg-white/10";

// mm:I2167:9091;186:1579 / ;186:1587 / ;186:1593 — one component, three states.
const ITEMS = [
  { href: "/", labelKey: "about" },
  { href: "/awards-information", labelKey: "awardInformation" },
  { href: "/kudos", labelKey: "kudos" },
] as const satisfies ReadonlyArray<{
  href: string;
  labelKey: keyof Dictionary["header"];
}>;

export function HomeNav({ dictionary }: { dictionary: Dictionary }) {
  const pathname = usePathname();

  return (
    // mm:I2167:9091;178:653 — desktop gap is 24px in one row; below `lg` the
    // three items alone measure 333px (min-content, links don't wrap
    // internally), wider than a 375px viewport, so the row must wrap onto
    // multiple lines instead of overflowing (was: nowrap, scrollWidth > 375).
    <nav className="flex flex-wrap items-center gap-x-3 gap-y-1 sm:gap-6">
      {ITEMS.map((item) => {
        const selected = pathname === item.href;
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={selected ? "page" : undefined}
            onClick={selected ? scrollToTopHandler : undefined}
            className={selected ? SELECTED_CLASS : NORMAL_CLASS}
          >
            {dictionary.header[item.labelKey]}
          </Link>
        );
      })}
    </nav>
  );
}
