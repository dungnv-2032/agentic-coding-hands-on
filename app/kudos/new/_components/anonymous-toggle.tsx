"use client";

import type { AnonymousToggleProps } from "@/lib/kudos/compose-contract";

/**
 * mm:I520:11647;520:14099 (`mms_G_Gửi ẩn danh`, 672×28 row, 16px gap) ·
 * mm:I520:11647;520:14099;520:14097 (24×24 checkbox box, border 1px `#999`,
 * radius 4px, bg white) · mm:I520:11647;520:14099;520:14095 (label text,
 * 22px/700/Montserrat, `#999`).
 *
 * `anonymous-name-input` has no Figma node (clarifications.md § Unresolved
 * question 4) — conditionally RENDERED, never CSS-hidden (DEC-001), so an
 * unchecked form can't submit a stale name and Playwright's
 * `not.toBeVisible()` sees the element gone from the DOM, not merely
 * `display:none` (ID-43/ID-44).
 */
export function AnonymousToggle({
  copy,
  checked,
  name,
  onToggle,
  onNameChange,
}: AnonymousToggleProps) {
  return (
    <div className="flex w-full flex-col gap-3">
      {/* mm:I520:11647;520:14099 */}
      <label className="flex items-center gap-4">
        {/* mm:I520:11647;520:14099;520:14097 */}
        <input
          data-testid="anonymous-checkbox"
          type="checkbox"
          checked={checked}
          onChange={(event) => onToggle(event.target.checked)}
          className="h-6 w-6 shrink-0 rounded border border-[#999] bg-white"
        />
        {/* mm:I520:11647;520:14099;520:14095 */}
        <span className="text-[22px] leading-7 font-bold text-[#999]">
          {copy.checkboxLabel}
        </span>
      </label>
      {checked && (
        // mm: no Figma node — reveal-on-check name field (unauthored,
        // clarifications.md § Unresolved question 4). Shell borrowed from
        // the measured recipient/title input (border #998C5F, radius 8,
        // padding 16/24, bg white) for visual consistency with the rest
        // of the form.
        <input
          data-testid="anonymous-name-input"
          type="text"
          aria-label={copy.nameInputLabel}
          placeholder={copy.nameInputLabel}
          value={name}
          onChange={(event) => onNameChange(event.target.value)}
          className="h-14 w-full rounded-lg border border-[#998C5F] bg-white px-6 py-4 text-base font-bold text-[#00101A] outline-none"
        />
      )}
    </div>
  );
}
