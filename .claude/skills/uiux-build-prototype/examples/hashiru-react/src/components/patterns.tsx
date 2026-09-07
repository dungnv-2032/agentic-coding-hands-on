import type { ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { EncourageBanner } from "./encourage-banner";
import { GuidePill } from "./guide-pill";
import { OptionChip } from "./option-chip";
import { StatCard } from "./stat-card";

/* プロジェクト固有パターンのカタログ（デザインシステムページに標本表示される） */
export interface Pattern {
  id: string;
  name: string;
  usage: string;
  tier?: "molecule" | "organism"; // Atomic Design 階層。省略時 molecule
  usedIn?: string[];
  element: ReactNode;
}

export const patterns: Pattern[] = [
  {
    id: "cta-big",
    name: "ビッグCTA",
    usage: "1画面1つの主操作。大きく・やさしい文言で押すハードルを下げる（インサイト『低いハードル』）",
    usedIn: ["onboarding", "home", "run", "done"],
    element: <Button size="lg">5分ランを始める</Button>,
  },
  {
    id: "option-chip",
    name: "選択チップ",
    usage: "設定は入力させず選ばせる（インサイト『機能の多さは拒否シグナル』）。選択中はaccent塗り",
    usedIn: ["onboarding"],
    element: (
      <div className="flex gap-2">
        <OptionChip label="5分でOK" selected />
        <OptionChip label="10分" />
      </div>
    ),
  },
  {
    id: "stat-card",
    name: "実績カード",
    usage: "回数など『やった事実』のみ表示。ペース等の性能数値は初心者に出さない",
    usedIn: ["home", "done"],
    element: <StatCard value="2回" label="今週走れた日" />,
  },
  {
    id: "encourage-banner",
    name: "励ましバナー",
    usage: "サボり復帰・承認の場面で使用。accent背景＋責めない文言（『それでいいんです』）",
    usedIn: ["home"],
    element: (
      <div className="w-full max-w-[300px]">
        <EncourageBanner title="3日ぶり。それでいいんです">みんな途切れながら続けています</EncourageBanner>
      </div>
    ),
  },
  {
    id: "guide-pill",
    name: "音声ガイドピル",
    usage: "ラン中の声かけ表示。丸ピル・穏やかなmutedで（急かさない）",
    usedIn: ["run"],
    element: <GuidePill>いいペースです。歩いてもかまいませんよ</GuidePill>,
  },
];
