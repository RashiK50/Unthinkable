import { useMutation } from "@tanstack/react-query";
import { Check, Copy, Mail } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import type { EmailDraft } from "@/types/api";

export function FollowUpEmailDialog({ meetingId }: { meetingId: string }) {
  const [open, setOpen] = useState(false);
  const [tone, setTone] = useState("professional");
  const [draft, setDraft] = useState<EmailDraft | null>(null);
  const [copied, setCopied] = useState(false);

  const generate = useMutation({
    mutationFn: () =>
      api<EmailDraft>(`/api/v1/meetings/${meetingId}/follow-up-email`, {
        method: "POST",
        body: JSON.stringify({ tone }),
      }),
    onSuccess: setDraft,
  });

  async function copy() {
    if (!draft) return;
    await navigator.clipboard.writeText(`Subject: ${draft.subject}\n\n${draft.body}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <>
      <Button variant="secondary" size="sm" onClick={() => setOpen(true)}>
        <Mail size={14} aria-hidden /> Follow-up email
      </Button>
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        title="Follow-up email"
        className="max-w-xl"
      >
        <div className="mb-3 flex items-center gap-2">
          <Select value={tone} onChange={(e) => setTone(e.target.value)} aria-label="Email tone">
            <option value="professional">Professional</option>
            <option value="friendly">Friendly</option>
            <option value="brief">Brief</option>
          </Select>
          <Button size="sm" onClick={() => generate.mutate()} disabled={generate.isPending}>
            {generate.isPending ? "Drafting…" : draft ? "Regenerate" : "Generate"}
          </Button>
        </div>

        {generate.isError && (
          <p className="mb-2 text-xs text-rose-400">
            {generate.error instanceof Error ? generate.error.message : "Generation failed"}
          </p>
        )}

        {draft && (
          <div className="space-y-3">
            <Input
              value={draft.subject}
              onChange={(e) => setDraft({ ...draft, subject: e.target.value })}
              aria-label="Email subject"
            />
            <Textarea
              rows={12}
              value={draft.body}
              onChange={(e) => setDraft({ ...draft, body: e.target.value })}
              aria-label="Email body"
            />
            <div className="flex justify-end">
              <Button variant="secondary" size="sm" onClick={copy}>
                {copied ? (
                  <>
                    <Check size={13} className="text-emerald-400" aria-hidden /> Copied
                  </>
                ) : (
                  <>
                    <Copy size={13} aria-hidden /> Copy to clipboard
                  </>
                )}
              </Button>
            </div>
          </div>
        )}
        {!draft && !generate.isPending && (
          <p className="text-xs text-zinc-500">
            MeetIQ drafts the recap from this meeting&apos;s report — decisions, action items, and
            open questions. You send it from your own email client.
          </p>
        )}
      </Dialog>
    </>
  );
}
