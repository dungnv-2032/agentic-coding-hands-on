"use client";

import Image from "next/image";
import { useRouter } from "next/navigation";
import { useCallback } from "react";

/**
 * mm:1466:7679 — the close glyph (FR-301). Reuses the
 * `hasHistoryToReturnTo()` idiom from
 * `app/standards/_components/rules-panel-dismiss.tsx` verbatim — measured
 * against a real Chromium there (see that file's docblock), not theorised —
 * with one change: this screen's fallback destination is `/kudos`, not `/`.
 * `/kudos/secret-box` is reached from the Kudos sidebar
 * (clarifications.md), so a deep link with no history returns to the Kudos
 * board, not the homepage.
 *
 * This is a route, not a modal (plan DEC-02 / phase-04's Key Insights): no
 * scrim, no `Escape` listener, no focus trap. The glyph is a plain
 * navigation control, exactly as `rules-panel-dismiss.tsx`'s own button is.
 */
type NavigationLike = { canGoBack?: boolean };

function hasHistoryToReturnTo(): boolean {
  const navigation = (window as Window & { navigation?: NavigationLike }).navigation;
  if (typeof navigation?.canGoBack === "boolean") return navigation.canGoBack;
  return window.history.length > 1;
}

/** `label` arrives resolved from `dictionary.secretBox.closeLabel` — a plain string, nothing else. */
export function SecretBoxDismiss({ label }: { label: string }) {
  const router = useRouter();

  const dismiss = useCallback(() => {
    if (hasHistoryToReturnTo()) {
      router.back();
      return;
    }
    router.push("/kudos");
  }, [router]);

  return (
    <button
      type="button"
      data-testid="secret-box-close"
      aria-label={label}
      onClick={dismiss}
      className="flex h-[19px] w-[19px] cursor-pointer items-center justify-center"
    >
      {/* mm:1466:7679 — 19×19. `close-icon.svg` ships `fill="white"`, the
          correct colour on this `#00101A` ground — byte-identical reuse of
          `/standards`'s asset, not a second copy. */}
      <Image src="/images/rules/close-icon.svg" alt="" aria-hidden width={19} height={19} />
    </button>
  );
}
