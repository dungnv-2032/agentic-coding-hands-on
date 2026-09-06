"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { RefObject } from "react";

/**
 * Scroll-spy + programmatic navigation for the award category menu (ALG-001).
 * Split out of `award-category-nav.tsx` to keep both files inside the 200-line
 * cap; the nav owns presentation, this owns geometry and timing.
 */

/**
 * Used until the header has been measured, and pinned again at `lg` by
 * `lg:[--award-header-offset:112px]` on the page wrapper. Keeping the desktop
 * value in the cascade rather than in this measurement is deliberate: it makes
 * the `lg` geometry the tester pinned unchangeable by anything that happens at
 * runtime.
 */
const FALLBACK_HEADER_OFFSET = 112;

/** Air between the sticky header's bottom edge and the card title it clears. */
const HEADER_BREATHING_ROOM = 40;

/** Ceiling on how long a click owns the active state when nothing interrupts. */
const SCROLL_SETTLE_MS = 700;

/** Bottom of the "which card am I on" band — mirrors the -55% rootMargin. */
const BAND_BOTTOM_RATIO = 0.45;

export function useAwardScrollSpy(slugKey: string, scopeRef: RefObject<HTMLElement | null>) {
  const [activeSlug, setActiveSlug] = useState(slugKey.split(",")[0] ?? "");
  const clickLock = useRef(false);
  const lockTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  /**
   * The offset actually in effect for this subtree. Read from the cascade, not
   * recomputed, so CSS stays the single source: `lg` resolves to the pinned
   * 112px, everything below resolves to the measured header height.
   */
  const readOffset = useCallback(() => {
    const scope = scopeRef.current;
    if (!scope) return FALLBACK_HEADER_OFFSET;
    const raw = Number.parseFloat(
      getComputedStyle(scope).getPropertyValue("--award-header-offset"),
    );
    return Number.isFinite(raw) ? raw : FALLBACK_HEADER_OFFSET;
  }, [scopeRef]);

  /**
   * W-1 — `home-header.tsx` and `home-nav.tsx` are both `flex-wrap`, so below
   * `lg` the sticky header stacks to several times its desktop height and one
   * pinned offset parks the card title behind it. Rather than pin three
   * guessed numbers, publish the header's real measured height and let the
   * wrapper's `lg:` class override it where the desktop value is already
   * proven.
   */
  useEffect(() => {
    const header = document.querySelector("header");
    if (!header) return;
    const publish = () => {
      const offset = Math.round(header.getBoundingClientRect().height) + HEADER_BREATHING_ROOM;
      document.documentElement.style.setProperty("--award-header-offset", `${offset}px`);
    };
    publish();
    // Watches the header itself, so a wrap caused by rotation or a font swap
    // is caught as directly as one caused by a viewport resize.
    const resizeObserver = new ResizeObserver(publish);
    resizeObserver.observe(header);
    return () => {
      resizeObserver.disconnect();
      document.documentElement.style.removeProperty("--award-header-offset");
    };
  }, []);

  /**
   * W-2 — resolve the active item from live geometry across ALL sections.
   * The observer callback only ever sees the entries that changed in that
   * batch, sampled at change time; under a fast flick that batch can rank a
   * section which has already left the band.
   */
  const resolveActive = useCallback(() => {
    const bandTop = readOffset();
    const bandBottom = window.innerHeight * BAND_BOTTOM_RATIO;
    let best: { slug: string; distance: number } | null = null;
    for (const slug of slugKey.split(",")) {
      const rect = document.getElementById(slug)?.getBoundingClientRect();
      if (!rect || rect.bottom <= bandTop || rect.top >= bandBottom) continue;
      const distance = Math.abs(rect.top - bandTop);
      if (!best || distance < best.distance) best = { slug, distance };
    }
    if (best) {
      setActiveSlug(best.slug);
      return;
    }
    // No card in the band. Above the first section — i.e. the hero still fills
    // the band — the frame lights the first item, so fall back to it rather
    // than retaining whichever card the user last scrolled past on the way up.
    // Below the last section (footer) there is nothing to fall back to, so keep
    // the current item. Either branch leaves something active, so the
    // "exactly one" invariant ID-9/11 asserts never drops to zero.
    const slugs = slugKey.split(",");
    const firstSlug = slugs[0] ?? "";
    const firstTop = document.getElementById(firstSlug)?.getBoundingClientRect().top;
    if (firstTop !== undefined && firstTop >= bandBottom) setActiveSlug(firstSlug);
  }, [slugKey, readOffset]);

  /**
   * W-2 — the lock used to expire on a bare timer while the callback threw
   * away everything it saw. Because `IntersectionObserver` only fires on
   * *change*, a scroll that ended inside the window left the menu lit on the
   * clicked item forever. Releasing hands the active state straight back to
   * measured geometry.
   */
  const releaseLock = useCallback(() => {
    if (!clickLock.current) return;
    clickLock.current = false;
    if (lockTimer.current) {
      clearTimeout(lockTimer.current);
      lockTimer.current = null;
    }
    resolveActive();
  }, [resolveActive]);

  // A wheel, touch or key scroll during the settle window means the user
  // overrode the click — the wheel is now the most recent input (BR-002).
  useEffect(() => {
    const passive = { passive: true } as const;
    window.addEventListener("wheel", releaseLock, passive);
    window.addEventListener("touchstart", releaseLock, passive);
    window.addEventListener("keydown", releaseLock);
    return () => {
      window.removeEventListener("wheel", releaseLock);
      window.removeEventListener("touchstart", releaseLock);
      window.removeEventListener("keydown", releaseLock);
    };
  }, [releaseLock]);

  // Deep link (`/awards-information#mvp`): land on the card explicitly, so the
  // arrival position does not depend on native-anchor timing. The hash is
  // matched against the frozen slug list before it reaches the DOM, so an
  // attacker-supplied fragment selects nothing. Unknown fragment: silent
  // no-op. This effect only scrolls; the observer seeds the active item.
  useEffect(() => {
    const slug = window.location.hash.slice(1);
    if (!slug || !slugKey.split(",").includes(slug)) return;
    document.getElementById(slug)?.scrollIntoView({ behavior: "auto", block: "start" });
  }, [slugKey]);

  useEffect(() => {
    const targets = slugKey
      .split(",")
      .map((slug) => document.getElementById(slug))
      .filter((element): element is HTMLElement => element !== null);
    if (targets.length === 0) return;

    const observer = new IntersectionObserver(
      () => {
        if (clickLock.current) return;
        resolveActive();
      },
      { rootMargin: `-${readOffset()}px 0px -55% 0px`, threshold: 0 },
    );
    targets.forEach((target) => observer.observe(target));
    return () => observer.disconnect();
  }, [slugKey, readOffset, resolveActive]);

  useEffect(
    () => () => {
      if (lockTimer.current) clearTimeout(lockTimer.current);
    },
    [],
  );

  /** Returns false when the slug has no section, so the caller can fall back
   *  to the browser's own anchor handling instead of swallowing the click. */
  const activate = useCallback(
    (slug: string) => {
      const target = document.getElementById(slug);
      if (!target) return false;
      const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

      setActiveSlug(slug);
      clickLock.current = true;
      target.scrollIntoView({ behavior: reduced ? "auto" : "smooth", block: "start" });
      // `replace`, never `push` — the back button stays on the previous page.
      window.history.replaceState(null, "", `#${slug}`);

      if (lockTimer.current) clearTimeout(lockTimer.current);
      lockTimer.current = setTimeout(releaseLock, reduced ? 0 : SCROLL_SETTLE_MS);
      return true;
    },
    [releaseLock],
  );

  return { activeSlug, activate };
}
