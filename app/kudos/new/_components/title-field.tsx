"use client";

import type { TitleFieldProps } from "@/lib/kudos/compose-contract";

/**
 * `Danh hiệu` — mm:I520:11647;1688:10436 (label "Danh hiệu" + required `*`,
 * unused here: `TitleFieldCopy` carries no label string, see this phase's
 * report § unresolved) · mm:I520:11647;1688:10437 (input shell, 514×56,
 * border `#998C5F`, radius 8px, padding 16px/24px, bg white — same measured
 * shell as the recipient search input, componentId `186:2757`) ·
 * mm:I520:11647;1688:10447 (the ONE hint element, both lines, 16px/700/
 * Montserrat, `#999`, letter-spacing 0.15px).
 *
 * Node family `1688:*`, not `520:*` like every other field on this frame —
 * added after the spec CSV and 57 test cases were authored, so this field
 * has no numbered spec row and no `ID-*` case beyond the shared required-
 * field error string every field reuses (clarifications.md § stale CSV,
 * Unresolved question 1).
 */
export function TitleField({ copy, value, error, onChange }: TitleFieldProps) {
  return (
    <div className="flex w-full flex-col gap-2">
      {/* mm:I520:11647;1688:10437 */}
      <input
        id="compose-title-input"
        data-testid="title-input"
        type="text"
        placeholder={copy.placeholder}
        value={value}
        aria-invalid={error ? "true" : undefined}
        onChange={(event) => onChange(event.target.value)}
        className={`h-14 w-full rounded-lg border bg-white px-6 py-4 text-base font-bold tracking-[0.15px] text-[#00101A] outline-none ${
          error ? "border-[#CF1322]" : "border-[#998C5F]"
        }`}
      />
      {/* mm:I520:11647;1688:10447 — one element, two lines (both required by
          the "Title field" test case's single `title-hint` locator) */}
      <p
        data-testid="title-hint"
        className="text-base leading-6 font-bold tracking-[0.15px] text-[#999]"
      >
        <span className="block">{copy.hintExample}</span>
        <span className="block">{copy.hintUsage}</span>
      </p>
    </div>
  );
}
