"use client";

import Image from "next/image";
import { useRouter } from "next/navigation";
import { useCallback, useEffect } from "react";

/**
 * "Closing the Thể lệ panel" — defined once, attached in two places.
 *
 * FR-401 / BR-004: `Đóng` returns the visitor to wherever they came from, so
 * its destination is a history entry rather than a URL — which is why the
 * control is a real `<button>` and not a `<Link>`. With no history behind the
 * route (a deep link, a fresh tab), it falls back to `/`. Never a dead end.
 *
 * The signal is read AT CLICK TIME, not at mount: both sources below are live
 * browser state and nothing here should cache them.
 *
 * WHY NOT `window.history.length > 1` ALONE — measured, not theorised.
 * Assumption A1 in technical-spec § 5.2 proposed exactly that, and phase 07
 * proved it wrong against a real Chromium:
 *
 *   fresh newPage()             -> url about:blank, history.length = 1
 *   after goto("/standards")    -> url /standards,  history.length = 2
 *
 * A tab's initial `about:blank` stays in session history, so a deep link
 * reports length 2 and takes the `back()` branch — landing the tab on
 * `about:blank`, the dead end BR-004 exists to forbid (e2e FUN_003b).
 *
 * The Navigation API separates the two cases where `history.length` cannot:
 * on a fresh tab `navigation.canGoBack` is `false`, while after a soft
 * navigation from `/` it is `true`. `history.length` stays as the fallback
 * for engines that do not implement it (Safari/Firefox as of writing), where
 * the original over-reporting behaviour applies — still not a dead end there,
 * since those engines do not synthesise an `about:blank` entry the way a
 * driven Chromium does.
 *
 * `document.referrer` is not an alternative: Next's client-side navigation
 * does not update it (technical-spec § 3.2).
 */

/**
 * `Navigation` is not in TypeScript's DOM lib yet, so the one property this
 * file needs is declared narrowly rather than pulling in a global shim.
 */
type NavigationLike = { canGoBack?: boolean };

function hasHistoryToReturnTo(): boolean {
  const navigation = (window as Window & { navigation?: NavigationLike }).navigation;
  if (typeof navigation?.canGoBack === "boolean") return navigation.canGoBack;
  return window.history.length > 1;
}

/**
 * The dismiss callback itself — see the contract above.
 *
 * No open-redirect surface: both destinations are fixed literals and neither
 * is read from the URL. That is the deliberate difference from
 * `/auth/callback`, where `callback-security.spec.ts` has to guard exactly
 * that.
 */
function useRulesDismiss() {
  const router = useRouter();

  return useCallback(() => {
    if (hasHistoryToReturnTo()) {
      router.back();
      return;
    }
    router.push("/");
  }, [router]);
}

/**
 * The scrim behind the drawer (FR-404). The frame's left region is flat dark
 * with no content (`3204:6051`), so a scrim reproduces it without inventing a
 * background.
 *
 * It is also where the `Escape` listener lives — one element owning both
 * "click outside" and "press Escape" keeps the two from drifting apart. The
 * listener sits on `document`, matching how `language-selector.tsx` and
 * `use-dismiss-on-outside.ts` attach global keydown handlers. Those two are
 * popover-shaped (`open` flag, `rootRef`, `triggerRef` to return focus to);
 * this drawer has no open state and no trigger, so it attaches its own rather
 * than bending that hook out of shape.
 *
 * `aria-hidden` and no keyboard affordance of its own: a scrim is decoration,
 * and its keyboard equivalent is the `Escape` handler registered right here,
 * not a focusable overlay in the tab order ahead of the panel content.
 *
 * Cleanup on unmount is not decorative either — `/standards` is left by
 * client-side navigation, and a listener that outlives the route would keep
 * firing `Escape` from pages that have no panel to close.
 */
export function RulesBackdrop() {
  const dismiss = useRulesDismiss();

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      // A nearer popover already consumed this Escape — most concretely
      // `language-selector.tsx`, whose dropdown lives in the header and
      // registers its own bubble-phase `keydown` on `document` too. Without
      // this guard, closing that dropdown with Escape ALSO dismisses the
      // panel and navigates the visitor off the page. `stopPropagation()`
      // cannot separate the two: both listeners sit on the same node, so
      // only `defaultPrevented` distinguishes them.
      if (event.defaultPrevented) return;
      if (event.key === "Escape") dismiss();
    }

    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [dismiss]);

  return <div className="fixed inset-0 z-40 bg-black/50" aria-hidden onClick={dismiss} />;
}

/**
 * mm:3204:6093 (`B.1_Button đóng`) — the left control of the drawer footer.
 *
 * Measured from the node: `border: 1px solid #998C5F`, background
 * `rgba(255, 234, 158, 0.10)`, `border-radius: 4px`, `padding: 16px`,
 * `gap: 8px`, 24x24 `MM_MEDIA_Close`, 56px tall. Hover lifts the fill with
 * `hover:bg-white/10`, the token already approved for this shared button in
 * `language-selector.tsx` / `home-nav.tsx` (clarifications § GUI_004) — reused,
 * not reinvented.
 *
 * The frame's 94px width is left to the content. The footer gives
 * `Viết KUDOS` `flex-1`, so `Đóng` settles at icon + gap + label + padding on
 * its own; hardcoding `w-[94px]` would clip the moment the label is anything
 * other than "Đóng".
 *
 * `Frame 483` (`I3204:6093;186:2758`), the inner row holding icon and label,
 * is flattened away: it declares the same `gap: 8px` / `align-items: center`
 * the button itself already provides, so keeping it would add a DOM node that
 * renders identically to its parent's layout.
 *
 * `close-icon.svg` ships `fill="white"`, which is the design colour on this
 * dark fill — no `currentColor` inlining needed, and `<Image>` matches how
 * `floating-widget.tsx` already serves its icons. (The gold `Viết KUDOS`
 * button is the case where the white fill is wrong; that is phase 06/07's.)
 *
 * No `disabled` prop (DEC-002). Nothing in this feature can put either footer
 * control out of service, so the prop could only ever be dead code, and a
 * fake dimmed button staged to turn `TC_THELE_GUI_003` / `TC_THELE_FUN_005`
 * green is precisely the stopgap `primary-workflow.md` forbids. Both cases
 * are carried in the suite as `test.skip` with that reason inline.
 *
 * `label` arrives resolved from `dictionary.rules.closeButton` — a plain
 * string across the server/client boundary, nothing else.
 */
export function RulesCloseButton({ label }: { label: string }) {
  const dismiss = useRulesDismiss();

  return (
    <button
      type="button"
      data-testid="rules-close-button"
      onClick={dismiss}
      className="flex h-14 cursor-pointer items-center justify-center gap-2 rounded border border-[#998C5F] bg-[#FFEA9E]/10 px-4 text-base leading-6 font-bold tracking-[0.5px] text-white transition-colors hover:bg-white/10"
    >
      {/* mm:I3204:6093;186:2759 — MM_MEDIA_Close, 24x24 */}
      <Image src="/images/rules/close-icon.svg" alt="" aria-hidden width={24} height={24} />
      {/* mm:I3204:6093;186:2760 */}
      {label}
    </button>
  );
}
