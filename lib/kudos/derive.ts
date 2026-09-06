/**
 * Pure helpers shared by both Kudos Live Board tracks (phase 01, frozen).
 *
 * Zero runtime dependencies: no I/O, no React, no `Intl` (ICU version drift
 * between the server and browser runtimes would hydration-mismatch a value
 * like "1.000" — see plan.md § Key Insights #4). This module is reachable
 * from the client bundle, so it must never import anything server-only.
 */

import type { BadgeTier, KudosCardView } from "./view-model";

/** 50 seeded rows page five times, satisfying assumption A4. */
export const FEED_PAGE_SIZE = 10;

/** `< 10` New Hero · `>= 10` Rising · `>= 20` Super · `>= 50` Legend Hero. */
export function badgeTierFor(receivedCount: number): BadgeTier {
  if (receivedCount >= 50) return "Legend Hero";
  if (receivedCount >= 20) return "Super Hero";
  if (receivedCount >= 10) return "Rising Hero";
  return "New Hero";
}

/**
 * Verbatim from clarifications.md § "Badge tooltip copy" — copy-pasted, not
 * retyped. `New Hero` has no published copy below the 10-Kudos threshold.
 */
const BADGE_TOOLTIPS: Record<BadgeTier, string | null> = {
  "New Hero": null,
  "Rising Hero":
    "Sunner đã nhận được 10 Kudos và bắt đầu lan tỏa năng lượng ấm áp đến mọi người xung quanh.",
  "Super Hero":
    "Sunner đã nhận được 20 Kudos và chứng minh sức ảnh hưởng của mình qua những hành động lan tỏa tích cực mỗi ngày.",
  "Legend Hero":
    "Sunner đã nhận được 50 Kudos và trở thành hình mẫu của sự công nhận, sẻ chia và lan tỏa tinh thần Sun*.",
};

export function badgeTooltipFor(tier: BadgeTier): string | null {
  return BADGE_TOOLTIPS[tier];
}

/**
 * Dot-grouped thousands, e.g. `1000` → `"1.000"`. Explicit digit-grouping,
 * never `toLocaleString`/`Intl` — see module doc.
 */
export function formatHeartCount(n: number): string {
  const negative = n < 0;
  const digits = Math.trunc(Math.abs(n)).toString();
  let grouped = "";
  for (let i = 0; i < digits.length; i++) {
    const fromEnd = digits.length - i;
    grouped += digits[i];
    if (fromEnd > 1 && fromEnd % 3 === 1) grouped += ".";
  }
  return negative ? `-${grouped}` : grouped;
}

/** Fixed UTC+7 offset (Asia/Ho_Chi_Minh) — no timezone database, no `Intl`. */
const FIXED_OFFSET_MINUTES = 7 * 60;

function pad2(n: number): string {
  return n.toString().padStart(2, "0");
}

/**
 * `HH:mm - MM/DD/YYYY` at a fixed offset, matching `e2e/kudos-live-board.spec.ts`
 * (`^\d{2}:\d{2} - \d{2}\/\d{2}\/\d{4}$`). Format server-side only, at render
 * time — the client never re-derives it (plan.md § Risk Assessment).
 */
export function formatSentAt(iso: string): string {
  const utcMs = new Date(iso).getTime();
  const shifted = new Date(utcMs + FIXED_OFFSET_MINUTES * 60_000);
  const hh = pad2(shifted.getUTCHours());
  const mm = pad2(shifted.getUTCMinutes());
  const mo = pad2(shifted.getUTCMonth() + 1);
  const dd = pad2(shifted.getUTCDate());
  const yyyy = shifted.getUTCFullYear();
  return `${hh}:${mm} - ${mo}/${dd}/${yyyy}`;
}

/**
 * ALG-001 — `[...cards].sort(hearts desc).slice(0, 5)`, stable tie-break on
 * `id desc` so SSR and the first client render agree.
 */
export function pickHighlight(cards: readonly KudosCardView[]): KudosCardView[] {
  return [...cards]
    .sort((a, b) => b.hearts - a.hearts || b.id - a.id)
    .slice(0, 5);
}

export interface KudosFilters {
  hashtag: string | null;
  department: string | null;
}

/** AND-combined; department matches `receiver.department`. */
export function matchesFilters(card: KudosCardView, filters: KudosFilters): boolean {
  if (filters.hashtag !== null && !card.hashtags.includes(filters.hashtag)) {
    return false;
  }
  if (filters.department !== null && card.receiver.department !== filters.department) {
    return false;
  }
  return true;
}
