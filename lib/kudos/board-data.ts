/**
 * `getKudosBoard()` — assembles the frozen `KudosBoardViewModel` (phase 01)
 * from the typed reads in `queries.ts` and the identity in `viewer.ts`.
 *
 * One client per request (`lib/supabase/server.ts`), independent reads run
 * with `Promise.all` (`app/_page-context.ts:28`'s pattern). `derive.ts`'s
 * pure helpers are reused, never reimplemented (badge tier, tooltip,
 * sent-at label, BR-001's heart formula).
 */

import { badgeTierFor, badgeTooltipFor, formatSentAt } from "@/lib/kudos/derive";
import type {
  FilterOptionView,
  GiftRowView,
  KudosBoardViewModel,
  KudosCardView,
  SidebarCountsView,
  SpotlightNodeView,
  SpotlightTickerRowView,
  SunnerView,
} from "@/lib/kudos/view-model";
import { createClient } from "@/lib/supabase/server";

import {
  fetchFilterOptions,
  fetchGifts,
  fetchKudos,
  fetchSidebarBoxCounts,
  fetchSpotlightEvents,
  fetchSpotlightTotal,
  fetchViewerLikes,
  type KudosFeedRow,
} from "./queries";
import { resolveSidebarSunnerId, resolveViewer } from "./viewer";

/** Asia/Ho_Chi_Minh fixed offset, mirroring derive.ts's (frozen, unexported) constant. */
const TICKER_OFFSET_MINUTES = 7 * 60;

/** Neutral fallback for a missing anonymous display name — data, not copy (clarifications § Unresolved question 4). */
const ANONYMOUS_FALLBACK_LABEL = "Ẩn danh";
/** Redacted `SunnerView` stand-in for an anonymous kudos: no real name, department, avatar or badge tooltip crosses the mapping boundary. */
function toAnonymousSenderView(label: string): SunnerView {
  return { id: 0, fullName: label, department: "", avatarUrl: "/images/kudos/sample-avatar.png", badge: "New Hero", badgeTooltip: null };
}

function formatTickerTime(iso: string): string {
  const shifted = new Date(new Date(iso).getTime() + TICKER_OFFSET_MINUTES * 60_000);
  const hours24 = shifted.getUTCHours();
  const period = hours24 >= 12 ? "PM" : "AM";
  const hours12 = hours24 % 12 === 0 ? 12 : hours24 % 12;
  const hh = hours12.toString().padStart(2, "0");
  const mm = shifted.getUTCMinutes().toString().padStart(2, "0");
  return `${hh}:${mm}${period}`;
}

function heartsOf(row: KudosFeedRow): number {
  return row.heart_baseline + (row.likes[0]?.count ?? 0);
}

function toSunnerView(sunner: KudosFeedRow["sender"], receivedCount: number): SunnerView {
  const badge = badgeTierFor(sunner.kudos_received_baseline + receivedCount);
  return {
    id: sunner.id,
    fullName: sunner.full_name,
    department: sunner.department?.name ?? "",
    avatarUrl: sunner.avatar_url,
    badge,
    badgeTooltip: badgeTooltipFor(badge),
  };
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

  const kudos: KudosCardView[] = rows.map((row) => {
    // Non-null only for anonymous rows; a blank/whitespace-only stored name falls back to the neutral label.
    const anonymousSenderLabel = row.is_anonymous
      ? row.anonymous_name?.trim() || ANONYMOUS_FALLBACK_LABEL
      : null;
    return {
      id: row.id,
      sender:
        anonymousSenderLabel === null
          ? toSunnerView(row.sender, receivedCountBySunnerId.get(row.sender.id) ?? 0)
          : toAnonymousSenderView(anonymousSenderLabel),
      receiver: toSunnerView(row.receiver, receivedCountBySunnerId.get(row.receiver.id) ?? 0),
      campaign: row.campaign,
      message: row.message,
      sentAtLabel: formatSentAt(row.sent_at),
      hashtags: [...row.hashtags]
        .sort((a, b) => a.position - b.position)
        .map((h) => h.hashtag?.name)
        .filter((name): name is string => Boolean(name)),
      attachments: [...row.attachments]
        .sort((a, b) => a.position - b.position)
        .map((a) => ({ id: a.id, imageUrl: a.image_url })),
      hearts: heartsOf(row),
      likedByViewer: viewerLikes.has(row.id),
      // Real sender id, never the redacted stub's `id: 0` — the author still cannot like their own anonymous kudos.
      canLike: viewer.isAuthenticated && viewer.sunnerId !== row.sender.id,
      isOwnedByViewer: viewer.sunnerId !== null && viewer.sunnerId === row.sender.id,
      // Narrowed by comparison, never cast — an unexpected value degrades to "plain", rendered as raw text.
      messageFormat: row.message_format === "doc" ? "doc" : "plain",
      anonymousSenderLabel,
    };
  });

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
    if (row.sender.id === sidebarSunnerId) {
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
