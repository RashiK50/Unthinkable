/** Mirrors backend/app/schemas — the API contract, hand-kept in sync. */

export type MeetingStatusValue =
  | "uploading"
  | "uploaded"
  | "transcribing"
  | "analyzing"
  | "completed"
  | "failed";

export interface Meeting {
  id: string;
  title: string;
  status: MeetingStatusValue;
  audio_size_bytes: number | null;
  duration_seconds: number | null;
  language: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface UploadTarget {
  signed_url: string;
  path: string;
  expires_in: number;
}

export interface MeetingCreated {
  meeting: Meeting;
  upload: UploadTarget;
}

export interface Topic {
  title: string;
  summary: string;
  start_ms: number | null;
  end_ms: number | null;
}

export interface Decision {
  decision: string;
  context: string;
  made_by: string | null;
}

export interface Risk {
  description: string;
  kind: "risk" | "blocker";
  severity: "low" | "medium" | "high";
}

export interface OpenQuestion {
  question: string;
  raised_by: string | null;
}

export interface Deadline {
  item: string;
  date_text: string;
  date_normalized: string | null;
}

export interface HealthDimension {
  score: number;
  rationale: string;
}

export interface Report {
  executive_summary: string;
  topics: Topic[];
  decisions: Decision[];
  risks: Risk[];
  open_questions: OpenQuestion[];
  deadlines: Deadline[];
  next_meeting_agenda: string[];
  health_score: number;
  health_breakdown: Record<string, HealthDimension>;
  agent_warnings: Record<string, string>;
  model: string;
}

export interface Speaker {
  id: string;
  label: string;
  display_name: string;
}

export interface Segment {
  id: number;
  speaker_label: string;
  start_ms: number;
  end_ms: number;
  text: string;
}

export interface Transcript {
  segments: Segment[];
  speakers: Speaker[];
}

export interface MeetingDetail {
  meeting: Meeting;
  report: Report | null;
  speakers: Speaker[];
}

export interface StageStatus {
  stage: string;
  status: "started" | "succeeded" | "failed";
  detail: string | null;
  at: string;
}

export interface MeetingStatusOut {
  status: MeetingStatusValue;
  error_message: string | null;
  stages: StageStatus[];
}

export type ActionPriority = "low" | "medium" | "high" | "urgent";
export type ActionStatus = "open" | "in_progress" | "done" | "blocked";

export interface ActionItem {
  id: string;
  meeting_id: string;
  task: string;
  owner: string | null;
  due_date: string | null;
  priority: ActionPriority;
  status: ActionStatus;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface SpeakerStat {
  label: string;
  display_name: string;
  talk_time_ms: number;
  contribution_count: number;
  share: number;
}

export interface TopicSpeakerRow {
  topic: string;
  speakers: Record<string, number>;
}

export interface Analytics {
  speakers: SpeakerStat[];
  topics_by_speaker: TopicSpeakerRow[];
}

export interface ChatSource {
  chunk_id: number;
  start_ms: number | null;
  end_ms: number | null;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources: ChatSource[];
  created_at: string;
}

export interface ChatAnswer {
  answer: string;
  sources: ChatSource[];
}

export interface HealthPoint {
  date: string;
  score: number;
}

export interface DashboardStats {
  total_meetings: number;
  meetings_this_week: number;
  hours_processed: number;
  open_action_items: number;
  overdue_action_items: number;
  avg_health_score: number | null;
  health_trend: HealthPoint[];
}

export interface Insight {
  kind: string;
  message: string;
}

export interface EmailDraft {
  subject: string;
  body: string;
}
