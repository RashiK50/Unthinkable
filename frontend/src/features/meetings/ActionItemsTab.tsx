import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ListTodo, Plus, Trash2 } from "lucide-react";
import { useState } from "react";

import { EmptyState } from "@/components/shared/EmptyState";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { ActionItem, ActionPriority, ActionStatus } from "@/types/api";

const PRIORITY_STYLES: Record<ActionPriority, string> = {
  low: "text-zinc-400",
  medium: "text-sky-300",
  high: "text-amber-300",
  urgent: "text-rose-300",
};

export function ActionItemsTab({ meetingId }: { meetingId: string }) {
  const queryClient = useQueryClient();
  const [newTask, setNewTask] = useState("");
  const [newOwner, setNewOwner] = useState("");

  const items = useQuery({
    queryKey: ["action-items", meetingId],
    queryFn: () => api<ActionItem[]>(`/api/v1/meetings/${meetingId}/action-items`),
  });

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: ["action-items", meetingId] });

  const update = useMutation({
    mutationFn: ({ id, patch }: { id: string; patch: Partial<ActionItem> }) =>
      api(`/api/v1/action-items/${id}`, { method: "PATCH", body: JSON.stringify(patch) }),
    onSuccess: invalidate,
  });

  const create = useMutation({
    mutationFn: () =>
      api(`/api/v1/meetings/${meetingId}/action-items`, {
        method: "POST",
        body: JSON.stringify({ task: newTask.trim(), owner: newOwner.trim() || null }),
      }),
    onSuccess: () => {
      setNewTask("");
      setNewOwner("");
      invalidate();
    },
  });

  const remove = useMutation({
    mutationFn: (id: string) => api(`/api/v1/action-items/${id}`, { method: "DELETE" }),
    onSuccess: invalidate,
  });

  if (items.isPending) return <Skeleton className="h-64" />;

  const today = new Date().toISOString().slice(0, 10);

  return (
    <div className="space-y-4">
      {items.data && items.data.length > 0 ? (
        <div className="overflow-x-auto rounded-xl border border-zinc-800 bg-zinc-900">
          <table className="w-full min-w-[640px] text-sm">
            <thead>
              <tr className="border-b border-zinc-800 text-left text-xs text-zinc-400">
                <th className="px-4 py-2.5 font-medium">Task</th>
                <th className="px-4 py-2.5 font-medium">Owner</th>
                <th className="px-4 py-2.5 font-medium">Deadline</th>
                <th className="px-4 py-2.5 font-medium">Priority</th>
                <th className="px-4 py-2.5 font-medium">Status</th>
                <th className="w-10" aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {items.data.map((item) => {
                const overdue =
                  item.due_date && item.due_date < today && item.status !== "done";
                return (
                  <tr key={item.id} className="border-b border-zinc-800/60 last:border-0">
                    <td
                      className={cn(
                        "px-4 py-2.5 text-zinc-200",
                        item.status === "done" && "text-zinc-500 line-through",
                      )}
                    >
                      {item.task}
                    </td>
                    <td className="px-4 py-2.5 text-zinc-300">{item.owner ?? "—"}</td>
                    <td className="px-4 py-2.5">
                      <input
                        type="date"
                        value={item.due_date ?? ""}
                        onChange={(e) =>
                          update.mutate({
                            id: item.id,
                            patch: { due_date: e.target.value || null },
                          })
                        }
                        className={cn(
                          "rounded border border-transparent bg-transparent text-xs hover:border-zinc-700",
                          overdue ? "text-rose-400" : "text-zinc-300",
                        )}
                        aria-label={`Deadline for ${item.task}`}
                      />
                    </td>
                    <td className="px-4 py-2.5">
                      <Select
                        value={item.priority}
                        className={PRIORITY_STYLES[item.priority]}
                        onChange={(e) =>
                          update.mutate({
                            id: item.id,
                            patch: { priority: e.target.value as ActionPriority },
                          })
                        }
                        aria-label={`Priority for ${item.task}`}
                      >
                        <option value="low">low</option>
                        <option value="medium">medium</option>
                        <option value="high">high</option>
                        <option value="urgent">urgent</option>
                      </Select>
                    </td>
                    <td className="px-4 py-2.5">
                      <Select
                        value={item.status}
                        onChange={(e) =>
                          update.mutate({
                            id: item.id,
                            patch: { status: e.target.value as ActionStatus },
                          })
                        }
                        aria-label={`Status for ${item.task}`}
                      >
                        <option value="open">open</option>
                        <option value="in_progress">in progress</option>
                        <option value="done">done</option>
                        <option value="blocked">blocked</option>
                      </Select>
                    </td>
                    <td className="px-2 py-2.5">
                      <button
                        onClick={() => remove.mutate(item.id)}
                        className="text-zinc-600 hover:text-rose-400"
                        aria-label={`Delete ${item.task}`}
                      >
                        <Trash2 size={14} />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <EmptyState
          icon={ListTodo}
          title="No action items"
          description="The AI didn't detect any commitments in this meeting. Add one manually below."
        />
      )}

      <form
        className="flex flex-wrap gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          if (newTask.trim()) create.mutate();
        }}
      >
        <Input
          className="min-w-48 flex-1"
          placeholder="Add a task…"
          value={newTask}
          onChange={(e) => setNewTask(e.target.value)}
          aria-label="New task"
        />
        <Input
          className="w-36"
          placeholder="Owner"
          value={newOwner}
          onChange={(e) => setNewOwner(e.target.value)}
          aria-label="New task owner"
        />
        <Button type="submit" disabled={!newTask.trim() || create.isPending}>
          <Plus size={15} aria-hidden /> Add
        </Button>
      </form>
    </div>
  );
}
