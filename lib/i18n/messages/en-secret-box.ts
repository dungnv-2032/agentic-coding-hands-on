import type { Dictionary } from "./dictionary";

/**
 * English Open Secret Box copy, typed against the shared
 * `Dictionary["secretBox"]` shape so a key missing here fails
 * `npm run typecheck`. A faithful translation of `vi-secret-box.ts`; vi is
 * authoritative and no e2e test asserts EN copy — same convention as
 * `en-rules.ts`.
 *
 * "Secret Box" stays untranslated as a product term, the same way
 * `writeKudosButton` keeps "Viết KUDOS" in both locales.
 */
export const enSecretBox: Dictionary["secretBox"] = {
  title: "DISCOVER YOUR SECRET BOX",
  instruction: "Click the box to open",
  countLabel: "Secretbox unopened",
  openerLabel: "Open Secret Box",
  closeLabel: "Close",
  signInPrompt: "Sign in to open your Secret Box",
  signInCta: "Sign in",
  badgeAltPrefix: "Badge",
  errorGeneric: "Something went wrong. Please try again.",
};
