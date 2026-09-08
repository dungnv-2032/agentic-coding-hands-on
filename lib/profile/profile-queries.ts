/**
 * Typed Supabase reads for the Profile bản thân screen (F006 phase 05).
 *
 * Same role as `lib/kudos/queries.ts`: the client is always an argument, so
 * one is created per request and the independent reads run under one
 * `Promise.all`. Nothing here assembles a view model.
 *
 * EVERY Kudos read goes through `public.kudos_readable` — never
 * `public.kudos`, whose `select` is revoked from `anon`/`authenticated`
 * (`20260908100000_profile_reader_view.sql`). The five `sender_*` columns
 * arrive already masked; a null among them is final, never re-queried. The
 * `sunners` read selects only the columns FR-603 allows — no `auth_user_id`,
 * and the table carries no email column at all.
 */

import type { SupabaseClient } from "@supabase/supabase-js";

import { FEED_PAGE_SIZE } from "@/lib/kudos/derive";
import { KUDOS_FEED_SELECT, type KudosFeedRow } from "@/lib/kudos/queries";
import type { Database } from "@/lib/supabase/database.types";
import type { FeedCursor } from "@/lib/profile/profile-view-model";

/** FR-603's allowed profile columns, and nothing else. `department` is the one embed. */
const PROFILE_SUNNER_SELECT =
  "id, full_name, avatar_url, kudos_received_baseline, secret_box_opened_count, secret_box_unopened_count, department:departments(name)";

export interface ProfileSunnerRow {
  id: number;
  full_name: string;
  avatar_url: string;
  kudos_received_baseline: number;
  secret_box_opened_count: number;
  secret_box_unopened_count: number;
  /** The only embed — `sunners.department_id` is a plain FK, so the hint resolves. */
  department: { name: string } | null;
}

/** The target profile, or `null` when no row matches — `notFound()` is the page's decision (FR-402), not a throw here. */
export async function fetchProfileSunner(
  supabase: SupabaseClient<Database>, sunnerId: number,
): Promise<ProfileSunnerRow | null> {
  const { data, error } = await supabase
    .from("sunners")
    .select(PROFILE_SUNNER_SELECT)
    .eq("id", sunnerId)
    .maybeSingle()
    .returns<ProfileSunnerRow | null>();

  if (error) throw new Error(`fetchProfileSunner failed: ${error.message}`);
  return data;
}

export interface ReceivedAggregate {
  count: number;
  hearts: number;
}
/**
 * BR-003/BR-004 — received count and heart total for one Sunner in one read,
 * using the board's exact `heart_baseline + likes` formula so the two
 * surfaces cannot print different numbers. The count excludes
 * `kudos_received_baseline`; the caller adds it (`board-data.ts`'s idiom).
 */
export async function fetchReceivedAggregate(
  supabase: SupabaseClient<Database>, sunnerId: number,
): Promise<ReceivedAggregate> {
  const { data, error } = await supabase
    .from("kudos_readable")
    .select("heart_baseline, likes:kudos_likes(count)")
    .eq("receiver_id", sunnerId)
    .returns<{ heart_baseline: number; likes: { count: number }[] }[]>();

  if (error) throw new Error(`fetchReceivedAggregate failed: ${error.message}`);
  const hearts = data.reduce((sum, r) => sum + r.heart_baseline + (r.likes[0]?.count ?? 0), 0);
  return { count: data.length, hearts };
}

/** The caller's own sent total — a plain count (no sent baseline column exists). Head-only, so no row body crosses the wire. */
export async function fetchSentCount(
  supabase: SupabaseClient<Database>, sunnerId: number,
): Promise<number> {
  const { count, error } = await supabase
    .from("kudos_readable")
    .select("id", { count: "exact", head: true })
    .eq("sender_id", sunnerId);

  if (error) throw new Error(`fetchSentCount failed: ${error.message}`);
  return count ?? 0;
}

/**
 * Kudos-received counts for a bounded set of Sunners — the badge-tier input
 * `toKudosCardView` needs for everyone on a page.
 *
 * A map built from the page's own rows would be WRONG (phase 04's handover):
 * a keyset page sees ten rows, so every tier would come out too low. This
 * asks the database for the real counts of exactly the Sunners on the page,
 * reproducing the board's full-table tally for those ids exactly.
 */
export async function fetchReceivedCounts(
  supabase: SupabaseClient<Database>, sunnerIds: readonly number[],
): Promise<Map<number, number>> {
  const counts = new Map<number, number>();
  if (sunnerIds.length === 0) return counts;

  const { data, error } = await supabase
    .from("kudos_readable")
    .select("receiver_id")
    .in("receiver_id", [...sunnerIds])
    .returns<{ receiver_id: number }[]>();

  if (error) throw new Error(`fetchReceivedCounts failed: ${error.message}`);
  for (const r of data) counts.set(r.receiver_id, (counts.get(r.receiver_id) ?? 0) + 1);
  return counts;
}

/**
 * A timestamp and nothing else. `sentAt` is interpolated into the PostgREST
 * `or=` filter below, where `,`, `(`, `)` and `"` are STRUCTURAL — so this
 * shape check is the injection boundary, not a convenience.
 */
const TIMESTAMP_PATTERN =
  /^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(\.\d{1,6})?(Z|[+-]\d{2}:?\d{2})?$/;

/** Validates a cursor arriving from a client. Exported so the A2 action can refuse one before any query. */
export function isValidFeedCursor(value: unknown): value is FeedCursor {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as { sentAt?: unknown; id?: unknown };
  return (
    typeof candidate.sentAt === "string" &&
    TIMESTAMP_PATTERN.test(candidate.sentAt) &&
    Number.isFinite(Date.parse(candidate.sentAt)) &&
    typeof candidate.id === "number" &&
    Number.isInteger(candidate.id) &&
    candidate.id > 0
  );
}

export interface KudosPageQuery {
  /** Chosen SERVER-SIDE, never from a client string: `sender_id` is only ever paired with the session's own `sunnerId` (FR-601). */
  column: "receiver_id" | "sender_id";
  sunnerId: number;
  cursor: FeedCursor | null;
}

/**
 * ALG-002 — one keyset page, `FEED_PAGE_SIZE + 1` rows deep so the caller can
 * derive `hasMore` without a second `count(*)`.
 *
 * The spec writes the cursor as the SQL row comparison
 * `(sent_at, id) < (:sentAt, :id)`. PostgREST has no syntax for that, so it
 * is expanded into the equivalent disjunction
 * `sent_at < :sentAt OR (sent_at = :sentAt AND id < :id)` — same semantics,
 * stable when two rows share a `sent_at`. `sent_at.lt` ALONE would silently
 * drop every row tying with the cursor's timestamp; the seed contains no
 * duplicate `sent_at` at all (measured), so only a deliberately constructed
 * tie catches that degraded form — `evidence/phase-05-measurements.log`.
 */
export async function fetchKudosPage(
  supabase: SupabaseClient<Database>,
  { column, sunnerId, cursor }: KudosPageQuery,
): Promise<KudosFeedRow[]> {
  // Unreachable from a client (A2 validates first) — but a programming error
  // must not become a hand-built filter string either.
  if (cursor !== null && !isValidFeedCursor(cursor)) {
    throw new Error("fetchKudosPage: malformed cursor");
  }

  let query = supabase
    .from("kudos_readable")
    .select(KUDOS_FEED_SELECT)
    .eq(column, sunnerId)
    .order("sent_at", { ascending: false })
    .order("id", { ascending: false })
    .limit(FEED_PAGE_SIZE + 1);

  if (cursor !== null) {
    const { sentAt, id } = cursor;
    query = query.or(`sent_at.lt.${sentAt},and(sent_at.eq.${sentAt},id.lt.${id})`);
  }

  const { data, error } = await query.returns<KudosFeedRow[]>();
  if (error) throw new Error(`fetchKudosPage failed: ${error.message}`);
  return data;
}
