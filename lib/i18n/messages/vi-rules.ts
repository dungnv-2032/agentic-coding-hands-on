import type { Dictionary } from "./dictionary";

/**
 * Vietnamese Thể lệ panel chrome, transcribed verbatim from
 * `plans/260909-0838-the-le-rules-panel/clarifications.md § "Resolved from
 * source data"` (MoMorph screen `b1Filzi9i6`, frame node `3204:6051`).
 * Do not paraphrase — this is design copy.
 *
 * Sourced nodes: `panelTitle` `3204:6055`, `closeButton` `3204:6093`,
 * `writeKudosButton` `3204:6094`.
 *
 * BR-002 — chrome only. The three prose sections, the four Hero tiers and the
 * six collectible icons are rows in `rule_sections`/`rule_items`; they reach
 * the components through `lib/rules/view-model.ts` and must never be added
 * here.
 *
 * BR-003 — the rules body has no `locale` column, because the frame carries
 * Vietnamese copy only and inventing an English translation is inventing data.
 * Stated plainly rather than hidden: with `NEXT_LOCALE=en` the panel chrome is
 * English and the rules body stays Vietnamese. A `locale` column is a
 * one-migration change the day real English copy exists.
 */
export const viRules: Dictionary["rules"] = {
  panelTitle: "Thể lệ",
  closeButton: "Đóng",
  writeKudosButton: "Viết KUDOS",
};
