import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

/* 写真 — オフライン自己完結のまま「サービス体験」が伝わるよう、手描きSVGの
   シーンイラストを写真代わりに使う（外部画像URLは使わない）。
   ※シーンの配色は情景表現のための固有パレット（UIトークンの適用外＝imagery、ui-craft §9） */
export type SceneId = "sea" | "cabin" | "machiya" | "port" | "bed" | "kitchen";

const SCENES: Record<SceneId, ReactNode> = {
  /* 夕暮れの海と古民家 */
  sea: (
    <>
      <defs>
        <linearGradient id="sc-sky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#FFE3B3" /><stop offset=".6" stopColor="#FFB07C" /><stop offset="1" stopColor="#F98D6B" />
        </linearGradient>
        <linearGradient id="sc-sea" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#E98A66" /><stop offset="1" stopColor="#3D6E8E" />
        </linearGradient>
      </defs>
      <rect width="400" height="190" fill="url(#sc-sky)" />
      <circle cx="290" cy="150" r="34" fill="#FFF3D6" opacity=".95" />
      <rect y="185" width="400" height="115" fill="url(#sc-sea)" />
      <rect x="60" y="270" width="300" height="4" fill="#FFD9A8" opacity=".35" rx="2" />
      <g>
        <path d="M60 190 L130 150 L200 190 Z" fill="#4A3B36" />
        <rect x="78" y="190" width="104" height="60" fill="#5C4A42" />
        <rect x="112" y="212" width="20" height="24" fill="#FFD9A0" rx="2" />
        <rect x="146" y="212" width="20" height="38" fill="#3A2E2A" rx="2" />
      </g>
    </>
  ),
  /* 森のサウナキャビン */
  cabin: (
    <>
      <rect width="400" height="300" fill="#E4EEDF" />
      <circle cx="320" cy="70" r="26" fill="#FFF7DA" />
      {[[30, 120], [90, 90], [330, 110], [370, 140]].map(([x, y], i) => (
        <path key={i} d={`M${x} 250 L${x + 28} ${y} L${x + 56} 250 Z`} fill={i % 2 ? "#4C7A56" : "#3B6647"} />
      ))}
      <rect y="245" width="400" height="55" fill="#CDE0C4" />
      <g>
        <rect x="150" y="170" width="120" height="80" fill="#8A6A4F" rx="4" />
        <path d="M140 176 L210 128 L280 176 Z" fill="#5C4534" />
        <rect x="196" y="200" width="28" height="50" fill="#4A382C" rx="2" />
        <rect x="240" y="196" width="20" height="20" fill="#FFE9B0" rx="2" />
        <path d="M256 128 q6 -18 -2 -30" stroke="#B9C7BE" strokeWidth="7" fill="none" strokeLinecap="round" />
      </g>
    </>
  ),
  /* 夕暮れの商店街と提灯 */
  machiya: (
    <>
      <defs>
        <linearGradient id="mc-sky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#5B4B7A" /><stop offset="1" stopColor="#9A6B8A" />
        </linearGradient>
      </defs>
      <rect width="400" height="300" fill="url(#mc-sky)" />
      <rect y="150" width="180" height="150" fill="#3A3244" />
      <rect x="220" y="130" width="180" height="170" fill="#332C3E" />
      <rect x="30" y="180" width="34" height="40" fill="#FFDF9E" rx="3" />
      <rect x="96" y="180" width="34" height="40" fill="#FFCF8A" rx="3" />
      <rect x="260" y="170" width="30" height="36" fill="#FFDF9E" rx="3" />
      <circle cx="200" cy="150" r="40" fill="#FFB35C" opacity=".25" />
      <ellipse cx="200" cy="150" rx="17" ry="22" fill="#F97A4A" />
      <rect x="196" y="124" width="8" height="8" fill="#4A382C" />
      <rect y="270" width="400" height="30" fill="#2A2433" />
    </>
  ),
  /* 島の港 */
  port: (
    <>
      <rect width="400" height="170" fill="#CBE7F2" />
      <circle cx="90" cy="60" r="22" fill="#FFF7DA" />
      <path d="M250 170 L310 120 L400 170 Z" fill="#8FB6A2" opacity=".8" />
      <rect y="170" width="400" height="130" fill="#4E8FB0" />
      <g>
        <path d="M150 208 q40 18 100 0 l-10 26 q-40 12 -80 0 Z" fill="#F4F1E8" />
        <path d="M198 130 L198 202 M198 138 q44 14 44 56 l-44 8 Z" fill="#E8845C" stroke="#C96A47" strokeWidth="3" />
      </g>
      <rect x="40" y="252" width="330" height="5" fill="#FFFFFF" opacity=".25" rx="2" />
    </>
  ),
  /* 寝室 */
  bed: (
    <>
      <rect width="400" height="300" fill="#F3E9DC" />
      <rect x="250" y="40" width="100" height="90" fill="#FFEFC4" rx="6" />
      <path d="M250 85 h100 M300 40 v90" stroke="#D9C6AC" strokeWidth="5" />
      <rect y="240" width="400" height="60" fill="#D9C0A5" />
      <g>
        <rect x="50" y="150" width="200" height="30" fill="#FBF7F0" rx="8" />
        <rect x="50" y="176" width="200" height="66" fill="#E9909E" rx="8" />
        <rect x="62" y="132" width="60" height="26" fill="#FFFFFF" rx="10" />
        <rect x="40" y="120" width="12" height="122" fill="#8A6A4F" rx="4" />
      </g>
    </>
  ),
  /* 朝のキッチン */
  kitchen: (
    <>
      <rect width="400" height="300" fill="#FBF2E2" />
      <rect x="40" y="40" width="90" height="80" fill="#FFF7D6" rx="6" />
      <path d="M40 80 h90" stroke="#E3D2B8" strokeWidth="5" />
      <rect y="200" width="400" height="24" fill="#C9A87F" />
      <rect y="224" width="400" height="76" fill="#8A6A4F" />
      <rect x="250" y="140" width="8" height="60" fill="#5C5048" />
      <circle cx="284" cy="196" r="32" fill="#3F3A36" />
      <circle cx="284" cy="196" r="24" fill="#FFE9B0" />
      <rect x="70" y="170" width="46" height="30" fill="#7FA3B5" rx="4" />
      <path d="M180 150 q4 -14 -2 -24 M196 150 q4 -14 -2 -24" stroke="#CDBBA4" strokeWidth="5" fill="none" strokeLinecap="round" />
    </>
  ),
};

export function Photo({ scene, className }: { scene: SceneId; className?: string }) {
  return (
    <svg
      viewBox="0 0 400 300"
      preserveAspectRatio="xMidYMid slice"
      className={cn("block h-full w-full", className)}
      role="img"
      aria-label="宿の写真"
    >
      {SCENES[scene]}
    </svg>
  );
}
