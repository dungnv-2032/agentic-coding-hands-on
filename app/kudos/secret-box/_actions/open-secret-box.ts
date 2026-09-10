"use server";

/**
 * The only writer for Open Secret Box (F009, `/kudos/secret-box`). Follows
 * `toggleKudosLike`'s discipline: no identity input at all, not even the
 * `sunnerId` `toggleKudosLike` receives implicitly through RLS — the actor
 * comes solely from the session `supabase.rpc("open_secret_box")` reads on
 * the database side (`auth.uid()`), so forging one is unrepresentable rather
 * than merely rejected (SB-08, technical-spec.md § 3.2).
 *
 * `open_secret_box()` `returns table (...)`, so a successful call always
 * hands back an ARRAY of rows (never a single object) — `data?.[0]` reads
 * the one row the guarded UPDATE ever produces, and an empty array (should
 * the RPC ever return zero rows without an error) is treated the same as
 * any other unmapped failure rather than assumed non-empty.
 *
 * Errors are mapped by Postgres `code`, never by message text, because the
 * three errcodes are fixed by the migration
 * (`supabase/migrations/20260910170000_secret_box_open_path.sql`) and a
 * wording change there must not silently reclassify a known case as
 * `failed`. The raw Postgres error never crosses into the returned
 * `OpenSecretBoxResult` — only `console.error` sees it, server-side.
 */

import { revalidatePath } from "next/cache";

import type { OpenSecretBoxResult } from "@/lib/secret-box/contract";
import { createClient } from "@/lib/supabase/server";

/** `auth.uid()` was null inside the function — no session at all (`28000`, invalid_authorization_specification). */
const UNAUTHENTICATED_ERRCODE = "28000";
/** The guarded `UPDATE ... WHERE secret_box_unopened_count > 0` matched no row — zero boxes left, or lost the concurrent-open race (`P0002`, no_data_found). */
const NO_BOXES_ERRCODE = "P0002";

const ROUTES_TO_REVALIDATE = ["/kudos/secret-box", "/kudos", "/profile"] as const;

export async function openSecretBox(): Promise<OpenSecretBoxResult> {
  const supabase = await createClient();

  const { data, error } = await supabase.rpc("open_secret_box");

  if (error) {
    if (error.code === UNAUTHENTICATED_ERRCODE) {
      return { ok: false, reason: "unauthenticated" };
    }
    if (error.code === NO_BOXES_ERRCODE) {
      return { ok: false, reason: "no-boxes" };
    }
    // Anything else (an empty odds table, a network error, a future errcode
    // this action does not yet know about) — logged with the errcode only,
    // never the message text, which could carry column/table detail.
    console.error("openSecretBox: rpc failed", error.code);
    return { ok: false, reason: "failed" };
  }

  const row = data?.[0];
  if (!row) {
    console.error("openSecretBox: rpc returned no row on success");
    return { ok: false, reason: "failed" };
  }

  // Only after a confirmed success: a rejected or failed call must not
  // invalidate three route caches for nothing.
  for (const route of ROUTES_TO_REVALIDATE) revalidatePath(route);

  return {
    ok: true,
    badge: {
      ruleItemId: row.rule_item_id,
      label: row.label,
      imagePath: row.image_path,
    },
    unopenedCount: row.unopened_count,
    openedCount: row.opened_count,
  };
}
