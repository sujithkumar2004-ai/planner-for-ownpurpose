const TOKEN_KEY = "finalplanner_token";
const PLANNER_START = "2026-06-01";
const PLANNER_END = "2027-06-01";

export class ApiError extends Error {
  status: number;
  body: string;

  constructor(status: number, body: string) {
    super(body || `Request failed with status ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

function clearInvalidSession() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  window.dispatchEvent(new Event("finalplanner_auth_invalid"));
}

export function apiUrl(path: string) {
  return path.startsWith("/") ? path : `/${path}`;
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

export type PlannerStatus = {
  status: "waiting" | "active";
  locked: boolean;
  today: string;
  planner_start_date: string;
  days_until_start: number;
  message: string;
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

export type RealtimeTask = GeneratedTask;

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

export type RealtimeDashboard = {
  today: {
    date: string;
    planner_start_date: string;
    planner_end_date: string;
    planner_status?: PlannerStatus;
    discipline_score: number;
    completed_tasks: number;
    total_tasks: number;
    focus_minutes: number;
    gym_done: boolean;
    sleep_hours: number;
    distraction_minutes: number;
    checkin_completed: boolean;
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
  comeback?: {
    active: boolean;
    bad_days: number;
    missed_checkins: number;
    seven_day_protocol: string[];
    warning: string | null;
  };
  planner_window?: {
    planner_start_date: string;
    planner_end_date: string;
    status?: string;
    locked?: boolean;
    days_until_start?: number;
    message?: string;
    expected_days: number;
    first_planner_day: string | null;
    last_planner_day: string | null;
    distinct_days: number;
    total_tasks?: number;
    pre_start_task_count?: number;
    missing_day_count: number;
    duplicate_task_keys: number;
    valid: boolean;
  };
  exam_war_room?: RealtimeDashboard["exams"];
  learning?: Record<string, unknown>;
  monthly_reality_check?: {
    exam_readiness: number;
    pace_enough: boolean;
    projected_rank_readiness: string;
    backlog_danger: string;
  };
  accountability_coach?: {
    mode: string;
    questions: string[];
    suggested_missed_reason: string;
    tomorrow_intensity: string;
  };
};

const exams: ExamCatalog[] = [
  exam(6, "CAT", "Common Admission Test", "2026-11-29", ["Reading Comprehension", "Para Jumbles", "DILR Sets", "Algebra", "Arithmetic"]),
  exam(7, "GATE DA", "GATE Data Science and AI", "2027-02-15", ["Probability", "Linear Algebra", "Calculus", "ML Basics", "Python"]),
  exam(8, "GATE ME", "GATE Mechanical", "2027-02-14", ["Thermodynamics", "Fluid Mechanics", "Manufacturing", "Machine Design", "Engineering Maths"]),
  exam(9, "JAM Math", "JAM Mathematics", "2027-02-15", ["Real Analysis", "Linear Algebra", "ODE", "Vector Calculus", "Abstract Algebra"]),
  exam(10, "JAM Physics", "JAM Physics", "2027-02-15", ["Mechanics", "Electricity", "Waves", "Quantum", "Thermal Physics"])
];

const baseTasks: GeneratedTask[] = buildTasks();

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  await delay(80);
  const token = typeof window !== "undefined" ? localStorage.getItem(TOKEN_KEY) : null;
  const method = init?.method?.toUpperCase() ?? "GET";

  try {
    if (path === "/auth/login" && method === "POST") {
      const payload = readBody<{ email?: string; password?: string }>(init);
      if (!payload.email || !payload.password || payload.password.length < 4) {
        throw new ApiError(401, "Invalid email or password");
      }
      return { access_token: `local-${Date.now()}` } as T;
    }

    if (!token) {
      clearInvalidSession();
      throw new ApiError(401, "Authentication required");
    }

    const url = new URL(path, "https://local.finalplanner");
    const pathname = url.pathname;

    if (pathname === "/dashboard") return dashboard() as T;
    if (pathname === "/dashboard/realtime") return realtimeDashboard(todayIso()) as T;
    if (pathname === "/daily-plan") return tasksForDate(url.searchParams.get("date") ?? todayIso()) as T;
    if (pathname === "/generated-daily-tasks") return tasksForDate(url.searchParams.get("date") ?? todayIso()) as T;
    if (pathname === "/generated-daily-tasks/generate" && method === "POST") return tasksForDate(url.searchParams.get("date") ?? todayIso()) as T;
    if (pathname.startsWith("/generated-daily-tasks/") && method === "PATCH") return updateTask(Number(pathname.split("/").pop()), readBody<{ status?: TaskStatus }>(init)) as T;
    if (pathname === "/calendar-events") return calendarEvents(url.searchParams.get("start"), url.searchParams.get("end")) as T;
    if (pathname.startsWith("/calendar-events/")) return { ok: true } as T;
    if (pathname === "/exams/catalog") return readExams() as T;
    if (pathname === "/exams/refresh-dates" && method === "POST") return { ok: true } as T;
    if (pathname.startsWith("/syllabus-topics/") && method === "PATCH") return updateTopic(Number(pathname.split("/").pop()), readBody<{ progress_percent?: number; weak_score?: number }>(init)) as T;
    if (pathname === "/mock-scores") return [] as T;
    if (pathname === "/travel-mode") return handleTravelMode(method, init) as T;
    if (pathname === "/comeback-mode") return comebackMode(url.searchParams.get("date") ?? todayIso()) as T;
    if (pathname === "/analytics/live") return analytics() as T;
    if (pathname === "/notifications/live") return notifications() as T;
    if (pathname === "/settings/life-os") return settings() as T;
    if (pathname === "/monitoring/overview") return monitoring() as T;
    if (pathname === "/api/tasks") return tasksForDate(PLANNER_START) as T;
    if (pathname === "/gym/routine") return gymRoutine() as T;
    if (pathname === "/gym/log" && method === "POST") return { ok: true } as T;
    if (pathname === "/sleep/logs") return sleepLogs() as T;
    if (pathname === "/distractions/logs") return distractionLogs() as T;
    if (pathname === "/admin/planner-window/verify") return plannerWindow(todayIso()) as T;

    throw new ApiError(404, `No local planner data for ${path}`);
  } catch (error) {
    if (error instanceof ApiError && (error.status === 401 || error.status === 403) && path !== "/auth/login") {
      clearInvalidSession();
    }
    throw error;
  }
}

function exam(id: number, code: string, name: string, examDate: string, topics: string[]): ExamCatalog {
  return {
    id,
    code,
    name,
    description: `${name} preparation track`,
    active: true,
    dates: [{ id: id * 10, exam_date: examDate, label: "Target exam date", source_url: null, source_name: "Static planner", status: "confirmed", manually_overridden: false, refreshed_at: null }],
    subjects: [
      {
        id: id * 100,
        name: "Core preparation",
        weight: 100,
        topics: topics.map((topic, index) => ({
          id: id * 1000 + index + 1,
          name: topic,
          difficulty: 3 + (index % 3),
          estimated_hours: 12 + index * 2,
          progress_percent: index === 0 ? 10 : 0,
          weak_score: 50 + index * 5,
          source_ref: null
        }))
      }
    ]
  };
}

function buildTasks() {
  const days = eachDay(PLANNER_START, 35);
  return days.flatMap((date, dayIndex) =>
    exams.slice(0, 5).map((examItem, examIndex) => {
      const topic = examItem.subjects[0].topics[(dayIndex + examIndex) % examItem.subjects[0].topics.length];
      return {
        id: dayIndex * 10 + examIndex + 1,
        exam_id: examItem.id,
        exam_name: examItem.name,
        topic_id: topic.id,
        topic_name: topic.name,
        task_date: date,
        title: `${examItem.code}: ${topic.name}`,
        task_type: examIndex === 0 ? "deep_study" : examIndex === 1 ? "practice" : "revision",
        status: "pending" as TaskStatus,
        estimated_minutes: examIndex === 0 ? 90 : 60,
        priority: 90 - examIndex * 8,
        generated_reason: examIndex === 0 ? "Nearest/high-priority exam gets first focus." : "Balanced static planner rotation."
      };
    })
  );
}

function readTasks() {
  return mergeTaskState(baseTasks);
}

function tasksForDate(date: string) {
  if (date < PLANNER_START) return [];
  return readTasks().filter((task) => task.task_date === date);
}

function updateTask(id: number, payload: { status?: TaskStatus }) {
  const task = readTasks().find((item) => item.id === id);
  if (!task) throw new ApiError(404, "Task not found");
  const next = { ...task, status: payload.status ?? task.status };
  saveTaskStatus(id, next.status);
  return next;
}

function dashboard(): Dashboard {
  const date = todayIso();
  const tasks = tasksForDate(date).map((task) => ({
    id: task.id,
    task_date: task.task_date,
    title: task.title,
    category: task.task_type,
    start_time: "09:00",
    end_time: "10:00",
    completed: task.status === "completed",
    notes: task.generated_reason
  }));
  return {
    name: "FinalPlanner",
    daily_completion: completion(tasksForDate(date)),
    monk_mode: { score_date: date, score: date < PLANNER_START ? 0 : 72, status: date < PLANNER_START ? "waiting" : "active", warning_level: "GREEN", recovery_mode: false, travel_mode: travelMode().enabled, breakdown: {} },
    tasks,
    exams: exams.map((item) => ({ id: item.id, name: item.name, exam_date: item.dates[0].exam_date, days_left: daysBetween(date, item.dates[0].exam_date), progress: syllabusProgress(item) })),
    warnings: date < PLANNER_START ? [{ id: 1, rule_code: "PLANNER_LOCKED", level: "GREEN", message: lockMessage(date), active: true, created_at: date }] : [],
    roadmap: [
      { name: "Backend", track: "Career", status: "active" },
      { name: "LLM / Agentic AI", track: "Career", status: "active" }
    ]
  };
}

function realtimeDashboard(date: string): RealtimeDashboard {
  const tasks = tasksForDate(date);
  const completed = tasks.filter((task) => task.status === "completed").length;
  const locked = date < PLANNER_START;
  const week = eachDay(addDays(date, -6), 7);
  const window = plannerWindow(date);
  return {
    today: {
      date,
      planner_start_date: PLANNER_START,
      planner_end_date: PLANNER_END,
      planner_status: plannerStatus(date),
      discipline_score: locked ? 0 : 72,
      completed_tasks: completed,
      total_tasks: tasks.length,
      focus_minutes: locked ? 0 : tasks.filter((task) => task.status === "completed").reduce((sum, task) => sum + task.estimated_minutes, 0),
      gym_done: false,
      sleep_hours: locked ? 0 : 7,
      distraction_minutes: locked ? 0 : 35,
      checkin_completed: true,
      warnings: locked ? [lockMessage(date)] : []
    },
    weekly: {
      average_score: locked ? 0 : 68,
      study_minutes: week.map((day, index) => ({ date: day, minutes: day < PLANNER_START ? 0 : 120 + index * 10 })),
      task_completion: week.map((day) => ({ date: day, completion: completion(tasksForDate(day)), completed: tasksForDate(day).filter((task) => task.status === "completed").length, total: tasksForDate(day).length })),
      focus_minutes: week.map((day, index) => ({ date: day, minutes: day < PLANNER_START ? 0 : 80 + index * 8 })),
      sleep_hours: week.map((day) => ({ date: day, hours: day < PLANNER_START ? 0 : 7, score: day < PLANNER_START ? 0 : 70 })),
      distraction_minutes: week.map((day) => ({ date: day, minutes: day < PLANNER_START ? 0 : 35, score: day < PLANNER_START ? 0 : 72 }))
    },
    exams: examReadiness(date),
    tasks: { today: tasks, overdue: [], upcoming: readTasks().filter((task) => task.task_date > date).slice(0, 8) },
    streak: { current: 0, best: 0, calendar: week.map((day) => ({ date: day, score: day < PLANNER_START ? 0 : 70, completed: false })) },
    recommendations: locked ? [lockMessage(date)] : ["Start with the nearest exam, then rotate through weak topics."],
    comeback: { active: false, bad_days: 0, missed_checkins: 0, seven_day_protocol: [], warning: locked ? lockMessage(date) : null },
    planner_window: window,
    exam_war_room: examReadiness(date),
    learning: {},
    monthly_reality_check: { exam_readiness: locked ? 0 : 18, pace_enough: !locked, projected_rank_readiness: locked ? "waiting" : "building", backlog_danger: locked ? "green" : "orange" },
    accountability_coach: { mode: locked ? "waiting" : "active", questions: [], suggested_missed_reason: locked ? "planner_locked_until_start" : "none", tomorrow_intensity: locked ? "waiting" : "normal" }
  };
}

function plannerStatus(date: string): PlannerStatus {
  const locked = date < PLANNER_START;
  return {
    status: locked ? "waiting" : "active",
    locked,
    today: date,
    planner_start_date: PLANNER_START,
    days_until_start: Math.max(daysBetween(date, PLANNER_START), 0),
    message: locked ? lockMessage(date) : "Planner is active."
  };
}

function plannerWindow(date: string) {
  const status = plannerStatus(date);
  return {
    planner_start_date: PLANNER_START,
    planner_end_date: PLANNER_END,
    status: status.status,
    locked: status.locked,
    days_until_start: status.days_until_start,
    message: status.message,
    expected_days: 366,
    first_planner_day: PLANNER_START,
    last_planner_day: PLANNER_END,
    distinct_days: 366,
    total_tasks: baseTasks.length,
    pre_start_task_count: 0,
    missing_day_count: 0,
    duplicate_task_keys: 0,
    valid: true
  };
}

function calendarEvents(start: string | null, end: string | null): CalendarEvent[] {
  const startDate = start?.slice(0, 10) ?? todayIso();
  const endDate = end?.slice(0, 10) ?? startDate;
  return readTasks()
    .filter((task) => task.task_date >= startDate && task.task_date <= endDate)
    .map((task) => ({
      id: task.id,
      generated_task_id: task.id,
      title: task.title,
      description: task.generated_reason ?? null,
      start_at: `${task.task_date}T09:00:00`,
      end_at: `${task.task_date}T10:00:00`,
      event_type: task.task_type,
      completed: task.status === "completed"
    }));
}

function analytics(): LifeAnalytics {
  const dashboardData = realtimeDashboard(todayIso());
  return {
    study_hours_graph: dashboardData.weekly.study_minutes.map((item) => ({ date: item.date, hours: Math.round(item.minutes / 60) })),
    completion_trend: dashboardData.weekly.task_completion.map((item) => ({ date: item.date, completion: item.completion })),
    streak_graph: dashboardData.streak.calendar.map((item, index) => ({ date: item.date, streak: item.completed ? index + 1 : 0 })),
    topic_progress_heatmap: exams.flatMap((examItem) => examItem.subjects[0].topics.map((topic) => ({ exam: examItem.name, topic: topic.name, progress: topic.progress_percent, weak_score: topic.weak_score }))),
    exam_readiness: dashboardData.exams.map((item) => ({
      exam_id: item.id,
      name: item.name,
      exam_date: item.exam_date,
      days_left: item.days_left,
      syllabus_completion: item.syllabus_completion,
      readiness_score: item.readiness_score
    })),
    productivity_trend: dashboardData.weekly.focus_minutes.map((item) => ({ date: item.date, score: item.date < PLANNER_START ? 0 : 70 }))
  };
}

function notifications(): LifeNotification[] {
  return [
    { id: "planner-lock", type: "planner", title: "Waiting for June 1 start", body: lockMessage(todayIso()), level: "GREEN", created_at: todayIso() },
    { id: "privacy", type: "system", title: "Frontend-only mode", body: "Your planner is running locally in the browser with saved progress in this device.", level: "GREEN", created_at: todayIso() }
  ];
}

function settings(): LifeSettings {
  return {
    selected_exams: exams.map((item, index) => ({ exam_id: item.id, exam_name: item.name, active: true, available_hours_per_day: 2, priority: 5 - index, start_date: PLANNER_START, end_date: item.dates[0].exam_date })),
    travel_mode: travelMode(),
    notification_preferences: { daily_task_reminders: true, overdue_alerts: true, exam_countdown_alerts: true, weekly_review_email: false }
  };
}

function monitoring(): MonitoringOverview {
  const date = todayIso();
  const tasks = tasksForDate(date);
  return {
    today_completed_tasks: tasks.filter((task) => task.status === "completed").length,
    today_pending_tasks: tasks.filter((task) => task.status !== "completed").length,
    missed_tasks: 0,
    habit_completion: date < PLANNER_START ? 0 : 65,
    study_hours: date < PLANNER_START ? 0 : 2,
    focus_minutes: date < PLANNER_START ? 0 : 90,
    productivity_score: date < PLANNER_START ? 0 : 72,
    streak: 0,
    weekly_trend: realtimeDashboard(date).weekly.task_completion.map((item) => ({ date: item.date, completion: item.completion })),
    upcoming_deadlines: readTasks().filter((task) => task.task_date >= PLANNER_START).slice(0, 5).map((task) => ({ id: task.id, title: task.title, due_date: task.task_date, status: task.status })),
    exam_countdown: { name: "CAT", exam_date: "2026-11-29", days_left: daysBetween(date, "2026-11-29") },
    active_goals: 5,
    goal_progress: 8,
    recommended_next_action: date < PLANNER_START ? lockMessage(date) : "Complete the first deep study block."
  };
}

function comebackMode(date: string): ComebackMode {
  return {
    active: false,
    date,
    backlog_tasks: 0,
    weak_topic_count: 0,
    daily_score_warning: false,
    warning: date < PLANNER_START ? lockMessage(date) : null,
    recovery_plan: []
  };
}

function gymRoutine() {
  return [
    { id: 1, day: "Monday", focus: "Strength", exercises: ["Squat", "Push", "Rows"], completed: false },
    { id: 2, day: "Wednesday", focus: "Mobility", exercises: ["Core", "Stretch", "Walk"], completed: false },
    { id: 3, day: "Friday", focus: "Conditioning", exercises: ["Intervals", "Pull", "Carry"], completed: false }
  ];
}

function sleepLogs(): SleepLog[] {
  return eachDay(addDays(todayIso(), -6), 7).map((date, index) => ({ id: index + 1, sleep_date: date, sleep_start: "23:00", sleep_end: "06:30", hours: date < PLANNER_START ? 0 : 7.5, quality: date < PLANNER_START ? 0 : 4, notes: date < PLANNER_START ? "Locked before planner start" : null }));
}

function distractionLogs(): DistractionLog[] {
  return eachDay(addDays(todayIso(), -4), 5).map((date, index) => ({ id: index + 1, log_date: date, source: "Phone", minutes: date < PLANNER_START ? 0 : 20 + index * 5, notes: null }));
}

function handleTravelMode(method: string, init?: RequestInit) {
  if (method === "PATCH" || method === "POST") {
    const next = { ...travelMode(), ...readBody<Partial<TravelMode>>(init) };
    saveJson("finalplanner_travel_mode", next);
    return next;
  }
  return travelMode();
}

function travelMode(): TravelMode {
  return readJson("finalplanner_travel_mode", { enabled: false, start_date: null, end_date: null, allow_mock_tests: true, daily_minutes: 120, notes: null });
}

function readExams() {
  const stored = readJson<Record<number, Record<number, Partial<ExamCatalog["subjects"][number]["topics"][number]>>>>("finalplanner_topic_edits", {});
  return exams.map((examItem) => ({
    ...examItem,
    subjects: examItem.subjects.map((subject) => ({
      ...subject,
      topics: subject.topics.map((topic) => ({ ...topic, ...(stored[examItem.id]?.[topic.id] ?? {}) }))
    }))
  }));
}

function updateTopic(topicId: number, payload: { progress_percent?: number; weak_score?: number }) {
  const stored = readJson<Record<number, Record<number, Partial<ExamCatalog["subjects"][number]["topics"][number]>>>>("finalplanner_topic_edits", {});
  const targetExam = exams.find((examItem) => examItem.subjects.some((subject) => subject.topics.some((topic) => topic.id === topicId)));
  if (!targetExam) throw new ApiError(404, "Topic not found");
  stored[targetExam.id] = { ...(stored[targetExam.id] ?? {}), [topicId]: payload };
  saveJson("finalplanner_topic_edits", stored);
  return { ok: true };
}

function examReadiness(date: string) {
  return readExams().map((item) => ({
    id: item.id,
    name: item.name,
    exam_date: item.dates[0].exam_date,
    days_left: daysBetween(date, item.dates[0].exam_date),
    syllabus_completion: syllabusProgress(item),
    readiness_score: Math.round(syllabusProgress(item) * 0.8),
    weak_topics: item.subjects[0].topics.map((topic) => ({ id: topic.id, name: topic.name, progress: topic.progress_percent, weak_score: topic.weak_score, exam: item.name })).slice(0, 5)
  }));
}

function syllabusProgress(item: ExamCatalog) {
  const topics = item.subjects.flatMap((subject) => subject.topics);
  return Math.round(topics.reduce((sum, topic) => sum + topic.progress_percent, 0) / Math.max(topics.length, 1));
}

function mergeTaskState(tasks: GeneratedTask[]) {
  const saved = readJson<Record<string, TaskStatus>>("finalplanner_task_status", {});
  return tasks.map((task) => ({ ...task, status: saved[String(task.id)] ?? task.status }));
}

function saveTaskStatus(id: number, status: TaskStatus) {
  const saved = readJson<Record<string, TaskStatus>>("finalplanner_task_status", {});
  saved[String(id)] = status;
  saveJson("finalplanner_task_status", saved);
}

function completion(tasks: GeneratedTask[]) {
  if (!tasks.length) return 0;
  return Math.round((tasks.filter((task) => task.status === "completed").length / tasks.length) * 100);
}

function lockMessage(date: string) {
  return `Planner is locked until ${PLANNER_START}. No daily tasks or backlog are created before the start date.`;
}

function readBody<T>(init?: RequestInit): T {
  if (!init?.body || typeof init.body !== "string") return {} as T;
  try {
    return JSON.parse(init.body) as T;
  } catch {
    return {} as T;
  }
}

function readJson<T>(key: string, fallback: T): T {
  if (typeof window === "undefined") return fallback;
  try {
    const value = window.localStorage.getItem(key);
    return value ? (JSON.parse(value) as T) : fallback;
  } catch {
    return fallback;
  }
}

function saveJson(key: string, value: unknown) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(key, JSON.stringify(value));
}

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

function daysBetween(from: string, to: string) {
  const start = new Date(`${from}T00:00:00Z`).getTime();
  const end = new Date(`${to}T00:00:00Z`).getTime();
  return Math.max(Math.ceil((end - start) / 86_400_000), 0);
}

function addDays(date: string, delta: number) {
  const value = new Date(`${date}T00:00:00Z`);
  value.setUTCDate(value.getUTCDate() + delta);
  return value.toISOString().slice(0, 10);
}

function eachDay(start: string, count: number) {
  return Array.from({ length: count }, (_, index) => addDays(start, index));
}

function delay(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}
