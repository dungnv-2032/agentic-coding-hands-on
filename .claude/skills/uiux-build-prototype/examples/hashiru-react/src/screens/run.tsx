import { Button } from "@/components/ui/button";
import { GuidePill } from "@/components/guide-pill";
import { useGoto } from "@/pt/navigation";
import type { ScreenProps } from "./index";

/* 初心者向けにペース・距離は表示しない（src-um インサイト『数値は中級者以降に効く』） */
export default function Run(_: ScreenProps) {
  const goto = useGoto();
  return (
    <div className="flex min-h-full flex-col items-center justify-center p-4 text-center">
      <svg className="size-[210px]" viewBox="0 0 120 120" aria-label="のこり 3分12秒">
        <circle cx="60" cy="60" r="52" fill="none" stroke="var(--accent)" strokeWidth="10" />
        <circle
          cx="60" cy="60" r="52" fill="none" stroke="var(--primary)" strokeWidth="10"
          strokeLinecap="round" strokeDasharray="327" strokeDashoffset="120" transform="rotate(-90 60 60)"
        />
        <text x="60" y="57" textAnchor="middle" className="tabular" fontSize="20" fontWeight="800" fill="var(--foreground)">03:12</text>
        <text x="60" y="74" textAnchor="middle" fontSize="8" fill="var(--muted-foreground)">のこり</text>
      </svg>
      <div className="mt-4">
        <GuidePill>いいペースです。歩いてもかまいませんよ</GuidePill>
      </div>
      <Button size="lg" className="mt-7 px-10" onClick={() => goto("done")}>ランを終える</Button>
    </div>
  );
}
