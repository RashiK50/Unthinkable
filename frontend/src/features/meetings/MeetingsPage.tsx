import { useQuery } from "@tanstack/react-query";
import { Mic, Plus, Search } from "lucide-react";
import { useEffect, useState } from "react";

import { EmptyState } from "@/components/shared/EmptyState";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { MeetingRow } from "@/features/meetings/MeetingRow";
import { UploadDialog } from "@/features/meetings/UploadDialog";
import { api } from "@/lib/api";
import type { Meeting, Page } from "@/types/api";

const PAGE_SIZE = 20;

export function MeetingsPage() {
  const [search, setSearch] = useState("");
  const [debounced, setDebounced] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [uploadOpen, setUploadOpen] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => {
      setDebounced(search);
      setPage(1);
    }, 300);
    return () => clearTimeout(t);
  }, [search]);

  const query = useQuery({
    queryKey: ["meetings", { q: debounced, status, page }],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page), page_size: String(PAGE_SIZE) });
      if (debounced) params.set("q", debounced);
      if (status) params.set("status", status);
      return api<Page<Meeting>>(`/api/v1/meetings?${params}`);
    },
  });

  const totalPages = query.data ? Math.max(1, Math.ceil(query.data.total / PAGE_SIZE)) : 1;

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Meetings</h1>
          <p className="mt-0.5 text-sm text-zinc-400">
            {query.data ? `${query.data.total} total` : "…"}
          </p>
        </div>
        <Button onClick={() => setUploadOpen(true)}>
          <Plus size={15} aria-hidden /> Upload meeting
        </Button>
      </div>

      <div className="mb-4 flex gap-2">
        <div className="relative flex-1">
          <Search
            size={14}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500"
            aria-hidden
          />
          <Input
            className="pl-8"
            placeholder="Search meetings…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label="Search meetings"
          />
        </div>
        <Select
          className="h-9"
          value={status}
          onChange={(e) => {
            setStatus(e.target.value);
            setPage(1);
          }}
          aria-label="Filter by status"
        >
          <option value="">All statuses</option>
          <option value="completed">Completed</option>
          <option value="analyzing">Analyzing</option>
          <option value="transcribing">Transcribing</option>
          <option value="failed">Failed</option>
        </Select>
      </div>

      {query.isPending ? (
        <Skeleton className="h-64" />
      ) : query.data && query.data.items.length > 0 ? (
        <>
          <div className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900">
            {query.data.items.map((m) => (
              <MeetingRow key={m.id} meeting={m} />
            ))}
          </div>
          {totalPages > 1 && (
            <div className="mt-4 flex items-center justify-between text-xs text-zinc-400">
              <span>
                Page {page} of {totalPages}
              </span>
              <div className="flex gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  Previous
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </>
      ) : (
        <EmptyState
          icon={Mic}
          title={debounced || status ? "No meetings match your filters" : "No meetings yet"}
          description={
            debounced || status
              ? "Try a different search or clear the status filter."
              : "Upload a recording to get started."
          }
        />
      )}

      <UploadDialog open={uploadOpen} onClose={() => setUploadOpen(false)} />
    </div>
  );
}
