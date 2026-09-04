/**
 * Locale primitives for the cookie-based i18n scheme (see clarifications.md,
 * "i18n scope for the VN/EN language selector"). Deliberately no I/O and no
 * `next/headers` import here — pure functions that both the server dictionary
 * loader and any future test can use without a request context.
 */

export type Locale = "vi" | "en";

export const LOCALES: readonly Locale[] = ["vi", "en"] as const;

export const DEFAULT_LOCALE: Locale = "vi";

export const LOCALE_COOKIE = "NEXT_LOCALE";

/**
 * Resolves an arbitrary, possibly-untrusted value (cookie content, form
 * input) to a known Locale. Anything not in LOCALES — including undefined,
 * empty string, or an unsupported code — falls back to DEFAULT_LOCALE per
 * BR-003, so the page never renders blank on a bad cookie value.
 */
export function resolveLocale(value?: string): Locale {
  return LOCALES.includes(value as Locale) ? (value as Locale) : DEFAULT_LOCALE;
}
