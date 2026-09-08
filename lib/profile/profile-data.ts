/**
 * `getProfileData()` — assembles the frozen `ProfileViewModel` (phase 01)
 * from the typed reads in `profile-queries.ts` (F006 phase 05, A1).
 *
 * The self/other branch is decided EXACTLY ONCE, here: `stats` is non-null
 * iff the viewer is on their own profile, `writeKudoTargetId` non-null iff
 * they are not, and `counts.sent` is null on anyone else's profile so that
 * number never leaves the server (SC-002, SEC_001). No component re-tests
 * "is this mine".
 *
 * Read-only, always: a GET never provisions a `sunners` row (BR-001). The
 * client is an argument rather than created here so the page can create ONE
 * per request and use it for `resolveViewer()` too — the viewer must be
 * resolved before `?id=` can be, which must happen before this call.
 */

import type { SupabaseClient } from "@supabase/supabase-js";

import { badgeTierFor, badgeTooltipFor, FEED_PAGE_SIZE } from "@/lib/kudos/derive";
import { toKudosCardView } from "@/lib/kudos/map-kudos-card";
import type { KudosFeedRow } from "@/lib/kudos/queries";
import { fetchViewerLikes } from "@/lib/kudos/queries";
import type { KudosCardView } from "@/lib/kudos/view-model";
import type { ViewerIdentity } from "@/lib/kudos/viewer";
import type { ProfileFeedPage, ProfileViewModel } from "@/lib/profile/profile-view-model";
import type { Database } from "@/lib/supabase/database.types";

import {
  fetchKudosPage, fetchProfileSunner, fetchReceivedAggregate, fetchReceivedCounts, fetchSentCount,
} from "./profile-queries";

/** The same fallback `create_kudos()` writes into `sunners.avatar_url` on a first write. */
const SAMPLE_AVATAR_URL = "/images/kudos/sample-avatar.png";
/** No `sunners` row matched the requested id — the page turns this into `notFound()` (FR-402). */
export type ProfileDataResult =
  | { kind: "found"; model: ProfileViewModel }
  | { kind: "not-found" };

/** A fresh empty page every call — never one shared object a caller could hold onto. */
export function emptyFeedPage(): ProfileFeedPage {
  return { cards: [], nextCursor: null, hasMore: false };
}

/**
 * Rows → one `ProfileFeedPage`. Shared by A1 (page 1, server-side) and A2
 * (every page after), so page 1 and the rest can never be built differently.
 * `rows` is the `FEED_PAGE_SIZE + 1` read: the extra row only answers "is
 * there more" and is dropped before mapping, so it never reaches the client.
 */
export async function buildFeedPage(
  supabase: SupabaseClient<Database>, rows: readonly KudosFeedRow[],
  viewer: ViewerIdentity, opts: { revealOwnAnonymous?: boolean } = {},
): Promise<ProfileFeedPage> {
  const hasMore = rows.length > FEED_PAGE_SIZE;
  const pageRows = hasMore ? rows.slice(0, FEED_PAGE_SIZE) : [...rows];
  if (pageRows.length === 0) return emptyFeedPage();

  // Badge tiers must match the board's, which tallies over the WHOLE table.
  // A tally of this page would understate every tier, so the real counts are
  // read for exactly the Sunners on the page.
  const sunnerIdsOnPage = new Set<number>();
  for (const row of pageRows) {
    sunnerIdsOnPage.add(row.receiver.id);
    if (row.sender_id !== null) sunnerIdsOnPage.add(row.sender_id);
  }

  const [likedKudosIds, receivedCountBySunnerId] = await Promise.all([
    viewer.userId ? fetchViewerLikes(supabase, viewer.userId) : Promise.resolve(new Set<number>()),
    fetchReceivedCounts(supabase, [...sunnerIdsOnPage]),
  ]);

  const ctx = {
    viewerSunnerId: viewer.sunnerId, viewerIsAuthenticated: viewer.isAuthenticated,
    likedKudosIds, receivedCountBySunnerId,
  };
  const cards: KudosCardView[] = pageRows.map((row) => toKudosCardView(row, ctx, opts));

  const last = pageRows[pageRows.length - 1];
  return { cards, nextCursor: hasMore ? { sentAt: last.sent_at, id: last.id } : null, hasMore };
}

/**
 * BR-001's identity fallback, copied from `create_kudos()`'s chain verbatim:
 * `user_metadata.full_name` → `.name` → the email LOCAL-PART, and
 * `avatar_url` → `picture` → the sample avatar; blank strings skipped exactly
 * as the SQL's `nullif(…, '')` does. The local-part is deliberate — it is the
 * same value a write would have stored, and it is not an address, so SEC_004
 * still holds. Nothing else escapes: the Supabase `User` object stays inside
 * this function, the guarantee `viewer.ts` makes for the same reason.
 */
async function readJwtIdentityFallback(
  supabase: SupabaseClient<Database>,
): Promise<{ fullName: string; avatarUrl: string } | null> {
  const { data: { user }, error } = await supabase.auth.getUser();
  if (error || !user) return null;

  // Supabase types `user_metadata` as `{[key: string]: any}`; narrowing it to
  // `unknown` values here is what stops that `any` leaking into this module.
  const metadata = user.user_metadata as Record<string, unknown> | null;
  const text = (key: string): string | null => {
    const value = metadata?.[key];
    return typeof value === "string" && value.trim() !== "" ? value : null;
  };
  const localPart = typeof user.email === "string" ? user.email.split("@")[0] : "";

  return {
    fullName: text("full_name") ?? text("name") ?? localPart,
    avatarUrl: text("avatar_url") ?? text("picture") ?? SAMPLE_AVATAR_URL,
  };
}

/** The sparse self view: signed in, no `sunners` row yet (A4/BR-001). Reads only; writes nothing. */
async function sparseSelfModel(supabase: SupabaseClient<Database>): Promise<ProfileDataResult> {
  // No session: no profile to render. Unreachable through the guarded page
  // (`proxy.ts` + the page's own re-check), and answered here rather than by
  // inventing a blank name.
  const identity = await readJwtIdentityFallback(supabase);
  if (!identity) return { kind: "not-found" };

  return {
    kind: "found",
    model: {
      isSelf: true,
      hero: {
        sunnerId: null, fullName: identity.fullName, department: null,
        avatarUrl: identity.avatarUrl, badge: null, badgeTooltip: null,
      },
      stats: {
        kudosReceived: 0, kudosSent: 0, heartsReceived: 0,
        secretBoxOpened: 0, secretBoxUnopened: 0,
      },
      writeKudoTargetId: null,
      counts: { received: 0, sent: 0 },
      initialPage: emptyFeedPage(),
      unlockedBadgeSlots: [],
    },
  };
}

/**
 * @param targetId - resolved `sunners.id`, or `null` for the self view of a
 *   session with no roster row. Never a raw query-param value —
 *   `resolveProfileId()` (phase 06) shape-checked it already.
 * @param viewer - `resolveViewer()`'s auth-only identity. `viewer.userId`
 *   stays server-side: it reads the viewer's own likes, and is never copied
 *   into the returned model.
 */
export async function getProfileData(
  supabase: SupabaseClient<Database>,
  targetId: number | null,
  viewer: ViewerIdentity,
): Promise<ProfileDataResult> {
  if (targetId === null) return sparseSelfModel(supabase);

  const isSelf = targetId === viewer.sunnerId;

  const [sunner, aggregate, sentCount, pageRows] = await Promise.all([
    fetchProfileSunner(supabase, targetId),
    fetchReceivedAggregate(supabase, targetId),
    // FR-601 — the sent total is only ever the CALLER's own, scoped by the
    // session's id, and is not read at all on another Sunner's profile.
    isSelf && viewer.sunnerId !== null
      ? fetchSentCount(supabase, viewer.sunnerId)
      : Promise.resolve(null),
    fetchKudosPage(supabase, { column: "receiver_id", sunnerId: targetId, cursor: null }),
  ]);

  if (!sunner) return { kind: "not-found" };

  // Counters follow F004's shipped idiom exactly, so the board and the profile
  // can never disagree. GUI_009 — the pill is HIDDEN at zero received, not
  // rendered as the "New Hero" tier `badgeTierFor(0)` would return.
  const received = sunner.kudos_received_baseline + aggregate.count;
  const badge = received > 0 ? badgeTierFor(received) : null;

  return {
    kind: "found",
    model: {
      isSelf,
      hero: {
        sunnerId: sunner.id, fullName: sunner.full_name, avatarUrl: sunner.avatar_url,
        department: sunner.department?.name ?? null,
        badge, badgeTooltip: badge === null ? null : badgeTooltipFor(badge),
      },
      stats: isSelf
        ? {
            kudosReceived: received, kudosSent: sentCount ?? 0,
            heartsReceived: aggregate.hearts,
            secretBoxOpened: sunner.secret_box_opened_count,
            secretBoxUnopened: sunner.secret_box_unopened_count,
          }
        : null,
      writeKudoTargetId: isSelf ? null : sunner.id,
      counts: { received, sent: isSelf ? sentCount ?? 0 : null },
      initialPage: await buildFeedPage(supabase, pageRows, viewer),
      unlockedBadgeSlots: [],
    },
  };
}
