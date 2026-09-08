/**
 * Frozen integration contract for the Profile bản thân screen (F006, phase 01).
 *
 * Types only — no runtime export, no `next/*`, no `@/lib/supabase/*`, no React,
 * no `Intl`/`toLocaleString` (see `lib/kudos/derive.ts` for why: ICU version
 * drift between server and browser runtimes hydration-mismatches a formatted
 * number). Must be importable from a Client Component.
 *
 * Track B (data layer) PRODUCES a `ProfileViewModel` from Supabase reads;
 * Track A (UI) CONSUMES it as props. Neither track imports the other — this
 * file is the only thing both sides depend on, same role as F004's
 * `lib/kudos/view-model.ts`.
 *
 * A missing field here is escalated to the orchestrator, which amends this
 * phase's contract once and notifies both tracks — never patched
 * unilaterally inside a track (F004's `view-model.ts` header states the same
 * rule; kept here on purpose).
 */

import type { BadgeTier, KudosCardView } from "@/lib/kudos/view-model";

export type FeedDirection = "received" | "sent";

export interface FeedCursor {
  sentAt: string;
  id: number;
}

export interface ProfileHeroView {
  /** null on the sparse self view (signed in, no `sunners` row — A4). */
  sunnerId: number | null;
  fullName: string;
  /** null hides the department text AND the separator dot together. */
  department: string | null;
  avatarUrl: string;
  /** null when received == 0 — the pill is hidden, not rendered as "New Hero". */
  badge: BadgeTier | null;
  badgeTooltip: string | null;
}

export interface ProfileStatsView {
  kudosReceived: number;
  kudosSent: number;
  heartsReceived: number;
  secretBoxOpened: number;
  secretBoxUnopened: number;
}

export interface ProfileFeedPage {
  cards: KudosCardView[];
  nextCursor: FeedCursor | null;
  hasMore: boolean;
}

export interface ProfileViewModel {
  isSelf: boolean;
  hero: ProfileHeroView;
  /** Non-null IFF `isSelf` — the single self/other branch (SC-002). */
  stats: ProfileStatsView | null;
  /** Non-null IFF NOT `isSelf` — the write-bar's `/kudos/new?receiverId=` target. */
  writeKudoTargetId: number | null;
  /** `sent` is null on another Sunner's profile: the number never leaves the server (SEC_001). */
  counts: { received: number; sent: number | null };
  /** Page 1 of the RECEIVED direction, read server-side (DEC-001). */
  initialPage: ProfileFeedPage;
  /**
   * Which of the six badge slots are unlocked. **Always empty today** and that
   * is deliberate, not a stub: the Secret Box that awards badges is a deferred
   * commission, so every slot renders locked (a flat `#323231` circle — the
   * frame carries no badge artwork at all, clarifications AMEND-2).
   *
   * It exists as a list rather than the UI hardcoding six locked circles so
   * that awarding a badge later is a data change, not a component rewrite —
   * the shape does not move when the feature arrives. Slot indices are 0-5 in
   * the design's fixed left-to-right order B2→B7 (`mm:362:5066`–`mm:362:5071`).
   *
   * ORCHESTRATOR AMENDMENT (2026-09-08, post-phase-01): added via the
   * escalation path this file's header mandates — ratified decision D12 called
   * for this list and phase 01 shipped without it, which would have left Track
   * A hardcoding the six slots. Amended once here and both tracks notified,
   * rather than patched inside a track.
   */
  unlockedBadgeSlots: readonly number[];
}

export type FetchProfileKudosPage = (input: {
  targetSunnerId: number | null;
  direction: FeedDirection;
  cursor: FeedCursor | null;
}) => Promise<ProfileFeedPage>;
