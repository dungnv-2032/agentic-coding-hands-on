import { Button } from "@/components/ui/button";
import { StatCard } from "@/components/stat-card";
import { useGoto } from "@/pt/navigation";
import type { ScreenProps } from "./index";

/* 褒めを最上部・最大サイズで。記録値は下部に控えめ（src-um インサイト『承認は努力へ』） */
export default function Done(_: ScreenProps) {
  const goto = useGoto();
  return (
    <div className="flex min-h-full flex-col items-center justify-center p-4 text-center">
      <div className="flex size-19 items-center justify-center rounded-full bg-primary text-4xl shadow-md">🎉</div>
      <h1 className="mt-4.5 text-[26px] font-extrabold leading-snug">
        今日も走れた。<br />それがいちばんすごい
      </h1>
      <p className="mt-2 text-sm text-muted-foreground">忙しい平日の夜に、自分との約束を守れました</p>
      <div className="mt-5 flex gap-2.5">
        <StatCard value="5分12秒" label="時間" />
        <StatCard value="0.8km" label="距離" />
        <StatCard value="7回目" label="通算" />
      </div>
      <Button size="lg" className="mt-7 px-9" onClick={() => goto("home")}>ホームへ戻る</Button>
    </div>
  );
}
