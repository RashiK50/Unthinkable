import { forwardRef, type TextareaHTMLAttributes } from "react";

import { cn } from "@/lib/cn";

export const Textarea = forwardRef<
  HTMLTextAreaElement,
  TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, ...props }, ref) => (
  <textarea
    ref={ref}
    className={cn(
      "w-full rounded-lg border border-zinc-700 bg-zinc-900 p-3 text-sm text-zinc-100",
      "placeholder:text-zinc-500 focus:border-indigo-500 focus:outline-none",
      "focus:ring-1 focus:ring-indigo-500",
      className,
    )}
    {...props}
  />
));
Textarea.displayName = "Textarea";
