import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Pencil } from "lucide-react";
import { useState } from "react";

import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { formatMs } from "@/lib/format";
import type { Meeting, Report, Speaker, Transcript } from "@/types/api";

const SPEAKER_COLORS = ["#818cf8", "#34d399", "#fbbf24", "#f472b6", "#38bdf8", "#fb923c"];

const TOPIC_COLORS = [
  "bg-indigo-500/60",
  "bg-emerald-500/60",
  "bg-amber-500/60",
  "bg-pink-500/60",
  "bg-sky-500/60",
  "bg-orange-500/60",
];

function speakerColor(speakers: Speaker[], label: string): string {
  const idx = speakers.findIndex((s) => s.label === label);
  return SPEAKER_COLORS[(idx >= 0 ? idx : 0) % SPEAKER_COLORS.length];
}

function SpeakerName({
  meetingId,
  speaker,
  color,
}: {
  meetingId: string;
  speaker: Speaker;
  color: string;
}) {
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(speaker.display_name);
  const queryClient = useQueryClient();

  const rename = useMutation({
    mutationFn: (display_name: string) =>
      api(`/api/v1/meetings/${meetingId}/speakers/${speaker.id}`, {
        method: "PATCH",
        body: JSON.stringify({ display_name }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transcript", meetingId] });
      queryClient.invalidateQueries({ queryKey: ["meeting", meetingId] });
      setEditing(false);
    },
  });

  if (editing) {
    return (
      <span className="inline-flex items-center gap-1">
        <Input
          className="h-6 w-32 px-1.5 text-xs"
          value={name}
          autoFocus
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && name.trim() && rename.mutate(name.trim())}
        />
        <button
          onClick={() => name.trim() && rename.mutate(name.trim())}
          className="text-emerald-400"
          aria-label="Save speaker name"
        >
          <Check size={13} />
        </button>
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className="h-2 w-2 rounded-full" style={{ background: color }} aria-hidden />
      <span className="text-xs font-semibold" style={{ color }}>
        {speaker.display_name}
      </span>
      <button
        onClick={() => setEditing(true)}
        className="text-zinc-600 hover:text-zinc-300"
        aria-label={`Rename ${speaker.display_name}`}
      >
        <Pencil size={11} />
      </button>
    </span>
  );
}

export function TranscriptTab({
  meetingId,
  meeting,
  report,
}: {
  meetingId: string;
  meeting: Meeting;
  report: Report;
}) {
  const transcript = useQuery({
    queryKey: ["transcript", meetingId],
    queryFn: () => api<Transcript>(`/api/v1/meetings/${meetingId}/transcript`),
  });

  if (transcript.isPending) return <Skeleton className="h-96" />;
  if (!transcript.data || transcript.data.segments.length === 0) {
    return <p className="text-sm text-zinc-500">No transcript available for this meeting.</p>;
  }

  const { segments, speakers } = transcript.data;
  const speakerById = new Map(speakers.map((s) => [s.label, s]));
  const totalMs =
    (meeting.duration_seconds ?? 0) * 1000 || segments[segments.length - 1]?.end_ms || 1;

  const timedTopics = report.topics.filter(
    (t) => t.start_ms != null && t.end_ms != null && t.end_ms > t.start_ms,
  );

  function jumpTo(startMs: number | null) {
    if (startMs == null) return;
    const target = segments.find((s) => s.end_ms >= startMs) ?? segments[0];
    document
      .getElementById(`seg-${target.id}`)
      ?.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  return (
    <div className="space-y-4">
      {timedTopics.length > 0 && (
        <Card className="p-4">
          <div className="mb-2 flex justify-between text-[10px] tabular-nums text-zinc-500">
            <span>00:00</span>
            <span>{formatMs(totalMs)}</span>
          </div>
          <div className="relative h-6 overflow-hidden rounded bg-zinc-800">
            {timedTopics.map((t, i) => (
              <button
                key={i}
                title={t.title}
                onClick={() => jumpTo(t.start_ms)}
                className={`absolute inset-y-0 ${TOPIC_COLORS[i % TOPIC_COLORS.length]} transition-opacity hover:opacity-80`}
                style={{
                  left: `${(t.start_ms! / totalMs) * 100}%`,
                  width: `${Math.max(1, ((t.end_ms! - t.start_ms!) / totalMs) * 100)}%`,
                }}
                aria-label={`Jump to topic: ${t.title}`}
              />
            ))}
          </div>
          <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1">
            {timedTopics.map((t, i) => (
              <button
                key={i}
                onClick={() => jumpTo(t.start_ms)}
                className="flex items-center gap-1.5 text-[11px] text-zinc-400 hover:text-zinc-200"
              >
                <span
                  className={`h-2 w-2 rounded-sm ${TOPIC_COLORS[i % TOPIC_COLORS.length]}`}
                  aria-hidden
                />
                {t.title}
              </button>
            ))}
          </div>
        </Card>
      )}

      <Card className="max-h-[32rem] overflow-y-auto p-0">
        <ul className="divide-y divide-zinc-800/70">
          {segments.map((seg) => {
            const speaker = speakerById.get(seg.speaker_label);
            const color = speakerColor(speakers, seg.speaker_label);
            return (
              <li key={seg.id} id={`seg-${seg.id}`} className="flex gap-3 px-4 py-3">
                <span className="w-11 shrink-0 pt-0.5 text-[11px] tabular-nums text-zinc-500">
                  {formatMs(seg.start_ms)}
                </span>
                <div className="min-w-0">
                  {speaker ? (
                    <SpeakerName meetingId={meetingId} speaker={speaker} color={color} />
                  ) : (
                    <span className="text-xs font-semibold" style={{ color }}>
                      {seg.speaker_label}
                    </span>
                  )}
                  <p className="mt-0.5 text-sm leading-relaxed text-zinc-200">{seg.text}</p>
                </div>
              </li>
            );
          })}
        </ul>
      </Card>
    </div>
  );
}
