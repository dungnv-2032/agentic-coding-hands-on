"use client";

import { useEffect, useRef, useState, type RefObject } from "react";

import { useDismissOnOutside } from "@/app/_components/use-dismiss-on-outside";
import { ACCEPTED_LINK_SCHEMES } from "@/lib/kudos/compose-contract";

/**
 * The link toolbar button's URL-entry dialog (spec item C.5, verbatim:
 * "Mở hộp thoại nhập URL … sau đó chèn liên kết vào vùng văn bản" —
 * test-contract.md § Rich-text toolbar, ID-31).
 *
 * No MoMorph node backs this dialog either (ratification item 6 lists it as
 * unauthored) — a centered overlay is the only reasonable shape for a modal
 * URL prompt, matching this screen's own dialog-over-dimmed-page pattern
 * (clarifications.md § Route, auth, and the modal question).
 *
 * Confirm is gated on `ACCEPTED_LINK_SCHEMES` (http/https/mailto) so a
 * `javascript:`/`data:`/`vbscript:` URL can never leave this dialog — the
 * first of the three checks `rich-text.ts`'s doc comment promises
 * (`isAcceptedLinkScheme` in `parseKudosDoc` and the renderer check again).
 */
export interface LinkDialogCopy {
  heading: string;
  urlLabel: string;
  confirm: string;
  cancel: string;
}

export interface LinkDialogProps {
  open: boolean;
  copy: LinkDialogCopy;
  onConfirm: (href: string) => void;
  onCancel: () => void;
  triggerRef?: RefObject<HTMLButtonElement | null>;
}

function isAcceptedScheme(href: string): boolean {
  try {
    return (ACCEPTED_LINK_SCHEMES as readonly string[]).includes(new URL(href).protocol);
  } catch {
    return false;
  }
}

export function LinkDialog({ open, copy, onConfirm, onCancel, triggerRef }: LinkDialogProps) {
  const [url, setUrl] = useState("");
  const rootRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const fallbackTriggerRef = useRef<HTMLButtonElement>(null);

  // `url` resets for free: `if (!open) return null` below unmounts this
  // component entirely while closed, so `useState("")` re-initializes on
  // the next open — no setState-in-effect needed for that part.
  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  useDismissOnOutside(open, rootRef, triggerRef ?? fallbackTriggerRef, onCancel);

  if (!open) return null;

  const valid = isAcceptedScheme(url);

  return (
    // mm: unauthored, see file doc — centered overlay over the dimmed compose modal
    <div className="fixed inset-0 z-30 flex items-center justify-center bg-black/40">
      <div
        ref={rootRef}
        data-testid="link-dialog"
        role="dialog"
        aria-modal="true"
        aria-label={copy.heading}
        className="flex w-full max-w-md flex-col gap-4 rounded-lg border border-[#998C5F] bg-[#FFF8E1] p-6"
      >
        <h2 className="text-lg font-bold text-[#00101A]">{copy.heading}</h2>
        <label className="flex flex-col gap-2 text-sm font-bold text-[#00101A]">
          {copy.urlLabel}
          <input
            ref={inputRef}
            data-testid="link-url-input"
            type="url"
            value={url}
            onChange={(event) => setUrl(event.target.value)}
            className="h-12 w-full rounded-lg border border-[#998C5F] bg-white px-4 text-base text-[#00101A] outline-none"
          />
        </label>
        <div className="flex justify-end gap-3">
          <button type="button" onClick={onCancel} className="rounded border border-[#998C5F] px-4 py-2 text-sm font-bold text-[#00101A]">
            {copy.cancel}
          </button>
          <button
            type="button"
            disabled={!valid}
            onClick={() => onConfirm(url)}
            className="rounded bg-[#FFEA9E] px-4 py-2 text-sm font-bold text-[#00101A] disabled:opacity-40"
          >
            {copy.confirm}
          </button>
        </div>
      </div>
    </div>
  );
}
