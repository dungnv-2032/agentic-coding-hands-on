/**
 * Viewer identity for the Kudos Live Board (phase 04).
 *
 * Two separate notions, kept apart by function (and never merged — plan.md
 * § Key Insight 2 / test-contract.md ratification #4):
 *
 * - `resolveViewer()` is the AUTH-ONLY identity used for `canLike`. It never
 *   falls back to the seeded frame viewer; a session with no linked
 *   `sunners` row stays `sunnerId: null`, which correctly leaves every
 *   card's heart enabled (not disabled) for that session.
 * - `resolveSidebarSunnerId()` is the DISPLAY-ONLY fallback used for the
 *   sidebar block only. It must never feed `canLike`.
 *
 * The full Supabase `User` object (email, metadata, identities, ...) never
 * leaves this module. `resolveViewer()`'s `userId` is a bare auth uuid, not
 * that object — the same class of value as `sunnerId` — kept because
 * `kudos_likes.user_id` references `auth.users(id)` directly (schema
 * ratification #4), so both `queries.fetchViewerLikes()` and the
 * `toggleKudosLike` action need it. Only `isAuthenticated` and `sunnerId`
 * are ever copied into `KudosBoardViewModel.viewer` (the frozen contract) —
 * `userId` never crosses into that view model or any Client Component,
 * which is the property `app/_page-context.ts:22-25` actually protects.
 */

import type { SupabaseClient } from "@supabase/supabase-js";

import type { Database } from "@/lib/supabase/database.types";

export interface ViewerIdentity {
  isAuthenticated: boolean;
  /** Resolved solely from `sunners.auth_user_id = auth.uid()`. Never the seeded display fallback. */
  sunnerId: number | null;
  /** Raw auth uuid, or null with no session. Internal-only — never reaches the view model. */
  userId: string | null;
}

export async function resolveViewer(
  supabase: SupabaseClient<Database>,
): Promise<ViewerIdentity> {
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return { isAuthenticated: false, sunnerId: null, userId: null };
  }

  const { data: sunner, error } = await supabase
    .from("sunners")
    .select("id")
    .eq("auth_user_id", user.id)
    .maybeSingle();

  if (error) {
    throw new Error(`resolveViewer: sunners identity lookup failed: ${error.message}`);
  }

  return { isAuthenticated: true, sunnerId: sunner?.id ?? null, userId: user.id };
}

/**
 * Display-only fallback for the sidebar block: the identity sunner when one
 * resolved, else the seeded frame viewer.
 *
 * The seed currently leaves `auth_user_id` NULL on every seeded `sunners`
 * row (no mechanism links a freshly-signed-up e2e user to one), so "the
 * row with `auth_user_id IS NULL`" is not unique by itself. The frame
 * viewer (`Huỳnh Dương Xuân Nhật`) is the first row the seed inserts and is
 * the only one whose stored counters match the frame's verbatim
 * `25`s — `order by id asc limit 1` deterministically selects it without
 * depending on future rows staying unlinked.
 */
export async function resolveSidebarSunnerId(
  supabase: SupabaseClient<Database>,
  identitySunnerId: number | null,
): Promise<number> {
  if (identitySunnerId !== null) {
    return identitySunnerId;
  }

  const { data, error } = await supabase
    .from("sunners")
    .select("id")
    .is("auth_user_id", null)
    .order("id", { ascending: true })
    .limit(1)
    .maybeSingle();

  if (error) {
    throw new Error(`resolveSidebarSunnerId: fallback lookup failed: ${error.message}`);
  }
  if (!data) {
    throw new Error("resolveSidebarSunnerId: no seeded frame-viewer sunner row found");
  }

  return data.id;
}
