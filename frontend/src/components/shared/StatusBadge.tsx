import { Badge } from "@/components/ui/badge";
import type { MeetingStatusValue } from "@/types/api";

const config: Record<MeetingStatusValue, { tone: "neutral" | "indigo" | "emerald" | "amber" | "rose"; label: string }> = {
  uploading: { tone: "neutral", label: "uploading" },
  uploaded: { tone: "neutral", label: "queued" },
  transcribing: { tone: "indigo", label: "transcribing" },
  analyzing: { tone: "indigo", label: "analyzing" },
  completed: { tone: "emerald", label: "completed" },
  failed: { tone: "rose", label: "failed" },
};

export function StatusBadge({ status }: { status: MeetingStatusValue }) {
  const { tone, label } = config[status];
  const inFlight = status === "transcribing" || status === "analyzing";
  return (
    <Badge tone={tone}>
      {inFlight && (
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-indigo-400" aria-hidden />
      )}
      {label}
    </Badge>
  );
}
