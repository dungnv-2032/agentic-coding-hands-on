"use client";

import type { ComposeHashtagOption } from "@/lib/kudos/compose-contract";

/**
 * One row of the Hashtag dropdown (MoMorph `p9zO-c4a4x`).
 *
 * Split out of `hashtag-picker.tsx` purely to keep that file under the
 * project's 200-line ceiling — the row owns no state of its own and reports
 * every click straight back up through `onToggle`.
 *
 * mm:1002:13185 (selected: 40px tall, padding `0 16px`, bg
 * `rgba(255,234,158,0.2)`) · mm:1002:13104 (unselected: same box, no fill) ·
 * mm:1002:13204 (the 24×24 check slot at the right edge).
 */

/** mm:1002:13204 — 24×24 circle, dark check on a light disc. */
function HashtagCheckIcon() {
  return (
    <svg
      data-testid="hashtag-check"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="12" fill="#FFFFFF" />
      <path
        d="M7 12.2l3.2 3.3L17 8.8"
        stroke="#00070C"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export interface HashtagOptionRowProps {
  option: ComposeHashtagOption;
  isSelected: boolean;
  /** True once `MAX_HASHTAGS` are selected — only gates UNSELECTED rows. */
  atLimit: boolean;
  onToggle: (option: ComposeHashtagOption, isSelected: boolean) => void;
}

export function HashtagOptionRow({
  option,
  isSelected,
  atLimit,
  onToggle,
}: HashtagOptionRowProps) {
  return (
    <button
      type="button"
      role="option"
      aria-selected={isSelected}
      data-selected={isSelected ? "true" : undefined}
      // FR-210: at the cap only the UNSELECTED rows go inert. A selected row
      // stays clickable — it is the only way back out of a full selection.
      disabled={!isSelected && atLimit}
      onClick={() => onToggle(option, isSelected)}
      className={`flex h-10 w-full items-center justify-between gap-0.5 rounded px-4 text-left text-base leading-6 font-bold tracking-[0.15px] text-white ${
        isSelected
          ? "bg-[rgba(255,234,158,0.2)]"
          : atLimit
            ? "opacity-50"
            : "hover:bg-white/10"
      }`}
    >
      <span>#{option.name}</span>
      {/*
        The slot is always rendered, empty when unselected, so the list never
        reflows as selection changes (frame item A.2, verbatim: "khoảng trống
        24x24px (không có icon) khi unselected").
      */}
      <span
        data-testid="hashtag-check-slot"
        className="flex h-6 w-6 shrink-0 items-center justify-center"
      >
        {isSelected && <HashtagCheckIcon />}
      </span>
    </button>
  );
}
