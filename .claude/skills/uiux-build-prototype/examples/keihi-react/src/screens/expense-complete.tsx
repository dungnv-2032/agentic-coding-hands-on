import { Button } from "@/components/ui/button";
import { AppHeader } from "@/components/app-header";
import { useGoto } from "@/pt/navigation";
import type { ScreenProps } from "./index";

export default function ExpenseComplete(_: ScreenProps) {
  const goto = useGoto();
  return (
    <div className="flex min-h-full flex-col">
      <AppHeader />
      <main className="flex flex-1 flex-col items-center justify-center px-4 py-10 text-center">
        <div className="flex size-16 items-center justify-center rounded-full bg-success text-3xl text-white">✓</div>
        <h1 className="mt-4 text-2xl font-bold">申請を送信しました</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          タクシー代（顧客訪問） <span className="tabular font-bold text-foreground">¥3,200</span>
          <br />
          承認者: 佐藤マネージャーに通知済み
        </p>
        <Button className="mt-6 px-8" onClick={() => goto("expense-list")}>一覧に戻る</Button>
      </main>
    </div>
  );
}
