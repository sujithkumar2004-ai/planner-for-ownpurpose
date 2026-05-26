const API_BASE = (
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  (process.env.NODE_ENV === "production" ? "https://planner-for-ownpurpose-production.up.railway.app" : "http://127.0.0.1:8000")
).replace(/\/+$/, "");

export function apiUrl(path: string) {
  return `${API_BASE}${path.startsWith("/") ? path : `/${path}`}`;
}

export type Task = {
  id: number;
  task_date: string;
  title: string;
  category: string;
  start_time: string;
  end_time: string;
  completed: boolean;
  notes?: string | null;
};

export type Warning = {
  id: number;
  rule_code: string;
  level: "GREEN" | "YELLOW" | "ORANGE" | "RED";
  message: string;
  active: boolean;
  created_at: string;
};

export type Dashboard = {
  name: string;
  daily_completion: number;
  monk_mode?: {
    score_date: string;
    score: number;
    status: string;
    warning_level: string;
    recovery_mode: boolean;
    travel_mode: boolean;
    breakdown: Record<string, number>;
  };
  tasks: Task[];
  exams: Array<{ id: number; name: string; exam_date: string; days_left: number; progress: number }>;
  warnings: Warning[];
  roadmap: Array<{ name: string; track: string; status: string }>;
};

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("finalplanner_token") : null;
  const res = await fetch(apiUrl(path), {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers
    },
    cache: "no-store"
  });
  if (!res.ok) {
    throw new Error(await res.text());
  }
  return res.json() as Promise<T>;
}

// --- NEW LIFE OS TYPES ---

export type GoalStatus = "active" | "completed" | "abandoned";
export type TaskStatus = "pending" | "active" | "completed" | "skipped" | "overdue";

export type Goal = {
  id: number;
  title: string;
  description: string | null;
  target_date: string | null;
  status: GoalStatus;
  progress_percent: number;
  created_at: string;
};

export type Milestone = {
  id: number;
  goal_id: number;
  title: string;
  target_date: string | null;
  completed: boolean;
};

export type LifeTask = {
  id: number;
  goal_id: number | null;
  milestone_id: number | null;
  title: string;
  status: TaskStatus;
  due_date: string | null;
  estimated_minutes: number | null;
  actual_minutes: number;
  created_at: string;
};

export type Habit = {
  id: number;
  title: string;
  frequency: string;
  current_streak: number;
  longest_streak: number;
};

export type LiveDashboard = {
  today_tasks: GeneratedTask[];
  completed_count: number;
  pending_count: number;
  overdue_count: number;
  active_task: GeneratedTask | null;
  current_streak: number;
  exam_readiness: Array<{ exam_id: number; name: string; exam_date: string; days_left: number; syllabus_completion: number; readiness_score: number }>;
  syllabus_completion: number;
  focus_minutes_today: number;
  focus_minutes_week: number;
  calendar_events_today: CalendarEvent[];
  next_exam_countdown: { name: string; exam_date: string; days_left: number } | null;
  weak_topics: Array<{ exam: string; topic: string; progress: number; weak_score: number }>;
  recommended_next_action: string;
  productivity_score: number;
  habit_completion_rate: number;
  travel_mode: boolean;
  comeback_mode?: ComebackMode;
};

export type RealtimeTask = {
  id: number;
  exam_id: number | null;
  exam_name?: string | null;
  topic_id: number | null;
  topic_name?: string | null;
  task_date: string;
  title: string;
  task_type: string;
  status: TaskStatus;
  estimated_minutes: number;
  priority: number;
  generated_reason?: string | null;
};

export type RealtimeDashboard = {
  today: {
    date: string;
    discipline_score: number;
    completed_tasks: number;
    total_tasks: number;
    focus_minutes: number;
    gym_done: boolean;
    sleep_hours: number;
    distraction_minutes: number;
    warnings: string[];
  };
  weekly: {
    average_score: number;
    study_minutes: Array<{ date: string; minutes: number }>;
    task_completion: Array<{ date: string; completion: number; completed: number; total: number }>;
    focus_minutes: Array<{ date: string; minutes: number }>;
    sleep_hours: Array<{ date: string; hours: number; score: number }>;
    distraction_minutes: Array<{ date: string; minutes: number; score: number }>;
  };
  exams: Array<{
    id: number;
    name: string;
    exam_date: string;
    days_left: number;
    syllabus_completion: number;
    readiness_score: number;
    weak_topics: Array<{ id: number; name: string; progress: number; weak_score: number; exam: string }>;
  }>;
  tasks: {
    today: RealtimeTask[];
    overdue: RealtimeTask[];
    upcoming: RealtimeTask[];
  };
  streak: {
    current: number;
    best: number;
    calendar: Array<{ date: string; score: number; completed: boolean }>;
  };
  recommendations: string[];
};

export type GeneratedTask = {
  id: number;
  exam_id: number | null;
  exam_name?: string | null;
  topic_id: number | null;
  topic_name?: string | null;
  task_date: string;
  title: string;
  task_type: string;
  status: TaskStatus;
  estimated_minutes: number;
  priority: number;
  generated_reason?: string | null;
};

export type CalendarEvent = {
  id: number;
  generated_task_id: number | null;
  title: string;
  description: string | null;
  start_at: string;
  end_at: string;
  event_type: string;
  completed: boolean;
};

export type ExamCatalog = {
  id: number;
  code: string;
  name: string;
  description: string | null;
  active: boolean;
  dates: Array<{ id: number; exam_date: string; label: string; source_url: string | null; source_name: string | null; status: string; manually_overridden: boolean; refreshed_at: string | null }>;
  subjects: Array<{ id: number; name: string; weight: number; topics: Array<{ id: number; name: string; difficulty: number; estimated_hours: number; progress_percent: number; weak_score: number; source_ref: string | null }> }>;
};

export type TravelMode = {
  enabled: boolean;
  start_date: string | null;
  end_date: string | null;
  allow_mock_tests: boolean;
  daily_minutes: number;
  notes: string | null;
};

export type StudyPlan = {
  id: number;
  exam_id: number;
  exam_name: string;
  active: boolean;
  available_hours_per_day: number;
  priority: number;
  start_date: string;
  end_date: string;
};

export type ComebackMode = {
  active: boolean;
  date: string;
  backlog_tasks: number;
  weak_topic_count: number;
  daily_score_warning: boolean;
  warning: string | null;
  recovery_plan: Array<{ topic_id: number; topic: string; progress: number; weak_score: number; action: string }>;
};

export type MockScore = {
  id: number;
  exam_id: number;
  exam_name: string | null;
  taken_on: string;
  score: number;
  max_score: number;
  analysis: string | null;
  weak_topics: Record<string, unknown>;
};

export type LifeAnalytics = {
  study_hours_graph: Array<{ date: string; hours: number }>;
  completion_trend: Array<{ date: string; completion: number }>;
  streak_graph: Array<{ date: string; streak: number }>;
  topic_progress_heatmap: Array<{ exam: string; topic: string; progress: number; weak_score: number }>;
  exam_readiness: Array<{ exam_id: number; name: string; exam_date: string; days_left: number; syllabus_completion: number; readiness_score: number }>;
  productivity_trend: Array<{ date: string; score: number }>;
};

export type LifeNotification = {
  id: string;
  type: string;
  title: string;
  body: string;
  level: "GREEN" | "YELLOW" | "ORANGE" | "RED";
  created_at: string;
};

export type LifeSettings = {
  selected_exams: Array<{ exam_id: number; exam_name: string; active: boolean; available_hours_per_day: number; priority: number; start_date: string; end_date: string }>;
  travel_mode: TravelMode;
  notification_preferences: {
    daily_task_reminders: boolean;
    overdue_alerts: boolean;
    exam_countdown_alerts: boolean;
    weekly_review_email: boolean;
  };
};

export type MonitoringOverview = {
  today_completed_tasks: number;
  today_pending_tasks: number;
  missed_tasks: number;
  habit_completion: number;
  study_hours: number;
  focus_minutes: number;
  productivity_score: number;
  streak: number;
  weekly_trend: Array<{ date: string; completion: number }>;
  upcoming_deadlines: Array<{ id: number; title: string; due_date: string | null; status: string }>;
  exam_countdown: { name: string; exam_date: string; days_left: number } | null;
  active_goals: number;
  goal_progress: number;
  recommended_next_action: string;
};

export type MonitoringDaily = {
  date: string;
  tasks: GeneratedTask[];
  completed_tasks: number;
  pending_tasks: number;
  overdue_tasks: number;
  habit_completion: number;
  focus_minutes: number;
  productivity_score: number;
};

export type MonitoringWeekly = {
  week_start: string;
  week_end: string;
  days: MonitoringDaily[];
  completed_tasks: number;
  pending_tasks: number;
  focus_minutes: number;
  average_productivity_score: number;
};

export type SleepLog = {
  id: number;
  sleep_date: string;
  sleep_start: string | null;
  sleep_end: string | null;
  hours: number;
  quality: number;
  notes: string | null;
};

export type DistractionLog = {
  id: number;
  log_date: string;
  source: string;
  minutes: number;
  notes: string | null;
};
