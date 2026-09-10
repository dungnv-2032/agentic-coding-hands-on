import type { Dictionary } from "./dictionary";

/**
 * English Thể lệ panel chrome, typed against the shared `Dictionary["rules"]`
 * shape so a key missing here fails `npm run typecheck`. A faithful
 * translation of `vi-rules.ts`; vi is authoritative and no test asserts EN
 * copy — same convention as `en-profile.ts`.
 *
 * `writeKudosButton` deliberately stays "Viết KUDOS" in both locales, for the
 * same reason `login.signInButton` stays "LOGIN With Google": it is design
 * copy / a product name on the frame (`3204:6094`), not prose to translate.
 *
 * BR-003 applies here too — translating the chrome does NOT translate the
 * rules body, which is Vietnamese-only database content. Under
 * `NEXT_LOCALE=en` the panel reads English chrome over a Vietnamese body.
 */
export const enRules: Dictionary["rules"] = {
  panelTitle: "Rules",
  closeButton: "Close",
  writeKudosButton: "Viết KUDOS",
};
