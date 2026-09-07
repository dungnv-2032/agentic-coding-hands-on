import type { ReactNode } from "react";

/* 励ましバナー — サボり復帰・承認の場面で使用。accent背景＋責めない文言（『それでいいんです』） */
export function EncourageBanner({ title, children }: { title: ReactNode; children?: ReactNode }) {
  return (
    <div className="rounded-lg border border-border bg-accent p-6 text-center">
      <div className="text-lg font-extrabold leading-relaxed">{title}</div>
      {children && <div className="mt-1.5 text-sm text-muted-foreground">{children}</div>}
    </div>
  );
}
