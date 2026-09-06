import { useEffect } from "react";

const AUTO_DISMISS_MS = 3000;

/**
 * The Copy Link result toast (test-contract § "Copy link"). No MoMorph node
 * maps to it — the frame only implies the affordance via the click action —
 * so it carries no `mm:` marker; styling follows the frame's gold-on-dark
 * palette (`clarifications.md` § Palette). Auto-dismisses so a second copy
 * click always restarts a fresh 3s window (plan.md § Key Insight 5). Carries
 * no `"use client"` of its own — always rendered inside `kudos-board.tsx`'s
 * client boundary.
 */
export function KudosToast({
  toast,
  onDismiss,
}: {
  toast: { message: string; key: number } | null;
  onDismiss: () => void;
}) {
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(onDismiss, AUTO_DISMISS_MS);
    return () => clearTimeout(timer);
  }, [toast, onDismiss]);

  if (!toast) return null;

  return (
    <div
      data-testid="toast"
      role="status"
      aria-live="polite"
      className="fixed bottom-8 left-1/2 z-50 -translate-x-1/2 rounded-lg border border-[#FFEA9E] bg-[#1A2527] px-6 py-4 text-base font-bold tracking-[0.15px] text-[#FFEA9E] shadow-lg"
    >
      {toast.message}
    </div>
  );
}
