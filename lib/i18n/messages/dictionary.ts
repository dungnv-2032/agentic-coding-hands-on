/**
 * Shape of a locale's message set. Fields are plain `string` (not literal
 * types via `as const`) so `en.ts` can satisfy the same type with different
 * copy while a missing/misspelled key is still a compile error.
 *
 * This is the compile-time contract for the homepage feature (F002): a key
 * added to `vi.ts`/`vi-home.ts` that is missing from `en.ts`/`en-home.ts`
 * fails `npm run typecheck` rather than falling back to a runtime blank.
 */

import type { AwardUnitKey } from "../../award-system";
import type { ComposeFieldErrorCode } from "../../kudos/compose-contract";
import type { LinkFieldError } from "../../kudos/validate-link";

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
      /** `aria-label` of the collapsed pill acting as the disclosure trigger. */
      trigger: string;
      /** Visible label on the expanded menu's `Thể lệ` button. */
      menuStandards: string;
      /** Visible label on the expanded menu's `Viết KUDOS` button. */
      menuWriteKudos: string;
      /** `aria-label` of the icon-only round close button. */
      close: string;
    };
  };
  /**
   * Award System screen copy (F003). Keyed by the same `AwardKey` as
   * `home.awards.cards` so the two screens can never disagree about which six
   * awards exist — `lib/awards.ts` stays the single source of slug/image
   * identity and iteration order.
   *
   * `units` is keyed by `AwardUnitKey` (`lib/award-system.ts`) rather than
   * repeating "Cá nhân" on four cards: which unit an award has is structural,
   * how that unit reads is copy that must translate (FR-002).
   */
  awardSystem: {
    hero: { eyebrow: string; title: string; wordmarkAlt: string };
    /**
     * Accessible name for the category `<nav>` landmark. Its own key rather
     * than a reuse of `hero.title`: the page carries three `<nav>` landmarks
     * (header, this one, footer), so each needs a name that says what it
     * navigates. Borrowing the `<h1>` text named the landmark after the page
     * instead of after the menu.
     */
    navAriaLabel: string;
    quantityLabel: string;
    prizeLabel: string;
    /** Separator between Signature's two prize rows ("Hoặc"). */
    prizeOr: string;
    units: Record<AwardUnitKey, string>;
    cards: Record<
      AwardKey,
      {
        /** Card heading — also the award image's alt text (test contract). */
        title: string;
        /** Left-menu label. Differs from `title` for signature2025Creator + mvp. */
        navLabel: string;
        /** One or two paragraphs, rendered in order. */
        paragraphs: string[];
        /** String, not number: the design renders the leading zero ("02"). */
        quantity: string;
        /**
         * BR-004 — one row for four awards, two for Signature. `note` is
         * optional so "Best Manager carries no note line" is a type-level
         * fact; `note: ""` would still render an empty note element.
         */
        prizes: Array<{ amount: string; note?: string }>;
      }
    >;
  };
  /** Copy for the shared `ComingSoon` placeholder route shell (phase 07). */
  comingSoon: {
    title: string;
    body: string;
  };
  /**
   * Sun* Kudos - Live board copy (F004, screen `MaZUn5xHXZ`). Badge tier
   * names/tooltips are NOT here — they flow via the frozen
   * `lib/kudos/view-model.ts` + `derive.ts`. Spotlight `388 KUDOS` is a
   * seeded DB value, not copy (test-contract.md ratification 2026-09-06c).
   */
  kudos: {
    /** `hero.title` is the page's only `<h1>`. */
    hero: { title: string; composePlaceholder: string; searchPlaceholder: string };
    /** Shared eyebrow above all three section headings. */
    eyebrow: string;
    sections: { highlight: string; spotlight: string; allKudos: string };
    filters: { hashtag: string; department: string };
    /** `viewDetail` is highlight-carousel-only (test-contract § Kudos card). */
    card: { copyLink: string; viewDetail: string; empty: string };
    spotlightBoard: {
      searchPlaceholder: string;
      /** Accessible label and `title` tooltip. */
      panZoom: string;
      /** Appended after "{timeLabel} {name}" to form one ticker sentence. */
      tickerSuffix: string;
      empty: string;
    };
    sidebar: {
      /** Five rows, in the test contract's exact order. */
      stats: {
        kudosReceived: string;
        kudosSent: string;
        heartsReceived: string;
        secretBoxOpened: string;
        secretBoxUnopened: string;
      };
      secretBoxButton: string;
      giftHeading: string;
      giftEmpty: string;
    };
    toast: { copySuccess: string; copyFailure: string };
  };
  /**
   * Profile bản thân screen copy (F006, screen `3FoIx6ALVb`). Badge tier
   * names/tooltips are NOT here — they flow via the frozen
   * `lib/kudos/view-model.ts` + `derive.ts`, same as `kudos` above.
   *
   * `badges.headingSelf`/`headingOther` and `feed.emptyReceived`/`emptySent`
   * are deliberately two keys each — the copy differs by viewer face
   * (clarifications.md § "Badge collection and hero tier", § "KUDOS
   * section") — never collapsed into one key with a runtime branch.
   */
  profile: {
    badges: { headingSelf: string; headingOther: string };
    /** Five rows; wording matches `kudos.sidebar.stats` verbatim (same board). */
    stats: {
      kudosReceived: string;
      kudosSent: string;
      heartsReceived: string;
      secretBoxOpened: string;
      secretBoxUnopened: string;
      secretBoxButton: string;
    };
    /** Carries "{name}" — the write-Kudo bar shown on another Sunner's profile. */
    writeBar: { label: string };
    /** Each carries "{count}" — the direction dropdown's two options. */
    direction: { receivedLabel: string; sentLabel: string };
    feed: { emptyReceived: string; emptySent: string; endOfFeed: string };
  };
  /**
   * Viết Kudo compose screen copy (F005, screen `ihQ26W78P2`, `/kudos/new`).
   * Hashtag names, recipient names and any other DB-sourced values are data
   * (from the `hashtags`/`sunners` tables), never copy — this namespace
   * holds only static UI text.
   *
   * `errors` is keyed by `ComposeFieldErrorCode`
   * (`lib/kudos/compose-contract.ts`, frozen) rather than by field, so
   * `Không được để trống` is written once and reused by all four required
   * fields (recipient/title/body/hashtag) instead of four separate copies
   * of the same literal.
   */
  kudosCompose: {
    /** The page's only `<h1>`. */
    title: string;
    /** The four fields the frame gives their own label + `*`. */
    labels: {
      recipient: string;
      title: string;
      body: string;
      hashtag: string;
      image: string;
    };
    placeholders: {
      recipient: string;
      title: string;
      body: string;
      /** Unauthored — the reveal-on-check name field has no design source. */
      anonymousName: string;
    };
    hints: {
      titleLine1: string;
      titleLine2: string;
      body: string;
    };
    buttons: {
      addHashtag: string;
      addImage: string;
      max: string;
      /** Also reused by `linkDialog`'s cancel action — same word, one key. */
      cancel: string;
      submit: string;
    };
    /** Rich-text toolbar button accessible names. */
    toolbar: {
      bold: string;
      italic: string;
      strike: string;
      orderedList: string;
      link: string;
      quote: string;
    };
    /**
     * Addlink Box (MoMorph `OyDLDuSGEa`, spec-delta FR-213..FR-219): `heading`/
     * `textLabel`/`urlLabel`/`confirm` are authored copy (frame items A/B.1/C.1/D.2,
     * vi verbatim from the frame image, en from spec item A/B/C/D). `errors` has no
     * design source — the frame carries no error state — flagged unauthored where used.
     */
    linkDialog: {
      heading: string;
      textLabel: string;
      urlLabel: string;
      confirm: string;
      /** Unauthored — keyed by `LinkFieldError` (validate-link.ts). */
      errors: Record<LinkFieldError, string>;
    };
    errors: Record<ComposeFieldErrorCode, string>;
    /** The `recipient-empty` text. */
    recipientEmpty: string;
    /** Unauthored (test-contract.md ratification item 6) — ships anyway. */
    communityStandards: string;
    anonymousCheckboxLabel: string;
    /** Unauthored — the reveal-on-check name field's own label. */
    anonymousNameLabel: string;
    /** The loading/pending state shown after pressing Gửi. */
    submitPending: string;
    /**
     * Live Board card fallback for an anonymous sender whose display name
     * was left blank (phase 04 consumes this).
     */
    anonymousFallbackName: string;
  };
  /**
   * Thể lệ rules panel copy (F007, screen `b1Filzi9i6`, frame `3204:6051`,
   * `/standards`).
   *
   * BR-002 draws the line this block must not cross: chrome lives here, the
   * rules body lives in the database. The three prose sections, the four Hero
   * tiers and the six collectible icons are rows in
   * `rule_sections`/`rule_items` and reach the components through the frozen
   * `lib/rules/view-model.ts` — never through a key added below.
   */
  rules: {
    /** Panel title — rendered as the page's `<h1>` (FR-201). */
    panelTitle: string;
    closeButton: string;
    writeKudosButton: string;
  };
  /**
   * Open Secret Box screen copy (F009, screen `J3-4YFIpMM`, frame `1466:7676`,
   * `/kudos/secret-box`). Badge labels are NOT here — they come from
   * `rule_items.label` (`kind = 'collectible_icon'`), the same catalogue the
   * Thể lệ screen reads, per BR-005.
   */
  secretBox: {
    /** The page's only `<h1>` (mm:1466:7678, FR-101). */
    title: string;
    /** Hidden when the viewer's unopened count is 0 (mm:1466:7683, FR-102). */
    instruction: string;
    /** Label beside the counter value (mm:1466:7692, FR-104). */
    countLabel: string;
    /** Accessible name of the clickable box control. Unauthored — the frame draws no separate a11y text. */
    openerLabel: string;
    /** Accessible name of the `X` close glyph (mm:1466:7679). Unauthored. */
    closeLabel: string;
    /** Shown to a signed-out visitor alongside the sign-in link (FR-105). Unauthored. */
    signInPrompt: string;
    /** The sign-in link's own label (FR-105). Unauthored. */
    signInCta: string;
    /**
     * Prefix for an auxiliary accessible description of the awarded badge
     * (e.g. an sr-only caption built by the consuming component) — NOT the
     * `alt` attribute on the `secret-box-badge` image itself, which must
     * equal `rule_items.label` verbatim (BR-005, e2e SB-03). Unauthored.
     */
    badgeAltPrefix: string;
    /** Shown when `openSecretBox()` resolves `{ ok: false, reason: 'failed' }`. Unauthored. */
    errorGeneric: string;
  };
}
