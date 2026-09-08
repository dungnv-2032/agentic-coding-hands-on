/**
 * Shared constants for Profile bản thân E2E tests.
 * Every value is transcribed from `plans/260908-0854-profile-ban-than/clarifications.md`,
 * which is authoritative.
 */

export const ROUTE = "/profile";

/** Frame viewer (id=1) — seeded in supabase/seed.sql */
export const FRAME_VIEWER_NAME = "Huỳnh Dương Xuân Nhật";
export const FRAME_VIEWER_ID = 1;

/**
 * Sunner 1's department and tier, measured off the running seed:
 * `kudos_received_baseline = 0` + 26 received rows = 26, and
 * `badgeTierFor(26)` (`lib/kudos/derive.ts:18`) is `Super Hero`. The next
 * threshold is 50, so 24 further Kudos would have to land on this Sunner
 * before the value moves — no test in this suite sends any to id=1.
 */
export const FRAME_VIEWER_DEPARTMENT = "CEVC10";
export const FRAME_VIEWER_BADGE_TIER = "Super Hero";

/** Frame receiver (id=2) — seeded in supabase/seed.sql */
export const FRAME_RECEIVER_NAME = "Huỳnh Dương Xuân";
export const FRAME_RECEIVER_ID = 2;

/**
 * SEC_002's compose target. Deliberately NOT the frame viewer or the frame
 * receiver: the anonymous Kudo that test writes changes its recipient's
 * received count, and no other case in this suite reads anything about
 * sunner 9. The name is also unambiguous in the recipient picker's substring
 * search, unlike "Huỳnh Dương Xuân", which is a prefix of sunner 1's name.
 */
export const COMPOSE_TARGET_NAME = "Nguyễn Hoàng Linh";

/**
 * `ANONYMOUS_FALLBACK_LABEL` from `lib/kudos/map-kudos-card.ts:22` — what a
 * viewer who is NOT the sender sees in the sender slot of an anonymous Kudo
 * composed with a blank display name.
 */
export const ANONYMOUS_SENDER_LABEL = "Ẩn danh";

/**
 * Where `profile-auth.setup.ts` records the signed-up session's email and its
 * local-part. The sparse self hero renders that local-part as its name
 * (`lib/profile/profile-data.ts` § `readJwtIdentityFallback`), so a test that
 * asserts the sparse hero needs the value the setup actually created rather
 * than a pattern. Gitignored with the rest of `e2e/.auth/`.
 */
export const PROFILE_SESSION_META_FILE = "e2e/.auth/profile-user-meta.json";

/** Number of badge slots (always rendered, always greyed) */
export const BADGE_SLOT_COUNT = 6;

/** Statistics card labels (from vi-profile.ts stats block, matching board sidebar) */
export const STATS_LABELS = [
  "Số Kudos bạn nhận được:",
  "Số Kudos bạn đã gửi:",
  "Số tim bạn nhận được:",
  "Số Secret Box bạn đã mở:",
  "Số Secret Box chưa mở:",
];

/**
 * Direction dropdown labels — BARE, while the UI renders
 * `"Đã nhận ({count})"` (`lib/i18n/messages/vi-profile.ts`). Every use must be
 * a substring match SCOPED to one element, e.g.
 * `getByTestId("profile-direction-option").filter({ hasText: … })`.
 *
 * A bare `page.getByText(DIRECTION_LABELS.received)` is a strict-mode
 * violation — the trigger and the active option both render the received
 * label. `DIRECTION_LABELS.sent` is no safer: the statistics card's label
 * `Số Kudos bạn đã gửi:` also contains "Đã gửi" (case-insensitively it is the
 * same substring `getByText` matches), which is what broke FUN_010, FUN_012
 * and SEC_002 on the first GREEN attempt.
 */
export const DIRECTION_LABELS = {
  received: "Đã nhận",
  sent: "Đã gửi",
};

/** Empty state copy for Received and Sent directions */
export const EMPTY_STATES = {
  received: "Hiện tại chưa có Kudos nào.",
  sent: "Bạn chưa gửi Kudos nào.",
};

/** End of feed message */
export const END_OF_FEED_MESSAGE = "Bạn đã xem hết Kudos.";

/** Secret Box button label */
export const SECRET_BOX_BUTTON_LABEL = "Mở Secret Box";
