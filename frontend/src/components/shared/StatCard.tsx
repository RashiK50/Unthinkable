import type { ReactNode } from "react";

import { Card } from "@/components/ui/card";

export function StatCard({
  label,
  value,
  hint,
  accent,
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  accent?: "rose" | "emerald";
}) {
  return (
    <Card className="p-4">
      <p className="text-xs text-zinc-400">{label}</p>
      <p className="mt-1 text-2xl font-semibold tabular-nums">{value}</p>
      {hint && (
        <p
          className={
            accent === "rose"
              ? "mt-0.5 text-xs text-rose-400"
              : accent === "emerald"
                ? "mt-0.5 text-xs text-emerald-400"
                : "mt-0.5 text-xs text-zinc-500"
          }
        >
          {hint}
        </p>
      )}
    </Card>
  );
}
