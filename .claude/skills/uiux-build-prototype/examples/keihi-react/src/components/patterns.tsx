import type { ReactNode } from "react";
import { Badge } from "@/components/ui/badge";
import { AppHeader } from "./app-header";
import { ExpenseCard } from "./expense-card";

/* プロジェクト固有パターンのカタログ（デザインシステムページに標本表示される） */
export interface Pattern {
  id: string;
  name: string;
  usage: string;
  tier?: "molecule" | "organism"; // Atomic Design 階層。省略時 molecule
  usedIn?: string[];
  element: ReactNode;
}

export const patterns: Pattern[] = [
  {
    id: "app-header",
    name: "グローバルヘッダー",
    usage: "Webアプリの定石として全画面に必須・一貫。768px以上では主CTAもここに置く（モバイルは下部固定CTA）",
    usedIn: ["expense-list", "expense-form", "expense-detail", "expense-complete"],
    element: (
      <div className="w-full max-w-[320px] overflow-hidden rounded-md border border-border">
        <AppHeader showCta />
      </div>
    ),
  },
  {
    id: "expense-card",
    name: "経費カード",
    usage: "一覧の1明細。左=用途と日付 / 右=金額とステータス。クリック可能なものだけ hover を付与",
    usedIn: ["expense-list"],
    element: (
      <div className="w-full max-w-[300px]">
        <ExpenseCard name="タクシー代（顧客訪問）" amount="¥3,200" date="7/1（火）" status="承認待ち" onClick={() => {}} />
      </div>
    ),
  },
  {
    id: "status-badge",
    name: "ステータスバッジ",
    usage: "warning=承認待ち / success=承認済み / destructive=差し戻し。色＋文字を必ず併記",
    usedIn: ["expense-list", "expense-detail"],
    element: (
      <div className="flex gap-3">
        <Badge variant="warning" dot>承認待ち</Badge>
        <Badge variant="success" dot>承認済み</Badge>
        <Badge variant="destructive" dot>差し戻し</Badge>
      </div>
    ),
  },
];
