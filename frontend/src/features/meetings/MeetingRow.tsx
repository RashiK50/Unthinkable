import { ChevronRight, Clock } from "lucide-react";
import { Link } from "react-router-dom";

import { StatusBadge } from "@/components/shared/StatusBadge";
import { formatDuration, timeAgo } from "@/lib/format";
import type { Meeting } from "@/types/api";

export function MeetingRow({ meeting }: { meeting: Meeting }) {
  return (
    <Link
      to={`/meetings/${meeting.id}`}
      className="flex items-center gap-3 border-b border-zinc-800 px-4 py-3 transition-colors last:border-0 hover:bg-zinc-800/50"
    >
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-zinc-100">{meeting.title}</p>
        <p className="mt-0.5 flex items-center gap-2 text-xs text-zinc-500">
          <Clock size={11} aria-hidden />
          {formatDuration(meeting.duration_seconds)}
          <span aria-hidden>·</span>
          {timeAgo(meeting.created_at)}
        </p>
      </div>
      <StatusBadge status={meeting.status} />
      <ChevronRight size={16} className="shrink-0 text-zinc-600" aria-hidden />
    </Link>
  );
}
