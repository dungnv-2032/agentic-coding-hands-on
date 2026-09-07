import { useState } from "react";
import { ArrowLeft, Star } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { AppHeader } from "@/components/app-header";
import { FavButton } from "@/components/fav-button";
import { Photo } from "@/components/photo";
import { Stepper } from "@/components/stepper";
import { PRIMARY_LISTING } from "@/mocks/listings";
import { useAppMode } from "@/pt/app-mode";
import { useGoto } from "@/pt/navigation";
import { cn } from "@/lib/utils";
import type { ScreenProps } from "./index";

const DATE_OPTIONS = [
  { id: "a", label: "7/18（土）〜19（日）", nights: 1 },
  { id: "b", label: "7/25（土）〜27（月）", nights: 2 },
];
const AMENITIES = ["一棟貸し", "Wi-Fi", "キッチン", "駐車場1台", "海まで徒歩3分"];

function yen(n: number) {
  return "¥" + n.toLocaleString("ja-JP");
}

/* 日程チップ・人数ステッパーは実際に操作でき、料金内訳が即時に再計算される */
export default function StayDetail(_: ScreenProps) {
  const goto = useGoto();
  const native = useAppMode() === "native";
  const l = PRIMARY_LISTING;
  const [fav, setFav] = useState(false);
  const [dateId, setDateId] = useState("a");
  const [guests, setGuests] = useState(2);
  const nights = DATE_OPTIONS.find((d) => d.id === dateId)!.nights;
  const base = 18000 * nights, cleaning = 3000, fee = Math.round(base * 0.1);
  const total = base + cleaning + fee;

  const Breakdown = (
    <dl className="space-y-1.5 text-sm">
      <div className="flex justify-between"><dt className="text-muted-foreground">{yen(18000)} × {nights}泊</dt><dd className="tabular">{yen(base)}</dd></div>
      <div className="flex justify-between"><dt className="text-muted-foreground">清掃料</dt><dd className="tabular">{yen(cleaning)}</dd></div>
      <div className="flex justify-between"><dt className="text-muted-foreground">サービス料</dt><dd className="tabular">{yen(fee)}</dd></div>
      <div className="flex justify-between border-t border-border pt-2 font-bold"><dt>合計</dt><dd className="tabular">{yen(total)}</dd></div>
    </dl>
  );

  return (
    <div className="flex min-h-full flex-col">
      <AppHeader />
      <main className={cn("mx-auto w-full max-w-[1120px] flex-1 px-4", native ? "pt-0" : "py-4")}>
        {/* 戻る導線: Web=テキストリンク / アプリ=写真上のフローティング円ボタン（ui-craft §0） */}
        {!native && (
          <button className="mb-3 cursor-pointer text-sm text-primary" onClick={() => goto("stay-search")}>‹ 検索結果へ戻る</button>
        )}

        {/* ギャラリー: モバイル1枚 → @3xl で1大+2小 */}
        <div className={cn("relative grid grid-cols-1 gap-2 @3xl:grid-cols-[2fr_1fr]", native && "-mx-4")}>
          <Photo scene="sea" className={cn("aspect-[16/10]", native ? "rounded-none @3xl:rounded-xl" : "rounded-xl")} />
          <div className="hidden grid-rows-2 gap-2 @3xl:grid">
            <Photo scene="bed" className="rounded-xl" />
            <Photo scene="kitchen" className="rounded-xl" />
          </div>
          {native && (
            <button
              type="button"
              aria-label="検索結果へ戻る"
              onClick={() => goto("stay-search")}
              className="absolute left-3 top-3 flex size-9 cursor-pointer items-center justify-center rounded-full bg-card/90 shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-ring active:scale-90"
            >
              <ArrowLeft className="size-4.5" />
            </button>
          )}
          <div className="absolute right-3 top-3"><FavButton on={fav} onToggle={() => setFav((v) => !v)} /></div>
        </div>

        <div className="mt-4 gap-8 @5xl:grid @5xl:grid-cols-[1fr_380px] @5xl:items-start">
          <div>
            <h1 className="text-xl font-extrabold">{l.title}</h1>
            <div className="mt-1 flex items-center gap-2 text-sm text-muted-foreground">
              <span className="flex items-center gap-1 text-foreground"><Star className="size-3.5 fill-foreground" />{l.rating}（86件）</span>
              ・ <span>{l.area}</span>
            </div>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {AMENITIES.map((a) => (
                <span key={a} className="rounded-full border border-border bg-card px-3 py-1 text-xs">{a}</span>
              ))}
            </div>
            <p className="mt-4 max-w-[620px] text-sm leading-relaxed text-muted-foreground">
              築90年の古民家を、地元の大工さんと一緒に直しました。縁側から海に沈む夕日が見えます。
              ホストの佐野が徒歩5分の距離に住んでいるので、困りごとにはすぐ駆けつけます。
            </p>

            {/* 予約条件（操作は1箇所に集約 — 合計はパネル/バーに即時反映） */}
            <section className="mt-5 max-w-[620px]">
              <h2 className="mb-2 text-sm font-bold">日程をえらぶ</h2>
              <div className="flex flex-wrap gap-2">
                {DATE_OPTIONS.map((d) => (
                  <button
                    key={d.id}
                    type="button"
                    aria-pressed={dateId === d.id}
                    onClick={() => setDateId(d.id)}
                    className={cn(
                      "cursor-pointer rounded-full border-[1.5px] px-4 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring",
                      dateId === d.id ? "border-primary bg-accent font-bold" : "border-border bg-card",
                    )}
                  >
                    {d.label}（{d.nights}泊）
                  </button>
                ))}
              </div>
              <h2 className="mb-2 mt-4 text-sm font-bold">人数</h2>
              <Stepper value={guests} onChange={setGuests} />
            </section>
          </div>

          {/* デスクトップ: 右側スティッキー予約パネル（web-app idiom） */}
          <Card className="sticky top-20 hidden p-5 @5xl:block">
            <div className="mb-3 text-lg font-bold"><span className="tabular">{yen(18000)}</span><span className="text-sm font-normal text-muted-foreground"> /泊</span></div>
            <div className="mb-3 rounded-lg border border-border p-3 text-sm">
              <div className="flex justify-between"><span className="text-muted-foreground">日程</span><span>{DATE_OPTIONS.find((d) => d.id === dateId)!.label}</span></div>
              <div className="mt-1.5 flex justify-between"><span className="text-muted-foreground">人数</span><span className="tabular">{guests}人</span></div>
            </div>
            {Breakdown}
            <Button size="lg" className="mt-4 w-full" onClick={() => goto("booking-confirm")}>予約リクエストへ進む</Button>
            <p className="mt-2 text-center text-xs text-muted-foreground">まだ請求は発生しません</p>
          </Card>
        </div>

        {/* モバイル: 内訳はコンテンツ内に */}
        <section className="mt-5 max-w-[620px] @5xl:hidden">
          <h2 className="mb-2 text-sm font-bold">料金の内訳</h2>
          <Card className="p-4">{Breakdown}</Card>
        </section>
      </main>

      {/* モバイル: 下部固定の予約バー */}
      <div className="sticky bottom-0 border-t border-border bg-card @5xl:hidden">
        <div className="mx-auto flex w-full max-w-[1120px] items-center justify-between gap-3 p-3 px-4">
          <div>
            <div className="tabular font-bold">{yen(total)} <span className="text-xs font-normal text-muted-foreground">合計（{nights}泊・{guests}人）</span></div>
            <div className="text-xs text-muted-foreground">まだ請求は発生しません</div>
          </div>
          <Button onClick={() => goto("booking-confirm")}>予約リクエストへ</Button>
        </div>
      </div>
    </div>
  );
}
