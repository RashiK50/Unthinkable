import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Card, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { formatMs } from "@/lib/format";
import type { Analytics } from "@/types/api";

const COLORS = ["#818cf8", "#34d399", "#fbbf24", "#f472b6", "#38bdf8", "#fb923c"];

const tooltipStyle = {
  backgroundColor: "#18181b",
  border: "1px solid #3f3f46",
  borderRadius: 8,
  fontSize: 12,
};

export function AnalyticsTab({ meetingId }: { meetingId: string }) {
  const analytics = useQuery({
    queryKey: ["analytics", meetingId],
    queryFn: () => api<Analytics>(`/api/v1/meetings/${meetingId}/analytics`),
  });

  if (analytics.isPending) return <Skeleton className="h-80" />;
  if (!analytics.data || analytics.data.speakers.length === 0) {
    return <p className="text-sm text-zinc-500">No speaker data available for this meeting.</p>;
  }

  const { speakers, topics_by_speaker } = analytics.data;
  const pieData = speakers.map((s) => ({ name: s.display_name, value: s.talk_time_ms }));
  const barData = speakers.map((s) => ({
    name: s.display_name,
    contributions: s.contribution_count,
  }));

  return (
    <div className="space-y-5">
      <div className="grid gap-5 lg:grid-cols-2">
        <Card>
          <CardTitle>Talk time</CardTitle>
          <div className="h-56">
            <ResponsiveContainer>
              <PieChart>
                <Pie
                  data={pieData}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={2}
                  stroke="none"
                >
                  {pieData.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={tooltipStyle}
                  formatter={(value: number) => formatMs(value)}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <ul className="mt-2 space-y-1.5">
            {speakers.map((s, i) => (
              <li key={s.label} className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-1.5 text-zinc-300">
                  <span
                    className="h-2 w-2 rounded-full"
                    style={{ background: COLORS[i % COLORS.length] }}
                    aria-hidden
                  />
                  {s.display_name}
                </span>
                <span className="tabular-nums text-zinc-400">
                  {formatMs(s.talk_time_ms)} · {Math.round(s.share * 100)}%
                </span>
              </li>
            ))}
          </ul>
        </Card>

        <Card>
          <CardTitle>Contributions</CardTitle>
          <div className="h-72">
            <ResponsiveContainer>
              <BarChart data={barData} layout="vertical" margin={{ left: 8, right: 8 }}>
                <XAxis type="number" tick={{ fill: "#a1a1aa", fontSize: 11 }} allowDecimals={false} />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={90}
                  tick={{ fill: "#a1a1aa", fontSize: 11 }}
                />
                <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "#27272a" }} />
                <Bar dataKey="contributions" radius={[0, 4, 4, 0]}>
                  {barData.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {topics_by_speaker.length > 0 && (
        <Card>
          <CardTitle>Who drove each topic</CardTitle>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[480px] text-sm">
              <thead>
                <tr className="border-b border-zinc-800 text-left text-xs text-zinc-400">
                  <th className="py-2 pr-4 font-medium">Topic</th>
                  <th className="py-2 font-medium">Speakers (time in topic)</th>
                </tr>
              </thead>
              <tbody>
                {topics_by_speaker.map((row, i) => (
                  <tr key={i} className="border-b border-zinc-800/60 last:border-0">
                    <td className="py-2.5 pr-4 text-zinc-200">{row.topic}</td>
                    <td className="py-2.5">
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(row.speakers)
                          .sort(([, a], [, b]) => b - a)
                          .map(([name, ms]) => (
                            <span
                              key={name}
                              className="rounded-full bg-zinc-800 px-2 py-0.5 text-[11px] text-zinc-300"
                            >
                              {name} · {formatMs(ms)}
                            </span>
                          ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
