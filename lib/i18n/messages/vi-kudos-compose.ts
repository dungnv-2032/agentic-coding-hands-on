import type { Dictionary } from "./dictionary";

/**
 * Vietnamese Viết Kudo compose copy, transcribed verbatim from
 * `e2e/fixtures/viet-kudo-constants.ts` and `plans/260907-0822-viet-kudo/
 * test-contract.md` where those exist — the fixture is the assertion
 * source, not the design CSV (test-cases are stale relative to the frame,
 * per `clarifications.md`). Straight quotes in `hints.body` are exact,
 * matching `BODY_HINT` in the fixture, not the frame's curly quotes.
 *
 * Strings marked "unauthored" below have no design/spec source and are
 * inferred faithful translations — flagged per phase-06's insight 3 and 6
 * so nobody mistakes them for spec-confirmed copy.
 */
export const viKudosCompose: Dictionary["kudosCompose"] = {
  title: "Gửi lời cám ơn và ghi nhận đến đồng đội",
  labels: {
    recipient: "Người nhận",
    title: "Danh hiệu",
    // Unauthored — no separate label node exists for the body field; only
    // its placeholder and hint are confirmed in the frame's node tree.
    body: "Nội dung",
    hashtag: "Hashtag",
    image: "Image",
  },
  placeholders: {
    recipient: "Tìm kiếm",
    title: "Dành tặng một danh hiệu cho đồng đội",
    body: "Hãy gửi gắm lời cám ơn và ghi nhận đến đồng đội tại đây nhé!",
    // Unauthored — see dictionary.ts doc comment.
    anonymousName: "Nhập tên bạn muốn hiển thị",
  },
  hints: {
    titleLine1: "Ví dụ: Người truyền động lực cho tôi.",
    titleLine2: "Danh hiệu sẽ hiển thị làm tiêu đề Kudos của bạn.",
    body: 'Bạn có thể "@ + tên" để nhắc tới đồng nghiệp khác',
  },
  buttons: {
    addHashtag: "+ Hashtag",
    addImage: "+ Image",
    max: "Tối đa 5",
    cancel: "Hủy",
    submit: "Gửi",
  },
  // Unauthored aria-labels, adapted from clarifications.md's abbreviated
  // toolbar names ("in đậm", "in nghiêng", "chèn liên kết", "trích dẫn").
  toolbar: {
    bold: "Đậm",
    italic: "Nghiêng",
    strike: "Gạch ngang",
    orderedList: "Danh sách đánh số",
    link: "Liên kết",
    quote: "Trích dẫn",
  },
  // Unauthored — test-contract.md § Rich-text toolbar requires the dialog
  // but names no literal copy for it. Its cancel action reuses
  // `buttons.cancel` rather than a second "Hủy" key.
  linkDialog: {
    heading: "Chèn liên kết",
    urlLabel: "URL",
    confirm: "Chèn",
  },
  errors: {
    required: "Không được để trống",
    tooMany: "Tối đa 5 hashtag",
    // Unauthored — test-contract.md ratification item 6.
    invalidType: "Định dạng file không được hỗ trợ",
    // Unauthored — no field-level "unknown" error is asserted anywhere.
    unknown: "Đã có lỗi xảy ra. Vui lòng thử lại.",
  },
  // Unauthored — the suite checks `role="option"` count, not this text.
  recipientEmpty: "Không tìm thấy người phù hợp.",
  // Unauthored — test-contract.md ratification item 6.
  communityStandards: "Tiêu chuẩn cộng đồng",
  anonymousCheckboxLabel: "Gửi lời cám ơn và ghi nhận ẩn danh",
  // Unauthored — see dictionary.ts doc comment.
  anonymousNameLabel: "Tên hiển thị ẩn danh",
  // Unauthored — no literal loading-state copy exists in the source data.
  submitPending: "Đang gửi...",
  // Unauthored — this phase's own string, per the task scope note.
  anonymousFallbackName: "Người ẩn danh",
};
