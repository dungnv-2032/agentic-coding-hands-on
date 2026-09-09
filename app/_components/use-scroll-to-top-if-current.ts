"use client";

import { usePathname } from "next/navigation";
import type { MouseEvent } from "react";

/**
 * Swallows a `<Link>` click and smooth-scrolls to top instead of navigating.
 * Only ever attach this when the link already points at the current route
 * (spec A1.2 / DEC-001, test cases ID-18, ID-19, ID-20).
 *
 * The condition is the whole point. Header logo, footer logo and the three
 * nav items all want this behaviour, and the two logos originally applied it
 * unconditionally — which turned "back to home" into a dead end on every
 * route that reuses the header and footer (the ComingSoon placeholders).
 * Three separate copies of the same five lines is how that divergence
 * happened, so the behaviour lives here once.
 */
export function scrollToTopHandler(event: MouseEvent<HTMLAnchorElement>) {
  event.preventDefault();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

/**
 * The route-aware form, for a single fixed `href` (the header and footer
 * logos). Returns `undefined` off-route so the Link navigates normally.
 *
 * `HomeNav` deliberately does NOT use this: it already reads `usePathname()`
 * for `aria-current` and its per-item state, and calling a hook inside its
 * `.map()` would be a hook in a loop. It composes `scrollToTopHandler` with
 * its own `selected` check instead — same behaviour, one source.
 */
export function useScrollToTopIfCurrent(href: string) {
  const pathname = usePathname();
  return pathname === href ? scrollToTopHandler : undefined;
}
