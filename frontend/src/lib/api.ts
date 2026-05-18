const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

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
  const res = await fetch(`${API_BASE}${path}`, {
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
  today_progress: number;
  weekly_progress: number;
  streak_count: number;
  productivity_score: number;
  focus_minutes: number;
  habit_completion_rate: number;
};
