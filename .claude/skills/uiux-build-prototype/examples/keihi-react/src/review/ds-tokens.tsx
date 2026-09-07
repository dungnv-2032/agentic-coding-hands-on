import { useState } from "react";
import { contrastRatio, spec } from "@/pt/spec";
import { cn } from "@/lib/utils";
import { Chip, MicroHead, Panel } from "./review-layout";
import { type Tweaks, cssSnippet, getTweaks, isTweaked, resetTweaks, setColor, setRadius } from "./token-tweaks";

/* デザインシステム §トークン — 見るだけでなく「検討調整」できるパネル群。
   カラー・角丸をその場で編集 → プロトタイプ/スペシメンに即反映 → :root CSSをコピーして確定 */

const COLOR_LABELS: Record<string, string> = {
  primary: "プライマリ（行動・選択）", primaryText: "プライマリ上の文字",
  bg: "背景", surface: "サーフェス", text: "テキスト", textSub: "サブテキスト",
  border: "ボーダー", accent: "アクセント（ウォッシュ）",
  success: "成功", warning: "注意", danger: "エラー",
};

function ContrastBadge({ label, fg, bg }: { label: string; fg?: string; bg?: string }) {
  const r = contrastRatio(fg, bg);
  if (!r) return null;
  const pass = r >= 4.5;
  return (
    <span className="mr-3 text-[11px]">
      {label}
      <span className={cn("ml-1 rounded-full px-1.5 py-px text-[10px]", pass ? "bg-[#EDF7F0] text-[#2c6e49]" : "bg-[#FFEEEC] text-[#AD0C00]")}>
        {r.toFixed(1)}:1{pass ? " ✓" : " ⚠"}
      </span>
    </span>
  );
}

export function DirectionPanel() {
  const d = spec.design;
  if (!d.direction && !d.source && !d.notes?.length) return null;
  return (
    <Panel>
      <MicroHead>デザイン方針</MicroHead>
      {d.direction && <div className="text-[17px] font-extrabold leading-snug">{d.direction}</div>}
      {d.notes?.length ? (
        <ul className="mt-2 list-disc pl-5 text-xs leading-relaxed">
          {d.notes.map((n) => <li key={n}>{n}</li>)}
        </ul>
      ) : null}
      {d.source && <div className="mt-2.5 border-t border-[#F2F2F5] pt-2 text-[11px] text-zinc-500">出典: {d.source}</div>}
    </Panel>
  );
}

/* カラー＋シェイプの調整パネル。調整値はモジュールストア（token-tweaks）に保持され、
   レビュー内のタブ移動でも維持される（リロードで破棄） */
export function TokenAdjustPanel() {
  const [tweaks, setTweaks] = useState<Tweaks>(getTweaks);
  const [copied, setCopied] = useState(false);
  const c = tweaks.colors;
  const radiusPx = parseInt(tweaks.radius, 10) || 0;

  const copyCss = async () => {
    try {
      await navigator.clipboard.writeText(cssSnippet());
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch { /* clipboard 不可の環境では無視 */ }
  };

  return (
    <Panel>
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <MicroHead>トークン（カラー・シェイプ）— その場で調整できます</MicroHead>
        <div className="flex items-center gap-1.5 text-[11px]">
          {isTweaked() && <span className="rounded-full bg-[#FFF6E5] px-2 py-px text-[10px] text-[#8a5a00]">調整中（未確定）</span>}
          <button onClick={copyCss} className="cursor-pointer rounded border border-[#ECECEF] bg-white px-2 py-1 hover:border-[#FF2200]">
            {copied ? "コピーしました ✓" : ":root CSS をコピー"}
          </button>
          <button onClick={() => setTweaks(resetTweaks())} className="cursor-pointer rounded border border-[#ECECEF] bg-white px-2 py-1 hover:border-[#FF2200]">
            リセット
          </button>
        </div>
      </div>

      <div className="grid grid-cols-[repeat(auto-fill,minmax(170px,1fr))] gap-2.5">
        {Object.entries(c).map(([k, v]) => (
          <label key={k} className="cursor-pointer overflow-hidden rounded-md border border-[#ECECEF]">
            <span className="relative flex h-13 items-center justify-center text-xs font-bold"
              style={{ background: v, color: (contrastRatio("#ffffff", v) ?? 0) >= 3 ? "#fff" : "#1a1a1a" }}>
              {k}
              <input
                type="color"
                value={v}
                aria-label={`${COLOR_LABELS[k] ?? k} の色を調整`}
                onChange={(e) => setTweaks(setColor(k, e.target.value))}
                className="absolute inset-0 cursor-pointer opacity-0"
              />
            </span>
            <span className="block px-2.5 py-1.5 text-[11px]">
              {COLOR_LABELS[k] ?? k}
              <span className="tabular block text-[10px] text-zinc-400">{v}</span>
            </span>
          </label>
        ))}
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-4 border-t border-[#F2F2F5] pt-2.5">
        <label className="flex items-center gap-2 text-[11px]">
          角丸 <input type="range" min={0} max={24} value={radiusPx} onChange={(e) => setTweaks(setRadius(`${e.target.value}px`))} />
          <span className="tabular w-9">{tweaks.radius}</span>
        </label>
        <span className="text-[10px] text-zinc-400">調整は一時的です — 確定するときは「:root CSS をコピー」して src/styles/globals.css に貼り戻してください</span>
      </div>

      <div className="mt-3">
        <span className="text-[9.5px] font-bold uppercase tracking-[.08em] text-zinc-400">コントラスト </span>
        <ContrastBadge label="text/bg" fg={c.text} bg={c.bg} />
        <ContrastBadge label="text/surface" fg={c.text} bg={c.surface} />
        <ContrastBadge label="textSub/surface" fg={c.textSub} bg={c.surface} />
        <ContrastBadge label="primaryText/primary" fg={c.primaryText} bg={c.primary} />
      </div>
    </Panel>
  );
}

export function TypographyPanel() {
  const d = spec.design;
  return (
    <Panel>
      <MicroHead>タイポグラフィ — {d.typography?.family ?? "（未指定）"}</MicroHead>
      {Object.entries(d.typography?.scale ?? {}).map(([k, v]) => (
        <div key={k} className="flex items-baseline gap-3.5 border-b border-[#F2F2F5] py-1.5">
          <span className="w-[110px] text-[10px] text-zinc-400">{k} ・ {v}</span>
          <span style={{ fontSize: v, fontFamily: d.typography?.family }}>見出しと本文のサンプル Aa</span>
        </div>
      ))}
      <div className="mt-2 flex flex-wrap gap-1">
        <Chip>baseSize: {d.typography?.baseSize ?? "—"}</Chip>
        <Chip>density: {d.shape?.density ?? "—"}</Chip>
        <Chip>shadow: {d.shape?.shadow ?? "—"}</Chip>
      </div>
    </Panel>
  );
}
