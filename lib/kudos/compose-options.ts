/**
 * Server-only read for the compose screen's pickers (phase 07).
 *
 * `createClient()` itself imports `next/headers`, so this module cannot be
 * pulled into a Client Component without a build error — the same guard
 * `board-data.ts` relies on instead of the `server-only` package (not a
 * dependency of this project).
 *
 * Fetched once, at page render (`page.tsx`, phase 12) — ALG-001 filters
 * client-side thereafter, never a per-keystroke round trip.
 */

import type {
  ComposeHashtagOption,
  ComposeOptionsView,
  ComposeSunnerOption,
} from "@/lib/kudos/compose-contract";
import { createClient } from "@/lib/supabase/server";

export async function getComposeOptions(): Promise<ComposeOptionsView> {
  const supabase = await createClient();

  const [sunnersResult, hashtagsResult] = await Promise.all([
    supabase.from("sunners").select("id, full_name, avatar_url").order("full_name", { ascending: true }),
    supabase.from("hashtags").select("id, name").order("position", { ascending: true }),
  ]);

  if (sunnersResult.error) {
    throw new Error(`getComposeOptions (sunners) failed: ${sunnersResult.error.message}`);
  }
  if (hashtagsResult.error) {
    throw new Error(`getComposeOptions (hashtags) failed: ${hashtagsResult.error.message}`);
  }

  const recipients: ComposeSunnerOption[] = sunnersResult.data.map((row) => ({
    id: Number(row.id),
    fullName: row.full_name,
    avatarUrl: row.avatar_url,
  }));

  const hashtags: ComposeHashtagOption[] = hashtagsResult.data.map((row) => ({
    id: Number(row.id),
    name: row.name,
  }));

  return { recipients, hashtags };
}
