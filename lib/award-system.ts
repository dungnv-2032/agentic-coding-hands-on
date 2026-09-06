import type { AwardKey } from "./i18n/messages/dictionary";

/**
 * Structural facts the Award System screen (F003) needs on top of the award
 * identity already frozen in `lib/awards.ts`.
 *
 * Deliberately does NOT redefine `AwardSlug` / `AwardKey` / `AWARDS`: the
 * homepage deep-links to `/awards-information#<slug>` from
 * `app/_components/award-card.tsx`, so a second slug list here would silently
 * strand those links the moment the two drift. Iterate `AWARDS` for order and
 * identity; read this module only for the unit.
 *
 * Unit is split across two modules on purpose (clarifications § "Where does
 * the award detail copy live"): *which* unit an award has never changes with
 * the locale and lives here; *how that unit reads* ("Cá nhân" / "Individual")
 * is copy and lives in `dictionary.awardSystem.units` (FR-002).
 */
export type AwardUnitKey = "individual" | "team" | "individualOrTeam";

/**
 * Award → unit, transcribed from clarifications § "The six awards" (D.1–D.6).
 * `Record<AwardKey, …>` is exhaustive, so a seventh award added to `AwardKey`
 * fails to compile until its unit is declared here.
 */
export const AWARD_UNITS: Record<AwardKey, AwardUnitKey> = {
  topTalent: "individual",
  topProject: "team",
  topProjectLeader: "individual",
  bestManager: "individual",
  signature2025Creator: "individualOrTeam",
  mvp: "individual",
};
