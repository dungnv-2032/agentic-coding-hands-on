/**
 * Shared constants for Kudos Live Board E2E tests.
 * Used by both kudos-live-board.spec.ts (anon) and kudos-live-board-authed.spec.ts (authed).
 *
 * Every value is transcribed from
 * `plans/260906-1945-kudos-live-board/clarifications.md`, which is authoritative.
 */

export const ROUTE = "/kudos";
export const PAGE_TITLE = "Hệ thống ghi nhận và cảm ơn";
export const HERO_EYEBROW = "Sun* Annual Awards 2025";

/** Compose bar accessible name (test-contract A.1, clarifications § Hero). */
export const COMPOSE_LABEL =
  "Hôm nay, bạn muốn gửi lời cảm ơn và ghi nhận đến ai?";

/** Sunner search placeholder (clarifications § Hero). */
export const SUNNER_SEARCH_PLACEHOLDER = "Tìm kiếm profile Sunner";

/** Spotlight search placeholder (test-contract B.7, clarifications § Spotlight). */
export const SPOTLIGHT_SEARCH_PLACEHOLDER = "Tìm kiếm";

/** Toast text when kudos link is copied (test-contract B.5, clarifications § Toast). */
export const COPY_LINK_TOAST = "Link copied — ready to share!";

/** Spotlight canvas heading (test-contract B.6). */
export const SPOTLIGHT_COUNT_TEXT = "388 KUDOS";

/** Secret Box button label (test-contract D.1.8). */
export const SECRET_BOX_LABEL = "Mở Secret Box";

/** Gift leaderboard heading (test-contract D.3). */
export const GIFT_LEADERBOARD_HEADING = "10 SUNNER NHẬN QUÀ MỚI NHẤT";

/** Empty state text (test-contract C.4.5). */
export const EMPTY_KUDOS_TEXT = "Hiện tại chưa có Kudos nào.";

/** Gift leaderboard empty state (test-contract D.3). */
export const GIFT_EMPTY_TEXT = "Chưa có dữ liệu";

/**
 * Hashtag filter options (clarifications § Resolved from source data,
 * from `JWpsISMAaM` item A, verbatim, 13 entries).
 */
export const HASHTAG_OPTIONS = [
  "Toàn diện",
  "Giỏi chuyên môn",
  "Hiệu suất cao",
  "Truyền cảm hứng",
  "Cống hiến",
  "Aim High",
  "Be Agile",
  "Wasshoi",
  "Hướng mục tiêu",
  "Hướng khách hàng",
  "Chuẩn quy trình",
  "Giải pháp sáng tạo",
  "Quản lý xuất sắc",
];

/**
 * Test department for K-26..K-30 — seed has 12 kudos to receiver in this department,
 * used as the narrowing target for filter assertions.
 */
export const TEST_DEPARTMENT = "STVC - R&D";

/**
 * Test hashtag for K-31..K-35 — position 8 of 13, so outside the 6 visible rows in the
 * 348px box; 8/69 seeded kudos carry this tag, narrowing is clear. Chosen to exercise
 * both the scroll box (K-31) and filter retention (K-34).
 */
export const TEST_HASHTAG = "Wasshoi";

/**
 * Department filter options (clarifications § Resolved from source data,
 * from `WXK5AYB_rG` item A, verbatim, 50 entries — the dropdown frame holds
 * 50; clarifications.md originally mislabelled it 48 and was corrected by
 * test-contract.md § "Blueprint ratification". `CEVC10` is deliberately NOT
 * among them: it is the frame people's department but not a filter option).
 */
export const DEPARTMENT_OPTIONS = [
  "CTO",
  "SPD",
  "FCOV",
  "CEVC1",
  "CEVC2",
  "STVC - R&D",
  "CEVC2 - CySS",
  "FCOV - LRM",
  "CEVC2 - System",
  "OPDC - HRF",
  "CEVC1 - DSV - UI/UX 1",
  "CEVC1 - DSV",
  "CEVEC",
  "OPDC - HRD - C&C",
  "STVC",
  "FCOV - F&A",
  "CEVC1 - DSV - UI/UX 2",
  "CEVC1 - AIE",
  "OPDC - HRF - C&B",
  "FCOV - GA",
  "FCOV - ISO",
  "STVC - EE",
  "GEU - HUST",
  "CEVEC - SAPD",
  "OPDC - HRF - OD",
  "CEVEC - GSD",
  "GEU - TM",
  "STVC - R&D - DTR",
  "STVC - R&D - DPS",
  "CEVC3",
  "STVC - R&D - AIR",
  "CEVC4",
  "PAO",
  "GEU",
  "GEU - DUT",
  "OPDC - HRD - L&D",
  "OPDC - HRD - TI",
  "OPDC - HRF - TA",
  "GEU - UET",
  "STVC - R&D - SDX",
  "OPDC - HRD - HRBP",
  "PAO - PEC",
  "IAV",
  "STVC - Infra",
  "CPV - CGP",
  "GEU - UIT",
  "OPDC - HRD",
  "BDV",
  "CPV",
  "PAO - PAO",
];

/**
 * Badge tiers and tooltip copy (test-contract B.3.2/B.3.6, clarifications).
 * Order matches the Figma spec; the badge text one of these four.
 */
export type BadgeTier = "New Hero" | "Rising Hero" | "Super Hero" | "Legend Hero";

export const BADGE_TIERS: Record<BadgeTier, string | null> = {
  // clarifications § "Card badges": four tiers over the three published hoa-thi
  // thresholds. New Hero (< 10 received) is the pre-threshold tier and has NO
  // published copy, so it carries no tooltip — null, not a borrowed sentence.
  "New Hero": null,
  // 1 hoa thi — >= 10 received.
  "Rising Hero":
    "Sunner đã nhận được 10 Kudos và bắt đầu lan tỏa năng lượng ấm áp đến mọi người xung quanh.",
  // 2 hoa thi — >= 20 received.
  "Super Hero":
    "Sunner đã nhận được 20 Kudos và chứng minh sức ảnh hưởng của mình qua những hành động lan tỏa tích cực mỗi ngày.",
  // 3 hoa thi — >= 50 received.
  "Legend Hero":
    "Sunner đã nhận được 50 Kudos và trở thành hình mẫu của sự công nhận, sẻ chia và lan tỏa tinh thần Sun*.",
};

/**
 * Spotlight word-cloud names (clarifications § Resolved from source data,
 * verbatim, 7 entries).
 */
export const SPOTLIGHT_NAMES = [
  "Đỗ hoàng Hiệp",
  "Dương thúy An",
  "Mai phương Thúy",
  "Nguyễn Văn Quy",
  "Lê Kiều Trang",
  "Nguyễn Bá Chức",
  "Nguyễn Hoàng Linh",
];

/**
 * Sidebar stat labels (test-contract D.1, clarifications § Resolved).
 * In order, as they appear in the sidebar.
 */
export const SIDEBAR_STATS = [
  "Số Kudos bạn nhận được:",
  "Số Kudos bạn đã gửi:",
  "Số tim bạn nhận được:",
  "Số Secret Box bạn đã mở:",
  "Số Secret Box chưa mở:",
];
