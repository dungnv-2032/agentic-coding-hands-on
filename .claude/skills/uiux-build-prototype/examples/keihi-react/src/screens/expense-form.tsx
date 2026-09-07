import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AppHeader } from "@/components/app-header";
import { useGoto } from "@/pt/navigation";
import type { ScreenProps } from "./index";

/* 入力体験が要点の画面なので入力欄は実際に打てる（契約 §8: マイクロインタラクション） */
export default function ExpenseForm({ state }: ScreenProps) {
  const goto = useGoto();
  return (
    <div className="flex min-h-full flex-col">
      <AppHeader />
      <main className="mx-auto w-full max-w-[560px] flex-1 px-4 py-5">
        <h1 className="mb-4 text-lg font-bold">経費申請</h1>

        {state === "error" && (
          <div className="mb-4 rounded-lg border border-destructive bg-card p-3 text-sm">
            <span className="font-bold text-destructive">エラー：金額を入力してください</span>
            <br />
            <span className="text-muted-foreground">半角数字で入力します（例: 3200）</span>
          </div>
        )}

        <Label>用途 <span className="text-destructive">必須</span></Label>
        <Input defaultValue="タクシー代（顧客訪問）" className="mb-4" />
        <Label>金額 <span className="text-destructive">必須</span></Label>
        <Input defaultValue="¥3,200" className="tabular mb-4 text-lg font-bold" />
        <Label>日付</Label>
        <Input defaultValue="2026/07/01（火）" className="mb-4" />
        <Label>領収書</Label>
        <div className="rounded-lg border-[1.5px] border-dashed border-border bg-card p-6 text-center text-sm text-muted-foreground">
          📷 クリックして領収書をアップロード
          <br />
          <span className="text-xs">あとから追加もできます</span>
        </div>
      </main>
      <div className="mx-auto flex w-full max-w-[560px] gap-2.5 p-4 @3xl:justify-end">
        <Button variant="secondary" className="flex-1 @3xl:flex-none @3xl:px-7" onClick={() => goto("expense-list")}>
          キャンセル
        </Button>
        <Button className="flex-[2] @3xl:flex-none @3xl:px-9" onClick={() => goto("expense-complete")}>
          申請を送信する
        </Button>
      </div>
    </div>
  );
}
