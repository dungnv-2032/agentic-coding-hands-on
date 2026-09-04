"use client";

import { useEffect, useId, useRef, useState, useTransition } from "react";

import type { Locale } from "@/lib/i18n/locales";

import { setLocale } from "../actions";
import { IconChevronDown, IconFlagVn } from "./icons";

interface LanguageSelectorProps {
  locale: Locale;
  labels: { language: string; vi: string; en: string };
}

const OPTIONS: Array<{ value: Locale; labelKey: "vi" | "en" }> = [
  { value: "vi", labelKey: "vi" },
  { value: "en", labelKey: "en" },
];

/**
 * Header language selector (E02, clarifications.md). Defaults to VN per
 * BR-003 — flag left, current label, chevron right. The accessible name is
 * built from the current label text ("VN"/"EN") rather than a translated
 * word alone, so it always satisfies /VN|EN|language/i regardless of locale.
 */
export function LanguageSelector({ locale, labels }: LanguageSelectorProps) {
  const [open, setOpen] = useState(false);
  const [, startTransition] = useTransition();
  const rootRef = useRef<HTMLDivElement>(null);
  const listboxId = useId();

  useEffect(() => {
    if (!open) return;

    function onPointerDown(event: PointerEvent) {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
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
    if (value === locale) return;
    startTransition(() => {
      void setLocale(value);
    });
  }

  const currentLabel = locale === "vi" ? labels.vi : labels.en;

  return (
    // mm:I662:14391;186:1696
    <div ref={rootRef} className="relative">
      <button
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listboxId}
        aria-label={`${labels.language}: ${currentLabel}`}
        onClick={() => setOpen((prev) => !prev)}
        className="flex cursor-pointer items-center gap-1 rounded px-4 py-2 text-white transition-colors hover:bg-white/10"
      >
        <IconFlagVn className="h-6 w-6" />
        <span className="text-base font-bold tracking-[0.15px]">
          {currentLabel}
        </span>
        <IconChevronDown
          className={`h-6 w-6 transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>
      {open && (
        <ul
          id={listboxId}
          role="listbox"
          aria-label={labels.language}
          className="absolute right-0 top-full z-30 mt-1 min-w-[108px] overflow-hidden rounded-md bg-[#0B0F12] py-1 shadow-lg"
        >
          {OPTIONS.map((option) => (
            <li key={option.value}>
              <button
                type="button"
                role="option"
                aria-selected={option.value === locale}
                onClick={() => handleSelect(option.value)}
                className="w-full cursor-pointer px-4 py-2 text-left text-base font-bold text-white transition-colors hover:bg-white/10"
              >
                {labels[option.labelKey]}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
