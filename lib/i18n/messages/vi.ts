import type { Dictionary } from "./dictionary";
import { viAwardSystem } from "./vi-award-system";
import { viHome } from "./vi-home";
import { viKudos } from "./vi-kudos";
import { viKudosCompose } from "./vi-kudos-compose";

export type { Dictionary };

/**
 * Vietnamese copy — the default locale (BR-003) and the authoritative source
 * shape for the Dictionary type. Copy is verbatim from the design/spec; do
 * not "improve" wording here without a spec change.
 */
export const vi: Dictionary = {
  login: {
    logoAlt: "Logo",
    wordmarkAlt: "ROOT FURTHER",
    subtitle: "Bắt đầu hành trình của bạn cùng SAA 2025.",
    tagline: "Đăng nhập để khám phá!",
    signInButton: "LOGIN With Google",
    errorOauthFailed: "Đăng nhập không thành công. Vui lòng thử lại.",
    languageLabel: "Ngôn ngữ",
    languageVi: "VN",
    languageEn: "EN",
  },
  footer: {
    copyright: "Bản quyền thuộc về Sun* © 2025",
    standards: "Tiêu chuẩn chung",
  },
  todo: {
    title: "Việc cần làm",
    signOut: "Đăng xuất",
  },
  header: {
    logoAlt: "Sun* Annual Awards 2025",
    about: "About SAA 2025",
    awardInformation: "Award Information",
    kudos: "Sun* Kudos",
    notificationsLabel: "Thông báo",
    notificationsEmpty: "Không có thông báo mới",
    accountLabel: "Tài khoản",
    profile: "Hồ sơ",
    signOut: "Đăng xuất",
    adminDashboard: "Trang quản trị",
  },
  home: viHome,
  awardSystem: viAwardSystem,
  comingSoon: {
    title: "Coming soon",
    body: "Nội dung đang được cập nhật. Vui lòng quay lại sau.",
  },
  kudos: viKudos,
  kudosCompose: viKudosCompose,
};
