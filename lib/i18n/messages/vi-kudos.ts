import type { Dictionary } from "./dictionary";

/**
 * Vietnamese Kudos Live Board copy, transcribed verbatim from
 * `plans/260906-1945-kudos-live-board/clarifications.md` (MoMorph screen
 * `MaZUn5xHXZ`, frame node `2940:13431`) and its test-contract companion.
 * Do not paraphrase — this is design copy. The em dash in the toast and the
 * trailing colons on every sidebar stat label are exact.
 */
export const viKudos: Dictionary["kudos"] = {
  hero: {
    title: "Hệ thống ghi nhận và cảm ơn",
    composePlaceholder: "Hôm nay, bạn muốn gửi lời cảm ơn và ghi nhận đến ai?",
    searchPlaceholder: "Tìm kiếm profile Sunner",
  },
  eyebrow: "Sun* Annual Awards 2025",
  sections: {
    highlight: "HIGHLIGHT KUDOS",
    spotlight: "SPOTLIGHT BOARD",
    allKudos: "ALL KUDOS",
  },
  filters: {
    hashtag: "Hashtag",
    department: "Phòng ban",
  },
  card: {
    copyLink: "Copy Link",
    viewDetail: "Xem chi tiết",
    empty: "Hiện tại chưa có Kudos nào.",
  },
  spotlightBoard: {
    searchPlaceholder: "Tìm kiếm",
    panZoom: "Pan/Zoom",
    tickerSuffix: "đã nhận được một Kudos mới",
    empty: "Không tìm thấy Sunner phù hợp.",
  },
  sidebar: {
    stats: {
      kudosReceived: "Số Kudos bạn nhận được:",
      kudosSent: "Số Kudos bạn đã gửi:",
      heartsReceived: "Số tim bạn nhận được:",
      secretBoxOpened: "Số Secret Box bạn đã mở:",
      secretBoxUnopened: "Số Secret Box chưa mở:",
    },
    secretBoxButton: "Mở Secret Box",
    giftHeading: "10 SUNNER NHẬN QUÀ MỚI NHẤT",
    giftEmpty: "Chưa có dữ liệu",
  },
  toast: {
    copySuccess: "Link copied — ready to share!",
    copyFailure: "Không thể copy liên kết. Vui lòng thử lại.",
  },
};
