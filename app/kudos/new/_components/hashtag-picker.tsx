"use client";

import { useRef, useState } from "react";

import { useDismissOnOutside } from "@/app/_components/use-dismiss-on-outside";
import { MAX_HASHTAGS, type ComposeFieldErrorCode, type ComposeHashtagOption } from "@/lib/kudos/compose-contract";

/**
 * `lib/kudos/compose-contract.ts`'s `HashtagPickerCopy` is `{ addLabel: string }`
 * only — it has no slot for the "Tối đa 5 hashtag" cap-error string that
 * `ImagePickerCopy` gets via its own `invalidTypeError` field. That's a gap,
 * not a design choice (surfaced to the orchestrator per phase-10.md § Next
 * Steps): hashtag's second error (`tooMany`) is exactly analogous to image's
 * `invalidType` and needs the same per-component copy slot. This file's own
 * `HashtagPickerCopy` — a `Dictionary["kudosCompose"]` slice, per
 * test-contract.md § Blueprint ratification → Copy plumbing — adds that one
 * field; `compose-form.tsx` (phase 11) builds it from the resolved
 * dictionary via `buildHashtagPickerCopy`.
 */
export interface HashtagPickerCopy {
  /** Contains both "Hashtag" and "Tối đa 5" (test-contract.md § Hashtags). */
  addLabel: string;
  /** `errors.tooMany` — "Tối đa 5 hashtag" verbatim (ID-17, ID-53). */
  maxError: string;
}

export function buildHashtagPickerCopy(copy: {
  buttons: { addHashtag: string; max: string };
  errors: Record<ComposeFieldErrorCode, string>;
}): HashtagPickerCopy {
  return { addLabel: `${copy.buttons.addHashtag} ${copy.buttons.max}`, maxError: copy.errors.tooMany };
}

export interface HashtagPickerProps {
  copy: HashtagPickerCopy;
  options: readonly ComposeHashtagOption[];
  selected: readonly ComposeHashtagOption[];
  /** `"tooMany"` renders `hashtag-error`; any other value is ignored here. */
  error?: ComposeFieldErrorCode;
  onAdd: (option: ComposeHashtagOption) => void;
  onRemove: (id: number) => void;
}

/**
 * mm:I520:11647;662:8595 (`mms_E.2_Tag Group`, 548px row) ·
 * mm:I520:11647;662:8911 (add button, 48px tall, border `#998C5F`, radius
 * 8px, bg white) · mm:1002:13102 (companion `Dropdown-List`, 318px, border
 * `#998C5F`, radius 8px, padding 6px, bg `#00070C`) · mm:1002:13185 (a
 * selected row, 40px tall, bg `rgba(255,234,158,0.2)`) · mm:1002:13104 (an
 * unselected row, no fill).
 *
 * Options are add-only and never `disabled` (test-contract.md § Blueprint
 * ratification item 5) — the companion frame's own toggle/disable spec
 * cannot satisfy ID-17/ID-53, which click an already-selected row at the
 * cap and expect the error with the chip count unchanged. The reducer
 * (`compose-state.ts`, frozen) is the only place `MAX_HASHTAGS` is
 * enforced; this component never re-implements that check. The menu closes
 * on every selection (ID-16's loop clicks `hashtag-add` again each round
 * and awaits `hashtag-menu` visible, which would fail if a second click
 * merely toggled an already-open menu shut).
 */
export function HashtagPicker({ copy, options, selected, error, onAdd, onRemove }: HashtagPickerProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  useDismissOnOutside(menuOpen, rootRef, triggerRef, () => setMenuOpen(false));

  function handleOptionClick(option: ComposeHashtagOption) {
    onAdd(option);
    setMenuOpen(false);
  }

  const atLimit = selected.length >= MAX_HASHTAGS;

  return (
    <div ref={rootRef} className="flex flex-col gap-2">
      {/* mm:I520:11647;662:8595 */}
      <div className="relative flex flex-wrap items-center gap-2">
        <button
          ref={triggerRef}
          type="button"
          data-testid="hashtag-add"
          onClick={() => setMenuOpen((open) => !open)}
          // mm:I520:11647;662:8911
          className="flex h-12 items-center gap-2 rounded-lg border border-[#998C5F] bg-white px-2 text-left text-[11px] leading-4 font-bold tracking-[0.5px] text-[#999]"
        >
          {copy.addLabel}
        </button>

        {menuOpen && (
          // mm:1002:13102
          <ul
            role="listbox"
            data-testid="hashtag-menu"
            className="absolute top-full left-0 z-10 mt-2 flex w-[318px] flex-col gap-0.5 rounded-lg border border-[#998C5F] bg-[#00070C] p-1.5"
          >
            {options.map((option) => {
              const isSelected = selected.some((tag) => tag.id === option.id);
              return (
                <li key={option.id}>
                  <button
                    type="button"
                    role="option"
                    aria-selected={isSelected}
                    data-selected={isSelected ? "true" : undefined}
                    onClick={() => handleOptionClick(option)}
                    // mm:1002:13185 (selected) / mm:1002:13104 (unselected)
                    className={`h-10 w-full rounded px-4 text-left text-base leading-6 font-bold tracking-[0.15px] text-white ${
                      isSelected ? "bg-[rgba(255,234,158,0.2)]" : atLimit ? "opacity-50" : ""
                    }`}
                  >
                    #{option.name}
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      {selected.length > 0 && (
        <div className="flex flex-wrap items-center gap-3">
          {selected.map((tag) => (
            // mm:app/kudos/_components/kudos-hashtag-row.tsx (shipped chip text style)
            <span
              key={tag.id}
              data-testid="hashtag-chip"
              className="flex items-center gap-1 text-base leading-6 font-bold tracking-[0.5px] text-[#D4271D]"
            >
              #{tag.name}
              <button
                type="button"
                data-testid="hashtag-chip-remove"
                aria-label={`Remove #${tag.name}`}
                onClick={() => onRemove(tag.id)}
                className="text-[#D4271D]"
              >
                ✕
              </button>
            </span>
          ))}
        </div>
      )}

      {error === "tooMany" && (
        <p data-testid="hashtag-error" className="text-sm font-semibold text-[#D4271D]">
          {copy.maxError}
        </p>
      )}
    </div>
  );
}
