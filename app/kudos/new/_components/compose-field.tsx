import type { ComposeFieldProps } from "@/lib/kudos/compose-contract";

/**
 * The ONLY place a `field-error-{recipient|title|body|hashtag}` element is
 * created (test-contract.md § Validation) — ID-56 requires all four to be
 * able to show at once, so one code path renders every one of them, never
 * duplicated per field. Purely the error TEXT: each field's own component
 * (`recipient-picker.tsx`, `title-field.tsx`, …) owns its own `error` prop
 * for the red-border / `aria-invalid` styling on the input itself — this
 * component does not touch that input.
 *
 * No dedicated Figma node — the design's error state lives in the
 * unauthored companion frame `5c7PkAibyD` (design/dev status both
 * unpopulated in MoMorph; clarifications.md § Unresolved question 3), so
 * the error text carries no `mm:` id. Colors follow the repo's existing
 * unauthored-error convention (`app/login/_components/error-banner.tsx`),
 * adjusted for this screen's light `#FFF8E1` card background.
 */
export function ComposeField({ field, error, copy }: ComposeFieldProps) {
  if (!error) return null;

  return (
    <p
      data-testid={`field-error-${field}`}
      role="alert"
      className="mt-1 text-sm font-semibold text-[#CF1322]"
    >
      {copy[error]}
    </p>
  );
}
