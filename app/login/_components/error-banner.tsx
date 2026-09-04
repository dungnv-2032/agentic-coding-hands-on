interface ErrorBannerProps {
  message: string;
}

/**
 * DEC-001 — shown above the login button when `?error` is present on the
 * URL (idle/error state in SCR-login spec.md §5). `role="alert"` already
 * implies an assertive live region; `aria-live` is kept explicit per the
 * Must-hold requirement so screen readers announce it the instant it mounts.
 */
export function ErrorBanner({ message }: ErrorBannerProps) {
  return (
    // mm:DEC-001 (error banner, no dedicated Figma node — see functional-spec.md)
    <div
      role="alert"
      aria-live="assertive"
      className="w-full max-w-[480px] rounded-md border border-red-400/40 bg-red-500/15 px-4 py-3 text-sm font-semibold text-red-100"
    >
      {message}
    </div>
  );
}
