/**
 * Shared constants for Viết Kudo compose screen E2E tests.
 * Every value is transcribed from
 * `plans/260907-0822-viet-kudo/clarifications.md` and `test-contract.md`,
 * which are authoritative.
 */

export const ROUTE = "/kudos/new";
export const PAGE_TITLE = "Gửi lời cám ơn và ghi nhận đến đồng đội";
export const RECIPIENT_PLACEHOLDER = "Tìm kiếm";
export const TITLE_PLACEHOLDER = "Dành tặng một danh hiệu cho đồng đội";
export const BODY_PLACEHOLDER =
  "Hãy gửi gắm lời cám ơn và ghi nhận đến đồng đội tại đây nhé!";
export const TITLE_HINT_1 = "Ví dụ: Người truyền động lực cho tôi.";
export const TITLE_HINT_2 =
  "Danh hiệu sẽ hiển thị làm tiêu đề Kudos của bạn.";
export const BODY_HINT =
  'Bạn có thể "@ + tên" để nhắc tới đồng nghiệp khác';
export const ANONYMOUS_CHECKBOX_LABEL =
  "Gửi lời cám ơn và ghi nhận ẩn danh";
export const HASHTAG_BUTTON_LABEL = "Hashtag";
export const HASHTAG_MAX_LABEL = "Tối đa 5";
export const HASHTAG_ERROR_FULL = "Tối đa 5 hashtag";
export const IMAGE_BUTTON_LABEL = "Image";
export const IMAGE_MAX_LABEL = "Tối đa 5";
export const RECIPIENT_ERROR = "Không được để trống";
export const TITLE_ERROR = "Không được để trống";
export const BODY_ERROR = "Không được để trống";
export const HASHTAG_REQUIRED_ERROR = "Không được để trống";
export const COMMUNITY_STANDARDS_LABEL = "Tiêu chuẩn cộng đồng";
export const CANCEL_BUTTON_LABEL = "Hủy";
export const SUBMIT_BUTTON_LABEL = "Gửi";
export const RECIPIENT_EMPTY_STATE = "No matches found"; // Will be localized; use role="option" count check instead
export const IMAGE_ERROR_INVALID_TYPE = "Định dạng file không được hỗ trợ";

/** Test data: two distinct sunner names for recipient selection
 * WARNING: These constants are NOT present in supabase/seed.sql (phase-02 repair):
 * - TEST_SUNNER_1 "Nguyễn Văn An" does not exist in the seed
 * - TEST_SUNNER_2 "Đỗ Hoàng Hiệp" exists in seed but with lowercase "hoàng" ("Đỗ hoàng Hiệp")
 * These are unused in viet-kudo.spec.ts (all tests use "Nguyễn" substring search + .first()).
 * Keep these constants available for future direct recipient selection tests, but do not rely on them without verifying against the live seed.
 */
export const TEST_SUNNER_1 = "Nguyễn Văn An";
export const TEST_SUNNER_2 = "Đỗ Hoàng Hiệp";

/** Test data: sample hashtags from the companion frame */
export const TEST_HASHTAG_1 = "Toàn diện";
export const TEST_HASHTAG_2 = "Giỏi chuyên môn";
export const TEST_HASHTAG_3 = "Hiệu suất cao";
export const TEST_HASHTAG_4 = "Truyền cảm hứng";
export const TEST_HASHTAG_5 = "Cống hiến";

/** Test data: sample title and body text */
export const TEST_TITLE = "Người truyền động lực cho tôi";
export const TEST_BODY = "Cảm ơn bạn vì đã luôn hỗ trợ và cầu chúc cho tôi";
export const TEST_ANONYMOUS_NAME = "Người bí ẩn";
