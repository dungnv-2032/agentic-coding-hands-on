/**
 * The one row→card mapper (F006 phase 04, BR-005).
 *
 * Lifted verbatim in behaviour out of `board-data.ts` so the F004 board and
 * the F006 profile feed produce `KudosCardView` from the SAME code rather
 * than from two copies that can drift. `derive.ts`'s pure helpers stay the
 * only source of badge tier, tooltip and sent-at formatting.
 *
 * The anonymity mask is NOT implemented here. It is already applied by
 * `public.kudos_readable` before the row arrives: the five `sender_*` columns
 * are null together when the caller may not see the sender. This module's job
 * is to react to that nullability correctly — never to recover a name behind
 * it, and never to assert it away with `!` or `as`.
 */

import { badgeTierFor, badgeTooltipFor, formatSentAt } from "@/lib/kudos/derive";
import type { KudosCardView, SunnerView } from "@/lib/kudos/view-model";

import type { KudosFeedRow } from "./queries";

/** Neutral fallback for a missing anonymous display name — data, not copy (clarifications § Unresolved question 4). */
export const ANONYMOUS_FALLBACK_LABEL = "Ẩn danh";

/** Everything both surfaces must supply once per read, not per row. */
export interface KudosCardContext {
  /** Auth-resolved identity only (`resolveViewer().sunnerId`) — never the sidebar display fallback. */
  viewerSunnerId: number | null;
  viewerIsAuthenticated: boolean;
  likedKudosIds: Set<number>;
  /** Kudos-received count per sunner, derived from the same read. */
  receivedCountBySunnerId: Map<number, number>;
}

export interface KudosCardOptions {
  /**
   * When `true`, a row the CALLER sent anonymously shows the caller as its
   * author (`anonymousSenderLabel: null`) while `sentAnonymously` stays
   * `true` — the profile Sent list's one deviation from the board
   * (clarifications § "My own Sent list and my own anonymous Kudos").
   *
   * Server-only switch. It may be set only by code that resolved the
   * caller's identity from the session; it must never be reachable from a
   * client argument, and it reveals nothing on its own — the database has
   * already decided whether `sender_id` is visible at all.
   */
  revealOwnAnonymous?: boolean;
}

/** Redacted `SunnerView` stand-in for an anonymous kudos: no real name, department, avatar or badge tooltip crosses the mapping boundary. */
function toAnonymousSenderView(label: string): SunnerView {
  return { id: 0, fullName: label, department: "", avatarUrl: "/images/kudos/sample-avatar.png", badge: "New Hero", badgeTooltip: null };
}

/** The four facts a `SunnerView` is built from, however the row carried them (flat sender columns / receiver embed). */
interface SunnerFacts {
  id: number;
  fullName: string;
  avatarUrl: string;
  receivedBaseline: number;
  departmentName: string | null;
}

function toSunnerView(facts: SunnerFacts, receivedCount: number): SunnerView {
  const badge = badgeTierFor(facts.receivedBaseline + receivedCount);
  return {
    id: facts.id,
    fullName: facts.fullName,
    department: facts.departmentName ?? "",
    avatarUrl: facts.avatarUrl,
    badge,
    badgeTooltip: badgeTooltipFor(badge),
  };
}

export function toReceiverView(row: KudosFeedRow, receivedCount: number): SunnerView {
  return toSunnerView(
    {
      id: row.receiver.id,
      fullName: row.receiver.full_name,
      avatarUrl: row.receiver.avatar_url,
      receivedBaseline: row.receiver.kudos_received_baseline,
      departmentName: row.receiver.department?.name ?? null,
    },
    receivedCount,
  );
}

/**
 * The sender the view actually disclosed, or `null` when it masked them.
 * The four columns are checked individually rather than trusted together:
 * they are values arriving from outside the process, and a null here has
 * exactly one correct answer — the anonymous view.
 */
function toSenderView(row: KudosFeedRow, receivedCounts: Map<number, number>): SunnerView | null {
  if (
    row.sender_id === null ||
    row.sender_full_name === null ||
    row.sender_avatar_url === null ||
    row.sender_kudos_received_baseline === null
  ) {
    return null;
  }
  return toSunnerView(
    {
      id: row.sender_id,
      fullName: row.sender_full_name,
      avatarUrl: row.sender_avatar_url,
      receivedBaseline: row.sender_kudos_received_baseline,
      departmentName: row.sender_department_name,
    },
    receivedCounts.get(row.sender_id) ?? 0,
  );
}

export function heartsOf(row: KudosFeedRow): number {
  return row.heart_baseline + (row.likes[0]?.count ?? 0);
}

/** One row → one card. Pure: every input is an argument, no client, no session read. */
export function toKudosCardView(
  row: KudosFeedRow,
  ctx: KudosCardContext,
  opts: KudosCardOptions = {},
): KudosCardView {
  // Non-null only for anonymous rows; a blank/whitespace-only stored name falls back to the neutral label.
  const anonymousLabel = row.is_anonymous
    ? row.anonymous_name?.trim() || ANONYMOUS_FALLBACK_LABEL
    : null;

  // Real sender id, never the redacted stub's `id: 0`. `sender_id === null`
  // means the database refused to disclose the sender, which by construction
  // means the viewer is not that sender — so the author still cannot like
  // their own anonymous kudos, and a viewer with no `sunners` row keeps every
  // heart enabled exactly as F004 shipped it.
  const viewerIsSender =
    row.sender_id !== null && ctx.viewerSunnerId !== null && ctx.viewerSunnerId === row.sender_id;

  const senderView = toSenderView(row, ctx.receivedCountBySunnerId);
  const revealOwn = opts.revealOwnAnonymous === true && viewerIsSender;
  const showsRealSender = senderView !== null && (anonymousLabel === null || revealOwn);

  return {
    id: row.id,
    sender: showsRealSender ? senderView : toAnonymousSenderView(anonymousLabel ?? ANONYMOUS_FALLBACK_LABEL),
    receiver: toReceiverView(row, ctx.receivedCountBySunnerId.get(row.receiver.id) ?? 0),
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
    likedByViewer: ctx.likedKudosIds.has(row.id),
    canLike: ctx.viewerIsAuthenticated && !viewerIsSender,
    isOwnedByViewer: viewerIsSender,
    // Narrowed by comparison, never cast — an unexpected value degrades to "plain", rendered as raw text.
    messageFormat: row.message_format === "doc" ? "doc" : "plain",
    // Null whenever the real sender is on the card, so the chip and the identity can never both render.
    anonymousSenderLabel: showsRealSender ? null : anonymousLabel ?? ANONYMOUS_FALLBACK_LABEL,
    sentAnonymously: row.is_anonymous,
  };
}
