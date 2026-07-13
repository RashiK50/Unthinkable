import { useQuery } from "@tanstack/react-query";
import { Lightbulb, Mic, Plus } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";

import { EmptyState } from "@/components/shared/EmptyState";
import { StatCard } from "@/components/shared/StatCard";
import { Button } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { MeetingRow } from "@/features/meetings/MeetingRow";
import { UploadDialog } from "@/features/meetings/UploadDialog";
import { api } from "@/lib/api";
import type { DashboardStats, Insight, Meeting, Page } from "@/types/api";

export function DashboardPage() {
  const [uploadOpen, setUploadOpen] = useState(false);

  const stats = useQuery({
    queryKey: ["dashboard", "stats"],
    queryFn: () => api<DashboardStats>("/api/v1/dashboard/stats"),
  });
  const insights = useQuery({
    queryKey: ["dashboard", "insights"],
    queryFn: () => api<{ insights: Insight[] }>("/api/v1/dashboard/insights"),
  });
  const recent = useQuery({
    queryKey: ["meetings", { page: 1, page_size: 5 }],
    queryFn: () => api<Page<Meeting>>("/api/v1/meetings?page=1&page_size=5"),
  });

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Dashboard</h1>
          <p className="mt-0.5 text-sm text-zinc-400">Your meeting intelligence at a glance</p>
        </div>
        <Button onClick={() => setUploadOpen(true)}>
          <Plus size={15} aria-hidden /> Upload meeting
        </Button>
      </div>

      {stats.isPending ? (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      ) : stats.data ? (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <StatCard
            label="Meetings"
            value={stats.data.total_meetings}
            hint={`+${stats.data.meetings_this_week} this week`}
            accent="emerald"
          />
          <StatCard label="Hours processed" value={stats.data.hours_processed} />
          <StatCard
            label="Open action items"
            value={stats.data.open_action_items}
            hint={
              stats.data.overdue_action_items > 0
                ? `${stats.data.overdue_action_items} overdue`
                : "none overdue"
            }
            accent={stats.data.overdue_action_items > 0 ? "rose" : undefined}
          />
          <StatCard
            label="Avg health score"
            value={stats.data.avg_health_score ?? "—"}
            hint="across analyzed meetings"
          />
        </div>
      ) : (
        <p className="text-sm text-rose-400">Couldn&apos;t load stats.</p>
      )}

      {insights.data && insights.data.insights.length > 0 && (
        <Card className="mt-6">
          <CardTitle>AI insights</CardTitle>
          <ul className="space-y-2">
            {insights.data.insights.map((insight, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-zinc-300">
                <Lightbulb size={14} className="mt-0.5 shrink-0 text-amber-400" aria-hidden />
                {insight.message}
              </li>
            ))}
          </ul>
        </Card>
      )}

      <div className="mt-6">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-zinc-300">Recent meetings</h2>
          <Link to="/meetings" className="text-xs text-indigo-400 hover:underline">
            View all
          </Link>
        </div>
        {recent.isPending ? (
          <Skeleton className="h-48" />
        ) : recent.data && recent.data.items.length > 0 ? (
          <div className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900">
            {recent.data.items.map((m) => (
              <MeetingRow key={m.id} meeting={m} />
            ))}
          </div>
        ) : (
          <EmptyState
            icon={Mic}
            title="No meetings yet"
            description="Upload your first recording and MeetIQ will turn it into a structured intelligence report."
            action={
              <Button onClick={() => setUploadOpen(true)}>
                <Plus size={15} aria-hidden /> Upload meeting
              </Button>
            }
          />
        )}
      </div>

      <UploadDialog open={uploadOpen} onClose={() => setUploadOpen(false)} />
    </div>
  );
}
