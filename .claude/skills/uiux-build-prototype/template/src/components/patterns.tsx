import type { ReactNode } from "react";

/* プロジェクト固有パターンのカタログ（デザインシステムページに Atomic Design 階層で標本表示される）。
   繰り返すUIパターンはここに一度だけ定義し、usage には「いつ使ってよいか」のルールを書く。
   tier: molecule=Atomsを組み合わせた最小の意味単位（既定）/ organism=自立したUI領域（ヘッダー・ナビ・複合カード）。
   ※ Atoms は components/ui のキット（デザインシステムページが網羅表示）、Pages は画面そのもの。
   例:
   import { StatusRow } from "./status-row";
   { id: "status-row", name: "ステータス行", usage: "一覧の1明細。左=名称/右=金額+状態", tier: "molecule",
     usedIn: ["expense-list"], element: <StatusRow label="タクシー代" amount="¥3,200" status="承認待ち" /> }
*/
export interface Pattern {
  id: string;
  name: string;
  usage: string;
  tier?: "molecule" | "organism"; // 省略時 molecule
  usedIn?: string[];
  element: ReactNode;
}

export const patterns: Pattern[] = [];
