import { AlertTriangle, CalendarClock, CheckCircle2, HelpCircle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardTitle } from "@/components/ui/card";
import type { Report } from "@/types/api";

const severityTone = { low: "neutral", medium: "amber", high: "rose" } as const;

export function OverviewTab({ report }: { report: Report }) {
  const warnings = Object.keys(report.agent_warnings);
  return (
    <div className="space-y-5">
      {warnings.length > 0 && (
        <p className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-300">
          Some analysis stages were unavailable for this meeting: {warnings.join(", ")}.
        </p>
      )}

      <Card>
        <CardTitle>Executive summary</CardTitle>
        <p className="whitespace-pre-line text-sm leading-relaxed text-zinc-200">
          {report.executive_summary}
        </p>
      </Card>

      <div className="grid gap-5 lg:grid-cols-2">
        <Card>
          <CardTitle>Decisions ({report.decisions.length})</CardTitle>
          {report.decisions.length === 0 ? (
            <p className="text-xs text-zinc-500">No explicit decisions were detected.</p>
          ) : (
            <ul className="space-y-3">
              {report.decisions.map((d, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <CheckCircle2 size={15} className="mt-0.5 shrink-0 text-emerald-400" aria-hidden />
                  <div>
                    <p className="text-zinc-200">{d.decision}</p>
                    {d.made_by && <p className="mt-0.5 text-xs text-zinc-500">by {d.made_by}</p>}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card>
          <CardTitle>Risks &amp; blockers ({report.risks.length})</CardTitle>
          {report.risks.length === 0 ? (
            <p className="text-xs text-zinc-500">No risks raised. 🎉</p>
          ) : (
            <ul className="space-y-3">
              {report.risks.map((r, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <AlertTriangle size={15} className="mt-0.5 shrink-0 text-amber-400" aria-hidden />
                  <div>
                    <p className="text-zinc-200">{r.description}</p>
                    <p className="mt-1 flex gap-1.5">
                      <Badge tone={severityTone[r.severity] ?? "neutral"}>{r.severity}</Badge>
                      <Badge tone={r.kind === "blocker" ? "rose" : "neutral"}>{r.kind}</Badge>
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      <Card>
        <CardTitle>Key topics</CardTitle>
        {report.topics.length === 0 ? (
          <p className="text-xs text-zinc-500">No topics detected.</p>
        ) : (
          <div className="space-y-3">
            {report.topics.map((t, i) => (
              <div key={i}>
                <p className="text-sm font-medium text-zinc-200">{t.title}</p>
                <p className="mt-0.5 text-xs text-zinc-400">{t.summary}</p>
              </div>
            ))}
          </div>
        )}
      </Card>

      <div className="grid gap-5 lg:grid-cols-2">
        <div className="space-y-5">
          <Card>
            <CardTitle>Open questions</CardTitle>
            {report.open_questions.length === 0 ? (
              <p className="text-xs text-zinc-500">Everything raised was resolved.</p>
            ) : (
              <ul className="space-y-2">
                {report.open_questions.map((q, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-zinc-200">
                    <HelpCircle size={14} className="mt-0.5 shrink-0 text-indigo-400" aria-hidden />
                    {q.question}
                    {q.raised_by && <span className="text-xs text-zinc-500">({q.raised_by})</span>}
                  </li>
                ))}
              </ul>
            )}
          </Card>

          <Card>
            <CardTitle>Deadlines</CardTitle>
            {report.deadlines.length === 0 ? (
              <p className="text-xs text-zinc-500">No deadlines mentioned.</p>
            ) : (
              <ul className="space-y-2">
                {report.deadlines.map((d, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <CalendarClock size={14} className="mt-0.5 shrink-0 text-zinc-500" aria-hidden />
                    <span className="text-zinc-200">
                      {d.item}
                      <span className="ml-2 text-xs text-zinc-400">
                        {d.date_normalized ?? d.date_text}
                      </span>
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </Card>

          <Card>
            <CardTitle>Suggested agenda for next meeting</CardTitle>
            {report.next_meeting_agenda.length === 0 ? (
              <p className="text-xs text-zinc-500">No follow-up agenda suggested.</p>
            ) : (
              <ol className="list-inside list-decimal space-y-1.5 text-sm text-zinc-200">
                {report.next_meeting_agenda.map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ol>
            )}
          </Card>
        </div>

        <Card className="self-start">
          <CardTitle>Health breakdown — {report.health_score}/100</CardTitle>
          <div className="space-y-3">
            {Object.entries(report.health_breakdown).map(([dim, v]) => (
              <div key={dim}>
                <div className="mb-1 flex items-center justify-between text-xs">
                  <span className="capitalize text-zinc-300">{dim}</span>
                  <span className="tabular-nums text-zinc-400">{v.score}</span>
                </div>
                <div className="h-1.5 overflow-hidden rounded-full bg-zinc-800">
                  <div
                    className={
                      v.score >= 75
                        ? "h-full bg-emerald-400"
                        : v.score >= 55
                          ? "h-full bg-amber-400"
                          : "h-full bg-rose-400"
                    }
                    style={{ width: `${v.score}%` }}
                  />
                </div>
                <p className="mt-1 text-[11px] text-zinc-500">{v.rationale}</p>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
