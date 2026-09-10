import type { Dictionary } from "./dictionary";

/**
 * Vietnamese Open Secret Box copy (F009, MoMorph screen `J3-4YFIpMM`, frame
 * `1466:7676`), transcribed verbatim from `design/geometry.md` — do not
 * paraphrase, this is design copy.
 *
 * `title`/`instruction`/`countLabel` come straight from `get_node` on the
 * frame ([clarifications.md](../../../plans/260910-1708-open-secret-box/clarifications.md):
 * the frame wins over the spec CSV, whose `MỞ SECRET BOX THÀNH CÔNG` /
 * `Click vào box để tiếp tục mở` leaked in from the *đã mở* sibling screen).
 * `Secretbox` is unspaced exactly as drawn — not a typo to fix.
 *
 * Sourced nodes: `title` `1466:7678`, `instruction` `1466:7683`, `countLabel`
 * `1466:7692`.
 *
 * `openerLabel`, `closeLabel`, `signInPrompt`, `signInCta`, `badgeAltPrefix`
 * and `errorGeneric` are unauthored — the frame draws no separate text for
 * them (an accessible name, a sign-in nudge, an error string). Phrased to
 * match the shipped `kudos.sidebar.secretBoxButton` ("Mở Secret Box") and
 * `rules.closeButton` ("Đóng") conventions rather than invented from
 * scratch.
 */
export const viSecretBox: Dictionary["secretBox"] = {
  title: "KHÁM PHÁ SECRET BOX CỦA BẠN",
  instruction: "Click vào box để mở",
  countLabel: "Secretbox chưa mở",
  openerLabel: "Mở Secret Box",
  closeLabel: "Đóng",
  signInPrompt: "Đăng nhập để mở Secret Box của bạn",
  signInCta: "Đăng nhập",
  badgeAltPrefix: "Huy hiệu",
  errorGeneric: "Có lỗi xảy ra. Vui lòng thử lại.",
};
