"use server";

/**
 * A2 — the next KUDOS page for the profile feed (F006 phase 05).
 *
 * A server action is a PUBLIC POST endpoint, so every field of the input is
 * validated before it is used, and no field of it names a table or a column.
 * Malformed input returns an EMPTY page rather than throwing: the caller is a
 * feed that must degrade to "nothing more to show", and a thrown error would
 * only tell a prober that its payload was interesting.
 *
 * The security boundary is `direction === "sent"` (FR-601/PERM013): the
 * filter column is chosen here, server-side, and paired with the CALLER's own
 * `sunnerId` resolved from the session. `targetSunnerId` is ignored entirely
 * in that branch, so a hand-rolled request naming somebody else still gets
 * its own sent list back (SC-003). Hiding the `Đã gửi` option on another
 * Sunner's profile is only the second layer.
 */

import { resolveViewer } from "@/lib/kudos/viewer";
import { buildFeedPage, emptyFeedPage } from "@/lib/profile/profile-data";
import { fetchKudosPage, isValidFeedCursor } from "@/lib/profile/profile-queries";
import type {
  FeedCursor,
  FeedDirection,
  ProfileFeedPage,
} from "@/lib/profile/profile-view-model";
import { createClient } from "@/lib/supabase/server";

/** Narrowed by comparison against the two literals — never cast. */
function isFeedDirection(value: unknown): value is FeedDirection {
  return value === "received" || value === "sent";
}

function isSunnerId(value: unknown): value is number {
  return typeof value === "number" && Number.isInteger(value) && value > 0;
}

export async function fetchProfileKudosPage(input: {
  targetSunnerId: number | null;
  direction: FeedDirection;
  cursor: FeedCursor | null;
}): Promise<ProfileFeedPage> {
  // --- boundary validation, before any query -----------------------------
  if (typeof input !== "object" || input === null) return emptyFeedPage();

  const { targetSunnerId, direction, cursor } = input;
  if (!isFeedDirection(direction)) return emptyFeedPage();
  if (targetSunnerId !== null && !isSunnerId(targetSunnerId)) return emptyFeedPage();

  let validCursor: FeedCursor | null = null;
  if (cursor !== null && cursor !== undefined) {
    if (!isValidFeedCursor(cursor)) return emptyFeedPage();
    validCursor = cursor;
  }

  // --- identity, from the session only -----------------------------------
  const supabase = await createClient();
  const viewer = await resolveViewer(supabase);
  // Gate A0: the whole screen is behind the auth guard, and this endpoint
  // does not widen it.
  if (!viewer.isAuthenticated) return emptyFeedPage();

  // `column` is chosen here, from the validated literal — never taken from
  // the request as a string.
  const column = direction === "sent" ? "sender_id" : "receiver_id";
  const sunnerId = direction === "sent" ? viewer.sunnerId : targetSunnerId;

  // `sent` with no `sunners` row yet is the NORMAL case for a fresh session
  // (A4), not an error: an empty page, no throw. `received` with no target
  // has nothing to read either.
  if (sunnerId === null) return emptyFeedPage();

  const rows = await fetchKudosPage(supabase, { column, sunnerId, cursor: validCursor });

  // `revealOwnAnonymous` is set from the resolved direction, never from an
  // argument. On the Sent list it shows the caller their own anonymous Kudo
  // as theirs (SEC_002) while `sentAnonymously` stays true; it cannot unmask
  // anybody else, because `kudos_readable` has already decided whether
  // `sender_id` is visible at all.
  return buildFeedPage(supabase, rows, viewer, {
    revealOwnAnonymous: direction === "sent",
  });
}
