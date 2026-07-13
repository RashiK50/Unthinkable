import { useQuery } from "@tanstack/react-query";
import { Check, Loader2, X } from "lucide-react";

import { Card, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { MeetingStatusOut } from "@/types/api";

const STAGES: { id: string; label: string }[] = [
  { id: "transcription", label: "Transcribe & diarize" },
  { id: "cleaning", label: "Clean transcript" },
  { id: "topics", label: "Detect topics" },
  { id: "decisions", label: "Extract decisions" },
  { id: "action_items", label: "Extract action items" },
  { id: "risks", label: "Detect risks" },
  { id: "deadlines", label: "Extract deadlines" },
  { id: "health", label: "Score meeting health" },
  { id: "summary", label: "Write executive summary" },
  { id: "report", label: "Assemble report" },
  { id: "embeddings", label: "Index for chat" },
];

export function ProcessingView({ meetingId }: { meetingId: string }) {
  const status = useQuery({
    queryKey: ["meeting-status", meetingId],
    queryFn: () => api<MeetingStatusOut>(`/api/v1/meetings/${meetingId}/status`),
    refetchInterval: 2000,
  });

  const byStage = new Map(status.data?.stages.map((s) => [s.stage, s]) ?? []);
  const uploadPhase = status.data?.status === "uploading" || status.data?.status === "uploaded";

  return (
    <Card>
      <CardTitle>Analyzing your meeting</CardTitle>
      <p className="mb-4 text-xs text-zinc-500">
        {uploadPhase
          ? "Waiting for processing to begin…"
          : "This usually takes a few minutes depending on recording length."}
      </p>
      <ol className="space-y-2.5">
        {STAGES.map(({ id, label }) => {
          const stage = byStage.get(id);
          const state = stage?.status ?? "pending";
          return (
            <li key={id} className="flex items-center gap-2.5 text-sm">
              {state === "succeeded" ? (
                <Check size={15} className="text-emerald-400" aria-hidden />
              ) : state === "failed" ? (
                <X size={15} className="text-rose-400" aria-hidden />
              ) : state === "started" ? (
                <Loader2 size={15} className="animate-spin text-indigo-400" aria-hidden />
              ) : (
                <span className="h-[15px] w-[15px] rounded-full border border-zinc-700" aria-hidden />
              )}
              <span
                className={cn(
                  state === "pending" && "text-zinc-500",
                  state === "started" && "text-zinc-100",
                  state === "succeeded" && "text-zinc-300",
                  state === "failed" && "text-rose-300",
                )}
              >
                {label}
                {state === "failed" && stage?.detail && (
                  <span className="ml-2 text-xs text-zinc-500">— continuing without it</span>
                )}
              </span>
            </li>
          );
        })}
      </ol>
    </Card>
  );
}
