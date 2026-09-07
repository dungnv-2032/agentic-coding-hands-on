import * as React from "react";
import { cn } from "@/lib/utils";

const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, type, ...props }, ref) => (
    <input
      type={type}
      ref={ref}
      className={cn(
        // 入力フォント15px以上（iOSズーム回避, ui-craft §7）
        "flex h-12 w-full rounded-lg border border-input bg-card px-3 py-2 text-[15px] text-foreground placeholder:text-muted-foreground outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 read-only:bg-card",
        className,
      )}
      {...props}
    />
  ),
);
Input.displayName = "Input";

export { Input };
