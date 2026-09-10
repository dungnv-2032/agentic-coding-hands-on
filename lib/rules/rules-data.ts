/**
 * `getRulesContent()` — assembles the frozen `RulesViewModel` (phase 01) from
 * the typed reads in `queries.ts`.
 *
 * One client per request (`lib/supabase/server.ts`), the two independent reads
 * run with `Promise.all`, the same shape `board-data.ts` and `profile-data.ts`
 * use. The page calls this with no arguments — the client is created here, so
 * nothing upstream has to thread one through.
 *
 * The `kind` split happens HERE and exactly once: components receive
 * `heroTiers` and `collectibleIcons` already separated and never filter rows
 * themselves (technical-spec § 4.2 "Polymorphic Behavior").
 *
 * Data layer only: it imports nothing from the i18n dictionary layer, and
 * every string it returns is database content. Panel chrome is dictionary
 * copy and travels the other way (BR-002).
 */

import type {
  RulesCollectibleIconView, RulesHeroTierView, RulesSectionView, RulesViewModel,
} from "@/lib/rules/view-model";
import { createClient } from "@/lib/supabase/server";

import type { RuleItemRow, RuleSectionRow } from "./queries";
import { RULE_ITEM_KIND, fetchRuleItems, fetchRuleSections } from "./queries";

function toSectionView(row: RuleSectionRow): RulesSectionView {
  return {
    position: row.position,
    heading: row.heading,
    body: row.body,
    // Only section 2 carries one; `null` hides the element rather than
    // rendering an empty paragraph.
    closingBody: row.closing_body,
  };
}

function toHeroTierView(row: RuleItemRow): RulesHeroTierView {
  return {
    position: row.position,
    label: row.label,
    // The column is nullable because collectible icons do not use it. A hero
    // tier missing its description still renders its label and image —
    // throwing here would turn one blank cell into a blank screen, which is
    // what functional-spec § 9 rules out.
    description: row.description ?? "",
    // FR-205 — the stored public path goes through untransformed.
    imagePath: row.image_path,
  };
}

function toIconView(row: RuleItemRow): RulesCollectibleIconView {
  return {
    position: row.position,
    caption: row.label,
    imagePath: row.image_path,
  };
}

/**
 * Read-only, per request. Empty tables yield three empty arrays, never a
 * throw: unseeded content is not an error (functional-spec § 9). A failed
 * query does throw — `fetchRuleSections failed: …` — because a database that
 * answers with an error is a different situation from one that answers with
 * nothing.
 */
export async function getRulesContent(): Promise<RulesViewModel> {
  const supabase = await createClient();

  const [sectionRows, itemRows] = await Promise.all([
    fetchRuleSections(supabase),
    fetchRuleItems(supabase),
  ]);

  const sections: RulesSectionView[] = sectionRows.map(toSectionView);
  const heroTiers: RulesHeroTierView[] = itemRows
    .filter((row) => row.kind === RULE_ITEM_KIND.heroTier)
    .map(toHeroTierView);
  const collectibleIcons: RulesCollectibleIconView[] = itemRows
    .filter((row) => row.kind === RULE_ITEM_KIND.collectibleIcon)
    .map(toIconView);

  return { sections, heroTiers, collectibleIcons };
}
