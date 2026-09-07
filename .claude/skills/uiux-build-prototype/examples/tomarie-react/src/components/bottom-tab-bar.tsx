import { CalendarDays, CircleUserRound, Heart, Search } from "lucide-react";
import { useAppMode } from "@/pt/app-mode";
import { cn } from "@/lib/utils";

/* ボトムタブバー — モバイルアプリ表示のグローバルナビ（ui-craft §0）。
   web 表示では描画しない（グローバルヘッダーが担う）。
   さがす以外のタブはMVPスコープ外（pt-spec assumptions 参照） */
export function BottomTabBar({ current = "search" }: { current?: "search" | "favs" | "trips" | "profile" }) {
  const mode = useAppMode();
  if (mode !== "native") return null;
  const tabs = [
    { id: "search", label: "さがす", icon: Search },
    { id: "favs", label: "お気に入り", icon: Heart },
    { id: "trips", label: "予約", icon: CalendarDays },
    { id: "profile", label: "プロフィール", icon: CircleUserRound },
  ] as const;
  return (
    <nav className="sticky bottom-0 z-10 border-t border-border bg-card pb-3">
      <div className="mx-auto flex max-w-[520px] justify-around pt-1.5">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            type="button"
            title={id === current ? undefined : "MVPスコープ外"}
            className={cn(
              "flex min-w-16 cursor-pointer flex-col items-center gap-0.5 rounded-md p-1 text-[10px] outline-none focus-visible:ring-2 focus-visible:ring-ring",
              id === current ? "font-bold text-primary" : "text-muted-foreground",
            )}
          >
            <Icon className="size-5" />
            {label}
          </button>
        ))}
      </div>
    </nav>
  );
}
