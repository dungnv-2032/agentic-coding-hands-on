/**
 * Shared constants for the Thể lệ (SCR007) E2E spec.
 *
 * Every string below is transcribed verbatim from
 * `plans/260909-0838-the-le-rules-panel/clarifications.md`
 * § "Resolved from source data" and § "Test contract", which are
 * AUTHORITATIVE (MoMorph screen `b1Filzi9i6`, frame node `3204:6051`).
 * Repo convention (researcher-02 § 3): Vietnamese copy is never inlined in a
 * spec body — a copy change must stay a one-line fix here.
 *
 * ONE VALUE BELOW LOOKS LIKE A TYPO AND IS DELIBERATE. Do not "fix" it:
 *
 * 1. `Có 10–20 người gửi Kudos cho bạn` uses an EN DASH (U+2013), not a
 *    hyphen — tiers 1 and 2 use plain hyphens, tier 3 does not. That is what
 *    the frame's text node holds.
 *
 * `ROOT FURTHER` was briefly shipped as `ROOT FUTHER`, on the reasoning that
 * "the text node reads FUTHER". That reasoning read the wrong field. On node
 * `I3204:6088;737:20392`, `itemName` — the Figma LAYER name — is
 * "ROOT FUTHER", while `character` — the rendered TEXT — is "ROOT FURTHER".
 * The frame render agrees with `character`. Corrected in phase 08 after a
 * MoMorph re-read; the seed carries the same correction.
 *
 * The tier descriptions for positions 1 and 4 also carry en dashes
 * (`bắt đầu – những`, `huyền thoại – người`), preserved byte-for-byte.
 */

/** The route the drawer ships on — replaces the `ComingSoon` placeholder. */
export const ROUTE = "/standards";

/** Where `Viết KUDOS` points (DEC-001: this repo's compose surface is a route). */
export const COMPOSE_ROUTE = "/kudos/new";

/** Panel title — `3204:6055`, rendered as the page `<h1>` (FR-201). */
export const PANEL_TITLE = "Thể lệ";

/** Section headings in ascending `position` order (FR-202, BR-001). */
export const SECTION_HEADINGS = [
  "NGƯỜI NHẬN KUDOS: HUY HIỆU HERO CHO NHỮNG ẢNH HƯỞNG TÍCH CỰC",
  "NGƯỜI GỬI KUDOS: SƯU TẬP TRỌN BỘ 6 ICON, NHẬN NGAY PHẦN QUÀ BÍ ẨN",
  "KUDOS QUỐC DÂN",
] as const;

/** Section bodies, same order as `SECTION_HEADINGS` (`3204:6133`, `:6078`, `:6091`). */
export const SECTION_BODIES = [
  "Dựa trên số lượng đồng đội gửi trao Kudos, bạn sẽ sở hữu Huy hiệu Hero tương ứng, được hiển thị trực tiếp cạnh tên profile",
  "Mỗi lời Kudos bạn gửi sẽ được đăng tải trên hệ thống và nhận về những lượt ❤️ từ cộng đồng Sunner. Cứ mỗi 5 lượt ❤️, bạn sẽ được mở 1 Secret Box, với cơ hội nhận về một trong 6 icon độc quyền của SAA.",
  "5 Kudos nhận về nhiều ❤️ nhất toàn Sun* sẽ chính thức trở thành Kudos Quốc Dân và được trao phần quà đặc biệt từ SAA 2025: Root Further.",
] as const;

/** Section 2's closing line, rendered AFTER the icon grid (`3204:6089`, FR-202). */
export const SECTION_2_CLOSING_BODY =
  "Những Sunner thu thập trọn bộ 6 icon sẽ nhận về một phần quà bí ẩn từ SAA 2025.";

/** Hero tier threshold labels in `position` order (FR-203, BR-001). */
export const HERO_TIER_LABELS = [
  "Có 1-4 người gửi Kudos cho bạn",
  "Có 5-9 người gửi Kudos cho bạn",
  "Có 10–20 người gửi Kudos cho bạn", // en dash — verbatim, see file header
  "Có hơn 20 người gửi Kudos cho bạn",
] as const;

/** Hero tier descriptions, same order as `HERO_TIER_LABELS`. */
export const HERO_TIER_DESCRIPTIONS = [
  "Hành trình lan tỏa điều tốt đẹp bắt đầu – những lời cảm ơn và ghi nhận đầu tiên đã tìm đến bạn.",
  "Hình ảnh bạn đang lớn dần trong trái tim đồng đội bằng sự tử tế và cống hiến của mình.",
  "Bạn đã trở thành biểu tượng được tin tưởng và yêu quý, người luôn sẵn sàng hỗ trợ và được nhiều đồng đội nhớ đến.",
  "Bạn đã trở thành huyền thoại – người để lại dấu ấn khó quên trong tập thể bằng trái tim và hành động của mình.",
] as const;

/** Collectible icon captions in `position` order (FR-204, BR-001). */
export const COLLECTIBLE_CAPTIONS = [
  "REVIVAL",
  "TOUCH OF LIGHT",
  "STAY GOLD",
  "FLOW TO HORIZON",
  "BEYOND THE BOUNDARY",
  "ROOT FURTHER",
] as const;

/** Footer control labels — `3204:6093` / `3204:6094`, also `vi-rules.ts`. */
export const CLOSE_LABEL = "Đóng";
export const WRITE_KUDOS_LABEL = "Viết KUDOS";

/**
 * The floating widget's `/standards` shortcut on the homepage
 * (`vi-home.ts:79` → `home.widget.standards`, used as the link's aria-label
 * in `app/_components/floating-widget.tsx`). FUN_003 clicks THIS to earn a
 * genuine client-side history entry before testing `Đóng`.
 */
export const WIDGET_STANDARDS_LABEL = "Thể lệ SAA";

/** Expected element counts — mirrors clarifications.md § "Test contract". */
export const SECTION_COUNT = 3;
export const HERO_TIER_COUNT = 4;
export const COLLECTIBLE_ICON_COUNT = 6;
