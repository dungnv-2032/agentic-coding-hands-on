"use client";

import { useCallback, useRef } from "react";
import type { MouseEvent } from "react";

import { IconTarget } from "./award-system-icons";
import { useAwardScrollSpy } from "./use-award-scroll-spy";

export interface AwardNavItem {
  slug: string;
  label: string;
}

interface AwardCategoryNavProps {
  items: AwardNavItem[];
  ariaLabel: string;
}

/**
 * mm:313:8459 (mms_C_Menu list) — six anchors, each `MM_MEDIA_Target` + label,
 * active one gold with a gold underline (mm:313:8460), the rest white
 * (mm:313:8461 …). The only Client Component on this screen.
 *
 * Hydration safety: the first client render must match the server's byte for
 * byte or React logs a console error, and the suite fails on ANY console
 * error. So the initial active item is always `items[0]`, and
 * `location.hash` / `matchMedia` / `history` are touched only inside effects
 * and handlers — never during render. Geometry and timing live in
 * `useAwardScrollSpy`.
 *
 * `aria-current` is present-or-absent rather than "true"/"false": the suite
 * counts `[aria-current="true"]` inside this nav and expects exactly one.
 * Since `activeSlug` is a single value, that is an invariant of the state
 * shape, not a cleanup step.
 */
export function AwardCategoryNav({ items, ariaLabel }: AwardCategoryNavProps) {
  const navRef = useRef<HTMLElement | null>(null);
  const slugKey = items.map((item) => item.slug).join(",");
  const { activeSlug, activate } = useAwardScrollSpy(slugKey, navRef);

  const handleClick = useCallback(
    (event: MouseEvent<HTMLAnchorElement>, slug: string) => {
      // A modified click is a request to open the award in a new tab/window
      // already scrolled to it — a legitimate use of the real `href`, so hand
      // it to the browser untouched rather than scrolling this tab instead.
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      if (event.button !== 0) return;
      // Only cancel the browser's own jump once we know we have the target.
      if (activate(slug)) event.preventDefault();
    },
    [activate],
  );

  return (
    // mm:313:8459 — sticky column at `lg`, a scrollable row below it. The
    // sticky offset reads the same custom property the sections use for their
    // scroll margin, so the menu and the scroll target can never disagree
    // about where the header ends.
    <nav
      ref={navRef}
      data-testid="award-nav"
      aria-label={ariaLabel}
      style={{ top: "var(--award-header-offset, 112px)" }}
      className="flex w-full gap-4 overflow-x-auto lg:sticky lg:w-[178px] lg:shrink-0 lg:flex-col lg:self-start lg:overflow-visible"
    >
      {items.map((item) => {
        const isActive = item.slug === activeSlug;
        return (
          // mm:313:8460 (active variant `186:1501`) / mm:313:8461 (rest `186:1433`)
          <a
            key={item.slug}
            href={`#${item.slug}`}
            data-testid={`award-nav-${item.slug}`}
            aria-current={isActive ? "true" : undefined}
            onClick={(event) => handleClick(event, item.slug)}
            className={`flex shrink-0 items-center gap-1 border-b p-4 text-sm leading-5 font-bold tracking-[0.25px] transition-colors duration-200 ease-out focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FFEA9E] ${
              isActive
                ? "border-[#FFEA9E] text-[#FFEA9E] [text-shadow:0_4px_4px_rgba(0,0,0,0.25),0_0_6px_#FAE287]"
                : "rounded border-transparent text-white hover:text-[#FFEA9E]"
            }`}
          >
            <IconTarget aria-hidden className="h-6 w-6 shrink-0" />
            {item.label}
          </a>
        );
      })}
    </nav>
  );
}
