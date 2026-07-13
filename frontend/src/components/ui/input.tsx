import { forwardRef, type InputHTMLAttributes } from "react";

import { cn } from "@/lib/cn";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        "h-9 w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 text-sm text-zinc-100",
        "placeholder:text-zinc-500 focus:border-indigo-500 focus:outline-none",
        "focus:ring-1 focus:ring-indigo-500",
        className,
      )}
      {...props}
    />
  ),
);
Input.displayName = "Input";
