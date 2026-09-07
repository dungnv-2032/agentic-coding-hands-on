import { Card } from "@/components/ui/card";

/* 実績カード — 回数など『やった事実』のみ。ペース等の性能数値は初心者に出さない（src-um インサイト） */
export function StatCard({ value, label }: { value: string; label: string }) {
  return (
    <Card className="px-4 py-3 text-center">
      <div className="tabular text-lg font-extrabold">{value}</div>
      <div className="mt-0.5 text-[11px] text-muted-foreground">{label}</div>
    </Card>
  );
}
