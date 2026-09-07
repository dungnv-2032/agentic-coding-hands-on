import type { ReactNode } from "react";
import { useAppMode } from "@/pt/app-mode";
import { useGoto } from "@/pt/navigation";

/* グローバルヘッダー — web 表示の定石（ui-craft §0）。全画面で一貫。
   モバイルアプリ表示ではヘッダーは置かない：children（検索ピル等）があればそれだけを
   スリムに表示し、なければ何も描画しない（ナビはボトムタブバーが担う） */
export function AppHeader({ children }: { children?: ReactNode }) {
  const goto = useGoto();
  const mode = useAppMode();

  if (mode === "native") {
    return children ? (
      <div className="sticky top-0 z-10 bg-background px-4 pb-2 pt-2">{children}</div>
    ) : null;
  }

  return (
    <header className="sticky top-0 z-10 border-b border-border bg-card">
      <div className="mx-auto flex h-14 w-full max-w-[1120px] items-center gap-3 px-4">
        <button className="cursor-pointer text-lg font-extrabold text-primary" onClick={() => goto("stay-search")}>
          Tomarie
        </button>
        <div className="min-w-0 flex-1">{children}</div>
        <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-accent text-xs font-bold">ゲ</span>
      </div>
    </header>
  );
}
