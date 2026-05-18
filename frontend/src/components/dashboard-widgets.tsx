"use client";

import { useEffect, useState } from "react";
import { Check, Loader2, TriangleAlert, TrendingUp, Calendar, AlertCircle } from "lucide-react";
import { motion } from "framer-motion";

import { apiFetch, type Dashboard } from "@/lib/api";
import { dashboard as seedDashboard } from "@/lib/seed-data";
import { levelClass } from "@/lib/utils";
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
  const [data, setData] = useState<Dashboard>(seedDashboard);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch<Dashboard>("/dashboard")
      .then(setData)
      .catch(() => setData(seedDashboard))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="grid gap-8 p-2 max-w-7xl mx-auto">
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-zinc-800 pb-6">
        <div>
          <p className="text-sm font-medium text-purple-400 mb-1 uppercase tracking-wider">Overview</p>
          <h1 className="text-3xl font-bold tracking-tight text-zinc-100">Welcome back, {data.name.split(' ')[0]}</h1>
        </div>
        <Button className="bg-zinc-900 text-zinc-100 border border-zinc-800 hover:bg-zinc-800 hover:text-white transition-all shadow-sm">
          {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Check className="h-4 w-4 mr-2 text-green-400" />} 
          {loading ? "Syncing..." : "Synced Just Now"}
        </Button>
      </div>

      <motion.section 
        variants={containerVars}
        initial="hidden"
        animate="show"
        className="grid gap-5 md:grid-cols-3"
      >
        <motion.div variants={itemVars}>
          <Card className="bg-zinc-950/50 border-zinc-800/80 shadow-xl overflow-hidden relative group">
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            <CardHeader className="pb-2 flex flex-row items-center justify-between">
              <CardTitle className="text-zinc-400 text-sm font-medium">Daily Completion</CardTitle>
              <TrendingUp className="h-4 w-4 text-blue-400" />
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-bold tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
                  {data.daily_completion}%
                </span>
              </div>
              <ProgressBar value={data.daily_completion} className="h-2 bg-zinc-900 [&>div]:bg-gradient-to-r [&>div]:from-blue-500 [&>div]:to-purple-500" />
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={itemVars}>
          <Card className="bg-zinc-950/50 border-zinc-800/80 shadow-xl overflow-hidden relative group">
            <div className="absolute inset-0 bg-gradient-to-br from-orange-500/5 to-red-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            <CardHeader className="pb-2 flex flex-row items-center justify-between">
              <CardTitle className="text-zinc-400 text-sm font-medium">Active Warnings</CardTitle>
              <TriangleAlert className="h-4 w-4 text-orange-400" />
            </CardHeader>
            <CardContent className="flex items-center gap-4 pt-2">
              <div className="p-3 bg-orange-500/10 rounded-2xl">
                <TriangleAlert className="h-8 w-8 text-orange-400" />
              </div>
              <div>
                <p className="text-4xl font-bold tracking-tighter text-zinc-100">{data.warnings.length}</p>
                <p className="text-xs text-zinc-500 font-medium">Require attention</p>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={itemVars}>
          <Card className="bg-zinc-950/50 border-zinc-800/80 shadow-xl overflow-hidden relative group">
            <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-teal-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            <CardHeader className="pb-2 flex flex-row items-center justify-between">
              <CardTitle className="text-zinc-400 text-sm font-medium">Roadmap Items</CardTitle>
              <Calendar className="h-4 w-4 text-emerald-400" />
            </CardHeader>
            <CardContent className="flex items-center gap-4 pt-2">
              <div className="p-3 bg-emerald-500/10 rounded-2xl">
                <Calendar className="h-8 w-8 text-emerald-400" />
              </div>
              <div>
                <p className="text-4xl font-bold tracking-tighter text-zinc-100">{data.roadmap.length}</p>
                <p className="text-xs text-zinc-500 font-medium">In progress</p>
              </div>
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
          <Card className="bg-zinc-950/50 border-zinc-800/80 shadow-xl h-full">
            <CardHeader className="border-b border-zinc-800/50 pb-4">
              <CardTitle className="text-lg font-semibold text-zinc-100 flex items-center gap-2">
                <GraduationCap className="h-5 w-5 text-purple-400" />
                Exam Countdown
              </CardTitle>
            </CardHeader>
            <CardContent className="grid gap-6 pt-6">
              {data.exams.map((exam) => (
                <div key={exam.id} className="grid gap-3 group">
                  <div className="flex items-center justify-between gap-3 text-sm">
                    <span className="font-semibold text-zinc-200 group-hover:text-purple-400 transition-colors">{exam.name}</span>
                    <span className="text-zinc-400 bg-zinc-900 px-2.5 py-1 rounded-full text-xs font-medium border border-zinc-800">{exam.days_left} days left</span>
                  </div>
                  <ProgressBar value={exam.progress} className="h-2 bg-zinc-900" />
                </div>
              ))}
              {data.exams.length === 0 && (
                <div className="text-center py-8 text-zinc-500 flex flex-col items-center">
                  <Calendar className="h-8 w-8 mb-2 opacity-50" />
                  <p>No exams approaching</p>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={itemVars}>
          <Card className="bg-zinc-950/50 border-zinc-800/80 shadow-xl h-full">
            <CardHeader className="border-b border-zinc-800/50 pb-4 flex flex-row items-center justify-between">
              <CardTitle className="text-lg font-semibold text-zinc-100 flex items-center gap-2">
                <ListChecks className="h-5 w-5 text-blue-400" />
                Today's Plan
              </CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3 pt-6">
              {data.tasks.map((task) => (
                <div key={task.id} className="flex items-center justify-between gap-4 rounded-xl border border-zinc-800/60 bg-zinc-900/30 p-4 transition-all hover:bg-zinc-900/80">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-zinc-200 truncate">{task.title}</p>
                    <p className="text-xs text-zinc-500 font-medium mt-1 flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                      {task.start_time} - {task.end_time}
                    </p>
                  </div>
                  <div className="flex items-center justify-center relative">
                    <input 
                      type="checkbox" 
                      defaultChecked={task.completed} 
                      className="peer h-6 w-6 appearance-none rounded-md border border-zinc-700 bg-zinc-900/50 checked:bg-blue-500 checked:border-blue-500 transition-all cursor-pointer" 
                    />
                    <Check className="h-3.5 w-3.5 text-white absolute pointer-events-none opacity-0 peer-checked:opacity-100 transition-opacity" />
                  </div>
                </div>
              ))}
              {data.tasks.length === 0 && (
                <div className="text-center py-8 text-zinc-500 flex flex-col items-center">
                  <ListChecks className="h-8 w-8 mb-2 opacity-50" />
                  <p>No tasks scheduled today</p>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </motion.section>

      {data.warnings.length > 0 && (
        <motion.div variants={containerVars} initial="hidden" animate="show">
          <Card className="bg-zinc-950/50 border-orange-900/30 shadow-xl overflow-hidden">
            <CardHeader className="bg-orange-950/10 border-b border-orange-900/20 pb-4">
              <CardTitle className="text-lg font-semibold text-orange-400 flex items-center gap-2">
                <AlertCircle className="h-5 w-5" />
                Active Warnings
              </CardTitle>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-2 pt-6">
              {data.warnings.map((warning) => (
                <div key={warning.id} className="rounded-xl border border-orange-900/30 bg-orange-950/10 p-4 flex gap-4">
                  <div className={`mt-0.5 p-2 rounded-lg shrink-0 ${levelClass(warning.level)} bg-opacity-10 border border-current`}>
                    <TriangleAlert className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-xs font-bold uppercase tracking-wider mb-1" style={{ color: "var(--warning-color)" }}>{warning.level} ALERT</p>
                    <p className="text-sm text-zinc-300 font-medium leading-relaxed">{warning.message}</p>
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
