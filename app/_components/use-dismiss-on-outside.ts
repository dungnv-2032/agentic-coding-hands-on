"use client";

import { useEffect, type RefObject } from "react";

/**
 * Shared outside-pointerdown + Escape dismissal for the header's popover
 * triggers (notification bell, account menu). Mirrors the inline behavior
 * already proven in `language-selector.tsx` (frozen this phase — not
 * retrofitted onto this hook) so every dropdown on the screen gets the same
 * contract: outside pointerdown closes without moving focus; Escape closes
 * and returns focus to the trigger (ID-30..35, test-contract.md).
 */
export function useDismissOnOutside(
  open: boolean,
  rootRef: RefObject<HTMLElement | null>,
  triggerRef: RefObject<HTMLElement | null>,
  onDismiss: () => void,
) {
  useEffect(() => {
    if (!open) return;

    function onPointerDown(event: PointerEvent) {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) {
        // No focus return here — the user aimed somewhere else on the page.
        onDismiss();
      }
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onDismiss();
        triggerRef.current?.focus();
      }
    }

    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open, rootRef, triggerRef, onDismiss]);
}
