import type { AwardKey } from "./i18n/messages/dictionary";

/**
 * The six award categories, frozen in design order (plan.md — "Integration
 * contract"). Award *identity* (slug, dictionary key, image) lives here;
 * award *copy* (title, description) lives in the dictionary under
 * `home.awards.cards`, keyed by the same `AwardKey` — see
 * `app/_components/award-card.tsx` (phase 06), which zips the two together.
 */
export type AwardSlug =
  | "top-talent"
  | "top-project"
  | "top-project-leader"
  | "best-manager"
  | "signature-2025-creator"
  | "mvp";

export interface Award {
  /** URL fragment target: `/awards-information#<slug>` (FR-405). */
  slug: AwardSlug;
  /** Dictionary key into `home.awards.cards` for this award's copy. */
  key: AwardKey;
  /** Composed thumbnail exported by phase 03 (`award-<slug>.png`). */
  image: string;
}

export const AWARDS: readonly Award[] = [
  { slug: "top-talent", key: "topTalent", image: "/images/home/award-top-talent.png" },
  { slug: "top-project", key: "topProject", image: "/images/home/award-top-project.png" },
  {
    slug: "top-project-leader",
    key: "topProjectLeader",
    image: "/images/home/award-top-project-leader.png",
  },
  { slug: "best-manager", key: "bestManager", image: "/images/home/award-best-manager.png" },
  {
    slug: "signature-2025-creator",
    key: "signature2025Creator",
    image: "/images/home/award-signature-2025-creator.png",
  },
  { slug: "mvp", key: "mvp", image: "/images/home/award-mvp.png" },
] as const;
