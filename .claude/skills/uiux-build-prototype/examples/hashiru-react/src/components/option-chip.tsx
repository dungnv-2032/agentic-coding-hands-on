import { cn } from "@/lib/utils";

/* 選択チップ — 設定は入力させず選ばせる（src-um インサイト『機能の多さは拒否シグナル』）。選択中はaccent塗り。
   onClick を渡せば実際に選択できる（マイクロインタラクション契約） */
export function OptionChip({
  label,
  selected,
  onClick,
}: {
  label: string;
  selected?: boolean;
  onClick?: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={selected}
      className={cn(
        "inline-flex cursor-pointer items-center rounded-full border-[1.5px] px-4 py-2.5 text-sm transition-colors",
        "outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 active:scale-[.97]",
        selected ? "border-primary bg-accent font-bold" : "border-border bg-card hover:border-primary/40",
      )}
    >
      {label}
    </button>
  );
}
