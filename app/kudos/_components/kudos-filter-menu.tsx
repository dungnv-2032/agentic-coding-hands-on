import type { FilterOptionView } from "@/lib/kudos/view-model";

/**
 * mm:563:8026 (mms_A_Dropdown-List, `JWpsISMAaM`/`WXK5AYB_rG`) — the listbox
 * both filter triggers open (dropdown spec A.1). Pure presentational: open
 * state and outside-dismiss live in `kudos-filter-bar.tsx`, selection state
 * in `kudos-board.tsx` (plan.md § Client/server split). Options carry
 * `aria-selected`; re-clicking the selected option is the caller's toggle
 * (`kudos-board.tsx` flips the id to `null`), not this component's job.
 *
 * The box is the default for both listboxes (FR-214): it bounds the list in
 * its own box (dropdown spec: it must not push the page layout) while every
 * option stays mounted for K-3's count. The box is exactly 348px tall: 6
 * rows x 56px (p-4 + text-base leading-6) + 6px top/bottom container
 * padding, with no gap between rows. FR-215: a keyboard-focused option shows
 * the same `#FAE287` glow as the selected state.
 */
export function KudosFilterMenu({
  testId,
  options,
  selectedId,
  onSelect,
}: {
  testId: "filter-menu-hashtag" | "filter-menu-department";
  options: FilterOptionView[];
  selectedId: number | null;
  onSelect: (option: FilterOptionView) => void;
}) {
  return (
    // mm:563:8026 — bg #00070C, 1px border #998C5F, 8px radius, 6px padding.
    <div
      role="listbox"
      data-testid={testId}
      className="absolute top-full left-0 z-20 mt-2 flex w-64 flex-col rounded-lg border border-[#998C5F] bg-[#00070C] p-[6px] max-h-[348px] overflow-y-auto"
    >
      {options.map((option) => {
        const selected = option.id === selectedId;
        return (
          // mm:186:1496 (mms_A.1_Tag1) — 16px padding, 4px radius; selected
          // state carries the measured gold glow (`JWpsISMAaM` tag preview).
          //
          // FR-215's `focus-visible:` glow is ADDITIVE to the browser's native
          // focus ring, never a replacement: a text-shadow alone does not
          // clear WCAG 2.1 AA non-text contrast (1.4.11) on its own. Do not
          // add `focus-visible:outline-none` here to tidy up the double ring —
          // that would silently drop the keyboard indicator this screen relies
          // on, and K-32 asserts only the glow, so no test would catch it.
          <button
            key={option.id}
            type="button"
            role="option"
            aria-selected={selected}
            onClick={() => onSelect(option)}
            className={`w-full cursor-pointer rounded p-4 text-center text-base leading-6 font-bold tracking-[0.5px] text-white focus-visible:[text-shadow:0_0_6px_#FAE287] ${
              selected
                ? "bg-[rgba(255,234,158,0.10)] [text-shadow:0_0_6px_#FAE287]"
                : "transition-colors hover:bg-[rgba(255,234,158,0.05)]"
            }`}
          >
            {option.name}
          </button>
        );
      })}
    </div>
  );
}
