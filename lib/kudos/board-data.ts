/**
 * `getKudosBoard()` — assembles the frozen `KudosBoardViewModel` (phase 01)
 * from the typed reads in `queries.ts` and the identity in `viewer.ts`.
 *
 * One client per request (`lib/supabase/server.ts`), independent reads run
 * with `Promise.all` (`app/_page-context.ts:28`'s pattern). `derive.ts`'s
 * pure helpers are reused, never reimplemented (badge tier, tooltip,
 * sent-at label, BR-001's heart formula).
 *
 * The row→card mapping lives in `map-kudos-card.ts` (F006 phase 04) so the
 * profile feed runs the board's mapper rather than a copy of it. Nothing in
 * this file re-implements it; it supplies the per-read context and consumes
 * the result.
 */

import { formatSentAt } from "@/lib/kudos/derive";
import { heartsOf, toKudosCardView } from "@/lib/kudos/map-kudos-card";
import type {
  FilterOptionView, GiftRowView, KudosBoardViewModel, KudosCardView,
  SidebarCountsView, SpotlightNodeView, SpotlightTickerRowView,
} from "@/lib/kudos/view-model";
import { createClient } from "@/lib/supabase/server";

import {
  fetchFilterOptions, fetchGifts, fetchKudos, fetchSidebarBoxCounts,
  fetchSpotlightEvents, fetchSpotlightTotal, fetchViewerLikes,
} from "./queries";
import { resolveSidebarSunnerId, resolveViewer } from "./viewer";

/** Asia/Ho_Chi_Minh fixed offset, mirroring derive.ts's (frozen, unexported) constant. */
const TICKER_OFFSET_MINUTES = 7 * 60;

function formatTickerTime(iso: string): string {
  const shifted = new Date(new Date(iso).getTime() + TICKER_OFFSET_MINUTES * 60_000);
  const hours24 = shifted.getUTCHours();
  const period = hours24 >= 12 ? "PM" : "AM";
  const hours12 = hours24 % 12 === 0 ? 12 : hours24 % 12;
  const hh = hours12.toString().padStart(2, "0");
  const mm = shifted.getUTCMinutes().toString().padStart(2, "0");
  return `${hh}:${mm}${period}`;
}

export async function getKudosBoard(): Promise<KudosBoardViewModel> {
  const supabase = await createClient();
  const viewer = await resolveViewer(supabase);

  const [rows, filterOptions, gifts, spotlightEvents, viewerLikes] = await Promise.all([
    fetchKudos(supabase),
    fetchFilterOptions(supabase),
    fetchGifts(supabase),
    fetchSpotlightEvents(supabase),
    viewer.userId ? fetchViewerLikes(supabase, viewer.userId) : Promise.resolve(new Set<number>()),
  ]);

  // Received-count per sunner, derived from the same full kudos read — no
  // extra query (NFR: one board read per request).
  const receivedCountBySunnerId = new Map<number, number>();
  for (const row of rows) {
    receivedCountBySunnerId.set(
      row.receiver.id,
      (receivedCountBySunnerId.get(row.receiver.id) ?? 0) + 1,
    );
  }

  // The board never reveals its own anonymous Kudos to their author: the
  // `revealOwnAnonymous` option stays off here (default), so the author sees
  // the same masked chip everyone else does — F004's shipped behaviour. Only
  // the profile Sent list turns it on.
  const kudos: KudosCardView[] = rows.map((row) =>
    toKudosCardView(row, {
      viewerSunnerId: viewer.sunnerId,
      viewerIsAuthenticated: viewer.isAuthenticated,
      likedKudosIds: viewerLikes,
      receivedCountBySunnerId,
    }),
  );

  const hashtagOptions: FilterOptionView[] = filterOptions.hashtags.map((h) => ({
    id: h.id,
    name: h.name,
  }));
  const departmentOptions: FilterOptionView[] = filterOptions.departments.map((d) => ({
    id: d.id,
    name: d.name,
  }));

  const sidebarSunnerId = await resolveSidebarSunnerId(supabase, viewer.sunnerId);
  const boxCounts = await fetchSidebarBoxCounts(supabase, sidebarSunnerId);
  let kudosReceived = 0;
  let kudosSent = 0;
  let heartsReceived = 0;
  for (const row of rows) {
    if (row.receiver.id === sidebarSunnerId) {
      kudosReceived += 1;
      heartsReceived += heartsOf(row);
    }
    // `sender_id` is null exactly when `kudos_readable` masked it, which by
    // construction means the caller is not that sender. So a signed-in
    // viewer's own anonymous sends still count here (the view reveals them to
    // their author), while the anonymous-visitor display fallback cannot
    // count the seeded frame viewer's anonymous sends — and must not: that
    // number is precisely what SEC_002 forbids publishing about someone else.
    if (row.sender_id !== null && row.sender_id === sidebarSunnerId) {
      kudosSent += 1;
    }
  }
  const sidebarCounts: SidebarCountsView = {
    kudosReceived,
    kudosSent,
    heartsReceived,
    secretBoxOpened: boxCounts.secretBoxOpened,
    secretBoxUnopened: boxCounts.secretBoxUnopened,
  };

  const giftRows: GiftRowView[] = gifts.map((g) => ({
    id: g.id,
    sunnerId: g.sunner_id,
    sunnerName: g.sunner?.full_name ?? "",
    giftLabel: g.gift_label,
  }));

  const spotlightNodes: SpotlightNodeView[] = spotlightEvents.map((event, index) => ({
    id: event.id,
    name: event.sunner?.full_name ?? "",
    kudosId: event.kudos_id,
    receivedAtLabel: formatSentAt(event.occurred_at),
    isJustUpdated: index === 0,
  }));
  const spotlightTicker: SpotlightTickerRowView[] = spotlightEvents.slice(0, 6).map((event) => ({
    id: event.id,
    timeLabel: formatTickerTime(event.occurred_at),
    name: event.sunner?.full_name ?? "",
  }));

  return {
    kudos,
    hashtagOptions,
    departmentOptions,
    spotlight: {
      nodes: spotlightNodes,
      ticker: spotlightTicker,
    },
    sidebar: {
      counts: sidebarCounts,
      gifts: giftRows,
    },
    viewer: {
      isAuthenticated: viewer.isAuthenticated,
      sunnerId: viewer.sunnerId,
    },
  };
}

/** `board_stats.spotlight_kudos_total` — used by the `388 KUDOS` heading (test-contract.md ratification "Overridden"). */
export async function getSpotlightTotal(): Promise<number> {
  const supabase = await createClient();
  return fetchSpotlightTotal(supabase);
}
