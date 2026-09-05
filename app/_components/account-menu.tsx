"use client";

import Link from "next/link";
import { useId, useRef, useState } from "react";
import type { SVGProps } from "react";

import type { Dictionary } from "@/lib/i18n/dictionaries";

import { useDismissOnOutside } from "./use-dismiss-on-outside";

/**
 * No MoMorph export exists for `MM_MEDIA_User Profile` — same "shared
 * icon-set glyph, no unique artwork" note as `IconBell` in
 * `notification-bell.tsx`. Hand-drawn at the recorded 24x24 size.
 */
function IconUser(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      {...props}
    >
      <path d="M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z" fill="currentColor" />
      <path
        d="M4 19.5C4 16.462 7.582 14 12 14s8 2.462 8 5.5v.5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-.5Z"
        fill="currentColor"
      />
    </svg>
  );
}

interface AccountMenuProps {
  dictionary: Dictionary;
  isAdmin: boolean;
  signOutAction: () => Promise<void>;
}

/**
 * A1.8 — 40x40 trigger (node `I2167:9091;186:1597`): 1px `#998C5F` border,
 * 4px radius, transparent fill — read verbatim from the node. Menu holds
 * Profile (link), Sign out (the real promoted `signOut` server action
 * inside a `<form action>`, matching the existing `/todo` pattern), and
 * Admin Dashboard (link, only when `isAdmin` — DEC-002). The Profile label
 * carries no admin/dashboard wording so ID-38's absence check on a regular
 * user's menu stays honest. `aria-haspopup="menu"` keeps `listbox` unique
 * to the language selector (test-contract.md).
 */
export function AccountMenu({
  dictionary,
  isAdmin,
  signOutAction,
}: AccountMenuProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const menuId = useId();

  useDismissOnOutside(open, rootRef, triggerRef, () => setOpen(false));

  const itemClassName =
    "rounded-[2px] px-4 py-3 text-left text-sm font-bold text-white transition-colors hover:bg-[rgba(255,234,158,0.08)]";

  return (
    // mm:I2167:9091;186:1597
    <div ref={rootRef} className="relative">
      <button
        ref={triggerRef}
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={menuId}
        aria-label={dictionary.header.accountLabel}
        onClick={() => setOpen((prev) => !prev)}
        className="flex h-10 w-10 cursor-pointer items-center justify-center rounded border border-[#998C5F] bg-transparent p-2.5 text-white transition-colors hover:bg-white/10 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[#998C5F]"
      >
        <IconUser className="h-6 w-6" aria-hidden />
      </button>
      {open && (
        // Menu tokens reuse the language selector's already-approved
        // dropdown surface — same component family, no captured open-state
        // node for this trigger.
        <div
          id={menuId}
          data-testid="account-menu"
          role="menu"
          aria-label={dictionary.header.accountLabel}
          className="absolute right-0 top-full z-30 mt-1 flex w-48 flex-col rounded-lg border border-[#998C5F] bg-[#00070C] p-1.5"
        >
          <Link
            href="/profile"
            onClick={() => setOpen(false)}
            className={itemClassName}
          >
            {dictionary.header.profile}
          </Link>
          {isAdmin && (
            <Link
              href="/admin"
              onClick={() => setOpen(false)}
              className={itemClassName}
            >
              {dictionary.header.adminDashboard}
            </Link>
          )}
          <form action={signOutAction}>
            <button type="submit" className={`w-full ${itemClassName}`}>
              {dictionary.header.signOut}
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
