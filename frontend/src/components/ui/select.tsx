import { forwardRef, type SelectHTMLAttributes } from "react";

import { cn } from "@/lib/cn";

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
  ({ className, ...props }, ref) => (
    <select
      ref={ref}
      className={cn(
        "h-8 rounded-lg border border-zinc-700 bg-zinc-900 px-2 text-xs text-zinc-100",
        "focus:border-indigo-500 focus:outline-none",
        className,
      )}
      {...props}
    />
  ),
);
Select.displayName = "Select";
