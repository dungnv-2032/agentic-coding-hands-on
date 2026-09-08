"use server";

import type { SupabaseClient } from "@supabase/supabase-js";
import { refresh } from "next/cache";

import { resolveViewer } from "@/lib/kudos/viewer";
import type { KudosLikeResult } from "@/lib/kudos/view-model";
import type { Database } from "@/lib/supabase/database.types";
import { createClient } from "@/lib/supabase/server";

/** A double click racing the `(kudos_id, user_id)` unique constraint (plan.md § Key Insight 7). */
const UNIQUE_VIOLATION = "23505";

interface KudosHeartRow {
  heart_baseline: number;
  likes: { count: number }[];
}

/** The database's own authoritative `{liked, hearts}` — never assumed client-side. */
async function readHeartState(
  supabase: SupabaseClient<Database>,
  kudosId: number,
  userId: string | null,
): Promise<KudosLikeResult> {
  const { data: kudosRow, error: kudosError } = await supabase
    .from("kudos_readable")
    .select("heart_baseline, likes:kudos_likes(count)")
    .eq("id", kudosId)
    .maybeSingle()
    .returns<KudosHeartRow>();

  if (kudosError || !kudosRow) {
    return { liked: false, hearts: 0 };
  }

  const hearts = kudosRow.heart_baseline + (kudosRow.likes[0]?.count ?? 0);

  if (!userId) {
    return { liked: false, hearts };
  }

  const { data: likeRow } = await supabase
    .from("kudos_likes")
    .select("id")
    .eq("kudos_id", kudosId)
    .eq("user_id", userId)
    .maybeSingle();

  return { liked: Boolean(likeRow), hearts };
}

/**
 * The only writer on `/kudos`. The acting user always comes from the
 * session, never from an argument (plan.md § Key Insight 6) — RLS re-checks
 * both identity and BR-003, but this action does not lean on that as its
 * only guard, and it never lets a write-path error crash the caller: every
 * rejected or failed path still returns the database's real current state.
 */
export async function toggleKudosLike(kudosId: number): Promise<KudosLikeResult> {
  const supabase = await createClient();

  if (!Number.isInteger(kudosId) || kudosId <= 0) {
    // Malformed input fails here, before it becomes a database round trip.
    return { liked: false, hearts: 0 };
  }

  const viewer = await resolveViewer(supabase);
  if (!viewer.isAuthenticated || !viewer.userId) {
    return readHeartState(supabase, kudosId, null);
  }

  const { data: kudosRow, error: kudosError } = await supabase
    .from("kudos_readable")
    .select("sender_id")
    .eq("id", kudosId)
    .maybeSingle();

  if (kudosError || !kudosRow) {
    return readHeartState(supabase, kudosId, viewer.userId);
  }

  if (viewer.sunnerId !== null && viewer.sunnerId === kudosRow.sender_id) {
    // BR-003 — cannot like your own kudos. App-level guard; RLS enforces it too.
    return readHeartState(supabase, kudosId, viewer.userId);
  }

  try {
    const { data: existingLike } = await supabase
      .from("kudos_likes")
      .select("id")
      .eq("kudos_id", kudosId)
      .eq("user_id", viewer.userId)
      .maybeSingle();

    if (existingLike) {
      const { error: deleteError } = await supabase
        .from("kudos_likes")
        .delete()
        .eq("id", existingLike.id);
      if (deleteError) throw deleteError;
    } else {
      const { error: insertError } = await supabase
        .from("kudos_likes")
        .insert({ kudos_id: kudosId, user_id: viewer.userId });
      if (insertError && insertError.code !== UNIQUE_VIOLATION) {
        throw insertError;
      }
    }
  } catch (error) {
    console.error("toggleKudosLike: write failed", error);
    return readHeartState(supabase, kudosId, viewer.userId);
  }

  const result = await readHeartState(supabase, kudosId, viewer.userId);
  refresh();
  return result;
}
