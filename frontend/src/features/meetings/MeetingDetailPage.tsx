import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Trash2 } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { HealthRing } from "@/components/shared/HealthRing";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { TabBar } from "@/components/ui/tabs";
import { ExportMenu } from "@/features/export/ExportMenu";
import { FollowUpEmailDialog } from "@/features/export/FollowUpEmailDialog";
import { ActionItemsTab } from "@/features/meetings/ActionItemsTab";
import { AnalyticsTab } from "@/features/meetings/AnalyticsTab";
import { ChatTab } from "@/features/meetings/ChatTab";
import { OverviewTab } from "@/features/meetings/OverviewTab";
import { ProcessingView } from "@/features/meetings/ProcessingView";
import { TranscriptTab } from "@/features/meetings/TranscriptTab";
import { api } from "@/lib/api";
import { formatDate, formatDuration } from "@/lib/format";
import type { MeetingDetail, MeetingStatusValue } from "@/types/api";

const TABS = [
  { id: "overview", label: "Overview" },
  { id: "transcript", label: "Transcript" },
  { id: "actions", label: "Action items" },
  { id: "analytics", label: "Analytics" },
  { id: "chat", label: "Chat" },
];

const IN_FLIGHT: MeetingStatusValue[] = ["uploading", "uploaded", "transcribing", "analyzing"];

export function MeetingDetailPage() {
  const { meetingId = "" } = useParams();
  const [tab, setTab] = useState("overview");
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const detail = useQuery({
    queryKey: ["meeting", meetingId],
    queryFn: () => api<MeetingDetail>(`/api/v1/meetings/${meetingId}`),
    refetchInterval: (query) => {
      const status = query.state.data?.meeting.status;
      return status && IN_FLIGHT.includes(status) ? 2500 : false;
    },
  });

  const retry = useMutation({
    mutationFn: () => api(`/api/v1/meetings/${meetingId}/process`, { method: "POST" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["meeting", meetingId] }),
  });

  const remove = useMutation({
    mutationFn: () => api(`/api/v1/meetings/${meetingId}`, { method: "DELETE" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["meetings"] });
      navigate("/meetings");
    },
  });

  if (detail.isPending) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-20" />
        <Skeleton className="h-64" />
      </div>
    );
  }
  if (detail.isError || !detail.data) {
    return <p className="text-sm text-rose-400">Meeting not found.</p>;
  }

  const { meeting, report } = detail.data;
  const inFlight = IN_FLIGHT.includes(meeting.status);

  return (
    <div>
      <Link
        to="/meetings"
        className="mb-4 inline-flex items-center gap-1 text-xs text-zinc-400 hover:text-zinc-200"
      >
        <ArrowLeft size={13} aria-hidden /> All meetings
      </Link>

      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-center gap-4">
          {report && <HealthRing score={report.health_score} size={52} />}
          <div>
            <h1 className="text-xl font-semibold">{meeting.title}</h1>
            <p className="mt-1 flex flex-wrap items-center gap-2 text-xs text-zinc-400">
              {formatDate(meeting.created_at)}
              <span aria-hidden>·</span>
              {formatDuration(meeting.duration_seconds)}
              <span aria-hidden>·</span>
              <StatusBadge status={meeting.status} />
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {meeting.status === "completed" && (
            <>
              <FollowUpEmailDialog meetingId={meetingId} />
              <ExportMenu meetingId={meetingId} />
            </>
          )}
          <Button
            variant="ghost"
            size="sm"
            aria-label="Delete meeting"
            onClick={() => {
              if (window.confirm("Delete this meeting and all its data?")) remove.mutate();
            }}
          >
            <Trash2 size={15} className="text-zinc-400" aria-hidden />
          </Button>
        </div>
      </div>

      {meeting.status === "failed" && (
        <Card className="mb-6 border-rose-500/30">
          <p className="text-sm font-medium text-rose-300">Processing failed</p>
          <p className="mt-1 text-xs text-zinc-400">
            {meeting.error_message ?? "Unknown error."}
          </p>
          <Button
            size="sm"
            variant="secondary"
            className="mt-3"
            onClick={() => retry.mutate()}
            disabled={retry.isPending}
          >
            {retry.isPending ? "Retrying…" : "Retry processing"}
          </Button>
        </Card>
      )}

      {inFlight && <ProcessingView meetingId={meetingId} />}

      {meeting.status === "completed" && report && (
        <>
          <TabBar tabs={TABS} active={tab} onChange={setTab} />
          <div className="pt-6">
            {tab === "overview" && <OverviewTab report={report} />}
            {tab === "transcript" && (
              <TranscriptTab meetingId={meetingId} meeting={meeting} report={report} />
            )}
            {tab === "actions" && <ActionItemsTab meetingId={meetingId} />}
            {tab === "analytics" && <AnalyticsTab meetingId={meetingId} />}
            {tab === "chat" && <ChatTab meetingId={meetingId} />}
          </div>
        </>
      )}
    </div>
  );
}
