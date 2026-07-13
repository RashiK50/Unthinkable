import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Play, Send } from "lucide-react";
import { useEffect, useRef, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { cn } from "@/lib/cn";
import { formatMs } from "@/lib/format";
import type { ChatAnswer, ChatMessage } from "@/types/api";

const SUGGESTIONS = [
  "What were the main decisions?",
  "Who owns which action items?",
  "Was budget discussed?",
  "What's blocking us right now?",
];

export function ChatTab({ meetingId }: { meetingId: string }) {
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();

  const history = useQuery({
    queryKey: ["chat", meetingId],
    queryFn: () => api<ChatMessage[]>(`/api/v1/meetings/${meetingId}/chat`),
  });

  const ask = useMutation({
    mutationFn: (message: string) =>
      api<ChatAnswer>(`/api/v1/meetings/${meetingId}/chat`, {
        method: "POST",
        body: JSON.stringify({ message }),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["chat", meetingId] }),
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history.data, ask.isPending]);

  function submit(e: FormEvent) {
    e.preventDefault();
    const message = input.trim();
    if (!message || ask.isPending) return;
    setInput("");
    ask.mutate(message);
  }

  if (history.isPending) return <Skeleton className="h-96" />;

  const messages = history.data ?? [];

  return (
    <Card className="flex h-[32rem] flex-col p-0">
      <div className="flex-1 space-y-4 overflow-y-auto p-5">
        {messages.length === 0 && !ask.isPending && (
          <div className="flex h-full flex-col items-center justify-center">
            <p className="mb-4 text-sm text-zinc-400">Ask anything about this meeting.</p>
            <div className="flex max-w-md flex-wrap justify-center gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => ask.mutate(s)}
                  className="rounded-full border border-zinc-700 px-3 py-1.5 text-xs text-zinc-300 transition-colors hover:border-indigo-500 hover:text-indigo-300"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m) => (
          <div key={m.id} className={cn("flex", m.role === "user" && "justify-end")}>
            <div
              className={cn(
                "max-w-[85%] rounded-xl px-3.5 py-2.5 text-sm leading-relaxed",
                m.role === "user"
                  ? "bg-indigo-500/20 text-zinc-100"
                  : "bg-zinc-800 text-zinc-200",
              )}
            >
              <p className="whitespace-pre-line">{m.content}</p>
              {m.sources.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {m.sources.map((s) => (
                    <span
                      key={s.chunk_id}
                      className="inline-flex items-center gap-1 rounded-full bg-zinc-900 px-2 py-0.5 text-[10px] tabular-nums text-zinc-400"
                      title="Transcript reference"
                    >
                      <Play size={8} aria-hidden />
                      {formatMs(s.start_ms ?? 0)}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {ask.isPending && (
          <div className="flex items-center gap-2 text-xs text-zinc-500">
            <Loader2 size={13} className="animate-spin" aria-hidden />
            Searching the transcript…
          </div>
        )}
        {ask.isError && (
          <p className="text-xs text-rose-400">
            {ask.error instanceof Error ? ask.error.message : "Something went wrong."}
          </p>
        )}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={submit} className="flex gap-2 border-t border-zinc-800 p-3">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about this meeting…"
          aria-label="Chat message"
        />
        <Button type="submit" disabled={!input.trim() || ask.isPending} aria-label="Send">
          <Send size={15} aria-hidden />
        </Button>
      </form>
    </Card>
  );
}
