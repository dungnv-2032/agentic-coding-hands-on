"use client";

import { useRef, useState } from "react";

import { useDismissOnOutside } from "@/app/_components/use-dismiss-on-outside";
import { HashtagOptionRow } from "./hashtag-option-row";
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
 * The list is a stateful multi-select, per the companion frame and
 * `plans/260911-0707-dropdown-list-hashtag/spec/.../spec-delta.md`
 * (promoted as FR-208..FR-212): a row carries its own selected state, a
 * click toggles it in both directions, and at the cap the UNSELECTED rows
 * go `disabled` with "Tối đa 5 hashtag" standing as the reason. This
 * supersedes the earlier add-only note here — ID-17/ID-53 used to click
 * `options.first()`, which at the cap is an already-selected row and under
 * toggle semantics means "deselect"; they now target an unselected row,
 * which is what "a 6th hashtag" actually means.
 *
 * The reducer (`compose-state.ts`, frozen) remains the only place
 * `MAX_HASHTAGS` is truly enforced; `disabled` is the display layer in
 * front of it, never a replacement for it. The menu still closes on every
 * toggle (ID-16's loop clicks `hashtag-add` again each round and awaits
 * `hashtag-menu` visible, which would fail if a second click merely
 * toggled an already-open menu shut). Row order stays `hashtags.position`
 * as Supabase returns it — selecting never re-sorts the list.
 */
// `error` stays in the props for contract parity but is deliberately not
// destructured — see the `atLimit` block below for why the cap, not the prop,
// drives `hashtag-error`.
export function HashtagPicker({ copy, options, selected, onAdd, onRemove }: HashtagPickerProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  useDismissOnOutside(menuOpen, rootRef, triggerRef, () => setMenuOpen(false));

  function handleOptionClick(option: ComposeHashtagOption, isSelected: boolean) {
    // FR-209: one row, both directions. The reducer owns `MAX_HASHTAGS`; this
    // only routes the click to the callback the frozen contract already gives us.
    if (isSelected) onRemove(option.id);
    else onAdd(option);
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
                  <HashtagOptionRow
                    option={option}
                    isSelected={isSelected}
                    atLimit={atLimit}
                    onToggle={handleOptionClick}
                  />
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

      {/*
        FR-211: derived from the count, never from the `error` prop. The frozen
        reducer's `removeHashtag` never clears `hashtagError`, so a stale
        `"tooMany"` would pin this message on screen after the user drops back
        to four. Here the message is the standing reason the unselected rows are
        inert, so it must appear and disappear exactly with the cap.
      */}
      {atLimit && (
        <p data-testid="hashtag-error" className="text-sm font-semibold text-[#D4271D]">
          {copy.maxError}
        </p>
      )}
    </div>
  );
}
