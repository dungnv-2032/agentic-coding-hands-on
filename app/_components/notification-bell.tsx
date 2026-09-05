"use client";

import { useId, useRef, useState } from "react";
import type { SVGProps } from "react";

import type { Dictionary } from "@/lib/i18n/dictionaries";

import { useDismissOnOutside } from "./use-dismiss-on-outside";

/**
 * No MoMorph export exists for `MM_MEDIA_Noti?=True` — asset-manifest.md
 * records it as a shared icon-set glyph with no unique per-node artwork.
 * Hand-drawn at the recorded 24x24 size, `currentColor` fill, following the
 * same precedent `icons.tsx` set for `IconFlagEn` (no design counterpart).
 */
function IconBell(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      {...props}
    >
      <path
        d="M12 3c-2.21 0-4 1.79-4 4v2.586c0 .466-.184.912-.513 1.241L6.29 12.023A2 2 0 0 0 5.707 13.44V15a1 1 0 0 0 1 1h10.586a1 1 0 0 0 1-1v-1.56a2 2 0 0 0-.586-1.415l-1.197-1.196A1.755 1.755 0 0 1 16 9.586V7c0-2.21-1.79-4-4-4Z"
        fill="currentColor"
      />
      <path d="M9.5 18a2.5 2.5 0 0 0 5 0h-5Z" fill="currentColor" />
    </svg>
  );
}

/**
 * A1.6 — 40x40 trigger (node `I2167:9091;186:2101`; inner `Button` instance
 * `186:2101;186:2020` is transparent, no border, 4px radius, 10px padding —
 * read verbatim, not guessed). Toggles a presentational panel with the
 * empty state only (clarifications A1: no notification backend exists, so
 * no badge is rendered — ID-29's "no badge when nothing unread" is the
 * shipped state; ID-28 stays deferred). `aria-haspopup="menu"` keeps
 * `listbox` unique to the language selector (test-contract.md).
 */
export function NotificationBell({ dictionary }: { dictionary: Dictionary }) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const panelId = useId();

  useDismissOnOutside(open, rootRef, triggerRef, () => setOpen(false));

  return (
    // mm:I2167:9091;186:2101
    <div ref={rootRef} className="relative">
      <button
        ref={triggerRef}
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={panelId}
        aria-label={dictionary.header.notificationsLabel}
        onClick={() => setOpen((prev) => !prev)}
        className="flex h-10 w-10 cursor-pointer items-center justify-center rounded p-2.5 text-white transition-colors hover:bg-white/10 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[#998C5F]"
      >
        <IconBell className="h-6 w-6" aria-hidden />
      </button>
      {open && (
        // Panel tokens reuse the language selector's already-approved
        // dropdown surface (`border-[#998C5F] bg-[#00070C]`) — the same
        // component family, no captured open-state node for this trigger.
        <div
          id={panelId}
          data-testid="notification-panel"
          role="menu"
          aria-label={dictionary.header.notificationsLabel}
          className="absolute right-0 top-full z-30 mt-1 w-64 rounded-lg border border-[#998C5F] bg-[#00070C] p-4 text-sm text-white"
        >
          {dictionary.header.notificationsEmpty}
        </div>
      )}
    </div>
  );
}
