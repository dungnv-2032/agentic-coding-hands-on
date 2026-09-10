/**
 * Typed Supabase reads for the Open Secret Box screen (F009, phase 05, A1).
 *
 * Same discipline as `lib/rules/queries.ts` and `lib/profile/profile-queries.ts`:
 * the client is always an argument, never created here, and this module
 * assembles no view model — `page.tsx` (phase 06) turns the raw number into
 * `{ unopenedCount, canOpen, showSignIn }`.
 *
 * `sunnerId` always comes from `resolveViewer()` (technical-spec.md § 3.1
 * step 1), never from the sidebar's display-only seed fallback in
 * `lib/kudos/viewer.ts` — that fallback exists for the sidebar block only
 * and would let a session with no roster row read (and appear to own) the
 * seeded frame viewer's boxes.
 */

import type { SupabaseClient } from "@supabase/supabase-js";

import type { Database } from "@/lib/supabase/database.types";

/**
 * The caller's own `secret_box_unopened_count`. A missing row is `0`, not a
 * throw: technical-spec.md § 3.1 step 2 treats "no session" and "no roster
 * row yet" the same way — an inert, zero-count screen — and this read is the
 * one place that distinction collapses into a plain number.
 */
export async function fetchUnopenedCount(
  supabase: SupabaseClient<Database>,
  sunnerId: number,
): Promise<number> {
  const { data, error } = await supabase
    .from("sunners")
    .select("secret_box_unopened_count")
    .eq("id", sunnerId)
    .maybeSingle();

  if (error) throw new Error(`fetchUnopenedCount failed: ${error.message}`);
  return data?.secret_box_unopened_count ?? 0;
}
