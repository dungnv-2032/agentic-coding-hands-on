import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export type ExpenseStatus = "承認待ち" | "承認済み" | "差し戻し";

const STATUS_VARIANT: Record<ExpenseStatus, "warning" | "success" | "destructive"> = {
  承認待ち: "warning",
  承認済み: "success",
  差し戻し: "destructive",
};

/* 経費カード — 一覧の1明細。左=用途と日付 / 右=金額とステータス（色＋文字併記）。
   onClick を渡すと詳細へのクリック可能カードになる（hover/カーソルはここで付与） */
export function ExpenseCard({
  name,
  amount,
  date,
  status,
  onClick,
}: {
  name: string;
  amount: string;
  date: string;
  status: ExpenseStatus;
  onClick?: () => void;
}) {
  return (
    <Card
      onClick={onClick}
      className={cn("p-4", onClick && "cursor-pointer transition-[filter] hover:brightness-[.98] active:scale-[.995]")}
    >
      <div className="flex items-baseline justify-between gap-2">
        <span className="font-bold">{name}</span>
        <strong className="tabular text-lg">{amount}</strong>
      </div>
      <div className="mt-1 flex items-center justify-between text-sm text-muted-foreground">
        <span>{date}</span>
        <Badge variant={STATUS_VARIANT[status]} dot>{status}</Badge>
      </div>
    </Card>
  );
}
