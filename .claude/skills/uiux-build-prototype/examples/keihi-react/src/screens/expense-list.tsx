import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { AppHeader } from "@/components/app-header";
import { ExpenseCard } from "@/components/expense-card";
import { useGoto } from "@/pt/navigation";
import type { ScreenProps } from "./index";

const EXPENSES = [
  { name: "タクシー代（顧客訪問）", amount: "¥3,200", date: "7/1（火）", status: "承認待ち" as const },
  { name: "会食費（○○商事様）", amount: "¥12,800", date: "6/27（金）", status: "承認済み" as const },
  { name: "駐車場代", amount: "¥5,400", date: "6/25（水）", status: "承認済み" as const },
];

export default function ExpenseList({ state }: ScreenProps) {
  const goto = useGoto();
  return (
    <div className="flex min-h-full flex-col">
      <AppHeader showCta />
      <main className="mx-auto w-full max-w-[1040px] flex-1 px-4 py-5">
        <div className="mb-4 flex items-baseline justify-between">
          <h1 className="text-lg font-bold">経費一覧</h1>
          <span className="text-sm text-muted-foreground">今月の立替合計 <b className="tabular text-foreground">¥21,400</b></span>
        </div>

        {state === "loading" && (
          <div className="grid grid-cols-1 gap-2.5 @3xl:grid-cols-2" aria-hidden>
            {[62, 48, 55].map((w, i) => (
              <div key={i} className="rounded-lg border border-border bg-card p-4">
                <Skeleton className="h-4" style={{ width: `${w}%` }} />
                <Skeleton className="mt-2.5 h-3 w-2/5 opacity-60" />
              </div>
            ))}
          </div>
        )}

        {state === "error" && (
          <div className="py-12 text-center">
            <div className="font-bold text-destructive">エラー：読み込みに失敗しました</div>
            <p className="mt-1.5 text-sm text-muted-foreground">通信環境を確認して再試行してください</p>
            <Button variant="outline" className="mt-4">再試行</Button>
          </div>
        )}

        {state === "empty" && (
          <div className="py-12 text-center">
            <div className="text-lg text-muted-foreground">まだ申請がありません</div>
            <p className="mt-1.5 text-sm text-muted-foreground">立替が発生したらその場で申請しましょう</p>
            <Button className="mt-4" onClick={() => goto("expense-form")}>最初の申請を作成</Button>
          </div>
        )}

        {state === "default" && (
          <div className="grid grid-cols-1 gap-2.5 @3xl:grid-cols-2">
            {EXPENSES.map((e, i) => (
              <ExpenseCard key={e.name} {...e} onClick={i === 0 ? () => goto("expense-detail") : undefined} />
            ))}
          </div>
        )}
      </main>

      {/* モバイルは下部固定CTA。768px以上ではヘッダーCTAに集約（ui-craft §0 web-app） */}
      {state !== "loading" && state !== "error" && (
        <div className="sticky bottom-0 bg-gradient-to-t from-background via-background/95 to-transparent pt-5 @3xl:hidden">
          <div className="mx-auto w-full max-w-[1040px] p-4 pt-0">
            <Button size="lg" className="w-full" onClick={() => goto("expense-form")}>＋ 経費を申請する</Button>
          </div>
        </div>
      )}
    </div>
  );
}
