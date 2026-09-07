import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { EncourageBanner } from "@/components/encourage-banner";
import { StatCard } from "@/components/stat-card";
import { useGoto } from "@/pt/navigation";
import type { ScreenProps } from "./index";

/* state "comeback" = 3日以上サボった後のやさしい復帰画面（ジャーニー『3日目の壁→再開』） */
export default function Home({ state }: ScreenProps) {
  const goto = useGoto();
  return (
    <div className="mx-auto w-full max-w-[560px] px-4 py-6">
      <h1 className="text-lg font-extrabold">こんばんは、さやかさん</h1>
      <p className="text-[11px] text-muted-foreground">7/3（金）夜・帰宅後の時間ですね</p>

      {state === "comeback" ? (
        <div className="mt-4">
          <EncourageBanner title={<>3日ぶり。<br />それでいいんです</>}>
            続けている人もみんな、途切れながら続けています。<br />
            今日はいちばん軽いメニューにしました
          </EncourageBanner>
          <Button size="lg" className="mt-4 w-full" onClick={() => goto("run")}>
            5分だけ、ゆるく再開する
          </Button>
        </div>
      ) : (
        <>
          <Card className="mt-4 p-6 text-center">
            <div className="text-[26px] font-extrabold leading-snug">
              今日は5分だけ、<br />走ってみませんか
            </div>
            <p className="mt-1.5 text-sm text-muted-foreground">ゆっくりでOK。音声ガイドがついています</p>
            <Button size="lg" className="mt-4 w-full" onClick={() => goto("run")}>
              5分ランを始める
            </Button>
          </Card>
          <div className="mt-3.5 grid grid-cols-2 gap-2.5 @3xl:grid-cols-3">
            <StatCard value="2回" label="今週走れた日" />
            <StatCard value="6回" label="はじめてから" />
          </div>
        </>
      )}
    </div>
  );
}
