import { Heart } from "lucide-react";
import { cn } from "@/lib/utils";

/* お気に入りボタン — 即時フィードバックのマイクロインタラクション（design.notes）。
   カード上に重ねるため click は伝播させない */
export function FavButton({ on, onToggle }: { on: boolean; onToggle: () => void }) {
  return (
    <button
      type="button"
      aria-pressed={on}
      title={on ? "お気に入りから外す" : "お気に入りに追加"}
      onClick={(e) => { e.stopPropagation(); onToggle(); }}
      className="flex size-9 cursor-pointer items-center justify-center rounded-full bg-card/90 shadow-sm outline-none transition-transform focus-visible:ring-2 focus-visible:ring-ring active:scale-90"
    >
      <Heart className={cn("size-4.5", on ? "fill-primary stroke-primary" : "stroke-foreground")} />
    </button>
  );
}
