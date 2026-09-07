import rawSpec from "../../pt-spec.json";

/* ---------- pt-spec.json の型（references/pt-spec-format.md v2 と対応） ---------- */
export interface Source {
  id: string;
  type: string;
  path?: string;
  note?: string;
}
export interface Grounding {
  iaScreen?: string;
  personas?: string[];
  stories?: string[];
  reqs?: string[];
  assumptions?: string[];
}
export interface ScreenMeta {
  id: string;
  name: string;
  role?: string;
  primaryAction?: string;
  device?: "mobile" | "tablet" | "desktop" | "responsive";
  states?: string[];
  grounding?: Grounding;
  mock?: { source?: string; notes?: string };
}
export interface Transition {
  from: string;
  to: string;
  condition?: string;
  kind?: "main" | "sub";
  flow?: string;
}
export type AppType = "mobile-app" | "web-app" | "both";
export interface PtSpec {
  meta: {
    product: string;
    users?: string;
    primaryGoal?: string;
    device?: string;
    appType?: AppType;          // デザインイディオムの分岐（フレーム表示・デバイス選択肢・観点）
    stage?: string;
    sources?: Source[];
    assumptions?: string[];
  };
  design: {
    direction?: string;
    source?: string;
    notes?: string[];
    colors?: Record<string, string>;
    typography?: { family?: string; baseSize?: string; scale?: Record<string, string> };
    shape?: { radius?: string; density?: string; shadow?: string };
  };
  requirements?: string[];
  screens: ScreenMeta[];
  transitions?: Transition[];
}

export const spec = rawSpec as unknown as PtSpec;
export const screensById: Record<string, ScreenMeta> = Object.fromEntries(
  spec.screens.map((s) => [s.id, s]),
);
export const firstScreenId = spec.screens[0]?.id ?? "";

/* アプリ種別: mobile-app = ネイティブ表示（ホームインジケータ・Desktopなし）/
   web-app = ブラウザ表示 / both = レビューで Web ⇄ アプリを切替可能 */
export function appType(): AppType {
  return spec.meta.appType ?? "web-app";
}
/* 既定の表示イディオム（ピュアモード・サムネイルで使用） */
export function defaultAppMode(): "web" | "native" {
  return appType() === "mobile-app" ? "native" : "web";
}
export function deviceOptions(native: boolean): string[] {
  return native ? ["mobile", "tablet"] : ["mobile", "tablet", "desktop"];
}

export function statesOf(s: ScreenMeta): string[] {
  const st = [...(s.states ?? [])];
  if (!st.includes("default")) st.unshift("default");
  return st;
}
export function transitionsFrom(id: string): Transition[] {
  return (spec.transitions ?? []).filter((t) => t.from === id);
}
export function transitionsTo(id: string): Transition[] {
  return (spec.transitions ?? []).filter((t) => t.to === id);
}
export function flows(): Record<string, Transition[]> {
  const g: Record<string, Transition[]> = {};
  for (const t of spec.transitions ?? []) (g[t.flow ?? "メインフロー"] ??= []).push(t);
  return g;
}
export function coveringScreens(req: string): ScreenMeta[] {
  return spec.screens.filter((s) => (s.grounding?.reqs ?? []).includes(req));
}
export function uncoveredReqs(): string[] {
  return (spec.requirements ?? []).filter((r) => coveringScreens(r).length === 0);
}

/* ---------- WCAG コントラスト（デザインシステムページの検査用） ---------- */
function luminance(hex: string): number | null {
  const m = /^#?([0-9a-f]{6})$/i.exec(hex.trim());
  if (!m) return null;
  const v = [0, 2, 4].map((i) => {
    const c = parseInt(m[1].slice(i, i + 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2];
}
export function contrastRatio(a?: string, b?: string): number | null {
  if (!a || !b) return null;
  const la = luminance(a), lb = luminance(b);
  if (la == null || lb == null) return null;
  const [hi, lo] = la > lb ? [la, lb] : [lb, la];
  return (hi + 0.05) / (lo + 0.05);
}
