import { useQueryClient } from "@tanstack/react-query";
import { UploadCloud } from "lucide-react";
import { useRef, useState, type DragEvent } from "react";
import { useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { api, uploadToSignedUrl } from "@/lib/api";
import { cn } from "@/lib/cn";
import { formatBytes } from "@/lib/format";
import type { MeetingCreated } from "@/types/api";

const ACCEPT = ".mp3,.wav,.mp4,.m4a";
const MAX_BYTES = 500 * 1024 * 1024;

type Phase = "idle" | "registering" | "uploading" | "starting";

export function UploadDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [phase, setPhase] = useState<Phase>("idle");
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const busy = phase !== "idle";

  function pick(f: File) {
    setError(null);
    if (f.size > MAX_BYTES) {
      setError("File exceeds the 500 MB limit");
      return;
    }
    setFile(f);
    if (!title) setTitle(f.name.replace(/\.[^.]+$/, "").replace(/[-_]+/g, " "));
  }

  function onDrop(e: DragEvent) {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) pick(f);
  }

  async function start() {
    if (!file || !title.trim()) return;
    setError(null);
    try {
      setPhase("registering");
      const created = await api<MeetingCreated>("/api/v1/meetings", {
        method: "POST",
        body: JSON.stringify({
          title: title.trim(),
          filename: file.name,
          content_type: file.type || "application/octet-stream",
          size_bytes: file.size,
        }),
      });
      setPhase("uploading");
      await uploadToSignedUrl(created.upload.signed_url, file, setProgress);
      setPhase("starting");
      await api(`/api/v1/meetings/${created.meeting.id}/process`, { method: "POST" });
      await queryClient.invalidateQueries({ queryKey: ["meetings"] });
      navigate(`/meetings/${created.meeting.id}`);
    } catch (err) {
      setPhase("idle");
      setError(err instanceof Error ? err.message : "Upload failed");
    }
  }

  return (
    <Dialog open={open} onClose={busy ? () => undefined : onClose} title="Upload meeting">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => !busy && inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
        className={cn(
          "flex cursor-pointer flex-col items-center rounded-xl border-2 border-dashed p-8 text-center transition-colors",
          dragging ? "border-indigo-500 bg-indigo-500/5" : "border-zinc-700 hover:border-zinc-500",
        )}
      >
        <UploadCloud className="mb-2 text-zinc-500" size={26} aria-hidden />
        <p className="text-sm text-zinc-300">Drag &amp; drop audio/video, or click to browse</p>
        <p className="mt-1 text-xs text-zinc-500">mp3 · wav · mp4 · m4a — up to 500 MB</p>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT}
          className="hidden"
          onChange={(e) => e.target.files?.[0] && pick(e.target.files[0])}
        />
      </div>

      <div className="mt-4 space-y-3">
        <div>
          <label htmlFor="meeting-title" className="mb-1.5 block text-xs font-medium text-zinc-400">
            Title
          </label>
          <Input
            id="meeting-title"
            value={title}
            disabled={busy}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Q3 Planning Sync"
          />
        </div>

        {file && (
          <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-3">
            <div className="flex items-center justify-between text-xs">
              <span className="truncate text-zinc-300">{file.name}</span>
              <span className="ml-2 shrink-0 text-zinc-500">{formatBytes(file.size)}</span>
            </div>
            {phase === "uploading" && (
              <div className="mt-2 flex items-center gap-2">
                <Progress value={progress} />
                <span className="w-9 text-right text-xs tabular-nums text-zinc-400">
                  {Math.round(progress * 100)}%
                </span>
              </div>
            )}
            {phase === "registering" && <p className="mt-2 text-xs text-zinc-500">Preparing…</p>}
            {phase === "starting" && (
              <p className="mt-2 text-xs text-indigo-400">Starting analysis…</p>
            )}
          </div>
        )}

        {error && <p className="text-xs text-rose-400">{error}</p>}

        <div className="flex justify-end gap-2 pt-1">
          <Button variant="secondary" onClick={onClose} disabled={busy}>
            Cancel
          </Button>
          <Button onClick={start} disabled={!file || !title.trim() || busy}>
            {busy ? "Working…" : "Upload & analyze"}
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
