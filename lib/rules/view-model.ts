/**
 * Frozen integration contract for the Thể lệ rules panel (F007, phase 01,
 * screen `b1Filzi9i6`, frame `3204:6051`).
 *
 * Types only — no runtime export, no `next/*`, no `@/lib/supabase/*`, no
 * React. Track B (phase 03/04) PRODUCES a `RulesViewModel` from Supabase
 * reads; Track A (phases 05-07) CONSUMES it as props. Neither track imports
 * the other — this file is the only thing both sides depend on, the same role
 * `lib/kudos/view-model.ts` and `lib/profile/profile-view-model.ts` play for
 * F004 and F006.
 *
 * A missing field here is escalated to the orchestrator, which amends this
 * phase's contract once and notifies both tracks — never patched
 * unilaterally inside a track (plan.md § Risk Assessment).
 *
 * The shape is page-shaped, not row-shaped: `rule_items.kind` is a schema
 * concern, so `rules-data.ts` splits the rows into `heroTiers` and
 * `collectibleIcons` exactly once and no component ever filters
 * (technical-spec § 4.2 "Polymorphic Behavior").
 *
 * NONE of the strings below are i18n copy — every one is database content
 * read from `rule_sections` / `rule_items` (BR-002). Panel chrome (title,
 * button labels, aria labels) travels the other way, through
 * `Dictionary["rules"]`.
 */

export interface RulesSectionView {
  /** `rule_sections.position` — ascending render order (BR-001). */
  position: number;
  heading: string;
  body: string;
  /**
   * The closing line rendered AFTER the section's list, not after its body.
   * Only section 2 has one (`Những Sunner thu thập trọn bộ 6 icon…`), so
   * `null` is the normal case and hides the element rather than rendering
   * an empty paragraph.
   */
  closingBody: string | null;
}

export interface RulesHeroTierView {
  /** `rule_items.position` within `kind = 'hero_tier'` (BR-001). */
  position: number;
  /** The threshold line, e.g. `Có 1-4 người gửi Kudos cho bạn`. */
  label: string;
  /**
   * Non-nullable here even though `rule_items.description` is nullable:
   * the column is nullable because collectible icons do not use it, and
   * a hero tier always does. The view-model knows which `kind` fills which
   * column, so the branch is resolved once in `rules-data.ts`.
   */
  description: string;
  /** Path under `public/images/rules/`, e.g. `/images/rules/…png` (FR-205). */
  imagePath: string;
}

export interface RulesCollectibleIconView {
  /** `rule_items.position` within `kind = 'collectible_icon'` (BR-001). */
  position: number;
  /** The uppercase caption, e.g. `REVIVAL`. Verbatim from the frame. */
  caption: string;
  /** Path under `public/images/rules/` (FR-205). */
  imagePath: string;
}

export interface RulesViewModel {
  /** Three prose sections, ascending `position` (FR-202). */
  sections: readonly RulesSectionView[];
  /** Four Hero tiers, ascending `position` (FR-203). */
  heroTiers: readonly RulesHeroTierView[];
  /** Six collectible icons, ascending `position` (FR-204). */
  collectibleIcons: readonly RulesCollectibleIconView[];
}
