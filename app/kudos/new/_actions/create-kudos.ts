"use server";

/**
 * The only writer of a new Kudos (F005, `/kudos/new`). Follows
 * `toggleKudosLike`'s discipline: identity comes from the session only —
 * `ComposePayload` carries no sender field, so forging one is
 * unrepresentable in this API, and `create_kudos` (phase 03) re-checks
 * ownership at the database besides (Bin-3 rule; a forged `sender_id`
 * proved 403/42501 in phase 03's live verification).
 *
 * `ComposePayload` is untrusted — it arrives from a client component and
 * Server Functions are POST-reachable directly (forms.md:9-10) — so every
 * rule is re-checked here regardless of what the client already validated.
 *
 * No `revalidatePath`/`refresh()`: `/kudos` reads `cookies()` and is
 * already dynamic, and `next.config.ts` sets no `cacheComponents`, so there
 * is no cache entry to invalidate — the redirect's own render is already
 * fresh (write-path-conventions.md § 1). `toggleKudosLike` calls
 * `refresh()` because it stays on the page; this action leaves it, so it
 * doesn't.
 */

import { redirect } from "next/navigation";

import type {
  ComposeFieldErrors,
  ComposePayload,
  CreateKudosState,
} from "@/lib/kudos/compose-contract";
import { isOwnStorageUrl, validateCompose } from "@/lib/kudos/validate-compose";
import { createClient } from "@/lib/supabase/server";

/** Postgres SQLSTATEs `create_kudos` raises (`supabase/migrations/20260907025909_viet_kudo_write_path.sql`). */
const NO_SESSION_ERRCODE = "28000";
const CHECK_VIOLATION_ERRCODE = "23514";

/** No design/spec length cap exists for the anonymous name (clarifications.md § Unresolved question 4) — a defensive boundary length, not a business rule. */
const ANONYMOUS_NAME_MAX_LENGTH = 100;

function supabaseOrigin(): string {
  return new URL(process.env.NEXT_PUBLIC_SUPABASE_URL ?? "http://127.0.0.1:54321").origin;
}

/**
 * Maps `create_kudos`'s raised errcode to a field code. `hashtagCount` is
 * already known-valid (1-5) by the time this runs, since `validateCompose`
 * ran first — the hashtag-count branch below is therefore a defense-in-depth
 * backstop for a direct RPC caller, not a path this action's own client can
 * reach. The raw database message is logged, never returned to the client.
 */
function mapDatabaseError(
  error: { code?: string; message: string },
  hashtagCount: number,
): ComposeFieldErrors {
  if (error.code === NO_SESSION_ERRCODE) {
    return { form: "unknown" };
  }
  if (error.code === CHECK_VIOLATION_ERRCODE && error.message.includes("hashtag")) {
    return { hashtag: hashtagCount > 5 ? "tooMany" : "required" };
  }
  console.error("createKudos: create_kudos rpc failed", error);
  return { form: "unknown" };
}

export async function createKudos(
  _prevState: CreateKudosState,
  payload: ComposePayload,
): Promise<CreateKudosState> {
  const supabase = await createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return { errors: { form: "unknown" } };
  }

  const errors = validateCompose(payload);
  if (Object.keys(errors).length > 0) {
    return { errors };
  }

  const origin = supabaseOrigin();
  if (!payload.imageUrls.every((url) => isOwnStorageUrl(url, origin))) {
    // A forged image URL: the object could not exist any other way —
    // `uploadKudosImage` validates MIME before it's ever written.
    return { errors: { form: "unknown" } };
  }

  const anonymousName = payload.isAnonymous
    ? (payload.anonymousName?.trim().slice(0, ANONYMOUS_NAME_MAX_LENGTH) ?? "")
    : "";

  const { data: kudosId, error } = await supabase.rpc("create_kudos", {
    p_receiver_id: payload.receiverId,
    p_campaign: payload.title.trim(),
    p_message: JSON.stringify(payload.doc),
    p_message_format: "doc",
    p_is_anonymous: payload.isAnonymous,
    // Codegen types this param as a non-nullable `string` (Postgres function
    // arguments carry no nullability info the generator can read), so a
    // blank name is sent as "" rather than `null`. The read side already
    // treats both identically (`board-data.ts:97`'s `?.trim() || fallback`).
    p_anonymous_name: anonymousName,
    p_hashtag_ids: payload.hashtagIds,
    p_image_urls: payload.imageUrls,
  });

  if (error || typeof kudosId !== "number") {
    return { errors: mapDatabaseError(error ?? { message: "create_kudos returned no id" }, payload.hashtagIds.length) };
  }

  // Top level, outside every try — `redirect()` throws a framework
  // control-flow exception; a catch here would swallow it after the row
  // was already written (mutating-data.md:504, "any code after it won't
  // execute").
  redirect("/kudos");
}
