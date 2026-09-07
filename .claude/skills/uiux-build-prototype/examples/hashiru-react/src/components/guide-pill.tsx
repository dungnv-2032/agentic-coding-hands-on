import type { ReactNode } from "react";

/* 音声ガイドピル — ラン中の声かけ表示。丸ピル・穏やかな muted で（急かさない） */
export function GuidePill({ children }: { children: ReactNode }) {
  return (
    <div className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-4 py-2.5 text-sm text-muted-foreground shadow-sm">
      🎧 {children}
    </div>
  );
}
