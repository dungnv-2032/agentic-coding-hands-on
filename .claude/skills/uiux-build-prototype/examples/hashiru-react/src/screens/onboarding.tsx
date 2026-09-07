import { useState } from "react";
import { Button } from "@/components/ui/button";
import { OptionChip } from "@/components/option-chip";
import { useGoto } from "@/pt/navigation";
import type { ScreenProps } from "./index";

const QUESTIONS: { q: string; options: string[] }[] = [
  { q: "1. なんのために走る？", options: ["健康のため", "気分転換", "体力づくり"] },
  { q: "2. 走りやすい時間は？", options: ["朝・出勤前", "夜・帰宅後", "休日"] },
  { q: "3. 1回どのくらいなら続けられそう？", options: ["5分でOK", "10分", "15分"] },
];

/* 選択はレビュアーが必ず触るマイクロインタラクション — ローカル状態で実際に動かす（契約 §8） */
export default function Onboarding(_: ScreenProps) {
  const goto = useGoto();
  const [answers, setAnswers] = useState<number[]>([0, 1, 0]);
  const answered = answers.every((a) => a >= 0);

  return (
    <div className="flex min-h-full flex-col">
      <main className="mx-auto w-full max-w-[520px] flex-1 px-4 py-6">
        <h1 className="text-[26px] font-extrabold leading-snug">3つだけ、教えてください</h1>
        <p className="mt-1.5 text-sm text-muted-foreground">あとで全部変えられます。気楽にどうぞ</p>
        {QUESTIONS.map(({ q, options }, qi) => (
          <section key={q} className="mt-6">
            <h2 className="mb-2.5 font-bold">{q}</h2>
            <div className="flex flex-wrap gap-2">
              {options.map((o, oi) => (
                <OptionChip
                  key={o}
                  label={o}
                  selected={answers[qi] === oi}
                  onClick={() => setAnswers((a) => a.map((v, i) => (i === qi ? oi : v)))}
                />
              ))}
            </div>
          </section>
        ))}
      </main>
      {/* 下部固定のアクションバー — sticky bottom-0 はピュア/デバイス枠どちらでも下端に張り付く */}
      <div className="sticky bottom-0 bg-gradient-to-t from-background via-background/95 to-transparent pt-6">
        <div className="mx-auto w-full max-w-[520px] p-4 pt-0">
          <Button size="lg" className="w-full" disabled={!answered} onClick={() => goto("home")}>
            はじめる
          </Button>
        </div>
      </div>
    </div>
  );
}
