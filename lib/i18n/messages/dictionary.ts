/**
 * Shape of a locale's message set. Fields are plain `string` (not literal
 * types via `as const`) so `en.ts` can satisfy the same type with different
 * copy while a missing/misspelled key is still a compile error.
 *
 * This is the compile-time contract for the homepage feature (F002): a key
 * added to `vi.ts`/`vi-home.ts` that is missing from `en.ts`/`en-home.ts`
 * fails `npm run typecheck` rather than falling back to a runtime blank.
 */

/**
 * The six award categories, in the design's fixed order. A string-literal
 * union (not a plain `string`) so a card missing from `home.awards.cards`
 * is a compile error rather than a silent gap in the grid.
 */
export type AwardKey =
  | "topTalent"
  | "topProject"
  | "topProjectLeader"
  | "bestManager"
  | "signature2025Creator"
  | "mvp";

export interface Dictionary {
  login: {
    logoAlt: string;
    wordmarkAlt: string;
    subtitle: string;
    tagline: string;
    signInButton: string;
    errorOauthFailed: string;
    languageLabel: string;
    languageVi: string;
    languageEn: string;
  };
  footer: {
    copyright: string;
    /** Fourth footer link — "Tiêu chuẩn chung" in the design. */
    standards: string;
  };
  todo: {
    title: string;
    signOut: string;
  };
  header: {
    logoAlt: string;
    about: string;
    awardInformation: string;
    kudos: string;
    notificationsLabel: string;
    notificationsEmpty: string;
    accountLabel: string;
    profile: string;
    signOut: string;
    adminDashboard: string;
  };
  home: {
    wordmarkAlt: string;
    comingSoon: string;
    days: string;
    hours: string;
    minutes: string;
    eventTimeLabel: string;
    eventTimeValue: string;
    eventVenueLabel: string;
    eventVenueValue: string;
    eventLivestream: string;
    ctaAwards: string;
    ctaKudos: string;
    rootFurther: {
      rootAlt: string;
      furtherAlt: string;
      /**
       * Renders in order. The design places the pull quote
       * (`quote` / `quoteSource`) after the 3rd paragraph (index 2), before
       * the two paragraphs that follow it.
       */
      paragraphs: string[];
      quote: string;
      quoteSource: string;
    };
    awards: {
      eyebrow: string;
      title: string;
      detailLabel: string;
      cards: Record<AwardKey, { title: string; description: string }>;
    };
    kudos: {
      eyebrow: string;
      title: string;
      subtitle: string;
      body: string;
      cta: string;
    };
    widget: {
      writeKudos: string;
      standards: string;
    };
  };
  /** Copy for the shared `ComingSoon` placeholder route shell (phase 07). */
  comingSoon: {
    title: string;
    body: string;
  };
}
