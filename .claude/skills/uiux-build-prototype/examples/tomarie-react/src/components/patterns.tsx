import { useState, type ReactNode } from "react";
import { AppHeader } from "./app-header";
import { BottomTabBar } from "./bottom-tab-bar";
import { FavButton } from "./fav-button";
import { ListingCard } from "./listing-card";
import { Photo } from "./photo";
import { Stepper } from "./stepper";
import { AppModeProvider } from "@/pt/app-mode";
import { LISTINGS } from "@/mocks/listings";

/* プロジェクト固有パターンのカタログ（デザインシステムページに標本表示される） */
export interface Pattern {
  id: string;
  name: string;
  usage: string;
  tier?: "molecule" | "organism"; // Atomic Design 階層。省略時 molecule
  usedIn?: string[];
  element: ReactNode;
}

function StepperSpecimen() {
  const [v, setV] = useState(2);
  return <Stepper value={v} onChange={setV} />;
}

export const patterns: Pattern[] = [
  {
    id: "app-header",
    name: "グローバルヘッダー",
    usage: "web-app の定石として全画面で一貫。中央スロットに検索ピル等の画面固有要素を差し込む",
    usedIn: ["stay-search", "stay-detail", "booking-confirm", "booking-done"],
    element: (
      <div className="pointer-events-none w-full max-w-[320px] overflow-hidden rounded-md border border-border">
        <AppHeader />
      </div>
    ),
  },
  {
    id: "listing-card",
    name: "物件カード",
    usage: "写真が主役・価格は「¥/泊」併記。クリック可能なカードだけ hover を付与",
    usedIn: ["stay-search"],
    element: (
      <div className="w-full max-w-[240px]">
        <ListingCard listing={LISTINGS[0]} fav={false} onToggleFav={() => {}} />
      </div>
    ),
  },
  {
    id: "fav-button",
    name: "お気に入りボタン",
    usage: "写真右上に重ねる。トグルは即時フィードバック（aria-pressed・押下スケール）",
    usedIn: ["stay-search", "stay-detail"],
    element: <FavButton on onToggle={() => {}} />,
  },
  {
    id: "stepper",
    name: "人数ステッパー",
    usage: "44pxタップ目標・上下限でdisabled。値の変更は料金内訳に即時反映させる",
    usedIn: ["stay-detail"],
    element: <StepperSpecimen />,
  },
  {
    id: "scene-photo",
    name: "シーン写真（SVGイラスト）",
    usage: "外部URLを使わずオフライン自己完結で体験を伝える。配色は情景用の固有パレット（UIトークン適用外）",
    usedIn: ["stay-search", "stay-detail", "booking-confirm", "booking-done"],
    element: (
      <div className="flex w-full max-w-[300px] gap-2">
        <Photo scene="sea" className="aspect-[4/3] rounded-lg" />
        <Photo scene="cabin" className="aspect-[4/3] rounded-lg" />
      </div>
    ),
  },
  {
    id: "bottom-tab-bar",
    name: "ボトムタブバー",
    usage: "アプリ表示のグローバルナビ（web表示では描画されない）。現在タブをprimaryで明示",
    usedIn: ["stay-search"],
    element: (
      <AppModeProvider value="native">
        <div className="pointer-events-none w-full max-w-[320px] overflow-hidden rounded-md border border-border">
          <BottomTabBar current="search" />
        </div>
      </AppModeProvider>
    ),
  },
];
