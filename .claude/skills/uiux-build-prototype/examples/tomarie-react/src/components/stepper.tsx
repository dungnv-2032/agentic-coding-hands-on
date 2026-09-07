import { Minus, Plus } from "lucide-react";

/* 人数ステッパー — 44px タップ目標・即時反映（マイクロインタラクション契約） */
export function Stepper({
  value,
  min = 1,
  max = 8,
  onChange,
}: {
  value: number;
  min?: number;
  max?: number;
  onChange: (v: number) => void;
}) {
  const btn =
    "flex size-9 cursor-pointer items-center justify-center rounded-full border border-border bg-card outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-30 disabled:cursor-not-allowed active:scale-95";
  return (
    <div className="flex items-center gap-3">
      <button type="button" className={btn} disabled={value <= min} onClick={() => onChange(value - 1)} aria-label="減らす">
        <Minus className="size-4" />
      </button>
      <span className="tabular w-8 text-center font-bold">{value}人</span>
      <button type="button" className={btn} disabled={value >= max} onClick={() => onChange(value + 1)} aria-label="増やす">
        <Plus className="size-4" />
      </button>
    </div>
  );
}
