"use client";

import { useEffect, useState } from "react";
import { Check, Loader2, TrendingUp, Calendar, AlertCircle, GraduationCap, ListChecks, Flame, Clock, Target } from "lucide-react";
import { motion } from "framer-motion";

import { apiFetch, type LifeNotification, type LiveDashboard } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ProgressBar } from "@/components/progress-ring";

const containerVars = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
};

const itemVars = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
};

export function DashboardWidgets() {
  const [liveData, setLiveData] = useState<LiveDashboard | null>(null);
  const [notifications, setNotifications] = useState<LifeNotification[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [liveRes, notificationRes] = await Promise.all([
          apiFetch<LiveDashboard>("/dashboard/live"),
          apiFetch<LifeNotification[]>("/notifications/live")
        ]);
        setLiveData(liveRes);
        setNotifications(notificationRes);
        setLoadError(null);
      } catch (error) {
        setLoadError(error instanceof Error ? error.message : "Dashboard failed to load");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const today = new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" });
  const tasks = liveData?.today_tasks ?? [];

  if (loadError) {
    return <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-6 text-sm text-red-200">Dashboard API error: {loadError}</div>;
  }

  if (!liveData) {
    return <div className="flex justify-center p-12"><Loader2 className="h-8 w-8 animate-spin text-purple-500" /></div>;
  }

  return (
    <div className="grid gap-8 p-2 max-w-7xl mx-auto">
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-white/10 pb-6">
        <div>
          <p className="text-sm font-medium text-purple-400 mb-1 uppercase tracking-widest">{today}</p>
          <h1 className="text-4xl font-bold tracking-tight text-white drop-shadow-sm">Welcome back</h1>
        </div>
        <Button className="glass border border-white/10 text-zinc-300 hover:text-white transition-all shadow-sm group hover:border-purple-500/50">
          {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Check className="h-4 w-4 mr-2 text-green-400 group-hover:scale-110 transition-transform" />} 
          {loading ? "Syncing..." : "Synced Just Now"}
        </Button>
      </div>

      <motion.section 
        variants={containerVars}
        initial="hidden"
        animate="show"
        className="grid gap-5 md:grid-cols-4"
      >
        <motion.div variants={itemVars}>
          <Card className="glass-card h-full relative group overflow-hidden border-blue-500/10">
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-purple-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
            <CardHeader className="pb-2 flex flex-row items-center justify-between relative z-10">
              <CardTitle className="text-zinc-400 text-sm font-medium tracking-wide">Productivity</CardTitle>
              <Target className="h-4 w-4 text-blue-400" />
            </CardHeader>
            <CardContent className="space-y-4 relative z-10">
              <div className="flex items-baseline gap-2">
                <span className="text-5xl font-extrabold tracking-tighter text-transparent bg-clip-text bg-gradient-to-br from-white via-blue-100 to-blue-400">
                  {liveData.productivity_score}%
                </span>
              </div>
              <ProgressBar value={liveData.productivity_score} className="h-2 bg-black/50" />
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={itemVars}>
          <Card className="glass-card h-full relative group overflow-hidden border-orange-500/10">
            <div className="absolute inset-0 bg-gradient-to-br from-orange-500/10 to-red-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
            <CardHeader className="pb-2 flex flex-row items-center justify-between relative z-10">
              <CardTitle className="text-zinc-400 text-sm font-medium tracking-wide">Habit Streak</CardTitle>
              <Flame className="h-4 w-4 text-orange-400" />
            </CardHeader>
            <CardContent className="flex items-center gap-5 pt-2 relative z-10">
              <div className="p-4 bg-orange-500/10 rounded-2xl">
                <Flame className="h-8 w-8 text-orange-400" />
              </div>
              <div>
                <p className="text-5xl font-extrabold tracking-tighter text-white">{liveData.current_streak}</p>
                <p className="text-xs text-zinc-500 font-medium uppercase tracking-wider mt-1">Days</p>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={itemVars}>
          <Card className="glass-card h-full relative group overflow-hidden border-emerald-500/10">
            <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/10 to-teal-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
            <CardHeader className="pb-2 flex flex-row items-center justify-between relative z-10">
              <CardTitle className="text-zinc-400 text-sm font-medium tracking-wide">Focus Minutes</CardTitle>
              <Clock className="h-4 w-4 text-emerald-400" />
            </CardHeader>
            <CardContent className="flex items-center gap-5 pt-2 relative z-10">
              <div className="p-4 bg-emerald-500/10 rounded-2xl">
                <Clock className="h-8 w-8 text-emerald-400" />
              </div>
              <div>
                <p className="text-5xl font-extrabold tracking-tighter text-white">{liveData.focus_minutes_today}</p>
                <p className="text-xs text-zinc-500 font-medium uppercase tracking-wider mt-1">Today</p>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={itemVars}>
          <Card className="glass-card h-full relative group overflow-hidden border-purple-500/10">
            <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-pink-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
            <CardHeader className="pb-2 flex flex-row items-center justify-between relative z-10">
              <CardTitle className="text-zinc-400 text-sm font-medium tracking-wide">Weekly Progress</CardTitle>
              <TrendingUp className="h-4 w-4 text-purple-400" />
            </CardHeader>
            <CardContent className="space-y-4 relative z-10">
              <div className="flex items-baseline gap-2">
                <span className="text-5xl font-extrabold tracking-tighter text-white">
                  {liveData.syllabus_completion}%
                </span>
              </div>
              <ProgressBar value={liveData.syllabus_completion} className="h-2 bg-black/50" />
            </CardContent>
          </Card>
        </motion.div>
      </motion.section>

      <motion.section 
        variants={containerVars}
        initial="hidden"
        animate="show"
        className="grid gap-5 lg:grid-cols-2"
      >
        <motion.div variants={itemVars}>
          <Card className="glass-card h-full">
            <CardHeader className="border-b border-white/5 pb-4">
              <CardTitle className="text-lg font-semibold text-white flex items-center gap-2">
                <GraduationCap className="h-5 w-5 text-purple-400" />
                Roadmap & Exams
              </CardTitle>
            </CardHeader>
            <CardContent className="grid gap-6 pt-6">
              {liveData.exam_readiness.map((exam) => (
                <div key={exam.exam_id} className="grid gap-3 group">
                  <div className="flex items-center justify-between gap-3 text-sm">
                    <span className="font-semibold text-zinc-200 group-hover:text-purple-400 transition-colors">{exam.name}</span>
                    <span className="text-zinc-300 bg-white/5 px-3 py-1 rounded-full text-xs font-medium border border-white/10 shadow-sm">{exam.days_left} days left</span>
                  </div>
                  <ProgressBar value={exam.readiness_score} className="h-2 bg-black/50" />
                </div>
              ))}
              {liveData.exam_readiness.length === 0 && (
                <div className="text-center py-10 text-zinc-500 flex flex-col items-center">
                  <Calendar className="h-10 w-10 mb-3 opacity-30" />
                  <p>No active roadmap items</p>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={itemVars}>
          <Card className="glass-card h-full">
            <CardHeader className="border-b border-white/5 pb-4 flex flex-row items-center justify-between">
              <CardTitle className="text-lg font-semibold text-white flex items-center gap-2">
                <ListChecks className="h-5 w-5 text-blue-400" />
                Today's Life Tasks
              </CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3 pt-6">
              {tasks.map((task) => (
                <div key={task.id} className="flex items-center justify-between gap-4 rounded-xl border border-white/5 bg-white/5 p-4 transition-all hover:bg-white/10 hover:border-white/10 group shadow-sm">
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-semibold truncate transition-colors ${task.status === "completed" ? "text-zinc-500 line-through" : "text-zinc-100 group-hover:text-white"}`}>
                      {task.title}
                    </p>
                    <p className="text-xs text-zinc-500 font-medium mt-1.5 flex items-center gap-2">
                      <span className={`w-1.5 h-1.5 rounded-full shadow-[0_0_8px_rgba(59,130,246,0.8)] ${task.status === "active" ? "bg-purple-500" : "bg-blue-500"}`} />
                      {task.status.toUpperCase()} · {task.task_type}
                    </p>
                  </div>
                  <div className="flex items-center justify-center relative">
                    <input 
                      type="checkbox" 
                      checked={task.status === "completed"} 
                      readOnly
                      className="peer h-6 w-6 appearance-none rounded-md border border-white/20 bg-black/50 checked:bg-blue-500 checked:border-blue-500 transition-all cursor-default shadow-inner" 
                    />
                    <Check className="h-3.5 w-3.5 text-white absolute pointer-events-none opacity-0 peer-checked:opacity-100 transition-opacity" />
                  </div>
                </div>
              ))}
              {tasks.length === 0 && (
                <div className="text-center py-10 text-zinc-500 flex flex-col items-center">
                  <ListChecks className="h-10 w-10 mb-3 opacity-30" />
                  <p>No tasks scheduled today</p>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </motion.section>

      {notifications.length > 0 && (
        <motion.div variants={containerVars} initial="hidden" animate="show">
          <Card className="glass-card border-orange-500/20 shadow-lg shadow-orange-500/5 relative overflow-hidden">
            <div className="absolute inset-0 bg-orange-500/5 pointer-events-none" />
            <CardHeader className="border-b border-orange-500/10 pb-4 relative z-10">
              <CardTitle className="text-lg font-semibold text-orange-400 flex items-center gap-2">
                <AlertCircle className="h-5 w-5" />
                Active Warnings
              </CardTitle>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-2 pt-6 relative z-10">
              {notifications.map((warning) => (
                <div key={warning.id} className="rounded-xl border border-white/5 bg-black/40 backdrop-blur-md p-5 flex gap-4 hover:border-orange-500/30 transition-colors shadow-sm">
                  <div className="mt-0.5 p-2 rounded-xl shrink-0 text-orange-400 bg-orange-500/10 border border-current shadow-sm">
                    <AlertCircle className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-xs font-bold uppercase tracking-widest mb-1.5" style={{ color: "var(--warning-color)" }}>{warning.level} ALERT</p>
                    <p className="text-sm text-zinc-300 font-medium leading-relaxed">{warning.body}</p>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  );
}
