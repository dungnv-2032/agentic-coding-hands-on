/**
 * Typed Supabase reads for the Kudos Live Board (phase 04).
 *
 * Every function takes the client as an argument, so `board-data.ts` creates
 * one per request and runs the independent reads with `Promise.all`. Raw row
 * shapes only — `board-data.ts` owns the frozen `KudosBoardViewModel`.
 *
 * Plain-table rows reuse the generated `Database[...]["Row"]` types, never
 * hand-retyped. Embedded selects (`.select("a:b(...)")`) are declared
 * explicitly and pinned with `.returns<T[]>()`: postgrest-js's select-string
 * inference is not exhaustive for nested FK-hinted embeds, and this keeps the
 * boundary typed without an `any`. `kudos_readable` (F006 phase 03) is a VIEW,
 * outside `Row<T>`'s reach, declared the same way; only the five `sender_*`
 * columns it genuinely nulls are typed nullable.
 */

import type { SupabaseClient } from "@supabase/supabase-js";

import type { Database } from "@/lib/supabase/database.types";

type Row<T extends keyof Database["public"]["Tables"]> = Database["public"]["Tables"][T]["Row"];

export type HashtagRow = Row<"hashtags">;
export type DepartmentRow = Row<"departments">;

interface SunnerEmbed {
  id: number;
  full_name: string;
  avatar_url: string;
  kudos_received_baseline: number;
  department: { name: string } | null;
}

export interface KudosFeedRow {
  id: number;
  campaign: string | null;
  message: string;
  sent_at: string;
  heart_baseline: number;
  message_format: string;
  is_anonymous: boolean;
  anonymous_name: string | null;
  /**
   * Five FLAT, PRE-MASKED sender columns — never an embed, `null` TOGETHER
   * when the database masked the sender: that nullability IS the anonymity
   * boundary. See `20260908100000_profile_reader_view.sql` § 3 and
   * `map-kudos-card.ts`.
   */
  sender_id: number | null;
  sender_full_name: string | null;
  sender_avatar_url: string | null;
  sender_kudos_received_baseline: number | null;
  sender_department_name: string | null;
  /** Still an embed — `receiver_id` stays plain and traceable, so the FK hint resolves through the view. */
  receiver: SunnerEmbed;
  hashtags: { position: number; hashtag: { name: string } | null }[];
  attachments: { id: number; image_url: string; position: number }[];
  likes: { count: number }[];
}

/**
 * The column list behind every `KudosFeedRow`, board and profile alike (they
 * must build the same card from the same row — BR-005). Single-sourced here
 * because `.returns<KudosFeedRow[]>()` is an ASSERTION: a column dropped from
 * one of two copies would surface as unexpected nulls in the mapper, not as a
 * type error. F006 phase 09 hoisted it; phase 05 had to duplicate it.
 */
export const KUDOS_FEED_SELECT = `id, campaign, message, sent_at, heart_baseline, message_format, is_anonymous, anonymous_name,
   sender_id, sender_full_name, sender_avatar_url, sender_kudos_received_baseline, sender_department_name,
   receiver:sunners!kudos_receiver_id_fkey(id, full_name, avatar_url, kudos_received_baseline, department:departments(name)),
   hashtags:kudos_hashtags(position, hashtag:hashtags(name)),
   attachments:kudos_attachments(id, image_url, position),
   likes:kudos_likes(count)`;

/** One board read: kudos + masked sender + receiver + hashtags + attachments + likes. */
export async function fetchKudos(supabase: SupabaseClient<Database>): Promise<KudosFeedRow[]> {
  const { data, error } = await supabase
    .from("kudos_readable")
    .select(KUDOS_FEED_SELECT)
    .order("sent_at", { ascending: false })
    .returns<KudosFeedRow[]>();

  if (error) throw new Error(`fetchKudos failed: ${error.message}`);
  return data;
}

/** The viewer's own likes, authed only — never carries other users' ids. */
export async function fetchViewerLikes(
  supabase: SupabaseClient<Database>, userId: string,
): Promise<Set<number>> {
  const { data, error } = await supabase
    .from("kudos_likes")
    .select("kudos_id")
    .eq("user_id", userId);

  if (error) throw new Error(`fetchViewerLikes failed: ${error.message}`);
  return new Set(data.map((row) => row.kudos_id));
}

export interface FilterOptionsResult {
  hashtags: HashtagRow[];
  departments: DepartmentRow[];
}

/** 13 hashtags (frame order) + 50 filterable departments (frame order). */
export async function fetchFilterOptions(supabase: SupabaseClient<Database>): Promise<FilterOptionsResult> {
  const [hashtagsResult, departmentsResult] = await Promise.all([
    supabase.from("hashtags").select("*").order("position", { ascending: true }),
    supabase
      .from("departments")
      .select("*")
      .not("filter_position", "is", null)
      .order("filter_position", { ascending: true }),
  ]);

  if (hashtagsResult.error) {
    throw new Error(`fetchFilterOptions (hashtags) failed: ${hashtagsResult.error.message}`);
  }
  if (departmentsResult.error) {
    throw new Error(`fetchFilterOptions (departments) failed: ${departmentsResult.error.message}`);
  }

  return { hashtags: hashtagsResult.data, departments: departmentsResult.data };
}

export interface SidebarBoxCounts {
  secretBoxOpened: number;
  secretBoxUnopened: number;
}

/** Stored per-sunner counters only — received/sent/hearts are derived from `fetchKudos()`'s result in `board-data.ts`, not re-queried. */
export async function fetchSidebarBoxCounts(
  supabase: SupabaseClient<Database>, sunnerId: number,
): Promise<SidebarBoxCounts> {
  const { data, error } = await supabase
    .from("sunners")
    .select("secret_box_opened_count, secret_box_unopened_count")
    .eq("id", sunnerId)
    .single();

  if (error) throw new Error(`fetchSidebarBoxCounts failed: ${error.message}`);
  return {
    secretBoxOpened: data.secret_box_opened_count,
    secretBoxUnopened: data.secret_box_unopened_count,
  };
}

export interface GiftFeedRow {
  id: number;
  gift_label: string;
  awarded_at: string;
  /** `gift_awards.sunner_id` — the plain NOT NULL FK column, not the embed, so `gift-leaderboard.tsx` can emit `?id=` (F006 FR-003). */
  sunner_id: number;
  sunner: { full_name: string } | null;
}

/** Top 10 by `awarded_at desc`. */
export async function fetchGifts(supabase: SupabaseClient<Database>): Promise<GiftFeedRow[]> {
  const { data, error } = await supabase
    .from("gift_awards")
    .select("id, gift_label, awarded_at, sunner_id, sunner:sunners(full_name)")
    .order("awarded_at", { ascending: false })
    .limit(10)
    .returns<GiftFeedRow[]>();

  if (error) throw new Error(`fetchGifts failed: ${error.message}`);
  return data;
}

export interface SpotlightFeedRow {
  id: number;
  kudos_id: number;
  occurred_at: string;
  sunner: { full_name: string } | null;
}

/** All 7 spotlight events, most recent first — feeds both nodes (7) and ticker (top 6). */
export async function fetchSpotlightEvents(supabase: SupabaseClient<Database>): Promise<SpotlightFeedRow[]> {
  const { data, error } = await supabase
    .from("spotlight_ticker_events")
    .select("id, kudos_id, occurred_at, sunner:sunners(full_name)")
    .order("occurred_at", { ascending: false })
    .returns<SpotlightFeedRow[]>();

  if (error) throw new Error(`fetchSpotlightEvents failed: ${error.message}`);
  return data;
}

/** The seeded `388 KUDOS` Spotlight total — data, never a live `count(*)`. */
export async function fetchSpotlightTotal(supabase: SupabaseClient<Database>): Promise<number> {
  const { data, error } = await supabase
    .from("board_stats")
    .select("spotlight_kudos_total")
    .eq("id", 1)
    .single();

  if (error) throw new Error(`fetchSpotlightTotal failed: ${error.message}`);
  return data.spotlight_kudos_total;
}
