/**
 * Shape of a locale's message set. Fields are plain `string` (not literal
 * types via `as const`) so `en.ts` can satisfy the same type with different
 * copy while a missing/misspelled key is still a compile error.
 */
export interface Dictionary {
  login: {
    logoAlt: string;
    wordmarkAlt: string;
    subtitle: string;
    tagline: string;
    signInButton: string;
    errorOauthFailed: string;
    languageLabel: string;
    languageVi: string;
    languageEn: string;
  };
  footer: {
    copyright: string;
  };
  todo: {
    title: string;
    signOut: string;
  };
}

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
  },
  todo: {
    title: "Việc cần làm",
    signOut: "Đăng xuất",
  },
};
