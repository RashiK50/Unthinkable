import { Download } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { apiDownload } from "@/lib/api";

const FORMATS = [
  { id: "pdf", label: "PDF report" },
  { id: "md", label: "Markdown" },
  { id: "txt", label: "Plain text" },
];

export function ExportMenu({ meetingId }: { meetingId: string }) {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, [open]);

  async function download(fmt: string) {
    setBusy(fmt);
    setError(null);
    try {
      await apiDownload(`/api/v1/meetings/${meetingId}/export?format=${fmt}`);
      setOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="relative" ref={ref}>
      <Button variant="secondary" size="sm" onClick={() => setOpen((v) => !v)}>
        <Download size={14} aria-hidden /> Export
      </Button>
      {open && (
        <div className="absolute right-0 z-30 mt-1 w-44 rounded-lg border border-zinc-800 bg-zinc-900 p-1 shadow-xl">
          {FORMATS.map((f) => (
            <button
              key={f.id}
              onClick={() => download(f.id)}
              disabled={busy !== null}
              className="w-full rounded-md px-3 py-2 text-left text-xs text-zinc-200 hover:bg-zinc-800 disabled:opacity-50"
            >
              {busy === f.id ? "Preparing…" : f.label}
            </button>
          ))}
          {error && <p className="px-3 py-1.5 text-[11px] text-rose-400">{error}</p>}
        </div>
      )}
    </div>
  );
}
