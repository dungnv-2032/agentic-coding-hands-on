"use client";

import { useEffect, useId, useRef, useState, useTransition } from "react";

import type { Locale } from "@/lib/i18n/locales";

import { setLocale } from "@/app/_actions/locale";
import { IconChevronDown, IconFlagEn, IconFlagVn } from "./icons";

interface LanguageSelectorProps {
  locale: Locale;
  labels: { language: string; vi: string; en: string };
}

/**
 * Each option carries its own flag. The design now HAS an open-state variant
 * (MoMorph `hUyaaugye2`, figma `721:4942` — spec-delta.md §3), so the visual
 * contract below is measured from that node, not invented.
 */
const OPTIONS: Array<{
  value: Locale;
  labelKey: "vi" | "en";
  Flag: typeof IconFlagVn;
}> = [
  { value: "vi", labelKey: "vi", Flag: IconFlagVn },
  { value: "en", labelKey: "en", Flag: IconFlagEn },
];

/**
 * Header language selector (E02, clarifications.md). Defaults to VN per
 * BR-003 — flag left, current label, chevron right. The accessible name is
 * built from the current label text ("VN"/"EN") rather than a translated
 * word alone, so it always satisfies /VN|EN|language/i regardless of locale.
 */
export function LanguageSelector({ locale, labels }: LanguageSelectorProps) {
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const [, startTransition] = useTransition();
  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const optionRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const listboxId = useId();

  // Single focus authority: whenever the panel opens (or the active option
  // changes while it's open), move real DOM focus there. Keeping every
  // Arrow/Home/End handler free of `.focus()` calls avoids a second source
  // of truth fighting this effect.
  useEffect(() => {
    if (!open) return;
    optionRefs.current[activeIndex]?.focus();
  }, [open, activeIndex]);

  useEffect(() => {
    if (!open) return;

    function onPointerDown(event: PointerEvent) {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) {
        // No focus return here — the user aimed somewhere else on the page.
        setOpen(false);
      }
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
        triggerRef.current?.focus();
      }
    }

    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  function handleSelect(value: Locale) {
    setOpen(false);
    triggerRef.current?.focus();
    if (value === locale) return;
    startTransition(() => {
      void setLocale(value);
    });
  }

  function handleListKeyDown(event: React.KeyboardEvent<HTMLDivElement>) {
    const lastIndex = OPTIONS.length - 1;
    switch (event.key) {
      case "ArrowDown":
        event.preventDefault();
        setActiveIndex((prev) => (prev + 1) % OPTIONS.length);
        break;
      case "ArrowUp":
        event.preventDefault();
        setActiveIndex((prev) => (prev - 1 + OPTIONS.length) % OPTIONS.length);
        break;
      case "Home":
        event.preventDefault();
        setActiveIndex(0);
        break;
      case "End":
        event.preventDefault();
        setActiveIndex(lastIndex);
        break;
      default:
        // Enter/Space are intentionally left alone — the native <button>
        // already fires onClick for both, so handling Space here too would
        // double-fire the selection.
        break;
    }
  }

  const currentLabel = locale === "vi" ? labels.vi : labels.en;
  // The flag tracks the SELECTED locale, not the app. Showing the VN flag
  // next to an "EN" label reads as a bug to anyone who switches.
  const CurrentFlag = locale === "vi" ? IconFlagVn : IconFlagEn;

  return (
    // mm:I662:14391;186:1696
    <div ref={rootRef} className="relative">
      <button
        ref={triggerRef}
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listboxId}
        aria-label={`${labels.language}: ${currentLabel}`}
        onClick={() => {
          const next = !open;
          setOpen(next);
          // Opening always re-seeds the active row from the current locale, so
          // focus lands on the selected option rather than wherever the last
          // Arrow-key cycle left it. Kept out of setOpen's updater — React
          // expects that to be a pure function, not a place for side effects.
          if (next) {
            setActiveIndex(OPTIONS.findIndex((o) => o.value === locale));
          }
        }}
        className="flex cursor-pointer items-center gap-1 rounded px-4 py-2 text-white transition-colors hover:bg-white/10"
      >
        <CurrentFlag className="h-6 w-6" />
        <span className="text-base font-bold tracking-[0.15px]">
          {currentLabel}
        </span>
        <IconChevronDown
          className={`h-6 w-6 transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>
      {open && (
        // mm:525:11713 — panel tokens are verbatim from spec-delta.md §3
        <div
          id={listboxId}
          role="listbox"
          aria-label={labels.language}
          onKeyDown={handleListKeyDown}
          className="absolute right-0 top-full z-30 mt-1 flex flex-col rounded-lg border border-[#998C5F] bg-[#00070C] p-1.5"
        >
          {OPTIONS.map((option, index) => {
            const selected = option.value === locale;
            return (
              <button
                key={option.value}
                ref={(el) => {
                  optionRefs.current[index] = el;
                }}
                type="button"
                role="option"
                aria-selected={selected}
                tabIndex={index === activeIndex ? 0 : -1}
                onClick={() => handleSelect(option.value)}
                className={`flex h-14 w-[108px] cursor-pointer items-center justify-center gap-1 rounded-[2px] text-base font-bold leading-6 tracking-[0.15px] text-white transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[#998C5F] ${
                  selected
                    ? "bg-[rgba(255,234,158,0.2)]"
                    : "hover:bg-[rgba(255,234,158,0.08)]"
                }`}
              >
                {/* Decorative: the adjacent label already names the locale, so
                    announcing the flag too would just double up for a reader. */}
                <option.Flag className="h-6 w-6 shrink-0" aria-hidden />
                {labels[option.labelKey]}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
