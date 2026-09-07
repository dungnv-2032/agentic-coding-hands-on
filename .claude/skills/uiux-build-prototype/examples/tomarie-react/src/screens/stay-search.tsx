import { useState } from "react";
import { Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { AppHeader } from "@/components/app-header";
import { BottomTabBar } from "@/components/bottom-tab-bar";
import { ListingCard } from "@/components/listing-card";
import { LISTINGS } from "@/mocks/listings";
import { useGoto } from "@/pt/navigation";
import { cn } from "@/lib/utils";
import type { ScreenProps } from "./index";

const CATEGORIES = ["すべて", "海の近く", "サウナ", "古民家", "一棟貸し"];

export default function StaySearch({ state }: ScreenProps) {
  const goto = useGoto();
  const [favs, setFavs] = useState<Set<string>>(new Set(["yama"]));
  const [category, setCategory] = useState("すべて");
  const toggleFav = (id: string) =>
    setFavs((s) => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n; });

  return (
    <div className="flex min-h-full flex-col">
      <AppHeader>
        {/* 検索ピル — 実際に入力できる（契約 §8） */}
        <label className="mx-auto flex h-10 w-full max-w-[420px] items-center gap-2 rounded-full border border-border bg-card px-4 shadow-sm focus-within:ring-2 focus-within:ring-ring">
          <Search className="size-4 shrink-0 text-muted-foreground" />
          <input
            defaultValue=""
            placeholder="行き先・キーワード（例: 海の近く）"
            className="w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground"
          />
          <span className="shrink-0 text-xs text-muted-foreground">7/18–19 ・ 2人</span>
        </label>
      </AppHeader>

      {/* カテゴリ絞り込み — 選択が実際に切り替わる */}
      <div className="border-b border-border bg-card">
        <div className="mx-auto flex w-full max-w-[1120px] gap-2 overflow-x-auto px-4 py-2.5">
          {CATEGORIES.map((c) => (
            <button
              key={c}
              type="button"
              aria-pressed={category === c}
              onClick={() => setCategory(c)}
              className={cn(
                "shrink-0 cursor-pointer rounded-full border px-3.5 py-1.5 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring",
                category === c ? "border-foreground bg-foreground font-bold text-card" : "border-border bg-card text-muted-foreground",
              )}
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      <main className="mx-auto w-full max-w-[1120px] flex-1 px-4 py-5">
        {state === "loading" && (
          <div className="grid grid-cols-1 gap-6 @3xl:grid-cols-2 @5xl:grid-cols-3" aria-hidden>
            {[0, 1, 2].map((i) => (
              <div key={i}>
                <Skeleton className="aspect-[4/3] w-full rounded-lg" />
                <Skeleton className="mt-2 h-4 w-3/5" />
                <Skeleton className="mt-1.5 h-3 w-2/5 opacity-60" />
              </div>
            ))}
          </div>
        )}

        {state === "empty" && (
          <div className="py-16 text-center">
            <div className="text-lg text-muted-foreground">この条件に合う宿が見つかりませんでした</div>
            <p className="mt-1.5 text-sm text-muted-foreground">日程を変えるか、カテゴリを「すべて」に戻してみてください</p>
            <Button variant="outline" className="mt-4" onClick={() => setCategory("すべて")}>条件をリセット</Button>
          </div>
        )}

        {state === "default" && (
          <div className="grid grid-cols-1 gap-6 @3xl:grid-cols-2 @5xl:grid-cols-3">
            {LISTINGS.map((l, i) => (
              <ListingCard
                key={l.id}
                listing={l}
                fav={favs.has(l.id)}
                onToggleFav={() => toggleFav(l.id)}
                onClick={i === 0 ? () => goto("stay-detail") : undefined}
              />
            ))}
          </div>
        )}
      </main>

      {/* アプリ表示のみ: グローバルナビはボトムタブバー（web表示ではヘッダーが担う） */}
      <BottomTabBar current="search" />
    </div>
  );
}
