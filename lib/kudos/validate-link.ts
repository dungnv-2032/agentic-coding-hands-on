/**
 * Field validation for the Addlink Box (F005 spec delta, `OyDLDuSGEa`).
 * Pure, no React / no I/O — mirrors the "no second allow-list" rule: URL
 * scheme checking reuses `ACCEPTED_LINK_SCHEMES` from `compose-contract.ts`
 * rather than redeclaring it here.
 */
import { ACCEPTED_LINK_SCHEMES } from "./compose-contract";

export const LINK_TEXT_MIN = 1;
export const LINK_TEXT_MAX = 100;
export const LINK_URL_MIN = 5;
export const LINK_URL_MAX = 2048;

export type LinkFieldError = "required" | "tooShort" | "tooLong" | "invalidUrl";

/** `required` on whitespace-only (trimmed empty); `tooLong` measured on the raw value. */
export function validateLinkText(value: string): LinkFieldError | undefined {
  if (value.trim().length === 0) return "required";
  if (value.length > LINK_TEXT_MAX) return "tooLong";
  return undefined;
}

/** Checks run most-specific-first: required → length → format, so only one message ever wins. */
export function validateLinkUrl(value: string): LinkFieldError | undefined {
  if (value.trim().length === 0) return "required";
  if (value.length < LINK_URL_MIN) return "tooShort";
  if (value.length > LINK_URL_MAX) return "tooLong";
  if (!isAcceptedLinkUrl(value)) return "invalidUrl";
  return undefined;
}

function isAcceptedLinkUrl(value: string): boolean {
  try {
    return (ACCEPTED_LINK_SCHEMES as readonly string[]).includes(new URL(value).protocol);
  } catch {
    return false;
  }
}

/** Backs the dialog's per-field error display (FR-216): keys omitted when valid. */
export function validateLinkFields(text: string, url: string): { text?: LinkFieldError; url?: LinkFieldError } {
  const textError = validateLinkText(text);
  const urlError = validateLinkUrl(url);
  return { ...(textError ? { text: textError } : {}), ...(urlError ? { url: urlError } : {}) };
}
