/**
 * Frozen integration contract for the Kudos Live Board (F004).
 *
 * Types only — no runtime export, no `next/headers`, no `@/lib/supabase/*`.
 * Track B (phase 04) PRODUCES these shapes from Supabase reads; Track A
 * (phases 05-08) CONSUMES them as props; phase 09 wires the two together at
 * `app/kudos/page.tsx`. Neither track imports the other — this file is the
 * only thing both sides depend on.
 *
 * A missing field here is escalated to the orchestrator, which amends this
 * phase's contract once and notifies both tracks — never patched
 * unilaterally inside a track (plan.md § Risk Assessment).
 */

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
