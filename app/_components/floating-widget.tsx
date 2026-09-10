"use client";

import { useCallback, useId, useRef, useState } from "react";
import Image from "next/image";
import Link from "next/link";

import type { Dictionary } from "@/lib/i18n/dictionaries";

import { useDismissOnOutside } from "./use-dismiss-on-outside";

/**
 * Item 6 — floating widget button, two states of one MoMorph component:
 * collapsed trigger (`_hphd32jN2`, node `313:9138`) and expanded quick-action
 * menu (`Sv7DFwBw1h`, node `313:9140`). The design's own navigation edge
 * (`313:9138` → `313:9139`) settles what an earlier reading, made from the
 * collapsed frame alone, got wrong: the pill is a disclosure trigger, not a
 * pair of direct links (clarifications.md, session 2026-09-10). The pen,
 * `/` and glyph stay exactly as drawn — they are the trigger's content, not
 * two hit targets.
 *
 * The trigger button stays mounted for the whole open/closed lifecycle so
 * `aria-expanded`/`aria-controls` remain queryable while the menu is shown,
 * and so `useDismissOnOutside`'s synchronous focus-return on Escape has a
 * live node to focus. Only its own visibility toggles — `open` swaps its
 * visible pill styling for an invisible, inert placeholder taken out of the
 * Tab order (`tabIndex={-1}`) so a keyboard user can't Tab into a control
 * they can't see, while `tabIndex={-1}` still permits the programmatic
 * `.focus()` call the Escape path relies on. Its own `onClick` toggles
 * `open` rather than only opening, since a disclosure trigger reporting
 * `aria-expanded="true"` must collapse when activated. The menu itself
 * mounts only while open. `fixed` keeps the whole thing overlaying R4-R6
 * regardless of scroll position.
 */
export function FloatingWidget({ widget }: { widget: Dictionary["home"]["widget"] }) {
  const [open, setOpen] = useState(false);
  const menuId = useId();
  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  // Outside pointerdown must not move focus — the user aimed elsewhere on the
  // page. `Hủy` and Escape must, because both are deliberate dismissals made
  // from inside the menu: without the focus return the menu unmounts and a
  // keyboard user is dropped on `document.body`, with no way back to the
  // trigger but a full Tab cycle. Hence two callbacks, not one.
  const close = useCallback(() => setOpen(false), []);
  const closeAndRestoreFocus = useCallback(() => {
    setOpen(false);
    triggerRef.current?.focus();
  }, []);
  useDismissOnOutside(open, rootRef, triggerRef, close);

  return (
    // mm:313:9138 mm:313:9140
    <div ref={rootRef} className="fixed right-6 bottom-6 z-30">
      {/* mm:313:9138 */}
      <button
        ref={triggerRef}
        type="button"
        data-testid="fab-trigger"
        aria-expanded={open}
        aria-controls={menuId}
        aria-label={widget.trigger}
        tabIndex={open ? -1 : undefined}
        onClick={() => setOpen((o) => !o)}
        className={
          open
            ? "pointer-events-none absolute inset-0 opacity-0"
            : "flex items-center gap-2 rounded-full bg-[#FFEA9E] p-4 shadow-[0_4px_4px_rgba(0,0,0,0.25),0_0_6px_#FAE287]"
        }
      >
        {/* mm:I313:9138;214:3839;186:1763 (MM_MEDIA_Pen) */}
        <Image src="/images/home/widget-pen-icon.svg" alt="" aria-hidden width={24} height={24} />
        {/* mm:I313:9138;214:3839;186:1568 — "/" separator */}
        <span aria-hidden className="text-2xl leading-8 font-bold text-[#00101A]">
          /
        </span>
        {/* mm:I313:9138;214:3839;186:1766 (MM_MEDIA_LOGO) */}
        <span className="flex h-6 w-6 items-center justify-center">
          <Image
            src="/images/home/widget-saa-kudos-glyph.svg"
            alt=""
            aria-hidden
            width={24}
            height={23}
          />
        </span>
      </button>
      {open && (
        // mm:313:9140
        <div id={menuId} data-testid="fab-menu" className="flex flex-col items-end gap-5">
          {/* mm:I313:9140;214:3799 (A_Button thể lệ) */}
          <Link
            href="/standards"
            data-testid="fab-standards"
            aria-label={widget.standards}
            className="flex h-16 items-center gap-2 rounded bg-[#FFEA9E] p-4 lg:w-[149px]"
          >
            <span className="flex h-6 w-6 items-center justify-center">
              <Image
                src="/images/home/widget-saa-kudos-glyph.svg"
                alt=""
                aria-hidden
                width={24}
                height={23}
              />
            </span>
            <span className="text-center text-2xl leading-8 font-bold text-[#00101A]">
              {widget.menuStandards}
            </span>
          </Link>
          {/* mm:I313:9140;214:3732 (B_Button viết kudos) */}
          <Link
            href="/kudos/new"
            data-testid="fab-write-kudos"
            aria-label={widget.writeKudos}
            className="flex h-16 items-center gap-2 rounded bg-[#FFEA9E] p-4 lg:w-[214px]"
          >
            <Image src="/images/home/widget-pen-icon.svg" alt="" aria-hidden width={24} height={24} />
            <span className="text-center text-2xl leading-8 font-bold text-[#00101A]">
              {widget.menuWriteKudos}
            </span>
          </Link>
          {/* mm:I313:9140;214:3827 (C_Button huỷ) */}
          <button
            type="button"
            data-testid="fab-close"
            aria-label={widget.close}
            onClick={closeAndRestoreFocus}
            className="flex h-14 w-14 items-center justify-center rounded-full bg-[#D4271D] p-4"
          >
            <Image src="/images/rules/close-icon.svg" alt="" aria-hidden width={24} height={24} />
          </button>
        </div>
      )}
    </div>
  );
}
