import type { Dictionary } from "./vi";

/**
 * English copy, typed against the `vi` module's shape so a missing or
 * mistyped key is a compile error rather than a silent runtime fallback.
 *
 * `login.signInButton` intentionally stays "LOGIN With Google" in both
 * locales — it is design copy (a fixed brand string), not prose to translate.
 */
export const en: Dictionary = {
  login: {
    logoAlt: "Logo",
    wordmarkAlt: "ROOT FURTHER",
    subtitle: "Start your journey with SAA 2025.",
    tagline: "Sign in to explore!",
    signInButton: "LOGIN With Google",
    errorOauthFailed: "Sign-in failed. Please try again.",
    languageLabel: "Language",
    languageVi: "VN",
    languageEn: "EN",
  },
  footer: {
    copyright: "Copyright belongs to Sun* © 2025",
  },
  todo: {
    title: "To-do",
    signOut: "Sign out",
  },
};
