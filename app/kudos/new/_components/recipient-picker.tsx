"use client";

import Image from "next/image";
import { useRef, useState, type KeyboardEvent } from "react";

import { useDismissOnOutside } from "@/app/_components/use-dismiss-on-outside";
import type { ComposeSunnerOption, RecipientPickerProps } from "@/lib/kudos/compose-contract";

import { foldVietnameseText } from "./use-body-editor-controller";

/**
 * mm:I520:11647;520:9871 (`mms_B_Chọn người nhận`, 672px row, 16px gap) ·
 * mm:I520:11647;520:9873 (`mms_B.2_Search` input shell, componentId
 * `186:2757`, flex-grow, 56px tall, border `#998C5F`, radius 8px, padding
 * 16px/24px, bg white) · mm:I520:11647;520:9873;186:2760 (the search
 * placeholder text node, 16px/700/Montserrat, letter-spacing 0.15px).
 *
 * `recipient-menu`'s shell has no measured node of its own — the companion
 * frame `zJzaC9GgXt` is unpopulated in MoMorph (design/dev status both
 * empty; clarifications.md § Unresolved question 3) — so it's borrowed
 * from `kudos-filter-menu.tsx`'s already-shipped, already-measured listbox
 * (bg `#00070C`, border 1px `#998C5F`, radius 8px, 6px padding), per this
 * phase's own instruction to copy that pattern rather than invent one.
 *
 * Menu-open rule (Key Insight #1, test-contract.md): visible whenever the
 * trimmed query is non-empty, independent of match count — ID-9 fills
 * `@#$%^&`, asserts the menu visible AND zero `role="option"` children.
 * `dismissed` layers Escape/outside-click closing on top of that rule
 * without fighting it: any subsequent keystroke (a new `onQueryChange`)
 * clears it, so typing always reopens the menu.
 */
export function RecipientPicker({
  copy,
  options,
  value,
  query,
  error,
  onQueryChange,
  onSelect,
}: RecipientPickerProps) {
  const [dismissed, setDismissed] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const rootRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const trimmedQuery = query.trim();
  const isOpen = trimmedQuery !== "" && !dismissed;
  // Diacritic-insensitive, same fold as the mention menu's (`ID-33`'s
  // authored test data types unaccented names against accented seed data) —
  // reused rather than a second, possibly-divergent implementation.
  const foldedQuery = foldVietnameseText(trimmedQuery);
  const matches: readonly ComposeSunnerOption[] = isOpen
    ? options.filter((option) => foldVietnameseText(option.fullName).includes(foldedQuery))
    : [];

  useDismissOnOutside(isOpen, rootRef, inputRef, () => {
    setDismissed(true);
    setActiveIndex(-1);
  });

  function handleQueryChange(next: string) {
    onQueryChange(next);
    setDismissed(false);
    setActiveIndex(-1);
  }

  function handleSelect(option: ComposeSunnerOption) {
    onSelect(option);
    setDismissed(true);
    setActiveIndex(-1);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (!isOpen || matches.length === 0) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((index) => Math.min(index + 1, matches.length - 1));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((index) => Math.max(index - 1, 0));
    } else if (event.key === "Enter" && activeIndex >= 0) {
      event.preventDefault();
      handleSelect(matches[activeIndex]);
    }
  }

  return (
    // mm:I520:11647;520:9871
    <div ref={rootRef} className="relative w-full">
      {/* mm:I520:11647;520:9873 */}
      <input
        ref={inputRef}
        id="compose-recipient-input"
        data-testid="recipient-input"
        role="combobox"
        aria-expanded={isOpen}
        aria-controls="compose-recipient-menu"
        aria-invalid={error ? "true" : undefined}
        autoComplete="off"
        placeholder={copy.placeholder}
        value={query}
        onChange={(event) => handleQueryChange(event.target.value)}
        onKeyDown={handleKeyDown}
        className={`h-14 w-full rounded-lg border bg-white px-6 py-4 text-base font-bold tracking-[0.15px] text-[#00101A] outline-none ${
          error ? "border-[#CF1322]" : "border-[#998C5F]"
        }`}
      />
      {value && (
        // mm: no dedicated node — the chosen person, avatar + name, mirrors
        // `sunner-chip.tsx`'s avatar treatment for visual consistency.
        <div data-testid="recipient-selected" className="mt-2 flex items-center gap-2 text-sm text-[#00101A]">
          <Image
            src={value.avatarUrl}
            alt=""
            width={24}
            height={24}
            className="h-6 w-6 shrink-0 rounded-full object-cover"
          />
          <span className="font-semibold">{value.fullName}</span>
        </div>
      )}
      {isOpen && (
        // mm:zJzaC9GgXt (unpopulated companion frame) — shell borrowed from
        // kudos-filter-menu.tsx's measured listbox.
        <div
          id="compose-recipient-menu"
          data-testid="recipient-menu"
          role="listbox"
          className="absolute top-full left-0 z-20 mt-2 max-h-64 w-full overflow-y-auto rounded-lg border border-[#998C5F] bg-[#00070C] p-[6px]"
        >
          {matches.length === 0 ? (
            <p data-testid="recipient-empty" className="p-4 text-sm text-white/70">
              {copy.emptyLabel}
            </p>
          ) : (
            matches.map((option, index) => (
              <button
                key={option.id}
                type="button"
                role="option"
                aria-selected={index === activeIndex}
                onClick={() => handleSelect(option)}
                className={`w-full rounded p-4 text-left text-base leading-6 font-bold tracking-[0.5px] text-white ${
                  index === activeIndex ? "bg-[rgba(255,234,158,0.10)]" : "hover:bg-[rgba(255,234,158,0.05)]"
                }`}
              >
                {option.fullName}
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}
