"use client";

import Image from "next/image";
import { useRef, type RefObject } from "react";

import { useDismissOnOutside } from "@/app/_components/use-dismiss-on-outside";
import type { ComposeSunnerOption } from "@/lib/kudos/compose-contract";

/**
 * `@mention` autocomplete (test-contract.md § Mentions, ID-12/13/33).
 *
 * No dedicated MoMorph node exists for this menu — it is a real behavior
 * (clarifications.md § Rich text) with no companion frame at all, unlike the
 * recipient dropdown which at least has an empty placeholder frame
 * (`zJzaC9GgXt`). Shell borrowed from the same already-measured listbox
 * `recipient-picker.tsx` uses (bg `#00070C`, border 1px `#998C5F`, radius
 * 8px, 6px padding) for visual consistency across the two autocompletes on
 * this screen, per this phase's own instruction to reuse rather than invent.
 *
 * `open`/`options` are driven entirely by the parent (`mentionQuery`/
 * `mentionOptions` in the frozen `BodyEditorProps`) — this component never
 * runs the trailing-`@` regex itself; it only renders what it is given and
 * reports dismissal/selection back up.
 */
export interface MentionMenuProps {
  open: boolean;
  options: readonly ComposeSunnerOption[];
  onSelect: (option: ComposeSunnerOption) => void;
  onDismiss: () => void;
  anchorRef: RefObject<HTMLTextAreaElement | null>;
}

export function MentionMenu({ open, options, onSelect, onDismiss, anchorRef }: MentionMenuProps) {
  const rootRef = useRef<HTMLDivElement>(null);
  useDismissOnOutside(open, rootRef, anchorRef, onDismiss);

  if (!open) return null;

  return (
    <div
      ref={rootRef}
      data-testid="mention-menu"
      role="listbox"
      className="absolute top-full left-0 z-20 mt-2 max-h-64 w-full overflow-y-auto rounded-lg border border-[#998C5F] bg-[#00070C] p-[6px]"
    >
      {options.map((option) => (
        <button
          key={option.id}
          type="button"
          data-testid="mention-option"
          role="option"
          aria-selected={false}
          onClick={() => onSelect(option)}
          className="flex w-full items-center gap-2 rounded p-3 text-left text-base leading-6 font-bold tracking-[0.5px] text-white hover:bg-[rgba(255,234,158,0.05)]"
        >
          <Image src={option.avatarUrl} alt="" width={24} height={24} className="h-6 w-6 shrink-0 rounded-full object-cover" />
          {option.fullName}
        </button>
      ))}
    </div>
  );
}
