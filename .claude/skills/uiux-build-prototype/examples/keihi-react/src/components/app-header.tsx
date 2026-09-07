import { Button } from "@/components/ui/button";
import { useGoto } from "@/pt/navigation";

/* グローバルヘッダー — Webアプリの定石（ui-craft §0: web-app はヘッダー必須・全画面で一貫）。
   768px（@3xl）以上では主CTAをヘッダーに置く（モバイルは各画面の下部固定CTA） */
export function AppHeader({ showCta = false }: { showCta?: boolean }) {
  const goto = useGoto();
  return (
    <header className="sticky top-0 z-10 border-b border-border bg-card">
      <div className="mx-auto flex h-14 w-full max-w-[1040px] items-center gap-4 px-4">
        <button className="cursor-pointer text-lg font-extrabold text-primary" onClick={() => goto("expense-list")}>
          Keihi
        </button>
        <nav className="hidden gap-1 text-sm text-muted-foreground @3xl:flex">
          <button className="cursor-pointer rounded-md bg-muted px-3 py-1.5 font-bold text-foreground" onClick={() => goto("expense-list")}>
            経費一覧
          </button>
        </nav>
        <div className="ml-auto flex items-center gap-3">
          {showCta && (
            <Button size="sm" className="hidden @3xl:inline-flex" onClick={() => goto("expense-form")}>
              ＋ 経費を申請する
            </Button>
          )}
          <span className="flex size-8 items-center justify-center rounded-full bg-accent text-xs font-bold">田</span>
        </div>
      </div>
    </header>
  );
}
