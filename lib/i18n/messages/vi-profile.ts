import type { Dictionary } from "./dictionary";

/**
 * Vietnamese Profile bản thân copy, transcribed verbatim from
 * `plans/260908-0854-profile-ban-than/clarifications.md` (MoMorph screen
 * `3FoIx6ALVb`, frame node `362:5037`) and its visual study companion.
 * Do not paraphrase — this is design copy.
 *
 * `stats.*` (all five rows) and `stats.secretBoxButton` are copy-pasted from
 * the shipped `vi-kudos.ts` `sidebar.stats`/`secretBoxButton` — the visual
 * study measured them identical to the board sidebar (AMEND-3), so they are
 * reused verbatim rather than retyped.
 */
export const viProfile: Dictionary["profile"] = {
  badges: {
    headingSelf: "Bộ sưu tập icon của tôi",
    headingOther: "Bộ sưu tập icon",
  },
  stats: {
    kudosReceived: "Số Kudos bạn nhận được:",
    kudosSent: "Số Kudos bạn đã gửi:",
    heartsReceived: "Số tim bạn nhận được:",
    secretBoxOpened: "Số Secret Box bạn đã mở:",
    secretBoxUnopened: "Số Secret Box chưa mở:",
    secretBoxButton: "Mở Secret Box",
  },
  writeBar: {
    label: "Gửi lời cảm ơn và ghi nhận đến {name}",
  },
  direction: {
    receivedLabel: "Đã nhận ({count})",
    sentLabel: "Đã gửi ({count})",
  },
  feed: {
    emptyReceived: "Hiện tại chưa có Kudos nào.",
    emptySent: "Bạn chưa gửi Kudos nào.",
    /**
     * UNSOURCED — `docs/screens/SCR006_ProfileBanThan/spec.md` marks this
     * copy key `TBD (draft)` in all three rows that reference it (lines 84,
     * 99-100, 133); the MoMorph frame never scrolled to `hasMore === false`.
     * F004's board shows NO end-of-feed message by design (functional-spec
     * "dừng lặng lẽ ở trạng thái hiện tại" — stops silently), so there is no
     * precedent to reuse either. Left empty rather than invented; a later
     * copy pass must fill this in before Track A renders `feed.D.end`.
     *
     * RESOLVED (orchestrator, 2026-09-08) — this string is **authored, not
     * frame-sourced**, and is marked as such on purpose. The frame genuinely
     * never captured it, but TC_WEB_PROFILE_FUN_013 requires that "an
     * end-of-feed message is shown instead of a loading indicator" when the
     * last page is reached, so shipping `""` would fail a design-authority
     * test case rather than honour it. Refusing to invent a *design value*
     * (a colour, a layout, badge artwork) is right — that is what retired the
     * hoa-thị stars. A copy string whose existence the behavioural spec
     * mandates is a different category: the decision is which words, not
     * whether the element exists. Voice matches the board's received-empty
     * copy (`Hiện tại chưa có Kudos nào.`): plain, sentence-terminated.
     */
    endOfFeed: "Bạn đã xem hết Kudos.",
  },
};
