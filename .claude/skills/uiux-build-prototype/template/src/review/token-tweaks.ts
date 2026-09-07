import { spec } from "@/pt/spec";

/* デザインシステムページの「検討調整」— design.colors / radius を document の
   :root CSSカスタムプロパティにライブ適用する一時オーバーライド。
   リロードで消える（確定は cssSnippet() をコピーして globals.css へ還元する）。
   モジュールスコープに保持するので、レビュー内のタブ移動では調整が維持される */

/* design のキー → shadcn 変数（references/pt-spec-format.md のトークン写像と同一） */
export const TOKEN_MAP: Record<string, string[]> = {
  bg: ["--background"],
  text: ["--foreground"],
  surface: ["--card"],
  primary: ["--primary", "--ring"],
  primaryText: ["--primary-foreground"],
  textSub: ["--muted-foreground"],
  accent: ["--accent"],
  border: ["--border", "--input"],
  success: ["--success"],
  warning: ["--warning"],
  danger: ["--destructive"],
};

export interface Tweaks {
  colors: Record<string, string>;
  radius: string;
}

function specDefaults(): Tweaks {
  const colors: Record<string, string> = {};
  for (const k of Object.keys(TOKEN_MAP)) {
    const v = spec.design.colors?.[k];
    if (v) colors[k] = v;
  }
  return { colors, radius: spec.design.shape?.radius ?? "10px" };
}

let store: Tweaks = specDefaults();

export function getTweaks(): Tweaks {
  return { colors: { ...store.colors }, radius: store.radius };
}

export function isTweaked(): boolean {
  const d = specDefaults();
  return d.radius !== store.radius || Object.keys(d.colors).some((k) => d.colors[k] !== store.colors[k]);
}

/* :root へ反映（レビューシェル自体は固定ニュートラル配色のため影響しない。
   影響するのはトークンを参照するプロトタイプ画面とスペシメン） */
function apply() {
  const root = document.documentElement;
  for (const [key, vars] of Object.entries(TOKEN_MAP)) {
    const v = store.colors[key];
    for (const cssVar of vars) {
      if (v) root.style.setProperty(cssVar, v);
      else root.style.removeProperty(cssVar);
    }
  }
  root.style.setProperty("--radius", store.radius);
}

export function setColor(key: string, value: string): Tweaks {
  store.colors[key] = value;
  apply();
  return getTweaks();
}

export function setRadius(radius: string): Tweaks {
  store.radius = radius;
  apply();
  return getTweaks();
}

export function resetTweaks(): Tweaks {
  store = specDefaults();
  const root = document.documentElement;
  for (const vars of Object.values(TOKEN_MAP)) for (const v of vars) root.style.removeProperty(v);
  root.style.removeProperty("--radius");
  return getTweaks();
}

/* 現在値を globals.css :root 用のスニペットに（調整の確定＝これを貼り戻す） */
export function cssSnippet(): string {
  const lines: string[] = [];
  for (const [key, vars] of Object.entries(TOKEN_MAP)) {
    const v = store.colors[key];
    if (v) for (const cssVar of vars) lines.push(`  ${cssVar}: ${v};`);
  }
  lines.push(`  --radius: ${store.radius};`);
  return `:root {\n${lines.join("\n")}\n}`;
}
