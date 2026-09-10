/**
 * Typed Supabase reads for the Thể lệ rules panel (F007, phase 04).
 *
 * Every function takes the client as an argument, so `rules-data.ts` creates
 * one per request and runs the two independent reads with `Promise.all`. Raw
 * row shapes only — `rules-data.ts` owns the frozen `RulesViewModel`, and no
 * database row ever reaches a component.
 *
 * `rule_sections` and `rule_items` are FLAT tables with no embed and no view,
 * so both reuse the generated `Database[...]["Row"]` types through the local
 * `Row<T>` alias. A hand-written interface plus `.returns<T[]>()` is reserved
 * for FK-hinted embeds and views (`kudos_readable`) where postgrest-js cannot
 * infer the shape; using one here would only invite drift from the schema.
 *
 * Both reads sort by `position` ascending, always (BR-001): the render order
 * is data, never `id` and never insertion order.
 */

import type { SupabaseClient } from "@supabase/supabase-js";

import type { Database } from "@/lib/supabase/database.types";

type Row<T extends keyof Database["public"]["Tables"]> = Database["public"]["Tables"][T]["Row"];

export type RuleSectionRow = Row<"rule_sections">;
export type RuleItemRow = Row<"rule_items">;

/**
 * `rule_items.kind` is a `text` column with a `check` constraint, not a
 * Postgres enum, so the generated type is plain `string`. These are the two
 * legal values, single-sourced here rather than sprinkled as literals.
 */
export const RULE_ITEM_KIND = {
  heroTier: "hero_tier",
  collectibleIcon: "collectible_icon",
} as const;

/** The three prose sections, ascending `position` (FR-202, BR-001). */
export async function fetchRuleSections(
  supabase: SupabaseClient<Database>,
): Promise<RuleSectionRow[]> {
  const { data, error } = await supabase
    .from("rule_sections")
    .select("*")
    .order("position", { ascending: true });

  if (error) throw new Error(`fetchRuleSections failed: ${error.message}`);
  // An empty table is content that has not been seeded yet, not a failure
  // (functional-spec § 9): the panel still renders its chrome.
  return data ?? [];
}

/**
 * Hero tiers and collectible icons in ONE read — they are one table
 * discriminated by `kind` (technical-spec § 4.2). `rules-data.ts` splits them
 * exactly once; `position` runs an independent sequence per kind, so the
 * ascending sort holds within each group after the split.
 */
export async function fetchRuleItems(
  supabase: SupabaseClient<Database>,
): Promise<RuleItemRow[]> {
  const { data, error } = await supabase
    .from("rule_items")
    .select("*")
    .order("position", { ascending: true });

  if (error) throw new Error(`fetchRuleItems failed: ${error.message}`);
  return data ?? [];
}
