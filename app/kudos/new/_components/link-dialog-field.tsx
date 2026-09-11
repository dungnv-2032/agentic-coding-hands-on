"use client";

import type { LinkFieldError } from "@/lib/kudos/validate-link";

/**
 * One labelled row of the Addlink Box dialog — `Nội dung` (`mm:I1002:12682;1002:12501`)
 * and `URL` (`mm:I1002:12682;1002:12652`) are the same shape, so they share one
 * component rather than two near-identical JSX blocks. Extracted also to keep
 * `link-dialog.tsx` under the repo's 200-line rule.
 *
 * Row: 672×56, `flex` row, gap 16, centered. The label is NOT a fixed-width column
 * (107px "Nội dung" vs 47px "URL" intrinsic), so the two inputs deliberately start at
 * different x — as drawn.
 */
export interface LinkDialogFieldProps {
  /** `link-text-input` / `link-url-input` — also the `<label for>` target and the error hook stem. */
  id: "link-text-input" | "link-url-input";
  label: string;
  value: string;
  type: "text" | "url";
  /** `Nội dung`'s label focuses its input on click (item B.1); `URL`'s is informational only (item C.1). */
  interactiveLabel: boolean;
  error?: LinkFieldError;
  errorCopy: Record<LinkFieldError, string>;
  inputRef?: React.RefObject<HTMLInputElement | null>;
  onChange: (value: string) => void;
  onBlur?: () => void;
}

export function LinkDialogField({
  id,
  label,
  value,
  type,
  interactiveLabel,
  error,
  errorCopy,
  inputRef,
  onChange,
  onBlur,
}: LinkDialogFieldProps) {
  // mm:I1002:12682;1002:12502;416:5534 (Nội dung) / mm:I1002:12682;1002:12653;416:5534 (URL)
  const labelClass = "text-[22px] leading-7 font-bold text-[#00101A]";

  return (
    <div className="flex w-full flex-col gap-2">
      <div className="flex h-14 w-full items-center gap-4">
        {interactiveLabel ? (
          <label htmlFor={id} className={labelClass}>
            {label}
          </label>
        ) : (
          <span className={labelClass}>{label}</span>
        )}
        {/* mm:I1002:12682;1002:12503 / mm:I1002:12682;1002:12654 — FR-213 "Focus: Hiện viền
            nổi" (item B.2). The lift itself is unauthored (the frame carries no focus state),
            so it reuses the screen's palette: dark border + #FFEA9E ring. Never `outline-none`
            with nothing behind it — that is a WCAG 2.4.7 regression. */}
        <input
          ref={inputRef}
          id={id}
          data-testid={id}
          type={type}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onBlur={onBlur}
          aria-invalid={error ? "true" : undefined}
          className={`h-14 flex-1 rounded-lg border bg-white px-6 py-4 text-base font-bold text-[#00101A] outline-none focus:border-[#00101A] focus:ring-2 focus:ring-[#FFEA9E] ${
            error ? "border-[#CF1322]" : "border-[#998C5F]"
          }`}
        />
      </div>
      {error && (
        // Unauthored — the frame draws no error state; follows the screen's own #CF1322 convention.
        <p data-testid={`${id === "link-text-input" ? "link-text" : "link-url"}-error`} className="text-sm font-semibold text-[#CF1322]">
          {errorCopy[error]}
        </p>
      )}
    </div>
  );
}
