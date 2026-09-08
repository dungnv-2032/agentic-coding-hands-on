/**
 * Frozen integration contract for the Kudos Live Board (F004).
 *
 * Types only — no runtime export, no `next/headers`, no `@/lib/supabase/*`.
 * Track B (phase 04) PRODUCES these shapes from Supabase reads; Track A
 * (phases 05-08) CONSUMES them as props; phase 09 wires the two together at
 * `app/kudos/page.tsx`. Neither track imports the other — this file is the
 * only thing both sides depend on.
 *
 * `MessageFormat` is imported as a type only from the frozen
 * `compose-contract.ts` (phase 01) — no runtime dependency crosses in.
 *
 * A missing field here is escalated to the orchestrator, which amends this
 * phase's contract once and notifies both tracks — never patched
 * unilaterally inside a track (plan.md § Risk Assessment).
 *
 * Phase 04 (Viết Kudo) adds `messageFormat` and `anonymousSenderLabel` to
 * `KudosCardView`, additively — every existing field keeps its meaning, so
 * F004's shipped card and its e2e suite are unaffected until phase 05 reads
 * the new fields.
 */

import type { MessageFormat } from "@/lib/kudos/compose-contract";

export type BadgeTier = "New Hero" | "Rising Hero" | "Super Hero" | "Legend Hero";

export interface SunnerView {
  id: number;
  fullName: string;
  department: string;
  avatarUrl: string;
  badge: BadgeTier;
  /** The hoa-thị tooltip sentence for the badge; null for New Hero — no published copy below 10. */
  badgeTooltip: string | null;
}

export interface KudosAttachmentView {
  id: number;
  imageUrl: string;
}

export interface KudosCardView {
  id: number;
  sender: SunnerView;
  receiver: SunnerView;
  campaign: string | null;
  message: string;
  /** Pre-formatted "HH:mm - MM/DD/YYYY", rendered server-side at a fixed offset. */
  sentAtLabel: string;
  hashtags: string[];
  attachments: KudosAttachmentView[];
  hearts: number;
  likedByViewer: boolean;
  canLike: boolean;
  isOwnedByViewer: boolean;
  /** `'doc'` selects the rich-text renderer (phase 05); `'plain'` keeps F004's raw-text rendering. */
  messageFormat: MessageFormat;
  /** Non-null ⇒ the card renders the anonymous chip with this label instead of `sender`. */
  anonymousSenderLabel: string | null;
  /**
   * Internal marker: the Kudos was sent anonymously (F006 FR-602). It has NO
   * visual surface in this commission — the design frame publishes no such
   * element, so a chip would be invented design data. It exists so the
   * profile Sent list can reveal its own author (`anonymousSenderLabel: null`)
   * while still knowing the row was anonymous, which is what makes the Sent
   * count and the Sent list agree (SEC_002).
   */
  sentAnonymously: boolean;
}

export interface FilterOptionView {
  id: number;
  name: string;
}

export interface SidebarCountsView {
  kudosReceived: number;
  kudosSent: number;
  heartsReceived: number;
  secretBoxOpened: number;
  secretBoxUnopened: number;
}

export interface GiftRowView {
  id: number;
  /**
   * `gift_awards.sunner_id` — the recipient's `sunners.id`, added additively
   * by F006 phase 09 so the row's name can link to `/profile?id=` (FR-003).
   * NOT NULL on the base table, so there is no nullability to handle.
   */
  sunnerId: number;
  sunnerName: string;
  giftLabel: string;
}

export interface SpotlightNodeView {
  id: number;
  name: string;
  kudosId: number;
  receivedAtLabel: string;
  isJustUpdated: boolean;
}

export interface SpotlightTickerRowView {
  id: number;
  timeLabel: string;
  name: string;
}

export interface KudosBoardViewModel {
  /** Full feed, newest first. */
  kudos: KudosCardView[];
  /** 13 options, frame order. */
  hashtagOptions: FilterOptionView[];
  /** 50 options, frame order. */
  departmentOptions: FilterOptionView[];
  spotlight: {
    nodes: SpotlightNodeView[];
    ticker: SpotlightTickerRowView[];
  };
  sidebar: {
    counts: SidebarCountsView;
    gifts: GiftRowView[];
  };
  viewer: {
    isAuthenticated: boolean;
    /** Identity only — resolved from `sunners.auth_user_id = auth.uid()`. Never falls back to the seeded display viewer. */
    sunnerId: number | null;
  };
}

export interface KudosLikeResult {
  liked: boolean;
  hearts: number;
}

export type ToggleKudosLike = (kudosId: number) => Promise<KudosLikeResult>;
