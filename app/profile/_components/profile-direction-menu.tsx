import { useMemo, useRef, useState } from "react";

import { useDismissOnOutside } from "@/app/_components/use-dismiss-on-outside";
import { IconChevronDown } from "@/app/kudos/_components/kudos-icons";
import type { Dictionary } from "@/lib/i18n/dictionaries";
import { formatHeartCount } from "@/lib/kudos/derive";
import type { FeedDirection } from "@/lib/profile/profile-view-model";

interface DirectionOption {
  direction: FeedDirection;
  /** Interpolated — `Đã nhận (N)` / `Đã gửi (M)`. */
  label: string;
}

// mm:362:5089 — 1px #998C5F border, rgba(255,234,158,0.10) fill, 4px radius,
// padding 16px 24px, 8px gap, `align-self: stretch` (the frame's row is 64px
// tall, set by the 57px/64px KUDOS heading beside it). Label 16px/24px/700,
// tracking 0.15px, white. Same Figma button family as the board's filter
// triggers (shared componentSetId 186:1426), so this is their `TRIGGER_CLASS`
// with this instance's wider 24px side padding.
const TRIGGER_CLASS =
  "flex items-center gap-2 self-stretch rounded border border-[#998C5F] bg-[rgba(255,234,158,0.10)] px-6 py-4 text-base leading-6 font-bold tracking-[0.15px] text-white";

/**
 * mm:362:5089 (`mms_C.3_Button`) plus the listbox it opens (SCR006 C.3.1).
 *
 * Trigger and panel live in one file because C.3.1 has **no node in the frame**
 * — the design CSV lists it as `Ẩn`/hidden and the screen spec records "không
 * có mm riêng" — so there is nothing to measure and nothing to own separately.
 * Every panel token below is lifted verbatim from the shipped
 * `app/kudos/_components/kudos-filter-menu.tsx` (built from `mm:563:8026`),
 * which is what phase 08 asks for: reuse that file's panel styling and its
 * `role="listbox"`/`role="option"` shape. Pairing the trigger with the panel
 * also mirrors `kudos-filter-bar.tsx`, which owns open-state and reuses the
 * shared `use-dismiss-on-outside` hook rather than a bespoke handler.
 *
 * This component owns **which options exist** (FR-206/SEC_001) and their
 * labels, plus open/close and outside-dismiss. It does NOT own selection:
 * `onSelect` fires for every option including the active one, and the caller
 * decides that re-picking the active direction means "close, change nothing"
 * (DEC-002).
 *
 * Two authored deviations, both because the frame defines nothing here:
 *   - anchored `right-0`, not the board's `left-0`. This trigger sits at the
 *     right edge of the 680px column (`mm:362:5089` startX 897 → endX 1060),
 *     so a left-anchored panel would hang past the content.
 *   - `w-max min-w-full` instead of the board's fixed `w-64`: at most two short
 *     labels, and a 256px panel under a ~163px trigger reads as a mismatch.
 *
 * Carries no `"use client"` of its own — only rendered inside
 * `kudos-direction-section.tsx`'s boundary, the convention every
 * `app/kudos/_components/*` child follows.
 */
export function ProfileDirectionMenu({
  counts,
  isSelf,
  copy,
  activeDirection,
  onSelect,
}: {
  counts: { received: number; sent: number | null };
  isSelf: boolean;
  copy: Dictionary["profile"]["direction"];
  activeDirection: FeedDirection;
  onSelect: (direction: FeedDirection) => void;
}) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  useDismissOnOutside(open, rootRef, triggerRef, () => setOpen(false));

  const options = useMemo<DirectionOption[]>(() => {
    const fill = (t: string, n: number) => t.replace("{count}", formatHeartCount(n));
    const list: DirectionOption[] = [
      { direction: "received", label: fill(copy.receivedLabel, counts.received) },
    ];
    // SEC_001 — `counts.sent` is null on another Sunner's profile, so the
    // `Đã gửi` label is never built: the string cannot reach the DOM at all,
    // which is what "remove the surface" means rather than hide it.
    if (isSelf && counts.sent !== null) {
      list.push({ direction: "sent", label: fill(copy.sentLabel, counts.sent) });
    }
    return list;
  }, [copy, counts, isSelf]);

  // FR-403 — the trigger shows the *committed* direction, so it only moves
  // once the caller has actually landed the new page.
  const triggerLabel = options.find((o) => o.direction === activeDirection)?.label ?? "";

  return (
    <div ref={rootRef} className="relative">
      {/* mm:362:5089 (mms_C.3_Button) */}
      <button
        ref={triggerRef}
        type="button"
        data-testid="profile-direction-trigger"
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
        className={TRIGGER_CLASS}
      >
        {triggerLabel}
        {/* mm:I362:5089;186:2761 ("Button down") — 24×24 chevron, the same
            shared glyph the board's triggers use. */}
        <IconChevronDown
          aria-hidden
          className={`h-6 w-6 shrink-0 transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>

      {open && (
        // Panel tokens verbatim from kudos-filter-menu.tsx (mm:563:8026) —
        // bg #00070C, 1px #998C5F border, 8px radius, 6px padding.
        <div
          role="listbox"
          data-testid="profile-direction-menu"
          className="absolute top-full right-0 z-20 mt-2 flex w-max min-w-full flex-col gap-1 rounded-lg border border-[#998C5F] bg-[#00070C] p-[6px]"
        >
          {options.map((option) => {
            const selected = option.direction === activeDirection;
            return (
              // Option tokens verbatim from kudos-filter-menu.tsx
              // (mm:186:1496) — 16px padding, 4px radius, gold glow when active.
              <button
                key={option.direction}
                type="button"
                role="option"
                aria-selected={selected}
                data-testid="profile-direction-option"
                onClick={() => {
                  setOpen(false);
                  onSelect(option.direction);
                }}
                className={`w-full rounded p-4 text-left text-base leading-6 font-bold tracking-[0.5px] whitespace-nowrap text-white ${
                  selected
                    ? "bg-[rgba(255,234,158,0.10)] [text-shadow:0_0_6px_#FAE287]"
                    : "hover:bg-[rgba(255,234,158,0.05)]"
                }`}
              >
                {option.label}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
