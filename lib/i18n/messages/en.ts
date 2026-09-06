import type { Dictionary } from "./dictionary";
import { enAwardSystem } from "./en-award-system";
import { enHome } from "./en-home";
import { enKudos } from "./en-kudos";

/**
 * English copy, typed against the shared `Dictionary` shape so a missing or
 * mistyped key is a compile error rather than a silent runtime fallback.
 *
 * `login.signInButton` intentionally stays "LOGIN With Google" in both
 * locales — it is design copy (a fixed brand string), not prose to translate.
 * The same applies to `header.about`/`header.awardInformation`/`header.kudos`:
 * the design shows the nav labels in English in both locales.
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
    standards: "General Standards",
  },
  todo: {
    title: "To-do",
    signOut: "Sign out",
  },
  header: {
    logoAlt: "Sun* Annual Awards 2025",
    about: "About SAA 2025",
    awardInformation: "Award Information",
    kudos: "Sun* Kudos",
    notificationsLabel: "Notifications",
    notificationsEmpty: "No new notifications",
    accountLabel: "Account",
    profile: "Profile",
    signOut: "Sign out",
    adminDashboard: "Admin Dashboard",
  },
  home: enHome,
  awardSystem: enAwardSystem,
  comingSoon: {
    title: "Coming soon",
    body: "This content is being updated. Please check back soon.",
  },
  kudos: enKudos,
};
