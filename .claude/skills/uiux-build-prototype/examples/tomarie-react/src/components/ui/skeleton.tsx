import { cn } from "@/lib/utils";

// ローディングはレイアウトを写したスケルトンで（ui-craft §6）
function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("animate-pulse rounded-md bg-border", className)} {...props} />;
}

export { Skeleton };
