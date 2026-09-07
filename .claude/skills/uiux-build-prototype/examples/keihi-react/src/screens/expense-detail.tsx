import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { AppHeader } from "@/components/app-header";
import { useGoto } from "@/pt/navigation";
import type { ScreenProps } from "./index";

export default function ExpenseDetail(_: ScreenProps) {
  const goto = useGoto();
  return (
    <div className="flex min-h-full flex-col">
      <AppHeader />
      <main className="mx-auto w-full max-w-[640px] flex-1 px-4 py-5">
        {/* Webの道しるべ: パンくず的な戻りリンク（ui-craft §0 web-app） */}
        <button className="mb-3 cursor-pointer text-sm text-primary" onClick={() => goto("expense-list")}>
          ‹ 経費一覧へ戻る
        </button>
        <Card>
          <CardHeader className="gap-2">
            <Badge variant="warning" dot className="self-start">承認待ち（承認者: 佐藤マネージャー）</Badge>
            <div className="tabular text-2xl font-bold">¥3,200</div>
            <div className="font-bold">タクシー代（顧客訪問）</div>
          </CardHeader>
          <CardContent>
            <table className="w-full border-t border-border text-sm">
              <tbody>
                {[
                  ["日付", "2026/07/01（火）"],
                  ["申請日", "2026/07/01（火）18:24"],
                  ["領収書", "receipt_0701.jpg（添付済み）"],
                ].map(([k, v]) => (
                  <tr key={k} className="border-b border-border/60">
                    <td className="w-20 py-2 text-muted-foreground">{k}</td>
                    <td className={k === "領収書" ? "py-2 text-primary" : "py-2"}>{v}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="mt-3 text-xs text-muted-foreground">承認されると翌月給与と合わせて振り込まれます</p>
          </CardContent>
        </Card>
        <div className="mt-4 flex @3xl:justify-end">
          <Button variant="destructive" className="w-full @3xl:w-auto" onClick={() => goto("expense-list")}>
            申請を取り下げる
          </Button>
        </div>
      </main>
    </div>
  );
}
