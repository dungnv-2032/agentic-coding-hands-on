/**
 * Typed Supabase reads for the Kudos Live Board (phase 04).
 *
 * Every function takes the client as an argument so `board-data.ts` creates
 * it once per request and runs the independent reads with `Promise.all`.
 * Returns raw row shapes only — `board-data.ts` owns assembling the frozen
 * `KudosBoardViewModel`.
 *
 * Row shapes for plain tables come straight from the generated
 * `Database["public"]["Tables"][...]["Row"]` types (never hand-retyped).
 * Embedded-select shapes (joins via `.select("a:b(...)")`) are declared
 * explicitly and pinned with `.returns<T[]>()`, since postgrest-js's
 * select-string inference is not exhaustive for nested FK-hinted embeds —
 * this keeps the boundary fully typed without an `any`.
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
  sender: SunnerEmbed;
  receiver: SunnerEmbed;
  hashtags: { position: number; hashtag: { name: string } | null }[];
  attachments: { id: number; image_url: string; position: number }[];
  likes: { count: number }[];
}

/** One board read: kudos + sender/receiver + hashtags + attachments + like counts. */
export async function fetchKudos(supabase: SupabaseClient<Database>): Promise<KudosFeedRow[]> {
  const { data, error } = await supabase
    .from("kudos")
    .select(
      `id, campaign, message, sent_at, heart_baseline, message_format, is_anonymous, anonymous_name,
       sender:sunners!kudos_sender_id_fkey(id, full_name, avatar_url, kudos_received_baseline, department:departments(name)),
       receiver:sunners!kudos_receiver_id_fkey(id, full_name, avatar_url, kudos_received_baseline, department:departments(name)),
       hashtags:kudos_hashtags(position, hashtag:hashtags(name)),
       attachments:kudos_attachments(id, image_url, position),
       likes:kudos_likes(count)`,
    )
    .order("sent_at", { ascending: false })
    .returns<KudosFeedRow[]>();

  if (error) throw new Error(`fetchKudos failed: ${error.message}`);
  return data;
}

/** The viewer's own likes, authed only — never carries other users' ids. */
export async function fetchViewerLikes(
  supabase: SupabaseClient<Database>,
  userId: string,
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
export async function fetchFilterOptions(
  supabase: SupabaseClient<Database>,
): Promise<FilterOptionsResult> {
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
  supabase: SupabaseClient<Database>,
  sunnerId: number,
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
  sunner: { full_name: string } | null;
}

/** Top 10 by `awarded_at desc`. */
export async function fetchGifts(supabase: SupabaseClient<Database>): Promise<GiftFeedRow[]> {
  const { data, error } = await supabase
    .from("gift_awards")
    .select("id, gift_label, awarded_at, sunner:sunners(full_name)")
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
export async function fetchSpotlightEvents(
  supabase: SupabaseClient<Database>,
): Promise<SpotlightFeedRow[]> {
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
