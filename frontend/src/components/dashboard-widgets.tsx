"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type React from "react";
import {
  AlertCircle,
  Activity,
  CalendarClock,
  CheckCircle2,
  Clock,
  Flame,
  GraduationCap,
  Loader2,
  Moon,
  RefreshCw,
  ShieldCheck,
  Target,
  ZapOff
} from "lucide-react";
import { motion } from "framer-motion";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ComposedChart,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

import { ApiError, apiFetch, type RealtimeDashboard, type RealtimeTask } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ProgressBar } from "@/components/progress-ring";

const POLL_MS = 20000;

const containerVars = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.06 } }
};

const itemVars = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 260, damping: 24 } }
};

const tooltipStyle = {
  background: "rgba(9, 9, 11, 0.94)",
  border: "1px solid rgba(255,255,255,0.12)",
  borderRadius: "8px",
  color: "#fafafa"
};

export function DashboardWidgets() {
  const [data, setData] = useState<RealtimeDashboard | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const loadDashboard = useCallback(async (initial = false) => {
    if (!initial) {
      setRefreshing(true);
    }
    try {
      const realtime = await apiFetch<RealtimeDashboard>("/dashboard/realtime");
      setData(realtime);
      setLoadError(null);
      setLastUpdated(new Date());
    } catch (error) {
      if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
        setLoadError("Your session expired. Redirecting to login...");
      } else {
        setLoadError("Dashboard failed to load. Please refresh or sign in again.");
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard(true);
    const interval = window.setInterval(() => loadDashboard(false), POLL_MS);
    return () => window.clearInterval(interval);
  }, [loadDashboard]);

  const chartData = useMemo(() => {
    if (!data) {
      return [];
    }
    return data.weekly.task_completion.map((day) => {
      const focus = data.weekly.focus_minutes.find((item) => item.date === day.date);
      const study = data.weekly.study_minutes.find((item) => item.date === day.date);
      const sleep = data.weekly.sleep_hours.find((item) => item.date === day.date);
      const distraction = data.weekly.distraction_minutes.find((item) => item.date === day.date);
      return {
        date: compactDate(day.date),
        completion: day.completion,
        focus: focus?.minutes ?? 0,
        study: study?.minutes ?? 0,
        sleep: sleep?.hours ?? 0,
        distraction: distraction?.minutes ?? 0,
        score: sleep?.score ?? distraction?.score ?? 0
      };
    });
  }, [data]);

  const weakTopics = useMemo(() => data?.exams.flatMap((exam) => exam.weak_topics.map((topic) => ({ ...topic, exam: exam.name }))).slice(0, 8) ?? [], [data]);
  const todayCompletion = data ? Math.round((data.today.completed_tasks / Math.max(data.today.total_tasks, 1)) * 100) : 0;
  const plannerLocked = Boolean(data?.planner_window?.locked || data?.today.planner_status?.locked);
  const plannerMessage = data?.planner_window?.message ?? data?.today.planner_status?.message;

  if (loading && !data) {
    return <DashboardSkeleton />;
  }

  if (!data) {
    return (
      <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-6 text-sm text-red-100">
        {loadError}
      </div>
    );
  }

  return (
    <motion.div variants={containerVars} initial="hidden" animate="show" className="grid gap-6">
      <header className="flex flex-wrap items-end justify-between gap-4 border-b border-white/10 pb-5">
        <div>
          <p className="text-sm font-medium uppercase tracking-widest text-cyan-300">{formatLongDate(data.today.date)}</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-white sm:text-4xl">Planner command center</h1>
        </div>
        <div className="flex items-center gap-3 rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-xs text-zinc-300">
          {refreshing ? <Loader2 className="h-4 w-4 animate-spin text-cyan-300" /> : <RefreshCw className="h-4 w-4 text-emerald-300" />}
          <span>{lastUpdated ? `Updated ${lastUpdated.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}` : "Live sync ready"}</span>
        </div>
      </header>

      {loadError && (
        <div className="rounded-lg border border-amber-400/30 bg-amber-400/10 p-4 text-sm text-amber-100">
          {loadError}
        </div>
      )}

      {plannerLocked && (
        <div className="rounded-lg border border-cyan-400/25 bg-cyan-400/10 p-5 text-sm text-cyan-50">
          <p className="font-semibold">Waiting for June 1 start</p>
          <p className="mt-1 text-xs text-cyan-100/85">{plannerMessage}</p>
        </div>
      )}

      <section className="grid gap-3 md:grid-cols-[1fr_auto]">
        <div className={cn("rounded-lg border p-4 text-sm", plannerLocked || data.today.checkin_completed ? "border-emerald-400/20 bg-emerald-400/10 text-emerald-100" : "border-red-400/30 bg-red-500/10 text-red-100")}>
          <p className="font-semibold">{plannerLocked ? "Check-in locked until start" : data.today.checkin_completed ? "Daily check-in complete" : "Daily check-in required"}</p>
          <p className="mt-1 text-xs opacity-85">{plannerLocked ? "No score penalty or backlog is created before June 1." : "Wake, sleep, study hours, gym, distractions, mood, win, and failure feed tomorrow's plan."}</p>
        </div>
        <div className={cn("rounded-lg border p-4 text-sm", data.planner_window?.valid ? "border-cyan-400/20 bg-cyan-400/10 text-cyan-100" : "border-amber-400/30 bg-amber-400/10 text-amber-100")}>
          <p className="font-semibold">{plannerLocked ? "Planner waiting" : "Planner window"}</p>
          <p className="mt-1 text-xs">{plannerLocked ? `${data.planner_window?.days_until_start ?? 0} day(s) until ${data.today.planner_start_date}` : `${data.planner_window?.first_planner_day ?? data.today.planner_start_date} to ${data.planner_window?.last_planner_day ?? data.today.planner_end_date}`}</p>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <motion.div variants={itemVars}>
          <MetricCard title="Discipline Score" icon={ShieldCheck}>
            <div className="flex items-center gap-5">
              <ScoreRing value={data.today.discipline_score} />
              <div>
                <p className="text-3xl font-bold text-white">{data.today.discipline_score}/100</p>
                <p className="mt-1 text-sm text-zinc-400">Weekly avg {data.weekly.average_score}</p>
              </div>
            </div>
          </MetricCard>
        </motion.div>
        <motion.div variants={itemVars}>
          <MetricCard title="Today Progress" icon={CheckCircle2}>
            <p className="text-3xl font-bold text-white">{data.today.completed_tasks}/{data.today.total_tasks}</p>
            <p className="mt-1 text-sm text-zinc-400">tasks complete</p>
            <ProgressBar value={todayCompletion} className="mt-4 h-2 bg-white/10" />
          </MetricCard>
        </motion.div>
        <motion.div variants={itemVars}>
          <MetricCard title="Focus Minutes" icon={Clock}>
            <p className="text-3xl font-bold text-white">{data.today.focus_minutes}</p>
            <p className="mt-1 text-sm text-zinc-400">deep work logged today</p>
            <div className="mt-4 grid grid-cols-2 gap-2 text-xs text-zinc-400">
              <span className="rounded-md bg-white/[0.04] px-2 py-1">Sleep {data.today.sleep_hours}h</span>
              <span className="rounded-md bg-white/[0.04] px-2 py-1">Gym {data.today.gym_done ? "done" : "open"}</span>
            </div>
          </MetricCard>
        </motion.div>
        <motion.div variants={itemVars}>
          <MetricCard title="Streak" icon={Flame}>
            <p className="text-3xl font-bold text-white">{data.streak.current} days</p>
            <p className="mt-1 text-sm text-zinc-400">best {data.streak.best} days</p>
            <div className="mt-4 flex gap-1">
              {data.streak.calendar.map((day) => (
                <span key={day.date} title={`${day.date}: ${day.score}`} className={cn("h-7 flex-1 rounded", day.completed ? "bg-emerald-400/80" : "bg-white/10")} />
              ))}
            </div>
          </MetricCard>
        </motion.div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <motion.div variants={itemVars}>
          <MetricCard title="Comeback Mode" icon={AlertCircle}>
            <p className="text-2xl font-bold text-white">{data.comeback?.active ? "Active" : "Clear"}</p>
            <p className="mt-1 text-sm text-zinc-400">{data.comeback?.bad_days ?? 0} bad days · {data.comeback?.missed_checkins ?? 0} missed check-ins</p>
          </MetricCard>
        </motion.div>
        <motion.div variants={itemVars}>
          <MetricCard title="Reality Check" icon={Target}>
            <p className="text-2xl font-bold text-white">{data.monthly_reality_check?.exam_readiness ?? 0}%</p>
            <p className="mt-1 text-sm text-zinc-400">{data.monthly_reality_check?.projected_rank_readiness ?? "unknown"} · backlog {data.monthly_reality_check?.backlog_danger ?? "unknown"}</p>
          </MetricCard>
        </motion.div>
        <motion.div variants={itemVars}>
          <MetricCard title="Coach Mode" icon={ShieldCheck}>
            <p className="text-2xl font-bold text-white">{data.accountability_coach?.tomorrow_intensity ?? "recovery"}</p>
            <p className="mt-1 text-sm text-zinc-400">reason: {data.accountability_coach?.suggested_missed_reason ?? "check-in"}</p>
          </MetricCard>
        </motion.div>
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <motion.div variants={itemVars}>
          <ChartCard title="Weekly Study Load" icon={Activity}>
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="focusFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.42} />
                    <stop offset="95%" stopColor="#22d3ee" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
                <XAxis dataKey="date" stroke="#a1a1aa" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#a1a1aa" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={tooltipStyle} cursor={{ stroke: "rgba(255,255,255,0.18)" }} />
                <Area type="monotone" dataKey="focus" stroke="#22d3ee" strokeWidth={2} fill="url(#focusFill)" name="Focus minutes" />
                <Line type="monotone" dataKey="study" stroke="#f59e0b" strokeWidth={2} dot={false} name="Completed study minutes" />
              </AreaChart>
            </ResponsiveContainer>
          </ChartCard>
        </motion.div>
        <motion.div variants={itemVars}>
          <ChartCard title="Task Completion" icon={Target}>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={chartData}>
                <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
                <XAxis dataKey="date" stroke="#a1a1aa" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#a1a1aa" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgba(255,255,255,0.05)" }} />
                <Bar dataKey="completion" fill="#34d399" radius={[6, 6, 0, 0]} name="Completion %" />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        </motion.div>
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
        <motion.div variants={itemVars}>
          <ChartCard title="Sleep vs Productivity" icon={Moon}>
            <ResponsiveContainer width="100%" height={245}>
              <ComposedChart data={chartData}>
                <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
                <XAxis dataKey="date" stroke="#a1a1aa" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis yAxisId="left" stroke="#a1a1aa" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis yAxisId="right" orientation="right" stroke="#a1a1aa" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={tooltipStyle} />
                <Bar yAxisId="left" dataKey="sleep" fill="#60a5fa" radius={[6, 6, 0, 0]} name="Sleep hours" />
                <Line yAxisId="right" type="monotone" dataKey="score" stroke="#f8fafc" strokeWidth={2} dot={false} name="Score" />
              </ComposedChart>
            </ResponsiveContainer>
          </ChartCard>
        </motion.div>
        <motion.div variants={itemVars}>
          <ChartCard title="Distraction Impact" icon={ZapOff}>
            <ResponsiveContainer width="100%" height={245}>
              <LineChart data={chartData}>
                <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
                <XAxis dataKey="date" stroke="#a1a1aa" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#a1a1aa" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={tooltipStyle} />
                <Line type="monotone" dataKey="distraction" stroke="#fb7185" strokeWidth={2} name="Distraction minutes" />
                <Line type="monotone" dataKey="score" stroke="#a3e635" strokeWidth={2} dot={false} name="Score" />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>
        </motion.div>
      </section>

      <section className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <motion.div variants={itemVars}>
          <Card className="glass-card h-full border-white/10 bg-zinc-950/70">
            <CardHeader className="border-b border-white/10">
              <CardTitle className="flex items-center gap-2 text-white">
                <GraduationCap className="h-5 w-5 text-cyan-300" />
                Exam Countdown
              </CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3 pt-5">
              {data.exams.slice(0, 5).map((exam) => (
                <div key={exam.id} className="rounded-lg border border-white/10 bg-white/[0.04] p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-semibold text-white">{exam.name}</p>
                      <p className="mt-1 text-xs text-zinc-400">{exam.exam_date}</p>
                    </div>
                    <span className="rounded-md bg-cyan-400/10 px-2 py-1 text-xs font-semibold text-cyan-200">{exam.days_left}d</span>
                  </div>
                  <div className="mt-4 grid gap-2">
                    <ProgressLine label="Syllabus" value={exam.syllabus_completion} color="bg-cyan-300" />
                    <ProgressLine label="Readiness" value={exam.readiness_score} color="bg-emerald-300" />
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={itemVars}>
          <Card className="glass-card h-full border-white/10 bg-zinc-950/70">
            <CardHeader className="border-b border-white/10">
              <CardTitle className="flex items-center gap-2 text-white">
                <CalendarClock className="h-5 w-5 text-amber-300" />
                Today&apos;s Task Timeline
              </CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3 pt-5">
              {data.tasks.today.map((task, index) => (
                <TaskRow key={task.id} task={task} index={index} />
              ))}
              {data.tasks.today.length === 0 && <EmptyState label="No generated tasks for today" />}
            </CardContent>
          </Card>
        </motion.div>
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
        <motion.div variants={itemVars}>
          <PanelList
            title="Weak Topics"
            icon={Target}
            items={weakTopics.map((topic) => ({
              key: `${topic.exam}-${topic.id}`,
              title: topic.name,
              meta: `${topic.exam} - ${topic.progress}% complete - weakness ${topic.weak_score}`
            }))}
            empty="No weak topics detected"
          />
        </motion.div>
        <motion.div variants={itemVars}>
          <PanelList
            title="Warnings & Recommendations"
            icon={AlertCircle}
            items={[...data.today.warnings, ...data.recommendations].map((item, index) => ({
              key: `${index}-${item}`,
              title: item,
              meta: index < data.today.warnings.length ? "Warning" : "Recommendation"
            }))}
            empty="No warnings. Keep the plan moving."
          />
        </motion.div>
      </section>
    </motion.div>
  );
}

function MetricCard({ title, icon: Icon, children }: { title: string; icon: React.ElementType; children: React.ReactNode }) {
  return (
    <Card className="glass-card h-full border-white/10 bg-zinc-950/70">
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <CardTitle className="text-sm font-medium text-zinc-300">{title}</CardTitle>
        <Icon className="h-4 w-4 text-zinc-400" />
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

function ChartCard({ title, icon: Icon, children }: { title: string; icon: React.ElementType; children: React.ReactNode }) {
  return (
    <Card className="glass-card h-full border-white/10 bg-zinc-950/70">
      <CardHeader className="border-b border-white/10">
        <CardTitle className="flex items-center gap-2 text-white">
          <Icon className="h-5 w-5 text-zinc-300" />
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-5">{children}</CardContent>
    </Card>
  );
}

function ScoreRing({ value }: { value: number }) {
  const radius = 42;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (Math.min(Math.max(value, 0), 100) / 100) * circumference;

  return (
    <div className="relative h-28 w-28 shrink-0">
      <svg className="h-28 w-28 -rotate-90" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r={radius} stroke="rgba(255,255,255,0.1)" strokeWidth="8" fill="none" />
        <circle
          cx="50"
          cy="50"
          r={radius}
          stroke={value >= 70 ? "#34d399" : value >= 50 ? "#f59e0b" : "#fb7185"}
          strokeWidth="8"
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      <span className="absolute inset-0 grid place-items-center text-lg font-bold text-white">{value}</span>
    </div>
  );
}

function ProgressLine({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div>
      <div className="mb-1 flex justify-between text-xs text-zinc-400">
        <span>{label}</span>
        <span>{value}%</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-white/10">
        <div className={cn("h-full rounded-full", color)} style={{ width: `${Math.min(Math.max(value, 0), 100)}%` }} />
      </div>
    </div>
  );
}

function TaskRow({ task, index }: { task: RealtimeTask; index: number }) {
  return (
    <div className="grid grid-cols-[auto_1fr_auto] gap-3 rounded-lg border border-white/10 bg-white/[0.04] p-3">
      <div className={cn("mt-1 h-8 w-8 rounded-full border text-center text-xs font-bold leading-8", task.status === "completed" ? "border-emerald-300/40 text-emerald-200" : "border-cyan-300/30 text-cyan-200")}>
        {index + 1}
      </div>
      <div className="min-w-0">
        <p className={cn("truncate text-sm font-semibold", task.status === "completed" ? "text-zinc-500 line-through" : "text-zinc-100")}>{task.title}</p>
        <p className="mt-1 text-xs text-zinc-500">{task.task_type} - {task.estimated_minutes} min - priority {task.priority}</p>
      </div>
      <span className="h-fit rounded-md bg-white/[0.06] px-2 py-1 text-xs uppercase text-zinc-300">{task.status}</span>
    </div>
  );
}

function PanelList({ title, icon: Icon, items, empty }: { title: string; icon: React.ElementType; items: Array<{ key: string; title: string; meta: string }>; empty: string }) {
  return (
    <Card className="glass-card h-full border-white/10 bg-zinc-950/70">
      <CardHeader className="border-b border-white/10">
        <CardTitle className="flex items-center gap-2 text-white">
          <Icon className="h-5 w-5 text-zinc-300" />
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3 pt-5">
        {items.map((item) => (
          <div key={item.key} className="rounded-lg border border-white/10 bg-white/[0.04] p-3">
            <p className="text-sm font-semibold text-zinc-100">{item.title}</p>
            <p className="mt-1 text-xs text-zinc-500">{item.meta}</p>
          </div>
        ))}
        {items.length === 0 && <EmptyState label={empty} />}
      </CardContent>
    </Card>
  );
}

function DashboardSkeleton() {
  return (
    <div className="grid gap-6">
      <div className="h-20 animate-pulse rounded-lg bg-white/10" />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="h-40 animate-pulse rounded-lg bg-white/10" />
        ))}
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <div className="h-80 animate-pulse rounded-lg bg-white/10" />
        <div className="h-80 animate-pulse rounded-lg bg-white/10" />
      </div>
    </div>
  );
}

function EmptyState({ label }: { label: string }) {
  return <div className="rounded-lg border border-dashed border-white/10 p-6 text-center text-sm text-zinc-500">{label}</div>;
}

function compactDate(value: string) {
  return new Date(`${value}T00:00:00`).toLocaleDateString([], { month: "short", day: "numeric" });
}

function formatLongDate(value: string) {
  return new Date(`${value}T00:00:00`).toLocaleDateString([], { weekday: "long", month: "long", day: "numeric" });
}
